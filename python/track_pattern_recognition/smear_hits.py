__author__ = 'Mikhail Hushchyn'

import ROOT
import numpy



def smearHits(sTree, ShipGeo, modules, no_amb=None):

    random = ROOT.TRandom()
    ROOT.gRandom.SetSeed(13)

    # smear strawtube points
    SmearedHits = []
    key = -1

    for ahit in sTree.strawtubesPoint:

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
