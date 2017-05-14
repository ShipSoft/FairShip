__author__ = 'Mikhail Hushchyn'

import ROOT
import numpy

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
    tmax=max(track, key=track.get)

    frac=0.
    if nh>0: frac=float(track[tmax])/float(nh)

    return frac,tmax