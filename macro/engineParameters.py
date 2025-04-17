#!/usr/bin/env python
import os
import sys
import ROOT

import shipunit as u
import rootUtils as ut
import yaml



def SetPrimGen(primGen,options,ship_geo,modules):

 with open(options.yaml_file) as file:
  config = yaml.safe_load(file)

 #### Cosmics
 if options.simEngine == "Cosmics":
  cosmics = AttrDict(config['Cosmics'])
  primGen.SetTarget(0., 0.)
  Cosmicsgen = ROOT.CosmicsGenerator()
  import CMBG_conf
  CMBG_conf.configure(Cosmicsgen, ship_geo)
  if not Cosmicsgen.Init(cosmics.opt):
   print("initialization of cosmic background generator failed ",cosmics.opt)
   sys.exit(0)
  Cosmicsgen.n_EVENTS = options.nEvents
  primGen.AddGenerator(Cosmicsgen)
  print('Process ',options.nEvents,' Cosmic events with option ',cosmics.opt)
  #

 #####Genie
 # -----Neutrino Background------------------------
 if options.simEngine == "Genie":
  genie = AttrDict(config['Genie'])
  # Genie
  ut.checkFileExists(genie.inputFile)
  primGen.SetTarget(0., 0.) # do not interfere with GenieGenerator
  Geniegen = ROOT.GenieGenerator()
  Geniegen.Init(genie.inputFile,options.firstEvent)
  Geniegen.SetPositions(ship_geo.target.z0, ship_geo.tauMudet.zMudetC-5*u.m, ship_geo.TrackStation2.z)
  primGen.AddGenerator(Geniegen)
  options.nEvents = min(options.nEvents,Geniegen.GetNevents())
  run.SetPythiaDecayer("DecayConfigNuAge.C")
  print('Generate ',options.nEvents,' with Genie input', ' first event',options.firstEvent)

 ##### nuRadiography

 if options.simEngine == "nuRadiography":
  nuRad = AttrDict(config['NuRadio'])
  ut.checkFileExists(nuRad.inputFile)
  primGen.SetTarget(0., 0.) # do not interfere with GenieGenerator
  Geniegen = ROOT.GenieGenerator()
  Geniegen.Init(nuRad.inputFile,options.firstEvent)
  # Geniegen.SetPositions(ship_geo.target.z0, ship_geo.target.z0, ship_geo.MuonStation3.z)
  Geniegen.SetPositions(ship_geo.target.z0, ship_geo.tauMudet.zMudetC, ship_geo.MuonStation3.z)
  Geniegen.NuOnly()
  primGen.AddGenerator(Geniegen)
  print('Generate ',options.nEvents,' for nuRadiography', ' first event',options.firstEvent)

 #####muonDIS
 if options.simEngine == "muonDIS":
  muDIS = AttrDict(config['MuonDIS'])
  ut.checkFileExists(muDIS.inputFile)
  primGen.SetTarget(0., 0.)
  DISgen = ROOT.MuDISGenerator()
  # from nu_tau detector to tracking station 2
  # mu_start, mu_end =  ship_geo.tauMudet.zMudetC,ship_geo.TrackStation2.z
  #
  # in front of UVT up to tracking station 1
  mu_start, mu_end = ship_geo.Chamber1.z-ship_geo.chambers.Tub1length-10.*u.cm,ship_geo.TrackStation1.z
  print('MuDIS position info input=',mu_start, mu_end)
  DISgen.SetPositions(mu_start, mu_end)
  DISgen.Init(muDIS.inputFile,options.firstEvent)
  primGen.AddGenerator(DISgen)
  options.nEvents = min(options.nEvents,DISgen.GetNevents())
  print('Generate ',options.nEvents,' with DIS input', ' first event',options.firstEvent)

 ######Nuage
 # -----neutrino interactions from nuage------------------------
 if options.simEngine == "Nuage":
  nuage = AttrDict(config['Nuage'])
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
  ut.checkFileExists(nuage.inputFile)
  Nuagegen.Init(nuage.inputFile,options.firstEvent)
  primGen.AddGenerator(Nuagegen)
  options.nEvents = min(options.nEvents,Nuagegen.GetNevents())
  print('Generate ',options.nEvents,' with Nuage input', ' first event',options.firstEvent)
  #-CAMM end broken part

 ######Ntuple

 if options.simEngine == "Ntuple":
  ntuple = AttrDict(config['Ntuple'])
  # reading previously processed muon events, [-50m - 50m]
  ut.checkFileExists(ntuple.inputFile)
  primGen.SetTarget(ship_geo.target.z0+50*u.m,0.)
  Ntuplegen = ROOT.NtupleGenerator()
  Ntuplegen.Init(ntuple.inputFile,options.firstEvent)
  primGen.AddGenerator(Ntuplegen)
  options.nEvents = min(options.nEvents,Ntuplegen.GetNevents())
  print('Process ',options.nEvents,' from input file')
  #

 #### MuonBack
 if options.simEngine == "MuonBack":
  # reading muon tracks from previous Pythia8/Geant4 simulation with charm replaced by cascade production
  muBkg = AttrDict(config['MuonBack'])
  fileType = ut.checkFileExists(muBkg.inputFile)
  if fileType == 'tree':
   # 2018 background production
   primGen.SetTarget(ship_geo.target.z0+70.845*u.m,0.)
  else:
   primGen.SetTarget(ship_geo.target.z0+50*u.m,0.)
   #
  MuonBackgen = ROOT.MuonBackGenerator()
  # MuonBackgen.FollowAllParticles() # will follow all particles after hadron absorber, not only muons
  MuonBackgen.Init(muBkg.inputFile,options.firstEvent,muBkg.phiRandom)
  MuonBackgen.SetSmearBeam(5 * u.cm) # radius of ring, thickness 8mm
  if muBkg.DownScaleDiMuon:
   testf = ROOT.TFile.Open(muBkg.inputFile)
   if not testf.FileHeader.GetTitle().find('diMu100.0')<0:
    MuonBackgen.SetDownScaleDiMuon()   # avoid interference with boosted channels
    print("MuonBackgenerator: set downscale for dimuon on")
   testf.Close()
  if muBkg.sameSeed: MuonBackgen.SetSameSeed(muBkg.sameSeed)
  primGen.AddGenerator(MuonBackgen)
  options.nEvents = min(options.nEvents,MuonBackgen.GetNevents())
  print('Process ',options.nEvents,' from input file, with Phi random=',options.phiRandom, ' with MCTracksWithHitsOnly True')
  if muBkg.followMuon :
   muBkg.fastMuon = True
   modules['Veto'].SetFollowMuon()
  if muBkg.fastMuon :
   modules['Veto'].SetFastMuon()

 #### Pythia8
 if options.simEngine == "Pythia8":
  p8dict = AttrDict(config['Pythia8'])
  primGen.SetTarget(ship_geo.target.z0, 0.)
  # -----Pythia8--------------------------------------
  if p8dict.HNL or p8dict.RPVSUSY:
   P8gen = ROOT.HNLPythia8Generator()
   import pythia8_conf
   if p8dict.HNL:
    print('Generating HNL events of mass %.3f GeV'%p8dict.theMass)
    pythia8_conf.configure(P8gen,p8dict.theMass,p8dict.theProductionCouplings,p8dict.theDecayCouplings,p8dict.inclusive,options.deepCopy)
   if p8dict.RPVSUSY:
    print('Generating RPVSUSY events of mass %.3f GeV'%(theMass*u.GeV))
    print('and with couplings=[%.3f,%.3f]'%(p8dict.theRPVCouplings[0],p8dict.theRPVCouplings[1]))
    print('and with stop mass=%.3f GeV\n'%p8dict.theRPVCouplings[2])
    pythia8_conf.configurerpvsusy(P8gen,p8dict.theMass,[p8dict.theRPVCouplings[0],p8dict.theRPVCouplings[1]],
                                  p8dict.theRPVCouplings[2],p8dict.RPVSUSYbench,p8dict.inclusive,options.deepCopy)
    P8gen.SetParameters("ProcessLevel:all = off")
   if p8dict.inputFile:
    ut.checkFileExists(p8dict.inputFile)
    # read from external file
    P8gen.UseExternalFile(p8dict.inputFile, options.firstEvent)
  if p8dict.DarkPhoton:
   P8gen = ROOT.DPPythia8Generator()
   if inclusive=='qcd':
    P8gen.SetDPId(4900023)
   else:
    P8gen.SetDPId(9900015)
   import pythia8darkphoton_conf
   passDPconf = pythia8darkphoton_conf.configure(P8gen,p8dict.theMass,p8dict.theDPepsilon,p8dict.inclusive, p8dict.motherMode, options.deepCopy)
   if (passDPconf!=1): sys.exit()
  if p8dict.HNL or p8dict.RPVSUSY or p8dict.DarkPhoton:
   P8gen.SetSmearBeam(1*u.cm) # finite beam size
   P8gen.SetLmin((ship_geo.Chamber1.z - ship_geo.chambers.Tub1length) - ship_geo.target.z0 )
   P8gen.SetLmax(ship_geo.TrackStation1.z - ship_geo.target.z0 )
  if charmonly:
   primGen.SetTarget(0., 0.) #vertex is set in pythia8Generator
   ut.checkFileExists(p8dict.inputFile)
   if ship_geo.Box.gausbeam:
    primGen.SetBeam(0.,0., 0.5, 0.5) #more central beam, for hits in downstream detectors
    primGen.SmearGausVertexXY(True) #sigma = x
   else:
    primGen.SetBeam(0.,0., ship_geo.Box.TX-1., ship_geo.Box.TY-1.) #Uniform distribution in x/y on the target (0.5 cm of margin at both sides)
    primGen.SmearVertexXY(True)
   P8gen = ROOT.Pythia8Generator()
   P8gen.UseExternalFile(p8dict.inputFile, options.firstEvent)
   P8gen.SetTarget("volTarget_1",0.,0.) # will distribute PV inside target, beam offset x=y=0.
   # pion on proton 500GeV
   # P8gen.SetMom(500.*u.GeV)
   # P8gen.SetId(-211)
   primGen.AddGenerator(P8gen)

 ####### fixed target
 if options.simEngine == "FixedTarget":
  P8gen = ROOT.FixedTargetGenerator()
  P8gen.SetTarget("volTarget_1",0.,0.)
  P8gen.SetMom(400.*u.GeV)
  P8gen.SetEnergyCut(0.)
  P8gen.SetHeartBeat(100000)
  P8gen.SetG4only()
  primGen.AddGenerator(P8gen)

 ####Pythia6
 if options.simEngine == "Pythia6":
  # set muon interaction close to decay volume
  primGen.SetTarget(ship_geo.target.z0+ship_geo.muShield.length, 0.)
  # -----Pythia6-------------------------
  test = ROOT.TPythia6() # don't know any other way of forcing to load lib
  P6gen = ROOT.tPythia6Generator()
  P6gen.SetMom(50.*u.GeV)
  P6gen.SetTarget("gamma/mu+","n0") # default "gamma/mu-","p+"
  primGen.AddGenerator(P6gen)


 #### EvtCalc

 # -----EvtCalc--------------------------------------
 if options.simEngine == "EvtCalc":
  evtcalc = AttrDict(config['EvtCalc'])
  primGen.SetTarget(0.0, 0.0)
  print(f"Opening input file for EvtCalc generator: {evtcalc.inputFile}")
  ut.checkFileExists(evtcalc.inputFile)
  EvtCalcGen = ROOT.EvtCalcGenerator()
  EvtCalcGen.Init(evtcalc.inputFile, options.firstEvent)
  EvtCalcGen.SetPositions(zTa=ship_geo.target.z, zDV=ship_geo.decayVolume.z)
  primGen.AddGenerator(EvtCalcGen)
  options.nEvents = min(options.nEvents, EvtCalcGen.GetNevents())
  print(
   f"Generate {options.nEvents} with EvtCalc input. First event: {options.firstEvent}"
  )


 # -----Particle Gun-----------------------
 if options.simEngine == "PG":
  pg = AttrDict(config['ParticleGun'])
  myPgun = ROOT.FairBoxGenerator(pg.pID,1)
  myPgun.SetPRange(pg.Estart,pg.Eend)
  myPgun.SetPhiRange(0, 360) # // Azimuth angle range [degree]
  myPgun.SetXYZ(0.*u.cm, 0.*u.cm, 0.*u.cm)
  myPgun.SetThetaRange(0,0) # // Polar angle in lab system range [degree]
  primGen.AddGenerator(myPgun)
