#ifndef RPCTRACK_H
#define RPCTRACK_H 1

#include "TObject.h"              //  

#include "Rtypes.h"                     // for Double_t, Int_t, Double32_t, etc

#ifndef __CINT__
#include <boost/serialization/access.hpp>
#include <boost/serialization/base_object.hpp>
#endif //__CINT__

class RPCTrack : public TObject
{

  public:

    /** Default constructor **/
    RPCTrack();
    /**  Standard constructor  **/
    RPCTrack(Float_t m, Float_t b);

    /**  Copy constructor  **/
    RPCTrack(const RPCTrack& t);

    /** Destructor **/
    virtual ~RPCTrack();

    /** Accessors **/
    float m(){return fm;}
    float b(){return fb;}

    /*** Output to screen */
    virtual void Print(const Option_t* opt ="") const {;}

    template<class Archive>
    void serialize(Archive& ar, const unsigned int version)
    {
        ar& boost::serialization::base_object<TObject>(*this);
        ar& fm;
        ar& fb;
    }

  protected:
#ifndef __CINT__ // for BOOST serialization
    friend class boost::serialization::access;
#endif // for BOOST serialization
    Float_t fm;
    Float_t fb;
   ClassDef(RPCTrack, 1)
};

#endif
