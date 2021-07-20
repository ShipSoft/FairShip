#ifndef HIT2MCPOINTS_H
#define HIT2MCPOINTS_H 1

#include "TObject.h"              //  
#include "Rtypes.h"                     // for Double_t, Int_t, Double32_t, etc
#include <unordered_map>

#ifndef __CINT__
#include <boost/serialization/access.hpp>
#include <boost/serialization/base_object.hpp>
#endif //__CINT__

class Hit2MCPoints : public TObject
{

  public:

    /** Default constructor **/
    Hit2MCPoints();

    /**  Copy constructor  **/
    Hit2MCPoints(const Hit2MCPoints& ti);

    void Add(int detID,int key, float w);

    /** Destructor **/
    virtual ~Hit2MCPoints();

    /** Accessors **/
    unsigned int N(int detID){return linksToMCPoints[detID].size();}
    std::unordered_map<int,float> wList(int detID){return linksToMCPoints[detID];}

    /*** Output to screen */
    virtual void Print(const Option_t* opt ="") const {;}

    template<class Archive>
    void serialize(Archive& ar, const unsigned int version)
    {
        ar& boost::serialization::base_object<TObject>(*this);
        ar& linksToMCPoints;
    }

  protected:
#ifndef __CINT__ // for BOOST serialization
    friend class boost::serialization::access;
#endif // for BOOST serialization
    std::unordered_map<int,std::unordered_map<int,float>>  linksToMCPoints;  ///< array of detector elements with list of contributing MCPoints
    ClassDef(Hit2MCPoints,1);
};

#endif
