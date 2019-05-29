#ifndef SCIFIPOINT_H
#define SCIFIPOINT_H 1


#include "FairMCPoint.h"

#include "TObject.h"
#include "TVector3.h"

class SciFiPoint : public FairMCPoint
{

  public:

    /** Default constructor **/
    SciFiPoint();


    /** Constructor with arguments
     *@param trackID  Index of MCTrack
     *@param detID    Detector ID
     *@param pos      Ccoordinates at entrance to active volume [cm]
     *@param mom      Momentum of track at entrance [GeV]
     *@param tof      Time since event start [ns]
     *@param length   Track length since creation [cm]
     *@param eLoss    Energy deposit [GeV]
     **/


    SciFiPoint(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom,
		Double_t tof, Double_t length, Double_t eLoss, Int_t pdgCode);

    /** Destructor **/
    virtual ~SciFiPoint();

    /** Output to screen **/
    virtual void Print(const Option_t* opt) const;
    Int_t PdgCode() const {return fPdgCode;}

  private:

    Int_t fPdgCode;

    /** Copy constructor **/

    SciFiPoint(const SciFiPoint& point);
    SciFiPoint operator=(const SciFiPoint& point);

    ClassDef(SciFiPoint,1)

};

#endif
