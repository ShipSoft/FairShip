__author__ = 'Mikhail Hushchyn'


import ROOT
import numpy
import rootUtils as ut

from utils import fracMCsame
from digitization import Digitization
from mctruth import get_track_ids

################################################ Helping functions #####################################################

class HitsMatchingEfficiency(object):
    def __init__(self, eff_threshold=0.5, n_tracks=None):
        """
        This class calculates tracks efficiencies, reconstruction efficiency, ghost rate and clone rate for one event using hits matching.
        :param eff_threshold: float, threshold value of a track efficiency to consider a track reconstructed.
        :return:
        """

        self.eff_threshold = eff_threshold
        self.n_tracks = n_tracks

    def fit(self, true_labels, track_inds):
        """
        The method calculates all metrics.
        :param true_labels: numpy.array, true labels of the hits.
        :param track_inds: numpy.array, hits of recognized tracks.
        :return:
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

    new_track_inds = []

    for atrack in track_inds:

        atrack = numpy.array(atrack)
        mask = selection[atrack]
        new_track_inds.append(atrack[mask])

    return numpy.array(new_track_inds)

def get_charges(stree, smeared_hits):

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

    pinvs = []

    for i in range(len(smeared_hits)):

        px = stree.strawtubesPoint[i].GetPx()
        py = stree.strawtubesPoint[i].GetPy()
        pz = stree.strawtubesPoint[i].GetPz()
        apinv = 1. / numpy.sqrt(px**2 + py**2 + pz**2)
        pinvs.append(apinv)

    return numpy.array(pinvs)


########################################## Main functions ##############################################################

def save_hists(h, path):
    ut.writeHists(h, path)

def init_book_hist():

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
    h['EventsPassed'].GetXaxis().SetBinLabel(1,"Reconstructible tracks")
    h['EventsPassed'].GetXaxis().SetBinLabel(2,"Y view station 1&2")
    h['EventsPassed'].GetXaxis().SetBinLabel(3,"Stereo station 1&2")
    h['EventsPassed'].GetXaxis().SetBinLabel(4,"station 1&2")
    h['EventsPassed'].GetXaxis().SetBinLabel(5,"Y view station 3&4")
    h['EventsPassed'].GetXaxis().SetBinLabel(6,"Stereo station 3&4")
    h['EventsPassed'].GetXaxis().SetBinLabel(7,"station 3&4")
    h['EventsPassed'].GetXaxis().SetBinLabel(8,"Combined stations 1&2/3&4")
    h['EventsPassed'].GetXaxis().SetBinLabel(9,"Matched")

    ut.bookHist(h,'ptrue-p/ptrue','(p - p-true)/p',200,-1.,1.)

    return h

def decodeDetectorID(detID):

    statnb = detID // 10000000
    vnb = (detID - statnb * 10000000) // 1000000
    pnb = (detID - statnb * 10000000 - vnb * 1000000) // 100000
    lnb = (detID - statnb * 10000000 - vnb * 1000000 - pnb * 100000) // 10000
    snb = detID - statnb * 10000000 - vnb * 1000000 - pnb * 100000 - lnb * 10000 - 2000

    return statnb, vnb, pnb, lnb, snb

def quality_metrics(smeared_hits, stree, reco_mc_tracks, reco_tracks, h):

    X = Digitization(stree,smeared_hits)
    y = get_track_ids(stree, smeared_hits)

    n_tracks = len(numpy.unique(y))
    h['NTracks'].Fill(n_tracks)

    track_inds = [atrack['hits'] for atrack in reco_tracks.values()]
    statnb, vnb, pnb, lnb, snb = decodeDetectorID(X[:, -1])

    n_reco_tracks = len(track_inds)
    h['NRecoTracks'].Fill(n_reco_tracks)

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
        h['EventsPassed'].Fill("Reconstructible tracks", 1)

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

    # Pinv
    pinvs = get_pinvs(stree, smeared_hits)

    for i in reco_tracks.keys():

        atrack = reco_tracks[i]['hits']
        frac, tmax = fracMCsame(y[atrack])
        pinv_true = pinvs[y == tmax][0]
        pinv = reco_tracks[i]['pinv']
        charge = reco_tracks[i]['charge']

        err = 1 - charge * pinv / pinv_true
        h['ptrue-p/ptrue'].Fill(err)



    return