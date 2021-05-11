"""
Base module holding methods for common operations for all tests related to gc cases.
"""
import logging
import csv
import pandas as pd
from retrying import retry
import requests
import os
import glob
import ntpath


def retry_if_error(exception):
    """
    Return True if we should retry (Currently all exceptions,
    but can be modified here for specific exceptions),
    False otherwise
    """
    return isinstance(exception, Exception)


def load_input_csv_file(key, input_file):
    """
    return input file as a text. Note that input file is a csv.
    Converting csv file to text file for input.
    """
    intermediate_file_csv = f'{input_file[0:-4]}_{key}_intermediate_org_strings_file.csv'
    intermediate_file_txt = f'{input_file[0:-4]}_{key}_intermediate_org_strings_file.txt'
    df = pd.read_csv(input_file, encoding='utf-8')['input']
    df.to_csv(intermediate_file_csv,
              header=False,
              index=False,
              encoding='utf-8')
    with open(intermediate_file_txt, "w", encoding='utf-8') as output_file:
        with open(intermediate_file_csv, "r", encoding='utf-8') as input_file:
            [output_file.write(" ".join(row) + '\n') for row in csv.reader(input_file)]
    return intermediate_file_txt


def load_expected_csv_file(output_file):
    """
    return expected csv files as a list.
    """
    return pd.read_csv(output_file, encoding='utf-8')['output'].values.tolist()


@retry(stop_max_attempt_number=3, wait_fixed=500, retry_on_exception=retry_if_error)
def invoke_url_invocations(url, data, content_type, file_or_input, key):
    response = None
    if file_or_input == "file":
        logging.info(f"API Test {key} Run : Invoking request for {data} with {url}")
        with open(data, 'r', encoding='utf-8') as gc_file:
            response = requests.post(url,
                                     headers={"Content-Type": content_type,
                                              'tracker-id': data,
                                              'log-level': 'DEBUG'},
                                     data=gc_file.read().strip().encode('utf-8'),
                                     timeout=999999)
    elif file_or_input == "input":
        response = requests.post(url,
                                 headers={"Content-Type": content_type},
                                 data=data.encode('utf-8'),
                                 timeout=999999)
    else:
        logging.error(f"API Test {key} Run : File or direct input was not passed while"
                      f" invoking end points.")
    logging.info(f"API Test {key} Run : Invoked request for {data}")
    return [response, data]


@retry(stop_max_attempt_number=3, wait_fixed=500, retry_on_exception=retry_if_error)
def invoke_url_get_method(url, key):
    logging.info(f"API Test {key} Run : Invoking request for {url}")
    response = requests.get(url,
                            headers={"Content-Type": "text/plain"},
                            timeout=999999)
    logging.info(f"API Test {key} Run : Completed invocation of request for {url}")
    return response


def split_file_equal_numbers(filename, number_of_lines, input_directory):
    """
    Code to split the input file in to equal parts.
    :param filename: app_config fixture from conftest.py
    :param number_of_lines: number_of_lines in ech file
    :param input_directory: input_directory
    :return: Boolean Success or Failure
    """
    if not os.path.exists(os.getcwd() + "/input_files/{}/".format(input_directory)):
        os.makedirs(os.getcwd() + "/input_files/{}/".format(input_directory))
    cmd = "split --numeric-suffixes=0 -l {} -a 3 {} {}input_file_".format(number_of_lines, filename,
                                                                          os.getcwd() +
                                                                          "/input_files/{}/".
                                                                          format(input_directory))
    logging.info(f"API split file : "
                 f"Running split command {cmd}")
    cmd_output = os.system(cmd)
    if cmd_output != 0:
        logging.error(f"API split file : "
                      "Running split command failed")
        return False
    logging.info(f"API split file : "
                 "Running split command successfully completed")
    return True


def read_split_files(input_file):
    return_dir_loc = os.getcwd()
    os.chdir(os.getcwd() + "/input_files/" + os.path.splitext(ntpath.basename(input_file))[0] + "/")
    lst_files = glob.glob("input_file*")
    lst_files.sort(key=os.path.getmtime)
    lst_files = [os.getcwd() + "/" + my_file for my_file in lst_files]
    os.chdir(return_dir_loc)
    return lst_files
