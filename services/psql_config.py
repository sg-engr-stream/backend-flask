import os
import socket
import env.local
import env.production
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'f1345cc87a16c056b0fde15dd84e7ac729e32b85f08e88c8537d0999a17f055c'
    if socket.gethostname() == 'DESKTOP-PHOENIX':
        db_uri = env.local.DB_URI
    else:
        db_uri = env.production.DB_URI
    SQLALCHEMY_DATABASE_URI = db_uri


class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True