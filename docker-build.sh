#!/bin/sh

export DOCKER_BUILDKIT=1

#sample of build arg
#--build-arg="APP_DIR="

docker build --no-cache -t ytdlp .