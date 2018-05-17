#ifndef SPLITCALPOINT_H
#define SPLITCALPOINT_H 1


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

    /** Output to screen **/
    /* virtual void Print(const Option_t* opt) const; */
    virtual void Print() const;
    Int_t PdgCode() const {return fPdgCode;}

  private:
    /** Copy constructor **/
    Int_t fPdgCode;
    splitcalPoint(const splitcalPoint& point);
    splitcalPoint operator=(const splitcalPoint& point);

    ClassDef(splitcalPoint,2)

};

#endif
