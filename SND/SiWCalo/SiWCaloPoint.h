#ifndef SND_SIWCALO_SIWCALOPOINT_H_
#define SND_SIWCALO_SIWCALOPOINT_H_ 1

#include "FairMCPoint.h"
#include "TObject.h"
#include "TVector3.h"

class SiWCaloPoint : public FairMCPoint
{

  public:
    /** Default constructor **/
    SiWCaloPoint();

    /** Constructor with arguments
     *@param trackID  Index of MCTrack
     *@param detID    Detector ID
     *@param pos      Ccoordinates at entrance to active volume [cm]
     *@param mom      Momentum of track at entrance [GeV]
     *@param tof      Time since event start [ns]
     *@param length   Track length since creation [cm]
     *@param eLoss    Energy deposit [GeV]
     *@param pdgcode  PDG code of MCTrack
     **/

    SiWCaloPoint(Int_t trackID,
                       Int_t detID,
                       TVector3 pos,
                       TVector3 mom,
                       Double_t tof,
                       Double_t length,
                       Double_t eLoss,
                       Int_t pdgcode);

    /** Destructor **/
    virtual ~SiWCaloPoint();

    /** Output to screen **/
    virtual void Print() const;
    Int_t PdgCode() const { return fPdgCode; }

    int constexpr GetLayer() { return fDetectorID >> 17;}
    int constexpr GetColumn() { return (fDetectorID >> 14) & 0x3;}
    int constexpr GetRow() { return (fDetectorID >> 13) & 0x1;}
    int constexpr GetPixelX() { return fDetectorID & 0x1F;} // 0-31
    int constexpr GetPixelY() { return (fDetectorID >> 5) & 0x1F;} // 0-31
    // Helpers
    int constexpr GetPixelID() { return GetPixelX() + 32 * GetPixelY();} // 0-1023
  
  private:
    Int_t fPdgCode;

    SiWCaloPoint(const SiWCaloPoint& point);
    SiWCaloPoint operator=(const SiWCaloPoint& point);

    ClassDef(SiWCaloPoint, 1)
};

#endif   // SND_SIWCALO_SIWCALOPOINT_H_
