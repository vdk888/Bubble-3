import openai
from typing import Dict, Any, Optional, List
import json
import re
from datetime import datetime
import yfinance as yf
from services.portfolio import PortfolioService
from services.yahoo_finance import YahooFinanceService

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
                "content": """You are an AI financial assistant with access to various tools and data sources. Your role is to help users with their financial and investment needs.

                You have access to the following tools:

                1. PRICE_DATA - Get price data for any stock or crypto
                Usage: When you need price data, respond with: 
                "TOOL:PRICE_DATA:{symbols}:{timeframe}"
                Example: "TOOL:PRICE_DATA:AAPL,MSFT:1mo"
                Timeframes: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max

                2. MARKET_SUMMARY - Get major market indices data
                Usage: When you need market overview, respond with:
                "TOOL:MARKET_SUMMARY"

                3. COMPANY_INFO - Get detailed company information
                Usage: When you need company details, respond with:
                "TOOL:COMPANY_INFO:{symbol}"
                Example: "TOOL:COMPANY_INFO:AAPL"

                4. PORTFOLIO_POSITIONS - Get current portfolio positions
                Usage: When you need portfolio positions, respond with:
                "TOOL:PORTFOLIO_POSITIONS"

                5. PORTFOLIO_PERFORMANCE - Get portfolio performance history
                Usage: When you need portfolio performance, respond with:
                "TOOL:PORTFOLIO_PERFORMANCE:{timeframe}"
                Example: "TOOL:PORTFOLIO_PERFORMANCE:1D"
                Timeframes: 1D, 1W, 1M, 3M, 1Y, ALL

                6. IMPORTANT_INFO - Save important user information
                Usage: When you detect important information about the user, respond with:
                "TOOL:IMPORTANT_INFO:{info_type}:{content}"
                Example: "TOOL:IMPORTANT_INFO:life_event:User mentioned they're planning to retire in 2025"
                Info types: life_event, preference, goal, risk_profile

                When users ask questions:
                1. Determine if you need any market data to provide a complete answer
                2. If yes, request the data using the appropriate tool command
                3. Once you receive the data, analyze it and provide insights
                4. Always explain your analysis and offer additional context

                Remember:
                - Be concise but informative
                - Explain market terms when used
                - Provide context for numbers and trends
                - Suggest relevant follow-up analysis when appropriate
                - If you're unsure about something, say so and explain what you do know"""
            }
        ]
        self.portfolio_service = None
        self.yahoo_finance = YahooFinanceService()

    def _validate_alpaca_key(self, key: str, key_type: str) -> bool:
        """Validate Alpaca key format"""
        if key_type == "api":
            return bool(re.match(r'^PK[A-Z0-9]{16,}$', key))
        elif key_type == "secret":
            return bool(re.match(r'^[A-Za-z0-9]{32,}$', key))
        return False

    def _validate_alpaca_credentials(self, api_key: str, secret_key: str) -> bool:
        """Validate Alpaca credentials against the API"""
        try:
            # Try to initialize portfolio service with these credentials
            temp_portfolio = PortfolioService()
            temp_portfolio.initialize_with_credentials(api_key, secret_key)
            # Test the connection
            temp_portfolio.get_positions()
            return True
        except Exception as e:
            print(f"Credential validation failed: {str(e)}")
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
                        "👋 Welcome back! I hope you're having a good day.\n\n"
                        "Before we dive into your portfolio, I'd like to know if there have been any significant changes "
                        "in your life or financial situation that we should consider?\n\n"
                        "I'm here to help you with:\n"
                        "🔹 Reviewing your current portfolio performance\n"
                        "🔹 Analyzing your total assets across different categories\n"
                        "🔹 Providing market insights and investment opportunities\n"
                        "🔹 Answering any questions about your financial strategy\n"
                        "What would you like to focus on today?"
                    )
                else:
                    return (
                        "👋 Welcome! I notice there seems to be an issue with your Alpaca credentials.\n\n"
                        "To help you manage your portfolio effectively, I'll need valid API credentials. "
                        "You can either update them in the settings page or paste them here.\n\n"
                        "How would you like to proceed?"
                    )
            else:
                return (
                    "👋 Welcome! There appears to be an issue with your stored credentials.\n\n"
                    "To ensure I can provide you with accurate portfolio management, please provide valid "
                    "Alpaca API credentials. You can update them in settings or share them here.\n\n"
                    "Which would you prefer?"
                )
        else:
            return (
                "👋 Welcome! I'm your AI financial assistant.\n\n"
                "To get started and provide you with personalized portfolio management, I'll need your "
                "Alpaca trading account credentials.\n\n"
                "You can either:\n"
                "🔹 Paste your API and Secret keys here\n"
                "🔹 Set them up in the settings page\n\n"
                "Which option works better for you?"
            )

    def initialize_portfolio_service(self, api_key, secret_key):
        """Initialize portfolio service with user credentials"""
        try:
            if not api_key or not secret_key:
                print("Missing Alpaca credentials")
                self.portfolio_service = None
                raise ValueError("Missing Alpaca credentials")

            from services.portfolio import PortfolioService
            print(f"Creating new portfolio service instance...")
            self.portfolio_service = PortfolioService()
            print(f"Initializing portfolio service with credentials...")
            self.portfolio_service.initialize_with_credentials(api_key, secret_key)
            
            # Verify the service is working by testing a basic operation
            test_positions = self.portfolio_service.get_positions()
            print(f"Portfolio service initialized successfully - found {len(test_positions)} positions")
            
        except Exception as e:
            print(f"Error initializing portfolio service: {str(e)}")
            self.portfolio_service = None
            raise


    def process_message(self, user_message: str, user=None) -> Dict[str, Any]:
        """Process a user message and return the response"""
        try:
            # Check for API keys in the message
            api_key_match = re.search(r'PK[A-Z0-9]{16,}', user_message)
            secret_key_match = re.search(r'[A-Za-z0-9]{32,}', user_message)

            if api_key_match and secret_key_match:
                api_key = api_key_match.group()
                secret_key = secret_key_match.group()
                
                try:
                    # Validate the credentials
                    if self._validate_alpaca_credentials(api_key, secret_key):
                        if user:
                            # Save credentials to user profile
                            user.save_alpaca_credentials(api_key, secret_key)
                            # Initialize portfolio service with new credentials
                            self.initialize_portfolio_service(api_key, secret_key)
                            return {
                                "response": "✅ Great! I've successfully saved your Alpaca credentials. "
                                          "Now I can help you manage your portfolio and provide detailed market insights. "
                                          "What would you like to know about?",
                                "requires_action": False
                            }
                        else:
                            return {
                                "response": "✅ Those credentials look valid, but I couldn't save them because you're not logged in. "
                                          "Please log in or sign up to save your credentials.",
                                "requires_action": True
                            }
                    else:
                        return {
                            "response": "❌ Those credentials appear to be invalid. Please check your Alpaca API key and Secret key and try again.",
                            "requires_action": True
                        }
                except Exception as e:
                    print(f"Error validating credentials: {str(e)}")
                    return {
                        "response": "❌ I encountered an error while validating your credentials. Please try again or use the settings page.",
                        "requires_action": True
                    }

            # Check if we have a user and if they have Alpaca credentials
            if user and user.has_alpaca_credentials() and not self.portfolio_service:
                try:
                    print("Initializing portfolio service with user credentials...")
                    self.initialize_portfolio_service(user.alpaca_api_key, user.alpaca_secret_key)
                    print("Portfolio service initialized successfully")
                except Exception as e:
                    print(f"Error initializing portfolio service: {str(e)}")
                    return {
                        "response": "I'm having trouble accessing your portfolio data. Please verify your Alpaca credentials in settings.",
                        "requires_action": True
                    }

            # Add user message to conversation
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })

            # Get initial response from OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                temperature=0.7,
                max_tokens=1800
            )

            bot_response = response.choices[0].message.content
            print(f"Initial bot response: {bot_response}")

            # The model will naturally use TOOL commands when needed
            if "TOOL:" in bot_response:
                # Extract the tool command - it might be followed by additional text
                command_parts = bot_response.split("\n")
                for part in command_parts:
                    if part.strip().startswith("TOOL:"):
                        tool_command = part.strip()
                        print(f"Detected tool command: {tool_command}")  # Debug log
                        
                        # Get tool response
                        tool_response = self._handle_tool_command(tool_command)
                        
                        # Add tool result to conversation for context
                        self.conversation_history.append({
                            "role": "assistant",
                            "content": f"I've fetched the following data:\n{tool_response['response']}"
                        })

                        # Get final analysis from OpenAI
                        final_response = self.client.chat.completions.create(
                            model=self.model,
                            messages=self.conversation_history,
                            temperature=0.7,
                            max_tokens=1500
                        )

                        bot_response = final_response.choices[0].message.content
                        break

            # Add final bot response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": bot_response
            })

            # Keep conversation history manageable
            if len(self.conversation_history) > 10:
                # Keep system message and last 9 exchanges
                self.conversation_history = [
                    self.conversation_history[0]  # Keep system message
                ] + self.conversation_history[-9:]

            return {
                "response": bot_response,
                "requires_action": False
            }

        except Exception as e:
            print(f"Error in process_message: {str(e)}")
            return {
                "response": "I apologize, but I encountered an error. Please try again.",
                "requires_action": False,
                "error": True
            }

    def _handle_tool_command(self, command: str) -> Dict:
        """Handle tool commands from the chatbot"""
        try:
            print(f"Processing tool command: {command}")
            parts = command.split(":")
            if len(parts) < 2:
                return {"error": "Invalid tool command"}

            tool = parts[1]
            print(f"Tool type: {tool}")

            # Check if portfolio service is initialized for portfolio-related tools
            if tool in ["PORTFOLIO_POSITIONS", "PORTFOLIO_PERFORMANCE"]:
                if not self.portfolio_service:
                    print("Portfolio service not initialized")
                    return {
                        "response": "I need access to your Alpaca trading account to provide portfolio information. "
                                   "Please make sure your credentials are set up in the settings page.",
                        "requires_action": True
                    }
                print("Portfolio service is initialized and ready")

            if tool == "PORTFOLIO_POSITIONS":
                try:
                    print("Fetching portfolio positions...")
                    positions = self.portfolio_service.get_positions()
                    if not positions:
                        return {
                            "response": "Your portfolio currently has no positions.",
                            "data": []
                        }
                    print(f"Retrieved {len(positions)} positions")
                    formatted_response = self._format_positions_response(positions)
                    print("Successfully formatted positions response")
                    return {
                        "response": formatted_response,
                        "data": positions
                    }
                except Exception as e:
                    print(f"Error in portfolio positions handling: {str(e)}")
                    return {
                        "response": "I encountered an error while fetching your portfolio positions. "
                                   "Please verify your Alpaca credentials are still valid.",
                        "requires_action": True
                    }

            elif tool == "PORTFOLIO_PERFORMANCE":
                if len(parts) != 3:
                    return {"error": "Invalid PORTFOLIO_PERFORMANCE command format"}
                timeframe = parts[2]
                try:
                    print(f"Fetching portfolio performance for timeframe: {timeframe}")
                    performance = self.portfolio_service.alpaca.get_portfolio_history(timeframe=timeframe)
                    print("Successfully retrieved portfolio performance")
                    formatted_response = self._format_performance_response(performance)
                    print("Successfully formatted performance response")
                    return {
                        "response": formatted_response,
                        "data": performance
                    }
                except Exception as e:
                    print(f"Error in portfolio performance handling: {str(e)}")
                    return {"error": f"Failed to get portfolio performance: {str(e)}"}

            elif tool == "PRICE_DATA":
                if len(parts) != 4:
                    return {"error": "Invalid PRICE_DATA command format"}
                symbols = [s.strip() for s in parts[2].split(",")]
                timeframe = parts[3]
                print(f"Fetching price data for symbols: {symbols}, timeframe: {timeframe}")  # Debug log
                
                try:
                    data = self.yahoo_finance.get_price_data(symbols, timeframe)
                    formatted_response = self._format_price_data_response(data)
                    print(f"Successfully formatted price data response")  # Debug log
                    return {
                        "response": formatted_response,
                        "data": data
                    }
                except Exception as e:
                    print(f"Error in price data handling: {str(e)}")  # Debug log
                    return {"error": f"Failed to process price data: {str(e)}"}

            elif tool == "MARKET_SUMMARY":
                print("Fetching market summary")  # Debug log
                data = self.yahoo_finance.get_market_summary()
                return {
                    "response": self._format_price_data_response(data),
                    "data": data
                }

            elif tool == "COMPANY_INFO":
                if len(parts) != 3:
                    return {"error": "Invalid COMPANY_INFO command format"}
                symbol = parts[2]
                print(f"Fetching company info for: {symbol}")  # Debug log
                data = self.yahoo_finance.get_company_info(symbol)
                return {
                    "response": self._format_company_info_response(data),
                    "data": data
                }

            elif tool == "IMPORTANT_INFO":
                if len(parts) != 4:
                    return {"error": "Invalid IMPORTANT_INFO command format"}
                info_type = parts[2]
                content = parts[3]
                
                try:
                    # Import necessary modules
                    from flask import current_app
                    from flask_login import current_user
                    from models import UserInfo, db
                    
                    if not current_user or not current_user.is_authenticated:
                        print("No authenticated user found")
                        return {
                            "response": "Cannot save user information - no user logged in",
                            "requires_action": True
                        }
                    
                    # Create new UserInfo instance
                    new_info = UserInfo(
                        user_id=current_user.id,
                        info_type=info_type,
                        content=content
                    )
                    
                    # Add and commit to database within app context
                    with current_app.app_context():
                        db.session.add(new_info)
                        db.session.commit()
                        print(f"Successfully stored important info for user {current_user.id}")
                    
                    return {
                        "response": f"✅ I've noted this important information about your {info_type}.",
                        "data": {"type": info_type, "content": content}
                    }
                except Exception as e:
                    print(f"Error saving important info: {str(e)}")
                    return {"error": f"Failed to save information: {str(e)}"}

            return {"error": f"Unknown tool: {tool}"}

        except Exception as e:
            print(f"Error handling tool command: {str(e)}")
            return {"error": str(e)}

    def _format_company_info_response(self, data: Dict) -> str:
        """Format company information into a user-friendly response"""
        if 'error' in data:
            return f"Sorry, I couldn't fetch the company information: {data['error']}"

        basic = data['basic_info']
        financial = data['financial_info']

        response = [
            f"📈 {basic['name']} Company Profile:",
            f"Sector: {basic['sector'] or 'N/A'}",
            f"Industry: {basic['industry'] or 'N/A'}",
            f"Country: {basic['country'] or 'N/A'}",
            "",
            "Key Metrics:",
            f"Market Cap: ${financial['market_cap']:,.2f}" if financial['market_cap'] else "Market Cap: N/A",
            f"Forward P/E: {financial['forward_pe']:.2f}" if financial['forward_pe'] else "Forward P/E: N/A",
            f"Dividend Yield: {financial['dividend_yield']*100:.2f}%" if financial['dividend_yield'] else "Dividend Yield: N/A",
            f"Beta: {financial['beta']:.2f}" if financial['beta'] else "Beta: N/A",
            "",
            "52-Week Range:",
            f"High: ${financial['fifty_two_week_high']:,.2f}" if financial['fifty_two_week_high'] else "High: N/A",
            f"Low: ${financial['fifty_two_week_low']:,.2f}" if financial['fifty_two_week_low'] else "Low: N/A"
        ]

        if basic.get('description'):
            response.extend(["", "Business Description:", basic['description']])

        return "\n".join(response)

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

    def _handle_price_data_request(self, request: Dict) -> Dict:
        """Handle a price data request"""
        try:
            # Fetch data from Yahoo Finance
            data = self.yahoo_finance.get_price_data(
                symbols=request['symbols'],
                timeframe=request['timeframe']
            )
            
            # Format response for the user
            response = self._format_price_data_response(data)
            
            return {
                "response": response,
                "requires_action": False,
                "data": data  # Include raw data for potential follow-up analysis
            }
            
        except Exception as e:
            print(f"Error handling price data request: {str(e)}")
            return {
                "response": f"I apologize, but I encountered an error while fetching the price data: {str(e)}",
                "requires_action": False,
                "error": True
            }

    def _format_price_data_response(self, data: Dict) -> str:
        """Format price data into a user-friendly response"""
        if 'error' in data:
            return f"Sorry, I couldn't fetch the price data: {data['error']}"
        
        response_parts = []
        for symbol, symbol_data in data.items():
            if 'error' in symbol_data:
                response_parts.append(f"❌ {symbol}: Could not fetch data ({symbol_data['error']})")
                continue
            
            metadata = symbol_data['metadata']
            prices = symbol_data['prices']
            
            if not prices:
                response_parts.append(f"❌ {symbol}: No price data available")
                continue
            
            latest_price = metadata['current_price']
            name = metadata['name']
            
            # Calculate price change
            first_price = prices[0]['Close']
            last_price = prices[-1]['Close']
            price_change = ((last_price - first_price) / first_price) * 100
            
            # Format the response with more details
            response = [
                f"📊 {name} ({symbol})",
                f"Current Price: ${latest_price:,.2f}",
                f"Period Change: {price_change:+.2f}%",
                f"Trading Period: {symbol_data['timeframe']}",
                f"Exchange: {metadata['exchange']}",
                "",
                "Additional Information:",
                f"• Market Cap: ${metadata['market_cap']:,.0f}" if metadata['market_cap'] else "• Market Cap: N/A",
                f"• Sector: {metadata['sector']}" if metadata['sector'] else "• Sector: N/A",
                f"• Industry: {metadata['industry']}" if metadata['industry'] else "• Industry: N/A",
                "",
                "Price Range:",
                f"• High: ${max(p['High'] for p in prices):,.2f}",
                f"• Low: ${min(p['Low'] for p in prices):,.2f}",
                f"• Volume: {sum(p['Volume'] for p in prices):,.0f} shares traded"
            ]
            
            response_parts.append("\n".join(response))
        
        return "\n\n".join(response_parts)

    def _format_positions_response(self, positions: List[Dict]) -> str:
        """Format positions data into a user-friendly response"""
        if not positions:
            return "No positions found in the portfolio."

        response = ["📊 Current Portfolio Positions:\n"]
        total_value = sum(position['market_value'] for position in positions)

        # Sort positions by market value in descending order
        sorted_positions = sorted(positions, key=lambda x: x['market_value'], reverse=True)

        for position in sorted_positions:
            allocation = (position['market_value'] / total_value * 100) if total_value > 0 else 0
            pl_class = "profit" if position['unrealized_pl'] >= 0 else "loss"
            
            position_details = [
                f"🔸 {position['symbol']} ({allocation:.1f}% of portfolio)",
                f"   Quantity: {position['qty']} shares",
                f"   Market Value: ${position['market_value']:,.2f}",
                f"   P/L: ${position['unrealized_pl']:,.2f} ({position['unrealized_plpc']:.2f}%)",
                f"   Current Price: ${position['current_price']:,.2f}",
                f"   Avg Entry: ${position['avg_entry_price']:,.2f}\n"
            ]
            response.extend(position_details)

        response.append(f"\nTotal Portfolio Value: ${total_value:,.2f}")
        return "\n".join(response)

    def _format_performance_response(self, performance: Dict) -> str:
        """Format performance data into a user-friendly response"""
        if not performance or 'equity' not in performance:
            return "No performance data available."

        equity_values = [v for v in performance['equity'] if v is not None]
        if not equity_values:
            return "No valid performance data available."

        current_value = equity_values[-1]
        start_value = equity_values[0]
        total_return = ((current_value - start_value) / start_value * 100) if start_value > 0 else 0
        max_value = max(equity_values)
        min_value = min(equity_values)

        response = [
            "📈 Portfolio Performance Summary:\n",
            f"Current Value: ${current_value:,.2f}",
            f"Period Return: {total_return:+.2f}%",
            f"Period High: ${max_value:,.2f}",
            f"Period Low: ${min_value:,.2f}",
            "\nNote: Past performance does not guarantee future results."
        ]

        return "\n".join(response)
