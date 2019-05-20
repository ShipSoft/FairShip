#ifndef PNDmuGENERATOR_H
#define PNDmuGENERATOR_H 1

#include "TROOT.h"
#include "FairGenerator.h"
#include "TTree.h"                      // for TTree
#include "TClonesArray.h"               
#include "FairLogger.h"                 // for FairLogger, MESSAGE_ORIGIN

class FairPrimaryGenerator;

class MuonBackGenerator : public FairGenerator
{
 public:
  
  /** default constructor **/
  MuonBackGenerator();
  
  /** destructor **/
  virtual ~MuonBackGenerator();
  
  /** public method ReadEvent **/
  Bool_t ReadEvent(FairPrimaryGenerator*);  
  virtual Bool_t Init(const char*, int, const Bool_t fl); //!
  virtual Bool_t Init(const char*); //!
  Int_t GetNevents();//!
  void CloseFile();//!
  void SetPhiRandom(Bool_t fl) { fPhiRandomize = fl; };
  void FollowAllParticles() { followMuons = false; };
  void SetSmearBeam(Double_t sb) { fsmearBeam = sb; };
  void SetSameSeed(Int_t s) {
    LOG(INFO)<<TString::Format("Seed: %d", s)<< FairLogger::endl;
    fSameSeed = s;
  };
  Bool_t checkDiMuon(Int_t muIndex);
  void SetDownScaleDiMuon(){ fdownScaleDiMuon = kTRUE; };

private:
protected:
  Float_t id,parentid,pythiaid,w,px,py,pz,vx,vy,vz,ecut;
  TClonesArray* MCTrack; //!
  TClonesArray* vetoPoints; //!
  TFile* fInputFile;    //! 
  FairLogger*  fLogger; //!   don't make it persistent, magic ROOT command
  TTree* fTree;         //! 
  int fNevents;
  float f_zOffset;      //!
  int fn;
  Bool_t fPhiRandomize;
  Bool_t fdownScaleDiMuon;
  Bool_t followMuons;
  Int_t fSameSeed;
  Double_t fsmearBeam ;
  ClassDef(MuonBackGenerator,6);
};

#endif /* !PNDmuGENERATOR_H */
