/**
 * Floating Notification Bar
 * Shows blood requests, news, and updates at bottom of screen
 * Auto-dismisses after 5 seconds with smooth animations
 */

class FloatingNotificationBar {
    constructor() {
        this.bar = null;
        this.notifications = [];
        this.currentNotification = null;
        this.autoDismissTimer = null;
        this.pollInterval = null;
        this.init();
    }

    init() {
        // Only show for authenticated users
        const authData = document.getElementById('user-auth-data');
        if (!authData || authData.dataset.authenticated !== 'true') {
            return;
        }

        this.createBar();
        this.startPolling();
        console.log('✅ Floating notification bar initialized');
    }

    createBar() {
        // Create floating bar
        this.bar = document.createElement('div');
        this.bar.id = 'floating-notification-bar';
        this.bar.className = 'floating-notification-bar';
        this.bar.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">
                    <span class="pulse-heart">🩸</span>
                </div>
                <div class="notification-text">
                    <h4 class="notification-title">No new notifications</h4>
                    <p class="notification-message">You're all caught up!</p>
                </div>
                <div class="notification-actions">
                    <button class="btn-view" onclick="window.location.href='/requests/'">
                        View All
                    </button>
                    <button class="btn-dismiss" onclick="floatingBar.dismiss()">
                        ✕
                    </button>
                </div>
            </div>
            <div class="notification-progress"></div>
        `;

        // Add styles
        this.addStyles();

        // Add to page
        document.body.appendChild(this.bar);

        // Initially hidden
        this.bar.classList.add('hidden');
    }

    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            /* Floating Notification Bar */
            .floating-notification-bar {
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%) translateY(150%);
                background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
                border: 1px solid rgba(255, 59, 59, 0.3);
                border-radius: 16px;
                padding: 16px 20px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4), 0 0 20px rgba(255, 59, 59, 0.2);
                z-index: 9999;
                max-width: 600px;
                width: calc(100% - 40px);
                transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
                backdrop-filter: blur(10px);
            }

            .floating-notification-bar.visible {
                transform: translateX(-50%) translateY(0);
            }

            .floating-notification-bar.hidden {
                transform: translateX(-50%) translateY(150%);
            }

            .notification-content {
                display: flex;
                align-items: center;
                gap: 16px;
            }

            .notification-icon {
                flex-shrink: 0;
            }

            .pulse-heart {
                font-size: 32px;
                display: inline-block;
                animation: pulse 2s ease-in-out infinite;
            }

            @keyframes pulse {
                0%, 100% {
                    transform: scale(1);
                }
                50% {
                    transform: scale(1.2);
                }
            }

            .notification-text {
                flex: 1;
                min-width: 0;
            }

            .notification-title {
                color: #ffffff;
                font-size: 16px;
                font-weight: 600;
                margin: 0 0 4px 0;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .notification-message {
                color: rgba(255, 255, 255, 0.7);
                font-size: 14px;
                margin: 0;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .notification-actions {
                display: flex;
                gap: 8px;
                flex-shrink: 0;
            }

            .btn-view {
                background: linear-gradient(135deg, #ef4444, #dc2626);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                white-space: nowrap;
            }

            .btn-view:hover {
                background: linear-gradient(135deg, #dc2626, #b91c1c);
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
            }

            .btn-dismiss {
                background: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.2);
                width: 32px;
                height: 32px;
                border-radius: 8px;
                font-size: 16px;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .btn-dismiss:hover {
                background: rgba(255, 255, 255, 0.2);
                color: white;
            }

            .notification-progress {
                position: absolute;
                bottom: 0;
                left: 0;
                height: 3px;
                background: linear-gradient(90deg, #ef4444, #dc2626);
                border-radius: 0 0 16px 16px;
                width: 100%;
                transform-origin: left;
                animation: progress 5s linear forwards;
            }

            @keyframes progress {
                from {
                    transform: scaleX(1);
                }
                to {
                    transform: scaleX(0);
                }
            }

            /* Mobile Responsive */
            @media (max-width: 768px) {
                .floating-notification-bar {
                    bottom: 10px;
                    left: 10px;
                    right: 10px;
                    transform: translateX(0) translateY(150%);
                    width: auto;
                    max-width: none;
                    padding: 12px 16px;
                }

                .floating-notification-bar.visible {
                    transform: translateX(0) translateY(0);
                }

                .floating-notification-bar.hidden {
                    transform: translateX(0) translateY(150%);
                }

                .notification-content {
                    flex-wrap: wrap;
                    gap: 12px;
                }

                .notification-icon {
                    display: none;
                }

                .notification-text {
                    flex: 1 1 100%;
                    order: 1;
                }

                .notification-actions {
                    flex: 1 1 100%;
                    order: 2;
                    justify-content: space-between;
                }

                .btn-view {
                    flex: 1;
                }

                .btn-dismiss {
                    flex-shrink: 0;
                }

                .notification-title {
                    font-size: 14px;
                }

                .notification-message {
                    font-size: 13px;
                }
            }

            @media (max-width: 480px) {
                .floating-notification-bar {
                    bottom: 5px;
                    left: 5px;
                    right: 5px;
                    padding: 10px 12px;
                    border-radius: 12px;
                }

                .notification-title {
                    font-size: 13px;
                }

                .notification-message {
                    font-size: 12px;
                }

                .btn-view {
                    padding: 6px 12px;
                    font-size: 13px;
                }
            }
        `;
        document.head.appendChild(style);
    }

    async startPolling() {
        // Initial fetch
        await this.fetchNotifications();

        // Poll every 30 seconds
        this.pollInterval = setInterval(async () => {
            await this.fetchNotifications();
        }, 30000);
    }

    async fetchNotifications() {
        try {
            const response = await fetch('/notifications/api/list/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                }
            });

            if (!response.ok) {
                console.warn('⚠️ Failed to fetch notifications');
                return;
            }

            const data = await response.json();
            
            // Filter unread blood request notifications
            const unreadRequests = data.notifications?.filter(n => 
                !n.is_read && n.notification_type === 'blood_request'
            ) || [];

            if (unreadRequests.length > 0) {
                // Show most recent notification
                this.showNotification(unreadRequests[0]);
            }
        } catch (error) {
            console.error('❌ Error fetching notifications:', error);
        }
    }

    showNotification(notification) {
        if (!this.bar) return;

        // Clear existing timer
        if (this.autoDismissTimer) {
            clearTimeout(this.autoDismissTimer);
        }

        // Update content
        const title = this.bar.querySelector('.notification-title');
        const message = this.bar.querySelector('.notification-message');
        const progress = this.bar.querySelector('.notification-progress');

        title.textContent = notification.title || '🩸 Blood Request';
        message.textContent = notification.message || 'New blood request needs your help!';

        // Store current notification
        this.currentNotification = notification;

        // Show bar
        this.bar.classList.remove('hidden');
        this.bar.classList.add('visible');

        // Reset progress animation
        progress.style.animation = 'none';
        setTimeout(() => {
            progress.style.animation = 'progress 5s linear forwards';
        }, 10);

        // Auto-dismiss after 5 seconds
        this.autoDismissTimer = setTimeout(() => {
            this.dismiss();
        }, 5000);
    }

    dismiss() {
        if (!this.bar) return;

        // Clear timer
        if (this.autoDismissTimer) {
            clearTimeout(this.autoDismissTimer);
            this.autoDismissTimer = null;
        }

        // Hide bar
        this.bar.classList.remove('visible');
        this.bar.classList.add('hidden');

        // Mark notification as read
        if (this.currentNotification && this.currentNotification.id) {
            this.markAsRead(this.currentNotification.id);
        }

        this.currentNotification = null;
    }

    async markAsRead(notificationId) {
        try {
            await fetch(`/notifications/api/${notificationId}/read/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                }
            });
        } catch (error) {
            console.error('❌ Error marking notification as read:', error);
        }
    }

    getCookie(name) {
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
}

// Initialize on page load
let floatingBar;
document.addEventListener('DOMContentLoaded', () => {
    floatingBar = new FloatingNotificationBar();
});
