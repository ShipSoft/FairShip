import ROOT,os
mcEngine  = "TGeant4"
simEngine = "Pythia8"
nEvents = 100
inclusive = False  # True = all processes if False only ccbar -> HNL

#
import shipunit as u
import ShipGeo,shipRoot_conf
shipRoot_conf.configure()

# Output file name
tag = simEngine+"-"+mcEngine
outFile ="ship."+tag+".root"  
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
# -----Create geometry----------------------------------------------
import shipDet_conf
shipDet_conf.configure(run)
# -----Create PrimaryGenerator--------------------------------------
primGen = ROOT.FairPrimaryGenerator()
primGen.SetTarget(ShipGeo.target.z0, 0.) 
# -----Pythia8--------------------------------------
P8gen = ROOT.Pythia8Generator()
import pythia8_conf
pythia8_conf.configure(P8gen,inclusive)
primGen.AddGenerator(P8gen)
run.SetGenerator(primGen)

if inclusive: 
  # check presence of HNL
  P8gen.GetPythiaInstance(9900014)
# ------------------------------------------------------------------------
 
#---Store the visualiztion info of the tracks, this make the output file very large!!
#--- Use it only to display but not for production!
run.SetStoreTraj(ROOT.kTRUE)
# run.SetStoreTraj(ROOT.kFALSE)
 
# -----Initialize simulation run------------------------------------
run.Init()
fStack = ROOT.gMC.GetStack()
fStack.SetEnergyCut(100.*u.MeV)

# ------------------------------------------------------------------------

# -----Runtime database---------------------------------------------
kParameterMerged = ROOT.kTRUE
parOut = ROOT.FairParRootFileIo(kParameterMerged)
parOut.open(parFile)
rtdb.setOutput(parOut)
rtdb.saveOutput()
rtdb.printParamContexts()
# -----Start run----------------------------------------------------
run.Run(nEvents)
# ------------------------------------------------------------------------
run.CreateGeometryFile("geofile_full."+tag+".root")  
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
 fGeo = ROOT.gGeoManager         # <ROOT.TGeoManager* object ("FAIRGeom")
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
 g4 = gMC.GetMC() # <ROOT.TGeant4 object ("TGeant4") 
 g4.NofVolumes()
 for i in range(1,g4.NofVolumes()+1): print i,g4.VolName(i)

 g4.StartGeantUI()
#
 gPrim = run.GetPrimaryGenerator()
 mch   = gPrim.GetEvent() # <ROOT.FairMCEventHeader object ("MCEventHeader.")
 print mch.GetEventID(),mch.GetZ()
 gPy8 = gPrim.GetListOfGenerators()[0]

