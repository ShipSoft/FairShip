#ifndef SND_SIWCALO_SIWCALO_H_
#define SND_SIWCALO_SIWCALO_H_

#include "Rtypes.h"
#include "SiWCaloPoint.h"
#include "TVector3.h"
#include "Detector.h"

class TGeoVolume;
class TGeoVolumeAssembly;
class TGeoMedium;
class FairVolume;

class SiWCalo : public SHiP::Detector<SiWCaloPoint>{
 public:
  SiWCalo(const char* name, Bool_t Active, const char* Title = "", Int_t DetId = 0);
  SiWCalo();

  void SetSiWCaloParameters(Double_t absWidth, Double_t absHeight,
                            Double_t sensorWidth, Double_t sensorLength,
                            Int_t nLayers, Double_t zPosition,
                            Double_t absThickness,
			    Double_t sensorThickness,
			    Double_t NPixels,
                            Double_t absSpacing, Double_t moduleOffset);

  virtual void CreateSiliconPlane(const char* name,
				  TGeoVolumeAssembly* modMotherVol,
				  Double_t sensorWidth,
                                  Double_t sensorLength,
				  Double_t sensorThickness,
                                  Double_t NPixels, TGeoMedium* material,
                                  Int_t layerId);

  void ConstructGeometry() override;

  Bool_t ProcessHits(FairVolume* vol = nullptr) override;

 private:
  Double_t fAbsWidth;
  Double_t fAbsHeight;
  Double_t fSensorWidth;
  Double_t fSensorLength;
  Double_t fSensorThickness;
  Int_t fLayers;
  Double_t fZPosition;
  Double_t fAbsThickness;
  Double_t fNPixels;
  Double_t fAbsSpacing;
  Double_t fModuleOffset;

  SiWCalo(const SiWCalo&) = delete;
  SiWCalo& operator=(const SiWCalo&) = delete;
  ClassDefOverride(SiWCalo, 2)
};

#endif  // SND_SIWCALO_SIWCALO_H_
