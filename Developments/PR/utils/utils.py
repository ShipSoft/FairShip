__author__ = 'Mikhail Hushchyn'

import ROOT
import numpy


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

########################################################################################################################
