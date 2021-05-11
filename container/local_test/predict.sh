#!/bin/bash

###################################################################################################
# Use this script to check for execution of gc.
# Example : ./predict.sh payload/gc/payload
###################################################################################################

payload=$1
port=9081

curl --data-binary @${payload} -H "Content-Type: text/plain" -v http://localhost:$port/invocations
