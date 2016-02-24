#include "pid.h"

#include <algorithm>
#include <iostream>

using namespace std;

pid::pid()
  : TObject(),
    fTrackID(0),            //!  track index
    fElectronID(0),         //!  electron id
    fHadronID(0),           //!  hadron id
    fMuonID(0)             //!  muon id
{
//   std::cout<<"create"<<std::endl;
}

pid::~pid()
{
//   std::cout<<"delete"<<std::endl;
}

