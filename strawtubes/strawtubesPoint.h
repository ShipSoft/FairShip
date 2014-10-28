#ifndef STRAWTUBESPOINT_H
#define STRAWTUBESPOINT_H 1


#include "FairMCPoint.h"

#include "TObject.h"
#include "TVector3.h"

class strawtubesPoint : public FairMCPoint
{
  public:

    /** Default constructor **/
    strawtubesPoint();

    /** Constructor with arguments
     *@param trackID  Index of MCTrack
     *@param detID    Detector ID
     *@param pos      Ccoordinates at entrance to active volume [cm]
     *@param mom      Momentum of track at entrance [GeV]
     *@param tof      Time since event start [ns]
     *@param length   Track length since creation [cm]
     *@param eLoss    Energy deposit [GeV]
     **/
    strawtubesPoint(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom,
                     Double_t tof, Double_t length, Double_t eLoss);

    /** Destructor **/
    virtual ~strawtubesPoint();

    /** Output to screen **/
    virtual void Print(Int_t detID) const;
    Double_t StrawY(Int_t detID);
    Double_t StrawXTop(Int_t detID);
    Double_t StrawXBot(Int_t detID);
    Double_t StrawYTop(Int_t detID);
    Double_t StrawYBot(Int_t detID);
    Double_t StrawZ(Int_t detID);
    
    Double_t fT0z;                    //!  z-position of veto station
    Double_t fT1z;                     //!  z-position of tracking station 1
    Double_t fT2z;                     //!  z-position of tracking station 2
    Double_t fT3z;                     //!  z-position of tracking station 3 (avoid overlap with magnet)
    Double_t fT4z;                     //!  z-position of tracking station 4 (avoid overlap with ecal)

    Double_t fStraw_length;             //!  Length (y) of a straw
    Double_t fInner_Straw_diameter;     //!  Inner Straw diameter
    Double_t fOuter_Straw_diameter;     //!  Outer Straw diameter
    Double_t fStraw_pitch;              //!  Distance (x) between straws in one layer
    Double_t fDeltaz_layer12;            //!  Distance (z) between layer 1&2
    Double_t fDeltaz_plane12;           //!  Distance (z) between plane 1&2
    Double_t fOffset_layer12; //!  Offset (x) between straws of layer1&2
    Double_t fOffset_plane12; //!  Offset (x) between straws of plane1&2
    Int_t fStraws_per_layer;             //!  Number of straws in one layer
    Int_t fView_angle;                     //!  Stereo angle of layers in a view
    Double_t fWire_thickness;          //!  Thickness of the wire
    Double_t fDeltaz_view;               //!  Distance (z) between views
    Double_t fVacbox_x;                 //!  x of station vacuum box
    Double_t fVacbox_y;                 //!  y of station vacuum box

  private:
    /** Copy constructor **/
    strawtubesPoint(const strawtubesPoint& point);
    strawtubesPoint operator=(const strawtubesPoint& point);

    ClassDef(strawtubesPoint,1);
    

};

#endif
