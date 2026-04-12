/**
 * Real-time Notification System using Django Channels WebSocket
 * Provides instant notifications like WhatsApp without page refresh
 * Falls back to HTTP polling if WebSocket is not available
 */

let notificationSocket = null;
let reconnectAttempts = 0;
let pollingInterval = null;
const MAX_RECONNECT_ATTEMPTS = 5;
const POLLING_INTERVAL = 60000; // 1 minute

/**
 * Initialize WebSocket connection for real-time notifications
 */
function initializeNotificationSocket() {
    // Only connect if user is authenticated (check for CSRF token)
    const csrfToken = document.querySelector('meta[name="csrf-token"]');
    if (!csrfToken) {
        console.log('User not authenticated, skipping WebSocket');
        return;
    }
    
    // Check if WebSocket is supported
    if (!('WebSocket' in window)) {
        console.warn('WebSocket not supported, falling back to polling');
        startNotificationPolling();
        return;
    }
    
    try {
        // Build WebSocket URL
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/notifications/`;
        
        console.log('Connecting to WebSocket:', wsUrl);
        
        // Create WebSocket connection
        notificationSocket = new WebSocket(wsUrl);
        
        // Connection opened
        notificationSocket.onopen = function(event) {
            console.log('✅ Notification WebSocket connected');
            reconnectAttempts = 0;
            // Stop polling if WebSocket is successful
            if (pollingInterval) {
                clearInterval(pollingInterval);
                pollingInterval = null;
            }
        };
        
        // Receive message
        notificationSocket.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                handleSocketMessage(data);
            } catch (e) {
                console.error('Error parsing notification message:', e);
            }
        };
        
        // Connection closed
        notificationSocket.onclose = function(event) {
            console.log('⚠️ Notification WebSocket disconnected');
            if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                reconnectAttempts++;
                setTimeout(initializeNotificationSocket, 3000);
            } else {
                console.log('Max reconnection attempts reached, using HTTP polling');
                startNotificationPolling();
            }
        };
        
        // Connection error
        notificationSocket.onerror = function(error) {
            console.error('⚠️ WebSocket error:', error);
            console.log('Falling back to HTTP polling...');
            startNotificationPolling();
        };
        
    } catch (error) {
        console.error('Failed to initialize WebSocket:', error);
    }
}

/**
 * Handle incoming WebSocket messages
 */
function handleSocketMessage(data) {
    switch(data.type) {
        case 'connection_established':
            console.log('🔔', data.message);
            break;
            
        case 'new_notification':
            handleNewNotification(data.notification);
            break;
            
        case 'unread_count':
            updateNotificationBadge(data.count);
            break;
            
        case 'update':
            updateNotificationBadge(data.unread_count);
            break;
            
        default:
            console.log('Unknown message type:', data.type);
    }
}

/**
 * Handle new notification received via WebSocket
 */
function handleNewNotification(notification) {
    console.log('🆕 New notification:', notification);
    
    // Update badge
    incrementNotificationBadge();
    
    // Show browser notification
    showBrowserNotification(notification);
    
    // Show toast/alert
    showNotificationToast(notification);
    
    // Play notification sound (optional)
    playNotificationSound();
    
    // Update notification dropdown if it exists
    updateNotificationDropdown();
}

/**
 * Send message through WebSocket
 */
function sendSocketMessage(data) {
    if (notificationSocket && notificationSocket.readyState === WebSocket.OPEN) {
        notificationSocket.send(JSON.stringify(data));
    }
}

/**
 * Mark notification as read via WebSocket
 */
function markNotificationAsRead(notificationId) {
    sendSocketMessage({
        action: 'mark_read',
        notification_id: notificationId
    });
}

/**
 * Schedule reconnection attempt
 */
function scheduleReconnect() {
    if (reconnectTimeout < MAX_RECONNECT_TIMEOUT) {
        reconnectTimeout += 1000; // Increase by 1 second each attempt
    }
    
    console.log(`🔄 Reconnecting in ${reconnectTimeout}ms...`);
    
    setTimeout(() => {
        console.log('Attempting to reconnect...');
        initializeNotificationSocket();
    }, reconnectTimeout);
}

/**
 * Update notification badge count
 */
function updateNotificationBadge(count) {
    const badge = document.getElementById('notification-count');
    if (!badge) return;
    
    if (count > 0) {
        badge.textContent = count > 9 ? '9+' : count;
        badge.style.display = 'inline-block';
        badge.classList.add('animate__animated', 'animate__bounceIn');
    } else {
        badge.style.display = 'none';
        badge.classList.remove('animate__animated', 'animate__bounceIn');
    }
}

/**
 * Increment notification badge by 1
 */
function incrementNotificationBadge() {
    const badge = document.getElementById('notification-count');
    if (!badge) return;
    
    let currentCount = parseInt(badge.textContent) || 0;
    currentCount++;
    
    badge.textContent = currentCount > 9 ? '9+' : currentCount;
    badge.style.display = 'inline-block';
    badge.classList.add('animate__animated', 'animate__pulse');
}

/**
 * Show browser notification
 */
function showBrowserNotification(notification) {
    // Check if browser supports notifications
    if (!('Notification' in window)) {
        console.log('Browser notifications not supported');
        return;
    }
    
    // Request permission if needed
    if (Notification.permission === 'granted') {
        new Notification(notification.title, {
            body: notification.message,
            icon: '/static/images/blood-drop-icon.png',
            badge: '/static/images/badge-icon.png',
            tag: `notification-${notification.id}`,
            requireInteraction: false
        });
    } else if (Notification.permission !== 'denied') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                showBrowserNotification(notification);
            }
        });
    }
}

/**
 * Show toast notification
 */
function showNotificationToast(notification) {
    // Create toast element
    const toastContainer = document.getElementById('notification-toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = 'notification-toast animate__animated animate__slideInRight';
    toast.innerHTML = `
        <div class="toast-header bg-primary text-white">
            <i class="fas fa-bell"></i>
            <strong class="mr-2">${escapeHtml(notification.title)}</strong>
            <button type="button" class="ml-auto btn-close btn-close-white" onclick="this.closest('.notification-toast').remove()"></button>
        </div>
        <div class="toast-body">
            ${escapeHtml(notification.message)}
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        toast.classList.remove('animate__slideInRight');
        toast.classList.add('animate__slideOutRight');
        setTimeout(() => toast.remove(), 500);
    }, 5000);
}

/**
 * Create toast container if it doesn't exist
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'notification-toast-container';
    container.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        max-width: 400px;
    `;
    document.body.appendChild(container);
    return container;
}

/**
 * Play notification sound (optional)
 */
function playNotificationSound() {
    // Uncomment to enable sound
    // const audio = new Audio('/static/sounds/notification.mp3');
    // audio.play().catch(e => console.log('Sound play failed:', e));
}

/**
 * Update notification dropdown content
 */
async function updateNotificationDropdown() {
    const notificationList = document.getElementById('notification-list');
    if (!notificationList) return;
    
    try {
        const response = await fetch('/api/notifications/list/');
        const notifications = await response.json();
        
        if (notifications.length === 0) {
            notificationList.innerHTML = `
                <li class="dropdown-item-text no-notifications">
                    <i class="fas fa-bell-slash"></i>
                    <p>No new notifications</p>
                </li>
            `;
        } else {
            let html = '';
            notifications.slice(0, 5).forEach(notification => {
                const iconClass = getIconClass(notification.notification_type);
                const timeAgo = getTimeAgo(new Date(notification.created_at));
                
                html += `
                    <li>
                        <a class="dropdown-item notification-item ${notification.is_read ? 'read' : 'unread'}" 
                           href="/notifications/${notification.id}/mark-read/"
                           data-notification-id="${notification.id}">
                            <div class="d-flex align-items-start">
                                <div class="notification-icon ${iconClass}">
                                    <i class="fas ${getIcon(notification.notification_type)}"></i>
                                </div>
                                <div class="flex-grow-1">
                                    <strong>${escapeHtml(notification.title)}</strong>
                                    <p class="mb-1 text-muted small">${escapeHtml(notification.message)}</p>
                                    <small class="text-muted">${timeAgo}</small>
                                </div>
                            </div>
                        </a>
                    </li>
                `;
            });
            
            notificationList.innerHTML = html;
        }
    } catch (error) {
        console.error('Failed to update dropdown:', error);
    }
}

/**
 * Get icon class based on notification type
 */
function getIconClass(type) {
    const icons = {
        'blood_request': 'icon-blood',
        'donation_reminder': 'icon-reminder',
        'eligibility': 'icon-success',
        'general': 'icon-info'
    };
    return icons[type] || 'icon-info';
}

/**
 * Get icon based on notification type
 */
function getIcon(type) {
    const icons = {
        'blood_request': 'fa-hand-holding-medical',
        'donation_reminder': 'fa-clock',
        'eligibility': 'fa-check-circle',
        'general': 'fa-info-circle'
    };
    return icons[type] || 'fa-bell';
}

/**
 * Format time as "X minutes ago"
 */
function getTimeAgo(date) {
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) return 'Just now';
    
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    
    const days = Math.floor(hours / 24);
    return `${days} day${days > 1 ? 's' : ''} ago`;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

/**
 * Request browser notification permission
 */
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize WebSocket connection
    initializeNotificationSocket();
    
    // Request notification permission
    requestNotificationPermission();
});

// Reconnect on visibility change (user returns to tab)
document.addEventListener('visibilitychange', function() {
    if (!document.hidden && (!notificationSocket || notificationSocket.readyState !== WebSocket.OPEN)) {
        console.log('Page visible, attempting reconnect...');
        initializeNotificationSocket();
    }
});
