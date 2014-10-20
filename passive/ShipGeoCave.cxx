/////////////////////////////////////////////////////////////
// ShipGeoCave
//
// Class for the geometry of the detector part CAVE
//
/////////////////////////////////////////////////////////////

#include "ShipGeoCave.h"

#include "FairGeoBasicShape.h"          // for FairGeoBasicShape
#include "FairGeoMedia.h"               // for FairGeoMedia
#include "FairGeoMedium.h"              // for FairGeoMedium
#include "FairGeoNode.h"                // for FairGeoNode, etc
#include "FairGeoShapes.h"              // for FairGeoShapes

#include "TList.h"                      // for TList

#include <string.h>                     // for strcmp
#include <iostream>                     // for cout

using namespace std;
ClassImp(ShipGeoCave)

ShipGeoCave::ShipGeoCave()
  : FairGeoSet(),
    name("cave")
{
  // Constructor
  fName="cave";
  name="cave";
  maxModules=1;
}

Bool_t ShipGeoCave::read(fstream& fin,FairGeoMedia* media)
{
  // Reads the geometry from file
  if (!media) { return kFALSE; }
  const Int_t maxbuf=256;
  char buf[maxbuf];
  FairGeoNode* volu=0;
  FairGeoMedium* medium;
  Bool_t rc=kTRUE;
  do {
    fin.getline(buf,maxbuf);
    if (buf[0]!='\0' && buf[0]!='/' && !fin.eof()) {
      if (strcmp(buf,name)==0) {
        volu=new FairGeoNode;
        volu->SetName(buf);
        volu->setVolumeType(kFairGeoTopNode);
        volu->setActive();
        fin.getline(buf,maxbuf);
        TString shape(buf);
        FairGeoBasicShape* sh=pShapes->selectShape(shape);
        if (sh) { volu->setShape(sh); }
        else { rc=kFALSE; }
        fin.getline(buf,maxbuf);
        medium=media->getMedium(buf);
        if (!medium) {
          medium=new FairGeoMedium();
          media->addMedium(medium);
        }
        volu->setMedium(medium);
        Int_t n=0;
        if (sh) { n=sh->readPoints(&fin,volu); }
        if (n<=0) { rc=kFALSE; }
      } else { rc=kFALSE; }
    }
  } while (rc && !volu && !fin.eof());
  if (volu && rc) {
    volumes->Add(volu);
    masterNodes->Add(new FairGeoNode(*volu));
  } else {
    delete volu;
    volu=0;
    rc=kFALSE;
  }
  return rc;
}

void ShipGeoCave::addRefNodes()
{
  // Adds the reference node
  FairGeoNode* volu=getVolume(name);
  if (volu) { masterNodes->Add(new FairGeoNode(*volu)); }
}

void ShipGeoCave::write(fstream& fout)
{
  // Writes the geometry to file
  fout.setf(ios::fixed,ios::floatfield);
  FairGeoNode* volu=getVolume(name);
  if (volu) {
    FairGeoBasicShape* sh=volu->getShapePointer();
    FairGeoMedium* med=volu->getMedium();
    if (sh&&med) {
      fout<<volu->GetName()<<'\n'<<sh->GetName()<<'\n'<<med->GetName()<<'\n';
      sh->writePoints(&fout,volu);
    }
  }
}

void ShipGeoCave::print()
{
  // Prints the geometry
  FairGeoNode* volu=getVolume(name);
  if (volu) {
    FairGeoBasicShape* sh=volu->getShapePointer();
    FairGeoMedium* med=volu->getMedium();
    if (sh&&med) {
      cout<<volu->GetName()<<'\n'<<sh->GetName()<<'\n'<<med->GetName()<<'\n';
      sh->printPoints(volu);
    }
  }
}
