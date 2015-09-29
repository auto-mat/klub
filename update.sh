#!/bin/bash
#version 0.3

app_name=aklub
db_name=klub

error() {
   printf '\E[31m'; echo "$@"; printf '\E[0m'
}

if [[ $EUID -eq 0 ]]; then
   error "This script should not be run using sudo or as the root user"
   exit 1
fi

source update_local.sh

set -e

if [ "$1" = "reinstall" ]; then
   rm env -rf
   virtualenv --no-site-packages env
fi

git pull
source env/bin/activate
env/bin/python env/bin/pip install -r requirements --upgrade
if [ "$1" = "migrate" ]; then
   echo "Backuping db..."
   mkdir -p db_backup
   sudo -u postgres pg_dump $db_name > db_backup/`date +"%y%m%d-%H:%M:%S"`.sql
   echo "Migrating..."
   env/bin/python ./manage.py migrate
fi
(cd apps/aklub/ && django-admin.py compilemessages)
env/bin/python ./manage.py collectstatic --noinput
touch wsgi.py
type supervisorctl && sudo supervisorctl restart $app_name
env/bin/python ./manage.py denorm_drop
env/bin/python ./manage.py denorm_init

echo "App succesfully updated"
