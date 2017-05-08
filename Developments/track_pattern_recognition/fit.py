__author__ = 'Mikhail Hushchyn'

import ROOT
import numpy
from array import array
import shipunit  as u

def prepare_theTrack(ShipGeo, hitPosList, charge, pinv):

    nM = len(hitPosList)

    if int(charge)<0:
        pdg=13
    else:
        pdg=-13
    rep = ROOT.genfit.RKTrackRep(pdg)
    posM = ROOT.TVector3(0, 0, 0)
    #would be the correct way but due to uncertainties on small angles the sqrt is often negative
    if abs(pinv) > 0.0 : momM = ROOT.TVector3(0,0,int(charge)/pinv)
    else: momM = ROOT.TVector3(0,0,999)
    covM = ROOT.TMatrixDSym(6)
    resolution = ShipGeo.strawtubes.sigma_spatial
    for  i in range(3):   covM[i][i] = resolution*resolution
    covM[0][0]=resolution*resolution*100.
    for  i in range(3,6): covM[i][i] = ROOT.TMath.Power(resolution / nM / ROOT.TMath.Sqrt(3), 2)
    # smeared start state
    stateSmeared = ROOT.genfit.MeasuredStateOnPlane(rep)
    rep.setPosMomCov(stateSmeared, posM, momM, covM)
    # create track
    seedState = ROOT.TVectorD(6)
    seedCov   = ROOT.TMatrixDSym(6)
    rep.get6DStateCov(stateSmeared, seedState, seedCov)
    theTrack=ROOT.genfit.Track(rep, seedState, seedCov)

    return theTrack


def TrackFit(ShipGeo, fitter, hitPosList, theTrack, theTracks):
    debug=1
    #if debug==1: fitter.setDebugLvl(1)
    resolution = ShipGeo.strawtubes.sigma_spatial
    hitCov = ROOT.TMatrixDSym(7)
    hitCov[6][6] = resolution*resolution

    for item in hitPosList:

        itemarray=array('d',[item[0],item[1],item[2],item[3],item[4],item[5],item[6]])
        ms=ROOT.TVectorD(7,itemarray)
        tp = ROOT.genfit.TrackPoint(theTrack) # note how the point is told which track it belongs to
        measurement = ROOT.genfit.WireMeasurement(ms,hitCov,1,6,tp) # the measurement is told which trackpoint it belongs to
        measurement.setMaxDistance(0.5*u.cm)
        tp.addRawMeasurement(measurement) # package measurement in the TrackPoint
        theTrack.insertPoint(tp)  # add point to Track


    theTracks.append(theTrack)
    if not debug == 1:
        return # leave track fitting shipDigiReco
#check
    if not theTrack.checkConsistency():
        if debug==1: print 'Problem with track before fit, not consistent',theTrack
        return
# do the fit
    try:
        fitter.processTrack(theTrack)
    except:
        if debug==1: print "genfit failed to fit track"
        return
#check
    if not theTrack.checkConsistency():
        if debug==1: print 'Problem with track after fit, not consistent',theTrack
        return

    return

def track_fit(ShipGeo, reco_tracks):

    ########################################### Select a track fitter ##################################################

    geoMat =  ROOT.genfit.TGeoMaterialInterface()
    bfield = ROOT.genfit.BellField(ShipGeo.Bfield.max ,ShipGeo.Bfield.z,2, ShipGeo.Yheight/2.*u.m)
    fM = ROOT.genfit.FieldManager.getInstance()
    fM.init(bfield)
    ROOT.genfit.MaterialEffects.getInstance().init(geoMat)
    fitter = ROOT.genfit.DAF()

    ########################################### Fit recognized tracks ##################################################

    theTracks = []

    for track_id in reco_tracks.keys():

        theTrack = prepare_theTrack(ShipGeo,
                                    reco_tracks[track_id]['hitPosList'],
                                    reco_tracks[track_id]['charge'],
                                    reco_tracks[track_id]['pinv'])

        TrackFit(ShipGeo,
                 fitter,
                 reco_tracks[track_id]['hitPosList'],
                 theTrack,
                 theTracks)

    return theTracks


