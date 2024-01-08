""" 
Description: 
Author: Xucheng(Timber) Zhang
Date: 2024-01-08
""" 

import os
import logging
import functools
import datetime

from config import CONFIG

@functools.lru_cache()
def create_logger(name=''):
    log_folder = CONFIG["base_dir"] + "/.logs"
    if not os.path.exists(log_folder):
        os.mkdir(log_folder)

    # create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # create formatter
    fmt = '[%(asctime)s %(name)s] (%(filename)s %(lineno)d): %(levelname)s %(message)s'

    # create file handlers
    file_handler = logging.FileHandler(os.path.join(log_folder, f"log_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"), mode='a')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(fmt=fmt, datefmt='%Y-%m-%d %H:%M:%S'))
    logger.addHandler(file_handler)

    return logger


logger = create_logger("logger")

