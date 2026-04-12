/**
 * Real-time Chat System using WebSockets
 * Handles chat connections, message sending/receiving, typing indicators
 */

class RealtimeChat {
    constructor(requestId, userId) {
        this.requestId = requestId;
        this.userId = userId;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        this.typingTimeout = null;
        this.isConnected = false;
        
        // DOM elements
        this.chatMessages = document.getElementById('chat-messages');
        this.messageInput = document.getElementById('chat-message-input');
        this.sendButton = document.getElementById('chat-send-btn');
        this.typingIndicator = document.getElementById('typing-indicator');
        this.connectionStatus = document.getElementById('chat-status');
        
        this.init();
    }
    
    init() {
        this.connect();
        this.setupEventListeners();
    }
    
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/chat/${this.requestId}/`;
        
        console.log('Connecting to WebSocket:', wsUrl);
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('✅ WebSocket connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.updateConnectionStatus('connected');
            this.loadChatHistory();
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };
        
        this.ws.onclose = () => {
            console.log('❌ WebSocket disconnected');
            this.isConnected = false;
            this.updateConnectionStatus('disconnected');
            this.attemptReconnect();
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateConnectionStatus('error');
        };
    }
    
    setupEventListeners() {
        // Send button click
        if (this.sendButton) {
            this.sendButton.addEventListener('click', () => this.sendMessage());
        }
        
        // Enter key to send
        if (this.messageInput) {
            this.messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
            
            // Typing indicator
            this.messageInput.addEventListener('input', () => {
                this.handleTyping();
            });
        }
    }
    
    sendMessage() {
        const message = this.messageInput.value.trim();
        
        if (!message || !this.isConnected) return;
        
        // Get receiver ID from page context
        const receiverId = this.getReceiverId();
        
        // Send via WebSocket
        this.ws.send(JSON.stringify({
            type: 'chat_message',
            message: message,
            receiver_id: receiverId
        }));
        
        // Clear input
        this.messageInput.value = '';
        
        // Scroll to bottom
        this.scrollToBottom();
    }
    
    handleMessage(data) {
        console.log('Received message:', data);
        
        switch(data.type) {
            case 'chat':
                this.displayMessage(data);
                this.playNotificationSound();
                break;
            
            case 'typing':
                this.showTypingIndicator(data.sender_id !== this.userId);
                break;
            
            case 'read_receipt':
                this.markAsRead(data.message_ids);
                break;
            
            case 'user_status':
                this.updateUserStatus(data.user_id, data.status);
                break;
        }
    }
    
    displayMessage(data) {
        const isMine = data.sender_id === this.userId;
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isMine ? 'message-mine' : 'message-theirs'}`;
        
        const time = new Date().toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        messageDiv.innerHTML = `
            <div class="message-bubble">
                <div class="message-sender">${data.sender_name}</div>
                <div class="message-text">${this.escapeHtml(data.message)}</div>
                <div class="message-time">${time}</div>
            </div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        
        // Mark as read if not mine
        if (!isMine) {
            this.markMessageAsRead(data.message_id);
        }
    }
    
    handleTyping() {
        // Clear previous timeout
        if (this.typingTimeout) {
            clearTimeout(this.typingTimeout);
        }
        
        // Send typing indicator
        if (this.isConnected && this.messageInput.value.length > 0) {
            this.ws.send(JSON.stringify({
                type: 'typing',
                is_typing: true
            }));
        }
        
        // Stop typing after 2 seconds
        this.typingTimeout = setTimeout(() => {
            if (this.isConnected) {
                this.ws.send(JSON.stringify({
                    type: 'typing',
                    is_typing: false
                }));
            }
        }, 2000);
    }
    
    showTypingIndicator(show) {
        if (this.typingIndicator) {
            this.typingIndicator.style.display = show ? 'block' : 'none';
        }
    }
    
    async loadChatHistory() {
        try {
            const response = await fetch(`/api/requests/${this.requestId}/chat/history/`);
            const data = await response.json();
            
            if (data.success && data.messages) {
                this.chatMessages.innerHTML = '';
                data.messages.forEach(msg => {
                    this.displayMessage({
                        type: 'chat',
                        sender_id: msg.sender_id,
                        sender_name: msg.sender_name,
                        message: msg.message,
                        message_id: msg.id,
                        timestamp: msg.created_at
                    });
                });
                this.scrollToBottom();
            }
        } catch (error) {
            console.error('Error loading chat history:', error);
        }
    }
    
    markMessageAsRead(messageId) {
        // Send read receipt
        if (this.isConnected) {
            this.ws.send(JSON.stringify({
                type: 'read_receipt',
                message_ids: [messageId]
            }));
        }
    }
    
    markAsRead(messageIds) {
        // Update UI to show messages as read
        messageIds.forEach(id => {
            const messageEl = document.querySelector(`[data-message-id="${id}"]`);
            if (messageEl) {
                messageEl.classList.add('read');
            }
        });
    }
    
    updateUserStatus(userId, status) {
        // Update online/offline indicator
        const userIndicator = document.querySelector(`[data-user-id="${userId}"]`);
        if (userIndicator) {
            userIndicator.className = `status-indicator status-${status}`;
        }
    }
    
    updateConnectionStatus(status) {
        if (this.connectionStatus) {
            const statusText = {
                'connected': '🟢 Online',
                'disconnected': '⚪ Offline',
                'connecting': '🟡 Connecting...',
                'error': '🔴 Connection Error'
            };
            
            this.connectionStatus.textContent = statusText[status] || status;
            this.connectionStatus.className = `chat-status status-${status}`;
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            this.updateConnectionStatus('error');
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
        
        setTimeout(() => {
            this.connect();
        }, delay);
    }
    
    scrollToBottom() {
        if (this.chatMessages) {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
    }
    
    playNotificationSound() {
        // Only play sound if tab is not active
        if (document.hidden) {
            const audio = new Audio();
            audio.volume = 0.5;
            audio.preload = 'none';
            audio.src = '/static/sounds/notification.mp3';
            
            // Try to play, but handle missing file gracefully
            audio.addEventListener('canplaythrough', () => {
                audio.play().catch(e => console.log('Audio play failed:', e));
            }, { once: true });
            
            audio.addEventListener('error', () => {
                console.log('ℹ️ Notification sound not available (silent mode)');
            }, { once: true });
        }
    }
    
    getReceiverId() {
        // Get from data attribute or URL context
        return document.querySelector('[data-receiver-id]')?.dataset.receiverId || null;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Initialize chat when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const chatContainer = document.getElementById('chat-container');
    if (chatContainer) {
        const requestId = chatContainer.dataset.requestId;
        const userId = chatContainer.dataset.userId;
        
        if (requestId && userId) {
            window.chat = new RealtimeChat(requestId, userId);
        }
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.chat) {
        window.chat.disconnect();
    }
});
