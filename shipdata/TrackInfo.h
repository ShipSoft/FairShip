// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN on behalf of the SHiP Collaboration

#ifndef SHIPDATA_TRACKINFO_H_
#define SHIPDATA_TRACKINFO_H_

#include "TObject.h"              //

#include "Rtypes.h"                     // for Double_t, Int_t, Double32_t, etc
#include "TVector.h"                   // for TVector
#include "Track.h"
#include <vector>

class TrackInfo : public TObject
{

  public:

    /** Default constructor **/
    TrackInfo();
    /**  Standard constructor  **/
        explicit TrackInfo(const genfit::Track* tr);

    /**  Copy constructor  **/
    TrackInfo(const TrackInfo& ti);

    /** Destructor **/
    virtual ~TrackInfo();

    /** Accessors **/
    unsigned int N() const {return fDetIDs.size();}
    unsigned int detId(Int_t n) const {return fDetIDs[n];}
    float wL(Int_t n) const {return fWL[n];}
    float wR(Int_t n) const {return fWR[n];}

    /*** Output to screen */
    virtual void Print(const Option_t* opt ="") const {;}

  protected:
    std::vector<unsigned int> fDetIDs;   ///< array of measurements
    std::vector<float> fWL;
    std::vector<float> fWR;
    ClassDef(TrackInfo,2);
};

#endif  // SHIPDATA_TRACKINFO_H_
