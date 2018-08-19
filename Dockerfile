FROM petrdlouhy/dopracenakole
RUN curl -sL https://deb.nodesource.com/setup_10.x | bash -
RUN apt-get -qq update; apt-get -y install nodejs gettext libgettextpo-dev libgraphviz-dev
RUN npm install -g less bower
ADD requirements.freeze.txt requirements.freeze.txt
RUN pip3 install --exists-action i -r requirements.freeze.txt
ADD requirements-test.txt requirements-test.txt
RUN pip3 install -r requirements-test.txt
RUN useradd test
RUN chsh test -s /bin/bash
RUN mkdir /home/test ; chown test /home/test ; chgrp test /home/test
