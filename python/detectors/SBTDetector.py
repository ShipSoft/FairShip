import ROOT
from BaseDetector import BaseDetector


class SBTDetector(BaseDetector):
    def __init__(
        self,
        name,
        intree,
        branchName=None,
        mcBranchType=None,
        mcBranchName="digiSBT2MC",
    ):
        super().__init__(name, intree, branchName, mcBranchType, mcBranchName)

    def digitize(self):
        """Digitize Surrounding Background Tagger MC hits.

        TDC defined as the time of the first MC hit in the cell.
        Eloss defined as the cumulative energy deposition of MC hits in the cell.

        """
        ElossPerDetId = {}
        tOfFlight = {}
        listOfVetoPoints = {}
        key = -1
        for aMCPoint in self.intree.vetoPoint:
            key += 1
            detID = aMCPoint.GetDetectorID()
            Eloss = aMCPoint.GetEnergyLoss()
            if detID not in ElossPerDetId:
                ElossPerDetId[detID] = 0
                listOfVetoPoints[detID] = []
                tOfFlight[detID] = []
            ElossPerDetId[detID] += Eloss
            listOfVetoPoints[detID].append(key)
            tOfFlight[detID].append(aMCPoint.GetTime())
        for seg in ElossPerDetId:
            aHit = ROOT.vetoHit(seg, ElossPerDetId[seg])
            aHit.SetTDC(min(tOfFlight[seg]) + self.intree.t0)
            if ElossPerDetId[seg] < 0.045:
                aHit.setInvalid()  # threshold for liquid scintillator, source Berlin group
            self.det.push_back(aHit)
            v = ROOT.std.vector("int")()
            for x in listOfVetoPoints[seg]:
                v.push_back(x)
            self.MCdet.push_back(v)
