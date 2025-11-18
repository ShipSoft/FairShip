#include "Tracklet.h"
#include "strawtubesPoint.h"
#include <unordered_map>

// -----   Default constructor   -------------------------------------------
Tracklet::Tracklet()

{
 flag = 0;
}

Tracklet::Tracklet(Int_t fl, std::vector<unsigned int>  aT)
{
 flag = fl;
 aTracklet = aT;

}

// -----   Destructor   ----------------------------------------------------
Tracklet::~Tracklet() { }
// -------------------------------------------------------------------------

Int_t Tracklet::link2MCTrack(std::vector<strawtubesPoint>* strawPoints, Float_t min)
{
 Int_t nTot = aTracklet.size();
 std::unordered_map<int, int> MC;
 Int_t trackID = -1;
 for(std::vector<int>::size_type i = 0; i != aTracklet.size(); i++) {
    trackID = (*strawPoints)[aTracklet[i]].GetTrackID();
    MC[trackID]+=1./nTot;
    if (MC[trackID]>min){break;}
 }
 return trackID;
}
