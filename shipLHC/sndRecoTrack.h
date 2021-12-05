#pragma once

#include "TObject.h"
#include "TVector3.h"

class sndRecoTrack : public TObject {
 public :
  sndRecoTrack(){;}
  sndRecoTrack(TVector3 track_start, TVector3 track_stop, std::vector<int> hits, std::vector<int> hitsLoose);
  ~sndRecoTrack(){;}

  TVector3 getStart() {return start;}
  TVector3 getStop() {return stop;}
  std::vector<int> getHits() {return hits_detectorID;}
  std::vector<int> getHitsLoose() {return hitsLoose_detectorID;}
  
  void setStart(TVector3 s){ start = s; }
  void setStop(TVector3 s){ stop = s; }
  void setHits(std::vector<int> l ) {hits_detectorID = l;}
  void setHitsLoose(std::vector<int> l) {hitsLoose_detectorID = l;}

 private :
  TVector3 start, stop;
  std::vector<int> hits_detectorID, hitsLoose_detectorID;

  ClassDef(sndRecoTrack, 1);
};
