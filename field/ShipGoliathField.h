// -------------------------------------------------------------------------
// -----                    ShipGoliathField header file                   -----
// -----                Created 12/03/18  by E. van Herwijnen          -----
// -------------------------------------------------------------------------


/** ShipGoliathField.h
 **
 **/


#ifndef ShipGoliathField_H
#define ShipGoliathField_H 1


#include "FairField.h"
#include "TFile.h"
#include "TH3D.h"
#include "TVector3.h"

class ShipGoliathField : public FairField
{

 public:    

  /** Default constructor **/
  ShipGoliathField();


  /** Standard constructor 
   ** @param name   Object name
   **/
  ShipGoliathField(const char* name);


  /** Destructor **/
  virtual ~ShipGoliathField();

  void Init(const char* fieldfile);

  Double_t coords[13][6]; 
  
  //! return value at position
  //TVector3 get(const TVector3& pos) const;
  //void get(const double& posX, const double& posY, const double& posZ, double& Bx, double& By, double& Bz) const;
  void getpos(TString vol, TVector3 &bot, TVector3 &top) const;

  void close();  
  
  /** Get components of field at a given point 
   ** @param x,y,z   Point coordinates [cm]
   **/
  virtual Double_t GetBx(Double_t x, Double_t y, Double_t z);
  virtual Double_t GetBy(Double_t x, Double_t y, Double_t z);
  virtual Double_t GetBz(Double_t x, Double_t y, Double_t z);

  /** Screen output **/
  virtual void Print();
  
  TFile* fieldmap = NULL;
  
  void sethistbxyz(TH3D* histbx, TH3D* histby,TH3D* histbz ) {
    fhistbx=histbx;  
    fhistby=histby;  
    fhistbz=histbz;
  };
  
  TH3D* gethistbx() const { return fhistbx;};  
  TH3D* gethistby() const { return fhistby;}; 
  TH3D* gethistbz() const { return fhistbz;};  
    
  Float_t kilogauss = 1.;
  Float_t tesla     = 10*kilogauss;

  Float_t cm  = 1;       // cm
  Float_t m   = 100*cm;  //  m
  Float_t mm  = 0.1*cm;  //  mm
     
 private:
   double fMiddle;
   double fPeak;
   int fOrient;

   TH3D* fhistbx;
   TH3D* fhistby;
   TH3D* fhistbz;   

   Double_t xmin, xmax, ymin, ymax, zmin, zmax;
   
   
   
ClassDef(ShipGoliathField, 2);

};


#endif
