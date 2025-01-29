// Chat Module
export class ChatModule {
    constructor() {
        this.chatMessages = null;
        this.messageInput = null;
        this.sendButton = null;
    }

    initialize() {
        this.chatMessages = document.getElementById('chat-messages');
        this.messageInput = document.getElementById('chat-input');
        this.sendButton = document.getElementById('send-button');

        if (this.messageInput && this.sendButton && this.chatMessages) {
            this.setupEventListeners();
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
                this.processMessage(this.messageInput.value.trim());
                this.messageInput.value = '';
            }
        });

        this.sendButton.addEventListener('click', () => {
            if (this.messageInput.value.trim()) {
                this.processMessage(this.messageInput.value.trim());
                this.messageInput.value = '';
            }
        });
    }

    async showInitialGreeting() {
        try {
            const response = await fetch('/api/portfolio/metrics');
            const data = await response.json();
            
            if (data.error && data.error.includes('credentials not set')) {
                this.addBotMessage(this.getCredentialsRequestMessage());
            } else {
                this.addBotMessage(this.getWelcomeMessage());
            }
        } catch (error) {
            console.error('Error checking credentials:', error);
            this.addBotMessage('❌ Sorry, there was an error checking your credentials status. Please try refreshing the page.');
        }
    }

    getCredentialsRequestMessage() {
        return `👋 Hello! I'm your AI financial assistant. I notice you haven't set up your Alpaca trading account credentials yet.

To get started, please paste both your Alpaca API Key and Secret Key together, separated by a comma:

ALPACA_API_KEY,ALPACA_SECRET_KEY

For example:
PK1234567890ABCDEFGHIJ1234567890AB,SK1234567890ABCDEFGHIJ1234567890ABCDEFGHIJ1234567890ABCDEFGHIJ

This will allow me to help you with:
• Real-time portfolio tracking
• Trade monitoring
• Market analysis
• Stock information`;
    }

    getWelcomeMessage() {
        return `👋 Hello! I'm your AI financial assistant. I can help you with:
• Checking your portfolio value and positions
• Viewing your recent trades
• Analyzing market trends
• Getting stock information

What would you like to know about?`;
    }

    maskSensitiveData(text) {
        text = text.replace(/ALPACA_API_KEY='[^']+'/g, "ALPACA_API_KEY='********'");
        text = text.replace(/ALPACA_SECRET_KEY='[^']+'/g, "ALPACA_SECRET_KEY='********'");
        return text;
    }

    addUserMessage(text) {
        if (!this.chatMessages) {
            console.error('Chat messages container not found');
            return;
        }

        const message = document.createElement('div');
        message.className = 'message user-message';
        message.innerHTML = this.maskSensitiveData(text);
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

    async processMessage(message) {
        if (!this.chatMessages) {
            console.error('Chat messages container not found');
            return;
        }

        this.addUserMessage(message);

        try {
            // Check for Alpaca credentials format
            const credentialsMatch = message.match(/^([A-Z0-9]{32})[,\s]*([A-Z0-9]{64})$/);
            if (credentialsMatch) {
                await this.handleCredentialsSubmission(credentialsMatch[1], credentialsMatch[2]);
                return;
            }

            // Normal message processing
            await this.handleNormalMessage(message);

        } catch (error) {
            console.error('Error processing message:', error);
            this.addBotMessage('❌ Sorry, there was an error processing your message. Please try again.');
        }
    }

    async handleCredentialsSubmission(apiKey, secretKey) {
        console.log('Detected Alpaca credentials, attempting to validate and store...');

        const response = await fetch('/api/store_alpaca_credentials', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                alpaca_api_key: apiKey,
                alpaca_secret_key: secretKey
            })
        });

        const data = await response.json();
        
        if (data.error) {
            console.error('Error storing credentials:', data.error);
            this.addBotMessage(`❌ Error: ${data.error}`);
            return;
        }

        this.addBotMessage(`✅ Perfect! Your Alpaca credentials have been validated and stored securely.

I can now help you with:
• Real-time portfolio tracking
• Trade monitoring
• Market analysis
• Stock information

What would you like to know about?`);

        // Emit event for dashboard update
        const event = new CustomEvent('credentialsStored', { detail: data.metrics });
        document.dispatchEvent(event);
    }

    async handleNormalMessage(message) {
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

        if (data.action) {
            // Emit event for tool actions
            const event = new CustomEvent('botAction', { detail: data.action });
            document.dispatchEvent(event);
        }
    }
} 