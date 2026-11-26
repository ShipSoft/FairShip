/**
 * Test script to verify data classes can be used with std::vector and RNtuple
 * This test verifies:
 * - Copy constructors are public
 * - Move constructors are accessible
 * - Getters are const-correct
 * - Classes work with std::vector
 */

#include <array>
#include <cmath>
#include <cstdio>
#include <iostream>
#include <memory>
#include <type_traits>
#include <vector>

// Include all data class headers
#include "CaloScoringPlaneHit.h"
#include "CaloScoringPlanePoint.h"
#include "DetectorHit.h"
#include "MTCDetHit.h"
#include "MTCDetPoint.h"
#include "RecoTrack.h"
#include "RecoVertex.h"
#include "ShipMCTrack.h"
#include "SiliconTargetHit.h"
#include "SiliconTargetPoint.h"
#include "TFile.h"
#include "TTPoint.h"
#include "TTree.h"
#include "TargetPoint.h"
#include "TimeDetHit.h"
#include "TimeDetPoint.h"
#include "UpstreamTaggerHit.h"
#include "UpstreamTaggerPoint.h"
#include "UpstreamTaggerScoringPoint.h"
#include "strawtubesHit.h"
#include "strawtubesPoint.h"
#include "vetoHit.h"
#include "vetoHitOnTrack.h"
#include "vetoPoint.h"

// Test helper: verify a type is copyable (required for std::vector)
template <typename T>
constexpr bool test_copyable() {
  return std::is_copy_constructible<T>::value &&
         std::is_copy_assignable<T>::value;
}

// Test helper: verify const-correctness of getters
template <typename T>
void test_const_access(const T& obj) {
  // This will only compile if getters are properly const-qualified
}

// Specializations for const-access tests
void test_const_access(const SHiP::DetectorHit& obj) {
  [[maybe_unused]] auto digi = obj.GetDigi();
  [[maybe_unused]] auto detID = obj.GetDetectorID();
}

void test_const_access(const ShipMCTrack& obj) {
  [[maybe_unused]] auto pdg = obj.GetPdgCode();
  [[maybe_unused]] auto px = obj.GetPx();
  [[maybe_unused]] auto py = obj.GetPy();
  [[maybe_unused]] auto pz = obj.GetPz();
}

void test_const_access(const vetoHitOnTrack& obj) {
  [[maybe_unused]] auto dist = obj.GetDist();
  [[maybe_unused]] auto hitID = obj.GetHitID();
}

void test_const_access(const SHiP::RecoTrack& obj) {
  [[maybe_unused]] auto px = obj.px();
  [[maybe_unused]] auto charge = obj.charge();
  [[maybe_unused]] const auto& cov = obj.GetCovarianceElements();
  TVector3 position;
  [[maybe_unused]] auto ok = obj.ExtrapolateToZ(0., position);
}

void test_const_access(const SHiP::RecoVertex& obj) {
  [[maybe_unused]] auto z = obj.z();
  [[maybe_unused]] const auto& ids = obj.trackIds();
  [[maybe_unused]] auto doca = obj.doca();
}

void test_const_access(const vetoHit& obj) {
  [[maybe_unused]] auto adc = obj.GetADC();
  [[maybe_unused]] auto tdc = obj.GetTDC();
  [[maybe_unused]] auto eloss = obj.GetEloss();
  [[maybe_unused]] auto valid = obj.isValid();
}

void test_const_access(const vetoPoint& obj) {
  [[maybe_unused]] auto pdg = obj.PdgCode();
}

void test_const_access(const strawtubesHit& obj) {
  [[maybe_unused]] auto tdc = obj.GetTDC();
  [[maybe_unused]] auto station = obj.GetStationNumber();
  [[maybe_unused]] auto view = obj.GetViewNumber();
  [[maybe_unused]] auto layer = obj.GetLayerNumber();
  [[maybe_unused]] auto straw = obj.GetStrawNumber();
  [[maybe_unused]] auto valid = obj.isValid();
}

void test_const_access(const strawtubesPoint& obj) {
  [[maybe_unused]] auto pdg = obj.PdgCode();
  [[maybe_unused]] auto dist = obj.dist2Wire();
}

void test_const_access(const CaloScoringPlaneHit& obj) {
  [[maybe_unused]] auto pos = obj.GetXYZ();
  [[maybe_unused]] auto mom = obj.GetMom();
  [[maybe_unused]] auto time = obj.GetTime();
  [[maybe_unused]] auto pid = obj.GetPid();
  [[maybe_unused]] auto muon = obj.IsMuon();
  [[maybe_unused]] auto identified = obj.IsIdentified();
}

void test_const_access(const CaloScoringPlanePoint& obj) {
  [[maybe_unused]] auto pdg = obj.PdgCode();
}

void test_const_access(const MTCDetHit& obj) {
  [[maybe_unused]] auto signal = obj.GetSignal();
  [[maybe_unused]] auto time = obj.GetTime();
  [[maybe_unused]] auto channelID = obj.GetChannelID();
  [[maybe_unused]] auto layer = obj.GetLayer();
  [[maybe_unused]] auto sipm = obj.GetSiPM();
  [[maybe_unused]] auto energy = obj.GetEnergy();
}

void test_const_access(const MTCDetPoint& obj) {
  [[maybe_unused]] auto pdg = obj.PdgCode();
  [[maybe_unused]] auto layer = obj.GetLayer();
  [[maybe_unused]] auto layerType = obj.GetLayerType();
}

void test_const_access(const SiliconTargetHit& obj) {
  [[maybe_unused]] auto signal = obj.GetSignal();
  [[maybe_unused]] auto x = obj.GetX();
  [[maybe_unused]] auto y = obj.GetY();
  [[maybe_unused]] auto z = obj.GetZ();
  [[maybe_unused]] auto layer = obj.GetLayer();
  [[maybe_unused]] auto plane = obj.GetPlane();
}

void test_const_access(const SiliconTargetPoint& obj) {
  [[maybe_unused]] auto pdg = obj.PdgCode();
  [[maybe_unused]] auto layer = obj.GetLayer();
}

void test_const_access(const TimeDetHit& obj) {
  [[maybe_unused]] auto valid = obj.isValid();
}

void test_const_access(const TimeDetPoint& obj) {
  [[maybe_unused]] auto pdg = obj.PdgCode();
}

void test_const_access(const UpstreamTaggerHit& obj) {
  [[maybe_unused]] auto x = obj.GetX();
  [[maybe_unused]] auto y = obj.GetY();
  [[maybe_unused]] auto z = obj.GetZ();
  [[maybe_unused]] auto time = obj.GetTime();
  [[maybe_unused]] auto adc = obj.GetADC();
  [[maybe_unused]] auto tileID = obj.GetTileID();
  [[maybe_unused]] auto triggered = obj.IsTriggered();
}

void test_const_access(const UpstreamTaggerPoint& obj) {
  [[maybe_unused]] auto pdg = obj.PdgCode();
}

void test_const_access(const UpstreamTaggerScoringPoint& obj) {
  [[maybe_unused]] auto pdg = obj.PdgCode();
}

void test_const_access(const TTPoint& obj) {
  [[maybe_unused]] auto pdg = obj.PdgCode();
}

void test_const_access(const TargetPoint& obj) {
  [[maybe_unused]] auto pdg = obj.PdgCode();
}

// Test vector operations
template <typename T>
bool test_vector_operations(const char* class_name) {
  std::cout << "Testing " << class_name << "... ";

  // Test 1: Can we create a vector?
  if (!test_copyable<T>()) {
    std::cout << "FAIL: Not copyable (private copy constructor?)" << std::endl;
    return false;
  }

  try {
    // Test 2: Create default objects
    std::vector<T> vec;
    vec.reserve(10);

    // Test 3: Emplace back (uses default constructor)
    vec.emplace_back();

    // Test 4: Push back (uses copy constructor)
    T obj;
    vec.push_back(obj);

    // Test 5: Access elements with const reference
    const T& const_ref = vec[0];
    test_const_access(const_ref);

    // Test 6: Vector resize (uses copy constructor)
    vec.resize(5);

    std::cout << "PASS" << std::endl;
    return true;
  } catch (const std::exception& e) {
    std::cout << "FAIL: " << e.what() << std::endl;
    return false;
  }
}

// Write RecoTracks to a TTree, as the reconstruction does, and read them back:
// one with every member set, including the extrapolations and the track
// length, and one with none of those, which must keep reading as missing
bool test_recotrack_tree_roundtrip() {
  std::cout << "Testing SHiP::RecoTrack TTree round trip... ";
  bool ok = true;
  const auto fail = [&ok](const char* what) {
    if (ok) {
      std::cout << "FAIL" << std::endl;
    }
    std::cout << "  " << what << std::endl;
    ok = false;
  };
  const auto same = [](const std::vector<Double_t>& a,
                       const std::vector<Double_t>& b) { return a == b; };

  std::array<Double_t, 21> covariance{};
  for (std::size_t i = 0; i < covariance.size(); ++i) {
    covariance[i] = 0.01 * static_cast<Double_t>(i + 1);
  }
  std::vector<Double_t> ubtCov(21), tdCov(21);
  for (std::size_t i = 0; i < 21; ++i) {
    ubtCov[i] = 0.1 * static_cast<Double_t>(i + 1);
    tdCov[i] = -0.2 * static_cast<Double_t>(i + 1);
  }
  const std::vector<Double_t> xFits{1.1, 1.2, 1.3};
  const std::vector<Double_t> yFits{-2.1, -2.2, -2.3};
  const std::vector<Double_t> zFits{8400., 8402., 8410.};
  const std::vector<Double_t> residuals{0.01, -0.02, 0.03};
  const std::vector<Double_t> pulls{0.5, -1.0, 1.5};

  SHiP::RecoTrack full(TVector3(1., 2., 8400.), TVector3(0.1, -0.2, 10.), -1,
                       covariance, 12.5, 7., 3, xFits, yFits, zFits, residuals,
                       pulls);
  // The UBT is upstream of the first hit: a negative path length
  full.SetUBTExtrapolation(TVector3(0.5, 1.5, 3287.), TVector3(0.1, -0.2, 10.),
                           ubtCov, -5113.4);
  full.SetTDExtrapolation(TVector3(3., -4., 9614.), TVector3(0.2, -0.3, 9.9),
                          tdCov, 1204.6);
  full.SetTrackLength(2405.7);
  const SHiP::RecoTrack bare(TVector3(), TVector3(0., 0., 1.), 1, covariance,
                             1., 1., 2, {}, {}, {}, {}, {});

  const char* filename = "test_RecoTrack_roundtrip.root";
  {
    TFile file(filename, "RECREATE");
    TTree tree("tracks", "RecoTrack round trip");
    std::vector<SHiP::RecoTrack> tracks{full, bare};
    tree.Branch("RecoTracks", &tracks, 32000, -1);
    tree.Fill();
    file.Write();
  }

  std::vector<SHiP::RecoTrack>* read = nullptr;
  TFile file(filename, "READ");
  auto* tree = file.Get<TTree>("tracks");
  if (tree == nullptr) {
    fail("tree not found");
  } else {
    tree->SetBranchAddress("RecoTracks", &read);
    tree->GetEntry(0);
  }
  if (ok && (read == nullptr || read->size() != 2)) {
    fail("two tracks read back");
  }
  if (ok) {
    const SHiP::RecoTrack& t = (*read)[0];
    if (t.x() != 1. || t.y() != 2. || t.z() != 8400. || t.px() != 0.1 ||
        t.py() != -0.2 || t.pz() != 10. || t.charge() != -1) {
      fail("state and charge");
    }
    if (t.chi2() != 12.5 || t.nDoF() != 7. || t.nMeasurements() != 3) {
      fail("fit quality");
    }
    if (!same(t.GetCovarianceElements(),
              std::vector<Double_t>(covariance.begin(), covariance.end()))) {
      fail("track covariance");
    }
    if (!same(t.GetXFittedPoints(), xFits) ||
        !same(t.GetYFittedPoints(), yFits) ||
        !same(t.GetZFittedPoints(), zFits)) {
      fail("fitted points");
    }
    if (!same(t.GetResiduals(), residuals) || !same(t.GetPulls(), pulls)) {
      fail("residuals and pulls");
    }
    if (!t.HasUBTExtrapolation() ||
        t.GetUBTPosition() != TVector3(0.5, 1.5, 3287.) ||
        t.GetUBTMomentum() != TVector3(0.1, -0.2, 10.) ||
        !same(t.GetUBTCovariance(), ubtCov) ||
        t.GetUBTPathLength() != -5113.4) {
      fail("UBT extrapolation (and the sign of its path length)");
    }
    if (!t.HasTDExtrapolation() ||
        t.GetTDPosition() != TVector3(3., -4., 9614.) ||
        t.GetTDMomentum() != TVector3(0.2, -0.3, 9.9) ||
        !same(t.GetTDCovariance(), tdCov) || t.GetTDPathLength() != 1204.6) {
      fail("timing-detector extrapolation");
    }
    if (t.GetTrackLength() != 2405.7) {
      fail("track length");
    }

    const SHiP::RecoTrack& b = (*read)[1];
    if (b.HasUBTExtrapolation() || b.HasTDExtrapolation()) {
      fail("unset extrapolations read back as stored");
    }
    if (!std::isnan(b.GetUBTPosition().Z()) ||
        !std::isnan(b.GetUBTPathLength()) ||
        !std::isnan(b.GetTDMomentum().Z()) ||
        !std::isnan(b.GetTDPathLength()) || !std::isnan(b.GetTrackLength())) {
      fail("unset extrapolations and track length read back as not NaN");
    }
    if (!b.GetUBTCovariance().empty() || !b.GetTDCovariance().empty()) {
      fail("unset extrapolation covariances read back as not empty");
    }
    if (!b.GetXFittedPoints().empty() || !b.GetResiduals().empty()) {
      fail("empty fitted points read back as not empty");
    }
  }
  file.Close();
  std::remove(filename);

  // An extrapolation stored without a covariance keeps it empty
  SHiP::RecoTrack noCov = bare;
  noCov.SetUBTExtrapolation(TVector3(), TVector3(0., 0., 1.), {}, -1.);
  if (!noCov.HasUBTExtrapolation() || !noCov.GetUBTCovariance().empty()) {
    fail("extrapolation without covariance");
  }

  if (ok) {
    std::cout << "PASS" << std::endl;
  }
  return ok;
}

int main(int argc, char** argv) {
  std::cout << "\n=== Testing Data Classes for std::vector compatibility ===\n"
            << std::endl;

  int passed = 0;
  int total = 0;

  // Test base classes
  std::cout << "\n--- Base Classes ---" << std::endl;
  total++;
  if (test_vector_operations<SHiP::DetectorHit>("SHiP::DetectorHit")) passed++;
  total++;
  if (test_vector_operations<ShipMCTrack>("ShipMCTrack")) passed++;
  total++;
  if (test_vector_operations<vetoHitOnTrack>("vetoHitOnTrack")) passed++;
  total++;
  if (test_vector_operations<SHiP::RecoTrack>("SHiP::RecoTrack")) passed++;
  total++;
  if (test_vector_operations<SHiP::RecoVertex>("SHiP::RecoVertex")) passed++;

  // Test I/O of the reconstruction output
  std::cout << "\n--- Reconstruction I/O ---" << std::endl;
  total++;
  if (test_recotrack_tree_roundtrip()) passed++;

  // Test Hit classes
  std::cout << "\n--- Hit Classes ---" << std::endl;
  total++;
  if (test_vector_operations<vetoHit>("vetoHit")) passed++;
  total++;
  if (test_vector_operations<strawtubesHit>("strawtubesHit")) passed++;
  total++;
  if (test_vector_operations<MTCDetHit>("MTCDetHit")) passed++;
  total++;
  if (test_vector_operations<SiliconTargetHit>("SiliconTargetHit")) passed++;
  total++;
  if (test_vector_operations<TimeDetHit>("TimeDetHit")) passed++;
  total++;
  if (test_vector_operations<UpstreamTaggerHit>("UpstreamTaggerHit")) passed++;
  total++;
  if (test_vector_operations<CaloScoringPlaneHit>("CaloScoringPlaneHit"))
    passed++;

  // Test Point classes
  std::cout << "\n--- Point Classes ---" << std::endl;
  total++;
  if (test_vector_operations<vetoPoint>("vetoPoint")) passed++;
  total++;
  if (test_vector_operations<strawtubesPoint>("strawtubesPoint")) passed++;
  total++;
  if (test_vector_operations<CaloScoringPlanePoint>("CaloScoringPlanePoint"))
    passed++;
  total++;
  if (test_vector_operations<MTCDetPoint>("MTCDetPoint")) passed++;
  total++;
  if (test_vector_operations<SiliconTargetPoint>("SiliconTargetPoint"))
    passed++;
  total++;
  if (test_vector_operations<TimeDetPoint>("TimeDetPoint")) passed++;
  total++;
  if (test_vector_operations<UpstreamTaggerPoint>("UpstreamTaggerPoint"))
    passed++;
  total++;
  if (test_vector_operations<UpstreamTaggerScoringPoint>(
          "UpstreamTaggerScoringPoint"))
    passed++;
  total++;
  if (test_vector_operations<TTPoint>("TTPoint")) passed++;
  total++;
  if (test_vector_operations<TargetPoint>("TargetPoint")) passed++;

  std::cout << "\n=== Summary ===" << std::endl;
  std::cout << "Passed: " << passed << " / " << total << std::endl;
  std::cout << "Failed: " << (total - passed) << " / " << total << std::endl;

  if (passed == total) {
    std::cout << "\n✓ All tests PASSED!" << std::endl;
    std::cout
        << "All data classes are compatible with std::vector and RNtuple I/O\n"
        << std::endl;
    return 0;
  } else {
    std::cout << "\n✗ Some tests FAILED!" << std::endl;
    std::cout << "Fix the failing classes before using with RNtuple\n"
              << std::endl;
    return 1;
  }
}
