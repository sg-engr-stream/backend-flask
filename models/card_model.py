from app import db
from datetime import datetime


class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_by = db.Column(db.String(50), nullable=False)
    owner = db.Column(db.String(50), nullable=False)
    card_id = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    icon_url = db.Column(db.String(1000), default=None, nullable=True)
    short_url = db.Column(db.String(50), unique=True, nullable=False)
    redirect_url = db.Column(db.String(1000), nullable=False)
    expiry = db.Column(db.DateTime, default=None, nullable=True)
    status = db.Column(db.Boolean, default=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('owner', 'card_id', name='owner_card_unique'), {'extend_existing': True})

    def __repr__(self):
        """Return json object with card details"""
        return {
            'created_by': self.created_by,
            'owner': self.owner,
            'card_id': self.card_id,
            'title': self.title,
            'description': self.description,
            'icon_url': self.icon_url,
            'short_url': self.short_url,
            'redirect_url': self.redirect_url,
            'expiry': None if self.expiry is None else self.expiry.isoformat(),
            'status': self.status,
            'date_created': self.date_created.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }
