// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

#ifndef SHIPMuDIS_DISparticle_H_
#define SHIPMuDIS_DISparticle_H_

#include <ostream>

class DISparticle {
 public:
  DISparticle() {
    pid = 0;
    px = 0;
    py = 0;
    pz = 0;
    E = 0;
  };
  ~DISparticle() {};

  int pid;
  double px;
  double py;
  double pz;
  double E;
};

inline std::ostream& operator<<(std::ostream& os, const DISparticle& p) {
  os << "[" << p.pid << "," << p.px << "," << p.py << "," << p.pz << "," << p.E
     << "]";
  return os;
}

#endif
