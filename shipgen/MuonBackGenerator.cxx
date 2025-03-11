#include <math.h>
#include "TSystem.h"
#include "TROOT.h"
#include "TRandom.h"
#include "TFile.h"
#include "TVector.h"
#include "FairPrimaryGenerator.h"
#include "MuonBackGenerator.h"
#include "TDatabasePDG.h"               // for TDatabasePDG
#include "TMath.h"                      // for Sqrt
#include "vetoPoint.h"
#include "ShipMCTrack.h"
#include "TMCProcess.h"
#include <algorithm>
#include <unordered_map>

// read events from Pythia8/Geant4 base simulation (only target + hadron absorber

// -----   Default constructor   -------------------------------------------
MuonBackGenerator::MuonBackGenerator() {
 followMuons = true;
}
// -------------------------------------------------------------------------
// -----   Default constructor   -------------------------------------------
Bool_t MuonBackGenerator::Init(const char* fileName) {
  return Init(fileName, 0, false);
}
// -----   Default constructor   -------------------------------------------
Bool_t MuonBackGenerator::Init(const char* fileName, const int firstEvent, const Bool_t fl = false ) {
    LOG(info) << "Opening input file " << fileName;
    fInputFile = TFile::Open(fileName);
    if (!fInputFile) {
        LOG(fatal) << "Error opening the Signal file: " << fileName;
    }
  fn = firstEvent;
  fPhiRandomize = fl;
  fSameSeed = 0;
  fsmearBeam = 0; // default no beam smearing, use SetSmearBeam(sb) if different, sb [cm]
  fdownScaleDiMuon = kFALSE; // only needed for muflux simulation
  fTree = fInputFile->Get<TTree>("pythia8-Geant4");
  if (fTree){
   fNevents = fTree->GetEntries();
   // count only events with muons
   fTree->SetBranchAddress("id",&id);                // particle id
   fTree->SetBranchAddress("parentid",&parentid);    // parent id, could be different
   fTree->SetBranchAddress("pythiaid",&pythiaid);    // pythiaid original particle
   fTree->SetBranchAddress("ecut",&ecut);    // energy cut used in simulation
   fTree->SetBranchAddress("w",&w);                  // weight of event
//  check if ntuple has information of momentum at origin
   if (fTree->GetListOfLeaves()->GetSize() < 17){
    fTree->SetBranchAddress("x",&vx);   // position with respect to startOfTarget at -89.27m
    fTree->SetBranchAddress("y",&vy);
    fTree->SetBranchAddress("z",&vz);
    fTree->SetBranchAddress("px",&px);   // momentum
    fTree->SetBranchAddress("py",&py);
    fTree->SetBranchAddress("pz",&pz);
   }else{
    fTree->SetBranchAddress("ox",&vx);   // position with respect to startOfTarget at -50m
    fTree->SetBranchAddress("oy",&vy);
    fTree->SetBranchAddress("oz",&vz);
    fTree->SetBranchAddress("opx",&px);   // momentum
    fTree->SetBranchAddress("opy",&py);
    fTree->SetBranchAddress("opz",&pz);
   }
  }else{
   id = -1;
   fTree = fInputFile->Get<TTree>("cbmsim");
   fNevents   = fTree->GetEntries();
   MCTrack = new TClonesArray("ShipMCTrack");
   vetoPoints = new TClonesArray("vetoPoint");
   fTree->SetBranchAddress("MCTrack",&MCTrack);
   fTree->SetBranchAddress("vetoPoint",&vetoPoints);
  }
  return kTRUE;
}
// -----   Destructor   ----------------------------------------------------
MuonBackGenerator::~MuonBackGenerator()
{
}
// -------------------------------------------------------------------------
Bool_t MuonBackGenerator::checkDiMuon(Int_t muIndex){
   Bool_t check = false;
   auto* mu = dynamic_cast<ShipMCTrack*>(MCTrack->At(muIndex));
   TString pName = mu->GetProcName();
   if ( strncmp("Hadronic inelastic",    pName.Data(),18)==0 ||
        strncmp("Positron annihilation" ,pName.Data(),21)==0 ||
        strncmp("Lepton pair production",pName.Data(),22)==0){
           check = true;}
   Int_t Pcode = TMath::Abs( (dynamic_cast<ShipMCTrack*>(MCTrack->At(mu->GetMotherId()))->GetPdgCode()));
   if (Pcode==221 || Pcode==223 || Pcode==333 || Pcode==113 || Pcode == 331){
           check = true;}
   return check;
}

// -----   Passing the event   ---------------------------------------------
Bool_t MuonBackGenerator::ReadEvent(FairPrimaryGenerator* cpg)
{
    auto* pdgBase = TDatabasePDG::Instance();
    Double_t mass, e, tof, phi;
    Double_t dx = 0, dy = 0;
    std::unordered_map<int, int> muList;
    std::unordered_map<int, std::vector<int>> moList;
    while (fn < fNevents) {
        fTree->GetEntry(fn);
        muList.clear();
        moList.clear();
        fn++;
        if (fn % 100000 == 0) {
            LOGF(info, "Reading event %i", fn);
        }
        // test if we have a muon, don't look at neutrinos:
        if (TMath::Abs(int(id)) == 13) {
            mass = pdgBase->GetParticle(id)->Mass();
            e = TMath::Sqrt(px * px + py * py + pz * pz + mass * mass);
            tof = 0;
            break;
        }
        if (id == -1) {   // use tree as input file
            Bool_t found = false;
            for (int i = 0; i < vetoPoints->GetEntries(); i++) {
                auto* v = dynamic_cast<vetoPoint*>(vetoPoints->At(i));
                Int_t abspid = TMath::Abs(v->PdgCode());
                if (abspid == 13 or (not followMuons and abspid != 12 and abspid != 14)) {
                    found = true;
                    Int_t muIndex = v->GetTrackID();
                    if (!fdownScaleDiMuon) {
                        muList.insert({muIndex, i});
                    } else if (abspid == 13) {
                        if (checkDiMuon(muIndex)) {
                            moList[(dynamic_cast<ShipMCTrack*>(MCTrack->At(muIndex)))->GetMotherId()].push_back(i);
                        } else {
                            muList.insert({muIndex, i});
                        }
                    }
                }
            }
            // reject muon if comes from boosted channel

            for (auto it = moList.begin(); it != moList.end(); it++) {
                if (gRandom->Uniform(0., 1.) > 0.99) {
                    std::vector<int> list = it->second;
                    for (Int_t i = 0; i < list.size(); i++) {
                        auto* v = dynamic_cast<vetoPoint*>(vetoPoints->At(list.at(i)));
                        Int_t muIndex = v->GetTrackID();
                        muList.insert({muIndex, i});
                    }
                }
            }
            if (!found) {
                LOGF(warn, "No muon found %i", fn - 1);
            }
            if (found) {
                break;
            }
        }
  }
  if (fn>fNevents-1){
     LOGF(info, "End of file reached %i", fNevents);
     return kFALSE;
  }
  if (fSameSeed) {
    Int_t theSeed = fn + fSameSeed * fNevents;
    LOGF(debug, "Seed: %d", theSeed);
    gRandom->SetSeed(theSeed);
  }
  if (fPhiRandomize){phi = gRandom->Uniform(0.,2.) * TMath::Pi();}
  if (fsmearBeam > 0) {
     Double_t r = fsmearBeam + 0.8 * gRandom->Gaus();
     Double_t _phi = gRandom->Uniform(0., 2.) * TMath::Pi();
     dx = r * TMath::Cos(_phi);
     dy = r * TMath::Sin(_phi);
  }
  if (id==-1){
     for (unsigned i = 0; i< MCTrack->GetEntries();  i++ ){
         auto* track = dynamic_cast<ShipMCTrack*>(MCTrack->At(i));
         Int_t abspid = TMath::Abs(track->GetPdgCode());
         px = track->GetPx();
         py = track->GetPy();
         pz = track->GetPz();
         if (fPhiRandomize) {
             Double_t phi0 = TMath::ATan2(py, px);
             Double_t pt = track->GetPt();
             px = pt * TMath::Cos(phi + phi0);
             py = pt * TMath::Sin(phi + phi0);
       }
       vx = track->GetStartX()+dx;
       vy = track->GetStartY()+dy;
       vz = track->GetStartZ();
       tof =  track->GetStartT()/1E9; // convert back from ns to sec;
       e = track->GetEnergy();
       Bool_t wanttracking = false; // only transport muons
       for (std::pair<int, int> element : muList){
         if (element.first==i){
          wanttracking = true;
          if (not followMuons){
              auto* v = dynamic_cast<vetoPoint*>(vetoPoints->At(element.second));
              TVector3 lpv = v->LastPoint();
              TVector3 lmv = v->LastMom();
              if (abspid == 22) {
                  e = lmv.Mag();}
           else{ e = TMath::Sqrt(lmv.Mag2()+(track->GetMass())*(track->GetMass()));}
           px = lmv[0];
           py = lmv[1];
           pz = lmv[2];
           vx = lpv[0];
           vy = lpv[1];
           vz = lpv[2];
           tof =  v->GetTime()/1E9; // convert back from ns to sec
          }
          break;
        }
       }
       cpg->AddTrack(track->GetPdgCode(),px,py,pz,vx,vy,vz,track->GetMotherId(),wanttracking,e,tof,track->GetWeight(),(TMCProcess)track->GetProcID());
     }
  }else{
    vx += dx/100.;
    vy += dy/100.;
    if (fPhiRandomize){
     Double_t pt  = TMath::Sqrt( px*px+py*py );
     px = pt*TMath::Cos(phi);
     py = pt*TMath::Sin(phi);
    }
    cpg->AddTrack(int(pythiaid),px,py,pz,vx*100.,vy*100.,vz*100.,-1.,false,e,pythiaid,parentid);
    cpg->AddTrack(int(id),px,py,pz,vx*100.,vy*100.,vz*100.,-1.,true,e,tof,w);
  }
  return kTRUE;
}

// -------------------------------------------------------------------------
Int_t MuonBackGenerator::GetNevents()
{
 return fNevents;
}
void MuonBackGenerator::CloseFile()
{
 fInputFile->Close();
 fInputFile->Delete();
 delete fInputFile;
}
