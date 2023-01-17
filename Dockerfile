FROM python:3.9-bullseye

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

ARG UID
RUN useradd test --uid $UID
RUN chsh test -s /bin/bash
RUN mkdir /home/test ; chown test /home/test ; chgrp test /home/test
RUN npm install -g bower
RUN mkdir -p /var/log/django/

copy requirements.txt requirements.txt
RUN su test ; pip3 install --default-timeout=100 -r requirements.txt
copy . .
RUN bash -c "export SECRET_KEY='fake_key'; \
    python3 manage.py bower install \
    && python3 manage.py compilemessages --ignore=third-party/* \
    && python3 manage.py collectstatic --noinput"
