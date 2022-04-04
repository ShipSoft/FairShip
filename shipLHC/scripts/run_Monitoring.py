#!/usr/bin/env python
import ROOT,os,sys,getopt,subprocess,atexit,time
import Monitor
import Scifi_monitoring
import Mufi_monitoring
import EventDisplay_Task

def pyExit():
    if options.online:
       print("Make suicide until solution found for freezing")
       os.system('kill '+str(os.getpid()))
atexit.register(pyExit)

from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("-A", "--auto", dest="auto", help="run in auto mode online monitoring",default=False,action='store_true')
parser.add_argument("-M", "--online", dest="online", help="online mode",default=False,action='store_true')
parser.add_argument("--server", dest="server", help="xrootd server",default=os.environ["EOSSHIP"])
parser.add_argument("-r", "--runNumber", dest="runNumber", help="run number", type=int,default=-1)
parser.add_argument("-p", "--path", dest="path", help="run number",required=False,default="")
parser.add_argument("-P", "--partition", dest="partition", help="partition of data", type=int,required=False,default=-1)
parser.add_argument("-d", "--Debug", dest="debug", help="debug", default=False)
parser.add_argument("-cpp", "--convRawCPP", action='store_true', dest="FairTask_convRaw", help="convert raw data using ConvRawData FairTask", default=False)
parser.add_argument( "--withCalibration", action='store_true', dest="makeCalibration", help="make QDC and TDC calibration, not taking from raw data", default=False)

parser.add_argument("-f", "--inputFile", dest="fname", help="file name for MC", type=str,default=None,required=False)
parser.add_argument("-g", "--geoFile", dest="geoFile", help="geofile", required=True)
parser.add_argument("-b", "--heartBeat", dest="heartBeat", help="heart beat", default=10000,type=int)
parser.add_argument("-c", "--command", dest="command", help="command", default="")
parser.add_argument("-n", "--nEvents", dest="nEvents", help="number of events", default=-1,type=int)
parser.add_argument("-s", "--nStart", dest="nStart", help="first event", default=0,type=int)
parser.add_argument("-t", "--trackType", dest="trackType", help="DS or Scifi", default="DS")

parser.add_argument("--ScifiNbinsRes", dest="ScifiNbinsRes", default=100)
parser.add_argument("--Scifixmin", dest="Scifixmin", default=-2000.)
parser.add_argument("--ScifialignPar", dest="ScifialignPar", default=False)

parser.add_argument("--goodEvents", dest="goodEvents", action='store_true',default=False)
parser.add_argument("--withTrack", dest="withTrack", action='store_true',default=False)
parser.add_argument("--nTracks", dest="nTracks",default=0,type=int)
parser.add_argument("--save", dest="save", action='store_true',default=False)
options = parser.parse_args()

options.dashboard = "currently_processed_file.txt"

def currentRun():
      with client.File() as f:
            f.open(options.server+options.path+options.dashboard)
            status, L = f.read()
            Lcrun = L.decode().split('\n')
            f.close()
         for l in Lcrun:
            if not l.find('/home/snd/snd/') < 0:
                 tmp = l.split('/')
                 currentRun = tmp[len(tmp)-2]
                 currentPart = tmp[len(tmp)-1]
                 break
      return currentRun,currentPart

('run_000045', 'data_0000.root')


if options.auto:
   options.online = True
   from XRootD import client
# search for current run
   if options.runNumber < 0:
        currentRun,currentPart =  currentRun()
        options.runNumber = int(currentRun.split('_')[1])
        options.partition = int(currentPart.split('_')[1].split('.')[0])
else:
   if options.runNumber < 0:
       print("run number required for non-auto mode")
       exit()

# prepare tasks:
FairTasks = []
houghTransform = False # under construction, not yet tested
if houghTransform:
   muon_reco_task = SndlhcMuonReco.MuonReco()
   muon_reco_task.SetName("houghTransform")
   FairTasks.append(muon_reco_task)
else:
   import SndlhcTracking
   trackTask = SndlhcTracking.Tracking() 
   trackTask.SetName('simpleTracking')
   FairTasks.append(trackTask)

M = Monitor.Monitoring(options,FairTasks)
if options.nEvents < 0 : 
    if options.online: options.nEvents = M.converter.fiN.event.GetEntries()
    else:    options.nEvents = M.eventTree.GetEntries()

monitorTasks = {}
monitorTasks['Scifi_hitMaps']   = Scifi_monitoring.Scifi_hitMaps()
monitorTasks['Mufi_hitMaps']   = Mufi_monitoring.Mufi_hitMaps()
monitorTasks['Scifi_residuals'] = Scifi_monitoring.Scifi_residuals()   # time consuming
monitorTasks['EventDisplay']   = EventDisplay_Task.twod()

for m in monitorTasks:
    monitorTasks[m].Init(options,M)

if not options.auto:   # default online/offline mode
   for n in range(options.nStart,options.nEvents):
     event = M.GetEvent(n)
     trackTask.event = event    #  this needs to be fixed, not a good solution
     for m in monitorTasks:
        monitorTasks[m].ExecuteEvent(M.eventTree)

   if options.nEvents>0:
       for m in monitorTasks:
          monitorTasks[m].Plot()

else: 
   """ auto mode
       check for open data file on the online machine
       analyze N events 
       re-open file and check for new events, 
       if none available, 
         check every 5 seconds: if no new file re-open again
         if new file, finish run, publish histograms, and restart with new file
   """

   dN = 10
   Nupdate = 10000
   N0 = 0
   lastEvent = M.converter.fiN.event.GetEntries()
   lastFile = M.converter.fiN.GetName()
   tmp = lastFile.split('/')
   lastRun  = tmp[len(tmp)-2]
   lastPart = tmp[len(tmp)-1]
   nLast = options.nEvents
   nStart = nLast-dN
   while 1>0:
      for n in range(nStart,nLast):
        event = M.GetEvent(n)
        N0+=1
        trackTask.event = event
        for m in monitorTasks:
           monitorTasks[m].ExecuteEvent(M.eventTree)
# update plots
        if N0%Nupdate==0:
           for m in monitorTasks:
               monitorTasks[m].Plot()

      M.converter.fiN = ROOT.TFile.Open(lastFile)
      newEntries = M.converter.fiN.event.GetEntries()
      if newEntries>lastEvent:
         nStart = max(nLast,newEntries-dN)
         nLast = newEntries
         continue
      else:  
      # check if file has changed
         currentRun,currentPart =  currentRun()
         if not currentRun == lastRun:
            for m in monitorTasks:
               monitorTasks[m].Plot()
            exit()  # should reinitialize everything with new run number
         if not currentPart == lastPart:
            lastPart = currentPart
            lastFile = options.server+ l
            M.converter.fiN = ROOT.TFile.Open(lastFile)
         else:
            time.sleep(5) # sleep 5 secondsile and check for new events
            print('do not know what to do')
            1/0
"""
       if none available, 
         check every 5 seconds: if no new file re-open again
         if new file, finish run, publish histograms, and restart with new file
"""



