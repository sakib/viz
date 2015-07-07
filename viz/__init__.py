#!venv/bin/python
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.httpauth import HTTPBasicAuth
from .api import api
import logging

app = Flask(__name__)
app.config.from_pyfile('../config.py')
app.register_blueprint(api, subdomain='api')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

auth = HTTPBasicAuth()

from .models import *
from .api import __init__
