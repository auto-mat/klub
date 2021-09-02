FROM python:3.6-buster

RUN curl -sL https://deb.nodesource.com/setup_14.x | bash -
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

RUN useradd test
RUN chsh test -s /bin/bash
RUN mkdir /home/test ; chown test /home/test ; chgrp test /home/test
RUN npm install -g bower
RUN mkdir -p /var/log/django/

copy requirements.txt requirements.txt
RUN su test ; pip3 install -r requirements.txt
copy . .
RUN SECRET_KEY="fake_key" python3 manage.py bower install
RUN SECRET_KEY="fake_key" python3 manage.py compilemessages
RUN SECRET_KEY="fake_key" python3 manage.py collectstatic --noinput
