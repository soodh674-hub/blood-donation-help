/**
 * WebSocket integration for real-time blood requests
 * Falls back to HTTP polling if WebSocket is not available
 */

let ws = null;
let reconnectAttempts = 0;
let pollingInterval = null;
const MAX_RECONNECT_ATTEMPTS = 5;
const POLLING_INTERVAL = 30000; // 30 seconds

function connectWebSocket() {
    // Check if WebSocket is supported
    if (!('WebSocket' in window)) {
        console.warn('WebSocket not supported, using HTTP polling');
        startHttpPolling();
        return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/requests/live/`;
    
    console.log('Connecting to WebSocket:', wsUrl);
    
    try {
        ws = new WebSocket(wsUrl);
        
        ws.onopen = function() {
            console.log('✅ WebSocket connected');
            reconnectAttempts = 0;
            showNotification('Connected to live updates', 'success');
            // Stop polling if WebSocket is successful
            if (pollingInterval) {
                clearInterval(pollingInterval);
                pollingInterval = null;
            }
        };
        
        ws.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                handleLiveRequestUpdate(data);
            } catch (e) {
                console.error('Error parsing WebSocket message:', e);
            }
        };
        
        ws.onerror = function(error) {
            console.error('❌ WebSocket error:', error);
            // Fall back to HTTP polling on error
            console.log('Falling back to HTTP polling...');
            startHttpPolling();
        };
        
        ws.onclose = function() {
            console.log('WebSocket disconnected');
            if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                reconnectAttempts++;
                const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
                console.log(`Reconnecting in ${delay}ms... (attempt ${reconnectAttempts})`);
                setTimeout(connectWebSocket, delay);
            } else {
                console.log('Max reconnection attempts reached, using HTTP polling');
                startHttpPolling();
            }
        };
    } catch (error) {
        console.error('Failed to create WebSocket:', error);
        console.log('Using HTTP polling instead');
        startHttpPolling();
    }
}

function startHttpPolling() {
    if (pollingInterval) return; // Already polling
    
    console.log('Starting HTTP polling for live requests');
    pollingInterval = setInterval(() => {
        fetchLiveRequests();
    }, POLLING_INTERVAL);
    
    // Initial fetch
    fetchLiveRequests();
}

function fetchLiveRequests() {
    fetch('/api/requests/live/')
        .then(response => response.json())
        .then(data => {
            if (data.requests) {
                handleLiveRequestUpdate({ requests: data.requests });
            }
        })
        .catch(error => {
            console.error('HTTP polling error:', error);
        });
}

function handleNewRequest(requestData) {
    // Play notification sound for emergency
    if (requestData.priority === 'emergency') {
        playAlertSound();
    }
    
    // Show browser notification
    if (Notification.permission === 'granted') {
        new Notification('🩸 New Blood Request', {
            body: `${requestData.patient_blood_group} needed at ${requestData.hospital_name}`,
            icon: '/static/favicon.ico'
        });
    }
    
    // Add to grid
    addRequestCard(requestData);
}

function addRequestCard(request) {
    const grid = document.getElementById('live-requests-grid');
    
    // Remove loading message if present
    const loadingMsg = grid.querySelector('.col-span-full');
    if (loadingMsg) {
        loadingMsg.remove();
    }
    
    const urgencyColors = {
        'emergency': 'border-red-500 bg-red-500/10',
        'urgent': 'border-orange-500 bg-orange-500/10',
        'normal': 'border-blue-500 bg-blue-500/10'
    };
    
    const card = document.createElement('div');
    card.className = `bg-gray-800 rounded-xl p-6 border-l-4 ${urgencyColors[request.priority] || urgencyColors.normal} hover:transform hover:scale-105 transition-all duration-300`;
    card.innerHTML = `
        <div class="flex justify-between items-start mb-4">
            <span class="px-3 py-1 rounded-full text-xs font-bold uppercase ${getUrgencyBadgeClass(request.priority)}">
                ${request.priority}
            </span>
            <span class="text-gray-400 text-sm">${formatTimeAgo(request.created_at)}</span>
        </div>
        
        <h3 class="text-2xl font-bold text-white mb-2">
            ${request.patient_blood_group} Blood Needed
        </h3>
        
        <p class="text-gray-300 mb-4">${request.hospital_name}, ${request.city}</p>
        
        <div class="flex items-center gap-4 text-sm text-gray-400 mb-4">
            <div class="flex items-center gap-1">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                </svg>
                <span>${request.distance_km || '?'} km away</span>
            </div>
            <div class="flex items-center gap-1">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <span>${request.required_units} unit(s)</span>
            </div>
        </div>
        
        <div class="flex gap-3">
            <button onclick="respondToRequest(${request.id})" 
                    class="flex-1 bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg font-semibold transition-colors">
                I Can Donate
            </button>
            <button onclick="trackRequest(${request.id})" 
                    class="flex-1 bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg font-semibold transition-colors">
                Track
            </button>
        </div>
    `;
    
    // Insert at beginning
    grid.insertBefore(card, grid.firstChild);
    
    // Keep only last 20 requests
    while (grid.children.length > 20) {
        grid.removeChild(grid.lastChild);
    }
}

function getUrgencyBadgeClass(priority) {
    const classes = {
        'emergency': 'bg-red-500 text-white',
        'urgent': 'bg-orange-500 text-white',
        'normal': 'bg-blue-500 text-white'
    };
    return classes[priority] || classes.normal;
}

function formatTimeAgo(timestamp) {
    const now = new Date();
    const date = new Date(timestamp);
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
}

function respondToRequest(requestId) {
    fetch(`/api/requests/${requestId}/respond/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('✅ You responded to this request!', 'success');
            window.location.href = `/requests/${requestId}/track/`;
        } else {
            showNotification(data.error || 'Failed to respond', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Network error', 'error');
    });
}

function trackRequest(requestId) {
    window.location.href = `/requests/${requestId}/track/`;
}

function playAlertSound() {
    const audio = new Audio('/static/sounds/alert.mp3');
    audio.play().catch(e => console.log('Audio play failed:', e));
}

function showNotification(message, type = 'info') {
    // Create toast notification
    const toast = document.createElement('div');
    const colors = {
        'success': 'bg-green-500',
        'error': 'bg-red-500',
        'info': 'bg-blue-500'
    };
    
    toast.className = `fixed top-4 right-4 ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-slide-in`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
    
    // Connect WebSocket
    connectWebSocket();
});
