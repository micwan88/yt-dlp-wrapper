#!/bin/sh

set -x

ffmpeg -i $1 -i $2 -c:v copy -c:a copy $3
