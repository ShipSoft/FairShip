#ifndef SHIPMuDIS_DISparticle_H_
#define SHIPMuDIS_DISparticle_H_

#include "TObject.h"           // for TObject
#include "Rtypes.h"            // for Double_t, Int_t, Double32_t, etc

class DISparticle : public TObject {
 public:
  DISparticle(){};
  ~DISparticle() override {};

  int pid;
  double px;
  double py;
  double pz;
  double E;

  ClassDefOverride(DISparticle, 1);

};

#endif
