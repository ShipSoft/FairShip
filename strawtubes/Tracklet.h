#ifndef Tracklet_H
#define Tracklet_H 1

#include "TObject.h"
#include "TClonesArray.h"

#include <stddef.h>
#include "Rtypes.h"                     // for Double_t, Int_t, Double32_t, etc

#ifndef __CINT__
#include <boost/serialization/access.hpp>
#include <boost/serialization/base_object.hpp>
#endif //__CINT__
/**
 *@author Thomas Ruf
 **
 ** Simple class to describe a tracklet
 ** list of indices pointing to strawtubesHit objects in the digiStraw container

 **/

class Tracklet: public TObject
{
  public:
    /** Default constructor **/
    Tracklet();
    /** Constructor with arguments **/
    Tracklet(Int_t f, std::vector<unsigned int>  aT);
 
/** Destructor **/
    virtual ~Tracklet();

    std::vector<unsigned int>* getList(){return &aTracklet;}
    Int_t getType(){return flag;}    
    void setType(Int_t f){flag=f;}
    Int_t link2MCTrack(TClonesArray* strawPoints, Float_t min);   // give back MCTrack ID with max matched strawtubesHits 
    /*** Output to screen */
    virtual void Print(const Option_t* opt ="") const {;}

    template<class Archive>
    void serialize(Archive& ar, const unsigned int version)
    {
        ar& boost::serialization::base_object<TObject>(*this);
        ar& flag;
        ar& aTracklet;
    }
  protected:
#ifndef __CINT__ // for BOOST serialization
    friend class boost::serialization::access;
#endif // for BOOST serialization

    std::vector<unsigned int>  aTracklet;         ///< list of indices
    Int_t flag; // reserved for type of tracklet  ///< type of tracklet
    ClassDef(Tracklet,1);

};

#endif
