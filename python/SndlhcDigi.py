import ROOT
import os
import shipunit as u
import SciFiMapping
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
        self.eventHeader  = self.sTree.Branch("EventHeader",self.header,32000,1)
        #scifi
        self.digiScifi   = ROOT.TClonesArray("sndScifiHit")
        self.digiScifiBranch   = self.sTree.Branch("Digi_ScifiHits",self.digiScifi,32000,1)
        self.digiScifi2MCPoints =  ROOT.TClonesArray("Hit2MCPoints")
        self.digiScifi2MCPoints.BypassStreamer(ROOT.kTRUE)
        self.digiScifi2MCPointsBranch   = self.sTree.Branch("Digi_ScifiHits2MCPoints",self.digiScifi2MCPoints,32000,1)
        lsOfGlobals  = ROOT.gROOT.GetListOfGlobals()
        self.scifiDet = lsOfGlobals.FindObject('Scifi')
        self.mufiDet = lsOfGlobals.FindObject('MuFilter')
        if not self.scifiDet or not self.mufiDet: 
              exit('detector(s) not found, stop')
# make sipm to fibre mapping
        self.fibresSiPM = SciFiMapping.getFibre2SiPMCPP(self.scifiDet)
        self.siPMFibres = SciFiMapping.getSiPM2FibreCPP(self.scifiDet)
        #scifi clusters
        self.clusScifi   = ROOT.TClonesArray("sndCluster")
        self.clusScifiBranch    = self.sTree.Branch("Cluster_Scifi",self.clusScifi,32000,1)

        #muonFilter
        self.digiMuFilter   = ROOT.TClonesArray("MuFilterHit")
        self.digiMuFilterBranch   = self.sTree.Branch("Digi_MuFilterHits",self.digiMuFilter,32000,1)
        self.digiMuFilter2MCPoints =  ROOT.TClonesArray("Hit2MCPoints")
        self.digiMuFilter2MCPoints.BypassStreamer(ROOT.kTRUE)
        self.digiMuFilter2MCPointsBranch   = self.sTree.Branch("Digi_MuFilterHits2MCPoints",self.digiMuFilter2MCPoints,32000,1)

    def setThresholds(self,S=0,ML=0,MS=0):
        self.ScifiThreshold = S
        self.MufiLargeThreshold = ML
        self.MufiSmallThreshold = MS

    def digitize(self):

        self.header.SetRunId( self.sTree.MCEventHeader.GetRunID() )
        self.header.SetMCEntryNumber( self.sTree.MCEventHeader.GetEventID() )  # counts from 1
        self.eventHeader.Fill()
        self.digiScifi.Delete()
        self.digiScifi2MCPoints.Delete()
        self.digitizeScifi()
        self.digiScifiBranch.Fill()
        self.digiScifi2MCPointsBranch.Fill()
        self.clusScifi.Delete()
        self.clusterScifi()
        self.clusScifiBranch.Fill()

        self.digiMuFilter.Delete()
        self.digiMuFilter2MCPoints.Delete()
        self.digitizeMuFilter()
        self.digiMuFilterBranch.Fill()
        self.digiMuFilter2MCPointsBranch.Fill()

    def digitizeScifi(self):
        hitContainer = {}
        mcLinks = ROOT.Hit2MCPoints()
        mcPoints = {}
        norm = {}
        k=-1
        for p in self.sTree.ScifiPoint:
            k+=1
            # collect all hits in same SiPM channel
            detID = p.GetDetectorID()
            locFibreID = detID%100000
            if not locFibreID in self.siPMFibres: continue # fibres in dead areas
            for sipmChan in self.siPMFibres[locFibreID]:
                  globsipmChan = int(detID/100000)*100000+sipmChan
                  if not globsipmChan in hitContainer: 
                       hitContainer[globsipmChan]=[]
                       mcPoints[globsipmChan] = {}
                       norm[globsipmChan] = 0
                  w = self.siPMFibres[locFibreID][sipmChan]['weight']
                  hitContainer[globsipmChan].append([p,w])
                  dE = p.GetEnergyLoss()*w
                  mcPoints[globsipmChan][k]=dE
                  norm[globsipmChan]+= dE
        index = 0
        for detID in hitContainer:
               allPoints = ROOT.std.vector('ScifiPoint*')()
               allWeights = ROOT.std.vector('Float_t')()
               for p in hitContainer[detID]:
                    allPoints.push_back(p[0])
                    allWeights.push_back(p[1])
               aHit = ROOT.sndScifiHit(detID,allPoints,allWeights)
               if self.digiScifi.GetSize() == index: self.digiScifi.Expand(index+100)
               self.digiScifi[index]=aHit
               index+=1
               for k in mcPoints[detID]:
                    mcLinks.Add(detID,k, mcPoints[detID][k]/norm[detID])
        self.digiScifi2MCPoints[0]=mcLinks

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

    def clusterScifi(self):
        index = 0
        hitDict = {}
        for k in range(self.sTree.Digi_ScifiHits.GetEntries()):
            d = self.sTree.Digi_ScifiHits[k]
            if not d.isValid(): continue 
            hitDict[d.GetDetectorID()] = k
        hitList = list(hitDict.keys())
        if len(hitList)>0:
              hitList.sort()
              tmp = [ hitList[0] ]
              cprev = hitList[0]
              ncl = 0
              last = len(hitList)-1
              hitlist = ROOT.std.vector("sndScifiHit*")()
              for i in range(len(hitList)):
                   if i==0 and len(hitList)>1: continue
                   c=hitList[i]
                   if (c-cprev)==1: 
                        tmp.append(c)
                   if (c-cprev)!=1 or c==hitList[last]:
                        first = tmp[0]
                        N = len(tmp)
                        hitlist.clear()
                        for aHit in tmp: hitlist.push_back( self.sTree.Digi_ScifiHits[hitDict[aHit]],)
                        aCluster = ROOT.sndCluster(first,N,hitlist,self.scifiDet)
                        if self.clusScifi.GetSize() == index: self.clusScifi.Expand(index+10)
                        self.clusScifi[index]=aCluster
                        index+=1
                        if c!=hitList[last]:
                             ncl+=1
                             tmp = [c]
                   cprev = c

            
    def finish(self):
        print('finished writing tree')
        self.sTree.Write()
