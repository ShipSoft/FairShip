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
  fTree->SetBranchAddress("cc",&cc);      // Is it a CC event?
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
Double_t GenieGenerator::MeanMaterialBudget(const Double_t *start, const Double_t *end, Double_t *mparam)
{
  //
  // Calculate mean material budget and material properties between
  //    the points "start" and "end".
  //
  // "mparam" - parameters used for the energy and multiple scattering
  //  corrections:
  //
  // mparam[0] - mean density: sum(x_i*rho_i)/sum(x_i) [g/cm3]
  // mparam[1] - equivalent rad length fraction: sum(x_i/X0_i) [adimensional]
  // mparam[2] - mean A: sum(x_i*A_i)/sum(x_i) [adimensional]
  // mparam[3] - mean Z: sum(x_i*Z_i)/sum(x_i) [adimensional]
  // mparam[4] - length: sum(x_i) [cm]
  // mparam[5] - Z/A mean: sum(x_i*Z_i/A_i)/sum(x_i) [adimensional]
  // mparam[6] - number of boundary crosses
  //
  //  Origin:  Marian Ivanov, Marian.Ivanov@cern.ch
  //
  //  Corrections and improvements by
  //        Andrea Dainese, Andrea.Dainese@lnl.infn.it,
  //        Andrei Gheata,  Andrei.Gheata@cern.ch
  //

  mparam[0]=0; mparam[1]=1; mparam[2] =0; mparam[3] =0;
  mparam[4]=0; mparam[5]=0; mparam[6]=0;
  //
  Double_t bparam[6]; // total parameters
  Double_t lparam[6]; // local parameters

  for (Int_t i=0;i<6;i++) bparam[i]=0;

  if (!gGeoManager) {
    //AliFatalClass("No TGeo\n");
    return 0.;
  }
  //
  Double_t length;
  Double_t dir[3];
  length = TMath::Sqrt((end[0]-start[0])*(end[0]-start[0])+
                       (end[1]-start[1])*(end[1]-start[1])+
                       (end[2]-start[2])*(end[2]-start[2]));
  mparam[4]=length;
  if (length<TGeoShape::Tolerance()) return 0.0;
  Double_t invlen = 1./length;
  dir[0] = (end[0]-start[0])*invlen;
  dir[1] = (end[1]-start[1])*invlen;
  dir[2] = (end[2]-start[2])*invlen;

  // Initialize start point and direction
  TGeoNode *currentnode = 0;
  TGeoNode *startnode = gGeoManager->InitTrack(start, dir);
  if (!startnode) {
    //AliErrorClass(Form("start point out of geometry: x %f, y %f, z %f",
    //		  start[0],start[1],start[2]));
    return 0.0;
  }
  TGeoMaterial *material = startnode->GetVolume()->GetMedium()->GetMaterial();
  lparam[0]   = material->GetDensity();
  lparam[1]   = material->GetRadLen();
  lparam[2]   = material->GetA();
  lparam[3]   = material->GetZ();
  lparam[4]   = length;
  lparam[5]   = lparam[3]/lparam[2];
  if (material->IsMixture()) {
    TGeoMixture * mixture = (TGeoMixture*)material;
    lparam[5] =0;
    Double_t sum =0;
    for (Int_t iel=0;iel<mixture->GetNelements();iel++){
      sum  += mixture->GetWmixt()[iel];
      lparam[5]+= mixture->GetZmixt()[iel]*mixture->GetWmixt()[iel]/mixture->GetAmixt()[iel];
    }
    lparam[5]/=sum;
  }

  // Locate next boundary within length without computing safety.
  // Propagate either with length (if no boundary found) or just cross boundary
  gGeoManager->FindNextBoundaryAndStep(length, kFALSE);
  Double_t step = 0.0; // Step made
  Double_t snext = gGeoManager->GetStep();
  // If no boundary within proposed length, return current density
  if (!gGeoManager->IsOnBoundary()) {
    mparam[0] = lparam[0];
    mparam[1] = lparam[4]/lparam[1];
    mparam[2] = lparam[2];
    mparam[3] = lparam[3];
    mparam[4] = lparam[4];
    return lparam[0];
  }
  // Try to cross the boundary and see what is next
  Int_t nzero = 0;
  while (length>TGeoShape::Tolerance()) {
    currentnode = gGeoManager->GetCurrentNode();
    if (snext<2.*TGeoShape::Tolerance()) nzero++;
    else nzero = 0;
    if (nzero>3) {
      // This means navigation has problems on one boundary
      // Try to cross by making a small step
      //AliErrorClass("Cannot cross boundary\n");
      mparam[0] = bparam[0]/step;
      mparam[1] = bparam[1];
      mparam[2] = bparam[2]/step;
      mparam[3] = bparam[3]/step;
      mparam[5] = bparam[5]/step;
      mparam[4] = step;
      mparam[0] = 0.;             // if crash of navigation take mean density 0
      mparam[1] = 1000000;        // and infinite rad length
      return bparam[0]/step;
    }
    mparam[6]+=1.;
    step += snext;
    bparam[1]    += snext/lparam[1];
    bparam[2]    += snext*lparam[2];
    bparam[3]    += snext*lparam[3];
    bparam[5]    += snext*lparam[5];
    bparam[0]    += snext*lparam[0];

    if (snext>=length) break;
    if (!currentnode) break;
    length -= snext;
    material = currentnode->GetVolume()->GetMedium()->GetMaterial();
    lparam[0] = material->GetDensity();
    lparam[1]  = material->GetRadLen();
    lparam[2]  = material->GetA();
    lparam[3]  = material->GetZ();
    lparam[5]   = lparam[3]/lparam[2];
    if (material->IsMixture()) {
      TGeoMixture * mixture = (TGeoMixture*)material;
      lparam[5]=0;
      Double_t sum =0;
      for (Int_t iel=0;iel<mixture->GetNelements();iel++){
        sum+= mixture->GetWmixt()[iel];
        lparam[5]+= mixture->GetZmixt()[iel]*mixture->GetWmixt()[iel]/mixture->GetAmixt()[iel];
      }
      lparam[5]/=sum;
    }
    gGeoManager->FindNextBoundaryAndStep(length, kFALSE);
    snext = gGeoManager->GetStep();
  }
  mparam[0] = bparam[0]/step;
  mparam[1] = bparam[1];
  mparam[2] = bparam[2]/step;
  mparam[3] = bparam[3]/step;
  mparam[5] = bparam[5]/step;
  return bparam[0]/step;
}

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
  boxs.push_back(box);
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
     for(int j=0; j<boxs.size(); j++) {
      cout << "Info GenieGenerator: nuMu X" << j << " - "<< -boxs[j].X()+dVecs[j].X() << " "<< boxs[j].X()+dVecs[j].X() << endl;
      cout << "Info GenieGenerator: nuMu Y" << j << " - "<< -boxs[j].Y()+dVecs[j].Y() << " "<< boxs[j].Y()+dVecs[j].Y() << endl;
      cout << "Info GenieGenerator: nuMu Z" << j << " - "<< -boxs[j].Z()+dVecs[j].Z() << " "<< boxs[j].Z()+dVecs[j].Z() << endl;
     }
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
      int j =  int(gRandom->Uniform(0.,boxs.size()+0.5));
      x=gRandom->Uniform(-boxs[j].X()+dVecs[j].X(),boxs[j].X()+dVecs[j].X());
      y=gRandom->Uniform(-boxs[j].Y()+dVecs[j].Y(),boxs[j].Y()+dVecs[j].Y());
      z=gRandom->Uniform(-boxs[j].Z()+dVecs[j].Z(),boxs[j].Z()+dVecs[j].Z());
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
    if (cc){oLPdgCode = copysign(fabs(neu)-1,neu);}
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
    fFirst = kFALSE;
    //some start/end positions in z (emulsion to Tracker 1)
    Double_t start[3]={0.,0.,-3400.};
    Double_t end[3]={0.,0.,2650.};
    if (fFirst){
      Double_t bparam=0.;
      Double_t mparam[7];
      bparam=MeanMaterialBudget(start, end, mparam);
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

      fFirst = kFALSE;
    }

    if (fn==fNevents) {fLogger->Fatal(MESSAGE_ORIGIN, "No more input events");}
    fTree->GetEntry(fn);
    fn++;
    if (fn%100==0) {
      cout << "Info GenieGenerator: neutrino event-nr "<< fn << endl;
    }

    //only accept neutrinos below ThetaMax
    Double_t ThetaMax=0.1;

// Incoming neutrino, get a random px,py
    //cout << "Info GenieGenerator: neutrino " << neu << "p-in "<< pxv << pyv << pzv << " nf "<< nf << endl;
    //cout << "Info GenieGenerator: ztarget " << ztarget << endl;
    Double_t bparam=0.;
    Double_t mparam[7];
    Double_t pout[3] ;
    Double_t txnu=0;
    Double_t tynu=0;
    //Does this neutrino fly through material? Otherwise draw another pt..
    //cout << "Info GenieGenerator Start bparam while loop" << endl;
    while (bparam<1.e-5){
     //generate pt of ~0.3 GeV
     pout[0] = gRandom->Exp(0.2);
     pout[1] = gRandom->Exp(0.2);
     pout[2] = pzv*pzv-pout[0]*pout[0]-pout[1]*pout[1];
      if (pout[2]>0.) {
       pout[2]=TMath::Sqrt(pout[2]);
       if(TMath::Sqrt(pout[0]*pout[0]+pout[1]*pout[1])/pout[2]<ThetaMax){
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
        bparam=MeanMaterialBudget(start, end, mparam);
       }
      }
    }

    //loop over trajectory between start and end to pick an interaction point
    Double_t prob2int = 0.;
    Double_t x;
    Double_t y;
    Double_t z;
    //Int_t count=0;
    //cout << "Info GenieGenerator Start prob2int while loop, bparam= " << bparam << ", " << bparam*1.e8 <<endl;
    while (prob2int<gRandom->Uniform(0.,1.)) {
      z=gRandom->Uniform(start[2],end[2]);
      x=txnu*(z-ztarget);
      y=tynu*(z-ztarget);
      //get local material at this point
      TGeoNode *node = gGeoManager->FindNode(x,y,z);
      TGeoMaterial *mat = 0;
      if (node && !gGeoManager->IsOutside()) mat = node->GetVolume()->GetMaterial();
      //cout << "Info GenieGenerator: mat " <<  count << ", " << mat->GetName() << ", " << mat->GetDensity() << endl;
      //density relative to Prob largest density on the market, i.e. use rho(Pt)
      prob2int= mat->GetDensity()/21.45;
      //count+=1;
    }
    //cout << "Info GenieGenerator: prob2int " << prob2int << ", " << count << endl;

    Double_t zrelative=z-ztarget;
    Double_t tof=TMath::Sqrt(x*x+y*y+zrelative*zrelative)/2.99792458e+6;
    cpg->AddTrack(neu,pout[0],pout[1],pout[2],x,y,z,-1,false,TMath::Sqrt(pout[0]*pout[0]+pout[1]*pout[1]+pout[2]*pout[2]),tof,mparam[0]*mparam[4]);

// second, outgoing lepton
    std::vector<double> pp = Rotate(x,y,zrelative,pxl,pyl,pzl);
    Int_t oLPdgCode = neu;
    if (cc){oLPdgCode = copysign(fabs(neu)-1,neu);}
    cpg->AddTrack(oLPdgCode,pp[0],pp[1],pp[2],x,y,z,0,true,TMath::Sqrt(pp[0]*pp[0]+pp[1]*pp[1]+pp[2]*pp[2]),tof,mparam[0]*mparam[4]);
// last, all others
    for(int i=0; i<nf; i++)
    	{
         pp = Rotate(x,y,zrelative,pxf[i],pyf[i],pzf[i]);
         cpg->AddTrack(pdgf[i],pp[0],pp[1],pp[2],x,y,z,0,true,TMath::Sqrt(pp[0]*pp[0]+pp[1]*pp[1]+pp[2]*pp[2]),tof,mparam[0]*mparam[4]);
         // cout << "f " << pdgf[i] << " pz "<< pzf[i] << endl;
       }
    //cout << "Info GenieGenerator Return from GenieGenerator" << endl;

  return kTRUE;
}
// -------------------------------------------------------------------------
Int_t GenieGenerator::GetNevents()
{
 return fNevents;
}


ClassImp(GenieGenerator)
