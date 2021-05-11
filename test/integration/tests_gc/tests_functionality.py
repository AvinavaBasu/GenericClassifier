"""
Below tests are used for test of story ELC-384. Please refer story for more details.
This covers all scenarios related to test data from tests_input_data.json.
"""

import test.settings as settings
import test.integration.tests_gc.base_test as base_test
import csv
from pytest import mark
import pytest
import pandas as pd
import logging


@mark.regression
@mark.aws_tests
class FunctionalityTests:
    """
    Common code for regression testing of all scenarios.
    Picks input from input directory and expected output from expected_output directory.
    Validates if the every response received for each reference matches the data as mentioned in
    expected output file (present in expected_output directory).

    How to add new regression test?

    Please add input file in input directory and expected output file in expected_output directory,
    add corresponding details like input, output, success and failure files
    in tests_input_data.json with input and output data files and below test should pick it up.
    """
    url = "{}://{}/{}"
    failed = False

    def test_functionality(self, app_config, input_details_json, env):
        """
        Generic code to check results of each reference with expected output.
        :param app_config: app_config fixture from conftest.py
        :param input_details_json: input_details_json fixture from conftest.py
        :param env : environment
        :return:
        """
        failed_list = []
        success_list = []
        for key, value in input_details_json.items():
            logging.info(f"API Test {key} Run : Regression test to cover {key} tests")
            try:
                input_file = base_test.load_input_csv_file("functionality",
                                                           getattr(settings, f"{value.get('input_file')}"))
                expected_classification_output = base_test.load_expected_csv_file(
                    getattr(settings, f"{value.get('expected_file')}"))
                response = base_test.invoke_url_invocations(self.url.format(app_config.tls,
                                                                            app_config.host,
                                                                            "invocations"),
                                                            input_file,
                                                            "text/plain",
                                                            "file",
                                                            key)
                errors = []
                if response[0].status_code != 200:
                    errors.append(f"Status code is not 200 instead {response[0].status_code}")
                assert not errors, "Assert failures :\n{}".format("\n".join(errors))
                with open(input_file, 'r', encoding='utf-8') as aft_file:
                    org_string_list = []
                    reader = csv.reader(aft_file, delimiter="\n")
                    for row in reader:
                        org_string_list.append(row[0])
                for gc_index, classification_response in \
                        enumerate(response[0].json().get('generic_classifier')):
                    logging.info(f"API Test {key} Run : classification "
                                 f"from response - {classification_response}")
                    logging.info(f"API Test {key} Run : classification from expected data - "
                                 f"{expected_classification_output[gc_index]}")
                    diff = True if \
                        classification_response == expected_classification_output[gc_index] else False
                    if not diff:
                        logging.error(f"API Test {key} Run : Failed Comparison of "
                                      f"output from api response {classification_response} to "
                                      f"expected classification "
                                      f"{expected_classification_output[gc_index]} "
                                      f"for org string {org_string_list[gc_index]}")
                        self.failed = True
                        status = "Failed"
                        failed_list.append([str(org_string_list[gc_index]),
                                            str(expected_classification_output[gc_index]),
                                            str(classification_response),
                                            status])
                    else:
                        logging.info(f"API Test {key} Run : Success comparison of "
                                     f"output from api response {classification_response} to "
                                     f"expected classification {expected_classification_output[gc_index]}"
                                     f" for org string {org_string_list[gc_index]}")
                        status = "Success"
                        success_list.append([str(org_string_list[gc_index]),
                                            str(expected_classification_output[gc_index]),
                                            str(classification_response),
                                            status])
                if len(success_list) > 0:
                    self.create_file(success_list, env + '_' +
                                     getattr(settings, f"{value.get('success_output_file')}"))
                if self.failed:
                    self.create_file(failed_list, env + '_' +
                                     getattr(settings, f"{value.get('failure_output_file')}"))
                    pytest.fail()
            except Exception as exception:
                logging.exception(f"API Test {key} Run : Exceptions - "
                                  f"{exception}", exc_info=True)
                pytest.fail()

    @classmethod
    def create_file(cls, output_list, file_name):
        df = pd.DataFrame.from_records(output_list)
        df.columns = ["Org String",
                      "Expected classification from Linking/accuracy testing",
                      "Response classification from End-end Generic classifier run",
                      "Status"]
        df.to_csv(file_name,
                  index=False,
                  encoding='utf-8-sig')
