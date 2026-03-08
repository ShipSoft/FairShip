#ifndef SHIPDATA_ISTLPOINTCONTAINER_H_
#define SHIPDATA_ISTLPOINTCONTAINER_H_

#include <map>
#include <vector>

#include "FairLink.h"

/**
 * @brief Interface for detectors using STL containers (std::vector) for MC
 * points
 *
 * Detectors migrated from TClonesArray to std::vector should implement this
 * interface to enable proper track index updating in ShipStack after track
 * filtering.
 */
class ISTLPointContainer {
 public:
  /**
   * @brief Update track indices in point collection after track filtering
   * @param indexMap Map from old (particle) track index to new (stored) track
   * index
   */
  virtual void UpdatePointTrackIndices(
      const std::map<Int_t, Int_t>& indexMap) = 0;

  virtual ~ISTLPointContainer() = default;
};

/// Reusable implementation of UpdatePointTrackIndices for any point type that
/// provides GetTrackID(), SetTrackID() and SetLink() (i.e. FairMCPoint
/// subclasses).
template <typename PointType>
void UpdatePointTrackIndicesImpl(std::vector<PointType>& points,
                                 const std::map<Int_t, Int_t>& indexMap) {
  for (auto& point : points) {
    Int_t oldTrackID = point.GetTrackID();
    auto iter = indexMap.find(oldTrackID);
    if (iter != indexMap.end()) {
      point.SetTrackID(iter->second);
      point.SetLink(FairLink("MCTrack", iter->second));
    }
  }
}

#endif  // SHIPDATA_ISTLPOINTCONTAINER_H_
