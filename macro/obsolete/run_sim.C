void run_sim(Int_t nEvents = 10, TString mcEngine = "TGeant4")
{
   gROOT->LoadMacro("$VMCWORKDIR/gconfig/basiclibs.C");
   basiclibs();

   gSystem->Load("libGen.so");

  // Output file name
  TString outFile ="ship.test.root";

  // Parameter file name
  TString parFile="ship.params.root";

  // In general, the following parts need not be touched
  // ========================================================================


  // -----   Timer   --------------------------------------------------------
  TStopwatch timer;
  timer.Start();
  // ------------------------------------------------------------------------

  // -----   Create simulation run   ----------------------------------------
  FairRunSim* run = new FairRunSim();
  run->SetName(mcEngine);              // Transport engine
  run->SetOutputFile(outFile);          // Output file
  FairRuntimeDb* rtdb = run->GetRuntimeDb();
  // ------------------------------------------------------------------------

  // -----   Create media   -------------------------------------------------
  run->SetMaterials("media.geo");       // Materials
  // ------------------------------------------------------------------------

  // -----   Create geometry   ----------------------------------------------

  FairModule* cave= new ShipCave("CAVE");
  cave->SetGeometryFileName("cave.geo");
  run->AddModule(cave);

  FairModule* TargetStation = new ShipTargetStation("TargetStation");
  run->AddModule(TargetStation);
  FairModule* MuonShield =  new ShipMuonShield("MuonShield",1);
  run->AddModule(MuonShield);

  FairModule* magnet = new ShipMagnet("Magnet");
  run->AddModule(magnet);


  FairModule* Chamber = new ShipChamber("Chamber");
  run->AddModule(Chamber);

  FairDetector* Veto = new veto("Veto", kTRUE);
  run->AddModule(Veto);


  FairDetector* ecal = new ecal("Ecal", kTRUE);
  run->AddModule(ecal);


  FairDetector* Muon = new muon("Muon", kTRUE);
  run->AddModule(Muon);

 // ------------------------------------------------------------------------


    // -----   Magnetic field   -------------------------------------------
    // Constant Field
    ShipConstField  *fMagField = new ShipConstField();
    fMagField->SetField(0., 2. ,0. ); // values are in kG
    fMagField->SetFieldRegion(-160, 160,-160, 160, 1940, 2125); // values are in cm
                          //  (xmin,xmax,ymin,ymax,zmin,zmax)
    run->SetField(fMagField);
    // --------------------------------------------------------------------



  // -----   Create PrimaryGenerator   --------------------------------------
  FairPrimaryGenerator* primGen = new FairPrimaryGenerator();


    // Pythia8
  Pythia8Generator* P8gen = new Pythia8Generator();
  P8gen->UseRandom3(); // TRandom1 or TRandom3 ?
  P8gen->SetParameters("PhaseSpace:pTHatMin = 0.001");
  P8gen->SetParameters("PhaseSpace:mHatMin = 0.001");
  P8gen->SetParameters("PhaseSpace:pTHatMinDiverge = 1.0000e-05");
  P8gen->SetParameters("PhaseSpace:minWidthBreitWigners = 0.00001");
  P8gen->SetParameters("HardQCD:all = on");
  P8gen->SetParameters("SoftQCD:all = on");
  P8gen->SetMom(400);  // p momentum
  primGen->AddGenerator(P8gen);


  run->SetGenerator(primGen);
  // ------------------------------------------------------------------------

  //---Store the visualiztion info of the tracks, this make the output file very large!!
  //--- Use it only to display but not for production!
  run->SetStoreTraj(kTRUE);



  // -----   Initialize simulation run   ------------------------------------
  run->Init();
  // ------------------------------------------------------------------------

  // -----   Runtime database   ---------------------------------------------

  Bool_t kParameterMerged = kTRUE;
  FairParRootFileIo* parOut = new FairParRootFileIo(kParameterMerged);
  parOut->open(parFile.Data());
  rtdb->setOutput(parOut);
  rtdb->saveOutput();
  rtdb->print();
  // ------------------------------------------------------------------------

  // -----   Start run   ----------------------------------------------------
   run->Run(nEvents);
  run->CreateGeometryFile("geofile_full.root");
  // ------------------------------------------------------------------------

  // -----   Finish   -------------------------------------------------------
  timer.Stop();
  Double_t rtime = timer.RealTime();
  Double_t ctime = timer.CpuTime();
  cout << endl << endl;
  cout << "Macro finished succesfully." << endl;
  cout << "Output file is "    << outFile << endl;
  cout << "Parameter file is " << parFile << endl;
  cout << "Real time " << rtime << " s, CPU time " << ctime
       << "s" << endl << endl;
  // ------------------------------------------------------------------------
}
