# Mikhail Hushchyn, mikhail.hushchyn@cern.ch

import ROOT
import numpy

import getopt
import sys

# For ShipGeo
from ShipGeoConfig import ConfigRegistry
from rootpyPickler import Unpickler

# For modules
import shipDet_conf
import __builtin__ as builtin

# For track pattern recognition


def get_n_hits(hits):
    return len(hits)




def run_track_pattern_recognition(input_file, geo_file, output_file, method):
    """
    Runs all steps of track pattern recognition.

    Parameters
    ----------
    input_file : string
        Path to an input .root file with events.
    geo_file : string
        Path to a file with SHiP geometry.
    output_file : string
        Path to an output .root file with quality plots.
    method : string
        Name of a track pattern recognition method.
    """


    ############################################# Load SHiP geometry ###################################################

    # Check geo file
    try:
        fgeo = ROOT.TFile(geo_file)
    except:
        print "An error with opening the ship geo file."
        raise

    sGeo = fgeo.FAIRGeom

    # Prepare ShipGeo dictionary
    if not fgeo.FindKey('ShipGeo'):

        if sGeo.GetVolume('EcalModule3') :
            ecalGeoFile = "ecal_ellipse6x12m2.geo"
        else:
            ecalGeoFile = "ecal_ellipse5x10m2.geo"

        if dy:
            ShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", Yheight = dy, EcalGeoFile = ecalGeoFile)
        else:
            ShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", EcalGeoFile = ecalGeoFile)

    else:
        upkl    = Unpickler(fgeo)
        ShipGeo = upkl.load('ShipGeo')
    
    # Globals
    builtin.ShipGeo = ShipGeo

    ############################################# Load SHiP modules ####################################################

    run = ROOT.FairRunSim()
    modules = shipDet_conf.configure(run,ShipGeo)

    ############################################# Load inpur data file #################################################

    # Check input file
    try:
        fn = ROOT.TFile(input_file,'update')
    except:
        print "An error with opening the input data file."
        raise

    sTree = fn.cbmsim
    sTree.Write()
    
    ############################################# Create hists #########################################################
    
    h = init_book_hist()

    ########################################## Start Track Pattern Recognition #########################################
    import shipPatRec

    # Init book of hists for the quality measurements
    metrics = {'n_hits': [], 
               'reconstructible': 0, 
               'passed_y12': 0, 'passed_stereo12': 0, 'passed_12': 0, 
               'passed_y34': 0, 'passed_stereo34': 0, 'passed_34': 0, 
               'passed_combined': 0, 'reco_passed': 0, 'reco_passed_no_clones': 0,
               'frac_y12': [], 'frac_stereo12': [], 'frac_12': [], 
               'frac_y34': [], 'frac_stereo34': [], 'frac_34': [], 
               'reco_frac_tot': [], 
               'reco_mc_p': [], 'reco_mc_theta': [], 
               'fitted_p': [], 'fitted_pval': [], 'fitted_chi': [], 
               'fitted_x': [], 'fitted_y': [], 'fitted_z': [], 'fitted_mass': []}

    # Start event loop
    nEvents   = sTree.GetEntries()
   

    for iEvent in range(nEvents):

        if iEvent%1000 == 0:
            print 'Event ', iEvent

        ########################################### Select one event ###################################################

        rc = sTree.GetEvent(iEvent)

        ########################################### Reconstructible tracks #############################################

        reconstructible_tracks = getReconstructibleTracks(iEvent, sTree, sGeo, ShipGeo)
        
        metrics['reconstructible'] += len(reconstructible_tracks)
        for i_reco in reconstructible_tracks:
            h['TracksPassed'].Fill("Reconstructible tracks", 1)
            h['TracksPassedU'].Fill("Reconstructible tracks", 1)
            
        in_y12 = []
        in_stereo12 = []
        in_12 = []
        in_y34 = []
        in_stereo34 = []
        in_34 = []
        in_combo = []
        
        ########################################## Recognized tracks ###################################################
        
        nTracklets = sTree.Tracklets.GetEntriesFast()
        
        for i_track in range(nTracklets):
            
            atracklet = sTree.Tracklets[i_track]
            
            if atracklet.getType() != 1: # this is a not full track (tracklet)
                continue
                
            atrack = atracklet.getList()
            
            if atrack.size() == 0:
                continue
            
            hits = {'X': [], 'Y': [], 'Z': [], 
                    'DetID': [], 'TrackID': [], 
                    'Pz': [], 'Px': [], 'Py': [], 
                    'dist2Wire': [], 'Pdg': []}
            
            for ihit in atrack:
                ahit = sTree.strawtubesPoint[ihit]
                hits['X'] += [ahit.GetX()]
                hits['Y'] += [ahit.GetY()]
                hits['Z'] += [ahit.GetZ()]
                hits['DetID'] += [ahit.GetDetectorID()]
                hits['TrackID'] += [ahit.GetTrackID()]
                hits['Pz'] += [ahit.GetPz()]
                hits['Px'] += [ahit.GetPx()]
                hits['Py'] += [ahit.GetPy()]
                hits['dist2Wire'] += [ahit.dist2Wire()]
                hits['Pdg'] += [ahit.PdgCode()]
                
            # List to numpy arrays
            for key in hits.keys():
                hits[key] = numpy.array(hits[key])
                
            # Decoding
            statnb, vnb, pnb, lnb, snb = decodeDetectorID(hits['DetID'])
            is_stereo = ((vnb == 1) + (vnb == 2))
            is_y = ((vnb == 0) + (vnb == 3))
            is_before = ((statnb == 1) + (statnb == 2))
            is_after = ((statnb == 3) + (statnb == 4)) 
                
            
            # Metrics
            metrics['n_hits'] += [get_n_hits(hits['TrackID'])]
            
            # Tracks passed
            frac_y12, tmax_y12 = fracMCsame(hits['TrackID'][is_before * is_y])
            n_hits_y12 = get_n_hits(hits['TrackID'][is_before * is_y])
            frac_stereo12, tmax_stereo12 = fracMCsame(hits['TrackID'][is_before * is_stereo])
            n_hits_stereo12 = get_n_hits(hits['TrackID'][is_before * is_stereo])
            frac_12, tmax_12 = fracMCsame(hits['TrackID'][is_before])
            n_hits_12 = get_n_hits(hits['TrackID'][is_before])
            
            frac_y34, tmax_y34 = fracMCsame(hits['TrackID'][is_after * is_y])
            n_hits_y34 = get_n_hits(hits['TrackID'][is_after * is_y])
            frac_stereo34, tmax_stereo34 = fracMCsame(hits['TrackID'][is_after * is_stereo])
            n_hits_stereo34 = get_n_hits(hits['TrackID'][is_after * is_stereo])
            frac_34, tmax_34 = fracMCsame(hits['TrackID'][is_after])
            n_hits_34 = get_n_hits(hits['TrackID'][is_after])
            frac_tot, tmax_tot = fracMCsame(hits['TrackID'])
            n_hits_tot = get_n_hits(hits['TrackID'])
            
            is_reconstructed = 0
            is_reconstructed_no_clones = 0
            
            
            if tmax_y12 in reconstructible_tracks:
                metrics['passed_y12'] += 1
                metrics['frac_y12'] += [frac_y12]
                h['TracksPassed'].Fill("Y view station 1&2", 1)
                if tmax_y12 not in in_y12:
                    h['TracksPassedU'].Fill("Y view station 1&2", 1)
                    in_y12.append(tmax_y12)
                
                if tmax_stereo12 == tmax_y12:
                    metrics['passed_stereo12'] += 1
                    metrics['frac_stereo12'] += [frac_stereo12]
                    h['TracksPassed'].Fill("Stereo station 1&2", 1)
                    if tmax_stereo12 not in in_stereo12:
                        h['TracksPassedU'].Fill("Stereo station 1&2", 1)
                        in_stereo12.append(tmax_stereo12)
                    
                    if tmax_12 == tmax_y12:
                        metrics['passed_12'] += 1
                        metrics['frac_12'] += [frac_12]
                        h['TracksPassed'].Fill("station 1&2", 1)
                        if tmax_12 not in in_12:
                            h['TracksPassedU'].Fill("station 1&2", 1)
                            in_12.append(tmax_12)
                        
                        if tmax_y34 in reconstructible_tracks:
                            metrics['passed_y34'] += 1
                            metrics['frac_y34'] += [frac_y34]
                            h['TracksPassed'].Fill("Y view station 3&4", 1)
                            if tmax_y34 not in in_y34:
                                h['TracksPassedU'].Fill("Y view station 3&4", 1)
                                in_y34.append(tmax_y34)
                            
                            if tmax_stereo34 == tmax_y34:
                                metrics['passed_stereo34'] += 1
                                metrics['frac_stereo34'] += [frac_stereo34]
                                h['TracksPassed'].Fill("Stereo station 3&4", 1)
                                if tmax_stereo34 not in in_stereo34:
                                    h['TracksPassedU'].Fill("Stereo station 3&4", 1)
                                    in_stereo34.append(tmax_stereo34)
                                
                                if tmax_34 == tmax_y34:
                                    metrics['passed_34'] += 1
                                    metrics['frac_34'] += [frac_34]
                                    h['TracksPassed'].Fill("station 3&4", 1)
                                    if tmax_34 not in in_34:
                                        h['TracksPassedU'].Fill("station 3&4", 1)
                                        in_34.append(tmax_34)
                                    
                                    if tmax_12 == tmax_34:
                                        metrics['passed_combined'] += 1
                                        h['TracksPassed'].Fill("Combined stations 1&2/3&4", 1)
                                        is_reconstructed = 1
                                        if tmax_34 not in in_combo:
                                            h['TracksPassedU'].Fill("Combined stations 1&2/3&4", 1)
                                            in_combo.append(tmax_34)
                                            is_reconstructed_no_clones = 1
                                        
            # For reconstructed tracks
            if is_reconstructed == 0:
                continue
                
            metrics['reco_passed'] += 1
            metrics['reco_passed_no_clones'] += 1
            metrics['reco_frac_tot'] += [frac_tot]
            
            # Momentum
            Pz = hits['Pz']
            Px = hits['Px']
            Py = hits['Py']
            P = numpy.sqrt(Pz**2 + Px**2 + Py**2)
            P = P[hits['TrackID'] == tmax_tot]
            p = numpy.mean(P)
            
            metrics['reco_mc_p'] += [p]
            h['TracksPassed_p'].Fill(p, 1)
            
            # Direction
            Z = hits['Z'][(hits['TrackID'] == tmax_tot) * is_before]
            X = hits['X'][(hits['TrackID'] == tmax_tot) * is_before]
            Y = hits['Y'][(hits['TrackID'] == tmax_tot) * is_before]
            Z = Z - Z[0]
            X = X - X[0]
            Y = Y - Y[0]
            R = numpy.sqrt(X**2 + Y**2 + Z**2)
            Theta = numpy.arccos(Z[1:] / R[1:])
            theta = numpy.mean(Theta)
            
            metrics['reco_mc_theta'] += [theta]
            
            h['n_hits_reco_y12'].Fill(n_hits_y12)
            h['n_hits_reco_stereo12'].Fill(n_hits_stereo12)
            h['n_hits_reco_12'].Fill(n_hits_12)
            h['n_hits_reco_y34'].Fill(n_hits_y34)
            h['n_hits_reco_stereo34'].Fill(n_hits_stereo34)
            h['n_hits_reco_34'].Fill(n_hits_34)
            h['n_hits_reco'].Fill(n_hits_tot)
            
            h['n_hits_y12'].Fill(p, n_hits_y12)
            h['n_hits_stereo12'].Fill(p, n_hits_stereo12)
            h['n_hits_12'].Fill(p, n_hits_12)
            h['n_hits_y34'].Fill(p, n_hits_y34)
            h['n_hits_stereo34'].Fill(p, n_hits_stereo34)
            h['n_hits_34'].Fill(p, n_hits_34)
            h['n_hits_total'].Fill(p, n_hits_tot)
            
            h['frac_y12'].Fill(p, frac_y12)
            h['frac_stereo12'].Fill(p, frac_stereo12)
            h['frac_12'].Fill(p, frac_12)
            h['frac_y34'].Fill(p, frac_y34)
            h['frac_stereo34'].Fill(p, frac_stereo34)
            h['frac_34'].Fill(p, frac_34)
            h['frac_total'].Fill(p, frac_tot)
            
            # Fitted track
            
            thetrack = sTree.FitTracks[i_track]
            
            fitStatus   = thetrack.getFitStatus()
            thetrack.prune("CFL") # http://sourceforge.net/p/genfit/code/HEAD/tree/trunk/core/include/Track.h#l280

            nmeas = fitStatus.getNdf()
            pval = fitStatus.getPVal()
            chi2 = fitStatus.getChi2() / nmeas
            
            metrics['fitted_pval'] += [pval]
            metrics['fitted_chi'] += [chi2]

            h['chi2fittedtracks'].Fill(chi2)
            h['pvalfittedtracks'].Fill(pval)

            fittedState = thetrack.getFittedState()
            fittedMom = fittedState.getMomMag()
            fittedMom = fittedMom #*int(charge)
            
            metrics['fitted_p'] += [fittedMom]
            perr = (p - fittedMom) / p
            h['ptrue-p/ptrue'].Fill(perr)
            h['perr'].Fill(p, perr)
            h['perr_direction'].Fill(numpy.rad2deg(theta), perr)

            if math.fabs(p) > 0.0 :
                h['pvspfitted'].Fill(p, fittedMom)
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
            
            metrics['fitted_x'] += [fittedx]
            metrics['fitted_y'] += [fittedy]
            metrics['fitted_z'] += [fittedz]
            metrics['fitted_mass'] += [fittedmass]
            
    ############################################# Save hists #########################################################
    
    save_hists(h, output_file)

    return metrics


    
    
################################################################################################################################
################################################################################################################################


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
        if track.has_key(tid):
            track[tid] += 1
        else:
            track[tid] = 1
    
    #now get track with largest number of hits
    if track != {}:
        tmax = max(track, key=track.get)
    else:
        track = {-999: 0}
        tmax = -999

    frac=0.0
    if nh > 0: 
        frac = float(track[tmax]) / float(nh)

    return frac, tmax


########################################################################################################################

def getReconstructibleTracks(iEvent, sTree, sGeo, ShipGeo):
    """
    Estimates reconstructible tracks of an event.

    Parameters
    ----------
    iEvent : int
        Event id.
    stree : root file
        Events in raw format.
    fGeo : object
        Contains SHiP detector geometry.
    ShipGeo : object
        Contains SHiP detector geometry.

    Returns
    -------
    MCTrackIDs : array-like
        List of reconstructible track ids.
    """

    VetoStationZ = ShipGeo.vetoStation.z
    VetoStationEndZ = VetoStationZ + (ShipGeo.strawtubes.DeltazView + ShipGeo.strawtubes.OuterStrawDiameter) / 2

    TStationz = ShipGeo.TrackStation1.z
    Zpos = TStationz - 3. /2. * ShipGeo.strawtubes.DeltazView - 1. / 2. * ShipGeo.strawtubes.DeltazPlane - 1. / 2. * ShipGeo.strawtubes.DeltazLayer
    TStation1StartZ = Zpos - ShipGeo.strawtubes.OuterStrawDiameter / 2

    Zpos = TStationz + 3. /2. * ShipGeo.strawtubes.DeltazView + 1. / 2. * ShipGeo.strawtubes.DeltazPlane + 1. / 2. * ShipGeo.strawtubes.DeltazLayer
    TStation4EndZ = Zpos + ShipGeo.strawtubes.OuterStrawDiameter / 2


    PDG=ROOT.TDatabasePDG.Instance()

    #returns a list of reconstructible tracks for this event
    #call this routine once for each event before smearing
    MCTrackIDs=[]
    rc = sTree.GetEvent(iEvent)
    nMCTracks = sTree.MCTrack.GetEntriesFast()

    
    #1. MCTrackIDs: list of tracks decaying after the last tstation and originating before the first
    for i in reversed(range(nMCTracks)):
        atrack = sTree.MCTrack.At(i)
        #track endpoint after tstations?
        if atrack.GetStartZ() > TStation4EndZ :
            motherId = atrack.GetMotherId()
            if motherId > -1 :
                mothertrack = sTree.MCTrack.At(motherId)
                mothertrackZ = mothertrack.GetStartZ()
                #this mother track is a HNL decay
                #track starts inside the decay volume? (after veto, before 1 st tstation)
                if mothertrackZ < TStation1StartZ and mothertrackZ > VetoStationEndZ:
                    if motherId not in MCTrackIDs:
                        MCTrackIDs.append(motherId)
                            
    if len(MCTrackIDs)==0: 
        return MCTrackIDs

    
    
    #2. hitsinTimeDet: list of tracks with hits in TimeDet
    nVetoHits = sTree.vetoPoint.GetEntriesFast()
    hitsinTimeDet=[]
    for i in range(nVetoHits):
        avetohit = sTree.vetoPoint.At(i)
        #hit in TimeDet?
        if sGeo.FindNode(avetohit.GetX(), avetohit.GetY(), avetohit.GetZ()).GetName() == 'TimeDet_1':
            if avetohit.GetTrackID() not in hitsinTimeDet:
                hitsinTimeDet.append(avetohit.GetTrackID())

    
    
    #3. Remove tracks from MCTrackIDs that are not in hitsinTimeDet
    itemstoremove = []
    for item in MCTrackIDs:
        if item not in hitsinTimeDet:
            itemstoremove.append(item)
    for item in itemstoremove:
        MCTrackIDs.remove(item)

    if len(MCTrackIDs)==0: 
        return MCTrackIDs
    
    
    
    #4. Find straws that have multiple hits
    nHits = sTree.strawtubesPoint.GetEntriesFast()
    hitstraws = {}
    duplicatestrawhit = []

    for i in range(nHits):
        ahit = sTree.strawtubesPoint[i]
        if (str(ahit.GetDetectorID())[:1]=="5") :
            continue
        strawname = str(ahit.GetDetectorID())

        if hitstraws.has_key(strawname):
            #straw was already hit
            if ahit.GetX() > hitstraws[strawname][1]:
                #this hit has higher x, discard it
                duplicatestrawhit.append(i)
            else:
                #del hitstraws[strawname]
                duplicatestrawhit.append(hitstraws[strawname][0])
                hitstraws[strawname] = [i,ahit.GetX()]
        else:
            hitstraws[strawname] = [i,ahit.GetX()]

    
    
    #5. Split hits up by station and outside stations
    hits1={}
    hits2={}
    hits3={}
    hits4={}
    trackoutsidestations=[]
    
    for i in range(nHits):
        
        if i in  duplicatestrawhit:
            continue
            
        ahit = sTree.strawtubesPoint[i]
        
        # is hit inside acceptance? if not mark the track as bad
        if (((ahit.GetX()/245.)**2 + (ahit.GetY()/495.)**2) >= 1.):
            if ahit.GetTrackID() not in trackoutsidestations:
                trackoutsidestations.append(ahit.GetTrackID())
        
        if ahit.GetTrackID() not in MCTrackIDs:
            #hit on not reconstructible track
            continue
            
        #group hits per tracking station, key = trackid
        if str(ahit.GetDetectorID())[:1]=="1" :
            if hits1.has_key(ahit.GetTrackID()):
                hits1[ahit.GetTrackID()] = [hits1[ahit.GetTrackID()][0], i]
            else:
                hits1[ahit.GetTrackID()] = [i]
        
        if str(ahit.GetDetectorID())[:1]=="2" :
            if hits2.has_key(ahit.GetTrackID()):
                hits2[ahit.GetTrackID()] = [hits2[ahit.GetTrackID()][0], i]
            else:
                hits2[ahit.GetTrackID()] = [i]
        
        if str(ahit.GetDetectorID())[:1]=="3" :
            if hits3.has_key(ahit.GetTrackID()):
                hits3[ahit.GetTrackID()] = [hits3[ahit.GetTrackID()][0], i]
            else:
                hits3[ahit.GetTrackID()] = [i]
        
        if str(ahit.GetDetectorID())[:1]=="4" :
            if hits4.has_key(ahit.GetTrackID()):
                hits4[ahit.GetTrackID()] = [hits4[ahit.GetTrackID()][0], i]
            else:
                hits4[ahit.GetTrackID()] = [i]

    
    
    #6. Make list of tracks with hits in in station 1,2,3 & 4
    tracks_with_hits_in_all_stations = []
    
    for key in hits1.keys():
        if (hits2.has_key(key) and hits3.has_key(key) ) and hits4.has_key(key):
            if key not in tracks_with_hits_in_all_stations and key not in trackoutsidestations:
                tracks_with_hits_in_all_stations.append(key)
    
    for key in hits2.keys():
        if (hits1.has_key(key) and hits3.has_key(key) ) and hits4.has_key(key):
            if key not in tracks_with_hits_in_all_stations and key not in trackoutsidestations:
                tracks_with_hits_in_all_stations.append(key)
    
    for key in hits3.keys():
        if ( hits2.has_key(key) and hits1.has_key(key) ) and hits4.has_key(key):
            if key not in tracks_with_hits_in_all_stations and key not in trackoutsidestations:
                tracks_with_hits_in_all_stations.append(key)
    
    for key in hits4.keys():
        if (hits2.has_key(key) and hits3.has_key(key)) and hits1.has_key(key):
            if key not in tracks_with_hits_in_all_stations and key not in trackoutsidestations:
                tracks_with_hits_in_all_stations.append(key)

    
    
    #7. Remove tracks from MCTrackIDs with hits outside acceptance or doesn't have hits in all stations
    itemstoremove = []
    
    for item in MCTrackIDs:
        if item not in tracks_with_hits_in_all_stations:
            itemstoremove.append(item)
    
    for item in itemstoremove:
        MCTrackIDs.remove(item)

    if len(MCTrackIDs)==0: 
        return MCTrackIDs
    
    # itemstoremove = []
    
    # for item in MCTrackIDs:
    #     atrack = sTree.MCTrack.At(item)
    #     motherId=atrack.GetMotherId()
    #     if motherId != 2: #!!!!
    #         itemstoremove.append(item)
    
    # for item in itemstoremove:
    #     MCTrackIDs.remove(item)

    
    
    return MCTrackIDs


#################################################################################################################################
#################################################################################################################################

import ROOT
import numpy
import rootUtils as ut
import math

################################################ Helping functions #####################################################


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

    ut.bookHist(h,'TracksPassed','Tracks passing the pattern recognition', 8, -0.5, 7.5)
    h['TracksPassed'].GetXaxis().SetBinLabel(1,"Reconstructible tracks")
    h['TracksPassed'].GetXaxis().SetBinLabel(2,"Y view station 1&2")
    h['TracksPassed'].GetXaxis().SetBinLabel(3,"Stereo station 1&2")
    h['TracksPassed'].GetXaxis().SetBinLabel(4,"station 1&2")
    h['TracksPassed'].GetXaxis().SetBinLabel(5,"Y view station 3&4")
    h['TracksPassed'].GetXaxis().SetBinLabel(6,"Stereo station 3&4")
    h['TracksPassed'].GetXaxis().SetBinLabel(7,"station 3&4")
    h['TracksPassed'].GetXaxis().SetBinLabel(8,"Combined stations 1&2/3&4")
    
    ut.bookHist(h,'TracksPassedU','Tracks passing the pattern recognition. No clones.', 8, -0.5, 7.5)
    h['TracksPassedU'].GetXaxis().SetBinLabel(1,"Reconstructible tracks")
    h['TracksPassedU'].GetXaxis().SetBinLabel(2,"Y view station 1&2")
    h['TracksPassedU'].GetXaxis().SetBinLabel(3,"Stereo station 1&2")
    h['TracksPassedU'].GetXaxis().SetBinLabel(4,"station 1&2")
    h['TracksPassedU'].GetXaxis().SetBinLabel(5,"Y view station 3&4")
    h['TracksPassedU'].GetXaxis().SetBinLabel(6,"Stereo station 3&4")
    h['TracksPassedU'].GetXaxis().SetBinLabel(7,"station 3&4")
    h['TracksPassedU'].GetXaxis().SetBinLabel(8,"Combined stations 1&2/3&4")

    ut.bookProf(h, 'TracksPassed_p', 'Tracks passing the pattern recognition from momentum', 30, 0, 150)
    h['TracksPassed_p'].GetXaxis().SetTitle('Momentum')
    h['TracksPassed_p'].GetYaxis().SetTitle('N')

    ut.bookHist(h,'ptrue-p/ptrue','(p - p-true)/p',200,-1.,1.)


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

    ut.bookProf(h,'perr_direction','(p - p-true)/p from track direction in YZ plane',20, 0, 10.01)
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


    # Fitted values
    ut.bookHist(h,'chi2fittedtracks','Chi^2 per NDOF for fitted tracks',210,-0.05,20.05)
    ut.bookHist(h,'pvalfittedtracks','pval for fitted tracks',110,-0.05,1.05)
    ut.bookHist(h,'momentumfittedtracks','momentum for fitted tracks',251,-0.05,250.05)
    ut.bookHist(h,'xdirectionfittedtracks','x-direction for fitted tracks',91,-0.5,90.5)
    ut.bookHist(h,'ydirectionfittedtracks','y-direction for fitted tracks',91,-0.5,90.5)
    ut.bookHist(h,'zdirectionfittedtracks','z-direction for fitted tracks',91,-0.5,90.5)
    ut.bookHist(h,'massfittedtracks','mass fitted tracks',210,-0.005,0.205)
    ut.bookHist(h,'pvspfitted','p-patrec vs p-fitted',401,-200.5,200.5,401,-200.5,200.5)



    return h


########################################################### Main ###############################################################
################################################################################################################################


#if __name__ == "__main__":

input_file = None
geo_file = None
output_file = 'hists.root'
method = 'Baseline'


argv = sys.argv[1:]

msg = '''Runs ship track pattern recognition.\n\
    Usage:\n\
      python RunPR.py [options] \n\
    Example: \n\
      python RunPR.py -f "ship.conical.Pythia8-TGeant4.root" -g "geofile_full.conical.Pythia8-TGeant4.root"
    Options:
      -f  --input                   : Input file path
      -g  --geo                     : Path to geo file
      -o  --output                  : Output .root file path. Default is hists.root
      -m  --method                  : Name of a track pattern recognition method: 'Baseline', 'FH', 'AR', 'R'
                                    : Default is 'Baseline'
      -h  --help                    : Shows this help
      '''

try:
    opts, args = getopt.getopt(argv, "hm:f:g:o:",
                                   ["help", "method=", "input=", "geo=", "output="])
except getopt.GetoptError:
    print "Wrong options were used. Please, read the following help:\n"
    print msg
    sys.exit(2)
if len(argv) == 0:
    print msg
    sys.exit(2)
for opt, arg in opts:
    if opt in ('-h', "--help"):
        print msg
        sys.exit()
    elif opt in ("-m", "--method"):
        method = arg
    elif opt in ("-f", "--input"):
        input_file = arg
    elif opt in ("-g", "--geo"):
        geo_file = arg
    elif opt in ("-o", "--output"):
        output_file = arg


metrics = run_track_pattern_recognition(input_file, geo_file, output_file, method)