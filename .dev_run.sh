#!/bin/bash

source .environ

docker build -t xtract:0.1 .
docker run --env APP_HOST --env APP_PORT --env DB_USER --env DB_PASSWD --env DB_HOST --env DB_NAME -p 9000:9000 xtract:0.1