#include "sndCluster.h"
#include "FairRunSim.h"

// -----   Default constructor   -------------------------------------------
sndCluster::sndCluster()
: TObject(),
	fType(0)
{
}

// -----   Standard constructor   ------------------------------------------
sndCluster::sndCluster(Int_t first, Int_t N,std::vector<sndScifiHit*> hitlist)
  :TObject(),
	fType(0),
	fFirst(first),
	fN(N)
{
	Scifi* ScifiDet = dynamic_cast<Scifi*> (FairRunSim::Instance()->GetListOfModules()->FindObject("Scifi") );
	Double_t weight = 0;
	TVector3 A(0,0,0);
	TVector3 B(0,0,0);
// make clusterCentre:
	for (int k = 0;k<fN; ++k){
		ScifiDet->GetSiPMPosition(k+fFirst, A, B);
		Double_t w = dynamic_cast<sndScifiHit*> (hitlist.at(k))->GetEnergy();
		weight+=w;
		fMeanPositionA+=w*TVector3(A);
		fMeanPositionB+=w*TVector3(B);
	}
	Double_t winv = 1./weight;
	fMeanPositionA = TVector3(fMeanPositionA)*winv;
	fMeanPositionB = TVector3(fMeanPositionB)*winv;
	fEnergy = weight;
}

sndCluster::sndCluster(Int_t first, Int_t N,std::vector<MuFilterHit*>)
  :TObject(),
	fType(1),
	fFirst(first),
	fN(N)
{
// make clusterCentre:
	MuFilter* MuDet = dynamic_cast<MuFilter*> (FairRunSim::Instance()->GetListOfModules()->FindObject("MuFilter") );
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
