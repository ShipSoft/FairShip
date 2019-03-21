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

<<<<<<< HEAD
	/** Default constructor **/
	RPCTrack();


	/** Minimal constructor with track angles **/
	

	RPCTrack(Double_t theta, Double_t phi);	

        /**  Standard constructor  **/
        RPCTrack(Float_t m, Float_t b);

        /**  Copy constructor  **/
        RPCTrack(const RPCTrack& t);

    /** Destructor **/
	virtual ~RPCTrack();


	/** Accessors **/
        float m(){return fm;}
        float b(){return fb;}
 
	/** Modifiers **/
	void AddCluster(Double_t x, Double_t y, Double_t z, Int_t dir, Int_t nstation);
	void SetTheta(Double_t theta) {ftheta = theta;};
	void SetPhi(Double_t phi) {fphi = phi;};

        /*** Output to screen */
        virtual void Print(const Option_t* opt ="") const {;}

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
    /** Attributes **/
    Double_t ftheta, fphi; //angles
    Int_t fnclusters;
    //position of clusters
    std::vector<Double_t> fcluster_posx;
    std::vector<Double_t> fcluster_posy; 
    std::vector<Double_t> fcluster_posz;  
    std::vector<Int_t> fcluster_dir;	//direction of cluster (1=vertical, 0=horizontal)
    std::vector<Int_t> fcluster_nstation; //index of station the cluster belongs to
    
    ClassDef(RPCTrack,2);
};

#endif
