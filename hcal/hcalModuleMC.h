/**  hcalModuleMC.h
 *@author Mikhail Prokudin
 **
 ** hcalModule module. This implementation carries an MC information
 **/

#ifndef HCALMODULEMC_H
#define HCALMODULEMC_H

/* $Id: hcalModuleMC.h,v 1.9 2012/01/18 18:15:23 prokudin Exp $ */

#include "hcalModule.h"

#include <list>
#include <map>
#include <algorithm>

class hcalModuleMC : public hcalModule
{
public:
  hcalModuleMC(Int_t number, Float_t x1=0, Float_t y1=0, Float_t x2=0, Float_t y2=0);

  Float_t GetTrackEnergy(Int_t num) const;
  Float_t GetTrackEnergy2(Int_t num) const;
	
  /** Reset all energies in module **/
  void ResetEnergy();
	
  inline void SetTrackEnergy(Int_t num, Float_t energy)
    { fTrackEnergy[num]=energy; }
  inline void AddTrackEnergy(Int_t num, Float_t energy)
    { fTrackEnergy[num]+=energy;}

  inline void SetTrackEnergy2(Int_t num, Float_t energy)
    { fTrackEnergy2[num]=energy; }
  inline void AddTrackEnergy2(Int_t num, Float_t energy)
    { fTrackEnergy2[num]+=energy;}
  
  // same for tracks
  Float_t GetTrackClusterEnergy(Int_t num);

  inline std::map<Int_t, Float_t>::const_iterator GetTrackEnergyBegin() const
	 {return fTrackEnergy.begin();}
  inline std::map<Int_t, Float_t>::const_iterator GetTrackEnergyEnd() const
	 {return fTrackEnergy.end();}

  inline std::map<Int_t, Float_t>::const_iterator GetTrackEnergy2Begin() const
	 {return fTrackEnergy2.begin();}
  inline std::map<Int_t, Float_t>::const_iterator GetTrackEnergy2End() const
	 {return fTrackEnergy2.end();}

private:
  /**  map<TrackId, Energy in first HCAL section> **/
  std::map<Int_t, Float_t> fTrackEnergy;

  /**  map<TrackId, Energy in second HCAL section> **/
  std::map<Int_t, Float_t> fTrackEnergy2;

  ClassDef(hcalModuleMC,1);
};
  

#endif
