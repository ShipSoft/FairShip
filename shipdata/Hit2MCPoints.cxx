#include "Hit2MCPoints.h"
#include <stdio.h>

// -----   Default constructor   -------------------------------------------
Hit2MCPoints::Hit2MCPoints()
  : TObject()
{
}

// -----   Fill   ------------------------------------------
void Hit2MCPoints::Add(int detID,int key, float w)
{
       linksToMCPoints[detID][key]=w;
}

// -----   Copy constructor   ----------------------------------------------
Hit2MCPoints::Hit2MCPoints(const Hit2MCPoints& ti)
  : TObject(ti),
   linksToMCPoints(ti.linksToMCPoints)
{
}
// -----   Destructor   ----------------------------------------------------
Hit2MCPoints::~Hit2MCPoints() { }
// -------------------------------------------------------------------------

ClassImp(Hit2MCPoints)
