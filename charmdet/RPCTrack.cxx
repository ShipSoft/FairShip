#include "RPCTrack.h"

// Default Constructor

RPCTrack::RPCTrack()
 :  TObject(),
        fm(0),
        fb(0),
        fnrun(0),
        ftrigger(0),
        ftrackID(0),
	ftheta(0.),
	fphi(0.),
	fnclusters(0),
        fslopexz(0.),
        fslopeyz(0.)
	{}

// -----   Standard constructor   ------------------------------------------
RPCTrack::RPCTrack(Float_t m, Float_t b)
  : TObject(),
    fm(m),
    fb(b),
    ftheta(0.),
    fphi(0.),
    fnrun(0),
    ftrigger(0),
    ftrackID(0),
    fslopexz(0.),
    fslopeyz(0.),
    fnclusters(0)
{
}

RPCTrack::RPCTrack(Float_t theta, Float_t phi, Float_t slopexz, Float_t slopeyz)
 :  TObject(),
    fnclusters(0),
    ftheta(theta),
    fphi(phi),
    fslopexz(slopexz),
    fslopeyz(slopeyz),
    fnrun(0),
    ftrigger(0),
    ftrackID(0),
    fm(0),
    fb(0)
 	{
	}

// -----   Copy constructor   ----------------------------------------------
RPCTrack::RPCTrack(const RPCTrack& ti)
  : TObject(ti),
    fm(ti.fm),
    fb(ti.fb),
    fnrun(ti.fnrun),
    fspill(ti.fspill),
    ftrigger(ti.ftrigger),
    ftrackID(ti.ftrackID),
    fnclusters(ti.fnclusters),
    ftheta(ti.ftheta),
    fphi(ti.fphi)
{
}

void RPCTrack::AddCluster(Float_t x, Float_t y, Float_t z, Int_t dir, Int_t nstation)
{
	fcluster_posx.push_back(x);
	fcluster_posy.push_back(y);
	fcluster_posz.push_back(z);
	fcluster_dir.push_back(dir);
	fcluster_nstation.push_back(nstation);

	fnclusters++;
}

TVector3 RPCTrack::GetClusterPos(const int icluster)

{
       Float_t x = fcluster_posx[icluster];
       Float_t y = fcluster_posy[icluster];
       Float_t z = fcluster_posz[icluster];

       return TVector3(x,y,z);

}

// -----   Destructor   ----------------------------------------------------
RPCTrack::~RPCTrack() 
{ 
}
// -------------------------------------------------------------------------

ClassImp(RPCTrack)
