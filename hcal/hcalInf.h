/**  hcalInf.h
 *@author Mikhail Prokudin
 **
 ** Container of HCAL geometry parameters
 **/

#ifndef HCALINF_H
#define HCALINF_H

#include "TObjArray.h"
#include "TString.h"
#include "TObjString.h"

#include <list>
#include <stdlib.h>

class TMap;

class hcalInf:public TObject
{
public:
  /** This is ROOT requirement **/
 hcalInf() : TObject(), fVariables(NULL), fHcalStr(), fXPos(0.), fYPos(0.),
    fZPos(0.), fNLayers(0), fXSize(0), fYSize(0), fModuleSize(0.), fAbsorber(0.),
    fScin(0.), fTyveec(0.), fThicknessLayer(0.), fCellSize(0.), fHcalSize(),
    fECut(0.), fHCut(0.), fSemiX(0.0), fSemiY(0.0), fFastMC(-1), 
    fSuccess(-1), fFileName("") 
    {};

  static hcalInf* GetInstance(const char* filename);
  /** Getters **/
  inline Double_t GetXPos() const {return fXPos;} 
  inline Double_t GetYPos() const {return fYPos;} 
  inline Double_t GetZPos() const {return fZPos;}
	
  inline Double_t GetModuleSize() const {return fModuleSize;}
  
  inline Int_t    GetNLayers() const {return fNLayers;}
  inline Int_t    GetN1Layers()const {return fN1Layers;}
  inline Double_t GetAbsorber()const {return fAbsorber;}
  inline Double_t GetScin()    const {return fScin;}
  inline Double_t GetTyveec()  const {return fTyveec;}
  inline Double_t GetThicknessLayer() const {return fThicknessLayer;}

  /** Size of HCAL in super modules **/
  inline Int_t GetXSize() const {return fXSize;}
  inline Int_t GetYSize() const {return fYSize;}
  inline Double_t GetContainerXSemiAxiss() const {return fSemiX;}
  inline Double_t GetContainerYSemiAxiss() const {return fSemiY;}

  /** Geant cuts information **/
  inline Double_t GetElectronCut() const {return fECut;}
  inline Double_t GetHadronCut()   const {return fHCut;}

  inline Double_t GetHcalSize(Int_t num) const {
    if (num>-1&&num<3) return fHcalSize[num];
    return -1;
  }
  char GetType(Int_t x, Int_t y) const; //returns type of (X,Y) supercell
  inline Int_t GetFastMC() const {return fFastMC;}
  void DumpContainer() const;
  
  void FreeInstance();

  /** key must be lower case. For example, if have in
   ** geo file AaaA=90, then you should call 
   ** GetVariableStrict("aaaa").
   ** If variable not found, will return -1111 **/
  Double_t GetVariable(const char* key);
  /** key must be lower case. For example, if have in
   ** geo file AaaA=90, then you should call 
   ** GetVariableStrict("aaaa").
   ** If variable not found, will generate Fatal **/
  Double_t GetVariableStrict(const char* key);
  TString GetStringVariable(const char* key);

  void AddVariable(const char* key, const char* value);
  /** If data from Parameter file differs from ours
   ** TODO: should understand a way of storring parameters in SHIP**/
  // void CheckVariables();
protected:

  /** Text file constructor **/
  hcalInf(const char* filename);	
  void CalculateHoleSize();
  virtual ~hcalInf();

  static hcalInf* fInf;
  static Int_t fRefCount;

  
private:
  /** Init all other variables from fVariables
   ** and fHcalStr**/
  void InitVariables();
  /** Ignore a parameter during comparision **/
  Bool_t ExcludeParameter(TString parname);
  /** A map containing all variables
   ** This variable should be saved in parameter file **/
  TMap* fVariables;
  /** Structure of HCAL as array of strings
   ** This variable should be saved in parameter file **/
  TObjArray fHcalStr;
  /** x-position of HCAL center [cm]	 **/
  Double_t fXPos;
  /** y-position of HCAL center [cm] **/
  Double_t fYPos;
  /** z-position of HCAL front [cm] **/
  Double_t fZPos;

  /** Number of HCAL layers **/
  Int_t fNLayers;
  /** Number of layers in first hcal section  **/
  Int_t fN1Layers;

  /** x-size of hcal in supermodules **/
  Int_t fXSize;
  /** y-size of hcal in supermodules **/
  Int_t fYSize;

  /** transverse supermodule size in cm **/
  Double_t fModuleSize;

  /**Thickness of absorber in one layer [cm] **/
  Double_t fAbsorber;
  /**Thickness of scintillator in one layer [cm] **/
  Double_t fScin;
  /**Thickness of tyvec in one layer [cm] **/
  Double_t fTyveec;
  /**Total thickness of layer	[cm] **/
  Double_t fThicknessLayer;
  /**transverse size of HCAL cell for simulation [cm] **/
  Double_t fCellSize;
  /**Size of HCAL container [cm] **/
  Double_t fHcalSize[3];
  /**Electron cut for HCAL **/
  Double_t fECut;
  /**Hadron cut for HCAL **/
  Double_t fHCut;
  /**Semiaxises of keeping volume **/
  Double_t fSemiX;
  Double_t fSemiY;

  /**Flag to run Fast (1) or Full (0) MC code **/
  Int_t fFastMC;

  /** 1 if evething Ok **/
  Int_t fSuccess;

  TString fFileName;

  hcalInf(const hcalInf&);
  hcalInf& operator=(const hcalInf&);

  ClassDef(hcalInf,2);
};

inline char hcalInf::GetType(Int_t x, Int_t y) const
{
  /** Returns the type of the module with position (x,y) **/
  if (x<0||y<0||y>fHcalStr.GetLast()) return 0;
  TObjString* str=(TObjString*)fHcalStr.At(y);
  if (str->GetString().Length()<x) return 0;
  char stri[2]={str->GetString()[x],0};
  return atoi(stri);
}

inline void hcalInf::FreeInstance()
{
  fRefCount--;
  if (fRefCount==0)
  {
    delete this;
    fInf=NULL;
  }
}
#endif
