// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include <cmath>
#include <iostream>

#include "TimeDet.h"
#include "TimeDetPoint.h"

namespace {

bool close(double lhs, double rhs, double tolerance = 1e-9) {
  return std::abs(lhs - rhs) < tolerance;
}

bool check_close(const char* name, double actual, double expected) {
  if (close(actual, expected)) return true;
  std::cerr << name << ": expected " << expected << ", got " << actual
            << std::endl;
  return false;
}

}  // namespace

int main() {
  TimeDet time_det("TimeDet", true);

  bool ok = true;
  ok &= time_det.GetNColumns() == 3;
  ok &= time_det.GetNRows() == 110;
  ok &= time_det.GetNBars() == 330;

  ok &= check_close("bar size X", time_det.GetBarSizeX(), 140.0);
  ok &= check_close("bar size Y", time_det.GetBarSizeY(), 6.0);
  ok &= check_close("bar size Z", time_det.GetBarSizeZ(), 1.0);
  ok &= check_close("bar overlap X", time_det.GetBarOverlapX(), 10.0);
  ok &= check_close("bar overlap Y", time_det.GetBarOverlapY(), 0.55);

  ok &= check_close("column 0 X", time_det.GetXCol(0), -130.0);
  ok &= check_close("column 1 X", time_det.GetXCol(1), 0.0);
  ok &= check_close("column 2 X", time_det.GetXCol(2), 130.0);
  ok &= check_close(
      "column overlap X",
      time_det.GetBarSizeX() - (time_det.GetXCol(1) - time_det.GetXCol(0)),
      10.0);

  ok &= check_close("row 0 Y", time_det.GetYRow(0), -297.025);
  ok &= check_close("row 109 Y", time_det.GetYRow(109), 297.025);
  ok &= check_close("row pitch Y", time_det.GetYRow(1) - time_det.GetYRow(0),
                    5.45);
  ok &= check_close(
      "row overlap Y",
      time_det.GetBarSizeY() - (time_det.GetYRow(1) - time_det.GetYRow(0)),
      0.55);
  ok &= check_close("covered height Y",
                    (time_det.GetYRow(109) + time_det.GetBarSizeY() / 2.0) -
                        (time_det.GetYRow(0) - time_det.GetBarSizeY() / 2.0),
                    600.05);

  ok &= check_close("Z col0 row0", time_det.GetZBar(0, 0), 0.0);
  ok &= check_close("Z col0 row1", time_det.GetZBar(1, 0), 1.2);
  ok &= check_close("Z col1 row0", time_det.GetZBar(0, 1), 9.0);
  ok &= check_close("Z col1 row1", time_det.GetZBar(1, 1), 10.2);

  int row = -1;
  int col = -1;
  time_det.GetBarRowCol(329, row, col);
  ok &= row == 109;
  ok &= col == 2;

  if (!ok) return 1;

  std::cout << "Timing detector geometry matches ShipSoft/Geometry: "
            << "3 columns x 110 rows, 1400 x 60 x 10 mm bars, "
            << "5.5 mm vertical overlap" << std::endl;
  return 0;
}
