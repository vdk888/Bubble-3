from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user, login_required
from models import db, User
import alpaca_trade_api as tradeapi
from services.portfolio import PortfolioService
import re
from datetime import datetime, timedelta
import pytz
from dateutil.relativedelta import relativedelta
from services.chatbot import ChatbotService

api = Blueprint('api', __name__)

def get_portfolio_service():
    """Get initialized portfolio service with user credentials"""
    if not current_user.has_alpaca_credentials():
        return None
    
    try:
        portfolio_service = PortfolioService()
        portfolio_service.initialize_with_credentials(
            current_user.alpaca_api_key,
            current_user.alpaca_secret_key
        )
        return portfolio_service
    except Exception as e:
        current_app.logger.error(f"Error initializing portfolio service: {str(e)}")
        return None

@api.route('/store_alpaca_credentials', methods=['POST'])
@login_required
def store_alpaca_credentials():
    try:
        data = request.get_json()
        api_key = data.get('alpaca_api_key')
        secret_key = data.get('alpaca_secret_key')
        
        # Validate input
        if not api_key or not secret_key:
            current_app.logger.error('Missing API credentials')
            return jsonify({'error': 'Both API key and secret key are required'}), 400
            
        # Validate format
        if not re.match(r'^[A-Z0-9]{32}$', api_key) or not re.match(r'^[A-Z0-9]{64}$', secret_key):
            current_app.logger.error('Invalid credential format')
            return jsonify({'error': 'Invalid credential format. Please check your API key and secret key.'}), 400
            
        # Test the credentials
        try:
            portfolio_service = PortfolioService()
            portfolio_service.initialize_with_credentials(api_key, secret_key)
            account_info = portfolio_service.alpaca.get_account_info()
            
            if not account_info:
                raise ValueError('Could not retrieve account information')
                
            # Save credentials only after successful validation
            current_user.save_alpaca_credentials(api_key, secret_key)
            db.session.commit()
            
            # Format metrics from account info
            metrics = {
                'Buying Power': float(account_info['buying_power']),
                'Cash Available': float(account_info['cash']),
                'Daily Change': float(account_info['day_change_percent']),
                'Total Value': float(account_info['portfolio_value'])
            }
            
            current_app.logger.info('Credentials validated and stored successfully')
            
            return jsonify({
                'message': 'Credentials validated and stored successfully',
                'metrics': metrics
            }), 200
            
        except Exception as e:
            current_app.logger.error(f'Error validating credentials: {str(e)}')
            return jsonify({'error': 'Invalid credentials. Please check your API key and secret key.'}), 400
        
    except Exception as e:
        current_app.logger.error(f'Error in credential storage: {str(e)}')
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500

@api.route('/portfolio/metrics', methods=['GET'])
@login_required
def get_portfolio_metrics():
    try:
        current_app.logger.info('Getting portfolio metrics...')
        
        if not current_user.has_alpaca_credentials():
            current_app.logger.info('No Alpaca credentials found')
            return jsonify({'error': 'Alpaca API credentials not set'}), 401

        portfolio_service = PortfolioService()
        try:
            portfolio_service.initialize_with_credentials(
                current_user.alpaca_api_key,
                current_user.alpaca_secret_key
            )
        except Exception as e:
            current_app.logger.error(f'Error initializing portfolio service: {str(e)}')
            return jsonify({'error': 'Invalid credentials. Please check your Alpaca API key and secret key.'}), 401
        
        try:
            account_info = portfolio_service.alpaca.get_account_info()
            
            if not account_info:
                raise ValueError('Could not retrieve account information')
                
            metrics = {
                'Buying Power': float(account_info['buying_power']),
                'Cash Available': float(account_info['cash']),
                'Daily Change': float(account_info['day_change_percent']),
                'Total Value': float(account_info['portfolio_value'])
            }
            
            current_app.logger.info('Successfully retrieved portfolio metrics')
            return jsonify({'metrics': metrics}), 200
            
        except Exception as e:
            current_app.logger.error(f'Error getting account info: {str(e)}')
            return jsonify({'error': 'Failed to retrieve portfolio information'}), 500

    except Exception as e:
        current_app.logger.error(f'Error in get_portfolio_metrics: {str(e)}')
        return jsonify({'error': 'An unexpected error occurred'}), 500

@api.route('/portfolio/positions', methods=['GET'])
@login_required
def get_positions():
    try:
        portfolio_service = get_portfolio_service()
        if not portfolio_service:
            return jsonify({'error': 'Alpaca API credentials not set'}), 401

        # Get positions directly from alpaca service
        positions = portfolio_service.alpaca.get_positions()
        
        # Log positions data for debugging
        current_app.logger.info(f"Positions data: {positions}")
        
        return jsonify({'positions': positions}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting positions: {str(e)}")
        return jsonify({'error': 'Failed to get positions'}), 500

@api.route('/portfolio/orders', methods=['GET'])
@login_required
def get_orders():
    try:
        portfolio_service = get_portfolio_service()
        if not portfolio_service:
            return jsonify({'error': 'Alpaca API credentials not set'}), 401

        # Get recent trades using alpaca service directly
        trades = portfolio_service.alpaca.get_recent_trades(limit=10)
        
        # Format the trades for frontend display
        formatted_trades = []
        for trade in trades:
            formatted_trades.append({
                'symbol': trade['symbol'],
                'side': trade['side'],
                'type': trade['type'],
                'qty': trade['qty'],
                'status': trade['status'],
                'submitted_at': trade['submitted_at'].isoformat() if trade['submitted_at'] else None,
                'filled_at': trade['filled_at'].isoformat() if trade['filled_at'] else None,
                'filled_qty': trade['filled_qty'],
                'filled_avg_price': trade['filled_avg_price']
            })
        
        return jsonify({'orders': formatted_trades}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting orders: {str(e)}")
        return jsonify({'error': 'Failed to get orders'}), 500

@api.route('/portfolio/analysis', methods=['GET'])
@login_required
def get_analysis():
    try:
        portfolio_service = get_portfolio_service()
        if not portfolio_service:
            return jsonify({'error': 'Alpaca API credentials not set'}), 401

        symbol = request.args.get('symbol')
        if not symbol:
            return jsonify({'error': 'Symbol parameter is required'}), 400

        try:
            # Get latest quote
            quote = portfolio_service.alpaca.data_client.get_stock_latest_quote(symbol)
            current_price = float(quote.ask_price)

            # Get technical indicators
            analysis = {
                'symbol': symbol,
                'current_price': current_price,
                'indicators': {
                    'price': current_price,
                    'change_24h': quote.ask_price - quote.bid_price,
                    'volume': quote.ask_size,
                }
            }
            
            return jsonify(analysis), 200
            
        except Exception as e:
            current_app.logger.error(f"Error analyzing {symbol}: {str(e)}")
            return jsonify({'error': f'Failed to analyze {symbol}'}), 500

    except Exception as e:
        current_app.logger.error(f"Error in get_analysis: {str(e)}")
        return jsonify({'error': 'Failed to get analysis'}), 500

@api.route('/portfolio/trade', methods=['POST'])
@login_required
def place_trade():
    try:
        portfolio_service = get_portfolio_service()
        if not portfolio_service:
            return jsonify({'error': 'Alpaca API credentials not set'}), 401

        data = request.get_json()
        symbol = data.get('symbol')
        qty = data.get('qty')
        side = data.get('side')
        type = data.get('type')
        
        if not all([symbol, qty, side, type]):
            return jsonify({'error': 'Missing required trade parameters'}), 400

        # Create proper order request based on type
        order_params = {
            'symbol': symbol,
            'qty': float(qty),
            'side': side,
            'time_in_force': 'day'
        }

        if type.lower() == 'market':
            order_params['type'] = 'market'
        elif type.lower() == 'limit':
            limit_price = data.get('limit_price')
            if not limit_price:
                return jsonify({'error': 'Missing limit price for limit order'}), 400
            order_params['type'] = 'limit'
            order_params['limit_price'] = float(limit_price)
        elif type.lower() == 'stop':
            stop_price = data.get('stop_price')
            if not stop_price:
                return jsonify({'error': 'Missing stop price for stop order'}), 400
            order_params['type'] = 'stop'
            order_params['stop_price'] = float(stop_price)
        elif type.lower() == 'stop_limit':
            stop_price = data.get('stop_price')
            limit_price = data.get('limit_price')
            if not stop_price or not limit_price:
                return jsonify({'error': 'Missing stop price or limit price for stop limit order'}), 400
            order_params['type'] = 'stop_limit'
            order_params['stop_price'] = float(stop_price)
            order_params['limit_price'] = float(limit_price)
        else:
            return jsonify({'error': 'Unsupported order type'}), 400

        # Submit the order with the constructed parameters
        order = portfolio_service.alpaca.client.submit_order(**order_params)
        
        return jsonify({
            'message': 'Order placed successfully',
            'order_id': order.id
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error placing trade: {str(e)}")
        return jsonify({'error': 'Failed to place trade'}), 500

def get_timeframe_params(timeframe, period):
    """Helper function to calculate start and end dates based on timeframe and period"""
    end_date = datetime.now(pytz.UTC)
    
    if period == '1D':
        start_date = end_date - timedelta(days=1)
        bar_size = '5Min'
    elif period == '1W':
        start_date = end_date - timedelta(weeks=1)
        bar_size = '1H'
    elif period == '1M':
        start_date = end_date - relativedelta(months=1)
        bar_size = '1H'
    elif period == '3M':
        start_date = end_date - relativedelta(months=3)
        bar_size = '1H'
    elif period == '1Y':
        start_date = end_date - relativedelta(years=1)
        bar_size = '1D'
    elif period == 'ALL':
        start_date = end_date - relativedelta(years=5)  # Default to 5 years for ALL
        bar_size = '1D'
    else:
        start_date = end_date - timedelta(days=1)
        bar_size = '5Min'
    
    return start_date, end_date, bar_size

@api.route('/portfolio/history', methods=['GET'])
@login_required
def get_portfolio_history():
    try:
        portfolio_service = get_portfolio_service()
        if not portfolio_service:
            return jsonify({'error': 'Alpaca API credentials not set'}), 401

        # Get timeframe from query (this will be the button value: '1D', '1W', etc.)
        timeframe = request.args.get('timeframe', '1D')

        try:
            # Get history using the timeframe directly
            history = portfolio_service.alpaca.get_portfolio_history(timeframe=timeframe)

            if not history or 'timestamp' not in history or 'equity' not in history:
                return jsonify({'error': 'No portfolio history data available'}), 404

            # Format response data
            response_data = {
                'timestamp': history['timestamp'],
                'equity': history['equity'],
                'profit_loss_pct': history.get('profit_loss_pct', []),
                'timeframe': history.get('timeframe'),
                'period': timeframe  # Use the original timeframe button value
            }

            if 'base_value' in history:
                response_data['base_value'] = history['base_value']
            if 'base_value_asof' in history:
                response_data['base_value_asof'] = history['base_value_asof']

            current_app.logger.info(f"Successfully retrieved portfolio history for timeframe: {timeframe}")
            return jsonify(response_data), 200

        except Exception as e:
            current_app.logger.error(f"Error retrieving portfolio history from Alpaca: {str(e)}")
            return jsonify({
                'error': 'Failed to retrieve portfolio history',
                'details': str(e)
            }), 500

    except Exception as e:
        current_app.logger.error(f"Error in get_portfolio_history: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@api.route('/chat/analyze_performance', methods=['GET'])
@login_required
def analyze_performance():
    try:
        portfolio_service = get_portfolio_service()
        if not portfolio_service:
            return jsonify({'error': 'Alpaca API credentials not set'}), 401

        chatbot.initialize_portfolio_service(
            current_user.alpaca_api_key,
            current_user.alpaca_secret_key
        )
        
        analysis = chatbot.analyze_portfolio_performance()
        return jsonify({'analysis': analysis}), 200

    except Exception as e:
        current_app.logger.error(f"Error analyzing performance: {str(e)}")
        return jsonify({'error': 'Failed to analyze performance'}), 500

@api.route('/portfolio/performance', methods=['POST'])
@login_required
def analyze_portfolio_performance():
    """Analyze portfolio performance with progress updates"""
    try:
        portfolio_service = get_portfolio_service()
        if not portfolio_service:
            return jsonify({'error': 'Alpaca API credentials not set'}), 401

        # Initialize chatbot with portfolio service
        chatbot = ChatbotService(current_app.config['OPENAI_API_KEY'])
        chatbot.initialize_portfolio_service(
            current_user.alpaca_api_key,
            current_user.alpaca_secret_key
        )
        
        # Get the analysis with progress updates
        response_data = chatbot.analyze_portfolio_performance()
        
        # If there's an attachment, encode it as base64
        if response_data.get('has_attachment') and response_data.get('attachment'):
            import base64
            attachment = response_data['attachment']
            if isinstance(attachment.get('data'), bytes):
                attachment['data'] = base64.b64encode(attachment['data']).decode('utf-8')
            current_app.logger.info('Attachment data encoded successfully')
        else:
            current_app.logger.warning('No attachment data found in response')
        
        return jsonify(response_data)

    except Exception as e:
        current_app.logger.error(f"Error analyzing performance: {str(e)}")
        return jsonify({
            'error': 'Failed to analyze performance',
            'details': str(e)
        }), 500

@api.route('/chat', methods=['POST'])
@login_required
def chat():
    """Handle chat messages and tool responses"""
    try:
        data = request.get_json()
        message = data.get('message')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400

        # Initialize chatbot with OpenAI key
        chatbot = ChatbotService(current_app.config['OPENAI_API_KEY'])
        
        # If user has Alpaca credentials, initialize portfolio service
        if current_user.has_alpaca_credentials():
            chatbot.initialize_portfolio_service(
                current_user.alpaca_api_key,
                current_user.alpaca_secret_key
            )

        # Process the message
        response = chatbot.process_message(message, current_user)
        
        # Log the interaction for debugging
        current_app.logger.info(f"Chat request processed. Message: {message}")
        if response.get('error'):
            current_app.logger.error(f"Chat error: {response.get('error')}")
        
        return jsonify(response)

    except Exception as e:
        current_app.logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'error': 'An error occurred processing your message',
            'details': str(e)
        }), 500

@api.route('/user/important-info', methods=['GET'])
@login_required
def get_user_important_info():
    """Get all important information stored for the user"""
    try:
        info_items = current_user.get_stored_info()
        
        # Format the response
        formatted_info = [{
            'type': item.info_type,
            'content': item.content,
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat()
        } for item in info_items]
        
        current_app.logger.info(f"Retrieved {len(formatted_info)} important info items for user {current_user.id}")
        
        return jsonify({
            'success': True,
            'data': formatted_info
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error retrieving important info: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve important information'
        }), 500
