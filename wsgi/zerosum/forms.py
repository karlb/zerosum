import re

from flask_wtf import Form
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, EqualTo
from wtforms.fields.html5 import DecimalField


class RegisterForm(Form):
    name = StringField('Public Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password',
                              validators=[DataRequired(), EqualTo('password')])


class EmailWithName(Email):

    def process_formdata(self, valuelist):
        self.data = (
            re.match(r'.* <(.*)>', valuelist[0]).group(1)
            or valuelist[0]
        )


class NewOweForm(Form):
    creditor = StringField('I owe to', validators=[DataRequired(), Email()])
    amount = DecimalField('Amount', validators=[DataRequired()])
    subject = StringField('Subject')


class RequestOweForm(Form):
    debitor = StringField('Who owes me?', validators=[DataRequired(), Email()])
    amount = DecimalField('Amount', validators=[DataRequired()])
    subject = StringField('Subject')
