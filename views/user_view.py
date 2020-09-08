from flask import request, jsonify
from sqlalchemy import exc
from app import app, db, logging
from models.auth_model import User
from datetime import datetime
import services.static_vars as s_vars
import services.auth_service as au_ser
from services.generators import code_gen
from services.email_service import send_mail


@app.route(s_vars.api_v1 + '/user/add/', methods=['POST'])
def add_user():
    data = request.json
    if data['username'] == 'public':
        return s_vars.cannot_create_user, 403
    verification_code = code_gen()
    try:
        new_user = User(
            name=data['name'],
            username=data['username'],
            email=data['email'],
            verification_code=verification_code
        )
        new_user.set_password(data['secret'])
        new_user.set_verification_expiry()
        db.session.add(new_user)
        db.session.commit()
        res = {'response': 'user: {} has been created'.format(new_user.username)}
        send_mail(data['email'], 'Welcome to ShortUrl', 'Verification Code: {}'.format(verification_code))
        db.session.expunge(new_user)
        db.session.close()
    except KeyError:
        return s_vars.bad_request, 400
    except exc.IntegrityError as e:
        logging.error(e)
        return s_vars.user_already_exist, 409
    return res, 200


@app.route(s_vars.api_v1 + '/user/id/<user_id>', methods=['GET'])
def get_user_by_username(user_id):
    user = User.query.filter_by(username=user_id).scalar()
    auth_status, auth_user = au_ser.check_auth_token(request.headers)
    if auth_user == user_id:
        if user is not None:
            return jsonify({'username': user.username, 'name': user.name,
                            'email': user.email, 'verified': user.verified}), 200
        else:
            return s_vars.user_not_exist, 404
    else:
        return s_vars.not_authorized, 401


@app.route(s_vars.api_v1 + '/user/available/<user_id>', methods=['GET'])
def get_availability_user(user_id):
    """Get username availability from db"""
    user_from_db = User.query.filter_by(username=user_id).first()
    if user_from_db is None:
        return s_vars.user_available, 200
    else:
        return s_vars.user_already_exist, 409


@app.route(s_vars.api_v1 + '/user/verify_status/<user_id>', methods=['GET'])
def get_user_verification(user_id):
    """Get user verification from db"""
    user_from_db = User.query.filter_by(username=user_id).first()
    if user_from_db is None:
        return s_vars.user_not_exist, 400
    else:
        auth_status, auth_user = au_ser.check_auth_token(request.headers)
        if auth_user == user_id:
            if auth_status:
                return s_vars.verified_user, 200
            else:
                return s_vars.not_verified_user, 403
        else:
            return s_vars.not_authorized, 401


@app.route(s_vars.api_v1 + '/user/update/<user_id>', methods=['POST'])
def update_user_by_username(user_id):
    data = request.json
    auth_status, auth_user = au_ser.check_auth_token(request.headers)
    if auth_user == user_id:
        update_user = User.query.filter_by(username=user_id).first()
        if update_user is not None:
            if update_user.verified:
                return s_vars.cannot_change_email, 403
            update_user.name = data['name'] if 'name' in list(data.keys()) else update_user.name
            update_user.email = data['email'] if 'email' in list(data.keys()) else update_user.email
            update_user.last_updated = datetime.utcnow()
            db.session.commit()
            res = {'username': update_user.username, 'name': update_user.name, 'email': update_user.email}
            return jsonify(res), 200
        else:
            return s_vars.user_not_exist, 404
    else:
        return s_vars.not_authorized, 401


@app.route(s_vars.api_v1 + '/user/update_pass/<user_id>', methods=['POST'])
def update_pass_by_username(user_id):
    data = request.json
    if 'secret' not in list(data.keys()):
        return s_vars.bad_request, 400
    auth_status, auth_user = au_ser.check_auth_token(request.headers)
    if auth_user == user_id:
        update_user = User.query.filter_by(username=user_id).first()
        if update_user is not None:
            update_user.set_password(data['secret'])
            update_user.last_updated = datetime.utcnow()
            db.session.commit()
            res = {'response': 'Password updated for user {}'.format(update_user.username)}
            return jsonify(res), 200
        else:
            return s_vars.user_not_exist, 404
    else:
        return s_vars.not_authorized, 401


@app.route(s_vars.api_v1 + '/user/action/<action_type>/', methods=['POST'])
def action_by_username(action_type):
    data = request.json
    if 'username' not in list(data.keys()):
        return s_vars.bad_request, 400
    auth_status, auth_user = au_ser.check_auth_token(request.headers)
    if auth_user == data['username']:
        update_user = User.query.filter_by(username=data['username']).first()
        if update_user is not None:
            msg_str = ''
            if action_type == 'deactivate':
                update_user.deactivated = True
                msg_str = ' deactivated'
            elif action_type == 'activate':
                update_user.deactivated = False
                msg_str = ' activated'
            elif action_type == 'delete':
                update_user.deactivated = True
                update_user.deleted = True
                msg_str = ' deleted'
            elif action_type == 'verify':
                try:
                    if update_user.verification_code == data['verification_code']:
                        update_user.verified = True
                        msg_str = ' verified'
                        send_mail(update_user.email, 'Account Verified at ShortUrl',
                                  'Hi, Your account has been verified')
                    else:
                        return s_vars.invalid_code, 401
                except KeyError:
                    return s_vars.bad_request, 400
            elif action_type == 'resend_verification':
                update_user.verification_code = code_gen()
                update_user.set_verification_expiry()
                send_mail(update_user.email, 'Welcome to ShortUrl', 'Verification Code: {}'.format(
                    update_user.verification_code
                ))
                msg_str = ', verification code resent.'
            else:
                return s_vars.action_not_available, 404
            update_user.last_updated = datetime.utcnow()
            db.session.commit()
            res = {'response': 'User {}{}'.format(update_user.username, msg_str)}
            return jsonify(res), 200
        else:
            return s_vars.user_not_exist, 404
    else:
        return s_vars.not_authorized, 401


@app.route(s_vars.api_v1 + '/user/login_check/<user_id>', methods=['POST'])
def check_if_can_login(user_id):
    data = request.json
    if 'secret' not in list(data.keys()):
        return s_vars.bad_request, 400
    auth_status, auth_user = au_ser.check_auth_token(request.headers)
    if auth_user == user_id:
        user = User.query.filter_by(username=user_id).first()
        if user is not None:
            if user.check_password(data['secret']):
                res = {'response': 'Can login'}
            else:
                res = {'response': 'Can\'t login'}
            return jsonify(res), 200
        else:
            return s_vars.user_not_exist, 404
    else:
        return s_vars.not_authorized, 401
