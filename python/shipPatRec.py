# SHiP Track Pattern Recognition
# Mikhail Hushchyn, mikhail.hushchyn@cern.ch

import numpy
import sys, os

import ROOT
from array import array
import shipunit  as u


######################################################## Main Functions ########################################################
################################################################################################################################

# Globals:
theTracks = []
ReconstructibleMCTracks = []
reco_tracks = {}

def initialize(fgeo):
    pass


# ShipGeo is defined in macro/ShipReco.py
def execute(smeared_hits, stree, ReconstructibleMCTracks, method='Baseline'):
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
        Name of a track pattern recognition model: 'Baseline' (Default), 'FH', 'AR'.

    Globals
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
        
    Returns
    -------
    fittedtrackids : list
        List of MC track ids correspond to recognized tracks.
    """

    ######################################## Hits digitization #########################################################

    X = Digitization(stree, smeared_hits)

    ######################################## Do Track Pattern Recognition ##############################################

    global reco_tracks
    reco_tracks = PatRec(X, ShipGeo, z_magnet=ShipGeo.Bfield.z, method=method)
    
    # reco_tracks : {track_id1: reco_track1, track_id2: reco_track2, ...}
    # reco_track : {'hits': [ind1, ind2, ind3, ...],
    #               'hitPosList': X[atrack, :-1],
    #               'charge': charge,
    #               'pinv': pinv,
    #               'params12': [[k_yz, b_yz], [k_xz, b_xz]],
    #               'params34': [[k_yz, b_yz], [k_xz, b_xz]]}


    ######################################### Fit recognized tracks ####################################################

    global theTracks
    theTracks = TrackFit(ShipGeo, reco_tracks, isfit=True)

    ######################################### Estimate true track ids ##################################################
    
    y = get_track_ids(stree, smeared_hits) # It uses MC truth
    fittedtrackids, fittedtrackfrac = get_fitted_trackids(y, reco_tracks) # It uses MC truth
    # fittedtrackids = range(len(theTracks))

    return fittedtrackids, reco_tracks



def finalize():
    pass



################################################################################################################################
################################################################################################################################


def PatRec(X, ShipGeo, z_magnet, method='Baseline'):
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
        Name of the track pattern recognition method: 'Baseline' (default), 'FH', 'AR'.

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
    
    angle = 1. * ShipGeo.strawtubes.ViewAngle


    ################################## Select models to search tracks in 2D planes #####################################

    if method=='FH':


        ptrack_y = FastHough(n_tracks=None, # search for all tracks
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
        X1[:, 1] += X1[:, 6] * numpy.cos(numpy.deg2rad(angle))
        X1[:, 4] += X1[:, 6] * numpy.cos(numpy.deg2rad(angle))

        X2 = X.copy()
        X2[:, 1] += - X2[:, 6] * numpy.cos(numpy.deg2rad(angle))
        X2[:, 4] += - X2[:, 6] * numpy.cos(numpy.deg2rad(angle))

        XX = numpy.concatenate((X1, X2), axis=0)
        sample_weight = None
        XX_inds = numpy.concatenate((range(len(X)), range(len(X))))
        global_inds = numpy.arange(len(XX))


    elif method=='AR':


        ptrack_y = ArtificialRetina(n_tracks=2, # TODO: search for all tracks
                                    min_hits=5,
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
        X1[:, 1] += X1[:, 6] * numpy.cos(numpy.deg2rad(angle))
        X1[:, 4] += X1[:, 6] * numpy.cos(numpy.deg2rad(angle))

        X2 = X.copy()
        X2[:, 1] += - X2[:, 6] * numpy.cos(numpy.deg2rad(angle))
        X2[:, 4] += - X2[:, 6] * numpy.cos(numpy.deg2rad(angle))

        XX = numpy.concatenate((X1, X2), axis=0)
        sample_weight = None
        XX_inds = numpy.concatenate((range(len(X)), range(len(X))))
        global_inds = numpy.arange(len(XX))


    elif method == 'Baseline':

        ptrack_y = Baseline(nrwant = 7, window = 0.7)
        ptrack_stereo = Baseline(nrwant = 6, window = 15)

        # Hits preprocessing
        XX = X.copy()
        resolution = ShipGeo.strawtubes.sigma_spatial
        sample_weight = 1. / numpy.sqrt(XX[:, 6]**2 + resolution**2)
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
    sample_weight_y12 = sample_weight[select_y12] if sample_weight is not None else None
    global_inds_y12 = global_inds[select_y12]

    # Look for tracks in the 16 layers with horizontal straw tubes in YZ-plane.

    track_inds_y12, track_params_y12 = y_track_recognition(ptrack_y, XX_y12, sample_weight_y12)
    
    # Remove clones
    
    tracks = [XX_inds[global_inds_y12[tr]] for tr in track_inds_y12]
    res_y12 = remove_clones(tracks, max_shared_hits=2)
    track_inds_y12 = [track_inds_y12[i] for i in res_y12]
    track_params_y12 = [track_params_y12[i] for i in res_y12]

    # track_inds_y12 = [[ind1, ind2, ind3, ...], [...], ...]
    # track_params_y12 = [[k1, b1], [k2, b2], ...], where y = k * x + b


    ######################################### Stereo-views, stations 1&2 ###############################################

    # Select hits in Stereo-views of stations 1&2

    select_stereo12 = ((statnb == 1) + (statnb == 2)) * ((vnb == 1) + (vnb == 2))
    XX_stereo12 = XX[select_stereo12]
    sample_weight_stereo12 = sample_weight[select_stereo12] if sample_weight is not None else None
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
    sample_weight_y34 = sample_weight[select_y34] if sample_weight is not None else None
    global_inds_y34 = global_inds[select_y34]

    # Look for tracks in the 16 layers with horizontal straw tubes in YZ-plane.

    track_inds_y34, track_params_y34 = y_track_recognition(ptrack_y, XX_y34, sample_weight_y34)
    
    # Remove clones
    
    tracks = [XX_inds[global_inds_y34[tr]] for tr in track_inds_y34]
    res_y34 = remove_clones(tracks, max_shared_hits=2)
    track_inds_y34 = [track_inds_y34[i] for i in res_y34]
    track_params_y34 = [track_params_y34[i] for i in res_y34]

    # track_inds_y34 = [[ind1, ind2, ind3, ...], [...], ...]
    # track_params_y34 = [[k1, b1], [k2, b2], ...], where y = k * x + b


    ######################################### Stereo-views, stations 3&4 ###############################################

    # Select hits in Stereo-views of stations 1&2

    select_stereo34 = ((statnb == 3) + (statnb == 4)) * ((vnb == 1) + (vnb == 2))
    XX_stereo34 = XX[select_stereo34]
    sample_weight_stereo34 = sample_weight[select_stereo34] if sample_weight is not None else None
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
    track_id = 0

    for acomb in comb.tracks_combinations_:

        track_before_y, track_before_stereo = track_inds_12[acomb[0]]
        track_before = numpy.concatenate((track_before_y, track_before_stereo))

        track_after_y, track_after_stereo = track_inds_34[acomb[1]]
        track_after = numpy.concatenate((track_after_y, track_after_stereo))

        atrack = numpy.concatenate((track_before, track_after))
        atrack = numpy.unique(XX_inds[atrack])

        reco_tracks[track_id] = {'hits': atrack,
                                 'flag': 1, # full track
                                 'hitPosList': X[atrack, :-1],
                                 'charge': comb.charges_[track_id],
                                 'pinv':comb.inv_momentums_[track_id],
                                 'params12': track_params_12[acomb[0]],
                                 'params34': track_params_34[acomb[1]]}
        track_id += 1
            

    ################################ Save tracks found only in 1&2 or 3&4 stations #####################################

    combined_ids_12 = [acomb[0] for acomb in comb.tracks_combinations_]
    combined_ids_34 = [acomb[1] for acomb in comb.tracks_combinations_]

    # Before
    for i_track in range(len(track_inds_12)):

        if i_track in combined_ids_12:
            continue

        track_before_y, track_before_stereo = track_inds_12[i_track]
        track_before = numpy.concatenate((track_before_y, track_before_stereo))

        atrack = track_before
        atrack = numpy.unique(XX_inds[atrack])

        reco_tracks[track_id] = {'hits': atrack,
                                 'flag': 0, # tracklet
                                 'hitPosList': X[atrack, :-1],
                                 'charge': -999,
                                 'pinv': -999,
                                 'params12': track_params_12[i_track],
                                 'params34': [[], []]}

        track_id += 1

#    # After
#    for i_track in range(len(track_inds_34)):
#
#        if i_track in combined_ids_34:
#            continue
#
#        track_after_y, track_after_stereo = track_inds_34[i_track]
#        track_after = numpy.concatenate((track_after_y, track_after_stereo))
#
#        atrack = track_after
#        atrack = numpy.unique(XX_inds[atrack])
#
#        reco_tracks[track_id] = {'hits': atrack,
#                                 'hitPosList': X[atrack, :-1],
#                                 'charge': -999,
#                                 'pinv': -999,
#                                 'params12': [[], []],
#                                 'params34': track_params_34[i_track]}
#
#        track_id += 1

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

        # # Init track fitter # It is done in shipDigiReco
        # geoMat =  ROOT.genfit.TGeoMaterialInterface()
        # bfield = ROOT.genfit.BellField(ShipGeo.Bfield.max ,ShipGeo.Bfield.z,2, ShipGeo.Yheight/2.*u.m)
        # fM = ROOT.genfit.FieldManager.getInstance()
        # fM.init(bfield)
        # ROOT.genfit.MaterialEffects.getInstance().init(geoMat)
        # fitter = ROOT.genfit.DAF()
        pass

    # Iterate recognized tracks
    for track_id in reco_tracks.keys():

        hitPosList = reco_tracks[track_id]['hitPosList']
        charge = reco_tracks[track_id]['charge']
        pinv = reco_tracks[track_id]['pinv']
        flag = reco_tracks[track_id]['flag']
        
        # Skip if it is a tracklet
        if flag == 0:
            continue

        # Track preparation before the fit

        nM = len(hitPosList)
        
        # if nM<25: # Insufficient for fitting.
        #    continue

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

        # # Track fit # shipDigiReco fits tthe track
        # 
        # if isfit:
        #  
        #     if not theTrack.checkConsistency():
        #         continue
        # 
        #     try:
        #         fitter.processTrack(theTrack)
        #     except:
        #         continue
        # 
        #     if not theTrack.checkConsistency():
        #         continue


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
    x = (Wx2 - Wx1) / (Wy2 - Wy1 + 10**-6) * (y - Wy1) + Wx1

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
            
            sel = (numpy.abs(ys) <= 293.)
            if unique_hit_labels: sel *= (used==0)
            sample_weight_stereo = sample_weight[sel] if sample_weight is not None else None
            
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
        This function estimates charge of particles.

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
        This function estimates momentum value of particles.

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

import numpy
from sklearn.linear_model import LinearRegression

class Baseline(object):

    def __init__(self, nrwant, window):

        self.nrwant = nrwant
        self.window = window

    def sort_hits(self, x, y):
        """
        Sort hits by x-layer and by y inside one layer.

        Parameters
        ----------
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.

        Returns
        -------
        xlayer : dict
            Dictionary of layer x values: {1: x1, 2: x2, 3: x3, ...}
        hits : dict
            Hits indexes inside layers: {x1: [ind1, ind2, ...], x2: [...], ...}
        """

        hits = {}
        xlayer = {}
        indexes = numpy.arange(len(x))

        for num, ax in enumerate(numpy.unique(x)):
            yx = y[x == ax]
            hits[ax] = indexes[x == ax][numpy.argsort(yx)]
            xlayer[num] = ax

        return xlayer, hits

    def get_tracks_params(self, x, y, track_inds, sample_weight=None):
        """
        Estimates track parameters y = k * x + b for the recognized tracks.

        Parameters
        ----------
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.
        track_inds : array-like
            Hit indexes of a track: [ind1, ind2, ...]
        sample_weight : array-like
            Hit weights used during the track fit.

        Return
        ------
        tracks_params : array-like
            Track parameters [k, b].
        """

        tracks_params = []

        if len(track_inds) == 0:
            return []

        for track in track_inds:

            x_track = x[track]
            y_track = y[track]

            if sample_weight is not None:
                sample_weight_track = sample_weight[track]
            else:
                sample_weight_track = None

            lr = LinearRegression(copy_X=False)
            lr.fit(x_track.reshape(-1,1), y_track, sample_weight_track)

            params = list(lr.coef_) + [lr.intercept_]
            tracks_params.append(params)

        return numpy.array(tracks_params)

    def fit(self, x, y, sample_weight=None):
        """
        Runs track pattern recognition. Track parametrization: y = k * x + b.

        Parameters
        ----------
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.
        sample_weight : array-like
            Hit weights used during the track fit.
        """

        track_params = []
        track_inds = []

        if len(x) == 0:
            self.tracks_params_ = numpy.array(track_params)
            self.track_inds_ = numpy.array(track_inds)
            return

        xlayer, hits = self.sort_hits(x, y)
        used = numpy.zeros(len(x))

        planes=xlayer.keys()
        planes.sort()
        i_1=planes[0]
        i_2=planes[len(planes)-1]
        ndrop=len(planes) - self.nrwant

        nrtracks=0

        # loop over maxnr hits, to max-ndrop
        for nhitw in range(i_2-i_1+1, i_2-i_1-ndrop, -1):

            # nhitw: wanted number of hits when looking for a track
            for idrop in range(ndrop):

                # only start if wanted nr hits <= the nr of planes
                nrhitmax = i_2 - i_1 - idrop + 1

                if nhitw <= nrhitmax:

                    for k in range(idrop+1):

                        # calculate the id of the first and last plane for this try.
                        ifirst = i_1 + k
                        ilast = i_2 - (idrop - k)

                        # now loop over hits in first/last planes, and construct line
                        dx = xlayer[ilast] - xlayer[ifirst]

                        # hits in first plane
                        for ifr in hits[xlayer[ifirst]]:

                            # has this hit been used already for a track: skip
                            if used[ifr] == 0:

                                yfirst = y[ifr]

                                # hits in last plane
                                for il in hits[xlayer[ilast]]:

                                    # has this hit been used already for a track: skip
                                    if used[il] == 0:

                                        ylast = y[il]

                                        nrhitsfound = 2
                                        tancand = (ylast - yfirst) / dx

                                        # fill temporary hit list for track-candidate with -1
                                        trcand=(i_2 - i_1 + 2) * [-1]

                                        # loop over in between planes
                                        for inbetween in range(ifirst + 1, ilast):

                                            # can wanted number of hits be satisfied?
                                            if nrhitsfound + ilast - inbetween >= nhitw:

                                                # calculate candidate hit
                                                ywinlow = yfirst + tancand * (xlayer[inbetween] - xlayer[ifirst]) - self.window

                                                for im in hits[xlayer[inbetween]]:

                                                    # has this hit been used?
                                                    if used[im] == 0:

                                                        yin= y[im]

                                                        # hit belwo window, try next one
                                                        if yin > ywinlow:

                                                            # if hit larger than upper edge of window: goto next plane
                                                            if yin > ywinlow + 2 * self.window:
                                                                break

                                                            # hit found, do administation
                                                            if trcand[inbetween] == -1:
                                                                nrhitsfound += 1

                                                            trcand[inbetween] = im

                                        # looped over in between planes, collected enough hits?
                                        if nrhitsfound == nhitw:

                                            atrack = []

                                            # mark used hits
                                            trcand[ifirst] = ifr
                                            trcand[ilast] = il

                                            for i in range(ifirst, ilast + 1):

                                                if trcand[i] >= 0:
                                                    used[trcand[i]] = 1
                                                    atrack.append(trcand[i])

                                            # store the track
                                            nrtracks += 1

                                            track_inds.append(atrack)


        self.track_inds_ = numpy.array(track_inds)
        self.tracks_params_ = self.get_tracks_params(x, y, self.track_inds_, sample_weight)




########################################################################################################################
########################################################################################################################

from sklearn.linear_model import LinearRegression
import numpy



################################################## Main class ##########################################################


class FastHough(object):

    def __init__(self,
                 n_tracks=None,
                 min_hits=4,
                 k_size=0.1,
                 b_size=10,
                 k_limits=(-0.3, 0.3),
                 b_limits=(-800, 800),
                 unique_hit_labels=True):
        """
        Track pattern recognition method based on Hough Transform.

        Parameters
        ----------
        n_tracks : int
            Number of tracks to recognize.
        min_hits : int
            Min hits per track to be considered as recognized.
        k_size : int
            Size of k-bin in track parameter space (k, b). Track parametrization: y = k * x + b.
        b_size : int
            Size of b-bin in track parameter space (k, b). Track parametrization: y = k * x + b.
        k_limits : tuple
            Tuple (min, max) of min and max allowable k-values.
        b_limits : tuple
            Tuple (min, max) of min and max allowable b-values.
        unique_hit_labels : boolean
            Is it allowable to take a hit for several tracks of not.
        """


        self.n_tracks = n_tracks
        self.min_hits = min_hits

        self.k_size = k_size
        self.b_size = b_size

        self.k_limits = k_limits
        self.b_limits = b_limits

        self.unique_hit_labels = unique_hit_labels

    def transform(self, x, y):
        """
        This function performs fast Hough Transform.

        Parameters
        ----------
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.

        Return
        ------
        track_inds : array-like
            List of recognized tracks. Recognized track is a list of hit indexes correspond to one bin in track parameters space.
            Example: [[ind1, ind2, ind3, ...], [...], ...]
        """

        track_inds = []

        for first in range(0, len(x)-1):
            for second in range(first+1, len(x)):

                x1, y1, layer1 = x[first], y[first], x[first]
                x2, y2, layer2 = x[second], y[second], x[second]

                if layer1 == layer2:
                    continue

                #if numpy.abs(x1 - x2) <= 100.:
                #    continue

                k = 1. * (y2 - y1) / (x2 - x1)
                b = y1 - k * x1

                if k >= self.k_limits[0] and k <= self.k_limits[1] and b >= self.b_limits[0] and b <= self.b_limits[1]:

                    one_track_inds = self.hits_in_bin(x, y, k, b)
                    one_track_inds1, one_track_inds2 = self.one_hit_per_layer(one_track_inds,
                                                                              x[one_track_inds],
                                                                              y[one_track_inds],
                                                                              x[one_track_inds],
                                                                              k,
                                                                              b)

                    if len(one_track_inds1) >= self.min_hits:
                        track_inds.append(one_track_inds1)

                    if len(one_track_inds2) >= self.min_hits:
                        track_inds.append(one_track_inds2)

        return numpy.array(track_inds)

    def one_hit_per_layer(self, track_inds, x, y, layer, k, b):
        """
        Drop hits from the same layer. In results, only one hit per layer remains.

        Parameters
        ----------
        track_inds : array-like
            Hit indexes of a track: [ind1, ind2, ...]
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.
        layer : array-like
            Array of layer ids of hits.
        k : float
            Track parameter: y = k * x + b
        b : float
            Track parameter: y = k * x + b

        Return
        ------
        track_inds1 : array-like
            Hit indexes of a track: [ind1, ind2, ...]
        track_inds2 : array-like
            Hit indexes of a track: [ind1, ind2, ...]
        """

        new_track_inds1 = []
        new_track_inds2 = []

        diff = numpy.abs(y - (b + k * x))
        sorted_inds = numpy.argsort(diff)
        used1 = []
        used2 = []

        for i in sorted_inds:

            if layer[i] not in used1:
                new_track_inds1.append(track_inds[i])
                used1.append(layer[i])
            elif layer[i] not in used2:
                new_track_inds2.append(track_inds[i])
                used2.append(layer[i])

        return numpy.array(new_track_inds1), numpy.array(new_track_inds2)


    def hits_in_bin(self, x, y, k_bin, b_bin):
        """
        Counts hits in a bin of track parameter space (b, k).

        Parameters
        ---------
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.
        k_bin : float
            Track parameter: y = k_bin * x + b_bin
        b_bin : float
            Track parameter: y = k_bin * x + b_bin

        Return
        ------
        track_inds : array-like
            Hit indexes of a track: [ind1, ind2, ...]
        """


        b_left = y - (k_bin - 0.5 * self.k_size) * x
        b_right = y - (k_bin + 0.5 * self.k_size) * x

        inds = numpy.arange(0, len(x))

        sel = (b_left >= b_bin - 0.5 * self.b_size) * (b_right <= b_bin + 0.5 * self.b_size) + \
              (b_left <= b_bin + 0.5 * self.b_size) * (b_right >= b_bin - 0.5 * self.b_size)

        track_inds = inds[sel]

        return track_inds



    def get_unique_hit_labels(self, track_inds, n_hits):
        """
        Selects the best track candidates. It supposed that a hit can belong to just one track.

        Parameters
        ----------
        track_inds : array-like
            List of recognized tracks. Recognized track is a list of hit indexes correspond to one bin in track parameters space.
            Example: [[ind1, ind2, ind3, ...], [...], ...]
        n_hits : int
            Number of hits in an event.

        Return
        ------
        track_inds : array-like
            List of recognized tracks. Recognized track is a list of hit indexes correspond to one bin in track parameters space.
            Example: [[ind1, ind2, ind3, ...], [...], ...]
        """

        new_track_inds = []
        used = numpy.zeros(n_hits)
        n_tracks = 0


        while 1:

            track_lens = numpy.array([len(i[used[i] == 0]) for i in track_inds])

            if len(track_lens) == 0:
                break

            max_len = track_lens.max()

            if max_len < self.min_hits:
                break

            one_track_inds = track_inds[track_lens == track_lens.max()][0]
            one_track_inds = one_track_inds[used[one_track_inds] == 0]

            used[one_track_inds] = 1
            new_track_inds.append(one_track_inds)

            n_tracks += 1
            if self.n_tracks != None and n_tracks >= self.n_tracks:
                break

        return numpy.array(new_track_inds)

    def remove_duplicates(self, track_inds):
        """
        Removes track duplicates.

        Parameters
        ----------
        track_inds : array-like
            List of recognized tracks. Recognized track is a list of hit indexes correspond to one bin in track parameters space.
            Example: [[ind1, ind2, ind3, ...], [...], ...]

        Return
        ------
        track_inds : array-like
            List of recognized tracks. Recognized track is a list of hit indexes correspond to one bin in track parameters space.
            Example: [[ind1, ind2, ind3, ...], [...], ...]
        """

        new_track_inds = []

        if len(track_inds) == 0:
            return numpy.array(new_track_inds)

        sorted_track_inds = [numpy.sort(track) for track in track_inds]

        for first_id in range(len(track_inds)-1):

            counter = 0
            first = sorted_track_inds[first_id]

            for second_id in range(first_id+1, len(track_inds)):

                second = sorted_track_inds[second_id]
                if list(first) == list(second):
                    counter += 1

            if counter == 0:
                new_track_inds.append(first)

        new_track_inds.append(sorted_track_inds[-1])

        return numpy.array(new_track_inds)

    def get_tracks_params(self, x, y, track_inds, sample_weight=None):
        """
        Estimates track parameters y = k * x + b for the recognized tracks.

        Parameters
        ----------
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.
        track_inds : array-like
            Hit indexes of a track: [ind1, ind2, ...]
        sample_weight : array-like
            Hit weights used during the track fit.

        Return
        ------
        tracks_params : array-like
            Track parameters [k, b].
        """

        tracks_params = []

        if len(track_inds) == 0:
            return []

        for track in track_inds:

            x_track = x[track]
            y_track = y[track]

            if sample_weight is not None:
                sample_weight_track = sample_weight[track]
            else:
                sample_weight_track = None

            lr = LinearRegression(copy_X=False)
            lr.fit(x_track.reshape(-1,1), y_track, sample_weight_track)

            params = list(lr.coef_) + [lr.intercept_]
            tracks_params.append(params)

        return numpy.array(tracks_params)


    def fit(self, x, y, sample_weight=None):
        """
        Runs track pattern recognition. Track parametrization: y = k * x + b.

        Parameters
        ----------
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.
        sample_weight : array-like
            Hit weights used during the track fit.
        """

        track_inds = self.transform(x, y)

        if self.unique_hit_labels:
            self.track_inds_ = self.get_unique_hit_labels(track_inds, len(x))
        else:
            self.track_inds_ = self.remove_duplicates(track_inds)

        self.tracks_params_ = self.get_tracks_params(x, y, self.track_inds_, sample_weight)




########################################################################################################################
########################################################################################################################

import numpy
from scipy.optimize import minimize


class ArtificialRetina(object):

    def __init__(self,
                 n_tracks,
                 min_hits,
                 residuals_threshold,
                 sigma,
                 k_size=0.1,
                 b_size=10,
                 k_limits=(-0.3, 0.3),
                 b_limits=(-800, 800),
                 unique_hit_labels=True):
        """
        Artificial Retina method of track pattern recognition.

        Parameters
        ----------
        n_tracks : int
            Number of tracks to recognize.
        min_hits : int
            Min hits per track to be considered as recognized.
        residuals_threshold : float
            Max hit distance from a track.
        sigma : float
            Standard deviation of hit form a track.
        k_size : int
            Size of k-bin in track parameter space (k, b). Track parametrization: y = k * x + b.
        b_size : int
            Size of b-bin in track parameter space (k, b). Track parametrization: y = k * x + b.
        k_limits : tuple
            Tuple (min, max) of min and max allowable k-values.
        b_limits : tuple
            Tuple (min, max) of min and max allowable b-values.
        unique_hit_labels : boolean
            Is it allowable to take a hit for several tracks of not.
        """

        self.n_tracks = n_tracks
        self.min_hits = min_hits
        self.sigma = sigma
        self.residuals_threshold = residuals_threshold

        self.k_size = k_size
        self.b_size = b_size

        self.k_limits = k_limits
        self.b_limits = b_limits

        self.unique_hit_labels = unique_hit_labels

        self.tracks_params_ = None
        self.track_inds_ = None

    def retina_func(self, track_prams, x, y, sigma, sample_weight=None):
        """
        Calculates the artificial retina function value.

        Parameters
        ----------
        track_prams : array-like
            Track parameters [k, b].
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.
        sigma : float
            Standard deviation of hit form a track.
        sample_weight : array-like
            Hit weights used during the track fit.

        Retunrs
        -------
        retina : float
            Negative value of the artificial retina function.
        """

        rs = track_prams[0] * x + track_prams[1] - y


        if sample_weight == None:
            exps = numpy.exp(- (rs/sigma)**2)
        else:
            exps = numpy.exp(- (rs/sigma)**2) * sample_weight


        retina = exps.sum()

        return -retina

    def retina_grad(self, track_prams, x, y, sigma, sample_weight=None):
        """
        Calculates the artificial retina gradient.

        Parameters
        ----------
        track_prams : array-like
            Track parameters [k, b].
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.
        sigma : float
            Standard deviation of hit form a track.
        sample_weight : array-like
            Hit weights used during the track fit.

        Retunrs
        -------
        retina : float
            Negative value of the artificial retina gradient.
        """

        rs = track_prams[0] * x + track_prams[1] - y


        if sample_weight == None:
            exps = numpy.exp(- (rs/sigma)**2)
        else:
            exps = numpy.exp(- (rs/sigma)**2) * sample_weight


        dks = - 2.*rs / sigma**2 * exps * x
        dbs = - 2.*rs / sigma**2 * exps

        return -numpy.array([dks.sum(), dbs.sum()])

    def one_hit_per_layer(self, track_inds, x, y, layer, k, b):
        """
        Drop hits from the same layer. In results, only one hit per layer remains.

        Parameters
        ----------
        track_inds : array-like
            Hit indexes of a track: [ind1, ind2, ...]
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.
        layer : array-like
            Array of layer ids of hits.
        k : float
            Track parameter: y = k * x + b
        b : float
            Track parameter: y = k * x + b

        Return
        ------
        track_inds1 : array-like
            Hit indexes of a track: [ind1, ind2, ...]
        track_inds2 : array-like
            Hit indexes of a track: [ind1, ind2, ...]
        """

        new_track_inds1 = []
        new_track_inds2 = []

        diff = numpy.abs(y - (b + k * x))
        sorted_inds = numpy.argsort(diff)
        used1 = []
        used2 = []

        for i in sorted_inds:

            if layer[i] not in used1:
                new_track_inds1.append(track_inds[i])
                used1.append(layer[i])
            elif layer[i] not in used2:
                new_track_inds2.append(track_inds[i])
                used2.append(layer[i])

        return numpy.array(new_track_inds1), numpy.array(new_track_inds2)

    def fit_one_track(self, x, y, sample_weight=None):
        """
        Finds the best track among hits. Track parametrization: y = k * x + b.

        Parameters
        ----------
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.
        sample_weight : array-like
            Hit weights used during the track fit.

        Returns
        -------
        track_prams : array-like
            Track parameters [k, b].
        """

        sigma = self.sigma


        rs = []
        ks = []
        bs = []

        for i in range(len(x)):
            for j in range(len(x)):

                if x[j] <= x[i]:
                    continue

                # if numpy.random.rand() > 0.5:
                #     continue

                x1 = x[i]
                x2 = x[j]
                y1 = y[i]
                y2 = y[j]

                k0 = (y2 - y1) / (x2 - x1)
                b0 = y1 - k0 * x1

                if k0 >= self.k_limits[0] and k0 <= self.k_limits[1] and b0 >= self.b_limits[0] and b0 <= self.b_limits[1]:

                    r = -self.retina_func([k0, b0], x, y, sigma, sample_weight)

                    rs.append(r)
                    ks.append(k0)
                    bs.append(b0)

        rs = numpy.array(rs)
        ks = numpy.array(ks)
        bs = numpy.array(bs)

        if len(rs) == 0:
            return []

        params = [ks[rs == rs.max()][0], bs[rs == rs.max()][0]]

        res = minimize(self.retina_func, params, args = (x, y, sigma, sample_weight), method='BFGS',
                       jac=self.retina_grad, options={'gtol': 1e-6, 'disp': False})

        params = res.x

        return res.x

    def fit(self, x, y, sample_weight=None):
        """
        Runs track pattern recognition. Track parametrization: y = k * x + b.

        Parameters
        ----------
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.
        sample_weight : array-like
            Hit weights used during the track fit.
        """

        labels = -1 * numpy.ones(len(x))
        tracks_params = []
        track_inds = []

        if len(x) == 0:
            self.labels_ = labels
            self.tracks_params_ = numpy.array(tracks_params)
            self.track_inds_ = numpy.array(track_inds)
            return


        used = numpy.zeros(len(x))
        indexes = numpy.arange(len(x))

        for track_id in range(self.n_tracks):

            x_track = x[used == 0]
            y_track = y[used == 0]

            if sample_weight == None:
                sample_weight_track = None
            else:
                sample_weight_track = sample_weight[used == 0]

            if len(numpy.unique(x_track)) < self.min_hits or len(x_track) <= 0:
                break

            one_track_params = self.fit_one_track(x_track, y_track, sample_weight_track)

            if len(one_track_params) == 0:
                break # continue

            dists = numpy.abs(one_track_params[0] * x + one_track_params[1] - y)
            dist_mask = (dists <= self.residuals_threshold)

            if (dist_mask * 1).sum() < self.min_hits:
                if self.unique_hit_labels == True:
                    used[dist_mask] = 1
                break # continue

            atrack = indexes[dist_mask & (used == 0)]
            atrack, _ = self.one_hit_per_layer(atrack, x[atrack], y[atrack], x[atrack], one_track_params[0], one_track_params[1])
            track_inds.append(atrack)
            if self.unique_hit_labels == True:
                used[atrack] = 1

            if len(atrack) >= 2:
                one_track_params = numpy.polyfit(x[atrack], y[atrack], 1)
            else:
                one_track_params = []
            tracks_params.append(one_track_params)


        self.tracks_params_ = numpy.array(tracks_params)
        self.track_inds_ = numpy.array(track_inds)



########################################################################################################################
########################################################################################################################


def get_track_ids(stree, smeared_hits):
    """
    Estimate MC true track ids of hits.

    Parameters
    ----------
    stree : root file
        Events in raw format.
    smeared_hits : list of dicts
        List of smeared hits. A smeared hit is a dictionary:
        {'digiHit':key,'xtop':top x,'ytop':top y,'z':top z,'xbot':bot x,'ybot':bot y,'dist':smeared dist2wire}

    Returns
    -------
    y : array-like
        MC true track ids of hits.
    """

    y = []

    for i in range(len(smeared_hits)):

        track_id = stree.strawtubesPoint[i].GetTrackID()
        y.append(track_id)

    return numpy.array(y)

########################################################################################################################

def get_fitted_trackids(y, reco_tracks):
    """
    Estimates max fraction of MC true track id for recognized tracks.

    Parameters
    ----------
    y : array-like
        MC true track ids of hits.
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
    fittedtrackids : array-like
        List of MC true track id with max fraction for recognized tracks.
    fittedtrackfrac : array-like
        List of max fractions of MC true track id for recognized tracks.
    """

    fittedtrackids = []
    fittedtrackfrac = []

    for track_id in reco_tracks.keys():
        
        if reco_tracks[track_id]['flag'] != 1:
            continue

        frac, tmax = fracMCsame(y[reco_tracks[track_id]['hits']])
        fittedtrackids.append(tmax)
        fittedtrackfrac.append(frac)

    return fittedtrackids, fittedtrackfrac


########################################################################################################################

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

########################################################################################################################

def remove_clones(tracks, max_shared_hits=0):
    
    results = []
    
    tot_max = 0
    for atrack in tracks:
        amax = max(atrack)
        if amax > tot_max:
            tot_max = amax
    used = numpy.zeros(tot_max+1)
    
    
    for i_track, atrack in enumerate(tracks):
        n_shared_hits = used[atrack].sum()
        if n_shared_hits <= max_shared_hits:
            used[atrack] = 1
            results.append(i_track)
    
    return results


########################################################################################################################
########################################################################################################################




########################################################################################################################
########################################################################################################################