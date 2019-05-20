// -------------------------------------------------------------------------
// -----                    ShipGoliathField source file                  -----
// -------------------------------------------------------------------------
#include "ShipGoliathField.h"
#include "math.h"
#include "TROOT.h"
#include "TGeoNavigator.h"              
#include "TGeoNode.h"
#include "TGeoManager.h"
#include "TGeoBBox.h"
#include "TVector3.h"
#include "TTreeReader.h"
#include "TTreeReaderValue.h"

#include <iomanip>
#include <iostream>

using std::cout;
using std::cerr;
using std::endl;
using std::setw;
using std::div;


// -----   Default constructor   -------------------------------------------
ShipGoliathField::ShipGoliathField() 
  : FairField()
{
}
// -------------------------------------------------------------------------



// -----   Standard constructor   ------------------------------------------
ShipGoliathField::ShipGoliathField(const char* name)
  : FairField(name)
{
}
// -------------------------------------------------------------------------


// -----   Destructor   ----------------------------------------------------
ShipGoliathField::~ShipGoliathField() { }
// -------------------------------------------------------------------------

/*void  ShipGoliathField::get(const double& posX, const double& posY, const double& posZ, double& Bx, double& By, double& Bz) const {
  if ((posX < coords[0][0]) && (posX > coords[0][3]) && (posY < coords[0][1]) && (posY > coords[0][4]) && (posZ < coords[0][2]+5.) && (posZ>coords[0][5]+5.) ) {
     Bx = GetBx(posX, posY, posZ);
     By = GetBy(posX, posY, posZ);
     Bz = GetBz(posX, posY, posZ);         
  }
  else {
    for (Int_t i=1;i<13;i++){  
     if ((posX < coords[i][0]) && (posX > coords[i][3]) && (posY < coords[i][1]) && (posY > coords[i][4]) && (posZ < coords[i][2]) && (posZ>coords[i][5])) {
       Bx = 0.;
       By = 0.5;
       Bz = 0.; 
       break;      
     }      
    } 
  } 
}
*/

void ShipGoliathField::Init(const char* fieldfile){

  fieldmap = TFile::Open(fieldfile);
  
  
  TH3D* histbx= (TH3D*)fieldmap->Get("Bx");
  TH3D* histby= (TH3D*)fieldmap->Get("By"); 
  TH3D* histbz= (TH3D*)fieldmap->Get("Bz");   
  xmin = histbx->GetXaxis()->GetXmin();
  xmax = histbx->GetXaxis()->GetXmax();  
  ymin = histbx->GetYaxis()->GetXmin();
  ymax = histbx->GetYaxis()->GetXmax();    
  zmin = histbx->GetZaxis()->GetXmin();
  zmax = histbx->GetZaxis()->GetXmax(); 
    
  ShipGoliathField::sethistbxyz(histbx, histby, histbz);

  /*    
  TVector3 bot,top;
  std::cout<<"ShipGoliathField::setup: making string vector"<<std::endl;  
  std::vector<TString> volume={"/volGoliath_1/VolVacuum_1","/volGoliath_1/volLateralS1_1","/volGoliath_1/volLateralS2_1","/volGoliath_1/volLateralSurface1low_1",\
  "/volGoliath_1/volLateralSurface2low_1","/volGoliath_1/volLateralS1_b_1","/volGoliath_1/volLateralS2_b_1","/volGoliath_1/volLateralSurface1blow_1",\
  "/volGoliath_1/volLateralSurface2blow_1","/volGoliath_1/volLateralS1_d_1","/volGoliath_1/volLateralS2_d_1","/volGoliath_1/volLateralS1_c_1",\
  "/volGoliath_1/volLateralS2_c_1"};
  for (Int_t i=0;i<13;i++){
    std::cout<<"ShipGoliathField::setup: getpos volume "<<volume[i]<<std::endl;  
    ShipGoliathField::getpos(volume[i],bot,top);
    for (Int_t j=0;j<3;j++) {
      coords[i][j]=top[j];
      coords[i][j+3]=bot[j];        
    }

    //std::cout<<volume[i]<<" "<<coords[i][3] << " posX " << posX <<" "<< coords[i][0] << ";" << coords[i][4] << " posY "<< posY <<" "<<  coords[i][1] << ";" << coords[i][5] << " posZ " << posZ<<" "<< coords[i][2]<<std::endl; 
  }   
  */
}


void ShipGoliathField::getpos(TString volname, TVector3 &vbot, TVector3 &vtop) const {
   std::cout<<"ShipGoliathField::getpos:  GetCurrentNavigator volname "<<volname<<std::endl; 
   TGeoNavigator* nav;
   if (gGeoManager) {
   nav = gGeoManager->GetCurrentNavigator();}
   else { std::cout<<"No geomanager"<<std::endl;}
   std::cout<<"ShipGoliathField::getpos: cd to volume "<<volname<<std::endl;   
   Bool_t rc = nav->cd(volname);
   if (not rc){
       cout << "ShipGoliathfield::getpos, TGeoNavigator failed "<<volname<<endl; 
       return;
   }  
   std::cout<<"ShipGoliathField::getpos GetCurrentNode"<<std::endl;      
   TGeoNode* W = nav->GetCurrentNode();
   TGeoBBox* S = dynamic_cast<TGeoBBox*>(W->GetVolume()->GetShape());
   Double_t top[3] = {S->GetDX(),S->GetDY(),S->GetDZ()};
   Double_t bot[3] = {-S->GetDX(),-S->GetDY(),-S->GetDZ()};
   Double_t Gtop[3],Gbot[3];
   nav->LocalToMaster(top, Gtop);
   nav->LocalToMaster(bot, Gbot);
   vtop.SetXYZ(Gtop[0],Gtop[1],Gtop[2]);
   vbot.SetXYZ(Gbot[0],Gbot[1],Gbot[2]);
}


void ShipGoliathField::close(){
  //char* mypath =  std::getenv("mySHIPSOFT");
  //strcat(mypath,"/FairShip/field/GoliathFieldMap.root");
  //fieldmap->Close(mypath); 
  //gROOT->cd();    
}

// -----   Get x component of field   --------------------------------------
Double_t ShipGoliathField::GetBx(Double_t x, Double_t y, Double_t z)  {
   Double_t bx=0.;
   TH3D* hbx;

   if ((x < xmin )|| (x> xmax) || (y < ymin) || (y>ymax) || ((z-350.75)<zmin) || ((z-350.75)>zmax)) {
       return bx;}  
    // FairShip: 0 after absorber -384.5<target<-240 -239.9<absorber<0<T1T2<121<Goliath<481<T3T4<755 766.6<RPC<966.6    
    hbx=ShipGoliathField::gethistbx();
    Int_t binx = hbx->GetXaxis()->FindBin(x); 
    Int_t biny = hbx->GetYaxis()->FindBin(y); 
    Int_t binz = hbx->GetZaxis()->FindBin(z - 350.75); 
    bx=hbx->GetBinContent(binx,biny,binz)*tesla;    
    //cout << "GetBX " << x << ", binx " << binx <<" y "<< y << " biny "<<biny<<" z "<< z << " binz "<<binz<<" Bx= " << bx <<  endl;
   return bx;
}

// -------------------------------------------------------------------------


// -----   Get y component of field   --------------------------------------
Double_t ShipGoliathField::GetBy(Double_t x, Double_t y, Double_t z) {
    Double_t by=0.;
    TH3D* hby;

   if ((x < xmin )|| (x> xmax) || (y < ymin) || (y>ymax) || ((z-350.75)<zmin) || ((z-350.75)>zmax)) {
       return by;}   
    hby=ShipGoliathField::gethistby();
    Int_t binx = hby->GetXaxis()->FindBin(x); 
    Int_t biny = hby->GetYaxis()->FindBin(y); 
    Int_t binz = hby->GetZaxis()->FindBin(z- 350.75); 
    by=hby->GetBinContent(binx,biny,binz)*tesla;    
   return by;
}

// -------------------------------------------------------------------------



// -----   Get z component of field   --------------------------------------
Double_t ShipGoliathField::GetBz(Double_t x, Double_t y, Double_t z)  {
    Double_t bz=0.;
    TH3D* hbz;

   if ((x < xmin )|| (x> xmax) || (y < ymin) || (y>ymax) || ((z-350.75)<zmin) || ((z-350.75)>zmax)) {
       return bz;}   
       
    hbz=ShipGoliathField::gethistbz(); 
    Int_t binx = hbz->GetXaxis()->FindBin(x); 
    Int_t biny = hbz->GetYaxis()->FindBin(y); 
    Int_t binz = hbz->GetZaxis()->FindBin(z- 350.75); 
    bz=hbz->GetBinContent(binx,biny,binz)*tesla;    
  return bz;
}


// -------------------------------------------------------------------------



// -----   Screen output   -------------------------------------------------
void ShipGoliathField::Print() {
  cout << "======================================================" << endl;
  cout << "----  " << fTitle << " : " << fName << endl;
  cout << "----" << endl;
  cout << "----  Field type    : constant" << endl;
  cout << "----" << endl;
  cout << "----  Field regions : " << endl;
  cout.precision(4);
  cout << "======================================================" << endl;
}
// -------------------------------------------------------------------------



ClassImp(ShipGoliathField)


