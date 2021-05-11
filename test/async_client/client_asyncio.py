import time
import logging
import json
import asyncio
import aiohttp
import settings

logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%d-%m-%Y:%H:%M:%S',
                    level=logging.INFO)
logging.Formatter.converter = time.gmtime
logger = logging.getLogger(__name__)


async def _worker(name, session, data):
    logger.info(f"Invoking worker-{name} with file - {data}.")
    with open(data, 'r', encoding='utf-8') as gc_file:
        response = await session.post(headers={"Content-Type": "text/plain",
                                               "Connection": "close"},
                                      data=gc_file.read().strip().encode('utf-8'),
                                      url=settings.TLS + "://" + settings.HOST + "/" + settings.API)
        value = await response.text()
        value = json.loads(value)
    logger.info(f"Completed processing of worker-{name} with file - {data}.")
    return value.get('generic_classifier')


async def main(directory, no_of_files):
    """
    Main async function.
    :param directory: input directory from where input files are read.
    :param no_of_files: number of files to be processed in that directory.
    :return:
    """
    async with aiohttp.ClientSession() as session:
        values = await asyncio.gather(*(_worker(f'{n}', session, directory + f"/input_file_{n}")
                                        for n in range(1, int(no_of_files)+1)))
        logger.info(values)
        logger.info("")


if __name__ == "__main__":
    num_of_files_dir = input("Enter files directory to be processed : ")
    num_of_files = input("Enter number of files to execute "
                         "in that directory : ")
    logger.info(f"Start processing files.")
    start = time.perf_counter()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(num_of_files_dir, num_of_files))
    loop.close()
    elapsed = time.perf_counter() - start
    logger.info(f"Executed in {elapsed:0.4f} seconds.")
