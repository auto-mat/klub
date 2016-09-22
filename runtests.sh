#!/bin/bash -e
env/bin/coverage run manage.py test aklub
env/bin/coverage html
