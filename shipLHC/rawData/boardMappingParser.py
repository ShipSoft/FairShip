#!/usr/bin/env python3

import json

def getBoardMapping(jsonString):
  boardMapsNew = {'Scifi': {}, 'MuFilter': {}}

  # converts the JSON string into a dictionary
  j = json.loads(jsonString)

  # the mapping is structured as: {<subsystem>: {<plane>: {<settings>...}, ...}, ...}
  # subsystem is veto, scifi, us, ds
  # plane depends on subsystem (e.g. '1x', '1y'... for Scifi)
  # settings depends on sybsystem as well
  # more info here: https://gitlab.cern.ch/snd-scifi/software/-/wikis/Board-Mapping

  # loops over the subsystems
  for subsys, planes in j.items():
    # each subsystem is treated separately
    if subsys == 'scifi':
      # loops over the planes in the subsystem
      for plane, conf in planes.items():
        # sanity check that the settings are correct
        if conf['class'] != 'multiboard' or conf['type'] != 'snd_scifi':
          raise RuntimeError('wrong class/type: ' + conf['class'] + '/' + conf['type'])
        
        # loops over the boards (for SciFi)
        for i, bid in enumerate(conf['boards']):
          boardMapsNew['Scifi'][f'board_{bid}'] = [f'M{plane}'.upper(), i]
    
    elif subsys == 'veto':
      for plane, conf in planes.items():
        if conf['class'] != 'multislot' or conf['type'] != 'snd_veto':
          raise RuntimeError('wrong class/type: ' + conf['class'] + '/' + conf['type'])

        # adds the 'board_XX' entry in the dictionary of not already there
        bString = f'board_{conf["board"]}'
        if bString not in boardMapsNew['MuFilter']:
          boardMapsNew['MuFilter'][bString] = {}
        
        # loops over the slots (the first is always left, the second always right)
        for i in range(2):
          boardMapsNew['MuFilter'][bString][conf['slots'][i]] = f'Veto_{plane}{"Left" if i == 0 else "Right"}'

    elif subsys == 'us':
      for plane, conf in planes.items():
        if conf['class'] != 'multislot' or conf['type'] != 'snd_us':
          raise RuntimeError('wrong class/type: ' + conf['class'] + '/' + conf['type'])

        bString = f'board_{conf["board"]}'
        if bString not in boardMapsNew['MuFilter']:
          boardMapsNew['MuFilter'][bString] = {}
        
        for i in range(2):
          boardMapsNew['MuFilter'][bString][conf['slots'][i]] = f'US_{plane}{"Left" if i == 0 else "Right"}'
    
    elif subsys == 'ds':
      for plane, conf in planes.items():
        if conf['class'] != 'multislot' or (conf['type'] != 'snd_dsh' and conf['type'] != 'snd_dsv'):
          raise RuntimeError('wrong class/type: ' + conf['class'] + '/' + conf['type'])

        bString = f'board_{conf["board"]}'
        if bString not in boardMapsNew['MuFilter']:
          boardMapsNew['MuFilter'][bString] = {}
        
        # for DS we have the additional complication of vertival planes, but they are two different plane types (snd_dsh and snd_dsv)
        if conf['type'] == 'snd_dsh':
          for i in range(2):
            boardMapsNew['MuFilter'][bString][conf['slots'][i]] = f'DS_{plane[0]}{"Left" if i == 0 else "Right"}'
        else:
          # vertical planes use one slot only
          boardMapsNew['MuFilter'][bString][conf['slots'][0]] = f'DS_{plane[0]}Vert'
    
    else:
      raise RuntimeError('unknown subsystem: ' + subsys)

  return boardMapsNew

def oldMapping(path):
# station mapping for SciFi
   stations = {}
   stations['M1Y'] =  {0:29, 1:3, 2:30}         # three fibre mats per plane
   stations['M1X'] =  {0:11, 1:17, 2:28}
   stations['M2Y'] =  {0:16, 1:14, 2:18}
   stations['M2X'] =  {0:1, 1:2, 2:25}
   stations['M3Y'] =  {0:15, 1:9, 2:5}
   stations['M3X'] =  {0:22, 1:27, 2:4}
   if path.find("commissioning-h6")>0: stations['M4Y'] =  {0:46, 1:40, 2:20}  # board 40 replaces 23
   else:                                                                   stations['M4Y'] =  {0:46, 1:23, 2:20}
   stations['M4X'] =  {0:8, 1:50, 2:49}
   stations['M5Y'] =  {0:19, 1:13, 2:36}
   stations['M5X'] =  {0:21, 1:10, 2:6}

# board mapping for Scifi
   boardMaps = {}
   boardMaps['Scifi'] = {}
   for station in stations:
      for mat in stations[station]:
         board = 'board_'+str(stations[station][mat])
         boardMaps['Scifi'][board]=[station,mat]

   boardMaps['MuFilter'] = {}
# hopefully final mapping of TI18
   boardMaps['MuFilter']['board_52'] = {'B':'Veto_1Left','C':'Veto_1Right','A':'Veto_2Left','D':'Veto_2Right'}
   boardMaps['MuFilter']['board_43'] = {'D':'US_1Left','A':'US_1Right','C':'US_2Left','B':'US_2Right'}
   boardMaps['MuFilter']['board_60'] = {'D':'US_3Left','A':'US_3Right','C':'US_4Left','B':'US_4Right'}
   boardMaps['MuFilter']['board_41'] = {'D':'US_5Left','A':'US_5Right','C':'DS_1Left','B':'DS_1Right'}
   boardMaps['MuFilter']['board_42'] = {'D':'DS_2Left','A':'DS_2Right','B':'DS_1Vert','C':'DS_2Vert'}
   boardMaps['MuFilter']['board_55'] = {'D':'DS_3Left','A':'DS_3Right','B':'DS_3Vert','C':'DS_4Vert'}

   if path.find("commissioning-h6")>0 or  path.find("TB_data_commissioning")>0 :
# H6 / H8
      boardMaps['MuFilter']['board_43'] = {'A':'US_1Left','B':'US_2Left','C':'US_2Right','D':'US_1Right'}
      boardMaps['MuFilter']['board_60'] = {'A':'US_3Left','B':'US_4Left','C':'US_4Right','D':'US_3Right'}
      boardMaps['MuFilter']['board_41'] = {'A':'US_5Left','B':'DS_1Left','C':'DS_1Right','D':'US_5Right'}
      if path.find("commissioning-h6")>0: boardMaps['MuFilter']['board_59'] = {'A':'DS_2Right','B':'DS_2Vert','C':'DS_1Vert','D':'DS_2Left'}
      else:                                                boardMaps['MuFilter']['board_59'] = {'A':'DS_2Left','B':'DS_1Vert','C':'DS_2Vert','D':'DS_2Right'}
      boardMaps['MuFilter']['board_42'] = {'A':'DS_3Left','B':'DS_4Vert','C':'DS_3Vert','D':'DS_3Right'}
      boardMaps['MuFilter']['board_52'] = {'A':'Veto_2Left','B':'Veto_1Left','C':'Veto_1Right','D':'Veto_2Right'}
   if path.find("data_commissioning_dune")>0:    # does not work
      boardMaps['MuFilter']['board_43'] = {'A':'US_1Left','B':'US_2Left','C':'US_2Right','D':'US_1Right'}
      boardMaps['MuFilter']['board_60'] = {'A':'US_3Left','B':'US_4Left','C':'US_4Right','D':'US_3Right'}
      boardMaps['MuFilter']['board_41'] = {'A':'US_5Left','B':'DS_1Left','C':'DS_1Right','D':'US_5Right'}
      boardMaps['MuFilter']['board_59'] = {'A':'DS_2Left','B':'DS_1Vert','C':'DS_2Vert','D':'DS_2Right'}
      boardMaps['MuFilter']['board_42'] = {'A':'DS_3Left','B':'DS_3Vert','C':'notconnected','D':'notconnected'}
      boardMaps['MuFilter']['board_52'] = {'A':'DS_3Right','B':'notconnected','C':'notconnected','D':'notconnected'}
   return boardMaps

from XRootD import client
import os
server = os.environ['EOSSHIP']
path    = "/eos/experiment/sndlhc/testbeam/commissioning-h6/run_000010/"

def main():
  # open the file as a normal text file and read it
  with client.File() as f:
      f.open(server+path+"/board_mapping.json")
      status, jsonStr = f.read()

  # pass the read string to getBoardMapping()
  return getBoardMapping(jsonStr)

  
if __name__ == '__main__':
  main()
