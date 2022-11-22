#!/bin/bash
docker-compose down
docker-compose up -d
exec docker exec -it klub_web_1 bash
