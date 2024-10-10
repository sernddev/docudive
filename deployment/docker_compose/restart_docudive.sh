#!/bin/bash


docker compose -f  docker-compose.dev.new.ssl.gpu.yml -p docudive-stack  down

echo 'starting containers'

docker compose -f  docker-compose.dev.new.ssl.gpu.yml -p docudive-stack  up  -d


