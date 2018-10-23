#ifndef MUONTAGGERHIT_H
#define MUONTAGGERHIT_H

#include "ShipHit.h"

class MuonTaggerHit : public ShipHit {
public:
   MuonTaggerHit() : ShipHit() {}
   ~MuonTaggerHit() = default;
   MuonTaggerHit(Int_t detID, Float_t digi);
   void EndPoints(TVector3 &top, TVector3 &bot);

private:
    MuonTaggerHit(const MuonTaggerHit& other); 
    MuonTaggerHit operator=(const MuonTaggerHit& other); 

   ClassDef(MuonTaggerHit, 1)
};

#endif
