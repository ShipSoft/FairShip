#include "Floor.h"
#include "vetoPoint.h"

#include "TGeoManager.h"
#include "FairRun.h"                    // for FairRun
#include "FairRuntimeDb.h"              // for FairRuntimeDb
#include "FairRootManager.h"            // for FairRun
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

#include "TGeoPara.h"
#include "TGeoArb8.h"

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
    TLorentzVector pos;
    gMC->TrackPosition(pos);
    if (fFastMuon && pos.Z()<fzPos && TMath::Abs(gMC->TrackPid())!=13){
        gMC->StopTrack();
    }
    TLorentzVector  mom;
    gMC->TrackMomentum(mom);
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
	SND_Z = conf_floats["Floor/z"];

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

         Double_t fTunnelDX = conf_floats["Floor/DX"];
         Double_t fTunnelDY = conf_floats["Floor/DY"];
         Double_t fTunnelDZ = conf_floats["Floor/DZ"];

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
  std::vector<double> TI18_1_bot = {   0.67644808637366, -74.85571453913, -4.530940169849, -221.4171473578, -18.33127539943,48818.967816717, 
                                                                                 0.63027909276104 ,-74.86684394728, -4.35010639392,   -221.4171473578, -93.32587539943,48818.036016717};
// side PLA TI18_08 and PLA TI18_09 
  std::vector<double> TI18_1_sid = {   -95.08832719702, 21.886725033285, -21.89021009926, -39.11837578468,3.7557255037298,48858.930618475,
                                                                               -94.65075310463, -21.38126814052,  -24.16767074894,-402.3825398293,  5.6093808446198,48770.79950338};
// PLA TI18_04 and PLA TI18_03 
  std::vector<double> TI18_2_bot = {   1.590393176461, -74.48871190132, -8.55964069504,     -92.6293750264,     13.94692460057, 48287.934643717,    
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

  // Since 2024 there is a pit on the TI18 floor hosting the veto
  // Unless defined in the geo config file, the pit dims are 0.
  auto vetoPit = new TGeoBBox("vetoPit",
                                 conf_floats["Floor/VetoPitXdim"]/2.,
                                 conf_floats["Floor/VetoPitZdim"]/2.,
                                 conf_floats["Floor/VetoPitYdim"]/2.);
  auto VetoPit_transl = new TGeoTranslation("VetoPit_transl",
                                -conf_floats["Floor/VetoPitX"]-conf_floats["Floor/VetoPitXdim"]/2.,
                                 conf_floats["Floor/VetoPitZ"]-conf_floats["Floor/VetoPitZdim"]/2.,
                                 conf_floats["Floor/VetoPitY"]-conf_floats["Floor/VetoPitYdim"]/2.);
  VetoPit_transl->RegisterYourself();
    
    //UJ18 tunnel
    // UJ18 translation and angle rotation
         Double_t dx_0_UJ18 = -2300.0;
         Double_t dy_0_UJ18 = -273.0;
         Double_t dz_0_UJ18 = 7346.0;
         Double_t rot_X = 1.3;
         Double_t rot_Y = -13.63;
         Double_t rot_Z = 0;
    
         TGeoRotation *rotA = new TGeoRotation("rotA");
         rotA->RotateX(rot_X);
         rotA->RotateY(rot_Y);
         rotA->RotateZ(rot_Z);
         TGeoCombiTrans *matA = new TGeoCombiTrans("matA",dx_0_UJ18, dy_0_UJ18, dz_0_UJ18, rotA);
   
    Double_t dx_UJ18, dy_UJ18, dz_UJ18;
    Double_t dx_UJ181, dx_UJ182, dy_UJ181, dy_UJ182;
    Double_t vert[20], par[20];
    Double_t theta, phi, h1, bl1, tl1, alpha1, h2, bl2, tl2, alpha2;
    Double_t twist;
    Double_t origin[3];
    Double_t rmin, rmax, rmin1, rmax1, rmin2, rmax2;
    Double_t r, rlo, rhi;
    Double_t a, b;
    Double_t point[3], norm[3];
    Double_t rin, stin, rout, stout;
    Double_t thx, phx, thy, phy, thz, phz;
    Double_t alpha, theta1, theta2, phi1, phi2, dphi;
    Double_t tr[3], rot[9];
    Double_t z, density, radl, absl, w;
    Double_t lx, ly, lz, tx, ty, tz;
    Double_t xvert[50], yvert[50];
    Double_t zsect, x0, y0, scale0;
    Int_t nel, numed, nz, nedges, nvert;
    TGeoBoolNode *Boolean = nullptr;

    // UJ18 construction: Sequential naming represents step-by-step Boolean operations (e.g., Cut_001, Add_001, trans_1).
    rmin = 0;
    rmax = 506.18;
    dz_UJ18   = 30;
    TGeoShape *GDMLTube_001 = new TGeoTube("GDMLTube_001",rmin,rmax,dz_UJ18);

    dx_UJ18 = 600;
    dy_UJ18 = 200;
    dz_UJ18 = 40;
    TGeoShape *GDMLBox_001 = new TGeoBBox("GDMLBox_001", dx_UJ18,dy_UJ18,dz_UJ18);

    dx_UJ18 = 0;
    dy_UJ18 = -524.94;
    dz_UJ18 = 0;
    auto trans_1 = new TGeoCombiTrans("trans_1"); // trans = translation
    trans_1->SetTranslation(dx_UJ18, dy_UJ18, dz_UJ18);
    Boolean = new TGeoSubtraction(GDMLTube_001,GDMLBox_001,0,trans_1);
 
    TGeoShape *Cut_001 = new TGeoCompositeShape("Cut_001", Boolean); //Cut = sustraction in boolean operation

    rmin = 0;
    rmax = 506.18;
    dz_UJ18   = 1799.5;
    TGeoShape *GDMLTube_002 = new TGeoTube("GDMLTube_002",rmin,rmax,dz_UJ18);

    rmin = 0;
    rmax = 450;
    dz_UJ18   = 1950;
    TGeoShape *GDMLTube_003 = new TGeoTube("GDMLTube_003",rmin,rmax,dz_UJ18);

    dx_UJ18 = 500;
    dy_UJ18 = 200;
    dz_UJ18 = 2000;
    TGeoShape *GDMLBox_002 = new TGeoBBox("GDMLBox_002", dx_UJ18,dy_UJ18,dz_UJ18);

    dx_UJ18 = 0;
    dy_UJ18 = -257.94;
    dz_UJ18 = 0;
    auto trans_2 = new TGeoCombiTrans("trans_2");
    trans_2->SetTranslation(dx_UJ18, dy_UJ18, dz_UJ18);
    Boolean = new TGeoSubtraction(GDMLTube_003,GDMLBox_002,0,trans_2);

    TGeoShape *Cut_002 = new TGeoCompositeShape("Cut_002", Boolean);
    Boolean = new TGeoSubtraction(GDMLTube_002,Cut_002,0,0);

    TGeoShape *Cut_003 = new TGeoCompositeShape("Cut_003", Boolean);

    dx_UJ18 = 600;
    dy_UJ18 = 200;
    dz_UJ18 = 2000;
    TGeoShape *GDMLBox_003 = new TGeoBBox("GDMLBox_003", dx_UJ18,dy_UJ18,dz_UJ18);

    dx_UJ18 = 0;
    dy_UJ18 = -524.94;
    dz_UJ18 = 0;
    auto trans_3 = new TGeoCombiTrans("trans_3");
    trans_3->SetTranslation(dx_UJ18, dy_UJ18, dz_UJ18);
    Boolean = new TGeoSubtraction(Cut_003,GDMLBox_003,0,trans_3);

    TGeoShape *Cut_004 = new TGeoCompositeShape("Cut_004", Boolean);

    rmin = 0;
    rmax = 506.18;
    dz_UJ18   = 30;
    TGeoShape *GDMLTube_004 = new TGeoTube("GDMLTube_004",rmin,rmax,dz_UJ18);

    dx_UJ18 = 600;
    dy_UJ18 = 200;
    dz_UJ18 = 40;
    TGeoShape *GDMLBox_004 = new TGeoBBox("GDMLBox_004", dx_UJ18,dy_UJ18,dz_UJ18);

    dx_UJ18 = 0;
    dy_UJ18 = -524.94;
    dz_UJ18 = 0;
    auto trans_4 = new TGeoCombiTrans("trans_4");
    trans_4->SetTranslation(dx_UJ18, dy_UJ18, dz_UJ18);
    Boolean = new TGeoSubtraction(GDMLTube_004,GDMLBox_004,0,trans_4);

    TGeoShape *Cut_005 = new TGeoCompositeShape("Cut_005", Boolean);

    dx_UJ18 = 0;
    dy_UJ18 = 0;
    dz_UJ18 = -1829.5;
    auto trans_5 = new TGeoCombiTrans("trans_5");
    trans_5->SetTranslation(dx_UJ18, dy_UJ18, dz_UJ18);
    Boolean = new TGeoUnion(Cut_004,Cut_005,0,trans_5);

    TGeoShape *Add_001 = new TGeoCompositeShape("Add_001", Boolean); // Add = union in boolean operation

    dx_UJ18 = 0;
    dy_UJ18 = 0;
    dz_UJ18 = -1829.5;
    auto trans_6 = new TGeoCombiTrans("trans_6");
    trans_6->SetTranslation(dx_UJ18, dy_UJ18, dz_UJ18);
    Boolean = new TGeoUnion(Cut_001,Add_001,0,trans_6);

    TGeoShape *Add_002 = new TGeoCompositeShape("Add_002", Boolean);

    rmin = 0;
    rmax = 175.65;
    dz_UJ18   = 50;
    TGeoShape *GDMLTube_005 = new TGeoTube("GDMLTube_005",rmin,rmax,dz_UJ18);

    dx_UJ18 = 250;
    dy_UJ18 = 100;
    dz_UJ18 = 60;
    TGeoShape *GDMLBox_005 = new TGeoBBox("GDMLBox_005", dx_UJ18,dy_UJ18,dz_UJ18);

    dx_UJ18 = 0;
    dy_UJ18 = -196.2;
    dz_UJ18 = 0;
    auto trans_7 = new TGeoCombiTrans("trans_7");
    trans_7->SetTranslation(dx_UJ18, dy_UJ18, dz_UJ18);
    Boolean = new TGeoSubtraction(GDMLTube_005,GDMLBox_005,0,trans_7);

    TGeoShape *Cut_006 = new TGeoCompositeShape("Cut_006", Boolean);

    dx_UJ18 = 245.426;
    dy_UJ18 = 106.189;
    dz_UJ18 = -3658.834;
    auto trans_8 = new TGeoCombiTrans("trans_8");
    trans_8->SetTranslation(dx_UJ18, dy_UJ18, dz_UJ18);
    Boolean = new TGeoSubtraction(Add_002,Cut_006,0,trans_8);

    TGeoShape *Cut_007 = new TGeoCompositeShape("Cut_007", Boolean);

    rmin = 0;
    rmax = 220.39;
    dz_UJ18   = 1900;
    TGeoShape *GDMLTube_006 = new TGeoTube("GDMLTube_006",rmin,rmax,dz_UJ18);

    dx_UJ18 = 250;
    dy_UJ18 = 100;
    dz_UJ18 = 1925;
    TGeoShape *GDMLBox_006 = new TGeoBBox("GDMLBox_006", dx_UJ18,dy_UJ18,dz_UJ18);

    dx_UJ18 = 0;
    dy_UJ18 = -224.647;
    dz_UJ18 = 0;
    auto trans_9 = new TGeoCombiTrans("trans_9");
    trans_9->SetTranslation(dx_UJ18, dy_UJ18, dz_UJ18);
    Boolean = new TGeoSubtraction(GDMLTube_006,GDMLBox_006,0,trans_9);

    TGeoShape *Cut_008 = new TGeoCompositeShape("Cut_008", Boolean);

    dx_UJ18 = -193.584;
    dy_UJ18 = 55.7;
    dz_UJ18 = -1829.5;
    auto trans_10 = new TGeoCombiTrans("trans_10");
    trans_10->SetTranslation(dx_UJ18, dy_UJ18, dz_UJ18);
    Boolean = new TGeoSubtraction(Cut_007,Cut_008,0,trans_10);

    TGeoShape *Cut_009 = new TGeoCompositeShape("Cut_009", Boolean);

    dz_UJ18     = 473.8;
    theta  = 0;
    phi    = 0;
    h1     = 37.375;
    bl1    = 204.985;
    tl1    = 204.985;
    alpha1 = 0;
    h2     = 0;
    bl2    = 204.985;
    tl2    = 204.985;
    alpha2 = 0;
    TGeoShape *GDMLTrap_1 = new TGeoTrap("GDMLTrap_1", dz_UJ18,theta,phi,h1,bl1,tl1,alpha1,h2,bl2,tl2,alpha2);

    dx_UJ18 = 236.991;
    dy_UJ18 = -45.068;
    dz_UJ18 = -3156.224;

    thx = 90;    phx = 0;
    thy = 87.92;    phy = 90;
    thz = 2.08;    phz = 270;
    TGeoRotation *rot_1 = new TGeoRotation("rot_1",thx,phx,thy,phy,thz,phz);
    auto trans_11 = new TGeoCombiTrans("trans_11", dx_UJ18, dy_UJ18, dz_UJ18, rot_1);
    Boolean = new TGeoUnion(Cut_009,GDMLTrap_1,0,trans_11);
    TGeoShape *pUJ18_shape_25 = new TGeoCompositeShape("UJ18_shape", Boolean);
    
    //get the new rotation and translation
    TGeoHMatrix * Matrix_setup = new TGeoHMatrix("Matrix_setup");
    Matrix_setup->Multiply(matA);
    Matrix_setup->Multiply(trans_11);
    
    //create the new translation for union(with TI18) subtraction(with rock)
    const Double_t *tr1 = Matrix_setup->GetTranslation();
    TGeoRotation *rot2 = new TGeoRotation();
    rot2->SetMatrix(Matrix_setup->GetRotationMatrix());
    //for registyourself
    auto new_translation_for_UJ18 = new TGeoCombiTrans("new_translation_for_UJ18", tr1[0], tr1[1], tr1[2], rot2);
    new_translation_for_UJ18->RegisterYourself();

    // UJ18_solid (to be subtracted from Bigbox)
    rmin = 0;
    rmax = 506.18;
    dz_UJ18   = 30;
    TGeoShape *GDMLTube_007 = new TGeoTube("GDMLTube_007",rmin,rmax,dz_UJ18);

    dx_UJ18 = 600;
    dy_UJ18 = 200;
    dz_UJ18 = 40;
    TGeoShape *GDMLBox_007 = new TGeoBBox("GDMLBox_007", dx_UJ18,dy_UJ18,dz_UJ18);

    dx_UJ18 = 0;
    dy_UJ18 = -524.94;
    dz_UJ18 = 0;
    auto trans_12 = new TGeoCombiTrans("trans_12");
    trans_12->SetTranslation(dx_UJ18, dy_UJ18, dz_UJ18);
    Boolean = new TGeoSubtraction(GDMLTube_007,GDMLBox_007,0,trans_12);

    TGeoShape *Cut_010 = new TGeoCompositeShape("Cut_010", Boolean);

    rmin = 0;
    rmax = 506.18;
    dz_UJ18   = 1799.5;
    TGeoShape *GDMLTube_008 = new TGeoTube("GDMLTube_8",rmin,rmax,dz_UJ18);

    dx_UJ18 = 600;
    dy_UJ18 = 200;
    dz_UJ18 = 2000;
    TGeoShape *GDMLBox_008 = new TGeoBBox("GDML_Box008", dx_UJ18,dy_UJ18,dz_UJ18);

    dx_UJ18 = 0;
    dy_UJ18 = -524.94;
    dz_UJ18 = 0;
    auto trans_13 = new TGeoCombiTrans("trans_13");
    trans_13->SetTranslation(dx_UJ18, dy_UJ18, dz_UJ18);
    Boolean = new TGeoSubtraction(GDMLTube_008,GDMLBox_008,0,trans_13);

    TGeoShape *Cut_011 = new TGeoCompositeShape("Cut_011", Boolean);

    rmin = 0;
    rmax = 506.18;
    dz_UJ18   = 30;
    TGeoShape *GDMLTube_009 = new TGeoTube("GDMLTube_009",rmin,rmax,dz_UJ18);

    dx_UJ18 = 600;
    dy_UJ18 = 200;
    dz_UJ18 = 40;
    TGeoShape *GDMLBox_009 = new TGeoBBox("GDMLBox_009", dx_UJ18,dy_UJ18,dz_UJ18);

    dx_UJ18 = 0;
    dy_UJ18 = -524.94;
    dz_UJ18 = 0;
    auto trans_14 = new TGeoCombiTrans("trans_14");
    trans_14->SetTranslation(dx_UJ18, dy_UJ18, dz_UJ18);
    Boolean = new TGeoSubtraction(GDMLTube_009,GDMLBox_009,0,trans_14);

    TGeoShape *Cut_012 = new TGeoCompositeShape("Cut_012", Boolean);

    dx_UJ18 = 0;
    dy_UJ18 = 0;
    dz_UJ18 = -1829.5;
    auto trans_15 = new TGeoCombiTrans("trans_15");
    trans_15->SetTranslation(dx_UJ18, dy_UJ18, dz_UJ18);
    Boolean = new TGeoUnion(Cut_011,Cut_012,0,trans_15);

    TGeoShape *Add_003 = new TGeoCompositeShape("Add_003", Boolean);

    dx_UJ18 = 0;
    dy_UJ18 = 0;
    dz_UJ18 = -1829.5;
    auto trans_16 = new TGeoCombiTrans("trans_16");
    trans_16->SetTranslation(dx_UJ18, dy_UJ18, dz_UJ18);
    Boolean = new TGeoUnion(Cut_010,Add_003,0,trans_16);
    TGeoShape *Solid_UJ18_shape = new TGeoCompositeShape("Solid_UJ18_shape", Boolean);

  auto total = new TGeoCompositeShape("Stotal","(UJ18_shape:new_translation_for_UJ18+TI18_1_union+TI18_2_union+TI18_3_union)-vetoPit:VetoPit_transl");
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
 double extended_z = 1860; //extend the rock to cover the new added UJ18

 auto bigBox   = new TGeoBBox("BigBox", 2000.,1500. , dz+extended_z);
 auto TR_1       = new TGeoTranslation("TR_1",0.,0.,-dz+extended_z+geoParameters["TI18_o1"][2]-SND_Z - 50.); // move a bit more upstream to have free view from the back
 TR_1->RegisterYourself();
 
 auto cutOut   = new TGeoCompositeShape("cutOut", "BigBox:TR_1-Ftotal2-(TI18_1_Funion+TI18_2_Funion+TI18_3_Funion+Solid_UJ18_shape:new_translation_for_UJ18)");
 auto volT3      = new TGeoVolume("Vrock",cutOut,rock);
 volT3->SetTransparency(75);
 volT3->SetLineColor(kRed);
 tunnel->AddNode(volT3, 1);

 double z_dim_exitPlane = 1.;
auto exitPlane =  gGeoManager->MakeBox("exitScoringPlane",vacuum,1000.,1000. , z_dim_exitPlane);
exitPlane->SetLineColor(kGreen);
exitPlane->SetVisibility(kFALSE);
if (fMakeSensitive) {AddSensitiveVolume(exitPlane);}
tunnel->AddNode(exitPlane,1, new TGeoTranslation(-1500.0,0,((2*extended_z)+geoParameters["TI18_o1"][2]-SND_Z - 50 + z_dim_exitPlane)));

   // COLDBOX GEOM
   InitMedium("Borated30polyethylene");
   TGeoMedium *Bor30Poly = gGeoManager->GetMedium("Borated30polyethylene");
   InitMedium("PMMA");
   TGeoMedium *Acrylic = gGeoManager->GetMedium("PMMA");
   TVector3 displacement;

   Double_t fAcrylicWidth = conf_floats["Floor/Acrylic_width"];
   Double_t fBPolyWidth = conf_floats["Floor/BPoly_width"];
   Double_t fCBFrontWallXDim = conf_floats["Floor/CBFrontWall_xdim"];
   Double_t fCBFrontWallYDim = conf_floats["Floor/CBFrontWall_ydim"];
   Double_t fCBLatWallZDim = conf_floats["Floor/CBLatWall_zdim"];
   Double_t fCBTinyZDim = conf_floats["Floor/CBTiny_zdim"];
   Double_t fCBExtraZDim = conf_floats["Floor/CBExtra_zdim"];
   Double_t fCBExtraXDim = conf_floats["Floor/CBExtra_xdim"];
   Double_t fSlopedWallZProj = conf_floats["Floor/SlopedWall_zproj"];
   Double_t fCBRearWallXDim =
      fCBFrontWallXDim - fSlopedWallZProj * TMath::Tan(TMath::DegToRad() * 15.) - fCBExtraXDim + fAcrylicWidth;
   Double_t fFeBlockX = conf_floats["Floor/MFeBlockX"];
   Double_t fFeBlockY = conf_floats["Floor/MFeBlockY"];
   Double_t fFeBlockZ = conf_floats["Floor/MFeBlockZ"];

   // ************************ ACRYLIC
   // Shapes definition
   TGeoBBox *FeBlock_cb = new TGeoBBox("FeBlock_cb", fFeBlockX / 2, fFeBlockY / 2, fFeBlockZ / 2);
   TGeoBBox *CBFrontWall_a =
      new TGeoBBox("CBFrontWall_a", fCBFrontWallXDim / 2., fCBFrontWallYDim / 2., fAcrylicWidth / 2.);
   TGeoBBox *CBLateral_a =
      new TGeoBBox("CBLateral_a", fAcrylicWidth / 2., fCBFrontWallYDim / 2., (fCBLatWallZDim - 2 * fAcrylicWidth) / 2.);
   TGeoBBox *CBExtraFront_a =
      new TGeoBBox("CBExtraFront_a", fCBExtraXDim / 2., fCBFrontWallYDim / 2., fAcrylicWidth / 2.);
   TGeoBBox *CBExtraLat_a =
      new TGeoBBox("CBExtraLat_a", fAcrylicWidth / 2., fCBFrontWallYDim / 2., (fCBExtraZDim - 2 * fAcrylicWidth) / 2.);
   TGeoBBox *CBTiny1_a = new TGeoBBox("CBTiny1_a", fAcrylicWidth / 2., fCBFrontWallYDim / 2.,
                                      (fCBTinyZDim - fAcrylicWidth - fBPolyWidth) / 2.);
   TGeoBBox *CBTiny2_a =
      new TGeoBBox("CBTiny2_a", fAcrylicWidth / 2., fCBFrontWallYDim / 2., (fCBTinyZDim - fAcrylicWidth) / 2.);
   TGeoBBox *CBRearWall_a =
      new TGeoBBox("CBRearWall_a", fCBRearWallXDim / 2., fCBFrontWallYDim / 2., fAcrylicWidth / 2.);

   TGeoTranslation *CBWallpos = new TGeoTranslation("CBWallpos", (fCBRearWallXDim - fFeBlockX) / 2. - 28.5,
                                                    (fCBFrontWallYDim - fFeBlockY) / 2. - 118., 0);
   CBWallpos->RegisterYourself();

   TGeoCompositeShape *CBWallDownstream =
      new TGeoCompositeShape("CBWallDownstream", "CBRearWall_a-(FeBlock_cb:CBWallpos)");
   TGeoPara *CBWallSlope_a =
      new TGeoPara("CBWallSlope_a", fAcrylicWidth / 2., fCBFrontWallYDim / 2., fSlopedWallZProj / 2., 0, -15, 0);

   // Coverings
   Double_t LatCover1_averts[8][2];
   LatCover1_averts[0][0] = 0.;
   LatCover1_averts[0][1] = 0.;
   LatCover1_averts[1][0] = fAcrylicWidth;
   LatCover1_averts[1][1] = 0;
   LatCover1_averts[2][0] = fAcrylicWidth;
   LatCover1_averts[2][1] = -(176.71 - 170.72);
   LatCover1_averts[3][0] = 0.;
   LatCover1_averts[3][1] = -(176.71 - 170.72);

   LatCover1_averts[4][0] = 0;
   LatCover1_averts[4][1] = 0;
   LatCover1_averts[5][0] = fAcrylicWidth;
   LatCover1_averts[5][1] = 0;
   LatCover1_averts[6][0] = fAcrylicWidth;
   LatCover1_averts[6][1] = -(187.03 - 170.72);
   LatCover1_averts[7][0] = 0;
   LatCover1_averts[7][1] = -(187.03 - 170.72);
   TGeoArb8 *LatCov1_a = new TGeoArb8("LatCov1_a", 176. / 2., (Double_t *)LatCover1_averts);

   Double_t tanalpha = (183.26 - 170.72) / 144.;
   Double_t LatCover21_averts[8][2];
   LatCover21_averts[0][0] = 0.;
   LatCover21_averts[0][1] = 0.;
   LatCover21_averts[1][0] = fAcrylicWidth;
   LatCover21_averts[1][1] = 0;
   LatCover21_averts[2][0] = fAcrylicWidth;
   LatCover21_averts[2][1] = 0;
   LatCover21_averts[3][0] = 0.;
   LatCover21_averts[3][1] = 0;

   LatCover21_averts[4][0] = 0;
   LatCover21_averts[4][1] = 0;
   LatCover21_averts[5][0] = fAcrylicWidth;
   LatCover21_averts[5][1] = 0;
   LatCover21_averts[6][0] = fAcrylicWidth;
   LatCover21_averts[6][1] = -fCBTinyZDim * tanalpha;
   LatCover21_averts[7][0] = 0;
   LatCover21_averts[7][1] = -fCBTinyZDim * tanalpha;
   TGeoArb8 *LatCov21_a = new TGeoArb8("LatCov21_a", fCBTinyZDim / 2., (Double_t *)LatCover21_averts);

   Double_t LatCover22_averts[8][2];
   LatCover22_averts[0][0] = 0.;
   LatCover22_averts[0][1] = 0.;
   LatCover22_averts[1][0] = fAcrylicWidth;
   LatCover22_averts[1][1] = 0;
   LatCover22_averts[2][0] = fAcrylicWidth;
   LatCover22_averts[2][1] = -fCBTinyZDim * tanalpha;
   LatCover22_averts[3][0] = 0.;
   LatCover22_averts[3][1] = -fCBTinyZDim * tanalpha;

   LatCover22_averts[4][0] = -fSlopedWallZProj * TMath::Tan(TMath::DegToRad() * 15.);
   LatCover22_averts[4][1] = 0;
   LatCover22_averts[5][0] = -fSlopedWallZProj * TMath::Tan(TMath::DegToRad() * 15.) + fAcrylicWidth;
   LatCover22_averts[5][1] = 0;
   LatCover22_averts[6][0] = -fSlopedWallZProj * TMath::Tan(TMath::DegToRad() * 15.) + fAcrylicWidth;
   LatCover22_averts[6][1] = -(fCBTinyZDim + fSlopedWallZProj) * tanalpha;
   LatCover22_averts[7][0] = -fSlopedWallZProj * TMath::Tan(TMath::DegToRad() * 15.);
   LatCover22_averts[7][1] = -(fCBTinyZDim + fSlopedWallZProj) * tanalpha;
   TGeoArb8 *LatCov22_a = new TGeoArb8("LatCov22_a", fSlopedWallZProj / 2., (Double_t *)LatCover22_averts);

   Double_t LatCover23_averts[8][2];
   LatCover23_averts[0][0] = 0.;
   LatCover23_averts[0][1] = 0.;
   LatCover23_averts[1][0] = fAcrylicWidth;
   LatCover23_averts[1][1] = 0;
   LatCover23_averts[2][0] = fAcrylicWidth;
   LatCover23_averts[2][1] = -(fCBTinyZDim + fSlopedWallZProj) * tanalpha;
   LatCover23_averts[3][0] = 0.;
   LatCover23_averts[3][1] = -(fCBTinyZDim + fSlopedWallZProj) * tanalpha;

   LatCover23_averts[4][0] = 0;
   LatCover23_averts[4][1] = 0;
   LatCover23_averts[5][0] = fAcrylicWidth;
   LatCover23_averts[5][1] = 0;
   LatCover23_averts[6][0] = fAcrylicWidth;
   LatCover23_averts[6][1] = -(183.26 - 170.72);
   LatCover23_averts[7][0] = 0;
   LatCover23_averts[7][1] = -(183.26 - 170.72);
   TGeoArb8 *LatCov23_a = new TGeoArb8("LatCov23_a", (fCBTinyZDim - fBPolyWidth) / 2., (Double_t *)LatCover23_averts);

   Double_t tanbeta = (176.74 - 170.72) / 219.0;
   Double_t FrontCover1_averts[8][2];
   FrontCover1_averts[0][0] = (fCBFrontWallXDim-2*fAcrylicWidth)/2.;
   FrontCover1_averts[0][1] = 0.;
   FrontCover1_averts[1][0] = (fCBFrontWallXDim-2*fAcrylicWidth)/2.; 
   FrontCover1_averts[1][1] = -(fAcrylicWidth)*tanbeta;
   FrontCover1_averts[2][0] = -(fCBFrontWallXDim-2*fAcrylicWidth)/2.; 
   FrontCover1_averts[2][1] = -(fCBFrontWallXDim-fAcrylicWidth)*tanbeta;
   FrontCover1_averts[3][0] = -(fCBFrontWallXDim-2*fAcrylicWidth)/2.; 
   FrontCover1_averts[3][1] = 0;

   FrontCover1_averts[4][0] = (fCBFrontWallXDim-2*fAcrylicWidth)/2.; 
   FrontCover1_averts[4][1] = 0;
   FrontCover1_averts[5][0] = (fCBFrontWallXDim-2*fAcrylicWidth)/2.; 
   FrontCover1_averts[5][1] = -(fAcrylicWidth)*tanbeta;
   FrontCover1_averts[6][0] = -(fCBFrontWallXDim-2*fAcrylicWidth)/2.; 
   FrontCover1_averts[6][1] =  -(fCBFrontWallXDim-fAcrylicWidth)*tanbeta;
   FrontCover1_averts[7][0] = -(fCBFrontWallXDim-2*fAcrylicWidth)/2.; 
   FrontCover1_averts[7][1] = 0;
   TGeoArb8 *FrontCov1_a = new TGeoArb8("FrontCov1_a", fAcrylicWidth / 2., (Double_t *)FrontCover1_averts);

   Double_t tangamma = (187.03 - 183.26) / (fCBRearWallXDim - fAcrylicWidth + fCBExtraXDim);
   Double_t xdim_projected = (187.03 - 170.72) / tangamma;
   Double_t extra = xdim_projected - (fCBRearWallXDim - fAcrylicWidth + fCBExtraXDim);
   Double_t RearCover_11_averts[8][2];
   RearCover_11_averts[0][0] = (fCBRearWallXDim-2*fAcrylicWidth)/2.; 
   RearCover_11_averts[0][1] = 0.;
   RearCover_11_averts[1][0] = (fCBRearWallXDim-2*fAcrylicWidth)/2.; 
   RearCover_11_averts[1][1] =  -(183.26-170.72); // approx
   RearCover_11_averts[2][0] = -(fCBRearWallXDim-2*fAcrylicWidth)/2.; 
   RearCover_11_averts[2][1] = -(fCBRearWallXDim-fAcrylicWidth+extra)*tangamma;
   RearCover_11_averts[3][0] = -(fCBRearWallXDim-2*fAcrylicWidth)/2.; 
   RearCover_11_averts[3][1] = 0;

   RearCover_11_averts[4][0] = (fCBRearWallXDim-2*fAcrylicWidth)/2.; 
   RearCover_11_averts[4][1] = 0;
   RearCover_11_averts[5][0] = (fCBRearWallXDim-2*fAcrylicWidth)/2.; 
   RearCover_11_averts[5][1] = -(183.26-170.72); // approx
   RearCover_11_averts[6][0] = -(fCBRearWallXDim-2*fAcrylicWidth)/2.; 
   RearCover_11_averts[6][1] =  -(fCBRearWallXDim-fAcrylicWidth+extra)*tangamma;
   RearCover_11_averts[7][0] = -(fCBRearWallXDim-2*fAcrylicWidth)/2.; 
   RearCover_11_averts[7][1] = 0;
   TGeoArb8 *RearCov11_atot = new TGeoArb8("RearCov11_atot", fAcrylicWidth / 2., (Double_t *)RearCover_11_averts);
   TGeoTranslation *CBWallpos2 =
      new TGeoTranslation("CBWallpos2", (fCBRearWallXDim - fFeBlockX) / 2. - 28.5, 0, -fAcrylicWidth / 2.);
   CBWallpos2->RegisterYourself();
   TGeoCompositeShape *RearCov11_a = new TGeoCompositeShape("RearCov11_a", "RearCov11_atot-(FeBlock_cb:CBWallpos2)");

   Double_t RearCover_12_averts[8][2];
   RearCover_12_averts[0][0] = fAcrylicWidth/2.; 
   RearCover_12_averts[0][1] = 0.;
   RearCover_12_averts[1][0] = fAcrylicWidth/2.; 
   RearCover_12_averts[1][1] =  -(fCBRearWallXDim-fAcrylicWidth+extra)*tangamma;
   RearCover_12_averts[2][0] = -fAcrylicWidth/2.; 
   RearCover_12_averts[2][1] = -(fCBRearWallXDim+extra)*tangamma;
   RearCover_12_averts[3][0] = -fAcrylicWidth/2.; 
   RearCover_12_averts[3][1] = 0;

   RearCover_12_averts[4][0] = fAcrylicWidth/2.; 
   RearCover_12_averts[4][1] = 0;
   RearCover_12_averts[5][0] = fAcrylicWidth/2.; 
   RearCover_12_averts[5][1] = -(fCBRearWallXDim-fAcrylicWidth+extra)*tangamma;
   RearCover_12_averts[6][0] = -fAcrylicWidth/2.; 
   RearCover_12_averts[6][1] = -(fCBRearWallXDim+extra)*tangamma; 
   RearCover_12_averts[7][0] = -fAcrylicWidth/2.; 
   RearCover_12_averts[7][1] = 0;
   TGeoArb8 *RearCov12_a = new TGeoArb8("RearCov12_a", fCBExtraZDim / 2., (Double_t *)RearCover_12_averts);

   Double_t RearCover_13_averts[8][2];
   RearCover_13_averts[0][0] = (fCBExtraXDim-2*fAcrylicWidth)/2.; 
   RearCover_13_averts[0][1] = 0.;
   RearCover_13_averts[1][0] = (fCBExtraXDim-2*fAcrylicWidth)/2.; 
   RearCover_13_averts[1][1] = -(fCBRearWallXDim+extra)*tangamma;
   RearCover_13_averts[2][0] = -(fCBExtraXDim-2*fAcrylicWidth)/2.; 
   RearCover_13_averts[2][1] =  -(187.03-170.72);
   RearCover_13_averts[3][0] = -(fCBExtraXDim-2*fAcrylicWidth)/2.; 
   RearCover_13_averts[3][1] = 0;

   RearCover_13_averts[4][0] = (fCBExtraXDim-2*fAcrylicWidth)/2.; 
   RearCover_13_averts[4][1] = 0;
   RearCover_13_averts[5][0] = (fCBExtraXDim-2*fAcrylicWidth)/2.; 
   RearCover_13_averts[5][1] = -(fCBRearWallXDim+extra)*tangamma;
   RearCover_13_averts[6][0] = -(fCBExtraXDim-2*fAcrylicWidth)/2.; 
   RearCover_13_averts[6][1] =  -(187.03-170.72); 
   RearCover_13_averts[7][0] = -(fCBExtraXDim-2*fAcrylicWidth)/2.; 
   RearCover_13_averts[7][1] = 0;
   TGeoArb8 *RearCov13_a = new TGeoArb8("RearCov13_a", fAcrylicWidth / 2., (Double_t *)RearCover_13_averts);

   // Acrylic mother shape definition
   TGeoTranslation *FrontWallpos =
      new TGeoTranslation("FrontWallpos", -fCBRearWallXDim / 2. - fCBExtraXDim + fAcrylicWidth + fCBFrontWallXDim / 2.,
                          0, -(fSlopedWallZProj + 2 * (fCBTinyZDim - fAcrylicWidth) + fAcrylicWidth) + fBPolyWidth);
   FrontWallpos->RegisterYourself();
   TGeoTranslation *Tiny1pos =
      new TGeoTranslation("Tiny1pos", (fCBRearWallXDim - fAcrylicWidth) / 2., 0, -fCBTinyZDim / 2. + fBPolyWidth / 2.);
   Tiny1pos->RegisterYourself();
   TGeoTranslation *SlopeWallpos =
      new TGeoTranslation("SlopeWallpos",
                          (fCBRearWallXDim + fAcrylicWidth) / 2. + fAcrylicWidth +
                             fSlopedWallZProj / (2 * TMath::Tan(TMath::DegToRad() * 85.)),
                          0, -fCBTinyZDim - fSlopedWallZProj / 2. + fAcrylicWidth / 2. + fBPolyWidth);
   SlopeWallpos->RegisterYourself();
   TGeoTranslation *Tiny2pos = new TGeoTranslation(
      "Tiny2pos",
      3 * fAcrylicWidth + fCBRearWallXDim / 2. + fAcrylicWidth / 2. +
         fSlopedWallZProj / (TMath::Tan(TMath::DegToRad() * 85.)),
      0, -(fSlopedWallZProj + 2 * (fCBTinyZDim - fAcrylicWidth) + fAcrylicWidth) + fCBTinyZDim / 2. + fBPolyWidth);
   Tiny2pos->RegisterYourself();
   TGeoTranslation *CBExtraLatpos = new TGeoTranslation("CBExtraLatpos", -fCBRearWallXDim / 2. + fAcrylicWidth / 2., 0,
                                                        fAcrylicWidth / 2. + (fCBExtraZDim - 2 * fAcrylicWidth) / 2.);
   CBExtraLatpos->RegisterYourself();
   TGeoTranslation *CBExtraFrontpos = new TGeoTranslation(
      "CBExtraFrontpos", -fCBRearWallXDim / 2. + fAcrylicWidth - fCBExtraXDim / 2., 0, fCBExtraZDim - fAcrylicWidth);
   CBExtraFrontpos->RegisterYourself();
   TGeoTranslation *CBLateralpos =
      new TGeoTranslation("CBLateralpos", -fCBRearWallXDim / 2. - fCBExtraXDim + fAcrylicWidth + fAcrylicWidth / 2., 0,
                          fCBExtraZDim - fCBLatWallZDim / 2. - fAcrylicWidth / 2.);
   CBLateralpos->RegisterYourself();
   TGeoTranslation *CBLatCov1pos =
      new TGeoTranslation("CBLatCov1pos", -fCBRearWallXDim / 2. - fCBExtraXDim + fAcrylicWidth, -fCBFrontWallYDim / 2.,
                          fCBExtraZDim - fCBLatWallZDim / 2. - fAcrylicWidth / 2.);
   CBLatCov1pos->RegisterYourself();
   TGeoTranslation *CBLatCov21pos = new TGeoTranslation(
      "CBLatCov21pos",
      3 * fAcrylicWidth + fCBRearWallXDim / 2. + fSlopedWallZProj / (TMath::Tan(TMath::DegToRad() * 85.)),
      -fCBFrontWallYDim / 2.,
      -(fSlopedWallZProj + 2 * (fCBTinyZDim - fAcrylicWidth) + fAcrylicWidth) + fCBTinyZDim / 2. + fBPolyWidth -
         fAcrylicWidth / 2.);
   CBLatCov21pos->RegisterYourself();
   TGeoTranslation *CBLatCov22pos = new TGeoTranslation(
      "CBLatCov22pos",
      3 * fAcrylicWidth + fCBRearWallXDim / 2. + fSlopedWallZProj / (TMath::Tan(TMath::DegToRad() * 85.)),
      -fCBFrontWallYDim / 2.,
      -(fSlopedWallZProj / 2 + 2 * (fCBTinyZDim - fAcrylicWidth) + fAcrylicWidth) + fCBTinyZDim / 2. + fBPolyWidth -
         fAcrylicWidth / 2. + fCBTinyZDim / 2.);
   CBLatCov22pos->RegisterYourself();
   TGeoTranslation *CBLatCov23pos =
      new TGeoTranslation("CBLatCov23pos", (fCBRearWallXDim - fAcrylicWidth) / 2. - fAcrylicWidth / 2.,
                          -fCBFrontWallYDim / 2., -fCBTinyZDim / 2. + fBPolyWidth + 0.5);
   CBLatCov23pos->RegisterYourself();
   TGeoTranslation *CBFrontCov1pos = new TGeoTranslation(
      "CBFrontCov1pos", -fCBRearWallXDim / 2. - fCBExtraXDim + fAcrylicWidth + fCBFrontWallXDim / 2.,
      -fCBFrontWallYDim / 2., -(fSlopedWallZProj + 2 * (fCBTinyZDim - fAcrylicWidth) + fAcrylicWidth) + fBPolyWidth);
   CBFrontCov1pos->RegisterYourself();
   TGeoTranslation *CBRearCov11pos = new TGeoTranslation("CBRearCov11pos", 0, -fCBFrontWallYDim / 2., 0);
   CBRearCov11pos->RegisterYourself();
   TGeoTranslation *CBRearCov12pos =
      new TGeoTranslation("CBRearCov12pos", -fCBRearWallXDim / 2. + fAcrylicWidth / 2., -fCBFrontWallYDim / 2.,
                          fAcrylicWidth / 2. + (fCBExtraZDim - 2 * fAcrylicWidth) / 2.);
   CBRearCov12pos->RegisterYourself();
   TGeoTranslation *CBRearCov13pos =
      new TGeoTranslation("CBRearCov13pos", -fCBRearWallXDim / 2. + fAcrylicWidth - fCBExtraXDim / 2.,
                          -fCBFrontWallYDim / 2., fCBExtraZDim - fAcrylicWidth);
   CBRearCov13pos->RegisterYourself();

   // Acrylic mother volume definition
   TGeoCompositeShape *COLDBOXA = new TGeoCompositeShape(
      "COLDBOXA",
      "CBWallDownstream+(CBFrontWall_a:FrontWallpos)+(CBTiny1_a:Tiny1pos)+(CBWallSlope_a:SlopeWallpos)+(CBTiny2_a:"
      "Tiny2pos)+(CBExtraLat_a:CBExtraLatpos)+(CBExtraFront_a:CBExtraFrontpos)+(CBLateral_a:CBLateralpos)+(LatCov1_a:"
      "CBLatCov1pos)+(LatCov21_a:CBLatCov21pos)+(LatCov22_a:CBLatCov22pos)+(LatCov23_a:CBLatCov23pos)+(FrontCov1_a:"
      "CBFrontCov1pos)+(RearCov11_a:CBRearCov11pos)+(RearCov12_a:CBRearCov12pos)+(RearCov13_a:CBRearCov13pos)");
   TGeoVolume *volCOLDBOXA = new TGeoVolume("volCOLDBOXA", COLDBOXA, Acrylic);

   // ************************ BORATED POLYETHYLENE
   Double_t fCBFrontWallXDim_b = fCBFrontWallXDim - 2 * fAcrylicWidth - fBPolyWidth; // cm
   Double_t fCBFrontWallYDim_b = fCBFrontWallYDim - fBPolyWidth;
   Double_t fCBLatWallZDim_b = fCBLatWallZDim - 2 * fAcrylicWidth; // cm
   Double_t fCBExtraXDim_b = fCBExtraXDim - 2 * fAcrylicWidth;     // cm
   Double_t fCBRearWallXDim_b = fCBRearWallXDim - fAcrylicWidth;
   // Shapes definition
   TGeoBBox *CBFrontWall_b = new TGeoBBox(
      "CBFrontWall_b", fCBFrontWallXDim_b / 2. + (fAcrylicWidth - fBPolyWidth) / 10., fCBFrontWallYDim_b / 2.,
      fBPolyWidth / 2.); // (fAcrylicWidth-fBPolyWidth)/10. is due to approximations, I guess
   TGeoBBox *CBLateral_b = new TGeoBBox("CBLateral_b", fBPolyWidth / 2., fCBFrontWallYDim_b / 2.,
                                        (fCBLatWallZDim - 2 * fBPolyWidth) / 2. - fAcrylicWidth);
   TGeoBBox *CBExtraFront_b =
      new TGeoBBox("CBExtraFront_b", fCBExtraXDim_b / 2., fCBFrontWallYDim_b / 2., fBPolyWidth / 2.);
   TGeoBBox *CBExtraLat_b = new TGeoBBox("CBExtraLat_b", fBPolyWidth / 2., fCBFrontWallYDim_b / 2.,
                                         (fCBExtraZDim - fAcrylicWidth - fBPolyWidth) / 2.);
   TGeoBBox *CBTiny1_b = new TGeoBBox("CBTiny1_b", fBPolyWidth / 2., fCBFrontWallYDim_b / 2.,
                                      (fCBTinyZDim - fAcrylicWidth - fBPolyWidth) / 2.);
   TGeoBBox *CBTiny2_b =
      new TGeoBBox("CBTiny2_b", fBPolyWidth / 2., fCBFrontWallYDim_b / 2., (fCBTinyZDim - fAcrylicWidth) / 2.);
   TGeoBBox *CBRearWall_b =
      new TGeoBBox("CBRearWall_b", fCBRearWallXDim_b / 2., fCBFrontWallYDim_b / 2., fBPolyWidth / 2.);
   TGeoPara *CBWallSlope_b =
      new TGeoPara("CBWallSlope_b", fBPolyWidth / 2., fCBFrontWallYDim_b / 2., fSlopedWallZProj / 2., 0, -15, 0);

   // Coverings
   Double_t tanomega = (187.03 - 176.71) / 176.;
   Double_t LatCover1_bverts[8][2];
   LatCover1_bverts[0][0] = 0.;
   LatCover1_bverts[0][1] = 0.;
   LatCover1_bverts[1][0] = fBPolyWidth;
   LatCover1_bverts[1][1] = 0;
   LatCover1_bverts[2][0] = fBPolyWidth;
   LatCover1_bverts[2][1] = -(176.71 - 170.72) - fAcrylicWidth * tanomega;
   LatCover1_bverts[3][0] = 0.;
   LatCover1_bverts[3][1] = -(176.71 - 170.72) - fAcrylicWidth * tanomega;

   LatCover1_bverts[4][0] = 0;
   LatCover1_bverts[4][1] = 0;
   LatCover1_bverts[5][0] = fBPolyWidth;
   LatCover1_bverts[5][1] = 0;
   LatCover1_bverts[6][0] = fBPolyWidth;
   LatCover1_bverts[6][1] = -(187.03 - 170.72) + fAcrylicWidth * tanomega;
   LatCover1_bverts[7][0] = 0;
   LatCover1_bverts[7][1] = -(187.03 - 170.72) + fAcrylicWidth * tanomega;
   TGeoArb8 *LatCov1_b = new TGeoArb8("LatCov1_b", 176. / 2. - fAcrylicWidth, (Double_t *)LatCover1_bverts);

   Double_t LatCover21_bverts[8][2];
   LatCover21_bverts[0][0] = 0.;
   LatCover21_bverts[0][1] = 0.;
   LatCover21_bverts[1][0] = fBPolyWidth;
   LatCover21_bverts[1][1] = 0;
   LatCover21_bverts[2][0] = fBPolyWidth;
   LatCover21_bverts[2][1] = 0.; //-fAcrylicWidth*tanalpha;
   LatCover21_bverts[3][0] = 0.;
   LatCover21_bverts[3][1] = 0.; //-fAcrylicWidth*tanalpha;

   LatCover21_bverts[4][0] = 0;
   LatCover21_bverts[4][1] = 0;
   LatCover21_bverts[5][0] = fBPolyWidth;
   LatCover21_bverts[5][1] = 0;
   LatCover21_bverts[6][0] = fBPolyWidth;
   LatCover21_bverts[6][1] = -fCBTinyZDim * tanalpha;
   LatCover21_bverts[7][0] = 0;
   LatCover21_bverts[7][1] = -fCBTinyZDim * tanalpha;
   TGeoArb8 *LatCov21_b = new TGeoArb8("LatCov21_b", (fCBTinyZDim - fAcrylicWidth) / 2., (Double_t *)LatCover21_bverts);

   Double_t LatCover22_bverts[8][2];
   LatCover22_bverts[0][0] = 0.;
   LatCover22_bverts[0][1] = 0.;
   LatCover22_bverts[1][0] = fBPolyWidth;
   LatCover22_bverts[1][1] = 0;
   LatCover22_bverts[2][0] = fBPolyWidth;
   LatCover22_bverts[2][1] = -fCBTinyZDim * tanalpha;
   LatCover22_bverts[3][0] = 0.;
   LatCover22_bverts[3][1] = -fCBTinyZDim * tanalpha;

   LatCover22_bverts[4][0] = -fSlopedWallZProj * TMath::Tan(TMath::DegToRad() * 15.);
   LatCover22_bverts[4][1] = 0;
   LatCover22_bverts[5][0] = -fSlopedWallZProj * TMath::Tan(TMath::DegToRad() * 15.) + fBPolyWidth;
   LatCover22_bverts[5][1] = 0;
   LatCover22_bverts[6][0] = -fSlopedWallZProj * TMath::Tan(TMath::DegToRad() * 15.) + fBPolyWidth;
   LatCover22_bverts[6][1] = -(fCBTinyZDim + fSlopedWallZProj) * tanalpha;
   LatCover22_bverts[7][0] = -fSlopedWallZProj * TMath::Tan(TMath::DegToRad() * 15.);
   LatCover22_bverts[7][1] = -(fCBTinyZDim + fSlopedWallZProj) * tanalpha;
   TGeoArb8 *LatCov22_b = new TGeoArb8("LatCov22_b", fSlopedWallZProj / 2., (Double_t *)LatCover22_bverts);

   Double_t LatCover23_bverts[8][2];
   LatCover23_bverts[0][0] = 0.;
   LatCover23_bverts[0][1] = 0.;
   LatCover23_bverts[1][0] = fBPolyWidth;
   LatCover23_bverts[1][1] = 0;
   LatCover23_bverts[2][0] = fBPolyWidth;
   LatCover23_bverts[2][1] = -(fCBTinyZDim + fSlopedWallZProj) * tanalpha;
   LatCover23_bverts[3][0] = 0.;
   LatCover23_bverts[3][1] = -(fCBTinyZDim + fSlopedWallZProj) * tanalpha;

   LatCover23_bverts[4][0] = 0;
   LatCover23_bverts[4][1] = 0;
   LatCover23_bverts[5][0] = fBPolyWidth;
   LatCover23_bverts[5][1] = 0;
   LatCover23_bverts[6][0] = fBPolyWidth;
   LatCover23_bverts[6][1] = -(183.26 - 170.72) + fAcrylicWidth * tanalpha;
   LatCover23_bverts[7][0] = 0;
   LatCover23_bverts[7][1] = -(183.26 - 170.72) + fAcrylicWidth * tanalpha;
   TGeoArb8 *LatCov23_b =
      new TGeoArb8("LatCov23_b", (fCBTinyZDim - fBPolyWidth - fAcrylicWidth) / 2., (Double_t *)LatCover23_bverts);

   Double_t FrontCover1_bverts[8][2];
   FrontCover1_bverts[0][0] = (fCBFrontWallXDim_b-2*fBPolyWidth)/2.; 
   FrontCover1_bverts[0][1] = 0.;
   FrontCover1_bverts[1][0] = (fCBFrontWallXDim_b-2*fBPolyWidth)/2.; 
   FrontCover1_bverts[1][1] = -(fBPolyWidth)*tanbeta;
   FrontCover1_bverts[2][0] = -(fCBFrontWallXDim_b-2*fBPolyWidth)/2.; 
   FrontCover1_bverts[2][1] =  -(176.71-170.72)-fAcrylicWidth*tanomega;
   FrontCover1_bverts[3][0] = -(fCBFrontWallXDim_b-2*fBPolyWidth)/2.; 
   FrontCover1_bverts[3][1] = 0;

   FrontCover1_bverts[4][0] = (fCBFrontWallXDim_b-2*fBPolyWidth)/2.; 
   FrontCover1_bverts[4][1] = 0;
   FrontCover1_bverts[5][0] = (fCBFrontWallXDim_b-2*fBPolyWidth)/2.; 
   FrontCover1_bverts[5][1] = -(fBPolyWidth)*tanbeta;
   FrontCover1_bverts[6][0] = -(fCBFrontWallXDim_b-2*fBPolyWidth)/2.; 
   FrontCover1_bverts[6][1] = -(176.71-170.72)-fAcrylicWidth*tanomega;
   FrontCover1_bverts[7][0] = -(fCBFrontWallXDim_b-2*fBPolyWidth)/2.; 
   FrontCover1_bverts[7][1] = 0;
   TGeoArb8 *FrontCov1_b = new TGeoArb8("FrontCov1_b", fBPolyWidth / 2., (Double_t *)FrontCover1_bverts);

   Double_t RearCover_11_bverts[8][2];
   RearCover_11_bverts[0][0] = (fCBRearWallXDim_b-2*fBPolyWidth)/2.+fBPolyWidth/2.; 
   RearCover_11_bverts[0][1] = 0.;
   RearCover_11_bverts[1][0] = (fCBRearWallXDim_b-2*fBPolyWidth)/2.+fBPolyWidth/2.; 
   RearCover_11_bverts[1][1] =  -(183.26-170.72)+fAcrylicWidth*tanalpha; // approx
   RearCover_11_bverts[2][0] = -(fCBRearWallXDim_b-2*fBPolyWidth)/2.-fBPolyWidth/2.; 
   RearCover_11_bverts[2][1] = -(fCBRearWallXDim_b-fBPolyWidth+extra)*tangamma;
   RearCover_11_bverts[3][0] = -(fCBRearWallXDim_b-2*fBPolyWidth)/2.-fBPolyWidth/2.; 
   RearCover_11_bverts[3][1] = 0;

   RearCover_11_bverts[4][0] = (fCBRearWallXDim_b-2*fBPolyWidth)/2.+fBPolyWidth/2.; 
   RearCover_11_bverts[4][1] = 0;
   RearCover_11_bverts[5][0] = (fCBRearWallXDim_b-2*fBPolyWidth)/2.+fBPolyWidth/2.; 
   RearCover_11_bverts[5][1] = -(183.26-170.72)+fAcrylicWidth*tanalpha; // approx
   RearCover_11_bverts[6][0] = -(fCBRearWallXDim_b-2*fBPolyWidth)/2.-fBPolyWidth/2.; 
   RearCover_11_bverts[6][1] =  -(fCBRearWallXDim_b-fBPolyWidth+extra)*tangamma;
   RearCover_11_bverts[7][0] = -(fCBRearWallXDim_b-2*fBPolyWidth)/2.-fBPolyWidth/2.; 
   RearCover_11_bverts[7][1] = 0;
   TGeoArb8 *RearCov11_b = new TGeoArb8("RearCov11_b", fBPolyWidth / 2., (Double_t *)RearCover_11_bverts);

   Double_t RearCover_12_bverts[8][2];
	 RearCover_12_bverts[0][0] = fBPolyWidth/2.; 
	 RearCover_12_bverts[0][1] = 0.;
	 RearCover_12_bverts[1][0] = fBPolyWidth/2.; 
	 RearCover_12_bverts[1][1] =  -(fCBRearWallXDim_b-fBPolyWidth+extra)*tangamma;
	 RearCover_12_bverts[2][0] = -fBPolyWidth/2.; 
	 RearCover_12_bverts[2][1] = -(fCBRearWallXDim_b+extra)*tangamma;
	 RearCover_12_bverts[3][0] = -fBPolyWidth/2.; 
	 RearCover_12_bverts[3][1] = 0;
	 
	 RearCover_12_bverts[4][0] = fBPolyWidth/2.; 
	 RearCover_12_bverts[4][1] = 0;
	 RearCover_12_bverts[5][0] = fBPolyWidth/2.; 
	 RearCover_12_bverts[5][1] = -(fCBRearWallXDim_b-fAcrylicWidth+extra)*tangamma;
	 RearCover_12_bverts[6][0] = -fBPolyWidth/2.; 
	 RearCover_12_bverts[6][1] = -(fCBRearWallXDim_b+extra)*tangamma; 
	 RearCover_12_bverts[7][0] = -fBPolyWidth/2.; 
	 RearCover_12_bverts[7][1] = 0;
   TGeoArb8 *RearCov12_b =
      new TGeoArb8("RearCov12_b", (fCBExtraZDim - fAcrylicWidth + fBPolyWidth) / 2., (Double_t *)RearCover_12_bverts);

   Double_t RearCover_13_bverts[8][2];
	 RearCover_13_bverts[0][0] = (fCBExtraXDim_b-2*fBPolyWidth)/2.; 
	 RearCover_13_bverts[0][1] = 0.;
	 RearCover_13_bverts[1][0] = (fCBExtraXDim_b-2*fBPolyWidth)/2.; 
	 RearCover_13_bverts[1][1] = -(fCBRearWallXDim_b+extra)*tangamma;
	 RearCover_13_bverts[2][0] = -(fCBExtraXDim_b-2*fBPolyWidth)/2.; 
	 RearCover_13_bverts[2][1] = -(187.03-170.72)+fAcrylicWidth*tanomega;
	 RearCover_13_bverts[3][0] = -(fCBExtraXDim_b-2*fBPolyWidth)/2.; 
	 RearCover_13_bverts[3][1] = 0;

	 RearCover_13_bverts[4][0] = (fCBExtraXDim_b-2*fBPolyWidth)/2.; 
	 RearCover_13_bverts[4][1] = 0;
	 RearCover_13_bverts[5][0] = (fCBExtraXDim_b-2*fBPolyWidth)/2.; 
	 RearCover_13_bverts[5][1] = -(fCBRearWallXDim_b+extra)*tangamma;
	 RearCover_13_bverts[6][0] = -(fCBExtraXDim_b-2*fBPolyWidth)/2.; 
	 RearCover_13_bverts[6][1] = -(187.03-170.72)+fAcrylicWidth*tanomega; 
	 RearCover_13_bverts[7][0] = -(fCBExtraXDim_b-2*fBPolyWidth)/2.; 
	 RearCover_13_bverts[7][1] = 0;
   TGeoArb8 *RearCov13_b = new TGeoArb8("RearCov13_b", fBPolyWidth / 2., (Double_t *)RearCover_13_bverts);

   // Borated Polyethylene mother shape definition
   TGeoTranslation *FrontWallpos_b = new TGeoTranslation(
      "FrontWallpos_b", -fCBRearWallXDim_b / 2. - fCBExtraXDim_b + fBPolyWidth + fCBFrontWallXDim_b / 2. + 0.1, 0,
      -fSlopedWallZProj - (fCBTinyZDim - fAcrylicWidth + fBPolyWidth)); // +0.1 is due to approximations, I guess
   FrontWallpos_b->RegisterYourself();
   TGeoTranslation *Tiny1pos_b =
      new TGeoTranslation("Tiny1pos_b", fCBRearWallXDim_b / 2. + fBPolyWidth / 2., 0, -fBPolyWidth / 2.);
   Tiny1pos_b->RegisterYourself();
   TGeoTranslation *SlopeWallpos_b = new TGeoTranslation(
      "SlopeWallpos_b",
      fSlopedWallZProj / (2 * TMath::Tan(TMath::DegToRad() * 85.)) + fCBRearWallXDim_b / 2. + 3 * fBPolyWidth, 0,
      -fBPolyWidth / 2. - fSlopedWallZProj / 2. - (fCBTinyZDim - fAcrylicWidth - fBPolyWidth) / 2.);
   SlopeWallpos_b->RegisterYourself();
   TGeoTranslation *Tiny2pos_b = new TGeoTranslation("Tiny2pos_b",
                                                     5 * fBPolyWidth + fCBRearWallXDim / 2. +
                                                        fSlopedWallZProj / (TMath::Tan(TMath::DegToRad() * 85.)) -
                                                        (fAcrylicWidth - fBPolyWidth) / 2.,
                                                     0, -fSlopedWallZProj - (fCBTinyZDim - fAcrylicWidth));
   Tiny2pos_b->RegisterYourself();
   TGeoTranslation *CBExtraLatpos_b = new TGeoTranslation("CBExtraLatpos_b", -fCBRearWallXDim_b / 2. + fBPolyWidth / 2.,
                                                          0, (fCBExtraZDim - fAcrylicWidth) / 2.);
   CBExtraLatpos_b->RegisterYourself();
   TGeoTranslation *CBExtraFrontpos_b =
      new TGeoTranslation("CBExtraFrontpos_b", -fCBRearWallXDim_b / 2. + fBPolyWidth - fCBExtraXDim_b / 2., 0,
                          fCBExtraZDim - fAcrylicWidth);
   CBExtraFrontpos_b->RegisterYourself();
   TGeoTranslation *CBLateralpos_b =
      new TGeoTranslation("CBLateralpos_b", -fCBRearWallXDim_b / 2. - fCBExtraXDim_b + fBPolyWidth + fBPolyWidth / 2.,
                          0, fCBExtraZDim - fCBLatWallZDim_b / 2. + fBPolyWidth / 2. - fAcrylicWidth);
   CBLateralpos_b->RegisterYourself();
   TGeoTranslation *CBLatCov1pos_b = new TGeoTranslation(
      "CBLatCov1pos_b", -fCBRearWallXDim / 2. - fCBExtraXDim + 2 * fAcrylicWidth + fBPolyWidth + fAcrylicWidth / 2.,
      -fCBFrontWallYDim_b / 2., fCBExtraZDim - fCBLatWallZDim / 2. + fAcrylicWidth / 2 - 0.5);
   CBLatCov1pos_b->RegisterYourself();
   TGeoTranslation *CBLatCov21pos_b =
      new TGeoTranslation("CBLatCov21pos_b",
                          3 * fAcrylicWidth + fCBRearWallXDim / 2. +
                             fSlopedWallZProj / (TMath::Tan(TMath::DegToRad() * 85.)) + fBPolyWidth / 2. + 0.4,
                          -fCBFrontWallYDim_b / 2.,
                          -(fSlopedWallZProj + 2 * (fCBTinyZDim - fAcrylicWidth) + fAcrylicWidth) + fCBTinyZDim / 2. +
                             fBPolyWidth + fAcrylicWidth - 0.5);
   CBLatCov21pos_b->RegisterYourself();
   TGeoTranslation *CBLatCov22pos_b = new TGeoTranslation(
      "CBLatCov22pos_b",
      3 * fAcrylicWidth + fCBRearWallXDim / 2. + fSlopedWallZProj / (TMath::Tan(TMath::DegToRad() * 85.)) +
         fBPolyWidth / 2. + 0.4,
      -fCBFrontWallYDim_b / 2.,
      -(fSlopedWallZProj / 2 + 2 * (fCBTinyZDim - fAcrylicWidth) + fAcrylicWidth) + fCBTinyZDim / 2. + fBPolyWidth -
         fAcrylicWidth / 2. + fCBTinyZDim / 2. + fAcrylicWidth - 0.5);
   CBLatCov22pos_b->RegisterYourself();
   TGeoTranslation *CBLatCov23pos_b = new TGeoTranslation(
      "CBLatCov23pos_b", (fCBRearWallXDim - fAcrylicWidth) / 2. - fAcrylicWidth / 2. + fBPolyWidth / 2. + 0.5,
      -fCBFrontWallYDim_b / 2., -fCBTinyZDim / 2. + fBPolyWidth + fBPolyWidth / 2. + 0.5);
   CBLatCov23pos_b->RegisterYourself();
   TGeoTranslation *CBFrontCov1pos_b = new TGeoTranslation(
      "CBFrontCov1pos_b", -fCBRearWallXDim_b / 2. - fCBExtraXDim_b + fBPolyWidth + fCBFrontWallXDim_b / 2.,
      -fCBFrontWallYDim_b / 2., -fSlopedWallZProj - (fCBTinyZDim - fAcrylicWidth + fBPolyWidth));
   CBFrontCov1pos_b->RegisterYourself();
   TGeoTranslation *CBRearCov11pos_b =
      new TGeoTranslation("CBRearCov11pos_b", +fBPolyWidth / 2., -fCBFrontWallYDim_b / 2., 0);
   CBRearCov11pos_b->RegisterYourself();
   TGeoTranslation *CBRearCov12pos_b =
      new TGeoTranslation("CBRearCov12pos_b", -fCBRearWallXDim_b / 2. + fAcrylicWidth / 2. - 0.5,
                          -fCBFrontWallYDim_b / 2., fAcrylicWidth / 2. + (fCBExtraZDim - 2 * fAcrylicWidth) / 2.);
   CBRearCov12pos_b->RegisterYourself();
   TGeoTranslation *CBRearCov13pos_b =
      new TGeoTranslation("CBRearCov13pos_b", -fCBRearWallXDim_b / 2. + fAcrylicWidth - fCBExtraXDim / 2 + fBPolyWidth,
                          -fCBFrontWallYDim_b / 2., fCBExtraZDim - fAcrylicWidth);
   CBRearCov13pos_b->RegisterYourself();

   // Borated Polyethylene mother volume definition
   TGeoCompositeShape *COLDBOXB = new TGeoCompositeShape(
      "COLDBOXB", "CBRearWall_b+(CBTiny1_b:Tiny1pos_b)+(CBExtraLat_b:CBExtraLatpos_b)+(CBWallSlope_b:SlopeWallpos_b)+("
                  "CBTiny2_b:Tiny2pos_b)+(CBExtraFront_b:CBExtraFrontpos_b)+(CBLateral_b:CBLateralpos_b)+(CBFrontWall_"
                  "b:FrontWallpos_b)+(LatCov1_b:CBLatCov1pos_b)+(LatCov21_b:CBLatCov21pos_b)+(LatCov22_b:CBLatCov22pos_"
                  "b)+(LatCov23_b:CBLatCov23pos_b)+(FrontCov1_b:CBFrontCov1pos_b)+(RearCov11_b:CBRearCov11pos_b)+("
                  "RearCov12_b:CBRearCov12pos_b)+(RearCov13_b:CBRearCov13pos_b)");
   TGeoVolume *volCOLDBOXB = new TGeoVolume("volCOLDBOXB", COLDBOXB, Bor30Poly);

   // Acrylic Roof shape definition
   Double_t Roof4_averts[8][2];
   Roof4_averts[0][0] = 0.;
   Roof4_averts[0][1] = 0.;
   Roof4_averts[1][0] = 0.;
   Roof4_averts[1][1] = fAcrylicWidth;
   Roof4_averts[2][0] = fSlopedWallZProj * (TMath::Tan(TMath::DegToRad() * 15.));
   Roof4_averts[2][1] = fAcrylicWidth;
   Roof4_averts[3][0] = fSlopedWallZProj * (TMath::Tan(TMath::DegToRad() * 15.));
   Roof4_averts[3][1] = 0;
   Roof4_averts[4][0] = 0;
   Roof4_averts[4][1] = 0;
   Roof4_averts[5][0] = 0;
   Roof4_averts[5][1] = fAcrylicWidth;
   Roof4_averts[6][0] = 0;
   Roof4_averts[6][1] = fAcrylicWidth;
   Roof4_averts[7][0] = 0;
   Roof4_averts[7][1] = 0;

   TGeoBBox *CBRoof1_a = new TGeoBBox("CBRoof1_a", fCBExtraXDim / 2., fAcrylicWidth / 2., fCBLatWallZDim / 2.);
   TGeoBBox *CBRoof2_a = new TGeoBBox("CBRoof2_a", (fCBRearWallXDim - fAcrylicWidth) / 2., fAcrylicWidth / 2.,
                                      (fCBLatWallZDim - fCBExtraZDim + fAcrylicWidth) / 2.);
   TGeoBBox *CBRoof3_a = new TGeoBBox("CBRoof3_a", (fSlopedWallZProj * (TMath::Tan(TMath::DegToRad() * 15.))) / 2.,
                                      fAcrylicWidth / 2., fCBTinyZDim / 2.);
   TGeoArb8 *CBRoof4_a = new TGeoArb8("CBRoof4_a", fSlopedWallZProj / 2., (Double_t *)Roof4_averts);

   TGeoTranslation *Roof1_apos =
      new TGeoTranslation("Roof1_apos", -(fCBRearWallXDim - fAcrylicWidth) / 2. - fCBExtraXDim / 2., 0,
                          fCBExtraZDim / 2. - fAcrylicWidth / 2.);
   Roof1_apos->RegisterYourself();
   TGeoTranslation *Roof3_apos = new TGeoTranslation(
      "Roof3_apos",
      (fCBRearWallXDim - fAcrylicWidth) / 2. + (fSlopedWallZProj * (TMath::Tan(TMath::DegToRad() * 15.))) / 2., 0,
      -(fCBLatWallZDim - fCBExtraZDim + fAcrylicWidth) / 2. + fCBTinyZDim / 2.);
   Roof3_apos->RegisterYourself();
   TGeoTranslation *Roof4_apos =
      new TGeoTranslation("Roof4_apos", (fCBRearWallXDim - fAcrylicWidth) / 2., -fAcrylicWidth / 2.,
                          -(fCBLatWallZDim - fCBExtraZDim + fAcrylicWidth) / 2. + fCBTinyZDim + fSlopedWallZProj / 2.);
   Roof4_apos->RegisterYourself();

   // Acrylic roof volume definition
   TGeoCompositeShape *CBRoof_a = new TGeoCompositeShape(
      "CBRoof_a", "CBRoof2_a+(CBRoof1_a:Roof1_apos)+(CBRoof3_a:Roof3_apos)+(CBRoof4_a:Roof4_apos)");
   TGeoVolume *volCBRoof_a = new TGeoVolume("volCBRoof_a", CBRoof_a, Acrylic);

   // Borated Polythylene Roof shape definition
   Double_t Roof4_bverts[8][2];
   Roof4_bverts[0][0] = 0.;
   Roof4_bverts[0][1] = 0.;
   Roof4_bverts[1][0] = 0.;
   Roof4_bverts[1][1] = fBPolyWidth;
   Roof4_bverts[2][0] = fSlopedWallZProj * (TMath::Tan(TMath::DegToRad() * 15.));
   Roof4_bverts[2][1] = fBPolyWidth;
   Roof4_bverts[3][0] = fSlopedWallZProj * (TMath::Tan(TMath::DegToRad() * 15.));
   Roof4_bverts[3][1] = 0;
   Roof4_bverts[4][0] = 0;
   Roof4_bverts[4][1] = 0;
   Roof4_bverts[5][0] = 0;
   Roof4_bverts[5][1] = fBPolyWidth;
   Roof4_bverts[6][0] = 0;
   Roof4_bverts[6][1] = fBPolyWidth;
   Roof4_bverts[7][0] = 0;
   Roof4_bverts[7][1] = 0;

   TGeoBBox *CBRoof1_b = new TGeoBBox("CBRoof1_b", fCBExtraXDim_b / 2., fBPolyWidth / 2., fCBLatWallZDim_b / 2.);
   TGeoBBox *CBRoof2_b = new TGeoBBox("CBRoof2_b", (fCBRearWallXDim_b - fBPolyWidth) / 2. + fBPolyWidth / 2.,
                                      fBPolyWidth / 2., (fCBLatWallZDim_b - fCBExtraZDim + fAcrylicWidth) / 2.);
   TGeoBBox *CBRoof3_b = new TGeoBBox("CBRoof3_b", (fSlopedWallZProj * (TMath::Tan(TMath::DegToRad() * 15.))) / 2.,
                                      fBPolyWidth / 2., (fCBTinyZDim - fAcrylicWidth) / 2.);
   TGeoArb8 *CBRoof4_b = new TGeoArb8("CBRoof4_b", fSlopedWallZProj / 2., (Double_t *)Roof4_bverts);

   TGeoTranslation *Roof1_bpos =
      new TGeoTranslation("Roof1_bpos", -(fCBRearWallXDim - fAcrylicWidth) / 2. - fCBExtraXDim_b / 2., 0,
                          fCBExtraZDim / 2. - fAcrylicWidth / 2.);
   Roof1_bpos->RegisterYourself();
   TGeoTranslation *Roof3_bpos = new TGeoTranslation(
      "Roof3_bpos",
      (fCBRearWallXDim - fAcrylicWidth) / 2. + (fSlopedWallZProj * (TMath::Tan(TMath::DegToRad() * 15.))) / 2., 0,
      -(fCBLatWallZDim_b - fCBExtraZDim + fAcrylicWidth) / 2. + (fCBTinyZDim - fAcrylicWidth) / 2.);
   Roof3_bpos->RegisterYourself();
   TGeoTranslation *Roof4_bpos = new TGeoTranslation(
      "Roof4_bpos", (fCBRearWallXDim - fAcrylicWidth) / 2., -fBPolyWidth / 2.,
      -(fCBLatWallZDim_b - fCBExtraZDim + fAcrylicWidth) / 2. + fCBTinyZDim - fAcrylicWidth + fSlopedWallZProj / 2.);
   Roof4_bpos->RegisterYourself();

   // Borated Polyethylene volume definition
   TGeoCompositeShape *CBRoof_b = new TGeoCompositeShape(
      "CBRoof_b", "CBRoof2_b+(CBRoof1_b:Roof1_bpos)+(CBRoof3_b:Roof3_bpos)+(CBRoof4_b:Roof4_bpos)");
   TGeoVolume *volCBRoof_b = new TGeoVolume("volCBRoof_b", CBRoof_b, Bor30Poly);

   // Volumes positioning
   TGeoVolumeAssembly *volColdBox = new TGeoVolumeAssembly("volColdBox");
   volCOLDBOXA->SetLineColor(kGray - 1);
   volCOLDBOXA->SetTransparency(60);
   volCOLDBOXB->SetLineColor(kGray - 1);
   volCOLDBOXB->SetTransparency(60);
   volCBRoof_a->SetLineColor(kGray - 1);
   volCBRoof_a->SetTransparency(60);
   volCBRoof_b->SetLineColor(kGray - 1);
   volCBRoof_b->SetTransparency(60);

   volColdBox->AddNode(volCOLDBOXA, 0, 0);
   volColdBox->AddNode(volCOLDBOXB, 0,
                       new TGeoTranslation(-fBPolyWidth - fAcrylicWidth / 2., -fBPolyWidth / 2.,
                                           -fAcrylicWidth / 2. - fBPolyWidth / 2.));
   volColdBox->AddNode(volCBRoof_a, 0,
                       new TGeoTranslation(fAcrylicWidth / 2., fCBFrontWallYDim / 2. + fAcrylicWidth / 2.,
                                           -(fCBLatWallZDim - fCBExtraZDim + fAcrylicWidth) / 2. + fAcrylicWidth / 2.));
   volColdBox->AddNode(volCBRoof_b, 0,
                       new TGeoTranslation(-fAcrylicWidth / 2., fCBFrontWallYDim / 2. - fBPolyWidth / 2.,
                                           -(fCBLatWallZDim - fCBExtraZDim + fAcrylicWidth) / 2. + fAcrylicWidth / 2.));

   displacement =
      TVector3(-37.79 - 1.40082, 44.66,
               368.11); // taken from MuFilter.cxx "edge_Iron[1]-TVector3(FeX, FeY, FeZ)" EDIT: 1.40082 for overlap fix
   tunnel->AddNode(volColdBox, 0,
                   new TGeoTranslation(displacement.X() - (fCBRearWallXDim - fFeBlockX) / 2. + 28.5,
                                       displacement.Y() - (fCBFrontWallYDim - fFeBlockY) / 2. + 121,
                                       displacement.Z() + fAcrylicWidth - fFeBlockZ / 2. - fBPolyWidth + 1.));

if (SND_Z<0.1){ // for H6 and H8 testbeam setup
   top->AddNode(detector, 0);
 }else{
   top->AddNode(detector, 0,localSND_physCS_comb);
   top->AddNode(tunnel , 1,new TGeoTranslation(fTunnelDX,fTunnelDY,fTunnelDZ));
 }

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
