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
                max_tokens=1500
            )

            bot_response = response.choices[0].message.content
            print(f"Initial bot response: {bot_response}")  # Debug log

            # Check if the response contains a tool command
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

    def _detect_price_data_request(self, message: str) -> Optional[Dict]:
        """Detect if the message is requesting price data"""
        # Pattern for price requests
        price_patterns = [
            r'(?i)(?:get|show|what(?:\'s)?|how?s? (?:is|are))?\s*(?:the)?\s*(?:price|prices|chart|data)\s+(?:for|of)?\s+([A-Za-z0-9,\s]+)',
            r'(?i)([A-Za-z0-9]+)\s+(?:price|chart|data)',
            r'(?i)how\s+is\s+([A-Za-z0-9]+)\s+(?:doing|performing)',
        ]
        
        # Pattern for timeframes
        timeframe_patterns = {
            r'(?i)last\s+(\d+)\s*(day|week|month|year)s?': lambda m: f"{m.group(1)}{m.group(2)[0]}",
            r'(?i)(today|daily)': lambda m: "1d",
            r'(?i)(week|weekly)': lambda m: "1wk",
            r'(?i)(month|monthly)': lambda m: "1mo",
            r'(?i)(year|yearly)': lambda m: "1y",
        }
        
        # Check for price request
        symbols = None
        for pattern in price_patterns:
            match = re.search(pattern, message)
            if match:
                symbols = [s.strip().upper() for s in match.group(1).split(',')]
                break
        
        if not symbols:
            return None
        
        # Check for timeframe
        timeframe = "1mo"  # default
        for pattern, timeframe_func in timeframe_patterns.items():
            match = re.search(pattern, message)
            if match:
                timeframe = timeframe_func(match)
                break
            
        return {
            'symbols': symbols,
            'timeframe': timeframe
        }

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

        for position in positions:
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
