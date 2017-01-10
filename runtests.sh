#!/bin/bash -e
if [ -z "$@" ]; then
   coverage run manage.py test aklub
else
   coverage run manage.py test $@
fi
coverage html
