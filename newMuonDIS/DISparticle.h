#ifndef SHIPMuDIS_DISparticle_H_
#define SHIPMuDIS_DISparticle_H_

#include "Rtypes.h"   // for Double_t, Int_t, Double32_t, etc
#include "TObject.h"  // for TObject

class DISparticle : public TObject {
 public:
  DISparticle() {};
  ~DISparticle() override {};

  int pid;
  double px;
  double py;
  double pz;
  double E;


  ClassDefOverride(DISparticle, 1);
};

inline std::ostream& operator<<(std::ostream& os,
				const DISparticle& p)
{
  os << "[" << p.pid
     << "," << p.px
     << "," << p.py
     << "," << p.pz
     << "," << p.E
     << "]";
  return os;
}

#endif
