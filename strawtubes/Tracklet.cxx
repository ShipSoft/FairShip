#include "Tracklet.h"
#include "strawtubesPoint.h"
#include <unordered_map>
#include <iostream>

using std::cout;
using std::endl;

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

Int_t Tracklet::link2MCTrack(TClonesArray* strawPoints, Float_t min=0.6)
{
 Int_t nTot = aTracklet.size();
 std::unordered_map<int, int> MC;
 Int_t trackID = -1;
 for(std::vector<int>::size_type i = 0; i != aTracklet.size(); i++) {
    trackID = dynamic_cast<strawtubesPoint*>(strawPoints->At(aTracklet[i]))->GetTrackID();
    MC[trackID]+=1./nTot;
    if (MC[trackID]>min){break;}
 }
 return trackID;
 
}

ClassImp(Tracklet)

