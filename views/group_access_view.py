from flask import request, jsonify
from sqlalchemy import exc
from app import app, db, logging
import models.auth_model as user_model
from models.group_model import Group
from models.group_access_model import GroupAccess
from services.common_service import access_from_group_access
import services.static_vars as s_vars
import services.auth_service as au_ser
from datetime import datetime


@app.route(s_vars.api_v1 + '/group_access/add/', methods=['POST'])
def add_group_access():
    data = request.json
    try:
        auth_status, auth_user = au_ser.check_auth_token(request.headers)
        group_from_db = Group.query.filter_by(group_id=data['group_id']).first()
        owner = group_from_db.owner
        access_by = auth_user
        if len(access_by) == 0:
            access_by = 'public'
        if owner == access_by or access_from_group_access(data['group_id'], access_by) == 'RW':

            username = data['username']
            username_in_db = user_model.User.query.filter_by(username=username, deactivated=False, verified=True).first()
            if username_in_db is None and username != 'public' or owner == username:
                return jsonify({'result': {username: False}})
            else:
                keys = list(data.keys())
                group_access = GroupAccess(
                    owner=owner,
                    username=username,
                    group_id=data['group_id'],
                    access_by=access_by,
                    access_type=data['access_type'] if 'access_type' in keys else 'RO'
                )
                db.session.add(group_access)
                try:
                    db.session.commit()
                    return jsonify({'result': {username: group_access.__repr__()}}), 200
                except exc.IntegrityError as e:
                    logging.info(e)
                    return jsonify({'result': {username: 'Already Exist'}}), 200
        else:
            return s_vars.not_authorized, 401
    except KeyError:
        return s_vars.bad_request, 400


@app.route(s_vars.api_v1 + '/group_access/action/', methods=['POST'])
def remove_change_group_access():
    data = request.json
    try:
        auth_status, auth_user = au_ser.check_auth_token(request.headers)
        group_from_db = Group.query.filter_by(group_id=data['group_id']).first()

        if group_from_db.owner == auth_user or access_from_group_access(group_from_db.card_id, auth_user) == 'RW':
            group_access = GroupAccess.query.filter_by(group_id=group_from_db.group_id, username=data['username']).first()
            if group_access is None:
                return jsonify(
                    {'result': '{} does not have access for group {}'.format(data['username'], group_from_db.title)}), 201
            msg = ''
            if data['action_name'] == 'delete':
                db.session.delete(group_access)
                msg = 'Deleted {} access from group {}'.format(data['username'], group_from_db.title)
            elif data['action_name'] == 'enable':
                group_access.access_status = True
                group_access.last_updated = datetime.utcnow()
                msg = 'Update: {} access from disable to enable'.format(data['username'])
            elif data['action_name'] == 'disable':
                group_access.access_status = False
                group_access.last_updated = datetime.utcnow()
                msg = 'Update: {} access from enable to disable'.format(data['username'])
            elif data['action_name'] == 'access_RO':
                group_access.access_type = 'RO'
                group_access.last_updated = datetime.utcnow()
                msg = 'Update: {} access from RW to RO'.format(data['username'])
            elif data['action_name'] == 'access_RW':
                group_access.access_type = 'RW'
                group_access.last_updated = datetime.utcnow()
                msg = 'Update: {} access from RO to RW'.format(data['username'])
            else:
                return s_vars.invalid_action, 403
            db.session.commit()
            return jsonify({'result': msg}), 200
        else:
            return s_vars.not_authorized, 401
    except KeyError:
        return s_vars.bad_request, 400