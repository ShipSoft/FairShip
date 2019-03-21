#ifndef TRACKINFO_H
#define TRACKINFO_H 1

#include "TObject.h"              //  

#include "Rtypes.h"                     // for Double_t, Int_t, Double32_t, etc
#include "TVector.h"                   // for TVector
#include "Track.h"

#ifndef __CINT__
#include <boost/serialization/access.hpp>
#include <boost/serialization/base_object.hpp>
#endif //__CINT__

class TrackInfo : public TObject
{

  public:

    /** Default constructor **/
    TrackInfo();
    /**  Standard constructor  **/
    TrackInfo(const genfit::Track* tr);

    /**  Copy constructor  **/
    TrackInfo(const TrackInfo& ti);

    /** Destructor **/
    virtual ~TrackInfo();

    /** Accessors **/
    unsigned int N(){return fDetIDs.size();}
    unsigned int detId(Int_t n){return fDetIDs[n];}
    float wL(Int_t n){return fWL[n];}
    float wR(Int_t n){return fWR[n];}

    /*** Output to screen */
    virtual void Print(const Option_t* opt ="") const {;}

    template<class Archive>
    void serialize(Archive& ar, const unsigned int version)
    {
        ar& boost::serialization::base_object<TObject>(*this);
        ar& fDetIDs;
        ar& fWL;
        ar& fWR;
    }

  protected:
#ifndef __CINT__ // for BOOST serialization
    friend class boost::serialization::access;
#endif // for BOOST serialization

    std::vector<unsigned int> fDetIDs;   ///< array of measurements
    std::vector<float> fWL;
    std::vector<float> fWR;
    ClassDef(TrackInfo,1);
};

#endif
