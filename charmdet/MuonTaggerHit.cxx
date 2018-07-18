#include "MuonTaggerHit.h"

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
   const float x_start = -(total_width - EXT_STRIP_XWIDTH_R + EXT_STRIP_XWIDTH_L) / 2;
   const float y_start = total_height / 2;
   const float Z = 0; //TODO
   switch (direction) {
   case horizontal:
      vbot.SetXYZ(x_start, y_start, Z); // TODO
      vtop.SetXYZ(x_start + total_width, y_start, Z); // TODO
      break;
   case vertical:
      vbot.SetXYZ(x_start , y_start - total_height, Z); // TODO
      vtop.SetXYZ(x_start , y_start, Z); // TODO
      break;
   }
}

ClassImp(MuonTaggerHit)
