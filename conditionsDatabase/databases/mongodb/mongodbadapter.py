""" This module implements a MongoDB storage back-end adapter. """
import sys

from json import loads
from datetime import datetime
from mongoengine import *
## As of Python 3.8 we can do more with typing. It is recommended to make
## the adapter class final. Use the following import and provided
## decorator for the class.
#from typing import final

from models.detector import Detector
from models.detectorWrapper import DetectorWrapper
from models.condition import Condition
from ...interface import APIInterface


# Package metadata
__authors__    = ["Nathan DPenha", "Juan van der Heijden",
                  "Vladimir Romashov", "Raha Sadeghi"]
__copyright__  = "TU/e ST2019"
__version__    = "1.0"
__status__     = "Prototype"


#TODO uncomment for python >= 3.8: @final
class MongoToCDBAPIAdapter(APIInterface):
    """
    Adapter class for a MongoDB back-end that implements the CDB interface.
    """
    # Holds the connection handle to the database
    __db_connection = None

    def __init__(self, connection_dict):
        """
        This constructor makes a connection to the MongoDB conditions DB.

        :param connection_dict: The mongoDB configuration for making the connection
                                to the Conditions Database.
        """
        self.__db_connection = self.__get_connection(connection_dict)

    def __get_connection(self, connection_dict):
        """
        Create a connection to a MongoDB server and return the connection handle.
        """
        return connect(
            db=connection_dict['db_name'],
            username=connection_dict['user'],
            password=connection_dict['password'],
            host=connection_dict['host'],
            port=connection_dict['port']
        )

    def __delete_db(self, db_name):
        """
        Delete the specified database.

        :param db_name: The name of the DB that needs to be deleted.
        """
        self.__db_connection.drop_database(db_name)

    def __validate_str(self, input_string):
        """
        This method validates if input_string is of string type.
        If it is not of String type it returns False.

        :param input_string: value that needs to be tested.
        """
        if type(input_string) == str:
            return True
        return False

    def __validate_datetime(self, input_datetime):
        """
        This method validates if input_datetime is of datetime type.
        If it is not of datetime type it returns False.

        :param input_datetime: value that needs to be tested.
        """
        if type(input_datetime) == datetime:
            return True
        return False

    def __validate_path(self, input_path):
        """
        This method validates if input_path is a valid path.
        If it is not of String type it returns False.

        :param input_path: value that needs to be tested.
        """
        if type(input_path) == str:
            return True
        return False

    def __validate_interval_parameters(self, input_date):
        """
        This method validates if input_date is a datetime type or string.
        If yes, it returns True. Otherwise it returns False.

        :param input_date: It could be String or datetime type.
        """
        if type(input_date) == datetime or type(input_date) == str:
            return True
        return False

    def __sanitize_str(self, input_string):
        """
        This method removes spaces at the beginning and at the end of the string and
        returns the String without spaces.

        :param input_string: string that will be sanitized.
        """
        return input_string.strip()

    def __sanitize_path(self, input_path):
        """
        This method removes slashes and spaces at the beginning and
        at the end of the parameter input_path.

        :param input_path: string that will be sanitized.
        """
        input_path = self.__sanitize_str(input_path)
        return input_path.strip('/')

    def __convert_date(self, input_date_string):
        """
        This method converts a date string to a datetime Object.

        :param 	input_date_string: String representing a date
		Accepted String formats: "Year", "Year-Month", "Year-Month-Day", "Year-Month-Day Hours",
		"Year-Month-Day Hours-Minutes", "Year-Month-Day Hours-Minutes-Seconds".
        :throw 	ValueError: If input_date_string is not as specified.
        """
        # Accepted formats for input_date_string
        time_stamp_str_format = ["%Y", "%Y-%m", "%Y-%m-%d", "%Y-%m-%d %H", "%Y-%m-%d %H:%M",
                                 "%Y-%m-%d %H:%M:%S"]
        datetime_value = None

        for time_stamp_format in time_stamp_str_format:
            try:
                datetime_value = datetime.strptime(input_date_string, time_stamp_format)
                break
            except ValueError:
                pass

        if datetime_value is None:
            raise ValueError("Please pass the correct date input. This date string should "
                             "contain only digits/:/ /-. The minimum length could be 4 digits, "
                             "representing the year. ")
        else:
            return datetime_value

    def __split_name(self, detector_id):
        """
        Splits the detector_id string using '/' and returns a list of detector names.
        Otherwise raises an exception if detector_id is not a valid path / id.

        :param detector_id: path to a detector (e.g. detect_name/subdetector_name/...).
        """
        if self.__validate_path(detector_id):
            detector_id = self.__sanitize_path(detector_id)
            return detector_id.split('/')
        else:
            raise TypeError("The provided detector_id needs to be a valid path")

    def __get_wrapper(self, wrapper_id):
        """
        Returns a DetectorWrapper object. Otherwise it raises a
        ValueError exception if the wrapper_id could not be found.

        :param wrapper_id: String specifying the ID for the wrapper to be returned.
        Must be unique. Must not contain a forward slash (i.e. /).
        """
        if not self.__validate_str(wrapper_id):
            raise ValueError("Please pass the correct type of the ID for the new detector. "
                             "It must be unique, and it must not contain a forward slash "
                             "(i.e. /)")

        wrapper_id = self.__sanitize_path(wrapper_id)
        detector_names = self.__split_name(wrapper_id)

        try:
            detector_wrapper = DetectorWrapper.objects().get(name=detector_names[0])
            return detector_wrapper
        except:
            raise ValueError("The detector wrapper ",
                             detector_names[0],
                             " does not exist in the database")

    def __get_subdetector(self, detector, sub_name):
        """
        Returns a subdetector with name sub_name under the specified parent detector.

        :param detector: Detector object.
        :param sub_name: (String) name of the subdetector that should be returned.
        """
        try:
            subdetector = detector.subdetectors.get(name=sub_name)
        except:
            return None

        return subdetector

    def __get_detector(self, detector_wrapper, detector_id):
        """
        Returns a Detector object identified by detector_id.
        It raises ValueError if the detector_id could not be found.

        :param detector_wrapper: DetectorWrapper object that contains a detector tree.
        :param detector_id: (String) The ID (i.e. path) to the detector that
        must be retrieved.
        """
        detector_names = self.__split_name(detector_id)
        detector = detector_wrapper.detector
        path = ""

        for i in range(1, len(detector_names)):
            detector = self.__get_subdetector(detector, detector_names[i])
            path = path + "/" + detector_names[i]

            if detector is None:
                path = self.__sanitize_path(path)
                raise ValueError("The detector " +
                                 path +
                                 " does not exist in the database")

        return detector

    def __add_wrapper(self, name):
        """
        Creates a new DetectorWrapper object and stores it in the DB.
        Returns this new wrapper or None if a detector with that name
        already exists.

        :param name: (String) uniquely identifying the wrapper.
        """
        if not DetectorWrapper.objects(name=name):
            wrapper = DetectorWrapper()
            wrapper.name = name
            wrapper.save()
            return wrapper

    def __remove_wrapper(self, wrapper_id):
        """
        Removes a detector wrapper and its contents from the database.

        :param wrapper_id: (String) identifying the wrapper to remove.
        """
        try:
            wrapper = self.__get_wrapper(wrapper_id)
        except Exception:
            raise ValueError("The detector '",
                             wrapper_id,
                             "' does not exist in the database")
        wrapper.delete()

    # Method signature description can be found in the toplevel interface.py file
    def list_detectors(self, parent_id=None):
        detector_list = []

        if not parent_id:
            detector_wrapper_list = DetectorWrapper.objects.all()

            for wrapper in detector_wrapper_list:
                detector_list.append(str(wrapper.detector.name))

        # This executes when a particular parent_id is provided.
        else:
            if not self.__validate_path(parent_id):
                raise TypeError("Please pass the correct type of input: parent_id, "
                                "parent_id should be of String type")

            try:
                wrapper = self.__get_wrapper(parent_id)
            except Exception:
                raise ValueError("The detector '",
                                 parent_id,
                                 "' does not exist in the database")

            detector = self.__get_detector(wrapper, parent_id)
            path = self.__sanitize_path(parent_id)

            for subdetector in detector.subdetectors:
                detector_list.append(str(path + "/" + subdetector.name))

        return detector_list

    # Method signature description can be found in the toplevel interface.py file
    def get_detector(self, detector_id):
        if detector_id == "":
            raise ValueError("Please specify a valid detector id. A detector id cannot be empty.")

        if not self.__validate_str(detector_id):
            raise TypeError("Please pass the correct type of input: detector_id "
                            "should be String")

        detector_id = self.__sanitize_path(detector_id)
        try:
            detector_wrapper = self.__get_wrapper(detector_id)
        except Exception:
            raise ValueError("The detector '",
                             detector_id,
                             "' does not exist in the database")

        try:
            detector = self.__get_detector(detector_wrapper, detector_id)
        except Exception:
            raise ValueError("The requested detector " + detector_id + " does not exist.")

        # Convert the internal Detector object to a generic Python dict type
        return loads(detector.to_json())

    # Method signature description can be found in the toplevel interface.py file
    def add_detector(self, name, parent_id=None):
        if not self.__validate_str(name):
            raise TypeError("Please pass the correct type of input: name should be String")
        # Detector names cannot be empty string
        if name == "":
            raise ValueError("Please pass the correct value of input: name should not "
                             "be an empty string")
        # If a / is in the name parameter we raise ValueError Exception
        if '/' in name:
            raise ValueError("The name parameter cannot contain a / ")

        # Remove any unwanted symbols from the name
        name = self.__sanitize_str(name)

        # This executes when trying to add a root level detector and wrapper
        if parent_id is None or parent_id is "":
            wrapper = self.__add_wrapper(name)

            if wrapper is not None:
                detector = Detector()
                detector.name = name
                wrapper.detector = detector
                wrapper.save()
            # If the wrapper already exist throw an error
            else:
                raise ValueError("The detector '" + name + "' already exists")

        # If we add a subdetector
        else:
            if not self.__validate_path(parent_id):
                raise TypeError("Please pass the correct type of input: parent_id  "
                                "should be String")

            parent_id = self.__sanitize_path(parent_id)
            detector_names = self.__split_name(parent_id)

            try:
                detector_wrapper = self.__get_wrapper(detector_names[0])
            except Exception:
                raise ValueError("The detector '",
                                 detector_names[0],
                                 "' does not exist in the database")

            try:
                detector = self.__get_detector(detector_wrapper, parent_id)
                added_detector = Detector()
                added_detector.name = name
            except Exception:
                raise ValueError("The detector with id '" + parent_id + "' does not exist")

            try:
                detector.subdetectors.get(name=name)
            except:
                detector.subdetectors.append(added_detector)
                detector_wrapper.save()
                return
            raise ValueError("Detector '" + parent_id + "/" + name + "' already exist")

    # Method signature description can be found in the toplevel interface.py file
    def remove_detector(self, detector_id):
        if not self.__validate_str(detector_id):
            raise TypeError("Please pass the correct type of input: detector_id should be String")

        if detector_id == "":
            raise ValueError("Please provide the correct input for detector_id: detector_id "
                             "cannot be an empty String")

        detector_id = self.__sanitize_path(detector_id)

        try:
            wrapper = self.__get_wrapper(detector_id)
        except Exception:
            raise ValueError("The detector '",
                             detector_id,
                             "' does not exist in the database")

        detector_names = self.__split_name(detector_id)
        # If we want to remove a root detector
        if len(detector_names) < 2:
            try:
                self.__remove_wrapper(detector_names[0])
            except Exception:
                raise ValueError("The detector '",
                                 detector_names[0],
                                 "' does not exist in the database")
            return

        # Otherwise, when we remove a subdetector
        path = ""

        for i in range(0, len(detector_names) - 1):
            path = path + "/" + detector_names[i]

        path = self.__sanitize_path(path)
        detector = self.__get_detector(wrapper, path)
        subdetectors = detector.subdetectors

        # Find the subdetector and remove it from the list
        for i in range(0, len(subdetectors)):
            if subdetectors[i].name == detector_names[-1]:
                detector.subdetectors.pop(i)
                break

        wrapper.save()

    # Method signature description can be found in the toplevel interface.py file
    def add_condition(self, detector_id, name, tag, values, type=None,
                      collected_at=datetime.now(), valid_since=datetime.now(),
                      valid_until=datetime.max):
        if detector_id == "" or name == "" or tag == "" or values == "" or values is None:
            raise TypeError("Please pass the correct parameters: parameters detector_id, name, "
                            "tag, values should not be empty")

        if not (
                self.__validate_path(detector_id)
                and self.__validate_str(tag)
                and self.__validate_str(name)
        ):
            raise TypeError("Please pass the correct type of input: detector_id, "
                            "tag, and name should be String")

        if not (
                (self.__validate_interval_parameters(valid_since) or valid_since is None)
                and (self.__validate_interval_parameters(valid_until) or valid_until is None)
                and (self.__validate_interval_parameters(collected_at) or collected_at is None)
        ):
            raise TypeError(
                "Please pass the correct type of input: valid_since, valid_until and collected_at "
                "should be either String or datetime object")

        if not self.__validate_str(type) and type != None:
            raise TypeError(
                "Please pass the correct type of input: type should be String")

        # Converting all dates given as a String to a datetime object
        if self.__validate_str(valid_until):
            valid_until = self.__convert_date(valid_until)
        elif self.__validate_datetime(valid_until):
            # Strip off the microseconds
            valid_until = valid_until.replace(microsecond=0)
        if self.__validate_str(valid_since):
            valid_since = self.__convert_date(valid_since)
        elif self.__validate_datetime(valid_since):
            # Strip off the microseconds
            valid_since = valid_since.replace(microsecond=0)
        if self.__validate_str(collected_at):
            collected_at = self.__convert_date(collected_at)
        elif self.__validate_datetime(collected_at):
            # Strip off the microseconds
            collected_at = collected_at.replace(microsecond=0)

        if valid_since > valid_until:
            raise ValueError("Incorrect validity interval")

        # Get the detector with the specified detector_id
        try:
            detector_wrapper = self.__get_wrapper(detector_id)
        except Exception:
            raise ValueError("The detector '",
                             detector_id,
                             "' does not exist in the database")

        detector = None
        try:
            detector = self.__get_detector(detector_wrapper, detector_id)
        except Exception:
            raise ValueError("The requested detector '" + detector_id + "' does not exist.")

        # Check if this condition already exists in the database
        condition = self.get_condition_by_name_and_tag(detector_id, name, tag)
        if condition is not None:
            raise ValueError("A condition with the same tag '", tag, "' already exists")

        name = self.__sanitize_str(name)
        tag = self.__sanitize_str(tag)

        # Create a new condition and associate it to the detector
        condition = Condition()
        condition.name = name
        condition.tag = tag
        condition.values = values
        condition.type = type
        condition.collected_at = collected_at
        condition.valid_until = valid_until
        condition.valid_since = valid_since

        detector.conditions.append(condition)
        detector_wrapper.save()

    # Method signature description can be found in the toplevel interface.py file
    def get_conditions(self, detector_id):
        if not self.__validate_str(detector_id):
            raise TypeError(
                "Please pass the correct type of input: detector_id should be String")

        try:
            detector_wrapper = self.__get_wrapper(detector_id)
        except Exception:
            raise ValueError("The detector '",
                             detector_id,
                             "' does not exist in the database")

        detector = None
        try:
            detector = self.__get_detector(detector_wrapper, detector_id)
        except Exception:
            raise ValueError("The requested detector '" + detector_id + "' does not exist.")

        conditions_list = []

        # Iterate over all conditions in the detector and append to conditions_list
        for condition in detector.conditions:
            # Convert the internal Condition object(s) to a generic Python dict type
            conditions_list.append(loads(condition.to_json()))

        if conditions_list:
            return conditions_list
        else:
            return None

    # Method signature description can be found in the toplevel interface.py file
    def get_conditions_by_name(self, detector_id, name):
        # Input validation
        if not self.__validate_str(detector_id):
            raise TypeError("Please pass the correct type of input: "
                            "detector_id should be String")

        if not self.__validate_str(name):
            raise TypeError("Please pass the correct form of input: "
                            "name should be String")

        # Input sanitization
        name = self.__sanitize_str(name)

        # Get the detector of the specified detector_id
        try:
            detector_wrapper = self.__get_wrapper(detector_id)
        except Exception:
            raise ValueError("The detector '",
                             detector_id,
                             "' does not exist in the database")

        detector = None
        try:
            detector = self.__get_detector(detector_wrapper, detector_id)
        except Exception:
            raise ValueError("The requested detector '" + detector_id + "' does not exist.")

        # Query the condition where the 'name' equals the specified name
        conditions = detector.conditions.filter(name=name)
        if not conditions:
            return None

        # Convert the internal Condition object(s) to a generic Python dict type
        condition_dicts = []
        for condition in conditions:
            condition_dicts.append(loads(condition.to_json()))

        return condition_dicts

    # Method signature description can be found in the toplevel interface.py file
    def get_conditions_by_tag(self, detector_id, tag):
        # Input validation
        if not self.__validate_str(detector_id):
            raise TypeError("Please pass the correct type of input: "
                            "detector_id should be String")

        if not self.__validate_str(tag):
            raise TypeError("Please pass the correct format of input: "
                            "tag should be String")

        # Input sanitization
        tag = self.__sanitize_str(tag)

        # Get the detector of the specified detector_id
        try:
            detector_wrapper = self.__get_wrapper(detector_id)
        except Exception:
            raise ValueError("The detector '",
                             detector_id,
                             "' does not exist in the database")

        detector = None
        try:
            detector = self.__get_detector(detector_wrapper, detector_id)
        except Exception:
            raise ValueError("The requested detector '" + detector_id + "' does not exist.")

        # Query the condition where the 'tag' equals the specified tag
        conditions = detector.conditions.filter(tag=tag)
        if not conditions:
            return None

        # Convert the internal Condition object(s) to a generic Python dict type
        condition_dicts = []
        for condition in conditions:
            condition_dicts.append(loads(condition.to_json()))

        return condition_dicts

    # Method signature description can be found in the toplevel interface.py file
    def get_conditions_by_name_and_validity(self, detector_id, name, start_date, end_date=None):
        # Input validation
        if not self.__validate_str(detector_id):
            raise TypeError("Please pass the correct type of input: "
                            "detector_id should be String")

        if not (self.__validate_str(name) and
                self.__validate_interval_parameters(start_date) and
                (self.__validate_interval_parameters(end_date) or end_date is None)):
            raise TypeError("Please pass the valid input type: name should be String, "
                            "dates could be either datetime or String type.")

        # Input sanitization
        name = self.__sanitize_str(name)

        # Converting all dates given as a String to a datetime object
        if self.__validate_str(start_date):
            start_date = self.__convert_date(start_date)
        elif self.__validate_datetime(start_date):
            start_date = start_date.replace(microsecond=0)  # Strip off the microseconds
        if self.__validate_str(end_date):
            end_date = self.__convert_date(end_date)
        elif self.__validate_datetime(end_date):
            end_date = end_date.replace(microsecond=0)  # Strip off the microseconds

        # Check for a valid interval
        if end_date is not None and start_date is not None:
            if start_date > end_date:
                raise ValueError("Invalid validity interval")

        # Get the detector of the specified detector_id
        try:
            detector_wrapper = self.__get_wrapper(detector_id)
        except Exception:
            raise ValueError("The detector '",
                             detector_id,
                             "' does not exist in the database")

        detector = None
        try:
            detector = self.__get_detector(detector_wrapper, detector_id)
        except Exception:
            raise ValueError("The requested detector '" + detector_id + "' does not exist.")

        # Query the condition where the 'name' equals the specified name
        conditions = detector.conditions.filter(name=name)

        # Loop over all conditions and check whether they are valid within the specified range
        result_list = []
        for condition in conditions:
            # Check if start_date is within the condition validation range
            if condition.valid_since <= start_date <= condition.valid_until:
                # Check if end_date is set
                if end_date is not None:
                    # If end_date is specified it should also be within the condition
                    # validation range
                    if condition.valid_since <= end_date <= condition.valid_until:
                        result_list.append(condition)
                else:
                    result_list.append(condition)

        if not result_list:
            return None

        # Convert the internal Condition object(s) to a generic Python dict type
        condition_dicts = []
        for condition in result_list:
            condition_dicts.append(loads(condition.to_json()))

        return condition_dicts

    # Method signature description can be found in the toplevel interface.py file
    def get_condition_by_name_and_tag(self, detector_id, name, tag):
        # Input validation
        if not self.__validate_str(detector_id):
            raise TypeError("Please pass the correct type of input: "
                            "detector_id should be String")

        if not (self.__validate_str(name) and self.__validate_str(tag)):
            raise TypeError("Please pass the correct form of input: "
                            "name and tag should be String")

        # Input sanitization
        name = self.__sanitize_str(name)
        tag = self.__sanitize_str(tag)

        # Get the detector of the specified detector_id
        try:
            detector_wrapper = self.__get_wrapper(detector_id)
        except Exception:
            raise ValueError("The detector '",
                             detector_id,
                             "' does not exist in the database")

        try:
            detector = self.__get_detector(detector_wrapper, detector_id)
        except Exception:
            raise ValueError("The requested detector '" + detector_id + "' does not exist.")

        # Query the condition where the 'name' and 'tag' equal the specified name and tag
        try:
            condition = detector.conditions.get(name=name, tag=tag)
        except DoesNotExist:
            return None

        # Convert the internal Condition object to a generic Python dict type
        return loads(condition.to_json())

    # Method signature description can be found in the toplevel interface.py file
    def get_condition_by_name_and_collection_date(self, detector_id, name, collected_at):
        # Input validation
        if not self.__validate_str(detector_id):
            raise TypeError("Please pass the correct type of input: "
                            "detector_id should be String")

        if not (self.__validate_str(name) and self.__validate_interval_parameters(collected_at)):
            raise TypeError(
                "Please pass the valid input type: name should be String, collected_at could be "
                "either datetime or String type.")

        # Input sanitization
        name = self.__sanitize_str(name)

        # Converting all dates given as a String to a datetime object
        if self.__validate_str(collected_at):
            collected_at = self.__convert_date(collected_at)
        elif self.__validate_datetime(collected_at):
            # Strip off the microseconds
            collected_at = collected_at.replace(microsecond=0)

        # Get the detector of the specified detector_id
        try:
            detector_wrapper = self.__get_wrapper(detector_id)
        except Exception:
            raise ValueError("The detector '",
                             detector_id,
                             "' does not exist in the database")

        detector = None
        try:
            detector = self.__get_detector(detector_wrapper, detector_id)
        except Exception:
            raise ValueError("The requested detector '" + detector_id + "' does not exist.")

        # Query the condition where the 'name' and 'collected_at' equal the specified name and
        # collection_date
        try:
            condition = detector.conditions.get(name=name, collected_at=collected_at)
            # Convert the internal Condition object to a generic Python dict type
            return loads(condition.to_json())
        except DoesNotExist:
            return None

    # Method signature description can be found in the toplevel interface.py file
    def update_condition_by_name_and_tag(self, detector_id, name, tag,
                                         type=None, valid_since=None, valid_until=None):
        # Input validation
        if not self.__validate_str(detector_id):
            raise TypeError("Please pass the correct type of input: "
                            "detector_id should be String")

        if not ((self.__validate_interval_parameters(valid_since) or valid_since is None) and
                (self.__validate_interval_parameters(valid_until) or valid_until is None) and
                (self.__validate_str(type) or type is None) and
                 self.__validate_str(name) and
                 self.__validate_str(tag)):
            raise TypeError(
                "Please pass correct form of input: for valid_since and/or valid_until, "
                "they could be String, datetime or None. Only String is accepted for name, "
                "tag and type.")

        # Converting all dates given as a String to a datetime object
        if self.__validate_str(valid_until):
            valid_until = self.__convert_date(valid_until)
        elif self.__validate_datetime(valid_until):
            # Strip off the microseconds
            valid_until = valid_until.replace(microsecond=0)
        if self.__validate_str(valid_since):
            valid_since = self.__convert_date(valid_since)
        elif self.__validate_datetime(valid_since):
            # Strip off the microseconds
            valid_since = valid_since.replace(microsecond=0)

        if valid_until is not None and valid_since is not None:
            if valid_since > valid_until:
                raise ValueError("Invalid validity interval")

        # Input sanitization
        name = self.__sanitize_str(name)
        tag = self.__sanitize_str(tag)

        if self.__validate_str(type):
            type = self.__sanitize_str(type)

        # Get the detector of the specified detector_id
        try:
            detector_wrapper = self.__get_wrapper(detector_id)
        except Exception:
            raise ValueError("The detector '",
                             detector_id,
                             "' does not exist in the database")

        detector = None
        try:
            detector = self.__get_detector(detector_wrapper, detector_id)
        except Exception:
            raise ValueError("The requested detector '" + detector_id + "' does not exist.")

        condition = None
        try:
            condition = detector.conditions.get(name=name, tag=tag)
        except DoesNotExist:
            raise ValueError("No condition with this name and tag can be found")

        # Only update fields that are not None
        if type is not None:
            condition.type = type
        if valid_since is not None:
            condition.valid_since = valid_since
        if valid_until is not None:
            condition.valid_until = valid_until

        detector_wrapper.save()
