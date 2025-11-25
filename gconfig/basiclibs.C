// $Id: basiclibs.C,v 1.1.1.1 2005/06/23 07:14:09 dbertini Exp $
//
// Macro for loading basic libraries used with both Geant3 and Geant4

void basiclibs()
{
 /*
  gSystem->Load("libPluto");
  */
  gSystem->Load("libRIO");
  gSystem->Load("libGeom");
  gSystem->Load("libGeomPainter");
  gSystem->Load("libVMC");
  gSystem->Load("libEG");

  // For ROOT >= 6.32, TPythia6 is not included in ROOT and must be loaded from EGPythia6
  // For ROOT < 6.32, TPythia6 is built into libEG
  Int_t rootVersion = gROOT->GetVersionInt();
  if (rootVersion >= 63200) {
    // Load external EGPythia6 for ROOT >= 6.32
    gSystem->Load("libEGPythia6");
  }

  gSystem->Load("libPythia6");
  gSystem->Load("libPhysics");
  gSystem->Load("libNet");
  gSystem->Load("libTree");
  gSystem->Load("libMinuit");
  gSystem->Load("libMathMore");
  gSystem->Load("libpythia8");
  gSystem->Load("libgenfit.so");
  gSystem->Load("libLHAPDF.so");
}
