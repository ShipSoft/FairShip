#ifndef vetoHitOnTrack_H
#define vetoHitOnTrack_H 1

#include "TObject.h"              //  

#include "Rtypes.h"                     // for Double_t, Int_t, Double32_t, etc
#include "TVector3.h"                   // for TVector3

#ifndef __CINT__
#include <boost/serialization/access.hpp>
#include <boost/serialization/base_object.hpp>
#endif //__CINT__

/**
 * copied from shipdata/ShipHit.h
 */
class vetoHitOnTrack : public TObject
{

  public:

    /** Default constructor **/
    vetoHitOnTrack();


    /** Constructor with hit parameters **/
    vetoHitOnTrack(Int_t hitID, Float_t dist);

    /** Destructor **/
    virtual ~vetoHitOnTrack();


    /** Accessors **/
    Double_t GetDist()          const { return fDist;      };
    Int_t    GetHitID()    const { return fHitID;  };
 
    /** Modifiers **/
    void SetDist(Float_t d) { fDist = d; }
    void SetHitID(Int_t hitID) { fHitID = hitID; }

    /*** Output to screen */
    virtual void Print(const Option_t* opt ="") const {;}

    template<class Archive>
    void serialize(Archive& ar, const unsigned int version)
    {
        ar& boost::serialization::base_object<TObject>(*this);
        ar& fHitID;
        ar& fDist;
    }

  protected:
#ifndef __CINT__ // for BOOST serialization
    friend class boost::serialization::access;
#endif // for BOOST serialization

    Float_t fDist;   ///< distance to closest veto hit 
    Int_t   fHitID;     ///< hit ID

    ClassDef(vetoHitOnTrack,1);
};

#endif
