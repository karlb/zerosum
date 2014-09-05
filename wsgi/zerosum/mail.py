import os

from flask import render_template
import sendgrid

from zerosum.db import get_row, get_scalar

sg = sendgrid.SendGridClient(os.environ['SENDGRID_USER'],
                             os.environ['SENDGRID_PASSWORD'],
                             raise_errors=True)


def send_mail(template, to, **tmpl_vars):
    rendered_tmpl = render_template(template, **tmpl_vars)
    subject, separator, body = rendered_tmpl.partition('\n--\n')
    message = sendgrid.Mail(
        to=to,
        subject=subject,
        text=body,
        from_email='noreply@zerosum-karlb.rhcloud.com')
    sg.send(message)


def confirm_code(user):
    return get_scalar("""
        INSERT INTO email_confirm(email) VALUES (%s)
        RETURNING code
    """, [user.email])


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
              confirm_code=confirm_code, **owe._asdict())
