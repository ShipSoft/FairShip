#ifndef SND_MTC_MTCDETPOINT_H_
#define SND_MTC_MTCDETPOINT_H_ 1

#include "FairMCPoint.h"
#include "TObject.h"
#include "TVector3.h"

class MtcDetPoint : public FairMCPoint
{

  public:
    /** Default constructor **/
    MtcDetPoint();

    /** Constructor with arguments
     *@param trackID  Index of MCTrack
     *@param detID    Detector ID
     *@param pos      Ccoordinates at entrance to active volume [cm]
     *@param mom      Momentum of track at entrance [GeV]
     *@param tof      Time since event start [ns]
     *@param length   Track length since creation [cm]
     *@param eLoss    Energy deposit [GeV]
     **/

    MtcDetPoint(Int_t trackID,
                Int_t detID,
                TVector3 pos,
                TVector3 mom,
                Double_t tof,
                Double_t length,
                Double_t eLoss,
                Int_t pdgcode);

    /** Destructor **/
    virtual ~MtcDetPoint();

    /** Output to screen **/
    virtual void Print() const;
    Int_t PdgCode() const { return fPdgCode; }
    Int_t GetStationType() const { return static_cast<int>(fDetectorID / 100000) % 10; }
    Int_t GetLayer();
    Int_t GetLayerType();
    Int_t fPdgCode;

    MtcDetPoint(const MtcDetPoint& point);
    MtcDetPoint operator=(const MtcDetPoint& point);

    ClassDef(MtcDetPoint, 2)
};

#endif   // SND_MTC_MTCDETPOINT_H_
