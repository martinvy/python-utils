# -*- coding: utf-8 -*-

import re
import argparse
import tailhead
import logging
import graypy

amqp_url = 'amqp://guest:guest@localhost/%2F'
amqp_exchange = 'logging.gelf'

regex = re.compile(r"(?P<level>(CRITICAL|ERROR|WARNING|INFO|DEBUG))")


def get_logger(graylog):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    if graylog:
        handler = graypy.GELFRabbitHandler(amqp_url, amqp_exchange)
    else:
        handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)
    return logger


def follow_file(file, logger):
    for line in tailhead.follow_path(file):
        if line:
            extract = re.search(regex, line)
            level = extract.group("level") if extract and extract.groupdict().get("level") else "info"
            getattr(logger, level.lower(), "info")(line)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Log file to follow")
    parser.add_argument("--graylog", action="store_true", help="Log messages to graylog")
    args = parser.parse_args()

    logger = get_logger(args.graylog)
    follow_file(args.file, logger)
