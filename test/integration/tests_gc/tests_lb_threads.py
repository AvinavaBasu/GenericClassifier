"""
Below tests are added as part of story ELC-1495.
To test if load balancer supports least outstanding requests.
The request is sent to ELB and the test will not know on which node the
request is sent.

To check if the requests are sent to both the nodes, then the logs
has to be checked either on direct container logs or ELK.
This test does not provide details on which node a request is processed.
This test only generates a request or its a client and the logs has to be
checked on ELK/container logs.
"""

import test.integration.tests_gc.base_test as base_test
from pytest import mark
import pytest
import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import Future


@mark.load_balancer_thread
@mark.aws_tests
@mark.load_balancer
class LoadBalancerTests:
    """
    Load balancer tests using threads and not co-operative multi tasking (asyncio).
    """
    def test_lb_threads(self, app_config, env, load_balancer):
        """
        Tests for checking the requests follows least outstanding requests in load balancer.
        :param app_config: app_config fixture from conftest.py
        :param env : environment
        :param load_balancer: load_balancer
        :return:
        """
        if load_balancer == "False":
            pytest.skip("API LB Run threads : "
                        "Skipping test to check for the "
                        "least outstanding requests test case.")
        logging.info(f"API LB Run threads : Start of LB threads tests on {env}.")
        try:
            input_file_25 = base_test.load_input_csv_file("lb_threads_example",
                                                          "integration/input/input_25.csv")
            input_file_90k = base_test.load_input_csv_file("lb_threads_100k",
                                                           "integration/input/input_100k.csv")
            input_file_list = [input_file_25 for index in range(0, 250)]
            input_file_list.insert(0, input_file_90k)
            input_file_list.insert(10, input_file_90k)
            input_file_list.insert(20, input_file_90k)
            logging.info(input_file_list)
            work = []
            with ThreadPoolExecutor(max_workers=5) as executor:
                for file in input_file_list:
                    f: Future = executor.submit(base_test.invoke_url_invocations, app_config.tls + "://" +
                                                app_config.host + "/" +
                                                "invocations",
                                                file,
                                                "text/plain",
                                                "file",
                                                "load balancer")
                    work.append(f)

                logging.info("API LB Run threads : Waiting for completion of all files invocation...")
            logging.info("API LB Run threads : Completed processing all files")
            failed = False
            for f in work:
                logging.info(f"API LB Run threads: request {f.result()[1]}"
                             f" has status code : {f.result()[0].status_code}")
                if f.result()[0].status_code != 200:
                    logging.error(f"API LB Run threads : Error found for request {f.result()[1]} "
                                  f"{f.result()[0].content}")
                    failed = True
            if failed:
                pytest.fail()
            logging.info(f"API LB Run threads : End of LB threads tests on {env}.")
        except Exception:
            logging.error(f"API LB Run threads : Caught with processing error ", exc_info=True)
            pytest.fail()
