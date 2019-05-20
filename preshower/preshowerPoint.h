#ifndef PRESHOWERPOINT_H
#define PRESHOWERPOINT_H 1


#include "FairMCPoint.h"

#include "TObject.h"
#include "TVector3.h"

class preshowerPoint : public FairMCPoint
{

  public:

    /** Default constructor **/
    preshowerPoint();


    /** Constructor with arguments
     *@param trackID  Index of MCTrack
     *@param detID    Detector ID
     *@param pos      Ccoordinates at entrance to active volume [cm]
     *@param mom      Momentum of track at entrance [GeV]
     *@param tof      Time since event start [ns]
     *@param length   Track length since creation [cm]
     *@param eLoss    Energy deposit [GeV]
     **/
    preshowerPoint(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom,
                     Double_t tof, Double_t length, Double_t eLoss, Int_t pdgCode);



    /** Destructor **/
    virtual ~preshowerPoint();

    /** Output to screen **/
    virtual void Print(const Option_t* opt) const;
    Int_t PdgCode() const {return fPdgCode;}

  private:
    /** Copy constructor **/
    Int_t fPdgCode;
    preshowerPoint(const preshowerPoint& point);
    preshowerPoint operator=(const preshowerPoint& point);

    ClassDef(preshowerPoint,2)

};

#endif
