import os
import boardMappingParser
from XRootD import client
import csv

class reversChannelMapping:
 " detector ID and SiPM channel nr to online board/tofpet_id/tofpet_channel "
 def Init(self,path):
    with client.File() as f:
        server = os.environ['EOSSHIP']
        f.open(server+path+"/board_mapping.json")
        status, jsonStr = f.read()
    self.boardMaps = boardMappingParser.getBoardMapping(jsonStr)
    self.slots = {0:'A',1:'A',2:'B',3:'B',4:'C',5:'C',6:'D',7:'D'}
    with client.File() as f:
        server = os.environ['EOSSHIP']
        f.open(server+path+"/board_mapping.json")
        status, jsonStr = f.read()
    self.MufiSystem = {}
    for b in self.boardMaps['MuFilter']:
        board_id = int(b.split('_')[1])
        self.MufiSystem[board_id]={}
        for x in self.boardMaps['MuFilter'][b]:
           for slot in self.slots:
              s = 0
              tmp = self.boardMaps['MuFilter'][b][x].split('_')[0]
              if tmp=='US': s = 1
              elif tmp=='DS': s = 2
              if self.slots[slot]==x: self.MufiSystem[board_id][slot]=s
    self.SiPMmap={}
    self.names = {'DS':2,'US':1,'Veto':0}
    self.sdict = {3:'DS',2:'US',1:'Veto'}
    for system in self.names:
      sndswPath = os.environ['SNDSW_ROOT']
      infile = sndswPath+"/geometry/"+system+"_SiPM_mapping.csv"
      self.SiPMmap[system] = {}
      if os.path.isdir(sndswPath+"/geometry"):
        with open(infile, "r") as f:
            reader = csv.DictReader(f, delimiter=',')
            for i, row in enumerate(reader):
                   self.SiPMmap[system][int(row['SiPM'])] = [int(row['CN']), int(row['pin']), int(row['TOFPET']), int(row['CHANNEL'])]
      self.offMap={}
      for s in range(1,3):
        for o in ['Left','Right']: 
           self.offMap['Veto_'+str(s)+o] =[10000 + (s-1)*1000+ 0,8,2]    # first channel, nSiPMs, nSides, from bottom to top
      for s in range(1,6):
          for o in ['Left','Right']: 
            self.offMap['US_'+str(s)+o] =[20000 + (s-1)*1000+ 9,-8,2]     # from top to bottom
      for s in range(1,5):
         for o in ['Vert']: 
            self.offMap['DS_'+str(s)+o] =[30000 + (s-1)*1000+ 119, -1,1] 
         if s>3: continue
         for o in ['Left','Right']: 
            self.offMap['DS_'+str(s)+o] =[30000 + (s-1)*1000+ 59,-1,2]   
    self.revBoardMaps={}
    self.revBoardMaps['MuFilter'] = {}
    for board in self.boardMaps['MuFilter']:
        for slot in self.boardMaps['MuFilter'][board]:
           key = self.boardMaps['MuFilter'][board][slot]
           self.revBoardMaps['MuFilter'][key]=[board,slot]
#
 def daqChannel(self,aHit,channel):
      if type(aHit).__name__ == 'int':  fDetectorID  = aHit
      else:                                     fDetectorID  = aHit.GetDetectorID()
      subsystem    = fDetectorID//10000
      plane        = fDetectorID//1000 - 10*subsystem
      bar_number   = fDetectorID%1000
      nSiPMs = aHit.GetnSiPMs()
      nSides = aHit.GetnSides()
      if subsystem==3 and bar_number>59: side="Vert"
      elif channel <  nSiPMs: side = 'Left'
      else: side = 'Right'
      tag = self.sdict[subsystem]+'_'+str(plane+1)+side
      direction = int(self.offMap[tag][1]/nSiPMs)
      sipmChannel = int( (fDetectorID - self.offMap[tag][0])/direction * nSiPMs)
      sipmChannel+=channel%(nSiPMs) + 1
      board = self.revBoardMaps['MuFilter'][tag]
      result = self.SiPMmap[self.sdict[subsystem]][sipmChannel]
      return {"sipmChannel":sipmChannel,"board":board,"channel":result[3],"tofpet":result[2],"pin":result[1],"CN":result[0]}

 def test(nSiPMs = 8,subsystem = 2,plane = 3):
    for side in ['Left','Right']:
      for bar_number in range(10):
         fDetectorID = 20000+plane*1000+bar_number
         tag = tself.sdict[subsystem]+'_'+str(plane+1)+side
         for n in range(nSiPMs):
            direction = int(tself.offMap[tag][1]/nSiPMs)
            sipmChannel = int( (fDetectorID - tself.offMap[tag][0])/direction * nSiPMs) + n + 1
            result = tself.SiPMmap[tself.sdict[subsystem]][sipmChannel]
            print(fDetectorID,n, " : ",sipmChannel,result)

