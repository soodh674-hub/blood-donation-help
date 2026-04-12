/**
 * BloodLife - Enhanced Notification Manager
 * Integrates heart notification system with real-time tracking
 */

class NotificationManager {
    constructor() {
        this.queue = [];
        this.activeNotifications = [];
        this.maxVisible = 3;
        this.soundEnabled = true;
        this.volume = 0.5;
        
        // Initialize sound manager
        this.soundManager = new SoundManager();
        
        console.log('🔔 Notification Manager initialized');
    }
    
    /**
     * Add notification to queue
     */
    add(notification) {
        // Priority sorting
        const priority = {
            'critical': 0,
            'high': 1,
            'medium': 2,
            'normal': 3,
            'success': 4
        };
        
        notification.id = notification.id || Date.now() + Math.random();
        notification.priority = priority[notification.urgency] || 3;
        notification.duration = notification.duration || this.getDefaultDuration(notification.urgency);
        
        this.queue.push(notification);
        this.queue.sort((a, b) => a.priority - b.priority);
        
        this.processQueue();
    }
    
    /**
     * Process notification queue
     */
    processQueue() {
        while (this.activeNotifications.length < this.maxVisible && this.queue.length > 0) {
            const notification = this.queue.shift();
            this.showNotification(notification);
        }
    }
    
    /**
     * Show notification toast
     */
    showNotification(notification) {
        const toast = this.createToastElement(notification);
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.classList.add('toast-visible');
            toast.classList.remove('toast-hidden');
        }, 100);
        
        // Play sound
        if (this.soundEnabled && notification.sound) {
            this.soundManager.play(notification.sound);
        }
        
        // Vibrate for critical notifications
        if (notification.urgency === 'critical' && navigator.vibrate) {
            navigator.vibrate(notification.vibration || [200, 100, 200]);
        }
        
        // Track active notification
        const notificationObj = {
            id: notification.id,
            element: toast,
            timeout: setTimeout(() => {
                this.dismissNotification(notification.id);
            }, notification.duration * 1000)
        };
        
        this.activeNotifications.push(notificationObj);
        
        // Add close button handler
        toast.querySelector('.toast-close').addEventListener('click', () => {
            this.dismissNotification(notification.id);
        });
        
        // Add action button handler
        if (notification.action_url) {
            toast.querySelector('.btn-update').addEventListener('click', (e) => {
                e.preventDefault();
                window.location.href = notification.action_url;
            });
        }
    }
    
    /**
     * Create toast HTML element
     */
    createToastElement(notification) {
        const toast = document.createElement('div');
        toast.className = `donation-toast toast-hidden ${this.getUrgencyClass(notification.urgency)}`;
        toast.id = `notification-${notification.id}`;
        
        const icon = this.getIconForType(notification.type);
        const title = notification.title || 'Notification';
        const message = notification.message || '';
        const actionText = notification.action_text || 'View Details';
        
        toast.innerHTML = `
            <!-- Decorative Background Elements -->
            <div class="toast-bg-decoration"></div>
            
            <div class="toast-content-wrapper">
                <div class="toast-content">
                    <div class="toast-icon-wrapper">
                        <span class="icon-heart">${icon}</span>
                    </div>
                    <div class="toast-message">
                        <div class="toast-header">
                            <h4>${title}</h4>
                            <div class="toast-glow-effect"></div>
                        </div>
                        <p>${message}</p>
                        ${notification.data && notification.data.distance_km ? `
                            <div class="eligibility-badge">
                                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                                </svg>
                                <span>${notification.data.distance_km.toFixed(1)} km away</span>
                            </div>
                        ` : ''}
                    </div>
                    <button class="toast-close" title="Dismiss">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                
                ${notification.action_url ? `
                <div class="toast-actions">
                    <a href="${notification.action_url}" class="btn-update">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6"></path>
                        </svg>
                        <span>${actionText}</span>
                    </a>
                    <button class="btn-dismiss">Later</button>
                </div>
                ` : ''}
            </div>
            
            <div class="toast-progress">
                <div class="toast-progress-bar" style="animation-duration: ${notification.duration}s;"></div>
            </div>
        `;
        
        return toast;
    }
    
    /**
     * Dismiss notification
     */
    dismissNotification(id) {
        const index = this.activeNotifications.findIndex(n => n.id === id);
        if (index === -1) return;
        
        const notification = this.activeNotifications[index];
        clearTimeout(notification.timeout);
        
        notification.element.classList.remove('toast-visible');
        notification.element.classList.add('toast-hidden');
        
        setTimeout(() => {
            notification.element.remove();
            this.activeNotifications.splice(index, 1);
            this.processQueue(); // Show next in queue
        }, 500);
    }
    
    /**
     * Get default duration based on urgency
     */
    getDefaultDuration(urgency) {
        const durations = {
            'critical': 10,
            'high': 8,
            'medium': 6,
            'normal': 5,
            'success': 7
        };
        return durations[urgency] || 5;
    }
    
    /**
     * Get urgency CSS class
     */
    getUrgencyClass(urgency) {
        const classes = {
            'critical': 'toast-emergency',
            'high': 'toast-urgent',
            'medium': 'toast-medium',
            'normal': '',
            'success': 'toast-success'
        };
        return classes[urgency] || '';
    }
    
    /**
     * Get icon for notification type
     */
    getIconForType(type) {
        const icons = {
            'donor_response': '❤️',
            'donor_selected': '🎉',
            'donor_en_route': '🚗',
            'emergency_request': '🚨',
            'donation_completed': '💖',
            'request_expiring': '⚠️',
            'default': '🔔'
        };
        return icons[type] || icons.default;
    }
    
    /**
     * Enable/disable sounds
     */
    setSoundEnabled(enabled) {
        this.soundEnabled = enabled;
    }
    
    /**
     * Set volume (0-1)
     */
    setVolume(volume) {
        this.volume = Math.max(0, Math.min(1, volume));
        this.soundManager.setVolume(this.volume);
    }
    
    /**
     * Clear all notifications
     */
    clearAll() {
        this.activeNotifications.forEach(notification => {
            clearTimeout(notification.timeout);
            notification.element.remove();
        });
        this.activeNotifications = [];
        this.queue = [];
    }
}


/**
 * Sound Manager for notification audio
 */
class SoundManager {
    constructor() {
        this.sounds = {};
        this.volume = 0.5;
        
        // Preload sounds (will be created when needed)
        this.preloadSounds();
    }
    
    /**
     * Preload sound files (only if they exist)
     */
    preloadSounds() {
        const soundFiles = {
            'soft-chime': '/static/sounds/soft-chime.mp3',
            'celebration': '/static/sounds/celebration.mp3',
            'notification': '/static/sounds/notification.mp3',
            'emergency-alarm': '/static/sounds/emergency-alarm.mp3',
            'success-chime': '/static/sounds/success-chime.mp3'
        };
        
        // Only try to load sounds - will fail silently if files don't exist
        Object.entries(soundFiles).forEach(([name, url]) => {
            const audio = new Audio();
            audio.volume = this.volume;
            audio.preload = 'none'; // Don't preload to avoid 404 errors
            
            // Try to load, but catch errors silently
            audio.addEventListener('canplaythrough', () => {
                this.sounds[name] = audio;
                console.log(`✅ Sound loaded: ${name}`);
            });
            
            audio.addEventListener('error', () => {
                console.log(`ℹ️ Sound not available: ${name} (using silent mode)`);
            });
            
            audio.src = url;
        });
    }
    
    /**
     * Play sound by name
     */
    play(soundName) {
        const sound = this.sounds[soundName];
        if (sound) {
            sound.currentTime = 0;
            sound.play().catch(err => {
                console.warn('Sound play failed:', err);
            });
        }
    }
    
    /**
     * Set volume for all sounds
     */
    setVolume(volume) {
        this.volume = volume;
        Object.values(this.sounds).forEach(sound => {
            sound.volume = volume;
        });
    }
}


// Export global instance
window.notificationManager = new NotificationManager();

console.log('✅ BloodLife Notification System loaded');
