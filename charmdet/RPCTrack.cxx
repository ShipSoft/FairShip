#include "RPCTrack.h"

// Default Constructor

RPCTrack::RPCTrack()
 :  TObject(),
	ftheta = 0.,
	fphi = 0,
	fnclusters = 0,
	{}

void RPCTrack::AddTrack(Double_t x, Double_t y, Double_t z)
{
	fcluster_posx.push_back(x);
	fcluster_posy.push_back(y);
	fcluster_posz.push_back(z);
}



