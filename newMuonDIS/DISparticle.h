// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef NEWMUONDIS_DISPARTICLE_H_
#define NEWMUONDIS_DISPARTICLE_H_

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

#endif  // NEWMUONDIS_DISPARTICLE_H_
