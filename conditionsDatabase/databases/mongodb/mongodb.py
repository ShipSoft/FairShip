""" This module implements a MongoDB adapter """
import sys
from ...interface import APIInterface

from json import loads
from datetime import datetime, date
from mongoengine import *

from models.detector import Detector
from models.detectorWrapper import DetectorWrapper
from models.condition import Condition

# Package metadata
__author__ = "Nathan DPenha, Juan van der Heijden, " \
             "Vladimir Romashov, Raha Sadeghi"
__copyright__ = "TU/e ST2019"
__version__ = "0.1"
__status__ = "Prototype"


class MongoToCDBAPIAdapter(APIInterface):
    """
    Class that implements the conditions db interface
    """
    __db_connection = None

    def __init__(self, connection_dict):
        """
        This constructor makes a connection to the MongoDB conditionsDB

        :param connection_dict the mongoDB configuration for making the connection
        to the Conditions Database
        connection handle to the database is stored in the private class vaiable __db_connect
        """
        self.__db_connection = self.__get_connection(connection_dict)

    def __validate_str(self, input_string):
        """
        This method validates if input_string is of string type.
        If it is not of String type it returns False

        :param input_string string type
        """
        if type(input_string) == str:
            return True
        return False

    def __validate_datetime(self, input_datetime):
        """
        This method validates if input_string is of string type.
        If it is not of String type it returns False

        :param input_string string type
        """
        if type(input_datetime) == datetime:
            return True
        return False

    def __validate_path(self, input_path):
        """
        This method validates if input_path is of string type.
        If it is not of String type it returns False

        :param input_string string type
        """
        if type(input_path) == str:
            return True
        return False

    def __sanitize_str(self, input_string):
        """
        This method removes spaces at the beginning and at the end of the string and
        returns the String without spaces.

        :param input_string string type
         """
        return input_string.strip()

    def __convert_date(self, input_date_string):
        """
        This method converts a date string to a datetime Object.

        :param 	input_date_string String representing a date
		Accepted String formats: "Year", "Year-Month", "Year-Month-Day", "Year-Month-Day Hours", 
		"Year-Month-Day Hours-Minutes", "Year-Month-Day Hours-Minutes-Seconds"
	:throw 	TypeError: If input type is not as specified

         """
        # Accepted formats for time_stamp
        time_stamp_str_format = ["%Y", "%Y-%m", "%Y-%m-%d", "%Y-%m-%d %H", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"]
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

    def __sanitize_path(self, input_path):
        """
        This method removes slashes and spaces symbols at the beginning and
        at the end of the parameter input_path

        :param input_string string type
         """
        input_path = self.__sanitize_str(input_path)
        return input_path.strip('/')

    def __validate_interval_parameters(self, input_date):
        """
        This method validates if input_date is a date type, string or None.
        If yes, it returns True. Otherwise it returns False

        :param input_date date type: It could be String, date type or None.
        """
        if type(input_date) == datetime or type(input_date) == str:
            return True
        return False

    def __validate_dict(self, input_dict):
        """
        This method validates if input_dict is of dictionary type.
        If yes, it returns True. Otherwise it returns False

        :param input_dict dict type
        """
        if type(input_dict) == dict:
            return True
        return False

    def __get_wrapper(self, wrapper_id):
        """
        This getter provides a DetectorWrapper object. Otherwise it raises
        ValueError exception if the parameter in the  wrapper_id could not be found

        :param wrapper_id: String specifying the ID for the wrapper to be returned.
        Must be unique. Must not contain a forward slash (i.e. /)
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
        This method provides a subdetector of the specified detector.

        :param detector: Detector object
        :param sub_name: specific subdetector name whose object should be returned
        """
        try:
            subdetector = detector.subdetectors.get(name=sub_name)
        except:
            return None
        return subdetector

    def __get_detector(self, detector_wrapper, detector_id):
        """
        Returns a detector object that contains all the data i.e. name, conditions,
        etc related to the subdetector name, which User has requested for
        It raises ValueError if the detector_id could not be found

        :param detector_wrapper: Detector wrapper object for which we will get specific
        subdetector.
        :param detector_id: String specifying the ID for the detector. Must be unique.
        Must not contain a forward slash (i.e. /)
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

    def __split_name(self, detector_id):
        """
        Splits the string using '/' and returns a list of detector names.
        Otherwise raises an exception if detector_id is not of dictionary type.

        :param: detector names (e.g. detect_name/subdetector_name/sub-subdetector_name/...)
        """
        if self.__validate_path(detector_id):
            detector_id = self.__sanitize_path(detector_id)
            return detector_id.split('/')
        else:
            raise TypeError("The provided detector_id needs to be a valid path")

    def __add_wrapper(self, name):
        """
        Adds a detector wrapper with specific name. It returns None if a detector
        with that name already exists

        :param: name - must be of type string
        """
        if not DetectorWrapper.objects(name=name):
            wrapper = DetectorWrapper()
            wrapper.name = name
            wrapper.save()
            return wrapper

    def add_detector(self, name, parent_id=None):
        # if we add detector
        if '/' in name:  # if a / is in the name parameter we raise ValueError Exception
            raise ValueError("The name parameter cannot contain a / ")

        if not parent_id:  # This executes when trying to add a root level detector and wrapper
            if not self.__validate_str(name):
                raise TypeError("Please pass the correct type of input: name should be String")

            wrapper = self.__add_wrapper(name)
            if wrapper is not None:
                detector = Detector()
                detector.name = name
                wrapper.detector = detector
                wrapper.save()
            else:  # if the wrapper does not exist we execute else
                raise ValueError("The wrapper/detector " + name + " already exists")

        # if we add subdetector
        else:
            if not (self.__validate_str(name) and self.__validate_path(parent_id)):
                raise TypeError("Please pass the correct type of input: parent_id and "
                                "name should be String")
            parent_id = self.__sanitize_path(parent_id)
            name = self.__sanitize_str(name)
            detector_names = self.__split_name(parent_id)
            try:
                detector_wrapper = self.__get_wrapper(detector_names[0])
            except Exception:
                raise ValueError("The detector wrapper ",
                                 detector_names[0],
                                 " does not exist in the database")

            try:
                detector = self.__get_detector(detector_wrapper, parent_id)
                added_detector = Detector()
                added_detector.name = name
            except Exception:
                raise ValueError("The path with parent_id " + parent_id + " does not exist")

            try:
                detector.subdetectors.get(name=name)
            except:
                detector.subdetectors.append(added_detector)
                detector_wrapper.save()
                return
            raise ValueError("Detector " + name + " already exist")

    def list_detectors(self, parent_id=None):
        detector_list = []
        if not parent_id:
            detector_wrapper_list = DetectorWrapper.objects.all()
            for wrapper in detector_wrapper_list:
                detector_list.append(str(wrapper.detector.name))
        else:  # this executes when a particular parent_id is provided.
            if not self.__validate_path(parent_id):
                raise TypeError("Please pass the correct type of input: parent_id, "
                                "parent_id should be of String type")

            try:
                wrapper = self.__get_wrapper(parent_id)
            except Exception:
                raise ValueError("The detector wrapper ",
                                 parent_id,
                                 " does not exist in the database")

            detector = self.__get_detector(wrapper, parent_id)
            path = self.__sanitize_path(parent_id)
            for subdetector in detector.subdetectors:
                detector_list.append(str(path + "/" + subdetector.name))
        return detector_list

    def get_detector(self, detector_id):
        if detector_id == "":
            return None

        if not self.__validate_str(detector_id):
            raise TypeError(
                "Please pass the correct type of input: detector_id")

        if not self.__validate_path(detector_id):
            raise ValueError("Please pass the correct type of input: detector_id, "
                             "tag and name should be String")

        detector_id = self.__sanitize_path(detector_id)
        try:
            detector_wrapper = self.__get_wrapper(detector_id)
        except Exception:
            raise ValueError("The detector wrapper ",
                             detector_id,
                             " does not exist in the database")

        try:
            detector = self.__get_detector(detector_wrapper, detector_id)
        except Exception:
            raise ValueError("The requested detector " + detector_id + " does not exist.")
        # Convert the internal Detector object to a generic Python dict type
        return loads(detector.to_json())

    def add_condition(self,
                      detector_id,
                      name,
                      tag,
                      collected_at,
                      values,
                      type=None,
                      valid_since=datetime.now(),
                      valid_until=datetime.max):

        if not (
                self.__validate_path(detector_id)
                and self.__validate_str(tag)
                and self.__validate_str(name)
        ):
            raise TypeError("Please pass the correct type of input: detector_id, "
                            "tag, and name should be String")

        if not (
                (self.__validate_interval_parameters(valid_since) or valid_until is None)
                and (self.__validate_interval_parameters(valid_until) or valid_until is None)
                and self.__validate_interval_parameters(collected_at)
        ):
            raise TypeError(
                "Please pass the correct type of input: valid_since, valid_until and collected_at "
                "should be either String or date")

        if not (self.__validate_dict(values)):
            raise TypeError("values type should be dictionary")

        if not self.__validate_str(type) and type != None:
            raise TypeError(
                "Please pass the correct type of input: type")

        # Converting all dates given as a String to a datetime Object
        if self.__validate_str(valid_until):
            valid_until = self.__convert_date(valid_until)
        elif self.__validate_datetime(valid_until):
            valid_until = valid_until.replace(microsecond=0)  # Strip off the microseconds
        if self.__validate_str(valid_since):
            valid_since = self.__convert_date(valid_since)
        elif self.__validate_datetime(valid_since):
            valid_since = valid_since.replace(microsecond=0)  # Strip off the microseconds
        if self.__validate_str(collected_at):
            collected_at = self.__convert_date(collected_at)
        elif self.__validate_datetime(collected_at):
            collected_at = collected_at.replace(microsecond=0)  # Strip off the microseconds

        if valid_since > valid_until:
            raise ValueError("Incorrect validity interval")

        # Check if this condition has already existed in the database
        condition = self.get_condition_by_name_and_tag(detector_id, name, tag)
        if condition is not None:
            raise ValueError("A condition with the same tag ", tag, " already exists")

        # Get the detector of the specified detector_id
        try:
            detector_wrapper = self.__get_wrapper(detector_id)
        except Exception:
            raise ValueError("The detector wrapper ",
                             detector_id,
                             " does not exist in the database")

        detector = None
        try:
            detector = self.__get_detector(detector_wrapper, detector_id)
        except Exception:
            raise ValueError("The requested detector: " + detector_id + " does not exist.")
        if detector is None:
            raise ValueError("The requested detector " + detector_id + "does not exist")

        name = self.__sanitize_str(name)
        tag = self.__sanitize_str(tag)

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

    def get_conditions(self, detector_id):
        # Get the detector of the specified detector_id
        if not self.__validate_str(detector_id):
            raise TypeError(
                "Please pass the correct type of input: detector_id")

        try:
            detector_wrapper = self.__get_wrapper(detector_id)
        except Exception:
            raise ValueError("The detector wrapper ",
                             detector_id,
                             " does not exist in the database")
        detector = None
        try:
            detector = self.__get_detector(detector_wrapper, detector_id)
        except Exception:
            raise ValueError("The requested detector " + detector_id + " does not exist.")
        if detector is None:
            raise ValueError("The requested detector " + detector_id + "does not exist")

        conditions_list = []

        # Iterate over all conditions in the detector and append to conditions_list
        for condition in detector.conditions:
            # Convert the internal Condition object(s) to a generic Python dict type
            conditions_list.append(loads(condition.to_json()))

        if conditions_list:
            return conditions_list
        else:
            return None

    def __remove_wrapper(self, wrapper_id):
        """
        Removes a detector wrapper from the database.

        :param detector_id: String identifying the detector to remove
        """
        try:
            wrapper = self.__get_wrapper(wrapper_id)
        except Exception:
            raise ValueError("The detector wrapper ",
                             wrapper_id,
                             " does not exist in the database")
        wrapper.delete()

    def remove_detector(self, detector_id):
        if not self.__validate_str(detector_id):
            raise TypeError(
                "Please pass the correct type of input: detector_id")
        detector_id = self.__sanitize_path(detector_id)
        try:
            wrapper = self.__get_wrapper(detector_id)
        except Exception:
            raise ValueError("The detector wrapper ",
                             detector_id,
                             " does not exist in the database")
        detector_names = self.__split_name(detector_id)
        if len(detector_names) < 2:
            try:
                self.__remove_wrapper(detector_names[0])
            except Exception:
                raise ValueError("The detector wrapper ",
                                 detector_names[0],
                                 " does not exist in the database")
            return
        path = ""
        for i in range(0, len(detector_names) - 1):
            path = path + "/" + detector_names[i]
        path = self.__sanitize_path(path)
        detector = self.__get_detector(wrapper, path)
        subdetectors = detector.subdetectors

        for i in range(0, len(subdetectors)):
            if subdetectors[i].name == detector_names[-1]:
                detector.subdetectors.pop(i)
                break

        wrapper.save()

    def get_conditions_by_tag(self, detector_id, tag):
        # Input validation
        if not self.__validate_str(tag):
            raise TypeError("Please pass the correct format of input: "
                            "tag should be String")

        if not self.__validate_str(detector_id):
            raise TypeError(
                "Please pass the correct type of input: detector_id")

        # Input sanitization
        tag = self.__sanitize_str(tag)

        # Get the detector of the specified detector_id
        try:
            detector_wrapper = self.__get_wrapper(detector_id)
        except Exception:
            raise ValueError("The detector wrapper ",
                             detector_id,
                             " does not exist in the database")

        detector = None
        try:
            detector = self.__get_detector(detector_wrapper, detector_id)
        except Exception:
            raise ValueError("The requested detector " + detector_id + " does not exist.")
        if detector is None:
            raise ValueError("The requested detector " + detector_id + "does not exist")

        # Query the condition where the 'tag' equals the specified tag
        conditions = detector.conditions.filter(tag=tag)

        if not conditions:
            return None

        # Convert the internal Condition object(s) to a generic Python dict type
        condition_dicts = []
        for condition in conditions:
            condition_dicts.append(loads(condition.to_json()))
        return condition_dicts

    def get_conditions_by_name(self, detector_id, name):
        # input validation
        if not self.__validate_str(name):
            raise TypeError("Please pass the correct form of input: "
                            "name should be String")

        if not self.__validate_str(detector_id):
            raise TypeError(
                "Please pass the correct type of input: detector_id")

        # Input sanitization
        name = self.__sanitize_str(name)

        # Get the detector of the specified detector_id
        try:
            detector_wrapper = self.__get_wrapper(detector_id)
        except Exception:
            raise ValueError("The detector wrapper ",
                             detector_id,
                             " does not exist in the database")

        detector = None
        try:
            detector = self.__get_detector(detector_wrapper, detector_id)
        except Exception:
            raise ValueError("The requested detector " + detector_id + " does not exist.")
        if detector is None:
            raise ValueError("The requested detector " + detector_id + "does not exist")

        # Query the condition where the 'name' equals the specified name
        conditions = detector.conditions.filter(name=name)
        if not conditions:
            return None

        # Convert the internal Condition object(s) to a generic Python dict type
        condition_dicts = []
        for condition in conditions:
            condition_dicts.append(loads(condition.to_json()))
        return condition_dicts

    def get_condition_by_name_and_tag(self, detector_id, name, tag):
        # Input validation
        if not self.__validate_str(detector_id):
            raise TypeError(
                "Please pass the correct type of input: detector_id")

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
            raise ValueError("The detector wrapper ",
                             detector_id,
                             " does not exist in the database")

        detector = None
        try:
            detector = self.__get_detector(detector_wrapper, detector_id)
        except Exception:
            raise ValueError("The requested detector " + detector_id + " does not exist.")
        if detector is None:
            raise ValueError("The requested detector " + detector_id + "does not exist")

        # Query the condition where the 'name' and 'tag' equal the specified name and tag
        try:
            condition = detector.conditions.get(name=name, tag=tag)
        except DoesNotExist:
            return None

        # Convert the internal Condition object to a generic Python dict type
        return loads(condition.to_json())

    def get_conditions_by_name_and_validity(self, detector_id, name, date):
        # Input validation
        if not self.__validate_str(detector_id):
            raise TypeError(
                "Please pass the correct type of input: detector_id")

        if not (self.__validate_str(name) and self.__validate_interval_parameters(date)):
            raise TypeError("Please pass the valid input type: name should be String, "
                            "date could be either Date or String type.")
        # Input sanitization
        name = self.__sanitize_str(name)

        # Converting all dates given as a String to a datetime Object
        if self.__validate_str(date):
            date = self.__convert_date(date)
        elif self.__validate_datetime(date):
            date = date.replace(microsecond=0)  # Strip off the microseconds

        # Get the detector of the specified detector_id
        try:
            detector_wrapper = self.__get_wrapper(detector_id)
        except Exception:
            raise ValueError("The detector wrapper ",
                             detector_id,
                             " does not exist in the database")

        detector = None
        try:
            detector = self.__get_detector(detector_wrapper, detector_id)
        except Exception:
            raise ValueError("The requested detector " + detector_id + " does not exist.")
        if detector is None:
            raise ValueError("The requested detector " + detector_id + "does not exist")

        # Query the condition where the 'name' equals the specified name
        conditions = detector.conditions.filter(name=name)
        # Loop over all conditions and check whether they are valid at the specified date
        result_list = []
        for condition in conditions:
            if condition.valid_since <= date <= condition.valid_until:
                result_list.append(condition)

        if not result_list:
            return None

        # Convert the internal Condition object(s) to a generic Python dict type
        condition_dicts = []
        for condition in conditions:
            condition_dicts.append(loads(condition.to_json()))
        return condition_dicts

    def get_condition_by_name_and_collection_date(self, detector_id, name, collected_at):
        # Input validation
        if not self.__validate_str(detector_id):
            raise TypeError(
                "Please pass the correct type of input: detector_id")

        if not (self.__validate_str(name) and self.__validate_interval_parameters(collected_at)):
            raise TypeError(
                "Please pass the valid input type: name should be String, collected_at could be "
                "either Date or String type.")
        # Input sanitization
        name = self.__sanitize_str(name)

        # Converting all dates given as a String to a datetime Object
        if self.__validate_str(collected_at):
            collected_at = self.__convert_date(collected_at)
        elif self.__validate_datetime(collected_at):
            collected_at = collected_at.replace(microsecond=0)  # Strip off the microseconds

        # Get the detector of the specified detector_id
        try:
            detector_wrapper = self.__get_wrapper(detector_id)
        except Exception:
            raise ValueError("The detector wrapper ",
                             detector_id,
                             " does not exist in the database")

        detector = None
        try:
            detector = self.__get_detector(detector_wrapper, detector_id)
        except Exception:
            raise ValueError("The requested detector " + detector_id + " does not exist.")
        if detector is None:
            raise ValueError("The requested detector " + detector_id + "does not exist")

        # Query the condition where the 'name' and 'collected_at' equal the specified name and
        # collection_date
        try:
            condition = detector.conditions.get(name=name, collected_at=collected_at)
            # Convert the internal Condition object to a generic Python dict type
            return loads(condition.to_json())
        except DoesNotExist:
            return None

    def update_condition_by_name_and_tag(self,
                                         detector_id,
                                         name,
                                         tag,
                                         type=None,
                                         valid_since=None,
                                         valid_until=None):
        # Input validation
        if not self.__validate_str(detector_id):
            raise TypeError(
                "Please pass the correct type of input: detector_id")

        if not ((self.__validate_interval_parameters(valid_since) or valid_since is None) and
                (self.__validate_interval_parameters(valid_until) or valid_until is None) and
                (self.__validate_str(type) or type is None) and
                self.__validate_str(name) and
                self.__validate_str(tag)):
            raise TypeError(
                "Please pass correct form of input: for valid_since and/or valid_until, they could "
                "be String, Date or None. Only String is accepted for name and tag. Type can be None or String.")

        # Converting all dates given as a String to a datetime Object
        if self.__validate_str(valid_until):
            valid_until = self.__convert_date(valid_until)
        elif self.__validate_datetime(valid_until):
            valid_until = valid_until.replace(microsecond=0)  # Strip off the microseconds
        if self.__validate_str(valid_since):
            valid_since = self.__convert_date(valid_since)
        elif self.__validate_datetime(valid_since):
            valid_since = valid_since.replace(microsecond=0)  # Strip off the microseconds

        if valid_until is not None and valid_since is not None:
            if valid_since > valid_until:
                raise ValueError("Invalid validity interval")

        # Input sanitization
        name = self.__sanitize_str(name)
        tag = self.__sanitize_str(tag)
        if type is not None: type = self.__sanitize_str(type)

        # Get the detector of the specified detector_id
        try:
            detector_wrapper = self.__get_wrapper(detector_id)
        except Exception:
            raise ValueError("The detector wrapper ",
                             detector_id,
                             " does not exist in the database")

        detector = None
        try:
            detector = self.__get_detector(detector_wrapper, detector_id)
        except Exception:
            raise ValueError("The requested detector " + detector_id + " does not exist.")
        if detector is None:
            raise ValueError("The requested detector " + detector_id + "does not exist")

        condition = None
        try:
            condition = detector.conditions.get(name=name, tag=tag)
        except DoesNotExist:
            raise ValueError("No condition with this name and tag can be found")

        if type is not None:
            condition.type = type
        if valid_since is not None:
            condition.valid_since = valid_since
        if valid_until is not None:
            condition.valid_until = valid_until
        detector_wrapper.save()

    def __get_connection(self, connection_dict):
        """
        Returns a  connection of a database whose meta information is in __connection_dict
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
        Delete the database of which name is taken from the db_name parameter
        """
        self.__db_connection.drop_database(db_name)
