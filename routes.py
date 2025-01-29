from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user, login_required
from models import db, User
import alpaca_trade_api as tradeapi

api = Blueprint('api', __name__)

def get_alpaca_api():
    if not current_user.alpaca_api_key or not current_user.alpaca_secret_key:
        return None
    try:
        alpaca = tradeapi.REST(
            current_user.alpaca_api_key,
            current_user.alpaca_secret_key,
            'https://paper-api.alpaca.markets',
            api_version='v2'
        )
        # Test the connection
        alpaca.get_account()
        return alpaca
    except Exception as e:
        current_app.logger.error(f"Error connecting to Alpaca API: {str(e)}")
        return None

@api.route('/store_alpaca_credentials', methods=['POST'])
@login_required
def store_alpaca_credentials():
    try:
        data = request.get_json()
        api_key = data.get('alpaca_api_key')
        secret_key = data.get('alpaca_secret_key')
        
        if not api_key or not secret_key:
            return jsonify({'error': 'Missing API credentials'}), 400
            
        # Test the credentials before saving
        test_api = tradeapi.REST(
            api_key,
            secret_key,
            'https://paper-api.alpaca.markets',
            api_version='v2'
        )
        test_api.get_account()  # This will throw an error if credentials are invalid
        
        current_user.save_alpaca_credentials(api_key, secret_key)
        return jsonify({'message': 'Credentials stored successfully'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Error storing credentials: {str(e)}")
        return jsonify({'error': 'Failed to store credentials. Please check if they are valid.'}), 500

@api.route('/portfolio/metrics', methods=['GET'])
@login_required
def get_portfolio_metrics():
    try:
        api = get_alpaca_api()
        if not api:
            return jsonify({'error': 'Alpaca API credentials not set'}), 401

        account = api.get_account()
        metrics = {
            'Buying Power': f"${float(account.buying_power):.2f}",
            'Cash Available': f"${float(account.cash):.2f}",
            'Daily Change': f"{float(account.portfolio_value) - float(account.last_equity):.2f}%",
            'Total Value': f"${float(account.portfolio_value):.2f}"
        }
        
        return jsonify({'metrics': metrics}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting portfolio metrics: {str(e)}")
        return jsonify({'error': 'Failed to get portfolio metrics'}), 500

@api.route('/portfolio/positions', methods=['GET'])
@login_required
def get_positions():
    try:
        api = get_alpaca_api()
        if not api:
            return jsonify({'error': 'Alpaca API credentials not set'}), 401

        positions = api.list_positions()
        positions_data = [{
            'symbol': pos.symbol,
            'qty': pos.qty,
            'market_value': float(pos.market_value),
            'unrealized_pl': float(pos.unrealized_pl),
            'unrealized_plpc': float(pos.unrealized_plpc) * 100
        } for pos in positions]
        
        return jsonify({'positions': positions_data}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting positions: {str(e)}")
        return jsonify({'error': 'Failed to get positions'}), 500

@api.route('/portfolio/orders', methods=['GET'])
@login_required
def get_orders():
    try:
        api = get_alpaca_api()
        if not api:
            return jsonify({'error': 'Alpaca API credentials not set'}), 401

        orders = api.list_orders(status='all', limit=10)
        orders_data = [{
            'symbol': order.symbol,
            'side': order.side,
            'type': order.type,
            'qty': order.qty,
            'status': order.status,
            'submitted_at': order.submitted_at.isoformat()
        } for order in orders]
        
        return jsonify({'orders': orders_data}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting orders: {str(e)}")
        return jsonify({'error': 'Failed to get orders'}), 500

@api.route('/portfolio/trade', methods=['POST'])
@login_required
def place_trade():
    try:
        api = get_alpaca_api()
        if not api:
            return jsonify({'error': 'Alpaca API credentials not set'}), 401

        data = request.get_json()
        symbol = data.get('symbol')
        qty = data.get('qty')
        side = data.get('side')
        type = data.get('type')
        
        if not all([symbol, qty, side, type]):
            return jsonify({'error': 'Missing required trade parameters'}), 400

        order = api.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=type,
            time_in_force='day'
        )
        
        return jsonify({
            'message': 'Order placed successfully',
            'order_id': order.id
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error placing trade: {str(e)}")
        return jsonify({'error': 'Failed to place trade'}), 500
