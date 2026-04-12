/**
 * BloodLife - Push Notification Setup
 * Registers service worker and handles push permissions
 */

class PushNotificationSetup {
    constructor() {
        this.isSupported = 'serviceWorker' in navigator && 'PushManager' in window;
        this.subscription = null;
    }
    
    /**
     * Initialize push notifications
     */
    async initialize() {
        if (!this.isSupported) {
            console.warn('⚠️ Push notifications not supported');
            return false;
        }
        
        try {
            // Register service worker
            const registration = await navigator.serviceWorker.register('/static/js/sw-push.js');
            console.log('✅ Service Worker registered');
            
            // Request permission
            const permission = await Notification.requestPermission();
            
            if (permission === 'granted') {
                console.log('✅ Notification permission granted');
                
                // Subscribe to push
                await this.subscribeToPush(registration);
                
                return true;
            } else {
                console.warn('⚠️ Notification permission denied');
                return false;
            }
            
        } catch (error) {
            console.error('❌ Push setup failed:', error);
            return false;
        }
    }
    
    /**
     * Subscribe to push notifications
     */
    async subscribeToPush(registration) {
        try {
            // VAPID public key (you'll need to generate this on your server)
            const vapidPublicKey = 'YOUR_VAPID_PUBLIC_KEY_HERE';
            
            this.subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(vapidPublicKey)
            });
            
            console.log('✅ Subscribed to push notifications');
            
            // Send subscription to server
            await this.sendSubscriptionToServer(this.subscription);
            
        } catch (error) {
            console.error('Failed to subscribe:', error);
        }
    }
    
    /**
     * Send subscription to backend
     */
    async sendSubscriptionToServer(subscription) {
        try {
            const response = await fetch('/api/notifications/subscribe/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    subscription: subscription
                })
            });
            
            if (response.ok) {
                console.log('✅ Subscription saved to server');
            }
            
        } catch (error) {
            console.error('Failed to save subscription:', error);
        }
    }
    
    /**
     * Convert VAPID key
     */
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');
        
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        
        return outputArray;
    }
    
    /**
     * Get CSRF token
     */
    getCSRFToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue || '';
    }
    
    /**
     * Unsubscribe from push
     */
    async unsubscribe() {
        if (this.subscription) {
            await this.subscription.unsubscribe();
            console.log('✅ Unsubscribed from push notifications');
        }
    }
}

// Create global instance
window.pushNotificationSetup = new PushNotificationSetup();

// Auto-initialize when page loads (optional - can be triggered by button instead)
// document.addEventListener('DOMContentLoaded', () => {
//     window.pushNotificationSetup.initialize();
// });

console.log('🔔 Push Notification Setup ready');
