"""
Similar to properties file containing details
needed for input, output, success and failure files and others.
"""
from datetime import datetime

# Below file_time is used for all files generated out of tests.
file_time = datetime.utcnow().strftime("GC_%Y_%m_%d_%H_%M_%S_%f")[:-3]

# Logs details, please note that there are 2 log handlers - file and console.
LOG_FILE = "tests_{}.log".format(file_time)

# input JSON file which contains the details needed for tests to run.
JSON_INPUT_DETAILS = "tests_input_data.json"

# Below details are data inputs to sample/example tests.
FAILURE_FILE = "failed_data_example_{}.csv".format(file_time)
SUCCESS_FILE = "success_data_example_{}.csv".format(file_time)
INPUT_FILE = "integration/input/input_25.csv"
EXPECTED_FILE = "integration/expected_output/output_25.csv"
# Below details are data inputs to sample/example tests.
FAILURE_FILE_100k = "failed_data_100k_{}.csv".format(file_time)
SUCCESS_FILE_100k = "success_data_100k_{}.csv".format(file_time)
INPUT_FILE_100k = "integration/input/input_100k.csv"
EXPECTED_FILE_100k = "integration/expected_output/output_100k.csv"
