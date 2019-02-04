#include "MufluxReco.h"
#include <TROOT.h>
#include <TChain.h>
#include <TH1D.h>
#include "TObject.h"
 
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

MufluxReco::trackKinematics(chi2UL){
 Int_t N = xSHiP->GetEntries(true);
 xSHiP->Restart();
 std::cout<< "fill trackKinematics: "<< N << " "<<xSHiP->GetCurrentEntry() <<std::endl;
 TTreeReaderArray <genfit::Track> FitTracks(*xSHiP, "FitTracks");
 TTreeReaderArray <RPCTrack> RPCTrackX(*xSHiP, "RPCTrackX");
 TTreeReaderArray <RPCTrack> RPCTrackY(*xSHiP, "RPCTrackY");
 while (xSHiP->Next()){
   for (Int_t k=0;k<FitTracks.GetSize();k++) {
     genfit::Track* aTrack = (genfit::Track*)FitTracks->At(k);
   //if MCdata and PR<10 and sTree.ShipEventHeader.GetUniqueID()==1: continue # non reconstructed events 
     auto fitStatus   = aTrack->getFitStatus();
// track quality
     if (!fitStatus->isFitConverged()){continue;}
missing     /*if PR<10: hitsPerStation = countMeasurements(N,PR)
     if len(hitsPerStation['x1'])<2: continue
     if len(hitsPerStation['x2'])<2: continue
     if len(hitsPerStation['x3'])<2: continue
     if len(hitsPerStation['x4'])<2: continue 
     auto chi2 = fitStatus->getChi2()/fitStatus->getNdf();
     auto fittedState = aTrack->getFittedState();
     Float_t P = fittedState->getMomMag();
     Float_t Px = fittedState->getMom().x();
     Float_t Py = fittedState->getMom().y();
     Float_t Pz = fittedState->getMom().z();
     gROOT->FindObject("chi2")->Fill(chi2);
     gROOT->FindObject("Nmeasurements"))->Fill(fitStatus.getNdf());
     if (chi2 > chi2UL){ continue;}
     gROOT->FindObject("p/pt")->Fill(P,TMath::Sqrt(Px*Px+Py*Py));
     auto pos = fittedState->getPos();
     gROOT->FindObject("xy")->Fill(pos[0],pos[1]);
     gROOT->FindObject("pxpy")->Fill(Px/Pz,Py/Pz);
// check for muon tag
missing     rc,posRPC,momRPC = extrapolateToPlane(aTrack,zRPC1)
      Float_t X =-1000;
      Float_t Y =-1000;
      if (RPCTrackX.GetSize()>0){X = RPCtracks['X'][0][0]*zRPC1+RPCtracks['X'][0][1];}
      if (RPCTrackY.GetSize()>0){Y = RPCtracks['Y'][0][0]*zRPC1+RPCtracks['Y'][0][1];}
      if (rc){
       if (TMath::Abs(posRPC[0]-X)<5. && TMath::Abs(posRPC[1]-Y)<10.) { // within ~3sigma  X,Y from mutrack
        gROOT->FindObject("chi2mu")->Fill(chi2);
        gROOT->FindObject("Nmeasurementsmu")->Fill(fitStatus.getNdf());
        gROOT->FindObject("p/ptmu")->Fill(P,ROOT.TMath.Sqrt(Px*Px+Py*Py));
        gROOT->FindObject("xymu")->Fill(pos[0],pos[1]);
        gROOT->FindObject("pxpymu")->Fill(Px/Pz,Py/Pz);
      }
     }
//
     if (FitTracks.GetSize()==2 && k==0){
      bTrack = theTracks[1]
      fitStatus   = bTrack.getFitStatus()
      if not fitStatus.isFitConverged(): continue
      chi2 = fitStatus.getChi2()/fitStatus.getNdf()
      fittedState = bTrack.getFittedState()
      Pb = fittedState.getMomMag()
      Pbx,Pby,Pbz = fittedState.getMom().x(),fittedState.getMom().y(),fittedState.getMom().z()
      if chi2 > chi2UL: continue
      rc = h['p1/p2'].Fill(P,Pb)
      rc = h['pt1/pt2'].Fill(ROOT.TMath.Sqrt(Px*Px+Py*Py),ROOT.TMath.Sqrt(Pbx*Pbx+Pby*Pby))
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
 std::cout<< "fillHitMaps: "<< N << " "<<xSHiP->GetCurrentEntry() <<std::endl;
 TTreeReaderArray <MufluxSpectrometerHit> Digi_MufluxSpectrometerHits(*xSHiP, "Digi_MufluxSpectrometerHits");
 //if (MCdata){TTreeReaderValue <FairEventHeader> rvShipEventHeader(*xSHiP, "ShipEventHeader");
 //} else {TTreeReaderValue <FairEventHeader> rvShipEventHeader(*xSHiP, "EventHeader.");}
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
     h->Fill(channelNr);
     auto check = std::find( noisyChannels.begin(), noisyChannels.end(), hit->GetDetectorID() );
     if (check!=noisyChannels.end()){ continue;}
     Float_t t0 = 0;
     /*if (MCdata){
       auto header = rvShipEventHeader.Get(); 
       t0 = header->GetEventTime();
        //rvShipEventHeader.Get()->GetEventTime(); doesn't work 
     }*/
     TString TDChisto = "TDC"; TDChisto+=histo;TDChisto+=moduleId+tot;
     h = (TH1D*)(gROOT->FindObject(TDChisto));
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
