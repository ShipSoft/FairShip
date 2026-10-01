#ifndef SHIPDATA_ISTLPOINTCONTAINER_H_
#define SHIPDATA_ISTLPOINTCONTAINER_H_

#include <vector>

#include "RtypesCore.h"

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
   * @param indexMap Old (particle) track index to new (stored) track index,
   * indexed by old track index; -2 marks tracks that were not stored
   */
  virtual void UpdatePointTrackIndices(const std::vector<Int_t>& indexMap) = 0;

  virtual ~ISTLPointContainer() = default;
};

#endif  // SHIPDATA_ISTLPOINTCONTAINER_H_
