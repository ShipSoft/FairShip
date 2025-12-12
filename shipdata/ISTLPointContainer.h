#ifndef SHIPDATA_ISTLPOINTCONTAINER_H_
#define SHIPDATA_ISTLPOINTCONTAINER_H_

#include <map>

/**
 * @brief Interface for detectors using STL containers (std::vector) for MC points
 *
 * Detectors migrated from TClonesArray to std::vector should implement this interface
 * to enable proper track index updating in ShipStack after track filtering.
 */
class ISTLPointContainer {
public:
    /**
     * @brief Update track indices in point collection after track filtering
     * @param indexMap Map from old (particle) track index to new (stored) track index
     */
    virtual void UpdatePointTrackIndices(const std::map<Int_t, Int_t>& indexMap) = 0;

    virtual ~ISTLPointContainer() = default;
};

#endif  // SHIPDATA_ISTLPOINTCONTAINER_H_
