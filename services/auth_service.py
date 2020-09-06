from basicauth import decode, DecodeError
import models.auth_model as au_model


def check_auth_token(headers):
    token = headers.get('Shorturl-Access-Token')
    try:
        user, passwd = decode(token)
        user_in_db = au_model.User.query.filter_by(username=user).first()
        if user_in_db is not None:
            if user_in_db.check_password(passwd):
                return True, user
        return False, None
    except DecodeError as e:
        return False, None

