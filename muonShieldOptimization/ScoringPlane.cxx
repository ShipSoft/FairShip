#include "ScoringPlane.h"
 #include <math.h>
 #include "vetoPoint.h"

 #include "FairLogger.h"                 // for FairLogger, MESSAGE_ORIGIN
 #include "FairVolume.h"
 #include "FairGeoVolume.h"
 #include "FairGeoNode.h"
 #include "FairRootManager.h"
 #include "FairGeoLoader.h"
 #include "FairGeoInterface.h"
 #include "FairGeoMedia.h"
 #include "FairGeoBuilder.h"
 #include "FairRun.h"
 #include "FairRuntimeDb.h"
 #include "ShipDetectorList.h"
 #include "ShipStack.h"

 #include "TClonesArray.h"
 #include "TVirtualMC.h"
 #include "TGeoManager.h"
 #include "TGeoBBox.h"
 #include "TGeoEltu.h"
 #include "TGeoBoolNode.h"
 #include "TGeoMaterial.h"
 #include "TParticle.h"
 #include "TROOT.h"
 #include "TH1D.h"
 #include "TH2D.h"
 #include "TDatabasePDG.h"

 #include <iostream>
 using std::cout;
 using std::endl;

 ScoringPlane::ScoringPlane()
   : FairDetector("ScoringPlane", kTRUE, kVETO),
     fTrackID(-1),
     fVolumeID(-1),
     fPos(),
     fMom(),
     fTime(-1.),
     fLength(-1.),
     fELoss(-1.),
     fOnlyMuons(kFALSE),
     //fSkipNeutrinos(kFALSE),
     fzPos(3E8),
     withNtuple(kFALSE),
     fScoringPlanePointCollection(new TClonesArray("vetoPoint")),
     fLastDetector(kFALSE),
     fFastMuon(kFALSE),
     fFollowMuon(kFALSE),
     fVetoName("veto"),
     fLx(999.9), // cm
     fLy(999.9), // cm
     fLz(000.1)  // cm
 {}

 ScoringPlane::ScoringPlane(const char* name, Bool_t active, Bool_t islastdetector)
     : FairDetector(name, active, kVETO),
     fTrackID(-1),
     fVolumeID(-1),
     fPos(),
     fMom(),
     fTime(-1.),
     fLength(-1.),
     fELoss(-1.),
     fOnlyMuons(kFALSE),
     //fSkipNeutrinos(kFALSE),
     fzPos(3E8),
     withNtuple(kFALSE),
     fScoringPlanePointCollection(new TClonesArray("vetoPoint")),
     fLastDetector(islastdetector),
     fFastMuon(kFALSE),
     fFollowMuon(kFALSE),
     fVetoName("veto"),
     fLx(999.9), // cm
     fLy(999.9), // cm
     fLz(000.1)  // cm
 {}

 ScoringPlane::ScoringPlane(const char* name, Bool_t active, Bool_t islastdetector,
                                        Double_t Lx=999.9, Double_t Ly=999.9, Double_t Lz=0.1)
     : FairDetector(name, active, kVETO),
     fTrackID(-1),
     fVolumeID(-1),
     fPos(),
     fMom(),
     fTime(-1.),
     fLength(-1.),
     fELoss(-1.),
     fOnlyMuons(kFALSE),
     //fSkipNeutrinos(kFALSE),
     fzPos(3E8),
     withNtuple(kFALSE),
     fScoringPlanePointCollection(new TClonesArray("vetoPoint")),
     fLastDetector(islastdetector),
     fFastMuon(kFALSE),
     fFollowMuon(kFALSE),
     fVetoName("veto")
 {
     fLx = Lx; // cm
     fLy = Ly; // cm
     fLz = Lz; // cm
 }

 ScoringPlane::~ScoringPlane()
 {
   if (fScoringPlanePointCollection) {
     fScoringPlanePointCollection->Delete();
     delete fScoringPlanePointCollection;
   }
 }

 Bool_t  ScoringPlane::ProcessHits(FairVolume* vol)
 {
   /** This method is called from the MC stepping */
   //Set parameters at entrance of volume. Reset ELoss.
   if ( gMC->IsTrackEntering() ) {
     fELoss  = 0.;
     fTime   = gMC->TrackTime() * 1.0e09;
     fLength = gMC->TrackLength();
     gMC->TrackPosition(fPos);
     gMC->TrackMomentum(fMom);
   }
   // Sum energy loss for all steps in the active volume
   fELoss += gMC->Edep();

   // Create vetoPoint when exiting active volume
   if ( gMC->IsTrackExiting()    ||
        gMC->IsTrackStop()       || 
        gMC->IsTrackDisappeared()   ) {

        // if (fELoss == 0. ) { return kFALSE; } // if you do not want hits with zero eloss

        TParticle* p = gMC->GetStack()->GetCurrentTrack();
        Int_t pdgCode = p->GetPdgCode();
        if (!(fOnlyMuons && TMath::Abs(pdgCode)!=13)){ 
          fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();
          Int_t detID;
          gMC->CurrentVolID(detID);
          TLorentzVector Pos;
          gMC->TrackPosition(Pos);
          TLorentzVector Mom;
          gMC->TrackMomentum(Mom);
          Double_t xmean = (fPos.X()+Pos.X())/2. ;
          Double_t ymean = (fPos.Y()+Pos.Y())/2. ;
          Double_t zmean = (fPos.Z()+Pos.Z())/2. ;

          AddHit(fTrackID, detID,
             //TVector3(xmean, ymean, zmean), put entrance and exit instead
               TVector3(fPos.X(), fPos.Y(), fPos.Z()),     // entrance position
               TVector3(fMom.Px(), fMom.Py(), fMom.Pz()),  // entrance momentum
               fTime, fLength, fELoss,pdgCode,
               TVector3(Pos.X(),Pos.Y(),Pos.Z()),          // exit position
               TVector3(Mom.Px(), Mom.Py(), Mom.Pz()) );   // exit momentum
          ShipStack* stack = (ShipStack*) gMC->GetStack();
          stack->AddPoint(kVETO);
        }
   }
   if (fLastDetector) gMC->StopTrack();
   return kTRUE;
 }

 void ScoringPlane::Initialize()
 {
   FairDetector::Initialize();
   TDatabasePDG* PDG = TDatabasePDG::Instance();
 }

 void ScoringPlane::EndOfEvent()
 {
   //std::cout << this->GetName() << this->GetName() << " EndOfEvent(): point collection has " << fScoringPlanePointCollection->GetEntries() << " entries" << std::endl;
   fScoringPlanePointCollection->Clear();
 }

 void ScoringPlane::PreTrack(){
     if (!fFastMuon){return;}
     if (TMath::Abs(gMC->TrackPid())!=13){
         gMC->StopTrack();
     }
 }

 void ScoringPlane::ConstructGeometry()
 {
    static FairGeoLoader *geoLoad=FairGeoLoader::Instance();
    static FairGeoInterface *geoFace=geoLoad->getGeoInterface();
    static FairGeoMedia *media=geoFace->getMedia();
    static FairGeoBuilder *geoBuild=geoLoad->getGeoBuilder();

    FairGeoMedium *ShipMedium=media->getMedium("vacuums");
    TGeoMedium* vac=gGeoManager->GetMedium("vacuums");
    if (vac==NULL) geoBuild->createMedium(ShipMedium);
    vac =gGeoManager->GetMedium("vacuums");
    TGeoVolume *top=gGeoManager->GetTopVolume();
    TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
    Double_t zLoc;
 /*
    if (fzPos>1E8){
       Float_t distance = 1.;
       Double_t local[3]= {0,0,0};
       if (not nav->cd("/MuonShieldArea_1/CoatWall_1")) {
         nav->cd("/MuonShieldArea_1/MagnAbsorb2_MagRetL_1");
         distance = -1.;
         std::cout << this->GetName() << ", ScoringPlane::ConstructGeometry(), WARNING: I don't know what we are doing in /MuonShieldArea_1/MagnAbsorb2_MagRetL_1" << std::endl;
       }
       TGeoBBox* tmp =  (TGeoBBox*)(nav->GetCurrentNode()->GetVolume()->GetShape());
       local[2] = distance * tmp->GetDZ();
       Double_t global[3] = {0,0,0};
       nav->LocalToMaster(local,global);
       zLoc = global[2] + distance; // cm
    }else{ zLoc = fzPos;} // use external input
 */
    zLoc = fzPos; // use external input
    TString myname(this->GetName());
    TString boxname( myname+"_box");
    TGeoVolume *sensPlane = gGeoManager->MakeBox(boxname,vac,fLx,fLy,fLz);
    sensPlane->SetLineColor(kBlue-10);
 /*
    if (nav->cd("/MuonShieldArea_1/")){
       nav->cd("/MuonShieldArea_1/");
       std::cout << this->GetName() << "WARNING: Massi from ScoringPlane::ConstructGeometry() says: I don't know what we are doing in MuonShieldArea_1..." << std::endl;
    }
    if (nav->cd("/Tunnel_1/")){ 
       nav->cd("/Tunnel_1/");
       std::cout << this->GetName() << "Massi from ScoringPlane::ConstructGeometry() says: cd to Tunnel_1" << std::endl;
    }
 */
    //nav->cd("/MuonShieldArea_1/"); Massi: does this always exist ?
    nav->GetCurrentNode()->GetVolume()->AddNode(sensPlane, 1, new TGeoTranslation(0, 0, zLoc));
    AddSensitiveVolume(sensPlane);

 // only for fastMuon simulation, otherwise output becomes too big
    if (fFastMuon && fFollowMuon){
        const char* Vol  = "TGeoVolume";
        const char* Mag  = "Mag";
        const char* Rock = "rock";
        const char* Shi  = "Shi"; // added by Massi, for shielding
        const char* Coi  = "Coi"; // added by Massi, for coil
        const char* Ram  = "Ram"; // added by Massi, for all Ram pieces, including Hadron Stopper
        const char* Ain  = "AbsorberAdd";
        const char* Aout = "AbsorberAddCore";
        TObjArray* volumelist = gGeoManager->GetListOfVolumes();
        int lastvolume = volumelist->GetLast();
        int volumeiterator=0;
        while ( volumeiterator<=lastvolume ) {
         const char* volumename = volumelist->At(volumeiterator)->GetName();
         const char* classname  = volumelist->At(volumeiterator)->ClassName();
         if (strstr(classname,Vol)){
          if (strstr(volumename,Mag) || strstr(volumename,Rock)|| strstr(volumename,Ain) || strstr(volumename,Aout)
                                     || strstr(volumename,Shi) || strstr(volumename,Coi) || strstr(volumename,Ram) )
          {
            AddSensitiveVolume(gGeoManager->GetVolume(volumename));
            cout << this->GetName() << ", ConstructGeometry(): made sensitive for following muons: "<< volumename <<endl;
          }
         }
         volumeiterator++;
        }
    }


 }

 vetoPoint* ScoringPlane::AddHit(Int_t trackID, Int_t detID,
                                       TVector3 pos, TVector3 mom,
                                       Double_t time, Double_t length,
                                       Double_t eLoss, Int_t pdgCode,TVector3 Lpos, TVector3 Lmom)
 {
   TClonesArray& clref = *fScoringPlanePointCollection;
   Int_t size = clref.GetEntriesFast();
   return new(clref[size]) vetoPoint(trackID, detID, pos, mom,
          time, length, eLoss, pdgCode,Lpos,Lmom);
 }

 void ScoringPlane::Register()
 {

   //FairRootManager::Instance()->Register("vetoPoint", "veto",
   //                                    fScoringPlanePointCollection, kTRUE);
   TString name  = fVetoName+"Point";
   TString title = fVetoName;
   FairRootManager::Instance()->Register(name, title, fScoringPlanePointCollection, kTRUE);
   std::cout << this->GetName() << ",  Register() says: registered " << fVetoName <<" collection"<<std::endl;
 }

 TClonesArray* ScoringPlane::GetCollection(Int_t iColl) const
 {
   if (iColl == 0) { return fScoringPlanePointCollection; }
   else { return NULL; }
 }
 void ScoringPlane::Reset()
 {
   fScoringPlanePointCollection->Clear();
 }


 ClassImp(ScoringPlane)