#ifndef SNDLHCHIT_H
#define SNDLHCHIT_H 1

#include "TObject.h"              //  

#include "Rtypes.h"                     // for Double_t, Int_t, Double32_t, etc
#include "TVector3.h"
#include "TArrayF.h"
#include <unordered_map>

#ifndef __CINT__
#include <boost/serialization/access.hpp>
#include <boost/serialization/base_object.hpp>
#endif //__CINT__

/**
 * copied from FairRoot FairHit and simplified
 */
class SndlhcHit : public TObject
{

  public:

    /** Default constructor **/
    SndlhcHit();


    /** Constructor with detector id, number of SiPMs per side, number of sides **/
    SndlhcHit(Int_t detID);

    /** Destructor **/
    virtual ~SndlhcHit();


    /** Accessors **/
    Int_t    GetDetectorID()    const { return fDetectorID;  };
    Float_t GetSignal(Int_t nChannel);
    Float_t GetTime(Int_t nChannel);
    Int_t GetnSiPMs() const { return nSiPMs;  };
    Int_t GetnSides() const { return nSides;  };
    /** Modifiers **/
    void SetDigi(Int_t i, Float_t s, Float_t t) { signals[i]=s;times[i]=t; }
    void SetDetectorID(Int_t detID) { fDetectorID = detID; }

// to be implemented by the subdetector

    /*** Output to screen */
    virtual void Print(const Option_t* opt ="") const {;}
    /*** Get position */
    virtual void GetPosition(TVector3 L,TVector3 R) const {;}
    /*** Get energy */
    // virtual Float_t GetEnergy();  // causes problems, don't know why: cling::DynamicLibraryManager::loadLibrary(): lib/libShipData.so.0.0.0: undefined symbol: _ZN9SndlhcHit9GetEnergyEv

    template<class Archive>
    void serialize(Archive& ar, const unsigned int version)
    {
        ar& boost::serialization::base_object<TObject>(*this);
        ar& fDetectorID;
        ar& nSiPMs;
        ar& nSides;
    }

  protected:
#ifndef __CINT__ // for BOOST serialization
    friend class boost::serialization::access;
#endif // for BOOST serialization
    Int_t   fDetectorID;     ///< Detector unique identifier
    Int_t   nSiPMs;   /// number of SiPMs per side
    Int_t   nSides;   /// number of sides
    Float_t signals[16];  /// SiPM signal
    Float_t times[16];     /// SiPM time
    ClassDef(SndlhcHit,1);
};

#endif
