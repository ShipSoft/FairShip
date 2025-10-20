#include "UpstreamTaggerHit.h"
#include "UpstreamTaggerPoint.h"
#include "TRandom.h"
#include <iostream>

using std::cout;
using std::endl;

// -----   Default constructor   --------------
UpstreamTaggerHit::UpstreamTaggerHit()
  : ShipHit(),
    fX(0.),
    fY(0.),
    fZ(0.),
    fTime(0.)
{
}

// -----   Constructor from UpstreamTaggerPoint   --------------
UpstreamTaggerHit::UpstreamTaggerHit(UpstreamTaggerPoint* p, Double_t t0,
                                     Double_t pos_res, Double_t time_res)
  : ShipHit()
{
    fDetectorID = p->GetDetectorID();

    // Smear position with Gaussian resolution
    fX = gRandom->Gaus(p->GetX(), pos_res);
    fY = gRandom->Gaus(p->GetY(), pos_res);
    fZ = gRandom->Gaus(p->GetZ(), pos_res);

    // Smear time with Gaussian resolution
    fTime = gRandom->Gaus(p->GetTime() + t0, time_res);
}

// -----   Destructor   -------------------------
UpstreamTaggerHit::~UpstreamTaggerHit() { }

// -----   Print   ------------------------------
void UpstreamTaggerHit::Print() const
{
    cout << "-I- UpstreamTaggerHit: detector " << fDetectorID << endl;
    cout << "    Position: (" << fX << ", " << fY << ", " << fZ << ") cm" << endl;
    cout << "    Time: " << fTime << " ns" << endl;
}
