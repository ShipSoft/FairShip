// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SHIPGEN_TTREEGENERATOR_H_
#define SHIPGEN_TTREEGENERATOR_H_

#include "FairPrimaryGenerator.h"
#include "Generator.h"
#include "TFile.h"
#include "TString.h"
#include "TTree.h"
#include "TLeaf.h"


class FloatOrDouble {
public:

    explicit FloatOrDouble(double init = 0.0) { set(init); }

    FloatOrDouble(TTree* tree, const char* name, double init = 0.0) : FloatOrDouble(init) {
        attach(tree, name);
    }

    void attach(TTree* tree, const char* name) {
        TLeaf* leaf = tree->GetLeaf(name);
        if (!leaf) throw std::runtime_error(std::string("No leaf ") + name);
        const std::string type = leaf->GetTypeName();
        if (type == "Float_t")       { isFloat_ = true;  tree->SetBranchAddress(name, &f_); }
        else if (type == "Double_t") { isFloat_ = false; tree->SetBranchAddress(name, &d_); }
        else throw std::runtime_error("Unsupported type " + type + " for " + name);
    }


    // ROOT stores the address of f_/d_, so the object must never move
    FloatOrDouble(const FloatOrDouble&) = delete;
    FloatOrDouble& operator=(const FloatOrDouble&) = delete;
    void set(double v) {
        f_ = static_cast<float>(v);
        d_ = v;
    }
    FloatOrDouble& operator=(double v) { set(v); return *this; }
    double get() const { return isFloat_ ? f_ : d_; }
    operator double() const { return get(); }

private:
    float  f_ = 0.f;
    double d_ = 0.0;
    bool   isFloat_ = false;
};

class FairPrimaryGenerator;

namespace SHiP {

/**
 * @class TTreeGenerator
 * @brief A FairRoot generator that reads particle data from ROOT TTrees
 *
 * The expected TTree structure contains the following branches:
 * - px, py, pz: Particle momentum components (GeV/c)
 * - x, y, z: Particle position coordinates (cm)
 * - id: PDG particle identification code
 * - w: Event weight factor
 */
class TTreeGenerator : public Generator {
 public:
  TTreeGenerator();
  ~TTreeGenerator() override;

  using Generator::Init;
  Bool_t Init(const char* fileName, int startEvent) override;
  Bool_t Init(const char* fileName) override;
  Bool_t ReadEvent(FairPrimaryGenerator* primGen) override;

  Long64_t GetNEvents() const { return fNEvents; }
  Long64_t GetCurrentEvent() const { return fCurrentEvent; }
  void SetTreeName(const char* treeName) { fTreeName = treeName; }

 private:
  TFile* fInputFile;  //!< Input ROOT file pointer
  TTree* fInputTree;  //!< Input TTree pointer
  TString fTreeName;  //!< Name of the TTree to read

  Long64_t fNEvents;       //!< Total number of events in the tree
  Long64_t fCurrentEvent;  //!< Current event index (0-based)

  FloatOrDouble fPx;      //!< Particle momentum x-component (GeV/c)
  FloatOrDouble fPy;      //!< Particle momentum y-component (GeV/c)
  FloatOrDouble fPz;      //!< Particle momentum z-component (GeV/c)
  FloatOrDouble fX;       //!< Particle position x-coordinate (cm)
  FloatOrDouble fY;       //!< Particle position y-coordinate (cm)
  FloatOrDouble fZ;       //!< Particle position z-coordinate (cm)
  Int_t fPdgId;      //!< PDG particle identification code
  FloatOrDouble fWeight;  //!< Event weight factor

  Bool_t InitBranches();
};

}  // namespace SHiP

#endif  // SHIPGEN_TTREEGENERATOR_H_
