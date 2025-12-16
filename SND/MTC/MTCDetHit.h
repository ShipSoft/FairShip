// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SND_MTC_MTCDETHIT_H_
#define SND_MTC_MTCDETHIT_H_ 1

#include "MTCDetPoint.h"
#include "ShipHit.h"
#include "TObject.h"
#include "TVector3.h"

class MTCDetPoint;
class FairVolume;

class MTCDetHit : public ShipHit {
 public:
  /** Default constructor **/
  MTCDetHit();
  /** Copy constructor **/
  MTCDetHit(const MTCDetHit& hit) = default;
  MTCDetHit& operator=(const MTCDetHit& hit) = default;
  //  Constructor from MTCDetPoint
  MTCDetHit(int detID, const std::vector<MTCDetPoint*>&,
            const std::vector<Float_t>&);

  /** Destructor **/
  virtual ~MTCDetHit();

  /** Output to screen **/
  using ShipHit::Print;
  void Print();
  Float_t GetSignal() const { return signals; };
  Float_t GetTime() const { return time; };
  /*
  Example of fiberID: 123051820, where:
    - 1: MTC unique ID
    - 23: layer number
    - 0: station type (0 for +5 degrees, 1 for -5 degrees, 2 for scint plane)
    - 5: z-layer number (0-5)
    - 1820: local fibre ID within the station
  Example of SiPM global channel (what is seen in the output file): 123004123,
  where:
    - 1: MTC unique ID
    - 23: layer number
    - 0: station type (0 for +5 degrees, 1 for -5 degrees)
    - 0: mat number (only 0 by June 2025)
    - 4: SiPM number (0-N, where N is the number of SiPMs in the station)
    - 123: number of the SiPM channel (0-127, 128 channels per SiPM)
*/
  Int_t GetChannelID() const { return fDetectorID; }
  Int_t GetLayer() const {
    return static_cast<int>(fDetectorID / 1000000) % 100;
  }
  Int_t GetStationType() const {
    return static_cast<int>(fDetectorID / 100000) % 10;
  }
  Int_t GetSiPM() const { return (static_cast<int>(fDetectorID / 1000) % 10); }
  Int_t GetSiPMChan() const { return (fDetectorID % 1000); }
  Float_t GetEnergy() const;
  void setInvalid() { flag = false; }
  bool isValid() const { return flag; }
  /*
          SND@LHC comment: from Guido (22.9.2021): A threshold of 3.5pe should
     be used, which corresponds to 0.031MeV. 1 SiPM channel has 104 pixels,
     pixel can only see 0 or >0 photons.
  */
 private:
  Float_t signals = 0;
  Float_t time;
  Float_t light_attenuation(Float_t distance);
  Float_t sipm_saturation(Float_t ly);
  Float_t n_pixels_to_qdc(Float_t npix);
  Float_t flag;  ///< flag

  ClassDef(MTCDetHit, 4);
};

#endif  // SND_MTC_MTCDETHIT_H_
