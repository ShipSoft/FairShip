__author__ = 'Mikhail Hushchyn'

import ROOT
import numpy

def decodeDetectorID(detID):
    """
    Decodes detector ID.

    Parameters
    ----------
    detID : int or array-like
        Detector ID values.

    Returns
    -------
    statnb : int or array-like
        Station numbers.
    vnb : int or array-like
        View numbers.
    pnb : int or array-like
        Plane numbers.
    lnb : int or array-like
        Layer numbers.
    snb : int or array-like
        Straw tube numbers.
    """

    statnb = detID // 10000000
    vnb = (detID - statnb * 10000000) // 1000000
    pnb = (detID - statnb * 10000000 - vnb * 1000000) // 100000
    lnb = (detID - statnb * 10000000 - vnb * 1000000 - pnb * 100000) // 10000
    snb = detID - statnb * 10000000 - vnb * 1000000 - pnb * 100000 - lnb * 10000 - 2000

    return statnb, vnb, pnb, lnb, snb

def fracMCsame(trackids):
    """
    Estimates max fraction of true hit labels for a recognized track.
    trackids : array_like
        hit indexes of a recognized track

    Retunrs
    -------
    frac : float
        Max fraction of true hit labels.
    tmax : int
        True hit label with max fraction in a recognized track.
    """

    track={}
    nh=len(trackids)
    for tid in trackids:
        if tid==999:
            nh-=1
            continue
        if track.has_key(tid):
            track[tid]+=1
        else:
            track[tid]=1
    #now get track with largest number of hits
    if track != {}:
        tmax=max(track, key=track.get)
    else:
        track = {-999:0}
        tmax = -999

    frac=0.
    if nh>0: frac=float(track[tmax])/float(nh)

    return frac,tmax