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
                            resp.append({username: 'Already Exist'})
                            logging.info(e)
            return jsonify({'result': resp}), 200
        else:
            return s_vars.not_authorized, 401
    except KeyError:
        return s_vars.bad_request, 400


@app.route(s_vars.api_v1 + '/card_access/action/', methods=['POST'])
def remove_card_access():
    data = request.json
    try:
        auth_status, auth_user = au_ser.check_auth_token(request.headers)
        card_from_db = Card.query.filter_by(card_id=data['card_id']).first()

        if card_from_db.owner == auth_user or access_from_card_access(card_from_db.card_id, auth_user) == 'RW':
            card_access = CardAccess.query.filter_by(card_id=card_from_db.card_id, username=data['username']).first()
            if card_access is None:
                return jsonify(
                    {'result': '{} does not have access for card {}'.format(data['username'], card_from_db.title)}), 201
            msg = ''
            if data['action_name'] == 'delete':
                db.session.delete(card_access)
                msg = 'Deleted {} access from card {}'.format(data['username'], card_from_db.title)
            elif data['action_name'] == 'enable':
                card_access.access_status = True
                card_access.last_updated = datetime.utcnow()
                msg = 'Update: {} access from disable to enable'.format(data['username'])
            elif data['action_name'] == 'disable':
                card_access.access_status = False
                card_access.last_updated = datetime.utcnow()
                msg = 'Update: {} access from enable to disable'.format(data['username'])
            elif data['action_name'] == 'access_RO':
                card_access.access_type = 'RO'
                card_access.last_updated = datetime.utcnow()
                msg = 'Update: {} access from RW to RO'.format(data['username'])
            elif data['action_name'] == 'access_RW':
                card_access.access_type = 'RW'
                card_access.last_updated = datetime.utcnow()
                msg = 'Update: {} access from RO to RW'.format(data['username'])
            else:
                return s_vars.invalid_action, 403
            db.session.commit()
            return jsonify({'result': msg}), 200
        else:
            return s_vars.not_authorized, 401
    except KeyError:
        return s_vars.bad_request, 400
