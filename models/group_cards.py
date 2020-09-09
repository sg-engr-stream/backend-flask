from app import db
from datetime import datetime


class GroupCards(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.String(20), nullable=False)
    card_id = db.Column(db.String(20), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('group_id', 'card_id', name='group_card_unique'), {'extend_existing': True})

    def __repr__(self):
        """Return json object with group_card details"""
        return {
            'group_id': self.group_id,
            'card_id': self.card_id,
            'date_created': self.date_created.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }
