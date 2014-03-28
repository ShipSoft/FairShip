// -------------------------------------------------------------------------
// -----                    ShipConstField source file                  -----
// -------------------------------------------------------------------------
#include "ShipConstField.h"

#include "ShipFieldPar.h"

#include <iomanip>
#include <iostream>

using std::cout;
using std::cerr;
using std::endl;
using std::setw;


// -----   Default constructor   -------------------------------------------
ShipConstField::ShipConstField() 
  : FairField(),
    fPeak(0.),
    fMiddle(0.),
    fBx(0.),
    fBy(0.),
    fBz(0.)
{
  fType = 1;
}
// -------------------------------------------------------------------------



// -----   Standard constructor   ------------------------------------------
ShipConstField::ShipConstField(const char* name, Double_t fPeak,Double_t fMiddle )
  : FairField(name),
    fPeak(fPeak),
    fMiddle(fMiddle)
{
  fType=1;
}
// -------------------------------------------------------------------------



// --------   Constructor from CbmFieldPar   -------------------------------
ShipConstField::ShipConstField(ShipFieldPar* fieldPar)
  : FairField(),
    fPeak(0.),
    fMiddle(0.),
    fBx(0.),
    fBy(0.),
    fBz(0.)
{
  if ( ! fieldPar ) {
    cerr << "-W- ShipBellField::ShipBellField: empty parameter container!"
	 << endl;
    fType=0;
  }
  else {
    fPeak = fieldPar->GetPeak();
    fMiddle = fieldPar->GetMiddle();
    fType = fieldPar->GetType();
  }
}
// -------------------------------------------------------------------------



// -----   Destructor   ----------------------------------------------------
ShipConstField::~ShipConstField() { }
// -------------------------------------------------------------------------


// -----   Get x component of field   --------------------------------------
Double_t ShipConstField::GetBx(Double_t x, Double_t y, Double_t z) {
  
  return 0.;
}
// -------------------------------------------------------------------------


// -----   Get y component of field   --------------------------------------
Double_t ShipConstField::GetBy(Double_t x, Double_t y, Double_t z) {
  return 0.;
}
// -------------------------------------------------------------------------



// -----   Get z component of field   --------------------------------------
Double_t ShipConstField::GetBz(Double_t x, Double_t y, Double_t z) {
  return 0.;
}
// -------------------------------------------------------------------------



// -----   Screen output   -------------------------------------------------
void ShipConstField::Print() {
  cout << "======================================================" << endl;
  cout << "----  " << fTitle << " : " << fName << endl;
  cout << "----" << endl;
  cout << "----  Field type    : constant" << endl;
  cout << "----" << endl;
  cout << "----  Field regions : " << endl;
  cout << "----        x = " << setw(4) << fXmin << " to " << setw(4) 
       << fXmax << " cm" << endl;
  cout << "----        y = " << setw(4) << fYmin << " to " << setw(4) 
       << fYmax << " cm" << endl;
  cout << "----        z = " << setw(4) << fZmin << " to " << setw(4)
       << fZmax << " cm" << endl;
  cout.precision(4);
  cout << "----  B = ( " << fBx << ", " << fBy << ", " << fBz << " ) kG"
       << endl;
  cout << "======================================================" << endl;
}
// -------------------------------------------------------------------------



ClassImp(ShipConstField)
