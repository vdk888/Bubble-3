from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user, login_required
from models import db, User

api = Blueprint('api', __name__)

@api.route('/store_alpaca_credentials', methods=['POST'])
@login_required
def store_alpaca_credentials():
    try:
        data = request.get_json()
        api_key = data.get('alpaca_api_key')
        secret_key = data.get('alpaca_secret_key')
        
        if not api_key or not secret_key:
            return jsonify({'error': 'Missing API credentials'}), 400
        
        current_user.save_alpaca_credentials(api_key, secret_key)
        return jsonify({'message': 'Credentials stored successfully'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Error storing credentials: {str(e)}")
        return jsonify({'error': 'Failed to store credentials'}), 500
