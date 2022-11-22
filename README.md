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

    $ cp .env-sample .env
    $ $EDITOR .env

    $ docker-compose build --build-arg UID=$UID
    $ docker-compose up

In a new terminal run

    $ docker exec -it klub_web_1 bash
    $ cd apps/aklub && django-admin.py compilemessages -l cs_CZ && cd ../../
    $ python manage.py migrate
    $ python manage.py createsuperuser2

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
