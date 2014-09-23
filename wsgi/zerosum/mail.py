import os

from flask import render_template
import sendgrid

from zerosum import app
from zerosum.db import get_row, get_scalar

sg = sendgrid.SendGridClient(os.environ.get('SENDGRID_USER'),
                             os.environ.get('SENDGRID_PASSWORD'),
                             raise_errors=True)


def send_mail(template, to, **tmpl_vars):
    rendered_tmpl = render_template(template, **tmpl_vars)
    if app.debug:
        app.logger.debug(rendered_tmpl)
        return
    subject, separator, body = rendered_tmpl.partition('\n--\n')
    message = sendgrid.Mail(
        to=to,
        subject=subject,
        text=body,
        from_email='noreply@zerosum-karlb.rhcloud.com')
    sg.send(message)


def confirm_code(email):
    return get_scalar("""
        INSERT INTO email_confirm(email) VALUES (%s)
        RETURNING code
    """, [email])


def send_owe_mail(owe_id):
    owe = get_row("""
            SELECT owe.*,
                  creditor.email AS creditor_email,
                  creditor.name AS creditor_name,
                  creditor.is_active,
                  debitor.name AS debitor_name
            FROM owe
                JOIN zerosum_user creditor ON (creditor_id = creditor.user_id)
                JOIN zerosum_user debitor ON (debitor_id = debitor.user_id)
            WHERE owe_id = %s
        """, [owe_id])
    send_mail('mails/new_owe.txt', owe.creditor_email,
            confirm_code=lambda: confirm_code(owe.creditor_email), **owe._asdict())


def send_registration_mail(email):
    send_mail('mails/register.txt', email,
            confirm_code=lambda: confirm_code(email))
