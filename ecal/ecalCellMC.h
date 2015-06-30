/**  ecalCellMC.h
 *@author Mikhail Prokudin
 **
 ** ECAL cell structure, a part of ECAL module. This implementation carries an MC information
 **/

#ifndef ECALCELLMC_H
#define ECALCELLMC_H

/* $Id: ecalCellMC.h,v 1.9 2012/01/18 18:15:23 prokudin Exp $ */

#include "ecalCell.h"

#include <list>
#include <map>
#include <algorithm>

class ecalCellMC : public ecalCell
{
public:
  ecalCellMC(Int_t cellnumber, Float_t x1=0, Float_t y1=0, Float_t x2=0, Float_t y2=0, Char_t type=0, Float_t energy=0);

  Float_t GetTrackEnergy(Int_t num) const;
  Float_t GetTrackTime(Int_t num) const;
	
  /** Reset all energies in cell **/
  void ResetEnergy();
	
  inline void SetTrackEnergy(Int_t num, Float_t energy, Float_t time=-1111)
  {fTrackEnergy[num]=energy; fTrackTime[num]=time; }
  inline void AddTrackEnergy(Int_t num, Float_t energy, Float_t time=-1111)
  {
    fTrackEnergy[num]+=energy;
    if (time==-1111) return;
    std::map<Int_t, Float_t>::const_iterator p=fTrackTime.find(num);
    if (p==fTrackTime.end()) fTrackTime[num]=time;
    else
      if (fTrackTime[num]>time) fTrackTime[num]=time;
  }
  // same for tracks
  Float_t GetTrackClusterEnergy(Int_t num);

  // For python users 
  Int_t TrackEnergySize() const {return fTrackEnergy.size();}
  Int_t TrackTimeSize() const {return fTrackEnergy.size();}
  // Don't use slow methods except in emergency!!!
  void GetTrackEnergySlow(Int_t n, Int_t& trackid, Double_t& energy_dep);
  void GetTrackTimeSlow(Int_t n, Int_t& trackid, Float_t& time);

  inline std::map<Int_t, Float_t>::const_iterator GetTrackEnergyBegin() const
	 {return fTrackEnergy.begin();}
  inline std::map<Int_t, Float_t>::const_iterator GetTrackEnergyEnd() const
	 {return fTrackEnergy.end();}

  inline std::map<Int_t, Float_t>::const_iterator GetTrackTimeBegin() const
	 {return fTrackTime.begin();}
  inline std::map<Int_t, Float_t>::const_iterator GetTrackTimeEnd() const
	 {return fTrackTime.end();}

private:
  /**  map<TrackId, Energy in ECAL> **/
  std::map<Int_t, Float_t> fTrackEnergy;

  /** map<TrackId, Time in ECAL>**/
  std::map<Int_t, Float_t> fTrackTime;

  ClassDef(ecalCellMC,1);
};
  

#endif
