#ifndef MUFLUXRECO_H
#define MUFLUXRECO_H 1
#include "TChain.h" 
#include "MufluxSpectrometerHit.h"
#include "MufluxSpectrometerPoint.h"
#include "ScintillatorHit.h"
#include "FairEventHeader.h"
#include "TClonesArray.h"
#include "TTreeReader.h"
#include "TTreeReaderArray.h"
#include "Track.h"
#include "TVector3.h"
#include "TrackInfo.h"

#include <iostream>
#include <map>
#include <string>

enum class view {x, u, v, y}; // to avoid using std::string to index
typedef std::map<std::string,float> StringFloatMap;
typedef std::map<std::string,std::vector<int>> StringVecIntMap;
typedef std::unordered_map<int, std::unordered_map<int, std::unordered_map<int, std::vector<MufluxSpectrometerHit*>>>> nestedList;

class MufluxReco {
public:
   /** Default constructor **/
   MufluxReco();
   /**  Standard constructor  **/
   MufluxReco(TTreeReader* t);

   /** Destructor **/
   virtual ~MufluxReco();

   /** methods **/
   Bool_t checkCharm();
   Int_t checkDiMuon();
   void fillHitMaps(Int_t nMax=-1);
   void RPCextrap(Int_t nMax=-1);
   void trackKinematics(Float_t chi2UL,Int_t nMax=-1);
   Bool_t findSimpleEvent(Int_t nmin, Int_t nmax);
   void setNoisyChannels(std::vector<int> x){noisyChannels = x;}
   void setDeadChannels(std::vector<int> x){deadChannels = x;}
   void setCuts(std::string s,float f){cuts[s]=f;}
   void setRPCPositions(Int_t c,float x,float y,float z){RPCPositions[c]=TVector3(x,y,z);}
   void sortHits(TClonesArray *t, nestedList *l, Bool_t flag=kTRUE);
   Double_t extrapolateToPlane(genfit::Track* fT,Float_t z, TVector3& pos, TVector3& mom);
   StringVecIntMap countMeasurements(TrackInfo* trInfo);
   std::vector<std::vector<int>> GroupIntegers(std::vector<int>& input_array, size_t span);

private:
  protected:
    Bool_t MCdata;
    TTreeReader* xSHiP;
    std::vector<int> noisyChannels;
    std::vector<int> deadChannels;
    StringFloatMap cuts;
    std::map<int,TVector3> RPCPositions;
    TClonesArray    *MCTrack;
    TClonesArray    *FitTracks;
    TClonesArray    *TrackInfos;
    TClonesArray    *RPCTrackY;
    TClonesArray    *RPCTrackX;
    TClonesArray    *Digi_MuonTaggerHits;
    TClonesArray    *cDigi_MufluxSpectrometerHits;
    TClonesArray    *MufluxSpectrometerPoints;
    TBranch        *b_MCTrack;   //!
    TBranch        *b_FitTracks;   //!
    TBranch        *b_TrackInfos;   //!
    TBranch        *b_RPCTrackY;   //!
    TBranch        *b_RPCTrackX;   //!
    TBranch        *b_Digi_MuonTaggerHits;   //!
    TBranch        *b_Digi_MufluxSpectrometerHits;   //!
    TBranch        *b_MufluxSpectrometerPoints;   //!
   ClassDef(MufluxReco,4);
};

#endif
