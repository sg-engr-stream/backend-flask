from flask import request, jsonify
from sqlalchemy import exc
from app import app, db, logging
from models.auth_model import User
from models.card_model import Card
from datetime import datetime
from dateutil import parser
import services.static_vars as s_vars
import services.auth_service as au_ser
from services.generators import id_gen


@app.route(s_vars.api_v1 + '/card/add/', methods=['POST'])
def add_card():
    data = request.json
    auth_status, auth_user = au_ser.check_auth_token(request.headers)
    owner = auth_user
    if len(owner) == 0:
        return s_vars.not_authorized, 401
    else:
        try:
            if owner != 'public':
                user = User.query.filter_by(username=owner).first()
                if user is None:
                    return s_vars.user_not_exist, 401
            short_url = data['short_url'] if 'short_url' in list(data.keys()) else id_gen(10)
            msg, resp_code = get_availability_su(short_url)
            if resp_code == 409:
                return msg, resp_code
            keys = list(data.keys())
            card = Card(
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
            res = {
                'owner': card.owner,
                'title': card.title,
                'description': card.description,
                'card_id': card.card_id,
                'short_url': card.short_url
            }
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
        if auth_user == card_from_db.owner or card_from_db.owner == 'public':
            return jsonify({
                'owner': card_from_db.owner,
                'card_id': card_from_db.card_id,
                'title': card_from_db.title,
                'description': card_from_db.description,
                'icon_url': card_from_db.icon_url,
                'short_url': card_from_db.short_url,
                'redirect_url': card_from_db.redirect_url,
                'expiry': card_from_db.expiry,
                'status': card_from_db.status,
                'deleted': card_from_db.deleted
            }), 200
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
    elif auth_user == owner or card_from_db.owner == 'public':
        msg_str = ''
        if action_type == 'deactivate':
            card_from_db.status = True
            msg_str = 'deactivated'
        elif action_type == 'activate':
            card_from_db.status = False
            msg_str = 'activated'
        elif action_type == 'delete':
            card_from_db.status = True
            card_from_db.deleted = True
            msg_str = 'deleted'
        else:
            return s_vars.action_not_available, 404
        card_from_db.last_updated = datetime.utcnow()
        db.session.commit()
        res = {'response': 'Card \'{}\' {}'.format(card_from_db.title, msg_str)}
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
    elif auth_user == owner or card_from_db.owner == 'public':
        keys = list(data.keys())
        card_from_db.owner = data['owner'] if 'owner' in keys else card_from_db.owner
        card_from_db.title = data['title'] if 'title' in keys else card_from_db.title
        card_from_db.description = data['description'] if 'description' in keys else card_from_db.description
        card_from_db.icon_url = data['icon_url'] if 'icon_url' in keys else card_from_db.icon_url
        card_from_db.short_url = data['short_url'] if 'short_url' in keys else card_from_db.short_url
        card_from_db.redirect_url = data['redirect_url'] if 'redirect_url' in keys else card_from_db.redirect_url
        card_from_db.expiry = parser.parse(data['expiry']) if 'expiry' in keys else card_from_db.expiry
        card_from_db.last_updated = datetime.utcnow()
        db.session.commit()
        res = {'response': 'Card \'{}\' updated'.format(card_from_db.title)}
        return jsonify(res), 200
    else:
        return s_vars.not_authorized, 401