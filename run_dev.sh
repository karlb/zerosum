. venv/bin/activate
export FLASK_DEBUG=true
export OPENSHIFT_POSTGRESQL_DB_URL='dbname=zerosum'
export OPENSHIFT_SECRET_TOKEN='insecure-token-for-local-dev'
python3 wsgi/runserver.py
