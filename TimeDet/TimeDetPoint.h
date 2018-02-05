#ifndef TIMEDETPOINT_H
#define TIMEDETPOINT_H 1


#include "FairMCPoint.h"

#include "TObject.h"
#include "TVector3.h"


class TimeDetPoint : public FairMCPoint
{

  public:

    /** Default constructor **/
    TimeDetPoint();


    /** Constructor with arguments
     *@param trackID  Index of MCTrack
     *@param detID    Detector ID
                      // for LiSc: segment T1 (seg=1), segment T2 (seg=2), normal detector (c=0) and corner detector (c=1), sequential number
                      //  nr + 100000*seg + 10000*c;
     *@param pos      Ccoordinates at entrance to active volume [cm]
     *@param mom      Momentum of track at entrance [GeV]
     *@param tof      Time since event start [ns]
     *@param length   Track length since creation [cm]
     *@param eLoss    Energy deposit [GeV]
     **/
    TimeDetPoint(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom,
                     Double_t tof, Double_t length, Double_t eLoss, Int_t pdgCode, TVector3 Lpos, TVector3 Lmom);

    /** Destructor **/
    virtual ~TimeDetPoint();

    /** Output to screen **/
    virtual void Print() const;
    Int_t PdgCode() const {return fPdgCode;}
    TVector3 LastPoint() const {return fLpos;}
    TVector3 LastMom() const {return fLmom;}

  private:
    /** Copy constructor **/
    Int_t fPdgCode;
    TVector3 fLpos,fLmom;
    TimeDetPoint(const TimeDetPoint& point);
    TimeDetPoint operator=(const TimeDetPoint& point);

    ClassDef(TimeDetPoint,1)

};

#endif
