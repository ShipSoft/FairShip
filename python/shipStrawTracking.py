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



def run_track_pattern_recognition(input_file, geo_file, output_file, dy, reconstructiblerequired, threeprong, method):
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
    dy : float
    reconstructiblerequired : int
        Number of reconstructible tracks in an event.
    threeprong : int
        If 1 - HNL decay into 3 particles is considered.
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

    ########################################## Start Track Pattern Recognition #########################################
    import shipPatRec

    # Init book of hists for the quality measurements
    h = init_book_hist()

    # Start event loop
    nEvents   = sTree.GetEntries()
   

    for iEvent in range(nEvents):

        if iEvent%1000 == 0:
            print 'Event ', iEvent

        ########################################### Select one event ###################################################

        rc = sTree.GetEvent(iEvent)

        ########################################### Smear hits #########################################################

        smeared_hits = smearHits(sTree, ShipGeo, modules, no_amb=None)

        if len(smeared_hits) == 0:
            continue

        ########################################### Do track pattern recognition #######################################
        
        ReconstructibleMCTracks = []
        fittedtrackids, reco_points  = shipPatRec.execute(smeared_hits, sTree, ReconstructibleMCTracks, method=method)
        reco_tracks = shipPatRec.reco_tracks
        theTracks = shipPatRec.theTracks

        ########################################### Get MC truth #######################################################

        y = get_track_ids(sTree, smeared_hits)

        fittedtrackids, fittedtrackfrac = get_fitted_trackids(y, reco_tracks)

        reco_mc_tracks = getReconstructibleTracks(iEvent,
                                                  sTree,
                                                  sGeo,
                                                  reconstructiblerequired,
                                                  threeprong,
                                                  ShipGeo)

        ########################################### Measure quality metrics ############################################

        quality_metrics(smeared_hits, sTree, reco_mc_tracks, reco_tracks, theTracks, reco_points, h)


    ############################################### Save results #######################################################

    save_hists(h, output_file)

    return


    
    
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

        frac, tmax = fracMCsame(y[reco_tracks[track_id]['hits']])
        fittedtrackids.append(tmax)
        fittedtrackfrac.append(frac)

    return fittedtrackids, fittedtrackfrac

########################################################################################################################

def getReconstructibleTracks(iEvent,sTree,sGeo, reconstructiblerequired, threeprong, ShipGeo):
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
    reconstructiblerequired : int
        Number of tracks of HNL decay (2 or 3).
    threeprong : int
        0 - HNL decays into 2 particles, 1 - HNL decays into 3 particles
    ShipGeo : object
        Contains SHiP detector geometry.

    Returns
    -------
    MCTrackIDs : array-like
        List of reconstructible track ids.
    """

    VetoStationZ = ShipGeo.vetoStation.z
    VetoStationEndZ = VetoStationZ+(ShipGeo.strawtubes.DeltazView+ShipGeo.strawtubes.OuterStrawDiameter)/2

    TStationz = ShipGeo.TrackStation1.z
    Zpos = TStationz-3./2.*ShipGeo.strawtubes.DeltazView-1./2.*ShipGeo.strawtubes.DeltazPlane-1./2.*ShipGeo.strawtubes.DeltazLayer
    TStation1StartZ = Zpos-ShipGeo.strawtubes.OuterStrawDiameter/2

    Zpos = TStationz+3./2.*ShipGeo.strawtubes.DeltazView+1./2.*ShipGeo.strawtubes.DeltazPlane+1./2.*ShipGeo.strawtubes.DeltazLayer
    TStation4EndZ=Zpos+ShipGeo.strawtubes.OuterStrawDiameter/2

    debug = 0

    PDG=ROOT.TDatabasePDG.Instance()

    #returns a list of reconstructible tracks for this event
    #call this routine once for each event before smearing
    MCTrackIDs=[]
    rc = sTree.GetEvent(iEvent)
    nMCTracks = sTree.MCTrack.GetEntriesFast()

    if debug==1: print "event nbr",iEvent,"has",nMCTracks,"tracks"
    #1. MCTrackIDs: list of tracks decaying after the last tstation and originating before the first
    for i in reversed(range(nMCTracks)):
        atrack = sTree.MCTrack.At(i)
        #for 3 prong decays check if its a nu
        if threeprong == 1:
            if PDG.GetParticle(atrack.GetPdgCode()):
                if PDG.GetParticle(atrack.GetPdgCode()).GetName()[:5]=="nu_mu":
                    if (atrack.GetStartZ() < TStation1StartZ and  atrack.GetStartZ() > VetoStationEndZ) and i not in MCTrackIDs:
                        MCTrackIDs.append(i)
                else:
                    if atrack.GetStartZ() > TStation4EndZ :
                        motherId=atrack.GetMotherId()
                        if motherId > -1 :
                            mothertrack=sTree.MCTrack.At(motherId)
                            mothertrackZ=mothertrack.GetStartZ()
                            #this mother track is a HNL decay
                            #track starts inside the decay volume? (after veto, before 1 st tstation)
                            if mothertrackZ < TStation1StartZ and mothertrackZ > VetoStationEndZ:
                                if motherId not in MCTrackIDs:
                                    MCTrackIDs.append(motherId)
        else:
            #track endpoint after tstations?
            if atrack.GetStartZ() > TStation4EndZ :
                motherId=atrack.GetMotherId()
                if motherId > -1 :
                    mothertrack=sTree.MCTrack.At(motherId)
                    mothertrackZ=mothertrack.GetStartZ()
                    #this mother track is a HNL decay
                    #track starts inside the decay volume? (after veto, before 1 st tstation)
                    if mothertrackZ < TStation1StartZ and mothertrackZ > VetoStationEndZ:
                        if motherId not in MCTrackIDs:
                            MCTrackIDs.append(motherId)
    if debug==1: print "Tracks with origin in decay volume",MCTrackIDs
    if len(MCTrackIDs)==0: return MCTrackIDs

    #2. hitsinTimeDet: list of tracks with hits in TimeDet
    nVetoHits = sTree.vetoPoint.GetEntriesFast()
    hitsinTimeDet=[]
    for i in range(nVetoHits):
        avetohit = sTree.vetoPoint.At(i)
        #hit in TimeDet?
        if sGeo.FindNode(avetohit.GetX(),avetohit.GetY(),avetohit.GetZ()).GetName() == 'TimeDet_1':
            if avetohit.GetTrackID() not in hitsinTimeDet:
                hitsinTimeDet.append(avetohit.GetTrackID())

    #3. Remove tracks from MCTrackIDs that are not in hitsinTimeDet
    itemstoremove=[]
    for item in MCTrackIDs:
        if threeprong==1:
            #don't remove the nu
            if PDG.GetParticle(sTree.MCTrack.At(item).GetPdgCode()).GetName()[:5]!="nu_mu" and item not in hitsinTimeDet:
                itemstoremove.append(item)
        else :
            if item not in hitsinTimeDet:
                itemstoremove.append(item)
    for item in itemstoremove:
        MCTrackIDs.remove(item)

    if debug==1: print "Tracks with hits in timedet",MCTrackIDs
    if len(MCTrackIDs)==0: return MCTrackIDs
    #4. Find straws that have multiple hits
    nHits = sTree.strawtubesPoint.GetEntriesFast()
    hitstraws={}
    duplicatestrawhit=[]
    if debug==1: print "Nbr of Rawhits=",nHits

    for i in range(nHits):
        ahit = sTree.strawtubesPoint[i]
        if (str(ahit.GetDetectorID())[:1]=="5") :
            if debug==1: print "Hit in straw Veto detector. Rejecting."
            continue
        strawname=str(ahit.GetDetectorID())

        if hitstraws.has_key(strawname):
            #straw was already hit
            if ahit.GetX()>hitstraws[strawname][1]:
                #this hit has higher x, discard it
                duplicatestrawhit.append(i)
            else:
                #del hitstraws[strawname]
                duplicatestrawhit.append(hitstraws[strawname][0])
                hitstraws[strawname]=[i,ahit.GetX()]
        else:
            hitstraws[strawname]=[i,ahit.GetX()]

    #5. Split hits up by station and outside stations
    hits1={}
    hits2={}
    hits3={}
    hits4={}
    trackoutsidestations=[]
    for i in range(nHits):
        if i in  duplicatestrawhit:
            if debug==1: print "Duplicate hit",i,"not reconstructible, rejecting."
            continue
        ahit = sTree.strawtubesPoint[i]
        #is hit inside acceptance? if not mark the track as bad
        if (((ahit.GetX()/245.)**2 + (ahit.GetY()/495.)**2) >= 1.):
            if ahit.GetTrackID() not in trackoutsidestations:
                trackoutsidestations.append(ahit.GetTrackID())
        if ahit.GetTrackID() not in MCTrackIDs:
            #hit on not reconstructible track
            if debug==1: print "Hit not on reconstructible track. Rejecting."
            continue
            #group hits per tracking station, key = trackid
        if str(ahit.GetDetectorID())[:1]=="1" :
            if hits1.has_key(ahit.GetTrackID()):
                hits1[ahit.GetTrackID()]=[hits1[ahit.GetTrackID()][0],i]
            else:
                hits1[ahit.GetTrackID()]=[i]
        if str(ahit.GetDetectorID())[:1]=="2" :
            if hits2.has_key(ahit.GetTrackID()):
                hits2[ahit.GetTrackID()]=[hits2[ahit.GetTrackID()][0],i]
            else:
                hits2[ahit.GetTrackID()]=[i]
        if str(ahit.GetDetectorID())[:1]=="3" :
            if hits3.has_key(ahit.GetTrackID()):
                hits3[ahit.GetTrackID()]=[hits3[ahit.GetTrackID()][0],i]
            else:
                hits3[ahit.GetTrackID()]=[i]
        if str(ahit.GetDetectorID())[:1]=="4" :
            if hits4.has_key(ahit.GetTrackID()):
                hits4[ahit.GetTrackID()]=[hits4[ahit.GetTrackID()][0],i]
            else:
                hits4[ahit.GetTrackID()]=[i]

                #6. Make list of tracks with hits in in station 1,2,3 & 4
    tracks_with_hits_in_all_stations=[]
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
    itemstoremove=[]
    for item in MCTrackIDs:
        if threeprong==1:
            #don't remove the nu
            if PDG.GetParticle(sTree.MCTrack.At(item).GetPdgCode()).GetName()[:5]!="nu_mu" and item not in tracks_with_hits_in_all_stations:
                itemstoremove.append(item)
        else:
            if item not in tracks_with_hits_in_all_stations:
                itemstoremove.append(item)
    for item in itemstoremove:
        MCTrackIDs.remove(item)

    if debug==1:
        print "tracks_with_hits_in_all_stations",tracks_with_hits_in_all_stations
        print "Tracks with hits in all stations & inside acceptance ellipse",MCTrackIDs
    if len(MCTrackIDs)==0: return MCTrackIDs
    nbrechits=0
    for i in range(nHits):
        if i in  duplicatestrawhit:
            continue
        nbrechits+=1
        ahit = sTree.strawtubesPoint[i]
        if ahit.GetTrackID()>-1 and ahit.GetTrackID() in MCTrackIDs:
            atrack = sTree.MCTrack.At(ahit.GetTrackID())
            for j in range(ahit.GetTrackID()+1,nMCTracks) :
                childtrack = sTree.MCTrack.At(j)
                if childtrack.GetMotherId() == ahit.GetTrackID():
                    trackmomentum=atrack.GetP()
                    trackweight=atrack.GetWeight()
                    #rc=h['reconstructiblemomentum'].Fill(trackmomentum,trackweight)
                    motherId=atrack.GetMotherId()
                    if motherId==1 :
                        HNLmomentum=sTree.MCTrack.At(1).GetP()
                        #rc=h['HNLmomentumvsweight'].Fill(trackweight,HNLmomentum)
                        if j==nMCTracks :
                            trackmomentum=atrack.GetP()
                            trackweight=atrack.GetWeight()
                            #rc=h['reconstructiblemomentum'].Fill(trackmomentum,trackweight)
                            if atrack.GetMotherId()==1 :
                                HNLmomentum=sTree.MCTrack.At(1).GetP()
                                #rc=h['HNLmomentumvsweight'].Fill(trackweight,HNLmomentum)
    itemstoremove=[]
    for item in MCTrackIDs:
        atrack = sTree.MCTrack.At(item)
        motherId=atrack.GetMotherId()
        if motherId != 2: #!!!!
            itemstoremove.append(item)
    for item in itemstoremove:
        MCTrackIDs.remove(item)
        if debug==1: print "After removing the non HNL track, MCTrackIDs",MCTrackIDs
    if debug==1: print "Tracks with HNL mother",MCTrackIDs

    #8. check if the tracks are HNL children
    mufound=0
    pifound=0
    nu_mufound=0
    itemstoremove=[]
    if MCTrackIDs:
        for item in MCTrackIDs:
            try:
                if PDG.GetParticle(sTree.MCTrack.At(item).GetPdgCode()).GetName()[:2]=="mu"   : mufound+=1
                if PDG.GetParticle(sTree.MCTrack.At(item).GetPdgCode()).GetName()[:2]=="pi"   : pifound+=1
                if PDG.GetParticle(sTree.MCTrack.At(item).GetPdgCode()).GetName()[:5]=="nu_mu":
                    nu_mufound+=1
                    itemstoremove.append(item)
            except:
                if debug==1: print "Unknown particle with pdg code:",sTree.MCTrack.At(item).GetPdgCode()
        if reconstructiblerequired == 1 :
            if mufound!=1  and pifound!=1:
                if debug==1: print "No reconstructible pion or muon."
                MCTrackIDs=[]
        if reconstructiblerequired == 2 :
            if threeprong == 1 :
                if mufound!=2 or nu_mufound!=1 :
                    if debug==1: print "No reconstructible mu-mu-nu."
                    MCTrackIDs=[]
                else:
                    #remove the neutrino from MCTrackIDs for the rest
                    for item in itemstoremove:
                        MCTrackIDs.remove(item)
            else:
                if mufound!=1 or pifound!=1 :
                    if debug==1: print "No reconstructible pion and muon."
                    MCTrackIDs=[]
    if len(MCTrackIDs)>0:
        #rc=h['nbrhits'].Fill(nHits)
        #rc=h['nbrtracks'].Fill(nMCTracks)
        pass
    if debug==1: print "Tracks with required HNL decay particles",MCTrackIDs
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

    ut.bookHist(h,'NTracks', 'Number of tracks in an event',20,0.,20.01)
    ut.bookHist(h,'NRecoTracks', 'Number of recognised tracks in an event',20,0.,20.01)

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

def strawtubesPoint(stree, attribute):
    
    res = []
    nHits = stree.strawtubesPoint.GetEntriesFast()
    
    for i in range(nHits):
        
        ahit = stree.strawtubesPoint[i]
        val = getattr(ahit, attribute)()
        res.append(val)
        
    return numpy.array(res)


def quality_metrics(smeared_hits, stree, reco_mc_tracks, reco_tracks, theTracks, reco_points, h):
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
    reco_points : dict
        Dictionary of hits of an event:
        {'TrackID': [id1, id2, id3, ...]
         'DetID': [det_id1, det_id2, ...]
         'X': [x1, x2, x3, ...]
         'Y': [y1, y2, y3, ...]
         'Z': [z1, z2, z3, ...]
         'Px': [px1, px2, px3, ...]
         'Py': [py1, py2, py3, ...]
         'Pz': [pz1, pz2, pz3, ...]
         'PdgCode': [pdg1, pdg2, pdg3, ...]
         'dist2wire': [dist1, dist2, dist3, ...]}
         where len(reco_points) == len(event)
    h : dict
        Dictionary of plots.
    """

    ############################################## Init preparation ####################################################
    
    reco_track_id = reco_points['TrackID']
    reco_det_id = reco_points['DetID']
    reco_x = reco_points['X']
    reco_y = reco_points['Y']
    reco_z = reco_points['Z']
    reco_px = reco_points['Px']
    reco_py = reco_points['Py']
    reco_pz = reco_points['Pz']
    reco_pdg = reco_points['PdgCode']
    reco_dist2wire = reco_points['dist2wire']
    
    true_track_id = strawtubesPoint(stree, 'GetTrackID')
    true_det_id = strawtubesPoint(stree, 'GetDetectorID')
    true_x = strawtubesPoint(stree, 'GetX')
    true_y = strawtubesPoint(stree, 'GetY')
    true_z = strawtubesPoint(stree, 'GetZ')
    true_px = strawtubesPoint(stree, 'GetPx')
    true_py = strawtubesPoint(stree, 'GetPy')
    true_pz = strawtubesPoint(stree, 'GetPz')
    true_pdg = strawtubesPoint(stree, 'PdgCode')
    true_dist2wire = strawtubesPoint(stree, 'dist2Wire')
    
    true_p = numpy.sqrt(true_px**2 + true_py**2 + true_pz**2)
    reco_p = numpy.sqrt(reco_px**2 + reco_py**2 + reco_pz**2)
    
    unique_reco_track_id = numpy.unique(reco_track_id[reco_track_id != -999])
    
    ####################################################################################################################

    # Only for reconstructible events.
    if len(reco_mc_tracks) < 2:
        return
    
    ################################################## N tracks ########################################################
    
    n_tracks = len(numpy.unique(true_track_id))
    h['NTracks'].Fill(n_tracks)
    
    n_reco_tracks = len(unique_reco_track_id)
    h['NRecoTracks'].Fill(n_reco_tracks)
    
    ######################################## Split hits on stations and views ##########################################
    
    statnb, vnb, pnb, lnb, snb = decodeDetectorID(reco_det_id)
    
    is_stereo = ((vnb == 1) + (vnb == 2))
    is_y = ((vnb == 0) + (vnb == 3))
    is_before = ((statnb == 1) + (statnb == 2))
    is_after = ((statnb == 3) + (statnb == 4))
    

    ############################################# H hits of true tracks ################################################

    # N hits of true tracks
    for t in reco_mc_tracks:

        if t not in true_track_id:
            continue

        p = numpy.mean(true_p[true_track_id == t])

        n_y12 = len(true_track_id[(true_track_id == t) * is_before * is_y])
        n_stereo12 = len(true_track_id[(true_track_id == t) * is_before * is_stereo])
        n_12 = len(true_track_id[(true_track_id == t) * is_before])

        n_y34 = len(true_track_id[(true_track_id == t) * is_after * is_y])
        n_stereo34 = len(true_track_id[(true_track_id == t) * is_after * is_stereo])
        n_34 = len(true_track_id[(true_track_id == t) * is_after])

        n_tot = len(true_track_id[(true_track_id == t)])

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
    
    ############################################# H hits of reco tracks ###############################################
    
    for t in unique_reco_track_id:
        
        # if t not in true_track_id:
        #    continue

        # p = numpy.mean(true_p[reco_track_id == t])

        n_y12 = len(reco_track_id[(reco_track_id == t) * is_before * is_y])
        n_stereo12 = len(reco_track_id[(reco_track_id == t) * is_before * is_stereo])
        n_12 = len(reco_track_id[(reco_track_id == t) * is_before])

        n_y34 = len(reco_track_id[(reco_track_id == t) * is_after * is_y])
        n_stereo34 = len(reco_track_id[(reco_track_id == t) * is_after * is_stereo])
        n_34 = len(reco_track_id[(reco_track_id == t) * is_after])

        n_tot = len(reco_track_id[(reco_track_id == t)])

        h['n_hits_reco'].Fill(n_tot)

        h['n_hits_reco_12'].Fill(n_12)
        h['n_hits_reco_y12'].Fill(n_y12)
        h['n_hits_reco_stereo12'].Fill(n_stereo12)

        h['n_hits_reco_34'].Fill(n_34)
        h['n_hits_reco_y34'].Fill(n_y34)
        h['n_hits_reco_stereo34'].Fill(n_stereo34)


    ############################################## Events Passed #######################################################

    # Track combinations
    combinations = []
    for i in unique_reco_track_id:

        frac12, tmax12 = fracMCsame(true_track_id[(reco_track_id == i) * is_before])
        frac34, tmax34 = fracMCsame(true_track_id[(reco_track_id == i) * is_after])

        if tmax12 == tmax34:
            combinations.append(tmax12)

    unique_combs = numpy.unique(combinations)
    if len(unique_combs[numpy.in1d(unique_combs, reco_mc_tracks)]) == len(reco_mc_tracks):
        is_combined = 1
    else:
        is_combined = 0

        
    # Matching
    is_matched = numpy.zeros(len(reco_mc_tracks))
    charges = -1 + 2 * ((true_pdg == -13) + (true_pdg == 211))
    reco_charges = -1 + 2 * (reco_pdg == -11)

    for num, track_id in enumerate(reco_mc_tracks):
        for i in unique_reco_track_id:

            frac, tmax = fracMCsame(true_track_id[reco_track_id == i])
            if tmax == track_id:
                true_charge = charges[true_track_id == track_id][0]
                reco_charge = reco_charges[reco_track_id == i][0]
                if reco_charge == true_charge:
                    is_matched[num] = 1
                    
                    
    
    reco_true_id_y12 = []
    reco_true_id_stereo12 = []
    reco_true_id_12 = []
    reco_true_id_y34 = []
    reco_true_id_stereo34 = []
    reco_true_id_34 = []
    
    for i in unique_reco_track_id:

        frac_y12, tmax_y12 = fracMCsame(true_track_id[(reco_track_id == i) * is_before * is_y])
        frac_stereo12, tmax_stereo12 = fracMCsame(true_track_id[(reco_track_id == i) * is_before * is_stereo])
        frac_12, tmax_12 = fracMCsame(true_track_id[(reco_track_id == i) * is_before])
        
        frac_y34, tmax_y34 = fracMCsame(true_track_id[(reco_track_id == i) * is_after * is_y])
        frac_stereo34, tmax_stereo34 = fracMCsame(true_track_id[(reco_track_id == i) * is_after * is_stereo])
        frac_34, tmax_34 = fracMCsame(true_track_id[(reco_track_id == i) * is_after])
        
        reco_true_id_y12.append(tmax_y12)
        reco_true_id_stereo12.append(tmax_stereo12)
        reco_true_id_12.append(tmax_12)
        reco_true_id_y34.append(tmax_y34)
        reco_true_id_stereo34.append(tmax_stereo34)
        reco_true_id_34.append(tmax_34)
        


    # Events Passed
    if len(reco_mc_tracks) == 2:
        h['EventsPassed'].Fill("Reconstructible events", 1)

        if len(numpy.intersect1d(reco_true_id_y12, reco_mc_tracks)) == len(reco_mc_tracks):
            h['EventsPassed'].Fill("Y view station 1&2", 1)

            if len(numpy.intersect1d(reco_true_id_stereo12, reco_mc_tracks)) == len(reco_mc_tracks):
                h['EventsPassed'].Fill("Stereo station 1&2", 1)

                if len(numpy.intersect1d(reco_true_id_12, reco_mc_tracks)) == len(reco_mc_tracks):
                    h['EventsPassed'].Fill("station 1&2", 1)

                    if len(numpy.intersect1d(reco_true_id_y34, reco_mc_tracks)) == len(reco_mc_tracks):
                        h['EventsPassed'].Fill("Y view station 3&4", 1)

                        if len(numpy.intersect1d(reco_true_id_stereo34, reco_mc_tracks)) == len(reco_mc_tracks):
                            h['EventsPassed'].Fill("Stereo station 3&4", 1)

                            if len(numpy.intersect1d(reco_true_id_34, reco_mc_tracks)) == len(reco_mc_tracks):
                                h['EventsPassed'].Fill("station 3&4", 1)

                                if is_combined == 1:
                                    h['EventsPassed'].Fill("Combined stations 1&2/3&4", 1)

                                    if is_matched.sum() == len(reco_mc_tracks):
                                        h['EventsPassed'].Fill("Matched", 1)

    ################################################ Tracks Passed #####################################################

    
    charges = -1 + 2 * ((true_pdg == -13) + (true_pdg == 211))
    reco_charges = -1 + 2 * (reco_pdg == -11)
    
    if len(reco_mc_tracks) == 2:
        h['TracksPassed'].Fill("Reconstructible tracks", 1)
        h['TracksPassed'].Fill("Reconstructible tracks", 1)

    for i in unique_reco_track_id:

        frac, tmax = fracMCsame(true_track_id[(reco_track_id == i)])

        if tmax not in reco_mc_tracks:
            continue

        p = numpy.mean(true_p[true_track_id == tmax])

        true_charge = charges[true_track_id == tmax][0]
        reco_charge = reco_charges[reco_track_id == i][0]

        reco = 0

        try:
            _, tmax_y12 = fracMCsame(true_track_id[(reco_track_id == i) * is_before * is_y])
            _, tmax_stereo12 = fracMCsame(true_track_id[(reco_track_id == i) * is_before * is_stereo])
            _, tmax_12 = fracMCsame(true_track_id[(reco_track_id == i) * is_before])

            _, tmax_y34 = fracMCsame(true_track_id[(reco_track_id == i) * is_after * is_y])
            _, tmax_stereo34 = fracMCsame(true_track_id[(reco_track_id == i) * is_after * is_stereo])
            _, tmax_34 = fracMCsame(true_track_id[(reco_track_id == i) * is_after])
            
        except:
            
            h['TracksPassed_p'].Fill(p , reco)
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

        h['TracksPassed_p'].Fill(p, reco)

    
    ########################################### Momentum reconstruction ################################################

    for i in unique_reco_track_id:

        frac, tmax = fracMCsame(true_track_id[(reco_track_id == i)])
        pinv_true = numpy.mean(1./true_p[true_track_id == tmax])
        pinv = numpy.mean(1./reco_p[reco_track_id == i])
        charge = reco_charges[reco_track_id == i][0]

        if tmax not in reco_mc_tracks:
            continue

        err = 1 - pinv / pinv_true

        h['ptrue-p/ptrue'].Fill(err)
        h['perr'].Fill(1./pinv_true, err)
        
        x = true_z[(reco_track_id == i) * is_before * is_y]
        y = true_y[(reco_track_id == i) * is_before * is_y]
        
        if len(x) < 2 or len(y) < 2:
            continue

        ky12, by12 = numpy.polyfit(x, y, 1)

        deg = numpy.rad2deg(numpy.arctan(ky12))
        h['perr_direction'].Fill(deg, err)

    ########################################### Momentum dependencies  #################################################

    for i in unique_reco_track_id:

        frac, tmax = fracMCsame(true_track_id[(reco_track_id == i)])

        if tmax not in reco_mc_tracks:
            continue

        p = numpy.mean(true_p[true_track_id == tmax])

        x = reco_z[(reco_track_id == i) * is_before * is_y]
        y = reco_y[(reco_track_id == i) * is_before * is_y]
        if len(x) < 2 or len(y) < 2: continue
        ky12, by12 = numpy.polyfit(x, y, 1)
        
        x = reco_z[(reco_track_id == i) * is_before * is_stereo]
        y = reco_x[(reco_track_id == i) * is_before * is_stereo]
        if len(x) < 2 or len(y) < 2: continue
        kx12, bx12 = numpy.polyfit(x, y, 1)
        
        x = reco_z[(reco_track_id == i) * is_after * is_y]
        y = reco_y[(reco_track_id == i) * is_after * is_y]
        if len(x) < 2 or len(y) < 2: continue
        ky34, by34 = numpy.polyfit(x, y, 1)
        
        x = reco_z[(reco_track_id == i) * is_after * is_stereo]
        y = reco_x[(reco_track_id == i) * is_after * is_stereo]
        if len(x) < 2 or len(y) < 2: continue
        kx34, bx34 = numpy.polyfit(x, y, 1)
        
        

        frac_total, tmax_total = fracMCsame(true_track_id[(reco_track_id == i)])
        n_hits_total = len(true_track_id[(reco_track_id == i) * (true_track_id == tmax_total)])
        h['n_hits_total'].Fill(p, n_hits_total)
        h['frac_total'].Fill(p, frac_total)

        frac_y12, tmax_y12 = fracMCsame(true_track_id[(reco_track_id == i) * is_before * is_y])
        n_hits_y12 = len(true_track_id[(reco_track_id == i) * is_before * is_y * (true_track_id == tmax_total)])
        h['n_hits_y12'].Fill(p, n_hits_y12)
        h['frac_y12'].Fill(p, frac_y12)
        h['n_hits_y12_direction'].Fill(numpy.rad2deg(numpy.arctan(ky12)), n_hits_y12)

        frac_stereo12, tmax_stereo12 = fracMCsame(true_track_id[(reco_track_id == i) * is_before * is_stereo])
        n_hits_stereo12 = len(true_track_id[(reco_track_id == i) * is_before * is_stereo * (true_track_id == tmax_total)])
        h['n_hits_stereo12'].Fill(p, n_hits_stereo12)
        h['frac_stereo12'].Fill(p, frac_stereo12)
        h['n_hits_stereo12_direction'].Fill(numpy.rad2deg(numpy.arctan(kx12)), n_hits_stereo12)

        frac_12, tmax_12 = fracMCsame(true_track_id[(reco_track_id == i) * is_before])
        n_hits_12 = len(true_track_id[(reco_track_id == i) * is_before * (true_track_id == tmax_total)])
        h['n_hits_12'].Fill(p, n_hits_12)
        h['frac_12'].Fill(p, frac_12)

        frac_y34, tmax_y34 = fracMCsame(true_track_id[(reco_track_id == i) * is_after * is_y])
        n_hits_y34 = len(true_track_id[(reco_track_id == i) * is_after * is_y * (true_track_id == tmax_total)])
        h['n_hits_y34'].Fill(p, n_hits_y34)
        h['frac_y34'].Fill(p, frac_y34)
        h['n_hits_y34_direction'].Fill(numpy.rad2deg(numpy.arctan(ky34)), n_hits_y34)

        frac_stereo34, tmax_stereo34 = fracMCsame(true_track_id[(reco_track_id == i) * is_after * is_stereo])
        n_hits_stereo34 = len(true_track_id[(reco_track_id == i) * is_after * is_stereo * (true_track_id == tmax_total)])
        h['n_hits_stereo34'].Fill(p, n_hits_stereo34)
        h['frac_stereo34'].Fill(p, frac_stereo34)
        h['n_hits_stereo34_direction'].Fill(numpy.rad2deg(numpy.arctan(kx34)), n_hits_stereo34)

        frac_34, tmax_34 = fracMCsame(true_track_id[(reco_track_id == i) * is_after])
        n_hits_34 = len(true_track_id[(reco_track_id == i) * is_after * (true_track_id == tmax_total)])
        h['n_hits_34'].Fill(p, n_hits_34)
        h['frac_34'].Fill(p, frac_34)

    #################################### Angle between two reconstructible tracks ######################################
    # Attention: Works only for two reconstructible tracks.

    angle = None
    alpha1 = None
    alpha2 = None

    for i in unique_reco_track_id:

        frac, tmax = fracMCsame(true_track_id[(reco_track_id == i)])

        if tmax not in reco_mc_tracks:
            continue
        
        p = numpy.mean(true_p[true_track_id == tmax])

        x = reco_z[(reco_track_id == i) * is_before * is_y]
        y = reco_y[(reco_track_id == i) * is_before * is_y]
        if len(x) < 2 or len(y) < 2: continue
        ky12, by12 = numpy.polyfit(x, y, 1)

        if tmax == reco_mc_tracks[0] and alpha1 == None:
            alpha1 = numpy.rad2deg(numpy.arctan(ky12))

        if tmax == reco_mc_tracks[1] and alpha2 == None:
            alpha2 = numpy.rad2deg(numpy.arctan(ky12))


    if alpha1 != None and alpha2 != None:
        angle = numpy.abs(alpha2 - alpha1)

    
    ############################################ The angle dependencies ################################################

    for i in unique_reco_track_id:

        frac, tmax = fracMCsame(true_track_id[(reco_track_id == i)])

        if tmax not in reco_mc_tracks:
            continue

        p = numpy.mean(true_p[true_track_id == tmax])

        n_hits_total = len(true_track_id[(reco_track_id == i)])
        frac_total, tmax_total = fracMCsame(true_track_id[(reco_track_id == i)])

        if angle != None:
            h['frac_total_angle'].Fill(angle, frac_total)

    ################################################# Track fit ########################################################

    for i, thetrack in enumerate(theTracks):

        try:
            frac, tmax = fracMCsame(true_track_id[(reco_track_id == i)])
            charge = charges[true_track_id == tmax][0] 
            p = numpy.mean(true_p[true_track_id == tmax])

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

            if math.fabs(p) > 0.0 :
                h['pvspfitted'].Fill(p*charge,fittedMom)
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

        except:
            print "Something wrong!"

    ############################################ left-right ambiguity ##################################################

    for i in unique_reco_track_id:

        frac, tmax = fracMCsame(true_track_id[(reco_track_id == i)])

        if tmax not in reco_mc_tracks:
            continue
        
        
        sel = (reco_track_id == i) * is_before * is_y
        if sel.sum() != 0:
            ratio_y12 = 1. * (numpy.abs(true_y[sel] - reco_y[sel]) < true_dist2wire[sel]).sum() / sel.sum()
            h['left_right_ambiguity_y12'].Fill(ratio_y12)
        
        sel = (reco_track_id == i) * is_before * is_stereo
        if sel.sum() != 0:
            ratio_stereo12 = 1. * (numpy.abs(true_y[sel] - reco_y[sel]) < true_dist2wire[sel]).sum() / sel.sum()
            h['left_right_ambiguity_stereo12'].Fill(ratio_stereo12)
        
        sel = (reco_track_id == i) * is_after * is_y
        if sel.sum() != 0:
            ratio_y34 = 1. * (numpy.abs(true_y[sel] - reco_y[sel]) < true_dist2wire[sel]).sum() / sel.sum()
            h['left_right_ambiguity_y34'].Fill(ratio_y34)
        
        sel = (reco_track_id == i) * is_after * is_stereo
        if sel.sum() != 0:
            ratio_stereo34 = 1. * (numpy.abs(true_y[sel] - reco_y[sel]) < true_dist2wire[sel]).sum() / sel.sum()
            h['left_right_ambiguity_stereo34'].Fill(ratio_stereo34)
          
        sel = (reco_track_id == i)
        if sel.sum() != 0:
            ratio_total = 1. * (numpy.abs(true_y[sel] - reco_y[sel]) < true_dist2wire[sel]).sum() / sel.sum()
            h['left_right_ambiguity'].Fill(ratio_total)


     
    ################################################ Hit Duplicates ####################################################

    for t in reco_mc_tracks:

        if t not in true_track_id:
            continue

        detid = true_det_id

        atrack_mask_tot = (true_track_id == t)
        atrack_detid = detid[atrack_mask_tot]
        other_detid = detid[~atrack_mask_tot]
        n_dup_tot = len(set(atrack_detid) & set(other_detid))
        frac_dup_tot = 1. * n_dup_tot / len(atrack_detid)
        h['duplicates_tot'].Fill(frac_dup_tot)

        atrack_mask_y12 = (true_track_id == t) * is_before * is_y
        atrack_detid = detid[atrack_mask_y12]
        other_detid = detid[~atrack_mask_y12]
        n_dup_y12 = len(set(atrack_detid) & set(other_detid))
        frac_dup_y12 = 1. * n_dup_y12 / len(atrack_detid)
        h['duplicates_y12'].Fill(frac_dup_y12)



    return

########################################################### Main ###############################################################
################################################################################################################################


#if __name__ == "__main__":

input_file = None
geo_file = None
output_file = 'hists.root'
dy = None
reconstructiblerequired = 2
threeprong = 0
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
      -y  --dy                      : dy
      -n  --n_reco                  : Number of reconstructible tracks per event is required
      -t  --three                   : Is threeprong mumunu decay?
      -m  --method                  : Name of a track pattern recognition method: 'Baseline', 'FH', 'AR', 'R'
                                    : Default is 'Baseline'
      -h  --help                    : Shows this help
      '''

try:
    opts, args = getopt.getopt(argv, "hm:f:g:y:n:t:o:",
                                   ["help", "method=", "input=", "geo=", "dy=", "n_reco=", "three=", "output="])
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
    elif opt in ("-y", "--dy"):
        dy = float(arg)
    elif opt in ("-n", "--n_reco"):
        reconstructiblerequired = int(arg)
    elif opt in ("-t", "--three"):
        threeprong = int(arg)
    elif opt in ("-o", "--output"):
        output_file = arg


run_track_pattern_recognition(input_file, geo_file, output_file, dy, reconstructiblerequired, threeprong, method)