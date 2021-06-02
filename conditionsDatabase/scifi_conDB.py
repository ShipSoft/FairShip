###
#
# This is an example file to demonstrate how the conditionsDatabase API works
# It read the geometry file and adds the positions to the condDB
#
###
from __future__ import print_function, division
from factory import APIFactory
import datetime, sys


from builtins import range
import operator
from argparse import ArgumentParser
from array import array
import os,ROOT,ast

api_factory = APIFactory()
conditionsDB = api_factory.construct_DB_API("/home/eric/snd-soft-23april-2021/sndsw/conditionsDatabase/config.yml")

	    
scifi_n=0
plane_n=0
board_n=0
#print ("conditions ",conditions)
board_id=0
if 1==0:
 #add board id condition to all boards in volTarget_1/SciFi
 for scifi_n in range(5):
   for plane_n in range(2):
      for board_n in range(3):
        conditionsDB.add_condition("volTarget_1/Scifi_"+str(scifi_n)+"/plane_"+str(plane_n)+"/board_"+str(board_n), "id", "board_id", board_id,None,datetime.datetime.now(), datetime.datetime.max)  
        board_id+=1
	
 #add all 36 boards with id, links them to subdetector they go into
 conditionsDB.add_detector("daq")
 for board_id in range(36):
   conditionsDB.add_detector("board_"+str(board_id) , "daq")
   conditionsDB.add_condition("daq/board_"+str(board_id), "id", "board_id", board_id,None,datetime.datetime.now(), datetime.datetime.max)  
 
 #check board id was correctly added
 for board_id in range(36):
  id = conditionsDB.get_conditions_by_tag("daq/board_"+str(board_id),"board_id")
  print ("Board id of daq/board_"+str(board_id)," : ",id)
   
board_id=0
#remove board for debugging
#conditionsDB.remove_detector("daq/board_"+str(board_id))
#sys.exit()
#add board_0 if it was removed for debugging
#conditionsDB.add_detector("board_"+str(board_id) , "daq")
#conditionsDB.add_condition("daq/board_"+str(board_id), "id", "board_id", board_id,None,datetime.datetime.now(), datetime.datetime.max)  

conditions={}
input= open("daq/channels_settings.dict","r")
contents=input.read()
orig_conditions=ast.literal_eval(contents)
#mongo doesn't accept integer keys - convert them to strings
keys_values = orig_conditions.items()              
conditions = {str(key): value for key, value in keys_values}
for skey,svalue in keys_values:
    skey_values = svalue.items()
    svalue= {str(key): value for key,value in skey_values} 
    conditions[str(skey)]=svalue  

conditionsDB.add_condition("daq/board_"+str(board_id), "settings", "Channel_settings", conditions,None,datetime.datetime.now(), datetime.datetime.max)  

orig_conditions={}
input= open("daq/qdc_range.dict","r")
contents=input.read()
orig_conditions=ast.literal_eval(contents)  
#mongo doesn't accept integer keys - convert them to strings
keys_values = orig_conditions.items()              
conditions = {str(key): value for key, value in keys_values}
for skey,svalue in keys_values:
    skey_values = svalue.items()
    svalue= {str(key): value for key,value in skey_values} 
    conditions[str(skey)]=svalue  

conditionsDB.add_condition("daq/board_"+str(board_id), "qdc", "qdc_range", conditions,None,datetime.datetime.now(), datetime.datetime.max)  
#result = conditionsDB.get_conditions_by_tag("daq/board_"+str(board_id),"qdc_range")
#print ("Conditions of board 0 qdc range:",result)


conditions={}
input= open("daq/thresholds_baselines.dict","r")
contents=input.read()
orig_conditions=ast.literal_eval(contents)  
#mongo doesn't accept integer keys - convert them to strings
keys_values = orig_conditions.items()              
conditions = {str(key): value for key, value in keys_values}
for skey,svalue in keys_values:
    skey_values = svalue.items()
    svalue= {str(key): value for key,value in skey_values} 
    conditions[str(skey)]=svalue   
conditionsDB.add_condition("daq/board_"+str(board_id), "thr_bl_cal", "thresholds_baselines", conditions,None,datetime.datetime.now(), datetime.datetime.max)  


conditions={}
input= open("daq/thresholds.dict","r")
contents=input.read()
orig_conditions=ast.literal_eval(contents)   
#mongo doesn't accept integer keys - convert them to strings
keys_values = orig_conditions.items()              
conditions = {str(key): value for key, value in keys_values}
for skey,svalue in keys_values:
    skey_values = svalue.items()
    svalue= {str(key): value for key,value in skey_values} 
    conditions[str(skey)]=svalue  
conditionsDB.add_condition("daq/board_"+str(board_id), "thresholds", "thresholds", conditions,None,datetime.datetime.now(), datetime.datetime.max)  

conditions={}
input= open("daq/tia-baselines.dict","r")
contents=input.read()
orig_conditions=ast.literal_eval(contents)  
#mongo doesn't accept integer keys - convert them to strings
keys_values = orig_conditions.items()              
conditions = {str(key): value for key, value in keys_values}
for skey,svalue in keys_values:
    skey_values = svalue.items()
    svalue= {str(key): value for key,value in skey_values} 
    conditions[str(skey)]=svalue   
conditionsDB.add_condition("daq/board_"+str(board_id), "tia_bl_cal", "tia-baselines", conditions,None,datetime.datetime.now(), datetime.datetime.max)  

print ("Calibration conditions for board_"+str(board_n)+" added to the database.")
