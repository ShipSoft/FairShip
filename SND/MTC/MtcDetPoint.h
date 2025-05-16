#ifndef MTCDET_MtcDetPoint_H_
#define MTCDET_MtcDetPoint_H_ 1

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
    virtual void Print(const Option_t* opt) const;
    Int_t PdgCode() const { return fPdgCode; }

    Int_t GetLayer();

    Int_t GetLayerType();
    /** Copy constructor **/
    Int_t fPdgCode;

    MtcDetPoint(const MtcDetPoint& point);
    MtcDetPoint operator=(const MtcDetPoint& point);

    ClassDef(MtcDetPoint, 1)
};

#endif   // MTCDET_MtcDetPoint_H_
