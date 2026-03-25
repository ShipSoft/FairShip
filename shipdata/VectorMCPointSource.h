// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SHIPDATA_VECTORMCPOINTSOURCE_H_
#define SHIPDATA_VECTORMCPOINTSOURCE_H_

#include "FairDataSourceI.h"
#include "FairRootManager.h"

/// Data source adapter that reads std::vector<PointType> branches
/// registered via FairRootManager::RegisterAny().
///
/// FairTCASource (the default) only supports TClonesArray branches.
/// Since FairShip migrated to RegisterAny with std::vector storage,
/// this adapter is needed for FairMCPointDraw to find the data.
template <typename PointType>
class VectorMCPointSource : public FairDataSourceI {
 public:
  VectorMCPointSource() = default;
  explicit VectorMCPointSource(TString branchName)
      : FairDataSourceI(branchName) {}

  InitStatus Init() override {
    fVec = FairRootManager::Instance()
               ->InitObjectAs<const std::vector<PointType>*>(
                   GetBranchName().Data());
    if (!fVec) {
      return kERROR;
    }
    return kSUCCESS;
  }

  int GetNData() override { return fVec ? fVec->size() : 0; }

  TObject* GetData(int index) override {
    return const_cast<PointType*>(&(*fVec)[index]);
  }

  double GetTime(int index) override { return (*fVec)[index].GetTime(); }

  void Reset() override {}

 private:
  const std::vector<PointType>* fVec = nullptr;
};

#endif  // SHIPDATA_VECTORMCPOINTSOURCE_H_
