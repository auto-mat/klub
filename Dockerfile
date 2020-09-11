FROM petrdlouhy/dopracenakole
RUN curl -sL https://deb.nodesource.com/setup_10.x | bash -
RUN apt-get -qq update; apt-get -y install nodejs gettext libgettextpo-dev libgraphviz-dev
RUN npm install -g less bower
RUN pip3 install pipenv
RUN useradd test
RUN chsh test -s /bin/bash
RUN mkdir /home/test ; chown test /home/test ; chgrp test /home/test
RUN su test -c 'cd /home/test ; pipenv install --dev --python python3'
