###
#
# This is an example file to demonstrate how the conditionsDatabase API works
# It reads the geometry file and adds subdetectors with their positions to the condDB
# Takes about 5 mins to fill the condDB
###
from __future__ import print_function, division
from factory import APIFactory
import datetime, sys


from builtins import range
import operator
from argparse import ArgumentParser
from array import array
import os,ROOT, getopt

level=0
try:
        opts, args = getopt.getopt(sys.argv[1:], "l:s:",[])
except getopt.GetoptError:
        # print help information and exit:
        print(' enter -l: level or -s: subdetector')
        sys.exit()
	
for o, a in opts:
   if o in ("-l",):
      level = int(a)
   if o in ("-s",):
      sd = str(a)      

# Instantiate an API factory
api_factory = APIFactory()
# Call construct_DB_API to get an CDB API instance, the path must lead to a valid config.yml file containing the database configuration

conditionsDB = api_factory.construct_DB_API("/home/eric/snd-soft-23april-2021/sndsw/conditionsDatabase/config.yml")

detector=""
count=0

def showdetectors(detector,count,level): 
  #print ("showdetectors called. count=",count," level=",level) 
  # Show all detector names in the database:
  result = conditionsDB.list_detectors(detector)
  if len(result) > 0:
    if detector=="":
        print ("snd subdetectors:",result)
    else:
        print ("subdetectors inside",detector," :",result)
    if count < level:
      count+=1    
      for j in range(len(result)):
        showdetectors(result[j],count,level)  
  else:
    print ("No more subdetectors below subdetector/channel:",detector)
  #print ("count=",count,"All subdetectors listed up to level",level,".")
  return 
  
#showdetectors(detector,count,level)
result = conditionsDB.get_conditions(sd)
print ("Conditions of subdetector ",sd," are ",result)
sys.exit()
