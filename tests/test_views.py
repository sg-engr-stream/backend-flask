import pytest
import json
from app import app as flask_app, db
from basicauth import encode
from models.auth_model import User
from models.card_model import Card
from models.card_access_model import CardAccess
from services.generators import code_gen


@pytest.fixture
def app():
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


def test_adduser(app, client):
    data = {
        'name': 'Test',
        'username': 'test',
        'email': 'kumar.nitin1122@gmail.com',
        'secret': 'alpha'
    }
    res = client.post('/api/v1/user/add', headers={'shorturl-access-token': 'bms5OmFscGhh', 'Content-Type': 'application/json'}, data=json.dumps(data))
    assert res.status_code == 200 or res.status_code == 409


def test_getuser_info(app, client):
    user_from_db = User.query.filter_by(username='test').first()
    res = client.get('/api/v1/user/id/'+user_from_db.username,
                     headers={'shorturl-access-token': encode(user_from_db.username, 'alpha').split(' ')[1], 'Content-Type': 'application/json'})
    assert res.status_code == 200


def test_update_user_info(app, client):
    data = {
        'name': 'Test123'
    }
    res = client.post('/api/v1/user/update/test',
                      headers={'shorturl-access-token': encode('test', 'alpha').split(' ')[1], 'Content-Type': 'application/json'},
                      data=json.dumps(data))
    assert res.status_code == 200


def test_update_user_pass(app, client):
    data = {
        'secret': 'alpha'
    }
    res = client.post('/api/v1/user/update_pass/test',
                      headers={'shorturl-access-token': encode('test', 'alpha').split(' ')[1],
                               'Content-Type': 'application/json'},
                      data=json.dumps(data))
    assert res.status_code == 200


def test_deactivate_user(app, client):
    data = {
        'username': 'test'
    }
    res = client.post('/api/v1/user/action/deactivate',
                      headers={'shorturl-access-token': encode('test', 'alpha').split(' ')[1],
                               'Content-Type': 'application/json'},
                      data=json.dumps(data))
    assert res.status_code == 200


def test_activate_user(app, client):
    data = {
        'username': 'test'
    }
    res = client.post('/api/v1/user/action/activate',
                      headers={'shorturl-access-token': encode('test', 'alpha').split(' ')[1],
                               'Content-Type': 'application/json'},
                      data=json.dumps(data))
    assert res.status_code == 200


def test_resend_verification_mail(app, client):
    data = {
        'username': 'test'
    }
    res = client.post('/api/v1/user/action/resend_verification',
                      headers={'shorturl-access-token': encode('test', 'alpha').split(' ')[1],
                               'Content-Type': 'application/json'},
                      data=json.dumps(data))
    assert res.status_code == 200


def test_verify_user(app, client):
    user_from_db = User.query.filter_by(username='test').first()
    data = {
        'username': 'test',
        'verification_code': user_from_db.verification_code
    }
    res = client.post('/api/v1/user/action/verify/',
                      headers={'shorturl-access-token': encode('test', 'alpha').split(' ')[1],
                               'Content-Type': 'application/json'},
                      data=json.dumps(data))
    assert res.status_code == 200


# card test cases
def test_add_pub_card(app, client):
    data = {
        'title': 'test pub card',
        'description': 'test public card',
        'redirect_url': 'https://www.google.com/',
        'short_url': 'test_url_pub'
    }
    res = client.post('/api/v1/card/add/',
                      headers={'Content-Type': 'application/json'},
                      data=json.dumps(data))
    assert res.status_code == 200 or res.status_code == 409


def test_add_pvt_card(app, client):
    data = {
        'title': 'test pvt card',
        'description': 'test pvt card',
        'redirect_url': 'https://www.google.com/',
        'short_url': 'test_url_pvt'
    }
    res = client.post('/api/v1/card/add/',
                      headers={'shorturl-access-token': encode('test', 'alpha').split(' ')[1],
                               'Content-Type': 'application/json'},
                      data=json.dumps(data))
    assert res.status_code == 200 or res.status_code == 409


def test_get_pub_details(app, client):
    card_from_db = Card.query.filter_by(short_url='test_url_pub').first()
    res = client.get('/api/v1/card/id/'+card_from_db.card_id,
                      headers={'Content-Type': 'application/json'})
    assert res.status_code == 200 or res.status_code == 409


def test_get_pvt_details(app, client):
    card_from_db = Card.query.filter_by(short_url='test_url_pvt').first()
    res = client.get('/api/v1/card/id/' + card_from_db.card_id,
                      headers={'shorturl-access-token': encode('test', 'alpha').split(' ')[1],
                               'Content-Type': 'application/json'})
    assert res.status_code == 200 or res.status_code == 409


def test_get_short_url_availability(app, client):
    res = client.get('/api/v1/card/available/test_url_pvt',
                      headers={'Content-Type': 'application/json'})
    assert res.status_code == 200 or res.status_code == 409


def test_activate_pub_card(app, client):
    card_from_db = Card.query.filter_by(short_url='test_url_pub').first()
    res = client.get('/api/v1/card/id/' + card_from_db.card_id,
                     headers={'Content-Type': 'application/json'})
    assert res.status_code == 200


def test_activate_pvt_card(app, client):
    card_from_db = Card.query.filter_by(short_url='test_url_pvt').first()
    res = client.get('/api/v1/card/id/' + card_from_db.card_id,
                     headers={'shorturl-access-token': encode('test', 'alpha').split(' ')[1],
                              'Content-Type': 'application/json'})
    assert res.status_code == 200


def test_update_pub_card(app, client):
    data = {
        'title': 'test pub card' + code_gen(3),
        'description': 'test pub card',
        'redirect_url': 'https://www.google.com/',
        'short_url': 'test_url_pub'
    }
    card_from_db = Card.query.filter_by(short_url='test_url_pub').first()
    res = client.post('/api/v1/card/update/' + card_from_db.card_id,
                     headers={'Content-Type': 'application/json'}, data=json.dumps(data))
    assert res.status_code == 200


def test_update_pvt_card(app, client):
    data = {
        'title': 'test pvt card'+code_gen(3),
        'description': 'test pvt card',
        'redirect_url': 'https://www.google.com/',
        'short_url': 'test_url_pvt',
        'username': 'test'
    }
    card_from_db = Card.query.filter_by(short_url='test_url_pvt').first()
    res = client.post('/api/v1/card/update/' + card_from_db.card_id,
                     headers={'shorturl-access-token': encode('test', 'alpha').split(' ')[1],
                              'Content-Type': 'application/json'}, data=json.dumps(data))
    assert res.status_code == 200


# card access testcases


def test_add_pub_card_access(app, client):
    card_from_db = Card.query.filter_by(short_url='test_url_pub').first()
    data = {
        'card_id': card_from_db.card_id,
        'username': ['test'],
        'access_type': 'RW'
    }
    res = client.post('/api/v1/card_access/add/',
                      headers={'Content-Type': 'application/json'}, data=json.dumps(data))
    assert res.status_code == 200


def test_add_pvt_card_access(app, client):
    card_from_db = Card.query.filter_by(short_url='test_url_pvt').first()
    data = {
        'card_id': card_from_db.card_id,
        'username': ['public'],
        'access_type': 'RW'
    }
    res = client.post('/api/v1/card_access/add/',
                      headers={'shorturl-access-token': encode('test', 'alpha').split(' ')[1],
                               'Content-Type': 'application/json'}, data=json.dumps(data))
    assert res.status_code == 200


def test_update_pvt_card_2(app, client):
    data = {
        'title': 'test pvt card available for all'+code_gen(3),
        'description': 'test pvt card',
        'redirect_url': 'https://www.google.com/',
        'short_url': 'test_url_pvt',
        'username': 'test'
    }
    card_from_db = Card.query.filter_by(short_url='test_url_pvt').first()
    res = client.post('/api/v1/card/update/' + card_from_db.card_id,
                     headers={'Content-Type': 'application/json'}, data=json.dumps(data))
    assert res.status_code == 200


# test user delete in last
def test_delete_user(app, client):
    data = {
        'username': 'test'
    }
    res = client.post('/api/v1/user/action/delete',
                      headers={'shorturl-access-token': encode('test', 'alpha').split(' ')[1],
                               'Content-Type': 'application/json'},
                      data=json.dumps(data))
    assert res.status_code == 200
