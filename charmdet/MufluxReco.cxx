

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
std::vector<int> beautyExtern = {5332,5232,5132,5232,5122,531,511,521};
std::vector<int> muSources   = {221,223,333,113,331};
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
  MufluxSpectrometerPoints = 0;
  TTree* fChain = xSHiP->GetTree();
  if (MCdata){
    fChain->SetBranchAddress("MCTrack", &MCTrack, &b_MCTrack);
    fChain->SetBranchAddress("MufluxSpectrometerPoint", &MufluxSpectrometerPoints, &b_MufluxSpectrometerPoints);
  }
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
Int_t MufluxReco::checkDiMuon(){
   Int_t mode = -1;
   Int_t channel = -1;
   std::vector<int> processed;
   Double_t weight;
   TH2D* h_weightVsSource=(TH2D*)(gDirectory->GetList()->FindObject("weightVsSource"));
   for (Int_t n=0;n<MufluxSpectrometerPoints->GetEntries();n++) {
      MufluxSpectrometerPoint* hit = (MufluxSpectrometerPoint*)MufluxSpectrometerPoints->At(n);
      Int_t i = hit->GetTrackID();
      if (i<0){ continue;}
      if(std::find(processed.begin(),processed.end(),i)!=processed.end()) { continue;}
      processed.push_back(i);
      ShipMCTrack* t = (ShipMCTrack*)MCTrack->At(i);
      if (TMath::Abs(t->GetPdgCode() )!=13) {continue;}
      ShipMCTrack* mo = (ShipMCTrack*)MCTrack->At(t->GetMotherId());
      Int_t moID      = TMath::Abs( mo->GetPdgCode());
      TString pName   = t->GetProcName();
      if ( strcmp("Decay",pName) == 0){ channel = 1;}
      if ( strcmp("Primary particle emission",pName) == 0){ channel = 1;}
      if(std::find(   muSources.begin(),muSources.end(),   moID)!=muSources.end())    {channel = 7;} // count dimuon channels separately
      if(std::find( charmExtern.begin(),charmExtern.end(), moID)!=charmExtern.end())  {channel = 5;} // this will go wrong for charm from beauty
      if(std::find(beautyExtern.begin(),beautyExtern.end(),moID)!=beautyExtern.end()) {channel = 6;}  
      if ( strcmp("Hadronic inelastic",pName) == 0){ channel = 2;}
      if ( strcmp("Lepton pair production",pName) == 0){ channel = 3;}
      if ( strcmp("Positron annihilation",pName) == 0){ channel = 4;}
      if (channel != mode and mode>1) {return -2;} // for the moment, discard events with two processes, and one boosted
      mode = channel;
      weight = t->GetWeight();
   }
   h_weightVsSource->Fill(mode,weight);
   return mode;
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
    Int_t s=info[0]; Int_t v=info[4]; Int_t p=info[2]; Int_t l=info[3]; Int_t channelNr=info[5]; 
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
Double_t MufluxReco::findTrueMomentum(TTree* sTree){
   Double_t trueP = -1.;
   if (findSimpleEvent(2,6)){
     if (FitTracks->GetEntries()==1){
      Double_t zmin = 1000.;
      Int_t kMin = -1;
      TrackInfo* ti = (TrackInfo*)TrackInfos->At(0);
      for (Int_t k=0;k<ti->N();k++) {
       if (ti->wL(k)<0.2 && ti->wR(k)<0.2){ continue;}
       if (ti->detId(k) > 20000000){ continue;}
       Double_t z = DTPositionsBot[ti->detId(k)][2];
       if (z<zmin){
         zmin = z;
         kMin = ti->detId(k);
       }
      }
      if (!(kMin<0)){ 
       for (Int_t n=0;n<MufluxSpectrometerPoints->GetEntries();n++) {
        MufluxSpectrometerPoint* hit = (MufluxSpectrometerPoint*)MufluxSpectrometerPoints->At(n);
        if (hit->GetDetectorID() == kMin) {
         trueP = TMath::Sqrt(hit->GetPx()*hit->GetPx()+hit->GetPy()*hit->GetPy()+hit->GetPz()*hit->GetPz());
         break;}
      }
     }
    }
   }
   return trueP;
}

void MufluxReco::trackKinematics(Float_t chi2UL, Int_t nMax){
 Int_t N = xSHiP->GetEntries(true);
 TTree* sTree = xSHiP->GetTree();
 if (nMax<0){nMax=N;}
 xSHiP->Restart();
 gROOT->cd();
 std::cout<< "fill trackKinematics: "<< N <<std::endl;

 TH1D* h_Trscalers =  (TH1D*)(gDirectory->GetList()->FindObject("Trscalers"));

 std::map<TString,TH1D*> h1D;
 std::map<TString,TH2D*> h2D;
 std::vector<TString> h1names = {"chi2","Nmeasurements","TrackMult","trueMom","recoMom"};
 std::vector<TString> h2names = {"p/pt","p/px","p/Abspx","xy","pxpy","p1/p2","pt1/pt2","p1/p2s","pt1/pt2s","momResol",
                                 "Fitpoints_u1","Fitpoints_v2","Fitpoints_x1","Fitpoints_x2","Fitpoints_x3","Fitpoints_x4"};
 std::vector<TString> tagged  = {"","mu"};
 std::vector<TString> Tsource  = {"","Decay","Hadronic inelastic","Lepton pair","Positron annihilation","charm","beauty","Di-muon P8"};

 std::vector<TString>::iterator its = Tsource.begin();
 while( its!=Tsource.end()){
  std::vector<TString>::iterator itt = tagged.begin();
  while( itt!=tagged.end()){
   std::vector<TString>::iterator it1 = h1names.begin();
   while( it1!=h1names.end()){
    TString hname = *it1+*itt+*its; 
    h1D[hname] = (TH1D*)(gDirectory->GetList()->FindObject(hname));
    it1++;}
   std::vector<TString>::iterator it2 = h2names.begin();
   while( it2!=h2names.end()){
    TString hname = *it2+*itt+*its;
    h2D[hname] = (TH2D*)(gDirectory->GetList()->FindObject(hname));
    it2++;}
   itt++;}
  its++;}

 Int_t nx = 0;
 while (nx<nMax){
   sTree->GetEvent(nx);
   h_Trscalers->Fill(1);
   nx+=1;
   Int_t Ntracks = FitTracks->GetEntries();
   Int_t Ngood = 0;
   Int_t Ngoodmu = 0;
   if(Ntracks>0){ h_Trscalers->Fill(2);}
   std::vector<int> muonTaggedTracks;
   TString source = "";
   if (MCdata){ Int_t channel = checkDiMuon();
         if (channel == 1){ source = "Decay";}
         if (channel == 7){ source = "Di-muon P8";}
         if (channel == 2){ source = "Hadronic inelastic";}
         if (channel == 3){ source = "Lepton pair";}
         if (channel == 4){ source = "Positron annihilation";}
         if (channel == 5){ source = "charm";}
         if (channel == 6){ source = "beauty";}
   }
   Bool_t fSource= kFALSE;
   if ( strcmp("", source.Data())!=0 ){fSource=kTRUE;}
   for (Int_t k=0;k<Ntracks;k++) {
     genfit::Track* aTrack = (genfit::Track*)FitTracks->At(k);
     auto fitStatus   = aTrack->getFitStatus();
// track quality
     h_Trscalers->Fill(3);
     if (!fitStatus->isFitConverged()){continue;}
     TrackInfo* info = (TrackInfo*)TrackInfos->At(k);
     StringVecIntMap hitsPerStation = countMeasurements(info);
// for MC
     if (MCdata){
       std::map<TString,int> detectors = { {"u",0}, {"v",0}, {"x2",0}, {"x3",0}, {"x1",0},{"x4",0}};
       std::map<TString, int>::iterator it;
       bool failed = false;
       for ( it = detectors.begin(); it != detectors.end(); it++ ){
        for ( int m=0; m<hitsPerStation[it->first.Data()].size();m+=1){
         float rnr = gRandom->Uniform();
         float eff = effFudgeFac[it->first.Data()];
         if (rnr < eff){detectors[it->first.Data()]+=1;}
        }
        if (detectors[it->first.Data()]<2){
           failed = true;
           break;}
       }
       if (failed){continue;}
     }
     if (hitsPerStation["x1"].size()<2){ continue;}
     if (hitsPerStation["x2"].size()<2){ continue;}
     if (hitsPerStation["x3"].size()<2){ continue;}
     if (hitsPerStation["x4"].size()<2){ continue;}
     h_Trscalers->Fill(4);
     auto chi2 = fitStatus->getChi2()/fitStatus->getNdf();
     auto fittedState = aTrack->getFittedState();
     Float_t P = fittedState.getMomMag();
     Float_t Px = fittedState.getMom().x();
     Float_t Py = fittedState.getMom().y();
     Float_t Pz = fittedState.getMom().z();
     h1D["chi2"]->Fill(chi2);
     h1D["Nmeasurements"]->Fill(fitStatus->getNdf());
     if (fSource){
        h1D["chi2"+source]->Fill(chi2);
        h1D["Nmeasurements"+source]->Fill(fitStatus->getNdf());}
     if (chi2 > chi2UL){ continue;}
     h_Trscalers->Fill(5);
     auto pos = fittedState.getPos();
     h2D["p/pt"]->Fill(P,TMath::Sqrt(Px*Px+Py*Py));
     h2D["p/px"]->Fill(P,Px);
     h2D["p/Abspx"]->Fill(P,TMath::Abs(Px));
     h2D["xy"]->Fill(pos[0],pos[1]);
     h2D["pxpy"]->Fill(Px/Pz,Py/Pz);
     if (fSource){
      h2D["p/pt"+source]->Fill(P,TMath::Sqrt(Px*Px+Py*Py));
      h2D["p/px"+source]->Fill(P,Px);
      h2D["p/Abspx"+source]->Fill(P,TMath::Abs(Px));
      h2D["xy"+source]->Fill(pos[0],pos[1]);
      h2D["pxpy"+source]->Fill(Px/Pz,Py/Pz);
     }
// record fitted points / station
    h2D["Fitpoints_u1"]->Fill(P,hitsPerStation["u"].size());
    h2D["Fitpoints_v2"]->Fill(P,hitsPerStation["v"].size());
    h2D["Fitpoints_x1"]->Fill(P,hitsPerStation["x1"].size());
    h2D["Fitpoints_x2"]->Fill(P,hitsPerStation["x2"].size());
    h2D["Fitpoints_x3"]->Fill(P,hitsPerStation["x3"].size());
    h2D["Fitpoints_x4"]->Fill(P,hitsPerStation["x4"].size());
// mom resolution, only simple events, one track
    if (MCdata){
     Double_t trueMom = findTrueMomentum(sTree);
     if (trueMom >0){
      h1D["trueMom"]->Fill(trueMom);
      h1D["recoMom"]->Fill(P);
      h2D["momResol"]->Fill((P-trueMom)/trueMom,trueMom);
      if (fSource){
       h1D["trueMom"+source]->Fill(trueMom);
       h1D["recoMom"+source]->Fill(P);
       h2D["momResol"+source]->Fill((P-trueMom)/trueMom,trueMom);
      }
     }
    }
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
        h1D["chi2mu"]->Fill(chi2);
        h1D["Nmeasurementsmu"]->Fill(fitStatus->getNdf());
        h2D["p/ptmu"]->Fill(P,TMath::Sqrt(Px*Px+Py*Py));
        h2D["p/pxmu"]->Fill(P,Px);
        h2D["p/Abspxmu"]->Fill(P,TMath::Abs(Px));
        h2D["xymu"]->Fill(pos[0],pos[1]);
        h2D["pxpymu"]->Fill(Px/Pz,Py/Pz);
        if (fSource){
         h2D["p/ptmu"+source]->Fill(P,TMath::Sqrt(Px*Px+Py*Py));
         h2D["p/pxmu"+source]->Fill(P,Px);
         h2D["p/Abspxmu"+source]->Fill(P,TMath::Abs(Px));
         h2D["xymu"+source]->Fill(pos[0],pos[1]);
         h2D["pxpymu"+source]->Fill(Px/Pz,Py/Pz);
        }
        if (P>5){
         Ngoodmu+=1;
         muonTaggedTracks.push_back(k);
        }
      }
     }
     h1D["TrackMult"]->Fill(Ngood);
     h1D["TrackMultmu"]->Fill(Ngoodmu);
     if (fSource){
      h1D["TrackMult"+source]->Fill(Ngood);
      h1D["TrackMultmu"+source]->Fill(Ngoodmu);
     }
     if (muonTaggedTracks.size()==2){
      genfit::Track* aTrack = (genfit::Track*)FitTracks->At(muonTaggedTracks[0]);
      genfit::Track* bTrack = (genfit::Track*)FitTracks->At(muonTaggedTracks[1]);
      auto fittedState = aTrack->getFittedState();
      auto fittedStateb = bTrack->getFittedState();
      Float_t Pb = fittedStateb.getMomMag();
      Float_t Pbx = fittedStateb.getMom().x();
      Float_t Pby = fittedStateb.getMom().y();
      Float_t Pbz = fittedStateb.getMom().z();
      Float_t P = fittedState.getMomMag();
      Float_t Px = fittedState.getMom().x();
      Float_t Py = fittedState.getMom().y();
      Float_t Pz = fittedState.getMom().z();
      if (fittedStateb.getCharge()*fittedState.getCharge()<0){
       h2D["p1/p2"]->Fill(P,Pb);
       h2D["pt1/pt2"]->Fill(TMath::Sqrt(Px*Px+Py*Py),TMath::Sqrt(Pbx*Pbx+Pby*Pby));
       if (fSource){
         h2D["p1/p2"+source]->Fill(P,Pb);
         h2D["pt1/pt2"+source]->Fill(TMath::Sqrt(Px*Px+Py*Py),TMath::Sqrt(Pbx*Pbx+Pby*Pby));
       }
      }else{
       h2D["p1/p2s"]->Fill(P,Pb);
       h2D["pt1/pt2s"]->Fill(TMath::Sqrt(Px*Px+Py*Py),TMath::Sqrt(Pbx*Pbx+Pby*Pby));
       if (fSource){
         h2D["p1/p2s"+source]->Fill(P,Pb);
         h2D["pt1/pt2s"+source]->Fill(TMath::Sqrt(Px*Px+Py*Py),TMath::Sqrt(Pbx*Pbx+Pby*Pby));
       }
     }
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
     if (MCdata){
      float rnr = gRandom->Uniform();
      TString station;
      if (info[4]==0){station = 'x';station += info[0];}
      if (info[4]==1){station = 'u';}
      if (info[4]==2){station = 'v';}
      float eff = effFudgeFac[station.Data()];
      if (rnr > eff){continue;}
     }
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
