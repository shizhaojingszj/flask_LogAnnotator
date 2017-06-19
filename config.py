# -*- coding: utf-8 -*-

import os
class Configuration(object):
    APPLICATION_DIR = os.path.dirname(os.path.realpath(__file__))
    DEBUG = True
    ## dialect+driver://username:password@host:port/database
    ## postgresql://postgres:secretpassword@localhost:5432/blog_db
    SQLALCHEMY_DATABASE_URI = 'sqlite:///%s/sqlite.db' % APPLICATION_DIR
    SQLALCHEMY_TRACK_MODIFICATIONS = True # to mute the warning
