#ifndef PRESTRAWDETECTORPOINT_H
#define PRESTRAWDETECTORPOINT_H 1

#include "FairMCPoint.h"
#include "TObject.h"
#include "TVector3.h"

class prestrawdetectorPoint : public FairMCPoint
{
  public:
    /** Default constructor **/
    prestrawdetectorPoint();

    /** Constructor with arguments
     *@param trackID  Index of MCTrack
     *@param detID    Detector ID
     *@param pos      Ccoordinates at entrance to active volume [cm]
     *@param mom      Momentum of track at entrance [GeV]
     *@param tof      Time since event start [ns]
     *@param length   Track length since creation [cm]
     *@param eLoss    Energy deposit [GeV]
     **/
    prestrawdetectorPoint(Int_t trackID,
                          Int_t detID,
                          TVector3 pos,
                          TVector3 mom,
                          Double_t tof,
                          Double_t length,
                          Double_t eLoss,
                          Int_t pdgcode);

    /** Destructor **/
    virtual ~prestrawdetectorPoint();

    /** Output to screen **/
    virtual void Print() const;
    Int_t PdgCode() const { return fPdgCode; }

  private:
    /** Copy constructor **/
    prestrawdetectorPoint(const prestrawdetectorPoint& point);
    prestrawdetectorPoint operator=(const prestrawdetectorPoint& point);

    Int_t fPdgCode;
    ClassDef(prestrawdetectorPoint, 2);
};

#endif
