from flask import jsonify
from app import *

with app.app_context():
    user_already_exist = jsonify({'response': 'Username or Email already exist'})
    user_not_exist = jsonify({'response': 'User not found'})
    action_not_available = jsonify({'response': 'Action not available'})
    not_authorized = jsonify({'response': 'Not Authorized'})
    cannot_create_user = jsonify({'response': 'Restricted user. Cannot Create'})
    bad_request = jsonify({'response': 'Bad request. Check your request again.'})
    card_not_exist = jsonify({'response': 'Card not found'})
    short_url_available = jsonify({'response': 'ShortUrl is available'})
    short_url_not_available = jsonify({'response': 'ShortUrl is not available'})
    error_try_again = jsonify({'response': 'Error Occurred. Please try again after some time.'})
    duplicate_record = jsonify({'response': 'Record already exist. Cannot create duplicate.'})
    api_v1 = '/api/v1'
