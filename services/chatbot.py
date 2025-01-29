import openai
from typing import Dict, Any, Optional
import json

class ChatbotService:
    def __init__(self, api_key: str):
        from openai import OpenAI  # Import at function level
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.openai.com/v1"  # Explicitly set the base URL
        )
        self.model = "gpt-3.5-turbo"  # Using a valid OpenAI model
        self.conversation_history = [
            {
                "role": "system",
                "content": """You are an AI financial assistant helping users manage their investment portfolio.
                You can help with portfolio analysis, market trends, and trading strategies.
                Be professional but friendly, and always provide clear, actionable insights.
                If you don't know something, admit it and suggest alternatives.
                Keep responses concise but informative."""
            }
        ]
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
        """Process a user message and return the response"""
        try:
            # Special initialization message
            if user_message == "__init__":
                self.greeted = True
                return {
                    "response": self.get_greeting(user),
                    "requires_action": False
                }

            # Add user context
            if user and user.has_alpaca_credentials():
                context = "The user has Alpaca trading account credentials set up and can perform portfolio operations."
            else:
                context = "The user has not set up their Alpaca trading account credentials yet."

            # Add context and user message to conversation
            self.conversation_history.append({
                "role": "system",
                "content": context
            })
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })

            # Get response from OpenAI using new API format
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                temperature=0.7,
                max_tokens=500
            )

            # Extract and store response using new response format
            bot_response = response.choices[0].message.content
            self.conversation_history.append({
                "role": "assistant",
                "content": bot_response
            })

            # Keep conversation history manageable
            if len(self.conversation_history) > 10:
                # Keep first system message and last 9 messages
                self.conversation_history = [
                    self.conversation_history[0]  # Keep initial system message
                ] + self.conversation_history[-9:]  # Keep last 9 messages

            return {
                "response": bot_response,
                "requires_action": False
            }

        except Exception as e:
            print(f"Error in process_message: {str(e)}")  # Log the error
            return {
                "response": "I apologize, but I encountered an error. Please try again.",
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
        """Clear the conversation history"""
        self.conversation_history = [self.conversation_history[0]]  # Keep only the initial system message
        self.greeted = False
