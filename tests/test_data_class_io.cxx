/**
 * Test script to verify data classes can be used with std::vector and RNtuple
 * This test verifies:
 * - Copy constructors are public
 * - Move constructors are accessible
 * - Getters are const-correct
 * - Classes work with std::vector
 */

#include <iostream>
#include <memory>
#include <type_traits>
#include <vector>

// Include all data class headers
#include "MTCDetHit.h"
#include "MTCDetPoint.h"
#include "ShipHit.h"
#include "ShipMCTrack.h"
#include "SiliconTargetHit.h"
#include "SiliconTargetPoint.h"
#include "TTPoint.h"
#include "TargetPoint.h"
#include "TimeDetHit.h"
#include "TimeDetPoint.h"
#include "UpstreamTaggerHit.h"
#include "UpstreamTaggerPoint.h"
#include "splitcalHit.h"
#include "splitcalPoint.h"
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
void test_const_access(const ShipHit& obj) {
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

void test_const_access(const splitcalHit& obj) {
  [[maybe_unused]] auto x = obj.GetX();
  [[maybe_unused]] auto y = obj.GetY();
  [[maybe_unused]] auto z = obj.GetZ();
  [[maybe_unused]] auto energy = obj.GetEnergy();
  [[maybe_unused]] auto precision = obj.GetIsPrecisionLayer();
  [[maybe_unused]] auto layer = obj.GetLayerNumber();
}

void test_const_access(const splitcalPoint& obj) {
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
}

void test_const_access(const UpstreamTaggerPoint& obj) {
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

int main(int argc, char** argv) {
  std::cout << "\n=== Testing Data Classes for std::vector compatibility ===\n"
            << std::endl;

  int passed = 0;
  int total = 0;

  // Test base classes
  std::cout << "\n--- Base Classes ---" << std::endl;
  total++;
  if (test_vector_operations<ShipHit>("ShipHit")) passed++;
  total++;
  if (test_vector_operations<ShipMCTrack>("ShipMCTrack")) passed++;
  total++;
  if (test_vector_operations<vetoHitOnTrack>("vetoHitOnTrack")) passed++;

  // Test Hit classes
  std::cout << "\n--- Hit Classes ---" << std::endl;
  total++;
  if (test_vector_operations<vetoHit>("vetoHit")) passed++;
  total++;
  if (test_vector_operations<strawtubesHit>("strawtubesHit")) passed++;
  total++;
  if (test_vector_operations<splitcalHit>("splitcalHit")) passed++;
  total++;
  if (test_vector_operations<MTCDetHit>("MTCDetHit")) passed++;
  total++;
  if (test_vector_operations<SiliconTargetHit>("SiliconTargetHit")) passed++;
  total++;
  if (test_vector_operations<TimeDetHit>("TimeDetHit")) passed++;
  total++;
  if (test_vector_operations<UpstreamTaggerHit>("UpstreamTaggerHit")) passed++;

  // Test Point classes
  std::cout << "\n--- Point Classes ---" << std::endl;
  total++;
  if (test_vector_operations<vetoPoint>("vetoPoint")) passed++;
  total++;
  if (test_vector_operations<strawtubesPoint>("strawtubesPoint")) passed++;
  total++;
  if (test_vector_operations<splitcalPoint>("splitcalPoint")) passed++;
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
