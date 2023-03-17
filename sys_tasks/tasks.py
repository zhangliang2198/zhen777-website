import datetime

from logger import logger


async def sys_print_task():
    print("sys_print_task 执行 在:" + str(datetime.datetime.now()))
    logger.info("sys_print_task 执行 在:" + str(datetime.datetime.now()))


async def init_data_task():
    logger.info("init_data_task 执行 在:" + str(datetime.datetime.now()))
