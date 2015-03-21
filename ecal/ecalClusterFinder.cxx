#include "ecalClusterFinder.h"

#include "TClonesArray.h"

#include "FairRootManager.h"
#include "FairTrackParam.h"

#include "ecalStructure.h"
#include "ecalCell.h"
#include "ecalInf.h"
#include "ecalCluster.h"
#include "ecalPreCluster.h"
#include "ecalMaximum.h"
#include "ecalClusterCalibration.h"

#include <iostream>
#include <list>

using namespace std;

/** Exec a task **/
void ecalClusterFinder::Exec(Option_t* option)
{
  fEv++;

  ClearPreClusters();
  FormPreClusters();
  FormClusters();
}

InitStatus ecalClusterFinder::Init()
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
  fInf=fStr->GetEcalInf();
  fMaximums=(TClonesArray*)io->GetObject("EcalMaximums");
  if (!fMaximums)
  {
    Fatal("Init", "Can't find array of calorimeter maximums in the system.");
    return kFATAL;
  }
  fCalib=(ecalClusterCalibration*)io->GetObject("ecalClusterCalibration");
  if (!fCalib)
  {
    Fatal("Init", "Can't find ecalClusterCalibration in the system.");
    return kFATAL;
  }

  fClusters=new TClonesArray("ecalCluster", 2000);
  io->Register("EcalClusters", "ECAL", fClusters, kTRUE);
  fEv=0;
  return kSUCCESS;
}

TClonesArray* ecalClusterFinder::InitPython(ecalStructure* structure, TClonesArray* maximums, ecalClusterCalibration* calib)
{
  fMaximums=maximums;
  fStr=structure;
  fCalib=calib;
  fClusters=new TClonesArray("ecalCluster", 2000);
  return fClusters;
}

/** Finish a task **/
void ecalClusterFinder::Finish()
{
  ;
}

/** Destructor **/
ecalClusterFinder::~ecalClusterFinder()
{
  if (fClusters)
  {
    fClusters->Delete();
    delete fClusters;
  }
}

/** Form a preclusters.
 ** A precluster --- a group of cells neighbor to maximum cell.
 ** A cluster is a group of preclusters with common cells. **/
void ecalClusterFinder::FormPreClusters()
{
  Int_t nm=fMaximums->GetEntriesFast();
  Int_t i=0;
  ecalMaximum* max;
  list<ecalCell*> all;
  list<ecalCell*>::const_iterator p;
  list<ecalCell*>::const_iterator p2;
  list<ecalCell*> cls;
  list<ecalCell*> cls2;
  ecalCell* cell;
  ecalCell* min;
  Double_t e;
  Double_t ecls;
  ecalPreCluster* precluster;
 

  for(;i<nm;i++)
  {
    max=(ecalMaximum*)fMaximums->At(i);
    if (max==NULL) continue;
    /** Remove maximums matched with charged tracks **/
    if (max->Mark()!=0) continue;
    cell=max->Cell();
    ecls=cell->GetEnergy();
//    cout << ecls << endl;
    /** Remove low energy maximums **/
    if (ecls<fMinMaxE) continue;
/*
    cell->GetNeighborsList(all);
    cls.clear();
    for(p=all.begin();p!=all.end();++p)
    {
      (*p)->GetNeighborsList(cls2);
      for(p2=cls2.begin();p2!=cls2.end();++p2)
        if (find(cls.begin(), cls.end(), *p2)==cls.end()) cls.push_back(*p2);
    }
*/
    cell->Get5x5Cluster(cls);
    ecls=0.0;
    for(p=cls.begin();p!=cls.end();++p)
      ecls+=(*p)->GetEnergy();
//    cout << ":" << ecls << endl;
    /** Remove low energy clusters **/
    if (ecls<fMinClusterE) continue;
    precluster=new ecalPreCluster(cls, max);
    fPreClusters.push_back(precluster);
  }
}

/** Form clusters from precluster **/
void ecalClusterFinder::FormClusters()
{
  /** ecalCluster needs a destructor call :-( **/
  fClusters->Delete();
  Int_t fN=0;
  list<ecalPreCluster*>::const_iterator p1=fPreClusters.begin();
  list<ecalPreCluster*>::const_iterator p2;
  list<ecalCell*> cluster;
  list<ecalMaximum*> maxs;
  list<ecalCell*>::const_iterator pc;
  list<ecalCell*>::const_iterator pc1;
  UInt_t oldsize;
  Int_t MaxSize=0;
  Int_t Maximums=0;
  Int_t max;
  Int_t type;
  
  if (fVerbose>9)
  {
    Info("FormClusters", "Total %d preclusters found.", (Int_t)fPreClusters.size());
  }
  for(;p1!=fPreClusters.end();++p1)
  if ((*p1)->fMark==0)
  {
    cluster.clear(); oldsize=0; maxs.clear();
    cluster=(*p1)->fCells; maxs.push_back((*p1)->fMax); type=(*p1)->fMaximum->GetType();
    max=1;
    while(cluster.size()!=oldsize)
    {
      oldsize=cluster.size();
      p2=p1;
      for(++p2;p2!=fPreClusters.end();++p2)
      if ((*p2)->fMark==0)
      {
        pc=cluster.begin();
	for(;pc!=cluster.end();++pc)
	{
	  pc1=find((*p2)->fCells.begin(), (*p2)->fCells.end(), (*pc));
	  if (pc1==(*p2)->fCells.end()) continue;
	  break;
	}
	if (pc!=cluster.end())
	{
	  (*p2)->fMark=1;
	  pc=(*p2)->fCells.begin();
	  for(;pc!=(*p2)->fCells.end();++pc)
	    if (find(cluster.begin(), cluster.end(), (*pc))==cluster.end())
	      cluster.push_back(*pc);
	  maxs.push_back((*p2)->fMax);
	  max++;
	}
      }
    }
    (*p1)->fMark=1;
    if ((Int_t)cluster.size()>MaxSize)
      MaxSize=cluster.size();
    if (max>Maximums) Maximums=max;
    ecalCluster* cls=new ((*fClusters)[fN]) ecalCluster(fN, cluster, maxs); fN++;
    cls->fPreCalibrated=fCalib->Calibrate(type, cls->fEnergy);
  }
  if (fVerbose>0)
  {
    Info("FormClusters", "Total %d clusters formed.", fN);
    Info("FormClusters", "Maximum size of cluster is %d cells.",  MaxSize);
    Info("FormClusters", "Maximum number of photons per cluster is %d.",  Maximums);
  }
}

/** Clear a preclusters list **/
void ecalClusterFinder::ClearPreClusters()
{
  list<ecalPreCluster*>::const_iterator p=fPreClusters.begin();
  for(;p!=fPreClusters.end();++p)
    delete (*p);
  fPreClusters.clear();
}

/** Standard constructor **/
ecalClusterFinder::ecalClusterFinder(const char* name, const Int_t verbose)
  : FairTask(name, verbose),
    fEv(0),
    fMaximums(NULL),
    fClusters(NULL),
    fStr(NULL),
    fInf(NULL),
    fPreClusters(),
    fMinClusterE(0.03),
    fMinMaxE(0.015)   
{
  ;
}


/** Only to comply with frame work. **/
ecalClusterFinder::ecalClusterFinder()
  : FairTask(),
    fEv(0),
    fMaximums(NULL),
    fClusters(NULL),
    fStr(NULL),
    fInf(NULL),
    fPreClusters(),
    fMinClusterE(0.03),
    fMinMaxE(0.015)   
{
  ;
}

ClassImp(ecalClusterFinder)
