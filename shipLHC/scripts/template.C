// ROOT.gROOT.LoadMacro('hsimple.C')
#include "Scifi.h"
#include "MuFilter.h"

void Execute() {
   std::cout<<"start"<<std::endl;
   auto vol = gGeoManager->FindVolumeFast("SiPMmapVol");
   auto nav = gGeoManager->GetCurrentNavigator();
   TTree* eventTree = dynamic_cast<class TTree*>(gROOT->FindObject("rawConv"));
   auto lsOfGlobals = gROOT->GetListOfGlobals();
   Scifi *Scifi = dynamic_cast<class Scifi*>(lsOfGlobals->FindObject("Scifi"));
   MuFilter* Mufi = dynamic_cast<class MuFilter*>(lsOfGlobals->FindObject("MuFilter"));

// dynamic_cast<genfit::KalmanFitterInfo*>(fitTrack->getPointWithMeasurement(i)->getFitterInfo(rep))->getWeights();
   
   std::cout<<"Nevents "<<eventTree->GetEntries()<<std::endl;
   TVector3 A;
   TVector3 B;
   Mufi->GetPosition(21001,A,B);
   A.Print();
   B.Print();

}
