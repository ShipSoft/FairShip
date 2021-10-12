#!/usr/bin/env python
import ROOT,os,sys,getopt
import global_variables
import shipRoot_conf

# raw data from Ettore: https://cernbox.cern.ch/index.php/s/Ten7ilKuD3qdnM2 
shipRoot_conf.configure()

chi2Max = 9999.

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-r", "--runNumber", dest="runNumber", help="run number", type=int,required=True)
parser.add_argument("-p", "--path", dest="path", help="path to raw data", default='/mnt/hgfs/VMgate/')
parser.add_argument("-n", "--nEvents", dest="nEvents", help="number of events to process", type=int,default=-1)
parser.add_argument("-t", "--nStart", dest="nStart", help="first event to process", type=int,default=-1)
parser.add_argument("-d", "--Debug", dest="debug", help="debug", default=False)
parser.add_argument("-s",dest="stop", help="do not start running", default=False)
parser.add_argument("-zM",dest="minMuHits", help="noise suppresion min MuFi hits", default=-1, type=int)
parser.add_argument("-zS",dest="minScifiHits", help="noise suppresion min ScifFi hits", default=-1, type=int)
parser.add_argument("-b", "--heartBeat", dest="heartBeat", help="heart beat", type=int,default=10000)

withGeoFile = False

options = parser.parse_args()
runNr   = str(options.runNumber).zfill(6)
path      = options.path+'run_'+ runNr+'/'
outFile = "sndsw_raw_"+runNr

local = False
if path.find('eos')<0 or os.path.isdir(path):
   local = True
   fqdc_cal = open(path+'/qdc_cal.csv')
   Lqdc = fqdc_cal.readlines()
   ftdc_cal = open(path+'/tdc_cal.csv')
   Ltdc = ftdc_cal.readlines()
else:
   from XRootD import client
   # https://xrootd.slac.stanford.edu/doc/python/xrootd-python-0.1.0/examples.html
   server = os.environ['EOSSHIP']
   with client.File() as f:
      # "/eos/experiment/sndlhc/testbeam/MuFilter/run_000032/qdc_cal.csv"
      f.open(server+path+"/qdc_cal.csv")
      status, L = f.read()
      Lqdc = L.decode().split('\n')
      f.close()
      f.open(server+path+"/tdc_cal.csv")
      status, L = f.read()
      Ltdc = L.decode().split('\n')
      f.close()

# read MuFilter mappings of SiPM channel to tofpet_id and tofpet_channel
import csv
SiPMmap={}
TofpetMap = {}
for system in ['DS','US','Veto']:
   infile = "/eos/experiment/sndlhc/testbeam/MuFilter/SiPM_mappings/"+system+"_SiPM_mapping.csv"
   SiPMmap[system] = {}
   if os.path.isdir("/eos/experiment/sndlhc/testbeam/MuFilter/SiPM_mappings"):
      with open(infile, "r") as f:
          reader = csv.DictReader(f, delimiter=',')
          for i, row in enumerate(reader):
                 SiPMmap[system][int(row['SiPM'])] = [int(row['CN']), int(row['pin']), int(row['TOFPET']), int(row['CHANNEL'])]
   else:
       from XRootD import client
       server = os.environ['EOSSHIP']
       with client.File() as f:
          f.open(server+infile)
          status, tmp = f.read()
       for x in tmp.decode().split('\r\n'):
          if x.find('TOF')>0: continue
          row = x.split(',')
          SiPMmap[system][int(row[0])] = [int(row[1]), int(row[2]), int(row[3]), int(row[4])]
   TofpetMap[system] = {}
   for channel in SiPMmap[system]:
         row = SiPMmap[system][channel]
         TofpetMap[system][row[2]*1000+row[3]] = channel
# calibration data
qdc_cal = {}

L = Lqdc
for l in range(1,len(L)):
    tmp = L[l].replace('\n','').split(',')
    if len(tmp)<10:continue
    board_id = int(tmp[0])
    if not board_id in qdc_cal: qdc_cal[board_id]={}
    fe_id = int(tmp[1])
    if not fe_id in qdc_cal[board_id]: qdc_cal[board_id][fe_id]={}
    channel = int(tmp[2])
    if not channel in qdc_cal[board_id][fe_id]: qdc_cal[board_id][fe_id][channel]={}
    tac = int(tmp[3])
    if not tac in qdc_cal[board_id][fe_id][channel]: qdc_cal[board_id][fe_id][channel][tac]={}
    X = qdc_cal[board_id][fe_id][channel][tac]
    X['a']=float(tmp[4])
    X['b']=float(tmp[5])
    X['c']=float(tmp[6])
    X['d']=float(tmp[8])
    X['e']=float(tmp[10])
    X['chi2']=float(tmp[7])
L=Ltdc
for l in range(1,len(L)):
    tmp = L[l].replace('\n','').split(',')
    if len(tmp)<9:continue
    board_id = int(tmp[0])
    if not board_id in qdc_cal: qdc_cal[board_id]={}
    fe_id = int(tmp[1])
    if not fe_id in qdc_cal[board_id]: qdc_cal[board_id][fe_id]={}
    channel = int(tmp[2])
    if not channel in qdc_cal[board_id][fe_id]: qdc_cal[board_id][fe_id][channel]={}
    tac = int(tmp[3])
    if not tac in qdc_cal[board_id][fe_id][channel]: qdc_cal[board_id][fe_id][channel][tac]={}
    tdc = int(tmp[4])
    if not tdc in qdc_cal[board_id][fe_id][channel][tac]: qdc_cal[board_id][fe_id][channel][tac][tdc]={}
    X = qdc_cal[board_id][fe_id][channel][tac][tdc]
    X['a']=float(tmp[5])
    X['b']=float(tmp[6])
    X['c']=float(tmp[7])
    X['d']=float(tmp[9])

# following procedure in https://gitlab.cern.ch/scifi-telescope/scifi-rec/-/blob/ettore-tofpet/lib/processors/applycalibration.cpp
def qdc_calibration(board_id,tofpet_id,channel,tac,v_coarse,v_fine,tf):
    GQDC = 1.0 # or 3.6
    par = qdc_cal[board_id][tofpet_id][channel][tac]
    x = v_coarse - tf
    fqdc = -par['c']*ROOT.TMath.Log(1+ROOT.TMath.Exp( par['a']*(x-par['e'])**2-par['b']*(x-par['e']) )) + par['d']
    value = (v_fine-fqdc)/GQDC
    return value
def qdc_chi2(board_id,tofpet_id,channel,tac,v_coarse,v_fine,tf):
    par = qdc_cal[board_id][tofpet_id][channel][tac]
    return par['chi2']

def time_calibration(board_id,tofpet_id,channel,tac,t_coarse,t_fine,TDC=0):  #??
    par = qdc_cal[board_id][tofpet_id][channel][tac][TDC]
    x = t_fine
    ftdc = (-par['b']-ROOT.TMath.Sqrt(par['b']**2-4*par['a']*(par['c']-x)))/(2*par['a'])+par['d']
    timestamp = t_coarse+ftdc
    return timestamp

# station mapping for SciFi
stations = {}
stations['M1Y'] =  {0:29, 1:3, 2:30}         # three fibre mats per plane
stations['M1X'] =  {0:11, 1:17, 2:28}
stations['M2Y'] =  {0:16, 1:14, 2:18}
stations['M2X'] =  {0:1, 1:2, 2:25}
stations['M3Y'] =  {0:15, 1:9, 2:5}
stations['M3X'] =  {0:22, 1:27, 2:4}
stations['M4Y'] =  {0:46, 1:23, 2:20}
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
# H6
boardMaps['MuFilter']['board_43'] = {'A':'US_1Left','B':'US_2Left','C':'US_2Right','D':'US_1Right'}
boardMaps['MuFilter']['board_60'] = {'A':'US_3Left','B':'US_4Left','C':'US_4Right','D':'US_3Right'}
boardMaps['MuFilter']['board_41'] = {'A':'US_5Left','B':'DS_1Left','C':'DS_1Right','D':'US_5Right'}
boardMaps['MuFilter']['board_59'] = {'A':'DS_2Left','B':'DS_1Vert','C':'DS_2Vert','D':'DS_2Right'}
slots = {0:'A',1:'A',2:'B',3:'B',4:'C',5:'C',6:'D',7:'D'}

# For the DS, Marco said the SiPM 1 is at the top. 

offMap={}
                                      # first bar, number of sipm channels / bar and direction
for s in range(1,3):
   for o in ['Left','Right']: 
      offMap['VETO_'+str(s)+o] =[10000 + (s-1)*1000+ 9,-8,2]
for s in range(1,6):
   for o in ['Left','Right']: 
      offMap['US_'+str(s)+o] =[20000 + (s-1)*1000+ 9,-8,2]
for s in range(1,5):
   for o in ['Vert']: 
      offMap['DS_'+str(s)+o] =[30000 + (s-1)*1000+ 119, -1,1] # direction not known
   if s>3: continue
   for o in ['Left','Right']: 
      offMap['DS_'+str(s)+o] =[30000 + (s-1)*1000+ 59,-1,2]   # direction not known

def channel(tofpet_id,tofpet_channel,position):
    return (64 * tofpet_id + 63 - tofpet_channel + 512*position) # 512 channels per mat, 1536 channels per plane
                                                                                                                                     # one channel covers all 6 layers of fibres

# reading hits and converting to event information
X=''
if not local: X = server
f0=ROOT.TFile.Open(X+path+'data.root')
if options.nEvents<0:  nEvent = f0.event.GetEntries()
else: nEvent = options.nEvents
print('converting ',nEvent,' events')

boards = {}
for b in f0.GetListOfKeys():
        name = b.GetName()
        if name.find('board')!=0: continue
        boards[name]=f0.Get(name)

fSink = ROOT.FairRootFileSink(outFile+'.root')
sTree     = ROOT.TTree('rawConv','raw data converted')
ROOT.gDirectory.pwd()
header  = ROOT.FairEventHeader()
eventSND  = sTree.Branch("EventHeader",header,32000,-1)

digiSciFi   = ROOT.TClonesArray("sndScifiHit")
digiSciFiBranch   = sTree.Branch("Digi_ScifiHits",digiSciFi,32000,1)
digiMuFilter   = ROOT.TClonesArray("MuFilterHit")
digiMuFilterHitBranch   = sTree.Branch("Digi_MuFilterHit",digiMuFilter,32000,1)
#scifi clusters
if withGeoFile:
  clusScifi   = ROOT.TClonesArray("sndCluster")
  clusScifiBranch    = sTree.Branch("Cluster_Scifi",clusScifi,32000,1)

B = ROOT.TList()
B.SetName('BranchList')
B.Add(ROOT.TObjString('sndScifiHit'))
B.Add(ROOT.TObjString('MuFilterHit'))
B.Add(ROOT.TObjString('FairEventHeader'))
fSink.WriteObject(B,"BranchList", ROOT.TObject.kSingleKey)

errorCounter={}
errorCounter['mult'] = 0
errorCounter['noise'] = 0

import time
def run(nEvent):
 event = f0.event
 for eventNumber in range(options.nStart,nEvent):
   ncreated = 0
   rc = event.GetEvent(eventNumber)
   T = event.timestamp
   if eventNumber%options.heartBeat==0: 
      tt = time.ctime()
      print('run ',options.runNumber, ' event',eventNumber," ",tt)
   # find entry numbers for all boards
   otherEvents={}
   maxHits = 0
   found = False
   for board in boards:
         board_id = int(board.split('_')[1])
         bt = boards[board]
         rc  = bt.GetEvent(eventNumber)
         if bt.n_hits < 1: continue
         if bt.n_hits > maxHits: 
             maxHits = bt.n_hits
             maxBoard = board_id
         t1 = asyn[board_id]
         for boardx in boards:
             boardx_id = int(boardx.split('_')[1])
             t2 = asyn[boardx_id]
             dt = t2 - t1
             newT = T + dt
             if newT<0 or dt==0: continue
             if newT in theMap:
                if options.debug: print("found",eventNumber)
                found = True
                key = theMap[newT]
                if not board_id in otherEvents: 
                   otherEvents[board_id]={}                   
                otherEvents[board_id][boardx_id]=theMap[newT]
# problem if more than one board has links to another event.
   if found and options.debug: print("+++",otherEvents)

   if len(otherEvents)>1:
           print("Houston we have a problem, more than one board match with other events",eventNumber,otherEvents)
           for b in otherEvents:
               rc = boards["board_"+str(b)].GetEvent(eventNumber)
               txt = "mult "+str( boards["board_"+str(b)].n_hits )
               for bx in otherEvents[b]:
                   rc = boards["board_"+str(bx)].GetEvent(otherEvents[b][bx])
                   txt+= " " +str( boards["board_"+str(bx)].n_hits )
               print(txt)     
           errorCounter['mult']+=1
           continue
   if len(otherEvents)==0:
           errorCounter['noise']+=1
           if maxHits>1: 
                otherEvents[maxBoard]={}
                otherEvents[maxBoard][maxBoard] = eventNumber
           else: continue
   else:
           thisBoard = list(otherEvents.keys())[0]
           otherEvents[thisBoard][thisBoard] = eventNumber
   listOfBoards = {}
   if found and options.debug: print("+++",otherEvents)
   for x in otherEvents:
      for b in otherEvents[x]:
         listOfBoards[b]=otherEvents[x][b]
   if found and options.debug: print("---",listOfBoards)

   header.SetEventTime(event.timestamp)
   header.SetRunId(options.runNumber)
   if options.debug: print('event:',eventNumber,event.timestamp)
   indexSciFi=0
   digiSciFi.Delete()
   digiSciFiStore = {}
   indexMuFilter=0
   digiMuFilter.Delete()
   digiMuFilterStore = {}
# special part for synchronizing the MuFilter testbeam data
   for board_id in listOfBoards:
      board = "board_"+str(board_id)
      scifi = True
      if board in boardMaps['Scifi']:
          station,mat = boardMaps['Scifi'][board]
      elif board in boardMaps['MuFilter']:
          scifi = False
      else: 
           print(board+' not known. Serious error, stop')
           1/0
      bt = boards[board]
      rc  = bt.GetEvent(listOfBoards[board_id])
      for n in range(bt.n_hits):
             if options.debug:
                  print(scifi,board_id,bt.tofpet_id[n],bt.tofpet_channel[n],bt.tac[n],bt.t_coarse[n],bt.t_fine[n],bt.v_coarse[n],bt.v_fine[n])
             TDC = time_calibration(board_id,bt.tofpet_id[n],bt.tofpet_channel[n],bt.tac[n],bt.t_coarse[n],bt.t_fine[n])
             QDC = qdc_calibration(board_id,bt.tofpet_id[n],bt.tofpet_channel[n],bt.tac[n],bt.v_coarse[n],bt.v_fine[n],TDC-bt.t_coarse[n])
             if options.debug:
                  print('calibrated: tdc = ',TDC,'  qdc = ',QDC)  # TDC clock cycle = 160 MHz or 6.25ns

# in case it is ever needed to read a UChar_t format:
             # Id = int(bin(ord(board.tofpet_id))[2:],2) ch = int(bin(ord(board.tofpet_channel))[2:],2)

 # for creating hit objects, need to know the mapping between electronic  channel and hit channel.
# in addition for   MuFilter Veto and Up, which SiPM channel. Problem, creating and filling unsorted. Easier for SciFi and downstream
# first check which detector it is Veto/Up/Down -> make MuFilterHit
#                                     tm->WriteObject(input.get());                             SciFi                       -> make ScifiHit
#         for the moment, only have SciFi data. For MuFilterHit, need to know nSiPM per side and number of sides
#         ROOT.SndlhcHit(detID,nSiPMs,nSides)

             if not scifi:
# mufi encoding
                slot = bt.tofpet_id[n]
                tmp = boardMaps['MuFilter'][board][slots[slot]]
                system = tmp.split('_')[0]
                key = (slot%2)*1000 + bt.tofpet_channel[n]
                if options.debug: print(system,key,board,bt.tofpet_id[n],bt.tofpet_id[n]%2,bt.tofpet_channel[n])
                sipmChannel = 99
                if not key in TofpetMap[system]:
                        print('key does not exist',key)
                        print(system, key, TofpetMap[system])
                else:
                       sipmChannel = TofpetMap[system][key]-1
                nSiPMs = abs(offMap[tmp][1])
                nSides =   abs(offMap[tmp][2])
                direction            = int(offMap[tmp][1]/nSiPMs)
                detID                   = offMap[tmp][0] + direction*(sipmChannel//(nSiPMs))
                sipm_number = sipmChannel%(nSiPMs)
                if tmp.find('Right')>0:
                       sipm_number += nSiPMs
                if not detID in digiMuFilterStore:
                        digiMuFilterStore[detID] =  ROOT.MuFilterHit(detID,nSiPMs,nSides)
                test = digiMuFilterStore[detID].GetSignal(sipm_number)
                digiMuFilterStore[detID].SetDigi(QDC,TDC,sipm_number)
                if qdc_chi2(board_id,bt.tofpet_id[n],bt.tofpet_channel[n],bt.tac[n],bt.v_coarse[n],bt.v_fine[n],TDC-bt.t_coarse[n]) > chi2Max:
                        digiMuFilterStore[detID].SetMasked(sipm_number)
                if options.debug:
                    ncreated +=1
                    print('create mu hit: ',detID,tmp,system,slot,offMap[tmp],sipmChannel,nSiPMs,nSides,test,slot)
                    print('                ',detID,sipm_number,QDC,TDC)
                if test>0 or detID%1000>200 or sipm_number>15:
                    print('what goes wrong?',detID,sipm_number,system,key,board,bt.tofpet_id[n],bt.tofpet_channel[n],test)
             else:
# scifi encoding
                chan = channel(bt.tofpet_id[n],bt.tofpet_channel[n],mat)
                orientation = 0
                if station[2]=="Y": orientation = 1
                sipmLocal = (chan - mat*512)
                sipmID = 1000000*int(station[1]) + 100000*orientation + 10000*mat + 1000*(sipmLocal//128) + chan%128
                if not sipmID in digiSciFiStore: digiSciFiStore[sipmID] =  ROOT.sndScifiHit(sipmID)
                digiSciFiStore[sipmID].SetDigi(QDC,TDC)
                if options.debug:
                    print('create scifi hit: tdc = ',board,sipmID,QDC,TDC)
                    print('tofpet:', bt.tofpet_id[n],bt.tofpet_channel[n],mat,chan)
                    print(station[1],station[2],mat,chan,int(chan/128)%4,chan%128)

   for sipmID in digiSciFiStore:
             if digiSciFi.GetSize() == indexSciFi: digiSciFi.Expand(indexSciFi+100)
             digiSciFi[indexSciFi]=digiSciFiStore[sipmID]
             indexSciFi+=1
   for detID in digiMuFilterStore:
             if digiMuFilter.GetSize() == indexMuFilter: digiMuFilter.Expand(indexMuFilter+100)
             digiMuFilter[indexMuFilter]=digiMuFilterStore[detID]
             indexMuFilter+=1
# make simple clustering for scifi, only works with geometry file. Don't think it is a good idea at the moment
   if withGeoFile:
    index = 0
    hitDict = {}
    for k in range(digiSciFi.GetEntries()):
        d = digiSciFi[k]
        if not d.isValid(): continue 
        hitDict[d.GetDetectorID()] = k
        hitList = list(hitDict.keys())
        if len(hitList)>0:
              hitList.sort()
              tmp = [ hitList[0] ]
              cprev = hitList[0]
              ncl = 0
              last = len(hitList)-1
              hitlist = ROOT.std.vector("sndScifiHit*")()
              for i in range(len(hitList)):
                   if i==0 and len(hitList)>1: continue
                   c=hitList[i]
                   if (c-cprev)==1: 
                        tmp.append(c)
                   if (c-cprev)!=1 or c==hitList[last]:
                        first = tmp[0]
                        N = len(tmp)
                        hitlist.clear()
                        for aHit in tmp: 
                                hitlist.push_back( digiSciFi[hitDict[aHit]])
                                print(aHit,hitDict[aHit],digiSciFi[hitDict[aHit]].GetDetectorID())
                        print(hitlist.size())
                        aCluster = ROOT.sndCluster(first,N,hitlist,scifiDet)
                        print("cluster created")
                        if  clusScifi.GetSize() == index: clusScifi.Expand(index+10)
                        clusScifi[index]=aCluster
                        index+=1
                        if c!=hitList[last]:
                             ncl+=1
                             tmp = [c]
                   cprev = c
# fill TTree
   sTree.Fill()
   if options.debug: 
        print('====> number of created hits',ncreated)
 if options.debug:
     print('number of events processed',sTree.GetEntries(),f0.event.GetEntries())
 sTree.Write()

# https://gitlab.cern.ch/snd-scifi/software/-/wikis/Raw-data-format 
# tac: 0-3, identifies the Time-To-Analogue converter used for this hit (each channel has four of them and they require separate calibration).
# t_coarse: Coarse timestamp of the hit, running on a 4 times the LHC clock
# t_fine: 0-1023, fine timestamp of the hit. It contains the raw value of the charge digitized by the TDC and requires calibration.
# v_coarse: 0-1023, QDC mode: it represents the number of clock cycles the charge integration lasted.
# v_fine = 0-1023, QDC mode: represents the charge measured. Requires calibration.

theMap = {}
def getMapEvent2Time():
     k = 0
     for event in f0.event:  
          theMap[event.timestamp]=k
          k+=1
          if k%10000000==0: print('key time map: now at ',k)

# for run 80
asyn = {41:288439008, 43:116829892, 59:740955516, 60:135082280}

def asynInfo(run):
    server = os.environ['EOSSHIP']
    with client.File() as f:
      location = "/eos/experiment/sndlhc/testbeam/MuFilter/Cal_tb2/run_logs/log_"+str(run)+".txt"
      f.open(server+location)
      status, L = f.read()
      A = L.decode().split('\n')
      f.close()
    info = {}
    for x in A:
      X = x.replace('\n','')
      if X=='':continue
      if X.find('2021')==0:
          tag = X
          info[tag]={}
      else:
          if X.find('disc')>0: info[tag]['summary'] = eval(X)
          else: info[tag]['detail'] = eval(X)
    T = list(info.keys())
# correction procedure
    A = {41:{},43:{},59:{},60:{}}
    C = {}
    prev = {41:False,43:False,59:False,60:False}
    errorCounter = 0
    for tag in T:
          C[tag] = {41:{},43:{},59:{},60:{}}
          test = info[tag]['summary']
          lastT = test['last_timestamp']
          if not 'desync_info' in test: continue
          for L in test['desync_info']:
             board = L[0]
             t = L[1][0]
             c = L[1][1]
             C[tag][board][c]=t
    # check that desync is constant over the complete run
          for c in C[tag][41]:
              tref = C[tag][41][c]
              break
          for board in C[tag]:
              if not c in C[tag][board]:
                  print('different trigger counts, problematic',tag,C[tag])
                  errorCounter+=1
              else:
                  if not prev[board] == None:
                         if not C[tag][board][c]-tref == prev[board]:
                              print('desync changed, problematic',tag,prev,C[tag])
                  prev[board] = C[tag][board][c]-tref
    
    for b in C[T[0]]:
        for c in C[T[0]][b]:
            A[b]= C[T[0]][b][c]
    return A

import pickle
def dumpMap():
 fout = open('map'+str(options.runNumber)+'.pkl','wb')
 pickle.dump(theMap,fout)

if not options.stop:
# special for the MuFilter testbeam, need to synchronize the boards

# map time stamp to event number
   test = 'map'+str(options.runNumber)+'.pkl'
   if os.path.exists(test):
     print('map exists')
     fin = open('map'+str(options.runNumber)+'.pkl','rb')
     theMap = pickle.load(fin)
   else: 
     getMapEvent2Time()
     dumpMap()
     asyn = asynInfo(options.runNumber)
   run(nEvent)
   f0.Close()
   fSink.Close()
   print("File closed")


