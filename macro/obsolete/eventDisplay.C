eventDisplay()
{
  //-----User Settings:-----------------------------------------------
  TString  SimEngine     ="TGeant4"; 
  TString  InputFile     ="ship.10.0.Pythia8-TGeant4_D.root";
  TString  ParFile       ="ship.params.10.0.Pythia8-TGeant4_D.root";
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
  
  //----------------------Tracks and points -------------------------------------
 FairMCTracks    *Track     =   new FairMCTracks("Monte-Carlo Tracks");
 FairMCPointDraw *VetoPoints  = new FairMCPointDraw("vetoPoint", kBlue, kFullDiamond);
 FairMCPointDraw *StrawPoints = new FairMCPointDraw("strawtubesPoint", kGreen, kFullCircle);
 FairMCPointDraw *EcalPoints  = new FairMCPointDraw("EcalPoint", kRed, kFullSquare);
 FairMCPointDraw *HcalPoints  = new FairMCPointDraw("HcalPoint", kMagenta, kFullSquare);
 FairMCPointDraw *MuonPoints  = new FairMCPointDraw("muonPoint", kYellow, kFullSquare);
 FairMCPointDraw *RpcPoints   = new FairMCPointDraw("ShipRpcPoint", kOrange, kFullSquare);
 fMan->AddTask(Track);
 fMan->AddTask(VetoPoints);
 fMan->AddTask(StrawPoints);
 fMan->AddTask(EcalPoints);
 fMan->AddTask(HcalPoints);
 fMan->AddTask(MuonPoints);
 fMan->AddTask(RpcPoints);
 fMan->Init(1,4,10000);   

 gGeoManager->GetVolume("rockD")->SetVisibility(0); 
 gGeoManager->GetVolume("rockS")->SetVisibility(0); 
 gGeoManager->GetVolume("wire")->SetVisibility(0); 
 gGeoManager->GetVolume("gas")->SetVisibility(0); 
 gGeoManager->GetVolume("Ecal")->SetVisibility(1); 
 gGeoManager->GetVolume("Hcal")->SetVisibility(1); 
 gGeoManager->GetVolume("Ecal")->SetLineColor(kYellow); 
 gGeoManager->GetVolume("Hcal")->SetLineColor(kOrange+3); 
 TEveElement* geoscene = gEve->GetScenes()->FindChild("Geometry scene");  
 gEve->ElementChanged(geoscene,true,true);   
}
