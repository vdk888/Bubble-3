from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    alpaca_api_key = db.Column(db.String(120), nullable=True)
    alpaca_secret_key = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'

    def save_alpaca_credentials(self, api_key, secret_key):
        self.alpaca_api_key = api_key
        self.alpaca_secret_key = secret_key
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def has_alpaca_credentials(self):
        return bool(self.alpaca_api_key and self.alpaca_secret_key)

    def get_stored_info(self):
        """Get all stored information for the user"""
        return UserInfo.query.filter_by(user_id=self.id).order_by(UserInfo.created_at.desc()).all()

class UserInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    info_type = db.Column(db.String(50), nullable=False)  # e.g., 'life_event', 'preference', 'goal'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Add relationship to User model
    user = db.relationship('User', backref=db.backref('important_info', lazy=True))

    def __repr__(self):
        return f'<UserInfo {self.info_type}: {self.content[:30]}...>'
