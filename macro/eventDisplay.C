eventDisplay()
{
  //-----User Settings:-----------------------------------------------
  TString  SimEngine     ="TGeant4"; 
  TString  InputFile     ="ship.test.root";
  TString  ParFile       ="ship.params.root";
  TString  OutFile	 ="tst.root";
    
  //----Load the default libraries------
  gROOT->LoadMacro("$VMCWORKDIR/gconfig/basiclibs.C");
  basiclibs();
  
    
  // -----   Reconstruction run   -------------------------------------------
  FairRunAna *fRun= new FairRunAna();
  fRun->SetInputFile(InputFile.Data());
  fRun->SetOutputFile(OutFile.Data());

  FairRuntimeDb* rtdb = fRun->GetRuntimeDb();
  FairParRootFileIo* parInput1 = new FairParRootFileIo();
  parInput1->open(ParFile.Data());
  rtdb->setFirstInput(parInput1);
   
  FairEventManager *fMan= new FairEventManager();
  
  //----------------------Traks and points -------------------------------------
  FairMCTracks    *Track     = new FairMCTracks("Monte-Carlo Tracks");
  FairMCPointDraw *TorinoDetectorPoints = new FairMCPointDraw("FairTestDetectorPoint", kRed, kFullSquare);
 
  fMan->AddTask(Track);
  fMan->AddTask(TorinoDetectorPoints);
  
  
  fMan->Init();                     

}
