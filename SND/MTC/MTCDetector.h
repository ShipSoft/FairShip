// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SND_MTC_MTCDETECTOR_H_
#define SND_MTC_MTCDETECTOR_H_

#include <array>
#include <map>
#include <string>  // for string

#include "Detector.h"
#include "MTCDetPoint.h"
#include "TGeoMatrix.h"

class TGeoVolume;
class TGeoVolumeAssembly;
class TGeoMedium;
class FairVolume;

class MTCDetector : public SHiP::Detector<MTCDetPoint> {
 public:
  MTCDetector(const char* name, Bool_t Active, const char* Title = "",
              Int_t DetId = 0);
  MTCDetector();

  void SetMTCParameters(Double_t width, Double_t height,
                        Double_t fiber_tilt_angle, Double_t iron_thickness,
                        Double_t scifi_thickness, Int_t num_of_agg_channels,
                        Double_t scint_cell_size, Double_t scint_thickness,
                        Int_t number_of_layers, Double_t z_position,
                        Double_t field_strength);
  virtual void CreateScintModule(const char* name,
                                 TGeoVolumeAssembly* modMotherVol,
                                 Double_t z_shift, Double_t width,
                                 Double_t height, Double_t thickness,
                                 Double_t cellSizeX, Double_t cellSizeY,
                                 TGeoMedium* material, Int_t color,
                                 Double_t transparency, Int_t LayerId);
  virtual void CreateSciFiModule(const char* name,
                                 TGeoVolumeAssembly* modMotherVol,
                                 Double_t width, Double_t height,
                                 Double_t thickness, Int_t LayerId);
  void ConstructGeometry() override;
  /** Get position of single fibre in global coordinate system**/
  void GetPosition(Int_t fDetectorID, TVector3& vLeft,
                   TVector3& vRight);  // or top and bottom
  /** Transform global position to local position in plane **/
  TVector3 GetLocalPos(Int_t fDetectorID, TVector3* glob);
  /** mean position of fibre2 associated with SiPM channel **/
  void GetSiPMPosition(Int_t SiPMChan, TVector3& A, TVector3& B);
  void SiPMmapping();
  std::map<Int_t, std::map<Int_t, std::array<float, 2>>> GetSiPMmapU() {
    return fibresSiPM_U;
  }
  std::map<Int_t, std::map<Int_t, std::array<float, 2>>> GetFibresMapU() {
    return siPMFibres_U;
  }
  std::map<Int_t, std::map<Int_t, std::array<float, 2>>> GetSiPMmapV() {
    return fibresSiPM_V;
  }
  std::map<Int_t, std::map<Int_t, std::array<float, 2>>> GetFibresMapV() {
    return siPMFibres_V;
  }
  std::map<Int_t, float> GetSiPMPos_U() { return SiPMPos_U; }
  std::map<Int_t, float> GetSiPMPos_V() { return SiPMPos_V; }
  Int_t Get_NSiPMChan() const { return fNSiPMChan; }
  Float_t Get_SciFiActiveX() const { return fSciFiActiveX; }
  virtual void SiPMOverlap();
  Bool_t ProcessHits(FairVolume* vol = nullptr) override;

 private:
  Double_t fWidth;
  Double_t fHeight;
  Double_t fSciFiActiveX;
  Double_t fSciFiActiveY;
  Double_t fSciFiBendingAngle;
  Double_t fIronThick;
  Double_t fSciFiThick;
  Double_t fScintThick;
  Double_t fScintCellSize;
  Int_t fLayers;
  Double_t fZCenter;
  Double_t fFieldY;
  Double_t fZEpoxyMat;
  Double_t fiberMatThick = 0.135;  // 1.35 mm
  Double_t fFiberLength;
  Double_t fFiberPitch = 0.025;  // cm
                                 // Define sublayer thicknesses (in cm)
  // These values mimic the GEANT4 setup:
  Double_t lowerIronThick = 0.3;  // 3 mm
  Double_t airGap = 0.1;          // 1 mm
  Double_t upperIronThick = 0.3;  // 3 mm
  Double_t zLowerIronInt = -3.5 / 10;
  Double_t zFiberMat1 = -1.325 / 10;
  Double_t zAirGap = -0.15 / 10;
  Double_t zFiberMat2 = 1.025 / 10;
  Double_t zUpperIronInt = 3.2 / 10;
  Double_t fFiberRadius = 0.01125;
  Int_t numFiberLayers = 6;  // number of fiber layers in epoxy block
  Int_t fNSiPMChan;          // Number of SiPM channels
  Int_t fChannelAggregated;  // Number of SiPM channels to be aggregated
  Int_t fNSiPMs = 1;         // Default number of SiPMs
  static constexpr Int_t kMaxChannelsPerSiPM = 1000;
  // Total module thickness = 0.3 + 0.135 + 0.1 + 0.135 + 0.3 ≈ 1.0 cm
  Int_t fNMats = 1;
  std::map<Int_t, std::map<Int_t, std::array<float, 2>>>
      fibresSiPM_U;  //! mapping of fibres to SiPM channels
  std::map<Int_t, std::map<Int_t, std::array<float, 2>>>
      siPMFibres_U;  //! inverse mapping
  std::map<Int_t, std::map<Int_t, std::array<float, 2>>>
      fibresSiPM_V;  //! mapping of fibres to SiPM channels
  std::map<Int_t, std::map<Int_t, std::array<float, 2>>>
      siPMFibres_V;                             //! inverse mapping
  std::map<Int_t, float> SiPMPos_U, SiPMPos_V;  //! local SiPM channel position

  MTCDetector(const MTCDetector&) = delete;
  MTCDetector& operator=(const MTCDetector&) = delete;
};

#endif  // SND_MTC_MTCDETECTOR_H_
