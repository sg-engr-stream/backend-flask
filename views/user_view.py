from flask import request, jsonify
from sqlalchemy import exc
from app import app, db, logging
import models.auth_model as user_model
from datetime import datetime
import services.static_vars as s_vars
import services.auth_service as au_ser
from services.generators import code_gen, id_gen
from services.email_service import send_mail
from services.common_service import change_user_activation, delete_user
import smtplib


@app.route(s_vars.api_v1 + '/user/add/', methods=['POST'])
def add_user():
    data = request.json
    if data['username'] == 'public':
        return s_vars.cannot_create_user, 403
    verification_code = code_gen()
    try:
        new_user = user_model.User(
            name=data['name'],
            username=data['username'],
            email=data['email'],
            verification_code=verification_code
        )
        new_user.set_password(data['secret'])
        new_user.set_verification_expiry()
        db.session.add(new_user)
        db.session.commit()
        res = {'result': new_user.__repr__()}
        send_mail(data['email'], 'Welcome to ShortUrl', 'Verification Code: {}'.format(verification_code))
        db.session.expunge(new_user)
        db.session.close()
    except KeyError:
        return s_vars.bad_request, 400
    except exc.IntegrityError as e:
        logging.error(e)
        return s_vars.user_already_exist, 409
    except smtplib.SMTPException:
        return s_vars.mail_sending_failed, 501
    return res, 200


@app.route(s_vars.api_v1 + '/user/id/<username>', methods=['GET'])
def get_user_by_username(username):
    auth_status, auth_user = au_ser.check_auth_token(request.headers)
    if auth_user == username:
        user = user_model.User.query.filter_by(username=username).scalar()
        if user is not None:
            return jsonify({'result': user.__repr__()}), 200
        else:
            return s_vars.user_not_exist, 404
    else:
        return s_vars.not_authorized, 401


@app.route(s_vars.api_v1 + '/user/email_available/', methods=['POST'])
def get_email_avaialability():
    """Get username availability from db"""
    data = request.json
    try:
        user_from_db = user_model.User.query.filter_by(email=data['email']).first()
        if user_from_db is None:
            return s_vars.user_available, 200
        else:
            return s_vars.user_already_exist, 409
    except KeyError:
        return s_vars.bad_request, 400


@app.route(s_vars.api_v1 + '/user/available/<username>', methods=['GET'])
def get_availability_user(username):
    """Get username availability from db"""
    if username == 'public':
        return s_vars.cannot_create_user, 403

    user_from_db = user_model.User.query.filter_by(username=username).first()
    if user_from_db is None:
        return s_vars.user_available, 200
    else:
        return s_vars.user_already_exist, 409


@app.route(s_vars.api_v1 + '/user/verify_status/<username>', methods=['GET'])
def get_user_verification(username):
    """Get user verification from db"""
    user_from_db = user_model.User.query.filter_by(username=username).first()
    if user_from_db is None:
        return s_vars.user_not_exist, 400
    else:
        auth_status, auth_user = au_ser.check_auth_token(request.headers)
        if auth_user == username:
            if auth_status:
                return s_vars.verified_user, 200
            else:
                return s_vars.not_verified_user, 403
        else:
            return s_vars.not_authorized, 401


@app.route(s_vars.api_v1 + '/user/update/<username>', methods=['POST'])
def update_user_by_username(username):
    data = request.json
    auth_status, auth_user = au_ser.check_auth_token(request.headers)
    try:
        if auth_user == username:
            update_user = user_model.User.query.filter_by(username=username).first()
            if update_user is not None:
                keys = list(data.keys())
                if update_user.verified and 'email' in keys:
                    return s_vars.cannot_change_email, 403
                update_user.name = data['name'] if 'name' in keys else update_user.name
                update_user.email = data['email'] if 'email' in keys else update_user.email
                update_user.last_updated = datetime.utcnow()
                db.session.commit()
                return jsonify({'result': update_user.__repr__()}), 200
            else:
                return s_vars.user_not_exist, 404
        else:
            return s_vars.not_authorized, 401
    except KeyError:
        return s_vars.bad_request, 400


@app.route(s_vars.api_v1 + '/user/update_pass/<username>', methods=['POST'])
def update_pass_by_username(username):
    data = request.json
    if 'secret' not in list(data.keys()):
        return s_vars.bad_request, 400
    auth_status, auth_user = au_ser.check_auth_token(request.headers)
    if auth_user == username:
        update_user = user_model.User.query.filter_by(username=username).first()
        if update_user is not None:
            update_user.set_password(data['secret'])
            update_user.last_updated = datetime.utcnow()
            db.session.commit()
            res = {'result': 'Password updated for user {}'.format(update_user.username)}
            return jsonify(res), 200
        else:
            return s_vars.user_not_exist, 404
    else:
        return s_vars.not_authorized, 401


@app.route(s_vars.api_v1 + '/user/password_reset/', methods=['POST'])
def password_reset_by_email():
    data = request.json
    if 'email' not in list(data.keys()):
        return s_vars.bad_request, 400
    update_user = user_model.User.query.filter_by(email=data['email']).first()
    if update_user is not None:
        update_user.reset_token = id_gen(25)
        update_user.last_updated = datetime.utcnow()
        db.session.commit()
        try:
            send_mail(update_user.email, 'Password Reset Link', '''Hi {},
            Click or open the provided URL to change your password.\n\n {}
            '''.format(update_user.name,
                       request.origin + s_vars.front_end_prefix + 'password_reset/' + update_user.reset_token + '/' + update_user.username))
        except smtplib.SMTPException:
            return s_vars.error_try_again, 501
        res = {'result': 'Password reset link sent for user {}'.format(update_user.email)}
        return jsonify(res), 200
    else:
        return s_vars.user_not_exist, 404


@app.route(s_vars.api_v1 + '/user/update_password_by_token/', methods=['POST'])
def password_update_by_token():
    data = request.json
    try:
        update_user = user_model.User.query.filter_by(username=data['username']).first()
        if update_user is not None:
            if update_user.reset_token != data['token'] or update_user.reset_token is None:
                return jsonify({'response': 'Token incorrect or expired'}), 401
            old_token = update_user.reset_token
            update_user.set_password(data['secret'])
            update_user.reset_token = None
            update_user.last_updated = datetime.utcnow()
            db.session.commit()
            try:
                send_mail(update_user.email, 'Password Updated', '''Hi {},
                Your password is updated
                '''.format(update_user.name))
            except smtplib.SMTPException:
                update_user.reset_token = old_token
                db.session.commit()
                return s_vars.error_try_again, 501
            res = {'result': 'Password reset link sent for user {}'.format(update_user.email)}
            return jsonify(res), 200
        else:
            return s_vars.user_not_exist, 404
    except KeyError:
        return s_vars.bad_request, 400


@app.route(s_vars.api_v1 + '/user/action/<action_type>/', methods=['POST'])
def action_by_username(action_type):
    data = request.json
    if 'username' not in list(data.keys()):
        return s_vars.bad_request, 400
    auth_status, auth_user = au_ser.check_auth_token(request.headers)
    if auth_user == data['username'] and auth_user != 'public':
        update_user = user_model.User.query.filter_by(username=data['username']).first()
        if update_user is not None:
            msg_str = ''
            if action_type == 'deactivate':
                change_user_activation(data['username'], False)
                msg_str = ' deactivated'
            elif action_type == 'activate':
                change_user_activation(data['username'], True)
                msg_str = ' activated'
            elif action_type == 'delete':
                delete_user(data['username'])
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
                except smtplib.SMTPException:
                    return s_vars.mail_sending_failed, 501
            elif action_type == 'resend_verification':
                update_user.verification_code = code_gen()
                update_user.set_verification_expiry()
                try:
                    send_mail(update_user.email, 'Welcome to ShortUrl', 'Verification Code: {}'.format(
                        update_user.verification_code
                    ))
                    msg_str = ', verification code resent.'
                except smtplib.SMTPException:
                    return s_vars.mail_sending_failed, 501
            else:
                return s_vars.action_not_available, 404
            update_user.last_updated = datetime.utcnow()
            db.session.commit()
            res = {'response': 'User \'{}\'{}'.format(update_user.username, msg_str)}
            return jsonify(res), 200
        else:
            return s_vars.user_not_exist, 404
    else:
        return s_vars.not_authorized, 401


@app.route(s_vars.api_v1 + '/user/login_check/<username>', methods=['POST'])
def check_if_can_login(username):
    data = request.json
    if 'secret' not in list(data.keys()):
        return s_vars.bad_request, 400
    auth_status, auth_user = au_ser.check_auth_token(request.headers)
    if auth_user == username:
        user = user_model.User.query.filter_by(username=username).first()
        if user is not None:
            if user.check_password(data['secret']):
                res = {'result': user.__repr__()}
                return jsonify(res), 200
            else:
                res = {'result': 'Can\'t login'}
                return jsonify(res), 403
        return s_vars.user_not_exist, 404
    else:
        return s_vars.not_authorized, 401
