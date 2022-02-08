#!/usr/bin/env python
import ROOT,os,sys,getopt
import shipRoot_conf
import rootUtils as ut
import boardMappingParser
import numpy as np
h={}

# raw data from Ettore: https://cernbox.cern.ch/index.php/s/Ten7ilKuD3qdnM2 
shipRoot_conf.configure()

chi2Max = 2000.
saturationLimit     = 0.95

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
parser.add_argument("-j", "--json", dest="json", help="read board mapping from EOS", type=int,default=1)
parser.add_argument("-cpp", "--convRawCPP", action='store_true', dest="FairTask_convRaw", help="convert raw data using ConvRawData FairTask", default=False)

withGeoFile = False

options = parser.parse_args()
runNr   = str(options.runNumber).zfill(6)
path      = options.path+'run_'+ runNr+'/'
outFile = "sndsw_raw_"+runNr

local = False

# Fair convRawData task
if options.FairTask_convRaw:
  run = ROOT.FairRunAna()
  ioman = ROOT.FairRootManager.Instance()
  # Set input
  X=''
  server = os.environ['EOSSHIP']
  if not local: X = server
  fIN = ROOT.TFile.Open(X+path+'data.root')
  # Pass raw data file as input object
  ioman.RegisterInputObject("rawData", fIN)

  # Set number of events to process
  inTree = fIN.Get('event')
  if options.nEvents<0:  nEvents = inTree.GetEntries()
  else: nEvents = min(options.nEvents, inTree.GetEntries())
  print('CPP: converting ',nEvents,' events ',' of run',options.runNumber)

  # Pass input parameters to the task - runN, paths, etc.
  ioman.RegisterInputObject('runN', ROOT.TObjString(str(options.runNumber)))
  ioman.RegisterInputObject('path', ROOT.TObjString(path))
  ioman.RegisterInputObject('nEvents', ROOT.TObjString(str(nEvents)))
  ioman.RegisterInputObject('nStart', ROOT.TObjString(str(options.nStart)))
  ioman.RegisterInputObject('debug', ROOT.TObjString(str(options.debug)))
  ioman.RegisterInputObject('stop', ROOT.TObjString(str(options.stop)))
  ioman.RegisterInputObject('heartBeat', ROOT.TObjString(str(options.heartBeat)))
  ioman.RegisterInputObject('withGeoFile', ROOT.TObjString(str(withGeoFile)))
  ioman.RegisterInputObject('isjson', ROOT.TObjString(str(options.json)))

  # Set output
  outfile = ROOT.FairRootFileSink(outFile+'_CPP.root')
  run.SetSink(outfile)

  run.AddTask(ROOT.ConvRawData())
  # Don't use FairRoot's default event header settings
  run.SetEventHeaderPersistence(False)
  run.Init()
  run.Run(options.nStart, nEvents)

else:
  timerCSV = ROOT.TStopwatch()
  timerCSV.Start()
    
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
  key = {'DS':2,'US':1,'Veto':0}
  for system in key:
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
     TofpetMap[key[system]] = {}
     for channel in SiPMmap[system]:
           row = SiPMmap[system][channel]
           TofpetMap[key[system]][row[2]*1000+row[3]] = channel
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
      if float(tmp[9]) < 2: X['chi2Ndof'] = 999999.
      else:                  X['chi2Ndof']=float(tmp[7])/float(tmp[9])

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
      if float(tmp[10]) < 2: X['chi2Ndof'] = 999999.
      else:                  X['chi2Ndof']=float(tmp[8])/float(tmp[10])
    

  if 0>1: # replacing python dict by numpy arrays did not improved memory access, became 10% slower
   # convert to fixed size numpy array:
   boards   = list(qdc_cal.keys())
   boards.sort()
   fes      = list(qdc_cal[boards[0]].keys())
   channels = list(qdc_cal[boards[0]][fes[0]].keys())
   channels.sort()
   tacs     = list(qdc_cal[boards[0]][fes[0]][channels[0]].keys())
   tacs.sort()
   pars     = list(qdc_cal[boards[0]][fes[0]][channels[0]][tacs[0]].keys())
   T        = list(qdc_cal[boards[0]][fes[0]][channels[0]][tacs[0]][0].keys())

   NPqdc_cal = np.zeros( (boards[len(boards)-1]+1,len(fes),len(channels),len(tacs),2,6),dtype=np.double)
   for kb in boards:
    for kf in fes:
       if not kf in qdc_cal[kb]: continue
       for kc in channels:
          if not kc in qdc_cal[kb][kf]: continue
          for kt in tacs:
             if not kt in qdc_cal[kb][kf][kc]: continue
             kp = -1 
             for p in ['a', 'b', 'c', 'd', 'e', 'chi2Ndof']:
                kp+=1
                if not p in qdc_cal[kb][kf][kc][kt]: continue
                NPqdc_cal[kb][kf][kc][kt][0][kp] =  qdc_cal[kb][kf][kc][kt][p]
                if p=='e': continue
                if not 1 in qdc_cal[kb][kf][kc][kt]: continue
                NPqdc_cal[kb][kf][kc][kt][1][kp] =  qdc_cal[kb][kf][kc][kt][0][p]

  timerCSV.Stop()
  print("read CVS", timerCSV.RealTime())                                  

  # following procedure in https://gitlab.cern.ch/scifi-telescope/scifi-rec/-/blob/ettore-tofpet/lib/processors/applycalibration.cpp
  def qdc_calibration(board_id,tofpet_id,channel,tac,v_coarse,v_fine,tf):
      GQDC = 1.0 # or 3.6
      par = qdc_cal[board_id][tofpet_id][channel][tac]
      x = v_coarse - tf
      fqdc = -par['c']*ROOT.TMath.Log(1+ROOT.TMath.Exp( par['a']*(x-par['e'])**2-par['b']*(x-par['e']) )) + par['d']
      value = (v_fine-fqdc)/GQDC
      return value

  def qdc_chi2(board_id,tofpet_id,channel,tac,TDC=0):
      par    = qdc_cal[board_id][tofpet_id][channel][tac]
      parT = qdc_cal[board_id][tofpet_id][channel][tac][TDC]
      return max(par['chi2Ndof'],parT['chi2Ndof'])

  def qdc_sat(board_id,tofpet_id,channel,tac,v_fine):
      par = qdc_cal[board_id][tofpet_id][channel][tac]
      return v_fine/par['d']

  def time_calibration(board_id,tofpet_id,channel,tac,t_coarse,t_fine,TDC=0):
      par = qdc_cal[board_id][tofpet_id][channel][tac][TDC]
      x = t_fine
      ftdc = (-par['b']-ROOT.TMath.Sqrt(par['b']**2-4*par['a']*(par['c']-x)))/(2*par['a'])+par['d']
      timestamp = t_coarse+ftdc
      return timestamp
    
  def comb_calibration(board_id,tofpet_id,channel,tac,v_coarse,v_fine,t_coarse,t_fine,GQDC = 1.0, TDC=0): # max gain QDC = 3.6
      par  = qdc_cal[board_id][tofpet_id][channel][tac]
      parT = par[TDC]
      x    = t_fine
      ftdc = (-parT['b']-ROOT.TMath.Sqrt(parT['b']**2-4*parT['a']*(parT['c']-x)))/(2*parT['a'])+parT['d']
      timestamp = t_coarse + ftdc
      tf = timestamp - t_coarse
      x = v_coarse - tf
      fqdc = -par['c']*ROOT.TMath.Log(1+ROOT.TMath.Exp( par['a']*(x-par['e'])**2-par['b']*(x-par['e']) )) + par['d']
      value = (v_fine-fqdc)/GQDC
      return timestamp,value,max(par['chi2Ndof'],parT['chi2Ndof']),v_fine/par['d']

  def NPqdc_calibration(board_id,tofpet_id,channel,tac,v_coarse,v_fine,tf):
      GQDC = 1.0 # or 3.6
      par = NPqdc_cal[board_id][tofpet_id][channel][tac][0]
      x = v_coarse - tf
      # ['a', 'b', 'c', 'd', 'e', 'chi2Ndof']
      fqdc = -par[2]*ROOT.TMath.Log(1+ROOT.TMath.Exp( par[0]*(x-par[4])**2-par[1]*(x-par[4]) )) + par[3]
      value = (v_fine-fqdc)/GQDC
      return value

  def NPqdc_chi2(board_id,tofpet_id,channel,tac):
      par  = NPqdc_cal[board_id][tofpet_id][channel][tac][0]
      parT = NPqdc_cal[board_id][tofpet_id][channel][tac][1]
      return max(par[5],parT[5])

  def NPqdc_sat(board_id,tofpet_id,channel,tac,v_fine):
      par = NPqdc_cal[board_id][tofpet_id][channel][tac][0]
      return v_fine/par[4]

  def NPtime_calibration(board_id,tofpet_id,channel,tac,t_coarse,t_fine):
      par = NPqdc_cal[board_id][tofpet_id][channel][tac][0]
      x = t_fine
      ftdc = (-par[1]-ROOT.TMath.Sqrt(par[1]**2-4*par[0]*(par[2]-x)))/(2*par[0])+par[3]
      timestamp = t_coarse+ftdc
      return timestamp

  def calibrationReport():
      ut.bookHist(h,'chi2','chi2',1000,0.,10000)
      report = {}
      TDC = 0
      for b in qdc_cal:
           for t in  qdc_cal[b]:
                for c in qdc_cal[b][t]:
                     for tac in qdc_cal[b][t][c]:
                               par    = qdc_cal[b][t][c][tac]
                               if 'chi2Ndof' in par:                             chi2 = par['chi2Ndof']
                               else: chi2=-1
                               parT = qdc_cal[b][t][c][tac][TDC]
                               if 'chi2Ndof' in parT:   chi2T = parT['chi2Ndof']
                               else: chi2T=-1
                               key = tac +10*c + t*10*100 + b*10*100*100
                               if not key in report: report[key]=[chi2,chi2T]
      for key in report:
           rc=h['chi2'].Fill(report[key][0])
           rc=h['chi2'].Fill(report[key][1])
      h['chi2'].Draw()
      return report

  timerBMap = ROOT.TStopwatch()
  timerBMap.Start()
  if options.json:   # read mapping from EOS
     if local:
         with open(path+'board_mapping.json') as f:
             jsonStr = f.read()
     else:
        with client.File() as f:
           server = os.environ['EOSSHIP']
           f.open(server+path+"/board_mapping.json")
           status, jsonStr = f.read()

     # pass the read string to getBoardMapping()
     boardMaps = boardMappingParser.getBoardMapping(jsonStr)

  else: # old internal mapping with IF statements
     boardMaps = boardMappingParser.oldMapping(path)

  timerBMap.Stop()
  print("Time to set board maps ", timerBMap.RealTime())
  
  slots = {0:'A',1:'A',2:'B',3:'B',4:'C',5:'C',6:'D',7:'D'}

  MufiSystem = {}
  for b in boardMaps['MuFilter']:
    board_id = int(b.split('_')[1])
    MufiSystem[board_id]={}
    for x in boardMaps['MuFilter'][b]:
       for slot in slots:
           s = 0
           tmp = boardMaps['MuFilter'][b][x].split('_')[0]
           if tmp=='US': s = 1
           elif tmp=='DS': s = 2
           if slots[slot]==x: MufiSystem[board_id][slot]=s

  offMap={}
                                        # first bar, number of sipm channels / bar and direction
  for s in range(1,3):
     for o in ['Left','Right']: 
        offMap['Veto_'+str(s)+o] =[10000 + (s-1)*1000+ 0,8,2]    # first channel, nSiPMs, nSides, from bottom to top
  for s in range(1,6):
     for o in ['Left','Right']: 
        offMap['US_'+str(s)+o] =[20000 + (s-1)*1000+ 9,-8,2]     # from top to bottom
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
  else: nEvent = min(options.nEvents,f0.event.GetEntries())
  print('converting ',nEvent,' events ',' of run',options.runNumber)

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
  digiMuFilterHitBranch   = sTree.Branch("Digi_MuFilterHits",digiMuFilter,32000,1)
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

  import time
  if not hasattr(time,'time_ns'):
       time.time_ns=time.time
  counters = {'N':0,'event':0,'qdc':0,'tdc':0,'chi2':0,'make':0,'storage':0,'createScifi':0,'createMufi':0}
  def run(nEvent):
   event = f0.event
   for eventNumber in range(options.nStart,nEvent):
     tE = time.time_ns()
     rc = event.GetEvent(eventNumber)
     if eventNumber%options.heartBeat==0:
        tt = time.ctime()
        print('run ',options.runNumber, ' event',eventNumber," ",tt)

     header.SetEventTime(event.timestamp)
     header.SetRunId(options.runNumber)
     if options.debug: print('event:',eventNumber,event.timestamp)
     indexSciFi=0
     digiSciFi.Delete()
     digiSciFiStore = {}
     indexMuFilter=0
     digiMuFilter.Delete()
     digiMuFilterStore = {}
     for board in boards:
        board_id = int(board.split('_')[1])
        scifi = True
        if board in boardMaps['Scifi']:
            station,mat = boardMaps['Scifi'][board]
        elif board in boardMaps['MuFilter']:
            scifi = False
        else: 
             print(board+' not known. Serious error, stop')
             1/0
        bt = boards[board]
        rc  = bt.GetEvent(eventNumber)
        for n in range(bt.n_hits):
               mask = False
               if options.debug:
                    print(scifi,board_id,bt.tofpet_id[n],bt.tofpet_channel[n],bt.tac[n],bt.t_coarse[n],bt.t_fine[n],bt.v_coarse[n],bt.v_fine[n])
               t0 = time.time_ns()
               tofpet_id = bt.tofpet_id[n]
               tofpet_channel = bt.tofpet_channel[n]
               tac = bt.tac[n]
               TDC,QDC,Chi2ndof,satur = comb_calibration(board_id,tofpet_id,tofpet_channel,tac,bt.v_coarse[n],bt.v_fine[n],bt.t_coarse[n],bt.t_fine[n])
               t1 = time.time_ns()
               if Chi2ndof > chi2Max:
                         if QDC>1E20:    QDC = 997.   # checking for inf
                         if QDC != QDC:  QDC = 998.   # checking for nan
                         if QDC>0: QDC = -QDC
                         mask = True
               elif satur  > saturationLimit or QDC>1E20 or QDC != QDC:
                         if QDC>1E20:    QDC = 987.   # checking for inf
                         if options.debug: 
                                print('inf',board_id,bt.tofpet_id[n],bt.tofpet_channel[n],bt.tac[n],bt.v_coarse[n],bt.v_fine[n],TDC-bt.t_coarse[n],eventNumber,Chi2ndof)
                         if QDC != QDC:  QDC = 988.   # checking for nan
                         if options.debug: 
                                 print('nan',board_id,bt.tofpet_id[n],bt.tofpet_channel[n],bt.tac[n],bt.v_coarse[n],bt.v_fine[n],\
                                          TDC-bt.t_coarse[n],TDC,bt.t_coarse[n],eventNumber,Chi2ndof)
                         A = int(min( QDC,1000))
                         B = min(satur,999)/1000.
                         QDC = A+B
                         mask = True
               elif Chi2ndof > chi2Max:
                         if QDC>0: QDC = -QDC
                         mask = True
               if options.debug:
                    print('calibrated: tdc = ',TDC,'  qdc = ',QDC)  # TDC clock cycle = 160 MHz or 6.25ns
               t4 = time.time_ns()
               counters['qdc']+=t1-t0
               counters['make']+=t4-t0

  # in case it is ever needed to read a UChar_t format:
               # Id = int(bin(ord(board.tofpet_id))[2:],2) ch = int(bin(ord(board.tofpet_channel))[2:],2)

               if not scifi:
  # mufi encoding
                  system = MufiSystem[board_id][tofpet_id]
                  key = (tofpet_id%2)*1000 + tofpet_channel
                  tmp = boardMaps['MuFilter'][board][slots[tofpet_id]]
                  if options.debug or not tmp.find('not')<0: print('debug',tmp,system,key,board,tofpet_id,tofpet_id%2,tofpet_channel)
                  sipmChannel = 99
                  if not key in TofpetMap[system]:
                          print('key does not exist',key)
                          print(system, key,board,tofpet_id, TofpetMap[system])
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
                  if mask: digiMuFilterStore[detID].SetMasked(sipm_number)

                  if options.debug:
                      print('create mu hit: ',detID,tmp,system,tofpet_id,offMap[tmp],sipmChannel,nSiPMs,nSides,test)
                      print('                ',detID,sipm_number,QDC,TDC)
                  if test>0 or detID%1000>200 or sipm_number>15:
                      print('what goes wrong?',detID,sipm_number,system,key,board,tofpet_id,tofpet_channel,test)
                  t5 = time.time_ns()
                  counters['createMufi']+=t5-t4

               else:
  # scifi encoding
                  chan = channel(tofpet_id,tofpet_channel,mat)
                  orientation = 1
                  if station[2]=="Y": orientation = 0
                  sipmLocal = (chan - mat*512)
                  sipmID = 1000000*int(station[1]) + 100000*orientation + 10000*mat + 1000*(sipmLocal//128) + chan%128
                  if not sipmID in digiSciFiStore: digiSciFiStore[sipmID] =  ROOT.sndScifiHit(sipmID)
                  digiSciFiStore[sipmID].SetDigi(QDC,TDC)
                  if mask: digiSciFiStore[sipmID].setInvalid()
                  if options.debug:
                      print('create scifi hit: tdc = ',board,sipmID,QDC,TDC)
                      print('tofpet:', tofpet_id,tofpet_channel,mat,chan)
                      print(station[1],station[2],mat,chan,int(chan/128)%4,chan%128)
                  t5 = time.time_ns()
                  counters['createScifi']+=t5-t4

     counters['N']+=1
     t6 = time.time_ns()
     for sipmID in digiSciFiStore:
               if digiSciFi.GetSize() == indexSciFi: digiSciFi.Expand(indexSciFi+100)
               digiSciFi[indexSciFi]=digiSciFiStore[sipmID]
               indexSciFi+=1
     for detID in digiMuFilterStore:
               if digiMuFilter.GetSize() == indexMuFilter: digiMuFilter.Expand(indexMuFilter+100)
               digiMuFilter[indexMuFilter]=digiMuFilterStore[detID]
               indexMuFilter+=1
     counters['storage']+=time.time_ns()-t6
     counters['event']+=time.time_ns()-tE

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
     for el in counters: print(el, counters[el])
   if options.debug:
       print('number of events processed',sTree.GetEntries(),f0.event.GetEntries())
   sTree.Write()

  # https://gitlab.cern.ch/snd-scifi/software/-/wikis/Raw-data-format 
  # tac: 0-3, identifies the Time-To-Analogue converter used for this hit (each channel has four of them and they require separate calibration).
  # t_coarse: Coarse timestamp of the hit, running on a 4 times the LHC clock
  # t_fine: 0-1023, fine timestamp of the hit. It contains the raw value of the charge digitized by the TDC and requires calibration.
  # v_coarse: 0-1023, QDC mode: it represents the number of clock cycles the charge integration lasted.
  # v_fine = 0-1023, QDC mode: represents the charge measured. Requires calibration.

  # check against boardMappingParser
  if options.stop:
     print('check board mapping')
     M = boardMappingParser.oldMapping(path)

     for s in M:
        for board in M[s]:
           print(s,board,M[s][board], boardMaps[s][board],M[s][board]==boardMaps[s][board])

  if not options.stop: 
     run(nEvent)
     f0.Close()
     fSink.Close()
     print("File closed")

  def debugMapping(board,tofpet_id,tofpet_channel):
                  key = (tofpet_id%2)*1000 + tofpet_channel
                  tmp = boardMaps['MuFilter'][board][slots[tofpet_id]]
                  sipmChannel = TofpetMap[system][key]-1
                  nSiPMs =   abs(offMap[tmp][1])
                  nSides =   abs(offMap[tmp][2])
                  direction            = int(offMap[tmp][1]/nSiPMs)
                  detID                   = offMap[tmp][0] + direction*(sipmChannel//(nSiPMs))
                  sipm_number = sipmChannel%(nSiPMs)
                  print(sipmChannel,nSiPMs,nSides,detID,sipm_number)

