#include "SndlhcHit.h"


// -----   Default constructor   -------------------------------------------
SndlhcHit::SndlhcHit()
  : TObject(),
   fdigiLowLeft(0),
   fdigiLowRight(0),
   fdigiHighLeft(0),
   fdigiHighRight(0),
    fDetectorID(-1)
{
}
// -------------------------------------------------------------------------



// -----   Standard constructor   ------------------------------------------
SndlhcHit::SndlhcHit(Int_t detID, Float_t dLL,Float_t dLR,Float_t dHL,Float_t dHR)
  :TObject(),
   fdigiLowLeft(dLL),
   fdigiLowRight(dLR),
   fdigiHighLeft(dHL),
   fdigiHighRight(dHR),
   fDetectorID  (detID)
{
}

std::unordered_map<std::string, float> SndlhcHit::GetDigis()
{
 std::unordered_map<std::string, float> digits;
 digits["lowLeft"]   =   fdigiLowLeft;
 digits["lowRight"]=   fdigiLowRight;
 digits["highLeft"]=   fdigiHighLeft;
 digits["highRight"]=   fdigiHighRight;
 return digits;
}
// -------------------------------------------------------------------------


// -----   Destructor   ----------------------------------------------------
SndlhcHit::~SndlhcHit() { }
// -------------------------------------------------------------------------


ClassImp(SndlhcHit)
