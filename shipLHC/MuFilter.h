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

		/** Other functions **/
		void SetIronBlockDimensions(Double_t , Double_t, Double_t);	       
		void SetMuFilterDimensions(Double_t, Double_t, Double_t);
		void SetCenterZ(Double_t);
                void SetXYDisplacement(Double_t , Double_t ); //global xy position
                void SetYPlanesDisplacement(Double_t); //displacement for downstream plates
                void SetSlope(Double_t);

		void SetUpstreamPlanesDimensions(Double_t, Double_t, Double_t);
		void SetNUpstreamPlanes(Int_t);
		void SetUpstreamBarsDimensions(Double_t, Double_t, Double_t);
		void SetNUpstreamBars(Int_t);

		void SetDownstreamPlanesDimensions(Double_t, Double_t, Double_t);
		void SetNDownstreamPlanes(Int_t);
		void SetDownstreamBarsDimensions(Double_t, Double_t, Double_t);
                void SetDownstreamVerticalBarsDimensions(Double_t, Double_t, Double_t);
		void SetNDownstreamBars(Int_t);

		


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

		ClassDef(MuFilter,3)

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

	protected:
			Double_t fMuFilterX;	//|MuonFilterBox dimensions
			Double_t fMuFilterY;	//|
			Double_t fMuFilterZ;	//|

			Double_t fFeBlockX;     //|Passive Iron blocks dimensions
			Double_t fFeBlockY;     //|
			Double_t fFeBlockZ;     //|

			Double_t fUpstreamDetX;	//|Upstream muon detector planes dimensions
			Double_t fUpstreamDetY;	//|
			Double_t fUpstreamDetZ;	//|			

			Int_t fNUpstreamPlanes;	//|Number of planes

			Double_t fUpstreamBarX; //|Staggered bars of upstream section
			Double_t fUpstreamBarY;
			Double_t fUpstreamBarZ;

		        Int_t fNUpstreamBars;   //|Number of staggered bars

			Double_t fDownstreamDetX;	//|Downstream muon detector planes dimensions
			Double_t fDownstreamDetY;	//|
			Double_t fDownstreamDetZ;	//|

			Int_t fNDownstreamPlanes;	//|Number of planes

			Double_t fDownstreamBarX; //|Staggered bars of upstream section
			Double_t fDownstreamBarY;
			Double_t fDownstreamBarZ;			

		        Int_t fNDownstreamBars;   //|Number of staggered bars

  			Double_t fDownstreamBarX_ver; //|Staggered bars of upstream section, vertical bars for x measurement
			Double_t fDownstreamBarY_ver;
			Double_t fDownstreamBarZ_ver;

			Double_t fCenterZ;	//|Zposition of the muon filter
			Double_t fShiftX;	//|Shift in x-y wrt beam line
			Double_t fShiftY;	//|
                        Double_t fShiftYEnd;    //|Shift for Downstream station
                        Double_t fSlope; //Slope for floor

			Int_t InitMedium(const char* name);
};

#endif
