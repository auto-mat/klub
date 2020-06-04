#!/bin/bash -e
if [ -z "$@" ]; then
   coverage run manage.py test aklub
   coverage run manage.py test api
else
   coverage run manage.py test $@
fi
coverage html
