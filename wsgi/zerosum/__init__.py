import os
from decimal import Decimal

from flask import Flask, render_template, redirect, request, url_for, flash
from flask.ext.login import login_required, current_user

app = Flask(__name__.split('.')[0])
app.debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        os.environ['OPENSHIFT_LOG_DIR'] + '/flask.log',
        maxBytes=10000, backupCount=1)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    print('added log handler')

from zerosum.db import get_db, get_scalar, get_all
import zerosum.owe
import zerosum.template_helpers

app.secret_key = os.environ['OPENSHIFT_SECRET_TOKEN']


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/user/")
@login_required
def home():
    cur = get_db().cursor()
    cur.execute("SELECT * FROM recent_owes(%s)", [current_user.get_id()])
    owes = cur.fetchall()

    cur.execute("SELECT * FROM balances(%s)", [current_user.get_id()])
    balances = cur.fetchall()

    cur.execute("""
        SELECT user_id, array_to_json(array_agg(recent_owes))
        FROM recent_owes(%s) GROUP BY 1
    """, [current_user.get_id()])
    details = dict(cur.fetchall())

    requests = get_all("""
        SELECT owe_request.*, name
        FROM owe_request
             JOIN zerosum_user ON (creditor_id = user_id)
        WHERE debitor_id = %s
          AND status = 'open'
        ORDER BY created_at
    """, [current_user.get_id()])

    my_open_requests = get_all("""
        SELECT owe_request.*, name
        FROM owe_request
             JOIN zerosum_user ON (debitor_id = user_id)
        WHERE creditor_id = %s
          AND status = 'open'
        ORDER BY created_at
    """, [current_user.get_id()])

    total = (
        sum(b.amount for b in balances if b.amount > 0),
        sum(b.amount for b in balances if b.amount < 0),
    )

    return render_template('home.html', owes=owes, balances=balances,
                           details=details, total=total, requests=requests,
                           my_open_requests=my_open_requests)


if __name__ == "__main__":
    app.run()
