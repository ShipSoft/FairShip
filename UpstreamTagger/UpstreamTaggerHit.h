#ifndef UPSTREAMTAGGER_UPSTREAMTAGGERHIT_H_
#define UPSTREAMTAGGER_UPSTREAMTAGGERHIT_H_

#include "ShipHit.h"
#include "TVector3.h"

class UpstreamTaggerPoint;

/**
 * @brief Hit class for UpstreamTagger scoring plane
 *
 * Simple hit class for UBT scoring plane detector.
 * Stores smeared position and time from MC truth.
 * Does not store MC truth information directly.
 */
class UpstreamTaggerHit : public ShipHit
{
  public:
    /** Default constructor **/
    UpstreamTaggerHit();

    /** Constructor from UpstreamTaggerPoint
     * @param p     MC point
     * @param t0    Event time offset
     * @param pos_res Position resolution (cm)
     * @param time_res Time resolution (ns)
     **/
    UpstreamTaggerHit(UpstreamTaggerPoint* p, Double_t t0,
                      Double_t pos_res, Double_t time_res);

    /** Destructor **/
    virtual ~UpstreamTaggerHit();

    /** Copy constructor **/
    UpstreamTaggerHit(const UpstreamTaggerHit& hit) = default;
    UpstreamTaggerHit& operator=(const UpstreamTaggerHit& hit) = default;

    /** Position accessors **/
    Double_t GetX() const { return fX; }
    Double_t GetY() const { return fY; }
    Double_t GetZ() const { return fZ; }
    TVector3 GetXYZ() const { return TVector3(fX, fY, fZ); }

    /** Time accessor **/
    Double_t GetTime() const { return fTime; }

    /** Output to screen **/
    virtual void Print() const;

  private:
    Double_t fX;      ///< Smeared x position (cm)
    Double_t fY;      ///< Smeared y position (cm)
    Double_t fZ;      ///< Smeared z position (cm)
    Double_t fTime;   ///< Smeared time (ns)

    ClassDef(UpstreamTaggerHit, 2);
};

#endif  // UPSTREAMTAGGER_UPSTREAMTAGGERHIT_H_
