from flask import Flask, request, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from time import strftime
import traceback
import flask_monitoringdashboard as dashboard
from flask_sqlalchemy import SQLAlchemy
import socket
import services.psql_config
import os

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})
app_settings = ''
if socket.gethostname() == 'DESKTOP-PHOENIX':
    app_settings = services.psql_config.DevelopmentConfig
    dashboard.config.init_from('dboard/config_local.cfg')
else:
    app_settings = services.psql_config.ProductionConfig
    dashboard.config.init_from('dboard/config_prod.cfg')

app.config.from_object(app_settings)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
dashboard.bind(app)

SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.yml'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "N4NITIN_service"
    },
    # oauth_config={  # OAuth config. See https://github.com/swagger-api/swagger-ui#oauth2-configuration .
    #    'clientId': "your-client-id",
    #    'clientSecret': "your-client-secret-if-required",
    #    'realm': "your-realms",
    #    'appName': "your-app-name",
    #    'scopeSeparator': " ",
    #    'additionalQueryStringParams': {'test': "hello"}
    # }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

logging.basicConfig(level=logging.DEBUG)
app.url_map.strict_slashes = False

today = datetime.utcnow().strftime('%Y-%m-%d')
os.makedirs('logs', exist_ok=True)
handler = RotatingFileHandler('logs/app_' + today + '.log', maxBytes=100000, backupCount=3)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

import models.auth_model
import models.card_model
import models.card_access_model
import models.group_model
import models.group_access_model
import models.group_cards

import views.user_view
import views.card_view
import views.card_access_view
import views.group_view
import views.group_access_view


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.after_request
def after_request(response):
    # this if avoids the duplication of registry in the log,
    # since that 500 is already logged via @app.errorhandler
    if response.status_code != 500:
        ts = strftime('[%Y-%b-%d %H:%M]')
        logger.error('%s %s %s %s %s %s %s',
                     ts,
                     request.remote_addr,
                     request.method,
                     request.scheme,
                     request.full_path,
                     response.status, response.json)
    return response


@app.errorhandler(Exception)
def exceptions(e):
    ts = strftime('[%Y-%b-%d %H:%M]')
    tb = traceback.format_exc()
    logger.error('%s %s %s %s %s 5xx INTERNAL SERVER ERROR\n%s',
                 ts,
                 request.remote_addr,
                 request.method,
                 request.scheme,
                 request.full_path,
                 tb)
    return "Internal Server Error", 500


if __name__ == '__main__':
    app.run()
