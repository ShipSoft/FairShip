import ROOT
from BaseDetector import BaseDetector


class strawtubesDetector(BaseDetector):
    def __init__(self, name, intree):
        super().__init__(name, intree, 'std.vector', 'Strawtubes')

    def digitize(self):
        """Digitize strawtube MC hits.

        The earliest hit per straw will be marked valid, all later ones invalid.
        """
        earliest_per_det_id = {}
        for index, point in enumerate(self.intree.strawtubesPoint):
            hit = ROOT.strawtubesHit(point, self.intree.t0)
            self.det.push_back(hit)
            if hit.isValid():
                detector_id = hit.GetDetectorID()
                if detector_id in earliest_per_det_id:
                    earliest = earliest_per_det_id[detector_id]
                    if self.det[earliest].GetTDC() > hit.GetTDC():
                        # second hit with smaller tdc
                        self.det[earliest].setInvalid()
                        earliest_per_det_id[detector_id] = index
                    else:
                        self.det[index].setInvalid()
                else:
                    earliest_per_det_id[detector_id] = index
