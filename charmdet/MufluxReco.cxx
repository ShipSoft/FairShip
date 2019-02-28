#include "MufluxReco.h"
#include <TROOT.h>
#include <TChain.h>
#include <TH1D.h>
#include <TH2D.h>
#include <TH3D.h>
#include "TRandom1.h"
#include "TRandom3.h"
#include "TString.h"
#include "TObject.h"
#include "RPCTrack.h"
#include "RKTrackRep.h"
#include "ShipMCTrack.h"
#include "MufluxSpectrometerHit.h"
#include "MuonTaggerHit.h"
#include <algorithm>
#include <vector>

TVector3* parallelToZ = new TVector3(0., 0., 1.);
TVector3* NewPosition = new TVector3(0., 0., 0.);
std::vector<int> charmExtern = {4332,4232,4132,4232,4122,431,411,421};
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
  FitTracks = 0;
  TrackInfos = 0;
  RPCTrackY = 0;
  RPCTrackX = 0;
  MCTrack = 0;
  Digi_MuonTaggerHits = 0;
  cDigi_MufluxSpectrometerHits = 0;
  TTree* fChain = xSHiP->GetTree();
  if (MCdata){fChain->SetBranchAddress("MCTrack", &MCTrack, &b_MCTrack);}
  fChain->SetBranchAddress("FitTracks", &FitTracks, &b_FitTracks);
  fChain->SetBranchAddress("Digi_MufluxSpectrometerHits", &cDigi_MufluxSpectrometerHits, &b_Digi_MufluxSpectrometerHits);
  fChain->SetBranchAddress("Digi_MuonTaggerHits", &Digi_MuonTaggerHits, &b_Digi_MuonTaggerHits);
  fChain->SetBranchAddress("TrackInfos", &TrackInfos, &b_TrackInfos);
  fChain->SetBranchAddress("RPCTrackY", &RPCTrackY, &b_RPCTrackY);
  fChain->SetBranchAddress("RPCTrackX", &RPCTrackX, &b_RPCTrackX);
}

/*
std::vector<int> MufluxReco::getKeys(std::unordered_map<int,MufluxSpectrometerHit*>> map){
 std::vector<int> keys;
 keys.reserve(map.size());
 std::vector<std::string> vals;
 vals.reserve(allHits.size());
 for(auto kv : allHits) {
    keys.push_back(kv.first);
    vals.push_back(kv.second);
 return  keys;
}*/

// Sort and group integers in arrays iff a[j] - a[i] <= span, where j > i >=0
std::vector<std::vector<int>> MufluxReco::GroupIntegers(std::vector<int>& input_array, size_t span) {
    if (input_array.empty())
        return std::vector<std::vector<int>>();
    if (input_array.size() == 1)
        return {{input_array[0]}};

    std::sort(input_array.begin(), input_array.end());

    std::vector<std::vector<int>> output;
    std::vector<int> running_array = {input_array[0]};

    for (size_t index = 1; index < input_array.size(); ++index) {
        if (input_array[index] - input_array[index - 1] > span) {
            output.emplace_back(running_array);
            running_array.clear();
        }
        running_array.push_back(input_array[index]);
    }
    output.emplace_back(running_array);
    return output;
}
/* unfinished C++ conversion
std::map<int,std::vector<int>> viewsI = { {1,{0,1}},{2,{0,2}},{3,{0}},{4,{0}} };
std::unordered_map<int,int> Nchannels = { {1,12},{2,12},{3,48},{4,48}};


std::vector<std::vector<int>>  MufluxReco::findDTClusters(TClonesArray* hits, removeBigClusters=True){
   spectrHitsSorted* = new nestedList();
   sortHits(hits, spectrHitsSorted);
   // if Debug: nicePrintout(spectrHitsSorted)
   std::vector<std::vector<int>> clusters;
   for (int s = 1; s<5; ++s) {
    for ( auto view = viewsI[s].begin(); view != viewsI[s].end(); view++ )   {
     std::map<int,std::unordered_map<int,MufluxSpectrometerHit*>> allHits = std::map<int,std::unordered_map<int,MufluxSpectrometerHit*>>();
     ncl=0;
     for ( int l = 0; l<4; l++ )   {
      for (auto hit = spectrHitsSorted[*view][s][l].begin(); hit != spectrHitsSorted[view][s][l].end(); hit++ )   {
       Int_t channelID = *hit->GetDetectorID()%1000;
       allHits[l][channelID] = hit;
      }
     }
     if (removeBigClusters){
      std::map<int,std::vector<int>>  clustersPerLayer = std::map<int,std::vector<int>>();
      for ( int l = 0; l<4; l++ )   {
       clustersPerLayer[l] = GroupIntegers( getKeys(allHits[l]), 1);
       for ( auto Acl = clustersPerLayer[l].begin(); Acl!=clustersPerLayer[l].end(); Acl++ )   {
        if ( clustersPerLayer[l][*Acl].size()>cuts["maxClusterSize"]) {
                       // kill cross talk brute force
          for ( auto x = clustersPerLayer[l][*Acl].begin(); x!=clustersPerLayer[l][*Acl].end(); x++ )   {
              allHits[l].pop(*x);}
        }
       }
      }
     }
     ncl=0;
     std::unordered_map<int,std::vector<MufluxSpectrometerHit*>> tmp = std::unordered_map<int,std::vector<MufluxSpectrometerHit*>>();
     std::unordered_map<int,std::vector<int>> perLayerUsedHits = std::unordered_map<int,std::vector<int>>();
     int level = 1;
     for ( int i = 1; i<Nchannels[s]+1; i++ )   {
       std::unordered_map<int,int> perLayer = { {0,0},{1,0},{2,0},{3,0} };
       for ( int i0 =  max(1,i-1); i0<min(Nchannels[s]+1,i+2); i0++ ) {
        auto search = allHits[0].find(i0);
        if (search != example.end()) {
          tmp[ncl].push_back(allHits[0][i0]);
          perLayer[0]=1;
        }
       }
       for ( int i1 =  max(1,i-1); i1<min(Nchannels[s]+1,i+2); i1++ ) {
        auto search = allHits[1].find(i1);
        if (search != example.end()) {
          tmp[ncl].push_back(allHits[1][i1]);
          perLayer[1]=1;
        }
       }
       for ( int i2 =  max(1,i-1); i2<min(Nchannels[s]+1,i+2); i2++ ) {
        auto search = allHits[2].find(i2);
        if (search != example.end()) {
          tmp[ncl].push_back(allHits[2][i2]);
          perLayer[2]=1;
        }
       }
       for ( int i3 =  max(1,i-1); i3<min(Nchannels[s]+1,i+2); i3++ ) {
        auto search = allHits[3].find(i3);
        if (search != example.end()) {
          tmp[ncl].push_back(allHits[3][i3]);
          perLayer[3]=1;
        }
       }
       if ( (perLayer[0]+perLayer[1]+perLayer[2]+perLayer[3]) > level){
       // at least 2 hits per station
        ncl+=1;
       }
     }
// cleanup, outliers
     tmpClean = {}
     for ( int ncl = 0; ncl<tmp.size(); ncl++ ) {
       std::unordered_map<int,std::vector<int>> tmp = std::unordered_map<int,std::vector<int>>();
       mean = 0;
       for (auto hit = tmp[ncl].begin(); hit != tmp[ncl].end(); hit++ )   {
          bot,top =  strawPositionsBotTop[hit.GetDetectorID()]
          x = (bot[0]+top[0])/2.
          mean+=x
          test.append([hit,x])
       mean=mean/float(len(test))
# more cleanup, outliers
       tmpClean[ncl]=[]
       for cl in test:
          if abs(mean-cl[1])<2.5 : 
            tmpClean[ncl].append(cl[0])
# cleanup, remove lists contained in another list
     clusters[s][view]=[]
     if len(tmpClean)>0:
      ncl = 0
      marked = []
      for n1 in range(len(tmpClean)):
        if len(tmpClean[n1])==0: continue
        contained = False
        for n2 in range(len(tmpClean)):
          if n1==n2: continue
          if n2 in marked: continue
          if set(tmpClean[n1]) <= set(tmpClean[n2]):
           contained = True
           break
        if contained:  marked.append(n1)
      for n1 in range(len(tmpClean)):
         if len(tmpClean[n1])<2: continue
         if n1 in marked: continue
         test = []
         mean = 0
         for hit in tmpClean[n1]:
          bot,top =  strawPositionsBotTop[hit.GetDetectorID()]
          x = (bot[0]+top[0])/2.
          z = (bot[2]+top[2])/2.
          mean+=x
          test.append([hit,x,z,hit.GetDetectorID()%1000])
         mean=mean/float(len(test))
# more cleanup, outliers
         clusters[s][view].append([])
         for cl in test:
          if abs(mean-cl[1])<2.5: clusters[s][view][ncl].append(cl)
         if len(clusters[s][view][ncl])==0:
           clusters[s][view].pop(ncl)
         else: ncl+=1
     rc = h['clsN'].Fill(ncl)
# eventually split too big clusters for stero layers:
   for s in [1,2]:
    for view in viewsI[s]:
     if view==0:continue
     tmp = {}
     for cl in clusters[s][view]:
      if len(cl)>5:
       for hit in cl: 
         if not tmp.has_key(hit[3]):tmp[hit[3]]=[]
         tmp[hit[3]].append(hit)
     for n in tmp:
       if len(tmp[n])>1:
         clusters[s][view].append(tmp[n])
   if Debug: 
    for s in range(1,5):
     for view in viewsI[s]:
      printClustersPerStation(clusters,s,view)
   return clusters
*/
Bool_t MufluxReco::checkCharm(){
   Bool_t check = false;
   for (Int_t m=0;m<MCTrack->GetEntries();m++) {
      ShipMCTrack* mu = (ShipMCTrack*)MCTrack->At(m);
      Int_t pdg = TMath::Abs(mu->GetPdgCode());
      if(std::find(charmExtern.begin(),charmExtern.end(),pdg)!=charmExtern.end()) {check=true;}
   }
   return check;
}
Bool_t MufluxReco::checkDiMuon(){
   std::vector<ShipMCTrack*> muplus;
   std::vector<ShipMCTrack*> muminus;
   Bool_t check = false;
   for (Int_t m=0;m<MCTrack->GetEntries();m++) {
      ShipMCTrack* mu = (ShipMCTrack*)MCTrack->At(m);
      if (mu->GetPdgCode()==13){ muminus.push_back(mu);}
      if (mu->GetPdgCode()==-13){ muplus.push_back(mu);}
   }
   TLorentzVector mompl;
   TLorentzVector mommi;
   for (auto mp : muplus) {
    mp->Get4Momentum(mompl);
    for (auto mm : muminus) {
      mm->Get4Momentum(mommi);
      auto resonance = mommi+mompl;
      if (TMath::Abs( resonance.M() - 0.7755) < 0.001){check = true;}
      if (TMath::Abs( resonance.M() - 1.0195) < 0.001){check = true;}
    }
   }
   if (check && gRandom->Uniform(0.,1.)>0.99){check = false;}
   return check;
}

Bool_t MufluxReco::findSimpleEvent(Int_t nmin, Int_t nmax){
   nestedList spectrHitsSorted = nestedList();
   sortHits(cDigi_MufluxSpectrometerHits,&spectrHitsSorted);
   Bool_t passed = kTRUE;
   Int_t check=0;
   for ( int s = 1; s<5; s++ )   {
    check=0;
    for ( int l = 0; l<4; l++ )   {
     check+=spectrHitsSorted[0][s][l].size();
    }
    if (check<nmin || check>nmax) {passed = kFALSE;}
   }
   check=0;
   // very stupid, works perfectly in python
   if (spectrHitsSorted[1].size()>0){
    if (spectrHitsSorted[1][1].size()>0){
    for ( int l = 0; l<4; l++ )   {
     check+=spectrHitsSorted[1][1][l].size();
    }
   }}
   if (check<nmin || check>nmax) {passed = kFALSE;}
   check=0;
   if (spectrHitsSorted[2].size()>0){
    if (spectrHitsSorted[2][2].size()>0){
    for ( int l = 0; l<4; l++ )   {
     check+=spectrHitsSorted[2][2][l].size();
    }
   }}
   if (check<nmin || check>nmax) {passed = kFALSE;}
   return passed;
}

void MufluxReco::RPCextrap(Int_t nMax){
 Int_t N = xSHiP->GetEntries(true);
 TTree* sTree = xSHiP->GetTree();
 if (nMax<0){nMax=N;}
 xSHiP->Restart();
 gROOT->cd();
 std::cout<< "make RPC analysis: "<< N <<std::endl;
 std::map<int,TH2D*> h_RPCResX;
 std::map<int,TH2D*> h_RPCResY;
 std::map<int,TH1D*> h_RPCextTrack;
 std::map<int,TH1D*> h_RPCfired;
 std::map<int,TH1D*> h_RPCfired_or;
 std::map<int,TH1D*> h_RPC;
 TString hname;
 for ( int s = 1; s<6; s++ )   {
  for ( int v = 0; v<2; v++ )   {
   hname = "RPCResY_";
   h_RPCResY[s*10+v]=(TH2D*)(gDirectory->GetList()->FindObject(hname+=(s*10+v)));
   hname = "RPCResX_";
   h_RPCResX[s*10+v]=(TH2D*)(gDirectory->GetList()->FindObject(hname+=(s*10+v)));
   hname = "RPCextTrack_";
   h_RPCextTrack[s*10+v]=(TH1D*)(gDirectory->GetList()->FindObject(hname+=(s*10+v)));
   hname = "RPCfired_";
   h_RPCfired[s*10+v]=(TH1D*)(gDirectory->GetList()->FindObject(hname+=(s*10+v)));
  }
  hname = "RPCfired_or_";
  h_RPCfired_or[s]=(TH1D*)(gDirectory->GetList()->FindObject(hname+=(s)));
  }
 for ( int k = 2; k<20; k++ )   {
  hname = "RPC<";hname+=(k);hname+="_p";
  h_RPC[k]=(TH1D*)(gDirectory->GetList()->FindObject(hname));
 }
 TH1D* h_RPC_p =  (TH1D*)(gDirectory->GetList()->FindObject("RPC_p"));
 TH2D* h_RPCResX1_p =  (TH2D*)(gDirectory->GetList()->FindObject("RPCResX1_p"));
 TH2D* h_RPC_2XY =  (TH2D*)(gDirectory->GetList()->FindObject("RPC<2XY"));
 TH3D* h_RPCMatchedHits =  (TH3D*)(gDirectory->GetList()->FindObject("RPCMatchedHits"));

 Int_t nx = 0;
 while (nx<nMax){
   sTree->GetEvent(nx);
   nx+=1;
   Int_t Nhits = Digi_MuonTaggerHits->GetEntries();
   if (Nhits==0){ continue;}
   Int_t Ntracks = FitTracks->GetEntries();
   if (!findSimpleEvent(2,6)){continue;}
   for (Int_t tr=0;tr<Ntracks;tr++) {
     genfit::Track* aTrack = (genfit::Track*)FitTracks->At(tr);
     auto fitStatus   = aTrack->getFitStatus();
// track quality
     if (!fitStatus->isFitConverged()){continue;}
     TrackInfo* info = (TrackInfo*)TrackInfos->At(tr);
     StringVecIntMap hitsPerStation = countMeasurements(info);
     if (hitsPerStation["x1"].size()<2){ continue;}
     if (hitsPerStation["x2"].size()<2){ continue;}
     if (hitsPerStation["x3"].size()<2){ continue;}
     if (hitsPerStation["x4"].size()<2){ continue;}
     Double_t pMom0 = aTrack->getFittedState(0).getMomMag();
     if (pMom0 < 1.){continue;}

     std::map<int,std::vector<int>> matchedHits;
     TVector3 posRPC;TVector3 pos1; TVector3 momRPC;
     Double_t rc = MufluxReco::extrapolateToPlane(aTrack,cuts["zRPC1"], pos1, momRPC);
     Bool_t inAcc = kFALSE;
     if (pos1[0]>cuts["xLRPC1"] && pos1[0]<cuts["xRRPC1"] && pos1[1]>cuts["yBRPC1"] && pos1[1]<cuts["yTRPC1"]){
       inAcc=kTRUE;}
     for (Int_t nHit=0;nHit<Nhits;nHit++) {
        MuonTaggerHit* hit = (MuonTaggerHit*)Digi_MuonTaggerHits->At(nHit);
        Int_t channelID = hit->GetDetectorID();
        Int_t s  = channelID/10000;
        Int_t v  = (channelID-10000*s)/1000;
        Float_t z = RPCPositions[channelID][2];
        rc = MufluxReco::extrapolateToPlane(aTrack, z, posRPC, momRPC);
        Double_t res;
        if (v==0){
          res = posRPC[1]-RPCPositions[channelID][1];
          h_RPCResY[10*s+v]->Fill(res,RPCPositions[channelID][1]);
        } else {
          res = posRPC[0]-RPCPositions[channelID][0];
          h_RPCResX[10*s+v]->Fill(res,RPCPositions[channelID][0]);
          if(s==1){ h_RPCResX1_p->Fill(res,pMom0);}
        }
        if (TMath::Abs(res) < cuts["RPCmaxDistance"]){
           matchedHits[s*10+v].push_back(nHit);
        }
       }
       // record number of hits per station and view and track momentum
       // but only for tracks in acceptance
       if (inAcc){
        Int_t Nmatched = 0;
        Double_t p = pMom0;
        if (p>99.9){p=99.9;}
/* try the following:
  require matched hit in station k+1
  record how often hit matched in station k 
*/
        for (Int_t k=1;k<5;k++) {
         for (Int_t v=0;v<2;v++) {
           if( matchedHits[ (k+1)*10+v].size()==0){continue;}
           h_RPCextTrack[10*k+v]->Fill(p);
           if ( matchedHits[k*10+v].size()>0){h_RPCfired[10*k+v]->Fill(p);}
           if (v==0){
             if ( matchedHits[k*10+v].size()>0 || matchedHits[k*10+v+1].size()>0){ h_RPCfired_or[k]->Fill(p);}
           }
          }
        }
        for (Int_t s=1;s<6;s++) {
         for (Int_t v=0;v<2;v++) {
          h_RPCMatchedHits->Fill(2*s-1+v,matchedHits[s*10+v].size(),p);
          Nmatched+=matchedHits[s*10+v].size();
         }
        }
        if ( Nmatched <2 && p>30){ h_RPC_2XY->Fill(pos1[0],pos1[1]);}
        h_RPC_p->Fill(p);
        for (Int_t k=2;k<20;k++) {
         if (Nmatched<k) {h_RPC[k]->Fill(p);}
        }
      }
  } // end track loop
 } // end event loop
}

Double_t MufluxReco::extrapolateToPlane(genfit::Track* fT,Float_t z, TVector3& pos, TVector3& mom){
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
    genfit::StateOnPlane fstate =  fT->getFittedState(mClose);
    NewPosition->SetXYZ(0., 0., z);
    Int_t pdgcode = -int(13*fstate.getCharge());
    genfit::RKTrackRep* rep      = new genfit::RKTrackRep( pdgcode );
    genfit::StateOnPlane* state   = new genfit::StateOnPlane(rep);
    auto Pos = fstate.getPos();
    auto Mom = fstate.getMom();
    rep->setPosMom(*state,Pos,Mom);
    rc = rep->extrapolateToPlane(*state, *NewPosition, *parallelToZ );
    pos = (state->getPos());
    mom = (state->getMom());
    delete rep;
    delete state;
   }else{
    genfit::StateOnPlane fstate = fT->getFittedState(0);
    if ( z > cuts["lastDTStation_z"]){
     Int_t nmeas = fT->getNumPointsWithMeasurement();
     Int_t M = TMath::Min(nmeas-1,30);
     fstate = fT->getFittedState(M);
    }
    pos = fstate.getPos();
    mom = fstate.getMom();
// use linear extrap 
    Float_t lam = (z-pos[2])/mom[2];
    pos[2]=z;
    pos[0]=pos[0]+lam*mom[0];
    pos[1]=pos[1]+lam*mom[1];
    rc = 0;
  }
 }
  return rc;
}


StringVecIntMap MufluxReco::countMeasurements(TrackInfo* trInfo){
 StringVecIntMap mStatistics = StringVecIntMap();
 for (Int_t n=0;n<trInfo->N();n++) {
    Int_t detID = trInfo->detId(n);
    MufluxSpectrometerHit* hit = new MufluxSpectrometerHit(detID,0);
    auto info = hit->StationInfo();
    delete hit;
    Int_t s=info[0]; Int_t v=info[1]; Int_t p=info[2]; Int_t l=info[3]; Int_t channelNr=info[5]; 
    if (trInfo->wL(n) <0.1 && trInfo->wR(n) <0.1){ continue;}
    if (v != 0){ 
       mStatistics["uv"].push_back(detID);
       if (v == 1) { mStatistics["u"].push_back(detID);}
       if (v == 2) { mStatistics["v"].push_back(detID);}
    }else{
     mStatistics["xAll"].push_back(detID);
     TString x = "x";x+=s;
     mStatistics[x.Data()].push_back(detID);
    }
    if (s > 2){  
       mStatistics["xDown"].push_back(detID);
    }else{
       mStatistics["xUp"].push_back(detID);
    }
 }
 return mStatistics;
}

void MufluxReco::trackKinematics(Float_t chi2UL, Int_t nMax){
 Int_t N = xSHiP->GetEntries(true);
 TTree* sTree = xSHiP->GetTree();
 if (nMax<0){nMax=N;}
 xSHiP->Restart();
 gROOT->cd();
 std::cout<< "fill trackKinematics: "<< N <<std::endl;
/* TTreeReader framework cannot deal with unsplit TClonesArray, too bad 
 TTreeReaderValue <TClonesArray> FitTracks(*xSHiP, "FitTracks");
 TTreeReaderValue <TClonesArray> RPCTrackX(*xSHiP, "RPCTrackX");
 TTreeReaderValue <TClonesArray> RPCTrackY(*xSHiP, "RPCTrackY");
 TTreeReaderValue <TClonesArray> TrackInfos(*xSHiP, "TrackInfos");*/

 TH1D* h_chi2 =  (TH1D*)(gDirectory->GetList()->FindObject("chi2"));
 TH1D* h_Nmeasurements = (TH1D*)(gDirectory->GetList()->FindObject("Nmeasurements"));
 TH2D* h_ppt = (TH2D*)(gDirectory->GetList()->FindObject("p/pt"));
 TH2D* h_ppx = (TH2D*)(gDirectory->GetList()->FindObject("p/px"));
 TH2D* h_Absppx = (TH2D*)(gDirectory->GetList()->FindObject("p/Abspx"));
 TH2D* h_xy = (TH2D*)(gDirectory->GetList()->FindObject("xy"));
 TH2D* h_pxpy = (TH2D*)(gDirectory->GetList()->FindObject("pxpy"));
 TH1D* h_TrackMult =  (TH1D*)(gDirectory->GetList()->FindObject("TrackMult"));
 TH1D* h_TrackMultmu =  (TH1D*)(gDirectory->GetList()->FindObject("TrackMultmu"));

 TH1D* h_chi2mu =  (TH1D*)(gDirectory->GetList()->FindObject("chi2mu"));
 TH1D* h_Nmeasurementsmu = (TH1D*)(gDirectory->GetList()->FindObject("Nmeasurementsmu"));
 TH2D* h_pptmu = (TH2D*)(gDirectory->GetList()->FindObject("p/ptmu"));
 TH2D* h_ppxmu = (TH2D*)(gDirectory->GetList()->FindObject("p/pxmu"));
 TH2D* h_Absppxmu = (TH2D*)(gDirectory->GetList()->FindObject("p/Abspxmu"));
 TH2D* h_xymu = (TH2D*)(gDirectory->GetList()->FindObject("xymu"));
 TH2D* h_pxpymu = (TH2D*)(gDirectory->GetList()->FindObject("pxpymu"));

 TH2D* h_p1p2 = (TH2D*)(gDirectory->GetList()->FindObject("p1/p2"));
 TH2D* h_pt1pt2 = (TH2D*)(gDirectory->GetList()->FindObject("pt1/pt2"));

 Int_t nx = 0;
 while (nx<nMax){
   sTree->GetEvent(nx);
   nx+=1;
   Int_t Ntracks = FitTracks->GetEntries();
   Int_t Ngood = 0;
   Int_t Ngoodmu = 0;
   if (Ntracks>0 && MCdata && checkDiMuon() ){continue;} // reject randomly events with boosted dimuon channels
   for (Int_t k=0;k<Ntracks;k++) {
     genfit::Track* aTrack = (genfit::Track*)FitTracks->At(k);
     auto fitStatus   = aTrack->getFitStatus();
// track quality
     if (!fitStatus->isFitConverged()){continue;}
     TrackInfo* info = (TrackInfo*)TrackInfos->At(k);
     StringVecIntMap hitsPerStation = countMeasurements(info);
     if (hitsPerStation["x1"].size()<2){ continue;}
     if (hitsPerStation["x2"].size()<2){ continue;}
     if (hitsPerStation["x3"].size()<2){ continue;}
     if (hitsPerStation["x4"].size()<2){ continue;}
     auto chi2 = fitStatus->getChi2()/fitStatus->getNdf();
     auto fittedState = aTrack->getFittedState();
     Float_t P = fittedState.getMomMag();
     Float_t Px = fittedState.getMom().x();
     Float_t Py = fittedState.getMom().y();
     Float_t Pz = fittedState.getMom().z();
     h_chi2->Fill(chi2);
     h_Nmeasurements->Fill(fitStatus->getNdf());
     if (chi2 > chi2UL){ continue;}
     h_ppt->Fill(P,TMath::Sqrt(Px*Px+Py*Py));
     h_ppx->Fill(P,Px);
     h_Absppx->Fill(P,TMath::Abs(Px));
     auto pos = fittedState.getPos();
     h_xy->Fill(pos[0],pos[1]);
     h_pxpy->Fill(Px/Pz,Py/Pz);
     if (P>5){Ngood+=1;}
// check for muon tag
     TVector3 posRPC; TVector3 momRPC;
     Double_t rc = MufluxReco::extrapolateToPlane(aTrack,cuts["zRPC1"], posRPC, momRPC);
     
     Bool_t X = kFALSE;
     Bool_t Y = kFALSE;
     for (Int_t mu=0;mu<RPCTrackX->GetEntries();mu++) {
        RPCTrack *hit = (RPCTrack*)RPCTrackX->At(mu);
        X = hit->m()*cuts["zRPC1"]+hit->b();
        if (TMath::Abs(posRPC[0]-X)<cuts["muTrackMatchX"]){X=kTRUE;}
     }
     for (Int_t mu=0;mu<RPCTrackY->GetEntries();mu++) {
        RPCTrack *hit = (RPCTrack*)RPCTrackY->At(mu);
        Y = hit->m()*cuts["zRPC1"]+hit->b();
        if (TMath::Abs(posRPC[1]-X)<cuts["muTrackMatchY"]){Y=kTRUE;}
     }
      if (X && Y) { // within ~3sigma  X,Y from mutrack
        h_chi2mu->Fill(chi2);
        h_Nmeasurementsmu->Fill(fitStatus->getNdf());
        h_pptmu->Fill(P,TMath::Sqrt(Px*Px+Py*Py));
        h_ppxmu->Fill(P,Px);
        h_Absppxmu->Fill(P,TMath::Abs(Px));
        h_xymu->Fill(pos[0],pos[1]);
        h_pxpymu->Fill(Px/Pz,Py/Pz);
        if (P>5){Ngoodmu+=1;}
      }
//
     if (Ntracks==2 && k==0){
      genfit::Track* bTrack = (genfit::Track*)FitTracks->At(1);
      auto fitStatusb   = bTrack->getFitStatus();
      if (!fitStatusb->isFitConverged()){ continue;}
      Float_t chi2b = fitStatusb->getChi2()/float(fitStatusb->getNdf());
      if (chi2b > chi2UL){ continue;}
      auto fittedStateb = bTrack->getFittedState();
      Float_t Pb = fittedStateb.getMomMag();
      Float_t Pbx = fittedStateb.getMom().x();
      Float_t Pby = fittedStateb.getMom().y();
      Float_t Pbz = fittedStateb.getMom().z();
      h_p1p2->Fill(P,Pb);
      h_pt1pt2->Fill(TMath::Sqrt(Px*Px+Py*Py),TMath::Sqrt(Pbx*Pbx+Pby*Pby));
     }
    h_TrackMult->Fill(Ngood);
    h_TrackMultmu->Fill(Ngoodmu);
   }
 }
}


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
   // statnb,   vnb,    pnb,    lnb,    view,         channelID,tdcId,nRT
   if (info[2] > 1 || info[3] >1){
    std::cout<< "sortHits: unphysical detector ID "<<hit->GetDetectorID()<<std::endl;
    hit->Dump();
   }else{
    spectrHitsSorted[info[4]][info[0]][info[2]*2+info[3]].push_back(hit);
  }
 }
 *l = spectrHitsSorted;
}

void MufluxReco::fillHitMaps(Int_t nMax)
{
 Float_t deadThreshold = 1.E-4; // ~1% typical occupancy
 Int_t N = xSHiP->GetEntries(true);
 if (nMax<0){nMax=N;}
 xSHiP->Restart();
 gROOT->cd();
 std::cout<< "fillHitMaps: "<< N  <<std::endl;
 TTreeReaderArray <MufluxSpectrometerHit> Digi_MufluxSpectrometerHits(*xSHiP, "Digi_MufluxSpectrometerHits");
 TTreeReaderValue<FairEventHeader>* rvShipEventHeader= NULL;
 if (MCdata){ rvShipEventHeader = new TTreeReaderValue<FairEventHeader>(*xSHiP, "ShipEventHeader");}
 Int_t nx = 0;
 while (xSHiP->Next()){
  nx+=1;
  if (nx>nMax){break;}
  // std::cout<< "next event. #hits "<< Digi_MufluxSpectrometerHits.GetSize()  <<std::endl;
  for (Int_t k=0;k<Digi_MufluxSpectrometerHits.GetSize();k++) {
     MufluxSpectrometerHit* hit = &(Digi_MufluxSpectrometerHits[k]);
     auto info = hit->StationInfo();
     Int_t s=info[0]; Int_t v=info[1]; Int_t p=info[2]; Int_t l=info[3]; Int_t channelNr=info[5]; 
     Int_t tdcId=info[6]; Int_t nRT=info[7]/cuts["RTsegmentation"];
     TString view = "_x"; 
     if (info[4]==1){view="_u";}
     if (info[4]==2){view="_v";}
     TString tot = "";
     if (!hit->hasTimeOverThreshold()){ tot = "_noToT";}
     TString histo; histo.Form("%d",1000*s+100*p+10*l);histo+=view;
     TH1D* h = (TH1D*)(gDirectory->GetList()->FindObject(histo));
     if (!h){
       std::cout<< "fillHitMaps: ERROR histo not known "<< histo <<" event "<< nx <<std::endl;
       continue;
     }
     h->Fill(channelNr);
     auto check = std::find( noisyChannels.begin(), noisyChannels.end(), hit->GetDetectorID() );
     if (check!=noisyChannels.end()){ continue;}
     Float_t t0 = 0;
     if (MCdata){ rvShipEventHeader->Get()->GetEventTime(); }
     TString TDChisto = "TDC"; TDChisto+=nRT; TDChisto+=tot;
     h = (TH1D*)(gDirectory->GetList()->FindObject(TDChisto));
     if (!h){
       std::cout<< "fillHitMaps: ERROR histo not known "<< TDChisto  <<" event "<< nx <<std::endl; 
       continue;
     }
     h->Fill( hit->GetDigi()-t0);
     TString channel = "TDC";channel+=hit->GetDetectorID();
     h = (TH1D*)(gDirectory->GetList()->FindObject(channel));
     h->Fill( hit->GetDigi()-t0);
   }
  }
}
// -----   Destructor   ----------------------------------------------------
MufluxReco::~MufluxReco() { }
// -------------------------------------------------------------------------

 
ClassImp(MufluxReco) 
