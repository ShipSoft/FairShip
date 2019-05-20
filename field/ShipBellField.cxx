// -------------------------------------------------------------------------
// -----                    ShipBellField source file                  -----
// -------------------------------------------------------------------------
#include "ShipBellField.h"
#include "math.h"
#include "ShipFieldPar.h"

#include <iomanip>
#include <iostream>

using std::cout;
using std::cerr;
using std::endl;
using std::setw;

Double_t kilogauss = 1.;
Double_t tesla     = 10*kilogauss;

Double_t cm  = 1;       // cm
Double_t m   = 100*cm;  //  m
Double_t mm  = 0.1*cm;  //  mm


// -----   Default constructor   -------------------------------------------
ShipBellField::ShipBellField() 
  : FairField(),
    fPeak(0.),
    fMiddle(0.),
    fBtube(0.)
{
  fType = 1;
  fInclTarget=kFALSE;
}
// -------------------------------------------------------------------------



// -----   Standard constructor   ------------------------------------------
ShipBellField::ShipBellField(const char* name, Double_t Peak,Double_t Middle,Int_t orientation, Double_t Btube )
  : FairField(name),
    fPeak(Peak),
    fMiddle(Middle),
    fBtube(Btube)
{
  fType=1;
  fInclTarget=kFALSE;
  fOrient = orientation;
  fBtube = Btube;
}
// -------------------------------------------------------------------------



// --------   Bell constructor from FieldPar   -------------------------------
ShipBellField::ShipBellField(ShipFieldPar* fieldPar)
  : FairField(),
    fPeak(0.),
    fMiddle(0.),
    fBtube(0.),
    fInclTarget(kFALSE)
{
  if ( ! fieldPar ) {
    cerr << "-W- ShipBellField::ShipBellField: empty parameter container!"
	 << endl;
    fType=0;
  }
  else {
    fPeak   = fieldPar->GetPeak();
    fMiddle = fieldPar->GetMiddle();
    fBtube  = fieldPar->GetBtube();
    fType   = fieldPar->GetType();
  }
}
// -------------------------------------------------------------------------



// -----   Destructor   ----------------------------------------------------
ShipBellField::~ShipBellField() { }
// -------------------------------------------------------------------------

// -----   Get x component of field   --------------------------------------
void ShipBellField::IncludeTarget(Double_t xy, Double_t z, Double_t l) {
  fInclTarget = kTRUE;
  targetXY = xy;
  targetZ0 = z;
  targetL = l;
}
// -----   Get x component of field   --------------------------------------
Double_t ShipBellField::GetBx(Double_t x, Double_t y, Double_t z) {
  if (fOrient==1){ return 0.;}
  else {
    Double_t zlocal=fabs(z-fMiddle)/100.; //zlocal: convert cm->m
   //old Bell field from Wilfried Flegel
   //Double_t bx= fPeak/(1.+pow(fabs(zlocal)/2.1,6.));
   //new field based on simulation of Davide Tommasini (22/1/2015)
    
    Double_t bx=0.;
    //field in box 20 cm larger than inner tube.
    if ( (fabs(x)<2.7*m) && (fabs(y)<fBtube+0.2*m))  {
      if (zlocal<3.8) {
        bx=0.14361*exp( -0.5 * pow((zlocal-0.45479E-01)/2.5046,2.));
      }else if (zlocal<11.9) {
        bx=0.19532-0.61512E-01*zlocal+0.68447E-02*pow(zlocal,2.)-0.25672E-03*pow(zlocal,3.);
      }
      bx=((fPeak/tesla)/0.14361)*bx*tesla;
    }
    // cout << "Bell GetBX " << x << ", " << y << ", " << z << ", Bx= " << bx << endl;
   return bx;
  }
}

// -------------------------------------------------------------------------


// -----   Get y component of field   --------------------------------------
Double_t ShipBellField::GetBy(Double_t x, Double_t y, Double_t z) {
  Double_t by = 0.;
  if (fInclTarget && z < targetZ0+targetL && z > targetZ0){
 // check if in target area
    if (fabs(x)<targetXY && fabs(y)<targetXY) {by = 1*tesla;}
    if (fabs(x)>2*targetXY && fabs(x)<3*targetXY && fabs(y)<targetXY) {by = -1*tesla;}
  }
  else if (fOrient==1){
   Double_t zlocal=(z-fMiddle)/100.;
   by= fPeak/(1.+pow(fabs(zlocal)/2.1,6.));
   //cout << "Bell GetBY " << z << ", By= " << by << endl;
  }
  return by;

}
// -------------------------------------------------------------------------



// -----   Get z component of field   --------------------------------------
Double_t ShipBellField::GetBz(Double_t x, Double_t y, Double_t z) {
  return 0.;
}
// -------------------------------------------------------------------------



// -----   Screen output   -------------------------------------------------
void ShipBellField::Print() {
  cout << "======================================================" << endl;
  cout << "----  " << fTitle << " : " << fName << endl;
  cout << "----" << endl;
  cout << "----  Field type    : constant" << endl;
  cout << "----" << endl;
  cout << "----  Field regions : " << endl;
  cout.precision(4);
  cout << "======================================================" << endl;
}
// -------------------------------------------------------------------------



ClassImp(ShipBellField)


