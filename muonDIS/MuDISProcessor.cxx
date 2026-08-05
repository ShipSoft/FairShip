#include "MuDISProcessor.h"

#include <TFile.h>
#include <TTree.h>

#include <cmath>
#include <iostream>

#include "FairLogger.h"
#include "TMath.h"
#include "TROOT.h"
#include "TRandom.h"
#include "TSystem.h"
#include "TVectorD.h"

using namespace ShipMuDIS;

// -----   Default constructor   -------------------------------------------
MuDISProcessor::MuDISProcessor() {
  ftree = 0;
  fouttree = 0;

  fLogger = FairLogger::GetLogger();
  fnEvts = -1;
  fPythia = TPythia6::Instance();
  fPDG = TDatabasePDG::Instance();

  fMinPythiaP = 2;
  fnDIS = 10;
  fP6seed = 0;

  fGeoProcessor.CheckAllVolumes();
}

void MuDISProcessor::init(const int& aEvts, const double& aMinPythiaP,
			  const int& aDIS, const int& aSeed,
                          const double& aZmax, const double& aZmin) {
  fnEvts = aEvts;
  fMinPythiaP = aMinPythiaP;
  fnDIS = aDIS;
  fP6seed = aSeed;
  fGeoProcessor.SetZmax(aZmax);
  fGeoProcessor.SetZmin(aZmin);
  fGeoProcessor.FillZmaxVolumes();
}

void MuDISProcessor::initPythia6() {
  // set process 1=QCD, 2=DY/others
  fPythia->SetMSEL(2);
  // set min hard scale: 2 GeV --->try 1.5 for soft muons ?
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
  // To direct specific verbose Pythia6 output to a special file.
  fPythia->SetMSTU(11, 11);
  // For standard output stream it would be:
  // fPythia->SetMSTU(11, 6);
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
  return InitFile(fileName,0);
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
    LOG(error) << "MuDISProcessor: Error opening input file "
               << fileNames.at(0)
               << ". Check that the path is correct and the file is a readable "
                  "ROOT file.";
    return kFALSE;
  }  
  const bool hastree =
    testKeys->FindObject("cbmsim") != nullptr;
  testFile->Close();
  delete testFile;

  if (hastree) {
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
  return process_file(fileNames,output);
}

void MuDISProcessor::process_file(const std::vector<std::string>& input,
                                  const std::string& output) {

  Bool_t treeOK = InitFiles(input);

  if (!treeOK) {
    LOG(error) << " -- Error reading input files: " << input.size() << " first file: " << input[0];
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
  for (unsigned i(0);i<nMats;++i) foutEv.br[i].initEvent(fnDIS);
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

void MuDISProcessor::generateDISevents(const std::string& tType,
				       const double& amuonW,
                                       const std::string& aLabel,
                                       const MuonPath& aPath,
                                       MuonDISBranches& aDISBr) {
  // for Pythia beam, just use the initial muon momentum...
  //@FIXME AMM - is this OK ? Reinitialising each time will be too heavy...
  if (aPath.GetNSlices()<1) {
    LOG(error) << " --- calling generateDISevents on an empty path. Doing nothing.";
    return;
  }
  double P = aPath.GetMomentum(0);
  if (P<fMinPythiaP) {
    LOG(info) << " --- calling Pythia initialise with momentum " << P << " in material " << aLabel
	      << " , min value for Pythia is: " << fMinPythiaP << ". Doing nothing.";
    return;
  }
  fPythia->Initialize("FIXT", tType.c_str(), "p+", P);  // target = "p+"
  bool isProton = true;
  // print summary of initialisation params
  fPythia->Pylist(1);

  double lastxs = 0;
  for (int ia(0); ia < fnDIS; ++ia) {
    LOG(debug) << " ---- Processing DIS event " << ia;
    //@FIXME AMM - half-way through, we change to neutron target with 50-50 :
    //---> update to real material ??
    if (ia == static_cast<int>(fnDIS / 2)) {
      fPythia->Initialize("FIXT", tType.c_str(), "n0", P);  // target = "n0"
      isProton = false;
    }

    fPythia->GenerateEvent();
    aDISBr.nDISevts++;
    // clean all but final stable particles
    fPythia->Pyedit(1);

    lastxs = fPythia->GetPARI(1);      // in mb
    aDISBr.DISxsec.push_back(lastxs);  // in mb
    aDISBr.DIStarget.push_back(isProton);

    // choose a random vertex position to set to all daughters
    // Take into account "broken" paths with different slices in z.
    
    double vtx_z = 0;
    //restrict to last lambda for MS...
    if (aLabel.find("MS")!=aLabel.npos) vtx_z = gRandom->Uniform(std::max(aPath.GetstartZ(),aPath.GetstartZ() + aPath.GetZLength() - 20),
								 aPath.GetstartZ() + aPath.GetZLength());
    else vtx_z = gRandom->Uniform(aPath.GetstartZ(),
				  aPath.GetstartZ() + aPath.GetZLength());
    
    // put back to real Z position for paths with different slices in z.
    unsigned slice = 0;
    double realz = aPath.GetZ(vtx_z, slice);
    aDISBr.DISvz.push_back(realz);
    aDISBr.DISvx.push_back(aPath.GetX(realz, slice));
    aDISBr.DISvy.push_back(aPath.GetY(realz, slice));
    aDISBr.DISvt.push_back(aPath.GetTimeNs(realz, slice));
    double sliceP = aPath.GetMomentum(slice);
    if (sliceP==0) {
      LOG(error) << " --- Slice in z has momentum " << sliceP << ". Skipping DIS event " << ia;
      continue;
    }
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
      double psq = dauP.Mag2();
      double masssq = pow(fPDG->GetParticle(adau.pid)->Mass(), 2);
      adau.E = TMath::Sqrt(masssq + psq);
      aDISBr.DISparticles.push_back(adau);
    }  // loop on daughters

    //
  }  // loop on DIS events

  // calculate weight
  // times length divided by length, length cancels out...
  if (fnDIS>0)
    aDISBr.wDIS = amuonW * lastxs / fnDIS * aPath.GetWeightedDensity();

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

  const Long64_t nEntries =
      fnEvts > 0 ? std::min(static_cast<Long64_t>(fnEvts), ftree->GetEntries())
                 : ftree->GetEntries();
  LOG(info) << " - Processing " << nEntries << " events" << std::endl;

  unsigned nplus = 0;
  unsigned nminus = 0;
  unsigned skipMu_pmin = 0;
  unsigned skipMu_acc = 0;
  unsigned skipEvt = 0;
  
  for (Long64_t iEvent = 0; iEvent < nEntries; ++iEvent) {
    LOG(debug) << " --- Processing event " << iEvent << std::endl;
    if (iEvent % 1000 == 0)
      LOG(info) << " --- Processing event " << iEvent/1000 << "k" << std::endl;
    Long64_t bytes = ftree->GetEntry(iEvent);

    if (bytes <= 0) {
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
    
    double mup =  track.GetP();

    if (mup < fMinPythiaP){
      LOG(debug) << iEvent << " skipped: muon momentum "
		 << mup << " below min value for Pythia:"
		 << fMinPythiaP;
      skipMu_pmin++;
      continue;
    }

    std::string targetType;
    if (pid == -13){
      nplus++;
      targetType = "gamma/mu+";
    }
    else if (pid == 13){
      nminus++;
      targetType = "gamma/mu-";
    }
    else {
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

    //Count events which have no hit in either UBT, SBT or SST, muon just flying out of vessel acceptance never bouncing back...
    //For those, very numerous in the cudaMu files, skip to optimise processing.
    //@FIXME AM to do: a study of whether the events created in the last lambda of MS could still contribute or would hit UBT...
    if (foutEv.ubtPt.size()==0 && foutEv.sbtPt.size()==0 && foutEv.sstPt.size() == 0) {
      LOG(debug) << " Skipping muon event " << iEvent
		 << " UBT Hits: " << foutEv.ubtPt.size()
		 << ", SBT Hits: " << foutEv.sbtPt.size()
		 << ", SST Hits: " << foutEv.sstPt.size()
		 << std::endl;
      skipMu_acc++;
      //counting, but want to still fill DIS in MS (and UBT detector)...
      continue;
    }

    
    LOG(debug) << " -- size of hits collections: " << std::endl
               << " ---- mcTracks: " << foutEv.mcTrks.size() << std::endl
               << " ---- UBT Hits: " << foutEv.ubtPt.size() << std::endl
               << " ---- SBT Hits: " << foutEv.sbtPt.size() << std::endl
               << " ---- SST Hits: " << foutEv.sstPt.size() << std::endl;

    // retrieve a map of material label, with same density, and lengths, and
    // [zin,zout] ranges
    fGeoProcessor.initialise(foutEv);
    std::map<std::string, MuonPath>& lPathMap = fGeoProcessor.FillMuonPath();

    if (lPathMap.size() == 0) {
      LOG(error) << " -- No elements in path... Not doing anything...";
      skipMu_acc++;
      continue;
    }

    // loop over the map, and do nDIS event in each element, with weight
    // length*density. That way, do only once the calculation of the path, and
    // plenty of DIS in each material. fill a branch with weight = path
    // length*density.
    // Discarding REST: many muons go through CONCRETE,no need to record DIS there....
    for (unsigned i(0);i<nMats-1;++i){
      if (lPathMap.find(MatTypeStr[i].Data()) != lPathMap.end())
	generateDISevents(targetType,muW,
			  MatTypeStr[i].Data(),
			  lPathMap.find(MatTypeStr[i].Data())->second,
			  foutEv.br[i]);
    }

    fouttree->Fill();
    
  }  // loop on events

  LOG(info) << "Found " << nplus << " mu+ and " << nminus << " mu-."
            << std::endl
	    << "Skipped: " << skipEvt << " events and "
	    << skipMu_pmin << " muons with too low p, "
	    << skipMu_acc << " muons outside of acceptance.";
}
