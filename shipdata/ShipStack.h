// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// -------------------------------------------------------------------------
// -----                       ShipStack header file                   -----
// -------------------------------------------------------------------------

/** ShipStack.h
 **
 ** This class handles the particle stack for the transport simulation.
 ** For the stack FILO functunality, it uses the STL stack. To store
 ** the tracks during transport, a TParticle array is used.
 ** At the end of the event, tracks satisfying the filter criteria
 ** are copied to a FairMCTrack array, which is stored in the output.
 **
 ** The filtering criteria for the output tracks are:
 ** - primary tracks are stored in any case.
 ** - secondary tracks are stored if they have a minimal number of
 **   points (sum of all detectors) and a minimal energy, or are the
 **
 ** The storage of secondaries can be switched off.
 ** The storage of all mothers can be switched off.
 ** By default, the minimal number of points is 1 and the energy cut is 0.
 **/

#ifndef SHIPDATA_SHIPSTACK_H_
#define SHIPDATA_SHIPSTACK_H_

#include <map>      // for map, map<>::iterator
#include <stack>    // for stack
#include <utility>  // for pair
#include <vector>   // for vector

#include "FairGenericStack.h"  // for FairGenericStack
#include "ShipDetectorList.h"  // for DetectorId
#include "TMCProcess.h"        // for TMCProcess

class TClonesArray;
class ShipMCTrack;
class TParticle;
class TRefArray;
class FairLogger;

enum { kDoneBit = 1 };

class ShipStack : public FairGenericStack {
 public:
  /** Default constructor
   *param size  Estimated track number
   **/
  explicit ShipStack(int32_t size = 100);

  /** Destructor  **/
  virtual ~ShipStack();

  /** Add a TParticle to the stack.
   ** Declared in TVirtualMCStack
   *@param toBeDone  Flag for tracking
   *@param parentID  Index of mother particle
   *@param pdgCode   Particle type (PDG encoding)
   *@param px,py,pz  Momentum components at start vertex [GeV]
   *@param e         Total energy at start vertex [GeV]
   *@param vx,vy,vz  Coordinates of start vertex [cm]
   *@param time      Start time of track [s]
   *@param polx,poly,polz Polarisation vector
   *@param proc      Production mechanism (VMC encoding)
   *@param ntr       Track number (filled by the stack)
   *@param weight    Particle weight
   *@param is        Generation status code (whatever that means)
   **/
  virtual void PushTrack(int32_t toBeDone, int32_t parentID, int32_t pdgCode,
                         double px, double py, double pz, double e, double vx,
                         double vy, double vz, double time, double polx,
                         double poly, double polz, TMCProcess proc,
                         int32_t& ntr, double weight, int32_t is);

  virtual void PushTrack(int32_t toBeDone, int32_t parentID, int32_t pdgCode,
                         double px, double py, double pz, double e, double vx,
                         double vy, double vz, double time, double polx,
                         double poly, double polz, TMCProcess proc,
                         int32_t& ntr, double weight, int32_t is,
                         int32_t secondParentId);

  /** Get next particle for tracking from the stack.
   ** Declared in TVirtualMCStack
   *@param  iTrack  index of popped track (return)
   *@return Pointer to the TParticle of the track
   **/
  virtual TParticle* PopNextTrack(int32_t& iTrack);

  /** Get primary particle by index for tracking from stack
   ** Declared in TVirtualMCStack
   *@param  iPrim   index of primary particle
   *@return Pointer to the TParticle of the track
   **/
  virtual TParticle* PopPrimaryForTracking(int32_t iPrim);

  /** Set the current track number
   ** Declared in TVirtualMCStack
   *@param iTrack  track number
   **/
  virtual void SetCurrentTrack(int32_t iTrack) { fCurrentTrack = iTrack; }

  /** Get total number of tracks
   ** Declared in TVirtualMCStack
   **/
  virtual int32_t GetNtrack() const { return fNParticles; }

  /** Get number of primary tracks
   ** Declared in TVirtualMCStack
   **/
  virtual int32_t GetNprimary() const { return fNPrimaries; }

  /** Get the current track's particle
   ** Declared in TVirtualMCStack
   **/
  virtual TParticle* GetCurrentTrack() const;

  /** Get the number of the current track
   ** Declared in TVirtualMCStack
   **/
  virtual int32_t GetCurrentTrackNumber() const { return fCurrentTrack; }

  /** Get the track number of the parent of the current track
   ** Declared in TVirtualMCStack
   **/
  virtual int32_t GetCurrentParentTrackNumber() const;

  /** Add a TParticle to the fParticles array **/
  virtual void AddParticle(TParticle* part);

  /** Fill the MCTrack output array, applying filter criteria **/
  virtual void FillTrackArray();

  /** Update the track index in the MCTracks and MCPoints **/
  virtual void UpdateTrackIndex(TRefArray* detArray = 0);

  /** Resets arrays and stack and deletes particles and tracks **/
  virtual void Reset();

  /** Register the MCTrack array to the Root Manager  **/
  virtual void Register();

  /** Output to screen
   **@param iVerbose: 0=events summary, 1=track info
   **/
  virtual void Print(int32_t iVerbose = 0) const;

  /** Modifiers  **/
  void StoreSecondaries(bool choice = kTRUE) { fStoreSecondaries = choice; }
  void SetMinPoints(int32_t min) { fMinPoints = min; }
  void SetEnergyCut(double eMin) { fEnergyCut = eMin; }
  void StoreMothers(bool choice = kTRUE) { fStoreMothers = choice; }

  /** Increment number of points for the current track in a given detector
   *@param iDet  Detector unique identifier
   **/
  void AddPoint(DetectorId iDet);

  /** Increment number of points for an arbitrary track in a given detector
   *@param iDet    Detector unique identifier
   *@param iTrack  Track number
   **/
  void AddPoint(DetectorId iDet, int32_t iTrack);

  /** Accessors **/
  TParticle* GetParticle(int32_t trackId) const;
  TClonesArray* GetListOfParticles() { return fParticles; }

 private:
  /** STL stack (FILO) used to handle the TParticles for tracking **/
  std::stack<TParticle*> fStack;  //!

  /** Array of TParticles (contains all TParticles put into or created
   ** by the transport
   **/
  TClonesArray* fParticles;  //!

  /** Array of FairMCTracks containing the tracks written to the output **/
  std::vector<ShipMCTrack>* fTracks;

  /** STL map from particle index to storage flag  **/
  std::map<int32_t, bool> fStoreMap;             //!
  std::map<int32_t, bool>::iterator fStoreIter;  //!

  /** STL map from particle index to track index  **/
  std::map<int32_t, int32_t> fIndexMap;             //!
  std::map<int32_t, int32_t>::iterator fIndexIter;  //!

  /** STL map from track index and detector ID to number of MCPoints **/
  std::map<std::pair<int32_t, int32_t>, int32_t> fPointsMap;  //!

  /** Some indizes and counters **/
  int32_t fCurrentTrack;  //! Index of current track
  int32_t fNPrimaries;    //! Number of primary particles
  int32_t fNParticles;    //! Number of entries in fParticles
  int32_t fNTracks;       //! Number of entries in fTracks
  int32_t fIndex;         //! Used for merging

  /** Variables defining the criteria for output selection **/
  bool fStoreSecondaries;
  int32_t fMinPoints;
  Double32_t fEnergyCut;
  bool fStoreMothers;
  int32_t fNsplits;

  /** Mark tracks for output using selection criteria  **/
  void SelectTracks();

  ShipStack(const ShipStack&);
  ShipStack& operator=(const ShipStack&);

  ClassDef(ShipStack, 1)
};

#endif  // SHIPDATA_SHIPSTACK_H_
