#include "Scifi.h"
#include "MuFilter.h"
#include "FairTask.h"
#include "FairRootFileSink.h"
#include "FairRootManager.h"
#include <KalmanFittedStateOnPlane.h>

void Execute() {
   std::cout<<"start"<<std::endl;
   auto vol = gGeoManager->FindVolumeFast("SiPMmapVol");
   auto nav = gGeoManager->GetCurrentNavigator();
   auto lsOfGlobals = gROOT->GetListOfGlobals();
   Scifi *Scifi = dynamic_cast<class Scifi*>(lsOfGlobals->FindObject("Scifi"));
   MuFilter* Mufi = dynamic_cast<class MuFilter*>(lsOfGlobals->FindObject("MuFilter"));
   FairRootManager* ioman = FairRootManager::Instance();
   FairRunAna* run = FairRunAna::Instance();
   TTree* eventTree = dynamic_cast<class TTree*>(ioman->GetInChain());
   FairTask* Tracking = run->GetTask("simpleTracking");
   auto T = dynamic_cast<class TObjArray*>( ioman->GetObject("Reco_MuonTracks"));

   std::cout<<"Nevents "<<eventTree->GetEntries()<<std::endl;
   TVector3 A;
   TVector3 B;
   Mufi->GetPosition(21001,A,B);
   A.Print();
   B.Print();

   for (Int_t n=0; n<100; n++) {
      eventTree->GetEvent(n);
      Tracking->ExecuteTask("DS");
      for (Int_t i=0; i< T->GetEntries(); i++) {
          genfit::Track* aTrack = (genfit::Track*)T->At(i);
          auto state = aTrack->getFittedState();
          auto pos = state.getPos();
          auto mom = state.getMom();
          std::cout<<"aTrack "<<aTrack->getNumPoints()<<std::endl;
          pos.Print();
          mom.Print();
      }
   }
}
