#ifndef SCIFIPOINT_H
#define SCIFIPOINT_H 1


#include "FairMCPoint.h"

#include "TObject.h"
#include "TVector3.h"

class ScifiPoint : public FairMCPoint
{

  public:

    /** Default constructor **/
    ScifiPoint();


    /** Constructor with arguments
     *@param trackID  Index of MCTrack
     *@param detID    Detector ID
     *@param pos      Ccoordinates at entrance to active volume [cm]
     *@param mom      Momentum of track at entrance [GeV]
     *@param tof      Time since event start [ns]
     *@param length   Track length since creation [cm]
     *@param eLoss    Energy deposit [GeV]
     **/
    ScifiPoint(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom,
                     Double_t tof, Double_t length, Double_t eLoss, Int_t pdgcode);




    /** Destructor **/
    virtual ~ScifiPoint();

    /** Output to screen **/
    virtual void Print(const Option_t* opt) const;
    Int_t PdgCode() const {return fPdgCode;}


/* STMRFFF
 First digit S: 			station # within the sub-detector
 Second digit T: 		type of the plane: 0-horizontal fiber plane, 1-vertical fiber plane
 Third digit M: 			determines the mat number
 Fourth digit R: 		row number (in Z direction)
 Last three digits F: 	fiber number
*/
	Int_t station(){return fDetectorID/1E6;}
	Int_t orientation(){return (fDetectorID-station()*1E6)/1E5;}
	Int_t mat(){return (fDetectorID-station()*1E6-orientation()*1E5)/1E4;}
	Int_t row(){return (fDetectorID-station()*1E6-orientation()*1E5-mat()*1E4)/1E3;}
	Int_t fibreN(){return fDetectorID%1000;}

  private:
    /** Copy constructor **/
    Int_t fPdgCode;
    ScifiPoint(const ScifiPoint& point);
    ScifiPoint operator=(const ScifiPoint& point);

    ClassDef(ScifiPoint,2)

};

#endif
