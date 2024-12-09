#ifndef PNDntGENERATOR_H
#define PNDntGENERATOR_H 1

#include "FairGenerator.h"
#include "FairLogger.h"   // for FairLogger, MESSAGE_ORIGIN
#include "TROOT.h"
#include "TTree.h"   // for TTree

class FairPrimaryGenerator;

class NtupleGenerator : public FairGenerator
{
  public:
    /** default constructor **/
    NtupleGenerator();

    /** destructor **/
    virtual ~NtupleGenerator();

    /** public method ReadEvent **/
    Bool_t ReadEvent(FairPrimaryGenerator*);
    virtual Bool_t Init(const char*, int);   //!
    virtual Bool_t Init(const char*);        //!
    Int_t GetNevents();

  private:
  protected:
    Int_t id, Nmeas, volid[500], procid[500], parentid;
    Float_t Ezero, tof;
    Double_t w;
    Float_t px[500], py[500], pz[500], vx[500], vy[500], vz[500];
    TFile* fInputFile;
    TTree* fTree;
    FairLogger* fLogger;   //!   don't make it persistent, magic ROOT command
    int fNevents;
    int fn;
    ClassDef(NtupleGenerator, 1);
};

#endif /* !PNDntGENERATOR_H */
