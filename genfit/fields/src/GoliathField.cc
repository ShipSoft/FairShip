/* Copyright 2008-2010, Technische Universitaet Muenchen,
   Authors: Christian Hoeppner & Sebastian Neubert & Johannes Rauch

   This file is part of GENFIT.

   GENFIT is free software: you can redistribute it and/or modify
   it under the terms of the GNU Lesser General Public License as published
   by the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   GENFIT is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU Lesser General Public License for more details.

   You should have received a copy of the GNU Lesser General Public License
   along with GENFIT.  If not, see <http://www.gnu.org/licenses/>.
   
   This file should stay in sync with charmdet/MuonfluxSpectrometer.cxx and charmdet/Spectrometer.cxx.
   It is used for fitting reconstructed tracks. After instantiating in shipDigiReco.py call setup():
   
   self.bfield = ROOT.genfit.GoliathField(0 ,1.*u.tesla,0)
   self.bfield.setup() 
   
   Contact EvH for help if necessary.
*/
#include "GoliathField.h" 
#include "TGeoNavigator.h"              
#include "TGeoNode.h"
#include "TGeoManager.h"
#include "TGeoBBox.h"
#include "TVector3.h"

#include <stddef.h>                     // for NULL
#include <iostream>                     // for operator<<, basic_ostream, etc

using std::cout;
using std::endl;
using std::vector;

namespace genfit {

TVector3 GoliathField::get(const TVector3&) const {
  return field_;
}

void  GoliathField::get(const double& posX, const double& posY, const double& posZ, double& Bx, double& By, double& Bz) const {
  Bx=0.;By=0.;Bz=0.;
  if ((posX < coords[0][0]) && (posX > coords[0][3]) && (posY < coords[0][1]) && (posY > coords[0][4]) && (posZ < coords[0][2]+5.) && (posZ>coords[0][5]+5.) ) {
     Bx = field_.X();
     By = field_.Y();
     Bz = field_.Z(); 
  }
  else {
    for (Int_t i=1;i<13;i++){  
     if ((posX < coords[i][0]) && (posX > coords[i][3]) && (posY < coords[i][1]) && (posY > coords[i][4]) && (posZ < coords[i][2]) && (posZ>coords[i][5])) {
       Bx = 0.;
       By = -10.;
       Bz = 0.; 
       break;      
     }      
    } 
  } 
}


void GoliathField::getpos(TString volname, TVector3 &vbot, TVector3 &vtop) const {
   TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
   Bool_t rc = nav->cd(volname);
   if (not rc){
       cout << "Goliathfield::getpos, TGeoNavigator failed "<<volname<<endl; 
       return;
   }  
   TGeoNode* W = nav->GetCurrentNode();
   TGeoBBox* S = dynamic_cast<TGeoBBox*>(W->GetVolume()->GetShape());
   Double_t top[3] = {S->GetDX(),S->GetDY(),S->GetDZ()};
   Double_t bot[3] = {-S->GetDX(),-S->GetDY(),-S->GetDZ()};
   Double_t Gtop[3],Gbot[3];
   nav->LocalToMaster(top, Gtop);
   nav->LocalToMaster(bot, Gbot);
   vtop.SetXYZ(Gtop[0],Gtop[1],Gtop[2]);
   vbot.SetXYZ(Gbot[0],Gbot[1],Gbot[2]);
}

void GoliathField::setup(){
  TVector3 bot,top;
  std::vector<TString> volume={"/volGoliath_1/VolVacuum_1","/volGoliath_1/volLateralS1_1","/volGoliath_1/volLateralS2_1","/volGoliath_1/volLateralSurface1low_1",
  "/volGoliath_1/volLateralSurface2low_1","/volGoliath_1/volLateralS1_b_1","/volGoliath_1/volLateralS2_b_1","/volGoliath_1/volLateralSurface1blow_1",
  "/volGoliath_1/volLateralSurface2blow_1","/volGoliath_1/volLateralS1_d_1","/volGoliath_1/volLateralS2_d_1","/volGoliath_1/volLateralS1_c_1",
  "/volGoliath_1/volLateralS2_c_1"};
  for (Int_t i=0;i<13;i++){
    getpos(volume[i],bot,top);
    for (Int_t j=0;j<3;j++) {
      coords[i][j]=top[j];
      coords[i][j+3]=bot[j];        
    }
    //std::cout<<volume[i]<<" "<<coords[i][3] << " posX " << posX <<" "<< coords[i][0] << ";" << coords[i][4] << " posY "<< posY <<" "<<  coords[i][1] << ";" << coords[i][5] << " posZ " << posZ<<" "<< coords[i][2]<<std::endl; 
  }
}


} /* End of namespace genfit */

