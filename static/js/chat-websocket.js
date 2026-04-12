/**
 * Real-time chat WebSocket
 */

// Get Django context variables from window object (set in template)
const DJANGO_CONTEXT = {
    receiverId: window.chatReceiverId || null,
    userId: window.chatUserId || null
};

const requestId = window.location.pathname.split('/')[2];
let chatWs = null;

function connectChat() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat/${requestId}/`;
    
    chatWs = new WebSocket(wsUrl);
    
    chatWs.onopen = function() {
        console.log('✅ Chat connected');
        loadChatHistory();
    };
    
    chatWs.onmessage = function(event) {
        const data = JSON.parse(event.data);
        displayMessage(data);
    };
    
    chatWs.onerror = function(error) {
        console.error('Chat error:', error);
    };
    
    chatWs.onclose = function() {
        console.log('Chat disconnected');
        setTimeout(connectChat, 3000);
    };
}

function displayMessage(data) {
    const container = document.getElementById('chat-messages');
    const isMine = data.is_mine;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `flex ${isMine ? 'justify-end' : 'justify-start'}`;
    
    messageDiv.innerHTML = `
        <div class="max-w-[70%] ${isMine ? 'bg-red-500' : 'bg-gray-700'} rounded-lg px-4 py-2">
            ${!isMine ? `<p class="text-xs text-gray-300 mb-1">${data.sender_name}</p>` : ''}
            <p class="text-white">${data.message}</p>
            <p class="text-xs text-gray-300 mt-1">${new Date().toLocaleTimeString()}</p>
        </div>
    `;
    
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

function sendMessage(message) {
    if (chatWs && chatWs.readyState === WebSocket.OPEN) {
        chatWs.send(JSON.stringify({
            message: message,
            receiver_id: DJANGO_CONTEXT.receiverId
        }));
    }
}

function loadChatHistory() {
    fetch(`/api/requests/${requestId}/chat/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const container = document.getElementById('chat-messages');
                container.innerHTML = '';
                data.messages.forEach(msg => {
                    displayMessage({
                        message: msg.message,
                        sender_name: msg.sender_name,
                        is_mine: msg.sender === DJANGO_CONTEXT.userId
                    });
                });
            }
        });
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    connectChat();
    
    const form = document.getElementById('chat-form');
    const input = document.getElementById('message-input');
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const message = input.value.trim();
        if (message) {
            sendMessage(message);
            input.value = '';
        }
    });
});
