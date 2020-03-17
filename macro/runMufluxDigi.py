#!/usr/bin/env python

from __future__ import print_function
from __future__ import division
firstEvent = 0
dy         = None

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
import rootUtils as ut
import shipunit as u
import shipRoot_conf

shipRoot_conf.configure()

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-f", "--inputFile", dest="inputFile", help="single input file", required=True)
parser.add_argument("-g", "--geoFile", dest="geoFile", help="geofile", required=True)
parser.add_argument("-n", "--nEvents", dest="nEvents", help="number of events to process", default=100000)
parser.add_argument("-d", "--Debug", dest="debug", help="debug", default=False)

options = parser.parse_args()

outFile = options.inputFile.replace('.root','_dig.root') 
# outfile should be in local directory
tmp = outFile.split('/')
outFile = tmp[len(tmp)-1]
os.system('cp '+options.inputFile+' '+outFile)

fgeo = ROOT.TFile.Open(options.geoFile)
from ShipGeoConfig import ConfigRegistry
from rootpyPickler import Unpickler
#load Shipgeo dictionary
upkl    = Unpickler(fgeo)
ShipGeo = upkl.load('ShipGeo')
 
# -----Create geometry----------------------------------------------
import charmDet_conf
run = ROOT.FairRunSim()
run.SetName("TGeant4")  # Transport engine
run.SetOutputFile(ROOT.TMemFile('output', 'recreate'))  # Output file
run.SetUserConfig("g4Config_basic.C") # geant4 transport not used, only needed for the mag field
rtdb = run.GetRuntimeDb()
modules = charmDet_conf.configure(run,ShipGeo)
fgeo.FAIRGeom

# make global variables
global_variables.debug = options.debug
global_variables.ShipGeo = ShipGeo

global_variables.iEvent = 0

# import reco tasks
import MufluxDigi
SHiP = MufluxDigi.MufluxDigi(outFile)

nEvents   = min(SHiP.sTree.GetEntries(),int(options.nEvents))
# main loop
for global_variables.iEvent in range(firstEvent, nEvents):
    if global_variables.iEvent % 50000 == 0 or global_variables.debug:
        print('event ', global_variables.iEvent, nEvents - firstEvent)
    SHiP.iEvent = global_variables.iEvent
    rc = SHiP.sTree.GetEvent(global_variables.iEvent)
    SHiP.digitize()
 # memory monitoring
 # mem_monitor()

# end loop over events
SHiP.finish()
