#ifndef SHIPGEN_MUONBACKGENERATOR_H_
#define SHIPGEN_MUONBACKGENERATOR_H_ 1

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
  virtual Bool_t Init(const char*, int);   //!
  virtual Bool_t Init(const char*); //!
  Int_t GetNevents();//!
  void CloseFile();   //!
  void FollowAllParticles() { followMuons = false; };
  void SetSmearBeam(Double_t sb) { fsmearBeam = sb; };
  void SetPaintRadius(Double_t r) { fPaintBeam = r; };
  void SetSameSeed(Int_t s) {
    LOGF(info, "Seed: %d", s);
    fSameSeed = s;
  };
  void SetPhiRandomize(Bool_t phiRandomize) { fPhiRandomize = phiRandomize; };
  Bool_t checkDiMuon(Int_t muIndex);
  void SetDownScaleDiMuon(){ fdownScaleDiMuon = kTRUE; };

private:
protected:
  Float_t id,parentid,pythiaid,w,px,py,pz,vx,vy,vz,ecut;
  TClonesArray* MCTrack; //!
  TClonesArray* vetoPoints; //!
  TFile* fInputFile;    //!
  TTree* fTree;         //!
  int fNevents;
  float f_zOffset;      //!
  int fn;
  Bool_t fPhiRandomize;
  Double_t fPaintBeam;
  Bool_t fdownScaleDiMuon;
  Bool_t followMuons;
  Int_t fSameSeed;
  Double_t fsmearBeam ;
  ClassDef(MuonBackGenerator,6);
};

#endif  // SHIPGEN_MUONBACKGENERATOR_H_ /* !PNDmuGENERATOR_H */
