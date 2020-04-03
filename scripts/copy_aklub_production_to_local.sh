#!/bin/bash
sudo su postgres -c "dropdb aklub-live"
heroku pg:pull klub-automat-production::DATABASE_URL postgresql://dpnk:@localhost/aklub-live --app klub-automat-production
python manage.py shell -c "from django.contrib.sites.models import Site; Site.objects.update(domain='localhost:8001')"
