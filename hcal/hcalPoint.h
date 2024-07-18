#ifndef HCALPOINT_H
#define HCALPOINT_H 1


#include "FairMCPoint.h"

#include "TObject.h"
#include "TVector3.h"

#include "TClonesArray.h"

class hcalPoint : public FairMCPoint
{
  friend class hcal;

  public:

    /** Default constructor **/
    hcalPoint();


    /** Constructor with arguments
     *@param trackID  Index of MCTrack
     *@param detID    Detector ID
     *@param pos      Ccoordinates at entrance to active volume [cm]
     *@param mom      Momentum of track at entrance [GeV]
     *@param tof      Time since event start [ns]
     *@param length   Track length since creation [cm]
     *@param eLoss    Energy deposit [GeV]
     **/
    hcalPoint(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom,
                     Double_t tof, Double_t length, Double_t eLoss, Int_t pdgcode=0);

    /** Constructor with arguments for lite points
     *@param trackID  Index of MCTrack
     *@param detID    Detector ID
     *@param tof      Time since event start [ns]
     *@param eLoss    Energy deposit [GeV]
     **/
    hcalPoint(Int_t trackID, Int_t detID, Double32_t tof, Double32_t eloss, UInt_t EventId=0)
	: FairMCPoint(trackID, detID, TVector3(-1111, -1111, -1111), TVector3(-1111, -1111, -1111), tof, -1111, eloss, EventId), fPdgCode(0)
      {};

    Int_t GetPdgCode() const {return fPdgCode;}
    Int_t PdgCode() const {return fPdgCode;}

    /** Destructor **/
    virtual ~hcalPoint();

    /** Output to screen **/
    virtual void Print(const Option_t* opt) const;

  private:
    /** Copy constructor **/
    hcalPoint(const hcalPoint& point);
    hcalPoint operator=(const hcalPoint& point);

    Int_t fPdgCode;

    ClassDef(hcalPoint,1)

};

#endif
