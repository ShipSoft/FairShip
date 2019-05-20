#ifndef TIMEDET_H
#define TIMEDET_H

#include "FairDetector.h"

#include "TVector3.h"
#include "TLorentzVector.h"

class TimeDetPoint;
class FairVolume;
class TClonesArray;


class TimeDet: public FairDetector
{

  public:

    /**      Name :  Detector Name
     *       Active: kTRUE for active detectors (ProcessHits() will be called)
     *               kFALSE for inactive detectors
    */
    TimeDet(const char* Name, Bool_t Active);

    /** default constructor */
    TimeDet();

    /** destructor */
    virtual ~TimeDet();

    /** Initialization of the detector is done here */
    virtual void   Initialize();

    /**   this method is called for each step during simulation
     *    (see FairMCApplication::Stepping())
    */
    virtual Bool_t ProcessHits( FairVolume* v=0);

    /**       Registers the produced collections in FAIRRootManager. */
    virtual void Register();

    /** Gets the produced collections */
    virtual TClonesArray* GetCollection(Int_t iColl) const;

    /** has to be called after each event to reset the containers */
    virtual void Reset();

    /** Sets detector position along z */
    void SetZposition(Double_t z) {fzPos = z;}
    void SetBarZspacing(Double_t row, Double_t column)
    {
       fdzBarRow = row;
       fdzBarCol = column;
    }
    void SetBarZ(Double_t dz) {fzBar = dz;}
    void SetSizeX(Double_t x) {fxSize = x;}
    void SetSizeY(Double_t y) {fySize = y;}

    double GetXCol(int ic) const;
    double GetYRow(int ir) const;
    void GetBarRowCol(int ib,int &irow,int& icol) const;
    double GetZBar(int ir,int ic) const;

    /**  Create the detector geometry */
    void ConstructGeometry();

    /**      This method is an example of how to add your own point
     *       of type TimeDetPoint to the clones array
    */
    TimeDetPoint* AddHit(Int_t trackID, Int_t detID,
			 TVector3 pos, TVector3 mom,
			 Double_t time, Double_t length,
			 Double_t eLoss, Int_t pdgCode,TVector3 Lpos, TVector3 Lmom);

    virtual void   EndOfEvent();
    virtual void   FinishPrimary() {;}
    virtual void   FinishRun() {;}
    virtual void   BeginPrimary() {;}
    virtual void   PostTrack() {;}
    virtual void   PreTrack() {;}
    virtual void   BeginEvent() {;}


  private:

    /** Track information to be stored until the track leaves the active volume.*/
    Int_t          fTrackID;            //!  track index
    Int_t          fVolumeID;           //!  volume id
    TLorentzVector fPos;                //!  position at entrance
    TLorentzVector fMom;                //!  momentum at entrance
    Double_t       fTime;               //!  time
    Double_t       fLength;             //!  length
    Double_t       fELoss;              //!  energy loss

    /** Detector parameters.*/
    Double_t     fzPos;     //!  z-position of veto station

    Double_t fxSize; //! width of the detector
    Double_t fySize; //! height of the detector

    Double_t fxBar;  //! length of the bar
    Double_t fyBar;  //! width of the bar
    Double_t fzBar;  //! depth of the bar
    
    Double_t fdzBarCol; //! z-distance between columns
    Double_t fdzBarRow; //! z-distance between rows
    
    Int_t fNCol;    //! Number of columns
    Int_t fNRow;    //! Number of rows
    
    Double_t fxCenter; //! x-position of the detector center
    Double_t fyCenter; //! y-position of the detector center

    Int_t fNBars;    //! Number of bars
    Double_t fxOv;   //! Overlap along x
    Double_t fyOv;   //! Overlap along y

    TGeoVolume* fDetector; // Timing detector object

    /** container for data points */
    TClonesArray* fTimeDetPointCollection;

    TimeDet(const TimeDet&);
    TimeDet& operator=(const TimeDet&);
    Int_t InitMedium(const char* name);


    ClassDef(TimeDet,3)
};

#endif //TIMEDET_H
