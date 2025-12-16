// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SND_EMULSIONTARGET_TTPOINT_H_
#define SND_EMULSIONTARGET_TTPOINT_H_

#include "FairMCPoint.h"
#include "TObject.h"
#include "TVector3.h"

class TTPoint : public FairMCPoint {
 public:
  /** Default constructor **/
  TTPoint();

  /** Constructor with arguments
   *@param trackID  Index of MCTrack
   *@param detID    Detector ID
   *@param pos      Ccoordinates at entrance to active volume [cm]
   *@param mom      Momentum of track at entrance [GeV]
   *@param tof      Time since event start [ns]
   *@param length   Track length since creation [cm]
   *@param eLoss    Energy deposit [GeV]
   **/

  /*TargetPoint(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom,
                   Double_t tof, Double_t length, Double_t eLoss, Int_t pdgCode,
              Bool_t emTop, Bool_t emBot,Bool_t emCESTop, Bool_t emCESBot,
     Bool_t tt, Int_t nPlate, Int_t nColumn, Int_t nRow, Int_t nWall);*/

  TTPoint(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom, Double_t tof,
          Double_t length, Double_t eLoss, Int_t pdgCode);

  /** Destructor **/
  virtual ~TTPoint();

  /** Copy constructor **/
  TTPoint(const TTPoint& point) = default;
  TTPoint& operator=(const TTPoint& point) = default;

  /** Output to screen **/
  virtual void Print(const Option_t* opt) const;

  Int_t PdgCode() const { return fPdgCode; }

 private:
  Int_t fPdgCode;

  ClassDef(TTPoint, 3)
};

#endif  // SND_EMULSIONTARGET_TTPOINT_H_
