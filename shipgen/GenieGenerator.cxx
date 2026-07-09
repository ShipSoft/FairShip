// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "GenieGenerator.h"

#include <cmath>

#include "FairPrimaryGenerator.h"
#include "MeanMaterialBudget.h"
#include "ShipUnit.h"
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

using ShipUnit::m;

using std::cout;
using std::endl;
// read events from ntuples produced with GENIE
// http://genie.hepforge.org/manuals/GENIE_PhysicsAndUserManual_20130615.pdf
// Genie momentum GeV
// Vertex in SI units, assume this means m
// important to read back number of events to give to FairRoot

// -----   Default constructor   -------------------------------------------
GenieGenerator::GenieGenerator() = default;
// -------------------------------------------------------------------------
// -----   Default constructor   -------------------------------------------
Bool_t GenieGenerator::Init(const char* fileName) { return Init(fileName, 0); }
// -----   Default constructor   -------------------------------------------
Bool_t GenieGenerator::Init(const char* fileName, const int startEvent) {
  if (fGenOption != 0 && fGenOption != 3) {
    LOG(fatal) << "Invalid GenieGen Option: " << fGenOption
               << " Please check the option provided with --GenieOption "
               << endl;
    return kFALSE;
  }
  fNuOnly = false;
  LOG(info) << "Opening input file " << fileName;
  if (startEvent < 0) {
    LOG(error) << "GenieGenerator: startEvent must be >= 0, got " << startEvent;
    return kFALSE;
  }
  fInputFile = TFile::Open(fileName, "READ");
  if (!fInputFile) {
    LOG(error) << "GenieGenerator: error opening input file " << fileName;
    delete fInputFile;
    fInputFile = nullptr;
    return kFALSE;
  }
  fTree = dynamic_cast<TTree*>(fInputFile->Get("gst"));
  if (!fTree) {
    LOG(error) << "GenieGenerator: cannot find tree gst in file " << fileName;
    fInputFile->Close();
    delete fInputFile;
    fInputFile = nullptr;
    return kFALSE;
  }
  fNevents = fTree->GetEntries();
  if (startEvent >= fNevents) {
    LOG(error) << "GenieGenerator: startEvent " << startEvent
               << " is out of range for " << fNevents << " entries";
    fInputFile->Close();
    delete fInputFile;
    fInputFile = nullptr;
    fTree = nullptr;
    return kFALSE;
  }
  fn = startEvent;
  bool ok = true;
  ok &= (fTree->SetBranchAddress("Ev", &Ev) >= 0);
  ok &= (fTree->SetBranchAddress("pxv", &pxv) >= 0);
  ok &= (fTree->SetBranchAddress("pyv", &pyv) >= 0);
  ok &= (fTree->SetBranchAddress("pzv", &pzv) >= 0);
  ok &= (fTree->SetBranchAddress("neu", &neu) >= 0);
  ok &= (fTree->SetBranchAddress("cc", &cc) >= 0);
  ok &= (fTree->SetBranchAddress("nuel", &nuel) >= 0);
  ok &= (fTree->SetBranchAddress("vtxx", &vtxx) >= 0);
  ok &= (fTree->SetBranchAddress("vtxy", &vtxy) >= 0);
  ok &= (fTree->SetBranchAddress("vtxz", &vtxz) >= 0);
  ok &= (fTree->SetBranchAddress("vtxt", &vtxt) >= 0);
  ok &= (fTree->SetBranchAddress("El", &El) >= 0);
  ok &= (fTree->SetBranchAddress("pxl", &pxl) >= 0);
  ok &= (fTree->SetBranchAddress("pyl", &pyl) >= 0);
  ok &= (fTree->SetBranchAddress("pzl", &pzl) >= 0);
  ok &= (fTree->SetBranchAddress("Ef", &Ef) >= 0);
  ok &= (fTree->SetBranchAddress("pxf", &pxf) >= 0);
  ok &= (fTree->SetBranchAddress("pyf", &pyf) >= 0);
  ok &= (fTree->SetBranchAddress("pzf", &pzf) >= 0);
  ok &= (fTree->SetBranchAddress("nf", &nf) >= 0);
  ok &= (fTree->SetBranchAddress("pdgf", &pdgf) >= 0);
  if (!ok) {
    LOG(error)
        << "GenieGenerator: failed to bind one or more required branches";
    fInputFile->Close();
    delete fInputFile;
    fInputFile = nullptr;
    fTree = nullptr;
    return kFALSE;
  }
  fFirst = kTRUE;
  return kTRUE;
}
// -------------------------------------------------------------------------
std::vector<double> GenieGenerator::Rotate(Double_t x, Double_t y, Double_t z,
                                           Double_t px, Double_t py,
                                           Double_t pz) {
  // rotate vector px,py,pz to point at x,y,z at origin.
  Double_t theta = atan(sqrt(x * x + y * y) / z);
  Double_t c = cos(theta);
  Double_t s = sin(theta);
  // rotate around y-axis
  Double_t px1 = c * px + s * pz;
  Double_t pzr = -s * px + c * pz;
  Double_t phi = atan2(y, x);
  c = cos(phi);
  s = sin(phi);
  // rotate around z-axis
  Double_t pxr = c * px1 - s * py;
  Double_t pyr = s * px1 + c * py;
  // cout << "Info GenieGenerator: rotated" << pxr << " " << pyr << " "
  // << pzr << " " << x << " " << y << " " << z <<endl;
  return {pxr, pyr, pzr};
}

// -----   Destructor   ----------------------------------------------------
GenieGenerator::~GenieGenerator() {
  if (fInputFile) {
    fInputFile->Close();
    fInputFile->Delete();
    delete fInputFile;
  }
}
// -------------------------------------------------------------------------
void GenieGenerator::AddBox(const TVector3& dVec, const TVector3& box) {
  dVecs.push_back(dVec);
  m_boxes.push_back(box);
  cout << "Debug GenieGenerator: " << dVec.X() << " " << box.Z() << endl;
}
// -----   Passing the event   ---------------------------------------------
Bool_t GenieGenerator::OldReadEvent(FairPrimaryGenerator* cpg) {
  if (fFirst) {
    TGeoVolume* top = gGeoManager->GetTopVolume();
    TGeoNode* linner = top->FindNode("lidT1I_1");
    TGeoNode* scint = top->FindNode("lidT1lisci_1");
    TGeoNode* louter = top->FindNode("lidT1O_1");
    TGeoNode* lidT6I = top->FindNode("lidT6I_1");
    TGeoNode* t2I = top->FindNode("T2I_1");
    TGeoNode* t1I = top->FindNode("T1I_1");
    TGeoEltu* temp = dynamic_cast<TGeoEltu*>(linner->GetVolume()->GetShape());
    fEntrDz_inner = temp->GetDZ();
    temp = dynamic_cast<TGeoEltu*>(louter->GetVolume()->GetShape());
    fEntrDz_outer = temp->GetDZ();
    fEntrA = temp->GetA();
    fEntrB = temp->GetB();
    fEntrZ_inner = linner->GetMatrix()->GetTranslation()[2];
    fEntrZ_outer = louter->GetMatrix()->GetTranslation()[2];
    Lvessel =
        lidT6I->GetMatrix()->GetTranslation()[2] - fEntrZ_inner - fEntrDz_inner;
    TGeoCompositeShape* tempC =
        dynamic_cast<TGeoCompositeShape*>(t2I->GetVolume()->GetShape());
    Xvessel = tempC->GetDX() - 2 * fEntrDz_inner;
    Yvessel = tempC->GetDY() - 2 * fEntrDz_inner;
    tempC = dynamic_cast<TGeoCompositeShape*>(t1I->GetVolume()->GetShape());
    fL1z = tempC->GetDZ() * 2;
    temp = dynamic_cast<TGeoEltu*>(scint->GetVolume()->GetShape());
    fScintDz = temp->GetDZ() * 2;
    cout << "Info GenieGenerator: geo inner " << fEntrDz_inner << " "
         << fEntrZ_inner << endl;
    cout << "Info GenieGenerator: geo outer " << fEntrDz_outer << " "
         << fEntrZ_outer << endl;
    cout << "Info GenieGenerator: A and B " << fEntrA << " " << fEntrB << endl;
    cout << "Info GenieGenerator: vessel length heig<ht width " << Lvessel
         << " " << Yvessel << " " << Xvessel << endl;
    cout << "Info GenieGenerator: scint thickness " << fScintDz << endl;
    cout << "Info GenieGenerator: rextra " << fScintDz / 2. + 2 * fEntrDz_inner
         << " " << 2 * fEntrDz_outer << " " << 2 * fEntrDz_inner << endl;
    for (size_t j = 0; j < m_boxes.size(); j++) {
      cout << "Info GenieGenerator: nuMu X" << j << " - "
           << -m_boxes[j].X() + dVecs[j].X() << " "
           << m_boxes[j].X() + dVecs[j].X() << endl;
      cout << "Info GenieGenerator: nuMu Y" << j << " - "
           << -m_boxes[j].Y() + dVecs[j].Y() << " "
           << m_boxes[j].Y() + dVecs[j].Y() << endl;
      cout << "Info GenieGenerator: nuMu Z" << j << " - "
           << -m_boxes[j].Z() + dVecs[j].Z() << " "
           << m_boxes[j].Z() + dVecs[j].Z() << endl;
    }
    fFirst = kFALSE;
  }
  if (fn == fNevents) {
    LOG(warning) << "End of input file. Rewind.";
  }
  fTree->GetEntry(fn % fNevents);
  fn++;
  if (fn % 1000 == 0) {
    cout << "Info GenieGenerator: neutrino event-nr " << fn << endl;
  }
  // generate a random point on the vessel, take veto z, and calculate outer lid
  // position
  // Double_t Yvessel=500.;
  // Double_t Lvessel=5.*Yvessel+3500.;
  // Double_t ztarget=zentrance-6350.;
  // Double_t ea=250.; //inside inner wall vessel
  Double_t eb = Yvessel;  // inside inner wall vessel
  Double_t x;
  Double_t y;
  Double_t z;
  Double_t where = gRandom->Uniform(0., 1.);
  if (where < 0.03) {
    // point on entrance lid
    Double_t ellip = 2.;
    while (ellip > 1.) {
      x = gRandom->Uniform(-fEntrA, fEntrA);
      y = gRandom->Uniform(-fEntrB, fEntrB);
      ellip = (x * x) / (fEntrA * fEntrA) + (y * y) / (fEntrB * fEntrB);
    }
    if (gRandom->Uniform(0., 1.) < 0.5) {
      z = fEntrZ_inner + gRandom->Uniform(-fEntrDz_inner, fEntrDz_inner);
    } else {
      z = fEntrZ_outer + gRandom->Uniform(-fEntrDz_outer, fEntrDz_outer);
    }
  } else if (where < 0.64) {
    // point on tube, place over 1 cm radius at 2 radii, separated by 10. cm
    //  first vessel has smaller size
    Double_t ea = Xvessel;
    Double_t zrand = gRandom->Uniform(0, Lvessel);
    if (zrand < fL1z) {
      ea = fEntrA;
    }
    z = fEntrZ_outer - fEntrDz_outer + zrand;
    Double_t theta = gRandom->Uniform(0., TMath::Pi());
    Double_t rextra;
    if (gRandom->Uniform(0., 1.) > 0.5) {
      // outer vessel
      rextra = fScintDz / 2. + 2 * fEntrDz_inner +
               gRandom->Uniform(0, 2 * fEntrDz_outer);
    } else {
      // inner vessel
      rextra = gRandom->Uniform(0., 2 * fEntrDz_inner);
    }
    x = (ea + rextra) * cos(theta);
    y = sqrt(1. - (x * x) / ((ea + rextra) * (ea + rextra))) * (eb + rextra);
    if (gRandom->Uniform(-1., 1.) > 0.) y = -y;
  } else {
    // point in nu-tau detector area
    int j = static_cast<int>(gRandom->Uniform(0., m_boxes.size() + 0.5));
    x = gRandom->Uniform(-m_boxes[j].X() + dVecs[j].X(),
                         m_boxes[j].X() + dVecs[j].X());
    y = gRandom->Uniform(-m_boxes[j].Y() + dVecs[j].Y(),
                         m_boxes[j].Y() + dVecs[j].Y());
    z = gRandom->Uniform(-m_boxes[j].Z() + dVecs[j].Z(),
                         m_boxes[j].Z() + dVecs[j].Z());
  }
  // first, incoming neutrino
  // rotate the particle
  Double_t zrelative = z - ztarget;
  // cout << "Info GenieGenerator: x,y,z " << x <<" " << y << " " << zrelative
  // << endl; cout << "Info GenieGenerator: neutrino " << neu << "p-in "<< pxv
  // << pyv << pzv << " nf "<< nf << endl;
  std::vector<double> pout = Rotate(x, y, zrelative, pxv, pyv, pzv);
  // cpg->AddTrack(neu,pxv,pyv,pzv,vtxx,vtxy,vtxz,-1,false);
  // cout << "Info GenieGenerator: neutrino " << neu << "p-rot "<< pout[0] << "
  // fn "<< fn << endl;
  cpg->AddTrack(neu, pout[0], pout[1], pout[2], x, y, z, -1, false);
  IncrementCounter("generated_events");
  if (cc) IncrementCounter("cc_events");
  if (nuel) IncrementCounter("nue_elastic_events");

  // second, outgoing lepton
  pout = Rotate(x, y, zrelative, pxl, pyl, pzl);
  Int_t oLPdgCode = neu;
  if (cc) {
    oLPdgCode = copysign(TMath::Abs(neu) - 1, neu);
  }
  if (nuel) {
    oLPdgCode = 11;
  }
  cpg->AddTrack(oLPdgCode, pout[0], pout[1], pout[2], x, y, z, 0, true);
  IncrementCounter("outgoing_leptons_stored");
  // last, all others
  for (int i = 0; i < nf; i++) {
    pout = Rotate(x, y, zrelative, pxf[i], pyf[i], pzf[i]);
    cpg->AddTrack(pdgf[i], pout[0], pout[1], pout[2], x, y, z, 0, true);
    IncrementCounter("outgoing_hadrons_stored");
    // cout << "f " << pdgf[i] << " pz "<< pzf[i] << endl;
  }

  return kTRUE;
}

Bool_t GenieGenerator::ReadEventGeometryDriver(FairPrimaryGenerator* cpg) {
  // Use GENIE geometry driver.
  // Get event from GENIE TTree. If we reach the end of the file, return
  // false.
  if (fTree->GetEntry(fn) == 0) return kFALSE;

  if (fn % 100 == 0) {
    cout << "Info GenieGenerator: neutrino event-nr " << fn << endl;
  }

  fn++;

  // Add the neutrino to the MCTrack stack:
  cpg->AddTrack(neu,            // Neutrino PDG
                pxv, pyv, pzv,  // Neutrino momentum
                vtxx * m, vtxy * m,
                vtxz * m,  // Event vertex [in cm!]
                -1,        // Parent
                false);    // Don't track this particle
  IncrementCounter("generated_events");
  if (cc) IncrementCounter("cc_events");
  if (nuel) IncrementCounter("nue_elastic_events");
  // Add the outgoing lepton and hadrons, if not in nu-only mode
  if (!fNuOnly) {
    // Add final state lepton to the MCTrack stack:
    int outgoing_lepton_pdg = neu;
    if (cc) outgoing_lepton_pdg = copysign(TMath::Abs(neu) - 1, neu);
    if (nuel) outgoing_lepton_pdg = 11;

    bool track_outgoing_lepton = (cc || nuel);
    cpg->AddTrack(outgoing_lepton_pdg, pxl, pyl, pzl, vtxx * m, vtxy * m,
                  vtxz * m, 0, track_outgoing_lepton);
    IncrementCounter("outgoing_leptons_stored");

    // Add final state hadrons to the MCTrack stack
    for (int i_hadron = 0; i_hadron < nf; i_hadron++) {
      cpg->AddTrack(pdgf[i_hadron], pxf[i_hadron], pyf[i_hadron], pzf[i_hadron],
                    vtxx * m, vtxy * m, vtxz * m, 0, true);
      IncrementCounter("outgoing_hadrons_stored");
    }
  }
  return kTRUE;
}

// -----   Passing the event   ---------------------------------------------
Bool_t GenieGenerator::ReadEvent(FairPrimaryGenerator* cpg) {
  if (fGenOption == 3) return this->ReadEventGeometryDriver(cpg);
  // Read simple event format from GENIE. Vertex positions need to be
  // generated here
  // some start/end positions in z (emulsion to Tracker 1)
  Double_t start[3] = {0., 0., startZ};
  Double_t end[3] = {0., 0., endZ};
  char ts[20];
  // cout << "Enter GenieGenerator " << endl;
  // pick histogram: 1100=100 momentum bins, 1200=25 momentum bins.
  Int_t idbase = 1200;
  if (fFirst) {
    Double_t bparam = 0.;
    Double_t mparam[10];
    bparam = shipgen::MeanMaterialBudget(start, end, mparam);
    cout << "Info GenieGenerator: MaterialBudget " << start[2] << " - "
         << end[2] << endl;
    cout << "Info GenieGenerator: MaterialBudget " << bparam << endl;
    cout << "Info GenieGenerator: MaterialBudget 0 " << mparam[0] << endl;
    cout << "Info GenieGenerator: MaterialBudget 1 " << mparam[1] << endl;
    cout << "Info GenieGenerator: MaterialBudget 2 " << mparam[2] << endl;
    cout << "Info GenieGenerator: MaterialBudget 3 " << mparam[3] << endl;
    cout << "Info GenieGenerator: MaterialBudget 4 " << mparam[4] << endl;
    cout << "Info GenieGenerator: MaterialBudget 5 " << mparam[5] << endl;
    cout << "Info GenieGenerator: MaterialBudget 6 " << mparam[6] << endl;
    cout << "Info GenieGenerator: MaterialBudget " << mparam[0] * mparam[4]
         << endl;
    // read the (log10(p),log10(pt)) hists to be able to draw a pt for every
    // neutrino momentum loop over neutrino types
    printf("Reading (log10(p),log10(pt)) Hists from file: %s\n",
           fInputFile->GetName());
    for (Int_t idnu = 12; idnu < 17; idnu += 2) {
      for (Int_t idadd = -1; idadd < 2; idadd += 2) {
        Int_t idhnu = static_cast<int>(idbase + idnu);
        if (idadd < 0) idhnu += 1000;
        sprintf(ts, "%d", idhnu);
        // pickup corresponding (log10(p),log10(pt)) histogram
        if (fInputFile->FindObjectAny(ts)) {
          TH2* h2tmp = dynamic_cast<TH2*>(fInputFile->Get(ts));
          printf("HISTID=%d, Title:%s\n", idhnu, h2tmp->GetTitle());
          sprintf(ts, "px_%d", idhnu);
          // make its x-projection, to later be able to convert log10(p) to its
          // bin-number
          pxhist[idhnu] = h2tmp->ProjectionX(ts, 1, -1);
          Int_t nbinx = h2tmp->GetNbinsX();
          // printf("idhnu=%d  ts=%s  nbinx=%d\n",idhnu,ts,nbinx);
          // project all slices on the y-axis
          for (Int_t k = 1; k < nbinx + 1; k += 1) {
            sprintf(ts, "h%d%d", idhnu, k);
            // printf("idnu %d idhnu %d bin%d  ts=%s\n",idnu,idhnu,k,ts);
            pyslice[idhnu][k] = h2tmp->ProjectionY(ts, k, k);
          }
        }
      }
    }
    fFirst = kFALSE;
  }

  if (fn == fNevents) {
    LOG(warning) << "End of input file. Rewind.";
  }
  fTree->GetEntry(fn % fNevents);
  fn++;
  if (fn % 100 == 0) {
    LOG(info) << "Info GenieGenerator: neutrino event-nr " << fn << endl;
  }

  // Incoming neutrino, get a random px,py
  Double_t mparam[10];
  Double_t pout[3] = {0., 0., -1.};
  Double_t txnu = 0;
  Double_t tynu = 0;
  // Does this neutrino fly through material? Otherwise draw another pt..
  while (pout[2] < 0.) {
    // get pt of this neutrino from 2D hists.
    Int_t idhnu = TMath::Abs(neu) + idbase;
    if (neu < 0) idhnu += 1000;
    Int_t nbinmx = pxhist[idhnu]->GetNbinsX();
    Double_t pl10 = log10(pzv);
    Int_t nbx = pxhist[idhnu]->FindBin(pl10);
    if (nbx < 1) nbx = 1;
    if (nbx > nbinmx) nbx = nbinmx;
    Double_t ptlog10 = pyslice[idhnu][nbx]->GetRandom();
    // hist was filled with: log10(pt+0.01)
    Double_t pt = pow(10., ptlog10) - 0.01;
    // rotate pt in phi:
    Double_t phi = gRandom->Uniform(0., 2 * TMath::Pi());
    pout[0] = cos(phi) * pt;
    pout[1] = sin(phi) * pt;
    pout[2] = pzv * pzv - pt * pt;

    if (pout[2] >= 0.) {
      pout[2] = TMath::Sqrt(pout[2]);
      if (gRandom->Uniform(-1., 1.) < 0.) pout[0] = -pout[0];
      if (gRandom->Uniform(-1., 1.) < 0.) pout[1] = -pout[1];
      //  xyz at start and end
      start[0] = (pout[0] / pout[2]) * (start[2] - ztarget);
      start[1] = (pout[1] / pout[2]) * (start[2] - ztarget);
      txnu = pout[0] / pout[2];
      tynu = pout[1] / pout[2];
      end[0] = txnu * (end[2] - ztarget);
      end[1] = tynu * (end[2] - ztarget);
      shipgen::MeanMaterialBudget(start, end, mparam);
    }
  }
  // loop over trajectory between start and end to pick an interaction point
  Double_t prob2int = -1.;
  Double_t x = 0.;
  Double_t y = 0.;
  Double_t z = 0.;
  while (prob2int < gRandom->Uniform(0., 1.)) {
    IncrementCounter("interaction_sampling_trials");
    // place x,y,z uniform along path
    z = gRandom->Uniform(start[2], end[2]);
    x = txnu * (z - ztarget);
    y = tynu * (z - ztarget);
    if (mparam[6] < 0.5) {
      // mparam is number of boundaries along path. mparam[6]=0.: uniform
      // material budget along path, use present x,y,z
      prob2int = 2.;
    } else {
      // get local material at this point, to calculate probability that
      // interaction is at this point.
      TGeoNode* node = gGeoManager->FindNode(x, y, z);
      TGeoMaterial* mat = nullptr;
      if (node && !gGeoManager->IsOutside()) {
        mat = node->GetVolume()->GetMaterial();
        // relative to Prob largest density along this trajectory, i.e. use
        // rho(Pt)
        prob2int = mat->GetDensity() / mparam[7];
        if (prob2int > 1.)
          LOG(warning) << " GenieGenerator: prob2int > Maximum density????"
                       << prob2int << " maxrho:" << mparam[7]
                       << " material: " << mat->GetName() << endl;
      } else {
        prob2int = 0.;
      }
    }
  }

  Double_t zrelative = z - ztarget;
  Double_t tof = TMath::Sqrt(x * x + y * y + zrelative * zrelative) /
                 2.99792458e+10;  // speed of light in cm/s
  cpg->AddTrack(
      neu, pout[0], pout[1], pout[2], x, y, z, -1, false,
      TMath::Sqrt(pout[0] * pout[0] + pout[1] * pout[1] + pout[2] * pout[2]),
      tof, mparam[0] * mparam[4]);
  IncrementCounter("generated_events");
  if (cc) IncrementCounter("cc_events");
  if (nuel) IncrementCounter("nue_elastic_events");
  if (!fNuOnly) {
    // second, outgoing lepton
    std::vector<double> pp = Rotate(x, y, zrelative, pxl, pyl, pzl);
    Int_t oLPdgCode = neu;
    if (cc) {
      oLPdgCode = copysign(TMath::Abs(neu) - 1, neu);
    }
    if (nuel) {
      oLPdgCode = 11;
    }
    cpg->AddTrack(oLPdgCode, pp[0], pp[1], pp[2], x, y, z, 0, true, El, tof,
                  mparam[0] * mparam[4]);
    IncrementCounter("outgoing_leptons_stored");
    // last, all others
    for (int i = 0; i < nf; i++) {
      pp = Rotate(x, y, zrelative, pxf[i], pyf[i], pzf[i]);
      cpg->AddTrack(pdgf[i], pp[0], pp[1], pp[2], x, y, z, 0, true, Ef[i], tof,
                    mparam[0] * mparam[4]);
      IncrementCounter("outgoing_hadrons_stored");
      // cout << "f " << pdgf[i] << " pz "<< pzf[i] << endl;
    }
    // cout << "Info GenieGenerator Return from GenieGenerator" << endl;
  }
  return kTRUE;
}
// -------------------------------------------------------------------------
Int_t GenieGenerator::GetNevents() { return fNevents; }
