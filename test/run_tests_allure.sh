#!/bin/bash

# https://github.com/allure-framework/allure2/issues/813
# Example : run_tests_allure.sh regression dev
# 3 steps : run pytest, store history and generate allure results

TEST_TYPE=$1
ENV=$2

pytest -v -m $TEST_TYPE --env $ENV --alluredir allure-results
cp -r ./allure-report/history/ ./allure-results
allure generate ./allure-results/ -o ./allure-report/ --clean
