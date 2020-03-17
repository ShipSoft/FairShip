#ifndef MUFLUXRECO_H
#define MUFLUXRECO_H 1
#include "TChain.h" 
#include "MufluxSpectrometerHit.h"
#include "ScintillatorHit.h"
#include "FairEventHeader.h"
#include "TClonesArray.h"
#include "TTreeReader.h"
#include "TTreeReaderArray.h"
#include "Track.h"
#include "TVector3.h"
#include "TrackInfo.h"
#include "TH2D.h"

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

   void fillHitMaps(Int_t nMax=-1);
   void RPCextrap(Int_t nMax=-1);
   void trackKinematics(Float_t chi2UL,Int_t nMax=-1);

   Int_t checkDiMuon(TH2D* h);
   void fillHitMaps(Int_t nMax=-1);
   void RPCextrap(Int_t nMax=-1);
   void trackKinematics(Float_t chi2UL,Int_t nMax=-1);
   TVector3 findTrueMomentum(TTree* sTree);

   Bool_t findSimpleEvent(Int_t nmin, Int_t nmax);
   void setNoisyChannels(std::vector<int> x){noisyChannels = x;}
   void setDeadChannels(std::vector<int> x){deadChannels = x;}
   void setCuts(std::string s,float f){cuts[s]=f;}
   void setRPCPositions(Int_t c,float x,float y,float z){RPCPositions[c]=TVector3(x,y,z);}
   void sortHits(TClonesArray *t, nestedList *l, Bool_t flag=kTRUE);
   Double_t extrapolateToPlane(genfit::Track* fT,Float_t z, TVector3& pos, TVector3& mom);
   StringVecIntMap countMeasurements(TrackInfo* trInfo);
   std::vector<std::vector<int>> GroupIntegers(std::vector<int>& input_array, size_t span);


   void setEffFudgeFactor(std::string s,float f){effFudgeFac[s]=f;}
   void DTreconstructible(std::vector<int> *i,std::vector<float> *x,std::vector<float> *y,std::vector<float> *z,TH2D* h);
   void RPCreconstructible(std::vector<int> *i,std::vector<float> *x,std::vector<float> *y,std::vector<float> *z);
   TVector3 findMCMomentum(int mctr);


private:
   //two vectors often needed, only helpers so that they don't need to be recreated everytime they are needed
   TVector3 m_new_position;
   const TVector3 m_parallelToZ;

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
    FairEventHeader *EventHeader;
    TClonesArray    *RPCTrackY;
    TClonesArray    *RPCTrackX;
    TClonesArray    *Digi_MuonTaggerHits;
    TClonesArray    *muonTaggerPoint;
    TClonesArray    *cDigi_MufluxSpectrometerHits;
    TBranch        *b_MCTrack;   //!
    TBranch        *b_FitTracks;   //!
    TBranch        *b_TrackInfos;   //!
    TBranch        *b_RPCTrackY;   //!
    TBranch        *b_RPCTrackX;   //!
    TBranch        *b_EventHeader;   //!
    TBranch        *b_Digi_MuonTaggerHits;   //!
    TBranch        *b_MuonTaggerPoint; //!
    TBranch        *b_Digi_MufluxSpectrometerHits;   //!

   ClassDef(MufluxReco,3);

    TBranch        *b_MufluxSpectrometerPoints;   //!
   ClassDef(MufluxReco,8);

};

#endif
