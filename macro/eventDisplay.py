#!/usr/bin/env python -i
import ROOT,sys,getopt

fMan = None
fRun = None
pdg  = ROOT.TDatabasePDG()
g    = ROOT.gROOT 

#-----prepare python exit-----------------------------------------------
def pyExit():
 global fMan,fRun
 del fMan
 del fRun
import atexit
atexit.register(pyExit)

#-----User Settings:-----------------------------------------------
mcEngine  = "TGeant4"
simEngine = "Pythia8"
# simEngine = "Genie"
#
try:
        opts, args = getopt.getopt(sys.argv[1:], "o:D:FHPu:f:x:c:hqv:sl:A",["Pythia6","Pythia8","Genie","Ntuple","MuonBack"])
except getopt.GetoptError:
        # print help information and exit:
        print ' enter --Pythia8/6 to generate events with Pythia8/6 or --Genie for reading and processing neutrino interactions'  
        sys.exit()
for o, a in opts:
        if o in ("--Pythia6"):
            simEngine = "Pythia6"
        if o in ("--Pythia8"):
            simEngine = "Pythia8"
        if o in ("--Genie"):
            simEngine = "Genie"
        if o in ("--Ntuple"):
            simEngine = "Ntuple"
        if o in ("--MuonBack"):
            simEngine = "MuonBack"
print "FairShip setup for",simEngine

tag = simEngine+"-"+mcEngine+'_D'
InputFile     ="ship."+tag+".root"
ParFile       ="ship.params."+tag+".root"  
OutFile	      ="tst."+tag+".root"

# draw Ecal yellow instead of black
def ecalYellow():
 evmgr = ROOT.gEve
 sc    = evmgr.GetScenes()
 geoscene = sc.FindChild('Geometry scene')
 fGeo = g.FindObjectAny("FAIRGeom")
 ecal = fGeo.GetVolume("EcalModule3")
 ecal.SetLineColor(ROOT.kYellow) 
 evmgr.ElementChanged(geoscene,True,True)

#----Load the default libraries------
ROOT.gROOT.LoadMacro("$VMCWORKDIR/gconfig/basiclibs.C")
ROOT.basiclibs()
  
# -----   Reconstruction run   -------------------------------------------
fRun = ROOT.FairRunAna()
fRun.SetInputFile(InputFile)
fRun.SetOutputFile(OutFile)

rtdb      = fRun.GetRuntimeDb()
parInput1 = ROOT.FairParRootFileIo()
parInput1.open(ParFile)
rtdb.setFirstInput(parInput1)
   
fMan= ROOT.FairEventManager()
fMan.SetMaxEnergy(400.) # default is 25 GeV only !
fMan.SetMinEnergy(0.1) #  100 MeV
fMan.SetEvtMaxEnergy(400.) # what is the difference between EvtMaxEnergy and MaxEnergy ?
fMan.SetPriOnly(False)  # display everything

#----------------------Tracks and points -------------------------------------
verbose = 0  # 3 lot of output
Track          = ROOT.FairMCTracks("Monte-Carlo Tracks",verbose)
VetoPoints     = ROOT.FairMCPointDraw("vetoPoint", ROOT.kBlue, ROOT.kFullSquare)
StrawPoints = ROOT.FairMCPointDraw("strawtubesPoint", ROOT.kGreen, ROOT.kFullSquare)
EcalPoints = ROOT.FairMCPointDraw("EcalPoint", ROOT.kRed, ROOT.kFullSquare)
MuonPoints = ROOT.FairMCPointDraw("muonPoint", ROOT.kYellow, ROOT.kFullSquare)
 
fMan.AddTask(Track)
fMan.AddTask(VetoPoints)
fMan.AddTask(MuonPoints)
fMan.AddTask(EcalPoints)
fMan.AddTask(StrawPoints)
fMan.Init(1,4,1000) # default Init(visopt=1, vislvl=3, maxvisnds=10000), ecal display requires vislvl=4
ecalYellow()

fGeo  = ROOT.gGeoManager  
sTree = g.FindObjectAny('cbmsim')
def search(lvdict,tag):
  for x in lvdict: 
   if not x.find(tag)<0: print x
def rename(name='ship.TGeant4.root'):
 f = ROOT.TFile(name,'UPDATE')
 t = f.Get('cbmsim')
 for x in t.GetListOfBranches():
  nm = x.GetName().replace('_1','')
  x.SetName(nm)
 t.Write()
 f.Close() 

def mydebug():               
 t = g.FindObjectAny('cbmsim')
 nev = t.GetEntriesFast()
 t.GetEntry(0)
# Loop over Geo tracks  
 for i in range( min(5,nev) ) :
   t.GetEntry(i)
   for gTr in t.GeoTracks: 
    gTr.Print()
    part = gTr.GetParticle()
    lorv = ROOT.TLorentzVector()
    print 'xyz E pxpypz',gTr.GetPoint(0)[0],gTr.GetPoint(0)[1] ,gTr.GetPoint(0)[2],lorv.E(),lorv.Px(),lorv.Py(),lorv.Pz()
# Loop over MC tracks  
 for i in range( min(5,nev) ) :
   t.GetEntry(i)
   for gMCTr in t.MCTrack: 
    gMCTr.Print()
    print  gMCTr.GetPdgCode(),gMCTr.GetMass(),gMCTr.GetP()
# MC event header  
 for i in range( nev ) :
   t.GetEntry(i)
   print t.MCEventHeader.GetEventID(),t.MCEventHeader.GetRunID(),t.MCEventHeader.GetZ()
# geometrie
 fGeo = g.FindObjectAny("FAIRGeom")
 cave = fGeo.GetTopVolume()
 cave.Draw('ogl')
# eve
 evmgr = ROOT.gEve
 sc    = evmgr.GetScenes()
 geoscene = sc.FindChild('Geometry scene')
 topnode  = geoscene.FindChild('cave_1')
 topnode.SetVisLevel(4)
 evmgr.ElementChanged(geoscene,True,True)
def debugStraw(n):
 fGeo = ROOT.gGeoManager  
 vols = fGeo.GetListOfVolumes()
 sTree = g.FindObjectAny('cbmsim')
 sTree.GetEntry(n)
 for s in sTree.strawtubesPoint:
  print vols[s.GetDetectorID()-1].GetName()
def access2Branches():
 MCTracks = ROOT.TClonesArray("ShipMCTrack")
 sTree = g.FindObjectAny('cbmsim')
 sTree.SetBranchAddress("MCTrack", MCTracks)
 TrackingHits   = ROOT.TClonesArray("vetoPoint")
 sTree.SetBranchAddress("vetoPoint", TrackingHits)
 Ecals = ROOT.TClonesArray("ecalPoint")
 sTree.SetBranchAddress("EcalPoint", Ecals)
 sTree.MCTrack   = MCTracks
 sTree.vetoPoint = TrackingHits
 sTree.EcalPoint = Ecals
 sTree.GetEntry(1)
 return sTree 

