"""
Below tests are added as part of story ELC-1495.
To test if load balancer supports least outstanding requests.
The request is sent to ELB and the test will not know on which node the
request is sent.

To check if the requests are sent to both the nodes, then the logs
has to be checked either on direct container logs or ELK.
This test does not provide details on which node a request is processed.
This test only generates a request or its a client and the logs has to be
check on ELK/container logs.
"""

import test.integration.tests_gc.base_test as base_test
from pytest import mark
import pytest
import json
import logging
import asyncio
import aiohttp


@mark.load_balancer_asyncio
@mark.aws_tests
@mark.load_balancer
class LoadBalancerTests:
    """
    Load balancer tests using asyncio.
    """
    def test_lb_asyncio(self, app_config, env, load_balancer):
        """
        Tests for checking the requests follows least outstanding requests in load balancer.
        :param app_config: app_config fixture from conftest.py
        :param env: environment
        :param load_balancer: load_balancer
        :return:
        """
        if load_balancer == "False":
            pytest.skip("API LB Run asyncio : "
                        "Skipping test to check for the  "
                        "least outstanding requests test case.")
        logging.info(f"API LB Run asyncio  : Start of LB asyncio tests on {env}.")
        try:
            input_file_25 = base_test.load_input_csv_file("lb_asyncio_example",
                                                          "integration/input/input_25.csv")
            logging.info(input_file_25)
            input_file_90k = base_test.load_input_csv_file("lb_asyncio_example",
                                                           "integration/input/input_100k.csv")
            input_file_list = [input_file_25 for index in range(0, 250)]
            input_file_list.insert(0, input_file_90k)
            input_file_list.insert(10, input_file_90k)
            input_file_list.insert(20, input_file_90k)
            logging.info(input_file_list)
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main(input_file_list,
                                         app_config.tls,
                                         app_config.host))
            loop.close()
            logging.info(f"API LB Run asyncio  : End of LB asyncio tests on {env}.")
        except Exception:
            logging.error(f"API LB Run asyncio  : Caught with processing error ", exc_info=True)
            pytest.fail()


async def main(input_file_list, tls, host):
    """
    Main async function.
    :param input_file_list: input from where input files are read.
    :param tls:
    :param host:
    :return:
    """
    async with aiohttp.ClientSession() as session:
        values = await asyncio.gather(*(_worker(f'{n}', session, input_file_list[n], tls, host)
                                        for n in range(0, len(input_file_list))))
    logging.info(f"API LB Run asyncio  : Final Output => {values}")
    failed = False
    for value in values:
        if value[0] is False:
            logging.error(f"API LB Run asyncio : Worker {value[1]} failed with data {value[3]} "
                          f"and error status code {value[2]}")
            failed = True
        else:
            logging.info(f"API LB Run asyncio : Worker {value[1]} success with data {value[3]} "
                         f"and status code {value[2]}")
    if failed:
        pytest.fail()
    logging.info("API LB Run asyncio  : ")


async def _worker(name, session, data, tls, host):
    logging.info(f"API LB Run asyncio  : Invoking worker-{name} with file - {data}.")
    try:
        with open(data, 'r', encoding='utf-8') as gc_file:
            response = await session.post(headers={"Content-Type": "text/plain"
                                                   , 'tracker-id': data},
                                          data=gc_file.read().strip().encode('utf-8'),
                                          url=tls + "://" + host + "/" + "invocations")
            ret_code = response.status
            if ret_code == 200:
                value = await response.text()
                value = json.loads(value)
            else:
                logging.error(f"API LB Run asyncio  : Return value {ret_code} for file: {data} "
                              f"and worker worker-{name}.")
                return [False, f"worker-{name}", ret_code, data]
        logging.info(f"API LB Run asyncio  : Completed processing of worker-{name} with file - {data}.")
        return [value.get('generic_classifier'), f"worker-{name}", ret_code, data]
    except Exception:
        logging.error("API LB Run asyncio  : Failed with exception ", exc_info=True)
        return [False, f"worker-{name}", 504, data]

