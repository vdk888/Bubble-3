from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
import os
from dotenv import load_dotenv
from services.chatbot import ChatbotService
from services.portfolio import PortfolioService

# Load environment variables
load_dotenv()

# Validate required environment variables
required_env_vars = ['SECRET_KEY', 'OPENAI_API_KEY', 'ALPACA_API_KEY', 'ALPACA_SECRET_KEY']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Create database directory if it doesn't exist
db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database')
os.makedirs(db_dir, exist_ok=True)
db_path = os.path.join(db_dir, 'users.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Initialize services
chatbot = ChatbotService(os.getenv('OPENAI_API_KEY'))
portfolio = PortfolioService()

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    alpaca_api_key = db.Column(db.String(120), nullable=True)
    alpaca_secret_key = db.Column(db.String(120), nullable=True)

    def has_alpaca_credentials(self):
        return bool(self.alpaca_api_key and self.alpaca_secret_key)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('signup'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('signup'))
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get initial greeting
    initial_message = chatbot.get_greeting(current_user)
    return render_template('dashboard.html', initial_message=initial_message)

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    if request.method == 'GET':
        if not current_user.has_alpaca_credentials():
            return jsonify({
                'initial_message': 'Hello! I\'m your AI financial assistant. I notice you haven\'t set up your Alpaca trading account credentials yet. Would you like to set them up now? This will allow me to help you with: • Real-time portfolio tracking • Trade monitoring • Market analysis • Stock information'
            })
        else:
            return jsonify({
                'initial_message': 'Welcome back! I\'m ready to help you with your portfolio analysis and trading decisions. What would you like to know about?'
            })
    
    message = request.json.get('message', '')
    response = chatbot.process_message(message, current_user)
    
    if response.get('credentials_updated'):
        db.session.commit()
    
    return jsonify(response)

@app.route('/chat/clear', methods=['POST'])
@login_required
def clear_chat():
    chatbot.clear_history()
    return jsonify({"status": "success"})

@app.route('/api/portfolio/metrics')
@login_required
def portfolio_metrics():
    if not current_user.has_alpaca_credentials():
        return jsonify({'error': 'Alpaca credentials not configured'}), 400
    try:
        portfolio.initialize_with_credentials(current_user.alpaca_api_key, current_user.alpaca_secret_key)
        return jsonify(portfolio.get_portfolio_summary())
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/portfolio/allocation')
@login_required
def portfolio_allocation():
    if not current_user.has_alpaca_credentials():
        return jsonify({'error': 'Alpaca credentials not configured'}), 400
    try:
        portfolio.initialize_with_credentials(current_user.alpaca_api_key, current_user.alpaca_secret_key)
        return jsonify(portfolio.get_asset_allocation())
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/portfolio/performance')
@login_required
def portfolio_performance():
    if not current_user.has_alpaca_credentials():
        return jsonify({'error': 'Alpaca credentials not configured'}), 400
    try:
        portfolio.initialize_with_credentials(current_user.alpaca_api_key, current_user.alpaca_secret_key)
        return jsonify(portfolio.get_portfolio_history())
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/portfolio/trades')
@login_required
def portfolio_trades():
    if not current_user.has_alpaca_credentials():
        return jsonify({'error': 'Alpaca credentials not configured'}), 400
    try:
        portfolio.initialize_with_credentials(current_user.alpaca_api_key, current_user.alpaca_secret_key)
        trades = portfolio.get_recent_trades()
        return jsonify({'trades': trades})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/store_alpaca_credentials', methods=['POST'])
@login_required
def store_alpaca_credentials():
    try:
        data = request.get_json()
        api_key = data.get('alpaca_api_key')
        secret_key = data.get('alpaca_secret_key')
        
        if not api_key or not secret_key:
            return jsonify({'error': 'Missing API credentials'}), 400
        
        current_user.alpaca_api_key = api_key
        current_user.alpaca_secret_key = secret_key
        db.session.commit()
        
        return jsonify({'message': 'Credentials stored successfully'}), 200
        
    except Exception as e:
        app.logger.error(f"Error storing credentials: {str(e)}")
        return jsonify({'error': 'Failed to store credentials'}), 500

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        alpaca_api_key = request.form.get('alpaca_api_key')
        alpaca_secret_key = request.form.get('alpaca_secret_key')
        
        if alpaca_api_key and alpaca_secret_key:
            current_user.alpaca_api_key = alpaca_api_key
            current_user.alpaca_secret_key = alpaca_secret_key
            db.session.commit()
            flash('API credentials updated successfully')
            return redirect(url_for('settings'))
    
    return render_template('settings.html')

if __name__ == '__main__':
    # Create data directory if it doesn't exist
    db_dir = os.path.dirname(db_path)
    os.makedirs(db_dir, exist_ok=True)
    
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")
    
    app.run(debug=True)
