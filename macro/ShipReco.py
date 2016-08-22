#!/usr/bin/env python
inputFile = 'ship.Pythia8-TGeant4.root'
geoFile   = None
debug = False
EcalDebugDraw = False
withNoStrawSmearing = None # True   for debugging purposes
nEvents    = 999999
firstEvent = 0
withHists = True
vertexing = True
dy  = None
saveDisk  = False # remove input file
pidProton = False # if true, take truth, if False fake with pion mass
realPR = ''

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
    print "memory: virtuell = %5.2F MB  physical = %5.2F MB"%(vmsize/1.0E3,pmsize/1.0E3)

import ROOT,os,sys,getopt
import __builtin__ as builtin
import rootUtils as ut
import shipunit as u
import shipRoot_conf

shipRoot_conf.configure()

try:
        opts, args = getopt.getopt(sys.argv[1:], "o:D:FHPu:n:f:g:c:hqv:sl:A:Y:i:",\
           ["ecalDebugDraw","inputFile=","geoFile=","nEvents=","noStrawSmearing","noVertexing","saveDisk","realPR"])
except getopt.GetoptError:
        # print help information and exit:
        print ' enter --inputFile=  --geoFile= --nEvents=  --firstEvent=,' 
        print ' noStrawSmearing: no smearing of distance to wire, default on' 
        print ' outputfile will have same name with _rec added'   
        sys.exit()
for o, a in opts:
        if o in ("noVertexing"):
            vertexing = False
        if o in ("noStrawSmearing"):
            withNoStrawSmearing = True
        if o in ("-f", "--inputFile"):
            inputFile = a
        if o in ("-g", "--geoFile"):
            geoFile = a
        if o in ("-n", "--nEvents="):
            nEvents = int(a)
        if o in ("-Y"): 
            dy = float(a)
        if o in ("--ecalDebugDraw"):
            EcalDebugDraw = True
        if o in ("--saveDisk"):
            saveDisk = True
	if o in ("--realPR"):
            realPR = "_PR"
if EcalDebugDraw: ROOT.gSystem.Load("libASImage")

# need to figure out which geometry was used
if not dy:
  # try to extract from input file name
  tmp = inputFile.split('.')
  try:
    dy = float( tmp[1]+'.'+tmp[2] )
  except:
    dy = None
print 'configured to process ',nEvents,' events from ' ,inputFile, \
      ' starting with event ',firstEvent, ' with option Yheight = ',dy,' with vertexing',vertexing,' and real pattern reco',realPR=="_PR"
if not inputFile.find('_rec.root') < 0: 
  outFile   = inputFile
  inputFile = outFile.replace('_rec.root','.root') 
else:
  outFile = inputFile.replace('.root','_rec.root') 
# outfile should be in local directory
  tmp = outFile.split('/')
  outFile = tmp[len(tmp)-1]
  if saveDisk: os.system('mv '+inputFile+' '+outFile)
  else :       os.system('cp '+inputFile+' '+outFile)

if not geoFile:
 tmp = inputFile.replace('ship.','geofile_full.')
 geoFile = tmp.replace('_rec','')
# try to figure out which ecal geo to load
fgeo = ROOT.TFile(geoFile)
sGeo = fgeo.FAIRGeom

from ShipGeoConfig import ConfigRegistry
from rootpyPickler import Unpickler

if not fgeo.FindKey('ShipGeo'):
 # old geofile, missing Shipgeo dictionary
 if sGeo.GetVolume('EcalModule3') :  ecalGeoFile = "ecal_ellipse6x12m2.geo"
 else: ecalGeoFile = "ecal_ellipse5x10m2.geo" 
 print 'found ecal geo for ',ecalGeoFile
 if dy: 
  ShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", Yheight = dy, EcalGeoFile = ecalGeoFile)
 else:
  ShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", EcalGeoFile = ecalGeoFile) 
else: 
 # new geofile, load Shipgeo dictionary
  upkl    = Unpickler(fgeo)
  ShipGeo = upkl.load('ShipGeo')
  ecalGeoFile = ShipGeo.ecal.File

ps = 0
if sGeo.GetVolume('PreshowerDetector'):ps = 1

h={}
log={}
if withHists:
 ut.bookHist(h,'distu','distance to wire',100,0.,5.)
 ut.bookHist(h,'distv','distance to wire',100,0.,5.)
 ut.bookHist(h,'disty','distance to wire',100,0.,5.)
 ut.bookHist(h,'nmeas','nr measuerements',100,0.,50.)
 ut.bookHist(h,'chi2','Chi2/DOF',100,0.,20.)

# -----Create geometry----------------------------------------------
import shipDet_conf
run = ROOT.FairRunSim()
modules = shipDet_conf.configure(run,ShipGeo)

# make global variables
builtin.debug    = debug
builtin.pidProton = pidProton
builtin.realPR = realPR
builtin.vertexing = vertexing
builtin.ecalGeoFile = ecalGeoFile
builtin.ShipGeo = ShipGeo
builtin.modules = modules
builtin.EcalDebugDraw  = EcalDebugDraw
builtin.withNoStrawSmearing = withNoStrawSmearing
builtin.h    = h
builtin.log  = log
iEvent = 0
builtin.iEvent  = iEvent

# import reco tasks
import shipDigiReco
SHiP = shipDigiReco.ShipDigiReco(outFile,fgeo)
nEvents   = min(SHiP.sTree.GetEntries(),nEvents)
# main loop
for iEvent in range(firstEvent, nEvents):
 if iEvent%1000 == 0 or debug: print 'event ',iEvent
 rc    = SHiP.sTree.GetEvent(iEvent) 
 SHiP.digitize()
 SHiP.reconstruct()
 # memory monitoring
 # mem_monitor() 
# end loop over events
SHiP.finish()
