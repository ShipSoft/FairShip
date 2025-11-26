// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

#include "MuDISGenerator.h"

#include "FairLogger.h"
#include "FairPrimaryGenerator.h"
#include "MeanMaterialBudget.h"
#include "TFile.h"
#include "TGeoCompositeShape.h"
#include "TGeoEltu.h"
#include "TGeoManager.h"
#include "TGeoNode.h"
#include "TGeoVolume.h"
#include "TMath.h"
#include "TROOT.h"
#include "TRandom.h"
#include "TSystem.h"
#include "TVectorD.h"

#include <math.h>

// MuDIS momentum GeV
// Vertex in SI units, assume this means m

const Double_t c_light = 29.9792458;              // speed of light in cm/ns
const Double_t muon_mass = 0.10565999895334244;   // muon mass in GeV

// -----   Default constructor   -------------------------------------------
MuDISGenerator::MuDISGenerator() {}
// -------------------------------------------------------------------------
// -----   Default constructor   -------------------------------------------
Bool_t MuDISGenerator::Init(const char* fileName)
{
    return Init(fileName, 0);
}
Bool_t MuDISGenerator::Init(const char* fileName, const int firstEvent)
{
    LOGF(info, "Opening input file %s", fileName);

    iMuon = 0;
    dPart = 0;
    dPartSoft = 0;
    fInputFile = TFile::Open(fileName);
    if (!fInputFile) {
        LOG(fatal) << "Error opening input file";
        return kFALSE;
    }
    fTree = fInputFile->Get<TTree>("DIS");
    fNevents = fTree->GetEntries();
    fn = firstEvent;

    fTree->SetBranchAddress("InMuon", &iMuon);   // incoming muon
    fTree->SetBranchAddress("DISParticles", &dPart);
    fTree->SetBranchAddress("SoftParticles", &dPartSoft);   // Soft interaction particles
    LOG(info) << "MuDISGenerator: Initialization successful.";
    return kTRUE;
}

// -----   Destructor   ----------------------------------------------------
MuDISGenerator::~MuDISGenerator()
{
    fInputFile->Close();
    fInputFile->Delete();
    delete fInputFile;
}
// -----   Passing the event   ---------------------------------------------
Bool_t MuDISGenerator::ReadEvent(FairPrimaryGenerator* cpg)
{
    if (fn == fNevents) {
        LOG(warning) << "End of input file. Rewind.";
    }
    fTree->GetEntry(fn % fNevents);
    fn++;
    if (fn % 10 == 0) {
        LOG(info) << "Info MuDISGenerator: MuDIS event-nr " << fn;
    }

    int nf = dPart->GetEntries();
    LOG(debug) << "*********************************************************";
    LOG(debug) << "muon DIS Generator debug " << iMuon->GetEntries() << " " << iMuon->AddrAt(0) << " nf " << nf
               << " fn=" << fn;

    // some start/end positions in z (f.i. emulsion to Tracker 1)
    Double_t start[3] = {0., 0., startZ};
    Double_t end[3] = {0., 0., endZ};

    // incoming muon  array('d',[pid,px,py,pz,E,x,y,z,w,t])
    TVectorD* mu = dynamic_cast<TVectorD*>(iMuon->AddrAt(0));
    LOG(debug) << "muon DIS Generator in muon " << int(mu[0][0]);
    Double_t x = mu[0][5] * 100.;                // come in m -> cm
    Double_t y = mu[0][6] * 100.;                // come in m -> cm
    Double_t z = mu[0][7] * 100.;                // come in m -> cm
    Double_t w = mu[0][8];                       // weight of the original muon ( normalised to a spill)
    Double_t cross_sec = mu[0][10];              // in mbarns
    Double_t t_muon = mu[0][11];                 // in ns
    Double_t DIS_multiplicity = 1 / mu[0][12];   // 1/nDIS

    // calculate start/end positions along this muon, and amount of material in between

    Double_t txmu = mu[0][1] / mu[0][3];
    Double_t tymu = mu[0][2] / mu[0][3];
    start[0] = x - (z - start[2]) * txmu;
    start[1] = y - (z - start[2]) * tymu;
    end[0] = x - (z - end[2]) * txmu;
    end[1] = y - (z - end[2]) * tymu;
    LOG(debug) << "MuDIS: mu xyz position " << x << ", " << y << ", " << z;
    LOG(debug) << "MuDIS: mu pxyz position " << mu[0][1] << ", " << mu[0][2] << ", " << mu[0][3];
    LOG(debug) << "MuDIS: mu weight*DISmultiplicity  " << w;
    LOG(debug) << "MuDIS: mu DIS cross section " << cross_sec;
    LOG(debug) << "MuDIS: start position " << start[0] << ", " << start[1] << ", " << start[2];
    LOG(debug) << "MuDIS: end position " << end[0] << ", " << end[1] << ", " << end[2];

    Double_t bparam;
    Double_t mparam[10];
    bparam = shipgen::MeanMaterialBudget(start, end, mparam);
    // loop over trajectory between start and end to pick an interaction point
    Double_t prob2int = 0.;
    Double_t xmu;
    Double_t ymu;
    Double_t zmu;
    Int_t count = 0;
    LOG(debug) << "Info MuDISGenerator Start prob2int while loop, bparam= " << bparam << ", " << bparam * 1.e8;
    LOG(debug) << "Info MuDISGenerator What was maximum density, mparam[7]= " << mparam[7] << ", " << mparam[7] * 1.e8;

    while (prob2int < gRandom->Uniform(0., 1.)) {
        zmu = gRandom->Uniform(start[2], end[2]);
        xmu = x - (z - zmu) * txmu;
        ymu = y - (z - zmu) * tymu;
        // get local material at this point
        TGeoNode* node = gGeoManager->FindNode(xmu, ymu, zmu);
        TGeoMaterial* mat = 0;
        if (node && !gGeoManager->IsOutside())
            mat = node->GetVolume()->GetMaterial();
        LOG(debug) << "Info MuDISGenerator: mat " << count << ", " << mat->GetName() << ", " << mat->GetDensity();
        // density relative to Prob largest density along this trajectory, i.e. use rho(Pt)
        prob2int = mat->GetDensity() / mparam[7];
        if (prob2int > 1.) {
            LOG(warning) << "MuDISGenerator: prob2int > Maximum density????";
            LOG(warning) << "prob2int: " << prob2int;
            LOG(warning) << "maxrho: " << mparam[7];
            LOG(warning) << "material: " << mat->GetName();
        }
        count += 1;
    }

    LOG(debug) << "Info MuDISGenerator: prob2int " << prob2int << ", " << count;
    LOG(debug) << "MuDIS: put position " << xmu << ", " << ymu << ", " << zmu;

    Double_t total_mom =
        TMath::Sqrt(TMath::Power(mu[0][1], 2) + TMath::Power(mu[0][2], 2) + TMath::Power(mu[0][3], 2));   // in GeV

    Double_t distance =
        TMath::Sqrt(TMath::Power(x - xmu, 2) + TMath::Power(y - ymu, 2) + TMath::Power(z - zmu, 2));   // in cm

    Double_t v = c_light * total_mom / TMath::Sqrt(TMath::Power(total_mom, 2) + TMath::Power(muon_mass, 2));
    Double_t t_rmu = distance / v;

    // Adjust time based on the relative positions
    if (zmu < z) {
        t_rmu = -t_rmu;
    }

    Double_t t_DIS = (t_muon + t_rmu) / 1e9;   // time taken in seconds to reach [xmu,ymu,zmu]

    cpg->AddTrack(static_cast<int>(mu[0][0]),   // incoming muon track ()
                  mu[0][1],
                  mu[0][2],
                  mu[0][3],
                  xmu,
                  ymu,
                  zmu,
                  -1,
                  false,   // tracking disabled
                  mu[0][4],
                  t_DIS,                   // shift time of the incoming muon track wrt t_muon from the input file.
                  w * DIS_multiplicity);   // muon weight associated with a spill* DISmultiplicity

    // outgoing DIS particles, [did,dpx,dpy,dpz,E], put density along trajectory as weight, g/cm^2

    w = mparam[0] * mparam[4];   // modify weight, by multiplying with average density * track length
    int index = 0;
    for (auto&& particle : *dPart) {
        TVectorD* Part = dynamic_cast<TVectorD*>(particle);
        LOG(debug) << "muon DIS Generator out part " << int((*Part)[0]);
        LOG(debug) << "muon DIS Generator out part mom " << (*Part)[1] << " " << (*Part)[2] << " " << (*Part)[3] << " "
                   << (*Part)[4];
        LOG(debug) << "muon DIS Generator out part pos " << xmu << " " << ymu << "" << zmu;
        LOG(debug) << "muon DIS Generator out part w " << w;

        if (index == 0) {
            cpg->AddTrack(static_cast<int>((*Part)[0]),
                          (*Part)[1],
                          (*Part)[2],
                          (*Part)[3],
                          xmu,
                          ymu,
                          zmu,
                          0,
                          true,
                          (*Part)[4],
                          t_DIS,
                          cross_sec);   // save DIS cross section in MCTrack[1]
        } else {
            cpg->AddTrack(static_cast<int>((*Part)[0]),
                          (*Part)[1],
                          (*Part)[2],
                          (*Part)[3],
                          xmu,
                          ymu,
                          zmu,
                          0,
                          true,
                          (*Part)[4],
                          t_DIS,
                          w);
        }
        index += 1;
    }

    // Soft interaction tracks
    for (auto&& softParticle : *dPartSoft) {
        TVectorD* SoftPart = dynamic_cast<TVectorD*>(softParticle);
        if ((*SoftPart)[7] > zmu) {
            continue;
        }   // Soft interactions after the DIS point are not saved
        Double_t t_soft = (*SoftPart)[8] / 1e9;   // Time in seconds
        cpg->AddTrack(static_cast<int>((*SoftPart)[0]),
                      (*SoftPart)[1],
                      (*SoftPart)[2],
                      (*SoftPart)[3],
                      (*SoftPart)[5],
                      (*SoftPart)[6],
                      (*SoftPart)[7],
                      0,
                      true,
                      (*SoftPart)[4],
                      t_soft,
                      w);
    }

    return kTRUE;
}
// -------------------------------------------------------------------------
Int_t MuDISGenerator::GetNevents()
{
    return fNevents;
}
