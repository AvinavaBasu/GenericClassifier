"""
This module is to be used for smoke tests.
"""
import test.integration.tests_gc.base_test as base_test
from pytest import mark
import pytest
import logging


@mark.smoke_tests
@mark.aws_tests
class EndPointsTests:
    """
    Contains end points tests for ping and invocations.
    """
    url = "{}://{}/{}"

    @mark.ping
    def test_ping(self, app_config, env):
        logging.info(f"API Smoke Test for ping Run : Started test to cover ping test")
        response = base_test.invoke_url_get_method(self.url.format(app_config.tls,
                                                                   app_config.host,
                                                                   "ping"),
                                                   "ping")
        if response.status_code != 200:
            logging.error(f"API Smoke Test ping Run : ping request does not return 200 response, "
                          f"instead returns {response.status_code} for environment {env}")
            pytest.fail()
        else:
            logging.info(f"API Smoke Test ping Run : ping request returned 200 response "
                         f"for environment {env}")

    @mark.execution_parameters
    def test_execution_parameters(self, app_config, env):
        logging.info(f"API Smoke Test execution-parameters Run : "
                     f"Started test to cover execution-parameters test")
        response = base_test.invoke_url_get_method(self.url.format(app_config.tls,
                                                                   app_config.host,
                                                                   "execution-parameters"),
                                                   "execution-parameters")
        if response.status_code != 200:
            logging.error(f"API Smoke Test execution-parameters Run : "
                          f"execution-parameters request does not return 200 response, "
                          f"instead returns {response.status_code} for environment {env}")
            pytest.fail()
        else:
            logging.info(f"API Smoke Test execution-parameters Run : "
                         f"execution-parameters request returned 200 response "
                         f"for environment {env}")
            assert response.json().get("MaxConcurrentTransforms") == 1
            assert response.json().get("BatchStrategy") == 'MULTI_RECORD'
            assert response.json().get("MaxPayloadInMB") == 5

    @mark.invocations_success
    def test_invocations(self, app_config, env):
        data = {
            "Hospital Lagomaggiore": "SPE",
            "Department Of Chemistry": "GEN",
            "Government Postgraduate College": "SPE",
            "St. John's Institute Of Dermatology": "SPE",
            "Tulane Univ. Sch. Med.": "SPE",
            "Rashtrasant Tukdoji Maharaj Nagpur University": "SPE",
            "Botanic Gardens Of Toyama": "SPE",
            "Eawag/eth": "GEN",
            "Max-planck Institute For Astronomy": "SPE",
            "Intl. Ctr. Of Insect Physiol./ecol.": "GEN"
        }
        logging.info(f"API Smoke Test invocations Run : Started test to cover invocations test")
        failed = False
        for key, value in data.items():
            response = base_test.invoke_url_invocations(self.url.format(app_config.tls,
                                                                        app_config.host,
                                                                        "invocations"),
                                                        key,
                                                        "text/plain",
                                                        "input",
                                                        "invocations")
            if response[0].status_code != 200:
                logging.error(f"API Smoke Test invocations Run : "
                              f"invocations request does not return 200 response, "
                              f"instead returns {response[0].status_code} for environment {env}")
                failed = True
            else:
                logging.info(f"API Smoke Test invocations Run : "
                             f"invocations request returned 200 response "
                             f"for environment {env}")
                if response[0].json().get('generic_classifier')[0] != data[key]:
                    logging.error(f"API Smoke Test invocations Run : "
                                  f"invocations request returned response for "
                                  f"org string {key} is {response[0].json().get('generic_classifier')} "
                                  f"for environment {env}")
                    failed = True
        if failed:
            pytest.fail()

    @mark.invocations_fail
    def test_invocations_failure_scenario(self, app_config, env):
        data = {
            "Hospital Lagomaggiore": "SPE"
        }
        logging.info(f"API Smoke Test invocations failure Run : "
                     f"Started test to cover invocations test")
        failed = False
        for key, value in data.items():
            response = base_test.invoke_url_invocations(self.url.format(app_config.tls,
                                                                        app_config.host,
                                                                        "invocations"),
                                                        key,
                                                        "application/json",
                                                        "input",
                                                        "invocations")
            if response[0].status_code != 415:
                logging.error(f"API Smoke Test invocations failure Run : "
                              f"invocations request does not return 415 response, "
                              f"instead returns {response[0].status_code} for environment {env}")
                failed = True
            else:
                logging.info(f"API Smoke Test invocations failure Run : "
                             f"invocations request returned 415 response "
                             f"for environment {env} which is as expected.")
        if failed:
            pytest.fail()
