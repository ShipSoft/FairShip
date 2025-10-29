# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN on behalf of the SHiP Collaboration

import ROOT
import global_variables
from BaseDetector import BaseDetector


class muonDetector(BaseDetector):
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
