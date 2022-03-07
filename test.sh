#!/usr/bin/env bash
docker run --rm -it -v $(pwd)/config.yaml:/app/config.yaml ipmi2mqtt:latest
