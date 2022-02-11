Auto\*mat klub
============
[![Build Status](https://travis-ci.org/auto-mat/klub.svg?branch=master)](https://travis-ci.org/auto-mat/klub)
[![Coverage Status](https://coveralls.io/repos/github/auto-mat/klub/badge.svg?branch=master)](https://coveralls.io/github/auto-mat/klub?branch=master)

Documentation
=================

[Docs](./docs/index.md)

Instalation
============

Copy `.env-sample`, to `.env` and change the CHANGE_MEs.

Instalace (Docker compose)
==========================

    $ docker-compose build
    $ docker-compose up

There will be errors that celery cannot be found, ignore them.

In a new terminal run

    $ docker attach klub_web_1
    $ virtualenv venv --activators bash,fish
    $ source venv/bin/activate
    $ pip3 install -r requirements.txt
    $ cd apps/aklub && django-admin.py compilemessages -l cs_CZ && cd ../../
    $ django-admin.py migrate
    $ django-admin.py createsuperuser2

Set django Site object domain name

    $ python manage.py shell

'localhost' if app will run on localhost

    >>> from django.contrib.sites.models import Site
    >>> Site.objects.create(name='localhost', domain='localhost')
    >>> exit()
    $ exit


Running
========

For development use

    $ ./develop.sh

To launch the dev environment. To launch the development web server run

    python manage.py runserver 0.0.0.0:8000

Other usefull commands are

Run formatter

    ./runblack.sh

Run test suit

    pytest apps

Run other test suit

    python3 manage.py test

Run a single test

    ./single-pytest.sh path/to/unit/file.py


K8S
======

[Configuration can be found here](https://github.com/auto-mat/k8s#adding-new-klub-p%C5%99atel-instances)
