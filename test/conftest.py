import test.settings as settings
from test.config import Config
import json
from pytest import fixture
import logging
import shutil
import os
import glob


# logging.FileHandler should be specified with 'utf-8' when dealing with writing to log file only (and not console),
# else python assumes the system default encoding while writing to log file and can cause UnicodeFailure exception.

logging.basicConfig(handlers=[logging.FileHandler(settings.LOG_FILE, 'a', 'utf-8')],
                    format=u'%(asctime)s %(levelname)-4s %(message)s',
                    level=logging.INFO,
                    datefmt='%Y-%m-%d %H:%M:%S')


def pytest_addoption(parser):
    """
    Default pytest addoption function to get information from user
    """
    parser.addoption("--env", action="store", default="local")
    parser.addoption("--split_count", action="store", default="1000")
    parser.addoption("--load_balancer", action="store", default="False")
    parser.addoption("--execute_number_of_mins", action="store", default="60")


@fixture(scope="session", autouse=True)
def suite_setup_teardown():
    logging.info("GC: setup commands: remove files in input_files/* directory")
    if os.path.exists("input_files/"):
        shutil.rmtree('input_files/')
        logging.info("GC: setup commands: successfully removed files in input_files/* directory before start "
                     "of new run")
    logging.info("GC: setup commands: no input_files/* directory, so nothing to delete ")
    yield "suite_setup_teardown"
    logging.info("GC: teardown commands: remove intermediate files in directory ==> integration/input/")
    os.chdir(os.getcwd() + "/integration/input/")
    lst_files = glob.glob("*intermediate_org_strings_file*")
    lst_files.sort(key=os.path.getmtime)
    lst_files = [os.getcwd() + "/" + my_file for my_file in lst_files]
    [os.remove(file) for file in lst_files]
    logging.info("GC: teardown commands: removed intermediate files in directory ==> integration/input/")


@fixture(scope="session")
def env(request):
    """
    input for env from user
    """
    return request.config.getoption("--env")


@fixture(scope="session")
def split_count(request):
    return request.config.getoption("--split_count")


@fixture(scope="session")
def load_balancer(request):
    return request.config.getoption("--load_balancer")


@fixture(scope="session")
def execute_number_of_mins(request):
    return request.config.getoption("--execute_number_of_mins")


@fixture(scope='session')
def app_config(env):
    """
    Read config from config.py
    """
    cfg = Config(env)
    return cfg


def load_test_data(path):
    """
    Read details from tests_input_data.json
    """
    with open(path) as data_file:
        data = json.load(data_file)
        return data


@fixture(params=load_test_data(settings.JSON_INPUT_DETAILS))
def input_details_json(request):
    """
    return details from tests_input_data.json
    """
    data = request.param
    return data
