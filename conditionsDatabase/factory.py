""" This module implements the factory pattern for getting a database API instance """

import os
import sys
import yaml
from databases.mongodb.mongodb import MongoToCDBAPIAdapter

class APIFactory:
    """
    This class creates an instance of the specified database API.
    """

    def __init__(self):
        # supported_db_types is the list of different databases which are supported
        self.__supported_db_types = ["mongo", "oracle"]
        pass

    def construct_DB_API(self, path):
        """
        Returns an instance of the specified database API based on a configuration file
        or raise an exception
        :param path the path to the configuration file. It could be "", then the default path will be considered.

        Default path is $FAIRHOME/conditionsDatabase/config.yml.
        """
        
        supported_db_names = ["mongo", "mysql"]
        config = self.__read_config_file(path)

        if config is None or len(config) <= 0:
            raise ValueError("Error in reading or accessing the configuration file")

        db_type = config.keys()[0]
        connection_dict = config[db_type]
        if db_type not in self.__supported_db_types:
            raise NotImplementedError(db_type + " database is not supported")

        if db_type == "mongo":
            return MongoToCDBAPIAdapter(connection_dict)
        # elif db_type == supported_db_names[1]: #oracle
        #     return OracleTOCDBAPIAdapter(connection_dict)
        else:
            raise NotImplementedError(db_type + " database is not supported")


    def __read_config_file(self, path):
        """
        Loads the configuration from the config file,
        including the database type and also the connection information
        :param path the path to the configuration file. It could be "", then the default path will be considered.
        """

        ret = {}
        if len(path) == 0:
            home_dir = str(os.getenv('FAIRHOME'))
            path = home_dir + "/conditionsDatabase/config.yml"
        else:
            path_details = path.split(".")
            file_extention = path_details[len(path_details) - 1]
            if not(file_extention == "yml" or file_extention == "yaml"):
                print("The file extension is incorrect. A YAML file is required.")
                return None

        try:
            with open(path, 'r') as ymlfile:
                cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
        except IOError:
            print("The configuration file does not exit or Invalid path to the file:", str(sys.exc_info()[0]))
            return None

        connection_dict = {'db_name': '', 'user': None, 'password': None, 'host': "", 'port': 0}
        db_type = None

        try:
            db_type = cfg["db_type"]
            if db_type is None:
                print("db type should be defined")
                return None

            if db_type not in cfg.keys():
                print("db config is not defined")
                return None

            connection_dict["host"] = cfg[db_type]["host"]
            connection_dict["db_name"] = cfg[db_type]["db_name"]
            connection_dict["user"] = cfg[db_type]["user"]
            connection_dict["password"] = cfg[db_type]["password"]
            connection_dict["port"] = cfg[db_type]["port"]
            ret[db_type.lower()] = connection_dict
            return ret
        except KeyError:
            print("Incorrect configuration file, missing some parameters. it should contain: db_type, db_name, user, password, host, and port.")
            return None
