#ifndef STRAWTUBESPOINT_H
#define STRAWTUBESPOINT_H 1


#include "FairMCPoint.h"

#include "TObject.h"
#include "TVector3.h"

class strawtubesPoint : public FairMCPoint
{
  public:

    /** Default constructor **/
    strawtubesPoint();

    /** Constructor with arguments
     *@param trackID  Index of MCTrack
     *@param detID    Detector ID
     *@param pos      Ccoordinates at entrance to active volume [cm]
     *@param mom      Momentum of track at entrance [GeV]
     *@param tof      Time since event start [ns]
     *@param length   Track length since creation [cm]
     *@param eLoss    Energy deposit [GeV]
     **/
    strawtubesPoint(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom,
                     Double_t tof, Double_t length, Double_t eLoss, Int_t pdgcode,Double_t dist);

    /** Destructor **/
    virtual ~strawtubesPoint();

    /** Output to screen **/
    virtual void Print() const;
    Int_t PdgCode() const {return fPdgCode;}
    Double_t dist2Wire() const {return fdist2Wire;}

  private:
    /** Copy constructor **/
    strawtubesPoint(const strawtubesPoint& point);
    strawtubesPoint operator=(const strawtubesPoint& point);

    Int_t fPdgCode;
    Double_t fdist2Wire;
    ClassDef(strawtubesPoint,2);
    

};

#endif
