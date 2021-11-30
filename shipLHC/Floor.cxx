#include "Floor.h"
#include "vetoPoint.h"

#include "TGeoManager.h"
#include "FairRun.h"                    // for FairRun
#include "FairRuntimeDb.h"              // for FairRuntimeDb
#include "TVirtualMC.h"          // for gMC
#include "TList.h"                      // for TListIter, TList (ptr only)
#include "TObjArray.h"                  // for TObjArray
#include "TString.h"                    // for TString
#include "TGeoBBox.h"
#include "TGeoCompositeShape.h"
#include "TGeoBoolNode.h"
#include "FairGeoMedia.h"
#include "FairGeoBuilder.h"
#include "TGeoTube.h"
#include "TVector3.h"
#include "TMatrixD.h"
#include "TGeoMaterial.h"
#include "TGeoMedium.h"
#include "ShipDetectorList.h"
#include "ShipStack.h"
#include "TParticle.h"

#include "TClonesArray.h"
#include <stddef.h>                     // for NULL
#include <iostream>                     // for operator<<, basic_ostream, etc

Floor::Floor()
  : FairDetector("Floor", kTRUE, kVETO),
    fFastMuon(kFALSE),
    fMakeSensitive(kFALSE),
    fEmin(0),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fThick(-1.),
    fzPos(3E8),
    fTotalEloss(0),
    fFloorPointCollection(new TClonesArray("vetoPoint"))
{}

Floor::~Floor()
{
  if (fFloorPointCollection) {
    fFloorPointCollection->Delete();
    delete fFloorPointCollection;
  }
}

Bool_t  Floor::ProcessHits(FairVolume* vol)
{
  /** This method is called from the MC stepping */
  //Set parameters at entrance of volume. Reset ELoss.
  if ( gMC->IsTrackEntering() ) {
    fELoss  = 0.;
    fTime   = gMC->TrackTime() * 1.0e09;
    fLength = gMC->TrackLength();
    gMC->TrackPosition(fPos);
    gMC->TrackMomentum(fMom);
  }
  // Sum energy loss for all steps in the active volume
  fELoss += gMC->Edep();

  // Create vetoPoint at exit of active volume
  if ( gMC->IsTrackExiting()    ||
       gMC->IsTrackStop()       ||
       gMC->IsTrackDisappeared()   ) {
    fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();

    Int_t veto_uniqueId = 47.;

    TParticle* p=gMC->GetStack()->GetCurrentTrack();
    Int_t pdgCode = p->GetPdgCode();
    TLorentzVector Pos;
    gMC->TrackPosition(Pos);
    TLorentzVector Mom;
    gMC->TrackMomentum(Mom);
    Double_t xmean = (fPos.X()+Pos.X())/2. ;
    Double_t ymean = (fPos.Y()+Pos.Y())/2. ;
    Double_t zmean = (fPos.Z()+Pos.Z())/2. ;
    LOG(DEBUG)<< veto_uniqueId << " :(" << xmean << ", " << ymean << ", " << zmean << "): " << fELoss;
    AddHit(fTrackID, veto_uniqueId, TVector3(xmean, ymean,  zmean),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
           fELoss,pdgCode,TVector3(Pos.X(), Pos.Y(), Pos.Z()),TVector3(Mom.Px(), Mom.Py(), Mom.Pz()) );
  }

  return kTRUE;
}

void Floor::EndOfEvent()
{
  fFloorPointCollection->Clear();
  fTotalEloss=0;
}

void Floor::PreTrack(){
    if (fFastMuon && TMath::Abs(gMC->TrackPid())!=13){
        gMC->StopTrack();
    }
    TLorentzVector  mom;
    TLorentzVector pos;
    gMC->TrackMomentum(mom);
    gMC->TrackPosition(pos);
    if  ( (mom.E()-mom.M() )<fEmin && pos.Z()<fzPos){
      gMC->StopTrack();
      return;
    }
}

void Floor::Initialize()
{
  FairDetector::Initialize();
}

Int_t Floor::InitMedium(const char* name) 
{
   static FairGeoLoader *geoLoad=FairGeoLoader::Instance();
   static FairGeoInterface *geoFace=geoLoad->getGeoInterface();
   static FairGeoMedia *media=geoFace->getMedia();
   static FairGeoBuilder *geoBuild=geoLoad->getGeoBuilder();

   FairGeoMedium *ShipMedium=media->getMedium(name);

   if (!ShipMedium)
   {
     Fatal("InitMedium","Material %s not defined in media file.", name);
     return -1111;
   }
   TGeoMedium* medium=gGeoManager->GetMedium(name);
   if (medium!=NULL)
     return ShipMedium->getMediumIndex();
   return geoBuild->createMedium(ShipMedium);
}

TVector3 Floor::crossing(TVector3 H1,TVector3 H2,TVector3 H3,TVector3 P1,TVector3 P2,TVector3 P3)
{
     TMatrixD M(3,3);
     TMatrixD P(3,1);
     TMatrixD X(3,1);
     std::map<int,TVector3> Row = {
     {0,H1},{1,H2},{2,H3}
     };
     std::map<int,TVector3> P123 = {
     {0,P1},{1,P2},{2,P3}
     };
     for( int j = 0;j<3;j+=1) {
          P[j][0] = Row[j].Dot(P123[j]);
         for( int k = 0;k<3;k+=1) {
              M[j][k] = Row[j][k];
        }
     }
     auto Minv  =  M.Invert();
     X.Mult(Minv,P);
     TVector3 Crossing(X[0][0],X[1][0],X[2][0]);
     return Crossing;
}
void Floor::ConstructGeometry()
{

	TGeoVolume *top = gGeoManager->GetTopVolume();
	InitMedium("Concrete");
	TGeoMedium *concrete = gGeoManager->GetMedium("Concrete");
	InitMedium("Rock");
	TGeoMedium *rock = gGeoManager->GetMedium("Rock");
         InitMedium("vacuum");
	TGeoMedium *vacuum = gGeoManager->GetMedium("vacuum");

        TGeoVolume *tunnel= new TGeoVolumeAssembly("Tunnel");

        TGeoVolume *detector = new TGeoVolumeAssembly("Detector");  // assembly to place detetector elements in local coordinates
         /** from geometer, with z pointing upwards, via localSND2CCS and then CCS2SNDPhysics
                 Double_t M[9] = {0.999978, 0.0000821516, -0.006606, 
                                                    -0.00660651, -0.0124347, 0.999901,
                                                   -4.69368*10^-15, 0.999923, 0.0124349}
         **/
         // with y-axis upwards, R = ((-1,0,0),(0,0,1),(0,1,0)), M = M R^-1
         Double_t M[9] = {0.999978,   -0.006606,   0.0000821516,
                                    0.00660651,  0.999901,  -0.0124347,
                                    4.69368E-15, 0.0124349, 0.999923};

         auto localSND_physCS_rot      = new TGeoRotation("localSND_physCS_rot");
         localSND_physCS_rot ->SetMatrix(M);
         auto localSND_physCS_comb = new TGeoCombiTrans("localSND_physCS",0.,0.,0.,localSND_physCS_rot);    // origin is 480m downstream of IP1
         localSND_physCS_comb->RegisterYourself();
         top->AddNode(detector, 0,localSND_physCS_comb);

// from Fluka, geo4SND.inp, 25.12.2020
  std::vector<double> TI18_o1  = {-221.4191473578 , 76.66172460057,   48820.152816717, 131.72892289383,   33.003800302801, -543.2846767937, 200.28612174928};
  std::vector<double> TI18_i1   = {-221.4191473578 , 76.66172460057,   48820.152816717, 131.72892289383,   33.003800302801, -543.2846767937, 175.0}; 
  std::vector<double> TI18_o2 = {-92.57914735775, 108.94172460057, 48288.782816717, 130.14367334394,   56.877589206698, -479.4033418058, 200.0};
  std::vector<double> TI18_i2   = {-92.57914735775, 108.94172460057, 48288.782816717, 130.14367334394,   56.877589206698, -479.4033418058, 175.0};
  std::vector<double> TI18_o3 = {14.66085264225,  155.81172460057, 47893.742816717, 1387.8506462618,  818.72395745673, -4733.240081082, 200.0};
  std::vector<double> TI18_i3   = {14.66085264225,  155.81172460057, 47893.742816717, 1387.8506462618,  818.72395745673, -4733.240081082, 175.0};
  std::vector<double> UJ18_o  = {-471.0, 25.5, 48750.0,   -201.8536100583633, 0.0, 3594.3365340638884, 495.0};
  std::vector<double> UJ18_i   = {-471.0,25.5, 48800.39, -201.8536100583633, 0.0, 3494.4938525621, 445.0};
  std::vector<double> UJ18_x  = {-92.57914735775,108.94172460057,48288.782816717,-141.138131672,-35.36121461014,582.09072513608,175.0};
  std::vector<double> tu012_i = {     -596.38194369,    30., 47654.730979, -155.10509191, 0.0,2761.9020453, 220.0};
  std::vector<double> tu012_o = {   -596.38194369,    30., 4.7654730979E+04, -155.10509191, 0.0,2761.9020453, 250.0};
  std::vector<double> tu011_i = {   -522.09173359,      30., 4.6171636594E+04, -99.7891926, 0.0,1954.9587043, 220.0};
  std::vector<double> tu011_o = {   -522.09173359,    30., 4.6171636594E+04, -99.7891926, 0.0,1954.9587043, 250.0,360.,850.};
  std::vector<double> tu010_i = {   -451.24339295,      30., 4.4607412772E+04, -89.817671994, 0.0,1955.4422017, 220.0};
  std::vector<double> tu010_o = {   -451.24339295,     30., 4.4607412772E+04, -89.817671994, 0.0,1955.4422017, 250.0,750.,1100.};
// PLA   TI18_01 and TI18_02
  std::vector<double> TI18_1_bot = {   0.67644808637366, -74.85571453913, -4.530940169849, -221.4171473578, -18.33127539943-3.5,48818.967816717,  // subtract 3.5cm to agree with Antonio measurements
                                                                                 0.63027909276104 ,-74.86684394728, -4.35010639392,   -221.4171473578, -93.32587539943,48818.036016717};
// side PLA TI18_08 and PLA TI18_09 
  std::vector<double> TI18_1_sid = {   -95.08832719702, 21.886725033285, -21.89021009926, -39.11837578468,3.7557255037298,48858.930618475,
                                                                               -94.65075310463, -21.38126814052,  -24.16767074894,-402.3825398293,  5.6093808446198,48770.79950338};
// PLA TI18_04 and PLA TI18_03 
  std::vector<double> TI18_2_bot = {   1.590393176461, -74.48871190132, -8.55964069504,     -92.6293750264,     13.94692460057-3.5, 48287.934643717,    // subtract 3.5cm to agree with Antonio measurements
                                                                                 1.12692975448,   -74.65145228529, -7.089125547405,    -92.57914735775, -61.04827539943, 48286.672816717};
// side PLA TI18_81 and PLA TI18_91 
  std::vector<double> TI18_2_sid = {   9.5229226656561, -2.052234306283, 2.2588218587662, 119.6722824853, -43.26523379053, 48132.959403311,
                                                                               0.9420958238706, 0.1874442034604, 0.2780649358884, -220.8962283082, 57.49004938073, 48051.134027534};
// PLA   TI18_05 and TI18_06
  std::vector<double> TI18_3_bot = {   2.6719179804842, -74.62099192635, -12.16834081665, 237.27547988904, 188.51303030346, 47133.251503475,
                                                                                2.2386457107868, -74.59695305235, -12.40093386351, 14.844992780245, -22.78799545647,   47890.126221505};
// side PLA TI18_08x and PLA TI18_09x 
  std::vector<double> TI18_3_sid = {   9.4281652604622, -2.374007701455, 2.3396124281475, 399.46744859669,       116.81598987751,      47153.021981939,
                                                                               9.332746336299,   1.9001431836442, 3.0478354225656, 88.79276895539223, 130.4393658272924, 47064.80229883217};
  std::vector<double> PM18_ci = {50660.2873, -1256.8854,700.0,500.};
  std::vector<double> PM18_co = {50660.2873, -1256.8854, 750.,500.};
  std::map<TString,std::vector<double>> geoParameters = {
  {"TI18_o1",TI18_o1},
  {"TI18_i1",TI18_i1},
  {"TI18_o2",TI18_o2},
  {"TI18_i2",TI18_i2},
  {"TI18_o3",TI18_o3},
  {"TI18_i3",TI18_i3},
  {"UJ18_o",UJ18_o},
  {"UJ18_i",UJ18_i},
  {"tu010_o",tu010_o},
  {"tu010_i",tu010_i},
  {"tu011_o",tu011_o},
  {"tu011_i",tu011_i},
  {"tu012_o",tu012_o},
  {"tu012_i",tu012_i},
  {"UJ18_x",UJ18_x},
  {"PM18_ci",PM18_ci},
  {"PM18_co",PM18_co},
  {"TI18_1_bot",TI18_1_bot},
  {"TI18_1_sid",TI18_1_sid},
  {"TI18_2_bot",TI18_2_bot},
  {"TI18_2_sid",TI18_2_sid},
  {"TI18_3_bot",TI18_3_bot},
  {"TI18_3_sid",TI18_3_sid}
  };
  std::vector<TString> loop1 = {"TI18_1","TI18_2","TI18_3"};
  std::vector<TGeoCompositeShape*> shapes;
  std::vector<TGeoCombiTrans*> trans;
  for(auto it = std::begin(loop1); it != std::end(loop1); ++it) {
    LOG(DEBUG)<<"Floor: DEBUG start" << *it;
    auto name = TString(*it);
    TString name_i       = TString(*it).ReplaceAll("_","_i");
    TString name_o     = TString(*it).ReplaceAll("_","_o");
    TString name_bot = name+"_bot";
    TString name_sid  = name+"_sid";
    LOG(DEBUG)<<"Floor: " << geoParameters[name_i.Data()][0]<< " "<< geoParameters[name_i.Data()][1]<< " "<< geoParameters[name_i.Data()][2]<<" "<<name_i;
    TVector3 P  = TVector3(geoParameters[name_i.Data()][0],geoParameters[name_i.Data()][1],geoParameters[name_i.Data()][2] - SND_Z);
    TVector3 H = TVector3(geoParameters[name_i.Data()][3],geoParameters[name_i.Data()][4],geoParameters[name_i.Data()][5]);
    auto T  =  P + 0.5*H;
    double rotBeta      = TMath::ACos(H[2]/H.Mag());
    double rotAlpha   = TMath::ATan2(H[0]/H.Mag(), -H[1]/H.Mag());
    double  rotGamma = TMath::ACos(H[1]/H.Mag()/TMath::Sqrt(1-pow(H[2]/H.Mag(),2)));
    auto R = new TGeoRotation("R_"+name,rotAlpha*180./TMath::Pi(),rotBeta*180./TMath::Pi(),rotGamma*180./TMath::Pi());
    auto CombiTrans = new TGeoCombiTrans("T_"+name,T[0],T[1],T[2],R);
    CombiTrans->RegisterYourself();
    auto X = geoParameters[name_bot.Data()];
   TVector3 Ptop(X[3],X[4], X[5]   -SND_Z);
   TVector3 Pbot(X[9],X[10], X[11]-SND_Z);
   TVector3 Htop(X[0], X[1],X[2]);
   TVector3 Hbot(X[6], X[7],X[8]);
   X = geoParameters[name_sid.Data()];
   TVector3 Pleft(X[9],X[10], X[11]   -SND_Z);
   TVector3 Prigh(X[3],X[4], X[5]-SND_Z);
   TVector3 Hleft(X[6], X[7],X[8]);
   TVector3 Hrigh(X[0], X[1],X[2]);
   std::map<TString,TVector3> face = {
   {"front",P},{"back",P+H}
   };
   std::vector<TVector3> points;
   std::vector<TVector3> GlobalPoints;
   Double_t  master[3], P1[3], P2[3], P3[3], P4[3];
#
   rotBeta       = TMath::ACos(Htop[2]/Htop.Mag());
   rotAlpha     = TMath::ATan2(Htop[0]/H.Mag(), -Htop[1]/H.Mag()) ;
   rotGamma = TMath::ACos(Htop[1]/Htop.Mag()/TMath::Sqrt(1-pow(Htop[2]/Htop.Mag(),2)));
   auto RF = new TGeoRotation( "R_tube_"+name,rotAlpha*180./TMath::Pi(),rotBeta*180./TMath::Pi(),rotGamma*180./TMath::Pi());
   Double_t dY = (Htop.Dot(Ptop)-Htop.Dot(Pbot))/Htop.Mag();
   std::vector<TString> loopF = {"front","back"};
   for(auto il = std::begin(loopF); il != std::end(loopF); ++il) {
      auto X0 = crossing(Hleft,Htop,H,Pleft,Ptop,face[*il]);
      for( int i = 0;i<3;i+=1) {   master[i]=X0[i];}
      GlobalPoints .push_back(X0);
      RF->MasterToLocal(master,P1);
      points.push_back(TVector3(P1[0],P1[1],P1[2]));
      LOG(DEBUG) << "top left "<<X0[0]<<","<<X0[1]<<","<<X0[2]<<";  "<<P1[0]<<","<<P1[1]<<","<<P1[2];
      X0 = crossing(Hrigh,Htop,H,Prigh,Ptop,face[*il]);
      for( int i = 0;i<3;i+=1) {   master[i]=X0[i];}
      GlobalPoints .push_back(X0);
      RF->MasterToLocal(master,P2);
      points.push_back(TVector3(P2[0],P2[1],P2[2]));
      LOG(DEBUG) << "top right "<<X0[0]<<","<<X0[1]<<","<<X0[2]<<";  "<<P2[0]<<","<<P2[1]<<","<<P2[2];
      X0 = crossing(Hrigh,Htop,H,Prigh,Pbot,face[*il]);
      for( int i = 0;i<3;i+=1) {   master[i]=X0[i];}
      GlobalPoints .push_back(X0);
      RF->MasterToLocal(master,P3);
      points.push_back(TVector3(P3[0],P3[1],P3[2]));
      LOG(DEBUG) << "bottom right "<<X0[0]<<","<<X0[1]<<","<<X0[2]<<";  "<<P3[0]<<","<<P3[1]<<","<<P3[2];
      X0 = crossing(Hleft,Htop,H,Pleft,Pbot,face[*il]);
      for( int i = 0;i<3;i+=1) {   master[i]=X0[i];}
      GlobalPoints .push_back(X0);
      RF->MasterToLocal(master,P4);
      points.push_back(TVector3(P4[0],P4[1],P4[2]));
      LOG(DEBUG) << "bottom left "<<X0[0]<<","<<X0[1]<<","<<X0[2]<<";  "<<P4[0]<<","<<P4[1]<<","<<P4[2];
   }
   Double_t dZ = (P3[2]-P1[2])/2.;
   auto arb = new TGeoArb8(name+"_arb8",dZ);
   arb->SetVertex(0, points[1][0], points[1][1]);
   arb->SetVertex(1, points[5][0], points[5][1]);
   arb->SetVertex(2, points[4][0], points[4][1]);
   arb->SetVertex(3, points[0][0], points[0][1]);
   arb->SetVertex(4, points[2][0], points[2][1]);
   arb->SetVertex(5, points[6][0], points[6][1]);
   arb->SetVertex(6, points[7][0], points[7][1]);
   arb->SetVertex(7, points[3][0], points[3][1]);
//   to get the transformation
   Double_t local[3] = {points[1][0],points[1][1],-dZ};
   RF->LocalToMaster(local,master);
   TVector3 Tf(GlobalPoints[1][0]-master[0],GlobalPoints[1][1]-master[1],GlobalPoints[1][2]-master[2]);
   auto CombiTransF = new TGeoCombiTrans("T_floor_"+name,Tf[0],Tf[1],Tf[2],RF);
   CombiTransF->RegisterYourself();
   auto tube   =  gGeoManager->MakeTube(name+"_tube", concrete, geoParameters[name_i.Data()][6], geoParameters[name_o.Data()][6],H.Mag()/2.);
   auto Fulltube   =  gGeoManager->MakeTube(name+"_fulltube", concrete, 0., geoParameters[name_o.Data()][6],H.Mag()/2.);
   LOG(DEBUG)<<name<<" "<<Tf[0]<<" "<<Tf[1]<<" "<<Tf[2];
   auto CombiTransF1 = new TGeoCombiTrans("T_floorS1_"+name,Tf[0],Tf[1]-2*dZ,Tf[2],RF);
   auto CombiTransF2 = new TGeoCombiTrans("T_floorS2_"+name,Tf[0],Tf[1]-2*dZ,Tf[2]-20,RF);
   CombiTransF1->RegisterYourself();
   CombiTransF2->RegisterYourself();
   auto sunion = new TGeoCompositeShape(name+"_union","("+name+"_tube:T_"+name+"+"+name+"_arb8:T_floor_"+name+"-"+
                                                                                            name+"_arb8:T_floorS1_"+name+"-"+name+"_arb8:T_floorS2_"+name+")");
   shapes.push_back(sunion);
   auto Fsunion = new TGeoCompositeShape(name+"_Funion","("+name+"_fulltube:T_"+name+"+"+name+"_arb8:T_floor_"+name+"-"+
                                                                                            name+"_arb8:T_floorS1_"+name+"-"+name+"_arb8:T_floorS2_"+name+")");
   shapes.push_back(Fsunion);

  }
  LOG(DEBUG) << "shapes "<<shapes[0]->GetName()<<" "<<shapes[1]->GetName()<<" "<<shapes[2]->GetName();
  auto total = new TGeoCompositeShape("Stotal","TI18_1_union+TI18_2_union+TI18_3_union");
  auto volT = new TGeoVolume("VTI18",total,concrete);
  volT->SetTransparency(0);
  volT->SetLineColor(kGray);
// make tunnel sensitive for debugging
  if (fMakeSensitive) {AddSensitiveVolume(volT);}
  tunnel->AddNode(volT, 1);

  std::vector<TString> loop2 = {"UJ18_","tu010_","tu011_","tu012_"};
  for(auto it = std::begin(loop2); it != std::end(loop2); ++it) {
    TString name_i = TString(*it).ReplaceAll("_","_i");
    TString name_o= TString(*it).ReplaceAll("_","_o");
    TString name_F = "F"+TString(*it);
    TVector3 P  = TVector3(geoParameters[name_i.Data()][0],geoParameters[name_i.Data()][1],geoParameters[name_i.Data()][2] - SND_Z);
    TVector3 H = TVector3(geoParameters[name_i.Data()][3],geoParameters[name_i.Data()][4],geoParameters[name_i.Data()][5]);
    auto vol = gGeoManager->MakeTube(*it, concrete, geoParameters[name_i.Data()][6], geoParameters[name_o.Data()][6],H.Mag()/2.-5.);  // subtract 5cm to avoid overlap
    auto Fvol = gGeoManager->MakeTube(name_F, concrete, 0., geoParameters[name_o.Data()][6],H.Mag()/2.-5.);
    vol->SetTransparency(0);
    vol->SetLineColor(kGray);
    auto T  =  P + 0.5*H;
    double rotBeta      = TMath::ACos(H[2]/H.Mag());
    double rotAlpha   = TMath::ATan2(H[0]/H.Mag(), -H[1]/H.Mag());
    double  rotGamma = TMath::ACos(H[1]/H.Mag()/TMath::Sqrt(1-pow(H[2]/H.Mag(),2)));
    TString name = "R_"+TString(*it);
    auto R = new TGeoRotation(name,rotAlpha*180./TMath::Pi(),rotBeta*180./TMath::Pi(),rotGamma*180./TMath::Pi());
    auto CombiTrans = new TGeoCombiTrans("TS_"+TString(*it),T[0],T[1],T[2],R);
    CombiTrans->RegisterYourself();
    trans.push_back(CombiTrans);
  }
    auto total2 = new TGeoCompositeShape("Stotal2","tu010_:TS_tu010_+tu011_:TS_tu011_");
    auto Ftotal2 = new TGeoCompositeShape("Ftotal2","Ftu010_:TS_tu010_+Ftu011_:TS_tu011_");
    auto volT2 = new TGeoVolume("VUJ",total2,concrete);
    volT2->SetTransparency(0);
    volT2->SetLineColor(kGray);
    tunnel->AddNode(volT2, 1);

/*
  std::vector<TString> loopr = {"tu010_","tu011_"};
  for(auto it = std::begin(loopr); it != std::end(loopr); ++it) {
    TString name_o= TString(*it).ReplaceAll("_","_o");
    TString name_b = TString(*it).ReplaceAll("_","_cone");
    TString name_c = TString(*it).ReplaceAll("_","_rock");
    TString name = TString(*it);
    TString name_x = TString(*it).ReplaceAll("_","_x");

    TVector3 H = TVector3(geoParameters[name_o.Data()][3],geoParameters[name_o.Data()][4],geoParameters[name_o.Data()][5]);
    auto tube    = new TGeoTube(name_x,0., geoParameters[name_o.Data()][6]+10.,H.Mag()/2.+0.1);
    auto cone    = gGeoManager->MakeCone(name_b,rock,H.Mag()/2.,0.,geoParameters[name_o.Data()][8],0.,geoParameters[name_o.Data()][7]);
    auto Srock   = new TGeoCompositeShape(name_c, name_b+":TS_"+name+"-"+name_x+":TS_"+name);
  }
    auto total3 = new TGeoCompositeShape("Stotal3","tu010_rock+tu011_rock");
    auto volT3  = new TGeoVolume("Vrock",total3,rock);
    volT3->SetTransparency(75);
    volT3->SetLineColor(kRed);
    tunnel->AddNode(volT3, 1);

// add rock up to Fluka scoring plane, 409 m from IP1.
  double zs = 40900.;
  double dz = (geoParameters["tu010_o"][2] - zs)/2.;
  auto fluka = gGeoManager->MakeBox("FlukaScoringPlane",rock, geoParameters["tu010_o"][8],geoParameters["tu010_o"][8],dz);
  fluka->SetLineColor(kRed);
  tunnel->AddNode(fluka,1, new TGeoTranslation(-350.,0,dz+zs- SND_Z-50.));  // move 50cm upstream to avoid overlap
*/

 double zs = 40900.;  // scoring plane
 double dz =  (geoParameters["TI18_o1"][2] - zs)/2.;

 auto bigBox   = new TGeoBBox("BigBox", 1000.,1000. , dz);
 auto TR_1       = new TGeoTranslation("TR_1",0.,0.,-dz+geoParameters["TI18_o1"][2]-SND_Z - 50.); // move a bit more upstream to have free view from the back
 TR_1->RegisterYourself();
 auto cutOut   = new TGeoCompositeShape("cutOut", "BigBox:TR_1-Ftotal2-(TI18_1_Funion+TI18_2_Funion+TI18_3_Funion)");
 auto volT3      = new TGeoVolume("Vrock",cutOut,rock);
 volT3->SetTransparency(75);
 volT3->SetLineColor(kRed);
 tunnel->AddNode(volT3, 1);

auto exitPlane =  gGeoManager->MakeBox("exitScoringPlane",vacuum,1000.,1000. , 1.);
exitPlane->SetLineColor(kGreen);
exitPlane->SetVisibility(kFALSE);
if (fMakeSensitive) {AddSensitiveVolume(exitPlane);}
tunnel->AddNode(exitPlane,1, new TGeoTranslation(0,0,1000.));

  top->AddNode(tunnel , 1);
}

vetoPoint* Floor::AddHit(Int_t trackID, Int_t detID,
                                      TVector3 pos, TVector3 mom,
                                      Double_t time, Double_t length,
                                      Double_t eLoss, Int_t pdgCode,TVector3 Lpos, TVector3 Lmom)
{
  TClonesArray& clref = *fFloorPointCollection;
  Int_t size = clref.GetEntriesFast();
  LOG(DEBUG) << "add veto point "<<size<<" "<<trackID<<" "<<detID;
  return new(clref[size]) vetoPoint(trackID, detID, pos, mom,
         time, length, eLoss, pdgCode,Lpos,Lmom);
}

void Floor::Register()
{

  FairRootManager::Instance()->Register("vetoPoint", "veto",
                                        fFloorPointCollection, kTRUE);
}

TClonesArray* Floor::GetCollection(Int_t iColl) const
{
  if (iColl == 0) { return fFloorPointCollection; }
  else { return NULL; }
}
void Floor::Reset()
{
  fFloorPointCollection->Clear();
}

ClassImp(Floor)
