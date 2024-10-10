#!/bin/bash
docker compose -f docker-compose.dev.new.ssl.gpu.yml -p docudive-stack build web_server
