#ifndef VETOPOINT_H
#define VETOPOINT_H 1


#include "FairMCPoint.h"

#include "TObject.h"
#include "TVector3.h"

class vetoPoint : public FairMCPoint
{

  public:

    /** Default constructor **/
    vetoPoint();


    /** Constructor with arguments
     *@param trackID  Index of MCTrack
     *@param detID    Detector ID
     *@param pos      Ccoordinates at entrance to active volume [cm]
     *@param mom      Momentum of track at entrance [GeV]
     *@param tof      Time since event start [ns]
     *@param length   Track length since creation [cm]
     *@param eLoss    Energy deposit [GeV]
     **/
    vetoPoint(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom,
                     Double_t tof, Double_t length, Double_t eLoss);




    /** Destructor **/
    virtual ~vetoPoint();

    /** Output to screen **/
    virtual void Print() const;

  private:
    /** Copy constructor **/
    vetoPoint(const vetoPoint& point);
    vetoPoint operator=(const vetoPoint& point);

    ClassDef(vetoPoint,1)

};

#endif
