/********************************************************************************
 *    Copyright (C) 2014 GSI Helmholtzzentrum fuer Schwerionenforschung GmbH    *
 *                                                                              *
 *              This software is distributed under the terms of the             *
 *         GNU Lesser General Public Licence version 3 (LGPL) version 3,        *
 *                  copied verbatim in the file "LICENSE"                       *
 ********************************************************************************/

#include <thread>
#include <chrono>

#include "TClonesArray.h"
#include "TH1F.h"
#include "TCanvas.h"
#include "TFolder.h"

#include "FairRootManager.h"
#include "FairRunOnline.h"

#include "ShipHit.h"
#include "ShipTdcTask.h"

ShipTdcTask::ShipTdcTask(const char* name, Int_t iVerbose)
    : FairTask(name, iVerbose)
    , fRawData(nullptr)
    , fhChannel(nullptr)
    , fhTime(nullptr)
{
}

ShipTdcTask::~ShipTdcTask()
{
}

InitStatus ShipTdcTask::Init()
{
    FairRootManager* mgr = FairRootManager::Instance();
    if (nullptr == mgr)
    {
        return kFATAL;
    }

    fRawData = static_cast<TClonesArray*>(mgr->GetObject("DriftTubesHit"));
    if (nullptr == fRawData)
    {
        return kERROR;
    }

    fhChannel = new TH1I("hChannel", "Raw Channel distribution", 100, 4000., 4500.);
    fhTime = new TH1I("hTime", "Raw Time distribution", 100, 0, 35000.);

    FairRunOnline* run = FairRunOnline::Instance();
    if (nullptr == run)
    {
        return kERROR;
    }

    run->AddObject(fhChannel);
    run->RegisterHttpCommand("/Reset_hChannel", "/hChannel/->Reset()");
    
    auto c1 = new TCanvas("c1", "", 10, 10, 500, 500);
    c1->Divide(1, 2);
    c1->cd(1);
    fhChannel->Draw();
    c1->cd(2);
    fhTime->Draw();
    run->AddObject(c1);
    
    TFolder *folder = new TFolder("ShipTdcFolder", "Example Folder");
    folder->Add(fhChannel);
    folder->Add(fhTime);
    run->AddObject(folder);

    return kSUCCESS;
}

void ShipTdcTask::Exec(Option_t*)
{
    if (nullptr == fRawData)
    {
        return;
    }
    for (TObject* item : *fRawData){
        if (nullptr == item)
        {
            continue;
        }
        auto hit = static_cast<ShipHit*>(item);
        fhChannel->Fill(hit->GetDetectorID());
        fhTime->Fill(hit->GetDigi());
    }
}

void ShipTdcTask::FinishEvent()
{
}

void ShipTdcTask::FinishTask()
{
}

ClassImp(ShipTdcTask)
