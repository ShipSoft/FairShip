/** Quality check file for calorimeter reconstruction.
 ** A try to develop a tool for comparison different reconstruction
 ** procedures.
 ** Idea: Select clean MC photons (e.g. without daughter particles) 
 ** and find closest reconstructed photon. **/

#ifndef ECALDRAWER_H
#define ECALDRAWER_H

#include "FairTask.h"

#include "TString.h"

#include <math.h>
#include <list>

class TTree;
class TClonesArray;
class TASImage;
class TText;

class ecalStructure;
class ecalInf;
class ecalCell;
class ecalDrawerItem;
class ecalPoint;

class ecalDrawer: public FairTask
{
public:
  /** Default constructor. Requirement of ROOT system **/
  ecalDrawer();

  /** Standard constructor **/
  ecalDrawer(const char *name, const Int_t iVerbose=1);

  /** Destructor **/
  virtual ~ecalDrawer();

  /** Set prefix to name of images
   ** File will be named like: prefix0000.png **/
  inline void SetNamePrefix(const char* prefix) {fNamePrefix=prefix;}
  inline void SetCellSize(Int_t size) {fCellSize=size;}

  Int_t InitPython(TClonesArray* mctracks, TClonesArray* ecalPoints, ecalStructure* structure, TClonesArray* clusters);
  /** Init **/
  virtual InitStatus Init();
  virtual void Exec(Option_t* option);
  virtual void Finish();
private:
  TString fNamePrefix;		//!
  /** An image and its size **/
  TASImage* fC;			//!
  Int_t fCellSize;
  Int_t fCX;
  Int_t fCY;

  /** Normalization **/
  Double_t fMaxEnergyDep;
  /** Structure and info for drawing **/
  ecalStructure* fStr;	//!
  ecalInf* fInf;		//!
  TString fEdging;		//!
  void PutPixel(Int_t x, Int_t y, Float_t r, Float_t g, Float_t b);
  void PutPixel(Int_t x, Int_t y, const char* color);
  /** type==0 for star, type==1 for square **/
  void DrawMark(Double_t x, Double_t y, const char* color, Int_t type);
  /** draw cell with filled color. fEdging used as egding of cell **/
  void DrawCell(ecalCell* cell, Float_t r, Float_t g, Float_t b);
  void DrawCell(ecalCell* cell, const char* color);

  void DrawLine(Double_t x, Double_t y, const char* color, Int_t track);
  void DrawLine(Double_t x1, Double_t y1, Double_t x2, Double_t y2,const char* color);
  /** Draw energy for given point **/
  void DrawEnergy(ecalPoint* p, const char* color);
  void DrawPDG(ecalPoint* p, const char* color);
  void DrawEnergy(Float_t x, Float_t y, Float_t p, const char* color);
  Double_t GetP(ecalPoint* p);

  /** Draw chi2 for photons **/
  void DrawChi2(Float_t x, Float_t y, Float_t chi2, const char* color);

  TText* fTxt;			//!
  void DrawMC();
//  void DrawPhotons();
//  void DrawTracks();
  void DrawCells();

  std::list<ecalDrawerItem*> fCells;		//!
  void DrawImage();

  TClonesArray* fMCTracks;	//!
  TClonesArray* fPoints;	//!
  TClonesArray* fClusters;	//!
  TString fInName;
  /** Event number **/
  Int_t fEventN;

  Double_t fX;
  Double_t fY;
  Double_t fZ;
  Double_t fMCX;
  Double_t fMCY;
  Double_t fMCZ;
  Int_t fMCMotherTrN;

  Double_t fE;
  Double_t fMCE;
  Double_t fPX;
  Double_t fPY;
  Double_t fPZ;
  Double_t fMCPX;
  Double_t fMCPY;
  Double_t fMCPZ;
  Double_t fChi2;
  /** Pdg code. Gamma and neutron(antineutron) only **/
  Int_t fPdgCode;
  /** Distance between this and closest other hit in the calorimeter **/
  Double_t fR;

  ecalDrawer(const ecalDrawer&);
  ecalDrawer& operator=(const ecalDrawer&);

  ClassDef(ecalDrawer, 1)
};

/** Convert Lab color to RGB. Formulas taken from www.easyrgb.com **
 ** L[0.0, 1.0], a[-0.5, 0.5], b[-0.5, 0.5] **/
inline void LabToRGB(Float_t L, Float_t a, Float_t b, Float_t& R, Float_t& G, Float_t& B)
{
  Float_t vY=(L+0.16)/1.16;
  Float_t vX=a/5.00+vY;
  Float_t vZ=vY-b/2.0;
  if (vY*vY*vY>0.008856) vY=vY*vY*vY; else vY=(vY-16.0/116.0)/7.787;
  if (vX*vX*vX>0.008856) vX=vX*vX*vX; else vX=(vX-16.0/116.0)/7.787;
  if (vZ*vZ*vZ>0.008856) vZ=vZ*vZ*vZ; else vZ=(vZ-16.0/116.0)/7.787;
  vX*=0.95047; vZ*=1.08883;
  R= vX*3.2406-vY*1.5372-vZ*0.4986;
  G=-vX*0.9689+vY*1.8758+vZ*0.0415;
  B= vX*0.0557-vY*0.2040+vZ*1.0570;
  if (R>0.0031308) R=1.055*powf(R, 1.0/2.4)-0.055; else R*=12.92;
  if (G>0.0031308) G=1.055*powf(G, 1.0/2.4)-0.055; else G*=12.92;
  if (B>0.0031308) B=1.055*powf(B, 1.0/2.4)-0.055; else B*=12.92;
  if (R<0.0) R=0.0;
  if (G<0.0) G=0.0;
  if (B<0.0) B=0.0;
  Float_t Ln=R*0.3+G*0.6+0.1*B;
  if (Ln>L)   { R*=L/Ln; G*=L/Ln; B*=L/Ln; }
  if (R>1.0) { G/=R; B/=R; R=1.0; }
  if (G>1.0) { R/=G; B/=G; G=1.0; }
  if (B>1.0) { R/=B; G/=B; B=1.0; }
}

inline Float_t Hue_2_RGB(Float_t v1, Float_t v2, Float_t h)
{
  Float_t vh=h;
  if (vh<0) vh+=1;
  if (vh>1) vh-=1;
  if (6*vh<1) return v1+(v2-v1)*6*vh;
  if (2*vh<1) return v2;
  if (3*vh<2) return (v1+(v2-v1)*(2.0/3.0-vh)*6);
  return v1;
}

inline void HSLToRGB(Float_t h, Float_t s, Float_t l, Float_t& R, Float_t& G, Float_t& B)
{
  if (s==0)
  {
    R=G=B=l;
    return;
  }
  Float_t v2;
  Float_t v1;
  if (l<0.5) v2=l*(1+s); else v2=(l+s)-(s*l);
  v1=2*l-v2;
  R=Hue_2_RGB(v1, v2, h+(1.0/3));
  G=Hue_2_RGB(v1, v2, h);
  B=Hue_2_RGB(v1, v2, h-(1.0/3));
}
#endif


