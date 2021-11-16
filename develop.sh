#!/bin/bash
docker-compose up -d
exec docker exec -it klub_web_1 bash --init-file /klub-v/venv/bin/activate
