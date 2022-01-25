#ifndef MUFILTERHIT_H
#define MUFILTERHIT_H 1

#include "SndlhcHit.h"
#include "MuFilterPoint.h"
#include "TObject.h"
#include "TVector3.h"
#include <map>

class MuFilterHit : public SndlhcHit
{
  public:

    /** Default constructor **/
    MuFilterHit();
    MuFilterHit(Int_t detID);
    /** Constructor with detector id, number of SiPMs per side, number of sides **/
    MuFilterHit(Int_t detID,Int_t nP,Int_t nS);

    // Constructor from MuFilterPoint
    MuFilterHit(Int_t detID,std::vector<MuFilterPoint*>);

 /** Destructor **/
    virtual ~MuFilterHit();

    /** Output to screen **/
    void Print() const;
    Float_t GetEnergy();
    Float_t SumOfSignals(char* opt,Bool_t mask=kTRUE);
    std::map<TString,Float_t> SumOfSignals(Bool_t mask=kTRUE);
    std::map<Int_t,Float_t> GetAllSignals(Bool_t mask=kTRUE);
    std::map<Int_t,Float_t> GetAllTimes(Bool_t mask=kTRUE);
    Float_t  GetDeltaT(Bool_t mask=kTRUE);
    Float_t  GetFastDeltaT(Bool_t mask=kTRUE);
    Float_t  GetImpactT(Bool_t mask=kTRUE);
    bool isValid() const {return flag;}
    bool isMasked(Int_t i) const {return fMasked[i];}
    void SetMasked(Int_t i) {fMasked[i]=kTRUE;}
    int GetSystem(){return floor(fDetectorID/10000);}
    bool isVertical();
    bool isShort(Int_t);
  private:
    /** Copy constructor **/
    MuFilterHit(const MuFilterHit& hit);
    MuFilterHit operator=(const MuFilterHit& hit);

    Float_t flag;   ///< flag
    Float_t fMasked[16];  /// masked signal

    ClassDef(MuFilterHit,4);
    

};

#endif
