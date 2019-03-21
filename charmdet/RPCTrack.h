#ifndef RPCTRACK_H
#define RPCTRACK_H 1

#include "TObject.h"              //  
#include "TVector3.h"

#include "Rtypes.h"                     // for Float_t, Int_t, Double32_t, etc

#ifndef __CINT__
#include <boost/serialization/access.hpp>
#include <boost/serialization/base_object.hpp>
#endif //__CINT__

//added attributes from RPC local reconstruction

class RPCTrack : public TObject
{

  public:

	/** Default constructor **/
	RPCTrack();


	/** Minimal constructor with track angles and slopes **/
	

	RPCTrack(Float_t theta, Float_t phi, Float_t slopexz, Float_t slopeyz);	

        /**  Standard constructor  **/
        RPCTrack(Float_t m, Float_t b);

        /**  Copy constructor  **/
        RPCTrack(const RPCTrack& t);

    /** Destructor **/
	virtual ~RPCTrack();


	/** Accessors **/
        float m(){return fm;}
        float b(){return fb;}
        //Track and spill information
        int GetTrackID() {return ftrackID;}
        int GetRunNumber() {return fnrun;}
        std::string GetSpillName() {return fspill;}
        int GetTrigger() {return ftrigger;}
        //general local track attributes
        float GetTheta() {return ftheta;}
        float GetPhi() {return fphi;}
        float GetSlopeXZ() {return fslopexz;}
        float GetSlopeYZ() {return fslopeyz;}
        int GetNClusters() {return fnclusters;}
        //attribute for a single cluster
        TVector3 GetClusterPos(const int icluster);
        int GetClusterDir(const int icluster){ return fcluster_dir[icluster]; }
        int GetClusterStation(const int icluster) { return fcluster_nstation[icluster];}
	/** Modifiers **/
	void AddCluster(Float_t x, Float_t y, Float_t z, Int_t dir, Int_t nstation);
        void SetTrackID(Int_t TrackID){ftrackID = TrackID;};
        void SetRunNumber(Int_t NRun) {fnrun = NRun;};
        std::string SetSpillName(std::string Spill) { fspill = Spill;};
        void SetTrigger(Int_t NTrigger) {ftrigger = NTrigger;};
	void SetTheta(Float_t theta) {ftheta = theta;};
	void SetPhi(Float_t phi) {fphi = phi;};

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
    Float_t fslopexz; 
    Float_t fslopeyz;
    /** Attributes **/
    std::string fspill;
    Int_t fnrun, ftrigger; //redundant information, probably to be removed
    Int_t ftrackID; //ID of the track
    Float_t ftheta, fphi; //angles
    Int_t fnclusters;
    //position of clusters
    std::vector<Float_t> fcluster_posx;
    std::vector<Float_t> fcluster_posy; 
    std::vector<Float_t> fcluster_posz;  
    std::vector<Int_t> fcluster_dir;	//direction of cluster (1=vertical, 0=horizontal)
    std::vector<Int_t> fcluster_nstation; //index of station the cluster belongs to
    
    ClassDef(RPCTrack,2);
};

#endif
