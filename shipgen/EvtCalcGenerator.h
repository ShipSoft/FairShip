#ifndef SHIPGEN_EVTCALCGENERATOR_H_
#define SHIPGEN_EVTCALCGENERATOR_H_ 1

#include "FairGenerator.h"
#include "TFile.h"
#include "TTree.h"

#include <memory>

class FairPrimaryGenerator;

class EvtCalcGenerator : public FairGenerator
{
  public:
    /** default constructor **/
    EvtCalcGenerator();

    /** destructor **/
    virtual ~EvtCalcGenerator();

    /** public method ReadEvent **/
    Bool_t ReadEvent(FairPrimaryGenerator*);
    virtual Bool_t Init(const char*, int);   //!
    virtual Bool_t Init(const char*);        //!

    Int_t GetNevents() { return fNevents; }
    void SetPositions(Double_t zTa, Double_t zDV)
    {
        ztarget = zTa;        // units cm (midpoint)
        zDecayVolume = zDV;   // units cm (midpoint)
    }
    
    // Wrapper function declarations
    Double_t GetNdaughters(const std::unique_ptr<TTree>&) const;
    Double_t GetMotherPx(const std::unique_ptr<TTree>&) const;
    Double_t GetMotherPy(const std::unique_ptr<TTree>&) const;
    Double_t GetMotherPz(const std::unique_ptr<TTree>&) const;
    Double_t GetMotherE(const std::unique_ptr<TTree>&) const;
    Double_t GetVx(const std::unique_ptr<TTree>&) const;
    Double_t GetVy(const std::unique_ptr<TTree>&) const;
    Double_t GetVz(const std::unique_ptr<TTree>&) const;
    Double_t GetDecayProb(const std::unique_ptr<TTree>&) const;
    Double_t GetDauPx(const std::unique_ptr<TTree>&, int) const;
    Double_t GetDauPy(const std::unique_ptr<TTree>&, int) const;
    Double_t GetDauPz(const std::unique_ptr<TTree>&, int) const;
    Double_t GetDauE(const std::unique_ptr<TTree>&, int) const;
    Double_t GetDauPDG(const std::unique_ptr<TTree>&, int) const;
    
  private:
  protected:
      // Generalized branch access
    Double_t GetBranchValue(const std::unique_ptr<TTree>&, int) const;

    // Generalized daughter variable access
    Double_t GetDaughterValue(const std::unique_ptr<TTree>& tree, int, int) const;

    Double_t ztarget, zDecayVolume;
    std::unique_ptr<TFile> fInputFile;
    std::unique_ptr<TTree> fTree;
    std::vector<double> branchVars;

    enum class BranchIndices {
      MotherPx = 0,
      MotherPy = 1,
      MotherPz = 2,
      MotherE = 3,
      DecayProb = 6,
      Vx = 7,
      Vy = 8,
      Vz = 9
    };

    int fNevents;
    int fn;
    int nBranches;
    int Ndau;
    ClassDef(EvtCalcGenerator, 1);
};

#endif   // SHIPGEN_EVTCALCGENERATOR_H_

