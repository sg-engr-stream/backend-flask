from app import db
from datetime import datetime


class Card(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    owner = db.Column(db.String(50), nullable=False)
    card_id = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    icon_url = db.Column(db.String(200), default=None, nullable=True)
    short_url = db.Column(db.String(50), unique=True, nullable=False)
    redirect_url = db.Column(db.String(500), nullable=False)
    expiry = db.Column(db.DateTime, default=None, nullable=True)
    status = db.Column(db.Boolean, default=False)
    deleted = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
