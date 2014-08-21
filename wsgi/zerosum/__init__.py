import os
from decimal import Decimal

from flask import Flask, render_template, redirect, request, url_for
from flask.ext.login import current_user, login_required

app = Flask(__name__.split('.')[0])

import zerosum.db as db
import zerosum.login

app.secret_key = os.environ['OPENSHIFT_SECURE_TOKEN']


@app.route("/user/")
@login_required
def home():
    cur = db.get_db().cursor()
    cur.execute("SELECT * FROM recent_owes(%s)", [current_user.get_id()])
    owes = cur.fetchall()

    cur.execute("SELECT * FROM balances(%s)", [current_user.get_id()])
    balances = cur.fetchall()

    user = current_user

    return render_template('index.html',
                           user=user, owes=owes, balances=balances)
    #return "Hello World!" + repr(rows)


@app.route("/user/new_owe", methods=['POST'])
def new_owe():
    conn = db.get_db()
    cur = conn.cursor()

    creditor_email = request.form['creditor']
    amount = Decimal(request.form['amount'])
    subject = request.form['subject']

    cur.execute("SELECT * FROM zerosum_user WHERE email = %s",
                [creditor_email])
    rows = cur.fetchall()
    if not rows:
        cur.execute("""
            INSERT INTO zerosum_user(email, name) VALUES (%(email)s, %(email)s)
            RETURNING user_id""",
                    dict(email=creditor_email))
        creditor_id = cur.fetchall()[0].user_id
    else:
        creditor_id = rows[0].user_id

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
