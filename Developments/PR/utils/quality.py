__author__ = 'Mikhail Hushchyn'


import ROOT
import numpy
import rootUtils as ut
import math

from utils import fracMCsame
from utils import Digitization
from utils import get_track_ids

################################################ Helping functions #####################################################

class HitsMatchingEfficiency(object):

    def __init__(self, eff_threshold=0.5, n_tracks=None):
        """
        This class calculates tracks efficiencies, reconstruction efficiency, ghost rate and clone rate for one event using hits matching.

        Prameters
        ---------
        eff_threshold : float
            Threshold value of a track efficiency to consider a track reconstructed.
        n_tracks : int
            Number of tracks in an event.
        """

        self.eff_threshold = eff_threshold
        self.n_tracks = n_tracks

    def fit(self, true_labels, track_inds):
        """
        The method calculates all metrics.

        Parameters
        ----------
        true_labels : array-like
            True labels of the hits.
        track_inds : array-like
            List of recognized tracks. Recognized track is a list of hit indexes correspond to one bin in track parameters space.
            Example: [[ind1, ind2, ind3, ...], [...], ...]
        """

        # Calculate efficiencies
        efficiencies = []
        tracks_id = []

        for one_track_inds in track_inds:

            track = true_labels[one_track_inds]
            # if len(track[track != -1]) == 0:
            #    continue
            unique, counts = numpy.unique(track, return_counts=True)

            if len(track) != 0:
                eff = 1. * counts.max() / len(track)
                efficiencies.append(eff)
                tracks_id.append(unique[counts == counts.max()][0])

        tracks_id = numpy.array(tracks_id)
        efficiencies = numpy.array(efficiencies)
        self.efficiencies_ = efficiencies

        # Calculate avg. efficiency
        avg_efficiency = efficiencies.mean()
        self.avg_efficiency_ = avg_efficiency

        # Calculate reconstruction efficiency
        true_tracks_id = numpy.unique(true_labels)

        if self.n_tracks == None:
            n_tracks = (true_tracks_id != -1).sum()
        else:
            n_tracks = self.n_tracks

        reco_tracks_id = tracks_id[efficiencies >= self.eff_threshold]
        unique, counts = numpy.unique(reco_tracks_id[reco_tracks_id != -1], return_counts=True)

        if n_tracks != 0:
            recognition_efficiency = 1. * len(unique) / (n_tracks)
        else:
            recognition_efficiency = 0
        self.recognition_efficiency_ = recognition_efficiency

        # Calculate ghost rate
        if n_tracks != 0:
            ghost_rate = 1. * (len(tracks_id) - len(reco_tracks_id[reco_tracks_id != -1])) / (n_tracks)
        else:
            ghost_rate = 0
        self.ghost_rate_ = ghost_rate

        # Calculate clone rate
        reco_tracks_id = tracks_id[efficiencies >= self.eff_threshold]
        unique, counts = numpy.unique(reco_tracks_id[reco_tracks_id != -1], return_counts=True)

        if n_tracks != 0:
            clone_rate = (counts - numpy.ones(len(counts))).sum() / (n_tracks)
        else:
            clone_rate = 0
        self.clone_rate_ = clone_rate


def select_track_hits(track_inds, selection):
    """
    Selects track hits that satisfy selection.

    Parameters
    ----------
    track_inds : array-like
        List of recognized tracks. Recognized track is a list of hit indexes correspond to one bin in track parameters space.
        Example: [[ind1, ind2, ind3, ...], [...], ...]
    selection : array-like
        Selection: [True, False, False, ...]. Shape = (hit number of an event, )

    Returns
    -------
    new_track_inds : array-like
        List of recognized tracks. Recognized track is a list of hit indexes correspond to one bin in track parameters space.
        Example: [[ind1, ind2, ind3, ...], [...], ...]
    """

    new_track_inds = []

    for atrack in track_inds:

        atrack = numpy.array(atrack)
        mask = selection[atrack]
        new_track_inds.append(atrack[mask])

    return numpy.array(new_track_inds)

def get_charges(stree, smeared_hits):
    """
    Estimates hit true particle charges.

    Parameters
    ----------
    stree : root file
        Events in raw format.
    smeared_hits : list of dicts
        List of smeared hits. A smeared hit is a dictionary:
        {'digiHit':key,'xtop':top x,'ytop':top y,'z':top z,'xbot':bot x,'ybot':bot y,'dist':smeared dist2wire}

    Returns
    -------
    charges : array-like
        True charges of hits: [q1, q2, ...]
    """

    PDG=ROOT.TDatabasePDG.Instance()

    charges = []

    for i in range(len(smeared_hits)):

        try:
            pdg = stree.strawtubesPoint[i].PdgCode()
            acharge = PDG.GetParticle(pdg).Charge() / 3.
        except:
            acharge = -999
        charges.append(acharge)

    return numpy.array(charges)

def get_pinvs(stree, smeared_hits):
    """
    Estimates hit true particle inverse momentum.

    Parameters
    ----------
    stree : root file
        Events in raw format.
    smeared_hits : list of dicts
        List of smeared hits. A smeared hit is a dictionary:
        {'digiHit':key,'xtop':top x,'ytop':top y,'z':top z,'xbot':bot x,'ybot':bot y,'dist':smeared dist2wire}

    Returns
    -------
    pinvs : array-like
        True inverse momentum values of hits: [pinv1, pinv2, ...]
    """

    pinvs = []

    for i in range(len(smeared_hits)):

        px = stree.strawtubesPoint[i].GetPx()
        py = stree.strawtubesPoint[i].GetPy()
        pz = stree.strawtubesPoint[i].GetPz()
        apinv = 1. / numpy.sqrt(px**2 + py**2 + pz**2)
        pinvs.append(apinv)

    return numpy.array(pinvs)

def get_true_coords(stree, smeared_hits):
    """
    Estimates hit true coordinates.

    Parameters
    ----------
    stree : root file
        Events in raw format.
    smeared_hits : list of dicts
        List of smeared hits. A smeared hit is a dictionary:
        {'digiHit':key,'xtop':top x,'ytop':top y,'z':top z,'xbot':bot x,'ybot':bot y,'dist':smeared dist2wire}

    Returns
    -------
    XYZ : ndarray-like
        True coordinates of hits: [[x1, y1, z1], [x2, y2, z2], ...]
    """

    X, Y, Z = [], [], []

    for i in range(len(smeared_hits)):

        x = stree.strawtubesPoint[i].GetX()
        y = stree.strawtubesPoint[i].GetY()
        z = stree.strawtubesPoint[i].GetZ()

        X.append(x)
        Y.append(y)
        Z.append(z)

    X = numpy.array(X).reshape(-1, 1)
    Y = numpy.array(Y).reshape(-1, 1)
    Z = numpy.array(Z).reshape(-1, 1)

    XYZ = numpy.concatenate((X, Y, Z), axis=1)

    return XYZ

def get_tube_coords(smeared_hits):
    """
    Estimates straw tube coordinates.

    Parameters
    ----------
    smeared_hits : list of dicts
        List of smeared hits. A smeared hit is a dictionary:
        {'digiHit':key,'xtop':top x,'ytop':top y,'z':top z,'xbot':bot x,'ybot':bot y,'dist':smeared dist2wire}

    Returns
    -------
    XYZ : ndarray-like
        Straw tube coordinates: [[x1, y1, z1], [x2, y2, z2], ...]
    """

    X, Y, Z = [], [], []

    for i in range(len(smeared_hits)):

        x = smeared_hits[i]['xtop']
        y = smeared_hits[i]['xtop']
        z = smeared_hits[i]['z']

        X.append(x)
        Y.append(y)
        Z.append(z)

    X = numpy.array(X).reshape(-1, 1)
    Y = numpy.array(Y).reshape(-1, 1)
    Z = numpy.array(Z).reshape(-1, 1)

    XYZ = numpy.concatenate((X, Y, Z), axis=1)

    return XYZ


def score(Z_tube, Y_tube, Z_hit, Y_hit, k, b):
    """
    Estimates efficiency of left-right ambiguity resolution for a track.

    Parameters
    ----------
    Z_tube : array-like
        Z-coordinates of straw tubes for a track.
    Y_tube : array-like
        Y-coordinates of straw tubes for a track.
    Z_hit : array-like
        Z-coordinates of hits for a track.
    Y_hit : array-like
        Y-coordinates of hits for a track.
    k : float
        Track parameter in z-y plane. Track parametrization: y = k * x + b.
    b : float
        Track parameter in z-y plane. Track parametrization: y = k * x + b.

    Returns
    -------
    tot_len : int
        Number of hits of a recognized track.
    reco_len : int
        Number of correctly resolved hits of a recognized track.
    ratio : float
        Efficiency of left-right ambiguity resolution for a track.
    """

    diff1 = Y_tube - Y_hit
    diff2 = Y_tube - (b + k * Z_tube)

    tot_len = 1. * len(diff1)
    reco_len = (((diff1 > 0) == (diff2 > 0)) * 1.).sum()

    ratio = reco_len / tot_len

    return tot_len, reco_len, ratio



def left_right_ambiguity(stree, X, track, deg=5):
    """
    Calculates efficiency of left-right ambiguity resolution for a track for all stations and views.

    Parameters
    ----------
    stree : root file
        Events in raw format.
    X : ndarray-like
        Information about active straw tubes: [[xtop, ytop, ztop, xbot, ybot, zboy, dist2wire, detID], [...], ...]
    track : array-like
        Hit indexes of a recognized track.
    deg : float
        Rotation degree of stereo views. Default 5 degree.

    Returns
    -------
    results : dict
        Dictionary with efficiency of left-right ambiguity resolution.
        Example: {'y12':[tot_len, reco_len, ratio], 'v1_12':[tot_len, reco_len, ratio], ...}
    """

    results = {}

    XYZ_hit = get_true_coords(stree, X)
    XYZ_tube = X[:, [0, 1, 2]]

    statnb, vnb, pnb, lnb, snb = decodeDetectorID(X[:, -1])


    track_inds = track['hits']

    params12 = track['params12']
    params34 = track['params34']

    if len(params12[0]) != 0:
        ky12, by12 = params12[0]
    else:
        return results

    if len(params12[1]) != 0:
        kx12, bx12 = params12[1]
    else:
        return results

    if len(params34[0]) != 0:
        ky34, by34 = params34[0]
    else:
        return results

    if len(params34[1]) != 0:
        kx34, bx34 = params34[1]
    else:
        return results

    r12 = numpy.matrix([[bx12],
                        [by12],
                        [0]])
    a12 = numpy.matrix([[kx12],
                        [ky12],
                        [1]])

    r34 = numpy.matrix([[bx34],
                        [by34],
                        [0]])
    a34 = numpy.matrix([[kx34],
                        [ky34],
                        [1]])

    Mplus = numpy.matrix([[numpy.cos(numpy.deg2rad(deg)), -numpy.sin(numpy.deg2rad(deg)), 0],
                          [ numpy.sin(numpy.deg2rad(deg)),  numpy.cos(numpy.deg2rad(deg)), 0],
                          [                           0,                            0, 1]]) # View 2

    Mminus = numpy.matrix([[numpy.cos(numpy.deg2rad(-deg)), -numpy.sin(numpy.deg2rad(-deg)), 0],
                          [ numpy.sin(numpy.deg2rad(-deg)),  numpy.cos(numpy.deg2rad(-deg)), 0],
                          [                           0,                            0, 1]]) # View 1


    is_v1 = ((vnb == 1))
    is_v2 = ((vnb == 2))
    is_y = ((vnb == 0) + (vnb == 3))
    is_before = ((statnb == 1) + (statnb == 2))
    is_after = ((statnb == 3) + (statnb == 4))

    track_inds_y12 = select_track_hits([track_inds], is_before * is_y)[0]
    track_inds_v1_12 = select_track_hits([track_inds], is_before * is_v1)[0]
    track_inds_v2_12 = select_track_hits([track_inds], is_before * is_v2)[0]

    track_inds_y34 = select_track_hits([track_inds], is_after * is_y)[0]
    track_inds_v1_34 = select_track_hits([track_inds], is_after * is_v1)[0]
    track_inds_v2_34 = select_track_hits([track_inds], is_after * is_v2)[0]


    #### Station 1&2

    ## Y views

    XYZ_hit_y12 = XYZ_hit[track_inds_y12]
    XYZ_tube_y12 = XYZ_tube[track_inds_y12]

    tot_len, reco_len, ratio = score(XYZ_tube_y12[:, 2],
                                     XYZ_tube_y12[:, 1],
                                     XYZ_hit_y12[:, 2],
                                     XYZ_hit_y12[:, 1],
                                     a12[1, 0],
                                     r12[1, 0])

    results['y12'] = [tot_len, reco_len, ratio]

    ## View 1

    XYZ_hit_v1_12 = XYZ_hit[track_inds_v1_12]
    XYZ_tube_v1_12 = XYZ_tube[track_inds_v1_12]

    XYZ_hit_v1_12 = numpy.array(Mminus * XYZ_hit_v1_12.T).T
    XYZ_tube_v1_12 = numpy.array(Mminus * XYZ_tube_v1_12.T).T

    aa12 = Mminus * a12
    rr12 = Mminus * r12

    tot_len, reco_len, ratio = score(XYZ_tube_v1_12[:, 2],
                                     XYZ_tube_v1_12[:, 1],
                                     XYZ_hit_v1_12[:, 2],
                                     XYZ_hit_v1_12[:, 1],
                                     aa12[1, 0],
                                     rr12[1, 0])

    results['v1_12'] = [tot_len, reco_len, ratio]

    ## View 2

    XYZ_hit_v2_12 = XYZ_hit[track_inds_v2_12]
    XYZ_tube_v2_12 = XYZ_tube[track_inds_v2_12]

    XYZ_hit_v2_12 = numpy.array(Mplus * XYZ_hit_v2_12.T).T
    XYZ_tube_v2_12 = numpy.array(Mplus * XYZ_tube_v2_12.T).T

    aa12 = Mplus * a12
    rr12 = Mplus * r12

    tot_len, reco_len, ratio = score(XYZ_tube_v2_12[:, 2],
                                     XYZ_tube_v2_12[:, 1],
                                     XYZ_hit_v2_12[:, 2],
                                     XYZ_hit_v2_12[:, 1],
                                     aa12[1, 0],
                                     rr12[1, 0])

    results['v2_12'] = [tot_len, reco_len, ratio]


    #### Station 3&4

    ## Y views

    XYZ_hit_y34 = XYZ_hit[track_inds_y34]
    XYZ_tube_y34 = XYZ_tube[track_inds_y34]

    tot_len, reco_len, ratio = score(XYZ_tube_y34[:, 2],
                                     XYZ_tube_y34[:, 1],
                                     XYZ_hit_y34[:, 2],
                                     XYZ_hit_y34[:, 1],
                                     a34[1, 0],
                                     r34[1, 0])

    results['y34'] = [tot_len, reco_len, ratio]

    ## View 1

    XYZ_hit_v1_34 = XYZ_hit[track_inds_v1_34]
    XYZ_tube_v1_34 = XYZ_tube[track_inds_v1_34]

    XYZ_hit_v1_34 = numpy.array(Mminus * XYZ_hit_v1_34.T).T
    XYZ_tube_v1_34 = numpy.array(Mminus * XYZ_tube_v1_34.T).T

    aa34 = Mminus * a34
    rr34 = Mminus * r34

    tot_len, reco_len, ratio = score(XYZ_tube_v1_34[:, 2],
                                     XYZ_tube_v1_34[:, 1],
                                     XYZ_hit_v1_34[:, 2],
                                     XYZ_hit_v1_34[:, 1],
                                     aa34[1, 0],
                                     rr34[1, 0])

    results['v1_34'] = [tot_len, reco_len, ratio]

    ## View 2

    XYZ_hit_v2_34 = XYZ_hit[track_inds_v2_34]
    XYZ_tube_v2_34 = XYZ_tube[track_inds_v2_34]

    XYZ_hit_v2_34 = numpy.array(Mplus * XYZ_hit_v2_34.T).T
    XYZ_tube_v2_34 = numpy.array(Mplus * XYZ_tube_v2_34.T).T

    aa34 = Mplus * a34
    rr34 = Mplus * r34

    tot_len, reco_len, ratio = score(XYZ_tube_v2_34[:, 2],
                                     XYZ_tube_v2_34[:, 1],
                                     XYZ_hit_v2_34[:, 2],
                                     XYZ_hit_v2_34[:, 1],
                                     aa34[1, 0],
                                     rr34[1, 0])

    results['v2_34'] = [tot_len, reco_len, ratio]


    return results




########################################## Main functions ##############################################################

def save_hists(h, path):
    """
    Save book of plots.

    Parameters
    ----------
    h : dict
        Dictionary of plots.
    path : string
        Path where the plots will be saved.
    """
    ut.writeHists(h, path)

def init_book_hist():
    """
    Creates empty plots.

    Returns
    -------
    h : dict
        Dictionary of plots.
    """

    h={} #dictionary of histograms

    ut.bookHist(h,'NTracks', 'Number of tracks in an event',20,0.,20.01)
    ut.bookHist(h,'NRecoTracks', 'Number of recognised tracks in an event',20,0.,20.01)

    ut.bookHist(h,'RecoEff_y12', 'Recognition Efficiency, Y view station 1&2',20,0.,1.01)
    ut.bookHist(h,'TrackEff_y12', 'Track Efficiency, Y view station 1&2',20,0.,1.01)
    ut.bookHist(h,'GhostRate_y12', 'Ghost Rate, Y view station 1&2',20,0.,1.01)
    ut.bookHist(h,'CloneRate_y12', 'Clone Rate, Y view station 1&2',20,0.,1.01)

    ut.bookHist(h,'RecoEff_stereo12', 'Recognition Efficiency, Stereo views station 1&2',20,0.,1.01)
    ut.bookHist(h,'TrackEff_stereo12', 'Track Efficiency, Stereo views station 1&2',20,0.,1.01)
    ut.bookHist(h,'GhostRate_stereo12', 'Ghost Rate, Stereo views station 1&2',20,0.,1.01)
    ut.bookHist(h,'CloneRate_stereo12', 'Clone Rate, Stereo views station 1&2',20,0.,1.01)

    ut.bookHist(h,'RecoEff_12', 'Recognition Efficiency, station 1&2',20,0.,1.01)
    ut.bookHist(h,'TrackEff_12', 'Track Efficiency, station 1&2',20,0.,1.01)
    ut.bookHist(h,'GhostRate_12', 'Ghost Rate, station 1&2',20,0.,1.01)
    ut.bookHist(h,'CloneRate_12', 'Clone Rate, station 1&2',20,0.,1.01)

    ut.bookHist(h,'RecoEff_y34', 'Recognition Efficiency, Y view station 3&4',20,0.,1.01)
    ut.bookHist(h,'TrackEff_y34', 'Track Efficiency, Y view station 3&4',20,0.,1.01)
    ut.bookHist(h,'GhostRate_y34', 'Ghost Rate, Y view station 3&4',20,0.,1.01)
    ut.bookHist(h,'CloneRate_y34', 'Clone Rate, Y view station 3&4',20,0.,1.01)

    ut.bookHist(h,'RecoEff_stereo34', 'Recognition Efficiency, Stereo views station 3&4',20,0.,1.01)
    ut.bookHist(h,'TrackEff_stereo34', 'Track Efficiency, Stereo views station 3&4',20,0.,1.01)
    ut.bookHist(h,'GhostRate_stereo34', 'Ghost Rate, Stereo views station 3&4',20,0.,1.01)
    ut.bookHist(h,'CloneRate_stereo34', 'Clone Rate, Stereo views station 3&4',20,0.,1.01)

    ut.bookHist(h,'RecoEff_34', 'Recognition Efficiency, station 3&4',20,0.,1.01)
    ut.bookHist(h,'TrackEff_34', 'Track Efficiency, station 3&4',20,0.,1.01)
    ut.bookHist(h,'GhostRate_34', 'Ghost Rate, station 3&4',20,0.,1.01)
    ut.bookHist(h,'CloneRate_34', 'Clone Rate, station 3&4',20,0.,1.01)

    ut.bookHist(h,'EventsPassed','Events passing the pattern recognition',9,-0.5,8.5)
    h['EventsPassed'].GetXaxis().SetBinLabel(1,"Reconstructible events")
    h['EventsPassed'].GetXaxis().SetBinLabel(2,"Y view station 1&2")
    h['EventsPassed'].GetXaxis().SetBinLabel(3,"Stereo station 1&2")
    h['EventsPassed'].GetXaxis().SetBinLabel(4,"station 1&2")
    h['EventsPassed'].GetXaxis().SetBinLabel(5,"Y view station 3&4")
    h['EventsPassed'].GetXaxis().SetBinLabel(6,"Stereo station 3&4")
    h['EventsPassed'].GetXaxis().SetBinLabel(7,"station 3&4")
    h['EventsPassed'].GetXaxis().SetBinLabel(8,"Combined stations 1&2/3&4")
    h['EventsPassed'].GetXaxis().SetBinLabel(9,"Matched")

    ut.bookHist(h,'TracksPassed','Tracks passing the pattern recognition',9,-0.5,8.5)
    h['TracksPassed'].GetXaxis().SetBinLabel(1,"Reconstructible tracks")
    h['TracksPassed'].GetXaxis().SetBinLabel(2,"Y view station 1&2")
    h['TracksPassed'].GetXaxis().SetBinLabel(3,"Stereo station 1&2")
    h['TracksPassed'].GetXaxis().SetBinLabel(4,"station 1&2")
    h['TracksPassed'].GetXaxis().SetBinLabel(5,"Y view station 3&4")
    h['TracksPassed'].GetXaxis().SetBinLabel(6,"Stereo station 3&4")
    h['TracksPassed'].GetXaxis().SetBinLabel(7,"station 3&4")
    h['TracksPassed'].GetXaxis().SetBinLabel(8,"Combined stations 1&2/3&4")
    h['TracksPassed'].GetXaxis().SetBinLabel(9,"Matched")

    ut.bookProf(h, 'TracksPassed_p', 'Tracks passing the pattern recognition from momentum', 30, 0, 150)
    h['TracksPassed_p'].GetXaxis().SetTitle('Momentum')
    h['TracksPassed_p'].GetYaxis().SetTitle('N')

    ut.bookHist(h,'ptrue-p/ptrue','(p - p-true)/p',200,-1.,1.)

    ut.bookHist(h,'n_hits_mc','Number of hits per track, total',64,0.,64.01)
    ut.bookHist(h,'n_hits_mc_12','Number of hits per track, station 1&2',32,0.,32.01)
    ut.bookHist(h,'n_hits_mc_y12','Number of hits per track, Y view station 1&2',16,0.,16.01)
    ut.bookHist(h,'n_hits_mc_stereo12','Number of hits per track, Stereo view station 1&2',16,0.,16.01)
    ut.bookHist(h,'n_hits_mc_34','Number of hits per track, station 3&4',32,0.,32.01)
    ut.bookHist(h,'n_hits_mc_y34','Number of hits per track, Y view station 3&4',16,0.,16.01)
    ut.bookHist(h,'n_hits_mc_stereo34','Number of hits per track, Stereo view station 3&4',16,0.,16.01)

    # Momentum dependencies
    ut.bookProf(h,'n_hits_mc_p','Number of hits per track, total', 30, 0, 150)
    h['n_hits_mc_p'].GetXaxis().SetTitle('Momentum')
    h['n_hits_mc_p'].GetYaxis().SetTitle('N')

    ut.bookProf(h,'n_hits_mc_12_p','Number of hits per track, station 1&2', 30, 0, 150)
    h['n_hits_mc_12_p'].GetXaxis().SetTitle('Momentum')
    h['n_hits_mc_12_p'].GetYaxis().SetTitle('N')

    ut.bookProf(h,'n_hits_mc_y12_p','Number of hits per track, Y view station 1&2', 30, 0, 150)
    h['n_hits_mc_y12_p'].GetXaxis().SetTitle('Momentum')
    h['n_hits_mc_y12_p'].GetYaxis().SetTitle('N')

    ut.bookProf(h,'n_hits_mc_stereo12_p','Number of hits per track, Stereo view station 1&2', 30, 0, 150)
    h['n_hits_mc_stereo12_p'].GetXaxis().SetTitle('Momentum')
    h['n_hits_mc_stereo12_p'].GetYaxis().SetTitle('N')

    ut.bookProf(h,'n_hits_mc_34_p','Number of hits per track, station 3&4', 30, 0, 150)
    h['n_hits_mc_34_p'].GetXaxis().SetTitle('Momentum')
    h['n_hits_mc_34_p'].GetYaxis().SetTitle('N')

    ut.bookProf(h,'n_hits_mc_y34_p','Number of hits per track, Y view station 3&4', 30, 0, 150)
    h['n_hits_mc_y34_p'].GetXaxis().SetTitle('Momentum')
    h['n_hits_mc_y34_p'].GetYaxis().SetTitle('N')

    ut.bookProf(h,'n_hits_mc_stereo34_p','Number of hits per track, Stereo view station 3&4', 30, 0, 150)
    h['n_hits_mc_stereo34_p'].GetXaxis().SetTitle('Momentum')
    h['n_hits_mc_stereo34_p'].GetYaxis().SetTitle('N')



    ut.bookHist(h,'n_hits_reco','Number of recognized hits per track, total',64,0.,64.01)
    ut.bookHist(h,'n_hits_reco_12','Number of recognized hits per track, station 1&2',32,0.,32.01)
    ut.bookHist(h,'n_hits_reco_y12','Number of recognized hits per track, Y view station 1&2',32,0.,32.01)
    ut.bookHist(h,'n_hits_reco_stereo12','Number of recognized hits per track, Stereo view station 1&2',32,0.,32.01)
    ut.bookHist(h,'n_hits_reco_34','Number of recognized hits per track, station 3&4',32,0.,32.01)
    ut.bookHist(h,'n_hits_reco_y34','Number of recognized hits per track, Y view station 3&4',32,0.,32.01)
    ut.bookHist(h,'n_hits_reco_stereo34','Number of recognized hits per track, Stereo view station 3&4',32,0.,32.01)

    # Momentum dependences
    ut.bookProf(h, 'n_hits_total', 'Number of recognized hits per track, total', 30, 0, 150)
    h['n_hits_total'].GetXaxis().SetTitle('Momentum')
    h['n_hits_total'].GetYaxis().SetTitle('N')

    ut.bookProf(h, 'n_hits_y12', 'Number of recognized hits per track, Y view station 1&2', 30, 0, 150)
    h['n_hits_y12'].GetXaxis().SetTitle('Momentum')
    h['n_hits_y12'].GetYaxis().SetTitle('N')

    ut.bookProf(h, 'n_hits_stereo12', 'Number of recognized hits per track, Stereo view station 1&2', 30, 0, 150)
    h['n_hits_stereo12'].GetXaxis().SetTitle('Momentum')
    h['n_hits_stereo12'].GetYaxis().SetTitle('N')

    ut.bookProf(h, 'n_hits_12', 'Number of recognized hits per track, station 1&2', 30, 0, 150)
    h['n_hits_12'].GetXaxis().SetTitle('Momentum')
    h['n_hits_12'].GetYaxis().SetTitle('N')

    ut.bookProf(h, 'n_hits_y34', 'Number of recognized hits per track, Y view station 3&4', 30, 0, 150)
    h['n_hits_y34'].GetXaxis().SetTitle('Momentum')
    h['n_hits_y34'].GetYaxis().SetTitle('N')

    ut.bookProf(h, 'n_hits_stereo34', 'Number of recognized hits per track, Stereo view station 3&4', 30, 0, 150)
    h['n_hits_stereo34'].GetXaxis().SetTitle('Momentum')
    h['n_hits_stereo34'].GetYaxis().SetTitle('N')

    ut.bookProf(h, 'n_hits_34', 'Number of recognized hits per track, station 3&4', 30, 0, 150)
    h['n_hits_34'].GetXaxis().SetTitle('Momentum')
    h['n_hits_34'].GetYaxis().SetTitle('N')

    ut.bookProf(h,'perr','(p - p-true)/p',30, 0, 150)
    h['perr'].GetXaxis().SetTitle('Momentum')
    h['perr'].GetYaxis().SetTitle('(p - p-true)/p')

    ut.bookProf(h,'perr_direction','(p - p-true)/p from track direction in YZ plane',40, -10.01, 10.01)
    h['perr_direction'].GetXaxis().SetTitle('Degree')
    h['perr_direction'].GetYaxis().SetTitle('(p - p-true)/p')


    ut.bookProf(h, 'frac_total', 'Fraction of hits the same as MC hits, total', 30, 0, 150)
    h['frac_total'].GetXaxis().SetTitle('Momentum')
    h['frac_total'].GetYaxis().SetTitle('Fraction')

    ut.bookProf(h, 'frac_y12', 'Fraction of hits the same as MC hits, Y view station 1&2', 30, 0, 150)
    h['frac_y12'].GetXaxis().SetTitle('Momentum')
    h['frac_y12'].GetYaxis().SetTitle('Fraction')

    ut.bookProf(h, 'frac_stereo12', 'Fraction of hits the same as MC hits, Stereo view station 1&2', 30, 0, 150)
    h['frac_stereo12'].GetXaxis().SetTitle('Momentum')
    h['frac_stereo12'].GetYaxis().SetTitle('Fraction')

    ut.bookProf(h, 'frac_12', 'Fraction of hits the same as MC hits, station 1&2', 30, 0, 150)
    h['frac_12'].GetXaxis().SetTitle('Momentum')
    h['frac_12'].GetYaxis().SetTitle('Fraction')

    ut.bookProf(h, 'frac_y34', 'Fraction of hits the same as MC hits, Y view station 3&4', 30, 0, 150)
    h['frac_y34'].GetXaxis().SetTitle('Momentum')
    h['frac_y34'].GetYaxis().SetTitle('Fraction')

    ut.bookProf(h, 'frac_stereo34', 'Fraction of hits the same as MC hits, Stereo view station 3&4', 30, 0, 150)
    h['frac_stereo34'].GetXaxis().SetTitle('Momentum')
    h['frac_stereo34'].GetYaxis().SetTitle('Fraction')

    ut.bookProf(h, 'frac_34', 'Fraction of hits the same as MC hits, station 3&4', 30, 0, 150)
    h['frac_34'].GetXaxis().SetTitle('Momentum')
    h['frac_34'].GetYaxis().SetTitle('Fraction')


    ut.bookProf(h, 'frac_total_angle', 'Fraction of hits the same as MC hits, total', 20, 0, 10.01)
    h['frac_total_angle'].GetXaxis().SetTitle('Angle between tracks, degree')
    h['frac_total_angle'].GetYaxis().SetTitle('Fraction')


    # Fitted values
    ut.bookHist(h,'chi2fittedtracks','Chi^2 per NDOF for fitted tracks',210,-0.05,20.05)
    ut.bookHist(h,'pvalfittedtracks','pval for fitted tracks',110,-0.05,1.05)
    ut.bookHist(h,'momentumfittedtracks','momentum for fitted tracks',251,-0.05,250.05)
    ut.bookHist(h,'xdirectionfittedtracks','x-direction for fitted tracks',91,-0.5,90.5)
    ut.bookHist(h,'ydirectionfittedtracks','y-direction for fitted tracks',91,-0.5,90.5)
    ut.bookHist(h,'zdirectionfittedtracks','z-direction for fitted tracks',91,-0.5,90.5)
    ut.bookHist(h,'massfittedtracks','mass fitted tracks',210,-0.005,0.205)
    ut.bookHist(h,'pvspfitted','p-patrec vs p-fitted',401,-200.5,200.5,401,-200.5,200.5)

    # left_right_ambiguity
    ut.bookHist(h,'left_right_ambiguity_y12','Left Right Ambiguity Resolution Efficiency, Y view station 1&2',10,0.,1.01)
    ut.bookHist(h,'left_right_ambiguity_stereo12','Left Right Ambiguity Resolution Efficiency, Stereo view station 1&2',10,0.,1.01)
    ut.bookHist(h,'left_right_ambiguity_y34','Left Right Ambiguity Resolution Efficiency, Y view station 3&4',10,0.,1.01)
    ut.bookHist(h,'left_right_ambiguity_stereo34','Left Right Ambiguity Resolution Efficiency, Stereo view station 3&4',10,0.,1.01)
    ut.bookHist(h,'left_right_ambiguity','Left Right Ambiguity Resolution Efficiency, Total',10,0.,1.01)

    ut.bookProf(h, 'n_hits_y12_direction', 'Number of recognized hits per track, Y view station 1&2', 40, -10.01, 10.01)
    h['n_hits_y12_direction'].GetXaxis().SetTitle('Degree')
    h['n_hits_y12_direction'].GetYaxis().SetTitle('N')

    ut.bookProf(h, 'n_hits_stereo12_direction', 'Number of recognized hits per track, Stereo view station 1&2', 40, -10.01, 10.01)
    h['n_hits_stereo12_direction'].GetXaxis().SetTitle('Degree')
    h['n_hits_stereo12_direction'].GetYaxis().SetTitle('N')

    ut.bookProf(h, 'n_hits_y34_direction', 'Number of recognized hits per track, Y view station 3&4', 40, -10.01, 10.01)
    h['n_hits_y34_direction'].GetXaxis().SetTitle('Degree')
    h['n_hits_y34_direction'].GetYaxis().SetTitle('N')

    ut.bookProf(h, 'n_hits_stereo34_direction', 'Number of recognized hits per track, Stereo view station 3&4', 40, -10.01, 10.01)
    h['n_hits_stereo34_direction'].GetXaxis().SetTitle('Degree')
    h['n_hits_stereo34_direction'].GetYaxis().SetTitle('N')


    ut.bookHist(h,'duplicates_tot','Fraction of hit duplicates per track, Total', 20 ,0., 1.01)
    ut.bookHist(h,'duplicates_y12','Fraction of hit duplicates per track, Y view station 1&2', 20 ,0., 1.01)



    return h

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


def quality_metrics(smeared_hits, stree, reco_mc_tracks, reco_tracks, theTracks, h):
    """
    Fill plots with values.

    Parameters
    ----------
    smeared_hits : list of dicts
        List of smeared hits. A smeared hit is a dictionary:
        {'digiHit':key,'xtop':top x,'ytop':top y,'z':top z,'xbot':bot x,'ybot':bot y,'dist':smeared dist2wire}
    stree : root file
        Events in raw format.
    reco_mc_tracks : array-like
        List of reconstructible track ids.
    reco_tracks : dict
        Dictionary of recognized tracks: {track_id: reco_track}.
        Reco_track is a dictionary:
        {'hits': [ind1, ind2, ind3, ...],
         'hitPosList': X[atrack, :-1],
         'charge': charge,
         'pinv': pinv,
         'params12': [[k_yz, b_yz], [k_xz, b_xz]],
         'params34': [[k_yz, b_yz], [k_xz, b_xz]]}
    theTracks : array-like
        List of fitted tracks.
    h : dict
        Dictionary of plots.
    """

    ############################################## Init preparation ####################################################

    # Only for reconstructible events.
    if len(reco_mc_tracks) < 2:
        return

    X = Digitization(stree,smeared_hits)
    y = get_track_ids(stree, smeared_hits)

    n_tracks = len(numpy.unique(y))
    h['NTracks'].Fill(n_tracks)

    track_inds = [atrack['hits'] for atrack in reco_tracks.values()]
    statnb, vnb, pnb, lnb, snb = decodeDetectorID(X[:, -1])

    n_reco_tracks = len(track_inds)
    h['NRecoTracks'].Fill(n_reco_tracks)

    ######################################## Split hits on stations and views ##########################################

    is_stereo = ((vnb == 1) + (vnb == 2))
    is_y = ((vnb == 0) + (vnb == 3))
    is_before = ((statnb == 1) + (statnb == 2))
    is_after = ((statnb == 3) + (statnb == 4))

    track_inds_y12 = select_track_hits(track_inds, is_before * is_y)
    track_inds_stereo12 = select_track_hits(track_inds, is_before * is_stereo)
    track_inds_12 = select_track_hits(track_inds, is_before)

    track_inds_y34 = select_track_hits(track_inds, is_after * is_y)
    track_inds_stereo34 = select_track_hits(track_inds, is_after * is_stereo)
    track_inds_34 = select_track_hits(track_inds, is_after)


    ######################## RecoEff, Clone and Ghost rates, TrackEff for stations and views ###########################

    # Pinv
    pinvs = get_pinvs(stree, smeared_hits)

    # N hits
    for t in reco_mc_tracks:

        if t not in y:
            continue

        pinv_true = pinvs[y == t][0]
        p = 1. / pinv_true

        n_y12 = len(y[(y == t) * is_before * is_y])
        n_stereo12 = len(y[(y == t) * is_before * is_stereo])
        n_12 = len(y[(y == t) * is_before])

        n_y34 = len(y[(y == t) * is_after * is_y])
        n_stereo34 = len(y[(y == t) * is_after * is_stereo])
        n_34 = len(y[(y == t) * is_after])

        n_tot = len(y[(y == t)])

        h['n_hits_mc'].Fill(n_tot)

        h['n_hits_mc_12'].Fill(n_12)
        h['n_hits_mc_y12'].Fill(n_y12)
        h['n_hits_mc_stereo12'].Fill(n_stereo12)

        h['n_hits_mc_34'].Fill(n_34)
        h['n_hits_mc_y34'].Fill(n_y34)
        h['n_hits_mc_stereo34'].Fill(n_stereo34)

        # Momentum dependencies
        h['n_hits_mc_p'].Fill(p, n_tot)

        h['n_hits_mc_12_p'].Fill(p, n_12)
        h['n_hits_mc_y12_p'].Fill(p, n_y12)
        h['n_hits_mc_stereo12_p'].Fill(p, n_stereo12)

        h['n_hits_mc_34_p'].Fill(p, n_34)
        h['n_hits_mc_y34_p'].Fill(p, n_y34)
        h['n_hits_mc_stereo34_p'].Fill(p, n_stereo34)


    for i in range(len(track_inds)):

        n_y12 = len(track_inds_y12[i])
        n_stereo12 = len(track_inds_stereo12[i])
        n_12 = len(track_inds_12[i])

        n_y34 = len(track_inds_y34[i])
        n_stereo34 = len(track_inds_stereo34[i])
        n_34 = len(track_inds_34[i])

        n_tot = len(track_inds[i])

        h['n_hits_reco'].Fill(n_tot)

        h['n_hits_reco_12'].Fill(n_12)
        h['n_hits_reco_y12'].Fill(n_y12)
        h['n_hits_reco_stereo12'].Fill(n_stereo12)

        h['n_hits_reco_34'].Fill(n_34)
        h['n_hits_reco_y34'].Fill(n_y34)
        h['n_hits_reco_stereo34'].Fill(n_stereo34)


    # Y view station 1&2
    hme_y12 = HitsMatchingEfficiency(eff_threshold=0.5, n_tracks=None)
    hme_y12.fit(y, track_inds_y12)
    reco_eff = hme_y12.recognition_efficiency_
    ghost_rate = hme_y12.ghost_rate_
    clone_rate = hme_y12.clone_rate_
    track_eff = hme_y12.efficiencies_

    h['RecoEff_y12'].Fill(reco_eff)
    h['GhostRate_y12'].Fill(ghost_rate)
    h['CloneRate_y12'].Fill(clone_rate)
    for i in track_eff:
        h['TrackEff_y12'].Fill(i)

    track_ids_y12 = []
    for atrack in track_inds_y12:

        frac, tmax = fracMCsame(y[atrack])
        track_ids_y12.append(tmax)


    # Stereo views station 1&2
    hme_stereo12 = HitsMatchingEfficiency(eff_threshold=0.5, n_tracks=None)
    hme_stereo12.fit(y, track_inds_stereo12)
    reco_eff = hme_stereo12.recognition_efficiency_
    ghost_rate = hme_stereo12.ghost_rate_
    clone_rate = hme_stereo12.clone_rate_
    track_eff = hme_stereo12.efficiencies_

    h['RecoEff_stereo12'].Fill(reco_eff)
    h['GhostRate_stereo12'].Fill(ghost_rate)
    h['CloneRate_stereo12'].Fill(clone_rate)
    for i in track_eff:
        h['TrackEff_stereo12'].Fill(i)

    track_ids_stereo12 = []
    for atrack in track_inds_stereo12:

        frac, tmax = fracMCsame(y[atrack])
        track_ids_stereo12.append(tmax)

    # Station 1&2
    hme_12 = HitsMatchingEfficiency(eff_threshold=0.5, n_tracks=None)
    hme_12.fit(y, track_inds_12)
    reco_eff = hme_12.recognition_efficiency_
    ghost_rate = hme_12.ghost_rate_
    clone_rate = hme_12.clone_rate_
    track_eff = hme_12.efficiencies_

    h['RecoEff_12'].Fill(reco_eff)
    h['GhostRate_12'].Fill(ghost_rate)
    h['CloneRate_12'].Fill(clone_rate)
    for i in track_eff:
        h['TrackEff_12'].Fill(i)

    track_ids_12 = []
    for atrack in track_inds_12:

        frac, tmax = fracMCsame(y[atrack])
        track_ids_12.append(tmax)

    # Y view station 3&4
    hme_y34 = HitsMatchingEfficiency(eff_threshold=0.5, n_tracks=None)
    hme_y34.fit(y, track_inds_y34)
    reco_eff = hme_y34.recognition_efficiency_
    ghost_rate = hme_y34.ghost_rate_
    clone_rate = hme_y34.clone_rate_
    track_eff = hme_y34.efficiencies_

    h['RecoEff_y34'].Fill(reco_eff)
    h['GhostRate_y34'].Fill(ghost_rate)
    h['CloneRate_y34'].Fill(clone_rate)
    for i in track_eff:
        h['TrackEff_y34'].Fill(i)

    track_ids_y34 = []
    for atrack in track_inds_y34:

        frac, tmax = fracMCsame(y[atrack])
        track_ids_y34.append(tmax)

    # Stereo views station 3&4
    hme_stereo34 = HitsMatchingEfficiency(eff_threshold=0.5, n_tracks=None)
    hme_stereo34.fit(y, track_inds_stereo34)
    reco_eff = hme_stereo34.recognition_efficiency_
    ghost_rate = hme_stereo34.ghost_rate_
    clone_rate = hme_stereo34.clone_rate_
    track_eff = hme_stereo34.efficiencies_

    h['RecoEff_stereo34'].Fill(reco_eff)
    h['GhostRate_stereo34'].Fill(ghost_rate)
    h['CloneRate_stereo34'].Fill(clone_rate)
    for i in track_eff:
        h['TrackEff_stereo34'].Fill(i)

    track_ids_stereo34 = []
    for atrack in track_inds_stereo34:

        frac, tmax = fracMCsame(y[atrack])
        track_ids_stereo34.append(tmax)

    # Station 3&4
    hme_34 = HitsMatchingEfficiency(eff_threshold=0.5, n_tracks=None)
    hme_34.fit(y, track_inds_34)
    reco_eff = hme_34.recognition_efficiency_
    ghost_rate = hme_34.ghost_rate_
    clone_rate = hme_34.clone_rate_
    track_eff = hme_34.efficiencies_

    h['RecoEff_34'].Fill(reco_eff)
    h['GhostRate_34'].Fill(ghost_rate)
    h['CloneRate_34'].Fill(clone_rate)
    for i in track_eff:
        h['TrackEff_34'].Fill(i)

    track_ids_34 = []
    for atrack in track_inds_34:

        frac, tmax = fracMCsame(y[atrack])
        track_ids_34.append(tmax)


################################################# Events Passed ########################################################

    # Track combinations
    combinations = []
    for track_id in range(len(track_inds)):

        track_before = track_inds_12[track_id]
        track_after = track_inds_34[track_id]

        frac12, tmax12 = fracMCsame(y[track_before])
        frac34, tmax34 = fracMCsame(y[track_after])

        if tmax12 == tmax34:
            combinations.append(tmax12)

    unique_combs = numpy.unique(combinations)
    if len(unique_combs[numpy.in1d(unique_combs, reco_mc_tracks)]) == len(reco_mc_tracks):
        is_combined = 1
    else:
        is_combined = 0

    # Matching
    is_matched = numpy.zeros(len(reco_mc_tracks))
    charges = get_charges(stree, smeared_hits)

    for num, track_id in enumerate(reco_mc_tracks):
        for i in reco_tracks.keys():

            atrack = reco_tracks[i]['hits']
            frac, tmax = fracMCsame(y[atrack])
            if tmax == track_id:
                true_charge = charges[y == tmax][0]
                reco_charge = reco_tracks[i]['charge']
                if reco_charge == true_charge:
                    is_matched[num] = 1


    # Events Passed
    if len(reco_mc_tracks) == 2:
        h['EventsPassed'].Fill("Reconstructible events", 1)

        if len(numpy.intersect1d(track_ids_y12, reco_mc_tracks)) == len(reco_mc_tracks):
            h['EventsPassed'].Fill("Y view station 1&2", 1)

            if len(numpy.intersect1d(track_ids_stereo12, reco_mc_tracks)) == len(reco_mc_tracks):
                h['EventsPassed'].Fill("Stereo station 1&2", 1)

                if len(numpy.intersect1d(track_ids_12, reco_mc_tracks)) == len(reco_mc_tracks):
                    h['EventsPassed'].Fill("station 1&2", 1)

                    if len(numpy.intersect1d(track_ids_y34, reco_mc_tracks)) == len(reco_mc_tracks):
                        h['EventsPassed'].Fill("Y view station 3&4", 1)

                        if len(numpy.intersect1d(track_ids_stereo34, reco_mc_tracks)) == len(reco_mc_tracks):
                            h['EventsPassed'].Fill("Stereo station 3&4", 1)

                            if len(numpy.intersect1d(track_ids_34, reco_mc_tracks)) == len(reco_mc_tracks):
                                h['EventsPassed'].Fill("station 3&4", 1)

                                if is_combined == 1:
                                    h['EventsPassed'].Fill("Combined stations 1&2/3&4", 1)

                                    if is_matched.sum() == len(reco_mc_tracks):
                                        h['EventsPassed'].Fill("Matched", 1)


    ################################################ Tracks Passed #####################################################

    # Reco Tracks
    pinvs = get_pinvs(stree, smeared_hits)
    charges = get_charges(stree, smeared_hits)

    if len(reco_mc_tracks) == 2:
        h['TracksPassed'].Fill("Reconstructible tracks", 1)
        h['TracksPassed'].Fill("Reconstructible tracks", 1)

    for i in reco_tracks.keys():

        atrack = reco_tracks[i]['hits']
        frac, tmax = fracMCsame(y[atrack])

        if tmax not in reco_mc_tracks:
            continue

        pinv_true = pinvs[y == tmax][0]

        true_charge = charges[y == tmax][0]
        reco_charge = reco_tracks[i]['charge']

        reco = 0

        try:
            tmax_y12 = track_ids_y12[i]
            tmax_stereo12 = track_ids_stereo12[i]
            tmax_12 = track_ids_12[i]

            tmax_y34 = track_ids_y34[i]
            tmax_stereo34 = track_ids_stereo34[i]
            tmax_34 = track_ids_34[i]
        except:
            h['TracksPassed_p'].Fill(1. / pinv_true, reco)
            continue

        if tmax_y12 in reco_mc_tracks:
            h['TracksPassed'].Fill("Y view station 1&2", 1)

            if tmax_stereo12 in reco_mc_tracks and tmax_stereo12 == tmax_y12:
                h['TracksPassed'].Fill("Stereo station 1&2", 1)

                if tmax_12 in reco_mc_tracks and tmax_12 == tmax_stereo12:
                    h['TracksPassed'].Fill("station 1&2", 1)

                    if tmax_y34 in reco_mc_tracks:
                        h['TracksPassed'].Fill("Y view station 3&4", 1)

                        if tmax_stereo34 in reco_mc_tracks and tmax_stereo34 == tmax_y34:
                            h['TracksPassed'].Fill("Stereo station 3&4", 1)

                            if tmax_34 in reco_mc_tracks and tmax_34 == tmax_stereo34:
                                h['TracksPassed'].Fill("station 3&4", 1)

                                if tmax_34 == tmax_12:
                                    h['TracksPassed'].Fill("Combined stations 1&2/3&4", 1)

                                    if true_charge == reco_charge:
                                        h['TracksPassed'].Fill("Matched", 1)
                                        reco = 1

        h['TracksPassed_p'].Fill(1. / pinv_true, reco)


    ########################################### Momentum reconstruction ################################################

    # Pinv
    pinvs = get_pinvs(stree, smeared_hits)

    for i in reco_tracks.keys():

        atrack = reco_tracks[i]['hits']
        frac, tmax = fracMCsame(y[atrack])
        pinv_true = pinvs[y == tmax][0]
        pinv = reco_tracks[i]['pinv']
        charge = reco_tracks[i]['charge']

        if tmax not in reco_mc_tracks:
            continue

        err = 1 - charge * pinv / pinv_true

        h['ptrue-p/ptrue'].Fill(err)
        h['perr'].Fill(1./pinv_true, err)

        params12 = reco_tracks[i]['params12']
        params34 = reco_tracks[i]['params34']

        if len(params12[0]) != 0:
            ky12, by12 = params12[0]
        else:
            continue

        if len(params12[1]) != 0:
            kx12, bx12 = params12[1]
        else:
            continue

        if len(params34[0]) != 0:
            ky34, by34 = params34[0]
        else:
            continue

        if len(params34[1]) != 0:
            kx34, bx34 = params34[1]
        else:
            continue

        deg = numpy.rad2deg(numpy.arctan(ky12))
        h['perr_direction'].Fill(deg, err)


    ########################################### Momentum dependencies  #################################################

    for i in reco_tracks.keys():

        atrack = reco_tracks[i]['hits']
        frac, tmax = fracMCsame(y[atrack])

        if tmax not in reco_mc_tracks:
            continue

        pinv_true = pinvs[y == tmax][0]
        p = 1. / pinv_true

        params12 = reco_tracks[i]['params12']
        params34 = reco_tracks[i]['params34']

        if len(params12[0]) != 0:
            ky12, by12 = params12[0]
        else:
            continue

        if len(params12[1]) != 0:
            kx12, bx12 = params12[1]
        else:
            continue

        if len(params34[0]) != 0:
            ky34, by34 = params34[0]
        else:
            continue

        if len(params34[1]) != 0:
            kx34, bx34 = params34[1]
        else:
            continue

        frac_total, tmax_total = fracMCsame(y[atrack])
        n_hits_total = len(atrack[y[atrack] == tmax_total])
        h['n_hits_total'].Fill(p, n_hits_total)
        h['frac_total'].Fill(p, frac_total)

        mask_y12 = (is_before * is_y)[atrack]
        frac_y12, tmax_y12 = fracMCsame(y[atrack[mask_y12]])
        atrack_y12 = atrack[mask_y12]
        n_hits_y12 = len(atrack_y12[y[atrack_y12] == tmax_y12])
        h['n_hits_y12'].Fill(p, n_hits_y12)
        h['frac_y12'].Fill(p, frac_y12)
        h['n_hits_y12_direction'].Fill(numpy.rad2deg(numpy.arctan(ky12)), n_hits_y12)

        mask_stereo12 = (is_before * is_stereo)[atrack]
        frac_stereo12, tmax_stereo12 = fracMCsame(y[atrack[mask_stereo12]])
        atrack_stereo12 = atrack[mask_stereo12]
        n_hits_stereo12 = len(atrack_stereo12[y[atrack_stereo12] == tmax_stereo12])
        h['n_hits_stereo12'].Fill(p, n_hits_stereo12)
        h['frac_stereo12'].Fill(p, frac_stereo12)
        h['n_hits_stereo12_direction'].Fill(numpy.rad2deg(numpy.arctan(kx12)), n_hits_stereo12)

        mask_12 = (is_before)[atrack]
        frac_12, tmax_12 = fracMCsame(y[atrack[mask_12]])
        atrack_12 = atrack[mask_12]
        n_hits_12 = len(atrack_12[y[atrack_12] == tmax_12])
        h['n_hits_12'].Fill(p, n_hits_12)
        h['frac_12'].Fill(p, frac_12)

        mask_y34 = (is_after * is_y)[atrack]
        frac_y34, tmax_y34 = fracMCsame(y[atrack[mask_y34]])
        atrack_y34 = atrack[mask_y34]
        n_hits_y34 = len(atrack_y34[y[atrack_y34] == tmax_y34])
        h['n_hits_y34'].Fill(p, n_hits_y34)
        h['frac_y34'].Fill(p, frac_y34)
        h['n_hits_y34_direction'].Fill(numpy.rad2deg(numpy.arctan(ky34)), n_hits_y34)

        mask_stereo34 = (is_after * is_stereo)[atrack]
        frac_stereo34, tmax_stereo34 = fracMCsame(y[atrack[mask_stereo34]])
        atrack_stereo34 = atrack[mask_stereo34]
        n_hits_stereo34 = len(atrack_stereo34[y[atrack_stereo34] == tmax_stereo34])
        h['n_hits_stereo34'].Fill(p, n_hits_stereo34)
        h['frac_stereo34'].Fill(p, frac_stereo34)
        h['n_hits_stereo34_direction'].Fill(numpy.rad2deg(numpy.arctan(kx34)), n_hits_stereo34)

        mask_34 = (is_after)[atrack]
        frac_34, tmax_34 = fracMCsame(y[atrack[mask_34]])
        atrack34 = atrack[mask_34]
        n_hits_34 = len(atrack34[y[atrack34] == tmax_34])
        h['n_hits_34'].Fill(p, n_hits_34)
        h['frac_34'].Fill(p, frac_34)


    #################################### Angle between two reconstructible tracks ######################################
    # Attention: Works only for two reconstructible tracks.

    angle = None
    alpha1 = None
    alpha2 = None

    for i in reco_tracks.keys():

        atrack = reco_tracks[i]['hits']
        frac, tmax = fracMCsame(y[atrack])

        if tmax not in reco_mc_tracks:
            continue

        pinv_true = pinvs[y == tmax][0]
        p = 1. / pinv_true

        params12 = reco_tracks[i]['params12']
        params34 = reco_tracks[i]['params34']

        if len(params12[0]) != 0:
            ky12, by12 = params12[0]
        else:
            continue

        if len(params12[1]) != 0:
            kx12, bx12 = params12[1]
        else:
            continue

        if len(params34[0]) != 0:
            ky34, by34 = params34[0]
        else:
            continue

        if len(params34[1]) != 0:
            kx34, bx34 = params34[1]
        else:
            continue

        if tmax == reco_mc_tracks[0] and alpha1 == None:
            alpha1 = numpy.rad2deg(numpy.arctan(ky12))

        if tmax == reco_mc_tracks[1] and alpha2 == None:
            alpha2 = numpy.rad2deg(numpy.arctan(ky12))


    if alpha1 != None and alpha2 != None:
        angle = numpy.abs(alpha2 - alpha1)


    ############################################ The angle dependencies ################################################

    for i in reco_tracks.keys():

        atrack = reco_tracks[i]['hits']
        frac, tmax = fracMCsame(y[atrack])

        if tmax not in reco_mc_tracks:
            continue

        pinv_true = pinvs[y == tmax][0]
        p = 1. / pinv_true

        n_hits_total = len(atrack)
        frac_total, tmax_total = fracMCsame(y[atrack])

        if angle != None:
            h['frac_total_angle'].Fill(angle, frac_total)


    ################################################# Track fit ########################################################

    for i, thetrack in enumerate(theTracks):

        atrack = reco_tracks[i]['hits']
        frac, tmax = fracMCsame(y[atrack])

        if tmax not in reco_mc_tracks:
            continue

        fitStatus   = thetrack.getFitStatus()
        thetrack.prune("CFL") # http://sourceforge.net/p/genfit/code/HEAD/tree/trunk/core/include/Track.h#l280

        nmeas = fitStatus.getNdf()
        pval = fitStatus.getPVal()
        chi2 = fitStatus.getChi2() / nmeas

        h['chi2fittedtracks'].Fill(chi2)
        h['pvalfittedtracks'].Fill(pval)

        fittedState = thetrack.getFittedState()
        fittedMom = fittedState.getMomMag()
        fittedMom = fittedMom*int(charge)

        if math.fabs(pinv) > 0.0 :
            h['pvspfitted'].Fill(1./pinv,fittedMom)
        fittedtrackDir = fittedState.getDir()
        fittedx=math.degrees(math.acos(fittedtrackDir[0]))
        fittedy=math.degrees(math.acos(fittedtrackDir[1]))
        fittedz=math.degrees(math.acos(fittedtrackDir[2]))
        fittedmass = fittedState.getMass()
        h['momentumfittedtracks'].Fill(fittedMom)
        h['xdirectionfittedtracks'].Fill(fittedx)
        h['ydirectionfittedtracks'].Fill(fittedy)
        h['zdirectionfittedtracks'].Fill(fittedz)
        h['massfittedtracks'].Fill(fittedmass)


    ############################################ left-right ambiguity ##################################################

    for i in reco_tracks.keys():

        atrack = reco_tracks[i]['hits']
        frac, tmax = fracMCsame(y[atrack])

        if tmax not in reco_mc_tracks:
            continue

        res = left_right_ambiguity(stree, X, reco_tracks[i], deg=5)
        if res == {}:
            continue

        tot_len_y12, reco_len_y12, ratio_y12 = res['y12']
        tot_len_v1_12, reco_len_v1_12, ratio_v1_12 = res['v1_12']
        tot_len_v2_12, reco_len_v2_12, ratio_v2_12 = res['v2_12']
        ratio_stereo12 = 1. * (reco_len_v1_12 + reco_len_v2_12) / (tot_len_v1_12 + tot_len_v2_12)

        tot_len_y34, reco_len_y34, ratio_y34 = res['y34']
        tot_len_v1_34, reco_len_v1_34, ratio_v1_34 = res['v1_34']
        tot_len_v2_34, reco_len_v2_34, ratio_v2_34 = res['v2_34']
        ratio_stereo34 = 1. * (reco_len_v1_34 + reco_len_v2_34) / (tot_len_v1_34 + tot_len_v2_34)

        ratio_total = 1. * (reco_len_y12 + reco_len_v1_12 + reco_len_v2_12 +
                          reco_len_y34 + reco_len_v1_34 + reco_len_v2_34) / \
                      (tot_len_y12 + tot_len_v1_12 + tot_len_v2_12 +
                       tot_len_y34 + tot_len_v1_34 + tot_len_v2_34)


        h['left_right_ambiguity_y12'].Fill(ratio_y12)
        h['left_right_ambiguity_stereo12'].Fill(ratio_stereo12)
        h['left_right_ambiguity_y34'].Fill(ratio_y34)
        h['left_right_ambiguity_stereo34'].Fill(ratio_stereo34)
        h['left_right_ambiguity'].Fill(ratio_total)


    ################################################ Hit Duplicates ####################################################

    for t in reco_mc_tracks:

        if t not in y:
            continue

        detid = X[:, -1]

        atrack_mask_tot = (y == t)
        atrack_detid = detid[atrack_mask_tot]
        other_detid = detid[~atrack_mask_tot]
        n_dup_tot = len(set(atrack_detid) & set(other_detid))
        frac_dup_tot = 1. * n_dup_tot / len(atrack_detid)
        h['duplicates_tot'].Fill(frac_dup_tot)

        atrack_mask_y12 = (y == t) * is_before * is_y
        atrack_detid = detid[atrack_mask_y12]
        other_detid = detid[~atrack_mask_y12]
        n_dup_y12 = len(set(atrack_detid) & set(other_detid))
        frac_dup_y12 = 1. * n_dup_y12 / len(atrack_detid)
        h['duplicates_y12'].Fill(frac_dup_y12)



    return