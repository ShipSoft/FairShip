#include "ecalDigi.h"

#include "ecalStructure.h"

#include "FairRootManager.h"

#include "TRandom.h"
#include "TSystem.h"
#include "TMath.h"

#include <iostream>
#include <fstream>
#include <list>

using namespace std;

/** --- Default constructor --------------------------------------------------- **/
ecalDigi::ecalDigi() 
  : FairTask(),
    fPedestal(80),
    fADCMax(16384),
    fADCNoise(1.0e-3),
    fADCChannel(1.0e-3),
    fStr(NULL), fChannelMap()
{
  fChannelMap.clear();
}

/** --- Standard constructor. Use this ---------------------------------------- **/
ecalDigi::ecalDigi(const char* name, Int_t iVerbose)
  : FairTask(name, iVerbose),
    fPedestal(80),
    fADCMax(16384),
    fADCChannel(1.0e-3),
    fADCNoise(1.0e-3),
    fStr(NULL), fChannelMap()
{
  fChannelMap.clear();
}

/** --- Ugly load of map channel number -> ADC channel from the file ---------- **/
void ecalDigi::LoadChannelMap(const char* filename)
{
  map<Int_t, Float_t> tmp;
  TString fname=filename;	gSystem->ExpandPathName(fname);
  ifstream f(fname);
  Int_t ch;
  Int_t i=0;
  Float_t adc;

  tmp.clear();
  for(;;)
  {
    f >> ch; if (f.eof()) break;
    f >> adc; if (f.eof()) break;
    tmp[ch]=adc;
    i++;
  }
  if (fVerbose>999)
    Info("LoadChannelMap", "%d records read", i);
  f.close();
  SetChannelMap(tmp);
}

/** --- Initialization of the task -------------------------------------------- **/
InitStatus ecalDigi::Init()
{
  FairRootManager* manager=FairRootManager::Instance();
  if (!manager)
  {
    Fatal("Init()", "Can't find IOManager.");
    return kFATAL;
  }

  fStr=(ecalStructure*)manager->GetObject("EcalStructure");
  if (!fStr) 
  {
    Fatal("Init()", "Can't find calorimeter structure in the system.");
    return kFATAL;
  }
  
  return kSUCCESS;
}

void ecalDigi::InitPython(ecalStructure* structure)
{
  fStr=structure;
}

/** --- Executed task --------------------------------------------------------- **/ 
void ecalDigi::Exec(Option_t* option)
{
  ecalCell* cell;
  list<ecalCell*> cells;
  fStr->GetCells(cells);
  list<ecalCell*>::const_iterator p=cells.begin();
  Short_t adc;

  for(;p!=cells.end();++p)
  {
    cell=(*p);
    if (fChannelMap.empty())
      adc=(Short_t)(gRandom->Gaus(cell->GetEnergy(), fADCNoise)/fADCChannel+fPedestal);
    else
    if (fChannelMap.find(cell->GetCellNumber())==fChannelMap.end())
    {
      Error("Exec", "Channel %d not found in map. Using default value!", cell->GetCellNumber());
      //TODO: Should we insert Fatal here?
      adc=(Short_t)(gRandom->Gaus(cell->GetEnergy(), fADCNoise)/fADCChannel+fPedestal);
    }
    else
    {
      adc=(Short_t)(gRandom->Gaus(cell->GetEnergy(), fADCNoise)/fChannelMap[cell->GetCellNumber()]+fPedestal);
    }
    if (adc>fADCMax) adc=fADCMax;
    cell->SetEnergy(-1111);
    cell->SetADC(adc);
  }
}

/** --- Finish task ----------------------------------------------------------- **/ 
void ecalDigi::Finish()
{
  ;
}
/** --- Destructor ------------------------------------------------------------ **/
ecalDigi::~ecalDigi()
{
  ;
}

ClassImp(ecalDigi)
