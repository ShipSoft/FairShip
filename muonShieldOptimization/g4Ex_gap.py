import os
local = False
if not os.uname()[1].find('ubuntu')<0: local = True

debug = False
if local: debug = True

withNtuple     = True
muonNuclear    = True
model          = "QGSP_BERT_EMX"
runnr     = 1
nev       = 100
nevTot    = 0
myEventnr = 0
mytrack   = 1
scoreLog  = 1
myTimer   = {'total':0,'pythia':0,'geant4_conv':0}
ecut      = 10 # GeV   with 1 : ~1sec / event, with 2: 0.4sec / event, 10: 0.13sec
               # pythia = geant4 conversion = 0.4/100 
# should divide number of events over different ecut values. 
import os

tauOnly = False
if len(os.sys.argv)>1:
 runnr  = int(os.sys.argv[1])
 nev    = int(os.sys.argv[2])
 ecut   = float(os.sys.argv[3])
 if len(os.sys.argv)>4:  tauOnly = True

# ==================================================================
#                         ROOT IMPORT                               #
# ==================================================================
import ROOT,time
from ROOT import TLorentzVector
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
ROOT.gSystem.Load("libEG")
ROOT.gSystem.Load("libpythia8")
ROOT.gSystem.Load("libEGPythia8")
myPythia = ROOT.TPythia8()
rnr      = ROOT.TRandom()
myPythia.ReadString("SoftQCD:inelastic = on")
myPythia.ReadString("PhotonCollision:gmgm2mumu = on")
myPythia.ReadString("PromptPhoton:all = on")
myPythia.ReadString("WeakBosonExchange:all = on")
# http://home.thep.lu.se/~torbjorn/pythia81html/ParticleDecays.html
if tauOnly :
  myPythia.ReadString("431:new  D_s+  D_s-  1   3   0    1.96849    0.00000    0.00000    0.00000  1.49900e-01   0   1   0   1   0")
  myPythia.ReadString("431:addChannel = 1   0.0640000    0      -15       16")

# set random number seed
myPythia.ReadString("Random:setSeed = On")
R = int(time.time()%900000000)
myPythia.ReadString("Random:seed = "+str(R))
# Initialize proton (400GeV) on proton at rest
myPythia.Initialize(2212,2212,400.,0.) # required to hack TPythia8 in root !
# W = 74 protons and 184-74= 110 neutrons
if tauOnly:  myPythia.plist(431) 

# Open an output file 
h = {}
if withNtuple:
 f  = ROOT.TFile.Open('pythia8_Geant4_'+str(runnr)+'_'+str(ecut)+'.root', 'RECREATE')
 h['ntuple'] = ROOT.TNtuple("pythia8-Geant4","muon/nu flux","id:px:py:pz:x:y:z:pythiaid:parentid")

leptons   = [12,13,14,15,16] # nu_e, mu, nu_mu, tau, nu_tau
pionkaons = [211,321] 
rest      = [130,310,3122]
allPart   = []
allPart.extend(leptons)
allPart.extend(pionkaons)
allPart.extend(rest)
notWanted = [22,11,-11,990]
# ==================================================================
#                         Geant4 PART                              #
# ==================================================================
# ------------------------------------------------------------------
# randum number
# ------------------------------------------------------------------
rand_engine = Ranlux64Engine()
HepRandom.setTheEngine(rand_engine)
HepRandom.setTheSeed(runnr)
# ==================================================================
# user actions in python
# ==================================================================

# ==================================================================
# visualization
# ==================================================================
if local:
 gVisManager.SetVerboseLevel(2)
 gVisManager.Initialize()
 gApplyUICommand('/vis/open OIX 1200x400-0+0')
 gApplyUICommand('/vis/viewer/set/viewpointThetaPhi -90. 90.')

# ------------------------------------------------------------------
class MyGeneratorAction(G4VUserPrimaryGeneratorAction):
 " My Generator Action"
 pos    = G4ThreeVector(0*cm, 0*cm, -50*m)

 def GeneratePrimaries(self,anEvent):
   global debug,nevTot
   t_0 = time.time()
   npart = 0
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
    vertex    = G4PrimaryVertex(self.pos,0.)
    for p in particles:
       if p.GetStatusCode()!=1 : continue
       pid = p.GetPdgCode()
       if tauOnly and abs(pid) != 16: continue
       if pid in notWanted : continue 
       G4particle = G4PrimaryParticle( pid )
       v = TLorentzVector()
       p.Momentum(v)
       if v.E()*GeV  < ecut : continue
       G4particle.Set4Momentum( v.Px()*GeV,v.Py()*GeV,v.Pz()*GeV,v.E()*GeV )
# store mother ID
       mkey   =  p.GetMother(0)+1  
       mother =  myPythia.GetParticle(mkey)
       curPid =  p.GetPdgCode()      + 10000  # make it positive
       moPid  =  mother.GetPdgCode() + 10000
       w      =  curPid + moPid * 100000
       G4particle.SetWeight(w)
       vertex.SetPrimary( G4particle )
       npart += 1
   # if debug: myPythia.EventListing()
   anEvent.AddPrimaryVertex( vertex )
   myTimer['geant4_conv']+=time.time()-t_0
class MyRunAction(G4UserRunAction):
  "My Run Action"

  def EndOfRunAction(self, run):
    global debug,nevTot
    print "*** End of Run"
    print "- Run summary : (id= %d, #events= %d)" \
          % (run.GetRunID(), nevTot)
    h['ntuple'].Fill(-1., float(nevTot) )
    h['ntuple'].Write()
    print 'lepton masses used'
    for l in leptons:
          G4particle = G4PrimaryParticle( l )
          G4def      = G4particle.GetParticleDefinition()
          print l, G4def.GetParticleName(),  G4particle.GetMass()
# ------------------------------------------------------------------
class MyEventAction(G4UserEventAction):
  "My Event Action"
  def EndOfEventAction(self, event):
    global myEventnr
    myEventnr += 1 
    # self.myPrintout(event)
  def myPrintout(self, event):
    prim = event.GetPrimaryVertex()
    print 'vertex ',prim.GetX0()/m,prim.GetY0()/m,prim.GetZ0()/m 
    for k in range( prim.GetNumberOfParticle() ):
      p = prim.GetPrimary(k) 
      print 'event',p.GetPDGcode(),p.GetPx()/GeV,p.GetPy()/GeV,p.GetPz()/GeV
# ------------------------------------------------------------------
class MySteppingAction(G4UserSteppingAction):
  "My Stepping Action"

  def UserSteppingAction(self, step):
    pass

# ------------------------------------------------------------------
class MyTrackingAction(G4UserTrackingAction):
 def PostUserTrackingAction(self,atrack):
    pass  
 def PreUserTrackingAction(self,atrack):
   # self.myPrintout(atrack)
   if atrack.GetTotalEnergy()/GeV < ecut : 
      G4TrackingManager().SetStoreTrajectory(False) 
      atrack.SetTrackStatus(atrack.GetTrackStatus().fStopAndKill)
   part         = atrack.GetDynamicParticle()
   pid          = part.GetPDGcode()
   if pid in notWanted:
      G4TrackingManager().SetStoreTrajectory(False) 
      atrack.SetTrackStatus(atrack.GetTrackStatus().fStopAndKill)

 def myPrintout(self, atrack):
   part         = atrack.GetDynamicParticle()
   pid          = part.GetPDGcode()
   print 'TA',pid,atrack.GetTotalEnergy()/GeV,ecut*GeV 

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
    if abs(pid) in leptons : 
      mom = track.GetMomentum()
      pos = track.GetPosition()
#
      # primPart = part.GetPrimaryParticle()
      w = track.GetWeight()
      parentid = int(w)/100000-10000
      pythiaid = int(w)%100000-10000
      h['ntuple'].Fill(float(pid), float(mom.x/GeV),float(mom.y/GeV),float(mom.z/GeV),
                   float(pos.x/m),float(pos.y/m),float(pos.z/m),pythiaid,parentid)
      if debug: 
        print 'xxx',pid, float(mom.x/GeV),float(mom.y/GeV),float(mom.z/GeV),pythiaid,parentid,float(pos.x/m),float(pos.y/m),float(pos.z/m)

def ConstructGeom():
  print "* Constructing geometry..."
  world_r = 100.*m 
  # reset world material
  vac = G4Material.GetMaterial("G4_Galactic")
  g4py.ezgeom.SetWorldMaterial(vac)
  g4py.ezgeom.ResizeWorld(world_r, world_r, world_r)
  # a snoopy world is placed
  global snoopy,snoopyPhys,scoreLog
  snoopy   = G4EzVolume("Snoopy")
  snoopy.CreateTubeVolume(vac, 0., 10*m,  50.*m)
  snoopyPhys = snoopy.PlaceIt(G4ThreeVector(0.,0.,0.*m))
  snoopyLog  = snoopyPhys.GetLogicalVolume()
  snoopy.SetVisibility(False)
  # a target box is placed
  global target,targetPhys
  iron     = G4Material.GetMaterial("G4_Fe")
  air      = G4Material.GetMaterial("G4_AIR")
  tungsten = G4Material.GetMaterial("G4_W")
  lead     = G4Material.GetMaterial("G4_Pb")
  alum     = G4Material.GetMaterial("G4_Al")
  target   = G4EzVolume("Target")
  targetOpt   = G4EzVolume("TargetOpt")
  slit     = G4EzVolume("Slit")
# target is sliced, 4 slits of 1cm, 5cm tungsten blocks
  target.CreateTubeVolume(tungsten, 0., 25.*cm,     5.*cm)
  target.SetColor(G4Color(0.0,0.5,0.5,1.0))
  target.SetVisibility(True)
# additional 5 interaction lengths 
  targetOpt.CreateTubeVolume(tungsten, 0., 25.*cm,     25.*cm)
  targetOpt.SetColor(G4Color(0.0,0.5,0.5,1.0))
  targetOpt.SetVisibility(True)
#
  slit.CreateTubeVolume(air, 0., 25.*cm,     0.5*cm) 
  slit.SetVisibility(False)
  targetPhys = []
  slitPhys = []
  for i in range(5):
   targetPhys.append(target.PlaceIt(G4ThreeVector(0.,0.,-50.*m + 5.*cm + i*(1.*cm+10.*cm)),1,snoopy))
   slitPhys.append(slit.PlaceIt(G4ThreeVector(0.,0.,    -50.*m+ 10.*cm + 0.5*cm + i*(1.*cm+10.*cm)),1,snoopy))
  targetPhys.append(targetOpt.PlaceIt(G4ThreeVector(0.,0.,-50.*m + 5*11.*cm + 25.*cm),1,snoopy))
  # = 0.1m3 = 2t
  # a hadron absorber is placed
  absorber = G4EzVolume("Absorber")
# iron alloys saturate at 1.6-2.2T
  #                             inner radius outer radius length    
  absorber.CreateTubeVolume(iron, 0.,         100.*cm,     250.*cm)
  absorberPhys = absorber.PlaceIt(G4ThreeVector(0.,0.,-50*m+5*11.*cm+50.*cm+250.*cm),1,snoopy)
  absorber.SetColor(G4Color(0.898,0.902,0.91,1.0))
  absorber.SetVisibility(True)
  xx = G4VisAttributes()
  xx.SetForceWireframe(True)
  absorberlog = absorberPhys.GetLogicalVolume()
  absorberlog.SetVisAttributes(xx)
# scoring plane
  afterHadronZ = -50*m+5*11.*cm+2*250.*cm+1*mm  
  scorez = afterHadronZ
  score  = G4EzVolume("Score")
  score.CreateTubeVolume(vac, 0.,          50.*m,     1.*mm)
  scorePhys = score.PlaceIt(G4ThreeVector(0.,0.,scorez),1,snoopy)
  scoreLog = scorePhys.GetLogicalVolume()
  g4py.ezgeom.Construct()

g4py.NISTmaterials.Construct()
#print Geant4.gMaterialTable
if not muonNuclear:
 physList =  Geant4.FTFP_BERT()
 gRunManager.SetUserInitialization(physList)
# with muon nuclear
else:
 if 'G4PhysListFactory' in dir(G4physicslists):
# old way
  factory = G4physicslists.G4PhysListFactory()
  xx = factory.GetReferencePhysList(model)
# new, SHIPFAIR
 else:
  xx = G4physicslists.GetReferencePhysList(model)
 gRunManager.SetUserInitialization(xx)

myGE = MyGeneratorAction()
gRunManager.SetUserAction(myGE)
#
myTA= MyTrackingAction()
gRunManager.SetUserAction(myTA)
#  

ConstructGeom()

myRA= MyRunAction()
gRunManager.SetUserAction(myRA)
  
myEA= MyEventAction()
gRunManager.SetUserAction(myEA)

# initialize
gRunManager.Initialize()
# scoring should be set after geometry construction
sens = ScoreSD('Score')
scoreLog.SetSensitiveDetector(sens)  

if local:
 gApplyUICommand('/vis/drawVolume')
 gApplyUICommand('/vis/scene/add/trajectories')
 gApplyUICommand('/vis/viewer/zoom 1.5')


t0 = time.time()
gRunManager.BeamOn(nev)
t1 = time.time()
print 'Time used',t1-t0, ' seconds' 
for x in myTimer: 
  print x,myTimer[x]

