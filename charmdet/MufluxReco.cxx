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
/* unfinished, C++ is not a language for serious physicists.
void MufluxReco::findDTClusters(TClonesArray* hits, Bool_t removeBigClusters=True,Bool_t Debug){
   spectrHitsSorted  = nestedList();
   sortHits(hits,spectrHitsSorted);
   clusters =  std::unordered_map<int, std::unordered_map<int, 
   for (Int_t s=0;s<5;s++) {
    for (Int_t v=0;v<3;v++) {
     if (s>2 && v!=0){continue;}
     if (s==2 && v==1){continue;}
     if (s==1 && v==2){continue;}
     allHits = std::unordered_map<int,std::unordered_map<int,MufluxSpectrometerHit*>>;
     for (Int_t l=0;l<4;l++) {
      std::vector<(MufluxSpectrometerHit*> list = spectrHitsSorted[v][s][l];
      for(list::iterator hit = list.begin(); hit != list.end(); +hit) {
       Int_t channelID = hit->GetDetectorID()%1000;
       allHits[l][channelID]=hit;
       }
     }
     if (removeBigClusters){
      clustersPerLayer = std::unordered_map<int,std::unordered_map<int,MufluxSpectrometerHit*>>;
      for (Int_t l=0;l<4;l++) {

        clustersPerLayer[l] = dict(enumerate(grouper(allHits[l].keys(),1), 1))
        for (Int_t Acl=0;Acl<clustersPerLayer[l].size();Acl++) {
         if ( clustersPerLayer[l][Acl].size()>cuts["maxClusterSize"]){ // kill cross talk brute force
           for x in clustersPerLayer[l][Acl]:
            allHits[l].pop(x);
            if (Debug){ std::cout << "pop "<<s<<" "<<v<<" "<<l<<" "<<x<<std::endl;}
         }
        }
      }
     }

     ncl=0
     tmp={}
     tmp[ncl]=[]
     perLayerUsedHits = {0:[],1:[],2:[],3:[]}
     for level in [1]:
      for i in range(1,Nchannels[s]+1):
       perLayer = {0:0,1:0,2:0,3:0}
       for i0 in range( max(1,i-1),min(Nchannels[s]+1,i+2)):
        if allHits[0].has_key(i0):
          tmp[ncl].append(allHits[0][i0])
          perLayer[0]=i0
       for i1 in range( max(1,i-1), min(Nchannels[s]+1,i+2)):
        if allHits[1].has_key(i1):
          tmp[ncl].append(allHits[1][i1])
          perLayer[1]=i1
       for i2 in range( max(1,i-1), min(Nchannels[s]+1,i+2)):
        if allHits[2].has_key(i2):  
          tmp[ncl].append(allHits[2][i2])
          perLayer[2]=i2
       for i3 in range( max(1,i-1), min(Nchannels[s]+1,i+2)):
        if allHits[3].has_key(i3): 
          tmp[ncl].append(allHits[3][i3])
          perLayer[3]=i3
       if ( (perLayer[0]>0) + (perLayer[1]>0) + (perLayer[2]>0) + (perLayer[3]>0) ) > level:
         # at least 2 hits per station
         ncl+=1
       tmp[ncl]=[]
     if len(tmp[ncl])==0: tmp.pop(ncl)
# cleanup, outliers
     tmpClean = {}
     for ncl in tmp:
       test = []
       mean = 0
       for hit in tmp[ncl]:
          bot,top = correctAlignment(hit)
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
          bot,top = correctAlignment(hit)
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
    for view in views[s]:
     if view=='_x':continue
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
     for view in views[s]:
      printClustersPerStation(clusters,s,view)
   return clusters
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
