""" This module contains regression tests for the MongoDB CDB adapter. """
import os
import pytest
import datetime

from ...factory import APIFactory


# Package metadata
__authors__     = ["Yusril Maulidan Raji", "Yitian Kong"]
__copyright__   = "TU/e ST2019"
__version__     = "1.0"
__status__      = "Prototype"
__description__ = "This file contains the test cases for Mongo DB API."


@pytest.fixture
def cdb_api():
    """
    provides access to the condition database api

    :return: api
    """

    home_dir = os.getenv('FAIRSHIP')
    factory = APIFactory()
    db_api = factory.construct_DB_API(home_dir + "/conditionsDatabase/tests/test_mongodb/test_mongodb_config.yml")

    return db_api


@pytest.mark.parametrize("detector_id", [
    # Test with None, int, and empty string
    None, 1, "",
    # Test with not exist detector id
    "detector_id_not_exist",
    # Test with exist detector id
    "detector_id_exist",
    # Test with exist detector id
    "detector_id_exist",
    # Test with exist sub detector
    "detector_id_exist/sub_detector_id_exist",
    # Test with exist sub sub detector
    "detector_id_exist/sub_detector_id_exist/sub_sub_detector_id_exist",
    # Test how the function deals with slashes at the beginning and end [ValueError]
    "/detector_id_exist/",
    # Test with multiple slashes in the middle of the path [ValueError]
    "detector///subdetector",
    # Test with multiple slashes in the beginning and end of the path [ValueError]
    "//detector/subdetector//",
    # Test with underscore delimiter [ValueError]
    "detector_subdetector",
    # Test with single quote character [Accepted]
    "detector'subdetector",
    # Test with tab special character [Accepted]
    "detector\\tsubdetector",
    # Test with double quote character [Accepted]
    "detector\"subdetector",
    # Test with whitespace delimiter [Accepted]
    "detector subdetector"
])
def test_get_detector(cdb_api, detector_id):
    """
    test get_detector()
    this function must be executed first because the other functions relies heavily
    on this function

    :param cdb_api: API
    :param detector_id: String identifying the detector to retrieve (i.e. 'muonflux/straw_tubes').
    """
    has_correct_parameter = True
    if type(detector_id) != str:
        has_correct_parameter = False
        # raise TypeError when detector_id is not an str.
        with pytest.raises(TypeError):
            assert cdb_api.get_detector(detector_id)

    value_error_parameters = ["", "//detector/subdetector//", "detector///subdetector"]
    if detector_id in value_error_parameters:
        has_correct_parameter = False
        # raise ValueError when detector_id is not valid.
        with pytest.raises(ValueError):
            assert cdb_api.get_detector(detector_id)

    value_not_found_parameters = ["detector_id_not_exist", "detector_subdetector",
                                  "detector'subdetector", "detector\\tsubdetector",
                                  "detector\"subdetector", "detector subdetector"]
    if detector_id in value_not_found_parameters:
        has_correct_parameter = False
        # raise TypeError when detector_id does not exist.
        with pytest.raises(ValueError):
            assert cdb_api.get_detector(detector_id)

    if has_correct_parameter:
        result = cdb_api.get_detector(detector_id)
        # check if the result is dict or None
        assert type(result) == dict or result is None, \
            "The result type must be a dict object (if found) or None (if not found)"

        # check if the result has the correct name
        if type(result) == dict:
            # check if the returned detector still has the same detector_id.
            if detector_id == "/detector_id_exist/":
                assert result["name"] == detector_id.split('/')[1], \
                    "the result has different detector name"
            else:
                assert result["name"] == detector_id.split('/')[-1], \
                    "the result has different detector name"

            # check if the detector has the correct value
            if result["name"] == "detector_id_exist":
                assert result["conditions"][0]["name"] == "condition_exist", \
                    "condition name has wrong value"
                assert result["conditions"][0]["tag"] == "tag", "condition tag has wrong value"
                assert result["conditions"][0]["type"] == "type", "condition tag has wrong value"
                assert result["conditions"][0]["collected_at"] == "2020,03,12,11,05,27,000000", \
                    "condition collected_at has wrong value"
                assert result["conditions"][0]["valid_since"] == "2020,03,12,11,05,27,000000", \
                    "condition valid_since has wrong value"
                assert result["conditions"][0]["valid_until"] == "2020,04,10,11,05,27,000000", \
                    "condition valid_until has wrong value"
                assert result["conditions"][0]["values"] == \
                       {"name": "name detector", "value": "value detector"}, \
                    "condition values has wrong value"

            # check if the sub detector has the correct value
            if result["name"] == "sub_detector_id_exist":
                assert result["conditions"][0]["name"] == "sub_detector_id_exist", \
                    "condition name has wrong value"
                assert result["conditions"][0]["tag"] == "sub_tag", "condition tag has wrong value"
                assert result["conditions"][0]["type"] == "sub_type", "condition tag has wrong value"
                assert result["conditions"][0]["collected_at"] == "2020,04,12,11,05,27,000000", \
                    "condition collected_at has wrong value"
                assert result["conditions"][0]["valid_since"] == "2020,04,12,11,05,27,000000", \
                    "condition valid_since has wrong value"
                assert result["conditions"][0]["valid_until"] == "2020,05,12,11,05,27,000000", \
                    "condition valid_until has wrong value"
                assert result["conditions"][0]["values"] == {"name": "name sub detector",
                                                             "value": "value sub detector"}, \
                    "condition values has wrong value"

            # check if the sub sub detector has the correct value
            if result["name"] == "sub_sub_detector_id_exist":
                assert result["conditions"][0]["name"] == "sub_sub_detector_id_exist", \
                    "condition name has wrong value"
                assert result["conditions"][0]["tag"] == "sub_sub_tag", "condition tag has wrong value"
                assert result["conditions"][0]["type"] == "sub_sub_type", \
                    "condition type has wrong value"
                assert result["conditions"][0]["collected_at"] == "2020,05,12,11,05,27,000000", \
                    "condition collected_at has wrong value"
                assert result["conditions"][0]["valid_since"] == "2020,05,12,11,05,27,000000", \
                    "condition valid_since has wrong value"
                assert result["conditions"][0]["valid_until"] == "2020,06,12,11,05,27,000000", \
                    "condition valid_until has wrong value"
                assert result["conditions"][0]["values"] == \
                       {"name": "name sub sub detector", "value": "value sub sub detector"}, \
                    "condition values has wrong value"


@pytest.mark.parametrize("detector_id", [
    # Test with None, int, and empty string
    None, 999, "",
    # Test with exist detector
    "detector_id_exist",
    # Test with exist detector, but not exist sub detector
    "detector_id_exist/sub_detector_id_not_exist",
    # Test with not exist detector
    "detector_id_not_exist",
    # Test with a detector without condition
    "detector_without_condition"
])
def test_get_conditions(cdb_api, detector_id):
    """
    test get_conditions()

    :param cdb_api: API
    :param detector_id: String identifying the detector for which the
    conditions must be retrieved (i.e. 'muonflux/straw_tubes').
    """
    has_correct_parameter = True
    if type(detector_id) != str:
        has_correct_parameter = False
        # raise TypeError when detector_id is not an str.
        with pytest.raises(TypeError):
            assert cdb_api.get_conditions(detector_id)

    not_exist_detectors = ["", "detector_id_not_exist",
                           "detector_id_exist/sub_detector_id_not_exist"]
    if detector_id in not_exist_detectors:
        has_correct_parameter = False
        # raise ValueError when detector_id does not exist.
        with pytest.raises(ValueError):
            assert cdb_api.get_conditions(detector_id)

    if has_correct_parameter:
        if detector_id == "detector_without_condition":
            assert cdb_api.get_conditions(detector_id) is None, \
                "detector with no condition must return None"

        result = cdb_api.get_conditions(detector_id)
        # check if the result is a list or None
        assert type(result) == list or result is None, \
            "the returned type must be list object (if found) or None (if not found)"

        # check if the result has the correct value
        if detector_id == "detector_id_exist":
            assert result[0]["name"] == "condition_exist", "the condition value is wrong"


@pytest.mark.parametrize("detector_id, name", [
    # Test all parameters with None, int, and empty string
    (None, None), (999, 999), ("", ""),
    # Test with exist detector and exist condition
    ("detector_id_exist", "condition_exist"),
    # Test with exist detector, but not exist condition
    ("detector_id_exist", "condition_not_exist"),
    # Test with not exist detector
    ("detector_id_not_exist", "condition_not_exist"),
    # Test with invalid detector_id and valid name
    (999, "condition_exist"),
    # Test with exist detector, not exist detector, and exist condition
    ("detector_id_exist/sub_detector_not_exist", "condition_exist")
])
def test_get_conditions_by_name(cdb_api, detector_id, name):
    """
    test get_conditions_by_name()

    :param cdb_api: API
    :param detector_id: String identifying the detector for which the
    condition must be retrieved (i.e. 'muonflux/straw_tubes').
    :param name: String specifying the name of the conditions to be retrieved (e.g.
    'strawPositions').
    """

    has_correct_parameter_type = True
    if type(detector_id) != str:
        has_correct_parameter_type = False
        # raise TypeError when detector_id is not an str.
        with pytest.raises(TypeError):
            assert cdb_api.get_conditions_by_name(detector_id, name)

    if type(name) != str:
        has_correct_parameter_type = False
        # raise TypeError when name is not an str.
        with pytest.raises(TypeError):
            assert cdb_api.get_conditions_by_name(detector_id, name)

    not_exist_detectors = ["", "detector_id_not_exist",
                           "detector_id_exist/sub_detector_not_exist"]
    if detector_id in not_exist_detectors:
        has_correct_parameter_type = False
        # raise ValueError when detector_id does not exist.
        with pytest.raises(ValueError):
            assert cdb_api.get_conditions_by_name(detector_id, name)

    if has_correct_parameter_type:
        result = cdb_api.get_conditions_by_name(detector_id, name)
        # check if the result is a list.
        assert type(result) == list or result is None, \
            "The result type must be a list (if found) or None (if not found)"
        # check if the result has the correct value
        if detector_id == "detector_id_exist" and name == "condition_exist":
            assert result[0] != name, "the condition has a wrong value"


@pytest.mark.parametrize("detector_id, name, start_date, end_date", [
    # Test with None input for each parameter
    (None, None, None, None),
    # Test with int input for each parameter
    (999, 999, 999, 999),
    # Test with empty string input for each parameter
    ("", "", "", ""),
    # Test with wrong string format for date parameter
    ("detector_id_exist", "condition_exist", "2020,03,16,12,07,30", None),
    # Test with correct string format for date parameter
    ("detector_id_exist", "condition_exist", "2020-03-16 12:07:30", None),
    # Test with datetime obj for date parameter
    ("detector_id_exist", "condition_exist", datetime.datetime(2020, 3, 16, 12, 7, 30), None),
    # Test with string obj for date parameter with precise millisecond (wrong format)
    ("detector_id_exist", "condition_exist", "2020,03,16,12,07,30,129920", None),
    # Test with string obj for date parameter with precise millisecond (correct format)
    ("detector_id_exist", "condition_exist", "2020-03-16 12:07:30:129920", None),
    # Test with datetime obj for date parameter with precise millisecond
    ("detector_id_exist", "condition_exist", datetime.datetime(2020, 3, 12, 11, 5, 27, 767563), None),
    # Test with datetime obj for date parameter with not precise millisecond
    ("detector_id_exist", "condition_exist", datetime.datetime(2020, 3, 12, 11, 5, 27, 555555), None),
    # Test with datetime obj for date parameter with day value
    ("detector_id_exist", "condition_exist", datetime.datetime(2020, 3, 13), None),
    # Test with valid detector id, but invalid name and date
    ("detector_id_exist", 999, 999, None),
    # Test with not exist detector
    ("detector_id_not_exist", "condition_exist", datetime.datetime(2020, 3, 16, 12, 7, 30), None),
    # Test with not exist detector, but not exist sub detector
    ("detector_id_exist/sub_detector_not_exist", "condition_exist", datetime.datetime(2020, 3, 16, 12, 7, 30), None),
    # Test with not found data and one date parameter
    ("detector_id_exist", "condition_exist", "2021-03-16 12:07:30", None),
    # Test with str obj for one date parameter with year, month, date, hour, minute, and second
    ("detector_id_exist", "condition_exist", "2020-03-16 12:07:30", None),
    # Test with str obj for one date parameter with year, month, date, hour, and minute
    ("detector_id_exist", "condition_exist", "2020-03-16 12:07", None),
    # Test with str obj for one date parameter with year, month, date, and hour
    ("detector_id_exist", "condition_exist", "2020-03-16 12", None),
    # Test with str obj for one date parameter with year, month, and date
    ("detector_id_exist", "condition_exist", "2020-03-16", None),
    # Test with str obj for one date parameter with year and month
    ("detector_id_exist", "condition_exist", "2020-03", None),
    # Test with str obj for one date parameter with year
    ("detector_id_exist", "condition_exist", "2020", None),
    # Test with not found date range parameter
    ("detector_id_exist", "condition_exist", "2021-03-16 12:07:30", "2021-04-16 12:07:30"),
    # Test with str obj for date range parameter with year, month, date, hour, minute, and second
    ("detector_id_exist", "condition_exist", "2020-03-16 12:07:30", "2020-04-10 10:07:30"),
    # Test with str obj for date range parameter with year, month, date, hour, and minute
    ("detector_id_exist", "condition_exist", "2020-03-16 12:07", "2020-04-10 10:07"),
    # Test with str obj for date range parameter with year, month, date, and hour
    ("detector_id_exist", "condition_exist", "2020-03-16 12", "2020-04-10 10"),
    # Test with str obj for date range parameter with year, month, and date
    ("detector_id_exist", "condition_exist", "2020-03-16", "2020-04-10"),
    # Test with str obj for date range parameter with year and month
    ("detector_id_exist", "condition_exist", "2020-03", "2020-04"),
    # Test with str obj for date range parameter with year
    ("detector_id_exist", "condition_exist", "2020", "2021"),
])
def test_get_conditions_by_name_and_validity(cdb_api, detector_id, name, start_date, end_date):
    """
    test get_conditions_by_name_and_validity()

    :param cdb_api: API
    :param detector_id: String identifying the detector for which the
    condition must be retrieved (i.e. 'muonflux/straw_tubes').
    :param name: String specifying the name of the conditions to be retrieved (e.g.
    'strawPositions').
    :param start_date: Timestamp specifying a date/time for which conditions must be valid.
    :param end_date: Timestamp specifying the end of a date/time range for which conditions must be valid.
    """

    has_correct_parameter_type = True
    if type(detector_id) != str:
        has_correct_parameter_type = False
        # raise TypeError when detector_id is not an str.
        with pytest.raises(TypeError):
            assert cdb_api.get_conditions_by_name_and_validity(detector_id, name,
                                                               start_date, end_date)

    if type(name) != str:
        has_correct_parameter_type = False
        # raise TypeError when name is not an str.
        with pytest.raises(TypeError):
            assert cdb_api.get_conditions_by_name_and_validity(detector_id, name,
                                                               start_date, end_date)

    if (type(start_date) != str and type(start_date) != datetime.datetime) or \
            (type(end_date) != str and type(end_date) != datetime.datetime and end_date is not None):
        has_correct_parameter_type = False
        # raise TypeError when date is not an str.
        with pytest.raises(TypeError):
            assert cdb_api.get_conditions_by_name_and_validity(detector_id, name,
                                                               start_date, end_date)

    if type(start_date) == str:
        if not has_correct_format(start_date):
            has_correct_parameter_type = False
            # raise ValueError when the format is wrong
            with pytest.raises(ValueError):
                assert cdb_api.get_conditions_by_name_and_validity(detector_id, name,
                                                                   start_date, end_date)

    if type(end_date) == str:
        if not has_correct_format(end_date):
            has_correct_parameter_type = False
            # raise ValueError when the format is wrong
            with pytest.raises(ValueError):
                assert cdb_api.get_conditions_by_name_and_validity(detector_id, name,
                                                                   start_date, end_date)

    not_exist_detectors = ["detector_id_not_exist", "detector_id_exist/sub_detector_not_exist"]
    if detector_id in not_exist_detectors:
        has_correct_parameter_type = False
        # raise ValueError when detector id does not exist.
        with pytest.raises(ValueError):
            assert cdb_api.get_conditions_by_name_and_validity(detector_id, name,
                                                               start_date, end_date)

    if has_correct_parameter_type:
        result = cdb_api.get_conditions_by_name_and_validity(detector_id, name,
                                                             start_date, end_date)
        # check if the result is a list or None
        assert type(result) == list or result is None, \
            "The result type must be a list (if found) or None (if not found)"

        valid_cases = [
            detector_id == "detector_id_exist" and name == "condition_exist" and
            start_date == datetime.datetime(2020, 3, 16, 12, 7, 30),
            detector_id == "detector_id_exist" and name == "condition_exist" and
            start_date == "2020-03-16 12:07:30",
            detector_id == "detector_id_exist" and name == "condition_exist" and
            start_date == "2020-03-16 12:07:30:129920",
            detector_id == "detector_id_exist" and name == "condition_exist" and
            start_date == datetime.datetime(2020, 3, 12, 11, 5, 27, 767563),
            detector_id == "detector_id_exist" and name == "condition_exist" and
            start_date == datetime.datetime(2020, 3, 12, 11, 5, 27, 555555),
            detector_id == "detector_id_exist" and name == "condition_exist" and
            start_date == datetime.datetime(2020, 3, 13),
            detector_id == "detector_id_exist" and name == "condition_exist" and
            start_date == "2020-03-16 12:07:30",
            detector_id == "detector_id_exist" and name == "condition_exist" and
            start_date == "2020-03-16 12:07",
            detector_id == "detector_id_exist" and name == "condition_exist" and
            start_date == "2020-03-16 12",
            detector_id == "detector_id_exist" and name == "condition_exist" and
            start_date == "2020-03-16"
        ]
        invalid_cases = [
            detector_id == "detector_id_exist" and name == "condition_exist" and
            start_date == "2020",
            detector_id == "detector_id_exist" and name == "condition_exist" and
            start_date == "2020-03"
        ]

        # check if the value is correct
        if True in valid_cases:
            assert type(result) == list, "it must return a value. detector_id: " + detector_id + \
                                         " name: " + name + " start_date: " + start_date + \
                                         " end_date: " + end_date
            assert result[0]["name"] == "condition_exist", "condition name value is wrong"
            assert result[0]["tag"] == "tag", "condition tag value is wrong"
            assert result[0]["type"] == "type", "condition type value is wrong"
            assert result[0]["collected_at"] == "2020,03,12,11,05,27,000000", \
                "condition collected_at value is wrong"
            assert result[0]["valid_since"] == "2020,03,12,11,05,27,000000", \
                "condition valid_since value is wrong"
            assert result[0]["valid_until"] == "2020,04,10,11,05,27,000000", \
                "condition valid_until value is wrong"
            assert result[0]["values"] == {"name": "name detector", "value": "value detector"}, \
                "condition values value is wrong"

        if True in invalid_cases:
            assert result is None, "it must return None"

        if type(result) == list:
            assert len(result) == 1, "the result must be a list with one data"


@pytest.mark.parametrize("detector_id, name, tag", [
    # Test all parameters with None, int, and empty string
    (None, None, None), (999, 999, 999), ("", "", ""),
    # Test with exist detector, condition, and tag
    ("detector_id_exist", "condition_exist", "tag"),
    # Test with not exist detector
    ("detector_id_not_exist", "condition_exist", "tag"),
    # Test with exist detector, but not valid name and tag
    ("detector_id_exist", 999, 999),
    # Test with exist detector, but not exist sub detector
    ("detector_id_exist/sub_detector_not_exist", "condition_exist", "tag"),
])
def test_get_condition_by_name_and_tag(cdb_api, detector_id, name, tag):
    """
    test get_condition_by_name_and_tag()

    :param cdb_api: API
    :param detector_id: String identifying the detector for which the
    condition must be retrieved (i.e. 'muonflux/straw_tubes').
    :param name: String specifying the name of the condition to be retrieved (e.g.
    'strawPositions').
    :param tag: String specifying the tag of the condition to be retrieved.
    """

    has_correct_parameter_type = True
    if type(detector_id) != str:
        has_correct_parameter_type = False
        # raise TypeError when detector_id is not an str.
        with pytest.raises(TypeError):
            assert cdb_api.get_condition_by_name_and_tag(detector_id, name, tag)

    if type(name) != str:
        has_correct_parameter_type = False
        # raise TypeError when name is not an str.
        with pytest.raises(TypeError):
            assert cdb_api.get_condition_by_name_and_tag(detector_id, name, tag)

    if type(tag) != str:
        has_correct_parameter_type = False
        # raise TypeError when tag is not an str.
        with pytest.raises(TypeError):
            assert cdb_api.get_condition_by_name_and_tag(detector_id, name, tag)

    not_exist_detectors = ["", "detector_id_not_exist", "detector_id_exist/sub_detector_not_exist"]
    if detector_id in not_exist_detectors:
        has_correct_parameter_type = False
        # raise ValueError when detector_id does not exists.
        with pytest.raises(ValueError):
            assert cdb_api.get_condition_by_name_and_tag(detector_id, name, tag)

    if has_correct_parameter_type:
        result = cdb_api.get_condition_by_name_and_tag(detector_id, name, tag)
        # check if the result is dict or None
        assert type(result) == dict or result is None, \
            "The result type must be a dict (if found) or None (if not found)"

        if detector_id == "detector_id_exist" and name == "condition_exist" and tag == "tag":
            # check if the value is correct
            assert type(result) == dict, "the returned value must be a dictionary"
            assert result["name"] == "condition_exist", "condition name value is wrong"
            assert result["tag"] == "tag", "condition tag value is wrong"
            assert result["type"] == "type", "condition type value is wrong"
            assert result["collected_at"] == "2020,03,12,11,05,27,000000", \
                "condition collected_at value is wrong"
            assert result["valid_since"] == "2020,03,12,11,05,27,000000", \
                "condition valid_since value is wrong"
            assert result["valid_until"] == "2020,04,10,11,05,27,000000", \
                "condition valid_until value is wrong"
            assert result["values"] == {"name": "name detector", "value": "value detector"}, \
                "condition values value is wrong"


@pytest.mark.parametrize("detector_id, tag", [
    # Test all parameters with None, int, and string
    (None, None), (999, 999), ("", ""),
    # Test with exist detector and condition tag
    ("detector_id_exist", "tag"),
    # Test with exist detector, but not exist condition tag
    ("detector_id_exist", "not_exist_condition"),
    # Test with not exist detector and condition tag
    ("detector_id_not_exist", "tag"),
    # Test with None detector_id, but valid tag
    (None, "tag"),
    # Test with detector_id exists, but sub detector not exists
    ("detector_id_exist/sub_detector_id_not_exist", "tag")
])
def test_get_conditions_by_tag(cdb_api, detector_id, tag):
    """
    test get_conditions_by_tag()

    :param cdb_api: API
    :param detector_id: String identifying the detector for which the
    condition must be retrieved (i.e. 'muonflux/straw_tubes').
    :param tag: String specifying the tag of the condition to be retrieved.
    """

    has_correct_parameter_type = True
    if type(detector_id) != str:
        has_correct_parameter_type = False
        # raise TypeError when detector_id is not an str.
        with pytest.raises(TypeError):
            assert cdb_api.get_conditions_by_tag(detector_id, tag)

    if type(tag) != str:
        has_correct_parameter_type = False
        # raise TypeError when tag is not an str.
        with pytest.raises(TypeError):
            assert cdb_api.get_conditions_by_tag(detector_id, tag)

    # not exist detector_id.
    not_exist_detector_id = ["", "detector_id_not_exist",
                             "detector_id_exist/sub_detector_id_not_exist"]
    if detector_id in not_exist_detector_id:
        has_correct_parameter_type = False
        # raise ValueError when detector_id does not exist.
        with pytest.raises(ValueError):
            assert cdb_api.get_conditions_by_tag(detector_id, tag)

    if has_correct_parameter_type:
        result = cdb_api.get_conditions_by_tag(detector_id, tag)
        # check if the result is dict or None
        assert type(result) == list or result is None, \
            "The result type must be a dict (if found) or None (if not found)"
        # check value
        if detector_id == "detector_id_exist" and tag == "tag":
            assert type(result) == list and len(result) == 1, \
                "the returned value must be a list with one element"
            assert result[0]["name"] == "condition_exist", "condition name value is wrong"
            assert result[0]["tag"] == "tag", "condition tag value is wrong"
            assert result[0]["type"] == "type", "condition type value is wrong"
            assert result[0]["collected_at"] == "2020,03,12,11,05,27,000000", \
                "condition collected_at value is wrong"
            assert result[0]["valid_since"] == "2020,03,12,11,05,27,000000", \
                "condition valid_since value is wrong"
            assert result[0]["valid_until"] == "2020,04,10,11,05,27,000000", \
                "condition valid_until value is wrong"
            assert result[0]["values"] == {"name": "name detector", "value": "value detector"}, \
                "condition values value is wrong"


@pytest.mark.parametrize("detector_id, name, collected_at", [
    # Test all parameters with None, int, and empty string
    (None, None, None), (999, 999, 999), ("", "", ""),
    # Test with str collected_at
    ("detector_id_exist", "condition_exist", "2020-03-12 11:05:27"),
    # Test with str collected_at with millisecond
    ("detector_id_exist", "condition_exist", "2020-03-12 11:05:27:767563"),
    # Test with datetime collected_at
    ("detector_id_exist", "condition_exist", datetime.datetime(2020, 3, 12, 11, 5, 27, 767563)),
    # Test with valid detector id, but invalid condition name and collected_at
    ("detector_id_exist", 999, 999),
    # Test with not exist detector_id
    ("detector_id_not_exist", "condition_exist", "2020-03-12 11:05:27"),
    # Test with exist detector_id, but not exist sub detector
    ("detector_id_exist/sub_detector_not_exist", "condition_exist", "2020-03-12 11:05:27"),
    # Test with exist detector_id, but not exist condition name and collected_at
    ("detector_id_exist", "condition_not_exist", "2021-03-12 11:05:27")
])
def test_get_condition_by_name_and_collection_date(cdb_api, detector_id, name, collected_at):
    """
    test get_condition_by_name_and_collection_date()

    :param cdb_api: API
    :param detector_id: String identifying the detector for which the
    condition must be retrieved (i.e. 'muonflux/straw_tubes').
    :param name: String specifying the name of the condition to be retrieved (e.g.
    'strawPositions').
    :param collected_at: Timestamp specifying the moment on which the
    condition was collected / measured. This timestamp must be unique w.r.t.
    the condition name.
    """

    has_correct_parameter_type = True
    if type(detector_id) != str:
        has_correct_parameter_type = False
        # raise TypeError when detector_id is not an str.
        with pytest.raises(TypeError):
            assert cdb_api.get_condition_by_name_and_collection_date(detector_id, name, collected_at)

    if type(name) != str:
        has_correct_parameter_type = False
        # raise TypeError when name is not an str.
        with pytest.raises(TypeError):
            assert cdb_api.get_condition_by_name_and_collection_date(detector_id, name, collected_at)

    if type(collected_at) != str and type(collected_at) != datetime.datetime:
        has_correct_parameter_type = False
        # raise TypeError when date is not an str.
        with pytest.raises(TypeError):
            assert cdb_api.get_condition_by_name_and_collection_date(detector_id, name, collected_at)

    if type(collected_at) is str:
        # if the format is wrong, the function has to raise ValueError
        if not has_correct_format(collected_at):
            has_correct_parameter_type = False
            with pytest.raises(ValueError):
                assert cdb_api.get_condition_by_name_and_collection_date(detector_id, name, collected_at)

    not_exist_detectors = ["detector_id_exist/sub_detector_not_exist", "detector_id_not_exist"]
    if detector_id in not_exist_detectors:
        has_correct_parameter_type = False
        # if detector_id does not exist, raise ValueError
        with pytest.raises(ValueError):
            assert cdb_api.get_condition_by_name_and_collection_date(detector_id, name, collected_at)

    if has_correct_parameter_type:
        result = cdb_api.get_condition_by_name_and_collection_date(detector_id, name, collected_at)
        # check if the result type is dict or None.
        assert type(result) == dict or result is None, \
            "The result type must be a dict (if found) or None (if not found)"

        # check the value
        if type(result) == dict:
            assert type(result) == dict, "the returned value must be a dict"
            assert result["name"] == "condition_exist", "condition name value is wrong"
            assert result["tag"] == "tag", "condition tag value is wrong"
            assert result["type"] == "type", "condition type value is wrong"
            assert result["collected_at"] == "2020,03,12,11,05,27,000000", \
                "condition collected_at value is wrong"
            assert result["valid_since"] == "2020,03,12,11,05,27,000000", \
                "condition valid_since value is wrong"
            assert result["valid_until"] == "2020,04,10,11,05,27,000000", \
                "condition valid_until value is wrong"
            assert result["values"] == {"name": "name detector", "value": "value detector"}, \
                "condition values value is wrong"


@pytest.mark.parametrize("parent_id", [
    # Test with None, int, and empty string
    None, 1, "",
    # Test with not exist detector
    "detector_id_not_exist",
    # Test with exist detector
    "detector_id_exist",
    # Test with exist detector and exist sub detector
    "detector_id_exist/sub_detector_id_exist",
    # Test with exist detector, exist sub detector, and exist sub sub detector
    "detector_id_exist/sub_detector_id_exist/sub_sub_detector_id_exist"
])
def test_list_detectors(cdb_api, parent_id):
    """
    test list_detectors()

    :param cdb_api: API
    :param parent_id: (optional) String identifying the parent detector to
    retrieve the (sub)detector names for (i.e. 'muonflux/straw_tubes').
    """
    has_correct_parameter = True
    if type(parent_id) != str and parent_id is not None:
        has_correct_parameter = False
        # raise TypeError when parent_id is not an str.
        with pytest.raises(TypeError):
            assert cdb_api.list_detectors(parent_id)

    if parent_id == "detector_id_not_exist":
        has_correct_parameter = False
        # raise ValueError when parent_id does not exist.
        with pytest.raises(ValueError):
            assert cdb_api.list_detectors(parent_id)

    if has_correct_parameter:
        result = cdb_api.list_detectors(parent_id)
        # check if the result is a list
        assert type(result) == list or result is None, \
            "The result type must be a list object (if found) or None (if not found)"

        # check when the parent_id is None, it should return all first level detectors
        if parent_id is None:
            assert sorted(result) == sorted(["detector_id_exist", "detector_without_condition"]), \
                "when parent_id is None, it should return all conditions"

        # check if there is an element that is not str and if the detector exists
        for detector in result:
            assert type(detector) == str, "Every element must be a str"
            tmp_detector = None
            try:
                tmp_detector = cdb_api.get_detector(detector)
            except ValueError:
                tmp_detector = None

            assert tmp_detector is not None, "Cannot find this detector: " + detector


@pytest.mark.parametrize("name, parent_id", [
    # Test with None, int, and empty string
    (None, None), (999, 999), ("", ""),
    # Test with a new detector and exist parent detector
    ("detector_id_new1", "detector_id_exist"),
    # Test with a new detector, exist parent detector, and exist parent sub detector
    ("detector_id_new2", "detector_id_exist/sub_detector_id_exist"),
    # Test with a new detector, exist parent detector, exist parent sub detector,
    # and exist parent sub sub detector
    ("detector_id_new3", "detector_id_exist/sub_detector_id_exist/sub_sub_detector_id_exist"),
    # Test with a new detector and not exist parent detector
    ("detector_id_new", "detector_id_not_exist"),
    # Test with sub detector exists and parent detector exists
    ("sub_detector_id_exist", "detector_id_exist"),
    # Test with int at name parameter
    (999, "detector1"),
    # Test with int at parent_id parameter
    ("detector_id_new", 999),
    # Test with none at name parameter
    ("detector_id_new", None),
    # Test with None at parent_id parameter
    (None, "detector_id_exist"),
    # Test with new detector and empty string parent_id
    ("detector_id_new4", ""),
    # Test with empty string detector and exist parent_id
    ("", "detector_id_exist"),
    # Test with / in name and exist parent_id
    ("detector_id_new4/", "detector_id_exist"),
    # Test with int name and None parent_id
    (999, None),
    # Test with name exists and None parent_id
    ("detector_id_exist", None),
    # Test with sub detector not exists and parent detector exists
    ("sub_sub_detector_id_not_exist", "detector_id_exist/sub_detector_id_not_exist"),
])
def test_add_detector(cdb_api, name, parent_id):
    """
    test add_detector()

    :param cdb_api: API
    :param name: String specifying the name for the new detector. Must
    be unique. Must not contain a forward slash (i.e. /).
    :param parent_id: (optional) String identifying the parent detector the
    new detector should be added to as subdetector.
    """

    has_correct_parameter = True
    if type(name) != str:
        has_correct_parameter = False
        # raise TypeError when detector_id is not a str.
        with pytest.raises(TypeError):
            assert cdb_api.add_detector(name, parent_id)

    if type(parent_id) != str and parent_id is not None:
        has_correct_parameter = False
        # raise TypeError when parent_id is not a str and not None.
        with pytest.raises(TypeError):
            assert cdb_api.add_detector(name, parent_id)

    if name == "detector_id_new4/":
        has_correct_parameter = False
        # raise ValueError when name has /.
        with pytest.raises(ValueError):
            assert cdb_api.add_detector(name, parent_id)

    if name == "":
        has_correct_parameter = False
        # raise ValueError when name is empty.
        with pytest.raises(ValueError):
            assert cdb_api.add_detector(name, parent_id)

    if name == "detector_id_exist":
        has_correct_parameter = False
        # raise ValueError when name exists.
        with pytest.raises(ValueError):
            assert cdb_api.add_detector(name, parent_id)

    if name == "sub_sub_detector_id_not_exist":
        has_correct_parameter = False
        # raise ValueError when sub detector not exists and parent detector exists.
        with pytest.raises(ValueError):
            assert cdb_api.add_detector(name, parent_id)

    if has_correct_parameter:
        if parent_id == "detector_id_not_exist":
            # if parent_id does not exist, then raise ValueError.
            with pytest.raises(ValueError):
                assert cdb_api.add_detector(name, parent_id)
        elif name == "sub_detector_id_exist":
            # if sub detector exists, then raise ValueError.
            with pytest.raises(ValueError):
                assert cdb_api.add_detector(name, parent_id)
        else:
            # Test if detector_id is the subdetector of the parent_id
            cdb_api.add_detector(name, parent_id)
            tmp_det_id = ""
            if parent_id is None:
                tmp_det_id = '/' + name
            else:
                tmp_det_id = parent_id + '/' + name

            new_detector_id = cdb_api.get_detector(tmp_det_id)
            if name == "":
                assert new_detector_id['name'] == parent_id, \
                    "detector name should be equal to parent_id when the inserted detector id is empty"
            else:
                assert new_detector_id['name'] == name, \
                    "detector name should be equal to the inserted detector id"


@pytest.mark.parametrize("detector_id, name, values, test_type, tag, collected_at, valid_since, valid_until", [
    # Test all parameters with None
    (None, None, None, None, None, None, None, None),
    # Test all parameters with integer
    (999, 999, 999, 999, 999, 999, 999, 999),
    # Test all parameters with empty string
    ("", "", "", "", "", "", "", ""),
    # Test with detector exists
    ("detector_id_exist", "strawPositions1", {"dictPar1": "dictVal1"}, "calibration", "tag-1",
     "2020-03-10 11:05:27", "2020-03-10 11:05:27", "2020-04-12 11:05:27"),
    # Test with condition name exists, but tag not exists
    ("detector_id_exist", "condition_exist", {"dictPar1": "dictVal1"}, "calibration", "tag-55",
     "2020-03-10 11:05:27", "2020-03-10 11:05:27", "2020-04-12 11:05:27"),
    # Test with condition tag exists, but name exists
    ("detector_id_exist", "condition_not_exist_but_tag_exist", {"dictPar1": "dictVal1"},
     "calibration", "tag", "2020-03-10 11:05:27", "2020-03-10 11:05:27", "2020-04-12 11:05:27"),
    # Test with condition name and tag exist
    ("detector_id_exist", "condition_exist", {"dictPar1": "dictVal1"}, "calibration", "tag",
     "2020-03-10 11:05:27", "2020-03-10 11:05:27", "2020-04-12 11:05:27"),
    # Test with str collected_at, valid_since, valid_until
    ("detector_id_exist", "strawPositions2", {"dictPar1": "dictVal1"}, "calibration", "tag-2",
     "2020-03-10 11:05:27", "2020-03-10 11:05:27", "2020-04-12 11:05:27"),
    # Test with str collected_at, valid_since, valid_until with millisecond
    ("detector_id_exist", "strawPositions3", {"dictPar1": "dictVal1"}, "calibration", "tag-3",
     "2020-03-10 11:05:27", "2020-03-10 11:05:27", "2020-04-12 11:05:27"),
    # Test with datetime collected_at, valid_since, valid_until
    ("detector_id_exist", "strawPositions4", {"dictPar1": "dictVal1"}, "calibration", "tag-4",
     datetime.datetime(2020, 3, 12, 11, 5, 27, 767563),
     datetime.datetime(2020, 3, 12, 11, 5, 27, 767563),
     datetime.datetime(2020, 4, 10, 11, 5, 27, 767563)),
    # Test with valid_since is greater than valid_until
    ("detector_id_exist", "strawPositions5", {"dictPar1": "dictVal1"}, "calibration", "tag-5",
     datetime.datetime(2020, 3, 12, 11, 5, 27, 767563),
     datetime.datetime(2020, 3, 12, 11, 5, 27, 767563),
     datetime.datetime(2020, 2, 10, 11, 5, 27, 767563)),
    # Test with detector not exists
    ("detector_id_not_exist", "strawPositions6", {"dictPar1": "dictVal1"}, "calibration", "tag-6",
     "2020-03-12 11:05:27", "2020-03-12 11:05:27", "2020-04-10 11:05:27"),
    # Test with valid parameters, except all datetime parameters are integer
    ("detector_id_exist", "strawPositions1", {"dictPar1": "dictVal1"}, "calibration", "tag-1",
     999, 999, 999),
    # Test with valid parameters, except type is integer
    ("detector_id_exist", "strawPositions1", {"dictPar1": "dictVal1"}, 999, "tag-1",
     "2020-03-10 11:05:27", "2020-03-10 11:05:27", "2020-04-12 11:05:27"),
    # Test with sub detector not exist
    ("detector_id_exist/sub_detector_not_exist", "strawPositions1", {"dictPar1": "dictVal1"},
     "calibration", "tag-1", "2020-03-10 11:05:27", "2020-03-10 11:05:27", "2020-04-12 11:05:27"),
    # Test with invalid collected_at, valid_since, and valid_until
    ("detector_id_with_invalid_date_parameters", "strawPositions1", {"dictPar1": "dictVal1"},
     "calibration", "tag-1", 999, 999, 999),
    # Test with None values
    ("detector_id_not_exist_with_values_none", "strawPositions7", None, "calibration", "tag-6",
     "2020-03-12 11:05:27", "2020-03-12 11:05:27", "2020-04-10 11:05:27"),
    # Test with empty string values
    ("detector_id_not_exist_with_values_empty", "strawPositions8", "", "calibration", "tag-6",
     "2020-03-12 11:05:27", "2020-03-12 11:05:27", "2020-04-10 11:05:27"),
])
def test_add_condition(cdb_api, detector_id, name, values, test_type, tag,
                       collected_at, valid_since, valid_until):
    """
    test add_condition()

    :param cdb_api: API
    :param detector_id: String identifying the detector to which the
    condition will be added (i.e. 'muonflux/straw_tubes').
    :param name: String specifying the name of the condition (e.g. 'strawPositions').
    :param values: Dictionary containing the values of the condition.
    :param test_type: String specifying the type of condition (e.g. 'calibration').
    :param tag: String specifying a tag for the condition. Must be unique
    for the same condition name.
    :param collected_at: Timestamp specifying the date/time the condition
    was acquired. Must be unique w.r.t. the condition name.
    :param valid_since: Timestamp specifying the date/time as of when the
    condition is valid.
    :param valid_until: Timestamp specifying the date/time the
    condition up until the condition is valid.
    """

    has_correct_parameter_type = True
    if type(detector_id) != str or detector_id == "" or type(name) != str or name == "" or \
            (type(test_type) != str and type(test_type) is not None) or \
            type(tag) != str or tag == "" or values == "" or values is None:
        has_correct_parameter_type = False
        # raise TypeError when detector_id /name /type /tag is not an str.
        # raise TypeError when /values is empty or None.
        with pytest.raises(TypeError):
            assert cdb_api.add_condition(detector_id, name, tag, values, test_type,
                                         collected_at, valid_since, valid_until)

    if (type(collected_at) != str and type(collected_at) != datetime.datetime and collected_at is not None) or \
            (type(valid_since) != str and type(valid_since) != datetime.datetime and valid_since is not None) or \
            (type(valid_until) != str and type(valid_until) != datetime.datetime and valid_until is not None):
        has_correct_parameter_type = False
        # raise TypeError when collected_at or valid_until has a wrong type.
        with pytest.raises(TypeError):
            assert cdb_api.add_condition(detector_id, name, tag, values, test_type,
                                         collected_at, valid_since, valid_until)

    if (type(collected_at) == str or type(valid_until) == str or type(valid_since) == str) and \
            has_correct_parameter_type:
        # if all parameters have correct type, but collected_at, valid_until, or
        # valid_since's format is wrong, the function must raise ValueError
        if not has_correct_format(collected_at) or not has_correct_format(valid_until) or \
                not has_correct_format(valid_since):
            has_correct_parameter_type = False
            with pytest.raises(ValueError):
                assert cdb_api.add_condition(detector_id, name, tag, values, test_type,
                                             collected_at, valid_since, valid_until)

    # when valid_since is greater than valid_until, raise ValueError
    if (type(valid_since) == datetime.datetime and type(valid_until) == datetime.datetime) and \
            valid_since > valid_until:
        has_correct_parameter_type = False
        with pytest.raises(ValueError):
            assert cdb_api.add_condition(detector_id, name, tag, values, test_type, collected_at,
                                         valid_since, valid_until)

    # when valid_since is greater than valid_until, raise ValueError
    if (type(valid_since) == str and type(valid_until) == str) and has_correct_parameter_type:
        if valid_since == "" or valid_until == "":
            has_correct_parameter_type = False
            with pytest.raises(ValueError):
                assert cdb_api.add_condition(detector_id, name, tag, values, test_type,
                                             collected_at, valid_since, valid_until)
        else:
            datetime_valid_since = __convert_str_to_datetime(valid_since)
            datetime_valid_until = __convert_str_to_datetime(valid_until)
            if datetime_valid_since > datetime_valid_until:
                has_correct_parameter_type = False
                with pytest.raises(ValueError):
                    assert cdb_api.add_condition(detector_id, name, tag, values, test_type,
                                                 collected_at, valid_since, valid_until)

    # when detector does not exist, it must raise ValueError
    if detector_id == "detector_id_not_exist" or \
            detector_id == "detector_id_exist/sub_detector_not_exist":
        has_correct_parameter_type = False
        with pytest.raises(ValueError):
            assert cdb_api.add_condition(detector_id, name, tag, values, test_type,
                                         collected_at, valid_since, valid_until)

    # when condition name and tag exist, it must raise ValueError
    if detector_id == "detector_id_exist" and name == "condition_exist" and tag == "tag":
        has_correct_parameter_type = False
        with pytest.raises(ValueError):
            assert cdb_api.add_condition(detector_id, name, tag, values, test_type,
                                         collected_at, valid_since, valid_until)

    if has_correct_parameter_type:
        # check detector value.
        cdb_api.add_condition(detector_id, name, tag, values, test_type,
                              collected_at, valid_since, valid_until)
        detector = cdb_api.get_detector(detector_id)

        # Check if the name is still the same
        assert detector["name"] == detector_id, "the detector has different name"

        # get the new inserted condition
        conditions = detector["conditions"]
        new_condition = None
        for condition in conditions:
            if condition["tag"] == tag and condition["name"] == name:
                new_condition = condition
                break

        # Check if the tag is correct
        assert new_condition["tag"] == tag, "tag is not correct"

        # Check if the values is correct
        assert new_condition["values"] == values, "value is not correct"

        # Check if the type is correct
        assert new_condition["type"] == test_type, "type is not correct"

        # Check if the collected_at is correct
        if type(collected_at) == datetime.datetime:
            assert __convert_str_to_datetime(new_condition["collected_at"]) \
                   == collected_at.replace(microsecond=0), \
                "collected_at is not correct"
        elif type(collected_at) == str:
            assert __convert_str_to_datetime(new_condition["collected_at"]) == \
                   __convert_str_to_datetime(collected_at).replace(microsecond=0), \
                "collected_at is not correct"

        # Check if the valid_until exists
        if type(valid_until) == datetime.datetime:
            assert __convert_str_to_datetime(new_condition["valid_until"]) \
                   == valid_until.replace(microsecond=0), \
                "valid_until is not correct"
        elif type(valid_until) == str:
            assert __convert_str_to_datetime(new_condition["valid_until"]) == \
                   __convert_str_to_datetime(valid_until).replace(microsecond=0), \
                "valid_until is not correct"


@pytest.mark.parametrize("detector_id, name, tag, test_type, valid_since, valid_until", [
    # Test with None input for each parameter
    (None, None, None, None, None, None),
    # Test with int input for each parameter
    (999, 999, 999, 999, 999, 999),
    # Test with empty string input for each parameter
    ("", "", "", "", "", ""),
    # Test with str format for valid_since and valid_until
    ("detector_id_exist", "condition_exist", "tag", "type",
     "2020-04-16 12:07:30", "2020-04-17 12:07:30"),
    # Test with str format for valid_since and valid_until, and with millisecond
    ("detector_id_exist", "condition_exist", "tag", "type",
     "2020-04-16 12:07:30:129910", "2020-04-17 12:07:30:129910"),
    # Test with datetime format for valid_since and valid_until
    ("detector_id_exist", "condition_exist", "tag", "type",
     datetime.datetime(2020, 4, 16, 12, 7, 30),
     datetime.datetime(2020, 4, 17, 12, 7, 30)),
    # Test with datetime format for valid_since and valid_until, and with millisecond
    ("detector_id_exist", "condition_exist", "tag", "type",
     datetime.datetime(2020, 4, 16, 12, 7, 30, 129910),
     datetime.datetime(2020, 4, 17, 12, 7, 30, 129910)),
    # Test with str valid_since and datetime valid_until
    ("detector_id_exist", "condition_exist", "tag", "type", "2020-04-16 12:07:30",
     datetime.datetime(2020, 4, 17, 12, 7, 30)),
    # Test with datetime valid_since and str valid_until
    ("detector_id_exist", "condition_exist", "tag", "type",
     datetime.datetime(2020, 4, 13), "2020-04-16 12:07:30"),
    # Test if it has invalid month or date
    ("detector_id_exist", "condition_exist", "tag", "type", "2020-24-16 12:07:30",
     datetime.datetime(2020, 4, 17, 12, 7, 30)),
    # Test if valid_Since > valid_until
    ("detector_id_exist", "condition_exist", "tag", "type",
     datetime.datetime(2020, 4, 20, 12, 7, 30),
     datetime.datetime(2020, 4, 17, 12, 7, 30)),
    # Test with valid detector_id, but not valid other parameters
    ("detector_id_exist", 999, 999, 999, 999, 999),
    # Test with not exist detector_id
    ("detector_id_not_exist", "condition_exist", "tag", "type",
     datetime.datetime(2020, 4, 16, 12, 7, 30),
     datetime.datetime(2020, 4, 17, 12, 7, 30)),
    # Test with exist detector_id, but not exist sub detector
    ("detector_id_exist/sub_detector_id_not_exist", "condition_exist", "tag", "type",
     datetime.datetime(2020, 4, 16, 12, 7, 30),
     datetime.datetime(2020, 4, 17, 12, 7, 30)),
    # Test with exist detector_id and condition name does not exist
    ("detector_id_exist", "condition_not_exist", "tag", "type",
     datetime.datetime(2020, 4, 16, 12, 7, 30),
     datetime.datetime(2020, 4, 17, 12, 7, 30)),
])
def test_update_condition_by_name_and_tag(cdb_api, detector_id, name, tag,
                                          test_type, valid_since, valid_until):
    """
    test update_condition_by_name_and_tag()

    :param cdb_api: API
    :param detector_id: String identifying the detector for which the
    condition must be retrieved (i.e. 'muonflux/straw_tubes').
    :param name: String specifying the name of the condition to be retrieved (e.g.
    'strawPositions').
    :param tag: String specifying the tag of the condition to be updated.
    :param test_type: (optional) String specifying the type of condition (e.g. 'calibration').
    :param  valid_since: Timestamp specifying the date/time as of when the
    condition is valid. Can be of type String or datetime.
    :param  valid_until: Timestamp specifying the date/time up until the
    condition is valid. Can be of type String or datetime.
    """
    has_correct_parameter = True
    if type(detector_id) != str or type(name) != str or type(tag) != str or \
            (type(test_type) != str and test_type is not None):
        has_correct_parameter = False
        # raise TypeError when detector/name/tag_id is not an str.
        with pytest.raises(TypeError):
            assert cdb_api.update_condition_by_name_and_tag(detector_id, name, tag,
                                                            test_type, valid_since, valid_until)

    if (type(valid_since) != str and type(valid_since) != datetime.datetime and valid_since is not None) or \
            (type(valid_until) != str and type(valid_until) != datetime.datetime and valid_until is not None):
        has_correct_parameter = False
        # raise TypeError when date is not correct format.
        with pytest.raises(TypeError):
            assert cdb_api.update_condition_by_name_and_tag(detector_id, name, tag,
                                                            test_type, valid_since, valid_until)

    if type(valid_since) == str and not has_correct_format(valid_since):
        has_correct_parameter = False
        # if the format is wrong, the function has to raise ValueError
        with pytest.raises(ValueError):
            assert cdb_api.update_condition_by_name_and_tag(detector_id, name, tag,
                                                            test_type, valid_since, valid_until)

    if type(valid_until) == str and not has_correct_format(valid_until):
        has_correct_parameter = False
        # if the format is wrong, the function has to raise ValueError
        with pytest.raises(ValueError):
            assert cdb_api.update_condition_by_name_and_tag(detector_id, name, tag,
                                                            test_type, valid_since, valid_until)

    if type(valid_since) == datetime.datetime \
            and type(valid_until) == datetime.datetime \
            and valid_since > valid_until:
        has_correct_parameter = False
        # if valid_since > valid_until, raise ValueError
        with pytest.raises(ValueError):
            assert cdb_api.update_condition_by_name_and_tag(detector_id, name, tag,
                                                            test_type, valid_since, valid_until)

    if detector_id == "detector_id_not_exist" \
            or detector_id == "detector_id_exist/sub_detector_id_not_exist":
        has_correct_parameter = False
        # if detector_id does not exist, raise ValueError
        with pytest.raises(ValueError):
            assert cdb_api.update_condition_by_name_and_tag(detector_id, name, tag,
                                                            test_type, valid_since, valid_until)

    if name == "condition_not_exist":
        has_correct_parameter = False
        # if condition name does not exist, raise ValueError
        with pytest.raises(ValueError):
            assert cdb_api.update_condition_by_name_and_tag(detector_id, name, tag, test_type,
                                                            valid_since, valid_until)

    if has_correct_parameter:
        cdb_api.update_condition_by_name_and_tag(detector_id, name, tag,
                                                 test_type, valid_since, valid_until)

        # check if the result is correct.
        if detector_id == "detector_id_exist":
            result_con = cdb_api.get_condition_by_name_and_tag(detector_id, name, tag)
            if type(valid_since) == str:
                assert __convert_str_to_datetime(result_con["valid_since"]) == \
                       __convert_str_to_datetime(valid_since).replace(microsecond=0), \
                    "valid_since is not updated successfully"
            elif type(valid_since) == datetime.datetime:
                assert __convert_str_to_datetime(result_con["valid_since"]) == \
                       valid_since.replace(microsecond=0), \
                    "valid_since is not updated successfully"

            if type(valid_until) == str:
                assert __convert_str_to_datetime(result_con["valid_until"]) == \
                       __convert_str_to_datetime(valid_until).replace(microsecond=0), \
                    "valid_until is not updated successfully"
            elif type(valid_until) == datetime.datetime:
                assert __convert_str_to_datetime(result_con["valid_until"]) == \
                       valid_until.replace(microsecond=0), \
                    "valid_until is not updated successfully"


@pytest.mark.parametrize("detector_id", [
    # Test with None, int, and empty string
    "", None, 1,
    # Test with not exist detector id
    "detector_id_not_exist",
    # Test with exist sub sub detector
    "detector_id_exist/sub_detector_id_exist/sub_sub_detector_id_exist",
    # Test with exist sub detector
    "detector_id_exist/sub_detector_id_exist",
    # Test with exist detector id
    "detector_id_exist"
])
def test_remove_detector(cdb_api, detector_id):
    """
    test remove_detector().
    This function must be executed last because the test data is used in the other test case

    :param cdb_api: API
    :param detector_id: String identifying the detector to remove (i.e. 'muonflux/straw_tubes').
    """

    if type(detector_id) != str:
        # raise TypeError when detector_id is not an str.
        with pytest.raises(TypeError):
            assert cdb_api.remove_detector(detector_id)
    elif detector_id == "detector_id_not_exist" or detector_id == "":
        # raise ValueError since detector does not exists.
        with pytest.raises(ValueError):
            assert cdb_api.remove_detector(detector_id)
    else:
        # check if detector_id still exists or not
        cdb_api.remove_detector(detector_id)
        tmp_detector = None
        try:
            tmp_detector = cdb_api.get_detector(detector_id)
        except ValueError:
            tmp_detector = None

        assert tmp_detector is None, "detector_id still exists: " + detector_id


def has_correct_format(time_stamp):
    """
    check if the passed time_stamp has a correct format or not
    allowed format: "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d %H", "%Y-%m-%d", "%Y-%m", "%Y"
    :param time_stamp: time_stamp with str type
    :return: Boolean validation result
    """

    if type(time_stamp) != str:
        raise TypeError("time_stamp must be a string")

    # Accepted formats for time_stamp
    time_stamp_str_format = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d %H",
                             "%Y-%m-%d", "%Y-%m", "%Y"]

    correct_format = False
    for time_stamp_format in time_stamp_str_format:
        try:
            datetime.datetime.strptime(time_stamp, time_stamp_format)
            correct_format = True
            break
        except ValueError:
            continue

    return correct_format


def __convert_str_to_datetime(input_date_string):
    """
    convert string into datetime

    :param input_date_string string that contains datetime value
    """
    # Accepted formats for time_stamp
    time_stamp_str_format = ["%Y,%m,%d,%H,%M,%S,%f", "%Y", "%Y-%m", "%Y-%m-%d", "%Y-%m-%d %H",
                             "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"]
    datetime_value = None
    for time_stamp_format in time_stamp_str_format:
        try:
            datetime_value = datetime.datetime.strptime(input_date_string, time_stamp_format)
            break
        except ValueError:
            pass

    if datetime_value is None:
        raise ValueError("Please pass the correct date input. This date string should "
                         "contain only digits/:/ /-. The minimum length could be 4 digits, "
                         "representing the year. ")
    else:
        return datetime_value
