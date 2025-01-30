import openai
from typing import Dict, Any, Optional
import json
import re
from datetime import datetime
import yfinance as yf
from services.portfolio import PortfolioService

class ChatbotService:
    def __init__(self, api_key: str):
        from openai import OpenAI  # Import at function level
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.openai.com/v1"  # Explicitly set the base URL
        )
        self.model = "gpt-4o-mini"  # Updated to latest model
        self.conversation_history = [
            {
                "role": "system",
                "content": """You are an AI financial assistant helping users manage their investment portfolio.
                You can help with portfolio analysis, market trends, and trading strategies.
                When analyzing portfolios:
                - Break down asset allocation by type (stocks, bonds, etc.)
                - Highlight diversification metrics
                - Point out any concentration risks
                - Suggest potential optimizations
                Keep responses concise but always offer to dig deeper into specific aspects.
                For example: "Would you like me to analyze the sector diversification in more detail?"
                or "I can provide a deeper analysis of any specific holding."
                Be professional but friendly, and always provide clear, actionable insights.
                If you don't know something, admit it and suggest alternatives."""
            }
        ]
        self.portfolio_service = None

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

    def analyze_portfolio(self, positions: list) -> Dict[str, Any]:
        """Analyze portfolio positions and get AI insights"""
        # Format positions data for the AI
        portfolio_prompt = (
            "Please analyze this investment portfolio and provide insights about:\n"
            "1. Asset allocation and diversification\n"
            "2. Any concentration risks\n"
            "3. Quick recommendations\n\n"
            "Portfolio positions:\n"
        )
        
        for position in positions:
            portfolio_prompt += (
                f"- {position['symbol']}: {position['qty']} shares "
                f"at ${position['current_price']:.2f} "
                f"(Market Value: ${position['market_value']:.2f})\n"
            )

        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": portfolio_prompt
        })

        # Get AI analysis
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.conversation_history,
            temperature=0.7,
            max_tokens=800
        )

        bot_response = response.choices[0].message.content
        self.conversation_history.append({
            "role": "assistant",
            "content": bot_response
        })

        return {
            "response": bot_response,
            "requires_action": False
        }

    def initialize_portfolio_service(self, api_key, secret_key):
        """Initialize portfolio service with user credentials"""
        self.portfolio_service = PortfolioService()
        self.portfolio_service.initialize_with_credentials(api_key, secret_key)

    def _send_progress(self, message):
        """Helper method to send progress updates"""
        print(f"Progress: {message}")  # For debugging
        return {
            "response": message,
            "requires_action": False,
            "in_progress": True,
            "show_typing": True  # Add this flag to keep the typing animation
        }

    def analyze_portfolio_performance(self):
        """Analyze portfolio performance across multiple timeframes and compare with benchmarks"""
        if not self.portfolio_service:
            return {
                "response": "I need access to your Alpaca credentials to analyze your portfolio performance.",
                "requires_action": True
            }

        try:
            # Create a list to store all progress messages
            progress_messages = []
            
            def add_progress(message):
                """Add a progress message to the list"""
                progress_messages.append(message)
                return {
                    "response": message,
                    "requires_action": False,
                    "in_progress": True,
                    "show_typing": True,
                    "progress_messages": progress_messages  # Include all progress messages so far
                }

            # Start the analysis process
            progress_response = add_progress("Starting portfolio performance analysis...")
            
            timeframes = {
                '1M': {'period': '1mo', 'interval': '1d'},
                '1Y': {'period': '1y', 'interval': '1d'}
            }
            
            performance_data = {}
            spy = yf.Ticker("SPY")
            
            # Get current positions for individual asset analysis
            progress_response = add_progress("Fetching current portfolio positions...")
            positions = self.portfolio_service.alpaca.get_positions()
            asset_performance = {}
            
            # Calculate individual asset performance
            for position in positions:
                symbol = position['symbol']
                progress_response = add_progress(f"Processing {symbol}...")
                ticker = yf.Ticker(symbol)
                asset_performance[symbol] = {
                    'weight': float(position['market_value']) / float(position['current_price']),
                    'performance': {}
                }
                
                for timeframe, params in timeframes.items():
                    history = ticker.history(period=params['period'], interval=params['interval'])
                    if len(history) >= 2:
                        start_price = history['Close'].iloc[0]
                        end_price = history['Close'].iloc[-1]
                        if start_price > 0:
                            return_pct = ((end_price / start_price) * 100) - 100
                            asset_performance[symbol]['performance'][timeframe] = return_pct
            
            progress_response = add_progress("Calculating portfolio performance across timeframes...")
            for timeframe, params in timeframes.items():
                progress_response = add_progress(f"Analyzing {timeframe} performance...")
                # Get portfolio performance
                portfolio_history = self.portfolio_service.alpaca.get_portfolio_history(timeframe=timeframe)
                
                if not portfolio_history or 'equity' not in portfolio_history:
                    continue
                
                # Filter out zero and None values
                equity_values = [v for v in portfolio_history['equity'] if v is not None and v > 0]
                
                if len(equity_values) < 2:
                    continue
                    
                # Find the first non-zero value for base calculation
                base_value = equity_values[0]
                if base_value <= 0:  # Additional safety check
                    continue
                    
                # Calculate return based on base 100
                start_value = 100  # Start at base 100
                end_value = (equity_values[-1] / base_value) * 100
                portfolio_return = end_value - start_value
                
                progress_response = add_progress(f"Comparing with S&P 500 benchmark for {timeframe}...")
                # Get benchmark data and normalize to base 100
                try:
                    benchmark = spy.history(period=params['period'], interval=params['interval'])
                    if len(benchmark) < 2:
                        add_progress(f"Warning: Insufficient S&P 500 data for {timeframe}. Skipping benchmark comparison...")
                        performance_data[timeframe] = {
                            'portfolio_return': portfolio_return,
                            'start_value': base_value,
                            'end_value': equity_values[-1],
                            'benchmark_return': None,  # No benchmark data available
                            'asset_returns': {symbol: data['performance'].get(timeframe) 
                                        for symbol, data in asset_performance.items() 
                                        if timeframe in data['performance']}
                        }
                        continue
                        
                    benchmark_start = benchmark['Close'].iloc[0]
                    if benchmark_start <= 0:  # Safety check for benchmark data
                        add_progress(f"Warning: Invalid S&P 500 data for {timeframe}. Skipping benchmark comparison...")
                        continue
                        
                    benchmark_end = (benchmark['Close'].iloc[-1] / benchmark_start) * 100
                    benchmark_return = benchmark_end - 100
                    
                    performance_data[timeframe] = {
                        'portfolio_return': portfolio_return,
                        'start_value': base_value,
                        'end_value': equity_values[-1],
                        'benchmark_return': benchmark_return,
                        'asset_returns': {symbol: data['performance'].get(timeframe) 
                                    for symbol, data in asset_performance.items() 
                                    if timeframe in data['performance']}
                    }
                except Exception as e:
                    add_progress(f"Warning: Error getting S&P 500 data for {timeframe}. Skipping benchmark comparison...")
                    performance_data[timeframe] = {
                        'portfolio_return': portfolio_return,
                        'start_value': base_value,
                        'end_value': equity_values[-1],
                        'benchmark_return': None,  # Error getting benchmark data
                        'asset_returns': {symbol: data['performance'].get(timeframe) 
                                    for symbol, data in asset_performance.items() 
                                    if timeframe in data['performance']}
                    }

            if not performance_data:
                return {
                    "response": "I couldn't retrieve enough performance data to provide a meaningful analysis.",
                    "requires_action": False
                }

            progress_response = add_progress("Preparing detailed performance analysis...")
            # Prepare detailed analysis prompt for GPT
            analysis_prompt = self._prepare_performance_analysis_prompt(performance_data, asset_performance)
            
            progress_response = add_progress("Generating AI insights...")
            # Get AI analysis
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a professional portfolio analyst. Analyze the provided portfolio performance data and provide insights about:
                        1. Overall portfolio performance across different timeframes
                        2. Individual asset contributions and performance
                        3. Comparison with benchmark (S&P 500)
                        4. Specific recommendations based on the data
                        Be specific with numbers but keep the analysis easy to understand."""
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                temperature=0.7,
                max_tokens=800
            )

            # Return the final analysis
            excel_data = self._generate_performance_excel(performance_data, asset_performance)
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            return {
                "response": response.choices[0].message.content,
                "requires_action": False,
                "in_progress": False,
                "show_typing": False,  # Final message, hide typing animation
                "progress_messages": progress_messages,  # Include all progress messages
                "has_attachment": True,
                "attachment": {
                    "data": excel_data,
                    "filename": f"portfolio_analysis_{current_time}.xlsx",
                    "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                }
            }

        except Exception as e:
            print(f"Error analyzing portfolio performance: {str(e)}")
            return {
                "response": "I encountered an error while analyzing your portfolio performance. Please try again later.",
                "requires_action": False,
                "error": True
            }

    def _prepare_performance_analysis_prompt(self, performance_data, asset_performance):
        """Prepare a detailed prompt for GPT analysis"""
        prompt = "Please analyze this portfolio performance data:\n\n"
        
        # Add timeframe performance data
        for timeframe, data in performance_data.items():
            prompt += f"\n{timeframe} Performance:\n"
            prompt += f"- Portfolio Return: {data['portfolio_return']:.2f}%\n"
            prompt += f"- S&P 500 Return: {data['benchmark_return']:.2f}%\n"
            prompt += "- Individual Asset Returns:\n"
            
            # Add individual asset performance
            for symbol, return_value in data['asset_returns'].items():
                weight = asset_performance[symbol]['weight']
                prompt += f"  • {symbol} (Weight: {weight:.2f}%): {return_value:.2f}%\n"
        
        prompt += "\nPlease provide:\n"
        prompt += "1. A detailed analysis of the portfolio's performance across all timeframes\n"
        prompt += "2. Insights about which assets are driving performance (both positive and negative)\n"
        prompt += "3. Specific recommendations based on the performance data\n"
        prompt += "4. Any notable trends or patterns in the data\n"
        
        return prompt

    def process_message(self, user_message: str, user=None) -> Dict[str, Any]:
        """Process a user message and return the response"""
        try:
            # Initialize portfolio service if user has credentials and it's not already initialized
            if user and user.has_alpaca_credentials() and not self.portfolio_service:
                self.initialize_portfolio_service(user.alpaca_api_key, user.alpaca_secret_key)

            # Check for performance analysis request
            if any(keyword in user_message.lower() for keyword in ['performance', 'analysis', 'compare', 'benchmark', 'return']) or user_message == 'portfolio-performance':
                # We already have credentials and portfolio service initialized
                if self.portfolio_service:
                    return self.analyze_portfolio_performance()
                elif user and user.has_alpaca_credentials():
                    self.initialize_portfolio_service(user.alpaca_api_key, user.alpaca_secret_key)
                    return self.analyze_portfolio_performance()
                else:
                    return {
                        "response": "I need your Alpaca credentials to analyze your portfolio performance. Please provide them or set them up in settings.",
                        "requires_action": True
                    }

            # Handle portfolio-overview command
            if user_message == "portfolio-overview":
                if self.portfolio_service:
                    positions = self.portfolio_service.alpaca.get_positions()
                    return self.analyze_portfolio(positions)
                elif user and user.has_alpaca_credentials():
                    self.initialize_portfolio_service(user.alpaca_api_key, user.alpaca_secret_key)
                    positions = self.portfolio_service.alpaca.get_positions()
                    return self.analyze_portfolio(positions)
                else:
                    return {
                        "response": "I need your Alpaca credentials to analyze your portfolio. Please provide them or set them up in settings.",
                        "requires_action": True
                    }

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
                max_tokens=1500
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

    def _generate_performance_excel(self, performance_data, asset_performance):
        """Generate an Excel file containing the performance analysis data"""
        try:
            import pandas as pd
            import io

            output = io.BytesIO()
            
            # Create a Pandas Excel writer
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Summary sheet
                summary_data = []
                for timeframe, data in performance_data.items():
                    summary_data.append({
                        'Timeframe': timeframe,
                        'Portfolio Return (%)': data['portfolio_return'],
                        'S&P 500 Return (%)': data['benchmark_return'] if data['benchmark_return'] is not None else 'N/A',
                        'Start Value ($)': data['start_value'],
                        'End Value ($)': data['end_value']
                    })
                
                if summary_data:
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Asset Performance sheet for each timeframe
                for timeframe, data in performance_data.items():
                    asset_data = []
                    for symbol, return_value in data['asset_returns'].items():
                        weight = asset_performance[symbol]['weight']
                        asset_data.append({
                            'Symbol': symbol,
                            'Weight (%)': weight,
                            f'Return ({timeframe}) (%)': return_value if return_value is not None else 'N/A'
                        })
                    
                    if asset_data:
                        asset_df = pd.DataFrame(asset_data)
                        asset_df.to_excel(writer, sheet_name=f'{timeframe} Details', index=False)
                        
                        # Get the xlsxwriter workbook and worksheet objects
                        workbook = writer.book
                        worksheet = writer.sheets[f'{timeframe} Details']
                        
                        # Add some formatting
                        header_format = workbook.add_format({
                            'bold': True,
                            'bg_color': '#2d2d2d',
                            'font_color': 'white',
                            'border': 1
                        })
                        
                        # Write the column headers with the header format
                        for col_num, value in enumerate(asset_df.columns.values):
                            worksheet.write(0, col_num, value, header_format)
                            worksheet.set_column(col_num, col_num, 15)  # Set column width
            
            # Reset pointer and return bytes
            output.seek(0)
            return output.getvalue()
            
        except Exception as e:
            print(f"Error generating Excel file: {str(e)}")
            raise
