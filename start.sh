#!/usr/bin/env bash
docker run -d --restart unless-stopped -it -v $(pwd)/config.yaml:/app/config.yaml --name ipmi2mqtt ipmi2mqtt:latest
