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

			Int_t InitMedium(const char* name);
};

#endif
