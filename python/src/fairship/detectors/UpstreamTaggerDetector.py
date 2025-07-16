import ROOT
import fairship.global_variables as global_variables
from fairship.detectors import BaseDetector


class UpstreamTaggerDetector(BaseDetector):
    def __init__(self, name, intree):
        super().__init__(name, intree)

    def digitize(self):
        ship_geo = global_variables.ShipGeo
        pos_res = ship_geo.UpstreamTagger.PositionResolution
        time_res = ship_geo.UpstreamTagger.TimeResolution

        index = 0
        for aMCPoint in self.intree.UpstreamTaggerPoint:
            aHit = ROOT.UpstreamTaggerHit(aMCPoint, self.intree.t0, pos_res, time_res)
            if self.det.GetSize() == index:
                self.det.Expand(index + 1000)
            self.det[index] = aHit
            index += 1
