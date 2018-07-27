#include "MuonTaggerHit.h"
#include <iostream>

MuonTaggerHit::MuonTaggerHit(Int_t detID, Float_t digi) : ShipHit(detID, digi) {}

enum Direction { horizontal = 0, vertical = 1 };

void MuonTaggerHit::EndPoints(TVector3 &vbot, TVector3 &vtop)
{
   // Detector ID scheme:
   // 10000 * station + 1000 * direction + strip;
   // sets vbot and vtop to opposing corners of the cuboid
   int station = fDetectorID / 10000;
   Direction direction = static_cast<Direction>((fDetectorID % 10000) / 1000);
   int strip = fDetectorID % 1000;
   const int NR_HORI_STRIPS = 116;    // nr horizontal strips, X dir, Y coord
   const int NR_VER_STRIPS = 184;     // nr vertical strips, Y dir, X coord
   const float STRIP_XWIDTH = 0.8625; // internal STRIP V, WIDTH, in cm
   const float EXT_STRIP_XWIDTH_L =
      0.9625; // nominal (R&L) and Left measured external STRIP V, WIDTH, in cm (beam along z, out from the V plane)
   const float EXT_STRIP_XWIDTH_R =
      0.86; // measured Right external STRIP V, WIDTH, in cm (beam along z, out from the V plane)
   const float STRIP_YWIDTH = 0.8625;  // internal STRIP H, WIDTH, in cm
   const float EXT_STRIP_YWIDTH = 0.3; // measured external STRIP H, WIDTH, in cm (nominal 0.4375)
   const float H_STRIP_OFF = 0.1983;   // offset between adjacent H strips, in cm
   const float V_STRIP_OFF = 0.2000;   // offset between adjacent V strips, in cm
   const float total_width =
      (NR_VER_STRIPS - 2) * STRIP_XWIDTH + EXT_STRIP_XWIDTH_L + EXT_STRIP_XWIDTH_R + (NR_VER_STRIPS - 1) * V_STRIP_OFF;
   const float total_height =
      (NR_HORI_STRIPS - 2) * STRIP_YWIDTH + 2 * EXT_STRIP_YWIDTH + (NR_HORI_STRIPS - 1) * H_STRIP_OFF;
   const float x_start = (total_width - EXT_STRIP_XWIDTH_R + EXT_STRIP_XWIDTH_L) / 2;
   const float y_start = total_height / 2;
   float Z = 0;
   /// station conditions - remove once z position automated from geo file
   switch (station) {
   case 1: Z = 874.25; break;
   case 2: Z = 959.25; break;
   case 3: Z = 1004.25; break;
   case 4: Z = 1049.25; break;
   case 5: Z = 1094.25; break;
   default: std::cout << "Invalid station" << std::endl;
   };

   switch (direction) {
   case horizontal: {
      float y;
      auto xtop = x_start;
      auto xbot = x_start - total_width;
      if (strip == 1) { // 1st strip (top)
         y = y_start - EXT_STRIP_YWIDTH / 2;
      } else if (strip == NR_HORI_STRIPS) { // last strip (bottom)
         y = y_start - total_height + EXT_STRIP_YWIDTH / 2;
      } else { // all other horizontal strips
         y = y_start - EXT_STRIP_YWIDTH - (strip - 1.5) * STRIP_YWIDTH - (strip - 1) * H_STRIP_OFF;
      }
      vtop.SetXYZ(xtop, y, Z);
      vbot.SetXYZ(xbot, y, Z);
      break;
   }
   case vertical: {
      float x;
      auto ytop = y_start - total_height;
      auto ybot = y_start;
      if (strip == 1) { // first strip (left)
         x = x_start - EXT_STRIP_XWIDTH_L / 2;
      } else if (strip == NR_VER_STRIPS) { // last strip (right)
         x = x_start - total_width + EXT_STRIP_XWIDTH_R / 2;
      } else { // all other vertical strips
         x = x_start - EXT_STRIP_XWIDTH_L - (strip - 1.5) * STRIP_XWIDTH - (strip - 1) * V_STRIP_OFF;
      }
      vtop.SetXYZ(x, ytop, Z);
      vbot.SetXYZ(x, ybot, Z);
      break;
   }
   }
}

ClassImp(MuonTaggerHit)
