from flask import request, jsonify
from sqlalchemy import exc
from app import app, db, logging
import models.auth_model as user_model
from models.card_model import Card
from models.card_access_model import CardAccess
from services.common_service import access_from_card_access
import services.static_vars as s_vars
import services.auth_service as au_ser
from datetime import datetime


@app.route(s_vars.api_v1 + '/card_access/add/', methods=['POST'])
def add_card_access():
    data = request.json
    try:
        auth_status, auth_user = au_ser.check_auth_token(request.headers)
        card_from_db = Card.query.filter_by(card_id=data['card_id']).first()
        owner = card_from_db.owner
        access_by = auth_user
        if len(access_by) == 0:
            access_by = 'public'
        if owner == access_by or access_from_card_access(data['card_id'], access_by) == 'RW':
            resp = []
            if len(data['username']) > 0:
                for username in data['username']:
                    username_in_db = user_model.User.query.filter_by(username=username, deactivated=False, verified=True).first()
                    if username_in_db is None and username != 'public' or owner == username:
                        resp.append({username: False})
                    else:
                        keys = list(data.keys())
                        card_access = CardAccess(
                            owner=owner,
                            username=username,
                            card_id=data['card_id'],
                            access_by=access_by,
                            access_type=data['access_type'] if 'access_type' in keys else 'RO'
                        )
                        db.session.add(card_access)
                        try:
                            db.session.commit()
                            resp.append({username: True})
                        except exc.IntegrityError as e:
                            resp.append({username: False})
                            logging.info(e)
            return jsonify({'result': resp}), 200
        else:
            return s_vars.not_authorized, 401
    except KeyError:
        return s_vars.bad_request, 400


@app.route(s_vars.api_v1 + '/card_access/list/', methods=['POST'])
def get_list_by_access_type():
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
