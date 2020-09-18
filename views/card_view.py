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
from views.group_view import get_group_data
import smtplib


@app.route(s_vars.api_v1 + '/card/add/', methods=['POST'])
def add_card():
    data = request.json
    auth_status, auth_user = au_ser.check_auth_token(request.headers)
    owner = auth_user
    if len(owner) == 0:
        return s_vars.not_authorized, 401
    else:
        try:
            user = None
            if owner != 'public':
                user = user_model.User.query.filter_by(username=owner, deactivated=False).first()
                if user is None:
                    return s_vars.user_not_exist, 401
                if not user.verified:
                    return s_vars.not_verified_user, 403
            short_url = data['short_url'] if 'short_url' in list(data.keys()) else id_gen(10)

            msg, resp_code = get_availability_su(short_url)
            if resp_code == 409:
                return msg, resp_code
            keys = list(data.keys())
            card = Card(
                created_by=owner,
                owner=owner,
                card_id=id_gen(),
                title=data['title'],
                description=data['description'],
                icon_url=data['icon_url'] if 'icon_url' in keys else None,
                short_url=short_url,
                redirect_url=data['redirect_url'],
                expiry=parser.parse(data['expiry']) if 'expiry' in keys else None,
            )
            db.session.add(card)
            db.session.commit()
            res = card.__repr__()
            if owner != 'public':
                send_mail(user.email, 'N4NITIN - Create Request', '''Hi {0},
                You have created new shorturl with below details:
                Owner: {0},
                Title: {1},
                Description: {2},
                ShortUrl: {3},
                RedirectUrl: {4},
                Expiry: {5}
                '''.format(res['owner'], res['title'], res['description'], request.origin if request.origin is not None else '' + '/' + short_url,
                           res['redirect_url'], res['expiry']))
            db.session.expunge(card)
            db.session.close()
        except KeyError:
            return s_vars.bad_request, 400
        except exc.IntegrityError:
            return s_vars.duplicate_record, 409
        except smtplib.SMTPException:
            return s_vars.mail_sending_failed, 501
        return jsonify(res), 200


@app.route(s_vars.api_v1 + '/card/id/', methods=['POST'])
def get_card():
    data = request.json
    if 'card_id' not in list(data.keys()):
        return s_vars.bad_request, 400
    auth_status, auth_user = au_ser.check_auth_token(request.headers)
    result_arr = []
    card_from_db = Card.query.filter(Card.card_id.in_(data['card_id'])).all()
    for card in card_from_db:
        acc = 'RW' if auth_user == card.owner else access_from_card_access(card.card_id, auth_user)
        if auth_user == card.owner or card.owner == 'public' or acc != '':
            user_access = [card_a.__repr__() for card_a in CardAccess.query.filter(CardAccess.card_id == card.card_id).all()]

            res = card.__repr__()
            res['access_type'] = acc
            res['user_access_list'] = user_access
            result_arr.append(res)

    if len(result_arr) > 0:
        return jsonify({'result': result_arr}), 200 if len(result_arr) == len(data['card_id']) else 200
    else:
        return s_vars.card_not_exist, 404


@app.route(s_vars.api_v1 + '/card/available/<short_url>', methods=['GET'])
def get_availability_su(short_url):
    """Get short url availability from db"""
    card_from_db = Card.query.filter_by(short_url=short_url).first()
    if card_from_db is None:
        return s_vars.short_url_available, 200
    else:
        return s_vars.short_url_not_available, 409


@app.route(s_vars.api_v1 + '/card/action/<action_type>', methods=['POST'])
def action_for_card(action_type):
    data = request.json
    if 'card_ids' not in list(data.keys()):
        return s_vars.bad_request, 400
    if 'username' in list(data.keys()):
        owner = data['username']
    else:
        owner = 'public'
    auth_status, auth_user = au_ser.check_auth_token(request.headers)
    try:
        card_from_db = Card.query.filter(Card.card_id.in_(data['card_ids'])).all()
    except KeyError:
        return s_vars.bad_request, 400
    if len(card_from_db) == 0:
        return s_vars.card_not_exist, 404
    else:
        result = {'result': []}
        for card in card_from_db:
            if auth_user == owner or card.owner == 'public' or access_from_card_access(card.card_id,
                                                                                                 auth_user) == 'RW':
                card_title = card.title
                if action_type == 'deactivate':
                    change_card_activation(card.card_id, False)
                    card.last_updated = datetime.utcnow()
                    result['result'].append(card.__repr__())
                elif action_type == 'activate':
                    change_card_activation(card.card_id, True)
                    card.last_updated = datetime.utcnow()
                    result['result'].append(card.__repr__())
                elif action_type == 'delete':
                    delete_card(card.card_id)
                    result['result'].append('Deleted : {}'.format(card_title))

                db.session.commit()
        return jsonify(result), 200


@app.route(s_vars.api_v1 + '/card/update/<card_id>', methods=['POST'])
def update_card(card_id):
    data = request.json
    auth_status, auth_user = au_ser.check_auth_token(request.headers)
    try:
        card_from_db = Card.query.filter_by(card_id=card_id).first()
        if card_from_db is None:
            return s_vars.card_not_exist, 404
        elif auth_user == '':
            return s_vars.not_authorized, 401
        elif card_from_db.owner == auth_user or card_from_db.owner == 'public' or access_from_card_access(card_id, auth_user) == 'RW':
            keys = list(data.keys())
            if card_from_db.owner == 'public' and card_from_db.created_by != auth_user and 'owner' in keys:
                return s_vars.cannot_change_owner, 403
            if 'owner' in keys:
                if data['owner'] != 'public':
                    user = user_model.User.query.filter_by(username=data['owner']).first()
                    if user is not None:
                        card_from_db.owner = data['owner'] if 'owner' in keys else card_from_db.owner
                    else:
                        return s_vars.user_not_exist, 404
                else:
                    card_from_db.owner = 'public'
            card_from_db.title = data['title'] if 'title' in keys else card_from_db.title
            card_from_db.description = data['description'] if 'description' in keys else card_from_db.description
            card_from_db.icon_url = data['icon_url'] if 'icon_url' in keys else card_from_db.icon_url
            card_from_db.short_url = data['short_url'] if 'short_url' in keys else card_from_db.short_url
            card_from_db.redirect_url = data['redirect_url'] if 'redirect_url' in keys else card_from_db.redirect_url
            card_from_db.expiry = parser.parse(data['expiry']) if 'expiry' in keys else card_from_db.expiry
            card_from_db.status = data['status'] if 'status' in keys else card_from_db.status

            card_from_db.last_updated = datetime.utcnow()
            db.session.commit()
            card_json_data = card_from_db.__repr__()
            card_json_data['user_access_list'] = [card_a.__repr__() for card_a in CardAccess.query.filter(CardAccess.card_id == card_from_db.card_id).all()]
            res = {'result': card_json_data}
            return jsonify(res), 200
        else:
            return s_vars.not_authorized, 401
    except KeyError:
        return s_vars.bad_request, 400


@app.route(s_vars.api_v1 + '/profile/get_data/', methods=['POST'])
def return_data_for_profile():
    data = request.json
    access_types = ['RO', 'RW']
    try:
        username = data['username']
        auth_status, auth_user = au_ser.check_auth_token(request.headers)
        if username != auth_user:
            return s_vars.not_authorized, 401
        result = {'owner': [], 'shared_with_me': [], 'cards_in_group': []}

        cards_owned = Card.query.filter(Card.owner == username).all()
        result['owner'] = [card.__repr__() for card in cards_owned]

        for card_details in result['owner']:
            card_details['user_access_list'] = [card_a.__repr__() for card_a in
                                CardAccess.query.filter(CardAccess.card_id == card_details['card_id']).all()]

        cards_shared_with_me = [[card.__repr__() for card in
                                 CardAccess.query.filter(CardAccess.username == username,
                                                         CardAccess.access_type == access_t).all()] for access_t in
                                access_types]
        for i in range(0, len(cards_shared_with_me)):
            card_ids_to_fetch = [card_access['card_id'] for card_access in cards_shared_with_me[i] if card_access['card_id'] not in result['owner']]
            cards = [card.__repr__() for card in Card.query.filter(
                Card.card_id.in_(card_ids_to_fetch)).all()]
            for card in cards:
                card['access_type'] = access_types[i]
                card['user_access_list'] = [card_a.__repr__() for card_a in
                                                    CardAccess.query.filter(
                                                        CardAccess.card_id == card['card_id']).all()]
                result['shared_with_me'].append(card)

        groups_owned = [group.__repr__() for group in Group.query.filter(Group.owner == username).all()]
        for group in groups_owned:
            group['access_type'] = 'RW'
            group['user_access_list'] = [group_a.__repr__() for group_a in
                                        GroupAccess.query.filter(
                                            GroupAccess.group_id == group['group_id']).all()]
        groups_owned_ids = [g['group_id'] for g in groups_owned]

        groups_shared_with_me = [group_a.__repr__() for group_a in
                                 GroupAccess.query.filter(GroupAccess.username == username).all()]

        group_ids_to_fetch = [group_access['group_id'] for group_access in groups_shared_with_me if group_access['group_id'] not in groups_owned_ids]
        access_type_for_group = {}
        for group_access in groups_shared_with_me:
            if group_access['group_id'] not in groups_owned_ids:
                access_type_for_group[group_access['group_id']] = group_access['access_type']
        groups = [group.__repr__() for group in Group.query.filter(
            Group.group_id.in_(group_ids_to_fetch)).all()]
        for group in groups:
            group['access_type'] = access_type_for_group[group['group_id']]
            group['user_access_list'] = [group_a.__repr__() for group_a in
                                         GroupAccess.query.filter(
                                             GroupAccess.group_id == group['group_id']).all()]

        cards_in_group, st = get_group_data(groups_owned_ids + groups)
        result['cards_in_group'] = cards_in_group.json['result']
        return jsonify({'result': result})
    except KeyError:
        return s_vars.bad_request, 400


@app.route(s_vars.api_v1 + '/short_url/<short_url>/', methods=['GET'])
def return_redirect_url(short_url):
    auth_status, auth_user = au_ser.check_auth_token(request.headers)
    if auth_user == '':
        auth_user = 'public'
    card_with_short_url = Card.query.filter_by(short_url=short_url, status=True).first()
    if card_with_short_url is None:
        return jsonify({'result': 'failure'}), 404
    else:
        if auth_user == card_with_short_url.owner or card_with_short_url.owner == 'public':
            return check_expiry_and_return(card_with_short_url.expiry, card_with_short_url.redirect_url)
        else:
            read_card_access = [access_from_card_access(card_id=card_with_short_url.card_id, auth_user=user) for user in
                                ['public', auth_user]]
            if 'RW' in read_card_access or 'RO' in read_card_access:
                return check_expiry_and_return(card_with_short_url.expiry, card_with_short_url.redirect_url)
            else:
                return s_vars.not_authorized, 401


@app.route(s_vars.api_v1 + '/card/valid_list/', methods=['POST'])
def get_list_of_valid_cards_owned():
    data = request.json
    try:
        auth_status, auth_user = au_ser.check_auth_token(request.headers)
        cards_owned = []
        if auth_user == data['username']:
            cards_owned = Card.query.filter_by(owner=auth_user).all()
            cards_owned = [card.__repr__() for card in cards_owned if card.expiry is None or card.expiry > datetime.utcnow()]
        return jsonify({'result': cards_owned}), 200
    except KeyError:
        return s_vars.bad_request, 400


@app.route(s_vars.api_v1 + '/card/add_to_group/', methods=['POST'])
def add_card_to_existing_group():
    data = request.json
    try:
        auth_status, auth_user = au_ser.check_auth_token(request.headers)
        if auth_user == '':
            auth_user = 'public'
        cards_from_db = list(set([card.card_id for card in Card.query.filter(Card.card_id.in_(data['card_ids'])).all()]))
        group = Group.query.filter_by(group_id=data['group_id']).first()
        if group is None:
            return s_vars.group_not_exist, 404
        else:
            result = {'result': []}
            for card_id in cards_from_db:
                group_card = GroupCards(group_id=group.group_id, card_id=card_id)
                try:
                    db.session.add(group_card)
                    db.session.commit()
                    result['result'].append({card_id: 'Added in group: ' + group.group_id})
                except exc.IntegrityError:
                    result['result'].append({card_id: 'Already exist'})
            return jsonify(result), 200
    except KeyError:
        return s_vars.bad_request, 400