#!/usr/bin/env python
import ROOT,os,sys,getopt,subprocess
import Monitor
import Scifi_monitoring

from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("-M", "--online", dest="online", help="online mode",default=False,action='store_true')
parser.add_argument("-r", "--runNumber", dest="runNumber", help="run number", type=int,required=True)
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
options = parser.parse_args()

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

if options.online:
    import ConvRawData
    options.chi2Max = 2000.
    options.saturationLimit  = 0.95
    options.stop = False
    options.withGeoFile = False
    converter = ConvRawData.ConvRawDataPY()
    converter.Init(options)
    options.online = converter

M = Monitor.Monitoring(options,FairTasks)
if options.nEvents < 0 : options.nEvents = M.eventTree.GetEntries()

S = Scifi_monitoring.Scifi_hitMaps()
S.Init(options,M)

for n in range(options.nStart,options.nEvents):
  event = M.GetEvent(n)
  S.ExecuteEvent(M.eventTree)

S.Plot()
