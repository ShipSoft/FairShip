//
//  EmulsionMagnet.h
//  
// Created by A. Buonaura on 12/09/16

#ifndef EmulsionMagnet_H
#define EmulsionMagnet_H

#include "FairModule.h"                 // for FairModule
#include "Rtypes.h"                     // for ShipMuonShield::Class, Bool_t, etc
#include "TVector3.h"
#include <iostream>

using std::cout;
using std::endl;

class EmulsionMagnet : public FairModule
{
 public:
  EmulsionMagnet(const char* name, const Double_t zC,  const char* Title="EmulsionMagnet");
  EmulsionMagnet();
  ~EmulsionMagnet();

  void SetGaps(Double_t Up, Double_t Down);
  void SetMagnetSizes(Double_t X, Double_t Y, Double_t Z);
  void SetMagnetColumn(Double_t ColX, Double_t ColY, Double_t ColZ);
  void SetBaseDim(Double_t BaseX, Double_t BaseY, Double_t BaseZ);
  void SetCoilParameters(Double_t radius, Double_t height1, Double_t height2, Double_t Distance);
  void SetCoilParameters(Double_t X, Double_t Y, Double_t height1, Double_t height2, Double_t Thickness);
  void SetDesign(Int_t Design);
  void SetMagneticField(Double_t B); 
  
  void SetPillarDimensions(Double_t X, Double_t Y, Double_t Z);
  void SetCutDimensions(Double_t CutLength, Double_t CutHeight); 

  void SetConstantField(Bool_t EmuMagnetConstField);

  void ConstructGeometry();
  Int_t InitMedium(const char* name);
 
  ClassDef(EmulsionMagnet,5);

 protected:

  Double_t fMagnetX;
  Double_t fMagnetY;
  Double_t fMagnetZ;
  Double_t fColumnX;
  Double_t fColumnY;
  Double_t fColumnZ;
  Double_t fCutLength; //dimensions of triangular cuts for lateral volumes (only in NuTauTargetDesign 3)
  Double_t fCutHeight;
  Double_t fBaseX;
  Double_t fBaseY;
  Double_t fBaseZ;
  Double_t fCenterZ;
  Double_t fCoilR;
  Double_t fCoilX;
  Double_t fCoilY;
  Double_t fCoilH1; //thickness of the upper (left) coil  
  Double_t fCoilH2; //thickness of the loweer (right) coil  
  Double_t fCoilDist;
  Double_t fCoilThickness;//Thickness in Z config. fDesign==3
  Double_t fGapUpstream;
  Double_t fGapDownstream;
  Double_t fField;
  Int_t fDesign; //0= TP_config, 1=new_config, 2=no magnet
  Double_t fPillarX;
  Double_t fPillarY;
  Double_t fPillarZ;  
  Bool_t fConstField;
};

#endif
