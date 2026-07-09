#include "SiWCaloHit.h"
#include "FairRunSim.h"
#include "ShipUnit.h"
#include "SiWCalo.h"
#include "TGeoBBox.h"
#include "TGeoManager.h"
#include "TGeoNavigator.h"
#include "TROOT.h"

#include <iostream>

SiWCaloHit::SiWCaloHit()
  : SHiP::DetectorHit()
{
    flag = true;
}

SiWCaloHit::SiWCaloHit(Int_t detID, const std::vector<SiWCaloPoint*>& V)
{
    // Sum up signal from all points within the hit
    std::vector<double> _signals;
    double totalSig = 0;

    for (auto* point : V) {
        _signals.push_back(point->GetEnergyLoss());
        fX = point->GetX();
        fY = point->GetY();
        fZ = point->GetZ();
    }

    for (unsigned i = 0; i < _signals.size(); i++) {
        totalSig += _signals[i];
    }

    fSignal = totalSig;
}
// -----   Destructor   ----------------------------------------------------
SiWCaloHit::~SiWCaloHit() {}
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void SiWCaloHit::Print()
{
    std::cout << Form("SiWCaloHit: Detector ID %d, Layer %d, Pixel X %d, Pixel Y %d, Pixel ID %d, Signal %.2f \n",
                      fDetectorID,
                      GetLayer(),
		      GetPixelX(),
		      GetPixelY(),
		      GetPixelID(),
                      GetSignal());
}
