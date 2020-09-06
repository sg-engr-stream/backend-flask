import app
from datetime import datetime


class GroupCards(app.db.Model):
    __table_args__ = {'extend_existing': True}
    id = app.db.Column(app.db.Integer, primary_key=True)
    group_id = app.db.Column(app.db.String(20), unique=False, nullable=False)
    card_id = app.db.Column(app.db.String(20), unique=False, nullable=False)
    date_created = app.db.Column(app.db.DateTime, default=datetime.utcnow)
    last_updated = app.db.Column(app.db.DateTime, default=datetime.utcnow)
