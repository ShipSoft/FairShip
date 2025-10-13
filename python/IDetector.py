import ROOT
import global_variables

class IDetector:
    def __init__(self, name, intree, branchType = 'TConesArray'):
        self.name = name
        self.det = eval(f"ROOT.{branchType}('{name}Hit')")
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

class timeDetector(IDetector):
    def __init__(self, name, intree):
        super().__init__(name, intree)

    def digitize(self):
        index = 0
        hitsPerDetId = {}
        for aMCPoint in self.intree.TimeDetPoint:
            aHit = ROOT.TimeDetHit(aMCPoint,self.intree.t0)
            if self.det.GetSize() == index:
                self.det.Expand(index+1000)
            self.det[index]=aHit
            detID = aHit.GetDetectorID()
            if aHit.isValid():
                if detID in hitsPerDetId:
                    t = aHit.GetMeasurements()
                    ct = aHit.GetMeasurements()
                    # this is not really correct, only first attempt
                    # case that one measurement only is earlier not taken into account
                    # SetTDC(Float_t val1, Float_t val2)
                    if  t[0]>ct[0] or t[1]>ct[1]:
                        # second hit with smaller tdc
                        self.det[hitsPerDetId[detID]].setInvalid()
                        hitsPerDetId[detID] = index
            index+=1

