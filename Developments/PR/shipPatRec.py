__author__ = 'Mikhail Hushchyn'

########################################################################################################################
# This is the main script of track pattern recognition.
#
#
########################################################################################################################

import numpy
import sys, os

from models.fast_hough import FastHough
from models.artificial_retina import ArtificialRetina
from models.baseline import Baseline

import ROOT
from array import array
import shipunit  as u

########################################################################################################################
########################################################################################################################

def execute(smeared_hits, stree, ShipGeo, method='Baseline'):
    """
    Does real track pattern recognition and track fit.

    Parameters
    ----------
    smeared_hits : list of dicts
        List of smeared hits. A smeared hit is a dictionary:
        {'digiHit':key,'xtop':top x,'ytop':top y,'z':top z,'xbot':bot x,'ybot':bot y,'dist':smeared dist2wire}
    stree : root file
        Events in raw format.
    ShipGeo : object
        Contains SHiP detector geometry.
    method : string
        Name of a track pattern recognition model.

    Returns
    -------
    reco_tracks : dict
        Dictionary of recognized tracks: {track_id: reco_track}.
        Reco_track is a dictionary:
        {'hits': [ind1, ind2, ind3, ...],
         'hitPosList': X[atrack, :-1],
         'charge': charge,
         'pinv': pinv,
         'params12': [[k_yz, b_yz], [k_xz, b_xz]],
         'params34': [[k_yz, b_yz], [k_xz, b_xz]]}

    theTracks : list
        List of fitted track objects.
    """

    ######################################## Hits digitization #########################################################

    X = Digitization(stree, smeared_hits)

    ######################################## Do Track Pattern Recognition ##############################################

    reco_tracks = PatRec(X, ShipGeo, z_magnet=ShipGeo.Bfield.z, method=method)

    ######################################### Fit recognized tracks ####################################################

    theTracks = TrackFit(ShipGeo, reco_tracks, isfit=True)

    ######################################### Estimate true track ids ##################################################

    return reco_tracks, theTracks





########################################################################################################################
########################################################################################################################


def PatRec(X, ShipGeo, z_magnet, method='FH'):
    """
    Does track pattern recognition.

    Parameters
    ----------
    X : ndarray-like
        Information about active straw tubes: [[xtop, ytop, ztop, xbot, ybot, zboy, dist2wire, detID], [...], ...]
    ShipGeo : object
        Contains SHiP detector geometry.
    z_magnet : float
        Z-coordinate of the magnet center.
    method : string
        Name of the track pattern recognition method.

    Retunrs
    -------
    reco_tracks : dict
        Dictionary of recognized tracks: {track_id: reco_track}.
        Reco_track is a dictionary:
        {'hits': [ind1, ind2, ind3, ...],
         'hitPosList': X[atrack, :-1],
         'charge': charge,
         'pinv': pinv,
         'params12': [[k_yz, b_yz], [k_xz, b_xz]],
         'params34': [[k_yz, b_yz], [k_xz, b_xz]]}
    """

    if len(X) == 0:
        return {}


    ################################## Select models to search tracks in 2D planes #####################################

    if method=='FH':


        ptrack_y = FastHough(n_tracks=2,
                             min_hits=3,
                             k_size=0.7/10000,
                             b_size=1700./10000,
                             k_limits=(-0.5, 0.5),
                             b_limits=(-1150, 1150),
                             unique_hit_labels=True)

        ptrack_stereo = FastHough(n_tracks=1,
                                  min_hits=3,
                                  k_size=0.6/200,
                                  b_size=1000./200,
                                  k_limits=(-0.3, 0.3),
                                  b_limits=(-500, 500),
                                  unique_hit_labels=True)

        # Double hits to increase PR precision.
        X1 = X.copy()
        X1[:, 1] += X1[:, 6] * numpy.cos(numpy.deg2rad(5))
        X1[:, 4] += X1[:, 6] * numpy.cos(numpy.deg2rad(5))

        X2 = X.copy()
        X2[:, 1] += - X2[:, 6] * numpy.cos(numpy.deg2rad(5))
        X2[:, 4] += - X2[:, 6] * numpy.cos(numpy.deg2rad(5))

        XX = numpy.concatenate((X1, X2), axis=0)
        sample_weight = None
        XX_inds = numpy.concatenate((range(len(X)), range(len(X))))
        global_inds = numpy.arange(len(XX))


    elif method=='AR':


        ptrack_y = ArtificialRetina(n_tracks=2,
                                    min_hits=2,
                                    residuals_threshold=0.15,
                                    sigma=0.2,
                                    k_size=0.7/10000,
                                    b_size=1700./10000,
                                    k_limits=(-0.5, 0.5),
                                    b_limits=(-1150, 1150))

        ptrack_stereo = ArtificialRetina(n_tracks=1,
                                         min_hits=2,
                                         residuals_threshold=2,
                                         sigma=2,
                                         k_size=0.6/200,
                                         b_size=1000./200,
                                         k_limits=(-0.3, 0.3),
                                         b_limits=(-500, 500))

        # Double hits to increase PR precision.
        X1 = X.copy()
        X1[:, 1] += X1[:, 6] * numpy.cos(numpy.deg2rad(5))
        X1[:, 4] += X1[:, 6] * numpy.cos(numpy.deg2rad(5))

        X2 = X.copy()
        X2[:, 1] += - X2[:, 6] * numpy.cos(numpy.deg2rad(5))
        X2[:, 4] += - X2[:, 6] * numpy.cos(numpy.deg2rad(5))

        XX = numpy.concatenate((X1, X2), axis=0)
        sample_weight = None
        XX_inds = numpy.concatenate((range(len(X)), range(len(X))))
        global_inds = numpy.arange(len(XX))


    elif method == 'Baseline':

        ptrack_y = Baseline(nrwant = 6, window = 0.6)
        ptrack_stereo = Baseline(nrwant = 7, window = 15)

        # Hits preprocessing
        XX = X.copy()
        sample_weight = 1. / numpy.sqrt(XX[:, 6]**2 + 0.2**2)
        XX_inds = numpy.arange(len(XX))
        global_inds = numpy.arange(len(XX))

    else:

        return {}

    ########################################### Decode detector IDs ####################################################

    # Decode detector ID of the hits
    detID = XX[:, -1]
    statnb, vnb, pnb, lnb, snb = decodeDetectorID(detID)

    ######################################### Y-views, stations 1&2 ####################################################

    # Select hits in Y-views of stations 1&2

    select_y12 = ((statnb == 1) + (statnb == 2)) * ((vnb == 0) + (vnb == 3))
    XX_y12 = XX[select_y12]
    if sample_weight is None:
        sample_weight_y12 = None
    else:
        sample_weight_y12 = sample_weight[select_y12]
    global_inds_y12 = global_inds[select_y12]

    # Look for tracks in the 16 layers with horizontal straw tubes in YZ-plane.

    track_inds_y12, track_params_y12 = y_track_recognition(ptrack_y, XX_y12, sample_weight_y12)

    # track_inds_y12 = [[ind1, ind2, ind3, ...], [...], ...]
    # track_params_y12 = [[k1, b1], [k2, b2], ...], where y = k * x + b


    ######################################### Stereo-views, stations 1&2 ###############################################

    # Select hits in Stereo-views of stations 1&2

    select_stereo12 = ((statnb == 1) + (statnb == 2)) * ((vnb == 1) + (vnb == 2))
    XX_stereo12 = XX[select_stereo12]
    if sample_weight is None:
        sample_weight_stereo12 = None
    else:
        sample_weight_stereo12 = sample_weight[select_stereo12]
    global_inds_stereo12 = global_inds[select_stereo12]

    # For each track found in the Y-views, intersect the plane defined by this track and the X-axis with the stereo (U,V) hits.
    # This gives (z, x) coordinates.
    # Look for tracks in 16 layers of Stereo-views in XZ plane using (z, x) coordinates of the intersections.
    # It is supposed that one track in Y-views has only one track in Stereo-views.

    track_inds_stereo12, track_params_stereo12 = stereo_track_recognition(ptrack_stereo, XX_stereo12,
                                                                                   track_params_y12, sample_weight_stereo12,
                                                                                   unique_hit_labels=True)

    # track_inds_stereo12 = [[ind1, ind2, ind3, ...], [...], ...]
    # track_params_stereo12 = [[k1, b1], [k2, b2], ...], where y = k * x + b

    ################################################## Stations 1&2 ####################################################
    # Unite the track projections

    track_inds_12 = []
    track_params_12 = []

    for track_id in range(len(track_inds_y12)):
        track_inds_12.append([global_inds_y12[track_inds_y12[track_id]],
                              global_inds_stereo12[track_inds_stereo12[track_id]]])
        track_params_12.append([track_params_y12[track_id], track_params_stereo12[track_id]])


    ######################################### Y-views, stations 3&4 ####################################################

    # Select hits in Y-views of stations 3&4

    select_y34 = ((statnb == 3) + (statnb == 4)) * ((vnb == 0) + (vnb == 3))
    XX_y34 = XX[select_y34]
    if sample_weight is None:
        sample_weight_y34 = None
    else:
        sample_weight_y34 = sample_weight[select_y34]
    global_inds_y34 = global_inds[select_y34]

    # Look for tracks in the 16 layers with horizontal straw tubes in YZ-plane.

    track_inds_y34, track_params_y34 = y_track_recognition(ptrack_y, XX_y34, sample_weight_y34)

    # track_inds_y34 = [[ind1, ind2, ind3, ...], [...], ...]
    # track_params_y34 = [[k1, b1], [k2, b2], ...], where y = k * x + b


    ######################################### Stereo-views, stations 3&4 ###############################################

    # Select hits in Stereo-views of stations 1&2

    select_stereo34 = ((statnb == 3) + (statnb == 4)) * ((vnb == 1) + (vnb == 2))
    XX_stereo34 = XX[select_stereo34]
    if sample_weight is None:
        sample_weight_stereo34 = None
    else:
        sample_weight_stereo34 = sample_weight[select_stereo34]
    global_inds_stereo34 = global_inds[select_stereo34]

    # For each track found in the Y-views, intersect the plane defined by this track and the X-axis with the stereo (U,V) hits.
    # This gives (z, x) coordinates.
    # Look for tracks in 16 layers of Stereo-views in XZ plane using (z, x) coordinates of the intersections.
    # It is supposed that one track in Y-views has only one track in Stereo-views.

    track_inds_stereo34, track_params_stereo34 = stereo_track_recognition(ptrack_stereo, XX_stereo34,
                                                                                   track_params_y34, sample_weight_stereo34,
                                                                                   unique_hit_labels=True)

    # track_inds_stereo34 = [[ind1, ind2, ind3, ...], [...], ...]
    # track_params_stereo34 = [[k1, b1], [k2, b2], ...], where y = k * x + b


    ################################################## Stations 3&4 ####################################################
    # Unite the track projections

    track_inds_34 = []
    track_params_34 = []

    for track_id in range(len(track_inds_y34)):
        track_inds_34.append([global_inds_y34[track_inds_y34[track_id]],
                              global_inds_stereo34[track_inds_stereo34[track_id]]])
        track_params_34.append([track_params_y34[track_id], track_params_stereo34[track_id]])


    ############################################## Tracks combination ##################################################

    # Combine tracks before and after the magnet.
    # Reconstruct particles charge and momentum

    comb = Combinator(z_magnet=z_magnet, magnetic_field=-0.75, dy_max=2., dx_max=20.)
    comb.combine(track_params_12, track_params_34)


    ############################################ Save combined tracks ##################################################

    reco_tracks = {}

    for track_id, acomb in enumerate(comb.tracks_combinations_):

        track_before_y, track_before_stereo = track_inds_12[acomb[0]]
        track_before = numpy.concatenate((track_before_y, track_before_stereo))

        track_after_y, track_after_stereo = track_inds_34[acomb[1]]
        track_after = numpy.concatenate((track_after_y, track_after_stereo))

        atrack = numpy.concatenate((track_before, track_after))
        atrack = numpy.unique(XX_inds[atrack])

        reco_tracks[track_id] = {'hits': atrack,
                                 'hitPosList': X[atrack, :-1],
                                 'charge': comb.charges_[track_id],
                                 'pinv':comb.inv_momentums_[track_id],
                                 'params12': track_params_12[acomb[0]],
                                 'params34': track_params_34[acomb[1]]}

    return reco_tracks






########################################################################################################################
########################################################################################################################


def TrackFit(ShipGeo, reco_tracks, isfit=True):
    """
    Fits all recognized tracks.

    Parameters
    ----------
    ShipGeo : object
        Contains SHiP detector geometry.
    reco_tracks : dict
        Dictionary of recognized tracks: {track_id: reco_track}.
        Reco_track is a dictionary:
        {'hits': [ind1, ind2, ind3, ...],
         'hitPosList': X[atrack, :-1],
         'charge': charge,
         'pinv': pinv,
         'params12': [[k_yz, b_yz], [k_xz, b_xz]],
         'params34': [[k_yz, b_yz], [k_xz, b_xz]]}

    Returns
    -------
    theTracks : array-like
        List of fitted tracks.
    """


    # ROOT.genfit is used to fit tracks.
    # Description: http://iopscience.iop.org/article/10.1088/1742-6596/608/1/012042/pdf

    # Fitted tracks
    theTracks = []

    if isfit:

        # Init track fitter
        geoMat =  ROOT.genfit.TGeoMaterialInterface()
        bfield = ROOT.genfit.BellField(ShipGeo.Bfield.max ,ShipGeo.Bfield.z,2, ShipGeo.Yheight/2.*u.m)
        fM = ROOT.genfit.FieldManager.getInstance()
        fM.init(bfield)
        ROOT.genfit.MaterialEffects.getInstance().init(geoMat)
        fitter = ROOT.genfit.DAF()

    # Iterate recognized tracks
    for track_id in reco_tracks.keys():

        hitPosList = reco_tracks[track_id]['hitPosList']
        charge = reco_tracks[track_id]['charge']
        pinv = reco_tracks[track_id]['pinv']

        # Track preparation before the fit

        nM = len(hitPosList)

        if int(charge)<0:
            pdg=13
        else:
            pdg=-13

        rep = ROOT.genfit.RKTrackRep(pdg)
        posM = ROOT.TVector3(0, 0, 0)

        if abs(pinv) > 0.0 :
            momM = ROOT.TVector3(0,0,int(charge)/pinv)
        else:
            momM = ROOT.TVector3(0,0,999)

        # Define covariance matrix
        covM = ROOT.TMatrixDSym(6)
        resolution = ShipGeo.strawtubes.sigma_spatial
        for i in range(3):
            covM[i][i] = resolution*resolution
        covM[0][0]=resolution*resolution*100.
        for i in range(3,6):
            covM[i][i] = ROOT.TMath.Power(resolution / nM / ROOT.TMath.Sqrt(3), 2)

        # Smeared start state
        stateSmeared = ROOT.genfit.MeasuredStateOnPlane(rep)
        rep.setPosMomCov(stateSmeared, posM, momM, covM)

        # Set up seed
        seedState = ROOT.TVectorD(6)
        seedCov   = ROOT.TMatrixDSym(6)
        rep.get6DStateCov(stateSmeared, seedState, seedCov)

        # Create track
        theTrack=ROOT.genfit.Track(rep, seedState, seedCov)


        # Fill the track

        # Define hit covariance matrix
        resolution = ShipGeo.strawtubes.sigma_spatial
        hitCov = ROOT.TMatrixDSym(7)
        hitCov[6][6] = resolution*resolution

        # Add hits to the track
        for item in hitPosList:

            itemarray=array('d',[item[0],item[1],item[2],item[3],item[4],item[5],item[6]])
            ms=ROOT.TVectorD(7,itemarray)
            tp = ROOT.genfit.TrackPoint(theTrack) # note how the point is told which track it belongs to
            measurement = ROOT.genfit.WireMeasurement(ms,hitCov,1,6,tp) # the measurement is told which trackpoint it belongs to
            measurement.setMaxDistance(0.5*u.cm)
            tp.addRawMeasurement(measurement) # package measurement in the TrackPoint
            theTrack.insertPoint(tp)  # add point to Track

        # Track fit

        if isfit:

            if not theTrack.checkConsistency():
                continue

            try:
                fitter.processTrack(theTrack)
            except:
                continue

            if not theTrack.checkConsistency():
                continue


        # Collect tracks
        theTracks.append(theTrack)

    return theTracks








########################################################################################################################
########################################################################################################################


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


########################################################################################################################
########################################################################################################################


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


########################################################################################################################
########################################################################################################################


def y_track_recognition(model, X, sample_weight=None):
    """
    Does track pattern recognition in y-z plane.

    Parameters
    ----------
    model : object
        Object of pattern recognition method.
    X : ndarray-like
        Information about active straw tubes: [[xtop, ytop, ztop, xbot, ybot, zboy, dist2wire, detID], [...], ...]
    sample_weight : array-like
        Hit weights used during the track fit.

    Returns
    -------
    track_inds_y : array-like
        List of recognized tracks. Recognized track is a list of hit indexes correspond to one bin in track parameters space.
        Example: [[ind1, ind2, ind3, ...], [...], ...]
    tracks_params_y : array-like
        List of parameters of the recognized tracks. Example: [[k1, b1], [k2, b2], ...]
    """

    indeces = numpy.arange(len(X))

    xs = X[:, 2]
    ys = X[:, 1]

    model.fit(xs, ys, sample_weight)

    track_inds = model.track_inds_
    for i in range(len(track_inds)):
        track_inds[i] = indeces[track_inds[i]]

    tracks_params = model.tracks_params_

    return track_inds, tracks_params


########################################################################################################################
########################################################################################################################


def get_xz(plane_k, plane_b, X):
    """
    This method returns (z, x) coordinated of intersections of straw tubes in stereo-views and
    a plane corresponding to a founded track in y-view.

    Parameters
    ----------
    plane_k : float
        Slope of the track in y-view.
    plane_b : float
        Intercept of the track in y-view.
    X : ndarray-like
        Information about active straw tubes: [[xtop, ytop, ztop, xbot, ybot, zboy, dist2wire, detID], [...], ...]

    Returns
    -------
    z : array-like
        Z coordinates of the intersections.
    x : array-like
        X coordinates of the intersections.
    """

    Wz1 = X[:, 2]
    Wx1 = X[:, 0]
    Wx2 = X[:, 3]
    Wy1 = X[:, 1]
    Wy2 = X[:, 4]

    y = plane_k * Wz1 + plane_b
    x = (Wx2 - Wx1) / (Wy2 - Wy1) * (y - Wy1) + Wx1

    return Wz1, x


########################################################################################################################
########################################################################################################################


def stereo_track_recognition(model, X, track_params_y, sample_weight=None, unique_hit_labels=True):
    """
    Does track pattern recognition in x-z plane.

    Parameters
    ----------
    model : object
        Object of pattern recognition method.
    X : ndarray-like
        Information about active straw tubes: [[xtop, ytop, ztop, xbot, ybot, zboy, dist2wire, detID], [...], ...]
    tracks_params_y : array-like
        List of parameters of the recognized tracks in y-z plane. Example: [[k1, b1], [k2, b2], ...]
    sample_weight : array-like
        Hit weights used during the track fit.
    unique_hit_labels : boolean
        Is a hit can be used only one time or not.

    Returns
    -------
    track_inds_stereo : array-like
        List of recognized tracks. Recognized track is a list of hit indexes correspond to one bin in track parameters space.
        Example: [[ind1, ind2, ind3, ...], [...], ...]
    tracks_params_stereo : array-like
        List of parameters of the recognized tracks. Example: [[k1, b1], [k2, b2], ...]
    """

    atrack_inds = []
    atracks_params = []

    indeces = numpy.arange(len(X))
    used = numpy.zeros(len(X))

    track_inds_stereo = []
    track_params_stereo = []

    for track_id, one_track_y in enumerate(track_params_y):

        if len(one_track_y) != 0:

            plane_k, plane_b = one_track_y
            xs, ys = get_xz(plane_k, plane_b, X)

            if unique_hit_labels:
                sel = (used==0) * (numpy.abs(ys) <= 293.)
            else:
                sel = (numpy.abs(ys) <= 293.)

            if sample_weight is not None:
                sample_weight_stereo = sample_weight[sel]
            else:
                sample_weight_stereo = None

            model.fit(xs[sel], ys[sel], sample_weight_stereo)

            if len(model.track_inds_) == 0:
                track_inds_stereo.append([])
                track_params_stereo.append([])
                continue

            atrack_inds = model.track_inds_[0]
            atrack_inds = indeces[sel][atrack_inds]
            atrack_params = model.tracks_params_[0]

            used[atrack_inds] = 1


        else:

            atrack_inds = []
            atrack_params = []


        track_inds_stereo.append(atrack_inds)
        track_params_stereo.append(atrack_params)


    return track_inds_stereo, track_params_stereo


########################################################################################################################
########################################################################################################################


class Combinator(object):

    def __init__(self, z_magnet=3070., magnetic_field=-0.75, dy_max=2., dx_max=20.):
        """
        This class combines tracks before and after the magnet,
        estimates a particles charge and momentum based on its deflection in the magnetic field.

        Parameters
        ----------
        z_magnet : float,
            Z-coordinate of the center of the magnet.
        magnetic_field : float,
            Inductivity of the magnetic field.
        dy_max : float,
            Max distance on y between the tracks before and after the magnet in center of the magnet.
        dx_max : float,
            Max distance on x between the tracks before and after the magnet in center of the magnet.
        """

        self.z_magnet = z_magnet
        self.magnetic_field = magnetic_field
        self.dy_max = dy_max
        self.dx_max = dx_max

        self.tracks_combinations_ = None
        self.charges_ = None
        self.inv_momentums_ = None

    def get_tracks_combination(self, tracks_before, tracks_after):
        """
        This function finds combinations of two tracks befor and after the magnet.

        Parameters
        ----------
        tracks_before : array-like,
            List of [[k_yz, b_yz], [k_xz, b_xz]], parameters of a track before the magnet.
            Track parametrization is y = kx + b.
        tracks_after : array-like,
            List of [[k_yz, b_yz], [k_xz, b_xz]], parameters of a track after the magnet.
            Track parametrization is y = kx + b.

        Return
        ------
        List of [track_id_before, track_id_after] for the track combinations.
        """

        z_magnet = self.z_magnet
        dy_max = self.dy_max
        dx_max = self.dx_max

        self.dx = []
        self.dy = []

        tracks_combinations = []

        for track_id_before, one_track_before in enumerate(tracks_before):

            for track_id_after, one_track_after in enumerate(tracks_after):


                if len(one_track_before[1])==0 or len(one_track_after[1])==0:
                    continue

                y_before = z_magnet * one_track_before[0][0] + one_track_before[0][1]
                x_before = z_magnet * one_track_before[1][0] + one_track_before[1][1]

                y_after = z_magnet * one_track_after[0][0] + one_track_after[0][1]
                x_after = z_magnet * one_track_after[1][0] + one_track_after[1][1]

                dy = numpy.abs(y_after - y_before)
                dx = numpy.abs(x_after - x_before)
                dr = numpy.sqrt(dy**2 + dx**2)


                if dy <= dy_max and dx <= dx_max:

                    self.dx.append(x_after - x_before)
                    self.dy.append(y_after - y_before)

                    tracks_combinations.append(numpy.array([track_id_before, track_id_after]))
                    #continue

        return numpy.array(tracks_combinations)

    def get_charges(self, tracks_before, tracks_after, tracks_combinations):
        """
        This function estimates charges of particles.

        Parameters
        ----------
        tracks_before : array-like,
            List of [[k_yz, b_yz], [k_xz, b_xz]], parameters of a track before the magnet.
            Track parametrization is y = kx + b.
        tracks_after : array-like,
            List of [[k_yz, b_yz], [k_xz, b_xz]], parameters of a track after the magnet.
            Track parametrization is y = kx + b.
        tracks_combinations : array-like,
            List of [track_id_before, track_id_after], indexes of the tracks in the combinations.

        Return
        ------
        List of estimated charges for the track combinations: [q1, q2, ...]
        """

        charges = []

        for one_tracks_combination in tracks_combinations:

            one_track_before = tracks_before[one_tracks_combination[0]]
            one_track_after = tracks_after[one_tracks_combination[1]]

            k_yz_before = one_track_before[0][0]
            k_yz_after = one_track_after[0][0]

            difftan = (k_yz_before - k_yz_after) / (1. + k_yz_before * k_yz_after)


            if difftan > 0:

                one_charge = -1.

            else:

                one_charge = 1.


            charges.append(one_charge)

        return numpy.array(charges)


    def get_inv_momentums(self, tracks_before, tracks_after, tracks_combinations):
        """
        This function estimates momentum values of particles.

        Parameters
        ----------
        tracks_before : array-like,
            List of [[k_yz, b_yz], [k_xz, b_xz]], parameters of a track before the magnet.
            Track parametrization is y = kx + b.
        tracks_after : array-like,
            List of [[k_yz, b_yz], [k_xz, b_xz]], parameters of a track after the magnet.
            Track parametrization is y = kx + b.
        tracks_combinations : array-like,
            List of [track_id_before, track_id_after], indexes of the tracks in the combinations.

        Return
        ------
        List of estimated inverse momentum values for the track combinations: [pinv1, pinv2, ...]
        """

        Bm = self.magnetic_field
        inv_momentums = []

        for one_tracks_combination in tracks_combinations:

            one_track_before = tracks_before[one_tracks_combination[0]]
            one_track_after = tracks_after[one_tracks_combination[1]]

            k_yz_before = one_track_before[0][0]
            k_yz_after = one_track_after[0][0]

            a = numpy.arctan(k_yz_before)
            b = numpy.arctan(k_yz_after)
            pinv = numpy.sin(a - b) / (0.3 * Bm)

            #pinv = numpy.abs(pinv) # !!!!

            inv_momentums.append(pinv)


        return numpy.array(inv_momentums)


    def combine(self, tracks_before, tracks_after):
        """
        Run the combinator.

        Parameters
        ----------
        tracks_before : array-like,
            List of [[k_yz, b_yz], [k_xz, b_xz]], parameters of a track before the magnet.
            Track parametrization is y = kx + b.
        tracks_after : array-like,
            List of [[k_yz, b_yz], [k_xz, b_xz]], parameters of a track after the magnet.
            Track parametrization is y = kx + b.

        Use the following attributes as outputs:
            tracks_combinations_
            charges_
            inv_momentums_
        """

        tracks_combinations = self.get_tracks_combination(tracks_before, tracks_after)
        charges = self.get_charges(tracks_before, tracks_after, tracks_combinations)
        inv_momentums = self.get_inv_momentums(tracks_before, tracks_after, tracks_combinations)


        # Use these attributes as outputs
        self.tracks_combinations_ = tracks_combinations
        self.charges_ = charges
        self.inv_momentums_ = inv_momentums


########################################################################################################################
########################################################################################################################





########################################################################################################################
########################################################################################################################