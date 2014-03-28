import ROOT
#-----User Settings:-----------------------------------------------
SimEngine     ="TGeant4"
InputFile     ="ship.test.root"
ParFile       ="ship.params.root"
OutFile	      ="tst.root"
    
#----Load the default libraries------
ROOT.gROOT.LoadMacro("$VMCWORKDIR/gconfig/basiclibs.C")
ROOT.basiclibs()
ROOT.gSystem.Load("libBase")
  
# -----   Reconstruction run   -------------------------------------------
fRun = ROOT.FairRunAna()
fRun.SetInputFile(InputFile)
fRun.SetOutputFile(OutFile)

rtdb      = fRun.GetRuntimeDb()
parInput1 = ROOT.FairParRootFileIo()
parInput1.open(ParFile)
rtdb.setFirstInput(parInput1)
   
fMan= ROOT.FairEventManager()

#----------------------Traks and points -------------------------------------
Track     = ROOT.FairMCTracks("Monte-Carlo Tracks")
TorinoDetectorPoints = ROOT.FairMCPointDraw("FairTestDetectorPoint", ROOT.kRed, ROOT.kFullSquare)
 
fMan.AddTask(Track)
fMan.AddTask(TorinoDetectorPoints)
fMan.Init()                     

