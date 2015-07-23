#ifndef TARGETPOINT_H
#define TARGETPOINT_H 1


#include "FairMCPoint.h"

#include "TObject.h"
#include "TVector3.h"

class TargetPoint : public FairMCPoint
{

  public:

    /** Default constructor **/
    TargetPoint();


    /** Constructor with arguments
     *@param trackID  Index of MCTrack
     *@param detID    Detector ID
     *@param pos      Ccoordinates at entrance to active volume [cm]
     *@param mom      Momentum of track at entrance [GeV]
     *@param tof      Time since event start [ns]
     *@param length   Track length since creation [cm]
     *@param eLoss    Energy deposit [GeV]
     **/
	TargetPoint(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom,
                     Double_t tof, Double_t length, Double_t eLoss, Int_t pdgCode,
		Bool_t emTop, Bool_t emBot,Bool_t emCESTop, Bool_t emCESBot, Bool_t tt, 
		Int_t nPlate, Int_t nColumn, Int_t nRow, Int_t nWall);

    /** Destructor **/
    virtual ~TargetPoint();

    /** Output to screen **/
    virtual void Print(const Option_t* opt) const;
    

    Int_t PdgCode() const {return fPdgCode;}
    Bool_t IsTop() const {return fEmTop;}
    Bool_t IsBot() const {return fEmBot;}
    Bool_t IsCESTop() const {return fEmCESTop;}
    Bool_t IsCESBot() const {return fEmCESBot;}
    Bool_t IsTT() const {return fTT;}
    Int_t NPlate() const {return fNPlate;}
    Int_t NColumn() const {return fNColumn;}
    Int_t NRow() const {return fNRow;}
    Int_t NWall() const {return fNWall;}

  private:
    /** Copy constructor **/
    Int_t fPdgCode;
    Bool_t fEmTop; //is emulsion top
    Bool_t fEmBot;//is emulsion bottom
    Bool_t fEmCESTop; //is emulsion from CES top
    Bool_t fEmCESBot; //is emulsion from CES bottom
    Bool_t fTT; //is point in Target Tracker
    Int_t fNPlate; //which emulsion plate (<57 for bricks, < 3 CES)
    Int_t fNColumn; //in which column is the brick (<15)
    Int_t fNRow; //in which row is the brick (<7)
    Int_t fNWall; //in which wall is the brick (<11)

    TargetPoint(const TargetPoint& point);
    TargetPoint operator=(const TargetPoint& point);

    ClassDef(TargetPoint,2)

};

#endif
