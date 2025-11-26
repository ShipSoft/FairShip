// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

#include <math.h>
#include "TSystem.h"
#include "TROOT.h"
#include "TMath.h"
#include "TFile.h"
#include "TRandom.h"
#include "FairPrimaryGenerator.h"
#include "GenieGenerator.h"
#include "MeanMaterialBudget.h"
#include "TGeoVolume.h"
#include "TGeoNode.h"
#include "TGeoManager.h"
#include "TGeoEltu.h"
#include "TGeoCompositeShape.h"

using std::cout;
using std::endl;
// read events from ntuples produced with GENIE
// http://genie.hepforge.org/manuals/GENIE_PhysicsAndUserManual_20130615.pdf
// Genie momentum GeV
// Vertex in SI units, assume this means m
// important to read back number of events to give to FairRoot

// -----   Default constructor   -------------------------------------------
GenieGenerator::GenieGenerator() {}
// -------------------------------------------------------------------------
// -----   Default constructor   -------------------------------------------
Bool_t GenieGenerator::Init(const char* fileName) {
  return Init(fileName, 0);
}
// -----   Default constructor   -------------------------------------------
Bool_t GenieGenerator::Init(const char* fileName, const int firstEvent) {
  fNuOnly = false;
  fInputFile = TFile::Open(fileName);
  LOG(info) << "Opening input file " << fileName;
  if (!fInputFile) {
      LOG(fatal) << "Error opening input file.";
      return kFALSE;
  }
  fTree = dynamic_cast<TTree*>(fInputFile->Get("gst"));
  fNevents = fTree->GetEntries();
  fn = firstEvent;
  fTree->SetBranchAddress("Ev",&Ev);    // incoming neutrino energy
  fTree->SetBranchAddress("pxv",&pxv);
  fTree->SetBranchAddress("pyv",&pyv);
  fTree->SetBranchAddress("pzv",&pzv);
  fTree->SetBranchAddress("neu",&neu);    // incoming neutrino PDG code
  fTree->SetBranchAddress("cc",&cc);      // Is it a CC event?
  fTree->SetBranchAddress("nuel",&nuel);  // Is it a NUEEL event?
  fTree->SetBranchAddress("vtxx",&vtxx);  // vertex  in SI units
  fTree->SetBranchAddress("vtxy",&vtxy);
  fTree->SetBranchAddress("vtxz",&vtxz);
  fTree->SetBranchAddress("vtxt",&vtxt);
  fTree->SetBranchAddress("El",&El);      // outgoing lepton momentum
  fTree->SetBranchAddress("pxl",&pxl);
  fTree->SetBranchAddress("pyl",&pyl);
  fTree->SetBranchAddress("pzl",&pzl);
  fTree->SetBranchAddress("Ef",&Ef);   // outgoing hadronic momenta
  fTree->SetBranchAddress("pxf",&pxf);
  fTree->SetBranchAddress("pyf",&pyf);
  fTree->SetBranchAddress("pzf",&pzf);
  fTree->SetBranchAddress("nf",&nf);     // nr of outgoing hadrons
  fTree->SetBranchAddress("pdgf",&pdgf);     // pdg code of hadron
  fFirst=kTRUE;
  return kTRUE;
}
// -------------------------------------------------------------------------
std::vector<double> GenieGenerator::Rotate(Double_t x, Double_t y, Double_t z, Double_t px, Double_t py, Double_t pz)
{
  //rotate vector px,py,pz to point at x,y,z at origin.
  Double_t theta=atan(sqrt(x*x+y*y)/z);
  Double_t c=cos(theta);
  Double_t s=sin(theta);
  //rotate around y-axis
  Double_t px1=c*px+s*pz;
  Double_t pzr=-s*px+c*pz;
  Double_t phi=atan2(y,x);
  c=cos(phi);
  s=sin(phi);
  //rotate around z-axis
  Double_t pxr=c*px1-s*py;
  Double_t pyr=s*px1+c*py;
  std::vector<double> pout;
  pout.push_back(pxr);
  pout.push_back(pyr);
  pout.push_back(pzr);
  //cout << "Info GenieGenerator: rotated" << pout[0] << " " << pout[1] << " " << pout[2] << " " << x << " " << y << " " << z <<endl;
  return pout;
}


// -----   Destructor   ----------------------------------------------------
GenieGenerator::~GenieGenerator()
{
 fInputFile->Close();
 fInputFile->Delete();
 delete fInputFile;
}
// -------------------------------------------------------------------------
void GenieGenerator::AddBox(TVector3 dVec, TVector3 box)
{
  dVecs.push_back(dVec);
  m_boxes.push_back(box);
  cout << "Debug GenieGenerator: "<< dVec.X() << " "<<box.Z() << endl;
}
// -----   Passing the event   ---------------------------------------------
Bool_t GenieGenerator::OldReadEvent(FairPrimaryGenerator* cpg)
{
    if (fFirst){
     TGeoVolume *top=gGeoManager->GetTopVolume();
     TGeoNode *linner = top->FindNode("lidT1I_1");
     TGeoNode *scint  = top->FindNode("lidT1lisci_1");
     TGeoNode *louter = top->FindNode("lidT1O_1");
     TGeoNode *lidT6I = top->FindNode("lidT6I_1");
     TGeoNode *t2I  = top->FindNode("T2I_1");
     TGeoNode *t1I  = top->FindNode("T1I_1");
     TGeoEltu *temp = dynamic_cast<TGeoEltu*>(linner->GetVolume()->GetShape());
     fEntrDz_inner = temp->GetDZ();
     temp = dynamic_cast<TGeoEltu*>(louter->GetVolume()->GetShape());
     fEntrDz_outer = temp->GetDZ();
     fEntrA = temp->GetA();
     fEntrB = temp->GetB();
     fEntrZ_inner  = linner->GetMatrix()->GetTranslation()[2];
     fEntrZ_outer  = louter->GetMatrix()->GetTranslation()[2];
     Lvessel = lidT6I->GetMatrix()->GetTranslation()[2] - fEntrZ_inner - fEntrDz_inner;
     TGeoCompositeShape *tempC = dynamic_cast<TGeoCompositeShape*>(t2I->GetVolume()->GetShape());
     Xvessel = tempC->GetDX() - 2*fEntrDz_inner ;
     Yvessel = tempC->GetDY() - 2*fEntrDz_inner ;
     tempC = dynamic_cast<TGeoCompositeShape*>(t1I->GetVolume()->GetShape());
     fL1z = tempC->GetDZ()*2;
     temp = dynamic_cast<TGeoEltu*>(scint->GetVolume()->GetShape());
     fScintDz = temp->GetDZ()*2;
     cout << "Info GenieGenerator: geo inner " << fEntrDz_inner << " "<< fEntrZ_inner << endl;
     cout << "Info GenieGenerator: geo outer " << fEntrDz_outer << " "<< fEntrZ_outer << endl;
     cout << "Info GenieGenerator: A and B " << fEntrA << " "<< fEntrB << endl;
     cout << "Info GenieGenerator: vessel length heig<ht width " << Lvessel << " "<<Yvessel<< " "<< Xvessel << endl;
     cout << "Info GenieGenerator: scint thickness " << fScintDz << endl;
     cout << "Info GenieGenerator: rextra " << fScintDz/2.+2*fEntrDz_inner << " "<< 2*fEntrDz_outer << " "<<2*fEntrDz_inner << endl;
     for (size_t j = 0; j < m_boxes.size(); j++) {
         cout << "Info GenieGenerator: nuMu X" << j << " - " << -m_boxes[j].X() + dVecs[j].X() << " "
              << m_boxes[j].X() + dVecs[j].X() << endl;
         cout << "Info GenieGenerator: nuMu Y" << j << " - " << -m_boxes[j].Y() + dVecs[j].Y() << " "
              << m_boxes[j].Y() + dVecs[j].Y() << endl;
         cout << "Info GenieGenerator: nuMu Z" << j << " - " << -m_boxes[j].Z() + dVecs[j].Z() << " "
              << m_boxes[j].Z() + dVecs[j].Z() << endl;
     }
     fFirst = kFALSE;
    }
    if (fn==fNevents) {LOG(warning) << "End of input file. Rewind.";}
    fTree->GetEntry(fn%fNevents);
    fn++;
    if (fn%1000==0) {
      cout << "Info GenieGenerator: neutrino event-nr "<< fn << endl;
      }
// generate a random point on the vessel, take veto z, and calculate outer lid position
    //Double_t Yvessel=500.;
    //Double_t Lvessel=5.*Yvessel+3500.;
    //Double_t ztarget=zentrance-6350.;
    //Double_t ea=250.; //inside inner wall vessel
    Double_t eb=Yvessel; //inside inner wall vessel
    Double_t x;
    Double_t y;
    Double_t z;
    Double_t where=gRandom->Uniform(0.,1.);
    if (where<0.03) {
      // point on entrance lid
      Double_t ellip=2.;
      while (ellip>1.){
         x = gRandom->Uniform(-fEntrA,fEntrA);
         y = gRandom->Uniform(-fEntrB,fEntrB);
         ellip=(x*x)/(fEntrA*fEntrA)+(y*y)/(fEntrB*fEntrB);
      }
      if (gRandom->Uniform(0.,1.)<0.5){
        z=fEntrZ_inner + gRandom->Uniform(-fEntrDz_inner,fEntrDz_inner);
      }else{
        z=fEntrZ_outer + gRandom->Uniform(-fEntrDz_outer,fEntrDz_outer);
      }
    }else if (where<0.64){
      //point on tube, place over 1 cm radius at 2 radii, separated by 10. cm
      // first vessel has smaller size
      Double_t ea = Xvessel;
      Double_t zrand =  gRandom->Uniform(0,Lvessel);
      if (zrand < fL1z){
        ea = fEntrA;
      }
      z = fEntrZ_outer-fEntrDz_outer + zrand;
      Double_t theta = gRandom->Uniform(0.,TMath::Pi());
      Double_t rextra;
      if ( gRandom->Uniform(0.,1.)>0.5) {
      // outer vessel
        rextra = fScintDz/2.+2*fEntrDz_inner + gRandom->Uniform(0,2*fEntrDz_outer);
      }else{
      // inner vessel
        rextra = gRandom->Uniform(0.,2*fEntrDz_inner);
      }
      x = (ea+rextra)*cos(theta);
      y = sqrt(1.-(x*x)/((ea+rextra)*(ea+rextra)))*(eb+rextra);
      if (gRandom->Uniform(-1.,1.)>0.) y=-y;
    }else{
      //point in nu-tau detector area
      int j = static_cast<int>(gRandom->Uniform(0., m_boxes.size() + 0.5));
      x = gRandom->Uniform(-m_boxes[j].X() + dVecs[j].X(), m_boxes[j].X() + dVecs[j].X());
      y = gRandom->Uniform(-m_boxes[j].Y() + dVecs[j].Y(), m_boxes[j].Y() + dVecs[j].Y());
      z = gRandom->Uniform(-m_boxes[j].Z() + dVecs[j].Z(), m_boxes[j].Z() + dVecs[j].Z());
    }
// first, incoming neutrino
    //rotate the particle
    Double_t zrelative=z-ztarget;
    //cout << "Info GenieGenerator: x,y,z " << x <<" " << y << " " << zrelative << endl;
    //cout << "Info GenieGenerator: neutrino " << neu << "p-in "<< pxv << pyv << pzv << " nf "<< nf << endl;
    std::vector<double> pout = Rotate(x,y,zrelative,pxv,pyv,pzv);
    //cpg->AddTrack(neu,pxv,pyv,pzv,vtxx,vtxy,vtxz,-1,false);
    //cout << "Info GenieGenerator: neutrino " << neu << "p-rot "<< pout[0] << " fn "<< fn << endl;
    cpg->AddTrack(neu,pout[0],pout[1],pout[2],x,y,z,-1,false);


// second, outgoing lepton
    pout = Rotate(x,y,zrelative,pxl,pyl,pzl);
    Int_t oLPdgCode = neu;
    if (cc){oLPdgCode = copysign(TMath::Abs(neu)-1,neu);}
    if (nuel){oLPdgCode = 11;}
    cpg->AddTrack(oLPdgCode,pout[0],pout[1],pout[2],x,y,z,0,true);
// last, all others
    for(int i=0; i<nf; i++)
	{
         pout = Rotate(x,y,zrelative,pxf[i],pyf[i],pzf[i]);
         cpg->AddTrack(pdgf[i],pout[0],pout[1],pout[2],x,y,z,0,true);
         // cout << "f " << pdgf[i] << " pz "<< pzf[i] << endl;
       }

  return kTRUE;
}

// -----   Passing the event   ---------------------------------------------
Bool_t GenieGenerator::ReadEvent(FairPrimaryGenerator* cpg)
{
    //some start/end positions in z (emulsion to Tracker 1)
    Double_t start[3]={0.,0.,startZ};
    Double_t end[3]={0.,0.,endZ};
    char ts[20];
    //cout << "Enter GenieGenerator " << endl;
    //pick histogram: 1100=100 momentum bins, 1200=25 momentum bins.
    Int_t idbase=1200;
    if (fFirst){
      Double_t bparam=0.;
      Double_t mparam[10];
      bparam=shipgen::MeanMaterialBudget(start, end, mparam);
      cout << "Info GenieGenerator: MaterialBudget " << start[2] << " - "<< end[2] <<  endl;
      cout << "Info GenieGenerator: MaterialBudget " << bparam <<  endl;
      cout << "Info GenieGenerator: MaterialBudget 0 " << mparam[0] <<  endl;
      cout << "Info GenieGenerator: MaterialBudget 1 " << mparam[1] <<  endl;
      cout << "Info GenieGenerator: MaterialBudget 2 " << mparam[2] <<  endl;
      cout << "Info GenieGenerator: MaterialBudget 3 " << mparam[3] <<  endl;
      cout << "Info GenieGenerator: MaterialBudget 4 " << mparam[4] <<  endl;
      cout << "Info GenieGenerator: MaterialBudget 5 " << mparam[5] <<  endl;
      cout << "Info GenieGenerator: MaterialBudget 6 " << mparam[6] <<  endl;
      cout << "Info GenieGenerator: MaterialBudget " << mparam[0]*mparam[4] <<  endl;
      //read the (log10(p),log10(pt)) hists to be able to draw a pt for every neutrino momentum
      //loop over neutrino types
      printf("Reading (log10(p),log10(pt)) Hists from file: %s\n",fInputFile->GetName());
      for (Int_t idnu=12;idnu<17;idnu+=2){
        for (Int_t idadd=-1;idadd<2;idadd+=2){
  	  Int_t idhnu = static_cast<int>(idbase + idnu);
          if (idadd<0) idhnu+=1000;
	  sprintf(ts,"%d",idhnu);
	  //pickup corresponding (log10(p),log10(pt)) histogram
          if (fInputFile->FindObjectAny(ts)){
           TH2* h2tmp = dynamic_cast<TH2*>(fInputFile->Get(ts));
           printf("HISTID=%d, Title:%s\n",idhnu,h2tmp->GetTitle());
	   sprintf(ts,"px_%d",idhnu);
          //make its x-projection, to later be able to convert log10(p) to its bin-number
           pxhist[idhnu]=h2tmp->ProjectionX(ts,1,-1);
           Int_t nbinx=h2tmp->GetNbinsX();
          //printf("idhnu=%d  ts=%s  nbinx=%d\n",idhnu,ts,nbinx);
	  //project all slices on the y-axis
           for (Int_t k=1;k<nbinx+1;k+=1){
	    sprintf(ts,"h%d%d",idhnu,k);
            //printf("idnu %d idhnu %d bin%d  ts=%s\n",idnu,idhnu,k,ts);
            pyslice[idhnu][k]=h2tmp->ProjectionY(ts,k,k);
	  }
         }
	}
      }
      fFirst = kFALSE;
    }

    if (fn==fNevents) {LOG(warning) << "End of input file. Rewind.";}
    fTree->GetEntry(fn%fNevents);
    fn++;
    if (fn%100==0) {
      cout << "Info GenieGenerator: neutrino event-nr "<< fn << endl;
    }

// Incoming neutrino, get a random px,py
    //cout << "Info GenieGenerator: neutrino " << neu << "p-in "<< pzv << " nf "<< nf << endl;
    //cout << "Info GenieGenerator: ztarget " << ztarget << endl;
    Double_t mparam[10];
    Double_t pout[3] = {0., 0., -1.};
    Double_t txnu=0;
    Double_t tynu=0;
    //Does this neutrino fly through material? Otherwise draw another pt..
    //cout << "Info GenieGenerator Start bparam while loop" << endl;
    while (pout[2]<0.) {
      //***OLD**** Keep for comparison maybe??
      //generate pt of ~0.3 GeV
      //pout[0] = gRandom->Exp(0.2);
      //pout[1] = gRandom->Exp(0.2);
      //pout[2] = pzv*pzv-pout[0]*pout[0]-pout[1]*pout[1];

      //**NEW** get pt of this neutrino from 2D hists.
      Int_t idhnu=TMath::Abs(neu)+idbase;
      if (neu<0) idhnu+=1000;
      Int_t nbinmx=pxhist[idhnu]->GetNbinsX();
      Double_t pl10=log10(pzv);
      Int_t nbx=pxhist[idhnu]->FindBin(pl10);
      //printf("idhnu %d, p %f log10(p) %f bin,binmx %d %d \n",idhnu,pzv,pl10,nbx,nbinmx);
      if (nbx<1) nbx=1;
      if (nbx>nbinmx) nbx=nbinmx;
      Double_t ptlog10=pyslice[idhnu][nbx]->GetRandom();
//hist was filled with: log10(pt+0.01)
      Double_t pt=pow(10.,ptlog10)-0.01;
      //rotate pt in phi:
      Double_t phi=gRandom->Uniform(0.,2*TMath::Pi());
      pout[0] = cos(phi)*pt;
      pout[1] = sin(phi)*pt;
      pout[2] = pzv*pzv-pt*pt;
      //printf("p= %f pt=%f px,py,pz**2=%f,%f,%f\n",pzv,pt,pout[0],pout[1],pout[2]);

      if (pout[2]>=0.) {
        pout[2]=TMath::Sqrt(pout[2]);
        if (gRandom->Uniform(-1.,1.)<0.) pout[0]=-pout[0];
        if (gRandom->Uniform(-1.,1.)<0.) pout[1]=-pout[1];
        //cout << "Info GenieGenerator: neutrino pxyz " << pout[0] << ", " << pout[1] << ", " << pout[2] << endl;
        // xyz at start and end
        start[0]=(pout[0]/pout[2])*(start[2]-ztarget);
        start[1]=(pout[1]/pout[2])*(start[2]-ztarget);
        //cout << "Info GenieGenerator: neutrino xyz-start " << start[0] << "-" << start[1] << "-" << start[2] << endl;
        txnu=pout[0]/pout[2];
        tynu=pout[1]/pout[2];
        end[0]=txnu*(end[2]-ztarget);
        end[1]=tynu*(end[2]-ztarget);
        //cout << "Info GenieGenerator: neutrino xyz-end " << end[0] << "-" << end[1] << "-" << end[2] << endl;
        //get material density between these two points
        shipgen::MeanMaterialBudget(start, end, mparam);
        //printf("param %e %e %e \n",bparam,mparam[6],mparam[7]);
       }
    }
    //loop over trajectory between start and end to pick an interaction point
    Double_t prob2int = -1.;
    Double_t x = 0.;
    Double_t y = 0.;
    Double_t z = 0.;
    Int_t count=0;
    while (prob2int<gRandom->Uniform(0.,1.)) {
      //place x,y,z uniform along path
      z=gRandom->Uniform(start[2],end[2]);
      x=txnu*(z-ztarget);
      y=tynu*(z-ztarget);
      if (mparam[6]<0.5){
        //mparam is number of boundaries along path. mparam[6]=0.: uniform material budget along path, use present x,y,z
        prob2int=2.;
      }else{
        //get local material at this point, to calculate probability that interaction is at this point.
        TGeoNode *node = gGeoManager->FindNode(x,y,z);
        TGeoMaterial *mat = 0;
        if (node && !gGeoManager->IsOutside()) {
          mat = node->GetVolume()->GetMaterial();
         //cout << "Info GenieGenerator: mat " <<  count << ", " << mat->GetName() << ", " << mat->GetDensity() << endl;
         //density relative to Prob largest density along this trajectory, i.e. use rho(Pt)
         prob2int= mat->GetDensity()/mparam[7];
         if (prob2int>1.) cout << "***WARNING*** GenieGenerator: prob2int > Maximum density????" << prob2int << " maxrho:" << mparam[7] << " material: " <<  mat->GetName() << endl;
         count+=1;
        }else{
          prob2int=0.;
        }
     }
    }
    //cout << "Info GenieGenerator: prob2int " << prob2int << ", " << count << endl;

    Double_t zrelative=z-ztarget;
    Double_t tof = TMath::Sqrt(x * x + y * y + zrelative * zrelative) / 2.99792458e+10;   // speed of light in cm/s
    cpg->AddTrack(neu,pout[0],pout[1],pout[2],x,y,z,-1,false,TMath::Sqrt(pout[0]*pout[0]+pout[1]*pout[1]+pout[2]*pout[2]),tof,mparam[0]*mparam[4]);
    if (!fNuOnly){
      // second, outgoing lepton
      std::vector<double> pp = Rotate(x,y,zrelative,pxl,pyl,pzl);
      Int_t oLPdgCode = neu;
      if (cc){oLPdgCode = copysign(TMath::Abs(neu)-1,neu);}
      if (nuel){oLPdgCode = 11;}
      cpg->AddTrack(oLPdgCode,pp[0],pp[1],pp[2],x,y,z,0,true,El,tof,mparam[0]*mparam[4]);
// last, all others
      for(int i=0; i<nf; i++)
    	{
	  pp = Rotate(x,y,zrelative,pxf[i],pyf[i],pzf[i]);
	  cpg->AddTrack(pdgf[i],pp[0],pp[1],pp[2],x,y,z,0,true,Ef[i],tof,mparam[0]*mparam[4]);
         //cout << "f " << pdgf[i] << " pz "<< pzf[i] << endl;
	}
    //cout << "Info GenieGenerator Return from GenieGenerator" << endl;
    }
  return kTRUE;
}
// -------------------------------------------------------------------------
Int_t GenieGenerator::GetNevents()
{
 return fNevents;
}
