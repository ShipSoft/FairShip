// -------------------------------------------------------------------------
// -----                  ShipDetectorList header file                  -----
// -------------------------------------------------------------------------


/** Defines unique identifier for all FAIR detector systems **/

#ifndef ShipDetectorList_H
#define ShipDetectorList_H 1

// kSTOPHERE is needed for iteration over the enum. All detectors have to be put before.
enum DetectorId {kVETO, ktauRpc, ktauHpt, ktauTT, ktauTarget, kStraw, kecal, khcal, kMuon ,kPreshower,kTRSTATION, kBox1, kSpectrometer, kMuonTagger};
                                                                                                                // last three for Charm detector only
#endif
