from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
import os
from dotenv import load_dotenv
from services.chatbot import ChatbotService
from services.portfolio import PortfolioService
from routes import api
from models import db, User

# Load environment variables
load_dotenv()

# Validate required environment variables
required_env_vars = ['SECRET_KEY', 'OPENAI_API_KEY', 'ALPACA_API_KEY', 'ALPACA_SECRET_KEY']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')

# Create database directory if it doesn't exist
db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database')
os.makedirs(db_dir, exist_ok=True)
db_path = os.path.join(db_dir, 'users.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and migrations
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Register blueprints
app.register_blueprint(api, url_prefix='/api')

# Initialize chatbot service
chatbot = ChatbotService(os.getenv('OPENAI_API_KEY'))

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

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    try:
        message = request.json.get('message', '')
        response = chatbot.process_message(message, current_user)
        return jsonify(response)
    except Exception as e:
        app.logger.error(f"Chat error: {str(e)}")
        return jsonify({
            "response": "I apologize, but I encountered an error. Please try again.",
            "error": True
        }), 500

@app.route('/chat/clear', methods=['POST'])
@login_required
def clear_chat():
    chatbot.clear_history()
    return jsonify({"status": "success"})

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        alpaca_api_key = request.form.get('alpaca_api_key')
        alpaca_secret_key = request.form.get('alpaca_secret_key')
        
        if alpaca_api_key and alpaca_secret_key:
            try:
                # Test credentials by initializing portfolio service
                portfolio_service = PortfolioService()
                portfolio_service.initialize_with_credentials(alpaca_api_key, alpaca_secret_key)
                # This will throw an error if credentials are invalid
                portfolio_service.alpaca.get_account_info()
                
                # Save credentials if test was successful
                current_user.alpaca_api_key = alpaca_api_key
                current_user.alpaca_secret_key = alpaca_secret_key
                db.session.commit()
                
                flash('API credentials updated and validated successfully')
                return redirect(url_for('settings'))
            except Exception as e:
                app.logger.error(f"Error validating Alpaca credentials: {str(e)}")
                flash('Invalid API credentials. Please check and try again.')
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
