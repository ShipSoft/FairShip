#!/usr/bin/env python
import os
import sys
import ROOT
ROOT.gSystem.Load('libEGPythia8')

import shipunit as u
import shipRoot_conf
import rootUtils as ut
from ShipGeoConfig import ConfigRegistry
from argparse import ArgumentParser

DownScaleDiMuon = False

# Default HNL parameters
theHNLMass   = 1.0*u.GeV
theProductionCouplings = theDecayCouplings = None

# Default dark photon parameters
theDPmass    = 0.2*u.GeV

# Alpaca
motherMode = True

mcEngine     = "TGeant4"
simEngine    = "Pythia8"  # "Genie" # Ntuple

inclusive    = "c"    # True = all processes if "c" only ccbar -> HNL, if "b" only bbar -> HNL, if "bc" only Bc+/Bc- -> HNL, and for darkphotons: if meson = production through meson decays, pbrem = proton bremstrahlung, qcd = ffbar -> DP.

MCTracksWithHitsOnly   = False  # copy particles which produced a hit and their history
MCTracksWithEnergyCutOnly = True # copy particles above a certain kin energy cut
MCTracksWithHitsOrEnergyCut = False # or of above, factor 2 file size increase compared to MCTracksWithEnergyCutOnly

charmonly    = False  # option to be set with -A to enable only charm decays, charm x-sec measurement
HNL          = True

inputFile    = "/eos/experiment/ship/data/Charm/Cascade-parp16-MSTP82-1-MSEL4-978Bpot.root"
defaultInputFile = True

globalDesigns = {
     '2016' : {
          'dy' : 10.,
          'dv' : 5,
          'ds' : 7,
          'nud' : 1,
          'caloDesign' : 0,
          'strawDesign' : 4
     }, '2018' : {
          'dy' : 10.,
          'dv' : 6,
          'ds' : 9,
          'nud' : 3,
          'caloDesign' : 3,
          'strawDesign' : 10
     }, '2022' : {
          'dy' : 8.,
          'dv' : 6,
          'ds' : 9,
          'nud' : 3,
          'caloDesign' : 3,
          'strawDesign' : 10
     }, '2023' : {
          'dy' : 6.,
          'dv' : 6,
          'ds' : 8,
          'nud' : 4,
          'caloDesign' : 3,
          'strawDesign' : 10
     }
}
default = '2023'

inactivateMuonProcesses = False   # provisionally for making studies of various muon background sources

parser = ArgumentParser()
group = parser.add_mutually_exclusive_group()
parser.add_argument("--evtcalc", help="Use EventCalc", action="store_true")
parser.add_argument("--Pythia6", dest="pythia6", help="Use Pythia6", required=False, action="store_true")
parser.add_argument("--Pythia8", dest="pythia8", help="Use Pythia8", required=False, action="store_true")
parser.add_argument("--PG",      dest="pg",      help="Use Particle Gun", required=False, action="store_true")
parser.add_argument("--pID",     dest="pID",     help="id of particle used by the gun (default=22)", required=False, default=22, type=int)
parser.add_argument("--Estart", help="start of energy range of particle gun (default=10 GeV)", default=10, type=float)
parser.add_argument("--Eend", help="end of energy range of particle gun (default=10 GeV)", default=10, type=float)
parser.add_argument("-A",        dest="A",       help="b: signal from b, c: from c (default), bc: from Bc, or inclusive", required=False, default='c')
parser.add_argument("--Genie",   dest="genie",   help="Genie for reading and processing neutrino interactions", required=False, action="store_true")
parser.add_argument("--NuRadio", dest="nuradio", help="misuse GenieGenerator for neutrino radiography and geometry timing test", required=False, action="store_true")
parser.add_argument("--Ntuple",  dest="ntuple",  help="Use ntuple as input", required=False, action="store_true")
parser.add_argument("--MuonBack",dest="muonback",  help="Generate events from muon background file, --Cosmics=0 for cosmic generator data", required=False, action="store_true")
parser.add_argument("--FollowMuon",dest="followMuon", help="Make muonshield active to follow muons", required=False, action="store_true")
parser.add_argument("--FastMuon",  dest="fastMuon",  help="Only transport muons for a fast muon only background estimate", required=False, action="store_true")
parser.add_argument("--Nuage",     dest="nuage",  help="Use Nuage, neutrino generator of OPERA", required=False, action="store_true")
parser.add_argument("--phiRandom", dest="phiRandom",  help="only relevant for muon background generator, random phi", required=False, action="store_true")
parser.add_argument("--Cosmics",   dest="cosmics",  help="Use cosmic generator, argument switch for cosmic generator 0 or 1", required=False,  default=None)
parser.add_argument("--MuDIS",     dest="mudis",  help="Use muon deep inelastic scattering generator", required=False, action="store_true")
parser.add_argument("--RpvSusy", dest="RPVSUSY",  help="Generate events based on RPV neutralino", required=False, action="store_true")
parser.add_argument("--DarkPhoton", dest="DarkPhoton",  help="Generate dark photons", required=False, action="store_true")
parser.add_argument("--SusyBench", dest="RPVSUSYbench",  help="Generate HP Susy", required=False, default=2)
parser.add_argument("-m", "--mass", dest="theMass",  help="Mass of hidden particle, default "+str(theHNLMass)+"GeV for HNL, "+str(theDPmass)+"GeV for DP", required=False, default=None, type=float)
parser.add_argument("-c", "--couplings", "--coupling", dest="thecouplings",  help="couplings \'U2e,U2mu,U2tau\' or -c \'U2e,U2mu,U2tau\' to set list of HNL couplings.\
 TP default for HNL, ctau=53.3km", required=False,default="0.447e-9,7.15e-9,1.88e-9")
parser.add_argument("-cp", "--production-couplings", dest="theprodcouplings",  help="production couplings \'U2e,U2mu,U2tau\' to set the couplings for HNL production only"\
                                            ,required=False,default=None)
parser.add_argument("-cd", "--decay-couplings", dest="thedeccouplings",  help="decay couplings  \'U2e,U2mu,U2tau\' to set the couplings for HNL decay only", required=False,default=None)
parser.add_argument("-e", "--epsilon", dest="theDPepsilon",  help="to set mixing parameter epsilon", required=False,default=0.00000008, type=float)
parser.add_argument("-n", "--nEvents",dest="nEvents",  help="Number of events to generate", required=False,  default=100, type=int)
parser.add_argument("-i", "--firstEvent",dest="firstEvent",  help="First event of input file to use", required=False,  default=0, type=int)
parser.add_argument("-s", "--seed",dest="theSeed",  help="Seed for random number. Only for experts, see TRrandom::SetSeed documentation", required=False,  default=0, type=int)
parser.add_argument("-S", "--sameSeed",dest="sameSeed",  help="can be set to an integer for the muonBackground simulation with specific seed for each muon, only for experts!"\
                                            ,required=False,  default=False, type=int)
group.add_argument("-f",        dest="inputFile",       help="Input file if not default file", required=False, default=False)
parser.add_argument("-g",        dest="geofile",       help="geofile for muon shield geometry, for experts only", required=False, default=None)
parser.add_argument("-o", "--output",dest="outputDir",  help="Output directory", required=False,  default=".")
parser.add_argument("-Y",        dest="dy",  help="max height of vacuum tank", required=False, default=globalDesigns[default]['dy'])
parser.add_argument("--tankDesign", dest="dv",      help="4=TP elliptical tank design, 5 = optimized conical rectangular design, 6=5 without segment-1"\
                                            ,required=False, default=globalDesigns[default]['dv'], type=int)
parser.add_argument("--muShieldDesign", dest="ds",  help="7=short magnet design, 9=optimised with T4 as constraint, 8=requires config file\
                                            ,10=with field map for hadron absorber", required=False, choices=range(7,11), default=globalDesigns[default]['ds'], type=int)
parser.add_argument("--nuTauTargetDesign", dest="nud"\
  ,help="0=TP, 1=new magnet option for short muon shield, 2= no magnet surrounding neutrino detector, 3= emulsion spectrometer and muon filter as in CDS, 4= not magnetized target and muon spectrometer for ECN3",required=False, default=globalDesigns[default]['nud'], type=int)
parser.add_argument("--caloDesign",
                    help="0=ECAL/HCAL TP 2=splitCal  3=ECAL/ passive HCAL",
                    default=globalDesigns[default]['caloDesign'],
                    type=int,
                    choices=[0,2,3])
parser.add_argument("--strawDesign", dest="strawDesign", help="simplistic tracker design,  4=sophisticated straw tube design, horizontal wires (default), 10=2cm straw"
                                            ,required=False, default=globalDesigns[default]['strawDesign'], type=int)
parser.add_argument("-F",        dest="deepCopy",  help="default = False: copy only stable particles to stack, except for HNL events", required=False, action="store_true")
parser.add_argument("-t", "--test", dest="testFlag",  help="quick test", required=False,action="store_true")
parser.add_argument("--dry-run", dest="dryrun",  help="stop after initialize", required=False,action="store_true")
parser.add_argument("-D", "--display", dest="eventDisplay", help="store trajectories", required=False, action="store_true")
parser.add_argument("--stepMuonShield", dest="muShieldStepGeo", help="activate steps geometry for the muon shield", required=False, action="store_true", default=False)
parser.add_argument("--coMuonShield", dest="muShieldWithCobaltMagnet", help="replace one of the magnets in the shield with 2.2T cobalt one, downscales other fields, works only for muShieldDesign >2", required=False, type=int, default=0)
parser.add_argument("--noSC", dest="SC_mag", help="Deactivate SC muon shield. Configuration: 1 SC magnet (3*B_warm) + 3 warm magnets with inverted fields", action='store_false')
parser.add_argument("--scName", help="The name of the SC shield in the database", default="sc_v6")
parser.add_argument("--MesonMother",   dest="MM",  help="Choose DP production meson source", required=False,  default=True)
parser.add_argument("--debug",  help="1: print weights and field 2: make overlap check", required=False, default=0, type=int, choices=range(0,3))
parser.add_argument(
    "--helium",
    dest="decayVolMed", 
    help="Set Decay Volume medium to helium. NOOP, as default is helium",
    action="store_const",
    const="helium",
    default="helium"
)
parser.add_argument(
    "--vacuums",
    dest="decayVolMed",
    help="Set Decay Volume medium to vacuum(vessel structure changes)",
    action="store_const",
    const="vacuums",
    default="helium"
)
parser.add_argument("--SND", dest="SND", help="Activate SND.", action='store_true')
parser.add_argument("--noSND", dest="SND", help="Deactivate SND. NOOP, as it currently defaults to off.", action='store_false')

options = parser.parse_args()

if options.evtcalc:  simEngine = "EvtCalc"
if options.pythia6:  simEngine = "Pythia6"
if options.pythia8:  simEngine = "Pythia8"
if options.pg:       simEngine = "PG"
if options.genie:    simEngine = "Genie"
if options.nuradio:  simEngine = "nuRadiography"
if options.ntuple:   simEngine = "Ntuple"
if options.muonback: simEngine = "MuonBack"
if options.nuage:    simEngine = "Nuage"
if options.mudis:    simEngine = "muonDIS"
if options.A != 'c':
     inclusive = options.A
     if options.A =='b': inputFile = "/eos/experiment/ship/data/Beauty/Cascade-run0-19-parp16-MSTP82-1-MSEL5-5338Bpot.root"
     if options.A.lower() == 'charmonly':
           charmonly = True
           HNL = False
     if options.A not in ['b','c','bc','meson','pbrem','qcd']: inclusive = True
if options.MM:
     motherMode=options.MM
if options.cosmics:
     simEngine = "Cosmics"
     Opt_high = int(options.cosmics)
if options.inputFile:
  if options.inputFile == "none": options.inputFile = None
  inputFile = options.inputFile
  defaultInputFile = False
if options.RPVSUSY: HNL = False
if options.DarkPhoton: HNL = False
if not options.theMass:
  if options.DarkPhoton: options.theMass  = theDPmass
  else:                  options.theMass  = theHNLMass
if options.thecouplings:
  theCouplings = [float(c) for c in options.thecouplings.split(",")]
if options.theprodcouplings:
  theProductionCouplings = [float(c) for c in options.theprodcouplings.split(",")]
if options.thedeccouplings:
  theDecayCouplings = [float(c) for c in options.thedeccouplings.split(",")]
if options.testFlag:
  inputFile = "$FAIRSHIP/files/Cascade-parp16-MSTP82-1-MSEL4-76Mpot_1_5000.root"


#sanity check
if (HNL and options.RPVSUSY) or (HNL and options.DarkPhoton) or (options.DarkPhoton and options.RPVSUSY):
 print("cannot have HNL and SUSY or DP at the same time, abort")
 sys.exit(2)

if (simEngine == "Genie" or simEngine == "nuRadiography") and defaultInputFile:
  inputFile = "/eos/experiment/ship/data/GenieEvents/genie-nu_mu.root"
            # "/eos/experiment/ship/data/GenieEvents/genie-nu_mu_bar.root"
if simEngine == "muonDIS" and defaultInputFile:
  print('input file required if simEngine = muonDIS')
  print(" for example -f  /eos/experiment/ship/data/muonDIS/muonDis_1.root")
  sys.exit()
if simEngine == "Nuage" and not inputFile:
 inputFile = 'Numucc.root'

print("FairShip setup for",simEngine,"to produce",options.nEvents,"events")
if (simEngine == "Ntuple" or simEngine == "MuonBack") and defaultInputFile :
  print('input file required if simEngine = Ntuple or MuonBack')
  print(" for example -f /eos/experiment/ship/data/Mbias/pythia8_Geant4-withCharm_onlyMuons_4magTarget.root")
  sys.exit()
ROOT.gRandom.SetSeed(options.theSeed)  # this should be propagated via ROOT to Pythia8 and Geant4VMC
shipRoot_conf.configure(0)     # load basic libraries, prepare atexit for python
# - muShieldDesign = 7  # 7 = short design+magnetized hadron absorber
# - targetOpt      = 5  # 0=solid   >0 sliced, 5: 5 pieces of tungsten, 4 H20 slits, 17: Mo + W +H2O (default)
#   nuTauTargetDesign = 0 # 0 = TP, 1 = NEW with magnet, 2 = NEW without magnet, 3 = 2018 design
ship_geo = ConfigRegistry.loadpy(
     "$FAIRSHIP/geometry/geometry_config.py",
     Yheight=options.dy,
     tankDesign=options.dv,
     muShieldDesign=options.ds,
     nuTauTargetDesign=options.nud,
     CaloDesign=options.caloDesign,
     strawDesign=options.strawDesign,
     muShieldGeo=options.geofile,
     muShieldStepGeo=options.muShieldStepGeo,
     muShieldWithCobaltMagnet=options.muShieldWithCobaltMagnet,
     SC_mag=options.SC_mag,
     scName=options.scName,
     DecayVolumeMedium=options.decayVolMed,
     SND=options.SND,
)

# Output file name, add dy to be able to setup geometry with ambiguities.
if simEngine == "PG": tag = simEngine + "_"+str(options.pID)+"-"+mcEngine
else: tag = simEngine+"-"+mcEngine
if charmonly: tag = simEngine+"CharmOnly-"+mcEngine
if options.eventDisplay: tag = tag+'_D'
if options.dv > 4 : tag = 'conical.'+tag
if not os.path.exists(options.outputDir):
  os.makedirs(options.outputDir)
outFile = "%s/ship.%s.root" % (options.outputDir, tag)

# rm older files !!!
for x in os.listdir(options.outputDir):
  if not x.find(tag)<0: os.system("rm %s/%s" % (options.outputDir, x) )
# Parameter file name
parFile="%s/ship.params.%s.root" % (options.outputDir, tag)

# In general, the following parts need not be touched
# ========================================================================

# -----Timer--------------------------------------------------------
timer = ROOT.TStopwatch()
timer.Start()
# ------------------------------------------------------------------------
# -----Create simulation run----------------------------------------
run = ROOT.FairRunSim()
run.SetName(mcEngine)  # Transport engine
run.SetSink(ROOT.FairRootFileSink(outFile))  # Output file
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
 if HNL or options.RPVSUSY:
  P8gen = ROOT.HNLPythia8Generator()
  import pythia8_conf
  if HNL:
   print('Generating HNL events of mass %.3f GeV'%options.theMass)
   if theProductionCouplings is None and theDecayCouplings is None:
    print('and with couplings=',theCouplings)
    theProductionCouplings = theDecayCouplings = theCouplings
   elif theProductionCouplings is not None and theDecayCouplings is not None:
    print('and with couplings',theProductionCouplings,'at production')
    print('and',theDecayCouplings,'at decay')
   else:
    raise ValueError('Either both production and decay couplings must be specified, or neither.')
   pythia8_conf.configure(P8gen,options.theMass,theProductionCouplings,theDecayCouplings,inclusive,options.deepCopy)
  if options.RPVSUSY:
   print('Generating RPVSUSY events of mass %.3f GeV'%theHNLMass)
   print('and with couplings=[%.3f,%.3f]'%(theCouplings[0],theCouplings[1]))
   print('and with stop mass=%.3f GeV\n'%theCouplings[2])
   pythia8_conf.configurerpvsusy(P8gen,options.theMass,[theCouplings[0],theCouplings[1]],
                                theCouplings[2],options.RPVSUSYbench,inclusive,options.deepCopy)
  P8gen.SetParameters("ProcessLevel:all = off")
  if inputFile:
   ut.checkFileExists(inputFile)
# read from external file
   P8gen.UseExternalFile(inputFile, options.firstEvent)
 if options.DarkPhoton:
  P8gen = ROOT.DPPythia8Generator()
  if inclusive=='qcd':
   P8gen.SetDPId(4900023)
  else:
   P8gen.SetDPId(9900015)
  import pythia8darkphoton_conf
  passDPconf = pythia8darkphoton_conf.configure(P8gen,options.theMass,options.theDPepsilon,inclusive, motherMode, options.deepCopy)
  if (passDPconf!=1): sys.exit()
 if HNL or options.RPVSUSY or options.DarkPhoton:
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
  P8gen.UseExternalFile(inputFile, options.firstEvent)
  P8gen.SetTarget("volTarget_1",0.,0.) # will distribute PV inside target, beam offset x=y=0.
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

# -----EvtCalc--------------------------------------
if simEngine == "EvtCalc":
    primGen.SetTarget(0.0, 0.0)
    print(f"Opening input file for EvtCalc generator: {inputFile}")
    ut.checkFileExists(inputFile)
    EvtCalcGen = ROOT.EvtCalcGenerator()
    EvtCalcGen.Init(inputFile, options.firstEvent)
    EvtCalcGen.SetPositions(zTa=ship_geo.target.z, zDV=ship_geo.decayVolume.z)
    primGen.AddGenerator(EvtCalcGen)
    options.nEvents = min(options.nEvents, EvtCalcGen.GetNevents())
    print(
        f"Generate {options.nEvents} with EvtCalc input. First event: {options.firstEvent}"
    )

# -----Particle Gun-----------------------
if simEngine == "PG":
  myPgun = ROOT.FairBoxGenerator(options.pID,1)
  myPgun.SetPRange(options.Estart,options.Eend)
  myPgun.SetPhiRange(0, 360) # // Azimuth angle range [degree]
  myPgun.SetXYZ(0.*u.cm, 0.*u.cm, 0.*u.cm)
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
 print('MuDIS position info input=',mu_start, mu_end)
 DISgen.SetPositions(mu_start, mu_end)
 DISgen.Init(inputFile,options.firstEvent)
 primGen.AddGenerator(DISgen)
 options.nEvents = min(options.nEvents,DISgen.GetNevents())
 inactivateMuonProcesses = True # avoid unwanted hadronic events of "incoming" muon flying backward
 print('Generate ',options.nEvents,' with DIS input', ' first event',options.firstEvent)
# -----neutrino interactions from nuage------------------------
if simEngine == "Nuage":
 primGen.SetTarget(0., 0.)
 Nuagegen = ROOT.NuageGenerator()
 Nuagegen.EnableExternalDecayer(1) #with 0 external decayer is disable, 1 is enabled
 print('Nuage position info input=',ship_geo.EmuMagnet.zC-ship_geo.NuTauTarget.zdim, ship_geo.EmuMagnet.zC+ship_geo.NuTauTarget.zdim)
 #--------------------------------
 #to Generate neutrino interactions in the whole neutrino target
# Nuagegen.SetPositions(ship_geo.EmuMagnet.zC, ship_geo.NuTauTarget.zC-ship_geo.NuTauTarget.zdim/2, ship_geo.NuTauTarget.zC+ship_geo.NuTauTarget.zdim/2, -ship_geo.NuTauTarget.xdim/2, ship_geo.NuTauTarget.xdim/2, -ship_geo.NuTauTarget.ydim/2, ship_geo.NuTauTarget.ydim/2)
 #--------------------------------
 #to Generate neutrino interactions ONLY in ONE brick
 ntt = 6
 nXcells = 7
 nYcells = 3
 nZcells = ntt -1
 startx = -ship_geo.NuTauTarget.xdim/2. + nXcells*ship_geo.NuTauTarget.BrX
 endx = -ship_geo.NuTauTarget.xdim/2. + (nXcells+1)*ship_geo.NuTauTarget.BrX
 starty = -ship_geo.NuTauTarget.ydim/2. + nYcells*ship_geo.NuTauTarget.BrY
 endy = - ship_geo.NuTauTarget.ydim/2. + (nYcells+1)*ship_geo.NuTauTarget.BrY
 startz = ship_geo.EmuMagnet.zC - ship_geo.NuTauTarget.zdim/2. + ntt *ship_geo.NuTauTT.TTZ + nZcells * ship_geo.NuTauTarget.CellW
 endz = ship_geo.EmuMagnet.zC - ship_geo.NuTauTarget.zdim/2. + ntt *ship_geo.NuTauTT.TTZ + nZcells * ship_geo.NuTauTarget.CellW + ship_geo.NuTauTarget.BrZ
 Nuagegen.SetPositions(ship_geo.target.z0, startz, endz, startx, endx, starty, endy)
 #--------------------------------
 ut.checkFileExists(inputFile)
 Nuagegen.Init(inputFile,options.firstEvent)
 primGen.AddGenerator(Nuagegen)
 options.nEvents = min(options.nEvents,Nuagegen.GetNevents())
 run.SetPythiaDecayer("DecayConfigNuAge.C")
 print('Generate ',options.nEvents,' with Nuage input', ' first event',options.firstEvent)
# -----Neutrino Background------------------------
if simEngine == "Genie":
# Genie
 ut.checkFileExists(inputFile)
 primGen.SetTarget(0., 0.) # do not interfere with GenieGenerator
 Geniegen = ROOT.GenieGenerator()
 Geniegen.Init(inputFile,options.firstEvent)
 Geniegen.SetPositions(ship_geo.target.z0, ship_geo.tauMudet.zMudetC-5*u.m, ship_geo.TrackStation2.z)
 primGen.AddGenerator(Geniegen)
 options.nEvents = min(options.nEvents,Geniegen.GetNevents())
 run.SetPythiaDecayer("DecayConfigNuAge.C")
 print('Generate ',options.nEvents,' with Genie input', ' first event',options.firstEvent)
if simEngine == "nuRadiography":
 ut.checkFileExists(inputFile)
 primGen.SetTarget(0., 0.) # do not interfere with GenieGenerator
 Geniegen = ROOT.GenieGenerator()
 Geniegen.Init(inputFile,options.firstEvent)
 # Geniegen.SetPositions(ship_geo.target.z0, ship_geo.target.z0, ship_geo.MuonStation3.z)
 Geniegen.SetPositions(ship_geo.target.z0, ship_geo.tauMudet.zMudetC, ship_geo.MuonStation3.z)
 Geniegen.NuOnly()
 primGen.AddGenerator(Geniegen)
 print('Generate ',options.nEvents,' for nuRadiography', ' first event',options.firstEvent)
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
 Ntuplegen.Init(inputFile,options.firstEvent)
 primGen.AddGenerator(Ntuplegen)
 options.nEvents = min(options.nEvents,Ntuplegen.GetNevents())
 print('Process ',options.nEvents,' from input file')
#
if simEngine == "MuonBack":
# reading muon tracks from previous Pythia8/Geant4 simulation with charm replaced by cascade production
 fileType = ut.checkFileExists(inputFile)
 if fileType == 'tree':
 # 2018 background production
  primGen.SetTarget(ship_geo.target.z0+70.845*u.m,0.)
 else:
  primGen.SetTarget(ship_geo.target.z0+50*u.m,0.)
 #
 MuonBackgen = ROOT.MuonBackGenerator()
 # MuonBackgen.FollowAllParticles() # will follow all particles after hadron absorber, not only muons
 MuonBackgen.Init(inputFile,options.firstEvent,options.phiRandom)
 MuonBackgen.SetSmearBeam(5 * u.cm) # radius of ring, thickness 8mm
 if DownScaleDiMuon:
    if inputFile[0:4] == "/eos": test = os.environ["EOSSHIP"]+inputFile
    else: test = inputFile
    testf = ROOT.TFile.Open(test)
    if not testf.FileHeader.GetTitle().find('diMu100.0')<0:
        MuonBackgen.SetDownScaleDiMuon()   # avoid interference with boosted channels
        print("MuonBackgenerator: set downscale for dimuon on")
    testf.Close()
 if options.sameSeed: MuonBackgen.SetSameSeed(options.sameSeed)
 primGen.AddGenerator(MuonBackgen)
 options.nEvents = min(options.nEvents,MuonBackgen.GetNevents())
 MCTracksWithHitsOnly = True # otherwise, output file becomes too big
 print('Process ',options.nEvents,' from input file, with Phi random=',options.phiRandom, ' with MCTracksWithHitsOnly',MCTracksWithHitsOnly)
 if options.followMuon :
    options.fastMuon = True
    modules['Veto'].SetFollowMuon()
 if options.fastMuon :    modules['Veto'].SetFastMuon()

 # optional, boost gamma2muon conversion
 # ROOT.kShipMuonsCrossSectionFactor = 100.
#
if simEngine == "Cosmics":
 primGen.SetTarget(0., 0.)
 Cosmicsgen = ROOT.CosmicsGenerator()
 import CMBG_conf
 CMBG_conf.configure(Cosmicsgen, ship_geo)
 if not Cosmicsgen.Init(Opt_high):
      print("initialization of cosmic background generator failed ",Opt_high)
      sys.exit(0)
 Cosmicsgen.n_EVENTS = options.nEvents
 primGen.AddGenerator(Cosmicsgen)
 print('Process ',options.nEvents,' Cosmic events with option ',Opt_high)
#
run.SetGenerator(primGen)
# ------------------------------------------------------------------------

#---Store the visualiztion info of the tracks, this make the output file very large!!
#--- Use it only to display but not for production!
if options.eventDisplay: run.SetStoreTraj(ROOT.kTRUE)
else:            run.SetStoreTraj(ROOT.kFALSE)
# -----Initialize simulation run------------------------------------
run.Init()
if options.dryrun: # Early stop after setting up Pythia 8
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
elif options.deepCopy:
 fStack.SetMinPoints(0)
 fStack.SetEnergyCut(0.*u.MeV)

if options.eventDisplay:
 # Set cuts for storing the trajectories, can only be done after initialization of run (?!)
  trajFilter = ROOT.FairTrajFilter.Instance()
  trajFilter.SetStepSizeCut(1*u.mm)
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
if hasattr(ship_geo.Bfield,"fieldMap"):
      fieldMaker = geomGeant4.addVMCFields(ship_geo, '', True)

# Print VMC fields and associated geometry objects
if options.debug == 1:
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
run.Run(options.nEvents)
# -----Runtime database---------------------------------------------
kParameterMerged = ROOT.kTRUE
parOut = ROOT.FairParRootFileIo(kParameterMerged)
parOut.open(parFile)
rtdb.setOutput(parOut)
rtdb.saveOutput()
rtdb.printParamContexts()
getattr(rtdb,"print")()
# ------------------------------------------------------------------------
run.CreateGeometryFile("%s/geofile_full.%s.root" % (options.outputDir, tag))
# save ShipGeo dictionary in geofile
import saveBasicParameters
saveBasicParameters.execute("%s/geofile_full.%s.root" % (options.outputDir, tag),ship_geo)

# checking for overlaps
if options.debug == 2:
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
print(' ')
print("Macro finished succesfully.")
if "P8gen" in globals() :
    if (HNL): print("number of retries, events without HNL ",P8gen.nrOfRetries())
    elif (options.DarkPhoton):
        print("number of retries, events without Dark Photons ",P8gen.nrOfRetries())
        print("total number of dark photons (including multiple meson decays per single collision) ",P8gen.nrOfDP())

print("Output file is ",  outFile)
print("Parameter file is ",parFile)
print("Real time ",rtime, " s, CPU time ",ctime,"s")

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
 fSink = ROOT.FairRootFileSink(fout)

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

 branches = ROOT.TList()
 branches.SetName('BranchList')
 branches.Add(ROOT.TObjString('MCTrack'))
 branches.Add(ROOT.TObjString('vetoPoint'))
 branches.Add(ROOT.TObjString('ShipRpcPoint'))
 branches.Add(ROOT.TObjString('TargetPoint'))
 branches.Add(ROOT.TObjString('TTPoint'))
 branches.Add(ROOT.TObjString('ScoringPoint'))
 branches.Add(ROOT.TObjString('strawtubesPoint'))
 branches.Add(ROOT.TObjString('EcalPoint'))
 branches.Add(ROOT.TObjString('sEcalPointLite'))
 branches.Add(ROOT.TObjString('smuonPoint'))
 branches.Add(ROOT.TObjString('TimeDetPoint'))
 branches.Add(ROOT.TObjString('MCEventHeader'))
 branches.Add(ROOT.TObjString('sGeoTracks'))

 sTree.AutoSave()
 fSink.WriteObject(branches, "BranchList", ROOT.TObject.kSingleKey)
 fSink.SetOutTree(sTree)

 fout.Close()
 print("removed empty events, left with:", nEvents)
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
