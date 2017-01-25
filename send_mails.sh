#!/bin/bash
source local_environment.sh
./env/bin/python manage.py send_queued_mail >> /var/log/django/send_mail.log 2>&1
