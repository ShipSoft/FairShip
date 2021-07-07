#ifndef SNDLHCHIT_H
#define SNDLHCHIT_H 1

#include "TObject.h"              //  

#include "Rtypes.h"                     // for Double_t, Int_t, Double32_t, etc
#include "TVector3.h"                
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


    /** Constructor with hit parameters **/
    SndlhcHit(Int_t detID, Float_t digiLowLeft,Float_t digiLowRight,Float_t digiHighLeft,Float_t digiHighRight);

    /** Destructor **/
    virtual ~SndlhcHit();


    /** Accessors **/
    std::unordered_map<std::string, float> GetDigis();
    Int_t    GetDetectorID()    const { return fDetectorID;  };
 
    /** Modifiers **/
    void SetDigi(Float_t dLL,Float_t dLR,Float_t dHL,Float_t dHR) { fdigiLowLeft=dLL;fdigiLowRight=dLR;fdigiHighLeft=dHL;fdigiHighRight=dHR; }
    void SetDetectorID(Int_t detID) { fDetectorID = detID; }

// to be implemented by the subdetector

    /*** Output to screen */
    virtual void Print(const Option_t* opt ="") const {;}
    /*** Get position */
    virtual void GetPosition(TVector3 L,TVector3 R) const {;}
    /*** Get energy */
    virtual Float_t GetEnergy() const;

    template<class Archive>
    void serialize(Archive& ar, const unsigned int version)
    {
        ar& boost::serialization::base_object<TObject>(*this);
        ar& fDetectorID;
        ar& fdigiLowLeft;
        ar& fdigiHighLeft;
        ar& fdigiLowRight;
        ar& fdigiHighRight;
    }

  protected:
#ifndef __CINT__ // for BOOST serialization
    friend class boost::serialization::access;
#endif // for BOOST serialization

    Float_t fdigiLowLeft;       ///< digitized detector hit, SiPM low dynamic range, left or top.
    Float_t fdigiLowRight;    ///< digitized detector hit, SiPM low dynamic range, right or bottom.
    Float_t fdigiHighLeft;      ///< digitized detector hit, SiPM high dynamic range, left or top.
    Float_t fdigiHighRight;   ///< digitized detector hit, SiPM high dynamic range, right or bottom.
    Int_t   fDetectorID;     ///< Detector unique identifier

    ClassDef(SndlhcHit,1);
};

#endif
