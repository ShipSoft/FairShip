#include "MtcDetHit.h"

#include "FairRunSim.h"
#include "MTCDetector.h"
#include "MtcDetPoint.h"
#include "TGeoBBox.h"
#include "TGeoManager.h"
#include "TGeoNavigator.h"
#include "TROOT.h"

#include <TRandom.h>
#include <iomanip>

namespace
{
// parameters for simulating the digitized information
const Float_t ly_loss_params[4] = {20., 300.};                       // x_0, lambda
const Float_t npix_to_qdc_params[4] = {0.172, -1.31, 0.006, 0.33};   // A, B, sigma_A, sigma_B
}   // namespace

// -----   Default constructor   -------------------------------------------
MtcDetHit::MtcDetHit()
    : ShipHit()
{
    flag = true;
}

// Optimized MtcDetHit Constructor

MtcDetHit::MtcDetHit(int SiPMChan, const std::vector<MtcDetPoint*>& points, const std::vector<Float_t>& weights)
{
    // Retrieve detector once
    static auto* MTCDet = dynamic_cast<MTCDetector*>(gROOT->GetListOfGlobals()->FindObject("MTC"));

    // Constants
    constexpr Float_t kNpheMin = 3.5f;
    constexpr Float_t kNpheMax = 104.0f;
    constexpr Float_t kTimeRes = 150e-3f;     // 150 ps
    constexpr Float_t kSignalSpeed = 15.0f;   // cm/ns
    const Float_t invSignalSpeed = 1.0f / kSignalSpeed;
    fDetectorID = SiPMChan;   // Set the detector ID
    // Determine plane type once
    const int plane_type = GetStationType();

    Float_t totalLy = 0.0f;
    Float_t earliestToA = std::numeric_limits<Float_t>::max();
    Float_t signalSum = 0.0f;
    bool hitFlag = false;

    // Separate handling for scintillating mat (plane_type == 2)
    if (plane_type == 2) {
        for (auto* pt : points) {
            signalSum += pt->GetEnergyLoss();
        }
        flag = true;
        signals = signalSum;
        return;
    }

    // Fiber hit processing
    const size_t n = points.size();
    totalLy = 0.0f;

    TVector3 sipmA, sipmB;
    MTCDet->GetSiPMPosition(SiPMChan, sipmA, sipmB);

    for (size_t i = 0; i < n; ++i) {
        auto* pt = points[i];
        Float_t energy = pt->GetEnergyLoss();
        Float_t weight = weights[i];
        Float_t signal = energy * weight;

        // Distance from deposit to SiPM
        TVector3 impact(pt->GetX(), pt->GetY(), pt->GetZ());
        const Float_t distance = (sipmB - impact).Mag();

        // Light yield before attenuation
        Float_t ly = signal * 1e6f * 0.16f;
        ly *= ly_loss(distance);
        totalLy += ly;

        // Track earliest arrival time
        Float_t arrival = pt->GetTime() + distance * invSignalSpeed;
        earliestToA = std::min(earliestToA, arrival);

        // Debug print per point (optional, can be gated behind verbose flag)
        // std::cout << Form("Hit: SiPM %d, Fibre %d, dist %.2f cm, eLoss %.2f keV, ly %.2f p.e., pdg %d",
        //                  SiPMChan, pt->GetDetectorID(), distance, energy*1e6f, ly, pt->PdgCode()) << std::endl;
    }

    // Apply statistical smearing and saturation
    const Int_t smearedLy = gRandom->Poisson(totalLy);
    const Float_t pix = sipm_saturation(smearedLy, kNpheMax);
    signals = npix_to_qdc(pix);

    // Final hit decision and time
    hitFlag = (smearedLy > kNpheMin);
    flag = hitFlag;
    time = gRandom->Gaus(earliestToA, kTimeRes);
}

// -----   Destructor   ----------------------------------------------------
MtcDetHit::~MtcDetHit() {}
// -------------------------------------------------------------------------

// -----   Public method GetEnergy   -------------------------------------------
Float_t MtcDetHit::GetEnergy()
{
    // to be calculated from digis and calibration constants, missing!
    return signals;
}

Float_t MtcDetHit::ly_loss(Float_t distance)
{
    //	It returns the light yield attenuation depending on the distance to SiPM
    return TMath::Exp(-(distance - ly_loss_params[0]) / ly_loss_params[1]);
}

Float_t MtcDetHit::sipm_saturation(Float_t ly, Float_t nphe_max)
{
    //	It returns the number of fired pixels per channel
    Float_t factor = 1 - TMath::Exp(-ly / nphe_max);
    return nphe_max * factor;
}

Float_t MtcDetHit::npix_to_qdc(Float_t npix)
{
    //	It returns QDC per channel after Gaussian smearing of the parameters
    Float_t A = gRandom->Gaus(npix_to_qdc_params[0], npix_to_qdc_params[2]);
    Float_t B = gRandom->Gaus(npix_to_qdc_params[1], npix_to_qdc_params[3]);
    return A * npix + B;
}

// -----   Public method Print   -------------------------------------------
void MtcDetHit::Print()
{
    std::cout << Form(
        "MtcDetHit: Detector ID %d, Layer %d, Station Type %d, SiPM %d, Channel %d, Signal %.2f, Time %.3f",
        fDetectorID,
        GetLayer(),
        GetStationType(),
        GetSiPM(),
        GetSiPMChan(),
        signals,
        time);
}
// -------------------------------------------------------------------------

ClassImp(MtcDetHit)
