import os

from flask import Flask, render_template, redirect, url_for, request
from flask.ext.login import current_user, login_required

from login import init_login

app = Flask(__name__)
# TODO: get the secret from somewhere else
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'


@app.route("/")
@login_required
def home():
    cur = conn.cursor()
    cur.execute("SELECT * FROM owe")
    rows = cur.fetchall()

    user = current_user

    return render_template('index.html', user=user)
    #return "Hello World!" + repr(rows)


if __name__ == "__main__":
    debug = bool(os.environ.get('FLASK_DEBUG', False))
    init_login(app)
    app.run(debug=debug)
