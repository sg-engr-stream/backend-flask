from flask import request, jsonify
from sqlalchemy import exc
from app import app, db, logging
import models.auth_model as user_model
from models.card_model import Card
from models.card_access_model import CardAccess
from models.group_model import Group
from models.group_access_model import GroupAccess
from models.group_cards import GroupCards
from services.common_service import access_from_card_access, change_card_activation, delete_card, \
    check_expiry_and_return
from datetime import datetime
from dateutil import parser
import services.static_vars as s_vars
import services.auth_service as au_ser
from services.generators import id_gen
from services.email_service import send_mail
import smtplib


@app.route(s_vars.api_v1 + '/group/add/', methods=['POST'])
def add_group():
    data = request.json
    try:
        auth_status, auth_user = au_ser.check_auth_token(request.headers)
        owner = auth_user
        if owner != data['username']:
            return s_vars.not_authorized, 401
        cards = Card.query.filter(Card.card_id.in_(data['card_ids'])).all()
        if len(cards) < len(set(data['card_ids'])) or len(data['card_ids']) == 0:
            return s_vars.card_not_exist, 404
        group = Group(
            owner=owner,
            group_id=id_gen(),
            title=data['title'],
            description=data['description'],
            icon_url=data['icon_url'] if 'icon_url' in list(data.keys()) else None,
        )
        db.session.add(group)
        db.session.commit()
        result = {'group': group.__repr__(), 'cards_in_group': []}
        for card_id in list(set(data['card_ids'])):
            group_card = GroupCards(group_id=group.group_id, card_id=card_id)
            db.session.add(group_card)
            db.session.commit()
            result['cards_in_group'].append(group_card.__repr__())
        try:
            user = user_model.User.query.filter_by(username=owner).first()
            send_mail(user.email, 'Successfully Created Group', '''Hi {},
            Group \'{}\' has been successfully with below cards.
            
            {}'''.format(user.name, group.title, ', '.join([card.title for card in cards])))
        except smtplib.SMTPException:
            return s_vars.mail_sending_failed, 501
        return jsonify({'result': result}), 200
    except KeyError:
        return s_vars.bad_request, 400