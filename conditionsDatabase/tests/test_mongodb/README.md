# Unit Test
This directory contains unit tests for the MongoDB adapter. We use PyTest for our unit test. 
Every time you want to execute the unit test, you have to run `generate_test_db.py` first to generate a test database 
and insert dummy data inside. For checking the test coverage, we use PyTest-Cov.

#### How to generate test database
Go to the FairSHiP root folder and execute:
```
python -m conditionsDatabase.tests.test_mongodb.generate_test_db
```

#### How to execute PyTest
Go to `/conditionsDatabase/tests/test_mongodb/` and execute:
```
py.test
```
You can also check the status of every unit by executing:
```
py.test --verbose
```

#### How to see test coverage
Go to `/conditionsDatabase/tests/test_mongodb/` and execute:
```
pytest --cov=../../databases/mongodb --cov-report term-missing --cov-report html
```
Then, open `/conditionsDatabase/tests/test_mongodb/htmlcov/index.html`.