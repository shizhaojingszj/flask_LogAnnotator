# -*- coding: utf-8 -*-

from flask import Flask
### deprecated: from flask.ext.sqlalchemy import SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
from config import Configuration  # import our configuration data.
app = Flask(__name__)

app.config.from_object(Configuration)  # use values from our Configuration object.
db = SQLAlchemy(app)                   # Flask => SQLAlchemy
