import openai
from typing import Dict, Any, Optional
import json

class ChatbotService:
    def __init__(self, api_key: str):
        openai.api_key = api_key
        self.model = "gpt-4o-mini"
        self.conversation_history = []
        self.waiting_for_alpaca_key = False
        self.waiting_for_alpaca_secret = False
        self.collected_alpaca_key = None
        self.greeted = False

    def get_greeting(self, user):
        if user.has_alpaca_credentials():
            return (
                "👋 Hello! I'm your AI financial assistant. I see you already have your Alpaca credentials set up - that's great! "
                "I can help you with:\n"
                "• Checking your portfolio value and positions\n"
                "• Viewing your recent trades\n"
                "• Analyzing market trends\n"
                "• Getting stock information\n\n"
                "What would you like to know about?"
            )
        else:
            return (
                "👋 Hello! I'm your AI financial assistant. I can help you manage your portfolio and provide market insights.\n\n"
                "I notice you haven't set up your Alpaca trading account credentials yet. Would you like to set them up now? "
                "This will allow me to help you with:\n"
                "• Real-time portfolio tracking\n"
                "• Trade monitoring\n"
                "• Market analysis\n"
                "• Stock information\n\n"
                "Just let me know if you'd like to proceed with setting up your credentials!"
            )

    def process_message(self, user_message: str, user=None) -> Dict[str, Any]:
        """
        Process a user message and return both the response and any visual data
        """
        # Send greeting on first message
        if not self.greeted and user:
            self.greeted = True
            return {
                "response": self.get_greeting(user),
                "requires_action": False
            }

        # Check if we're in the process of collecting Alpaca credentials
        if self.waiting_for_alpaca_key:
            self.collected_alpaca_key = user_message
            self.waiting_for_alpaca_key = False
            self.waiting_for_alpaca_secret = True
            return {
                "response": "Great! Now please provide your Alpaca Secret Key. Don't worry, this will be stored securely in your account.",
                "requires_action": True
            }
        
        if self.waiting_for_alpaca_secret:
            self.waiting_for_alpaca_secret = False
            if user:
                user.alpaca_api_key = self.collected_alpaca_key
                user.alpaca_secret_key = user_message
                self.collected_alpaca_key = None
                return {
                    "response": (
                        "Perfect! I've saved your Alpaca credentials securely. Now I can help you with all your portfolio needs!\n\n"
                        "Would you like to:\n"
                        "• Check your current portfolio value?\n"
                        "• See your positions?\n"
                        "• View recent trades?\n"
                        "Just let me know what interests you!"
                    ),
                    "requires_action": False,
                    "credentials_updated": True
                }

        # Handle response to initial greeting or credential request
        if not user.has_alpaca_credentials() and any(keyword in user_message.lower() for keyword in ["yes", "sure", "okay", "set up", "setup", "proceed", "credentials"]):
            self.waiting_for_alpaca_key = True
            return {
                "response": (
                    "Excellent! Let's get your Alpaca account connected. First, I'll need your Alpaca API Key. "
                    "You can find this in your Alpaca dashboard under 'Paper Trading' settings.\n\n"
                    "Please provide your Alpaca API Key:"
                ),
                "requires_action": True
            }

        # Check if the message is about portfolio or trading
        portfolio_keywords = ["portfolio", "investment", "stock", "trade", "position", "market", "balance", "alpaca"]
        if any(keyword in user_message.lower() for keyword in portfolio_keywords):
            if user and not user.has_alpaca_credentials():
                self.waiting_for_alpaca_key = True
                return {
                    "response": (
                        "I'd love to help you with that! But first, I'll need your Alpaca trading account credentials. "
                        "These will be stored securely and used to access your portfolio data.\n\n"
                        "Please provide your Alpaca API Key:"
                    ),
                    "requires_action": True
                }

        # Add the user's message to the conversation history
        self.conversation_history.append({"role": "user", "content": user_message})

        try:
            if any(keyword in user_message.lower() for keyword in portfolio_keywords) and user and user.has_alpaca_credentials():
                response = (
                    "I can help you with your portfolio information. What specific information would you like to know?\n\n"
                    "• Your current portfolio value and cash balance\n"
                    "• Your positions and their performance\n"
                    "• Your recent trades\n\n"
                    "Just let me know what interests you!"
                )
            else:
                # Get response from OpenAI
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant. When appropriate, you can provide visual data like charts or metrics in JSON format."},
                        *self.conversation_history
                    ]
                )
                response = response.choices[0].message.content
            
            # Check if the response contains visual data (in JSON format)
            visual_data = self._extract_visual_data(response)
            
            # Clean the message if it contains JSON
            if visual_data:
                response = self._clean_message(response)
            
            # Add assistant response to history
            self.conversation_history.append({"role": "assistant", "content": response})
            
            return {
                "response": response,
                "visual_data": visual_data
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "visual_data": None
            }
    
    def _extract_visual_data(self, message: str) -> Optional[Dict]:
        """
        Extract JSON visual data from the message if present
        """
        try:
            # Look for JSON blocks in the message
            if '```json' in message and '```' in message:
                json_str = message.split('```json')[1].split('```')[0]
                return json.loads(json_str)
        except:
            pass
        return None
    
    def _clean_message(self, message: str) -> str:
        """
        Remove JSON blocks from the message
        """
        if '```json' in message and '```' in message:
            parts = message.split('```json')
            message = parts[0]
            if len(parts) > 1:
                message += parts[1].split('```', 1)[1]
        return message.strip()

    def clear_history(self):
        """
        Clear the conversation history
        """
        self.conversation_history = []
        self.waiting_for_alpaca_key = False
        self.waiting_for_alpaca_secret = False
        self.collected_alpaca_key = None
        self.greeted = False
