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

#include <iostream>
#include <map>
#include <string>

enum class view {x, u, v, y}; // to avoid using std::string to index
typedef std::map<std::string,float> StringFloatMap;
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
   void fillHitMaps();
   void trackKinematics(Float_t chi2UL);
   void setNoisyChannels(std::vector<int> x){noisyChannels = x;}
   void setDeadChannels(std::vector<int> x){deadChannels = x;}
   void setCuts(std::string s,float f){cuts[s]=f;}
   void sortHits(TClonesArray *t, nestedList *l, Bool_t flag=kTRUE);
   Double_t extrapolateToPlane(genfit::Track* fT,Float_t z, TVector3* pos, TVector3* mom);
private:
  protected:
    Bool_t MCdata;
    TTreeReader* xSHiP;
    std::vector<int> noisyChannels;
    std::vector<int> deadChannels;
    StringFloatMap cuts;

   ClassDef(MufluxReco, 1);
};

#endif
