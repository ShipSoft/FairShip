#include "MufluxReco.h"
#include <TROOT.h>
#include <TChain.h>
#include <TH1D.h>
#include <TH2D.h>
#include "TObject.h"
#include "TrackInfo.h"
#include "RPCTrack.h"
#include "RKTrackRep.h"

TVector3 parallelToZ = TVector3(0., 0., 1.);
// -----   Standard constructor   ------------------------------------------ 
MufluxReco::MufluxReco() {}
// -----   Standard constructor   ------------------------------------------ 
MufluxReco::MufluxReco(TTreeReader* t)
{
  xSHiP = t;
  MCdata = false;
  if (xSHiP->GetTree()->GetBranch("MCTrack")){MCdata=true;}
  std::cout << "MufluxReco initialized for "<<xSHiP->GetEntries(true) << " events "<<std::endl;
  xSHiP->ls();
}
/* 

MufluxReco::getKeys(std::unordered_map<int,MufluxSpectrometerHit*>> map){
 std::vector<int> keys;
 keys.reserve(map.size());
 std::vector<std::string> vals;
 vals.reserve(allHits.size());
 for(auto kv : allHits) {
    keys.push_back(kv.first);
    vals.push_back(kv.second);  
}

Double_t MufluxReco::extrapolateToPlane(genfit::Track* fT,Float_t z, TVector3* pos, TVector3* mom){
// etrapolate to a plane perpendicular to beam direction (z)
  Double_t rc = -1;
  auto fst = fT->getFitStatus();
  if (fst->isFitConverged()){
   if (z > cuts["firstDTStation_z"]-10 and z < cuts["lastDTStation_z"] + 10){
// find closest measurement
    Float_t mClose = 0;
    Float_t mZmin = 999999.;
    for (Int_t m=0;m<fT->getNumPointsWithMeasurement();m++) {
      auto st  = fT->getFittedState(m);
      auto Pos = st.getPos();
      if (TMath::Abs(z-Pos.z())<mZmin){
       mZmin = TMath::Abs(z-Pos.z());
       mClose = m;
      }
    }
    auto fstate =  fT->getFittedState(mClose);
    TVector3 NewPosition = TVector3(0., 0., z);
    Int_t pdgcode = -int(13*fstate.getCharge());
    genfit::RKTrackRep* rep      = new genfit::RKTrackRep( pdgcode );
    genfit::StateOnPlane* state   = new genfit::StateOnPlane(rep);
    auto Pos = fstate->getPos();
    auto Mom = fstate->getMom();
    rep->setPosMom(state,Pos,Mom);
    rc = rep->extrapolateToPlane(state, NewPosition, parallelToZ );
    pos = state->getPos();
    mom = state->getMom();
   }else{
    if (z < cuts["firstDTStation_z"]){
     auto fstate = fT.getFittedState(0);
    }else if(z > cuts["lastDTStation_z"]){
     M = min(fT->getNumPointsWithMeasurement()-1,30)
     fstate = fT->getFittedState(fT.getNumPointsWithMeasurement()-1);
    }
    pos = fstate->getPos();
    mom = fstate->getMom();
// use linear extrap 
    Float_t lam = (z-pos[2])/mom[2];
    pos[2]=z;
    pos[0]=pos[0]+lam*mom[0];
    pos[1]=pos[1]+lam*mom[1];
    rc = 0;
  }
  return rc;
}




std::unordered_map<std::string,std::vector<int>> MufluxReco::countMeasurements(TrackInfo* trInfo){
 mStatistics = std::unordered_map<std::string,std::vector<int>>();
 for (Int_t n=0;n<trInfo->N();n++) {
    detID = trInfo->detId(n);
    (MufluxSpectrometerHit)hit = MufluxSpectrometerHit(detID,0);
    auto info = hit->StationInfo();
    Int_t s=info[0]; Int_t v=info[1]; Int_t p=info[2]; Int_t l=info[3]; Int_t channelNr=info[5]; 
    if (trInfo->wL(n) <0.1 && trInfo->wR(n) <0.1){ continue;}
    if (v != 0){ 
       mStatistics["uv"].push_back(detID);
       if (v == 1) { mStatistics["u"].push_back(detID);}
       if (v == 2) { mStatistics["v"].push_back(detID);}
    }else{
     mStatistics["xAll"].push_back(detID);
     mStatistics["x"+std::string(s)].push_back(detID);
    }
    if (s > 2){  
       mStatistics["xDown"].push_back(detID);
    }else{
       mStatistics["xUp"].push_back(detID);
    }
 }
 return mStatistics;
}


void MufluxReco::trackKinematics(Float_t chi2UL){
 Int_t N = xSHiP->GetEntries(true);
 xSHiP->Restart();
 std::cout<< "fill trackKinematics: "<< N <<std::endl;
 TTreeReaderArray <genfit::Track> FitTracks(*xSHiP, "FitTracks");
 TTreeReaderArray <RPCTrack> RPCTrackX(*xSHiP, "RPCTrackX");
 TTreeReaderArray <RPCTrack> RPCTrackY(*xSHiP, "RPCTrackY");
 TTreeReaderArray <TrackInfo> TrackInfos(*xSHiP, "TrackInfos");
 while (xSHiP->Next()){
   for (Int_t k=0;k<FitTracks.GetSize();k++) {
   //if MCdata and PR<10 and sTree.ShipEventHeader.GetUniqueID()==1: continue # non reconstructed events 
     genfit::Track* aTrack = &(FitTracks[k]);
     auto fitStatus   = aTrack->getFitStatus();
// track quality
     if (!fitStatus->isFitConverged()){continue;}
     std::unordered_map<std::string,std::vector<int>> hitsPerStation = countMeasurements(N);
     if (hitsPerStation["x1"].size()<2){ continue;}
     if (hitsPerStation["x2"].size()<2){ continue;}
     if hitsPerStation["x3"].size()<2){ continue;}
     if hitsPerStation["x4"].size()<2){ continue;}
     auto chi2 = fitStatus->getChi2()/fitStatus->getNdf();
     auto fittedState = aTrack->getFittedState();
     Float_t P = fittedState.getMomMag();
     Float_t Px = fittedState.getMom().x();
     Float_t Py = fittedState.getMom().y();
     Float_t Pz = fittedState.getMom().z();
     TH1D* h =  (TH1D*)(gROOT->FindObject("chi2"));
     h->Fill(chi2);
     h = (TH1D*)(gROOT->FindObject("Nmeasurements"));
     h->Fill(fitStatus->getNdf());
     if (chi2 > chi2UL){ continue;}
     TH2D* h2 = (TH2D*)(gROOT->FindObject("p/pt"));
     h2->Fill(P,TMath::Sqrt(Px*Px+Py*Py));
     auto pos = fittedState.getPos();
     h2 = (TH2D*)(gROOT->FindObject("xy"));
     h2->Fill(pos[0],pos[1]);
     h2 = (TH2D*)(gROOT->FindObject("pxpy"));
     h2->Fill(Px/Pz,Py/Pz);
// check for muon tag
// !!! missing     rc,posRPC,momRPC = extrapolateToPlane(FitTracks->At(k),zRPC1)
     Int_t rc = -1;
     Float_t X =-1000;
     Float_t Y =-1000;
     if (RPCTrackX.GetSize()>0){X = RPCTrackX[0].m()*cuts["zRPC1"]+RPCTrackX[0].b();}
     if (RPCTrackY.GetSize()>0){Y = RPCTrackY[0].m()*cuts["zRPC1"]+RPCTrackY[0].b();}
     if (rc){
       if (TMath::Abs(posRPC[0]-X)<5. && TMath::Abs(posRPC[1]-Y)<10.) { // within ~3sigma  X,Y from mutrack
        h = (TH1D*)(gROOT->FindObject("chi2mu"));
        h->Fill(chi2);
        h = (TH1D*)(gROOT->FindObject("Nmeasurementsmu"));
        h->Fill(fitStatus.getNdf());
        h2=(TH2D*)(gROOT->FindObject("p/ptmu"));
        h2->Fill(P,ROOT.TMath.Sqrt(Px*Px+Py*Py));
        h2=(TH2D*)(gROOT->FindObject("xymu"));
        h2->Fill(pos[0],pos[1]);
        h2=(TH2D*)(gROOT->FindObject("pxpymu"));
        h2->Fill(Px/Pz,Py/Pz);
      }
     }
//
     if (FitTracks.GetSize()==2 && k==0){
      auto fitStatus   = &(FitTracks[1])->getFitStatus()
      if (!fitStatus->isFitConverged()){ continue;}
      Float_t chi2 = fitStatus->getChi2()/float(fitStatus->getNdf());
      if (chi2 > chi2UL){ continue;}
      auto fittedStateb = theTracks[1].getFittedState();
      Float_t Pb = fittedStateb.getMomMag();
      Float_t Pbx = fittedStateb.getMom()->x();
      Float_t Pby = fittedStateb.getMom()->y();
      Float_t Pbz = fittedStateb.getMom()->z();
      (TH2D*)(gROOT->FindObject("p1/p2"))->Fill(P,Pb);
      (TH2D*)(gROOT->FindObject("pt1/pt2"))->Fill(TMath::Sqrt(Px*Px+Py*Py),TMath::Sqrt(Pbx*Pbx+Pby*Pby));
     }
   }
 }
}
*/

void MufluxReco::sortHits(TClonesArray* hits, nestedList* l, Bool_t flag){
  nestedList spectrHitsSorted = *l;
 //spectrHitsSorted = {'_x':{1:{0:[],1:[],2:[],3:[]},2: {0:[],1:[],2:[],3:[]},3: {0:[],1:[],2:[],3:[]},4: {0:[],1:[],2:[],3:[]}},\
 //                    '_u':{1:{0:[],1:[],2:[],3:[]},2: {0:[],1:[],2:[],3:[]},3: {0:[],1:[],2:[],3:[]},4: {0:[],1:[],2:[],3:[]}},\
 //                    '_v':{1:{0:[],1:[],2:[],3:[]},2: {0:[],1:[],2:[],3:[]},3: {0:[],1:[],2:[],3:[]},4: {0:[],1:[],2:[],3:[]}}}
 for (Int_t k=0;k<hits->GetEntries();k++) {
   MufluxSpectrometerHit* hit = (MufluxSpectrometerHit*)hits->At(k);
   if ( !hit->isValid() && MCdata){continue;}
   if (flag && !MCdata){
    if (!hit->hasTimeOverThreshold() || !hit->hasDelay() || !hit->hasTrigger() ){ continue;} // no reliable TDC measuerement
  // remove noise hits
    auto result = std::find( noisyChannels.begin(), noisyChannels.end(), hit->GetDetectorID() );
    if ( result !=  noisyChannels.end()){ continue;}
   }
   if (hit->GetTimeOverThreshold() < cuts["tot"]) { continue;}
   auto info = hit->StationInfo();
   // info[0],info[1],info[2],info[3],viewDict[info[4]],info[5],info[6],info[7]
   // statnb,   vnb,    pnb,    lnb,    view,         channelID,tdcId,moduleId
   if (info[2] > 1 || info[3] >1){
    std::cout<< "sortHits: unphysical detctor ID "<<hit->GetDetectorID()<<std::endl;
    hit->Dump();
   }else{
    spectrHitsSorted[info[4]][info[0]][info[2]*2+info[3]].push_back(hit);
  }
 }
 *l = spectrHitsSorted;
}

void MufluxReco::fillHitMaps()
{ 
 Float_t deadThreshold = 1.E-4; // ~1% typical occupancy
 Int_t N = xSHiP->GetEntries(true);
 xSHiP->Restart();
 gROOT->cd();
 std::cout<< "fillHitMaps: "<< N  <<std::endl;
 TTreeReaderArray <MufluxSpectrometerHit> Digi_MufluxSpectrometerHits(*xSHiP, "Digi_MufluxSpectrometerHits");
 TTreeReaderValue <FairEventHeader> MCShipEventHeader(*xSHiP, "ShipEventHeader");
 TTreeReaderValue <FairEventHeader> rvShipEventHeader(*xSHiP, "EventHeader.");
 while (xSHiP->Next()){
   for (Int_t k=0;k<Digi_MufluxSpectrometerHits.GetSize();k++) {
     MufluxSpectrometerHit* hit = &(Digi_MufluxSpectrometerHits[k]);
     auto info = hit->StationInfo();
     Int_t s=info[0]; Int_t v=info[1]; Int_t p=info[2]; Int_t l=info[3]; Int_t channelNr=info[5]; 
     Int_t tdcId=info[6]; Int_t moduleId=info[7];
     TString view = "_x"; 
     if (info[4]==1){view="_u";}
     if (info[4]==2){view="_v";}
     TString tot = "";
     if (!hit->hasTimeOverThreshold()){ tot = "_noToT";}
     TString histo; histo.Form("%d",1000*s+100*p+10*l);histo+=view;
     TH1D* h = (TH1D*)(gROOT->FindObject(histo));
     if (!h){
       std::cout<< "fillHitMaps: ERROR histo not known "<< histo  <<std::endl;
       continue;
     }
     h->Fill(channelNr);
     auto check = std::find( noisyChannels.begin(), noisyChannels.end(), hit->GetDetectorID() );
     if (check!=noisyChannels.end()){ continue;}
     Float_t t0 = 0;
     if (MCdata){
       FairEventHeader * header = (FairEventHeader *) MCShipEventHeader.Get(); 
       t0 = header->GetEventTime();
     }
     TString TDChisto = "TDC"; TDChisto+=histo;TDChisto+=moduleId+tot;
     h = (TH1D*)(gROOT->FindObject(TDChisto));
     if (!h){
       std::cout<< "fillHitMaps: ERROR histo not known "<< TDChisto  <<std::endl; 
       continue;
     }
     h->Fill( hit->GetDigi()-t0);
     TString channel = "TDC";channel+=hit->GetDetectorID();
     h = (TH1D*)(gROOT->FindObject(channel));
     h->Fill( hit->GetDigi()-t0);
   }
  }
}
// -----   Destructor   ----------------------------------------------------
MufluxReco::~MufluxReco() { }
// -------------------------------------------------------------------------

 
ClassImp(MufluxReco) 
