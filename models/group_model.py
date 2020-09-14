from app import db
from datetime import datetime


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner = db.Column(db.String(50), nullable=False)
    group_id = db.Column(db.String(20), nullable=False)
    icon_url = db.Column(db.String(1000), nullable=True)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    status = db.Column(db.Boolean, default=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('owner', 'group_id', name='owner_group_unique'), {'extend_existing': True})

    def __repr__(self):
        """Return json object with group details"""
        return {
            'owner': self.owner,
            'group_id': self.group_id,
            'title': self.title,
            'description': self.description,
            'icon_url': self.icon_url,
            'status': self.status,
            'date_created': self.date_created.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }

