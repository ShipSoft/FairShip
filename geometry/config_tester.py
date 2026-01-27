#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import os
import json
import importlib.util
import logging
import argparse

logging.info("")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def parse_arguments():
    ap = argparse.ArgumentParser(description="test configuration file")
    ap.add_argument("-d", "--debug", action="store_true")
    ap.add_argument(
        "-p", "--params", type=json.loads, help="""config parameters in json form '{"a": 1, "b": 2}' """, default={}
    )

    ap.add_argument("config_file", help="config file to test")
    args = ap.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    assert os.path.exists(args.config_file)
    return args


def main(arguments):
    logger.info("file: %s" % arguments.config_file)
    if arguments.params:
        logger.info("parameters: %s" % arguments.params)

    # Load the geometry config module
    spec = importlib.util.spec_from_file_location("geometry_config", arguments.config_file)
    geometry_config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(geometry_config)

    # Create config with parameters
    config = geometry_config.create_config(**arguments.params)

    # Print configuration
    for k, v in config.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main(parse_arguments())
