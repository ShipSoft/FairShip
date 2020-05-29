#ifndef UPSTREAMTAGGERPOINT_H
#define UPSTREAMTAGGERPOINT_H 1


#include "FairMCPoint.h"
#include "UpstreamTaggerHit.h"
#include "UpstreamTagger.h"
#include "TObject.h"
#include "TVector3.h"


class UpstreamTaggerPoint : public FairMCPoint
{

  public:

    /** Default constructor **/
    UpstreamTaggerPoint();


    /** Constructor with arguments
     *@param trackID  Index of MCTrack
     *@param detID    Detector ID
     *@param pos      Ccoordinates at entrance to active volume [cm]
     *@param mom      Momentum of track at entrance [GeV]
     *@param tof      Time since event start [ns]
     *@param length   Track length since creation [cm]
     *@param eLoss    Energy deposit [GeV]
    **/
    UpstreamTaggerPoint(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom,
                     Double_t tof, Double_t length, Double_t eLoss, Int_t pdgCode, TVector3 Lpos, TVector3 Lmom);

    /** Destructor **/
    virtual ~UpstreamTaggerPoint();

    /** Output to screen **/
    virtual void Print() const;
    Int_t PdgCode() const {return fPdgCode;}
    TVector3 LastPoint() const {return fLpos;}
    TVector3 LastMom() const {return fLmom;}

  private:
    /** Copy constructor **/
    Int_t fPdgCode;
    TVector3 fLpos,fLmom;
    UpstreamTaggerPoint(const UpstreamTaggerPoint& point);
    UpstreamTaggerPoint operator=(const UpstreamTaggerPoint& point);

    ClassDef(UpstreamTaggerPoint,1)

};

#endif
