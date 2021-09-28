#!/usr/bin/python3
import shutil
import subprocess
import os
import time

####
# GLOBALS
####
bronto_dump = "/home/timothy/pr/auto-mat/kp-backups/brontosaurus/"
bronto_dump_file = "bis.20210413-0910.sql"
maria_container_name = "bronto_maria"
kp_network_name = "klub_default"
kp_web_container = "klub_web_1"

####
# START
####

def docker_compose(*args):
    args = ["docker-compose"] + list(args)
    print("###############################################")
    print("$ " + " ".join(args))
    subprocess.run(args)
    print("\n")

def docker(*args):
    args = ["docker"] + list(args)
    print("###############################################")
    print("$ " + str(args))
    subprocess.run(args)
    print("\n")

docker("stop", maria_container_name)
docker("rm", maria_container_name)
docker("run", "--publish", "3306:3306", "-e", "MYSQL_ALLOW_EMPTY_PASSWORD=yes", "-e", "MYSQL_DATABASE=bronto", "--name", maria_container_name, "--detach", "-v", bronto_dump + ":/bronto", "mariadb")
docker_compose("down")
docker_compose("rm")
try:
    shutil.rmtree("./db")
except FileNotFoundError:
    pass
os.mkdir("./db")
docker_compose("up", "--detach")
docker("network", "connect", kp_network_name, maria_container_name)
time.sleep(3)
print("Loading db dump into mariadb...")
docker("exec", maria_container_name, "bash", "-c", "mysql -uroot -hlocalhost -P 3306 --protocol=tcp -Dbronto < bronto/" + bronto_dump_file)
docker("exec", kp_web_container, "venv/bin/python3", "manage.py", "migrate")
docker("exec", kp_web_container, "venv/bin/python3", "manage.py", "bronto_migrate", "--dbhost", maria_container_name, "--dbuser", "root", "--db", "bronto")
docker("exec", "-it", kp_web_container, "venv/bin/python3", "manage.py", "createsuperuser2")
