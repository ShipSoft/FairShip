#!/usr/bin/env python
from __future__ import print_function
from __future__ import division
from argparse import ArgumentParser

withHists = True
pidProton = False # if true, take truth, if False fake with pion mass
 
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

import ROOT,os,sys
import global_variables
import rootUtils as ut
import shipunit as u
import shipRoot_conf

shipRoot_conf.configure()

parser = ArgumentParser()

parser.add_argument("-f", "--inputFile", dest="inputFile", help="Input file", required=True)
parser.add_argument("-n", "--nEvents",   dest="nEvents",   help="Number of events to reconstruct", required=False,  default=999999,type=int)
parser.add_argument("-g", "--geoFile",   dest="geoFile",   help="ROOT geofile", required=True)
parser.add_argument("--noVertexing",     dest="noVertexing", help="switch off vertexing", required=False, action="store_true")
parser.add_argument("--noStrawSmearing", dest="withNoStrawSmearing", help="no smearing of distance to wire, default on", required=False, action="store_true")
parser.add_argument("--withT0",          dest="withT0", help="simulate arbitrary T0 and correct for it", required=False, action="store_true")
parser.add_argument("--ecalDebugDraw",   dest="EcalDebugDraw", help="switch in debog for ECAL", required=False, action="store_true")
parser.add_argument("--saveDisk",        dest="saveDisk", help="if set, will remove input file, only rec file kept", required=False, action="store_true")
parser.add_argument("-i", "--firstEvent",dest="firstEvent",  help="First event of input file to use", required=False,  default=0,type=int)
parser.add_argument("--realPR",          dest="realPR",  help="Option for pattern recognition without MC truth. \n\
           FH                        : Hough transform.\n\
           AR                        : Artificial retina.\n\
      TemplateMatching               : Tracks are searched for based on the template: track seed + hits within a window around the seed."\
                                     , required=False, choices=['FH','AR','TemplateMatching'],  default='')
parser.add_argument("-dy",               dest="dy", help="Max height of tank", required=False, default=None,type=int)
parser.add_argument("--Debug",           dest="Debug", help="Switch on debugging", required=False, action="store_true")

options = parser.parse_args()
vertexing = not options.noVertexing
 
if options.EcalDebugDraw: ROOT.gSystem.Load("libASImage")

# need to figure out which geometry was used, only needed if no geo file
if not options.dy:
  # try to extract from input file name
  tmp = options.inputFile.split('.')
  try:
    dy = float( tmp[1]+'.'+tmp[2] )
  except:
    dy = None

print('configured to process ', options.nEvents, ' events from ', options.inputFile,
      ' starting with event ', options.firstEvent, ' with option Yheight = ' ,dy,
      ' with vertexing', vertexing, ' and real pattern reco ', options.realPR)
if not options.inputFile.find('_rec.root') < 0: 
  outFile   = options.inputFile
  options.inputFile = outFile.replace('_rec.root','.root') 
else:
  outFile = options.inputFile.replace('.root','_rec.root') 
# outfile should be in local directory
  tmp = outFile.split('/')
  outFile = tmp[len(tmp)-1]
  if options.inputFile[:7]=="root://" : os.system('xrdcp '+options.inputFile+' '+outFile)
  elif options.saveDisk: os.system('mv '+options.inputFile+' '+outFile)
  else :       os.system('cp '+options.inputFile+' '+outFile)

if not options.geoFile:
 tmp = options.inputFile.replace('ship.','geofile_full.')
 options.geoFile = tmp.replace('_rec','')

fgeo = ROOT.TFile.Open(options.geoFile)
geoMat =  ROOT.genfit.TGeoMaterialInterface()  # if only called in ShipDigiReco -> crash, reason unknown

from ShipGeoConfig import ConfigRegistry
from rootpyPickler import Unpickler
#load Shipgeo dictionary
upkl    = Unpickler(fgeo)
ShipGeo = upkl.load('ShipGeo')
ecalGeoFile = ShipGeo.ecal.File

h={}
log={}
if withHists:
 ut.bookHist(h,'distu','distance to wire',100,0.,5.)
 ut.bookHist(h,'distv','distance to wire',100,0.,5.)
 ut.bookHist(h,'disty','distance to wire',100,0.,5.)
 ut.bookHist(h,'nmeas','nr measuerements',100,0.,50.)
 ut.bookHist(h,'chi2','Chi2/DOF',100,0.,20.)

import shipDet_conf
run = ROOT.FairRunSim()
run.SetName("TGeant4")  # Transport engine
run.SetOutputFile(ROOT.TMemFile('output', 'recreate'))  # Output file
run.SetUserConfig("g4Config_basic.C") # geant4 transport not used, only needed for creating VMC field
rtdb = run.GetRuntimeDb()
# -----Create geometry----------------------------------------------
modules = shipDet_conf.configure(run,ShipGeo)
# run.Init()
fgeo.FAIRGeom
import geomGeant4

if hasattr(ShipGeo.Bfield,"fieldMap"):
  fieldMaker = geomGeant4.addVMCFields(ShipGeo, '', True,withVirtualMC = False)

# make global variables
global_variables.debug = options.Debug
global_variables.fieldMaker = fieldMaker
global_variables.pidProton = pidProton
global_variables.withT0 = options.withT0
global_variables.realPR = options.realPR
global_variables.vertexing = vertexing
global_variables.ecalGeoFile = ecalGeoFile
global_variables.ShipGeo = ShipGeo
global_variables.modules = modules
global_variables.EcalDebugDraw = options.EcalDebugDraw
global_variables.withNoStrawSmearing = options.withNoStrawSmearing
global_variables.h = h
global_variables.log = log
global_variables.iEvent = 0

# import reco tasks
import shipDigiReco

SHiP = shipDigiReco.ShipDigiReco(outFile,fgeo)
options.nEvents   = min(SHiP.sTree.GetEntries(),options.nEvents)
# main loop
for global_variables.iEvent in range(options.firstEvent, options.nEvents):
    if global_variables.iEvent % 1000 == 0 or global_variables.debug:
        print('event ', global_variables.iEvent)
    rc = SHiP.sTree.GetEvent(global_variables.iEvent)
    SHiP.digitize()
    SHiP.reconstruct()
 # memory monitoring
 # mem_monitor()
# end loop over events
SHiP.finish()
