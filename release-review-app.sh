#!/bin/bash
sh ./release.sh
python3 manage.py createsuperuser2 --username=admin --password=$REVIEW_APP_PASSWORD  --noinput --email 'blank@email.com'
python3 manage.py loaddata apps/aklub/fixtures/conditions.json
python3 manage.py dump_data
