// -------------------------------------------------------------------------
// -----                       ShipStack source file                   -----
// -------------------------------------------------------------------------
#include "ShipStack.h"

#include "FairDetector.h"               // for FairDetector
#include "FairLink.h"                   // for FairLink
#include "FairMCPoint.h"                // for FairMCPoint
#include "ShipMCTrack.h"                // for ShipMCTrack
#include "FairRootManager.h"            // for FairRootManager
#include "FairLogger.h"                 // for FairLogger, MESSAGE_ORIGIN

#include <iosfwd>                    // for ostream
#include "TClonesArray.h"               // for TClonesArray
#include "TIterator.h"                  // for TIterator
#include "TLorentzVector.h"             // for TLorentzVector
#include "TParticle.h"                  // for TParticle
#include "TRefArray.h"                  // for TRefArray

#include <stddef.h>                     // for NULL
#include <iostream>                     // for operator<<, etc

using std::cout;
using std::endl;
using std::pair;


// -----   Default constructor   -------------------------------------------
ShipStack::ShipStack(Int_t size)
  : FairGenericStack(),
    fStack(),
    fParticles(new TClonesArray("TParticle", size)),
    fTracks(new TClonesArray("ShipMCTrack", size)),
    fStoreMap(),
    fStoreIter(),
    fIndexMap(),
    fIndexIter(),
    fPointsMap(),
    fCurrentTrack(-1),
    fNPrimaries(0),
    fNParticles(0),
    fNTracks(0),
    fIndex(0),
    fStoreSecondaries(kTRUE),
    fMinPoints(1),
    fEnergyCut(0.),
    fStoreMothers(kTRUE),
    fLogger(FairLogger::GetLogger())
{
}

// -------------------------------------------------------------------------



// -----   Destructor   ----------------------------------------------------
ShipStack::~ShipStack()
{
  if (fParticles) {
    fParticles->Delete();
    delete fParticles;
  }
  if (fTracks) {
    fTracks->Delete();
    delete fTracks;
  }
}
// -------------------------------------------------------------------------

void ShipStack::PushTrack(Int_t toBeDone, Int_t parentId, Int_t pdgCode,
                          Double_t px, Double_t py, Double_t pz,
                          Double_t e, Double_t vx, Double_t vy, Double_t vz,
                          Double_t time, Double_t polx, Double_t poly,
                          Double_t polz, TMCProcess proc, Int_t& ntr,
                          Double_t weight, Int_t is)
{

  PushTrack( toBeDone, parentId, pdgCode,
             px,  py,  pz,
             e,  vx,  vy,  vz,
             time,  polx,  poly,
             polz, proc, ntr,
             weight, is, -1);
}



// -----   Virtual public method PushTrack   -------------------------------
void ShipStack::PushTrack(Int_t toBeDone, Int_t parentId, Int_t pdgCode,
                          Double_t px, Double_t py, Double_t pz,
                          Double_t e, Double_t vx, Double_t vy, Double_t vz,
                          Double_t time, Double_t polx, Double_t poly,
                          Double_t polz, TMCProcess proc, Int_t& ntr,
                          Double_t weight, Int_t is, Int_t secondparentID)
{
 // cout << "ShipStack:  " << fNParticles << " " << pdgCode << " " << parentId <<    " " << secondparentID<<" "<<proc<< endl;

  // --> Get TParticle array
  TClonesArray& partArray = *fParticles;

  // --> Create new TParticle and add it to the TParticle array
  Int_t trackId = fNParticles;
  Int_t nPoints = 0;
  Int_t daughter1Id = -1;
  Int_t daughter2Id = -1;
  TParticle* particle =
    new(partArray[fNParticles++]) TParticle(pdgCode, trackId, parentId,nPoints, 
        daughter1Id, daughter2Id, px, py, pz, e, vx, vy, vz, time);
// from root, how does this fit ? misuse of status and mother2 ??? status is used for trackID definetely 
// TParticle(Int_t pdg, Int_t status, Int_t mother1, Int_t mother2, 
//   Int_t daughter1, Int_t daughter2, Double_t px, Double_t py, Double_t pz, Double_t etot, Double_t vx, Double_t vy, Double_t vz, Double_t time)
  particle->SetPolarisation(polx, poly, polz);
  particle->SetWeight(weight);
  particle->SetUniqueID(proc);
// TR August 2014, still trying to understand the logic of FairRoot, due to misuse of secondparentID, all is a big mess
  if (parentId < 0){ 
     particle->SetFirstMother(secondparentID);
     particle->SetLastMother(secondparentID);
  }
  else {            
      particle->SetFirstMother(parentId);  
      particle->SetLastMother(parentId);  
  }
  // --> Increment counter
  if (parentId < 0) { fNPrimaries++; }

  // --> Set argument variable
  ntr = trackId;

  // --> Push particle on the stack if toBeDone is set
  if (toBeDone == 1) {
      particle->SetBit(kDoneBit);
      fStack.push(particle);
  }

}
// -------------------------------------------------------------------------



// -----   Virtual method PopNextTrack   -----------------------------------
TParticle* ShipStack::PopNextTrack(Int_t& iTrack)
{

  // If end of stack: Return empty pointer
  if (fStack.empty()) {
    iTrack = -1;
    return NULL;
  }

  // If not, get next particle from stack
  TParticle* thisParticle = fStack.top();
  fStack.pop();

  if ( !thisParticle) {
    iTrack = 0;
    return NULL;
  }

  fCurrentTrack = thisParticle->GetStatusCode();
  iTrack = fCurrentTrack;

  return thisParticle;

}
// -------------------------------------------------------------------------



// -----   Virtual method PopPrimaryForTracking   --------------------------
TParticle* ShipStack::PopPrimaryForTracking(Int_t iPrim)
{

  // Get the iPrimth particle from the fStack TClonesArray. This
  // should be a primary (if the index is correct).

  // Test for index
  if (iPrim < 0 || iPrim >= fNPrimaries) {
    fLogger->Fatal(MESSAGE_ORIGIN, "ShipStack: Primary index out of range! %i ", iPrim );
    Fatal("ShipStack::PopPrimaryForTracking", "Index out of range");
  }

  // Return the iPrim-th TParticle from the fParticle array. This should be
  // a primary.
  TParticle* part = (TParticle*)fParticles->At(iPrim);
  /* do not understand the logic behind this !!! TR July 2014
    if ( ! (part->GetMother(0) < 0) ) {
    fLogger->Fatal(MESSAGE_ORIGIN, "ShipStack:: Not a primary track! %i ",iPrim);
    Fatal("ShipStack::PopPrimaryForTracking", "Not a primary track");
  }*/
  if(!part->TestBit(kDoneBit)) return NULL;
  else return part;

}
// -------------------------------------------------------------------------



// -----   Virtual public method GetCurrentTrack   -------------------------
TParticle* ShipStack::GetCurrentTrack() const
{
  TParticle* currentPart = GetParticle(fCurrentTrack);
  if ( ! currentPart) {
    fLogger->Warning(MESSAGE_ORIGIN,"ShipStack: Current track not found in stack!");
    Warning("ShipStack::GetCurrentTrack", "Track not found in stack");
  }
  return currentPart;
}
// -------------------------------------------------------------------------



// -----   Public method AddParticle   -------------------------------------
void ShipStack::AddParticle(TParticle* oldPart)
{
  TClonesArray& array = *fParticles;
  TParticle* newPart = new(array[fIndex]) TParticle(*oldPart);
  newPart->SetWeight(oldPart->GetWeight());
  newPart->SetUniqueID(oldPart->GetUniqueID());
  fIndex++;
}
// -------------------------------------------------------------------------



// -----   Public method FillTrackArray   ----------------------------------
void ShipStack::FillTrackArray()
{

  fLogger->Debug(MESSAGE_ORIGIN, "ShipStack: Filling MCTrack array...");

  // --> Reset index map and number of output tracks
  fIndexMap.clear();
  fNTracks = 0;

  // --> Check tracks for selection criteria
  SelectTracks();

  // --> Loop over fParticles array and copy selected tracks
  for (Int_t iPart=0; iPart<fNParticles; iPart++) {

    fStoreIter = fStoreMap.find(iPart);
    if (fStoreIter == fStoreMap.end() ) {
      fLogger->Fatal(MESSAGE_ORIGIN, "ShipStack: Particle %i not found in storage map! ", iPart);
      Fatal("ShipStack::FillTrackArray",
            "Particle not found in storage map.");
    }
    Bool_t store = (*fStoreIter).second;

    if (store) {
      ShipMCTrack* track =
        new( (*fTracks)[fNTracks]) ShipMCTrack(GetParticle(iPart));
      fIndexMap[iPart] = fNTracks;
      // --> Set the number of points in the detectors for this track
      for (Int_t iDet=kVETO; iDet<kEndOfList; iDet++) {
        pair<Int_t, Int_t> a(iPart, iDet);
        track->SetNPoints(iDet, fPointsMap[a]);
      }
      fNTracks++;
    } else { fIndexMap[iPart] = -2; }

  }

  // --> Map index for primary mothers
  fIndexMap[-1] = -1;

  // --> Screen output
  //Print(1);

}
// -------------------------------------------------------------------------



// -----   Public method UpdateTrackIndex   --------------------------------
void ShipStack::UpdateTrackIndex(TRefArray* detList)
{

  fLogger->Debug(MESSAGE_ORIGIN, "ShipStack: Updating track indizes...");
  Int_t nColl = 0;

  // First update mother ID in MCTracks
  for (Int_t i=0; i<fNTracks; i++) {
    ShipMCTrack* track = (ShipMCTrack*)fTracks->At(i);
    Int_t iMotherOld = track->GetMotherId();
    fIndexIter = fIndexMap.find(iMotherOld);
    if (fIndexIter == fIndexMap.end()) {
      fLogger->Fatal(MESSAGE_ORIGIN, "ShipStack: Particle index %i not found in dex map! ", iMotherOld);
      Fatal("ShipStack::UpdateTrackIndex", "Particle index not found in map");
    }
    track->SetMotherId( (*fIndexIter).second );
  }


  if(fDetList==0) {
    // Now iterate through all active detectors
    fDetIter = detList->MakeIterator();
    fDetIter->Reset();
  } else {
    fDetIter->Reset();
  }

  FairDetector* det = NULL;
  while( (det = (FairDetector*)fDetIter->Next() ) ) {


    // --> Get hit collections from detector
    Int_t iColl = 0;
    TClonesArray* hitArray;
    while ( (hitArray = det->GetCollection(iColl++)) ) {
      nColl++;
      Int_t nPoints = hitArray->GetEntriesFast();

      // --> Update track index for all MCPoints in the collection
      for (Int_t iPoint=0; iPoint<nPoints; iPoint++) {
        FairMCPoint* point = (FairMCPoint*)hitArray->At(iPoint);
        Int_t iTrack = point->GetTrackID();

        fIndexIter = fIndexMap.find(iTrack);
        if (fIndexIter == fIndexMap.end()) {
          fLogger->Fatal(MESSAGE_ORIGIN, "ShipStack: Particle index %i not found in index map! ", iTrack);
          Fatal("ShipStack::UpdateTrackIndex", "Particle index not found in map");
        }
        point->SetTrackID((*fIndexIter).second);
        point->SetLink(FairLink("MCTrack", (*fIndexIter).second));
      }

    }   // Collections of this detector
  }     // List of active detectors
  fLogger->Debug(MESSAGE_ORIGIN, "...stack and  %i collections updated.", nColl);
}
// -------------------------------------------------------------------------



// -----   Public method Reset   -------------------------------------------
void ShipStack::Reset()
{
  fIndex = 0;
  fCurrentTrack = -1;
  fNPrimaries = fNParticles = fNTracks = 0;
  while (! fStack.empty() ) { fStack.pop(); }
  fParticles->Clear();
  fTracks->Clear();
  fPointsMap.clear();
}
// -------------------------------------------------------------------------



// -----   Public method Register   ----------------------------------------
void ShipStack::Register()
{
  FairRootManager::Instance()->Register("MCTrack", "Stack", fTracks,kTRUE);
}
// -------------------------------------------------------------------------



// -----   Public method Print  --------------------------------------------
void ShipStack::Print(Int_t iVerbose) const
{
  cout << "-I- ShipStack: Number of primaries        = "
       << fNPrimaries << endl;
  cout << "              Total number of particles  = "
       << fNParticles << endl;
  cout << "              Number of tracks in output = "
       << fNTracks << endl;
  if (iVerbose) {
    for (Int_t iTrack=0; iTrack<fNTracks; iTrack++) {
      ((ShipMCTrack*) fTracks->At(iTrack))->Print(iTrack);
    }
  }
}
// -------------------------------------------------------------------------



// -----   Public method AddPoint (for current track)   --------------------
void ShipStack::AddPoint(DetectorId detId)
{
  Int_t iDet = detId;
// cout << "Add point for Detektor" << iDet << endl;
  pair<Int_t, Int_t> a(fCurrentTrack, iDet);
  if ( fPointsMap.find(a) == fPointsMap.end() ) { fPointsMap[a] = 1; }
  else { fPointsMap[a]++; }
}
// -------------------------------------------------------------------------



// -----   Public method AddPoint (for arbitrary track)  -------------------
void ShipStack::AddPoint(DetectorId detId, Int_t iTrack)
{
  if ( iTrack < 0 ) { return; }
  Int_t iDet = detId;
  pair<Int_t, Int_t> a(iTrack, iDet);
  if ( fPointsMap.find(a) == fPointsMap.end() ) { fPointsMap[a] = 1; }
  else { fPointsMap[a]++; }
}
// -------------------------------------------------------------------------




// -----   Virtual method GetCurrentParentTrackNumber   --------------------
Int_t ShipStack::GetCurrentParentTrackNumber() const
{
  TParticle* currentPart = GetCurrentTrack();
  if ( currentPart ) { return currentPart->GetFirstMother(); }
  else { return -1; }
}
// -------------------------------------------------------------------------



// -----   Public method GetParticle   -------------------------------------
TParticle* ShipStack::GetParticle(Int_t trackID) const
{
  if (trackID < 0 || trackID >= fNParticles) {
    fLogger->Info(MESSAGE_ORIGIN, "ShipStack: Particle index %i out of range. Max=%i",trackID,fNParticles);
    Fatal("ShipStack::GetParticle", "Index out of range ");
  }
  return (TParticle*)fParticles->At(trackID);
}
// -------------------------------------------------------------------------



// -----   Private method SelectTracks   -----------------------------------
void ShipStack::SelectTracks()
{

  // --> Clear storage map
  fStoreMap.clear();

  // --> Check particles in the fParticle array
  for (Int_t i=0; i<fNParticles; i++) {

    TParticle* thisPart = GetParticle(i);
    Bool_t store = kTRUE;

    // --> Get track parameters
    Int_t iMother   = thisPart->GetMother(0);
    TLorentzVector p;
    thisPart->Momentum(p);
    Double_t energy = p.E();
    Double_t mass   = p.M();
//    Double_t mass   = thisPart->GetMass();
    Double_t eKin = energy - mass;

    // --> Calculate number of points
    Int_t nPoints = 0;
    for (Int_t iDet=kVETO; iDet<kEndOfList; iDet++) {
      pair<Int_t, Int_t> a(i, iDet);
      if ( fPointsMap.find(a) != fPointsMap.end() ) {
        nPoints += fPointsMap[a];
      }
    }

    // --> Check for cuts (store primaries in any case)
    if (iMother < 0) { store = kTRUE; }
    else {
      if (!fStoreSecondaries) { store = kFALSE; }
      if (nPoints < fMinPoints) { store = kFALSE; }
      if (eKin < fEnergyCut) { store = kFALSE; }
      if ((nPoints >= fMinPoints && fMinPoints > 0) || (eKin >= fEnergyCut && fEnergyCut > 0)) {
         store=kTRUE;
      }
    }
    // --> Set storage flag
    fStoreMap[i] = store;
// special case for Ship generators, want to keep all original particles with their mother daughter relationship 
// independent if tracked or not. apply a dirty trick and use second mother to identify original generator particles. 
// doesn't work, always true: Int_t iMother2 = GetParticle(i)->GetMother(1); maybe should set Mother2 to -1 in the generator
// if (iMother == iMother2) {fStoreMap[i] = kTRUE;}
  }
  // --> If flag is set, flag recursively mothers of selected tracks
  if (fStoreMothers) {
    for (Int_t i=0; i<fNParticles; i++) {
      if (fStoreMap[i]) {
        Int_t iMother  = GetParticle(i)->GetMother(0);
	{
          while(iMother >= 0)
	  {
            fStoreMap[iMother] = kTRUE;
            iMother = GetParticle(iMother)->GetMother(0);
          }
       }
      }
    }
  }

}
// -------------------------------------------------------------------------



ClassImp(ShipStack)
