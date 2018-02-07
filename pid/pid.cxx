#include "pid.h"

#include <algorithm>
#include <iostream>

using namespace std;

pid::pid()
  : TObject(),
    fTrackID(-999),            //!  track index
    fElectronID(-999),         //!  electron id
    fHadronID(-999),           //!  hadron id
    fMuonID(-999),             //!  muon id
    fTrackPID(-999)            //!  track pid 
{
//   std::cout<<"create"<<std::endl;
}

pid::~pid()
{
//   std::cout<<"delete"<<std::endl;
}

