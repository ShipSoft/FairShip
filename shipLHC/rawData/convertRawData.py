#!/usr/bin/env python
import ROOT,os,sys,getopt
import global_variables
import shipRoot_conf

# raw data from Ettore: https://cernbox.cern.ch/index.php/s/Ten7ilKuD3qdnM2 
shipRoot_conf.configure()

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-r", "--runNumber", dest="runNumber", help="run number", type=int,required=True)
parser.add_argument("-p", "--path", dest="path", help="path to raw data", default='/mnt/hgfs/VMgate/')
parser.add_argument("-n", "--nEvents", dest="nEvents", help="number of events to process", type=int,default=-1)
parser.add_argument("-d", "--Debug", dest="debug", help="debug", default=False)
parser.add_argument("-s",dest="stop", help="do not start running", default=False)

options = parser.parse_args()
runNr   = str(options.runNumber).zfill(6)
path      = options.path+'run_'+ runNr+'/'
outFile = "sndsw_raw_"+runNr

if path.find('eos')<0 or os.path.isdir(path):
   fqdc_cal = open(path+'qdc_cal.csv')
   Lqdc = fqdc_cal.readlines()
   ftdc_cal = open(path+'tdc_cal.csv')
   Ltdc = ftdc_cal.readlines()
else:
   from XRootD import client
   server = os.environ['EOSSHIP']
   with client.File() as f:
      # "/eos/experiment/sndlhc/testbeam/MuFilter/run_000032/qdc_cal.csv"
      f.open(server+path+"qdc_cal.csv")
      status, Lqdc = f.read()
   with client.File() as f:
      f.open(server+path+"tdc_cal.csv")
      status, Ltdc = f.read()

# calibration dahttps://xrootd.slac.stanford.edu/doc/python/xrootd-python-0.1.0/examples.htmlta
qdc_cal = {}

L = Lqdc
for l in range(1,len(L)):
    tmp = L[l].replace('\n','').split(',')
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
L=Ltdc
for l in range(1,len(L)):
    tmp = L[l].replace('\n','').split(',')
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

def channel(tofpet_id,tofpet_channel,position):
    return (64 * tofpet_id + 63 - tofpet_channel + 512*position) # 512 channels per mat, 1536 channels per plane
                                                                                                                                     # one channel covers all 6 layers of fibres

# reading hits and converting to event information
f0=ROOT.TFile(path+'data.root')
if options.nEvents<0:  nEvent = f0.event.GetEntries()
else: nEvent = options.nEvents

boards = {}
for b in f0.GetListOfKeys():
        name = b.GetName()
        if name.find('board')!=0: continue
        boards[name]=f0.Get(name)

F = ROOT.TFile(outFile+'.root','recreate')
sTree     = ROOT.TTree('rawConv','raw data converted')
ROOT.gDirectory.pwd()
header  = ROOT.FairEventHeader()
eventSND  = sTree.Branch("EventHeader",header,32000,-1)

digiSciFi   = ROOT.TClonesArray("sndScifiHit")
digiSciFiBranch   = sTree.Branch("Digi_SciFiHits",digiSciFi,32000,1)
digiMuFilter   = ROOT.TClonesArray("MuFilterHit")
digiMuFilterHitBranch   = sTree.Branch("Digi_MuFilterHit",digiMuFilter,32000,1)

def run(nEvent):
 event = f0.event
 for n in range(nEvent):
   event.GetEvent(n)
   header.SetEventTime(event.timestamp)
   header.SetRunId(options.runNumber)
   if options.debug: print('event:',n,event.timestamp)
   indexSciFi=0
   digiSciFi.Delete()
   digiSciFiStore = {}
   nStation = -1
   for station in stations:
      nStation += 1
      for position in stations[station]:
         b = stations[station][position]
         board = boards['board_'+str(b)]
         rc  = board.GetEvent(n)
         for n in range(board.n_hits):
             chan = channel(board.tofpet_id[n],board.tofpet_channel[n],position)
             if options.debug:
                  print(chan,board.tofpet_id[n],board.tofpet_channel[n],board.tac[n],board.t_coarse[n],board.t_fine[n],board.v_coarse[n],board.v_fine[n])
             TDC = time_calibration(b,board.tofpet_id[n],board.tofpet_channel[n],board.tac[n],board.t_coarse[n],board.t_fine[n])
             QDC = qdc_calibration(b,board.tofpet_id[n],board.tofpet_channel[n],board.tac[n],board.v_coarse[n],board.v_fine[n],TDC-board.t_coarse[n])
             if options.debug:
                  print('calibrated: tdc = ',TDC,'  qdc = ',QDC)  # TDC clock cycle = 160 MHz or 6.25ns
# for creating hit objects, need to know the mapping between electronic  channel and hit channel.
# in addition for   MuFilter Veto and Up, which SiPM channel. Problem, creating and filling unsorted. Easier for SciFi and downstream
# first check which detector it is Veto/Up/Down -> make MuFilterHit
#                                                                  SciFi                       -> make ScifiHit
#         for the moment, only have SciFi data. For MuFilterHit, need to know nSiPM per side and number of sides
#         ROOT.SndlhcHit(detID,nSiPMs,nSides)

             detID = 100000*nStation + chan
             if not detID in digiSciFiStore: digiSciFiStore[detID] =  ROOT.sndScifiHit(detID)
             digiSciFiStore[detID].SetDigi(QDC,TDC)
             if options.debug:
                  print('create hit: tdc = ',detID)
   for detID in digiSciFiStore:
             if digiSciFi.GetSize() == indexSciFi: digiSciFi.Expand(indexSciFi+100)
             digiSciFi[indexSciFi]=digiSciFiStore[detID]
             indexSciFi+=1
# fill TTree
   sTree.Fill()
 if options.debug:
     print('number of events processed',sTree.GetEntries(),f0.event.GetEntries())
 sTree.Write()

# https://gitlab.cern.ch/snd-scifi/software/-/wikis/Raw-data-format 
# tac: 0-3, identifies the Time-To-Analogue converter used for this hit (each channel has four of them and they require separate calibration).
# t_coarse: Coarse timestamp of the hit, running on a 4 times the LHC clock
# t_fine: 0-1023, fine timestamp of the hit. It contains the raw value of the charge digitized by the TDC and requires calibration.
# v_coarse: 0-1023, QDC mode: it represents the number of clock cycles the charge integration lasted.
# v_fine = 0-1023, QDC mode: represents the charge measured. Requires calibration.

if not options.stop: run(nEvent)

