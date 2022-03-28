#include "sndCluster.h"
#include "FairRunSim.h"

// -----   Default constructor   -------------------------------------------
sndCluster::sndCluster()
: TObject(),
	fType(0)
{
}

// -----   Standard constructor   ------------------------------------------
sndCluster::sndCluster(Int_t first, Int_t N,std::vector<sndScifiHit*> hitlist,Scifi* ScifiDet, Bool_t withQDC)
  :TObject(),
	fType(0),
	fTime(999),
	fFirst(first),
	fN(N)
{
	Double_t weight = 0;
	TVector3 A(0,0,0);
	TVector3 B(0,0,0);
// make clusterCentre:
	for (int k = 0;k<fN; ++k){
		ScifiDet->GetSiPMPosition(k+fFirst, A, B);
		Double_t w = 1.;
		if (withQDC) {dynamic_cast<sndScifiHit*> (hitlist.at(k))->GetEnergy();}
		Double_t t = 6.25 * dynamic_cast<sndScifiHit*> (hitlist.at(k))->GetTime();
		weight+=w;
		fMeanPositionA+=w*TVector3(A);
		fMeanPositionB+=w*TVector3(B);
		if(t<fTime){fTime = t;}
	}
	Double_t winv = 1./weight;
	fMeanPositionA = TVector3(fMeanPositionA)*winv;
	fMeanPositionB = TVector3(fMeanPositionB)*winv;
	fEnergy = weight;
}

sndCluster::sndCluster(Int_t first, Int_t N,std::vector<MuFilterHit*>,MuFilter* MuDet)
  :TObject(),
	fType(1),
	fFirst(first),
	fN(N)
{
// make clusterCentre:
	
}

void sndCluster::Print() const
{
	std::cout << "-I- SND cluster " << " first " << fFirst << " of "<<fN<< " hits"<<std::endl;
	fMeanPositionA.Print();
	fMeanPositionB.Print();
	std::cout << std::endl;
}
// -----   Destructor   ----------------------------------------------------
sndCluster::~sndCluster() { }
// -------------------------------------------------------------------------

ClassImp(sndCluster)
