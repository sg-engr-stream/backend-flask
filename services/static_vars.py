from flask import jsonify
from app import *

with app.app_context():
    user_already_exist = jsonify({'response': 'Username or Email already exist'})
    user_not_exist = jsonify({'response': 'User not found'})
    action_not_available = jsonify({'response': 'Action not available'})
    not_authorized = jsonify({'response': 'Not Authorized'})
    cannot_create_user = jsonify({'response': 'Restricted user. Cannot Create'})
    bad_request = jsonify({'response': 'Bad request. Check your request again.'})
    api_v1 = '/api/v1'
