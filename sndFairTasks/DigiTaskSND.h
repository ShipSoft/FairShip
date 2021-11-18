/********************************************************************************
 *    Copyright (C) 2014 GSI Helmholtzzentrum fuer Schwerionenforschung GmbH    *
 *                                                                              *
 *              This software is distributed under the terms of the             *
 *              GNU Lesser General Public Licence (LGPL) version 3,             *
 *                  copied verbatim in the file "LICENSE"                       *
 ********************************************************************************/
#ifndef DIGITASKSND_H_
#define DIGITASKSND_H_

#include <Rtypes.h>             // for THashConsistencyHolder, ClassDef
#include <RtypesCore.h>         // for Double_t, Int_t, Option_t
#include <TClonesArray.h> 
#include "FairTask.h"           // for FairTask, InitStatus
#include "FairEventHeader.h"    // for FairEventHeader
#include "FairMCEventHeader.h"  // for FairMCEventHeader
#include "Scifi.h"              // for Scifi detector
class TBuffer;
class TClass;
class TClonesArray;
class TMemberInspector;

using namespace std;

class DigiTaskSND : public FairTask
{
  public:
    /** Default constructor **/
    DigiTaskSND();

    /** Destructor **/
    ~DigiTaskSND();

    /** Virtual method Init **/
    virtual InitStatus Init();

    /** Virtual method Exec **/
    virtual void Exec(Option_t* opt);
    
    /** setting thresholds **/
    void setThresholds(Float_t S,Float_t ML=0,Float_t MS=0){ScifiThreshold = S; MufiLargeThreshold = ML; MufiSmallThreshold = MS;}

  private:
    void digitizeMuFilter();
    void digitizeScifi();
    void clusterScifi();

    Scifi* scifi;
    map<Int_t, map<Int_t, array<float, 2>>> fibresSiPM;
    map<Int_t, map<Int_t, array<float, 2>>> siPMFibres;

    // Input
    FairMCEventHeader* fMCEventHeader;
    TClonesArray* fMuFilterPointArray; // MC points
    TClonesArray* fScifiPointArray;
    TClonesArray* fScifiClusterArray;
    // Output
    FairEventHeader* fEventHeader;
    TClonesArray* fMuFilterDigiHitArray; // hit class (digitized!)
    TClonesArray* fScifiDigiHitArray;
    TClonesArray* fMuFilterHit2MCPointsArray; // link to MC truth
    TClonesArray* fScifiHit2MCPointsArray;
    TClonesArray* fvetoPointArray;
    TClonesArray* fEmulsionPointArray;

    TClonesArray* fMCTrackArray;
    DigiTaskSND(const DigiTaskSND&);
    DigiTaskSND& operator=(const DigiTaskSND&);

    // thresholds
    Float_t ScifiThreshold;
    Float_t MufiLargeThreshold;
    Float_t MufiSmallThreshold;

    ClassDef(DigiTaskSND, 1);
};

#endif /* DIGITASKSND_H_ */
