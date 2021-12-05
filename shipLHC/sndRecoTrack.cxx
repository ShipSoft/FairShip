#include "sndRecoTrack.h"

sndRecoTrack::sndRecoTrack(TVector3 track_start, TVector3 track_stop, std::vector<int> hits, std::vector<int> hitsLoose) : 
  start(track_start), stop(track_stop), hits_detectorID(hits), hitsLoose_detectorID(hitsLoose) {;}

