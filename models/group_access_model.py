from app import db
from datetime import datetime


class GroupAccess(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    group_id = db.Column(db.String(20), nullable=False)
    access_by = db.Column(db.String(50), nullable=False)
    access_type = db.Column(db.String(20), default='RO')
    access_status = db.Column(db.Boolean, default=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('username', 'group_id', name='group_with_user_unique'), {'extend_existing': True})

    def __repr__(self):
        """Return json object with group_access details"""
        return {
            'owner': self.owner,
            'username': self.username,
            'group_id': self.group_id,
            'access_by': self.access_by,
            'access_type': self.access_type,
            'access_status': self.access_status,
            'date_created': self.date_created.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }
