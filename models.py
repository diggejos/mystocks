# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime


# Initialize SQLAlchemy and Bcrypt here
db = SQLAlchemy()
bcrypt = Bcrypt()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    theme = db.Column(db.String(50), nullable=True)  # New field for storing the theme
    watchlists = db.relationship('Watchlist', backref='user', lazy=True)
    confirmed = db.Column(db.Boolean, default=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)


class Watchlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    stocks = db.Column(db.Text, nullable=False)  # JSON list of stock symbols
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_default = db.Column(db.Boolean, default=False)  # New field to mark as default
    
    # Define your StockKPI model
class StockKPI(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    pe_ratio = db.Column(db.Float)
    pb_ratio = db.Column(db.Float)
    beta = db.Column(db.Float)
    dividend_yield = db.Column(db.Float)
    market_cap = db.Column(db.Float)
    roe = db.Column(db.Float)
    debt_to_equity = db.Column(db.Float)
    price_momentum = db.Column(db.Float)
    risk_tolerance = db.Column(db.String(10), nullable=False)  # "low", "medium", or "high"
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    batch_id = db.Column(db.Integer, nullable=False)  # New field to track load batches
