// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

#ifndef STRAWTUBES_TRACKLET_H_
#define STRAWTUBES_TRACKLET_H_
#include "TObject.h"

#include <stddef.h>
#include <vector>
#include "Rtypes.h"                     // for Double_t, Int_t, Double32_t, etc

class strawtubesHit;
class strawtubesPoint;

/**
 *@author Thomas Ruf
 **
 ** Simple class to describe a tracklet
 ** list of indices pointing to strawtubesHit objects in the digiStraw container

 **/

class Tracklet: public TObject
{
  public:
    /** Default constructor **/
    Tracklet();

    /** Constructor with hit indices **/
    Tracklet(Int_t f, const std::vector<unsigned int>& indices);

    /** Constructor with hits (extracts indices from container) **/
    Tracklet(Int_t f, const std::vector<strawtubesHit>& hits, const std::vector<strawtubesHit>& container);

    /** Destructor **/
    virtual ~Tracklet();

    std::vector<unsigned int>* getList(){return &aTracklet;}
    const std::vector<unsigned int>& getIndices() const {return aTracklet;}
    Int_t getType() const {return flag;}
    void setType(Int_t f){flag=f;}
    Int_t link2MCTrack(std::vector<strawtubesPoint>* strawPoints, Float_t min);   // give back MCTrack ID with max matched strawtubesHits

/*** Output to screen */
    virtual void Print(const Option_t* opt ="") const {;}

  protected:
    std::vector<unsigned int>  aTracklet;         ///< list of indices
    Int_t flag; // reserved for type of tracklet  ///< type of tracklet
    ClassDef(Tracklet,2);

};

#endif  // STRAWTUBES_TRACKLET_H_
