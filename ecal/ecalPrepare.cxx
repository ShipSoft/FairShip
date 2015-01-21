#include "ecalPrepare.h"

#include "ecalStructure.h"

#include "FairRootManager.h"

#include "TRandom.h"
#include "TSystem.h"

#include <iostream>
#include <fstream>
#include <list>

using namespace std;

/** --- Default constructor --------------------------------------------------- **/
ecalPrepare::ecalPrepare() 
  : FairTask(),
    fPedestal(80),
    fADCMax(16384),
    fADCChannel(1.0e-3),
    fStr(NULL), fChannelMap()
{
  fChannelMap.clear();
}

/** --- Standard constructor. Use this ---------------------------------------- **/
ecalPrepare::ecalPrepare(const char* name, Int_t iVerbose)
  : FairTask(name, iVerbose),
    fPedestal(80),
    fADCMax(16384),
    fADCChannel(1.0e-3),
    fStr(NULL), fChannelMap()
{
  fChannelMap.clear();
}

/** --- Ugly load of map channel number -> ADC channel from the file ---------- **/
void ecalPrepare::LoadChannelMap(const char* filename)
{
  map<Int_t, Float_t> tmp;
  TString fname=filename;	gSystem->ExpandPathName(fname);
  ifstream f(filename);
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
InitStatus ecalPrepare::Init()
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

void ecalPrepare::InitPython(ecalStructure* structure)
{
  fStr=structure;
}

/** --- Executed task --------------------------------------------------------- **/ 
void ecalPrepare::Exec(Option_t* option)
{
  ecalCell* cell;
  list<ecalCell*> cells;
  fStr->GetCells(cells);
  list<ecalCell*>::const_iterator p=cells.begin();
  Short_t adc;

  for(;p!=cells.end();++p)
  {
    cell=(*p);
    adc=cell->GetADC();
    adc-=fPedestal; //if (adc<0) adc=0;
    if (fChannelMap.empty())
      cell->SetEnergy(adc*fADCChannel);
    else
    if (fChannelMap.find(cell->GetCellNumber())==fChannelMap.end())
    {
      Error("Exec", "Channel %d not found in map. Using default value!", cell->GetCellNumber());
      //TODO: Should we insert Fatal here?
      cell->SetEnergy(adc*fADCChannel);
    }
    else
    {
      cell->SetEnergy(adc*fChannelMap[cell->GetCellNumber()]);
    }
  }
}

/** --- Finish task ----------------------------------------------------------- **/ 
void ecalPrepare::Finish()
{
  ;
}
/** --- Destructor ------------------------------------------------------------ **/
ecalPrepare::~ecalPrepare()
{
  ;
}

ClassImp(ecalPrepare)
