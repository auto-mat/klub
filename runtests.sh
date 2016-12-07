#!/bin/bash -e
env/bin/coverage run manage.py test $@
env/bin/coverage html
