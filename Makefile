docker-compose: Dockerfile
	mkdir -p venv
	mkdir -p db
	sudo docker-compose build --build-arg UID=$(shell id -u)
