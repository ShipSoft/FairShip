# Unit Test
This directory contains unit tests for the MongoDB adapter. We use PyTest for our unit test.
Every time you want to execute the unit test, you have to run `generate_test_db.py` first to
generate a test database and insert dummy data inside. For checking the test coverage, we use PyTest-Cov.

In these unit tests, we rely heavily on the `get_detector()` function.
Therefore, the unit test execution must be stopped whenever `test_get_detector()` has any fails.

#### How to generate test database
Go to the FairSHiP root folder and execute:
```
python -m conditionsDatabase.tests.test_mongodb.generate_test_db
```

#### How to execute PyTest
We order the test case functions based on their priority.
We set `test_get_detector()` as the first function to make sure `get_detector()` works fine before executing the
other test functions. We also use `--maxfail=1` to shun any false information when there is a fail in `test_get_detector()`.

To execute our Unit Test, go to `/conditionsDatabase/tests/test_mongodb/` and execute:
```
py.test --maxfail=1
```
You can also check the status of every unit by executing:
```
py.test --maxfail=1 --verbose
```

Alternatively, if you don't want to abort the tests after a failing test you can omit the
`--maxfail=1` argument. I.e. execute:
```
py.test
```

#### How to see test coverage
Go to `/conditionsDatabase/tests/test_mongodb/` and execute:
```
pytest --cov=../../databases/mongodb --cov-report term-missing --cov-report html
```
Then, open `/conditionsDatabase/tests/test_mongodb/htmlcov/index.html`.
