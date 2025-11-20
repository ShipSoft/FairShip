import global_variables
import ROOT
from BaseDetector import BaseDetector


class UpstreamTaggerDetector(BaseDetector):
    def __init__(self, name, intree, outtree=None):
        super().__init__(name, intree, outtree=outtree)

    def digitize(self):
        ship_geo = global_variables.ShipGeo
        pos_res = ship_geo.UpstreamTagger.PositionResolution
        time_res = ship_geo.UpstreamTagger.TimeResolution

        for aMCPoint in self.intree.UpstreamTaggerPoint:
            aHit = ROOT.UpstreamTaggerHit(aMCPoint, self.intree.t0, pos_res, time_res)
            self.det.push_back(aHit)
