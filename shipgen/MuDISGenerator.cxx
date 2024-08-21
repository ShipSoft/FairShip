#include "MuDISGenerator.h"
#include "FairLogger.h"
#include "FairPrimaryGenerator.h"
#include "TFile.h"
#include "TGeoCompositeShape.h"
#include "TGeoEltu.h"
#include "TGeoManager.h"
#include "TGeoNode.h"
#include "TGeoVolume.h"
#include "TMath.h"
#include "TROOT.h"
#include "TRandom.h"
#include "TSystem.h"
#include "TVectorD.h"

#include <math.h>

using std::cout;
using std::endl;

const Double_t c_light = 29.9792458;//speed of light in cm/ns
// MuDIS momentum GeV
// Vertex in SI units, assume this means m

// -----   Default constructor   -------------------------------------------
MuDISGenerator::MuDISGenerator() {}
// -------------------------------------------------------------------------
// -----   Default constructor   -------------------------------------------
Bool_t MuDISGenerator::Init(const char* fileName) {
  return Init(fileName, 0);
}
Bool_t MuDISGenerator::Init(const char* fileName, const int firstEvent) {
    LOGF(info, "Opening input file %s", fileName);

  iMuon = 0;
  dPart = 0;
  dPartSoft = 0; 
  fInputFile = TFile::Open(fileName);
  if (!fInputFile) {
      LOG(FATAL) << "Error opening input file";
      return kFALSE;
  }
  fTree = fInputFile->Get<TTree>("DIS");
  fNevents = fTree->GetEntries();
  fn = firstEvent;

  fTree->SetBranchAddress("InMuon", &iMuon);    // incoming muon
  fTree->SetBranchAddress("DISParticles", &dPart);
  fTree->SetBranchAddress("SoftParticles", &dPartSoft); // Soft interaction particles
  return kTRUE;
}

Double_t MuDISGenerator::MeanMaterialBudget(const Double_t *start, const Double_t *end, Double_t *mparam)
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
  // mparam[7] - maximum density encountered (g/cm^3)
  //
  //  Origin:  Marian Ivanov, Marian.Ivanov@cern.ch
  //
  //  Corrections and improvements by
  //        Andrea Dainese, Andrea.Dainese@lnl.infn.it,
  //        Andrei Gheata,  Andrei.Gheata@cern.ch
  //        Anupama Reghunath, anupama.reghunath@cern.ch
  //
  mparam[0] = 0;
  mparam[1] = 1;
  mparam[2] = 0;
  mparam[3] = 0;
  mparam[4] = 0;
  mparam[5] = 0;
  mparam[6] = 0;
  mparam[7] = 0;
  //
    Double_t bparam[6];   // total parameters
    Double_t lparam[6];   // local parameters

    for (Int_t i = 0; i < 6; i++)
        bparam[i] = 0;

    if (!gGeoManager) {
        return 0.;
    }
    //
    Double_t length;
    Double_t dir[3];
    length = TMath::Sqrt((end[0] - start[0]) * (end[0] - start[0]) + (end[1] - start[1]) * (end[1] - start[1])
                         + (end[2] - start[2]) * (end[2] - start[2]));
    mparam[4] = length;
    if (length < TGeoShape::Tolerance())
        return 0.0;
    Double_t invlen = 1. / length;
    dir[0] = (end[0] - start[0]) * invlen;
    dir[1] = (end[1] - start[1]) * invlen;
    dir[2] = (end[2] - start[2]) * invlen;

    // Initialize start point and direction
    TGeoNode* currentnode = 0;
    TGeoNode* startnode = gGeoManager->InitTrack(start, dir);
    if (!startnode) {
        LOG(ERROR) << "Start point out of geometry: x " << start[0] << ", y " << start[1] << ", z " << start[2];
        return 0.0;
    }
    TGeoMaterial* material = startnode->GetVolume()->GetMedium()->GetMaterial();
    lparam[0] = material->GetDensity();
    if (lparam[0] > mparam[7])
        mparam[7] = lparam[0];
    lparam[1] = material->GetRadLen();
    lparam[2] = material->GetA();
    lparam[3] = material->GetZ();
    lparam[4] = length;
    lparam[5] = lparam[3] / lparam[2];
    if (material->IsMixture()) {
        TGeoMixture* mixture = (TGeoMixture*)material;
        lparam[5] = 0;
        Double_t sum = 0;
        for (Int_t iel = 0; iel < mixture->GetNelements(); iel++) {
            sum += mixture->GetWmixt()[iel];
            lparam[5] += mixture->GetZmixt()[iel] * mixture->GetWmixt()[iel] / mixture->GetAmixt()[iel];
        }
        lparam[5] /= sum;
    }

    // Locate next boundary within length without computing safety.
    // Propagate either with length (if no boundary found) or just cross boundary
    gGeoManager->FindNextBoundaryAndStep(length, kFALSE);
    Double_t step = 0.0;   // Step made
    Double_t snext = gGeoManager->GetStep();
    // If no boundary within proposed length, return current density
    if (!gGeoManager->IsOnBoundary()) {
        mparam[0] = lparam[0];
        mparam[1] = lparam[4] / lparam[1];
        mparam[2] = lparam[2];
        mparam[3] = lparam[3];
        mparam[4] = lparam[4];
        return lparam[0];
    }
    // Try to cross the boundary and see what is next
    Int_t nzero = 0;
    while (length > TGeoShape::Tolerance()) {
        currentnode = gGeoManager->GetCurrentNode();
        if (snext < 2. * TGeoShape::Tolerance())
            nzero++;
        else
            nzero = 0;
        if (nzero > 3) {
            // This means navigation has problems on one boundary
            // Try to cross by making a small step
            // AliErrorClass("Cannot cross boundary\n");
            mparam[0] = bparam[0] / step;
            mparam[1] = bparam[1];
            mparam[2] = bparam[2] / step;
            mparam[3] = bparam[3] / step;
            mparam[5] = bparam[5] / step;
            mparam[4] = step;
            mparam[0] = 0.;        // if crash of navigation take mean density 0
            mparam[1] = 1000000;   // and infinite rad length
            return bparam[0] / step;
        }
        mparam[6] += 1.;
        step += snext;
        bparam[1] += snext / lparam[1];
        bparam[2] += snext * lparam[2];
        bparam[3] += snext * lparam[3];
        bparam[5] += snext * lparam[5];
        bparam[0] += snext * lparam[0];

        if (snext >= length)
            break;
        if (!currentnode)
            break;
        length -= snext;
        material = currentnode->GetVolume()->GetMedium()->GetMaterial();
        lparam[0] = material->GetDensity();
        if (lparam[0] > mparam[7])
            mparam[7] = lparam[0];
        lparam[1] = material->GetRadLen();
        lparam[2] = material->GetA();
        lparam[3] = material->GetZ();
        lparam[5] = lparam[3] / lparam[2];
        if (material->IsMixture()) {
            TGeoMixture* mixture = (TGeoMixture*)material;
            lparam[5] = 0;
            Double_t sum = 0;
            for (Int_t iel = 0; iel < mixture->GetNelements(); iel++) {
                sum += mixture->GetWmixt()[iel];
                lparam[5] += mixture->GetZmixt()[iel] * mixture->GetWmixt()[iel] / mixture->GetAmixt()[iel];
            }
            lparam[5] /= sum;
        }
        gGeoManager->FindNextBoundaryAndStep(length, kFALSE);
        snext = gGeoManager->GetStep();
    }
    mparam[0] = bparam[0] / step;
    mparam[1] = bparam[1];
    mparam[2] = bparam[2] / step;
    mparam[3] = bparam[3] / step;
    mparam[5] = bparam[5] / step;
    return bparam[0] / step;
}

// -----   Destructor   ----------------------------------------------------
MuDISGenerator::~MuDISGenerator()
{
    fInputFile->Close();
    fInputFile->Delete();
    delete fInputFile;
}
// -----   Passing the event   ---------------------------------------------
Bool_t MuDISGenerator::ReadEvent(FairPrimaryGenerator* cpg)
{
    if (fn==fNevents) {LOG(WARNING) << "End of input file. Rewind.";}
    fTree->GetEntry(fn%fNevents);
    fn++;
    if (fn%10==0) {
      cout << "Info MuDISGenerator: MuDIS event-nr "<< fn << endl;
    }
    

    int nf = dPart->GetEntries();
    int ns = dPartSoft->GetEntries(); 
    //cout << "*********************************************************" << endl;
    //cout << "muon DIS Generator debug " << iMuon->GetEntries()<< " "<< iMuon->AddrAt(0) << " nf "<< nf << " fn=" << fn <<endl; 
    // some start/end positions in z (f.i. emulsion to Tracker 1)
    Double_t start[3] = {0., 0., startZ};
    Double_t end[3] = {0., 0., endZ};

// incoming muon  array('d',[pid,px,py,pz,E,x,y,z,w,t])
    TVectorD* mu = dynamic_cast<TVectorD*>(iMuon->AddrAt(0));
    //cout << "muon DIS Generator in muon " << int(mu[0][0])<< endl; 
    Double_t x = mu[0][5]*100.; // come in m -> cm
    Double_t y = mu[0][6]*100.; // come in m -> cm
    Double_t z = mu[0][7]*100.; // come in m -> cm
    Double_t w = mu[0][8];
    Double_t t_muon = mu[0][11]; // in ns

// calculate start/end positions along this muon, and amout of material in between
                    
    Double_t txmu=mu[0][1]/mu[0][3];
    Double_t tymu=mu[0][2]/mu[0][3];
    start[0]=x-(z-start[2])*txmu;
    start[1]=y-(z-start[2])*tymu;
    end[0]=x-(z-end[2])*txmu;
    end[1]=y-(z-end[2])*tymu;

    // skip the event if the muon trajectory doesn't intersect the pre-set x-y range
    // these steps save a lot of computing time!
    // first, look for overlaps in the x or y axes - if none, continue

    if (max(start[1], startY) > min(end[1], endY)) {return kTRUE;}
    Double_t max_of_start = max(start[0], startX);
    Double_t min_of_end = min(end[0], endX);
    if (max_of_start > min_of_end) {return kTRUE;}
    // then find the z range of the x-axis overlap
    Double_t z_at_max=z-(x-max_of_start)/(txmu+1e-20);
    Double_t z_at_min=z-(x-min_of_end)/(txmu+1e-20);
    // finally check if for the latter z range there is also an overlap in the y axis - if none, continue
    Double_t y_at_max=y-(z-z_at_max)*tymu;
    Double_t y_at_min=y-(z-z_at_min)*tymu;
    if (max( min(y_at_max, y_at_min), startY) > min( max(y_at_max, y_at_min), endY)) {
       return kTRUE;
    }
    
    LOG(DEBUG) << "MuDIS: mu xyz position " << x << ", " << y << ", " << z;
    LOG(DEBUG) << "MuDIS: mu pxyz position " << mu[0][1] << ", " << mu[0][2] << ", " << mu[0][3];
    LOG(DEBUG) << "MuDIS: mu weight*DISmultiplicity  " << w;
    LOG(DEBUG) << "MuDIS: mu DIS cross section " << cross_sec;
    LOG(DEBUG) << "MuDIS: start position " << start[0] << ", " << start[1] << ", " << start[2];
    LOG(DEBUG) << "MuDIS: end position " << end[0] << ", " << end[1] << ", " << end[2];

    Double_t bparam;
    Double_t mparam[8];
    bparam = MeanMaterialBudget(start, end, mparam);
    // loop over trajectory between start and end to pick an interaction point
    Double_t prob2int = 0.;
    Double_t xmu;
    Double_t ymu;
    Double_t zmu;
    Int_t count=0;
    //cout << "Info MuDISGenerator Start prob2int while loop, bparam= " << bparam << ", " << bparam*1.e8 <<endl;
    //cout << "Info MuDISGenerator What was maximum density, mparam[7]= " << mparam[7] << ", " << mparam[7]*1.e8 <<endl;
    

    while (prob2int<gRandom->Uniform(0.,1.)) {
      zmu=gRandom->Uniform(start[2],end[2]);
      xmu=x-(z-zmu)*txmu;
      ymu=y-(z-zmu)*tymu;

    Int_t count = 0;
    LOG(DEBUG) << "Info MuDISGenerator Start prob2int while loop, bparam= " << bparam << ", " << bparam * 1.e8;
    LOG(DEBUG) << "Info MuDISGenerator What was maximum density, mparam[7]= " << mparam[7] << ", " << mparam[7] * 1.e8;

    while (prob2int < gRandom->Uniform(0., 1.)) {
        zmu = gRandom->Uniform(start[2], end[2]);
        xmu = x - (z - zmu) * txmu;
        ymu = y - (z - zmu) * tymu;

	// check if the selected interaction position is inside the pre-set x-y range
	//if not retry! This will force the generator to simulate interactions in our selected range!!!
	if (xmu<startX || xmu>endX || ymu<startY || ymu>endY){
	  prob2int=0.;
	  continue;
	}

	// get local material at this point
        TGeoNode* node = gGeoManager->FindNode(xmu, ymu, zmu);
        TGeoMaterial* mat = 0;
        if (node && !gGeoManager->IsOutside())
            mat = node->GetVolume()->GetMaterial();
        LOG(DEBUG) << "Info MuDISGenerator: mat " << count << ", " << mat->GetName() << ", " << mat->GetDensity();
        // density relative to Prob largest density along this trajectory, i.e. use rho(Pt)
        prob2int = mat->GetDensity() / mparam[7];
        if (prob2int > 1.) {
            LOG(WARNING) << "MuDISGenerator: prob2int > Maximum density????";
            LOG(WARNING) << "prob2int: " << prob2int;
            LOG(WARNING) << "maxrho: " << mparam[7];
            LOG(WARNING) << "material: " << mat->GetName();
        }
        count += 1;
    }

    //cout << "MuDIS: put position " << xmu << ", " << ymu << ", " << zmu << endl;

    double total_mom = TMath::Sqrt(TMath::Power(mu[0][1], 2) +
                                  TMath::Power(mu[0][2], 2) +
                                  TMath::Power(mu[0][3], 2));    //in GeV

    double distance = TMath::Sqrt(TMath::Power(x - xmu, 2) +
                                  TMath::Power(y - ymu, 2) +
                                  TMath::Power(z - zmu, 2));    // in cm

    
    double mass = 0.10565999895334244;  //muon mass in GeV
    double v    = c_light*total_mom/TMath::Sqrt(TMath::Power(total_mom,2)+
                                                TMath::Power(mass,2));
    double t_rmu=distance/v;

    // Adjust time based on the relative positions
    if (zmu < z) {
        t_rmu = -t_rmu;
    }

    double t_DIS=(t_muon+t_rmu)/1e9; //time taken in seconds to reach [xmu,ymu,zmu]
    
    cpg->AddTrack(int(mu[0][0]),mu[0][1],mu[0][2],mu[0][3],xmu,ymu,zmu,-1,false,mu[0][4],t_DIS,w);//set time of the track start as t_muon from the input file

    // outgoing particles, [did,dpx,dpy,dpz,E], put density along trajectory as weight, g/cm^2
    w=mparam[0]*mparam[4];//modify weight, by multiplying with average densiy along track??
    
    for(int i=0; i<nf; i++)
    	{
         TVectorD* Part = dynamic_cast<TVectorD*>(dPart->AddrAt(i));
         //cout << "muon DIS Generator out part " << int(Part[0][0]) << endl; 
         //cout << "muon DIS Generator out part mom " << Part[0][1]<<" " << Part[0][2] <<" " << Part[0][3] << " " << Part[0][4] << endl; 
         //cout << "muon DIS Generator out part pos " << mu[0][5]<<" " << mu[0][6] <<" " << mu[0][7] << endl; 
         //cout << "muon DIS Generator out part w " << mu[0][8] << endl; 
         cpg->AddTrack(int(Part[0][0]),Part[0][1],Part[0][2],Part[0][3],xmu,ymu,zmu,0,true,Part[0][4],t_DIS,w); //it takes times in seconds.
         //cout << "muon DIS part added "<<endl;
       }
    
    //Soft interaction tracks
    

    for (int i = 0; i < ns; i++) {
        TVectorD* SoftPart = dynamic_cast<TVectorD*>(dPartSoft->AddrAt(i));
        if ( SoftPart[0][7] > zmu ) { //if the softinteractions are after the DIS point, don't save the soft interaction.
          continue;
        }
        double t_soft=SoftPart[0][8]/1e9;
        cpg->AddTrack(int(SoftPart[0][0]), SoftPart[0][1], SoftPart[0][2], SoftPart[0][3], SoftPart[0][5], SoftPart[0][6], SoftPart[0][7], 0, true, SoftPart[0][4], t_soft, w);

    }

  return kTRUE;
}
// -------------------------------------------------------------------------
Int_t MuDISGenerator::GetNevents()
{
    return fNevents;
}

