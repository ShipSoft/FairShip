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
        for p in self.sTree.MuFilterPoint:
            # collect all hits in same detector element
            detID = p.GetDetectorID()
            if not detID in hitContainer: hitContainer[detID]=[]
            hitContainer[detID].append(p)
        index = 0
        for detID in hitContainer:
            allPoints = ROOT.std.vector('MuFilterPoint*')()
            norm = 0
            mcPoints[detID]={}
            k=-1
            for p in hitContainer[detID]:
                 k+=1
                 allPoints.push_back(p)
                 norm+= p.GetEnergyLoss()
                 mcPoints[detID][k]=p.GetEnergyLoss()
            aHit = ROOT.MuFilterHit(detID,allPoints)
            if index>0 and self.digiMuFilter.GetSize() == index: self.digiMuFilter.Expand(index+1000)
            self.digiMuFilter[index]=aHit

            for k in mcPoints[detID]: mcLinks.Add(detID,k, mcPoints[detID][k]/norm)
        self.digiMuFilter2MCPoints[0]=mcLinks
            
    def finish(self):
        print('finished writing tree')
        self.sTree.Write()
