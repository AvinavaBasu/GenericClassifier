"""
Code to run tests for specified number of mins i.e. as mentioned in input execute_number_of_mins.
"""

import test.integration.tests_gc.base_test as base_test
from pytest import mark
import pytest
import time
import ntpath
import logging
import os


@mark.aws_tests
@mark.recurring
class RecurringTests:
    """
    Code to run tests for specified number of mins i.e. as mentioned in input execute_number_of_mins.
    """
    url = "{}://{}/{}"
    failed = False

    def test_recurring_for_provided_minutes(self,
                                            app_config,
                                            split_count,
                                            execute_number_of_mins):
        """
        Code to run tests for specified number of mins i.e. as mentioned in input execute_number_of_mins.
        :param app_config: app_config fixture from conftest.py
        :param split_count: split_count as input
        :param execute_number_of_mins: execute_number_of_mins
        :return:
        """
        if execute_number_of_mins is None or int(execute_number_of_mins) <= 0:
            pytest.skip("Please pass execute_number_of_mins or pass valid execute_number_of_mins "
                        "when running test related to recurring runs, \n"
                        "For example: pytest -m recurring --env uat --execute_number_of_mins 60")
        logging.info(f"API recurring test : Execute for {execute_number_of_mins} mins")
        t_end = time.time() + 60 * int(execute_number_of_mins)  # Add execute_number_of_mins to current time
        input_file_90k = base_test.load_input_csv_file("recurring",
                                                       "integration/input/input_100k.csv")
        success_split = base_test.split_file_equal_numbers(input_file_90k,
                                                           split_count,
                                                           os.path.
                                                           splitext(ntpath.basename(input_file_90k))[0])
        logging.info(f"API recurring test : current time {time.time()} and ending time {t_end}")
        if not success_split:
            pytest.fail("API recurring test : Could not split the file as expected.")
        lst_files = base_test.read_split_files(input_file_90k)
        logging.info(f"API recurring test : Starting recurring runs")
        count = 1
        while time.time() < t_end:
            try:
                logging.info(f"API recurring test : Start of Iteration number {count}")
                start_timer = time.perf_counter()
                for file in lst_files:
                    self.url = self.url.format(app_config.tls, app_config.host, "invocations")
                    results = base_test.invoke_url_invocations(self.url,
                                                               file,
                                                               "text/plain",
                                                               "file",
                                                               "recurring")
                    if results[0].status_code != 200:
                        logging.error(f"API recurring test: Non 200 response found for request,"
                                      f" with file {results[1]}, so, ending the test.")
                        pytest.fail()
                    else:
                        logging.info(f"API recurring test: 200 response found for request,"
                                     f" with file {results[1]}.")
                end_timer = time.perf_counter()
                logging.info(f"API recurring test: Finished test with recurring runs "
                             f"in {round(end_timer - start_timer, 3)} second(s) for "
                             f"{ntpath.basename(input_file_90k)}_batch")
                logging.info(f"API recurring test : End of Iteration number {count}")
                count += 1
                time.sleep(10)
            except Exception as exception:
                logging.exception(f"API recurring test : Exceptions - "
                                  f"{exception}", exc_info=True)
                pytest.fail()
        logging.info("API recurring test : ending recurring runs")
