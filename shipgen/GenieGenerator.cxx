#include <math.h>
#include "TROOT.h"
#include "TMath.h"
#include "TFile.h"
#include "TRandom.h"
#include "FairPrimaryGenerator.h"
#include "GenieGenerator.h"
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
  fLogger = FairLogger::GetLogger();
  fLogger->Info(MESSAGE_ORIGIN,"Opening input file %s",fileName);
  fInputFile  = new TFile(fileName);
  if (fInputFile->IsZombie()) {
    fLogger->Fatal(MESSAGE_ORIGIN, "Error opening the Signal file");
  }
  fTree = (TTree *)fInputFile->Get("gst");
  fNevents = fTree->GetEntries();
  fn = firstEvent;
  fTree->SetBranchAddress("Ev",&pxl);    // incoming neutrino energy
  fTree->SetBranchAddress("pxv",&pxv);
  fTree->SetBranchAddress("pyv",&pyv);
  fTree->SetBranchAddress("pzv",&pzv);
  fTree->SetBranchAddress("neu",&neu);    // incoming neutrino PDG code
  fTree->SetBranchAddress("vtxx",&vtxx);  // vertex  in SI units
  fTree->SetBranchAddress("vtxy",&vtxy);
  fTree->SetBranchAddress("vtxz",&vtxz);
  fTree->SetBranchAddress("vtxt",&vtxt);
  fTree->SetBranchAddress("El",&El);      // outgoing lepton momentum
  fTree->SetBranchAddress("pxl",&pxl);
  fTree->SetBranchAddress("pyl",&pyl);
  fTree->SetBranchAddress("pzl",&pzl);
  fTree->SetBranchAddress("pxf",&pxf);   // outgoing hadronic momenta
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

// -----   Passing the event   ---------------------------------------------
Bool_t GenieGenerator::ReadEvent(FairPrimaryGenerator* cpg)
{
    if (fFirst){
     TGeoVolume *top=gGeoManager->GetTopVolume();
     TGeoNode *linner = top->FindNode("lidT1I_1");
     TGeoNode *scint  = top->FindNode("lidT1lisci_1");
     TGeoNode *louter = top->FindNode("lidT1O_1");
     TGeoEltu *temp = dynamic_cast<TGeoEltu*>(linner->GetVolume()->GetShape());  
     fEntrDz_inner = temp->GetDZ();
     temp = dynamic_cast<TGeoEltu*>(louter->GetVolume()->GetShape());  
     fEntrDz_outer = temp->GetDZ();
     fEntrA = temp->GetA(); 
     fEntrB = temp->GetB(); 
     fEntrZ_inner  = linner->GetMatrix()->GetTranslation()[2];
     fEntrZ_outer  = louter->GetMatrix()->GetTranslation()[2];
     TGeoNode *lidT6I = top->FindNode("lidT6I_1");
     Lvessel = lidT6I->GetMatrix()->GetTranslation()[2] - fEntrZ_inner - fEntrDz_inner;
     TGeoNode *t2I  = top->FindNode("T2I_1");
     TGeoCompositeShape *tempC = dynamic_cast<TGeoCompositeShape*>(t2I->GetVolume()->GetShape());  
     Xvessel = tempC->GetDX() - 2*fEntrDz_inner ;
     Yvessel = tempC->GetDY() - 2*fEntrDz_inner ;
     TGeoNode *t1I  = top->FindNode("T1I_1");
     tempC = dynamic_cast<TGeoCompositeShape*>(t1I->GetVolume()->GetShape()); 
     fL1z = tempC->GetDZ()*2;  
     temp = dynamic_cast<TGeoEltu*>(scint->GetVolume()->GetShape());  
     fScintDz = temp->GetDZ()*2;
     cout << "Info GenieGenerator: geo inner " << fEntrDz_inner << " "<< fEntrZ_inner << endl;
     cout << "Info GenieGenerator: geo outer " << fEntrDz_outer << " "<< fEntrZ_outer << endl;
     cout << "Info GenieGenerator: A and B " << fEntrA << " "<< fEntrB << endl;
     cout << "Info GenieGenerator: vessel length height width " << Lvessel << " "<<Yvessel<< " "<< Xvessel << endl;
     cout << "Info GenieGenerator: scint thickness " << fScintDz << endl;
     cout << "Info GenieGenerator: rextra " << fScintDz/2.+2*fEntrDz_inner << " "<< 2*fEntrDz_outer << " "<<2*fEntrDz_inner << endl;
     // if ( gRandom->Uniform(0.,1.)>0.5) {rextra=rextra+11.;}  //outer wall.

     fFirst = kFALSE;
    }
    if (fn==fNevents) {fLogger->Fatal(MESSAGE_ORIGIN, "No more input events");}
    fTree->GetEntry(fn);
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
      if (gRandom->Uniform(0,1) < fL1z/Lvessel){ ea = fEntrA; }
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
      z = fEntrZ_outer+fEntrDz_outer + gRandom->Uniform(0.,Lvessel);
    }else{
      //point in nu-tau muon shield
      x=gRandom->Uniform(-225.,225.);
      y=gRandom->Uniform(-400.,400.);
      z=fEntrZ_outer-205.+gRandom->Uniform(0.,80.);
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
    cpg->AddTrack(copysign(fabs(neu)-1,neu),pout[0],pout[1],pout[2],x,y,z,0,true);
// last, all others
    for(int i=0; i<nf; i++)
	{
         pout = Rotate(x,y,zrelative,pxf[i],pyf[i],pzf[i]);
         cpg->AddTrack(pdgf[i],pout[0],pout[1],pout[2],x,y,z,0,true);
         // cout << "f " << pdgf[i] << " pz "<< pzf[i] << endl;
       }

  return kTRUE;
}
// -------------------------------------------------------------------------
Int_t GenieGenerator::GetNevents()
{
 return fNevents;
}


ClassImp(GenieGenerator)
