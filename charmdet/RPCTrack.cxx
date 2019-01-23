#include "RPCTrack.h"

// -----   Default constructor   -------------------------------------------
RPCTrack::RPCTrack()
  : TObject()
{
}

// -----   Standard constructor   ------------------------------------------
RPCTrack::RPCTrack(Float_t m, Float_t b)
{
  fm=m;
  fb=b;
}

// -----   Copy constructor   ----------------------------------------------
RPCTrack::RPCTrack(const RPCTrack& ti)
  : TObject(ti),
    fm(ti.fm),
    fb(ti.fb)
{
}
// -----   Destructor   ----------------------------------------------------
RPCTrack::~RPCTrack() 
{ 
}
// -------------------------------------------------------------------------

ClassImp(RPCTrack)
