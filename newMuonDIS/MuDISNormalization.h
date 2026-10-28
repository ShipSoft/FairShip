// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef NEWMUONDIS_MUDISNORMALIZATION_H_
#define NEWMUONDIS_MUDISNORMALIZATION_H_

#include <cmath>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

#include "TChain.h"
#include "TFile.h"
#include "TList.h"
#include "TNamed.h"
#include "TParameter.h"
#include "TTree.h"
#include "TUUID.h"

namespace ShipMuDIS {

// Only standard ROOT objects are persisted, in TTree::GetUserInfo(). Each
// invocation has an immutable UUID, allowing ancestors shared by split jobs
// to be carried unchanged and counted only once when outputs are combined.
class Normalization {
 public:
  explicit Normalization(const char* stage = "NewMuDISGenerator") {
    Reset(stage);
  }

  void Reset(const char* stage) {
    fRecords.Delete();
    fRecords.SetOwner(kTRUE);
    fRecords.SetName("muDIS_normalization");
    fComplete = std::string(stage) == "prepareEvents";
    auto* record = new TList;
    record->SetOwner(kTRUE);
    record->SetName(TUUID().AsString());
    record->Add(new TNamed("stage", stage));
    fCount = new TParameter<Long64_t>("input_muons", 0);
    fSum = new TParameter<double>("sum_weights", 0.);
    fSquares = new TParameter<double>("sum_weights_squared", 0.);
    record->Add(fCount);
    record->Add(fSum);
    record->Add(fSquares);
    fRecords.Add(record);
  }

  void Add(double weight) {
    if (!std::isfinite(weight) || !std::isfinite(weight * weight))
      throw std::runtime_error("Nonfinite input muon normalization weight");
    fCount->SetVal(fCount->GetVal() + 1);
    fSum->SetVal(fSum->GetVal() + weight);
    fSquares->SetVal(fSquares->GetVal() + weight * weight);
  }

  void ImportFiles(const std::vector<std::string>& paths,
                   const std::string& treename) {
    fComplete = !paths.empty();
    for (const auto& path : paths) {
      TDirectory::TContext context;
      std::unique_ptr<TFile> file(TFile::Open(path.c_str(), "READ"));
      if (!file || file->IsZombie())
        throw std::runtime_error("Cannot read normalization input: " + path);
      auto* tree = file->Get<TTree>(treename.c_str());
      auto* records =
          tree ? dynamic_cast<TList*>(
                     tree->GetUserInfo()->FindObject("muDIS_normalization"))
               : nullptr;
      auto* complete = records
                           ? dynamic_cast<TParameter<int>*>(
                                 records->FindObject("preparation_complete"))
                           : nullptr;
      fComplete = fComplete && complete && complete->GetVal() == 1;
      if (!records) continue;  // Legacy inputs remain usable without scaling.
      for (auto* object : *records) {
        auto* record = dynamic_cast<TList*>(object);
        if (!record) continue;
        auto* stage = dynamic_cast<TNamed*>(record->FindObject("stage"));
        if (!stage) throw std::runtime_error("Missing normalization stage");
        const auto count = Value<Long64_t>(*record, "input_muons");
        const auto sum = Value<double>(*record, "sum_weights");
        const auto squares = Value<double>(*record, "sum_weights_squared");
        if (count < 0 || !std::isfinite(sum) || !std::isfinite(squares) ||
            squares < 0.)
          throw std::runtime_error("Invalid normalization record");
        if (auto* previous =
                dynamic_cast<TList*>(fRecords.FindObject(record->GetName()))) {
          if (Value<Long64_t>(*previous, "input_muons") != count ||
              Value<double>(*previous, "sum_weights") != sum ||
              Value<double>(*previous, "sum_weights_squared") != squares ||
              std::string(previous->FindObject("stage")->GetTitle()) !=
                  stage->GetTitle())
            throw std::runtime_error("Conflicting normalization record UUID");
        } else {
          fRecords.Add(record->Clone());
        }
      }
    }
  }

  void ImportChain(TChain* chain) {
    std::vector<std::string> paths;
    for (auto* file : *chain->GetListOfFiles())
      paths.emplace_back(file->GetTitle());
    ImportFiles(paths, chain->GetName());
  }

  void Attach(TTree* tree) const {
    if (!tree || tree->GetUserInfo()->FindObject("muDIS_normalization"))
      throw std::runtime_error(
          "Normalization requires a tree without existing metadata");
    auto* records = static_cast<TList*>(fRecords.Clone());
    records->SetOwner(kTRUE);
    records->Add(new TParameter<int>("version", 1));
    records->Add(
        new TParameter<int>("preparation_complete", fComplete ? 1 : 0));
    tree->GetUserInfo()->Add(records);
  }

 private:
  template <typename T>
  static T Value(const TList& record, const char* name) {
    auto* parameter = dynamic_cast<TParameter<T>*>(record.FindObject(name));
    if (!parameter)
      throw std::runtime_error(std::string("Missing normalization field: ") +
                               name);
    return parameter->GetVal();
  }

  TList fRecords;
  TParameter<Long64_t>* fCount = nullptr;
  TParameter<double>* fSum = nullptr;
  TParameter<double>* fSquares = nullptr;
  bool fComplete = false;
};

}  // namespace ShipMuDIS

#endif  // NEWMUONDIS_MUDISNORMALIZATION_H_
