""" This module generates a test database for MongoDB tests. """
import datetime
import yaml

from ...databases.mongodb.models.detector import Detector
from ...databases.mongodb.models.detectorWrapper import DetectorWrapper
from ...databases.mongodb.models.condition import Condition
from mongoengine import connect


# Module metadata
__author__      = "Yitian Kong"
__copyright__   = "TU/e ST2019"
__version__     = "1.0"
__status__      = "Prototype"
__description__ = "Delete test database > Create test database > Insert test data"


# Delete database
def delete_db(connection_dict):
    """
    Delete the database of which name is provided.
    :param connection_dict: Dict containinig all the information to make a connection.
    """
    db_connect = connect(
        db=connection_dict['db_name'],
        username=connection_dict['user'],
        password=connection_dict['password'],
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

# Everytime empty database before filling data
delete_db(connection_dict)

# Create a DB connection
connect(
    db=connection_dict['db_name'],
    username=connection_dict['user'],
    password=connection_dict['password'],
    host=connection_dict['host'],
    port=connection_dict['port']
)

# Create detector detector_id_exist
detector_wrapper = DetectorWrapper(name="detector_id_exist")

detector_id_exist = Detector(name="detector_id_exist")
condition = Condition(name="condition_exist", tag="tag", type="type",
                      collected_at=datetime.datetime(2020, 3, 12, 11, 5, 27),
                      valid_since=datetime.datetime(2020, 3, 12, 11, 5, 27),
                      valid_until=datetime.datetime(2020, 4, 10, 11, 5, 27),
                      values={
                          "name": "name detector",
                          "value": "value detector"
                      })
detector_id_exist.conditions.append(condition)

# Create detector detector_id_exist/sub_detector_id_exist
sub_detector = Detector(name="sub_detector_id_exist")
sub_condition = Condition(name="sub_detector_id_exist", tag="sub_tag", type="sub_type",
                          collected_at=datetime.datetime(2020, 4, 12, 11, 5, 27),
                          valid_since=datetime.datetime(2020, 4, 12, 11, 5, 27),
                          valid_until=datetime.datetime(2020, 5, 12, 11, 5, 27),
                          values={
                              "name": "name sub detector",
                              "value": "value sub detector"
                          })
sub_detector.conditions.append(sub_condition)
detector_id_exist.subdetectors.append(sub_detector)

# Create detector detector_id_exist/sub_detector_id_exist/sub_sub_detector_id_exist
sub_sub_detector = Detector(name="sub_sub_detector_id_exist")
sub_sub_condition = Condition(name="sub_sub_detector_id_exist", tag="sub_sub_tag", type="sub_sub_type",
                              collected_at=datetime.datetime(2020, 5, 12, 11, 5, 27),
                              valid_since=datetime.datetime(2020, 5, 12, 11, 5, 27),
                              valid_until=datetime.datetime(2020, 6, 12, 11, 5, 27),
                              values={
                                  "name": "name sub sub detector",
                                  "value": "value sub sub detector"
                              })
sub_sub_detector.conditions.append(sub_sub_condition)
sub_detector.subdetectors.append(sub_sub_detector)

detector_wrapper.detector = detector_id_exist

detector_wrapper.save()

# Create another detector without condition
detector_wrapper = DetectorWrapper(name="detector_without_condition")

detector_2 = Detector(name="detector_without_condition")

sub_detector_2 = Detector(name="sub_detector_2")

sub_condition_2 = Condition(name="sub_condition_2", tag="sub_2", type="sub_type_2",
                            collected_at=datetime.datetime.now(),
                            valid_since=datetime.datetime.now(),
                            valid_until=datetime.datetime.now())

sub_detector_2.conditions.append(sub_condition_2)
detector_2.subdetectors.append(sub_detector_2)

detector_wrapper.detector = detector_2
detector_wrapper.save()
