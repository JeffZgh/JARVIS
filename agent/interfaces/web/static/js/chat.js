// JARVIS Agent Chat Interface JavaScript
class JarvisChat {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.websocket = null;
        this.isConnected = false;
        this.messageHistory = [];
        
        this.initializeElements();
        this.initializeEventListeners();
        this.connectWebSocket();
        this.loadSessionInfo();
    }
    
    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }
    
    initializeElements() {
        this.chatContainer = document.querySelector('.chat-container');
        this.messagesContainer = document.querySelector('.chat-messages');
        this.messageInput = document.querySelector('.message-input');
        this.sendButton = document.querySelector('.send-button');
        this.typingIndicator = document.querySelector('.typing-indicator');
        this.statusDot = document.querySelector('.status-dot');
        this.sessionIdElement = document.querySelector('.session-id');
        this.messageCountElement = document.querySelector('.message-count');
        this.clearHistoryBtn = document.querySelector('.clear-history-btn');
    }
    
    initializeEventListeners() {
        // Send message on button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Send message on Enter (Shift+Enter for new line)
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
        });
        
        // Clear history
        this.clearHistoryBtn.addEventListener('click', () => this.clearHistory());
        
        // Handle page visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.websocket) {
                this.websocket.close();
            } else if (!document.hidden) {
                this.connectWebSocket();
            }
        });
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${this.sessionId}`;
        
        try {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                this.isConnected = true;
                this.updateConnectionStatus(true);
                console.log('WebSocket connected');
            };
            
            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.websocket.onclose = () => {
                this.isConnected = false;
                this.updateConnectionStatus(false);
                console.log('WebSocket disconnected');
                
                // Attempt to reconnect after 3 seconds
                setTimeout(() => {
                    if (!this.isConnected) {
                        this.connectWebSocket();
                    }
                }, 3000);
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.showError('Connection error. Trying to reconnect...');
            };
            
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.showError('Failed to connect to server');
        }
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'message':
                this.hideTypingIndicator();
                this.addMessage(data.response, 'assistant', data.timestamp);
                this.updateMessageCount();
                break;
                
            case 'typing':
                if (data.status === 'started') {
                    this.showTypingIndicator();
                } else {
                    this.hideTypingIndicator();
                }
                break;
                
            case 'error':
                this.hideTypingIndicator();
                this.showError(data.message);
                break;
        }
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || !this.isConnected) return;
        
        // Add user message to UI
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        this.updateMessageCount();
        
        // Disable send button while processing
        this.sendButton.disabled = true;
        
        try {
            if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                // Send via WebSocket
                this.websocket.send(JSON.stringify({
                    message: message,
                    message_type: 'text'
                }));
            } else {
                // Fallback to HTTP API
                await this.sendMessageViaAPI(message);
            }
        } catch (error) {
            console.error('Failed to send message:', error);
            this.showError('Failed to send message. Please try again.');
        } finally {
            this.sendButton.disabled = false;
        }
    }
    
    async sendMessageViaAPI(message) {
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    message_type: 'text',
                    session_id: this.sessionId
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.addMessage(data.response, 'assistant', data.timestamp);
            this.updateMessageCount();
            
        } catch (error) {
            console.error('API error:', error);
            this.showError('Failed to get response from server');
        }
    }
    
    addMessage(content, sender, timestamp = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = sender === 'user' ? 'U' : 'J';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = content;
        
        const messageTimestamp = document.createElement('div');
        messageTimestamp.className = 'message-timestamp';
        const time = timestamp ? new Date(timestamp) : new Date();
        messageTimestamp.textContent = this.formatTime(time);
        
        messageContent.appendChild(messageTimestamp);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        this.messagesContainer.appendChild(messageDiv);
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        
        // Store in history
        this.messageHistory.push({
            content,
            sender,
            timestamp: timestamp || time.toISOString()
        });
    }
    
    showTypingIndicator() {
        this.typingIndicator.classList.add('show');
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
    
    hideTypingIndicator() {
        this.typingIndicator.classList.remove('show');
    }
    
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        
        this.messagesContainer.appendChild(errorDiv);
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        
        // Remove error after 5 seconds
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }
    
    updateConnectionStatus(connected) {
        if (connected) {
            this.statusDot.classList.remove('disconnected');
        } else {
            this.statusDot.classList.add('disconnected');
        }
    }
    
    updateMessageCount() {
        const count = this.messageHistory.filter(m => m.sender === 'user').length;
        this.messageCountElement.textContent = `${count} messages`;
    }
    
    async loadSessionInfo() {
        try {
            const response = await fetch(`/sessions/${this.sessionId}`);
            if (response.ok) {
                const data = await response.json();
                this.sessionIdElement.textContent = this.sessionId;
                this.updateMessageCount();
            }
        } catch (error) {
            console.error('Failed to load session info:', error);
        }
    }
    
    async clearHistory() {
        if (!confirm('Are you sure you want to clear the chat history?')) return;
        
        try {
            const response = await fetch(`/chat/sessions/${this.sessionId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                // Clear UI
                this.messagesContainer.innerHTML = '';
                this.messageHistory = [];
                this.updateMessageCount();
                
                // Add welcome message
                this.addMessage('Chat history cleared. How can I help you today?', 'assistant');
            } else {
                throw new Error('Failed to clear history');
            }
        } catch (error) {
            console.error('Failed to clear history:', error);
            this.showError('Failed to clear chat history');
        }
    }
    
    formatTime(date) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
}

// Initialize chat when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new JarvisChat();
});
