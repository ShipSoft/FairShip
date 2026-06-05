#include "MuDISProcessor.h"

#include <iostream>
#include <cmath>

#include <TFile.h>
#include <TTree.h>

#include "FairLogger.h"
#include "TMath.h"
#include "TROOT.h"
#include "TRandom.h"
#include "TSystem.h"
#include "TVectorD.h"


// -----   Default constructor   -------------------------------------------
MuDISProcessor::MuDISProcessor() {
  ftree=0;
  fouttree=0;
  
  fLogger = FairLogger::GetLogger();
  fnEvts=-1;
  fPythia = TPythia6::Instance();
  fPDG = TDatabasePDG::Instance();

  fnDIS = 10;
  fP6seed = 0;

}

void MuDISProcessor::init(const int & aEvts, const int & aDIS, const int & aSeed){
  fnEvts=aEvts;
  fnDIS=aDIS;
  fP6seed = aSeed;
}

void MuDISProcessor::initPythia6(){

  //set process 1=QCD, 2=DY/others
  fPythia->SetMSEL(2);
    //set min hard scale: 2 GeV --->try 1.5 for soft muons ?
  fPythia->SetPARP(2, 2);
  //disable decay for those PDGID
  unsigned hadrons[10] = {
    211, 321, 130, 310, 3112,
    3122, 3222, 3312, 3322, 3334
  };
  for (unsigned ikf(0); ikf<10;++ikf){ 
    int kc = fPythia->Pycomp(hadrons[ikf]);
    fPythia->SetMDCY(kc, 1, 0);
  }

  int seed = static_cast<int>(fP6seed % 900000000);
  LOG(info) << "Pythia6 seed set to " << fP6seed << " wrapped to " << seed << std::endl;
  fPythia->SetMRPY(1, seed);
  fPythia->SetMSTU(11, 11);
}

void MuDISProcessor::rotate(const TVector3 & pvec,
			    const double & theta,
			    const double & phi,
			    TVector3 & newp)
{
  //Rotate the daughter particle momentum to align with respect to the muon's momentum."""

  TRotation rotation;
  rotation.RotateY(theta);  // Rotate around the Y-axis
  rotation.RotateZ(phi);  // Rotate around the Z-axis

  // Apply the rotation to the momentum vector
  newp = rotation * pvec; 
}


void MuDISProcessor::process_file(const std::string& input,
				  const std::string& output)
{
  TFile *infile = TFile::Open(input.c_str(), "READ");
  if (!infile) return;
  ftree = (TTree*)infile->Get("cbmsim");
  
  if (!ftree) return;
  finEv.Setup(ftree);
  
  TFile *outfile = TFile::Open(output.c_str(), "RECREATE");
  outfile->cd();
  fouttree = new TTree("MuonDIS", "Muon information, DIS products and soft interaction tracks");
  foutEv.InitTree(fouttree);

  initPythia6();
  
  Long64_t n = ftree->GetEntries();
  LOG(info) << " tree with " << n << " entries" << std::endl;  

  ProcessMuons();
  
  outfile->cd();
  fouttree->Write();
  outfile->Close();
  infile->Close();
}

void MuDISProcessor::initEvent(){
  foutEv.mcTrks.clear();
  foutEv.mcTrks.reserve(20);
  foutEv.ubtPt.clear();
  foutEv.ubtPt.reserve(1);
  foutEv.sbtPt.clear();
  foutEv.sbtPt.reserve(30);
  foutEv.sstPt.clear();
  foutEv.sstPt.reserve(32);
  foutEv.brMS.initEvent(fnDIS);
  foutEv.brUBT.initEvent(fnDIS);
  foutEv.brSBT.initEvent(fnDIS);
  foutEv.brSST.initEvent(fnDIS);
  foutEv.brREST.initEvent(fnDIS);
}

void  MuDISProcessor::fillMCTracks(const Int_t aIdx)
{
  Int_t iEle = 0;
  for (auto& tkIt: (*finEv.MCTrack))
    {
      if (iEle==aIdx) foutEv.mcTrks.push_back(tkIt);
      
      if (tkIt.GetMotherId() == aIdx){
	std::string procName = tkIt.GetProcName().Data();
	if (procName.find("Muon nuclear interaction")==procName.npos) foutEv.mcTrks.push_back(tkIt);
      }
      iEle++;
    }
}

void  MuDISProcessor::fillSBTHits(const Int_t aIdx)
{
  for (auto& hitIt: (*finEv.sbtPt))
    {
      if (hitIt.GetTrackID()==aIdx){
	foutEv.sbtPt.push_back(hitIt);
      }
    }
}

void  MuDISProcessor::fillUBTHits(const Int_t aIdx)
{
  for (auto& hitIt: (*finEv.ubtPt))
    {
      if (hitIt.GetTrackID()==aIdx){
	foutEv.ubtPt.push_back(hitIt);
      }
    }
}

void  MuDISProcessor::fillSSTHits(const Int_t aIdx)
{
  for (auto& hitIt: (*finEv.sstPt))
    {
      if (hitIt.GetTrackID()==aIdx){
	foutEv.sstPt.push_back(hitIt);
      }
    }
}


void MuDISProcessor::generateDISevents(const std::string & tType,
				       const std::string & aLabel,
				       const Path & aPath,
				       MuonDISBranches & aDISBr)
{

  fPythia->Initialize("FIXT", tType.c_str(), "p+", aPath.P);  // target = "p+"
  bool isProton = true;
  //print summary of initialisation params
  fPythia->Pylist(1);

  double theta = TMath::ACos(aPath.pz / aPath.P);
  //returns phi between -pi and pi
  double phi = TMath::ATan2(aPath.py,aPath.px);


  for (int ia(0); ia < fnDIS; ++ia)
    {
      //half-way through, we change to neutron target with 50-50 : ---> update to real material ??
      if (ia == static_cast<int>(fnDIS / 2)){
	fPythia->Initialize("FIXT", tType.c_str(), "n0", aPath.P);  // target = "n0"
	isProton = false;
      }
      
      fPythia->GenerateEvent();
      aDISBr.nDISevts++;
      //clean all but final stable particles
      fPythia->Pyedit(1);
	  
      aDISBr.DISxsec.push_back(fPythia->GetPARI(1)); //in mb
      aDISBr.DIStarget.push_back(isProton);
      // choose a random vertex position to set to all daughters
      double vtx_z = gRandom->Uniform(aPath.startZ, aPath.endZ);
      aDISBr.DISvz.push_back(vtx_z);
      aDISBr.DISvx.push_back(aPath.GetX(vtx_z));
      aDISBr.DISvy.push_back(aPath.GetY(vtx_z));
      aDISBr.DISvt.push_back(aPath.GetTimeNs(vtx_z));

      unsigned ndaugh = fPythia->GetN();
      aDISBr.nDISdau.push_back(ndaugh);
	  
      //loop over daughters and rotate in muon input direction
      for (unsigned itrk(1); itrk<ndaugh + 1; ++itrk)
	{
	  DISparticle adau;
	  adau.pid = fPythia->GetK(itrk, 2);
	  TVector3 dauP(0,0,0);
	  TVector3 indauP(fPythia->GetP(itrk, 1),
			  fPythia->GetP(itrk, 2),
			  fPythia->GetP(itrk, 3));
	  rotate(indauP,theta,phi,dauP);
	  adau.px = dauP.X();
	  adau.py = dauP.Y();
	  adau.pz = dauP.Z();
	  double psq = dauP.Mag2();
	  double masssq = pow(fPDG->GetParticle(adau.pid)->Mass(),2);
	  adau.E = TMath::Sqrt(masssq + psq);
	  aDISBr.DISparticles.push_back(adau);
	}//loop on daughters

      //	  
    }//loop on DIS events
  
  LOG(info) << " -- path " << aLabel
	    << " -- size of DISparticles collections: " << std::endl
	    << " ---- particles: " << aDISBr.DISparticles.size() << std::endl
	    << " ---- nDIS events: " << aDISBr.nDISevts << std::endl
	    << " ---- xsec: " ;
  for (int i(0);i<aDISBr.nDISevts;++i){
    LOG(info) << aDISBr.DISxsec[i] << " " ;
  }
  LOG(info) << " ---- vertex: " ;
  for (int i(0);i<aDISBr.nDISevts;++i){
    LOG(info) << "(" << aDISBr.DISvx[i] << ","
	      << aDISBr.DISvy[i] << ","
	      << aDISBr.DISvz[i] << ","
	      << aDISBr.DISvt[i] << ") ";
  }
  
}


void MuDISProcessor::ProcessMuons()
{
  LOG(info) << "Start of event loop" << std::endl;
  
  const Long64_t nEntries = fnEvts>0 ? std::min(static_cast<Long64_t>(fnEvts),ftree->GetEntries()) : ftree->GetEntries();
  LOG(info) << "- Processing " << nEntries << " events" << std::endl;

  unsigned nplus=0;
  unsigned nminus=0;
  
  for (Long64_t iEvent = 0; iEvent < nEntries; ++iEvent)
    {
      if (iEvent%100==0) LOG(info) << "- Processing event " << iEvent << std::endl;
      ftree->GetEntry(iEvent);

      if (finEv.MCTrack==nullptr) continue;
      
      unsigned nTr = (*finEv.MCTrack).size();
      if (nTr==0) continue;
      
      //interested in the first muon track - for PG setting
      //@FIXME AMM adapt also to MuonBack input, take all muons?
      //for now take MCTrack[0]
      Int_t muIdx = 0;
      
      ShipMCTrack & track = (*finEv.MCTrack)[static_cast<unsigned>(muIdx)];
      int pid = track.GetPdgCode();
      
      if (pid==13) nplus++;
      else if (pid==-13) nminus++;
      else {
	LOG(warning) << iEvent << " skipped: "
		     << " nTracks= " << nTr
		     << " -- 1st track pid not a muon: " << pid
		     << std::endl;
	continue;
      }
      
      initEvent();
      fillMCTracks(muIdx);
      fillUBTHits(muIdx);
      fillSBTHits(muIdx);
      fillSSTHits(muIdx);
      
      LOG(info) << " -- size of hits collections: " << std::endl
		<< " ---- mcTracks: " << foutEv.mcTrks.size() << std::endl
		<< " ---- UBT Hits: " << foutEv.ubtPt.size() << std::endl
		<< " ---- SBT Hits: " << foutEv.sbtPt.size() << std::endl
		<< " ---- SST Hits: " << foutEv.sstPt.size() << std::endl;
      
      
      std::string targetType;
      if (pid==13) targetType="gamma/mu+";
      else targetType="gamma/mu-";

      //retrieve a map of material label, with same density, and lengths, and [zin,zout] ranges
      fGeoProcessor.initialise(foutEv);
      std::map<std::string,Path> & lPathMap = fGeoProcessor.FillMuonPath();

      if (lPathMap.size()==0){
	LOG(error) << " -- No elements in path... Not doing anything...";
	continue;
      }
      
      //loop over the map, and do nDIS event in each element, with weight length*density. That way, do only once the calculation of the path, and plenty of DIS in each material.
      //fill a branch with weight = path length*density.
      if (lPathMap.find("MS")!=lPathMap.end())
	generateDISevents(targetType,"MS",lPathMap.find("MS")->second,foutEv.brMS);
      if (lPathMap.find("UBT")!=lPathMap.end())
	generateDISevents(targetType,"UBT",lPathMap.find("UBT")->second,foutEv.brUBT);
      if (lPathMap.find("SBT")!=lPathMap.end())
	generateDISevents(targetType,"SBT",lPathMap.find("SBT")->second,foutEv.brSBT);
      if (lPathMap.find("SST")!=lPathMap.end())
	generateDISevents(targetType,"SST",lPathMap.find("SST")->second,foutEv.brSST);
      if (lPathMap.find("REST")!=lPathMap.end())
	generateDISevents(targetType,"REST",lPathMap.find("REST")->second,foutEv.brREST);
      
      fouttree->Fill();
      
    }//loop on events
  
  LOG(info) << "Found " << nplus << " mu+ and "
	    << nminus << " mu-."
	    << std::endl;
  // fPythia->SetMSTU(11, 6)
  // logging.info(
  //    f"DIS generated for muons (index {first_mu_event} - {last_mu_event - 1}) , output saved in {args.outputFile}, nDISPerMuon = {args.nDIS}"
  // )
}
