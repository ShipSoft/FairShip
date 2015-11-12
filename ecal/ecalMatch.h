/* Matching for the calorimeter. Use photon or electron with maximum energy deposition in 3x3 cluster
 */
#ifndef ECALMATCH
#define ECALMATCH

#include "FairTask.h"

class TClonesArray;
class ecalStructure;

class ecalMatch : public FairTask
{
public:
  /** Standard constructor **/
  ecalMatch(const char* name, const Int_t verbose);
  /** Only to comply with frame work. **/
  ecalMatch();

  /** Should we use 3x3 cluster instead of 5x5 **/
  Int_t GetUse3x3() const {return fUse3x3;}
  void SetUse3x3(Int_t use3x3=0) {fUse3x3=use3x3;}

  /** Finish a task **/
  virtual void Finish();
  /** Exec a task **/
  virtual void Exec(Option_t* option, TClonesArray* reconstructed, TClonesArray* mctracks);
  /** Initialization **/
  virtual InitStatus Init();
  void InitPython(ecalStructure* str, TClonesArray* reconstructed, TClonesArray* mctracks);
  /** Destructor **/
  ~ecalMatch();
private:
  /** Current event **/
  Int_t fEv;
  /** Current reconstructed particle **/
  Int_t fN;
  /** Number of rejected clusters **/
  Int_t fRejected;
  /** Use 3x3 cluster instead of 5x5 **/
  Int_t fUse3x3;

  /** Array of reconstructed objects **/
  TClonesArray* fReconstucted;		//!
  /** Array of MC tracks **/
  TClonesArray* fMCTracks;		//!
  /** A calorimeter structure **/
  ecalStructure* fStr;			//!

  ClassDef(ecalMatch, 1)
};

#endif
