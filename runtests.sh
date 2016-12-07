#!/bin/bash -e
if [ -z "$@" ]; then
   env/bin/coverage run manage.py test aklub
else
   env/bin/coverage run manage.py test $@
fi
env/bin/coverage html
