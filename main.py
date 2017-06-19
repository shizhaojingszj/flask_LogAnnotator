# -*- coding: utf-8 -*-

from app import app, db  # import our Flask app as well db

import models

import views

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8099)                   # no need to say debug=True here, because we already using Configuration object
