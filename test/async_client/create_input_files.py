import random
import logging
import time
import os
import settings

logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%d-%m-%Y:%H:%M:%S',
                    level=logging.INFO)
logging.Formatter.converter = time.gmtime
logger = logging.getLogger(__name__)


def _rand(start_value, end_value, total_len):
    res = []
    for j in range(total_len):
        res.append(random.randint(start_value, end_value - 1))
    return res


def create_files(input_file, count, num_files, file_name):
    """
    This function will create input files to be sent as input to running instance of gc.
    :param input_file: input_file from where org strings are read.
    :param count: count of org strings in each file.
    :param num_files: number of files to be created.
    :param file_name: prefix of file name.
    :return:
    """
    with open(input_file, encoding='utf-8') as input_file:
        input_list = input_file.readlines()
        input_list = [org.strip() for org in input_list]

    logging.info("Count of org strings in each file : {}".format(count))
    for ind in range(1, int(num_files)+1):
        start = 0
        end = len(input_list)
        random_list = _rand(start, end, int(count))
        output_list = [input_list[ref_index] for ref_index in random_list]
        if not os.path.exists(os.getcwd() + f"/input_files/{num_files}"):
            os.makedirs(os.getcwd() + f"/input_files/{num_files}")
        output_file = f"{file_name}_{ind}"
        with open(os.getcwd() + f"/input_files/{num_files}/" + output_file, 'w', encoding='utf-8') as output_file:
            for item in output_list:
                output_file.write("%s\n" % item)


if __name__ == "__main__":
    file = settings.INPUT_FILE
    count_org = input("Enter number of org strings in file: ")
    num_of_files = input("Enter number of files to be created : ")
    create_files(file, count_org, num_of_files, 'input_file')
