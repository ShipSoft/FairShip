#!/usr/bin/env python 
import ROOT,os,sys,getopt,time
import shipunit as u
import shipRoot_conf
from ShipGeoConfig import ConfigRegistry
debug = 0  # 1 print weights and field
           # 2 make overlap check
# Default HNL parameters
theMass = 1.0*u.GeV
#theCouplings = [1.e-8, 1.e-8, 1.e-8] # may not correspond to ctau=54km
theCouplings = [0.447e-9, 7.15e-9, 1.88e-9] # ctau=53.3km

mcEngine     = "TGeant4"
simEngine    = "Pythia8"  # "Genie" # Ntuple
nEvents      = 1000
firstEvent   = 0
inclusive    = "c"    # True = all processes if "c" only ccbar -> HNL, if "b" only bbar -> HNL
deepCopy     = False  # False = copy only stable particles to stack, except for HNL events
charmonly    = False  # option to be set with -A to enable only charm decays, charm x-sec measurement  
HNL          = True
RPVSUSY      = False
RPVSUSYbench = 2

eventDisplay = False
#inputFile    = "/eos/ship/data/Charm/Cascade-parp16-MSTP82-1-MSEL4-76Mpot_1.root"
inputFile    = "/home/vagrant/ShipSoft/Cascade-parp16-MSTP82-1-MSEL4-76Mpot_1.root"
defaultInputFile = True
outputDir    = "."
theSeed      = int(10000 * time.time() % 10000000)
dy           = 10.
dv           = 4 # 4=TP elliptical tank design, 5 = optimized conical rectangular design
ds           = 5 # 5=TP muon shield, 6=magnetized hadron, 7=short magnet design 
inactivateMuonProcesses = False   # provisionally for making studies of various muon background sources
checking4overlaps = False
if debug>1 : checking4overlaps = True
phiRandom   = False  # only relevant for muon background generator
followMuon  = False   # only transport muons for a fast muon only background estimate
nuRadiography = False # misuse GenieGenerator for neutrino radiography and geometry timing test
Opt_high = None # switch for cosmic generator
try:
        opts, args = getopt.getopt(sys.argv[1:], "D:FHPu:n:i:f:c:hqv:s:l:A:Y:i:m:co:",[\
                                   "PG","Pythia6","Pythia8","Genie","MuDIS","Ntuple","Nuage","MuonBack","FollowMuon",\
                                   "Cosmics=","nEvents=", "display", "seed=", "firstEvent=", "phiRandom", "mass=",\
                                   "couplings=", "coupling=","output=","tankDesign=","muShieldDesign=","NuRadio",\
                                   "RpvSusy","SusyBench="])
except getopt.GetoptError:
        # print help information and exit:
        print ' enter --Pythia8 to generate events with Pythia8 (-A b: signal from b, -A c: signal from c (default)  or -A inclusive)'
        print ' or    --Genie for reading and processing neutrino interactions '
        print ' or    --Pythia6 for muon nucleon scattering'  
        print ' or    --PG for particle gun'  
        print '       --MuonBack to generate events from muon background file, --Cosmics=0 for cosmic generator data'  
        print '       --RpvSusy to generate events based on RPV neutralino (default HNL)'
        print '       --SusyBench to specify which of the preset benchmarks to generate (default 2)'
        print '       --mass or -m to set HNL or New Particle mass'
        print '       --couplings \'U2e,U2mu,U2tau\' or -c \'U2e,U2mu,U2tau\' to set list of HNL couplings'
        print '                   Note that for RPVSUSY the third entry of the couplings is the stop mass'
        sys.exit()
for o, a in opts:
        if o in ("-D","--display"):
            eventDisplay = True
        if o in ("--Pythia6"):
            simEngine = "Pythia6"
        if o in ("--Pythia8"):
            simEngine = "Pythia8"
        if o in ("--PG"):
            simEngine = "PG"
        if o in ("-A"):
            inclusive = a
            if a.lower() == 'charmonly': 
               charmonly = True
               HNL = False  
            if a not in ['b','c']: inclusive = True
        if o in ("--Genie"):
            simEngine = "Genie"
        if o in ("--NuRadio"):
            simEngine = "nuRadiography"
        if o in ("--Ntuple"):
            simEngine = "Ntuple"
        if o in ("--FollowMuon"):
            followMuon = True
        if o in ("--MuonBack"):
            simEngine = "MuonBack"
        if o in ("--Nuage"):
            simEngine = "Nuage"
        if o in ("--phiRandom"):
            phiRandom = True
        if o in ("--Cosmics"):
            simEngine = "Cosmics"
            Opt_high = 0
            if a!=str(0): Opt_high = int(a)
        if o in ("--MuDIS"):
            simEngine = "muonDIS"
        if o in ("-n", "--nEvents"):
            nEvents = int(a)
        if o in ("-i", "--firstEvent"):
            firstEvent = int(a)
        if o in ("-s", "--seed"):
            theSeed = int(a)
        if o in ("-f"):
            if a.lower() == "none": inputFile = None
            else: inputFile = a
            defaultInputFile = False
        if o in ("-o", "--output"):
            outputDir = a
        if o in ("-Y"): 
            dy = float(a)
        if o in ("--tankDesign"): 
            dv = int(a)
        if o in ("--muShieldDesign"): 
            ds = int(a)
        if o in ("-F"):
            deepCopy = True
        if o in ("--RpvSusy"):
            HNL = False
            RPVSUSY = True
        if o in ("--SusyBench"):
            RPVSUSYbench = int(a)
        if o in ("-m", "--mass"):
            theMass = float(a)
        if o in ("-c", "--couplings", "--coupling"):
            theCouplings = [float(c) for c in a.split(",")]
            

if (simEngine == "Genie" or simEngine == "nuRadiography") and defaultInputFile: 
  inputFile = "/eos/ship/data/GenieEvents/genie-nu_mu.root"
            # "/eos/ship/data/GenieEvents/genie-nu_mu_bar.root"
if simEngine == "muonDIS" and defaultInputFile:
  print 'input file required if simEngine = muonDIS'
  print " for example -f  /eos/ship/data/muonDIS/muonDis_1.root"
  sys.exit()
if simEngine == "Nuage" and not inputFile:
 inputFile = 'Numucc.root'

print "FairShip setup for",simEngine,"to produce",nEvents,"events"
if (simEngine == "Ntuple" or simEngine == "MuonBack") and defaultInputFile :
  print 'input file required if simEngine = Ntuple or MuonBack'
  print " for example -f /eos/ship/data/Mbias/pythia8_Geant4-withCharm_onlyMuons_4magTarget.root"
  sys.exit()
ROOT.gRandom.SetSeed(theSeed)  # this should be propagated via ROOT to Pythia8 and Geant4VMC
shipRoot_conf.configure()      # load basic libraries, prepare atexit for python
# - muShieldDesign = 2  # 1=passive 5=active (default) 7=short design+magnetized hadron absorber
# - targetOpt      = 5  # 0=solid   >0 sliced, 5: 5 pieces of tungsten, 4 H20 slits, 17: Mo + W +H2O (default)
# - strawDesign    = 4  # simplistic tracker design,  4=sophisticated straw tube design, horizontal wires (default)
# - HcalOption     = -1 # no hcal,  0=hcal after muon,  1=hcal between ecal and muon (default)
# - preshowerOption = 0 # no preshower, default. 1= simple preshower 
ship_geo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", Yheight = dy, tankDesign = dv, muShieldDesign = ds)
# Output file name, add dy to be able to setup geometry with ambiguities.
tag = simEngine+"-"+mcEngine
if charmonly: tag = simEngine+"CharmOnly-"+mcEngine
if eventDisplay: tag = tag+'_D'
if dv == 5 : tag = 'conical.'+tag
elif dy: tag = str(dy)+'.'+tag 
if not os.path.exists(outputDir):
  os.makedirs(outputDir)
outFile = "%s/ship.%s.root" % (outputDir, tag)

# rm older files !!! 
for x in os.listdir(outputDir):
  if not x.find(tag)<0: os.system("rm %s/%s" % (outputDir, x) )
# Parameter file name
parFile="%s/ship.params.%s.root" % (outputDir, tag)

# In general, the following parts need not be touched
# ========================================================================

# -----Timer--------------------------------------------------------
timer = ROOT.TStopwatch()
timer.Start()
# ------------------------------------------------------------------------

# -----Create simulation run----------------------------------------
run = ROOT.FairRunSim()
run.SetName(mcEngine)  # Transport engine
run.SetOutputFile(outFile)  # Output file
run.SetUserConfig("g4Config.C") # user configuration file default g4Config.C 
rtdb = run.GetRuntimeDb() 
# -----Create geometry----------------------------------------------
# import shipMuShield_only as shipDet_conf # special use case for an attempt to convert active shielding geometry for use with FLUKA
# import shipTarget_only as shipDet_conf
import shipDet_conf
modules = shipDet_conf.configure(run,ship_geo)
# -----Create PrimaryGenerator--------------------------------------
primGen = ROOT.FairPrimaryGenerator()
if simEngine == "Pythia8":
 primGen.SetTarget(ship_geo.target.z0, 0.) 
# -----Pythia8--------------------------------------
 if HNL:
  P8gen = ROOT.HNLPythia8Generator()
  import pythia8_conf
  print 'Generating HNL events of mass %.3f GeV\n'%theMass
  print 'and with couplings=',theCouplings
  pythia8_conf.configure(P8gen,theMass,theCouplings,inclusive,deepCopy)
  P8gen.SetSmearBeam(1*u.cm) # finite beam size
  P8gen.SetParameters("ProcessLevel:all = off")
  if ds==7: # short muon shield
   P8gen.SetLmin(44*u.m)
   P8gen.SetLmax(107*u.m)
  if inputFile: 
# read from external file
   P8gen.UseExternalFile(inputFile, firstEvent)


 if RPVSUSY:
  P8gen = ROOT.HNLPythia8Generator()
  import pythia8_conf
  print 'Generating RPVSUSY events of mass %.3f GeV\n'%theMass
  print 'and with couplings=[%.3f,%.3f]\n'%(theCouplings[0],theCouplings[1])
  print 'and with stop mass=\%.3f GeV\n',theCouplings[2]
  pythia8_conf.configurerpvsusy(P8gen,theMass,[theCouplings[0],theCouplings[1]],
                                theCouplings[2],RPVSUSYbench,'c',deepCopy)
  P8gen.SetSmearBeam(1*u.cm) # finite beam size
  P8gen.SetParameters("ProcessLevel:all = off")
  if ds==7: # short muon shield
   P8gen.SetLmin(44*u.m)
   P8gen.SetLmax(107*u.m)
  if inputFile: 
# read from external file
   P8gen.UseExternalFile(inputFile, firstEvent)
 
 if charmonly: 
  P8gen = ROOT.Pythia8Generator()
  P8gen.UseExternalFile(inputFile, firstEvent)
# pion on proton 500GeV
# P8gen.SetMom(500.*u.GeV)
# P8gen.SetId(-211)
 primGen.AddGenerator(P8gen)
if simEngine == "Pythia6":
# set muon interaction close to decay volume
 primGen.SetTarget(ship_geo.target.z0+ship_geo.muShield.length, 0.) 
# -----Pythia6-------------------------
 test = ROOT.TPythia6() # don't know any other way of forcing to load lib
 P6gen = ROOT.tPythia6Generator()
 P6gen.SetMom(50.*u.GeV)
 P6gen.SetTarget("gamma/mu+","n0") # default "gamma/mu-","p+"
 primGen.AddGenerator(P6gen)
# -----Particle Gun-----------------------
if simEngine == "PG": 
  myPgun = ROOT.FairBoxGenerator(22,1)
  myPgun.SetPRange(10,10.2)
  myPgun.SetPhiRange(0, 360) # // Azimuth angle range [degree]
  myPgun.SetThetaRange(0,0) # // Polar angle in lab system range [degree]
  myPgun.SetXYZ(0.*u.cm, 0.*u.cm, 0.*u.cm) 
  primGen.AddGenerator(myPgun)
  run.SetGenerator(primGen)
# -----muon DIS Background------------------------
if simEngine == "muonDIS":
 primGen.SetTarget(0., 0.) 
 DISgen = ROOT.MuDISGenerator()
 # from nu_tau detector to tracking station 2
 # mu_start, mu_end =  ship_geo.tauMS.zMSC,ship_geo.TrackStation2.z
 #
 # in front of UVT up to tracking station 1
 mu_start, mu_end = ship_geo.Chamber1.z-ship_geo.chambers.Tub1length-10.*u.cm,ship_geo.TrackStation1.z
 print 'MuDIS position info input=',mu_start, mu_end
 DISgen.SetPositions(ship_geo.target.z0, mu_start, mu_end)
 DISgen.Init(inputFile,firstEvent) 
 primGen.AddGenerator(DISgen)
 nEvents = min(nEvents,DISgen.GetNevents())
 print 'Generate ',nEvents,' with DIS input', ' first event',firstEvent
# -----neutrino interactions from nuage------------------------
if simEngine == "Nuage":
 primGen.SetTarget(0., 0.)
 Nuagegen = ROOT.NuageGenerator()
 Nuagegen.EnableExternalDecayer(1) #with 0 external decayer is disable, 1 is enabled
 print 'Nuage position info input=',ship_geo.EmuMagnet.zC-ship_geo.NuTauTarget.zdim, ship_geo.EmuMagnet.zC+ship_geo.NuTauTarget.zdim
 #--------------------------------
 #to Generate neutrino interactions in the whole neutrino target
# Nuagegen.SetPositions(ship_geo.EmuMagnet.zC, ship_geo.NuTauTarget.zC-ship_geo.NuTauTarget.zdim/2, ship_geo.NuTauTarget.zC+ship_geo.NuTauTarget.zdim/2, -ship_geo.NuTauTarget.xdim/2, ship_geo.NuTauTarget.xdim/2, -ship_geo.NuTauTarget.ydim/2, ship_geo.NuTauTarget.ydim/2)
 #--------------------------------
 #to Generate neutrino interactions ONLY in ONE brick
 ntt = 6
 nXcells = 7
 nYcells = 3
 nZcells = ntt -1
 startx = -ship_geo.NuTauTarget.xdim/2 + nXcells*ship_geo.NuTauTarget.BrX
 endx = -ship_geo.NuTauTarget.xdim/2 + (nXcells+1)*ship_geo.NuTauTarget.BrX
 starty = -ship_geo.NuTauTarget.ydim/2 + nYcells*ship_geo.NuTauTarget.BrY 
 endy = - ship_geo.NuTauTarget.ydim/2 + (nYcells+1)*ship_geo.NuTauTarget.BrY
 startz = ship_geo.EmuMagnet.zC - ship_geo.NuTauTarget.zdim/2 + ntt *ship_geo.NuTauTT.TTZ + nZcells * ship_geo.NuTauTarget.CellW
 endz = ship_geo.EmuMagnet.zC - ship_geo.NuTauTarget.zdim/2 + ntt *ship_geo.NuTauTT.TTZ + nZcells * ship_geo.NuTauTarget.CellW + ship_geo.NuTauTarget.BrZ
 Nuagegen.SetPositions(ship_geo.target.z0, startz, endz, startx, endx, starty, endy)
 #--------------------------------
 Nuagegen.Init(inputFile,firstEvent)
 primGen.AddGenerator(Nuagegen)
 nEvents = min(nEvents,Nuagegen.GetNevents())
 run.SetPythiaDecayer("DecayConfigNuAge.C")
 print 'Generate ',nEvents,' with Nuage input', ' first event',firstEvent
# -----Neutrino Background------------------------
if simEngine == "Genie":
# Genie
 primGen.SetTarget(0., 0.) # do not interfere with GenieGenerator
 Geniegen = ROOT.GenieGenerator()
 Geniegen.Init(inputFile,firstEvent) 
 Geniegen.SetPositions(ship_geo.target.z0, ship_geo.tauMS.zMSC-5*u.m, ship_geo.TrackStation2.z)
 primGen.AddGenerator(Geniegen)
 nEvents = min(nEvents,Geniegen.GetNevents())
 print 'Generate ',nEvents,' with Genie input', ' first event',firstEvent
if simEngine == "nuRadiography":
 primGen.SetTarget(0., 0.) # do not interfere with GenieGenerator
 Geniegen = ROOT.GenieGenerator()
 Geniegen.Init(inputFile,firstEvent) 
 # Geniegen.SetPositions(ship_geo.target.z0, ship_geo.target.z0, ship_geo.MuonStation3.z)
 Geniegen.SetPositions(ship_geo.target.z0, ship_geo.tauMS.zMSC, ship_geo.MuonStation3.z)
 Geniegen.NuOnly()
 primGen.AddGenerator(Geniegen)
 print 'Generate ',nEvents,' for nuRadiography', ' first event',firstEvent
#  add tungsten to PDG
 pdg = ROOT.TDatabasePDG.Instance()
 pdg.AddParticle('W','Ion', 1.71350e+02, True, 0., 74, 'XXX', 1000741840)
#
 run.SetPythiaDecayer('DecayConfigPy8.C')  # this does not work !! It insists of using DecayConfig.C 
 # this requires writing a C macro, would have been easier to do directly in python! 
 # for i in [431,421,411,-431,-421,-411]:
 # ROOT.gMC.SetUserDecay(i) # Force the decay to be done w/external decayer
if simEngine == "Ntuple":
# reading previously processed muon events, [-50m - 50m]
 primGen.SetTarget(ship_geo.target.z0+50*u.m,0.)
 Ntuplegen = ROOT.NtupleGenerator()
 Ntuplegen.Init(inputFile,firstEvent)
 primGen.AddGenerator(Ntuplegen)
 nEvents = min(nEvents,Ntuplegen.GetNevents())
 print 'Process ',nEvents,' from input file'
#
if simEngine == "MuonBack":
# reading muon tracks from previous Pythia8/Geant4 simulation with charm replaced by cascade production 
 primGen.SetTarget(ship_geo.target.z0+50*u.m,0.)
 MuonBackgen = ROOT.MuonBackGenerator()
 MuonBackgen.Init(inputFile,firstEvent,phiRandom)
 MuonBackgen.SetSmearBeam(3*u.cm) # beam size mimicking spiral
 primGen.AddGenerator(MuonBackgen)
 nEvents = min(nEvents,MuonBackgen.GetNevents())
 print 'Process ',nEvents,' from input file, with Phi random=',phiRandom
 if followMuon :  modules['Veto'].SetFastMuon()
#
if simEngine == "Cosmics":
 primGen.SetTarget(0., 0.)
 Cosmicsgen = ROOT.CosmicsGenerator()
 import CMBG_conf
 CMBG_conf.configure(Cosmicsgen, ship_geo)
 if not Cosmicsgen.Init(Opt_high): 
      print "initialization of cosmic background generator failed ",Opt_high
      sys.exit(0)
 primGen.AddGenerator(Cosmicsgen)
 print 'Process ',nEvents,' Cosmic events'
#
run.SetGenerator(primGen)
# ------------------------------------------------------------------------

#---Store the visualiztion info of the tracks, this make the output file very large!!
#--- Use it only to display but not for production!
if eventDisplay: run.SetStoreTraj(ROOT.kTRUE)
else:            run.SetStoreTraj(ROOT.kFALSE)
# -----Initialize simulation run------------------------------------
run.Init()
gMC = ROOT.TVirtualMC.GetMC()
fStack = gMC.GetStack()
if not deepCopy : fStack.SetEnergyCut(100.*u.MeV)

if eventDisplay:
 # Set cuts for storing the trajectories, can only be done after initialization of run (?!)
  trajFilter = ROOT.FairTrajFilter.Instance()
  trajFilter.SetStepSizeCut(1*u.mm);  
  trajFilter.SetVertexCut(-20*u.m, -20*u.m,ship_geo.target.z0-1*u.m, 20*u.m, 20*u.m, 200.*u.m)
  trajFilter.SetMomentumCutP(0.1*u.GeV)
  trajFilter.SetEnergyCut(0., 400.*u.GeV)
  trajFilter.SetStorePrimaries(ROOT.kTRUE)
  trajFilter.SetStoreSecondaries(ROOT.kTRUE)
# manipulate G4 geometry to enable magnetic field in active shielding, VMC can't do it.
if ship_geo.muShieldDesign != 1:
 import geomGeant4
 geomGeant4.setMagnetField() # ('dump') for printout of mag fields
 if debug > 0: geomGeant4.printWeightsandFields()
if inactivateMuonProcesses : 
 mygMC = ROOT.TGeant4.GetMC()
 mygMC.ProcessGeantCommand("/process/inactivate muPairProd")
 mygMC.ProcessGeantCommand("/process/inactivate muBrems")
 mygMC.ProcessGeantCommand("/process/inactivate muIoni")
 mygMC.ProcessGeantCommand("/particle/select mu+")
 mygMC.ProcessGeantCommand("/particle/process/dump")
 import G4processes
 gProcessTable = G4processes.G4ProcessTable.GetProcessTable()
 procmu = gProcessTable.FindProcess('muIoni','mu+')
 procmu.SetVerboseLevel(2)
# -----Start run----------------------------------------------------
run.Run(nEvents)
# -----Runtime database---------------------------------------------
kParameterMerged = ROOT.kTRUE
parOut = ROOT.FairParRootFileIo(kParameterMerged)
parOut.open(parFile)
rtdb.setOutput(parOut)
rtdb.saveOutput()
rtdb.printParamContexts()
getattr(rtdb,"print")()
# ------------------------------------------------------------------------
run.CreateGeometryFile("%s/geofile_full.%s.root" % (outputDir, tag))
# save ShipGeo dictionary in geofile
import saveBasicParameters
saveBasicParameters.execute("%s/geofile_full.%s.root" % (outputDir, tag),ship_geo)

# checking for overlaps
if checking4overlaps:
 fGeo = ROOT.gGeoManager
 fGeo.SetNmeshPoints(10000)
 fGeo.CheckOverlaps(0.0001)  # 1 micron takes 5minutes
 fGeo.PrintOverlaps()
# -----Finish-------------------------------------------------------
timer.Stop()
rtime = timer.RealTime()
ctime = timer.CpuTime()
print ' ' 
print "Macro finished succesfully." 
if "P8gen" in globals() : print "number of retries, events without HNL",P8gen.nrOfRetries()
print "Output file is ",  outFile 
print "Parameter file is ",parFile
print "Real time ",rtime, " s, CPU time ",ctime,"s"

# ------------------------------------------------------------------------
import checkMagFields
def visualizeMagFields():
 checkMagFields.run()
def checkOverlapsWithGeant4():
 # after /run/initialize, but prints warning messages, problems with TGeo volume
 mygMC = ROOT.TGeant4.GetMC()
 mygMC.ProcessGeantCommand("/geometry/test/recursion_start 0")
 mygMC.ProcessGeantCommand("/geometry/test/recursion_depth 2")
 mygMC.ProcessGeantCommand("/geometry/test/run")
