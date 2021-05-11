#!/bin/sh

image=$1
local_port=$2
model_location=$3

docker run \
       -v $model_location:/opt/ml/model/ \
       -p $local_port:8080 \
       -e MODEL_SERVER_WORKERS=1 \
       -e MODEL_SERVER_TIMEOUT=600 \
       --cpus=1 \
       --memory=7g \
       --rm ${image} \
       serve
