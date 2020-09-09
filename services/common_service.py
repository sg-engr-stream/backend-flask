from models.card_access_model import CardAccess
import models.auth_model as user_model
from models.card_model import Card
from models.group_model import Group
from models.group_cards import GroupCards
from models.group_access_model import GroupAccess
from datetime import datetime
from app import db


def access_from_card_access(card_id, auth_user):
    card_from_card_access = [CardAccess.query.filter_by(card_id=card_id, username=username,
                                                        access_status=True).first()
                             for username in ['public', auth_user]]
    res = ''
    for item in card_from_card_access:
        if item is not None:
            if item.access_type == 'RW':
                return 'RW'
            else:
                res = 'RO'
    return res


def change_user_activation(username, state):
    """state true means activate, false means deactivate"""
    user = user_model.User.query.filter_by(username=username).first()
    user.deactivated = not state
    Card.query.filter(Card.owner == username).update(
        {Card.status: state, Card.last_updated: datetime.utcnow()}, synchronize_session='fetch')
    CardAccess.query.filter(CardAccess.owner == username).update(
        {CardAccess.access_status: state, CardAccess.last_updated: datetime.utcnow()}, synchronize_session='fetch')
    Group.query.filter(Group.owner == username).update(
        {Group.status: state, Group.last_updated: datetime.utcnow()}, synchronize_session='fetch')
    GroupAccess.query.filter(GroupAccess.owner == username).update(
        {GroupAccess.access_status: state, GroupAccess.last_updated: datetime.utcnow()}, synchronize_session='fetch')

    db.session.commit()


def delete_user(username):
    user_model.User.query.filter(user_model.User.username == username).delete(synchronize_session='fetch')

    """Get cards to be deleted"""
    card_ids_to_delete = [row.card_id for row in Card.query.filter(Card.owner == username).all()]
    GroupCards.query.filter(GroupCards.card_id.in_(card_ids_to_delete)).delete(synchronize_session='fetch')
    Card.query.filter(Card.owner == username).delete(synchronize_session='fetch')
    CardAccess.query.filter(CardAccess.owner == username).delete(synchronize_session='fetch')
    CardAccess.query.filter(CardAccess.username == username).delete(synchronize_session='fetch')

    """Get groups to be deleted"""
    group_ids_to_delete = [row.group_id for row in Group.query.filter(Group.owner == username).all()]
    GroupCards.query.filter(GroupCards.group_id.in_(group_ids_to_delete)).delete(synchronize_session='fetch')
    Group.query.filter(Group.owner == username).delete(synchronize_session='fetch')
    GroupAccess.query.filter(GroupAccess.owner == username).delete(synchronize_session='fetch')
    GroupAccess.query.filter(GroupAccess.username == username).delete(synchronize_session='fetch')
    db.session.commit()


def change_group_activation(group_id, state):
    """state true means activate, false means deactivate"""
    Group.query.filter(Group.group_id == group_id).update(
        {Group.status: state, Group.last_updated: datetime.utcnow()}, synchronize_session='fetch')
    GroupAccess.query.filter(GroupAccess.group_id == group_id).update(
        {GroupAccess.access_status: state, GroupAccess.last_updated: datetime.utcnow()}, synchronize_session='fetch')

    db.session.commit()


def delete_group(group_id):
    GroupCards.query.filter(GroupCards.group_id == group_id).delete(synchronize_session='fetch')
    Group.query.filter(Group.group_id == group_id).delete(synchronize_session='fetch')
    GroupAccess.query.filter(GroupAccess.group_id == group_id).delete(synchronize_session='fetch')

    db.session.commit()


def change_card_activation(card_id, state):
    Card.query.filter(Card.card_id == card_id).update(
        {Card.status: state, Card.last_updated: datetime.utcnow()}, synchronize_session='fetch')
    db.session.commit()


def delete_card(card_id):
    Card.query.filter(Card.card_id == card_id).delete(synchronize_session='fetch')
    CardAccess.query.filter(CardAccess.card_id == card_id).delete(synchronize_session='fetch')
    GroupCards.query.filter(GroupCards.card_id == card_id).delete(synchronize_session='fetch')
    db.session.commit()
