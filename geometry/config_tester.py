#!/usr/bin/env python
import os
from ShipGeoConfig import ConfigRegistry
import logging
import argparse

logging.info("")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def parse_arguments():
    ap = argparse.ArgumentParser(
        description='test configuration file')
    ap.add_argument('-d', '--debug', action='store_true')
    ap.add_argument('config_file', help='config file to test')
    args = ap.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    assert os.path.exists(args.config_file)
    return args


def main(arguments):
    logger.info(arguments.config_file)
    ConfigRegistry.loadpy(arguments.config_file, muShieldDesign=2, targetOpt=5)
    for k, v in ConfigRegistry().iteritems():
        print "%s: %s" % (k, v)

if __name__ == '__main__':
    main(parse_arguments())
