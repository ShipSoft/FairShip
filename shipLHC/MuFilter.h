//  
//  MuFilter.h 
//  
//  by A. Buonaura

#ifndef MuFilter_H
#define MuFilter_H

#include "FairModule.h"                 // for FairModule
#include "FairDetector.h"

#include "Rtypes.h"                     // for ShipMuonShield::Class, Bool_t, etc

#include <string>                       // for string

#include "TVector3.h"
#include "TString.h"
#include "TLorentzVector.h"

class MuFilterPoint;
class FairVolume;
class TClonesArray;

class MuFilter : public FairDetector
{
	public:
		MuFilter(const char* name, Bool_t Active, const char* Title="MuonFilter");
		MuFilter();
		virtual ~MuFilter();

		/**      Create the detector geometry        */
		void ConstructGeometry();

    /** Getposition **/
                 void GetPosition(Int_t id, TVector3& vLeft, TVector3& vRight); // or top and bottom
                 Int_t GetnSiPMs(Int_t detID);
                 Int_t GetnSides(Int_t detID);

		void SetConfPar(TString name, Float_t value){conf_floats[name]=value;}
		void SetConfPar(TString name, Int_t value){conf_ints[name]=value;}
		void SetConfPar(TString name, TString value){conf_strings[name]=value;}
		Float_t  GetConfParF(TString name){return conf_floats[name];} 
		Int_t       GetConfParI(TString name){return conf_ints[name];}
		TString  GetConfParS(TString name){return conf_strings[name];}

		/**      Initialization of the detector is done here    */
		virtual void Initialize();

		/**  Method called for each step during simulation (see FairMCApplication::Stepping()) */
		virtual Bool_t ProcessHits( FairVolume* v=0);

		/**       Registers the produced collections in FAIRRootManager.     */
		virtual void   Register();

		/** Gets the produced collections */
		virtual TClonesArray* GetCollection(Int_t iColl) const ;

		/**      has to be called after each event to reset the containers      */
		virtual void   Reset();

		/**      How to add your own point of type EmulsionDetPoint to the clones array */

		MuFilterPoint* AddHit(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom,
				Double_t time, Double_t length, Double_t eLoss, Int_t pdgCode);


		virtual void   CopyClones( TClonesArray* cl1,  TClonesArray* cl2 , Int_t offset) {;}
		virtual void   SetSpecialPhysicsCuts() {;}
		virtual void   EndOfEvent();
		virtual void   FinishPrimary() {;}
		virtual void   FinishRun() {;}
		virtual void   BeginPrimary() {;}
		virtual void   PostTrack() {;}
		virtual void   PreTrack() {;}
		virtual void   BeginEvent() {;}

		MuFilter(const MuFilter&);
		MuFilter& operator=(const MuFilter&);

		ClassDef(MuFilter,4)

	private:

			/** Track information to be stored until the track leaves the active volume. */
			Int_t          fTrackID;           //!  track index
			Int_t          fVolumeID;          //!  volume id
			TLorentzVector fPos;               //!  position at entrance
			TLorentzVector fMom;               //!  momentum at entrance
			Double32_t     fTime;              //!  time
			Double32_t     fLength;            //!  length
			Double32_t     fELoss;             //!  energy loss

			/** container for data points */
			TClonesArray*  fMuFilterPointCollection;

			/** configuration parameters **/
			std::map<TString,Float_t> conf_floats;
			std::map<TString,Int_t> conf_ints;
			std::map<TString,TString> conf_strings;

	protected:
			Double_t fVetoShiftX;  //|Shift of Veto with respect to beam line
			Double_t fVetoShiftY;  //|
			
			Double_t fVetoPlaneX;  //|Veto Plane dimensions
			Double_t fVetoPlaneY;  //|
			Double_t fVetoPlaneZ;  //|
			
			Double_t fVetoBarX;    //!Veto Bar dimensions
			Double_t fVetoBarY;
			Double_t fVetoBarZ;
			
			Double_t fVetoCenterZ;
			Int_t fNVetoPlanes;
			Int_t fNVetoBars;
			Double_t fVetoPlaneShiftY;			
			
			Double_t fMuFilterX;	//|MuonFilterBox dimensions
			Double_t fMuFilterY;	//|
			Double_t fMuFilterZ;	//|

			Double_t fFeBlockX;     //|Passive Iron blocks dimensions
			Double_t fFeBlockY;     //|
			Double_t fFeBlockZ;     //|

			Double_t fUpstreamDetX;	//|Upstream muon detector planes dimensions
			Double_t fUpstreamDetY;	//|
			Double_t fUpstreamDetZ;	//|			

			Double_t fUSShiftX;  //| US with respect to nominal
			Double_t fUSShiftY;  //|
			Double_t fUSShiftZ;  //|

			Int_t fNUpstreamPlanes;	//|Number of planes

			Double_t fUpstreamBarX; //|Staggered bars of upstream section
			Double_t fUpstreamBarY;
			Double_t fUpstreamBarZ;

		        Int_t fNUpstreamBars;   //|Number of staggered bars

			Double_t fDownstreamDetX;	//|Downstream muon detector planes dimensions
			Double_t fDownstreamDetY;	//|
			Double_t fDownstreamDetZ;	//|

			Double_t fDSHShiftX;  //| DS with respect to nominal
			Double_t fDSHShiftY;  //|
			Double_t fDSHShiftZ;  //|
			Double_t fDSVShiftX;  //|  
			Double_t fDSVShiftY;  //|
			Double_t fDSVShiftZ;  //|

			Int_t fNDownstreamPlanes;	//|Number of planes

			Double_t fDownstreamBarX; //|Staggered bars of upstream section
			Double_t fDownstreamBarY;
			Double_t fDownstreamBarZ;			

		        Int_t fNDownstreamBars;   //|Number of staggered bars
		        Double_t fDS4ZGap;

  			Double_t fDownstreamBarX_ver; //|Staggered bars of upstream section, vertical bars for x measurement
			Double_t fDownstreamBarY_ver;
			Double_t fDownstreamBarZ_ver;

			Double_t fCenterZ;	//|Zposition of the muon filter
			Double_t fShiftX;	//|Shift in x-y wrt beam line
			Double_t fShiftY;	//|
                        Double_t fShiftYEnd;    //|Shift for Downstream station
                        Double_t fSlope; //Slope for floor

                        Float_t attLength;   //| attenuation length for Downstream bars
                        Float_t attLengthVandUp; //| attenuation length for Veto and Upstream bars
                        Float_t dynRangeLow;   //max value for low dynamic range
                        Float_t dynRangeHigh; //max value for high dynamic range
                        Float_t siPMcalibration; // Volt/MeV
                        Float_t nSiPMs[3];             //  number of SiPMs per side
                        Float_t nSides[3];             //  number of sides readout

			Int_t InitMedium(const char* name);
};

#endif
