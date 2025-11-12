#ifndef SPLITCAL_SPLITCALPOINT_H_
#define SPLITCAL_SPLITCALPOINT_H_


#include "FairMCPoint.h"

#include "TObject.h"
#include "TVector3.h"

class splitcalPoint : public FairMCPoint
{

  public:

    /** Default constructor **/
    splitcalPoint();


    /** Constructor with arguments
     *@param trackID  Index of MCTrack
     *@param detID    Detector ID
     *@param pos      Ccoordinates at entrance to active volume [cm]
     *@param mom      Momentum of track at entrance [GeV]
     *@param tof      Time since event start [ns]
     *@param length   Track length since creation [cm]
     *@param eLoss    Energy deposit [GeV]
     **/
    splitcalPoint(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom,
                     Double_t tof, Double_t length, Double_t eLoss, Int_t pdgCode);



    /** Destructor **/
    virtual ~splitcalPoint();

    /** Copy constructor **/
    splitcalPoint(const splitcalPoint& point) = default;
    splitcalPoint& operator=(const splitcalPoint& point) = default;

    /** Output to screen **/
    /* virtual void Print(const Option_t* opt) const; */
    virtual void Print() const;
    Int_t PdgCode() const {return fPdgCode;}

  private:
    Int_t fPdgCode;

    ClassDef(splitcalPoint, 3)
};

#endif  // SPLITCAL_SPLITCALPOINT_H_
