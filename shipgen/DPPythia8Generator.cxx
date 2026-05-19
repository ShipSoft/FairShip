// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "DPPythia8Generator.h"

#include <cmath>
#include <vector>

#include "BeamSmearingUtils.h"
#include "FairPrimaryGenerator.h"
#include "Pythia8/Pythia.h"
#include "ShipUnit.h"
#include "TDatabasePDG.h"  // for TDatabasePDG
#include "TMath.h"
#include "TROOT.h"
#include "TSystem.h"

using ShipUnit::cm;
using ShipUnit::mm;
const Double_t c_light = 2.99792458e+10;  // speed of light in cm/sec (c_light
                                          // = 2.99792458e+8 * m/s)
const Int_t debug = 1;

// -----   Default constructor   -------------------------------------------
DPPythia8Generator::DPPythia8Generator() {
  // fHadDecay = false;
  fId = 2212;           // proton
  fMom = 400;           // proton
  fDP = 9900015;        // DP  pdg code
  fLmin = 5000. * cm;   // mm minimum  decay position z  ROOT units !
  fLmax = 12000. * cm;  // mm maximum decay position z
  fFDs = 7.7 / 10.4;  // correction for Pythia6 to match measured Ds production
  fpbrem = kFALSE;
  fpbremPDF = 0;
  fsmearBeam = 8 * mm;  // default value for smearing beam (8 mm)
  fPaintBeam = 5 * cm;  // default value for painting beam (5 cm)
  fdy = kFALSE;
  fDPminM = 0.5;
  fInputFile = nullptr;
  fnRetries = 0;
  fnDPtot = 0;
  fShipEventNr = 0;
  fPythia = new Pythia8::Pythia();
  // fPythiaHadDecay =  new Pythia8::Pythia();
}
// -------------------------------------------------------------------------

void DPPythia8Generator::Print() { fPythia->settings.listAll(); };

// -----   Init   ----------------------------------------------------------
Bool_t DPPythia8Generator::Init() {
  if (fUseRandom1) fRandomEngine = std::make_shared<PyTr1Rng>();
  if (fUseRandom3) fRandomEngine = std::make_shared<PyTr3Rng>();
  fPythia->setRndmEnginePtr(fRandomEngine);
  // fPythiaHadDecay->setRndmEnginePtr(fRandomEngine);
  fn = 0;

  if (!fpbrem) {
    if (debug) {
      std::cout << "Beam Momentum " << fMom << std::endl;
    }
    fPythia->settings.mode("Beams:idA", fId);
    fPythia->settings.mode("Beams:idB", 2212);
    fPythia->settings.mode("Beams:frameType", 2);
    fPythia->settings.parm("Beams:eA", fMom);  // codespell:ignore parm
    fPythia->settings.parm("Beams:eB", 0.);    // codespell:ignore parm

    if (fdy)
      fPythia->settings.parm("PhaseSpace:mHatMin",  // codespell:ignore parm
                             fDPminM);

  } else {
    if (!fpbremPDF) {
      LOG(fatal) << "Failed in retrieving dark photon PDF for production by "
                    "proton bremstrahlung!";
      return kFALSE;
    }
  }

  TDatabasePDG* pdgBase = TDatabasePDG::Instance();
  Double_t root_ctau = pdgBase->GetParticle(fDP)->Lifetime();

  if (debug) {
    std::cout << "Final particle parameters for PDGID " << fDP << ":"
              << std::endl;
    List(fDP);
  }
  if (debug) {
    std::cout << "tau root PDG database " << root_ctau
              << "[s] ctau root = " << root_ctau * 3e10 << "[cm]" << std::endl;
  }
  fctau = fPythia->particleData.tau0(fDP);  //* 3.3333e-12
  if (debug) {
    std::cout << "ctau pythia " << fctau << "[mm]" << std::endl;
  }
  int initPass = fPythia->init();
  if (debug) {
    std::cout << "Pythia initialisation bool: " << initPass << std::endl;
  }

  if (!initPass) {
    LOG(fatal) << "Pythia initialisation failed";
    return kFALSE;
  }

  return kTRUE;
}
// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
DPPythia8Generator::~DPPythia8Generator() {
  delete fPythia;
  fPythia = nullptr;
}
// -------------------------------------------------------------------------

// -----   Passing the event   ---------------------------------------------
Bool_t DPPythia8Generator::ReadEvent(FairPrimaryGenerator* cpg) {
  auto [dx, dy] = CalculateBeamOffset(fsmearBeam, fPaintBeam);
  Double_t tp, tS, zp, xp, yp, zS, xS, yS, pz, px, py, e, w;
  Double_t tm, zm, xm, ym, pmz, pmx, pmy, em;
  Int_t im;
  Int_t imout;
  Double_t tN, zN, xN, yN, pzN, pxN, pyN, eN;

  int iDP =
      0;  // index of the chosen DP, also ensures that at least 1 DP is produced
  // Pythia indices of the particles stored on the FairShip MCTrack stack.
  // In this implementation the exported chain is:
  //   [Pythia event[1] beam particle, mother meson, dark photon, daughters...]
  // Pythia event[0] is the internal system entry and is not exported.
  std::vector<int>
      dec_chain;  // pythia indices of the particles to be stored on the stack
  std::vector<int> dpvec;  // pythia indices of DP particles

  do {
    // clear containers at every retry to avoid mixing different events
    dec_chain.clear();
    dpvec.clear();

    // bit for proton brem
    if (fpbrem) {
      fPythia->event.reset();
      double dpmom = 0;
      double thetain = 0;
      fpbremPDF->GetRandom2(dpmom, thetain);
      double dpm = fPythia->particleData.m0(fDP);
      double dpe = sqrt(dpmom * dpmom + dpm * dpm);
      double phiin = 2. * M_PI * gRandom->Rndm();

      if (debug > 1) {
        std::cout << " Adding DP gun with p " << dpmom << " m " << dpm << " e "
                  << dpe << " theta,phi " << thetain << "," << phiin
                  << std::endl
                  << std::flush;
      }
      fPythia->event.append(fDP, 1, 0, 0, dpmom * sin(thetain) * cos(phiin),
                            dpmom * sin(thetain) * sin(phiin),
                            dpmom * cos(thetain), dpe, dpm);
    }

    if (!fPythia->next()) LOG(fatal) << "fPythia->next() failed";

    // fPythia->event.list();
    for (int i = 0; i < fPythia->event.size(); i++) {
      // find all DP
      if (abs(fPythia->event[i].id()) == fDP) {
        dpvec.push_back(i);
      }
    }
    iDP = dpvec.size();
    fnDPtot += iDP;
    if (iDP == 0) {
      fnRetries += 1;
    } else {
      // filter DPs by vessel acceptance
      std::vector<int> accepted;
      for (int idx : dpvec) {
        if (IsInVesselAcceptance(fPythia->event[idx].px(),
                                 fPythia->event[idx].py(),
                                 fPythia->event[idx].pz())) {
          accepted.push_back(idx);
        }
      }
      if (accepted.empty()) {
        iDP = 0;
        dpvec.clear();
        fnGeoRejects += 1;
        continue;
      }
      int r = static_cast<int>(gRandom->Uniform(0, accepted.size()));
      int i = accepted[r];
      // production vertex
      zp = fPythia->event[i].zProd();
      xp = fPythia->event[i].xProd();
      yp = fPythia->event[i].yProd();
      tp = fPythia->event[i].tProd();
      // momentum
      pz = fPythia->event[i].pz();
      px = fPythia->event[i].px();
      py = fPythia->event[i].py();
      e = fPythia->event[i].e();
      // old decay vertex
      if (debug > 1) {
        int id1 = fPythia->event[i].daughter1();
        int id2 = fPythia->event[i].daughter2();
        std::cout << " Debug: decay product of A: ";
        if (id1 > 0)
          std::cout << fPythia->event[id1].id() << " ";
        else
          std::cout << "none ";
        if (id2 > 0)
          std::cout << fPythia->event[id2].id();
        else
          std::cout << "none";
        std::cout << std::endl;
      }

      //  new decay vertex
      Double_t LS = gRandom->Uniform(fLmin / mm, fLmax / mm);  // in mm
      Double_t p = TMath::Sqrt(px * px + py * py + pz * pz);
      Double_t lam = LS / p;
      xS = xp + lam * px;
      yS = yp + lam * py;
      zS = zp + lam * pz;
      Double_t gam = e / TMath::Sqrt(e * e - p * p);
      Double_t beta = p / e;
      tS = tp + LS / beta;  // all in Pythia units
      w = TMath::Exp(-LS / (beta * gam * fctau)) *
          ((fLmax / mm - fLmin / mm) / (beta * gam * fctau));

      // direct mother of the DP
      im = (Int_t)fPythia->event[i].mother1();

      if (!fpbrem && im > 0) {
        // Meson-production chain: store event[1] (beam nucleon), mother, DP
        if (fPythia->event.size() > 1) {
          zN = fPythia->event[1].zProd();
          xN = fPythia->event[1].xProd();
          yN = fPythia->event[1].yProd();
          pzN = fPythia->event[1].pz();
          pxN = fPythia->event[1].px();
          pyN = fPythia->event[1].py();
          eN = fPythia->event[1].e();
          tN = fPythia->event[1].tProd();

          cpg->AddTrack((Int_t)fPythia->event[1].id(), pxN, pyN, pzN,
                        xN * mm + dx, yN * mm + dy, zN * mm, -1, false, eN,
                        tN * mm / c_light,
                        w);  // event[0] is the root of the exported chain

          dec_chain.push_back(1);

          if (debug > 1)
            std::cout << std::endl
                      << " insert nucleon ancestor id 0"
                      << " pdg=" << fPythia->event[1].id() << " pz = " << pzN
                      << " [GeV], z = " << zN << " [mm] t = " << tN << " [mm/c]"
                      << std::endl;
        }

        zm = fPythia->event[im].zProd();
        xm = fPythia->event[im].xProd();
        ym = fPythia->event[im].yProd();
        pmz = fPythia->event[im].pz();
        pmx = fPythia->event[im].px();
        pmy = fPythia->event[im].py();
        em = fPythia->event[im].e();
        tm = fPythia->event[im].tProd();

        // mother points to track 0 (event[1]) in the exported chain
        imout = 0;

        cpg->AddTrack(
            (Int_t)fPythia->event[im].id(), pmx, pmy, pmz, xm * mm + dx,
            ym * mm + dy, zm * mm, imout, false, em, tm * mm / c_light,
            w);  // convert pythia's (x,y,z[mm], t[mm/c]) to ([cm], [s])

        // DP points to the direct mother in the exported chain, which is track
        // 1
        cpg->AddTrack(fDP, px, py, pz, xp * mm + dx, yp * mm + dy, zp * mm, 1,
                      false, e, tp * mm / c_light, w);

        // bookkeep the indices of stored particles
        dec_chain.push_back(im);
        dec_chain.push_back(i);

        if (debug > 1)
          std::cout << std::endl
                    << " insert mother id " << im
                    << " pdg=" << fPythia->event[im].id() << " pmz = " << pmz
                    << " [GeV],  zm = " << zm << " [mm] tm = " << tm
                    << " [mm/c]" << std::endl;
        if (debug > 1)
          std::cout << " ----> insert DP id " << i << " pdg=" << fDP
                    << " pz = " << pz << " [GeV] zp = " << zp
                    << " [mm] tp = " << tp << " [mm/c]" << std::endl;
      } else {
        // Proton bremsstrahlung or no valid mother: export only the DP as root
        cpg->AddTrack(fDP, px, py, pz, xp * mm + dx, yp * mm + dy, zp * mm, -1,
                      false, e, tp * mm / c_light, w);
        dec_chain.push_back(i);

        if (debug > 1)
          std::cout << " ----> insert DP (root) id " << i << " pdg=" << fDP
                    << " pz = " << pz << " [GeV] zp = " << zp
                    << " [mm] tp = " << tp << " [mm/c]" << std::endl;
      }
      iDP = i;
    }
  } while (iDP ==
           0);  // ----------- avoid rare empty events w/o any DP's produced

  if (fShipEventNr % 100 == 0) {
    LOGF(info, "ship event %i / pythia event-nr %i", fShipEventNr, fn);
  }
  fShipEventNr += 1;
  // number of prefix entries (nucleon + mother + DP, or just DP for fpbrem)
  size_t prefix_len = dec_chain.size();
  // fill a container with pythia indices of the DP decay chain
  if (debug > 1) std::cout << "Filling daughter particles" << std::endl;
  // if (!hadDecay){
  for (int k = 0; k < fPythia->event.size(); k++) {
    // if daughter of DP, copy
    if (debug > 1)
      std::cout << k << " pdg =" << fPythia->event[k].id() << " mum "
                << fPythia->event[k].mother1() << std::endl;
    im = fPythia->event[k].mother1();
    while (im > 0) {
      if (im == iDP) {
        break;
      }  // pick the decay products of only 1 chosen DP
      // if ( abs(fPythia->event[im].id())==fDP && im == iDP ){break;}
      else {
        im = fPythia->event[im].mother1();
      }
    }
    if (im < 1) {
      if (debug > 1) std::cout << "reject" << std::endl;
      continue;
    }
    if (debug > 1) std::cout << "accept" << std::endl;
    dec_chain.push_back(k);
  }

  // go over daughters and store them on the stack
  // dec_chain now contains prefix entries followed by daughters
  for (std::vector<int>::iterator it = dec_chain.begin() + prefix_len;
       it != dec_chain.end(); ++it) {
    // pythia index of the particle to store
    int k = *it;
    // find mother position on the output stack: impy -> im
    int impy = fPythia->event[k].mother1();
    std::vector<int>::iterator itm =
        std::find(dec_chain.begin(), dec_chain.end(), impy);
    im = -1;  // safety
    if (itm != dec_chain.end()) {
      im = itm - dec_chain.begin();  // convert iterator into sequence number
    }

    Bool_t wanttracking = false;
    if (fPythia->event[k].isFinal()) {
      wanttracking = true;
    }
    pz = fPythia->event[k].pz();
    px = fPythia->event[k].px();
    py = fPythia->event[k].py();
    e = fPythia->event[k].e();

    cpg->AddTrack((Int_t)fPythia->event[k].id(), px, py, pz, xS * mm, yS * mm,
                  zS * mm, im, wanttracking, e, tS * mm / c_light, w);
  }
  return kTRUE;
}
// -------------------------------------------------------------------------
void DPPythia8Generator::SetParameters(char* par) {
  // Set Parameters
  fPythia->readString(par);
  if (debug) {
    std::cout << "fPythia->readString(\"" << par << "\")" << std::endl;
  }
}

// -------------------------------------------------------------------------
