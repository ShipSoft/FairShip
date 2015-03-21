#include "ecalReco.h"

#include "ecalCell.h"
#include "ecalCluster.h"
#include "ecalStructure.h"
#include "ecalClusterCalibration.h"
#include "ecalReconstructed.h"

#include "TClonesArray.h"

#include <iostream>
#include <list>

using namespace std;

void ecalReco::Exec(Option_t* option)
{
  fEv++; fN=0; fRejected=0; fRejectedP=0;
//  if (fVerbose>0) Info("Exec", "Event %d.", fEv);

  fReconstucted->Delete();

  Int_t i;
  Int_t nc=fClusters->GetEntriesFast();
  ecalCluster* cls;
  ecalReconstructed* reco;
  Float_t x;
  Float_t y;
  ecalCell* maxs[40];		//maximums of the cluster
  Float_t e3[40];		//energy in 3x3 area near the maximum
  list<ecalCell*> lists[40];	//lists of 5x5-3x3 clusters near the maximum
  Int_t n;
  Int_t j;
  Int_t k;
  list<ecalCell*> cells;
  list<ecalCell*> cells2;
  list<ecalCell*>::const_iterator p;
  list<ecalCell*>::const_iterator p2;
  Float_t rawE;
  Float_t ourE;
  Float_t allE;
  ecalCell* tcell;

  for(i=0;i<nc;i++)
  {
    cls=(ecalCluster*)fClusters->At(i);
    // Clusters with single maximum. Separate code for speedup
    if (cls->Maxs()==1)
    {
      ReconstructXY(fStr->GetHitCell(cls->PeakNum(0)), x, y);
      reco=new ((*fReconstucted)[fN++]) ecalReconstructed(cls->Energy(), cls->PreCalibrated(), x, y, cls->PeakNum(0), i); 
      cls->SetStatus(1);
      continue;
    }
    TryReconstruct(cls, i);
/*
    //Multimaximum case
    n=cls->Maxs();
    for(j=0;j<n;j++)
    {
      maxs[j]=fStr->GetHitCell(cls->PeakNum(j));
      e3[j]=maxs[j]->GetEnergy(); 
      lists[j].clear();
      maxs[j]->GetNeighborsList(cells);
      for(p=cells.begin();p!=cells.end();++p)
      {
	e3[j]+=(*p)->GetEnergy();
	for(k=0;k<j-1;k++)
	{
	  tcell=fStr->GetHitCell(cls->PeakNum(k));
          tcell->GetNeighborsList(cells2);
	  // Have an intersection between 3x3 areas near maximum
	  if (find(cells2.begin(), cells2.end(), *p)!=cells2.end()) break;
	}
	if (j!=0&&k!=j-1) break;

	//form 5x5-3x3
	(*p)->GetNeighborsList(cells2);
        for(p2=cells2.begin();p2!=cells2.end();++p2)
	{
	  if (*p2==maxs[j])
	    continue;	//exclude maximum
	  if (find(cells.begin(), cells.end(), *p2)!=cells.end())
	    continue;	//exclude 3x3 area
	  if (find(lists[j].begin(), lists[j].end(), *p2)==lists[j].end())
	    lists[j].push_back(*p2);
	}
      }
      if (p!=cells.end()) break;
    }
    if (j!=n) 
    {
      cls->SetStatus(-1);
      fRejected++; fRejectedP+=cls->Maxs();
      if (fVerbose>9)
	Info("Exec", "Cluster %d with %d maximums rejected", i, n);
      continue;
    }
    //Second pass. Reconstruction
    for(j=0;j<n;j++)
    {
      ReconstructXY(maxs[j], x, y);
      rawE=ourE=e3[j];
      for(p=lists[j].begin();p!=lists[j].end();++p)
      {
	allE=ourE;
	for(k=0;k<n;k++)
	{
	  if (k==j) continue;
	  maxs[k]->Get5x5Cluster(cells2);
	  if (find(cells2.begin(), cells2.end(), *p)!=cells2.end()) allE+=e3[k];
	}
	rawE+=(*p)->GetEnergy()*ourE/allE;
      }
      reco=new ((*fReconstucted)[fN++]) ecalReconstructed(rawE, fCalib->Calibrate(maxs[j]->GetType(), rawE), x, y, cls->PeakNum(j), i); 
    }
    cls->SetStatus(1);
*/
  }
  if (fVerbose>0) Info("Exec", "Event %d. Good %d. Bad %d cls, %d maxs.", fEv, fN, fRejected, fRejectedP);
}

void ecalReco::TryReconstruct(ecalCluster* cls, Int_t clsnum)
{
  Int_t n=cls->Maxs();
  Int_t i;
  Int_t k;
  ecalCell* maxs[40];		//maximums of the cluster
  Float_t e3[40];		//energy in 3x3 area near the maximum
  list<ecalCell*> lists[40];	//lists of 5x5-3x3 areas near maximum
  Int_t isgood[40];		//good maximum (no intersection of 3x3 areas)
  Int_t rejected=0;
  list<ecalCell*> cells;
  list<ecalCell*> cells2;
  list<ecalCell*>::const_iterator p;
  list<ecalCell*>::const_iterator p2;
  ecalReconstructed* reco;
  Float_t rawE;
  Float_t ourE;
  Float_t allE;
  ecalCell* tcell;
  Float_t x;
  Float_t y;

  for(i=0;i<n;i++)
  {
    maxs[i]=fStr->GetHitCell(cls->PeakNum(i));
    e3[i]=maxs[i]->GetEnergy(); 
    lists[i].clear();
    isgood[i]=1;
    maxs[i]->GetNeighborsList(cells);
    for(p=cells.begin();p!=cells.end();++p)
    {
      e3[i]+=(*p)->GetEnergy();
      for(k=0;k<i-1;k++)
      {
	tcell=fStr->GetHitCell(cls->PeakNum(k));
	tcell->GetNeighborsList(cells2);
	// Have an intersection between 3x3 areas near maximum
	if (find(cells2.begin(), cells2.end(), *p)!=cells2.end()) isgood[i]--;
      }
      //form 5x5-3x3
      (*p)->GetNeighborsList(cells2);
      for(p2=cells2.begin();p2!=cells2.end();++p2)
      {
	if (*p2==maxs[i])
	  continue;	//exclude maximum
	if (find(cells.begin(), cells.end(), *p2)!=cells.end())
	  continue;	//exclude 3x3 area
	if (find(lists[i].begin(), lists[i].end(), *p2)==lists[i].end())
	  lists[i].push_back(*p2);
      }
    }
    if (p!=cells.end()) break;
  }

  //Second pass. Reconstruction
  for(i=0;i<n;i++)
  {
    if (isgood[i]!=1)
    {
      rejected++; fRejectedP++;
      continue;
    }
    ReconstructXY(maxs[i], x, y);
    rawE=ourE=e3[i];
    for(p=lists[i].begin();p!=lists[i].end();++p)
    {
      allE=ourE;
      for(k=0;k<n;k++)
      {
	if (k==i) continue;
	maxs[k]->Get5x5Cluster(cells2);
	if (find(cells2.begin(), cells2.end(), *p)!=cells2.end()) allE+=e3[k];
      }
      rawE+=(*p)->GetEnergy()*ourE/allE;
    }
    reco=new ((*fReconstucted)[fN++]) ecalReconstructed(rawE, fCalib->Calibrate(maxs[i]->GetType(), rawE), x, y, cls->PeakNum(i), clsnum); 
  }
  cls->SetStatus(1);
  if (rejected>0)
  {
    cls->SetStatus(-rejected);
    fRejected++;
  }
}

void ecalReco::ReconstructXY(ecalCell* max, Float_t& x, Float_t& y)
{
  // Now use just center of gravity
  Float_t e=max->GetEnergy();
  list<ecalCell*> cls;
  list<ecalCell*>::const_iterator p;

  x=max->GetCenterX()*max->GetEnergy();
  y=max->GetCenterY()*max->GetEnergy();
  max->GetNeighborsList(cls);
  for(p=cls.begin();p!=cls.end();++p)
  {
    x+=(*p)->GetCenterX()*(*p)->GetEnergy();
    y+=(*p)->GetCenterY()*(*p)->GetEnergy();
    e+=(*p)->GetEnergy();
  }
  x/=e; y/=e;
//  cout << x << ", " << y << " : " << max->GetCenterX() << ", " << max->GetCenterY() << endl;
}

/** Standard constructor **/
ecalReco::ecalReco(const char* name, const Int_t verbose)
  : FairTask(name, verbose), fEv(0), fN(0), fRejected(0), fRejectedP(0),
    fClusters(NULL), fReconstucted(NULL), fStr(NULL), fCalib(NULL)
{
  ;
}

/** Only to comply with frame work. **/
ecalReco::ecalReco()
  : FairTask(), fEv(-1111), fN(0), fRejected(0), fRejectedP(0),
    fClusters(NULL), fReconstucted(NULL), fStr(NULL), fCalib(NULL)
{
  ;
}

/** Finish a task **/
void ecalReco::Finish()
{
  ;
}

/** Destructor **/
ecalReco::~ecalReco()
{
  if (fReconstucted)
  {
    fReconstucted->Delete();
    delete fReconstucted;
  }
}

InitStatus ecalReco::Init()
{
  FairRootManager* io=FairRootManager::Instance();
  if (!io)
  {
    Fatal("Init", "Can't find IOManager.");
    return kFATAL;
  }
  fStr=(ecalStructure*)io->GetObject("EcalStructure");
  if (!fStr) 
  {
    Fatal("Init()", "Can't find calorimeter structure in the system.");
    return kFATAL;
  }
  fCalib=(ecalClusterCalibration*)io->GetObject("ecalClusterCalibration");
  if (!fCalib)
  {
    Fatal("Init", "Can't find ecalClusterCalibration in the system.");
    return kFATAL;
  }
  fClusters=(TClonesArray*)io->GetObject("EcalClusters");
  if (!fClusters) 
  {
    Fatal("Init()", "Can't find calorimeter clusters in the system.");
    return kFATAL;
  }

  fReconstucted=new TClonesArray("ecalReconstructed", 2000);
  io->Register("EcalReco", "ECAL", fReconstucted, kTRUE);

  fEv=0;
  return kSUCCESS;
}

TClonesArray* ecalReco::InitPython(TClonesArray* clusters, ecalStructure* str, ecalClusterCalibration* calib)
{
  fStr=str;
  fCalib=calib;
  fClusters=clusters;
  fReconstucted=new TClonesArray("ecalReconstructed", 2000);
  
  fEv=0;
  return fReconstucted;
}

ClassImp(ecalReco)
