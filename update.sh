#!/bin/bash

git pull
source env/bin/activate
pip install -r requirements
if [ "$1" = "migrate" ]; then
   echo "Backuping db..."
   mkdir db_backup
   ./manage.py dumpdata > db_backup/`date +"%y%m%d-%H:%M:%S"`-aklub.json
   echo "Migrating..."
   ./manage.py migrate
fi
(cd apps/aklub/ && django-admin.py compilemessages)
./manage.py collectstatic --noinput
touch wsgi.py
