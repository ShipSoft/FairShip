mcEngine  = "TGeant4"
simEngine = "Pgun"
nEvents = 5

import ROOT,os
ROOT.gROOT.LoadMacro("$VMCWORKDIR/gconfig/basiclibs.C")
ROOT.basiclibs()

#-----prepare python exit-----------------------------------------------
def pyExit():
 global run
 del run
import atexit
atexit.register(pyExit)

#
muShieldLength       = 7000 # m
targetHadronAbsorber = 350  # m
decayVolumeLength    = 5000 # m
# Output file name
tag = simEngine+"-"+mcEngine
outFile = "ship."+tag+".root"
os.system("rm *."+tag+".root")
# Parameter file name
parFile="ship.params."+tag+".root"

# In general, the following parts need not be touched
# ========================================================================

# -----Timer--------------------------------------------------------
timer = ROOT.TStopwatch()
timer.Start()
# ------------------------------------------------------------------------

# -----Create simulation run----------------------------------------
run = ROOT.FairRunSim()
run.SetName(mcEngine)# Transport engine
run.SetOutputFile(outFile) # Output file
rtdb = run.GetRuntimeDb()
# ------------------------------------------------------------------------

# -----Create media-------------------------------------------------
run.SetMaterials("media.geo")  # Materials
# ------------------------------------------------------------------------

# -----Create geometry----------------------------------------------

cave= ROOT.ShipCave("CAVE")
cave.SetGeometryFileName("cave.geo")
run.AddModule(cave)

TargetStation = ROOT.ShipTargetStation("TargetStation",muShieldLength)
run.AddModule(TargetStation)
MuonShield = ROOT.ShipMuonShield("MuonShield",1)
run.AddModule(MuonShield)

magnet = ROOT.ShipMagnet("Magnet")
run.AddModule(magnet)

Chamber = ROOT.ShipChamber("Chamber")
run.AddModule(Chamber)

Veto = ROOT.veto("Veto", ROOT.kTRUE)
run.AddModule(Veto)

ecal = ROOT.ecal("Ecal", ROOT.kTRUE)
run.AddModule(ecal)

Muon = ROOT.muon("Muon", ROOT.kTRUE)
run.AddModule(Muon)

#-----   Magnetic field   -------------------------------------------
    # Constant Field
fMagField = ROOT.ShipConstField()
fMagField.SetField(0., 2. ,0. ) # values are in kG
fMagField.SetFieldRegion(-160, 160,-160, 160, 1940, 125); # values are in cm  (xmin,xmax,ymin,ymax,zmin,zmax)
run.SetField(fMagField)

# -----Create PrimaryGenerator--------------------------------------
primGen = ROOT.FairPrimaryGenerator()
pointZero =  -decayVolumeLength/2. - targetHadronAbsorber - muShieldLength - 200.

mom = ROOT.TVector3(0.,0.,100.)
pos = ROOT.TVector3(0.,0.,pointZero)
myPgun = ROOT.FairParticleGenerator(2212,1,0.,0.,100.,0.,0.,pointZero)
primGen.AddGenerator(myPgun)

run.SetGenerator(primGen)
# ------------------------------------------------------------------------

#---Store the visualiztion info of the tracks, this make the output file very large!!
#--- Use it only to display but not for production!
run.SetStoreTraj(ROOT.kTRUE)

# -----Initialize simulation run------------------------------------
run.Init()
# ------------------------------------------------------------------------

# -----Runtime database---------------------------------------------
kParameterMerged = ROOT.kTRUE
parOut = ROOT.FairParRootFileIo(kParameterMerged)
parOut.open(parFile)
rtdb.setOutput(parOut)
rtdb.saveOutput()
#rtdb.print() does not work in python ??
rtdb.printParamContexts()
# -----Start run----------------------------------------------------
run.Run(nEvents)
run.CreateGeometryFile("geofile_full."+tag+".root")
# ------------------------------------------------------------------------

# -----Finish-------------------------------------------------------
timer.Stop()
rtime = timer.RealTime()
ctime = timer.CpuTime()
print ' '
print "Macro finished succesfully."
print "Output file is ",  outFile
print "Parameter file is ",parFile
print "Real time ",rtime, " s, CPU time ",ctime,"s"

# ------------------------------------------------------------------------

def someDebug():
 g = ROOT.gROOT
 lm = run.GetListOfModules()
 for x in lm: print x.GetName()
 fGeo = ROOT.gGeoManager
 cave = fGeo.GetTopVolume()
 cave.Draw('ogl')
#
 tf = g.FindObjectAny('cbmroot')
 for l in tf.GetListOfFolders(): print l.GetName()
 l   = tf.FindObject('MCGeoTrack')
 trs = l.FindObject('GeoTracks')
 for x in trs: print x
 l = tf.FindObject('Stack')
 trs = l.FindObject('MCTrack')
 for x in trs: print x
#
 gMC = ROOT.gMC # <ROOT.TVirtualMC* object ("TGeant4") at 0x2a5d3e8>
 fStack = gMC.GetStack()
 gMC.ProcessRun(1) # 1 event
#
 gMC.GetMC() # <ROOT.TGeant4 object ("TGeant4")
 g4.NofVolumes()
 g4.StartGeantUI()
#
 gPrim = run.GetPrimaryGenerator()
 mch   = gPrim.GetEvent() # <ROOT.FairMCEventHeader object ("MCEventHeader.")
 print mch.GetEventID(),mch.GetZ()
 gPy8 = gPrim.GetListOfGenerators()[0]
