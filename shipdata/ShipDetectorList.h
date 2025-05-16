// -------------------------------------------------------------------------
// -----                  ShipDetectorList header file                  -----
// -------------------------------------------------------------------------

/** Defines unique identifier for all SHiP detector systems **/

#ifndef SHIPDATA_SHIPDETECTORLIST_H_
#define SHIPDATA_SHIPDETECTORLIST_H_ 1

// kSTOPHERE is needed for iteration over the enum. All detectors have to be put before.
enum DetectorId
{
    kVETO,
    kTimeDet,
    ktauRpc,
    ktauHpt,
    kMTC,
    ktauTT,
    ktauTarget,
    kStraw,
    kecal,
    khcal,
    kMuon,
    kPreshower,
    kTRSTATION,
    kSplitCal,
    kBox1,
    kSpectrometer,
    kPixelModules,
    kSciFi,
    kScintillator,
    kMufluxSpectrometer,
    kMuonTagger,
    kUpstreamTagger,
    kEndOfList
};
// last five for muonflux and Charm measurement
#endif   // SHIPDATA_SHIPDETECTORLIST_H_
