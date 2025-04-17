




#### Cosmics
simEngine = "Cosmics"
     Opt_high = int(options.cosmics)

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
     
     
if (simEngine == "Genie" or simEngine == "nuRadiography") and defaultInputFile:
  inputFile = "/eos/experiment/ship/data/GenieEvents/genie-nu_mu.root"


if simEngine == "muonDIS" and defaultInputFile:
  print('input file required if simEngine = muonDIS')
  print(" for example -f  /eos/experiment/ship/data/muonDIS/muonDis_1.root")
  sys.exit()


if simEngine == "Nuage" and not inputFile:
 inputFile = 'Numucc.root'


if (simEngine == "Ntuple" or simEngine == "MuonBack") and defaultInputFile :
  print('input file required if simEngine = Ntuple or MuonBack')
  print(" for example -f /eos/experiment/ship/data/Mbias/pythia8_Geant4-withCharm_onlyMuons_4magTarget.root")
  sys.exit()

#### MuonBack
DownScaleDiMuon = False
MCTracksWithHitsOnly   = False  # copy particles which produced a hit and their history
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
    testf = ROOT.TFile.Open(inputFile)
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

  

  #### HNL, RPVsusy, DP
# Default HNL parameters
theHNLMass   = 1.0*u.GeV
theProductionCouplings = theDecayCouplings = None

# Default dark photon parameters
theDPmass    = 0.2*u.GeV
  inclusive    = "c"    # True = all processes if "c" only ccbar -> HNL, if "b" only bbar -> HNL, if "bc" only Bc+/Bc- -> HNL, and for darkphotons: if meson = production through meson decays, pbrem = proton bremstrahlung, qcd = ffbar -> DP.
charmonly    = False  # option to be set with -A to enable only charm decays, charm x-sec measurement
HNL          = True
if options.A != 'c':
     inclusive = options.A
     if options.A =='b': inputFile = "/eos/experiment/ship/data/Beauty/Cascade-run0-19-parp16-MSTP82-1-MSEL5-5338Bpot.root"
     if options.A.lower() == 'charmonly':
           charmonly = True
           HNL = False
     if options.A not in ['b','c','bc','meson','pbrem','qcd']: inclusive = True

if options.MM:
     motherMode=options.MM

     if not options.theMass:
  if options.DarkPhoton: options.theMass  = theDPmass
  else:                  options.theMass  = theHNLMass
if options.thecouplings:
  theCouplings = [float(c) for c in options.thecouplings.split(",")]
if options.theprodcouplings:
  theProductionCouplings = [float(c) for c in options.theprodcouplings.split(",")]
if options.thedeccouplings:
  theDecayCouplings = [float(c) for c in options.thedeccouplings.split(",")]


  
SetPrimGen():

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
  primGen.SetTarget(0., 0.) #vertex is set in pythia8Generator
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
 print('Generate ',options.nEvents,' with DIS input', ' first event',options.firstEvent)

# -----neutrino interactions from nuage------------------------
if simEngine == "Nuage":
 primGen.SetTarget(0., 0.)
 Nuagegen = ROOT.NuageGenerator()
 Nuagegen.EnableExternalDecayer(1) #with 0 external decayer is disable, 1 is enabled

 #CAMM - This is broken now, need info from dedicated SND geo...
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
 #-CAMM end broken part
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
    testf = ROOT.TFile.Open(inputFile)
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
  
