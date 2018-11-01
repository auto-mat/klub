release: python manage.py migrate
web: gunicorn wsgi --timeout ${GUNICORN_TIMEOUT:-"60"} --workers ${GUNICORN_WORKERS:-"6"}
