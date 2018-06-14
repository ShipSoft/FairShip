import random

from models import *
from mongoengine import *

connect(db='cern',
        # user='',
        # password='',
        host='localhost',
        port=27017
        )

for i in range(1000):
    sub = Subdetector(name='subdetector' + i.__str__())

    for j in range(random.randint(1,10)):
        seq = random.randint(1,1000)
        # param = Parameter(name='param' + seq.__str__(), value='value' + seq.__str__())
        # param.save()
        sub.parameters.append(Parameter(name='param' + seq.__str__(), value='value' + seq.__str__()))

    sub.save()
