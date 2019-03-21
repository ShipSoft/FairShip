#!/usr/bin/env python2
import os
import sys
import getopt
import ROOT
import shipunit as u
import shipRoot_conf
import rootUtils as ut
from ShipGeoConfig import ConfigRegistry

debug = 0  # 1 print weights and field
           # 2 make overlap check
dryrun = False # True: just setup Pythia and exit

CharmdetSetup = 0 # 1 charm cross section setup, 0 muon flux setup
CharmTarget = 3 #six different configurations used in July 2018 exposure for charm
# Default HNL parameters
theMass = 1.0*u.GeV
theCouplings = [0.447e-9, 7.15e-9, 1.88e-9] # ctau=53.3km  TP default for HNL
theProductionCouplings = theDecayCouplings = None

# Default dark photon parameters
theDPmass = 0.2*u.GeV
theDPepsilon = 0.00000008

mcEngine     = "TGeant4"
simEngine    = "Pythia8"  # "Genie" # Ntuple
nEvents      = 100
firstEvent   = 0
inclusive    = "c"    # True = all processes if "c" only ccbar -> HNL, if "b" only bbar -> HNL, if "bc" only Bc+/Bc- -> HNL, and for darkphotons: if meson = production through meson decays, pbrem = proton bremstrahlung, qcd = ffbar -> DP.
deepCopy     = False  # False = copy only stable particles to stack, except for HNL events
MCTracksWithHitsOnly   = False  # copy particles which produced a hit and their history
MCTracksWithEnergyCutOnly = True # copy particles above a certain kin energy cut
MCTracksWithHitsOrEnergyCut = False # or of above, factor 2 file size increase compared to MCTracksWithEnergyCutOnly

charmonly    = False  # option to be set with -A to enable only charm decays, charm x-sec measurement  
HNL          = True
DarkPhoton   = False
RPVSUSY      = False
RPVSUSYbench = 2

eventDisplay = False
inputFile    = "/eos/experiment/ship/data/Charm/Cascade-parp16-MSTP82-1-MSEL4-978Bpot.root"

defaultInputFile = True
outputDir    = "."
sameSeed     = False # can be set to an integer for the muonBackground simulation with specific seed for each muon 
theSeed      = 0 # see TRrandom::SetSeed documentation

globalDesigns = {'2016':{'dy':10.,'dv':5,'ds':7,'nud':1,'caloDesign':0,'strawDesign':4},\
                 '2018':{'dy':10.,'dv':6,'ds':9,'nud':3,'caloDesign':3,'strawDesign':10}}
default = '2018'

dy           = globalDesigns[default]['dy'] # max height of vacuum tank
dv           = globalDesigns[default]['dv'] # 4=TP elliptical tank design, 5 = optimized conical rectangular design, 6=5 without segment-1
ds           = globalDesigns[default]['ds'] # 5=TP muon shield, 6=magnetized hadron, 7=short magnet design, 9=optimised with T4 as constraint, 8=requires config file
nud          = globalDesigns[default]['nud'] # 0=TP, 1=new magnet option for short muon shield, 2= no magnet surrounding neutrino detector
caloDesign   = globalDesigns[default]['caloDesign'] # 0=ECAL/HCAL TP  1=ECAL/HCAL TP + preshower 2=splitCal  3=ECAL/ passive HCAL 
strawDesign  = globalDesigns[default]['strawDesign'] # simplistic tracker design,  4=sophisticated straw tube design, horizontal wires (default), 10=2cm straw diameter for 2018 layout

charm        = 0 # !=0 create charm detector instead of SHiP
pID          = 22 # default for the particle gun
geofile = None

inactivateMuonProcesses = False   # provisionally for making studies of various muon background sources
checking4overlaps = False
if debug>1 : checking4overlaps = True
phiRandom   = False  # only relevant for muon background generator
followMuon  = False  # make muonshield active to follow muons
fastMuon    = False  # only transport muons for a fast muon only background estimate
nuRadiography = False # misuse GenieGenerator for neutrino radiography and geometry timing test
Opt_high = None # switch for cosmic generator
try:
        opts, args = getopt.getopt(sys.argv[1:], "D:FHPu:n:i:f:c:hqv:s:l:A:Y:i:m:co:t:g",[\
                                   "PG","pID=","Muflux","Pythia6","Pythia8","Genie","MuDIS","Ntuple","Nuage","MuonBack","FollowMuon","FastMuon",\
                                   "Cosmics=","nEvents=", "display", "seed=", "firstEvent=", "phiRandom", "mass=", "couplings=", "coupling=", "epsilon=",\
                                   "output=","tankDesign=","muShieldDesign=","NuRadio","test",\
                                   "DarkPhoton","RpvSusy","SusyBench=","sameSeed=","charm=","CharmdetSetup=","CharmTarget=","nuTauTargetDesign=","caloDesign=","strawDesign=","Estart=",\
                                   "Eend=","production-couplings=","decay-couplings=","dry-run"])

except getopt.GetoptError:
        # print help information and exit:
        print ' enter --Pythia8 to generate events with Pythia8 (-A b: signal from b, -A c: signal from c (default), -A bc: signal from Bc, or -A inclusive)'
        print ' or    --Genie for reading and processing neutrino interactions '
        print ' or    --Pythia6 for muon nucleon scattering'  
        print ' or    --PG for particle gun'  
	print '       --pID= id of particle used by the gun (default=22)'
	print '       --Estart= start of energy range of particle gun for muflux detector (default=10 GeV)'
	print '       --Eend= end of energy range of particle gun for muflux detector (default=10 GeV)'	
        print '       --MuonBack to generate events from muon background file, --Cosmics=0 for cosmic generator data'  
        print '       --RpvSusy to generate events based on RPV neutralino (default HNL)'
        print '       --DarkPhoton to generate events with dark photons (default HNL)'
        print ' for darkphoton generation, use -A meson or -A pbrem or -A qcd'
        print '       --SusyBench to specify which of the preset benchmarks to generate (default 2)'
        print '       --mass or -m to set HNL or New Particle mass'
        print '       --couplings \'U2e,U2mu,U2tau\' or -c \'U2e,U2mu,U2tau\' to set list of HNL couplings'
        print '       --production-couplings \'U2e,U2mu,U2tau\' to set the couplings for HNL production only'
        print '       --decay-couplings \'U2e,U2mu,U2tau\' to set the couplings for HNL decay only'
        print '       --epsilon value or -e value to set mixing parameter epsilon' 
        print '                   Note that for RPVSUSY the third entry of the couplings is the stop mass'
        sys.exit(2)
for o, a in opts:
        if o in ("-D","--display"):
            eventDisplay = True
        if o in ("--Pythia6",):
            simEngine = "Pythia6"
        if o in ("--Pythia8",):
            simEngine = "Pythia8"
        if o in ("--PG",):
            simEngine = "PG"
        if o in ("--Muflux",):
            simEngine = "FixedTarget"
            HNL = False
        if o in ("--pID",):
            if a: pID = int(a)
        if o in ("--Estart",):
            Estart = 10.
            if a!=str(0): Estart = float(a)
        if o in ("--Eend",):
            Eend = 10.
            if a!=str(0): Eend = float(a)   
        if o in ("-A",):
            inclusive = a
            if a=='b': inputFile = "/eos/experiment/ship/data/Beauty/Cascade-run0-19-parp16-MSTP82-1-MSEL5-5338Bpot.root"
            if a.lower() == 'charmonly':
               charmonly = True
               HNL = False 
            if a not in ['b','c','bc','meson','pbrem','qcd']: inclusive = True
        if o in ("--Genie",):
            simEngine = "Genie"
        if o in ("--NuRadio",):
            simEngine = "nuRadiography"
        if o in ("--Ntuple",):
            simEngine = "Ntuple"
        if o in ("--FollowMuon",):
            followMuon = True
        if o in ("--FastMuon",):
            fastMuon = True
        if o in ("--MuonBack",):
            simEngine = "MuonBack"
        if o in ("--Nuage",):
            simEngine = "Nuage"
        if o in ("--phiRandom",):
            phiRandom = True
        if o in ("--Cosmics",):
            simEngine = "Cosmics"
            Opt_high = 0
            if a!=str(0): Opt_high = int(a)
        if o in ("--MuDIS",):
            simEngine = "muonDIS"
        if o in ("-n", "--nEvents",):
            nEvents = int(a)
        if o in ("-i", "--firstEvent",):
            firstEvent = int(a)
        if o in ("-s", "--seed",):
            theSeed = int(a)
        if o in ("-s", "--sameSeed",):
            sameSeed = int(a)
        if o in ("-f",):
            if a.lower() == "none": inputFile = None
            else: inputFile = a
            defaultInputFile = False
        if o in ("-g",):
            geofile = a
        if o in ("-o", "--output",):
            outputDir = a
        if o in ("-Y",): 
            dy = float(a)
        if o in ("--tankDesign",):
            dv = int(a)
        if o in ("--muShieldDesign",):
            ds = int(a)
        if o in ("--nuTauTargetDesign",):
            nud = int(a)
        if o in ("--caloDesign",):
            caloDesign = int(a)
        if o in ("--strawDesign",):
            strawDesign = int(a)
        if o in ("--charm",):
            charm = int(a)
        if o in ("--CharmdetSetup",):
            CharmdetSetup = int(a)
        if o in ("--CharmTarget",):
            CharmTarget = int(a)
        if o in ("-F",):
            deepCopy = True
        if o in ("--RpvSusy",):
            HNL = False
            RPVSUSY = True
        if o in ("--DarkPhoton",):
            HNL = False
            DarkPhoton = True
        if o in ("--SusyBench",):
            RPVSUSYbench = int(a)
        if o in ("-m", "--mass",):
           if DarkPhoton: theDPmass = float(a)
           else: theMass = float(a)
        if o in ("-c", "--couplings", "--coupling",):
           theCouplings = [float(c) for c in a.split(",")]
        if o in ("-cp", "--production-couplings"):
            theProductionCouplings = [float(c) for c in a.split(",")]
        if o in ("-cd", "--decay-couplings"):
            theDecayCouplings = [float(c) for c in a.split(",")]
        if o in ("-e", "--epsilon",):
           theDPepsilon = float(a)
        if o in ("-t", "--test"):
            inputFile = "$FAIRSHIP/files/Cascade-parp16-MSTP82-1-MSEL4-76Mpot_1_5000.root"
            nEvents = 50
        if o in ("--dry-run",):
            dryrun = True

#sanity check
if (HNL and RPVSUSY) or (HNL and DarkPhoton) or (DarkPhoton and RPVSUSY): 
 print "cannot have HNL and SUSY or DP at the same time, abort"
 sys.exit(2)

if (simEngine == "Genie" or simEngine == "nuRadiography") and defaultInputFile: 
  inputFile = "/eos/experiment/ship/data/GenieEvents/genie-nu_mu.root"
            # "/eos/experiment/ship/data/GenieEvents/genie-nu_mu_bar.root"
if simEngine == "muonDIS" and defaultInputFile:
  print 'input file required if simEngine = muonDIS'
  print " for example -f  /eos/experiment/ship/data/muonDIS/muonDis_1.root"
  sys.exit()
if simEngine == "Nuage" and not inputFile:
 inputFile = 'Numucc.root'

print "FairShip setup for",simEngine,"to produce",nEvents,"events"
if (simEngine == "Ntuple" or simEngine == "MuonBack") and defaultInputFile :
  print 'input file required if simEngine = Ntuple or MuonBack'
  print " for example -f /eos/experiment/ship/data/Mbias/pythia8_Geant4-withCharm_onlyMuons_4magTarget.root"
  sys.exit()
ROOT.gRandom.SetSeed(theSeed)  # this should be propagated via ROOT to Pythia8 and Geant4VMC
shipRoot_conf.configure(0)     # load basic libraries, prepare atexit for python
# - muShieldDesign = 2  # 1=passive 5=active (default) 7=short design+magnetized hadron absorber
# - targetOpt      = 5  # 0=solid   >0 sliced, 5: 5 pieces of tungsten, 4 H20 slits, 17: Mo + W +H2O (default)
#   nuTauTargetDesign = 0 # 0 = TP, 1 = NEW with magnet, 2 = NEW without magnet, 3 = 2018 design
if charm == 0: ship_geo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", Yheight = dy, tankDesign = dv, \
                                                muShieldDesign = ds, nuTauTargetDesign=nud, CaloDesign=caloDesign, strawDesign=strawDesign, muShieldGeo=geofile)
else: 
 ship_geo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/charm-geometry_config.py", Setup = CharmdetSetup, cTarget = CharmTarget)
 if CharmdetSetup == 0: print "Setup for muon flux measurement has been set"
 else: 
  print "Setup for charm cross section measurement has been set"
  if (((CharmTarget > 6) or (CharmTarget < 0)) and (CharmTarget != 16)): #check if proper option for emulsion target has been set
   print "ERROR: unavailable option for CharmTarget. Currently implemented options: 1,2,3,4,5,6,16"
   1/0
# switch off magnetic field to measure muon flux
#ship_geo.muShield.Field = 0.
#ship_geo.EmuMagnet.B = 0.
#ship_geo.tauMudet.B = 0.


# Output file name, add dy to be able to setup geometry with ambiguities.
if simEngine == "PG": tag = simEngine + "_"+str(pID)+"-"+mcEngine
else: tag = simEngine+"-"+mcEngine
if charmonly: tag = simEngine+"CharmOnly-"+mcEngine
if eventDisplay: tag = tag+'_D'
if dv > 4 : tag = 'conical.'+tag
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
if charm!=0: import charmDet_conf as shipDet_conf 
else:        import shipDet_conf

modules = shipDet_conf.configure(run,ship_geo)
# -----Create PrimaryGenerator--------------------------------------
primGen = ROOT.FairPrimaryGenerator()
if simEngine == "Pythia8":
 primGen.SetTarget(ship_geo.target.z0, 0.) 
# -----Pythia8--------------------------------------
 if HNL or RPVSUSY:
  P8gen = ROOT.HNLPythia8Generator()
  import pythia8_conf
  if HNL:
   print 'Generating HNL events of mass %.3f GeV'%theMass
   if theProductionCouplings is None and theDecayCouplings is None:
    print 'and with couplings=',theCouplings
    theProductionCouplings = theDecayCouplings = theCouplings
   elif theProductionCouplings is not None and theDecayCouplings is not None:
    print 'and with couplings',theProductionCouplings,'at production'
    print 'and',theDecayCouplings,'at decay'
   else:
    raise ValueError('Either both production and decay couplings must be specified, or neither.')
   pythia8_conf.configure(P8gen,theMass,theProductionCouplings,theDecayCouplings,inclusive,deepCopy)
  if RPVSUSY:
   print 'Generating RPVSUSY events of mass %.3f GeV'%theMass
   print 'and with couplings=[%.3f,%.3f]'%(theCouplings[0],theCouplings[1])
   print 'and with stop mass=%.3f GeV\n'%theCouplings[2]
   pythia8_conf.configurerpvsusy(P8gen,theMass,[theCouplings[0],theCouplings[1]],
                                theCouplings[2],RPVSUSYbench,inclusive,deepCopy)
  P8gen.SetParameters("ProcessLevel:all = off")
  if inputFile: 
   ut.checkFileExists(inputFile)
# read from external file
   P8gen.UseExternalFile(inputFile, firstEvent)
 if DarkPhoton:
  P8gen = ROOT.DPPythia8Generator()
  if inclusive=='qcd':
	  P8gen.SetDPId(4900023)
  else:
	  P8gen.SetDPId(9900015)
  import pythia8darkphoton_conf
  passDPconf = pythia8darkphoton_conf.configure(P8gen,theDPmass,theDPepsilon,inclusive,deepCopy)
  if (passDPconf!=1): sys.exit()
 if HNL or RPVSUSY or DarkPhoton: 
  P8gen.SetSmearBeam(1*u.cm) # finite beam size
  P8gen.SetLmin((ship_geo.Chamber1.z - ship_geo.chambers.Tub1length) - ship_geo.target.z0 )
  P8gen.SetLmax(ship_geo.TrackStation1.z - ship_geo.target.z0 )
 if charmonly:
  primGen.SetTarget(0., 0.) #vertex is setted in pythia8Generator
  ut.checkFileExists(inputFile)
  if ship_geo.Box.gausbeam:
   primGen.SetBeam(0.,0., 0.5, 0.5) #more central beam, for hits in downstream detectors    
   primGen.SmearGausVertexXY(True) #sigma = x
  else:
   primGen.SetBeam(0.,0., ship_geo.Box.TX-1., ship_geo.Box.TY-1.) #Uniform distribution in x/y on the target (0.5 cm of margin at both sides)
   primGen.SmearVertexXY(True)
  P8gen = ROOT.Pythia8Generator()
  P8gen.UseExternalFile(inputFile, firstEvent)
  if ship_geo.MufluxSpectrometer.muflux == False :
     P8gen.SetTarget("volTarget_1",0.,0.) # will distribute PV inside target, beam offset x=y=0.
  else: 
     print "ERROR: charmonly option should not be used for the muonflux measurement"
     1/0
# pion on proton 500GeV
# P8gen.SetMom(500.*u.GeV)
# P8gen.SetId(-211)
 primGen.AddGenerator(P8gen)
if simEngine == "FixedTarget":
 P8gen = ROOT.FixedTargetGenerator()
 P8gen.SetTarget("volTarget_1",0.,0.)
 P8gen.SetMom(400.*u.GeV)
 P8gen.SetEnergyCut(0.)
 P8gen.SetHeartBeat(100000)
 P8gen.SetG4only()
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
  myPgun = ROOT.FairBoxGenerator(pID,1)
  myPgun.SetPRange(Estart,Eend)
  myPgun.SetPhiRange(0, 360) # // Azimuth angle range [degree]
  myPgun.SetXYZ(0.*u.cm, 0.*u.cm, 0.*u.cm) 
  if charm!=0:
     myPgun.SetThetaRange(0,6) # // Pdefault for muon flux
     primGen.SetTarget(ship_geo.target.z0,0.)
  else:  
     myPgun.SetThetaRange(0,0) # // Polar angle in lab system range [degree]
  primGen.AddGenerator(myPgun)
# -----muon DIS Background------------------------
if simEngine == "muonDIS":
 ut.checkFileExists(inputFile)
 primGen.SetTarget(0., 0.) 
 DISgen = ROOT.MuDISGenerator()
 # from nu_tau detector to tracking station 2
 # mu_start, mu_end =  ship_geo.tauMudet.zMudetC,ship_geo.TrackStation2.z
 #
 # in front of UVT up to tracking station 1
 mu_start, mu_end = ship_geo.Chamber1.z-ship_geo.chambers.Tub1length-10.*u.cm,ship_geo.TrackStation1.z
 print 'MuDIS position info input=',mu_start, mu_end
 DISgen.SetPositions(ship_geo.target.z0, mu_start, mu_end)
 DISgen.Init(inputFile,firstEvent) 
 primGen.AddGenerator(DISgen)
 nEvents = min(nEvents,DISgen.GetNevents())
 inactivateMuonProcesses = True # avoid unwanted hadronic events of "incoming" muon flying backward
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
 ut.checkFileExists(inputFile)
 Nuagegen.Init(inputFile,firstEvent)
 primGen.AddGenerator(Nuagegen)
 nEvents = min(nEvents,Nuagegen.GetNevents())
 run.SetPythiaDecayer("DecayConfigNuAge.C")
 print 'Generate ',nEvents,' with Nuage input', ' first event',firstEvent
# -----Neutrino Background------------------------
if simEngine == "Genie":
# Genie
 ut.checkFileExists(inputFile)
 primGen.SetTarget(0., 0.) # do not interfere with GenieGenerator
 Geniegen = ROOT.GenieGenerator()
 Geniegen.Init(inputFile,firstEvent) 
 Geniegen.SetPositions(ship_geo.target.z0, ship_geo.tauMudet.zMudetC-5*u.m, ship_geo.TrackStation2.z)
 primGen.AddGenerator(Geniegen)
 nEvents = min(nEvents,Geniegen.GetNevents())
 run.SetPythiaDecayer("DecayConfigNuAge.C")
 print 'Generate ',nEvents,' with Genie input', ' first event',firstEvent
if simEngine == "nuRadiography":
 ut.checkFileExists(inputFile)
 primGen.SetTarget(0., 0.) # do not interfere with GenieGenerator
 Geniegen = ROOT.GenieGenerator()
 Geniegen.Init(inputFile,firstEvent) 
 # Geniegen.SetPositions(ship_geo.target.z0, ship_geo.target.z0, ship_geo.MuonStation3.z)
 Geniegen.SetPositions(ship_geo.target.z0, ship_geo.tauMudet.zMudetC, ship_geo.MuonStation3.z)
 Geniegen.NuOnly()
 primGen.AddGenerator(Geniegen)
 print 'Generate ',nEvents,' for nuRadiography', ' first event',firstEvent
#  add tungsten to PDG
 pdg = ROOT.TDatabasePDG.Instance()
 pdg.AddParticle('W','Ion', 1.71350e+02, True, 0., 74, 'XXX', 1000741840)
#
 run.SetPythiaDecayer('DecayConfigPy8.C')
 # this requires writing a C macro, would have been easier to do directly in python! 
 # for i in [431,421,411,-431,-421,-411]:
 # ROOT.gMC.SetUserDecay(i) # Force the decay to be done w/external decayer
if simEngine == "Ntuple":
# reading previously processed muon events, [-50m - 50m]
 ut.checkFileExists(inputFile)
 primGen.SetTarget(ship_geo.target.z0+50*u.m,0.)
 Ntuplegen = ROOT.NtupleGenerator()
 Ntuplegen.Init(inputFile,firstEvent)
 primGen.AddGenerator(Ntuplegen)
 nEvents = min(nEvents,Ntuplegen.GetNevents())
 print 'Process ',nEvents,' from input file'
#
if simEngine == "MuonBack":
# reading muon tracks from previous Pythia8/Geant4 simulation with charm replaced by cascade production 
 fileType = ut.checkFileExists(inputFile)
 if fileType == 'tree':
 # 2018 background production 
  primGen.SetTarget(ship_geo.target.z0+70.1225*u.m,0.)
 else:
  primGen.SetTarget(ship_geo.target.z0+50*u.m,0.)
 #
 MuonBackgen = ROOT.MuonBackGenerator()
 # MuonBackgen.FollowAllParticles() # will follow all particles after hadron absorber, not only muons
 MuonBackgen.Init(inputFile,firstEvent,phiRandom)
 if charm == 0: MuonBackgen.SetSmearBeam(5 * u.cm) # radius of ring, thickness 8mm
 else: 
    if inputFile[0:4] == "/eos": test = os.environ["EOSSHIP"]+inputFile
    else: test = inputFile
    testf = ROOT.TFile.Open(test)
    if not testf.FileHeader.GetTitle().find('diMu100.0')<0:
        MuonBackgen.SetDownScaleDiMuon()   # avoid interference with boosted channels
        print "MuonBackgenerator: set downscale for dimuon on"
    testf.Close()
 if sameSeed: MuonBackgen.SetSameSeed(sameSeed)
 primGen.AddGenerator(MuonBackgen)
 nEvents = min(nEvents,MuonBackgen.GetNevents())
 MCTracksWithHitsOnly = True # otherwise, output file becomes too big
 print 'Process ',nEvents,' from input file, with Phi random=',phiRandom, ' with MCTracksWithHitsOnly',MCTracksWithHitsOnly
 if followMuon :  
    fastMuon = True
    modules['Veto'].SetFollowMuon()
 if fastMuon :    modules['Veto'].SetFastMuon()

 # optional, boost gamma2muon conversion
 # ROOT.kShipMuonsCrossSectionFactor = 100. 
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
if dryrun: # Early stop after setting up Pythia 8
 sys.exit(0)
gMC = ROOT.TVirtualMC.GetMC()
fStack = gMC.GetStack()
if MCTracksWithHitsOnly:
 fStack.SetMinPoints(1)
 fStack.SetEnergyCut(-100.*u.MeV)
elif MCTracksWithEnergyCutOnly:
 fStack.SetMinPoints(-1)
 fStack.SetEnergyCut(100.*u.MeV)
elif MCTracksWithHitsOrEnergyCut: 
 fStack.SetMinPoints(1)
 fStack.SetEnergyCut(100.*u.MeV)
elif deepCopy: 
 fStack.SetMinPoints(0)
 fStack.SetEnergyCut(0.*u.MeV)

if eventDisplay:
 # Set cuts for storing the trajectories, can only be done after initialization of run (?!)
  trajFilter = ROOT.FairTrajFilter.Instance()
  trajFilter.SetStepSizeCut(1*u.mm);  
  trajFilter.SetVertexCut(-20*u.m, -20*u.m,ship_geo.target.z0-1*u.m, 20*u.m, 20*u.m, 200.*u.m)
  trajFilter.SetMomentumCutP(0.1*u.GeV)
  trajFilter.SetEnergyCut(0., 400.*u.GeV)
  trajFilter.SetStorePrimaries(ROOT.kTRUE)
  trajFilter.SetStoreSecondaries(ROOT.kTRUE)

# The VMC sets the fields using the "/mcDet/setIsLocalMagField true" option in "gconfig/g4config.in"
import geomGeant4
# geomGeant4.setMagnetField() # replaced by VMC, only has effect if /mcDet/setIsLocalMagField  false

# Define extra VMC B fields not already set by the geometry definitions, e.g. a global field,
# any field maps, or defining if any volumes feel only the local or local+global field.
# For now, just keep the fields already defined by the C++ code, i.e comment out the fieldMaker
if charm == 0:   # charm and muflux testbeam not yet updated for using the new bfield interface
 if hasattr(ship_geo.Bfield,"fieldMap"):
  fieldMaker = geomGeant4.addVMCFields(ship_geo, '', True)

# Print VMC fields and associated geometry objects
if debug > 0:
 geomGeant4.printVMCFields()
 geomGeant4.printWeightsandFields(onlyWithField = True,\
             exclude=['DecayVolume','Tr1','Tr2','Tr3','Tr4','Veto','Ecal','Hcal','MuonDetector','SplitCal'])
# Plot the field example
#fieldMaker.plotField(1, ROOT.TVector3(-9000.0, 6000.0, 50.0), ROOT.TVector3(-300.0, 300.0, 6.0), 'Bzx.png')
#fieldMaker.plotField(2, ROOT.TVector3(-9000.0, 6000.0, 50.0), ROOT.TVector3(-400.0, 400.0, 6.0), 'Bzy.png')

if inactivateMuonProcesses :
 ROOT.gROOT.ProcessLine('#include "Geant4/G4ProcessTable.hh"')
 mygMC = ROOT.TGeant4.GetMC()
 mygMC.ProcessGeantCommand("/process/inactivate muPairProd")
 mygMC.ProcessGeantCommand("/process/inactivate muBrems")
 mygMC.ProcessGeantCommand("/process/inactivate muIoni")
 mygMC.ProcessGeantCommand("/process/inactivate muonNuclear")
 mygMC.ProcessGeantCommand("/particle/select mu+")
 mygMC.ProcessGeantCommand("/particle/process/dump")
 gProcessTable = ROOT.G4ProcessTable.GetProcessTable()
 procmu = gProcessTable.FindProcess(ROOT.G4String('muIoni'),ROOT.G4String('mu+'))
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
 fGeo.CheckOverlaps(0.1)  # 1 micron takes 5minutes
 fGeo.PrintOverlaps()
 # check subsystems in more detail
 for x in fGeo.GetTopNode().GetNodes(): 
   x.CheckOverlaps(0.0001)
   fGeo.PrintOverlaps()
# -----Finish-------------------------------------------------------
timer.Stop()
rtime = timer.RealTime()
ctime = timer.CpuTime()
print ' ' 
print "Macro finished succesfully." 
if "P8gen" in globals() : 
	if (HNL): print "number of retries, events without HNL ",P8gen.nrOfRetries()
	elif (DarkPhoton): 
		print "number of retries, events without Dark Photons ",P8gen.nrOfRetries()
		print "total number of dark photons (including multiple meson decays per single collision) ",P8gen.nrOfDP()

print "Output file is ",  outFile 
print "Parameter file is ",parFile
print "Real time ",rtime, " s, CPU time ",ctime,"s"

# remove empty events
if simEngine == "MuonBack":
 tmpFile = outFile+"tmp"
 xxx = outFile.split('/')
 check = xxx[len(xxx)-1]
 fin = False
 for ff in ROOT.gROOT.GetListOfFiles():
    nm = ff.GetName().split('/')
    if nm[len(nm)-1] == check: fin = ff
 if not fin: fin   = ROOT.TFile.Open(outFile)
 t     = fin.cbmsim
 fout  = ROOT.TFile(tmpFile,'recreate')
 sTree = t.CloneTree(0)
 nEvents = 0
 pointContainers = []
 for x in sTree.GetListOfBranches():
   name = x.GetName() 
   if not name.find('Point')<0: pointContainers.append('sTree.'+name+'.GetEntries()') # makes use of convention that all sensitive detectors fill XXXPoint containers
 for n in range(t.GetEntries()):
     rc = t.GetEvent(n)
     empty = True 
     for x in pointContainers:
        if eval(x)>0: empty = False
     if not empty:
        rc = sTree.Fill()
        nEvents+=1
 sTree.AutoSave()
 fout.Close()
 print "removed empty events, left with:", nEvents
 rc1 = os.system("rm  "+outFile)
 rc2 = os.system("mv "+tmpFile+" "+outFile)
 fin.SetWritable(False) # bpyass flush error
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


