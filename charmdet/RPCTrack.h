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
	void AddTrack(Double_t x, Double_t y, Double_t z);
	void SetTheta(Double_t theta) {ftheta = theta;};
	void SetPhi(Double_t phi) {fphi = phi;};
	void SetNclusters(Int_t fnclusters) {fnclusters = SetNclusters;};

	/*** Output to screen */
	virtual void Print(const Option_t* opt ="") const {;}

  private:
	/** Attributes **/
	Double_t ftheta, fphi; //angles
	Int_t fnclusters;

	std::vector<Double_t> fcluster_posx;
	std::vector<Double_t> fcluster_posy; 
	std::vector<Double_t> fcluster_posz;  

    ClassDef(RPCTrack,1);
};

#endif


#endif