FROM python:3.6

RUN curl -sL https://deb.nodesource.com/setup_10.x | bash -
run apt-get update && apt-get install -y \
   binutils \
   gdal-bin \
   gettext \
   git \
   gunicorn \
   libfreetype6-dev \
   libgeos-dev \
   libjpeg-dev \
   liblcms2-dev \
   memcached \
   poppler-utils \
   postgresql-common \
   zlib1g-dev \
   nodejs \
   libgettextpo-dev \
   libgraphviz-dev

run mkdir /home/aplikace -p
WORKDIR "/home/aplikace"

RUN pip3 install pipenv==2020.11.15
RUN useradd test
RUN chsh test -s /bin/bash
RUN mkdir /home/test ; chown test /home/test ; chgrp test /home/test
RUN npm install -g bower
RUN mkdir -p /var/log/django/

copy Pipfile.lock Pipfile.lock
copy Pipfile Pipfile
RUN su test ; pipenv install --dev --python python3.6
copy . .
RUN SECRET_KEY="fake_key" pipenv run python manage.py bower install
RUN SECRET_KEY="fake_key" pipenv run python manage.py compilemessages
RUN SECRET_KEY="fake_key" pipenv run python manage.py collectstatic --noinput
