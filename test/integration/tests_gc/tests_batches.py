"""
Below tests are added as part of story ELC-1690 for checking the ideal batch size.
"""

import test.integration.tests_gc.base_test as base_test
from pytest import mark
import pytest
import logging
import os
import time
import ntpath
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import Future


@mark.batches
@mark.aws_tests
class BatchTests:
    """
    Split the input request into batches as set in settings.py file and parameter split_count.
    """
    def test_batches(self, app_config, env, split_count):
        """
        Tests for checking the requests follows least outstanding requests in load balancer.
        :param app_config: app_config fixture from conftest.py
        :param env : environment
        :param split_count: split_count
        :return:
        """
        logging.info(f"API batch run threads : Start of batch tests on {env}.")
        try:
            input_file_90k = base_test.load_input_csv_file("batch",
                                                           "integration/input/input_100k.csv")
            return_split_status = base_test.split_file_equal_numbers(input_file_90k,
                                                                     split_count,
                                                                     os.path.
                                                                     splitext(ntpath.basename(input_file_90k))[0])
            if not return_split_status:
                logging.error(f"API batch run threads : "
                              f"Could not split files, ending the tests.")
            work = []
            lst_files = base_test.read_split_files(input_file_90k)
            logging.info(lst_files)
            start_timer = time.perf_counter()
            with ThreadPoolExecutor(max_workers=5) as executor:
                for file in lst_files:
                    f: Future = executor.submit(base_test.invoke_url_invocations, app_config.tls + "://" +
                                                app_config.host + "/" +
                                                "invocations",
                                                file,
                                                "text/plain",
                                                "file",
                                                "batches")
                    work.append(f)
                logging.info("API batch run threads : Waiting for completion of all files invocation...")
            logging.info("API batch run threads : Completed processing all files")
            end_timer = time.perf_counter()
            logging.info(f"API batch run threads : "
                         f"Finished API invocation for batch "
                         f"in {round(end_timer - start_timer, 3)} second(s) for "
                         f"{os.path.splitext(ntpath.basename(input_file_90k))[0]}_batch")
            failed = False
            for ret_value in work:
                logging.info(f"API batch run threads: Status code of {ret_value.result()[1]} is "
                             f"request : {ret_value.result()[0].status_code}")
                logging.info(f"API batch run threads: Output : {ret_value.result()[0].content}")
                if ret_value.result()[0].status_code != 200:
                    logging.error(f"API batch run threads : Error found for request {f.result().content}")
                    failed = True
            if failed:
                pytest.fail()
        except Exception:
            logging.error(f"API batch run threads : Caught with processing error ", exc_info=True)
            pytest.fail()
