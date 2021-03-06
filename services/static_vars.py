from flask import jsonify
from app import *

with app.app_context():
    user_already_exist = jsonify({'response': 'Username or Email already exist'})
    user_available = jsonify({'response': 'Username is available.'})
    user_not_exist = jsonify({'response': 'User not found'})
    not_authorized = jsonify({'response': 'Not Authorized'})
    cannot_create_user = jsonify({'response': 'Restricted user. Cannot Create'})
    bad_request = jsonify({'response': 'Bad request. Check your request again.'})
    card_not_exist = jsonify({'response': 'Card not found'})
    group_not_exist = jsonify({'response': 'Group not found'})
    short_url_available = jsonify({'response': 'ShortUrl is available'})
    short_url_not_available = jsonify({'response': 'ShortUrl is not available'})
    error_try_again = jsonify({'response': 'Error Occurred. Please try again after some time.'})
    duplicate_record = jsonify({'response': 'Record already exist. Cannot create duplicate.'})
    cannot_change_email = jsonify({'response': 'Email address cannot be changed after verification.'})
    invalid_code = jsonify({'response': 'Invalid Verification Code.'})
    expired_code = jsonify({'response': 'Verification Code is Expired'})
    verified_user = jsonify({'response': 'Verification User.'})
    not_verified_user = jsonify({'response': 'User is not verified.'})

    cannot_give_card_access = jsonify({'response': 'Cannot give access. You are read only or not authorized.'})
    cannot_change_owner = jsonify({'response': 'Ownership cannot be changed for public owned cards not created by you.'})
    mail_sending_failed = jsonify({'response': 'Error occurred during triggering e-mail.'})
    invalid_action = jsonify({'response': 'Invalid action type.'})

    api_v1 = '/api/v1'
    front_end_prefix = '/app/'
