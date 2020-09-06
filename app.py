from flask import Flask
import logging
import flask_monitoringdashboard as dashboard
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
dashboard.bind(app)

logging.basicConfig(level=logging.DEBUG)

import models.auth_model
import views.user


@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
