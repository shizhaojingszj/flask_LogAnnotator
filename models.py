# -*- coding: utf-8 -*-

import datetime, re

from app import app, db # app is just a namespace, db is a SQLAlchemy obj
from flask_script import Manager
from flask_migrate import (Migrate, MigrateCommand)

manager = Manager(app)
migrate = Migrate(app, db)      # this is how to create a migrate
manager.add_command('db', MigrateCommand)

class LogFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    hash = db.Column(db.String(100), unique=True)
    entries = db.relationship("LogEntry", backref="logfile", lazy="dynamic")  # One-To-Many
    comment = db.Column(db.String(300))

## Now create a ORMer
class LogEntry(db.Model):          # Model is an attribute for SQLAlchemy obj, and still a class
    ## just schema
    id = db.Column(db.Integer, primary_key=True)
    line_num = db.Column(db.Integer)  # line number inside the file
    timestamp = db.Column(db.DateTime)
    body = db.Column(db.Text)
    annotate = db.Column(db.Text)
    logfile_id = db.Column(db.Integer, db.ForeignKey('log_file.id'))  # This is magic table name

    def __init__(self, *args, **kwargs):
        super(LogEntry, self).__init__(*args, **kwargs)  # Call parent constructor. Popup all the attrs.

    def __repr__(self):
        return '<LogEntry in Line %s from File id %s>' % (self.line_num, self.logfile_id)

if __name__ == '__main__':
    manager.run()
