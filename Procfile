release: python manage.py migrate && python ./manage.py denorm_drop && python ./manage.py denorm_init
web: gunicorn wsgi --timeout ${GUNICORN_TIMEOUT:-"60"} --workers ${GUNICORN_WORKERS:-"6"}
