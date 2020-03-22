# Unit Test
This directory contains unit tests for the MongoDB adapter. We use PyTest for our unit test. 
Every time you want to execute the unit test, you have to run `generate_test_db.py` first to generate a test database 
and insert dummy data inside. 

#### How to generate test database
```
python generate_test_db.py
```

#### How to execute PyTest
```
py.test
```

#### Check the status of every test unit
```
py.test --verbose
```

#### (Optional)
In some environments, relative-import module does not work. A work around would be to use `sys.path.append()` instead. 
For example, in relative-import:
```
from ...factory import APIFactory
```
You can change it into:
```
import sys
sys.path.append("../..")
from factory import APIFactory
```
