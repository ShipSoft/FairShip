#include <iostream>
#include <algorithm>
#include <fstream>
#include <sstream>
#include <map>
#include <tuple>                // to return multiple values
#include <chrono>               // for time estimations
#include <ctime>
#include <string>
#include <stdint.h>
#include <stdlib.h>             // exit
#include <vector>
#include <algorithm>            // std::sort
#include <sys/stat.h>
#include "TKey.h"
#include "FairEventHeader.h"    // for FairEventHeader
#include "FairRunAna.h"         // for FairRunAna
#include "FairRootManager.h"    // for FairRootManager
#include "FairParamList.h"
#include "ConvRawData.h"
#include "TClonesArray.h"
#include "TObjString.h"
#include "TROOT.h"
#include "TList.h"
#include "TFile.h"
#include "TTree.h"
#include "TBranch.h"
#include "TLeaf.h"
#include "TH1F.h"
#include "TStopwatch.h"
#include "TSystem.h"
#include "SndlhcHit.h"
#include "Scifi.h"	        // for SciFi detector
#include "sndScifiHit.h"	// for SciFi Hit
#include "MuFilterHit.h"	// for Muon Filter Hit
#include "sndCluster.h"         // for Clusters
#include "TString.h"
#include "nlohmann/json.hpp"     // library to operate with json files
#include "boardMappingParser.h"  // for board mapping
#include "XrdCl/XrdClFile.hh"

using namespace std;
using namespace std::chrono;
using namespace XrdCl;


ConvRawData::ConvRawData()
    : FairTask("ConvRawData")
    , fEventTree(nullptr)
    , boards{}
    , fEventHeader(nullptr)
    , fDigiSciFi(nullptr)
    , fDigiMuFilter(nullptr)
    , fClusScifi(nullptr)
{}

ConvRawData::~ConvRawData() {}

InitStatus ConvRawData::Init()
{
    FairRootManager* ioman = FairRootManager::Instance();
    if (!ioman) {
        cout << "-E- ConvRawData::Init: "
                  << "RootManager not instantiated!" << endl;
        return kFATAL;
    }
        
    // Reading input - initiating parameters
    TObjString* runN_obj = dynamic_cast<TObjString*>(ioman->GetObject("runN"));
    TObjString* path_obj = dynamic_cast<TObjString*>(ioman->GetObject("path"));// maybe static?
    TObjString* nEvents_obj = dynamic_cast<TObjString*>(ioman->GetObject("nEvents"));
    TObjString* nStart_obj = dynamic_cast<TObjString*>(ioman->GetObject("nStart"));
    TObjString* debug_obj = dynamic_cast<TObjString*>(ioman->GetObject("debug"));
    TObjString* stop_obj = dynamic_cast<TObjString*>(ioman->GetObject("stop"));
    TObjString* heartBeat_obj = dynamic_cast<TObjString*>(ioman->GetObject("heartBeat"));
    TObjString* withGeoFile_obj = dynamic_cast<TObjString*>(ioman->GetObject("withGeoFile"));
    // Input raw data file is read from the FairRootManager
    // This allows to have it in custom format, e.g. have arbitary names of TTrees
    TFile* f0 = dynamic_cast<TFile*>(ioman->GetObject("rawData"));
    // Set run parameters
    std::istringstream(runN_obj->GetString().Data()) >> frunNumber;
    fpath = path_obj->GetString().Data();
    std::istringstream(nEvents_obj->GetString().Data()) >> fnEvents;
    std::istringstream(nStart_obj->GetString().Data()) >> fnStart;
    std::istringstream(debug_obj->GetString().Data()) >> debug;
    std::istringstream(stop_obj->GetString().Data()) >> stop;
    std::istringstream(heartBeat_obj->GetString().Data()) >> fheartBeat;
    std::istringstream(withGeoFile_obj->GetString().Data()) >> withGeoFile;
    
    fEventTree = (TTree*)f0->Get("event"); 
    // Get board_x data
    TIter next(f0->GetListOfKeys());
    TKey *b = new TKey();
    string name;
    while ((b = (TKey*)next()))
    {
     name = b->GetName();
     // string.find func: If no matches were found, the function returns string::npos.
     if ( name.find("board") == string::npos ) continue;
     boards[name] = (TTree*)f0->Get(name.c_str());
    }
     
    fEventHeader = new FairEventHeader();
    ioman->Register("EventHeader", "sndEventHeader", fEventHeader, kTRUE);
    fDigiSciFi    = new TClonesArray("sndScifiHit");
    ioman->Register("Digi_ScifiHits", "DigiScifiHit_det", fDigiSciFi, kTRUE);
    fDigiMuFilter = new TClonesArray("MuFilterHit");
    ioman->Register("Digi_MuFilterHits", "DigiMuFilterHit_det", fDigiMuFilter, kTRUE);
    //Scifi clusters
    fClusScifi = new TClonesArray("sndCluster");
    ScifiDet = dynamic_cast<Scifi*> (gROOT->GetListOfGlobals()->FindObject("Scifi") );
    if (withGeoFile)
    {    
      ioman->Register("Cluster_Scifi", "ScifiCluster_det", fClusScifi, kTRUE);
    }
    
    local = false; 
    
    struct stat buffer;  
    // Setting path to input data
    string set_path;
    if( fpath.find("eos") == string::npos || stat(fpath.c_str(), &buffer) == 0)
    {
      local = true;
      set_path = fpath; 
      cout<<"path to use: "<< set_path<<endl;
    }
    else
    {
      TString server = gSystem->Getenv("EOSSHIP");
      set_path = server.Data()+fpath; 
      cout<<"path to use: "<< set_path<<endl;
    }
 
    TStopwatch timerCSV;
    timerCSV.Start();
    read_csv(set_path);
    timerCSV.Stop();
    cout<<"Time to read CSV "<<timerCSV.RealTime()<<endl;
    //calibrationReport();
    TStopwatch timerBMap;
    timerBMap.Start();
    DetMapping(set_path);
    timerBMap.Stop();
    cout<<"Time to set the board mapping "<<timerBMap.RealTime()<<endl;
    
    eventNumber = fnStart-1;
    
    return kSUCCESS;
}

void ConvRawData::Exec(Option_t* /*opt*/)
{
  fDigiSciFi->Delete();
  fDigiMuFilter->Delete();
  fClusScifi->Delete();
    
  // Set number of events to process
  int indexSciFi{}, indexMuFilter{};
  bool scifi = false, mask = false;
  int board_id{};
  TTree* bt;
  int tofpet_id{}, tofpet_channel{}, tac{}, mat{};
  string station;
  double TDC{}, QDC{}, Chi2ndof{}, satur{};
  int A{};
  double B{};
  high_resolution_clock::time_point tE{}, t0{}, t1{}, t4{}, t5{}, t6{}, tt{};
  int system{}, key{}, sipmChannel{};
  string tmp;
  int nSiPMs{}, nSides{}, direction{}, detID{}, sipm_number{}, chan{}, orientation{}, sipmLocal{};
  int sipmID{};
  double test{};
  //TStopwatch timer;
      
  // Manually change event number as input file is not set for this task
  if (eventNumber > fnEvents)
  {
    cout<<"Check nEvents settings!"<< endl;
    exit(0);
  }
  eventNumber++;
  
  tE = high_resolution_clock::now();
  //timer.Start();
  fEventTree->GetEvent(eventNumber);
  if ( eventNumber%fheartBeat == 0 )
  {
     tt = high_resolution_clock::now();
     time_t ttp = high_resolution_clock::to_time_t(tt);
     cout << "run " << frunNumber << " event " << eventNumber
          << " local time " << ctime(&ttp) << endl;
  }
     
  fEventHeader->SetRunId(frunNumber);
  fEventHeader->SetEventTime(fEventTree->GetLeaf("evtTimestamp")->GetValue());
  if (debug) cout << "event: " << eventNumber << " timestamp: "
                  << fEventTree->GetLeaf("evtTimestamp")->GetValue() << endl;
  // Delete pointer map elements
  TStopwatch timerDel;
  timerDel.Start();
  for (auto it : digiSciFiStore)
  {
      delete it.second;
  }
  digiSciFiStore.clear();
  for (auto it : digiMuFilterStore)
  {
      delete it.second;
  }
  digiMuFilterStore.clear();
  timerDel.Stop();
  //cout<<timerDel.RealTime()<< " CPU "<< timerDel.CpuTime()<<endl;
     
  // Loop over boards
  for ( auto board : boards )// loop over TTrees
  { 
       board_id = stoi(board.first.substr(board.first.find("_")+1));
       scifi = true;
       if (boardMaps["Scifi"].count(board.first)!=0) 
       {
         for (auto it : boardMaps["Scifi"][board.first])
         {
           station = it.first;
           mat = it.second;
         }         
       }
       else if (boardMaps["MuFilter"].count(board.first)!=0) scifi = false;
       else
       {
         cout<<board.first<<" not known. Serious error, stop!"<<endl;
         break;
       }
       bt = boards[board.first];
       bt->GetEvent(eventNumber);
       // Loop over hits in event
       for ( int n = 0; n <  bt->GetLeaf("nHits")->GetValue(); n++ )
       {
         mask = false;
         if (debug) cout<< scifi << " " << board_id << " " << bt->GetLeaf("tofpetId")->GetValue(n)
                        << " " << bt->GetLeaf("tofpetChannel")->GetValue(n)
                        << " " << bt->GetLeaf("tac")->GetValue(n)
                        << " " << bt->GetLeaf("tCoarse")->GetValue(n)
                        << " " << bt->GetLeaf("tFine")->GetValue(n)
                        << " " << bt->GetLeaf("vCoarse")->GetValue(n)
                        << " " << bt->GetLeaf("vFine")->GetValue(n)<< endl;
         t0 = high_resolution_clock::now();
         tofpet_id = bt->GetLeaf("tofpetId")->GetValue(n);
         tofpet_channel = bt->GetLeaf("tofpetChannel")->GetValue(n);
         tac = bt->GetLeaf("tac")->GetValue(n);
         tie(TDC,QDC,Chi2ndof,satur) = comb_calibration(board_id, tofpet_id, tofpet_channel, tac,
                                                   bt->GetLeaf("vCoarse")->GetValue(n),
                                                   bt->GetLeaf("vFine")->GetValue(n),
                                                   bt->GetLeaf("tCoarse")->GetValue(n),
                                                   bt->GetLeaf("tFine")->GetValue(n),
                                                   1.0, 0);
         t1 = high_resolution_clock::now();
         if ( Chi2ndof > chi2Max )
         {
           if (QDC>1E20) QDC = 997.; // checking for inf
           if (QDC != QDC) QDC = 998.; // checking for nan
           if (QDC>0) QDC = -QDC;
           mask = true;
         }
         else if (satur > saturationLimit || QDC>1E20 || QDC != QDC)
         {
           if (QDC>1E20) QDC = 987.; // checking for inf
           if (debug) cout << "inf " << board_id << " " << bt->GetLeaf("tofpetId")->GetValue(n)    
                           << " " << bt->GetLeaf("tofpetChannel")->GetValue(n)
                           << " " << bt->GetLeaf("tac")->GetValue(n) 
                           << " " << bt->GetLeaf("vCoarse")->GetValue(n)
                           << " " << bt->GetLeaf("vFine")->GetValue(n)
                           << " " << TDC-bt->GetLeaf("tCoarse")->GetValue(n) 
                           << " " << eventNumber << " " << Chi2ndof << endl;
           if (QDC != QDC) QDC = 988.; // checking for nan
           if (debug) cout << "nan " << board_id << " " << bt->GetLeaf("tofpetId")->GetValue(n)
                           << " " << bt->GetLeaf("tofpetChannel")->GetValue(n)
                           << " " << bt->GetLeaf("tac")->GetValue(n)
                           << " " << bt->GetLeaf("vCoarse")->GetValue(n)
                           << " " << bt->GetLeaf("vFine")->GetValue(n)
                           << " " << TDC-bt->GetLeaf("tCoarse")->GetValue(n)
                           << " " << TDC << " " << bt->GetLeaf("tCoarse")->GetValue(n)
                           << " " << eventNumber << " " << Chi2ndof << endl;
           A = int(min(QDC,double(1000.)));
           B = min(satur,double(999.))/1000.;
           QDC = A+B;
           mask = true;
         }
         else if ( Chi2ndof > chi2Max )
         {
            if (QDC>0) QDC = -QDC;
            mask = true;
         }         
         if (debug) cout << "calibrated: tdc = " << TDC << ", qdc = " << QDC << endl;//TDC clock cycle = 160 MHz or 6.25ns
         t4 = high_resolution_clock::now();
         // Set the unit of the execution time measurement to ns
         counters["qdc"]+= duration_cast<nanoseconds>(t1 - t0).count();
         counters["make"]+= duration_cast<nanoseconds>(t4-t0).count();
         
         // MuFilter encoding
         if (!scifi)
         {
           system = MufiSystem[board_id][tofpet_id];
           key = (tofpet_id%2)*1000 + tofpet_channel;
           tmp = boardMapsMu["MuFilter"][board.first][slots[tofpet_id]];
           if (debug || !tmp.find("not") == string::npos )
           {
             cout << system << " " << key << " " << board.first << " " << tofpet_id
                            << " " << tofpet_id%2 << " " << tofpet_channel << endl;
           }
           sipmChannel = 99;
           if ( TofpetMap[system].count(key) == 0)
           {
                        cout << "key " << key << " does not exist. " << endl
                             << board.first << " Tofpet id " << tofpet_id
                             << " System " << system << " has Tofpet map elements: {";
                        for ( auto it : TofpetMap[system])
                        {
                          cout << it.first << " : " << it.second << ", ";
                        }
                        cout << "}\n";
           }
           else sipmChannel = TofpetMap[system][key]-1;
           
           nSiPMs = abs(offMap[tmp][1]);
           nSides = abs(offMap[tmp][2]);
           direction = int(offMap[tmp][1]/nSiPMs);
           detID = offMap[tmp][0] + direction*int(sipmChannel/nSiPMs);
           sipm_number = sipmChannel%(nSiPMs);
           if ( tmp.find("Right") != string::npos ) sipm_number+= nSiPMs;
           if (digiMuFilterStore.count(detID)==0) 
           {
 	     digiMuFilterStore[detID] = new MuFilterHit(detID,nSiPMs,nSides);
           }
           test = digiMuFilterStore[detID]->GetSignal(sipm_number);
           digiMuFilterStore[detID]->SetDigi(QDC,TDC,sipm_number);
           if (mask) digiMuFilterStore[detID]->SetMasked(sipm_number);
           
           if (debug)
           {
                    cout << "create mu hit: " << detID << " " << tmp << " " << system
                         << " " << tofpet_id << " " << offMap[tmp][0] << " " << offMap[tmp][1]
                         << " " << offMap[tmp][2] << " " << sipmChannel << " " << nSiPMs
                         << " " << nSides << " " << test << endl;
                    cout << "  " << detID << " " << sipm_number << " " << QDC << " " << TDC <<endl;
           }
           if (test>0 || detID%1000>200 || sipm_number>15)
           {
             cout << "what goes wrong? " << detID << " SiPM " << sipm_number << " system " << system
                  << " key " << key << " board " << board.first << " tofperID " << tofpet_id
                  << " tofperChannel " << tofpet_channel << " test " << test << endl;
           }
           t5 = high_resolution_clock::now();
           counters["createMufi"]+= duration_cast<nanoseconds>(t5 - t4).count();
         } // end MuFilter encoding
         
         else // now Scifi encoding
         {
           chan = channel_func(tofpet_id, tofpet_channel, mat);
           orientation = 1;
           if (station[2]=='Y') orientation = 0;
           sipmLocal = (chan - mat*512);
           sipmID = 1000000*int(station[1]-'0') + 100000*orientation + 10000*mat
                                            + 1000*(int(sipmLocal/128)) + chan%128;
           if (digiSciFiStore.count(sipmID)==0)
           {
             digiSciFiStore[sipmID] =  new sndScifiHit(sipmID);             
           }
           digiSciFiStore[sipmID]->SetDigi(QDC,TDC);
           if (mask) digiSciFiStore[sipmID]->setInvalid();
           if (debug)
           {
              cout << "create scifi hit: tdc = " << board.first << " " << sipmID
                   << " " << QDC << " " << TDC <<endl;
              cout << "tofpet:" << " " << tofpet_id << " " << tofpet_channel << " " << mat
                   << " " << chan << endl
                   << station[1] << " " << station[2] << " " << mat << " " << chan
                   << " " << int(chan/128)%4 << " " << chan%128 << endl;
           }
           t5 = high_resolution_clock::now();
           counters["createScifi"]+= duration_cast<nanoseconds>(t5 - t4).count();
         } // end Scifi encoding
       } // end loop over hits in event
  } // end loop over boards (TTrees in data file)

  counters["N"]+= 1;
  t6 = high_resolution_clock::now();
  for (auto it_sipmID : digiSciFiStore)
  {
    (*fDigiSciFi)[indexSciFi]=digiSciFiStore[it_sipmID.first];
    indexSciFi+= 1;
  }
  for (auto it_detID : digiMuFilterStore)
  {
    (*fDigiMuFilter)[indexMuFilter]=digiMuFilterStore[it_detID.first];
    indexMuFilter+= 1;
  }
  counters["storage"]+= duration_cast<nanoseconds>(high_resolution_clock::now() - t6).count();
  counters["event"]+= duration_cast<nanoseconds>(high_resolution_clock::now() - tE).count();
  //timer.Stop();
  //cout<<timer.RealTime()<<endl;
    
  /* 
    Make simple clustering for scifi, only works with geometry file. 
    Don't think it is a good idea at the moment.
  */
  if (withGeoFile)
  {
    map<int, int > hitDict{};
    vector<int> hitList{};
    vector<int> tmpV{};
    int index{}, ncl{}, cprev{}, c{}, last{}, first{}, N{};
    for (int k = 0, kEnd = fDigiSciFi->GetEntries(); k < kEnd; k++)
    {
        sndScifiHit* d = static_cast<sndScifiHit*>(fDigiSciFi->At(k));
        if (!d->isValid()) continue;
        hitDict[d->GetDetectorID()] = k ;
        hitList.push_back(d->GetDetectorID());
    }
    if (hitList.size() > 0)
    {
        sort(hitList.begin(), hitList.end());
        tmpV.push_back(hitList[0]);
        cprev = hitList[0];
        ncl = 0;
        last = hitList.size()-1;
        vector<sndScifiHit*> hitlist{};
        for (unsigned int i =0; i<hitList.size(); i++)
        {
          if (i==0 && hitList.size()>1) continue;
          c = hitList[i];
          if (c-cprev ==1) tmpV.push_back(c);
          if (c-cprev !=1 || c==hitList[last])
          {
            first = tmpV[0];
            N = tmpV.size();
            hitlist.clear();
            for (unsigned int j=0; j<tmpV.size(); j++)
            {
              sndScifiHit* aHit = static_cast<sndScifiHit*>(fDigiSciFi->At(hitDict[tmpV[j]]));
              hitlist.push_back(aHit);
            }
            new ((*fClusScifi)[index]) sndCluster(first, N, hitlist, ScifiDet);
            index++;
            if (c!=hitList[last])
            {
              ncl++;
              tmpV.clear();
              tmpV.push_back(c);
            }
          }
          cprev = c;
        }
    }
  } // end if (withGeoFile)
  if (debug)
  {
    cout << "number of events processed " << fnEvents << " "
         << fEventTree->GetEntries()<< endl;
  }
  /*
  cout << "Monitor computing time:" << endl;
  for (auto it: counters)
  {
     if( it.first=="N" )
     {
       cout << "Processed " << it.first<< " = " << it.second << " events." << endl;
     }
     else
     {
       // Print execution time in seconds
       cout << "stage " << it.first<< " took " << it.second*1e-9 << " [s]" << endl;
     }
  }
  */

}
  
/* https://gitlab.cern.ch/snd-scifi/software/-/wikis/Raw-data-format 
      tac: 0-3, identifies the Time-To-Analogue converter used for this hit (each channel has four of them and they require separate calibration).
      t_coarse: Coarse timestamp of the hit, running on a 4 times the LHC clock
      t_fine: 0-1023, fine timestamp of the hit. It contains the raw value of the charge digitized by the TDC and requires calibration.
      v_coarse: 0-1023, QDC mode: it represents the number of clock cycles the charge integration lasted.
      v_fine = 0-1023, QDC mode: represents the charge measured. Requires calibration.
*/

/** Board mapping for Scifi and MuFilter **/
void ConvRawData::DetMapping(string Path)
{
  nlohmann::json j;
  // reading file with xrootd protocol
  File file;
  XRootDStatus status;
  StatInfo *info;
  uint64_t offset = 0;
  uint32_t size;
  uint32_t bytesRead = 0;
  // Call boardMappingParser
  if (local)
  {
    ifstream jsonfile(Form("%s/board_mapping.json", Path.c_str()));      
    jsonfile >> j;
  }
  else
  {
    status = file.Open(Form("%s/board_mapping.json", Path.c_str()), OpenFlags::Read);
    if( !status.IsOK() )
    {
      cout << "Error opening file\n";
      exit(0);
    }
    file.Stat(false, info);
    size = info->GetSize();
    char *buff = new char[size];
    status = file.Read(offset, size, buff, bytesRead);
    vector<char> vec;
    for (int i = 0; i < size; i++){vec.push_back(buff[i]);}
    j = json::parse(vec);
    status = file.Close();
    delete info;
    delete [] buff;    
  }
  // Pass the read string to getBoardMapping()
  tie(boardMaps, boardMapsMu) = getBoardMapping(j);
  
  int board_id_mu{}, s{};
  string tmp;
  for ( auto it : boardMapsMu["MuFilter"] )
  {
     board_id_mu = stoi(it.first.substr(it.first.find("_") + 1));
     for ( auto x : boardMapsMu["MuFilter"][it.first] )
     {
       for ( auto slot : slots )
       {
         s = 0;
         tmp = x.second.substr(0, x.second.find("_"));
         if ( tmp =="US" ) s = 1;
         if ( tmp=="DS" ) s = 2;
         if ( slots[slot.first] == x.first )
         {
            MufiSystem[board_id_mu][slot.first] = s;
            boardMaps["MuFilter"][it.first][slot.second] = slot.first;
         }
       }
     }
  }
  
  //string o;
  for (int i = 1 ; i < 6; i++ )
  {
    if (i<3)
    {
      offMap[Form("Veto_%iLeft",i)]  = {10000 + (i-1)*1000+ 0, 8, 2};//first channel, nSiPMs, nSides
      offMap[Form("Veto_%iRight",i)] = {10000 + (i-1)*1000+ 0, 8, 2};
    }
    if (i<4)
    {
      // DS
      offMap[Form("DS_%iLeft",i)]  = {30000 + (i-1)*1000+ 59, -1, 2};// direction not known
      offMap[Form("DS_%iRight",i)] = {30000 + (i-1)*1000+ 59, -1, 2};// direction not known
    }
    if (i<5)
    {
      offMap[Form("DS_%iVert",i)] = {30000 + (i-1)*1000+ 119, -1, 1};// direction not known
    }
    offMap[Form("US_%iLeft",i)]  = {20000 + (i-1)*1000+ 9, -8, 2}; // from top to bottom
    offMap[Form("US_%iRight",i)] = {20000 + (i-1)*1000+ 9, -8, 2};
  }  
}
/* Define calibration functions **/
double ConvRawData::qdc_calibration( int board_id, int tofpet_id, int channel,
                       int tac, uint16_t v_coarse, uint16_t v_fine, uint16_t tf )
  {
    double GQDC = 1.0; // or 3.6
    map<string, double> par= X_qdc[{board_id,tofpet_id,channel,tac}];
    double x = v_coarse - tf;
    double fqdc = -par["c"]*log(1+exp( par["a"]*pow((x-par["e"]),2)
                 -par["b"]*(x-par["e"]) )) + par["d"];
    double value = (v_fine-fqdc)/GQDC;
    return value;
}
double ConvRawData::qdc_chi2( int board_id, int tofpet_id, int channel, int tac, int TDC=0 )
{
    map<string, double> par = X_qdc[{board_id,tofpet_id,channel,tac}];
    map<string, double> parT = X_tdc[{board_id,tofpet_id,channel,tac, TDC}];
    return max(par["chi2Ndof"],parT["chi2Ndof"]);
}
double ConvRawData::qdc_sat( int board_id, int tofpet_id, int channel, int tac, uint16_t v_fine )
{
    map<string, double> par = X_qdc[{board_id,tofpet_id,channel,tac}];
    return v_fine/par["d"];  
}
double ConvRawData::time_calibration( int board_id, int tofpet_id, int channel,
                        int tac, int64_t t_coarse, uint16_t t_fine, int TDC=0 )
{
    map<string, double> parT = X_tdc[{board_id,tofpet_id,channel,tac, TDC}];
    double x = t_fine;
    double ftdc = (-parT["b"]-sqrt(pow(parT["b"],2)
                  -4*parT["a"]*(parT["c"]-x)))/(2*parT["a"]);
    double timestamp = t_coarse+ftdc;
    return timestamp;
}
tuple<double, double, double, double> ConvRawData::comb_calibration( int board_id, int tofpet_id, int channel,int tac, uint16_t v_coarse, uint16_t v_fine,int64_t t_coarse, uint16_t t_fine, double GQDC = 1.0, int TDC=0 )// max gain QDC = 3.6
{
    map<string, double> par= X_qdc[{board_id,tofpet_id,channel,tac}];
    map<string, double> parT = X_tdc[{board_id,tofpet_id,channel,tac,TDC}];
    double x    = t_fine;
    double ftdc = (-parT["b"]-sqrt(pow(parT["b"],2)
                  -4*parT["a"]*(parT["c"]-x)))/(2*parT["a"]); // Ettore 28/01/2022 +par['d']
    double timestamp = t_coarse + ftdc;
    double tf = timestamp - t_coarse;
    x = v_coarse - tf;
    double fqdc = - par["c"]*log(1+exp( par["a"]*pow((x-par["e"]),2)-par["b"]*(x-par["e"]) ))
                 + par["d"];
    double value = (v_fine-fqdc)/GQDC;
    return make_tuple(timestamp,value,max(par["chi2Ndof"],parT["chi2Ndof"]),v_fine/par["d"]);
}
map<double, pair<double, double> > ConvRawData::calibrationReport()
{
    TH1F* h = new TH1F("chi2","chi2", 1000, 0., 10000);
    map<double, pair<double, double> > report{};
    int TDC = 0;
    double chi2{}, chi2T{}, key{};
    // loop over entries of X_qdc and get map keys
    for (auto it : X_qdc)
    {
      map<string, double> par= X_qdc[{it.first[0], it.first[1], it.first[2], it.first[3]}];
      if (par["chi2Ndof"]) chi2 = par["chi2Ndof"];
      else chi2 = -1;
      map<string, double> parT = X_tdc[{it.first[0], it.first[1], it.first[2], it.first[3], TDC}];
      if (parT["chi2Ndof"]) chi2T = parT["chi2Ndof"];
      else chi2T = -1;
      key = it.first[3] +10*it.first[2] + it.first[1]*10*100 + it.first[0]*10*100*100;
      if (report.count(key)==0) report[key] = make_pair(chi2,chi2T);
    }
    for (auto it : report)
    {
         h->Fill(report[it.first].first);
         h->Fill(report[it.first].second);
    }
    h->Draw();
    return report;
}
/** Define some other functions **/
int ConvRawData::channel_func( int tofpet_id, int tofpet_channel, int position)
{
    return (64*tofpet_id + 63 - tofpet_channel + 512*position);// 512 channels per mat, 1536 channels per plane. One channel covers all 6 layers of fibres.
}
/** Read csv data files **/
void ConvRawData::read_csv(string Path)
{
  ifstream infile; // ifstream is the stream class to only read! from files.
  stringstream X;
  // reading file with xrootd protocol
  File file;
  XRootDStatus status;
  StatInfo *info;
  uint64_t offset = 0;
  uint32_t size;
  uint32_t bytesRead = 0;
  
  string line, element;
  double chi2_Ndof{};
  // counter of number of elements
  vector<int> key_vector{};
  
  // Get QDC calibration data
  if (local)
  {
   infile.open(Form("%s/qdc_cal.csv", Path.c_str()));
   X << infile.rdbuf();
   infile.close();
  }
  else
  {
    status = file.Open(Form("%s/qdc_cal.csv", Path.c_str()), OpenFlags::Read);
    if( !status.IsOK() )
    {
      cout << "Error opening file\n";
      exit(0);
    }
    file.Stat(false, info);
    size = info->GetSize();
    char *buff = new char[size];
    status = file.Read(offset, size, buff, bytesRead);
    X << buff;
    status = file.Close();
    delete info;
    delete [] buff;  
  }
  cout<<"Read_csv "<<Path.c_str()<<endl;
  // Skip 1st line
  getline(X, line);
  cout << "In QDC cal file: " << line << endl;
  vector<double> qdcData{};
  // Read all other lines
  while (getline(X, line))
  {    
    qdcData.clear();
    stringstream items(line);
    while (getline(items, element, ','))
    {
      if(iscntrl(element[0])) break;
      qdcData.push_back(stof(element));
    }
    if (qdcData.size()<10) continue;
    key_vector.clear();
    key_vector = {int(qdcData[0]), int(qdcData[1]), int(qdcData[2]), int(qdcData[3])};
    chi2_Ndof = (qdcData[9] < 2) ? 999999. : qdcData[7]/qdcData[9]; 
    X_qdc[key_vector] = { {"a",qdcData[4]}, {"b",qdcData[5]}, {"c",qdcData[6]},
                          {"d",qdcData[8]}, {"e",qdcData[10]}, {"chi2Ndof",chi2_Ndof} };
    if (X.peek() == EOF) break;
  }
  X.str(string()); X.clear(); line.clear();
  size = 0; offset = 0; bytesRead = 0;
  // Get TDC calibration data
  if (local)
  {
   infile.open(Form("%s/tdc_cal.csv", Path.c_str()));
   X << infile.rdbuf();
   infile.close();
  }
  else
  {
    status = file.Open(Form("%s/tdc_cal.csv", Path.c_str()), OpenFlags::Read);
    if( !status.IsOK() )
    {
      cout << "Error opening file\n";
      exit(0);
    }
    file.Stat(false, info);
    size = info->GetSize();
    char *buff = new char[size];
    status = file.Read(offset, size, buff, bytesRead);
    X << buff;
    status = file.Close();
    delete info;
    delete [] buff;
  }
  // Skip 1st line
  getline(X, line);
  cout << "In TDC cal file: " << line << endl;
  vector<double> tdcData{};
  // Read all other lines
  while (getline(X, line))
  {
    tdcData.clear();
    stringstream items(line);
    if (line.length()<5){continue;}
    while (getline(items, element, ','))
    {
      if(iscntrl(element[0])) break;
      tdcData.push_back(stof(element));
    }
    if (tdcData.size()<9) continue;
    key_vector.clear();
    key_vector = {int(tdcData[0]), int(tdcData[1]), int(tdcData[2]), int(tdcData[3]), int(tdcData[4])};
    chi2_Ndof = (tdcData[10] < 2) ? 999999. : tdcData[8]/tdcData[10]; 
    X_tdc[key_vector] = { {"a",tdcData[5]}, {"b",tdcData[6]}, {"c",tdcData[7]},
                          {"d",tdcData[9]}, {"chi2Ndof",chi2_Ndof} };
    if (X.peek() == EOF) break;
  }
  X.str(string()); X.clear(); line.clear();
  size = 0; offset = 0; bytesRead = 0;
  
  int SiPM{};
  vector<int> data_vector{};
  map<string, map<int, vector<int>> > SiPMmap{};
  vector<int> row{};
  map<string, int> key { {"DS",2}, {"US",1}, {"Veto",0} };
  struct stat buffer;
  TString sndRoot = gSystem->Getenv("SNDSW_ROOT");
  string sndswPath = sndRoot.Data();
  string path_SiPMmap = Form("%s/geometry", sndswPath.c_str());
  if (stat(path_SiPMmap.c_str(), &buffer) != 0)
  {
    cout << "Path "<< path_SiPMmap.c_str() << " does not exist!\n";
    exit (0); 
  }
  for (auto sys : key)
  {
    infile.open(Form("%s/%s_SiPM_mapping.csv", path_SiPMmap.c_str(), sys.first.c_str()));
    X << infile.rdbuf();
    infile.close();
          
    // Skip 1st line
    getline(X,line);
    cout << "In " << sys.first << " SiPM map file: " << line << endl;
    // Read all other lines
    while (getline(X,line))
    {
        data_vector.clear();
        stringstream items(line);
        // first element in line is SiPM
        getline(items, element, ',');
        SiPM = stoi(element);
        // only taking first few elements of line
        while (data_vector.size()<4 && getline(items, element, ',')) 
        {
           data_vector.push_back(stoi(element));
        }
        SiPMmap[sys.first][SiPM] = data_vector;
        if (X.peek() == EOF) break;
    }
    X.str(string()); X.clear(); line.clear();
    size = 0; offset = 0; bytesRead = 0;
    for (auto channel : SiPMmap[sys.first])
    {
      row = channel.second;
      TofpetMap[sys.second][row.at(2)*1000+row.at(3)] = channel.first;
    }
  } // end filling SiPMmap and TofpetMap
}
void ConvRawData::debugMapping(string brd, int tofpetID, int tofpetChannel)
{
  int Key{}, SiPMChannel{}, n_SiPMs{}, n_Sides{}, Direction{}, DetID{}, SiPM_number{};
  string Tmp;
  int brdID{}, System{};
  Key = (tofpetID%2)*1000 + tofpetChannel;
  Tmp = boardMapsMu["MuFilter"][brd][slots[tofpetID]];
  brdID = stoi(brd.substr(brd.find("_")+1));
  System = MufiSystem[brdID][tofpetID];
  SiPMChannel = TofpetMap[System][Key]-1;
  n_SiPMs = abs(offMap[Tmp][1]);
  n_Sides = abs(offMap[Tmp][2]);
  Direction = int(offMap[Tmp][1]/n_SiPMs);
  DetID = offMap[Tmp][0] + Direction*int(SiPMChannel/n_SiPMs);
  SiPM_number = SiPMChannel%(n_SiPMs);
  cout << "SiPM channel " << SiPMChannel << " nSiPM " << n_SiPMs << " nSides " << n_Sides
       << " detID " << DetID << " SiPM number " << SiPM_number << endl;
}

ClassImp(ConvRawData);
