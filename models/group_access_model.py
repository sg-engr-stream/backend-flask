from app import db
from datetime import datetime


class GroupAccess(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    owner = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.String(50), nullable=False)
    group_id = db.Column(db.String(20), nullable=False)
    access_by = db.Column(db.String(50), nullable=False)
    access_type = db.Column(db.String(20), default='RO')
    access_status = db.Column(db.Boolean, default=True)
    access_deleted = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
