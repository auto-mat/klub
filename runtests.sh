#!/bin/bash -e
if [ -z "$@" ]; then
   coverage run manage.py test aklub
   coverage run manage.py test api
   coverage run manage.py test pdf_storage
   coverage run manage.py test notifications_edit
else
   coverage run manage.py test $@
fi
coverage html
