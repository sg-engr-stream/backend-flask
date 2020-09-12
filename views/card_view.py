from flask import request, jsonify
from sqlalchemy import exc
from app import app, db, logging
import models.auth_model as user_model
from models.card_model import Card
from services.common_service import access_from_card_access, change_card_activation, delete_card, check_expiry_and_return
from datetime import datetime
from dateutil import parser
import services.static_vars as s_vars
import services.auth_service as au_ser
from services.generators import id_gen
from services.email_service import send_mail


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
                short_url=data['host'] + '/' + short_url,
                redirect_url=data['redirect_url'],
                expiry=parser.parse(data['expiry']) if 'expiry' in keys else None,
            )
            db.session.add(card)
            db.session.commit()
            res = card.__repr__()
            if owner != 'public':
                send_mail(user.email, 'ShortUrl - Create Request', '''Hi {0},
                You have created new shorturl with below details:
                Owner: {0},
                Title: {1},
                Description: {2},
                ShortUrl: {3},
                RedirectUrl: {4},
                Expiry: {5}
                '''.format(res['owner'], res['title'], res['description'], res['short_url'], res['redirect_url'], res['expiry']))
            db.session.expunge(card)
            db.session.close()
        except KeyError:
            return s_vars.bad_request, 400
        except exc.IntegrityError:
            return s_vars.duplicate_record, 409
        return jsonify(res), 200


@app.route(s_vars.api_v1 + '/card/id/<card_id>', methods=['GET'])
def get_card(card_id):
    auth_status, auth_user = au_ser.check_auth_token(request.headers)
    card_from_db = Card.query.filter_by(card_id=card_id).first()
    if card_from_db is None:
        return s_vars.card_not_exist, 404
    else:
        if auth_user == card_from_db.owner or card_from_db.owner == 'public' or access_from_card_access(card_id, auth_user) != '':
            return jsonify(card_from_db.__repr__()), 200
        else:
            return s_vars.not_authorized, 401


@app.route(s_vars.api_v1 + '/card/available/<short_url>', methods=['GET'])
def get_availability_su(short_url):
    """Get short url availability from db"""
    card_from_db = Card.query.filter_by(short_url=short_url).first()
    if card_from_db is None:
        return s_vars.short_url_available, 200
    else:
        return s_vars.short_url_not_available, 409


@app.route(s_vars.api_v1 + '/card/action/<type>/', methods=['POST'])
def action_for_card(action_type):
    data = request.json
    if 'card_id' not in list(data.keys()):
        return s_vars.bad_request, 400
    if 'username' in list(data.keys()):
        owner = data['username']
    else:
        owner = 'public'
    auth_status, auth_user = au_ser.check_auth_token(request.headers)
    try:
        card_from_db = Card.query.filter_by(card_id=data['card_id']).first()
    except KeyError:
        return s_vars.bad_request, 400
    if card_from_db is None:
        return s_vars.card_not_exist, 404
    elif auth_user == owner or card_from_db.owner == 'public' or access_from_card_access(data['card_id'], auth_user) == 'RW':
        msg_str = ''
        if action_type == 'deactivate':
            change_card_activation(card_from_db.card_id, False)
            msg_str = 'deactivated'
        elif action_type == 'activate':
            change_card_activation(card_from_db.card_id, True)
            msg_str = 'activated'
        elif action_type == 'delete':
            delete_card(card_from_db.card_id)
            msg_str = 'deleted'
        else:
            return s_vars.action_not_available, 404
        card_from_db.last_updated = datetime.utcnow()
        db.session.commit()
        res = {'result': card_from_db.__repr__()}
        return jsonify(res), 200
    else:
        return s_vars.not_authorized, 401


@app.route(s_vars.api_v1 + '/card/update/<card_id>/', methods=['POST'])
def update_card(card_id):
    data = request.json
    if 'username' in list(data.keys()):
        owner = data['username']
    else:
        owner = 'public'
    auth_status, auth_user = au_ser.check_auth_token(request.headers)
    try:
        card_from_db = Card.query.filter_by(card_id=card_id).first()
    except KeyError:
        return s_vars.bad_request, 400
    if card_from_db is None:
        return s_vars.card_not_exist, 404
    elif auth_user == owner or card_from_db.owner == 'public' or access_from_card_access(card_id, auth_user) == 'RW':
        keys = list(data.keys())
        if card_from_db.owner == 'public' and card_from_db.created_by != owner and 'owner' in keys:
            return s_vars.cannot_change_owner, 403
        card_from_db.owner = data['owner'] if 'owner' in keys else card_from_db.owner
        card_from_db.title = data['title'] if 'title' in keys else card_from_db.title
        card_from_db.description = data['description'] if 'description' in keys else card_from_db.description
        card_from_db.icon_url = data['icon_url'] if 'icon_url' in keys else card_from_db.icon_url
        card_from_db.short_url = data['short_url'] if 'short_url' in keys else card_from_db.short_url
        card_from_db.redirect_url = data['redirect_url'] if 'redirect_url' in keys else card_from_db.redirect_url
        card_from_db.expiry = parser.parse(data['expiry']) if 'expiry' in keys else card_from_db.expiry
        card_from_db.last_updated = datetime.utcnow()
        db.session.commit()
        res = {'result': card_from_db.__repr__()}
        return jsonify(res), 200
    else:
        return s_vars.not_authorized, 401


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
            read_card_access = [access_from_card_access(card_id=card_with_short_url.card_id, auth_user=user) for user in ['public', auth_user]]
            if 'RW' in read_card_access or 'RO' in read_card_access:
                return check_expiry_and_return(card_with_short_url.expiry, card_with_short_url.redirect_url)
            else:
                return s_vars.not_authorized, 401
