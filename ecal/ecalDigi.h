// A very simple digitization scheme for Ship ECAL
// Operate over ecalStructure

#ifndef ECALDIGI_H
#define ECALDIGI_H

#include "FairTask.h"

#include <map>

class ecalStructure;

class ecalDigi : public FairTask
{
public:
  /** Default constructor **/
  ecalDigi();
  /** Standard constructor. Use this **/
  ecalDigi(const char* name, Int_t iVerbose);
  /** Destructor **/
  virtual ~ecalDigi();
  /** Initialization of the task **/  
  virtual InitStatus Init();
  void InitPython(ecalStructure* structure);
  /** Executed task **/ 
  virtual void Exec(Option_t* option);
  /** Finish task **/ 
  virtual void Finish();
  

  void SetPedestal(Short_t ped=80) {fPedestal=ped;}
  void SetADCMax(Short_t adcmax=16384) {fADCMax=adcmax;}
  void SetADCNoise(Float_t adcnoise=1.0e-3) {fADCNoise=adcnoise;}
  void SetADCChannel(Float_t adcchannel=1.0e-3) {fADCChannel=adcchannel;}

  //Map: channel number -> ADC channel in GeV 
  void SetChannelMap(std::map<Int_t, Float_t> map) {fChannelMap=map;}
  //TODO: An ugly way, need database here
  void LoadChannelMap(const char* filename);

  Short_t GetPedestal() const {return fPedestal;}
  Short_t GetADCMax() const {return fADCMax;}
  Float_t GetADCNoise() const {return fADCNoise;}
  Float_t GetADCChannel() const {return fADCChannel;}
private:
  // Pedestal 
  Short_t fPedestal;
  // ADC maximum
  Short_t fADCMax;
  // ADC Noise
  Float_t fADCNoise;
  // ADC channel (in energy deposition in _SCINTILLATOR_)
  Float_t fADCChannel;
  // Calorimeter structure
  ecalStructure* fStr;	//!

  // May be better use Float_t*?
  std::map<Int_t, Float_t> fChannelMap;	//! Map: channel number -> ADC channel in GeV

  ecalDigi(const ecalDigi&);
  ecalDigi& operator=(const ecalDigi&);

  ClassDef(ecalDigi, 1);
};

#endif
