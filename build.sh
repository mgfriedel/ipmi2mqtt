#!/usr/bin/env bash
docker build -t ipmi2mqtt:latest .
docker image prune -f
