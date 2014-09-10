import os
from decimal import Decimal
from datetime import datetime

from flask import Flask, render_template, redirect, request, url_for
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

from zerosum.db import get_db, get_scalar
from zerosum.login import get_or_create_user
from zerosum.mail import send_owe_mail
from zerosum import forms

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

    cur.execute("SELECT user_id, array_to_json(array_agg(recent_owes)) FROM recent_owes(%s) GROUP BY 1", [current_user.get_id()])
    details = dict(cur.fetchall())

    total = (
        sum(b.amount for b in balances if b.amount > 0),
        sum(b.amount for b in balances if b.amount < 0),
    )

    return render_template('home.html', owes=owes, balances=balances, details=details, total=total)


@app.route("/user/new_owe", methods=['POST'])
def new_owe_old():
    creditor_email = request.form['creditor']
    amount = Decimal(request.form['amount'])
    subject = request.form['subject']

    creditor_id = get_or_create_user(creditor_email).user_id

    owe_id = get_scalar("""
            INSERT INTO owe(creditor_id, debitor_id, amount, subject)
            VALUES (%s, %s, %s, %s)
            RETURNING owe_id
        """, [creditor_id, current_user.get_id(), amount, subject])
    send_owe_mail(owe_id)
    return redirect(url_for('home'))


@app.route("/new_owe", methods=['GET', 'POST'])
def new_owe():
    form = forms.NewOweForm()
    form.creditor.kwargs = dict(autofocus=True)
    if form.validate_on_submit():
        creditor_id = get_or_create_user(form.creditor.data).user_id
        owe_id = get_scalar("""
                INSERT INTO owe(creditor_id, debitor_id, amount, subject)
                VALUES (%s, %s, %s, %s)
                RETURNING owe_id
            """, [creditor_id, current_user.get_id(),
                  form.amount.data, form.subject.data])
        send_owe_mail(owe_id)
        return redirect(url_for('home'))
    else:
        return render_template('new_owe.html', form=form)


import pytz


@app.template_filter('dt')
def format_dt(dt):
    if isinstance(dt, str):
        dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S.%f")
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


@app.context_processor
def inject_user():
    return dict(app_name='TrackMyOwe')


if __name__ == "__main__":
    app.run()
