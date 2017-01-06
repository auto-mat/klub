#!/bin/sh
./env/bin/python manage.py send_queued_mail >> /var/log/django/send_mail.log 2>&1
