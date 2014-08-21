import os

import psycopg2
import psycopg2.extras
from flask import g

from zerosum import app


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'db_conn'):
        g.db_conn = psycopg2.connect(
            os.environ['OPENSHIFT_POSTGRESQL_DB_URL'],
            cursor_factory=psycopg2.extras.NamedTupleCursor
        )
    return g.db_conn


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'db_conn'):
        if error is None:
            g.db_conn.commit()
        g.db_conn.close()
