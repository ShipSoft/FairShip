###
#
# This is an example file to demonstrate how the conditionsDatabase API works
#
###
from ..factory import APIFactory
import datetime


# Instantiate an API factory
api_factory = APIFactory()
# Call construct_DB_API to get an CDB API instance, the path must lead to a valid config.yml file containing the database configuration
conditionsDB = api_factory.construct_DB_API("/FairShip/conditionsDatabase/config.yml")

value_array = {"x": [5, 2, 6, 3, 7]}

# How to add a main detector to the database:
conditionsDB.add_detector("detector3")
# How to add a subdetector to a parent detector in the database:
# Params: (subdetector name, parent detector ID)
conditionsDB.add_detector("subdetector1" , "detector3")

# Show all main detector names in the database:
result = conditionsDB.list_detectors()
print(result)
# Show all subdetectors of a specific detector
result = conditionsDB.list_detectors("detector3")
print(result)

# Adding a condition to the database
# Name-Tag and Name-CollectedAt combinations should be unique in the database
# Dates can be parsed as a string: year-month-day hour:minutes:second    OR    as a datetime object
conditionsDB.add_condition("detector3/subdetector1", "conditionName1", "SampleTag", "2020-03-21 18:14", value_array, "testType", "2020-03-21 18:12", "2020-05-20")
conditionsDB.add_condition("detector3/subdetector1", "conditionsName1", "SampleTag2", datetime.datetime(2020,3,22,20,20), value_array, "testType", datetime.datetime(2020,3,23,18,12), datetime.datetime(2020,3,23,18,12))
# A condition can also be added to the database without specifying the type, valid_since and/or valid_until, they will take the default values: None, datetime.datetime.now(), datetime.datetime.MAX respectively
conditionsDB.add_condition("detector3/subdetector1", "conditionsName1", "SampleTag3", datetime.datetime(2020,3,25,20,20), value_array)

# Get detector dictionary by specifying the detectorID: "Detector/subdetector/subdetector ..."
# This function gets subdetector: "subdetector1" of detector: "detector3"
result = conditionsDB.get_detector("detector3/subdetector1")
print(result)

# Get a list of all conditions of a detector
# This function gets a list of conditions in subdetector: "subdetector1" of detector: "detector3"
result = conditionsDB.get_conditions("detector3/subdetector1")
print(result)

# Get a list of all conditions with a specific tag for the specified detector
# This function gets a list of conditions in subdetector: "subdetector1" of detector: "detector3" WITH the tag "SampleTag"
result = conditionsDB.get_conditions_by_tag("detector3/subdetector1", "SampleTag")
print(result)

# Get a condition dictionary by specifying the detectorID, condition name, condition tag
# This function gets a condition in subdetector: "subdetector1" of detector: "detector3" WITH the name "conditionName1" AND the tag "SampleTag2"
result = conditionsDB.get_condition_by_name_and_tag("detector3/subdetector1", "conditionsName1", "SampleTag2")
print(result)

# Get a condition dictionary by specifying the detectorID and condition collected_at
# This function gets a condition in subdetector: "subdetector1" of detector: "detector3" WITH the name "conditionName1" AND the collected_at: 2020-03-21 18:14:00
# If a certain time accuracy is omitted then defaults are assumed. See API documentation for details
conditionsDB.get_condition_by_name_and_collection_date("detector3/subdetector1", "conditionName1",  "2020-03-21 18:14")

# Get a list of conditions by specifying the detectorID, condition name, and date where it should be valid
# This function gets a condition in subdetector: "subdetector1" of detector: "detector3" WITH the name "conditionName1" AND the valid_since <= 2020-03-22 00:00:00 AND the valid_until >= 2020-03-22 00:00:00
conditionsDB.get_conditions_by_name_and_validity("detector3/subdetector1", "conditionName1", "2020-03-22")

# Update a condition type, valid_since and valid_until by specifying the detectorID, condition name and condition tag
# This function sets the following values to the subdetector: "subdetector1" of detector: "detector3" WITH the name "conditionName1" AND the tag "SampleTag"
# Values updated: Type:  "testType2"   valid_since: "2020-03-20 18:12:00"    valid_until: stays the same
conditionsDB.update_condition_by_name_and_tag("detector3/subdetector1", "conditionName1", "SampleTag", "testType2", "2020-03-20 18:12")

# EXECUTE WITH CARE: Removes a subdetector including all of it's values from the database
# This function removes subdetector: "subdetector1" of detector: "detector3" and all of it's values from the database
conditionsDB.remove_detector("detector3/subdetector1")
