from flask import request, jsonify
from sqlalchemy import exc
from app import app, db
import models.auth_model as user_model
from models.card_model import Card
from models.card_access_model import CardAccess
from models.group_model import Group
from models.group_access_model import GroupAccess
from models.group_cards import GroupCards
from services.common_service import access_from_card_access, change_group_activation, delete_group, \
    access_from_group_access
from datetime import datetime
import services.static_vars as s_vars
import services.auth_service as au_ser
from services.generators import id_gen
from services.email_service import send_mail
import smtplib
import socket


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
        except socket.gaierror:
            return s_vars.mail_sending_failed, 502
        return jsonify({'result': result}), 200
    except KeyError:
        return s_vars.bad_request, 400
    except exc.IntegrityError:
        return jsonify({'result': 'Duplicate record'}), 409


@app.route(s_vars.api_v1 + '/group/id/', methods=['POST'])
def get_group_data(group_ids=None):
    data = request.json
    try:
        if group_ids is None:
            group_ids = data['group_ids']
        result = {}
        auth_status, auth_user = au_ser.check_auth_token(request.headers)
        if auth_user == '':
            return s_vars.not_authorized, 401
        for group_id in group_ids:
            user_has_access = False
            user_access_type = 'RO'
            group = Group.query.filter_by(group_id=group_id, owner=auth_user).first()
            if group is None:
                group_access = GroupAccess.query.filter_by(group_id=group_id, username=auth_user,
                                                           access_status=True).first()
                if group_access is not None:
                    user_access_type = group_access.access_type
                    user_has_access = True
            else:
                user_has_access = True
                user_access_type = 'RW'

            if user_has_access:
                group = Group.query.filter_by(group_id=group_id).first()
                card_ids = [gc.card_id for gc in GroupCards.query.filter_by(group_id=group_id).all()]
                cards = [card.__repr__() for card in Card.query.filter(Card.card_id.in_(card_ids)).all()]
                for card in cards:
                    if user_access_type == 'RW' or access_from_card_access(card['card_id'], auth_user) == 'RW':
                        card['access_type'] = 'RW'
                    else:
                        card['access_type'] = 'RO'
                    card['user_access_list'] = [card_a.__repr__() for card_a in
                                                CardAccess.query.filter(
                                                    CardAccess.card_id == card['card_id']).all()]
                result[group_id] = {}
                result[group_id]['card_list'] = cards
                group_json = group.__repr__()
                group_json['access_type'] = user_access_type
                group_json['user_access_list'] = [group_a.__repr__() for group_a in
                                                  GroupAccess.query.filter(
                                                      GroupAccess.group_id == group.group_id).all()]
                result[group_id]['group_details'] = group_json
                return jsonify({'result': result}), 200
            else:
                return s_vars.not_authorized, 401
    except KeyError:
        return s_vars.bad_request, 400


@app.route(s_vars.api_v1 + '/group/action/<group_action>', methods=['POST'])
def perform_group_action(group_action):
    data = request.json
    try:
        group_id = data['group_id']
        auth_status, auth_user = au_ser.check_auth_token(request.headers)
        if auth_user == '':
            return s_vars.not_authorized, 401
        else:
            group = Group.query.filter_by(group_id=group_id).first()
            if group is None:
                return s_vars.group_not_exist, 404
            else:
                if group.owner == auth_user or access_from_group_access(group_id, auth_user):
                    msg = ''
                    if group_action == 'deactivate':
                        change_group_activation(group_id, False)
                        msg = '{} deactivated'.format(group_id)
                    elif group_action == 'activate':
                        change_group_activation(group_id, True)
                        msg = '{} activated'.format(group_id)
                    elif group_action == 'delete':
                        delete_group(group_id)
                        msg = '{} activated'.format(group_id)
                    else:
                        return s_vars.invalid_action, 403
                    return jsonify({'result': msg})
                else:
                    return s_vars.not_authorized, 401
    except KeyError:
        return s_vars.bad_request, 400


@app.route(s_vars.api_v1 + '/group/remove_cards_from_group/', methods=['POST'])
def remove_cards_from_group():
    data = request.json
    try:
        auth_status, auth_user = au_ser.check_auth_token(request.headers)
        if auth_user == '':
            return s_vars.not_authorized, 401
        else:
            group = Group.query.filter_by(group_id=data['group_id']).first()
            if group is None:
                return s_vars.group_not_exist, 404
            else:
                if group.owner == auth_user or access_from_group_access(data['group_id'], auth_user):
                    GroupCards.query.filter(GroupCards.card_id.in_(data['card_ids'])).filter_by(
                        group_id=data['group_id']).delete(synchronize_session='fetch')
                    db.session.commit()
                    return jsonify({'result': '{} deleted from group {}'.format(data['card_ids'], data['group_id'])})
                else:
                    return s_vars.not_authorized, 401
    except KeyError:
        return s_vars.bad_request, 400


@app.route(s_vars.api_v1 + '/group/update/<group_id>', methods=['POST'])
def update_group(group_id):
    data = request.json
    auth_status, auth_user = au_ser.check_auth_token(request.headers)
    try:
        group_from_db = Group.query.filter_by(group_id=group_id).first()
        if group_from_db is None:
            return s_vars.group_not_exist, 404
        elif auth_user == '':
            return s_vars.not_authorized, 401
        elif group_from_db.owner == auth_user or access_from_group_access(group_id, auth_user) == 'RW':
            keys = list(data.keys())
            if 'owner' in keys:
                if data['owner'] != 'public':
                    user = user_model.User.query.filter_by(username=data['owner']).first()
                    if user is not None:
                        group_from_db.owner = data['owner'] if 'owner' in keys else group_from_db.owner
                    else:
                        return s_vars.user_not_exist, 404
                else:
                    return s_vars.user_not_exist, 404
            group_from_db.title = data['title'] if 'title' in keys else group_from_db.title
            group_from_db.description = data['description'] if 'description' in keys else group_from_db.description
            group_from_db.icon_url = data['icon_url'] if 'icon_url' in keys else group_from_db.icon_url
            group_from_db.status = data['status'] if 'status' in keys else group_from_db.status

            group_from_db.last_updated = datetime.utcnow()
            db.session.commit()
            group_json_data = group_from_db.__repr__()
            group_json_data['user_access_list'] = [group_a.__repr__() for group_a in GroupAccess.query.filter(
                GroupAccess.group_id == group_from_db.group_id).all()]
            res = {'result': group_json_data}
            return jsonify(res), 200
        else:
            return s_vars.not_authorized, 401
    except KeyError:
        return s_vars.bad_request, 400
