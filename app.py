from flask import Flask
import logging
import flask_monitoringdashboard as dashboard
from flask_sqlalchemy import SQLAlchemy
import socket
import services.psql_config

app = Flask(__name__)
app_settings = ''
if socket.gethostname() == 'DESKTOP-PHOENIX':
    app_settings = services.psql_config.DevelopmentConfig
else:
    app_settings = services.psql_config.ProductionConfig

app.config.from_object(app_settings)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
dashboard.bind(app)

logging.basicConfig(level=logging.DEBUG)

import models.auth_model
import models.card_model
import models.card_access_model
import models.group_model
import models.group_access_model
import models.group_cards
import views.user


@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
