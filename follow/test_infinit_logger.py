# -*- coding: utf-8 -*-

import time
import logging
import argparse
from logging.handlers import RotatingFileHandler


def get_logger(rotate):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    if rotate:
        handler = RotatingFileHandler("rot-test.log", maxBytes=rotate, backupCount=3)
    else:
        handler = logging.FileHandler("test.log")
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger


def infinite_logging(logger):
    counter = 0
    print("Starting infinite logging, hit CTRL-C to exit.")
    while True:
        counter += 1
        logger.info("Message number %s" % counter)
        time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rotate", default=None, type=int, help="Rotate log file after specified bytes")
    args = parser.parse_args()
    logger = get_logger(args.rotate)
    infinite_logging(logger)
