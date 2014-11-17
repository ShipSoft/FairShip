#ifndef HCALLIGHTMAP_H
#define HCALLIGHTMAP_H

#include "TNamed.h"

class hcalLightMap : public TNamed
{
public:
 hcalLightMap() : TNamed(), fSSide(0.), fS(0), fSize(0), fData(NULL) {};
  hcalLightMap(const char* fname, const char* title="Light collection efficiency map");
  Double_t Data(Double_t x, Double_t y)
    {Int_t n=GetNum(x,y); if (n<0) return n; return fData[n];}
  Int_t GetNum(Double_t x, Double_t y)
  {
    Double_t lx=x+0.5; Double_t ly=y+0.5;
    if (lx<0) lx=0; if (ly<0) ly=0;
    if (lx>1) lx=1; if (ly>1) ly=1;
    Int_t ix=(Int_t)(lx/fSSide);
    Int_t iy=(Int_t)(ly/fSSide);
    return iy*fS+ix;
  }
  virtual ~hcalLightMap() {delete fData;}
private:
  /** Read information from file **/
  void Init(const char* filename);
  /** Fix a light collection map **/
  void FillGaps();
  /** Set average efficiency of light collection to 1.0 **/
  void Normalize();
  /** Step of the light map **/
  Double_t fSSide;		//!
  /** Size of side of the light map in steps**/
  Int_t fS;			//!
  /** Size of the light map **/
  Int_t fSize;			//!
  /** Light collection efficiency map **/
  Double_t* fData;		//!

  hcalLightMap(const hcalLightMap&);
  hcalLightMap& operator=(const hcalLightMap&);

  ClassDef(hcalLightMap, 1)
};

#endif
