#!/bin/bash
sh ./release.sh
python3 manage.py createsuperuser2 --username=admin --password=$REVIEW_APP_PASSWORD
