#pragma once

#include "TObject.h"
#include "TVector3.h"

class sndRecoTrack : public TObject {
 public :
  sndRecoTrack(TVector3 track_start, TVector3 track_stop, std::vector<int> hits, std::vector<int> hitsLoose);
  ~sndRecoTrack(){;}

  TVector3 getStart() {return start;}
  TVector3 getStop() {return stop;}
  std::vector<int> getHits() {return hits_detectorID;}
  std::vector<int> getHitsLoose() {return hitsLoose_detectorID;}
  
 private :
  TVector3 start, stop;
  std::vector<int> hits_detectorID, hitsLoose_detectorID;

  ClassDef(sndRecoTrack, 1);
};
