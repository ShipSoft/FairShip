import ROOT
import global_variables
from BaseDetector import BaseDetector
import shipunit as u
import global_variables


class strawtubesDetector(BaseDetector):
    def __init__(self, name, intree, branchType="std.vector"):
        super().__init__(name, intree, branchType)

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

    def withT0Estimate(self):
        # loop over all straw tdcs and make average, correct for ToF
        n = 0
        t0 = 0.0
        key = -1
        stop = ROOT.TVector3()
        start = ROOT.TVector3()
        SmearedHits = []
        v_drift = global_variables.modules["strawtubes"].StrawVdrift()
        global_variables.modules["strawtubes"].StrawEndPoints(1002001, start, stop)
        z1 = stop.z()
        for aDigi in self.det:
            key += 1
            if not aDigi.isValid():
                continue
            detID = aDigi.GetDetectorID()
            global_variables.modules["strawtubes"].StrawEndPoints(detID, start, stop)
            delt1 = (start[2] - z1) / u.speedOfLight
            t0 += aDigi.GetDigi() - delt1
            SmearedHits.append(
                {
                    "digiHit": key,
                    "xtop": stop.x(),
                    "ytop": stop.y(),
                    "z": stop.z(),
                    "xbot": start.x(),
                    "ybot": start.y(),
                    "dist": aDigi.GetDigi(),
                    "detID": detID,
                }
            )
            n += 1
        if n > 0:
            t0 = t0 / n - 73.2 * u.ns
        for s in SmearedHits:
            delt1 = (s["z"] - z1) / u.speedOfLight
            s["dist"] = (s["dist"] - delt1 - t0) * v_drift
        return SmearedHits

    def smearHits(self, no_amb=None):
        # smear strawtube points
        SmearedHits = []
        key = -1
        stop = ROOT.TVector3()
        start = ROOT.TVector3()
        v_drift = global_variables.modules["strawtubes"].StrawVdrift()
        global_variables.modules["strawtubes"].StrawEndPoints(1002001, start, stop)
        z1 = stop.z()
        for aDigi in self.det:
            key += 1
            if not aDigi.isValid():
                continue
            detID = aDigi.GetDetectorID()
            global_variables.modules["strawtubes"].StrawEndPoints(detID, start, stop)
            # distance to wire
            delt1 = (start[2] - z1) / u.speedOfLight
            p = self.intree.strawtubesPoint[key]
            # use true t0  construction:
            #     fdigi = t0 + p->GetTime() + t_drift + ( stop[0]-p->GetX() )/ speedOfLight;
            smear = (
                aDigi.GetDigi()
                - self.intree.t0
                - p.GetTime()
                - (stop[0] - p.GetX()) / u.speedOfLight
            ) * v_drift
            if no_amb:
                smear = p.dist2Wire()
            SmearedHits.append(
                {
                    "digiHit": key,
                    "xtop": stop.x(),
                    "ytop": stop.y(),
                    "z": stop.z(),
                    "xbot": start.x(),
                    "ybot": start.y(),
                    "dist": smear,
                    "detID": detID,
                }
            )
            # Note: top.z()==bot.z() unless misaligned, so only add key 'z' to smearedHit
            if abs(stop.y()) == abs(start.y()):
                global_variables.h["disty"].Fill(smear)
            elif abs(stop.y()) > abs(start.y()):
                global_variables.h["distu"].Fill(smear)
            elif abs(stop.y()) < abs(start.y()):
                global_variables.h["distv"].Fill(smear)

        return SmearedHits
