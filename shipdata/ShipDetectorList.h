// -------------------------------------------------------------------------
// -----                  ShipDetectorList header file                  -----
// -------------------------------------------------------------------------


/** Defines unique identifier for all FAIR detector systems **/

#ifndef ShipDetectorList_H
#define ShipDetectorList_H 1

// kSTOPHERE is needed for iteration over the enum. All detectors have to be put before.
enum DetectorId {kVETO, kecal,kMuon ,kTRSTATION};

#endif
