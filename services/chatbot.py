import openai
from typing import Dict, Any, Optional
import json

class ChatbotService:
    def __init__(self, api_key: str):
        openai.api_key = api_key
        self.model = "gpt-4o-mini"  # Restored original model name
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
        try:
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
            if user and not user.has_alpaca_credentials() and any(keyword in user_message.lower() for keyword in ["yes", "sure", "okay", "set up", "setup", "proceed", "credentials"]):
                self.waiting_for_alpaca_key = True
                return {
                    "response": "Please provide your Alpaca API Key. This will be stored securely in your account.",
                    "requires_action": True
                }

            # Process normal message with OpenAI
            messages = self.conversation_history + [{"role": "user", "content": user_message}]
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )

            # Extract the response text
            bot_response = response.choices[0].message.content

            # Update conversation history
            self.conversation_history.extend([
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": bot_response}
            ])

            # Keep conversation history manageable
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]

            return {
                "response": bot_response,
                "requires_action": False
            }

        except Exception as e:
            return {
                "response": f"I apologize, but I encountered an error: {str(e)}. Please try again.",
                "requires_action": False,
                "error": True
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
