__author__ = 'Mikhail Hushchyn'

import ROOT
import numpy



def smearHits(sTree, ShipGeo, modules, no_amb=None):
    """
    Smears hits.

    Parameters
    ----------
    sTree : root file
        Events in raw format.
    ShipGeo : object
        Contains SHiP detector geometry.
    modules : object
        Contains SHiP detector geometry.
    no_amb : boolean
        If False - no hit smearing.

    Returns
    -------
    SmearedHits : list of dicts
        List of smeared hits. A smeared hit is a dictionary:
        {'digiHit':key,'xtop':top x,'ytop':top y,'z':top z,'xbot':bot x,'ybot':bot y,'dist':smeared dist2wire}
    """

    random = ROOT.TRandom()
    ROOT.gRandom.SetSeed(13)


    # Loking for duplicates
    hitstraws = {}
    duplicatestrawhit = []

    nHits = sTree.strawtubesPoint.GetEntriesFast()
    for i in range(nHits):

        ahit = sTree.strawtubesPoint[i]

        if (str(ahit.GetDetectorID())[:1]=="5") :
            continue

        strawname=str(ahit.GetDetectorID())

        if hitstraws.has_key(strawname):

            if ahit.GetX()>hitstraws[strawname][1]:
                duplicatestrawhit.append(i)
            else:
                duplicatestrawhit.append(hitstraws[strawname][0])
                hitstraws[strawname]=[i,ahit.GetX()]
        else:

            hitstraws[strawname]=[i,ahit.GetX()]


    # Smear strawtube points
    SmearedHits = []
    key = -1

    for i in range(nHits):

        ahit = sTree.strawtubesPoint[i]

        # if i in duplicatestrawhit:
        #     continue
        #
        # if (str(ahit.GetDetectorID())[:1]=="5") :
        #     continue
        #
        # if (((ahit.GetX()/245.)**2 + (ahit.GetY()/495.)**2) >= 1.):
        #     continue

        key+=1
        detID = ahit.GetDetectorID()
        top = ROOT.TVector3()
        bot = ROOT.TVector3()

        modules["Strawtubes"].StrawEndPoints(detID,bot,top)

        #distance to wire, and smear it.
        dw  = ahit.dist2Wire()
        smear = dw
        if not no_amb:
            random = ROOT.TRandom()
            smear = abs(random.Gaus(dw,ShipGeo.strawtubes.sigma_spatial))

        SmearedHits.append( {'digiHit':key,'xtop':top.x(),'ytop':top.y(),'z':top.z(),'xbot':bot.x(),'ybot':bot.y(),'dist':smear} )


    return SmearedHits
