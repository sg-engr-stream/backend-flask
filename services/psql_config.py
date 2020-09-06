import os
from app import env_config
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'f1345cc87a16c056b0fde15dd84e7ac729e32b85f08e88c8537d0999a17f055c'
    SQLALCHEMY_DATABASE_URI = env_config.DB_URI


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