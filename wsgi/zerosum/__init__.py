import os
from decimal import Decimal

from flask import Flask, render_template, redirect, request, url_for
from flask.ext.login import login_required, current_user

app = Flask(__name__.split('.')[0])

import zerosum.db as db
from zerosum.login import get_or_create_user

app.secret_key = os.environ['OPENSHIFT_SECURE_TOKEN']


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/user/")
@login_required
def home():
    cur = db.get_db().cursor()
    cur.execute("SELECT * FROM recent_owes(%s)", [current_user.get_id()])
    owes = cur.fetchall()

    cur.execute("SELECT * FROM balances(%s)", [current_user.get_id()])
    balances = cur.fetchall()

    cur.execute("SELECT user_id, array_to_json(array_agg(recent_owes)) FROM recent_owes(%s) GROUP BY 1", [current_user.get_id()])
    details = dict(cur.fetchall())

    return render_template('home.html', owes=owes, balances=balances, details=details)


@app.route("/user/new_owe", methods=['POST'])
def new_owe():
    conn = db.get_db()
    cur = conn.cursor()

    creditor_email = request.form['creditor']
    amount = Decimal(request.form['amount'])
    subject = request.form['subject']

    creditor_id = get_or_create_user(creditor_email).user_id

    #cur.execute("SELECT create_owe(%s, %s, %s)")
    cur.execute("""INSERT INTO owe(creditor_id, debitor_id, amount, subject)
                   VALUES (%s, %s, %s, %s)""",
                [creditor_id, current_user.get_id(), amount, subject])
    conn.commit()
    return redirect(url_for('home'))


import pytz


@app.template_filter('dt')
def format_dt(dt):
    tz = pytz.timezone('Europe/Berlin')
    dt_with_tz = dt.replace(tzinfo=pytz.timezone('UTC')).astimezone(tz)
    return dt_with_tz.strftime('%Y-%m-%d %H:%M')


@app.template_filter('plusminus')
def format_plusminus(value):
    if value < 0:
        return 'minus'
    if value > 0:
        return 'plus'
    else:
        return ''


if __name__ == "__main__":
    debug = bool(os.environ.get('FLASK_DEBUG', False))
    app.run(debug=debug)
