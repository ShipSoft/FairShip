#include "RPCTrack.h"

<<<<<<< HEAD
// Default Constructor

RPCTrack::RPCTrack()
 :  TObject(),
        fm(0),
        fb(0),
	ftheta(0.),
	fphi(0.),
	fnclusters(0)
	{}

// -----   Standard constructor   ------------------------------------------
RPCTrack::RPCTrack(Float_t m, Float_t b)
  : TObject(),
    fm(m),
    fb(b),
    ftheta(0.),
    fphi(0.),
    fnclusters(0)
{
}

RPCTrack::RPCTrack(Double_t theta, Double_t phi)
 :  TObject(),
    fnclusters(0),
    ftheta(theta),
    fphi(phi)
 	{
	}

// -----   Copy constructor   ----------------------------------------------
RPCTrack::RPCTrack(const RPCTrack& ti)
  : TObject(ti),
    fm(ti.fm),
    fb(ti.fb),
    fnclusters(ti.fnclusters)
    ftheta(ti.ftheta)
    fphi(ti.fphi)
{
}

void RPCTrack::AddCluster(Double_t x, Double_t y, Double_t z, Int_t dir, Int_t nstation)
{
	fcluster_posx.push_back(x);
	fcluster_posy.push_back(y);
	fcluster_posz.push_back(z);
	fcluster_dir.push_back(dir);
	fcluster_nstation.push_back(nstation);

	fnclusters++;
}

// -----   Destructor   ----------------------------------------------------
RPCTrack::~RPCTrack() 
{ 
}
// -------------------------------------------------------------------------

ClassImp(RPCTrack)
