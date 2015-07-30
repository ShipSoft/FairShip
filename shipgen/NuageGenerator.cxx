#include <math.h>
#include "TROOT.h"
#include "TMath.h"
#include "TFile.h"
#include "TRandom.h"
#include "FairPrimaryGenerator.h"
#include "NuageGenerator.h"
#include "TGeoVolume.h"
#include "TGeoNode.h"
#include "TGeoManager.h"
#include "TGeoEltu.h"
#include "TGeoCompositeShape.h"

using std::cout;
using std::endl;
using namespace TMath;
// read events from ntuples produced with Nuage
// Nuage momentum GeV
// Vertex in SI units, assume this means m
// important to read back number of events to give to FairRoot

// -----   Default constructor   -------------------------------------------
NuageGenerator::NuageGenerator() {}
// -------------------------------------------------------------------------
// -----   Default constructor   -------------------------------------------
Bool_t NuageGenerator::Init(const char* fileName) {
    return Init(fileName, 0);
}
// -----   Default constructor   -------------------------------------------
Bool_t NuageGenerator::Init(const char* fileName, const int firstEvent) {
    fNuOnly = false;
    fLogger = FairLogger::GetLogger();
    fLogger->Info(MESSAGE_ORIGIN,"Opening input file %s",fileName);
    fInputFile  = new TFile(fileName);
    if (fInputFile->IsZombie()) {
        fLogger->Fatal(MESSAGE_ORIGIN, "Error opening the Signal file");
    }
    fTree = (TTree *)fInputFile->Get("tree");
    fNevents = fTree->GetEntries();
    fn = firstEvent;
    fTree->SetBranchAddress("Ev",&pxl);    // incoming neutrino energy
    fTree->SetBranchAddress("pxv",&pxv);
    fTree->SetBranchAddress("pyv",&pyv);
    fTree->SetBranchAddress("pzv",&pzv);
    fTree->SetBranchAddress("neu",&neu);    // incoming neutrino PDG code
    fTree->SetBranchAddress("cc",&cc);  // Is it a CC event?
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

Double_t NuageGenerator::MeanMaterialBudget(const Double_t *start, const Double_t *end, Double_t *mparam)
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
    //
    
    mparam[0]=0; mparam[1]=1; mparam[2] =0; mparam[3] =0;
    mparam[4]=0; mparam[5]=0; mparam[6]=0; mparam[7]=0;
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
    if (lparam[0] > mparam[7]) mparam[7]=lparam[0];
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
        if (lparam[0] > mparam[7]) mparam[7]=lparam[0];
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

//----------------------------------------------------------------------------------------

std::vector<double> NuageGenerator::Rotate(Double_t x, Double_t y, Double_t z, Double_t px, Double_t py, Double_t pz)
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
    //cout << "Info NuageGenerator: rotated" << pout[0] << " " << pout[1] << " " << pout[2] << " " << x << " " << y << " " << z <<endl;
    return pout;
}


// -----   Destructor   ----------------------------------------------------
NuageGenerator::~NuageGenerator()
{
    fInputFile->Close();
    fInputFile->Delete();
    delete fInputFile;
}
// -------------------------------------------------------------------------


// -----   Passing the event   ---------------------------------------------
Bool_t NuageGenerator::ReadEvent(FairPrimaryGenerator* cpg)
{
  fFirst = kFALSE;
    //some start/end positions in z (emulsion to Tracker 1)
    Double_t start[3]={startX,startY,startZ};
    //cout << "startX = " << startX << "    Y = " << startY << "   Z = " << startZ << endl;
    //cout << "endX = " << endX << "    Y = " << endY << "    Z = " << endZ << endl;
    
    Double_t end[3]={endX,endY,endZ};
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
    //cout << endl;
    //cout << "*****************************************************************" << endl;
    
    if (fn==fNevents) {fLogger->Warning(MESSAGE_ORIGIN, "End of input file. Rewind.");}
    fTree->GetEntry(fn%fNevents);
    fn++;
    if (fn%100==0) {
        cout << "Info GenieGenerator: neutrino event-nr "<< fn << endl;
    }

    //Mean distance between start[2] and end[2]
    Double_t zMean = (start[2]+end[2])/2;
    //Distance from the target (Beam Dump (0,0));
    Double_t zBD = zMean - ztarget;
    
    //only accept neutrinos with a ThetaX in the ThetaXMin/Max range and same for ThetaY
    Double_t ThetaXMax = startX/zBD;
    Double_t ThetaXMin = endX/zBD;
    Double_t ThetaYMax = startY/zBD;
    Double_t ThetaYMin = endY/zBD;
    // cout << "ThetaXMax = " << ThetaXMax << "   ThetaXMin = " << ThetaXMin << endl;
    //cout << "ThetaYMax = " << ThetaYMax << "   ThetaYMin = " << ThetaYMin << endl;
    
    // Incoming neutrino, get a random px,py
    //cout << "Info GenieGenerator: neutrino " << neu << "p-in "<< pxv << pyv << pzv << " nf "<< nf << endl;
    //cout << "Info GenieGenerator: ztarget " << ztarget << endl;
    Double_t bparam=0.;
    Double_t mparam[8];
    Double_t pout[3] ;
    Double_t txnu=0;
    Double_t tynu=0;
    //Does this neutrino fly through material? Otherwise draw another pt..
    //cout << "Info GenieGenerator Start bparam while loop" << endl;
    while (bparam<1.e-10)
      {
        //generate pt of ~0.3 GeV
	txnu = gRandom->Uniform(ThetaXMax,ThetaXMin);
	tynu = gRandom->Uniform(ThetaYMax,ThetaYMin);
	
	pout[2] = pzv*pzv/(1+txnu*txnu+tynu*tynu);
	  
        if (pout[2]>0.)
	  {
            pout[2]=TMath::Sqrt(pout[2]);
	    pout[0] = pout[2]*txnu;
	    pout[1] = pout[2]*tynu;
	    //cout << "txnu = " << txnu << "     tynu = " << tynu << endl;
	    
	    //cout << "Info GenieGenerator: neutrino pxyz " << pout[0] << ", " << pout[1] << ", " << pout[2] << endl;

	    start[0]=txnu*(start[2]-ztarget);
	    start[1]=tynu*(start[2]-ztarget);		
	    //cout << "Info GenieGenerator: neutrino xyz-start " << start[0] << "  -  " << start[1] << "  -   " << start[2] << endl;
		
	    end[0]=txnu*(end[2]-ztarget);
	    end[1]=tynu*(end[2]-ztarget);  
	    //cout << "Info GenieGenerator: neutrino xyz-end " << end[0] << "  -   " << end[1] << "   -  " << end[2] << endl;
	    
                //get material density between these two points
	    bparam=MeanMaterialBudget(start, end, mparam);
            
	  }
      }
    
    //loop over trajectory between start and end to pick an interaction point
    Double_t prob2int = 0.;
    Double_t x;
    Double_t y;
    Double_t z;
    //Int_t count=0;
    //cout << "Info GenieGenerator Start prob2int while loop, bparam= " << bparam << ", " << bparam*1.e8 <<endl;
    //cout << "Info GenieGenerator What was maximum density, mparam[7]= " << mparam[7] << ", " << mparam[7]*1.e8 <<endl;
    while (prob2int<gRandom->Uniform(0.,1.)) {
        z=gRandom->Uniform(start[2],end[2]);
	// x=gRandom->Uniform(start[0],end[0]);
        //y=gRandom->Uniform(start[1],end[1]);
	x= txnu*(z-ztarget);
        y= tynu*(z-ztarget);
	//cout << "x = " << x << "  y = " << y << "   z " << z << endl;
        //get local material at this point
        TGeoNode *node = gGeoManager->FindNode(x,y,z);
        TGeoMaterial *mat = 0;
        if (node && !gGeoManager->IsOutside()) mat = node->GetVolume()->GetMaterial();
        //cout << "Info GenieGenerator: mat " <<  count << ", " << mat->GetName() << ", " << mat->GetDensity() << endl;
        //density relative to Prob largest density along this trajectory, i.e. use rho(Pt)
        prob2int= mat->GetDensity()/mparam[7];
        if (prob2int>1.) cout << "***WARNING*** GenieGenerator: prob2int > Maximum density????" << prob2int << " maxrho:" << mparam[7] << " material: " <<  mat->GetName() << endl;
        //count+=1;
    }
    //cout << "Info GenieGenerator: prob2int " << prob2int << ", " << count << endl;

    //cout <<" Neutrino pdg = " <<  neu << endl;
    
    Double_t zrelative=z-ztarget;
    Double_t tof=TMath::Sqrt(x*x+y*y+zrelative*zrelative)/2.99792458e+6;
    cpg->AddTrack(neu,pout[0],pout[1],pout[2],x,y,z,-1,false,TMath::Sqrt(pout[0]*pout[0]+pout[1]*pout[1]+pout[2]*pout[2]),tof,mparam[0]*mparam[4]);
    if (not fNuOnly){
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
            //cout << "f " << pdgf[i] << " pz "<< pzf[i] << endl;
        }
        
        //cout << "Info GenieGenerator Return from GenieGenerator" << endl;
    }
    return kTRUE;
}







// -------------------------------------------------------------------------
Int_t NuageGenerator::GetNevents()
{
    return fNevents;
}


ClassImp(NuageGenerator)
