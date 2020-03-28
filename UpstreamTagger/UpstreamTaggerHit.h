#ifndef UpstreamTaggerHIT_H
#define UpstreamTaggerHIT_H 1
#include "FairVolume.h"
#include "ShipHit.h"
#include "UpstreamTaggerPoint.h"
#include "UpstreamTagger.h"
#include "TObject.h"
#include "TGeoShape.h"
#include "TGeoPhysicalNode.h"


class UpstreamTaggerHit : public ShipHit, UpstreamTagger
{
  public:
  
    /** Default constructor **/
    UpstreamTaggerHit();

    UpstreamTaggerHit(UpstreamTaggerPoint* p, Double_t t0);

    /** Destructor **/
    virtual ~UpstreamTaggerHit();

    /** Accessors **/
    Double_t GetX();
    Double_t GetY();
    Double_t GetZ();
    TVector3 GetXYZ();
   
      
    TGeoNode* GetNode(Double_t &hit_final, Int_t &mod);
    std::vector<double> GetTime(Double_t x);
    std::vector<double> GetTime();
    std::vector<double> GetMeasurements();
    /** Modifier **/
    void SetTDC(Float_t val1, Float_t val2){t_1=val1;t_2=val2;}
    void SetPoint(Double_t p1, Double_t p2, Double_t p3){point_final[0]=p1;point_final[1]=p2;point_final[2]=p3;}
    /** Output to screen **/
    virtual void Print() const;

    void Dist(Float_t x, Float_t& lpos, Float_t& lneg);
    void setInvalid() {flag = false;}
    void setIsValid() {flag = true;}
    Int_t GetModule() const {return RpcModule;}
    Int_t GetGlass() const {return RpcGlass;}
    Int_t GetStrip() const {return RpcStrip;}
    Int_t GetNeighbour() const {return Rpc_NeighbourStrip;}
    Int_t GetRpcDetector() const {return RpcDetector;}
    
    //Rpc time is invalid if isValid returns False
    bool isValid() const {return flag;}
  private:
    UpstreamTaggerHit(const UpstreamTaggerHit& point);
    UpstreamTaggerHit operator=(const UpstreamTaggerHit& point);
    Double_t v_drift = 17.7;// cm/ns
    Double_t T_resol = 0.283; // Rpc time resolution in ns

    Double_t point_final[3];
    const Double_t * mom[3];

    Float_t flag;     ///< flag
    Float_t t_1,t_2;  ///< TDC on both sides
    Int_t RpcModule; //Rpc module
    Int_t RpcGlass;  //Rpc glass
    Int_t RpcStrip;  //Rpc Strip
    Int_t RpcDetector;  //Rpc detector 1 or 2
    Int_t Rpc_NeighbourStrip; //Neighbour strip likely to be activated
    Double_t det_zdet1;     //!  z-position of veto station
    
    ClassDef(UpstreamTaggerHit,1);

};

#endif
