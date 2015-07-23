#ifndef RPCPOINT_H
#define RPCPOINT_H 1


#include "FairMCPoint.h"

#include "TObject.h"
#include "TVector3.h"

class ShipRpcPoint : public FairMCPoint
{

  public:

    /** Default constructor **/
    ShipRpcPoint();


    /** Constructor with arguments
     *@param trackID  Index of MCTrack
     *@param detID    Detector ID
     *@param pos      Ccoordinates at entrance to active volume [cm]
     *@param mom      Momentum of track at entrance [GeV]
     *@param tof      Time since event start [ns]
     *@param length   Track length since creation [cm]
     *@param eLoss    Energy deposit [GeV]
     **/
    /*ShipRpcPoint(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom,
                     Double_t tof, Double_t length, Double_t eLoss, Int_t pdgcode, Int_t nArm, Int_t nRpc, Int_t nHpt);
*/

    ShipRpcPoint(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom,
                     Double_t tof, Double_t length, Double_t eLoss, Int_t pdgcode);


    /** Destructor **/
    virtual ~ShipRpcPoint();

    /** Output to screen **/
    virtual void Print(const Option_t* opt) const;
    Int_t PdgCode() const {return fPdgCode;}
/*   
    Int_t NArm() const {return fNArm;}
    Int_t NRpc() const {return fNRpc;}
    Int_t NHpt() const {return fNHpt;}
    */

  private:
    /** Copy constructor **/
    Int_t fPdgCode;
    /*
    Int_t fNArm; //in which Arm is the Rpc (1 or 2)
    Int_t fNRpc; //in which Rpc is the hit (<=11)
    Int_t fNHpt; //in which HPT is the hit (<=6)
*/

    ShipRpcPoint(const ShipRpcPoint& point);
    ShipRpcPoint operator=(const ShipRpcPoint& point);

    ClassDef(ShipRpcPoint,2)

};

#endif
