#ifndef SNDCLUSTER_H
#define SNDCLUSTER_H 1

#include "TObject.h"              //  
#include <stdlib.h>

#include "Rtypes.h"                     // for Double_t, Int_t, Double32_t, etc
#include "TVector3.h"
#include "TArrayF.h"
#include "sndScifiHit.h"
#include "MuFilterHit.h"
#include "Scifi.h"
#include "MuFilter.h"

#ifndef __CINT__
#include <boost/serialization/access.hpp>
#include <boost/serialization/base_object.hpp>
#endif //__CINT__

/**
 * class for scifi and muFilter clusters made of Hit objects
 */
class sndCluster : public TObject
{

  public:

    /** Default constructor **/
    sndCluster();


    /** Constructor with list of hits**/
    sndCluster(Int_t first, Int_t N,std::vector<sndScifiHit*> hitlist,Scifi* ScifiDet,Bool_t withQDC=kTRUE);
    sndCluster(Int_t first, Int_t N,std::vector<MuFilterHit*> hitlist,MuFilter* MuDet);

    /** Destructor **/
    virtual ~sndCluster();

    /** Accessors **/
    Int_t    GetType()   const { return fType;  };
    Int_t    GetFirst()    const { return fFirst;  };
    Int_t    GetN()    const { return fN;  };
    /*** Get total energy */
    Double_t GetEnergy()    const { return fEnergy;  };
    /*** Get time in ns, use fastest TDC of cluster*/
    Double_t GetTime()    const { return fTime;  };
    /*** Get position */
    virtual void GetPosition(TVector3& L,TVector3& R) {
	L.SetXYZ(fMeanPositionA[0],fMeanPositionA[1],fMeanPositionA[2]);
	R.SetXYZ(fMeanPositionB[0],fMeanPositionB[1],fMeanPositionB[2]);
	}

    /*** Output to screen */
    void Print() const;

    template<class Archive>
    void serialize(Archive& ar, const unsigned int version)
    {
        ar& boost::serialization::base_object<TObject>(*this);
        ar& fFirst;
        ar& fN;
        ar& fEnergy;
        ar& fMeanPositionA;
        ar& fMeanPositionB;
    }

  protected:
#ifndef __CINT__ // for BOOST serialization
    friend class boost::serialization::access;
#endif // for BOOST serialization
    Int_t   fType;     /// Scifi or MuFilter
    Int_t   fFirst;     /// first hit channel ID of cluster
    Int_t   fN;   /// number of hits
    TVector3   fMeanPositionA;   /// mean position 
    TVector3   fMeanPositionB;   /// mean position 
    Double_t fEnergy;  /// total energy
    Double_t fTime;  /// Time from fastest hit TDC
    ClassDef(sndCluster,2);
};

#endif
