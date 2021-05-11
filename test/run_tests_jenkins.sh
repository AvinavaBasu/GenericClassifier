#!/bin/bash

TEST_TYPE=$1
ENV=$2
SPLIT_COUNT=$3
LOAD_BALANCER=$4
EXPECTED_MINS=$5

if [[ -z $SPLIT_COUNT ]]
then
  echo "SPLIT_COUNT value is not provided, using default values."
  SPLIT_COUNT=1000
fi

if [[ -z $LOAD_BALANCER ]]
then
  echo "LOAD_BALANCER value is not provided, using default values."
  LOAD_BALANCER=False
fi

if [[ -z $EXPECTED_MINS ]]
then
  echo "EXPECTED_MINS value is not provided, using default values."
  EXPECTED_MINS=0
fi

pytest -v -m $TEST_TYPE --env $ENV --split_count $SPLIT_COUNT --load_balancer $LOAD_BALANCER --execute_number_of_mins $EXPECTED_MINS -s --junit-xml="BUILD_${BUILD_NUMBER}_${TEST_TYPE}_${ENV}_reports.xml"
