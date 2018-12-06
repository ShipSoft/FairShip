#include "RPCTrack.h"

// Default Constructor

RPCTrack::RPCTrack()
 :  TObject(),
	ftheta = 0.,
	fphi = 0,
	fnclusters = 0,
	{}
RpcTrack(Double_t theta, Double_t phi)
 :  TObject(),
 	ftheta = theta,
 	fphi = 0,
 	fnclusters=0,
 	{}

void RPCTrack::AddCluster(Double_t x, Double_t y, Double_t z, Int_t dir, Int_t nstation)
{
	fcluster_posx.push_back(x);
	fcluster_posy.push_back(y);
	fcluster_posz.push_back(z);
	fcluster_dir.push_back(dir);
	fcluster_nstation.push_back(nstation);

	fnclusters++;
}



