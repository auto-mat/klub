Auto\*mat klub
============
[![Build Status](https://travis-ci.org/auto-mat/klub.svg?branch=master)](https://travis-ci.org/auto-mat/klub)
[![Coverage Status](https://coveralls.io/repos/github/auto-mat/klub/badge.svg?branch=master)](https://coveralls.io/github/auto-mat/klub?branch=master)

Instalace
============

Ke zprovoznění je zapotřebí následující

* Virtualenv
* Postgres 8.4 + postgis 1.5
* pipenv

Vzorová lokální konfigurace je v `.env-sample`, stačí přejmenovat na `.env` a doplnit SECRET\_KEY.

Instalace probíhá pomocí následujícíh příkazů:

* sudo apt-get install libgraphviz-dev
* pipenv install
* pipenv shell
* python manage.py compilemessages -l "cs_CZ"

Instalace (Docker compose)
==========================

    $ docker-compose build
    $ docker-compose up

    $ docker attach klub_web_1
    # su test
    $ pipenv shell
    $ export PYTHONPATH=/klub-v
    $ cd apps/aklub && django-admin.py compilemessages -l cs_CZ
    $ django-admin.py migrate
    $ django-admin.py createsuperuser
    # Set django Site object domain name
    $ python manage.py shell
    # 'localhost' if app will run on localhost
    >>> from django.contrib.sites.models import Site
    >>> Site.objects.create(name='localhost', domain='localhost')
    >>> exit()

Spuštění
============

Pro testovací účely spustíte projekt pomocí následujícího příkazu:

* env/bin/python manage.py runserver 0.0.0.0:8000


Heroku
======

````
heroku config:set BUILD_WITH_GEO_LIBRARIES=1 (DEPRICATED duben 2020) => nadále neni třeba
````

Nejdřív musíš [povolit heroku.yml](https://devcenter.heroku.com/articles/buildpack-builds-heroku-yml)

Pak je důležité, aby buildpacky byli ve správném pořádi. Tj. nodejs, musí mít index=1.

Více informace o buildpackech nalezntete [zde](https://devcenter.heroku.com/articles/using-multiple-buildpacks-for-an-app).
