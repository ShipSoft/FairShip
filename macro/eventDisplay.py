#!/usr/bin/env python -i
import ROOT,sys,getopt

fMan = None
fRun = None


#-----prepare python exit-----------------------------------------------
def pyExit():
 global fMan,fRun
 del fMan
 del fRun
import atexit
atexit.register(pyExit)

#-----User Settings:-----------------------------------------------
mcEngine      ="TGeant4"
simEngine = "Pythia8"
# simEngine = "Genie"
#
try:
        opts, args = getopt.getopt(sys.argv[1:], "o:D:FHPu:f:x:c:hqv:sl:A",["Pythia6","Pythia8","Genie","Ntuple"])
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
print "FairShip setup for",simEngine

tag = simEngine+"-"+mcEngine+'_D'
InputFile     ="ship."+tag+".root"
ParFile       ="ship.params.Pythia8-TGeant4_D.root"   # "ship.params."+tag+".root"
OutFile	      ="tst."+tag+".root"
    
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
Track                = ROOT.FairMCTracks("Monte-Carlo Tracks",verbose)
TorinoDetectorPoints = ROOT.FairMCPointDraw("FairTestDetectorPoint", ROOT.kRed, ROOT.kFullSquare)
 
fMan.AddTask(Track)
fMan.AddTask(TorinoDetectorPoints)
fMan.Init()     


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
 g = ROOT.gROOT 
 f = g.GetFile("ship.TGeant4.root")
 t = f.Get('cbmsim')
 nev = t.GetEntriesFast()
# organization
 leaves = t.GetListOfLeaves()
 lvdict = {}
 key = 0
 for l in leaves:
  lvdict[l.GetName()] = key
  key+=1 
 t.GetEntry(0)
 search(lvdict,'cbmroot.Event.MCEventHeader.')
 leaves.At(lvdict['cbmroot.Event.MCEventHeader..fZ']).GetValue()
 search(lvdict,'cbmroot.Stack.MCTrack')
 leaves.At(lvdict['cbmroot.Stack.MCTrack_']).GetValue()
 
# Loop over Geo tracks  
 fT = ROOT.TClonesArray("TGeoTrack")
 t.SetBranchAddress("GeoTracks",fT)
 for i in range( nev ) :
   t.GetEntry(i)
   for gTr in fT: 
    gTr.Print()
    part = gTr.GetParticle()
    print 'xyz',gTr.GetPoint(0)[0] ,gTr.GetPoint(0)[1] ,gTr.GetPoint(0)[2] 
    lorv = ROOT.TLorentzVector()
    print lorv.E(),lorv.Px(),lorv.Py(),lorv.Pz()
# Loop over MC tracks  
 fMCT = ROOT.TClonesArray("FairMCTrack")
 t.SetBranchAddress("MCTrack",fMCT)
 for i in range( nev ) :
   t.GetEntry(i)
   for gMCTr in fMCT: 
    gMCTr.Print()
    part = gTr.GetParticle()
    print 'xyz',gTr.GetPoint(0)[0] ,gTr.GetPoint(0)[1] ,gTr.GetPoint(0)[2] 
    lorv = ROOT.TLorentzVector()
    print lorv.E(),lorv.Px(),lorv.Py(),lorv.Pz()
# MC event header  
 fMCH = ROOT.TClonesArray("FairMCEventHeader")
 t.SetBranchAddress("MCEventHeader_",fMCH)
 for i in range( nev ) :
   t.GetEntry(i)

# geometrie
 gf   = ROOT.TFile('geofile_full.TGeant4.root')
 fGeo = gf.Get("FAIRGeom")
 cave = fGeo.GetTopVolume()
 cave.Draw('ogl')
