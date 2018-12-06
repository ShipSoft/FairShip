#ifndef RPCTRACK_H
#define RPCTRACK_H

#include "TObject.h"              //  

/**
 * class for storage of RPC Track data from July 2018 testbeam
 */
class RpcTrack : public TObject
{

  public:

	/** Default constructor **/
	RpcTrack();


	/** Minimal constructor with track angles **/
	

	RpcTrack(Double_t theta, Double_t phi);	


    /** Destructor **/
	virtual ~RpcTrack();


	/** Accessors **/
 
	/** Modifiers **/
	void AddCluster(Double_t x, Double_t y, Double_t z, Int_t dir, Int_t nstation);
	void SetTheta(Double_t theta) {ftheta = theta;};
	void SetPhi(Double_t phi) {fphi = phi;};

	/*** Output to screen */
	virtual void Print(const Option_t* opt ="") const {;}

  private:
	/** Attributes **/
	Double_t ftheta, fphi; //angles
	Int_t fnclusters;

    //position of clusters
	std::vector<Double_t> fcluster_posx;
	std::vector<Double_t> fcluster_posy; 
	std::vector<Double_t> fcluster_posz;  
    std::vector<Int_t> fcluster_dir;	//direction of cluster (1=vertical, 0=horizontal)
    std::vector<Int_t> fcluster_nstation; //index of station the cluster belongs to
    
    ClassDef(RPCTrack,1);
};

#endif


#endif