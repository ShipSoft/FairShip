"""
This module tests the factory
"""
import os
import pytest
import yaml

from ..factory import APIFactory
from ..databases.mongodb.mongodbadapter import MongoToCDBAPIAdapter


@pytest.fixture
def supply_dbAPI():
    """
    This method creates an instance of database implementation of the API.
    This can be used by other functions.
    """
    factory = APIFactory()
    db_api = factory.construct_DB_API()
    return db_api

@pytest.mark.smoke_test
def test_create_mongo_api():
    """
    This method checks if the factory can create a proper instance of the API.
    """
    factory = APIFactory()
    db_api = factory.construct_DB_API()
    assert isinstance(db_api, MongoToCDBAPIAdapter)

@pytest.mark.smoke_test
def test_create_unknown_api():
    """
    This method checks if the factory can raise a proper exception
    if unsupported databse type is specified in the configuration file
    """
    factory = APIFactory()
    home_dir = os.getenv('FAIRSHIP')

    with pytest.raises(NotImplementedError):
        assert factory.construct_DB_API(home_dir + "/conditionsDatabase/tests/test_config.yml")
