from flask import redirect, url_for, request, render_template, flash
from flask.ext.login import LoginManager, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

from zerosum import app
from zerosum.db import get_db

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


class User:

    @classmethod
    def get(cls, user_id):
        cur = get_db().cursor()
        cur.execute("SELECT * FROM zerosum_user WHERE user_id = %s", [user_id])
        return cls(cur.fetchall()[0])

    def __init__(self, row):
        self.row = row
        self.nickname = row.email

    def __getattr__(self, attr):
        print(self.row)
        return getattr(self.row, attr)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        cur = get_db().cursor()
        cur.execute("""
            UPDATE zerosum_user SET password_hash = %s, is_active = true
            WHERE user_id = %s
        """, [self.password_hash, self.user_id])
        assert cur.rowcount == 1

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_active(self):
        return True

    def get_id(self):
        return self.user_id

    def is_authenticated(self):
        return True


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


def get_or_create_user(email):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM zerosum_user WHERE email = %s",
                [email])
    rows = cur.fetchall()
    if not rows:
        cur.execute("""
            INSERT INTO zerosum_user(email, name) VALUES (%(email)s, %(email)s)
            RETURNING *""",
                    dict(email=email))
        rows = cur.fetchall()
    return rows[0]


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        # get user
        cur = get_db().cursor()
        cur.execute("SELECT * FROM zerosum_user WHERE email = %s", [login])
        user = User(cur.fetchall()[0])
        if user.check_password(password):
            login_user(user)
            return redirect(url_for('home'))
    return render_template('login.html')


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


class FormError(Exception):

    def __init__(self, message):
        self.message = message


@app.route("/email_confirm/<string:code>", methods=['GET', 'POST'])
def email_confirm(code):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE email_confirm
        SET opened = current_timestamp
        WHERE code = %s
        RETURNING email
        """, [code])
    email = cur.fetchall()[0].email

    if request.method == 'POST':
        try:
            if email != request.form['email']:
                raise FormError('Invalid Email')
            if request.form['password'] != request.form['password2']:
                raise FormError('Passwords do not match')
            user = User(get_or_create_user(email))
            user.set_password(request.form['password'])

            login_user(user)
            flash('Created new user!', 'success')
            return redirect(url_for('home'))
        except FormError as e:
            flash(e.message, 'error')

    #cur.execute("""
    #        SELECT *
    #        FROM zerosum_user
    #        WHERE email = (
    #            SELECT email FROM email_confirm WHERE code = %s
    #        )
    #    """, [code])
    return render_template('register.html', email=email)
    #user = User(cur.fetchall()[0])
    #login_user(user)
    #return redirect(url_for('home'))
