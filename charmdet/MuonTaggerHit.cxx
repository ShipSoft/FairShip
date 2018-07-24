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
   const float STRIP_XWIDTH = 0.8625; // internal STRIP V, WIDTH, in cm
   const float EXT_STRIP_XWIDTH_L =
      0.9625; // nominal (R&L) and Left measured external STRIP V, WIDTH, in cm (beam along z, out from the V plane)
   const float EXT_STRIP_XWIDTH_R =
      0.86; // measured Right external STRIP V, WIDTH, in cm (beam along z, out from the V plane)
   const float STRIP_YWIDTH = 0.8625;  // internal STRIP H, WIDTH, in cm
   const float EXT_STRIP_YWIDTH = 0.3; // measured external STRIP H, WIDTH, in cm (nominal 0.4375)
   /* gGeoManager-> */                 // Get Z position
   const float total_width = 182 * STRIP_XWIDTH + EXT_STRIP_XWIDTH_L + EXT_STRIP_XWIDTH_R;
   const float total_height = 114 * STRIP_YWIDTH + 2 * EXT_STRIP_YWIDTH;
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
   case horizontal:
      if (strip == 1) { // 1st strip (top)
         vtop.SetXYZ(x_start, y_start, Z);
         vbot.SetXYZ(x_start - total_width, y_start - EXT_STRIP_YWIDTH, Z);
      } else if (strip == 116) { // last strip (bottom)
         vtop.SetXYZ(x_start, y_start - EXT_STRIP_YWIDTH - 114 * STRIP_YWIDTH, Z);
         vbot.SetXYZ(x_start - total_width, y_start - total_height, Z);
      } else { // all other horizontal strips
         vtop.SetXYZ(x_start, y_start - EXT_STRIP_YWIDTH - (strip - 2) * STRIP_YWIDTH, Z);
         vbot.SetXYZ(x_start - total_width, y_start - EXT_STRIP_YWIDTH - (strip - 1) * STRIP_YWIDTH, Z);
      }
      break;
   case vertical:
      if (strip == 1) { // first strip (left)
         vtop.SetXYZ(x_start, y_start - total_height, Z);
         vbot.SetXYZ(x_start - EXT_STRIP_XWIDTH_L, y_start, Z);
      } else if (strip == 184) { // last strip (right)
         vtop.SetXYZ(x_start - EXT_STRIP_XWIDTH_L - 182 * STRIP_XWIDTH, y_start - total_height, Z);
         vbot.SetXYZ(x_start - total_width, y_start, Z);
      } else { // all other vertical strips
         vtop.SetXYZ(x_start - EXT_STRIP_XWIDTH_L - (strip - 2) * STRIP_XWIDTH, y_start - total_height, Z);
         vbot.SetXYZ(x_start - EXT_STRIP_XWIDTH_L - (strip - 1) * STRIP_XWIDTH, y_start, Z);
      }
      break;
   }
}

ClassImp(MuonTaggerHit)
