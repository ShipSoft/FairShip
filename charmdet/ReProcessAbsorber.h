#ifndef PNDreGENERATOR_H
#define PNDreGENERATOR_H 1

#include "FairGenerator.h"
#include "FairLogger.h"   // for FairLogger, MESSAGE_ORIGIN
#include "TROOT.h"
#include "TTree.h"   // for TTree

class FairPrimaryGenerator;

class ReProcessAbsorber : public FairGenerator
{
  public:
    /** default constructor **/
    ReProcessAbsorber();

    /** destructor **/
    virtual ~ReProcessAbsorber();

    /** public method ReadEvent **/
    Bool_t ReadEvent(FairPrimaryGenerator*);
    void SetZposition(Double_t z) { fZ = z; };
    virtual Bool_t Init(const char*);   //!
    Int_t GetNevents();

  private:
  protected:
    Float_t fZ;
    TFile* fInputFile;
    TTree* fTree;
    FairLogger* fLogger;   //!   don't make it persistent, magic ROOT command
    int fNevents;
    int fn;
    Float_t muMass;
    TClonesArray* FitTracks;   //!
    ClassDef(ReProcessAbsorber, 1);
};

#endif /* !PNDntGENERATOR_H */
