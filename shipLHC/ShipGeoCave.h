#ifndef SNOOPYGEOCAVE_H
#define SNOOPYGEOCAVE_H

#include "FairGeoSet.h"                 // for FairGeoSet

#include <iosfwd>                    // for fstream
#include "Rtypes.h"                     // for ShipGeoCave::Class, Bool_t, etc
#include "TString.h"                    // for TString

#include <fstream>                      // for fstream

class FairGeoMedia;

class  ShipGeoCave : public FairGeoSet
{
  protected:
    TString name;
  public:
    ShipGeoCave();
    ~ShipGeoCave() {}
    const char* getModuleName(Int_t) {return name.Data();}
    Bool_t read(std::fstream&,FairGeoMedia*);
    void addRefNodes();
    void write(std::fstream&);
    void print();
    ClassDef(ShipGeoCave,0) // Class for the geometry of CAVE
};

#endif  /* !PNDGEOCAVE_H */
