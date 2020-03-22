############################################################################
# This file is used to generate test database and fill initial data in.
############################################################################

import datetime
import yaml

from ...databases.mongodb.models.detector import Detector
from ...databases.mongodb.models.detectorWrapper import DetectorWrapper
from ...databases.mongodb.models.condition import Condition
from mongoengine import connect

# Package metadata
__author__ = "Yitian Kong"
__copyright__ = "TU/e ST2019"
__version__ = "0.2"
__status__ = "Prototype"
__description__ = "Delete test database > Create test database > Insert test data"


# delete database
def delete_db(connection_dict):
    """
    Delete the database of which name is provided.
    :param connection_dict: Dict containinig all the information to make a connection.
    """
    db_connect = connect(
        db=connection_dict['db_name'],
        #             user=user,
        #             password=password,
        host=connection_dict['host'],
        port=connection_dict['port']
    )

    db_connect.drop_database(connection_dict['db_name'])


# Fetch database details from config file
# with open(r'test_mongodb_config.yml') as file:  # local path
with open(r'conditionsDatabase/tests/test_mongodb/test_mongodb_config.yml') as file:  # CI path
    # The FullLoader parameter handles the conversion from YAML
    # scalar values to Python the dictionary format
    con_dic = yaml.load(file, Loader=yaml.FullLoader)

connection_dict = con_dic['mongo']

# DbConnect.delete_db(connection_dict)
connect(
    db=connection_dict['db_name'],
    #             user=user,
    #             password=password,
    host=connection_dict['host'],
    port=connection_dict['port']
)

# Everytime empty database before filling data
delete_db(connection_dict)

# define detector_id_exist
dw = DetectorWrapper(name="detector_id_exist")

detector_id_exist = Detector(name="detector_id_exist")
condition = Condition(name="condition_exist", tag="1", type="type1",
                      collected_at=datetime.datetime(2020, 3, 12, 11, 5, 27, 767563),
                      valid_since=datetime.datetime(2020, 3, 12, 11, 5, 27, 767563),
                      valid_until=datetime.datetime(2020, 4, 10, 11, 5, 27, 767563),
                      values={
                          "name": "name detector",
                          "value": "value detector"
                      })
detector_id_exist.conditions.append(condition)

# define detector_id_exist/sub_detector_id_exist
subdetector1 = Detector(name="sub_detector_id_exist")
subCondition1 = Condition(name="sub_detector_id_exist", tag="sub1", type="subtype1",
                          collected_at=datetime.datetime(2020, 4, 12, 11, 5, 27, 767563),
                          valid_since=datetime.datetime(2020, 4, 12, 11, 5, 27, 767563),
                          valid_until=datetime.datetime(2020, 5, 12, 11, 5, 27, 767563),
                          values={
                              "name": "name sub detector",
                              "value": "value sub detector"
                          })
subdetector1.conditions.append(subCondition1)
detector_id_exist.subdetectors.append(subdetector1)

# define detector_id_exist/sub_detector_id_exist/sub_sub_detector_id_exist
subsubdetector1 = Detector(name="sub_sub_detector_id_exist")
subsubCondition1 = Condition(name="sub_sub_detector_id_exist", tag="subsub1", type="subsubtype1",
                             collected_at=datetime.datetime(2020, 5, 12, 11, 5, 27, 767563),
                             valid_since=datetime.datetime(2020, 5, 12, 11, 5, 27, 767563),
                             valid_until=datetime.datetime(2020, 6, 12, 11, 5, 27, 767563),
                             values={
                                 "name": "name sub sub detector",
                                 "value": "value sub sub detector"
                             })
subsubdetector1.conditions.append(subsubCondition1)
subdetector1.subdetectors.append(subsubdetector1)

dw.detector = detector_id_exist

dw.save()

# another detector without condition
dw2 = DetectorWrapper(name="detector_without_condition")

detector2 = Detector(name="detector_without_condition")

subdetector2 = Detector(name="subdetector2")

subCondition2 = Condition(name="subcondition2", tag="sub2", type="subtype2",
                          collected_at=datetime.datetime.now(), valid_since=datetime.datetime.now(),
                          valid_until=datetime.datetime.now())

subdetector2.conditions.append(subCondition2)
detector2.subdetectors.append(subdetector2)

dw2.detector = detector2
dw2.save()
