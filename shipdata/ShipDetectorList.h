// -------------------------------------------------------------------------A
// -----                  ShipDetectorList header file                  -----
// -------------------------------------------------------------------------


/** Defines unique identifier for all FAIR detector systems **/

#ifndef ShipDetectorList_H
#define ShipDetectorList_H 1

// kSTOPHERE is needed for iteration over the enum. All detectors have to be put before.
 enum DetectorId {kEmulsionDet,kLHCScifi,kMuFilter, kVETO, kTimeDet, ktauRpc, ktauHpt, ktauTT, ktauTarget, kStraw, kecal, khcal, kMuon , kPreshower, kTRSTATION, kSplitCal, kBox1, kSpectrometer\
			  , kPixelModules, kSciFi, kScintillator, kMufluxSpectrometer, kMuonTagger, kUpstreamTagger, kEndOfList};
// last one for UpstreamTagger, then last five for muonflux and Charm measurement, first three for ship@lhc
#endif
