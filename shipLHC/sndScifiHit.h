#ifndef SNDSCIFIHIT_H
#define SNDSCIFIHIT_H 1

#include "SndlhcHit.h"
#include "ScifiPoint.h"
#include "TObject.h"
#include "TVector3.h"

class sndScifiHit : public SndlhcHit
{
  public:

    /** Default constructor **/
    sndScifiHit();
    sndScifiHit(Int_t detID);
    // Constructor from MuFilterPoint
    sndScifiHit(int detID,std::vector<ScifiPoint*>,std::vector<Float_t>);

 /** Destructor **/
    virtual ~sndScifiHit();

    /** Output to screen **/
	void Print() ;
	Float_t GetEnergy();

	void setInvalid() {flag = false;}
	bool isValid() const {return flag;}
	Int_t GetStation(){return int(fDetectorID/10000000);}
	bool isVertical(){
		if ( int(fDetectorID/100000)%10 == 1){return true;}
		else{return (false);}
	}
	Int_t  GetMat(){return ( int(fDetectorID/100000)%10);}
	Int_t  GetSiPM(){return ( int(fDetectorID/10000)%10);}
	Int_t GetSiPMChan(){return ( fDetectorID%1000);}
	Int_t GetChannelID(){return fDetectorID;}

  private:
    /** Copy constructor **/
    sndScifiHit(const sndScifiHit& hit);
    sndScifiHit operator=(const sndScifiHit& hit);
    Float_t ly_loss_mean(Float_t distance, Float_t* params);
    Float_t flag;   ///< flag

    ClassDef(sndScifiHit,1);
    

};

#endif
