#include "Pythia8/Pythia.h"
#include "algorithm"
#include "TCanvas.h"
#include "TGraphErrors.h"
#include "TFile.h"
#include "TH1F.h"
#include "TH2F.h"
#include "TRandom3.h"
#include "TTree.h"

using namespace Pythia8;

//global counters

unsigned nP;
unsigned nN;
unsigned nG;
unsigned nPiP;
unsigned nPiM;
unsigned nPi0;
unsigned nEta;
unsigned nOmega;
unsigned nEtaPrime;

void pythiaSettings(Pythia & fPythia,
            const int idA,
            const int idB,
            const Vec4 & p4A,
            const unsigned doAllQCD,
            const unsigned frameType){
  
  fPythia.readString("Print:quiet = on");

  //fPythia.readString("Init:showChangedSettings = on");
  
  if (doAllQCD==1) fPythia.readString("SoftQCD:all = on");
  else if (doAllQCD==2) {
    fPythia.readString("SoftQCD:all = off");
    fPythia.readString("SoftQCD:nonDiffractive = on");
  }
  else if (doAllQCD==3){
    fPythia.readString("SoftQCD:all = off");
    fPythia.readString("SoftQCD:nonDiffractive = off");
    fPythia.readString("SoftQCD:elastic = on");
    fPythia.readString("SoftQCD:singleDiffractive = on");
    fPythia.readString("SoftQCD:doubleDiffractive = on");
    fPythia.readString("SoftQCD:centralDiffractive = on"); 
  }
  
  fPythia.settings.mode("Beams:idA",  idA);
  fPythia.settings.mode("Beams:idB",  idB);
  fPythia.settings.mode("Beams:frameType", frameType);
  if (frameType==2){
    fPythia.settings.parm("Beams:eA",p4A.e());
    fPythia.settings.parm("Beams:eB",0.);
  } else {
    fPythia.settings.parm("Beams:pxA",p4A.px());
    fPythia.settings.parm("Beams:pyA",p4A.py());
    fPythia.settings.parm("Beams:pzA",p4A.pz());
    fPythia.settings.parm("Beams:pxB",0.);
    fPythia.settings.parm("Beams:pyB",0.);
    fPythia.settings.parm("Beams:pzB",0.);
  }

}


bool runPythia(const int idA,
           const int idB,
           const Vec4 & p4A,
           const unsigned doAllQCD,
           const unsigned frameType,
           std::vector<Particle> & aStash,
           std::vector<Particle> & aMesons,
           const unsigned aIteration){
  // Generator. Process selection. LHC initialization. Histogram.
  Pythia fPythia("../share/Pythia8/xmldoc",false);

  //need to reinitialise the seed each time: or will produce same events....
  fPythia.readString("Random:setSeed = on");  
  std::ostringstream lseed;
  lseed << "Random:seed = " << 0;//aIteration;
  fPythia.readString(lseed.str());

  pythiaSettings(fPythia,idA,idB,p4A,doAllQCD,frameType);

  if (!fPythia.init()) return false;
  std::cout << fPythia.settings.output("Random:seed") << std::endl;
  
  std::cout << " -- Doing " << idA << " pz=" << p4A.pz() << " on " << idB << " collision." << std::endl;

  
  if (!fPythia.next()) return false;
  for(int i=0; i<fPythia.event.size(); i++){
    Particle lP = fPythia.event[i];
    //apply some kinematic selection: below MMIN=2GeV+m(beam particles), Pythia fails to calculate XS properly.
    //remove beam particles, status 12 or negative.
    //choose a value for min threshold, here 10 GeV, to consider it as interesting to make a cascade event.
    //Too low pz = not boosted enough = not interesting.
    if (lP.pz()>10. && lP.status()>0 && lP.status() != 12){
      if (abs(lP.id())==2212) {aStash.push_back(lP); nP++;}
      if (abs(lP.id())==2112) {aStash.push_back(lP); nN++;}
      if (abs(lP.id())==211)  {aStash.push_back(lP); if (lP.id()>0) nPiP++; else nPiM++;}
    }
    if (lP.id()==111)  {aMesons.push_back(lP); nPi0++;}
    if (lP.id()==221)  {aMesons.push_back(lP); nEta++;}
    if (lP.id()==223)  {aMesons.push_back(lP); nOmega++;}
    if (lP.id()==331)  {aMesons.push_back(lP); nEtaPrime++;}
    if (lP.id()==22)   {aMesons.push_back(lP); nG++;}

  }

  return true;

}//runPythia

int main() {


  //1 = All, 2 = nonDiff, 3 = Diff
  const unsigned doAllQCD = 1;
  const bool doCascade = true;

  std::string label;
  if (doAllQCD==1) label = "AllQCD";
  else if (doAllQCD==2) label = "NonDiffQCD";
  else if (doAllQCD==3) label = "DiffQCD";

  if (!doCascade) label += "_primOnly";
  
  TFile *fout = TFile::Open(("CascadeParticles_"+label+".root").c_str(),"RECREATE");
  fout->cd();
  
  TTree *mesonTree = new TTree("Mesons","Tree with cascade mesons");
  TTree *protonTree = new TTree("Protons","Tree with cascade protons");
  
  const unsigned nMax = 100;

  unsigned nPi0s = 0;
  double pPi0[100];
  double thetaPi0[100];
  double phiPi0[100];
  int isPrimaryPi0[100];

  for (unsigned iP(0); iP<nMax; ++iP){
    pPi0[iP] =-1.;
    thetaPi0[iP] =-10.;
    phiPi0[iP] =-10.;
    isPrimaryPi0[iP] =-1.;
  }
  
  mesonTree->Branch("nPi0s",&nPi0s);
  mesonTree->Branch("pPi0",pPi0,"pPi0[nPi0s]/D");
  mesonTree->Branch("thetaPi0",thetaPi0,"thetaPi0[nPi0s]/D");
  mesonTree->Branch("phiPi0",phiPi0,"phiPi0[nPi0s]/D");
  mesonTree->Branch("isPrimaryPi0",isPrimaryPi0,"isPrimaryPi0[nPi0s]/I");

  unsigned nEtas = 0;
  double pEta[100];
  double thetaEta[100];
  double phiEta[100];
  int isPrimaryEta[100];

  for (unsigned iP(0); iP<nMax; ++iP){
    pEta[iP] =-1.;
    thetaEta[iP] =-10.;
    phiEta[iP] =-10.;
    isPrimaryEta[iP] =-1.;
  }
  
  mesonTree->Branch("nEtas",&nEtas);
  mesonTree->Branch("pEta",pEta,"pEta[nEtas]/D");
  mesonTree->Branch("thetaEta",thetaEta,"thetaEta[nEtas]/D");
  mesonTree->Branch("phiEta",phiEta,"phiEta[nEtas]/D");
  mesonTree->Branch("isPrimaryEta",isPrimaryEta,"isPrimaryEta[nEtas]/I");

  unsigned nOmegas = 0;
  double pOmega[100];
  double thetaOmega[100];
  double phiOmega[100];
  int isPrimaryOmega[100];

  for (unsigned iP(0); iP<nMax; ++iP){
    pOmega[iP] =-1.;
    thetaOmega[iP] =-10.;
    phiOmega[iP] =-10.;
    isPrimaryOmega[iP] =-1.;
  }
  
  mesonTree->Branch("nOmegas",&nOmegas);
  mesonTree->Branch("pOmega",pOmega,"pOmega[nOmegas]/D");
  mesonTree->Branch("thetaOmega",thetaOmega,"thetaOmega[nOmegas]/D");
  mesonTree->Branch("phiOmega",phiOmega,"phiOmega[nOmegas]/D");
  mesonTree->Branch("isPrimaryOmega",isPrimaryOmega,"isPrimaryOmega[nOmegas]/I");

  unsigned nEtaPrimes = 0;
  double pEtaPrime[100];
  double thetaEtaPrime[100];
  double phiEtaPrime[100];
  int isPrimaryEtaPrime[100];

  for (unsigned iP(0); iP<nMax; ++iP){
    pEtaPrime[iP] =-1.;
    thetaEtaPrime[iP] =-10.;
    phiEtaPrime[iP] =-10.;
    isPrimaryEtaPrime[iP] =-1.;
  }
  
  mesonTree->Branch("nEtaPrimes",&nEtaPrimes);
  mesonTree->Branch("pEtaPrime",pEtaPrime,"pEtaPrime[nEtaPrimes]/D");
  mesonTree->Branch("thetaEtaPrime",thetaEtaPrime,"thetaEtaPrime[nEtaPrimes]/D");
  mesonTree->Branch("phiEtaPrime",phiEtaPrime,"phiEtaPrime[nEtaPrimes]/D");
  mesonTree->Branch("isPrimaryEtaPrime",isPrimaryEtaPrime,"isPrimaryEtaPrime[nEtaPrimes]/I");

  unsigned nProtons = 0;
  double pProton[100];
  double thetaProton[100];
  double phiProton[100];
  int isPrimaryProton[100];
  int statusProton[100];
  
  for (unsigned iP(0); iP<nMax; ++iP){
    pProton[iP] =-1.;
    thetaProton[iP] =-10.;
    phiProton[iP] =-10.;
    isPrimaryProton[iP] =-1.;
    statusProton[iP] = -1;
  }
  
  protonTree->Branch("nProtons",&nProtons);
  protonTree->Branch("pProton",pProton,"pProton[nProtons]/D");
  protonTree->Branch("thetaProton",thetaProton,"thetaProton[nProtons]/D");
  protonTree->Branch("phiProton",phiProton,"phiProton[nProtons]/D");
  protonTree->Branch("isPrimaryProton",isPrimaryProton,"isPrimaryProton[nProtons]/I");
  protonTree->Branch("statusProton",statusProton,"statusProton[nProtons]/I");

  unsigned nGammas = 0;
  double pGamma[100];
  double thetaGamma[100];
  double phiGamma[100];
  int isPrimaryGamma[100];

  for (unsigned iP(0); iP<nMax; ++iP){
    pGamma[iP] =-1.;
    thetaGamma[iP] =-10.;
    phiGamma[iP] =-10.;
    isPrimaryGamma[iP] =-1.;
  }
  
  protonTree->Branch("nGammas",&nGammas);
  protonTree->Branch("pGamma",pGamma,"pGamma[nGammas]/D");
  protonTree->Branch("thetaGamma",thetaGamma,"thetaGamma[nGammas]/D");
  protonTree->Branch("phiGamma",phiGamma,"phiGamma[nGammas]/D");
  protonTree->Branch("isPrimaryGamma",isPrimaryGamma,"isPrimaryGamma[nGammas]/I");

  nP = 0;
  nN = 0;
  nG = 0;
  nPiP = 0;
  nPiM = 0;
  nPi0 = 0;
  nEta = 0;
  nOmega = 0;
  nEtaPrime = 0;

  TRandom3 lRndm;
  const double mProton = 0.93827;
  
  unsigned nEvts = 100 ;
  
  for (int iEvent = 0; iEvent < int(nEvts); ++iEvent) {//loop over p.o.t

    if (doCascade) std::cout << "*************************************" << std::endl
                 << "*************************************" << std::endl
                 << "*************************************" << std::endl;
    std::cout << "*******  Processing event #" << iEvent << std::endl;
    if (doCascade) std::cout << "*************************************" << std::endl
                 << "*************************************" << std::endl
                 << "*************************************" << std::endl;


    std::vector<Particle> lStash;
    lStash.reserve(100);
    std::vector<Particle> lMesons;
    lMesons.reserve(100);
    double val = lRndm.Rndm();
    int idB = (val < 0.43) ? 2212 : 2112;
    Vec4 p4A(0,0,400,sqrt(400*400+mProton*mProton));

    nProtons = 1;
    pProton[0] = 400;
    thetaProton[0] = 0;
    phiProton[0] = 0;
    isPrimaryProton[0] = 1;
    statusProton[0] = 12;
    unsigned initIter = iEvent*22+1;
    unsigned iterationNum = initIter;
    
    if (!runPythia(2212,idB,p4A,doAllQCD,2,lStash,lMesons,iterationNum)) continue;

    //Commented out: to identify events with outgoing proton taking everything and other particles produced.
    //Can't see any anymore: pb fixed ? In case not saving also the status code of the protons -> can discard offline.
    //if (!(lStash.size()>1 && lStash[0].id()==2212 && lStash[0].pz() > 398)) continue;
    if (doCascade){
      std::cout << " -- Stash size after primary interaction: " << lStash.size() << std::endl;
      std::cout << " -- Mesons size after primary interaction: " << lMesons.size() << std::endl;
      std::cout << " -- Printing stash: " << lStash.size() << std::endl;
      for (unsigned iP(0); iP<lStash.size(); ++iP){
    std::cout << " ----- stash particle " << iP << " id " << lStash[iP].id() << " pz=" << lStash[iP].pz() << " status " << lStash[iP].status() << std::endl;
      }
    }
    
    const unsigned nPrimMesons = lMesons.size();

    if (doCascade){
      std::vector<Particle>::iterator lIter =  lStash.begin();
      unsigned lCounter = 0;
      for ( ; lIter != lStash.end(); lIter++){
    iterationNum++;
    val = lRndm.Rndm();
    idB = (val < 0.43) ? 2212 : 2112;
    std::cout << " -- Processing particle " << lCounter << " / " << lStash.size() << " id  " << lIter->id() << " idB = " << idB << std::endl;
    if (lIter->id() == 2212){
      if (nProtons < nMax){
        pProton[nProtons] = lIter->p().pAbs();
        thetaProton[nProtons] = lIter->p().thetaXZ();
        phiProton[nProtons] = lIter->p().phi();
        isPrimaryProton[nProtons] = 0;
        statusProton[nProtons] = lIter->status();
        nProtons++;
      }
      else {
        std::cout << " -- Warning, set to save only " << nMax << " protons but found " << nProtons << " in cascade production." << std::endl;
      }
    }
    lCounter++;
    unsigned absId = abs(lIter->id());
    if (absId!=2212 && absId != 2112 && absId != 211) {
      std::cout << " -- Error, wrong id !" << absId << std::endl;
      for (unsigned iP(0); iP<lStash.size(); ++iP){
        std::cout << " -- stash particle " << iP << " id " << lStash[iP].id() << " pz=" << lStash[iP].pz() << " status " << lStash[iP].status() << std::endl;
      }
      exit(1);
    }
    //std::vector<Particle> lStashTmp;
    runPythia(lIter->id(),idB,lIter->p(),doAllQCD,3,lStash,lMesons,iterationNum);
    lStash.erase(lIter);
    lIter--;
    
    //for (unsigned iP(0); iP<lStashTmp.size(); ++iP){
    //lStash.push_back(lStashTmp[iP]);
    //}
    std::cout << " ---- Stash size after secondary interactions: " << lStash.size() << std::endl;
    std::cout << " ---- Mesons size after secondary interactions: " << lMesons.size() << std::endl;
    std::cout << " -- Printing stash: " << lStash.size() << std::endl;
    for (unsigned iP(0); iP<lStash.size(); ++iP){
      std::cout << " ----- stash particle " << iP << " id " << lStash[iP].id() << " pz=" << lStash[iP].pz() << " status " << lStash[iP].status() << std::endl;
    }
    //if (lCounter > 1){
    //break;
    //}
      }
    }//doCascade

    unsigned nMesons = lMesons.size();
    if (nMesons > nMax) {
      std::cout << " -- Warning, set to save only " << nMax << " mesons but found " << nMesons << " in cascade production." << std::endl;
      nMesons = nMax;
    }
    nPi0s = 0;
    nEtas = 0;
    nOmegas = 0;
    nEtaPrimes = 0;
    nGammas = 0;
    for (unsigned iM(0); iM<nMesons; ++iM){
      int idMeson = lMesons[iM].id();
      if (idMeson==111){
    pPi0[nPi0s] = lMesons[iM].p().pAbs();
    thetaPi0[nPi0s] = lMesons[iM].p().thetaXZ();
    phiPi0[nPi0s] = lMesons[iM].p().phi();
    if (iM<nPrimMesons) isPrimaryPi0[nPi0s] = 1;
    else isPrimaryPi0[nPi0s] = 0;
    nPi0s++;
      }
      else if (idMeson==221){
    pEta[nEtas] = lMesons[iM].p().pAbs();
    thetaEta[nEtas] = lMesons[iM].p().thetaXZ();
    phiEta[nEtas] = lMesons[iM].p().phi();
    if (iM<nPrimMesons) isPrimaryEta[nEtas] = 1;
    else isPrimaryEta[nEtas] = 0;
    nEtas++;
      }
       else if (idMeson==223){
    pOmega[nOmegas] = lMesons[iM].p().pAbs();
    thetaOmega[nOmegas] = lMesons[iM].p().thetaXZ();
    phiOmega[nOmegas] = lMesons[iM].p().phi();
    if (iM<nPrimMesons) isPrimaryOmega[nOmegas] = 1;
    else isPrimaryOmega[nOmegas] = 0;
    nOmegas++;
      }
       else if (idMeson==331){
    pEtaPrime[nEtaPrimes] = lMesons[iM].p().pAbs();
    thetaEtaPrime[nEtaPrimes] = lMesons[iM].p().thetaXZ();
    phiEtaPrime[nEtaPrimes] = lMesons[iM].p().phi();
    if (iM<nPrimMesons) isPrimaryEtaPrime[nEtaPrimes] = 1;
    else isPrimaryEtaPrime[nEtaPrimes] = 0;
    nEtaPrimes++;
       }
       else if (idMeson==22){
    pGamma[nGammas] = lMesons[iM].p().pAbs();
    thetaGamma[nGammas] = lMesons[iM].p().thetaXZ();
    phiGamma[nGammas] = lMesons[iM].p().phi();
    if (iM<nPrimMesons) isPrimaryGamma[nGammas] = 1;
    else isPrimaryGamma[nGammas] = 0;
    nGammas++;
       }
    }
    mesonTree->Fill();
    protonTree->Fill();
    
    std::cout << std::endl << std::endl << " Number of iterations: " << iterationNum-initIter << std::endl;
  }//loop over p.o.t
  


  std::cout << " Number of hadrons per p.o.t:" << std::endl
        << " -- protons " << nP << " " << nEvts << " " << 1.*nP/nEvts << std::endl
        << " -- neutrons " << nN << " " << nEvts << " " << 1.*nN/nEvts << std::endl
        << " -- pi+ " << nPiP << " " << nEvts << " " << 1.*nPiP/nEvts << std::endl
        << " -- pi- " << nPiM << " " << nEvts << " " << 1.*nPiM/nEvts << std::endl
        << " -- pi0 " << nPi0 << " " << nEvts << " " << 1.*nPi0/nEvts << std::endl
        << " -- eta "<< nEta << " " << nEvts << " " << 1.*nEta/nEvts << std::endl
        << " -- omega "<< nOmega << " " << nEvts << " " << 1.*nOmega/nEvts << std::endl
        << " -- eta' "<< nEtaPrime << " " << nEvts << " " << 1.*nEtaPrime/nEvts << std::endl
        << " -- gamma "<< nG << " " << nEvts << " " << 1.*nG/nEvts << std::endl;

  fout->cd();
  mesonTree->Write();
  protonTree->Write();
  fout->Close();
  
  return 0;
}//main
