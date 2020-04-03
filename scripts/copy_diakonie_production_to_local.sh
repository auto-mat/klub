#!/bin/bash
sudo su postgres -c "dropdb diakonie-live"
heroku pg:pull klub-diakonie-real-production::DATABASE_URL postgresql://dpnk:@localhost/diakonie-live --app klub-diakonie-real-production
python manage.py shell -c "from django.contrib.sites.models import Site; Site.objects.update(domain='localhost:8001')"
