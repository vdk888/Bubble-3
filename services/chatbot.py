import openai
from typing import Dict, Any, Optional
import json
import re

class ChatbotService:
    def __init__(self, api_key: str):
        from openai import OpenAI  # Import at function level
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.openai.com/v1"  # Explicitly set the base URL
        )
        self.model = "gpt-4o-mini"  # Using a valid OpenAI model
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

    def _validate_alpaca_key(self, key: str, key_type: str = "api") -> bool:
        """Validate Alpaca key format"""
        if key_type == "api":
            return bool(re.match(r'^PK[A-Z0-9]{16,}$', key))
        elif key_type == "secret":
            return bool(re.match(r'^[A-Za-z0-9]{32,}$', key))
        return False

    def _validate_alpaca_credentials(self, api_key: str, secret_key: str) -> bool:
        """Validate Alpaca credentials by making a test API call"""
        try:
            import requests
            headers = {
                'APCA-API-KEY-ID': api_key,
                'APCA-API-SECRET-KEY': secret_key
            }
            response = requests.get('https://paper-api.alpaca.markets/v2/account', headers=headers)
            return response.status_code == 200
        except Exception as e:
            print(f"Error validating Alpaca credentials: {str(e)}")
            return False

    def _detect_alpaca_keys(self, message: str) -> dict:
        """Detect Alpaca API and Secret keys in a message"""
        # Look for API key pattern
        api_key_match = re.search(r'PK[A-Z0-9]{16,}', message)
        # Look for Secret key pattern
        secret_key_match = re.search(r'[A-Za-z0-9]{32,}', message)
        
        result = {}
        if api_key_match:
            api_key = api_key_match.group(0)
            if self._validate_alpaca_key(api_key, "api"):
                result["api_key"] = api_key
                
        if secret_key_match:
            secret_key = secret_key_match.group(0)
            # Make sure we don't capture the API key as secret key
            if secret_key != result.get("api_key") and self._validate_alpaca_key(secret_key, "secret"):
                result["secret_key"] = secret_key
                
        return result

    def get_greeting(self, user):
        if user.has_alpaca_credentials():
            # First check if the credentials format is valid
            if (self._validate_alpaca_key(user.alpaca_api_key, "api") and 
                self._validate_alpaca_key(user.alpaca_secret_key, "secret")):
                # Then validate against the Alpaca API
                if self._validate_alpaca_credentials(user.alpaca_api_key, user.alpaca_secret_key):
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
                        "👋 Hello! I notice your stored Alpaca credentials are not working with the Alpaca API. "
                        "Please provide valid Alpaca API and Secret keys to access trading features. "
                        "You can either paste them here or update them in the settings page."
                    )
            else:
                return (
                    "👋 Hello! I notice your stored Alpaca credentials appear to be invalid. "
                    "Please provide valid Alpaca API and Secret keys to access trading features. "
                    "You can either paste them here or update them in the settings page."
                )
        else:
            return (
                "👋 Hello! I'm your AI financial assistant. To help you manage your portfolio and provide market insights, "
                "I'll need your Alpaca trading account credentials. You can paste your API key and Secret key here, "
                "or set them up in the settings page. What would you prefer?"
            )

    def process_message(self, user_message: str, user=None) -> Dict[str, Any]:
        """Process a user message and return the response"""
        try:
            # Special initialization message
            if user_message == "__init__":
                return {
                    "response": self.get_greeting(user),
                    "requires_action": False
                }

            # Check for Alpaca keys in the message
            detected_keys = self._detect_alpaca_keys(user_message)
            if detected_keys:
                if user:
                    current_api_key = user.alpaca_api_key
                    current_secret_key = user.alpaca_secret_key
                    
                    # Update the detected keys
                    if "api_key" in detected_keys:
                        user.alpaca_api_key = detected_keys["api_key"]
                    if "secret_key" in detected_keys:
                        user.alpaca_secret_key = detected_keys["secret_key"]
                    
                    # Validate credentials before saving if we have both keys
                    if user.has_alpaca_credentials():
                        if self._validate_alpaca_credentials(user.alpaca_api_key, user.alpaca_secret_key):
                            # Save to database if validation successful
                            if current_api_key != user.alpaca_api_key or current_secret_key != user.alpaca_secret_key:
                                user.save_alpaca_credentials(user.alpaca_api_key, user.alpaca_secret_key)
                            return {
                                "response": "✅ Great! I've validated your Alpaca credentials and they're working perfectly. You're now ready to start trading! What would you like to do first?",
                                "requires_action": False
                            }
                        else:
                            # Reset the invalid credentials
                            user.alpaca_api_key = current_api_key
                            user.alpaca_secret_key = current_secret_key
                            return {
                                "response": "❌ The provided credentials are not valid with the Alpaca API. Please check your credentials and try again.",
                                "requires_action": False
                            }
                    
                    # If we only have one key, save it and ask for the other
                    if current_api_key != user.alpaca_api_key or current_secret_key != user.alpaca_secret_key:
                        user.save_alpaca_credentials(user.alpaca_api_key, user.alpaca_secret_key)
                    
                    if not user.alpaca_api_key:
                        return {
                            "response": "I've saved your Alpaca Secret key. I still need your API key (starts with 'PK'). Please provide it when you're ready.",
                            "requires_action": False
                        }
                    else:
                        return {
                            "response": "I've saved your Alpaca API key. I still need your Secret key. Please provide it when you're ready.",
                            "requires_action": False
                        }

            # Add user context and message to conversation
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
