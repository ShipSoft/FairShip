__author__ = 'Thomas Ruf', 'Mikhail Hushchyn'

# Based on Thomas Ruf's code

import ROOT
import numpy

def Digitization(sTree, SmearedHits):
    """
    Digitizes hit for the track pattern recognition.

    Parameters
    ----------
    sTree : root file
        Events in raw format.
    SmearedHits : list of dicts
        List of smeared hits. A smeared hit is a dictionary:
        {'digiHit':key,'xtop':top x,'ytop':top y,'z':top z,'xbot':bot x,'ybot':bot y,'dist':smeared dist2wire}

    Retruns
    -------
    X : ndarray-like
        Information about active straw tubes: [[xtop, ytop, ztop, xbot, ybot, zboy, dist2wire, detID], [...], ...]
    """

    Hits = []

    for i in range(len(SmearedHits)):
        xtop=SmearedHits[i]['xtop']
        xbot=SmearedHits[i]['xbot']
        ytop=SmearedHits[i]['ytop']
        ybot=SmearedHits[i]['ybot']
        ztop=SmearedHits[i]['z']
        zbot=SmearedHits[i]['z']
        distance=SmearedHits[i]['dist']
        detid=sTree.strawtubesPoint[i].GetDetectorID()

        ahit=[xtop, ytop, ztop, xbot, ybot, zbot, float(distance), int(detid)]
        Hits.append(ahit)

    return numpy.array(Hits)
