#ifndef SHIPHIT_H
#define SHIPHIT_H 1

#include "TObject.h"              //  

#include "Rtypes.h"                     // for Double_t, Int_t, Double32_t, etc
#include "TVector3.h"                   // for TVector3

#ifndef __CINT__
#include <boost/serialization/access.hpp>
#include <boost/serialization/base_object.hpp>
#endif //__CINT__

/**
 * copied from FairRoot FairHit and simplified
 */
class ShipHit : public TObject
{

  public:

    /** Default constructor **/
    ShipHit();


    /** Constructor with hit parameters **/
    ShipHit(Int_t detID, Float_t digi);

    /** Destructor **/
    virtual ~ShipHit();


    /** Accessors **/
    Double_t GetDigi()          const { return fdigi;      };
    Int_t    GetDetectorID()    const { return fDetectorID;  };
 
    /** Modifiers **/
    void SetDigi(Float_t d) { fdigi = d; }
    void SetDetectorID(Int_t detID) { fDetectorID = detID; }

    /*** Output to screen */
    virtual void Print(const Option_t* opt ="") const {;}

    template<class Archive>
    void serialize(Archive& ar, const unsigned int version)
    {
        ar& boost::serialization::base_object<TObject>(*this);
        ar& fDetectorID;
        ar& fdigi;
    }

  protected:
#ifndef __CINT__ // for BOOST serialization
    friend class boost::serialization::access;
#endif // for BOOST serialization

    Float_t fdigi;   ///< digitized detector hit
    Int_t   fDetectorID;     ///< Detector unique identifier

    ClassDef(ShipHit,1);
};

#endif
