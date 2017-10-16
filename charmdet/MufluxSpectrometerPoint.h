#ifndef MUFLUXSPECTROMETERPOINT_H
#define MUFLUXSPECTROMETERPOINT_H 1


#include "FairMCPoint.h"

#include "TObject.h"
#include "TVector3.h"

class MufluxSpectrometerPoint:public FairMCPoint
{

  public:

    /** Default constructor **/
    MufluxSpectrometerPoint();


    /** Constructor with arguments
     *@param trackID  Index of MCTrack
     *@param detID    Detector ID
     *@param pos      Ccoordinates at entrance to active volume [cm]
     *@param mom      Momentum of track at entrance [GeV]
     *@param tof      Time since event start [ns]
     *@param length   Track length since creation [cm]
     *@param eLoss    Energy deposit [GeV]
     **/
    

    MufluxSpectrometerPoint(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom,
                     Double_t tof, Double_t length, Double_t eLoss, Int_t pdgcode, Double_t dist);


    /** Destructor **/
    virtual ~MufluxSpectrometerPoint();

    /** Output to screen **/
    virtual void Print(const Option_t* opt) const;
    Int_t PdgCode() const {return fPdgCode;}
    Double_t dist2Wire() const {return fdist2Wire;}

  private:
    
    Int_t fPdgCode;
    Double_t fdist2Wire; 
        
    /** Copy constructor **/
    
    MufluxSpectrometerPoint(const MufluxSpectrometerPoint& point);
    MufluxSpectrometerPoint operator=(const MufluxSpectrometerPoint& point);

    ClassDef(MufluxSpectrometerPoint,1)

};

#endif
