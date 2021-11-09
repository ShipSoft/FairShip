#!/usr/bin/env python
firstEvent = 0

import resource
def mem_monitor():
 # Getting virtual memory size 
    pid = os.getpid()
    with open(os.path.join("/proc", str(pid), "status")) as f:
        lines = f.readlines()
    _vmsize = [l for l in lines if l.startswith("VmSize")][0]
    vmsize = int(_vmsize.split()[1])
    #Getting physical memory size  
    pmsize = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print("memory: virtuell = %5.2F MB  physical = %5.2F MB"%(vmsize/1.0E3,pmsize/1.0E3))

import ROOT,os,sys,getopt
import global_variables
import shipRoot_conf
import shipunit as u

shipRoot_conf.configure()

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-f", "--inputFile", dest="inputFile", help="single input file", required=True)
parser.add_argument("-g", "--geoFile", dest="geoFile", help="geofile", required=True)
parser.add_argument("-n", "--nEvents", dest="nEvents",  type=int, help="number of events to process", default=100000)
parser.add_argument("-ts", "--thresholdScifi", dest="ts", type=float, help="threshold energy for Scifi [keV]", default=3.5)
parser.add_argument("-tML", "--thresholdMufiL", dest="tml", type=float, help="threshold energy for Mufi large [keV]", default=0.0)
parser.add_argument("-tMS", "--thresholdMufiS", dest="tms", type=float, help="threshold energy for Mufi small [keV]", default=0.0)
parser.add_argument("-d", "--Debug", dest="debug", help="debug", default=False)

options = parser.parse_args()

if options.inputFile.find('/eos')==0:
      x = options.inputFile
      filename = x[x.rfind('/')+1:]
      os.system('xrdcp '+os.environ['EOSSHIP']+options.inputFile+' '+filename)
      options.inputFile = filename
outFile = options.inputFile.replace('.root','_dig.root') 
# outfile should be in local directory
tmp = outFile.split('/')
outFile = tmp[len(tmp)-1]
os.system('cp '+options.inputFile+' '+outFile)

# -----Create geometry----------------------------------------------
import shipLHC_conf as sndDet_conf

if options.geoFile.find('/eos')==0:
       options.geofile = os.environ['EOSSHIP']+options.geoFile
import SndlhcGeo
snd_geo = SndlhcGeo.GeoInterface(options.geoFile)

# set digitization parameters for MuFilter
lsOfGlobals  = ROOT.gROOT.GetListOfGlobals()
scifiDet  = lsOfGlobals.FindObject('Scifi')
mufiDet = lsOfGlobals.FindObject('MuFilter')
mufiDet.SetConfPar("MuFilter/DsAttenuationLength",350 * u.cm)		#  values between 300 cm and 400cm observed for H6 testbeam
mufiDet.SetConfPar("MuFilter/DsTAttenuationLength",700 * u.cm)		# top readout with mirror on bottom
mufiDet.SetConfPar("MuFilter/VandUpAttenuationLength",999 * u.cm)	# no significante attenuation observed for H6 testbeam
mufiDet.SetConfPar("MuFilter/DsSiPMcalibrationS",25.*1000.)			# in MC: 1.65 keV are about 41.2 qdc
mufiDet.SetConfPar("MuFilter/VandUpSiPMcalibration",25.*1000.);
mufiDet.SetConfPar("MuFilter/VandUpSiPMcalibrationS",25.*1000.);
mufiDet.SetConfPar("MuFilter/VandUpPropSpeed",12.5*u.cm/u.nanosecond);
mufiDet.SetConfPar("MuFilter/DsPropSpeed",14.3*u.cm/u.nanosecond);
scifiDet.SetConfPar("Scifi/nphe_min",3.5)   # threshold
scifiDet.SetConfPar("Scifi/nphe_max ",104) # saturation
scifiDet.SetConfPar("Scifi/timeResol",150.*u.picosecond) # time resolution in ps
scifiDet.SetConfPar("MuFilter/timeResol",150.*u.picosecond) # time resolution in ps, first guess

# import digi task
import SndlhcDigi
Sndlhc = SndlhcDigi.SndlhcDigi(outFile)
Sndlhc.setThresholds(options.ts,options.tml,options.tms)

nEvents   = min(Sndlhc.sTree.GetEntries(),options.nEvents)
# main loop
for iEvent in range(firstEvent, nEvents):
    if iEvent % 50000 == 0 or options.debug:
        print('event ', iEvent, nEvents - firstEvent)
    Sndlhc.iEvent = iEvent
    rc = Sndlhc.sTree.GetEvent(iEvent)
    Sndlhc.digitize()
 # memory monitoring
 # mem_monitor()

# end loop over events
Sndlhc.finish()
