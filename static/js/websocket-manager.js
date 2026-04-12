/**
 * BloodLife - WebSocket Connection Manager
 * For real-time updates (future enhancement)
 * Currently uses polling, but ready for WebSocket upgrade
 */

class WebSocketManager {
    constructor() {
        this.ws = null;
        this.reconnectInterval = 3000;
        this.maxReconnectAttempts = 5;
        this.reconnectAttempts = 0;
        this.isConnected = false;
        this.messageHandlers = {};
    }
    
    /**
     * Connect to WebSocket server
     */
    connect(userId) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.log('WebSocket already connected');
            return;
        }
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/notifications/${userId}/`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('✅ WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                
                // Send authentication
                this.send({
                    type: 'authenticate',
                    user_id: userId
                });
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            };
            
            this.ws.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
            };
            
            this.ws.onclose = () => {
                console.log('⚠️ WebSocket disconnected');
                this.isConnected = false;
                this.attemptReconnect(userId);
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.attemptReconnect(userId);
        }
    }
    
    /**
     * Handle incoming messages
     */
    handleMessage(data) {
        console.log('📨 Received:', data);
        
        // Trigger registered handlers
        if (this.messageHandlers[data.type]) {
            this.messageHandlers[data.type].forEach(handler => handler(data));
        }
        
        // Show notification if notification manager exists
        if (window.notificationManager && data.notification) {
            window.notificationManager.add(data.notification);
        }
    }
    
    /**
     * Register message handler
     */
    on(messageType, handler) {
        if (!this.messageHandlers[messageType]) {
            this.messageHandlers[messageType] = [];
        }
        this.messageHandlers[messageType].push(handler);
    }
    
    /**
     * Send message to server
     */
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket not connected');
        }
    }
    
    /**
     * Attempt reconnection
     */
    attemptReconnect(userId) {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            return;
        }
        
        this.reconnectAttempts++;
        console.log(`🔄 Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        setTimeout(() => {
            this.connect(userId);
        }, this.reconnectInterval * this.reconnectAttempts);
    }
    
    /**
     * Disconnect
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

// Create global instance (but don't auto-connect yet)
window.webSocketManager = new WebSocketManager();

console.log('🔌 WebSocket Manager ready (polling mode active)');
