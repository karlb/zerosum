from flask import render_template, redirect, request, url_for, flash
from flask.ext.login import login_required, current_user

from zerosum import app
from zerosum.login import get_or_create_user
from zerosum.db import get_db, get_scalar, get_all, get_row
from zerosum.mail import send_owe_mail
import zerosum.forms as forms
import zerosum.db as db


@login_required
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
        flash('Successfully added owe!', 'success')
        return redirect(url_for('home'))
    else:
        return render_template('new_owe.html', form=form)


@login_required
@app.route("/request_owe", methods=['GET', 'POST'])
def request_owe():
    form = forms.RequestOweForm()
    form.debitor.kwargs = dict(autofocus=True)
    if form.validate_on_submit():
        debitor_id = get_or_create_user(form.debitor.data).user_id
        owe_id = get_scalar("""
                INSERT INTO owe_request(creditor_id, debitor_id, amount, subject)
                VALUES (%s, %s, %s, %s)
                RETURNING owe_request_id
            """, [current_user.get_id(), debitor_id,
                  form.amount.data, form.subject.data])
        #send_owe_request_mail(owe_request_id)
        flash('Owe request sent successfully!', 'success')
        return redirect(url_for('home'))
    else:
        return render_template('request_owe.html', form=form)

    
@login_required
@app.route("/respond_to_request", methods=['POST'])
def respond_to_request():
    request_id = int(request.form['request_id'])
    action = request.form['action']
    assert action in ('confirm', 'reject')
    if action == 'confirm':
        assert db.exec("""
            WITH new_owe AS (
                INSERT INTO owe(debitor_id, creditor_id, amount, subject)
                SELECT debitor_id, creditor_id, amount, subject
                FROM owe_request
                WHERE owe_request_id = %(request_id)s
                  AND debitor_id = %(debitor_id)s
                  AND status = 'open'
                RETURNING owe_id
            )
            UPDATE owe_request
            SET status = 'accepted',
                responded_at = now(),
                owe_id = new_owe.owe_id
            FROM new_owe
            WHERE owe_request_id = %(request_id)s
        """, dict(request_id=request_id, debitor_id=current_user.get_id())) == 1
    else:
        assert db.exec("""
            UPDATE owe_request
            SET status = 'rejected',
                responded_at = now()
            WHERE owe_request_id = %s
              AND debitor_id = %s
              AND status = 'open'
        """, [request_id, current_user.get_id()]) == 1
    return redirect(url_for('home'))


@login_required
@app.route("/reject_request", methods=['POST'])
def reject_request():
    return redirect(url_for('home'))