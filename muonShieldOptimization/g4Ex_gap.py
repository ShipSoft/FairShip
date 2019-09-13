#!/usr/bin/env python
from __future__ import print_function
import os
import saveBasicParameters

local = False
if not os.uname()[1].find('ubuntu')<0: local = True

debug = False
particleGun = False

withStepping = False
# if debug: withStepping = True


# new attempt, make general Ekin cut at 0.5
withNtuple     = True
muonNuclear    = True
model          = "QGSP_BERT_EMV" # QGSP_BERT_EMV <-- less accurate EM showers, should be fine, otherwise  "QGSP_BERT_EMX"
runnr     = 1
nev       = 1000
nevTot    = 0
myEventnr = 0
mytrack   = 1
scoreLog  = 1
inclusive = True # write out all particles crossing scoring plane !
myTimer   = {'total':0,'pythia':0,'geant4_conv':0}
tauOnly    = False
JpsiMainly = False
fullTungsten = False

work_dir  = "./"
ecut      = 0.5 # GeV   with 1 : ~1sec / event, with 2: 0.4sec / event, 10: 0.13sec
                 # pythia = geant4 conversion = 0.4/100 
allPart   = True 
qedlist   = [22,11,-11,12,-12,14,14,2212,2112,13,-13]  
rangeCut  = False
trackHistory = {}
#----------------------------- Yandex production ------------------------------
import shutil
import argparse
import logging
logging.info("")
logger = logging.getLogger(os.path.splitext(os.path.basename(os.sys.argv[0]))[0])
logger.setLevel(logging.INFO)


def get_work_dir(run_number):
  import socket
  host = socket.gethostname()
  job_base_name = os.path.splitext(os.path.basename(os.sys.argv[0]))[0]
  out_dir = "{host}_{base}_{runnr}".format(host=host, base=job_base_name, runnr=run_number)
  return out_dir


def init():
  global runnr, nev, ecut, tauOnly,JpsiMainly,fullTungsten, work_dir
  logger.info("SHiP proton-on-taget simulator (C) Thomas Ruf, 2014")

  ap = argparse.ArgumentParser(
      description='Run SHiP "pot" simulation')
  ap.add_argument('-d', '--debug', action='store_true')
  ap.add_argument('-f', '--force', action='store_true', help="force overwriting output directory")
  ap.add_argument('-r', '--run-number', type=int, dest='runnr', default=runnr)
  ap.add_argument('-e', '--ecut', type=float, help="energy cut", dest='ecut', default=ecut)
  ap.add_argument('-n', '--num-events', type=int, help="number of events to generate", dest='nev', default=nev)
  ap.add_argument('-t', '--tau-only',     action='store_true', dest='tauOnly',default=False)
  ap.add_argument('-J', '--Jpsi-mainly',  action='store_true', dest='JpsiMainly',default=False)
  ap.add_argument('-W', '--FullTungsten', action='store_true',dest='fullTungsten',default=False)
  ap.add_argument('-o', '--output', type=str, help="output directory", dest='work_dir', default=None)
  args = ap.parse_args()
  if args.debug:
      logger.setLevel(logging.DEBUG)
  runnr        = args.runnr
  nev          = args.nev
  ecut         = args.ecut
  tauOnly      = args.tauOnly
  JpsiMainly   = args.JpsiMainly
  fullTungsten = args.fullTungsten
  if args.work_dir is None:
    args.work_dir = get_work_dir(runnr)
  work_dir = args.work_dir
  logger.debug("work_dir: %s" % work_dir)
  logger.debug("command line arguments: %s", args)
  if os.path.exists(work_dir):
    logger.warn("output directory '%s' already exists." % work_dir)
    if args.force:
      logger.warn("...cleaning")
      for root, dirs, files in os.walk(work_dir):
        for f in files:
          os.unlink(os.path.join(root, f))
        for d in dirs:
          shutil.rmtree(os.path.join(root, d))
    else:
      logger.warn("...use '-f' option to overwrite it")
  else:
    os.makedirs(work_dir)
  return args

args = init()

os.chdir(work_dir)
# -------------------------------------------------------------------


# ==================================================================
#                         ROOT IMPORT                               #
# ==================================================================
import ROOT,time
# ==================================================================
#                         GEANT4 IMPORT                             #
# ==================================================================
from Geant4 import *
import g4py.NISTmaterials
import g4py.ezgeom
from g4py.ezgeom import G4EzVolume
# ==================================================================
#                         PYTHIA8 PART                              #
# ==================================================================
pdg  = ROOT.TDatabasePDG()
pdg.AddParticle("Pomeron","Pomeron",            0,False,0,0,'',990)
pdg.AddParticle("ccbar[1S0(8)]","ccbar[1S0(8)]",0,False,0,0,'',9900441)
pdg.AddParticle("c~c[3P08]","c~c[3P08]",0,False,0,0,'',9910441)

ROOT.gSystem.Load("libEG")
ROOT.gSystem.Load("libpythia8")
ROOT.gSystem.Load("libEGPythia8")
myPythia = ROOT.TPythia8()
rnr      = ROOT.TRandom()
myPythia.ReadString("Next:numberCount = 100000")
myPythia.ReadString("SoftQCD:inelastic = on")
myPythia.ReadString("PhotonCollision:gmgm2mumu = on")
myPythia.ReadString("PromptPhoton:all = on")
myPythia.ReadString("WeakBosonExchange:all = on")
# http://home.thep.lu.se/~torbjorn/pythia81html/ParticleDecays.html
if tauOnly :
  myPythia.ReadString("431:new  D_s+  D_s-  1   3   0    1.96849    0.00000    0.00000    0.00000  1.49900e-01   0   1   0   1   0")
  myPythia.ReadString("431:addChannel = 1   0.0640000    0      -15       16")
if JpsiMainly :
  myPythia.ReadString("443:new  J/psi  J/psi  4   0   0    3.09692    0.00009    3.09602    3.09782  0.   1   1   0   1   0")
  myPythia.ReadString("443:addChannel = 1   0.1    0      -13       13")
# make pions/kaons/lambda stable
for s in [211,321,130,310,3122,3112,3312]:   # last two added 18Feb2015
  myPythia.ReadString(str(s)+':mayDecay = false')

# set random number seed
myPythia.ReadString("Random:setSeed = On")
R = int(time.time()%900000000)
myPythia.ReadString("Random:seed = "+str(R))
# Initialize proton (400GeV) on proton at rest
myPythia.Initialize(2212,2212,400.,0.) # required to hack TPythia8 in root !
# W = 74 protons and 184-74= 110 neutrons
if tauOnly:  myPythia.Plist(431) 

# if there is no energy cut, there are no particles to apply it to.
if ecut == 0: qedlist = []
# ecut applied to all particles
if allPart: qedlist = []

# Open an output file 
h = {}
if withNtuple:
 f  = ROOT.TFile.Open('pythia8_Geant4_'+str(runnr)+'_'+str(ecut)+'.root', 'RECREATE')
 h['ntuple'] = ROOT.TNtuple("pythia8-Geant4","muon/nu flux","id:px:py:pz:x:y:z:opx:opy:opz:ox:oy:oz:pythiaid:parentid")
 
# ==================================================================
#                         Geant4 PART                              #
# ==================================================================
# ------------------------------------------------------------------
# randum number
# ------------------------------------------------------------------
rand_engine = Ranlux64Engine()
HepRandom.setTheEngine(rand_engine)
HepRandom.setTheSeed(runnr)
world_r   = 200.*m 

# ==================================================================
# user actions in python
# ==================================================================

# ==================================================================
# visualization
# ==================================================================
if local:
 gVisManager.SetVerboseLevel(2)
 gVisManager.Initialize()
 gApplyUICommand('/vis/open OGLIX 1200x400-0+0')
 gApplyUICommand('/vis/viewer/set/viewpointThetaPhi -90. 90.')

# ------------------------------------------------------------------
class MyGeneratorAction(G4VUserPrimaryGeneratorAction):
 " My Generator Action"
 pos    = G4ThreeVector(0*cm, 0*cm,   -world_r/2.)

 def GeneratePrimaries(self,anEvent):
  global debug,nevTot,particleGun,fullTungsten
  t_0 = time.time()
  npart = 0
  if particleGun:
# to evaluate interaction position
   ztarget   = G4ThreeVector(0*cm, 0*cm,  -50.*m)
   vertex    = G4PrimaryVertex(ztarget,0.)
   G4particle = G4PrimaryParticle( 2212 )
   G4particle.Set4Momentum( 0,0,400*GeV,400.0011*GeV )
# store mother ID
   w      =  2212 + 0 * 100000
   G4particle.SetWeight(w)
   vertex.SetPrimary( G4particle )
   npart += 1
  else:
   while npart == 0:
    myPythia.GenerateEvent()   
    nevTot+=1
    myTimer['pythia']+=time.time()-t_0
# pythia interaction happens at 0,0,0
    #x = rnr.Uniform(-3.,3.) 
    #y = rnr.Uniform(-3.,3.)
    # leave this smearing for later
  # create new primaries and set them to the vertex
    particles = myPythia.GetListOfParticles()
    if fullTungsten: z = rnr.Exp(10*cm) -50.*m # tungsten interaction length
    else: z = rnr.Exp(16*cm) -50.*m # Mo/H20/W average interaction length
    ztarget   = G4ThreeVector(0*cm, 0*cm,   z)
    vertex    = G4PrimaryVertex(ztarget,0.)
    v = ROOT.TLorentzVector()
    for p in particles:
       if p.GetStatusCode()!=1 : continue
       pid = p.GetPdgCode()
       mkey   =  p.GetMother(0)+1  
       mother =  myPythia.GetParticle(mkey)
       if JpsiMainly and abs(pid) != 13  : continue
       if tauOnly    and abs(pid) != 16 : continue
       if JpsiMainly and mother.GetPdgCode() != 443 : continue
       if tauOnly  : 
         mmkey   =  mother.GetMother(0)+1  
         mmother =  myPythia.GetParticle(mmkey)
         if abs(mother.GetPdgCode()) != 431 and abs(mmother.GetPdgCode()) != 431 : 
          myPythia.EventListing()
          continue
       qed = pid in qedlist  # use cut only for photons, leptons/neutrinos, protons and neutrons
       p.Momentum(v)
       Ekin = (v.E()-v.M())
       if Ekin*GeV < ecut and (qed or allPart): continue
       G4particle = G4PrimaryParticle( pid )
       G4particle.Set4Momentum( v.Px()*GeV,v.Py()*GeV,v.Pz()*GeV,v.E()*GeV )
# store mother ID
       curPid =  p.GetPdgCode()      + 10000  # make it positive
       moPid  =  mother.GetPdgCode() + 10000
       w      =  curPid + moPid * 100000
       G4particle.SetWeight(w)
       vertex.SetPrimary( G4particle )
       npart += 1
   # if debug: myPythia.EventListing()
  anEvent.AddPrimaryVertex( vertex )
  if debug and not particleGun: print('new event at ',ztarget.z/m)
  myTimer['geant4_conv']+=time.time()-t_0
class MyRunAction(G4UserRunAction):
  "My Run Action"

  def EndOfRunAction(self, run):
    global debug,nevTot
    print("*** End of Run")
    print("- Run summary : (id= %d, #events= %d)" \
          % (run.GetRunID(), nevTot))
    h['ntuple'].Write()
    print('ecut applied to',allPart,qedlist,' range cut for e,gamma:',rangeCut)
# ------------------------------------------------------------------
class MyEventAction(G4UserEventAction):
  "My Event Action"
  def EndOfEventAction(self, event):
    global myEventnr
    if debug and not particleGun: print('end of event',myEventnr)
    myEventnr += 1 
    # self.myPrintout(event)
  def StartOfEventAction(self, event):
    global trackHistory
    trackHistory={}
  def myPrintout(self, event):
    prim = event.GetPrimaryVertex()
    print('vertex ',prim.GetX0()/m,prim.GetY0()/m,prim.GetZ0()/m) 
    for k in range( prim.GetNumberOfParticle() ):
      p = prim.GetPrimary(k) 
      print('event',p.GetPDGcode(),p.GetPx()/GeV,p.GetPy()/GeV,p.GetPz()/GeV)
# ------------------------------------------------------------------
class MySteppingAction(G4UserSteppingAction):
  "My Stepping Action"

  def UserSteppingAction(self, step):
    preStepPoint = step.GetPreStepPoint()
    touch        = preStepPoint.GetTouchableHandle()
    volName      = touch.GetVolume().GetName().__format__('')
    pos    = preStepPoint.GetPosition()
    print('stepping name, z pos  dedx (MeV): ',volName,pos.z/m,step.GetTotalEnergyDeposit()/MeV)
# ------------------------------------------------------------------
class MyTrackingAction(G4UserTrackingAction):
 def PostUserTrackingAction(self,atrack):
    pass  
 def PreUserTrackingAction(self,atrack):
# need to be careful with energy cut, anti-protons and anti-neutrons can always produce pions and kaons
   part         = atrack.GetDynamicParticle()
   pid          = part.GetPDGcode()
   muCut = JpsiMainly and abs(pid)!=13
   qed          = pid in qedlist  # use cut only for photons, electrons, protons and neutrons
   if (atrack.GetKineticEnergy()/GeV < ecut and (qed or allPart) ) or muCut : 
      G4TrackingManager().SetStoreTrajectory(False) 
      atrack.SetTrackStatus(atrack.GetTrackStatus().fStopAndKill)

# ------------------------------------------------------------------
class MyTrackingActionD(G4UserTrackingAction):
 def PostUserTrackingAction(self,atrack):
   if particleGun and atrack.GetTrackID() == 1:
     # record dead of 400GeV proton
     if atrack.GetTrackStatus() != atrack.GetTrackStatus().fAlive :
      part         = atrack.GetDynamicParticle()
      pid          = part.GetPDGcode()
      vx           = atrack.GetVertexPosition()
      mom  = atrack.GetMomentum()
      ekin = atrack.GetKineticEnergy()/GeV
      pos  = atrack.GetPosition()
      w = atrack.GetWeight()
      parentid = int(w)/100000-10000
      pythiaid = int(w)%100000-10000
      h['ntuple'].Fill(float(pid), float(mom.x/GeV),float(mom.y/GeV),float(mom.z/GeV),\
                   float(pos.x/m),float(pos.y/m),float(pos.z/m),\
                   float(vx.x/m),float(vx.y/m),float(vx.z/m),pythiaid,parentid)
       
 def PreUserTrackingAction(self,atrack):
   global trackHistory
# need to be careful with energy cut, anti-protons and neutrons can always produce pions and kaons
   part         = atrack.GetDynamicParticle()
   pid          = part.GetPDGcode()
   # if debug: self.myPrintout(atrack)
   moid = atrack.GetParentID()
   trackHistory[atrack.GetTrackID()]=[pid,moid]
   tmoid = str(moid)
   if moid in trackHistory: 
         mo = pdg.GetParticle(trackHistory[moid][0])
         if mo : tmoid = mo.GetName()
   tid = str(pid)
   if pdg.GetParticle(pid): tid = pdg.GetParticle(pid).GetName()
   mom = atrack.GetMomentum()
   p = ROOT.TMath.Sqrt(mom.x*mom.x+mom.y*mom.y+mom.z*mom.z)
   if debug and abs(pid)==13: print('track',atrack.GetTrackID(),tid,tmoid,moid,atrack.GetKineticEnergy()/MeV,p/MeV)
   if pid==12:
      if moid in trackHistory: 
        gmoid = trackHistory[moid][1]
        if gmoid in trackHistory:
          tgmoid = str(gmoid)
          mo = pdg.GetParticle(trackHistory[gmoid][0])
          if mo : tgmoid = mo.GetName()
          print('   <--',gmoid,tgmoid)
          gmoid = trackHistory[gmoid][1]
          if gmoid in trackHistory:
           tgmoid = str(gmoid)
           mo = pdg.GetParticle(trackHistory[gmoid][0])
           if mo : tgmoid = mo.GetName()
           print('      <--',gmoid,tgmoid)

   qed          = pid in qedlist  # use cut only for photons, electrons, protons and neutrons
   if atrack.GetKineticEnergy()/GeV < ecut and (qed or allPart): 
      G4TrackingManager().SetStoreTrajectory(False) 
      atrack.SetTrackStatus(atrack.GetTrackStatus().fStopAndKill)

 def myPrintout(self, atrack):
   part         = atrack.GetDynamicParticle()
   pid          = part.GetPDGcode()
   vx  = atrack.GetVertexPosition()
   pos = atrack.GetPosition()
   mom = atrack.GetMomentum()
   print('TA',pid,atrack.GetTotalEnergy()/GeV,ecut*GeV) 
   print('start tracking',atrack.GetDynamicParticle().GetPDGcode(),atrack.GetKineticEnergy()/GeV,vx.z/m,pos.z/m,mom.z/GeV)

# ------------------------------------------------------------------
class ScoreSD(G4VSensitiveDetector):
  "SD for score voxels"

  def __init__(self,Name):
    G4VSensitiveDetector.__init__(self, Name)

  def ProcessHits(self, step, rohist):
    preStepPoint = step.GetPreStepPoint()
    track        = step.GetTrack()
    part         = track.GetDynamicParticle()
    pid          = part.GetPDGcode()
    vx           = track.GetVertexPosition()
    pvx          = track.GetVertexMomentumDirection()  
    ekinvx       = track.GetVertexKineticEnergy()
    M            = part.GetMass()
    Pvx          = ROOT.TMath.Sqrt( ekinvx*(ekinvx+2*M) )
    mom  = track.GetMomentum()
    ekin = track.GetKineticEnergy()/GeV
    pos = track.GetPosition()
#
    # primPart = part.GetPrimaryParticle()
    w = track.GetWeight()
    parentid = int(w)/100000-10000
    pythiaid = int(w)%100000-10000
    h['ntuple'].Fill(float(pid), float(mom.x/GeV),float(mom.y/GeV),float(mom.z/GeV),\
                   float(pos.x/m),float(pos.y/m),float(pos.z/m),\
                   float(Pvx*pvx.x/GeV),float(Pvx*pvx.y/GeV),float(Pvx*pvx.z/GeV),\
                   float(vx.x/m),float(vx.y/m),float(vx.z/m),pythiaid,parentid)
    if debug: 
        print('xxx',pid, float(mom.x/GeV),float(mom.y/GeV),float(mom.z/GeV),\
                   float(pos.x/m),float(pos.y/m),float(pos.z/m),\
                   float(Pvx*pvx.x/GeV),float(Pvx*pvx.y/GeV),float(Pvx*pvx.z/GeV),\
                   float(vx.x/m),float(vx.y/m),float(vx.z/m),pythiaid,parentid)

def ConstructGeom():
  print("* Constructing geometry...")
  # reset world material
  vac = G4Material.GetMaterial("G4_Galactic")
  g4py.ezgeom.SetWorldMaterial(vac)
  g4py.ezgeom.ResizeWorld(world_r/2., world_r/2., world_r)
  # a snoopy world is placed
  global snoopy,snoopyPhys,scoreLog
  snoopy   = G4EzVolume("Snoopy")
  snoopy.CreateTubeVolume(vac, 0.,          20*m,     world_r/2.)
  snoopyPhys = snoopy.PlaceIt(G4ThreeVector(0.,0.,0.*m))
  snoopyLog  = snoopyPhys.GetLogicalVolume()
  snoopy.SetVisibility(False)
  # a target box is placed
  global target,targetPhys
  iron     = G4Material.GetMaterial("G4_Fe")
  air      = G4Material.GetMaterial("G4_AIR")
  water    = G4Material.GetMaterial("G4_WATER")
  tungsten = G4Material.GetMaterial("G4_W")
  lead     = G4Material.GetMaterial("G4_Pb")
  alum     = G4Material.GetMaterial("G4_Al")
  elementMo  = G4Element("Molybdenum","Mo",42.,   95.94*g/mole)
  molybdenum = G4Material("molybdenum", 10.22*g/cm3, 1)
  molybdenum.AddElement(elementMo, 1.00)
# 
  if fullTungsten:
   target   = G4EzVolume("Target")
   slit     = G4EzVolume("Slit")
   slitDZ   =      0.5*cm
   targetDZ =       5.*cm
# target is sliced, 4 slits of 1cm, 10cm tungsten blocks
   target.CreateTubeVolume(tungsten, 0., 25.*cm,targetDZ)
   target.SetColor(G4Color(0.0,0.5,0.5,1.0))
   target.SetVisibility(True)
# additional 5 interaction lengths 
  #targetOpt = G4EzVolume("TargetOpt")
  #targetOpt.CreateTubeVolume(tungsten, 0., 25.*cm,     25.*cm)
  #targetOpt.SetColor(G4Color(0.0,0.5,0.5,1.0))
  #targetOpt.SetVisibility(True)
   slit.CreateTubeVolume(water, 0., 25.*cm, slitDZ) 
   slit.SetVisibility(False)
   targetPhys = []
   slitPhys = []
   targetL = 0*cm
   z0Pos   = -50.*m
   for i in range(4):
    targetPhys.append(target.PlaceIt(G4ThreeVector(0.,0.,z0Pos + targetL + targetDZ)           ,1,snoopy))
    slitPhys.append(slit.PlaceIt(G4ThreeVector(0.,0.,    z0Pos + targetL + 2*targetDZ + slitDZ),1,snoopy))
    targetL+= 2*(slitDZ+targetDZ)
   targetPhys.append(target.PlaceIt(G4ThreeVector(0.,0., z0Pos + targetL + targetDZ),1,snoopy))
   targetL+= 2*(targetDZ)
  # put iron around
   moreShielding = G4EzVolume("moreShielding")
   moreShielding.CreateTubeVolume(iron, 30.*cm, 400.*cm,  targetL/2.)
   moreShieldingPhys = moreShielding.PlaceIt(G4ThreeVector(0.,0.,z0Pos + targetL/2.),1,snoopy)
#
  else:  # new design with mixture Molybdaen and Tungsten
   slitDZ   = 0.5*cm
   diameter = 30.*cm
   spaceTopBot = 10.*cm
   spaceSide   = 5.*cm
   slit     = G4EzVolume("Slit")
   slit.CreateBoxVolume(water, diameter,diameter,slitDZ) 
   slit.SetVisibility(False)
   targetPhys = []
   targetVol  = []
   slitPhys   = []
   targetL = 0*cm
   z0Pos   = -50.*m
   #          material,length  
   layout = {1:[molybdenum,8.*cm],\
             2:[molybdenum,2.5*cm],3:[molybdenum,2.5*cm],4:[molybdenum,2.5*cm],5:[molybdenum,2.5*cm],\
             6:[molybdenum,2.5*cm],7:[molybdenum,2.5*cm],8:[molybdenum,2.5*cm],\
             9:[molybdenum,5.0*cm],10:[molybdenum,5.0*cm],\
            11:[molybdenum,6.5*cm],\
            12:[molybdenum,8.0*cm],13:[molybdenum,8.0*cm],\
            14:[tungsten,5.*cm],15:[tungsten,8.*cm],16:[tungsten,10.*cm],17:[tungsten,35.*cm] }
   for i in range(1,18): 
     targetVol.append(G4EzVolume("Target_Layer_"+str(i)))
     targetVol[i-1].CreateBoxVolume(layout[i][0], diameter,diameter,layout[i][1])
     if layout[i][0]==tungsten:     targetVol[i-1].SetColor(G4Color(0.0,0.5,0.5,1.0))
     else:                          targetVol[i-1].SetColor(G4Color(0.3,0.2,0.5,1.0))
     targetVol[i-1].SetVisibility(True)
     targetPhys.append(targetVol[i-1].PlaceIt(G4ThreeVector(0.,0.,z0Pos + targetL + layout[i][1]/2.),1,snoopy))
     if i<17:
      slitPhys.append(slit.PlaceIt(            G4ThreeVector(0.,0.,z0Pos + targetL + layout[i][1] + slitDZ/2.),1,snoopy))
      targetL+= slitDZ+layout[i][1]
     else: targetL+= layout[i][1]
  # put iron around
   xTot = 400.*cm
   yTot = 400.*cm
   moreShieldingTopBot = G4EzVolume("moreShieldingTopBot")
   moreShieldingTopBot.CreateBoxVolume(iron, xTot, yTot/2., targetL)
   moreShieldingTopPhys = moreShieldingTopBot.PlaceIt(G4ThreeVector(0.,diameter/2. +spaceTopBot+yTot/4.,z0Pos + targetL/2.),1,snoopy)
   moreShieldingBotPhys = moreShieldingTopBot.PlaceIt(G4ThreeVector(0.,-diameter/2.-spaceTopBot-yTot/4.,z0Pos + targetL/2.),1,snoopy)
   moreShieldingSide = G4EzVolume("moreShieldingSide")
   moreShieldingSide.CreateBoxVolume(iron, xTot/2., diameter+1.9*spaceTopBot, targetL)
   moreShieldingLeftPhys  = moreShieldingSide.PlaceIt(G4ThreeVector(diameter/2. +spaceSide+xTot/4.,0.,z0Pos + targetL/2.),1,snoopy)
   moreShieldingRightPhys = moreShieldingSide.PlaceIt(G4ThreeVector(-diameter/2.-spaceSide-xTot/4.,0.,z0Pos + targetL/2.),1,snoopy)
  # = 0.1m3 = 2t
  # a hadron absorber is placed
  absorberL = 2*150.*cm
  absorber = G4EzVolume("Absorber")
  #                             inner radius outer radius length    
  absorber.CreateTubeVolume(iron, 0.,         400.*cm,     absorberL/2.)
  absorberPhys = absorber.PlaceIt(G4ThreeVector(0.,0.,z0Pos+targetL+absorberL/2.+5.*cm),1,snoopy)
  absorber.SetColor(G4Color(0.898,0.902,0.91,1.0))
  absorber.SetVisibility(True)
  xx = G4VisAttributes()
  xx.SetForceWireframe(True)
  absorberlog = absorberPhys.GetLogicalVolume()
  absorberlog.SetVisAttributes(xx)
# scoring plane
  afterHadronZ = z0Pos+targetL+absorberL+5.1*cm  
  scorez = afterHadronZ
  score  = G4EzVolume("Score")
  score.CreateTubeVolume(vac, 0.,          20.*m,     1.*mm)
  scorePhys = score.PlaceIt(G4ThreeVector(0.,0.,scorez),1,snoopy)
  scoreLog = scorePhys.GetLogicalVolume()
  g4py.ezgeom.Construct()

g4py.NISTmaterials.Construct()
#print Geant4.gMaterialTable
xx = G4physicslists.GetReferencePhysList(model)
if rangeCut:
 xx.SetCutValue(10.,'gamma')
 xx.SetCutValue(10.,'e-')
 xx.SetCutValue(10.,'e+')
gRunManager.SetUserInitialization(xx)

myGE = MyGeneratorAction()
gRunManager.SetUserAction(myGE)
#
if debug: myTA= MyTrackingActionD()
else:     myTA= MyTrackingAction()
gRunManager.SetUserAction(myTA)
#  

ConstructGeom()
myRA= MyRunAction()
gRunManager.SetUserAction(myRA)
  
myEA= MyEventAction()
gRunManager.SetUserAction(myEA)

mySA= MySteppingAction()
if withStepping :    gRunManager.SetUserAction(mySA)

# initialize
gRunManager.Initialize()
# scoring should be set after geometry construction
sens = ScoreSD('Score')
scoreLog.SetSensitiveDetector(sens)  

if local and not particleGun:
 gApplyUICommand('/vis/drawVolume')
 gApplyUICommand('/vis/scene/add/trajectories')
 gApplyUICommand('/vis/viewer/zoom 1.5')

t0 = time.time()
gRunManager.BeamOn(nev)
t1 = time.time()
print('Time used',t1-t0, ' seconds') 
for x in myTimer: 
  print(x,myTimer[x])

logger.info("output directory: %s" % work_dir)
# save arguments and GIT tags
import saveBasicParameters
saveBasicParameters.execute(f,args,'SHiP-Params')

if local:
 wrld = snoopyPhys.GetMotherLogical()
 parser = G4GDMLParser()
 geofile = work_dir+'/g4Geom.gdml' 
 if os.path.isfile(geofile): os.system('rm '+geofile)
 parser.Write('g4Geom.gdml',wrld)
 ROOT.TGeoManager()
 geomgr = ROOT.gGeoManager
 geomgr.Import('g4Geom.gdml','world','new')
 ROOT.gGeoManager.CheckOverlaps()
 ROOT.gGeoManager.PrintOverlaps()
 geomgr.GetTopVolume().Draw('ogl')

