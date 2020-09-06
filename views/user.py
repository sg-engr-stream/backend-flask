from flask import request, jsonify
from sqlalchemy import exc
from app import app, db, logging
import models.auth_model as au_model
from datetime import datetime
# import services.auth_service as au_ser


@app.route('/user/add/', methods=['POST'])
def add_user():
    data = request.json
    new_user = au_model.User(name=data['name'], username=data['username'], email=data['email'])
    new_user.set_password(data['secret'])
    try:
        db.session.add(new_user)
        db.session.commit()
        res = {'response': 'user: {} has been created'.format(new_user.username)}
        db.session.expunge(new_user)
        db.session.close()
    except exc.IntegrityError as e:
        logging.error(e)
        return {'response': 'Username or Email already exist'}
    return res


@app.route('/user/id/<user_id>', methods=['GET'])
def get_user_by_username(user_id):
    user = au_model.User.query.filter_by(username=user_id).scalar()
    # auth_status, auth_user = au_ser.check_auth_token(request.headers)
    # print(auth_user == user_id)

    if user is not None:
        return jsonify({'username': user.username, 'name': user.name, 'email': user.email}), 200
    else:
        return jsonify({'response': 'User not found'}), 404


@app.route('/user/update/<user_id>', methods=['POST'])
def update_user_by_username(user_id):
    data = request.json
    update_user = au_model.User.query.filter_by(username=user_id).first()
    if update_user is not None:
        update_user.name = data['name']
        update_user.email = data['email']
        update_user.last_updated = datetime.utcnow()
        db.session.commit()
        res = {'username': update_user.username, 'name': update_user.name, 'email': update_user.email}
        return jsonify(res), 200
    else:
        return jsonify({'response': 'User not found'}), 404


@app.route('/user/update_pass/<user_id>', methods=['POST'])
def update_pass_by_username(user_id):
    data = request.json
    update_user = au_model.User.query.filter_by(username=user_id).first()
    if update_user is not None:
        update_user.set_password(data['secret'])
        update_user.last_updated = datetime.utcnow()
        db.session.commit()
        res = {'response': 'Password updated for user {}'.format(update_user.username)}
        return jsonify(res), 200
    else:
        return jsonify({'response': 'User not found'}), 404


@app.route('/user/action/<type>/', methods=['POST'])
def action_by_username(action_type):
    data = request.json
    update_user = au_model.User.query.filter_by(username=data['username']).first()
    if update_user is not None:
        msg_str = ''
        if action_type == 'deactivate':
            update_user.deactivated = True
            msg_str = 'deactivated'
        elif action_type == 'activate':
            update_user.deactivated = False
            msg_str = 'activated'
        elif action_type == 'delete':
            update_user.deactivated = True
            update_user.deleted = True
            msg_str = 'deleted'
        else:
            return jsonify({'response': 'path does not exist'}), 404
        update_user.last_updated = datetime.utcnow()
        db.session.commit()
        res = {'response': 'User {} {}'.format(update_user.username, msg_str)}
        return jsonify(res), 200
    else:
        return jsonify({'response': 'User not found'}), 404


@app.route('/user/login_check/<user_id>', methods=['POST'])
def check_if_can_login(user_id):
    data = request.json
    user = au_model.User.query.filter_by(username=user_id).first()
    if user is not None:
        if user.check_password(data['secret']):
            res = {'response': 'Can login'}
        else:
            res = {'response': 'Can\'t login'}
        return jsonify(res), 200
    else:
        return jsonify({'response': 'User not found'}), 404