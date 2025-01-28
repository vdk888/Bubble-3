from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
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
