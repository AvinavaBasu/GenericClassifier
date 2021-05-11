How to run tests:
------------------
Execute script, from ${base_dir}/test directory.

To run all tests:
-----------------

$ bash run_tests_jenkins.sh aws_tests dev 500 True 600

where:

aws_tests : test type which runs all tests

dev - environment

500 - split so that each request has 500 org strings. Default is 1000.

True - send requests to check load balancer's least outstanding requests. Please note that this test does not bring down any aws instances to check for test cases 5 to 9 in above table.

Default is False (no checks for load balancer).

600 - runs for 600 mins (10 hours). Set for value in mins needed. Default is 60 mins.

Above command will run all the tests as below in dev env (use dev, uat and prod for respective envs):

Test for functionality


Load balancer tests. This runs using asyncio and threads based approach.

Smoke tests

Checks for ideal batch size based on parameter split_count which by default is 1000

Recurring test which runs for pre-defined time based on parameter execute_number_of_mins which by default is 60 mins.

So, essentially all tests will be run when test_type is aws_tests.


To only run for functionality (This is default set with CI/CD):
-------------------------------------------------

$ bash run_tests_jenkins.sh functionality dev

This will only run the test where match with result of API and expected output is compared.

To specifically run so as to check the effective batch size:
------------------------------------------------------

$ bash run_tests_jenkins.sh batch dev

To specifically run so as to check the LB least outstanding requests:
-----------------------------------------------------------

$ bash run_tests_jenkins.sh load_balancer dev
