import ROOT
import os
import shipunit as u
import global_variables
from array import array

stop  = ROOT.TVector3()
start = ROOT.TVector3()

class SndlhcDigi:
    " convert  MC hits to digitized hits"
    def __init__(self,fout):

        self.iEvent = 0

        outdir=os.getcwd()
        outfile=outdir+"/"+fout
        self.fn = ROOT.TFile(fout,'update')
        self.sTree = self.fn.cbmsim

        # event header
        self.header  = ROOT.FairEventHeader()
        self.eventHeader  = self.sTree.Branch("ShipEventHeader",self.header,32000,1)
        #muonFilter
        self.digiMuFilter   = ROOT.TClonesArray("MuFilterHit")
        self.digiMuFilterBranch   = self.sTree.Branch("Digi_MuFilterHits",self.digiMuFilter,32000,1)
        self.digiMuFilter2MCPoints =  ROOT.TClonesArray("Hit2MCPoints")
        self.digiMuFilter2MCPoints.BypassStreamer(ROOT.kTRUE)
        self.digiMuFilter2MCPointsBranch   = self.sTree.Branch("Digi_MuFilterHits2MCPoints",self.digiMuFilter2MCPoints,32000,1)

    def digitize(self):

        self.header.SetRunId( self.sTree.MCEventHeader.GetRunID() )
        self.header.SetMCEntryNumber( self.sTree.MCEventHeader.GetEventID() )  # counts from 1
        self.eventHeader.Fill()
        self.digiMuFilter.Delete()
        self.digiMuFilter2MCPoints.Delete()
        self.digitizeMuFilter()
        self.digiMuFilterBranch.Fill()
        self.digiMuFilter2MCPointsBranch.Fill()
# SciFi to be added

    def digitizeMuFilter(self):
        hitContainer = {}
        mcLinks = ROOT.Hit2MCPoints()
        mcPoints = {}
        norm = {}
        k=-1
        for p in self.sTree.MuFilterPoint:
            k+=1
            # collect all hits in same detector element
            detID = p.GetDetectorID()
            if not detID in hitContainer: 
                  hitContainer[detID]=[]
                  mcPoints[detID] = {}
                  norm[detID] = 0
            hitContainer[detID].append(p)
            mcPoints[detID][k]=p.GetEnergyLoss()
            norm[detID]+= p.GetEnergyLoss()
        index = 0
        for detID in hitContainer:
            allPoints = ROOT.std.vector('MuFilterPoint*')()
            for p in hitContainer[detID]:
                 allPoints.push_back(p)
            aHit = ROOT.MuFilterHit(detID,allPoints)
            if self.digiMuFilter.GetSize() == index: self.digiMuFilter.Expand(index+100)
            self.digiMuFilter[index]=aHit
            index+=1
            for k in mcPoints[detID]:
                mcLinks.Add(detID,k, mcPoints[detID][k]/norm[detID])
        self.digiMuFilter2MCPoints[0]=mcLinks
            
    def finish(self):
        print('finished writing tree')
        self.sTree.Write()
