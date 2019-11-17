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

run pip3 install pipenv

RUN npm install -g less bower sass
RUN pip3 install pipenv==2018.11.14
RUN useradd test
RUN chsh test -s /bin/bash
RUN mkdir /home/test ; chown test /home/test ; chgrp test /home/test
RUN su test ; cd /home/test ; pipenv install --dev --python python3
