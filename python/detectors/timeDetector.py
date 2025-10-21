import ROOT
import global_variables
from BaseDetector import BaseDetector

class timeDetector(BaseDetector):
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
