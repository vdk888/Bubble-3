// Chat Module
export class ChatModule {
    constructor() {
        this.chatMessages = null;
        this.messageInput = null;
        this.sendButton = null;
        this.isInitialized = false;
        this.sensitiveInputMode = false;
        this.typingIndicator = null;
    }

    initialize() {
        this.chatMessages = document.getElementById('chat-messages');
        this.messageInput = document.getElementById('chat-input');
        this.sendButton = document.getElementById('send-button');
        this.typingIndicator = document.querySelector('.typing-indicator');

        if (this.messageInput && this.sendButton && this.chatMessages) {
            this.setupEventListeners();
            
            // Store initial message if it exists
            const initialMessage = this.chatMessages.querySelector('.bot-message');
            const initialMessageHtml = initialMessage ? initialMessage.outerHTML : '';
            
            // Clear chat messages
            this.chatMessages.innerHTML = '';
            
            // Restore initial message if it existed
            if (initialMessageHtml) {
                this.chatMessages.innerHTML = initialMessageHtml;
            }
            
            // Add typing indicator at the end
            this.typingIndicator = document.createElement('div');
            this.typingIndicator.className = 'typing-indicator';
            this.typingIndicator.innerHTML = '<span></span><span></span><span></span>';
            this.typingIndicator.style.display = 'none';
            this.chatMessages.appendChild(this.typingIndicator);
            
            // Only initialize once
            if (!this.isInitialized) {
                this.initializeChat();
                this.isInitialized = true;
            }
        } else {
            console.error('Chat elements not found');
        }
    }

    setupEventListeners() {
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey && this.messageInput.value.trim()) {
                e.preventDefault();
                this.sendMessage(this.messageInput.value.trim());
                this.messageInput.value = '';
            }
        });

        this.sendButton.addEventListener('click', () => {
            if (this.messageInput.value.trim()) {
                this.sendMessage(this.messageInput.value.trim());
                this.messageInput.value = '';
            }
        });

        // Add input event listener to detect potential API keys
        this.messageInput.addEventListener('input', (e) => {
            const value = e.target.value;
            if (this._containsApiKey(value)) {
                this.sensitiveInputMode = true;
                this.messageInput.type = 'password';
            } else {
                this.sensitiveInputMode = false;
                this.messageInput.type = 'text';
            }
        });
    }

    _containsApiKey(text) {
        // Check for potential Alpaca API key patterns
        return /PK[A-Z0-9]{16,}|[A-Za-z0-9]{32,}/.test(text);
    }

    async initializeChat() {
        try {
            // Check if there are already messages
            if (this.chatMessages.children.length > 0) {
                return; // Skip initialization if messages exist
            }

            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: "__init__" })
            });
            
            const data = await response.json();
            if (data.response) {
                this.addBotMessage(data.response);
            }
        } catch (error) {
            console.error('Error initializing chat:', error);
            this.addBotMessage('❌ Sorry, there was an error initializing the chat. Please refresh the page.');
        }
    }

    async sendMessage(message) {
        if (!this.chatMessages) {
            console.error('Chat messages container not found');
            return;
        }

        // Add user message to chat with masked content if it contains API keys
        const displayMessage = this.sensitiveInputMode ? '******* [API Key] *******' : message;
        this.addUserMessage(displayMessage);

        // Show typing indicator before making the request
        this.showTypingIndicator();

        try {
            // Send message to backend
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            // Hide typing indicator before processing response
            this.hideTypingIndicator();

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.error) {
                this.addBotMessage(`❌ Error: ${data.error}`);
                return;
            }

            if (data.response) {
                this.addBotMessage(data.response);
            }

            // Reset sensitive input mode after sending
            if (this.sensitiveInputMode) {
                this.sensitiveInputMode = false;
                this.messageInput.type = 'text';
            }
        } catch (error) {
            // Make sure to hide typing indicator on error
            this.hideTypingIndicator();
            console.error('Error sending message:', error);
            this.addBotMessage('❌ Sorry, there was an error processing your message. Please try again.');
        }
    }

    addUserMessage(text) {
        if (!this.chatMessages) {
            console.error('Chat messages container not found');
            return;
        }

        // Remove typing indicator if it exists
        if (this.typingIndicator) {
            this.typingIndicator.remove();
        }

        const message = document.createElement('div');
        message.className = 'message user-message';
        message.innerHTML = text;
        this.chatMessages.appendChild(message);

        // Add typing indicator back after the message
        if (this.typingIndicator) {
            this.chatMessages.appendChild(this.typingIndicator);
        }

        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    addBotMessage(text) {
        if (!this.chatMessages) {
            console.error('Chat messages container not found');
            return;
        }

        const message = document.createElement('div');
        message.className = 'message bot-message';
        text = text.replace(/•/g, '•').replace(/\n/g, '<br>');
        message.innerHTML = text;
        this.chatMessages.appendChild(message);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    showTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'block';
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
    }

    hideTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'none';
        }
    }
} 