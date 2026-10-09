// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef NEWMUONDIS_DISPARTICLE_H_
#define NEWMUONDIS_DISPARTICLE_H_

#include <ostream>

class DISparticle {
 public:
  int pid = 0;
  double px = 0.;
  double py = 0.;
  double pz = 0.;
  double E = 0.;
};

inline std::ostream& operator<<(std::ostream& os, const DISparticle& p) {
  os << "[" << p.pid << "," << p.px << "," << p.py << "," << p.pz << "," << p.E
     << "]";
  return os;
}

#endif  // NEWMUONDIS_DISPARTICLE_H_
