#!/usr/bin/env python
import os
from ShipGeoConfig import Config
import logging
import argparse

logging.info("")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def init():
    ap = argparse.ArgumentParser(
        description='test configuration file')
    ap.add_argument('-d', '--debug', action='store_true')
    ap.add_argument('config_file', help='config file to test')
    args = ap.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    assert os.path.exists(args.config_file)
    return args.config_file


def main():
    filename = init()
    config = Config().\
        set_logger(logger).\
        loadpy(filename)
    logger.info(filename)
    print config

if __name__ == '__main__':
    main()
