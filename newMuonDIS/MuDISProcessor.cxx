// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "MuDISProcessor.h"

#include <TFile.h>
#include <TTree.h>

#include <chrono>
#include <cmath>
#include <iomanip>
#include <iostream>

#include "FairLogger.h"
#include "TMath.h"
#include "TROOT.h"
#include "TRandom.h"
#include "TRotation.h"
#include "TSystem.h"
#include "TVectorD.h"

using namespace ShipMuDIS;

namespace {
double DISMinLength(const std::string& label, const MuonPath& path) {
  // Restrict MS to the material tail in accumulated z, with gaps removed.
  return label.find("MS") != label.npos
             ? path.GetLengthAtZ(
                   path.GetstartZ() +
                   std::max(0., path.GetZLength() - kMuonShieldTailZ))
             : 0.;
}
}  // namespace

// -----   Default constructor   -------------------------------------------
MuDISProcessor::MuDISProcessor() {
  ftree = nullptr;
  fouttree = nullptr;

  fLogger = FairLogger::GetLogger();
  fnEvts = -1;
  fstartEvt = 0;
  fPythia = TPythia6::Instance();

  fMinPythiaP = 2;
  fnDIS = 10;
  fP6seed = 0;
}

bool MuDISProcessor::init(const int& aEvts, const int& aStart,
                          const double& aMinPythiaP, const int& aDIS,
                          const int& aSeed, const double& aZmax,
                          const double& aZmin) {
  fnEvts = aEvts;
  fstartEvt = aStart;
  fMinPythiaP = aMinPythiaP;
  if (aDIS <= 0) {
    LOG(warn) << " -- Invalid value passed for nDIS: " << aDIS
              << ", should be strictly positive.";
    return false;
  } else {
    fnDIS = aDIS;
  }
  fP6seed = aSeed;
  fGeoProcessor.SetZmax(aZmax);
  fGeoProcessor.SetZmin(aZmin);
  return true;
}

void MuDISProcessor::initPythia6() {
  // set process 1=QCD, 2=DY/others
  fPythia->SetMSEL(2);
  // Minimum centre-of-mass energy in GeV (not a transverse-momentum cut).
  fPythia->SetPARP(2, fMinPythiaP);
  // disable decay for those PDGID
  unsigned hadrons[10] = {211,  321,  130,  310,  3112,
                          3122, 3222, 3312, 3322, 3334};
  for (unsigned ikf(0); ikf < 10; ++ikf) {
    int kc = fPythia->Pycomp(hadrons[ikf]);
    fPythia->SetMDCY(kc, 1, 0);
  }

  int seed = static_cast<int>(fP6seed % 900000000);
  LOG(info) << " * Pythia6 seed set to " << fP6seed << " wrapped to " << seed
            << std::endl;
  fPythia->SetMRPY(1, seed);
  fPythia->SetMSTU(11, fPythiaOutputUnit);
  LOG(info) << "Pythia6 messages: "
            << (fPythiaOutputUnit == 6 ? "stdout" : "fort.11");
}

void MuDISProcessor::rotate(const TVector3& pvec, const double& theta,
                            const double& phi, TVector3& newp) {
  // Rotate the daughter particle momentum to align with respect to the muon's
  // momentum."""

  TRotation rotation;
  rotation.RotateY(theta);  // Rotate around the Y-axis
  rotation.RotateZ(phi);    // Rotate around the Z-axis

  // Apply the rotation to the momentum vector
  newp = rotation * pvec;
}

Bool_t MuDISProcessor::InitFile(const char* fileName) {
  return InitFile(fileName, 0);
}

Bool_t MuDISProcessor::InitFiles(const std::vector<std::string>& fileNames) {
  return InitFiles(fileNames, 0);
}

// -----   Default constructor   -------------------------------------------
Bool_t MuDISProcessor::InitFile(const char* fileName, const int startEvent) {
  std::vector<std::string> fileNames = {fileName};
  return InitFiles(fileNames, startEvent);
}

Bool_t MuDISProcessor::InitFiles(const std::vector<std::string>& fileNames,
                                 const int startEvent) {
  if (fileNames.empty()) {
    LOG(error) << "MuDISProcessor: no input files provided. "
               << "Check the -f/--inputFile argument or input file glob.";
    return kFALSE;
  }
  for (const auto& fileName : fileNames) {
    if (fileName.empty()) {
      LOG(error) << "MuDISProcessor: received an empty input file name. "
                 << "Check the -f/--inputFile argument.";
      return kFALSE;
    }
  }

  LOG(info) << "Opening input file to find keys " << fileNames.at(0);
  TFile* testFile = TFile::Open(fileNames.at(0).c_str(), "READ");
  auto testKeys = testFile ? testFile->GetListOfKeys() : nullptr;
  if (testKeys == nullptr) {
    delete testFile;
    LOG(error) << "MuDISProcessor: Error opening input file " << fileNames.at(0)
               << ". Check that the path is correct and the file is a readable "
                  "ROOT file.";
    return kFALSE;
  }
  const bool hastree = testKeys->FindObject("cbmsim") != nullptr;
  testFile->Close();
  delete testFile;

  if (hastree) {
    delete ftree;
    ftree = new TChain("cbmsim");
    for (auto& f : fileNames) {
      LOG(info) << "Opening input file " << f;
      ftree->Add(f.c_str());
    }
    int treeEvts = ftree->GetEntries();
    LOG(info) << "Reading " << treeEvts << " entries.";

    bool ok = finEv.Setup(ftree);

    if (!ok) {
      LOG(error)
          << "MuDISProcessor: failed to bind one or more required branches";
      return kFALSE;
    }
    LOG(info) << "MuDISProcessor: Initialization successful.";
    return kTRUE;
  }
  return kFALSE;
}

void MuDISProcessor::process_file(const std::string& input,
                                  const std::string& output) {
  std::vector<std::string> fileNames = {input};
  return process_file(fileNames, output);
}

void MuDISProcessor::process_file(const std::vector<std::string>& input,
                                  const std::string& output) {
  Bool_t treeOK = InitFiles(input);

  if (!treeOK) {
    LOG(error) << " -- Error reading input files: n=" << input.size();
    if (input.size() > 0) LOG(error) << " first file: " << input[0];
    return;
  }

  TFile* outfile = TFile::Open(output.c_str(), "RECREATE");
  if (!outfile) {
    LOG(error) << " -- Error creating outputfile: " << output;
    return;
  }
  outfile->cd();
  fouttree = new TTree(
      "MuonDIS", "Muon information, DIS products and soft interaction tracks");
  foutEv.InitTree(fouttree);

  initPythia6();

  Long64_t n = ftree->GetEntries();
  LOG(info) << " * input tree with " << n << " entries" << std::endl;

  ProcessMuons();

  outfile->cd();
  fouttree->Write();
  outfile->Close();

  fGeoProcessor.PrintVolumes();
}

void MuDISProcessor::initEvent() {
  // soft particles + detector hits
  foutEv.initEvent(100);
  // Number of DIS events generated per volume.
  for (unsigned i(0); i < nMats; ++i) {
    foutEv.br[i].initEvent(fnDIS);
  }
}

void MuDISProcessor::fillMCTracks(const Int_t aIdx) {
  Int_t iEle = 0;
  for (auto& tkIt : (*finEv.MCTrack)) {
    if (iEle == aIdx) foutEv.mcTrks.push_back(tkIt);

    if (tkIt.GetMotherId() == aIdx) {
      std::string procName = tkIt.GetProcName().Data();
      if (procName.find("Muon nuclear interaction") == procName.npos)
        foutEv.mcTrks.push_back(tkIt);
    }
    iEle++;
  }
}

void MuDISProcessor::fillSBTHits(const Int_t aIdx) {
  for (auto& hitIt : (*finEv.sbtPt)) {
    if (hitIt.GetTrackID() == aIdx) {
      foutEv.sbtPt.push_back(hitIt);
    }
  }
}

void MuDISProcessor::fillUBTHits(const Int_t aIdx) {
  for (auto& hitIt : (*finEv.ubtPt)) {
    if (hitIt.GetTrackID() == aIdx) {
      foutEv.ubtPt.push_back(hitIt);
    }
  }
}

void MuDISProcessor::fillSSTHits(const Int_t aIdx) {
  for (auto& hitIt : (*finEv.sstPt)) {
    if (hitIt.GetTrackID() == aIdx) {
      foutEv.sstPt.push_back(hitIt);
    }
  }
}

void MuDISProcessor::fillTDHits(const Int_t aIdx) {
  for (const auto& hit : *finEv.tdPt) {
    if (hit.GetTrackID() == aIdx) foutEv.tdPt.push_back(hit);
  }
}

void MuDISProcessor::generateDISevents(const std::string& tType,
                                       const double& amuonW,
                                       const std::string& aLabel,
                                       const MuonPath& aPath,
                                       MuonDISBranches& aDISBr) {
  // for Pythia beam, just use the initial muon momentum...
  //@FIXME AMM - is this OK ? Reinitialising each time will be too heavy...
  if (aPath.GetNSlices() < 1) {
    LOG(error)
        << " --- calling generateDISevents on an empty path. Doing nothing.";
    return;
  }
  aDISBr.nDISevtsGenerated = 0;
  double P = aPath.GetMomentum(0);
  LOG(debug) << " ** initial mu momentum: " << (*finEv.MCTrack).front().GetP()
             << " Pythia init P: " << P;

  if (P < fMinPythiaP) {
    LOG(info) << " --- calling Pythia initialise with momentum " << P
              << " in material " << aLabel
              << " , min value for Pythia is: " << fMinPythiaP
              << ". Doing nothing.";
    return;
  }
  const Long64_t entry = ftree ? ftree->GetReadEntry() : -1;
  const auto initialize = [&](const char* target) {
    // PYINPR/PYSAVE overwrite these cuts for photon-process mixing.
    // PYGAGA reads them at the NEXT initialization before they are recomputed;
    // a previous, harder muon can otherwise leave an empty photon phase space.
    // Restore our starting cuts (Pythia defaults) for each beam/target pair.
    fPythia->SetCKIN(1, 2.);
    fPythia->SetCKIN(3, 0.);
    LOG(debug1) << std::setprecision(17) << "PYTHIA Initialize BEGIN: entry="
                << entry << " material=" << aLabel << " beam=" << tType
                << " target=" << target << " beamP=" << P
                << " GeV/c MSEL=" << fPythia->GetMSEL()
                << " PARP(2)=" << fPythia->GetPARP(2)
                << " MSTP(14)=" << fPythia->GetMSTP(14)
                << " CKIN(1:4)=" << fPythia->GetCKIN(1) << ","
                << fPythia->GetCKIN(2) << "," << fPythia->GetCKIN(3) << ","
                << fPythia->GetCKIN(4)
                << " CKIN(5)=" << fPythia->GetCKIN(5)
                << " CKIN(77:78)=" << fPythia->GetCKIN(77) << ","
                << fPythia->GetCKIN(78) << std::endl;
    fPythia->Initialize("FIXT", tType.c_str(), target, P);
    LOG(debug1) << "PYTHIA Initialize END: entry=" << entry
                << " material=" << aLabel << " target=" << target
                << std::endl;
  };
  initialize("p+");
  aDISBr.pPythia = P;
  bool isProton = true;
  // print summary of initialisation params
  // fPythia->Pylist(1);

  // Preserve the shield's material-tail restriction in compact z, then sample
  // actual segment length so changes of direction do not bias the vertices.
  const double minLength = DISMinLength(aLabel, aPath);
  double lastxs = 0;
  for (int ia(0); ia < fnDIS; ++ia) {
    LOG(debug) << " ---- Processing DIS event " << ia;
    //@FIXME AMM - half-way through, we change to neutron target with 50-50 :
    //---> update to real material ??
    if (ia == static_cast<int>(fnDIS / 2)) {
      initialize("n0");
      isProton = false;
    }

    // Choose a point on the measured segments, excluding spatial jumps.
    LOG(debug1) << "DIS vertex sampling BEGIN: entry=" << entry
                << " material=" << aLabel << " DIS=" << ia << std::endl;
    unsigned slice = 0;
    const double sampledLength = gRandom->Uniform(minLength, aPath.GetLength());
    double realz = aPath.GetZAtLength(sampledLength, slice);
    double sliceP = aPath.GetMomentum(slice);
    if (sliceP == 0) {
      LOG(error) << " --- Slice in z has momentum " << sliceP
                 << ". Skipping DIS event " << ia;
      continue;
    }

    LOG(debug1) << std::setprecision(17)
                << "PYTHIA GenerateEvent BEGIN: entry=" << entry
                << " material=" << aLabel << " DIS=" << ia
                << " target=" << (isProton ? "p+" : "n0")
                << " beamP=" << P << " sliceP=" << sliceP << " GeV/c"
                << " slice=" << slice << "/" << aPath.GetNSlices()
                << " sampledLength=" << sampledLength << " range=["
                << minLength << "," << aPath.GetLength() << "] cm z="
                << realz << " cm muonWeight=" << amuonW
                << " MRPY(1:6)=" << fPythia->GetMRPY(1) << ","
                << fPythia->GetMRPY(2) << "," << fPythia->GetMRPY(3) << ","
                << fPythia->GetMRPY(4) << "," << fPythia->GetMRPY(5) << ","
                << fPythia->GetMRPY(6) << std::endl;
    const auto generationStart = std::chrono::steady_clock::now();
    fPythia->GenerateEvent();
    const double generationSeconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - generationStart).count();
    LOG(debug1) << "PYTHIA GenerateEvent END: entry=" << entry
                << " material=" << aLabel << " DIS=" << ia
                << " elapsed=" << generationSeconds << " s N="
                << fPythia->GetN() << " MSTI(61)=" << fPythia->GetMSTI(61)
                << std::endl;
    aDISBr.nDISevts++;
    // clean all but final stable particles
    LOG(debug1) << "PYTHIA Pyedit BEGIN: entry=" << entry
                << " material=" << aLabel << " DIS=" << ia << std::endl;
    fPythia->Pyedit(1);
    LOG(debug1) << "PYTHIA Pyedit END: entry=" << entry
                << " material=" << aLabel << " DIS=" << ia
                << " N=" << fPythia->GetN() << std::endl;

    lastxs = fPythia->GetPARI(1);      // in mb
    aDISBr.DISxsec.push_back(lastxs);  // in mb
    aDISBr.DIStarget.push_back(isProton);

    aDISBr.DISvz.push_back(realz);
    aDISBr.DISvx.push_back(aPath.GetX(realz, slice));
    aDISBr.DISvy.push_back(aPath.GetY(realz, slice));
    aDISBr.DISvt.push_back(aPath.GetTimeNs(realz, slice));

    double theta = TMath::ACos(aPath.Getpz(slice) / sliceP);
    // returns phi between -pi and pi
    double phi = TMath::ATan2(aPath.Getpy(slice), aPath.Getpx(slice));

    unsigned ndaugh = fPythia->GetN();
    aDISBr.nDISdau.push_back(ndaugh);

    // loop over daughters and rotate in muon input direction
    for (unsigned itrk(1); itrk < ndaugh + 1; ++itrk) {
      DISparticle adau;
      adau.pid = fPythia->GetK(itrk, 2);
      TVector3 dauP(0, 0, 0);
      TVector3 indauP(fPythia->GetP(itrk, 1), fPythia->GetP(itrk, 2),
                      fPythia->GetP(itrk, 3));
      rotate(indauP, theta, phi, dauP);
      adau.px = dauP.X();
      adau.py = dauP.Y();
      adau.pz = dauP.Z();
      // A spatial rotation leaves the Pythia event-record energy unchanged.
      adau.E = fPythia->GetP(itrk, 4);
      aDISBr.DISparticles.push_back(adau);
    }  // loop on daughters

    //
  }  // loop on DIS events

  aDISBr.nDISevtsGenerated = aDISBr.nDISevts;

  // Normalize to the density integrated over the sampled path interval.
  if (aDISBr.nDISevts > 0)
    aDISBr.wDIS =
        amuonW / aDISBr.nDISevts * aPath.GetWeightedDensity(minLength);

  LOG(debug) << " -- path " << aLabel << " muonW " << amuonW
             << " -- size of DISparticles collections: " << std::endl
             << " ---- particles: " << aDISBr.DISparticles.size() << std::endl
             << " ---- nDIS events: " << aDISBr.nDISevts << std::endl
             << " ---- weightDIS: " << aDISBr.wDIS << std::endl
             << " ---- xsec: ";
  for (int i(0); i < aDISBr.nDISevts; ++i) {
    LOG(debug) << aDISBr.DISxsec[i] << " ";
  }
  LOG(debug) << " ---- vertex: ";
  for (int i(0); i < aDISBr.nDISevts; ++i) {
    LOG(debug) << "(" << aDISBr.DISvx[i] << "," << aDISBr.DISvy[i] << ","
               << aDISBr.DISvz[i] << "," << aDISBr.DISvt[i] << ") ";
  }
}

void MuDISProcessor::ProcessMuons() {
  LOG(info) << " * Start of event loop" << std::endl;
  fGeoProcessor.ResetDiagnostics();

  if (static_cast<Long64_t>(fstartEvt) >= ftree->GetEntries()) {
    LOG(error) << " ** Trying to start from event " << fstartEvt
               << " which is greater than the tree entries: "
               << ftree->GetEntries() << ". Doing nothing...";
    return;
  }

  const Long64_t nEntries =
      fnEvts >= 0 ? std::min(static_cast<Long64_t>(fstartEvt + fnEvts),
                             ftree->GetEntries())
                  : ftree->GetEntries();
  LOG(info) << " - Processing event " << fstartEvt << " to event "
            << nEntries - 1 << std::endl;

  unsigned nplus = 0;
  unsigned nminus = 0;
  unsigned skipMu_pmin = 0;
  unsigned skipMu_acc = 0;
  unsigned skipEvt = 0;
  double wplus = 0.;
  double wminus = 0.;
  double skipMu_pminW = 0.;
  double skipMu_accW = 0.;
  double skipMu_pathW = 0.;

  struct PathTotals {
    Long64_t muons = 0;
    double weight = 0.;
    double length = 0.;
    double weightedLength = 0.;
    void Add(double w, double l) {
      ++muons;
      weight += w;
      length += l;
      weightedLength += w * l;
    }
  };
  PathTotals pathTotals;
  std::array<PathTotals, nMats> pathTotalsByMat = {};

  for (Long64_t iEvent = static_cast<Long64_t>(fstartEvt); iEvent < nEntries;
       ++iEvent) {
    LOG(debug) << " --- Processing event " << iEvent << std::endl;
    if (iEvent % 100 == 0)
      LOG(info) << " --- Processing event " << iEvent << std::endl;
    if (!finEv.PrepareEntry(ftree, iEvent) || ftree->GetEntry(iEvent) <= 0) {
      LOG(error) << " --- Error reading tree entry: " << iEvent;
      skipEvt++;
      continue;
    }

    if (finEv.MCTrack == nullptr) {
      skipEvt++;
      continue;
    }

    unsigned nTr = (*finEv.MCTrack).size();
    if (nTr == 0) {
      skipEvt++;
      continue;
    }
    // interested in the first muon track - for PG setting
    //@FIXME AMM adapt also to MuonBack input, take all muons?
    // for now take MCTrack[0]
    Int_t muIdx = 0;

    ShipMCTrack& track = (*finEv.MCTrack)[static_cast<unsigned>(muIdx)];
    int pid = track.GetPdgCode();
    double muW = track.GetWeight();

    double mup = track.GetP();

    if (mup < fMinPythiaP) {
      LOG(debug) << iEvent << " skipped: muon momentum " << mup
                 << " below min value for Pythia:" << fMinPythiaP;
      skipMu_pmin++;
      skipMu_pminW += muW;
      continue;
    }

    std::string targetType;
    if (pid == -13) {
      nplus++;
      wplus += muW;
      targetType = "gamma/mu+";
    } else if (pid == 13) {
      nminus++;
      wminus += muW;
      targetType = "gamma/mu-";
    } else {
      LOG(warning) << iEvent << " skipped: "
                   << " nTracks= " << nTr
                   << " -- 1st track pid not a muon: " << pid << std::endl;
      skipEvt++;
      continue;
    }

    initEvent();
    fillMCTracks(muIdx);
    fillUBTHits(muIdx);
    fillSBTHits(muIdx);
    fillSSTHits(muIdx);
    fillTDHits(muIdx);

    // Count events which have no hit in UBT, SBT, SST or TD, muon just
    // flying out of vessel acceptance never bouncing back... For those, very
    // numerous in the cudaMu files, skip to optimise processing.
    //@FIXME AM to do: a study of whether the events created in the last lambda
    // of MS could still contribute or would hit UBT...
    if (foutEv.ubtPt.size() == 0 && foutEv.sbtPt.size() == 0 &&
        foutEv.sstPt.size() == 0 && foutEv.tdPt.size() == 0) {
      LOG(debug) << " Counting muon event with no hit " << iEvent
                 << " UBT Hits: " << foutEv.ubtPt.size()
                 << ", SBT Hits: " << foutEv.sbtPt.size()
                 << ", SST Hits: " << foutEv.sstPt.size()
                 << ", TD Hits: " << foutEv.tdPt.size() << std::endl;
      skipMu_acc++;
      skipMu_accW += muW;
      // counting, but want to still fill DIS in MS (and UBT detector)...
      // continue;
    }

    LOG(debug) << " -- size of hits collections: " << std::endl
               << " ---- mcTracks: " << foutEv.mcTrks.size() << std::endl
               << " ---- UBT Hits: " << foutEv.ubtPt.size() << std::endl
               << " ---- SBT Hits: " << foutEv.sbtPt.size() << std::endl
               << " ---- SST Hits: " << foutEv.sstPt.size() << std::endl;

    // retrieve a map of material label, with same density, and lengths, and
    // [zin,zout] ranges
    if (!fGeoProcessor.initialise(foutEv)) {
      skipEvt++;
      skipMu_pathW += muW;
      continue;
    }
    std::map<std::string, MuonPath>& lPathMap = fGeoProcessor.FillMuonPath();

    if (lPathMap.size() == 0) {
      LOG(error) << " -- No elements in path... Not doing anything...";
      skipEvt++;
      skipMu_pathW += muW;
      continue;
    }

    // Persist the intervals used for DIS vertex sampling, including the MS
    // restriction. Keep REST separately, but exclude it from the total.
    for (unsigned i = 0; i < nMats; ++i) {
      const auto path = lPathMap.find(MatTypeStr[i].Data());
      if (path == lPathMap.end() || path->second.GetNSlices() < 1) continue;
      // Crossed but not generated (including REST) is distinct from unvisited.
      foutEv.br[i].nDISevtsGenerated = 0;
      foutEv.pathLengthByMat[i] =
          path->second.GetLength() - DISMinLength(path->first, path->second);
      if (i != REST) foutEv.pathLength += foutEv.pathLengthByMat[i];
      if (foutEv.pathLengthByMat[i] > 0.)
        pathTotalsByMat[i].Add(muW, foutEv.pathLengthByMat[i]);
    }

    // loop over the map, and do nDIS event in each element, with weight
    // length*density. That way, do only once the calculation of the path, and
    // plenty of DIS in each material. fill a branch with weight = path
    // length*density.
    // Discarding REST: many muons go through CONCRETE,no need to record DIS
    // there....
    for (unsigned i(0); i < nMats - 1; ++i) {
      if (lPathMap.find(MatTypeStr[i].Data()) != lPathMap.end())
        generateDISevents(targetType, muW, MatTypeStr[i].Data(),
                          lPathMap.find(MatTypeStr[i].Data())->second,
                          foutEv.br[i]);
    }

    fouttree->Fill();
    pathTotals.Add(muW, foutEv.pathLength);

  }  // loop on events

  LOG(info) << "Found " << nplus << " mu+ and " << nminus << " mu-."
            << std::endl
            << "Skipped: " << skipEvt << " events and " << skipMu_pmin
            << " muons with too low p" << std::endl
            << "Counted: " << skipMu_acc
            << " muons with no recorded hits in UBT,SBT,SST,TD.";
  LOG(info) << "Weighted counts (sum MCTrack[0].fW): " << wplus << " mu+ and "
            << wminus << " mu- (after momentum cut)." << std::endl
            << "Skipped (sum MCTrack[0].fW): " << skipMu_pminW
            << " with too low p, " << skipMu_pathW
            << " muons with invalid or empty paths." << std::endl
            << "Counted (sum MCTrack[0].fW): " << skipMu_accW
            << " muons with no recorded hits in UBT,SBT,SST,TD.";
  fGeoProcessor.PrintDiagnostics();
  // Print additive quantities so jobs can be combined before taking means.
  LOG(info) << std::setprecision(17)
            << "Muon path totals (cm, excluding REST): output muons = "
            << pathTotals.muons << ", sum(fW) = " << pathTotals.weight
            << ", sum(L) = " << pathTotals.length
            << ", sum(fW*L) = " << pathTotals.weightedLength;
  for (unsigned i = 0; i < nMats; ++i) {
    const auto& totals = pathTotalsByMat[i];
    LOG(info) << std::setprecision(17) << "Muon path totals " << MatTypeStr[i]
              << " (cm): crossing muons = " << totals.muons
              << ", sum(fW) = " << totals.weight
              << ", sum(L) = " << totals.length
              << ", sum(fW*L) = " << totals.weightedLength;
  }
}
