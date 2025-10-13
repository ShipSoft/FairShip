import ROOT
import global_variables

class IDetector:
    def __init__(self, name, intree):
        self.name = name
        self.det = ROOT.TClonesArray(f"{name}Hit")
        self.intree = intree
        self.branch = self.intree.Branch(f"Digi_{name}Hits", self.det, 32000,-1)

    def clear(self):
        pass

    def Delete(self):
        self.det.Delete()

    def Fill(self):
        self.branch.Fill()

    def digitize(self):
        pass

    def process(self):
        self.Delete()
        self.digitize()
        self.Fill()

class muonDetector(IDetector):
    def __init__(self, name, intree):
        super().__init__(name, intree)
#        self.det = ROOT.TClonesArray(f"{name}Hit")
#        self.branch = self..Branch(f"Digi_{name}Hits", self.det, 32000,-1)



    def digitize(self):
        index = 0
        hitsPerDetId = {}
        for aMCPoint in self.intree.muonPoint:
            aHit = ROOT.muonHit(aMCPoint,self.intree.t0)
            if self.det.GetSize() == index:
                self.det.Expand(index+1000)
            self.det[index]=aHit
            detID = aHit.GetDetectorID()
            if aHit.isValid():
                if detID in hitsPerDetId:
                    if self.det[hitsPerDetId[detID]].GetDigi() > aHit.GetDigi():
                    # second hit with smaller tdc
                        self.det[hitsPerDetId[detID]].setValidity(0)
                        hitsPerDetId[detID] = index
            index+=1    

