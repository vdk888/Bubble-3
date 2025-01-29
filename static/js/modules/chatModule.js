// Chat Module
export class ChatModule {
    constructor() {
        this.chatMessages = null;
        this.messageInput = null;
        this.sendButton = null;
        this.isInitialized = false;
    }

    initialize() {
        this.chatMessages = document.getElementById('chat-messages');
        this.messageInput = document.getElementById('chat-input');
        this.sendButton = document.getElementById('send-button');

        if (this.messageInput && this.sendButton && this.chatMessages) {
            this.setupEventListeners();
            
            // Only initialize once
            if (!this.isInitialized) {
                this.initializeChat();
                this.isInitialized = true;
            }
        } else {
            console.error('Chat elements not found:', {
                messageInput: !!this.messageInput,
                sendButton: !!this.sendButton,
                chatMessages: !!this.chatMessages
            });
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
    }

    async initializeChat() {
        try {
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

        // Add user message to chat
        this.addUserMessage(message);

        try {
            // Send message to backend
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

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
        } catch (error) {
            console.error('Error sending message:', error);
            this.addBotMessage('❌ Sorry, there was an error processing your message. Please try again.');
        }
    }

    addUserMessage(text) {
        if (!this.chatMessages) {
            console.error('Chat messages container not found');
            return;
        }

        const message = document.createElement('div');
        message.className = 'message user-message';
        message.innerHTML = text;
        this.chatMessages.appendChild(message);
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
} 