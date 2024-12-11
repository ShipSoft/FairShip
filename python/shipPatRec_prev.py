#!/usr/bin/env python
#module with functions for digitization & pattern recognition
#configuration, histograms etc done in shipPatRec_config
#for documentation, see CERN-SHiP-NOTE-2015-002, https://cds.cern.ch/record/2005715/files/main.pdf
#17-04-2015 comments to EvH
from builtins import range
import ROOT, os
import global_variables
from global_variables import ShipGeo
import shipunit  as u
import math
import copy
from collections import OrderedDict
from ROOT import TVector3
from ROOT import gStyle
from ROOT import TGraph
from ROOT import TMultiGraph
from array import array
import operator, sys

import rootUtils as ut

reconstructiblehorizontalidsfound12=0
reconstructiblestereoidsfound12=0
reconstructiblehorizontalidsfound34=0
reconstructiblestereoidsfound34=0
reconstructibleidsfound12=0
reconstructibleidsfound34=0
morethan500=0
morethan100tracks=0
falsenegative=0
falsepositive=0
reconstructibleevents=0

cheated = 0
monitor = 0
printhelp = 0
reconstructiblerequired = 2
threeprong = 0
geoFile=''
fgeo = ''

totalaftermatching=0
totalafterpatrec=0
ReconstructibleMCTracks=[]
MatchedReconstructibleMCTracks=[]
fittedtrackids=[]
theTracks=[]

random = ROOT.TRandom()
ROOT.gRandom.SetSeed(13)

PDG=ROOT.TDatabasePDG.Instance()
fitter = ROOT.genfit.DAF()

h={} #dictionary of histograms
ut.bookHist(h,'pinvvstruepinv','1/p vs 1/p-true',100,-2.,2.,100,-2.,2.)
ut.bookHist(h,'pvspfitted','p-patrec vs p-fitted',401,-200.5,200.5,401,-200.5,200.5)
ut.bookHist(h,'ptrue-p/ptrue','(p - p-true)/p',100,0.,1.)
ut.bookHist(h,'hits1','hits per track/station1',20,-0.5,19.5)
ut.bookHist(h,'hits12x','stereo hits per track/station 1&2 ',30,0,30)
ut.bookHist(h,'hits12y','Y view hits per track/station 1&2 ',30,0,30)
ut.bookHist(h,'hits1xy','(x,y) hits for station 1 (true)',600,-300,300,1200,-600,600)
ut.bookHist(h,'hits2','hits per track/station2',20,-0.5,19.5)
ut.bookHist(h,'hits3','hits per track/station3',20,-0.5,19.5)
ut.bookHist(h,'hits4','hits per track/station4',20,-0.5,19.5)
ut.bookHist(h,'hits1-4','hits per track/4-stations',80,-0.5,79.5)
ut.bookHist(h,'fracsame12','Fraction of hits the same as MC hits (station 1&2 y & stereo tracks)',10,0.05,1.05)
ut.bookHist(h,'fracsame34','Fraction of hits the same as MC hits (station 3&4 y & stereo tracks)',10,0.05,1.05)
ut.bookHist(h,'fracsame12-y','Fraction of hits the same as MC hits (station 1&2 y-tracks)',10,0.05,1.05)
ut.bookHist(h,'fracsame12-stereo','Fraction of hits the same as MC hits (station 1&2 stereo-tracks)',10,0.05,1.05)
ut.bookHist(h,'fracsame34-y','Fraction of hits the same as MC hits (station 3&4 y-tracks)',10,0.05,1.05)
ut.bookHist(h,'fracsame34-stereo','Fraction of hits the same as MC hits (station 3&4 stereo-tracks)',10,0.05,1.05)
ut.bookHist(h,'digi-truevstruey','y from digitisation - y true (Y view)',100,-0.5,0.5)
ut.bookHist(h,'digi-truevstruex','projected x from digitisation - x true (stereo view)',500,-250,250)
ut.bookHist(h,'dx-matchedtracks','x distance (cm) between matched tracks',200,-100,100)
ut.bookHist(h,'dy-matchedtracks','y distance (cm) between matched tracks',200,-10,10)
ut.bookHist(h,'disthittoYviewtrack','distance (cm) from hit to fitted Y-view track',300,-3,3)
ut.bookHist(h,'disthittostereotrack','distance (cm) from hit to fitted stereo-view track',100,-20,20)
ut.bookHist(h,'disthittoYviewMCtrack','distance (cm) from hit to Y-view MC track',300,-3,3)
ut.bookHist(h,'disthittostereoMCtrack','distance (cm) from hit to stereo-view MC track',100,-20,20)
ut.bookHist(h,'matchedtrackefficiency','station 1,2 vs station 3,4 efficiency for matched tracks',10,0.05,1.05,10,0.05,1.05)
ut.bookHist(h,'unmatchedparticles','Reconstructible but unmatched particles',7,-0.5,6.5)
ut.bookHist(h,'reconstructiblemomentum','Momentum of reconstructible particles',100,0,200)
ut.bookHist(h,'reconstructibleunmmatchedmomentum','Momentum of reconstructible (unmatched) particles',100,0,200)
ut.bookHist(h,'HNLmomentumvsweight','HNL momentum vs weight',100,0.,0.0002,100,0.,200.)
ut.bookHist(h,'eventspassed','Events passing the pattern recognition',9,-0.5,8.5)
ut.bookHist(h,'nbrhits','Number of hits per reconstructible event',400,0.,400.)
ut.bookHist(h,'nbrtracks','Number of tracks per reconstructible event',400,0.,400.)
ut.bookHist(h,'chi2fittedtracks','Chi^2 per NDOF for fitted tracks',210,-0.05,20.05)
ut.bookHist(h,'pvalfittedtracks','pval for fitted tracks',110,-0.05,1.05)
ut.bookHist(h,'momentumfittedtracks','momentum for fitted tracks',251,-0.05,250.05)
ut.bookHist(h,'xdirectionfittedtracks','x-direction for fitted tracks',91,-0.5,90.5)
ut.bookHist(h,'ydirectionfittedtracks','y-direction for fitted tracks',91,-0.5,90.5)
ut.bookHist(h,'zdirectionfittedtracks','z-direction for fitted tracks',91,-0.5,90.5)
ut.bookHist(h,'massfittedtracks','mass fitted tracks',210,-0.005,0.205)

rc=h['pinvvstruepinv'].SetMarkerStyle(8)
rc=h['matchedtrackefficiency'].SetMarkerStyle(8)

particles=["e-","e+","mu-","mu+","pi-","pi+","other"]
for i in range (1,8) :
   rc=h['unmatchedparticles'].GetXaxis().SetBinLabel(i,particles[i-1])
h['eventspassed'].GetXaxis().SetBinLabel(1,"Reconstructible tracks")
h['eventspassed'].GetXaxis().SetBinLabel(2,"Y view station 1&2")
h['eventspassed'].GetXaxis().SetBinLabel(3,"Stereo station 1&2")
h['eventspassed'].GetXaxis().SetBinLabel(4,"station 1&2")
h['eventspassed'].GetXaxis().SetBinLabel(5,"Y view station 3&4")
h['eventspassed'].GetXaxis().SetBinLabel(6,"Stereo station 3&4")
h['eventspassed'].GetXaxis().SetBinLabel(7,"station 3&4")
h['eventspassed'].GetXaxis().SetBinLabel(8,"Combined stations 1&2/3&4")
h['eventspassed'].GetXaxis().SetBinLabel(9,"Matched")

i1=1 #1st layer
i2=16 #last layer
zlayer={} #dictionary with z coordinates of station1,2 layers
zlayerv2={} #z-positions for stereo views
z34layer={} #dictionary with z coordinates of station3,4 layers
z34layerv2={} #z-positions for stereo views
TStation1StartZ=0.
TStation4EndZ=0.
VetoStationZ=0.
VetoStationEndZ=0.


def initialize(fGeo):
   #creates a dictionary with z coordinates of layers
   #and variables with station start/end coordinates
   #to be called once at the beginning of the eventloop
   global i1,i2,zlayer,zlayerv2,z34layer,z34layerv2,TStation1StartZ,TStation4EndZ,VetoStationZ,VetoStationEndZ
   global fgeo
   fgeo=fGeo
   #z-positions of Y-view tracking
   #4 stations, 4 views (Y,u,v,Y); each view has 2 planes and each plane has 2 layers

   for i in range(i1,i2+1):
     TStationz = ShipGeo.TrackStation1.z
     if (i>8) :
        TStationz = ShipGeo.TrackStation2.z
     # Y: vnb=0 or 3
     vnb=0.
     if (i>4): vnb=3.
     if (i>8): vnb=0.
     if (i>12): vnb=3.
     lnb = 0.
     if (i % 2 == 0) : lnb=1.
     pnb=0.
     if (i==3 or i==4 or i==7 or i==8 or i==11 or i==12 or i==15 or i==16) : pnb=1.

     #z positions of Y view of stations
     Zpos = TStationz+(vnb-3./2.)*ShipGeo.strawtubes.DeltazView+(float(pnb)-1./2.)*ShipGeo.strawtubes.DeltazPlane+(float(lnb)-1./2.)*ShipGeo.strawtubes.DeltazLayer
     zlayer[i]=[Zpos]

   #z-positions for stereo views

   for i in range(i1,i2+1):
     TStationz = ShipGeo.TrackStation1.z
     if (i>8) :
        TStationz = ShipGeo.TrackStation2.z
     #stereo views: vnb=1 or 2
     vnb=1.
     if (i>4): vnb=2.
     if (i>8): vnb=1.
     if (i>12): vnb=2.
     lnb = 0.
     if (i % 2 == 0) : lnb=1.
     pnb=0.
     if (i==3 or i==4 or i==7 or i==8 or i==11 or i==12 or i==15 or i==16) : pnb=1.

     #z positions of u,v view of stations
     Zpos_u = TStationz+(vnb-3./2.)*ShipGeo.strawtubes.DeltazView+(float(pnb)-1./2.)*ShipGeo.strawtubes.DeltazPlane+(float(lnb)-1./2.)*ShipGeo.strawtubes.DeltazLayer
     zlayerv2[i]=[Zpos_u]


   for i in range(i1,i2+1):
     TStationz = ShipGeo.TrackStation3.z
     if (i>8) :
        TStationz = ShipGeo.TrackStation4.z
     # Y: vnb=0 or 3
     vnb=0.
     if (i>4): vnb=3.
     if (i>8): vnb=0.
     if (i>12): vnb=3.
     lnb = 0.
     if (i % 2 == 0) : lnb=1.
     pnb=0.
     if (i==3 or i==4 or i==7 or i==8 or i==11 or i==12 or i==15 or i==16) : pnb=1.

     #z positions of x1 view of stations
     Zpos = TStationz+(vnb-3./2.)*ShipGeo.strawtubes.DeltazView+(float(pnb)-1./2.)*ShipGeo.strawtubes.DeltazPlane+(float(lnb)-1./2.)*ShipGeo.strawtubes.DeltazLayer
     z34layer[i]=[Zpos]


   for i in range(i1,i2+1):
     #zlayerv2[i]=[i*100.+50.]
     TStationz = ShipGeo.TrackStation3.z
     if (i>8) :
        TStationz = ShipGeo.TrackStation4.z
     #stereo views: vnb=1 or 2
     vnb=1.
     if (i>4): vnb=2.
     if (i>8): vnb=1.
     if (i>12): vnb=2.
     lnb = 0.
     if (i % 2 == 0) : lnb=1.
     pnb=0.
     if (i==3 or i==4 or i==7 or i==8 or i==11 or i==12 or i==15 or i==16) : pnb=1.

     #z positions of u,v view of stations
     Zpos_u = TStationz+(vnb-3./2.)*ShipGeo.strawtubes.DeltazView+(float(pnb)-1./2.)*ShipGeo.strawtubes.DeltazPlane+(float(lnb)-1./2.)*ShipGeo.strawtubes.DeltazLayer
     z34layerv2[i]=[Zpos_u]

   VetoStationZ = ShipGeo.vetoStation.z
   if global_variables.debug:
     print("VetoStation midpoint z=", VetoStationZ)
   VetoStationEndZ=VetoStationZ+(ShipGeo.strawtubes.DeltazView+ShipGeo.strawtubes.OuterStrawDiameter)/2
   for i in range(1,5):
     if i==1: TStationz = ShipGeo.TrackStation1.z
     if i==2: TStationz = ShipGeo.TrackStation2.z
     if i==3: TStationz = ShipGeo.TrackStation3.z
     if i==4: TStationz = ShipGeo.TrackStation4.z
     if global_variables.debug:
       print("TrackStation",i," midpoint z=",TStationz)
       for vnb in range(0,4):
         for pnb in range (0,2):
           for lnb in range (0,2):
              Zpos = TStationz+(vnb-3./2.)*ShipGeo.strawtubes.DeltazView+(float(pnb)-1./2.)*ShipGeo.strawtubes.DeltazPlane+(float(lnb)-1./2.)*ShipGeo.strawtubes.DeltazLayer
              print("TStation=",i,"view=",vnb,"plane=",pnb,"layer=",lnb,"z=",Zpos)

   TStation1StartZ=zlayer[1][0]-ShipGeo.strawtubes.OuterStrawDiameter/2
   TStation4EndZ=z34layer[16][0]+ShipGeo.strawtubes.OuterStrawDiameter/2

   return

def getReconstructibleTracks(iEvent,sTree,sGeo):

  #returns a list of reconstructible tracks for this event
  #call this routine once for each event before smearing
  MCTrackIDs=[]
  rc = sTree.GetEvent(iEvent)
  nMCTracks = sTree.MCTrack.GetEntriesFast()

  if global_variables.debug:
    print("event nbr", iEvent, "has", nMCTracks, "tracks")
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
  if global_variables.debug:
    print("Tracks with origin in decay volume", MCTrackIDs)
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

  if global_variables.debug:
    print("Tracks with hits in timedet", MCTrackIDs)
  if len(MCTrackIDs)==0: return MCTrackIDs
  #4. Find straws that have multiple hits
  nHits = sTree.strawtubesPoint.GetEntriesFast()
  hitstraws={}
  duplicatestrawhit=[]
  if global_variables.debug:
    print("Nbr of Rawhits=", nHits)

  for i in range(nHits):
    ahit = sTree.strawtubesPoint[i]
    if (str(ahit.GetDetectorID())[:1]=="5") :
       if global_variables.debug:
	 print("Hit in straw Veto detector. Rejecting.")
       continue
    strawname=str(ahit.GetDetectorID())

    if strawname in hitstraws:
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
       if global_variables.debug:
	 print("Duplicate hit", i, "not reconstructible, rejecting.")
       continue
    ahit = sTree.strawtubesPoint[i]
    #is hit inside acceptance? if not mark the track as bad
    if (((ahit.GetX()/245.)**2 + (ahit.GetY()/495.)**2) >= 1.):
       if ahit.GetTrackID() not in trackoutsidestations:
          trackoutsidestations.append(ahit.GetTrackID())
    if ahit.GetTrackID() not in MCTrackIDs:
       #hit on not reconstructible track
       if global_variables.debug:
	 print("Hit not on reconstructible track. Rejecting.")
       continue
    #group hits per tracking station, key = trackid
    if str(ahit.GetDetectorID())[:1]=="1" :
       if ahit.GetTrackID() in hits1:
            hits1[ahit.GetTrackID()]=[hits1[ahit.GetTrackID()][0],i]
       else:
            hits1[ahit.GetTrackID()]=[i]
    if str(ahit.GetDetectorID())[:1]=="2" :
       if ahit.GetTrackID() in hits2:
            hits2[ahit.GetTrackID()]=[hits2[ahit.GetTrackID()][0],i]
       else:
            hits2[ahit.GetTrackID()]=[i]
    if str(ahit.GetDetectorID())[:1]=="3" :
       if ahit.GetTrackID() in hits3:
            hits3[ahit.GetTrackID()]=[hits3[ahit.GetTrackID()][0],i]
       else:
            hits3[ahit.GetTrackID()]=[i]
    if str(ahit.GetDetectorID())[:1]=="4" :
       if ahit.GetTrackID() in hits4:
            hits4[ahit.GetTrackID()]=[hits4[ahit.GetTrackID()][0],i]
       else:
            hits4[ahit.GetTrackID()]=[i]

  #6. Make list of tracks with hits in in station 1,2,3 & 4
  tracks_with_hits_in_all_stations=[]
  for key in hits1.keys():
      if (key in hits2 and key in hits3 ) and key in hits4:
         if key not in tracks_with_hits_in_all_stations and key not in trackoutsidestations:
            tracks_with_hits_in_all_stations.append(key)
  for key in hits2.keys():
      if (key in hits1 and key in hits3 ) and key in hits4:
         if key not in tracks_with_hits_in_all_stations and key not in trackoutsidestations:
            tracks_with_hits_in_all_stations.append(key)
  for key in hits3.keys():
      if ( key in hits2 and key in hits1 ) and key in hits4:
         if key not in tracks_with_hits_in_all_stations and key not in trackoutsidestations:
            tracks_with_hits_in_all_stations.append(key)
  for key in hits4.keys():
      if (key in hits2 and key in hits3) and key in hits1:
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

  if global_variables.debug:
     print("tracks_with_hits_in_all_stations",tracks_with_hits_in_all_stations)
     print("Tracks with hits in all stations & inside acceptance ellipse",MCTrackIDs)
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
	    rc=h['reconstructiblemomentum'].Fill(trackmomentum,trackweight)
	    motherId=atrack.GetMotherId()
	    if motherId==1 :
		HNLmomentum=sTree.MCTrack.At(1).GetP()
		rc=h['HNLmomentumvsweight'].Fill(trackweight,HNLmomentum)
	        if j==nMCTracks :
 		     trackmomentum=atrack.GetP()
		     trackweight=atrack.GetWeight()
		     rc=h['reconstructiblemomentum'].Fill(trackmomentum,trackweight)
		     if atrack.GetMotherId()==1 :
		       HNLmomentum=sTree.MCTrack.At(1).GetP()
		       rc=h['HNLmomentumvsweight'].Fill(trackweight,HNLmomentum)
  itemstoremove=[]
  for item in MCTrackIDs:
    atrack = sTree.MCTrack.At(item)
    motherId=atrack.GetMotherId()
    if motherId != 1:
        itemstoremove.append(item)
  for item in itemstoremove:
      MCTrackIDs.remove(item)
      if global_variables.debug:
	print("After removing the non HNL track, MCTrackIDs", MCTrackIDs)
  if global_variables.debug:
    print("Tracks with HNL mother", MCTrackIDs)

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
        if global_variables.debug:
	  print("Unknown particle with pdg code:", sTree.MCTrack.At(item).GetPdgCode())
    if reconstructiblerequired == 1 :
      if mufound!=1  and pifound!=1:
          if global_variables.debug:
	    print("No reconstructible pion or muon.")
	  MCTrackIDs=[]
    if reconstructiblerequired == 2 :
      if threeprong == 1 :
          if mufound!=2 or nu_mufound!=1 :
            if global_variables.debug:
	      print("No reconstructible mu-mu-nu.")
	    MCTrackIDs=[]
	  else:
	    #remove the neutrino from MCTrackIDs for the rest
	    for item in itemstoremove:
               MCTrackIDs.remove(item)
      else:
          if mufound!=1 or pifound!=1 :
            if global_variables.debug:
	      print("No reconstructible pion and muon.")
	    MCTrackIDs=[]
  if len(MCTrackIDs)>0:
     rc=h['nbrhits'].Fill(nHits)
     rc=h['nbrtracks'].Fill(nMCTracks)
  if global_variables.debug:
    print("Tracks with required HNL decay particles", MCTrackIDs)
  return MCTrackIDs

def SmearHits(iEvent,sTree,modules,SmearedHits,ReconstructibleMCTracks):
  #smears hits (when not cheated)
  #apply cuts for >500 hits, duplicate straw hits and acceptance
  #call this routine once for each event, before the digitization

  top=ROOT.TVector3()
  bot=ROOT.TVector3()
  random = ROOT.TRandom()
  ROOT.gRandom.SetSeed(13)

  rc = sTree.GetEvent(iEvent)
  nHits = sTree.strawtubesPoint.GetEntriesFast()
  withNoStrawSmearing=None
  hitstraws={}
  duplicatestrawhit=[]

  for i in range(nHits):
    ahit = sTree.strawtubesPoint[i]
    if (str(ahit.GetDetectorID())[:1]=="5") : continue
    strawname=str(ahit.GetDetectorID())
    if strawname in hitstraws:
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

  #the following code prints some histograms related to the MC hits
  strawname=''
  if global_variables.debug:
    print("nbr of hits=", nHits, "in event", iEvent)
  station1hits={}
  station12xhits={}
  station12yhits={}
  station2hits={}
  station3hits={}
  station4hits={}

  for i in range(nHits):
    ahit = sTree.strawtubesPoint[i]
    strawname=str(ahit.GetDetectorID())
    #is it a duplicate hit? if so, ignore it
    if i in duplicatestrawhit:
      continue
    #only look at hits in the strawtracking stations
    if (str(ahit.GetDetectorID())[:1]=="5") : continue
    #is hit inside acceptance?
    if (((ahit.GetX()/245.)**2 + (ahit.GetY()/495.)**2) >= 1.): continue

    modules["Strawtubes"].StrawEndPoints(ahit.GetDetectorID(),bot,top)
    if cheated==False :
       #this is where the smearing takes place. the hit coordinates can also be read from somewhere else.
       sm   = hit2wire(ahit,bot,top,withNoStrawSmearing)
       m = array('d',[i,sm['xtop'],sm['ytop'],sm['z'],sm['xbot'],sm['ybot'],sm['z'],sm['dist'],ahit.GetDetectorID()])
    else :
       #for MC truth
       m = array('d',[i,ahit.GetX(),ahit.GetY(),top[2],ahit.GetX(),ahit.GetY(),top[2],ahit.dist2Wire(),ahit.GetDetectorID()])

    measurement = ROOT.TVectorD(9,m)

    smHits = SmearedHits.GetEntries()
    if SmearedHits.GetSize() == smHits: SmearedHits.Expand(smHits+1000)
    SmearedHits[smHits] = measurement


    angle=0.
    if (str(ahit.GetDetectorID())[1:2]=="1"): angle=ShipGeo.strawtubes.ViewAngle
    if (str(ahit.GetDetectorID())[1:2]=="2"): angle=ShipGeo.strawtubes.ViewAngle*-1.
    if (str(ahit.GetDetectorID())[:1]=="1") :
       if ahit.GetTrackID() in station1hits:
          station1hits[ahit.GetTrackID()]+=1
	  rc=h['hits1xy'].Fill(ahit.GetX(),ahit.GetY())
       else:
          station1hits[ahit.GetTrackID()]=1
    if (str(ahit.GetDetectorID())[:1]=="2") :
       if ahit.GetTrackID() in station2hits:
          station2hits[ahit.GetTrackID()]+=1
       else:
          station2hits[ahit.GetTrackID()]=1
    if (str(ahit.GetDetectorID())[:1]=="3") :
       if ahit.GetTrackID() in station3hits:
          station3hits[ahit.GetTrackID()]+=1
       else:
          station3hits[ahit.GetTrackID()]=1
    if (str(ahit.GetDetectorID())[:1]=="4") :
       if ahit.GetTrackID() in station4hits:
          station4hits[ahit.GetTrackID()]+=1
       else:
          station4hits[ahit.GetTrackID()]=1

    if ((str(ahit.GetDetectorID())[:2]=="11" or str(ahit.GetDetectorID())[:2]=="12") or (str(ahit.GetDetectorID())[:2]=="21" or str(ahit.GetDetectorID())[:2]=="22")):
       if ahit.GetTrackID() in station12xhits:
	  station12xhits[ahit.GetTrackID()]+=1
       else:
          station12xhits[ahit.GetTrackID()]=1

    if ((str(ahit.GetDetectorID())[:2]=="10" or str(ahit.GetDetectorID())[:2]=="13") or (str(ahit.GetDetectorID())[:2]=="20" or str(ahit.GetDetectorID())[:2]=="23")):
       if ahit.GetTrackID() in station12yhits:
	  station12yhits[ahit.GetTrackID()]+=1
       else:
          station12yhits[ahit.GetTrackID()]=1

  total1hits=0
  total12xhits=0
  total12yhits=0
  hits1pertrack=0
  hits12xpertrack=0
  hits12ypertrack=0
  total2hits=0
  hits2pertrack=0
  total3hits=0
  hits3pertrack=0
  total4hits=0
  hits4pertrack=0
  for items in station1hits:
     # only count the hits on reconstructible tracks
     if monitor==True:
       if items in ReconstructibleMCTracks: total1hits=total1hits+station1hits[items]
     else : total1hits=total1hits+station1hits[items]
  if len(station1hits) > 0 :
     hits1pertrack=total1hits/len(station1hits)
  for items in station12xhits:
     if monitor==True:
        if items in ReconstructibleMCTracks: total12xhits=total12xhits+station12xhits[items]
     else: total12xhits=total12xhits+station12xhits[items]
  if len(station12xhits) > 0 : hits12xpertrack=total12xhits/len(station12xhits)
  for items in station12yhits:
     if monitor==True:
        if items in ReconstructibleMCTracks: total12yhits=total12yhits+station12yhits[items]
     else: total12yhits=total12yhits+station12yhits[items]
  if len(station12yhits) > 0 : hits12ypertrack=total12yhits/len(station12yhits)
  for items in station2hits:
     if monitor==True:
        if items in ReconstructibleMCTracks: total2hits=total2hits+station2hits[items]
     else: total2hits=total2hits+station2hits[items]
  if len(station2hits) > 0 :
     hits2pertrack=total2hits/len(station2hits)
  for items in station3hits:
     if monitor==True:
        if items in ReconstructibleMCTracks: total3hits=total3hits+station3hits[items]
     else: total3hits=total3hits+station3hits[items]
  if len(station3hits) > 0 :
     hits3pertrack=total3hits/len(station3hits)
  for items in station4hits:
     if monitor==True:
        if items in ReconstructibleMCTracks: total4hits=total4hits+station4hits[items]
     else:  total4hits=total4hits+station4hits[items]
  if len(station4hits) > 0 :
     hits4pertrack=total4hits/len(station4hits)

  rc=h['hits1-4'].Fill(hits1pertrack+hits2pertrack+hits3pertrack+hits4pertrack)
  rc=h['hits1'].Fill(hits1pertrack)
  rc=h['hits12x'].Fill(hits12xpertrack)
  rc=h['hits12y'].Fill(hits12ypertrack)
  rc=h['hits2'].Fill(hits2pertrack)
  rc=h['hits3'].Fill(hits3pertrack)
  rc=h['hits4'].Fill(hits4pertrack)
  return SmearedHits


def Digitization(sTree,SmearedHits):
  #digitization
  #input: Smeared TrackingHits
  #output: StrawRaw, StrawRawLink

  StrawRaw={} #raw hit dictionary: key=hit number, values=xtop,ytop,ztop,xbot,ybot,zbot,dist2Wire,strawname
  StrawRawLink={} #raw hit dictionary: key=hit number, value=the hit object
  j=0
  for i in range(len(SmearedHits)):
    xtop=SmearedHits[i]['xtop']
    xbot=SmearedHits[i]['xbot']
    ytop=SmearedHits[i]['ytop']
    ybot=SmearedHits[i]['ybot']
    ztop=SmearedHits[i]['z']
    zbot=SmearedHits[i]['z']
    distance=SmearedHits[i]['dist']
    strawname=sTree.strawtubesPoint[i].GetDetectorID()
    a=[]
    a.append(xtop)
    a.append(ytop)
    a.append(ztop)
    a.append(xbot)
    a.append(ybot)
    a.append(zbot)
    a.append(float(distance))
    a.append(str(strawname))
    StrawRaw[j]=a
    StrawRawLink[j]=[sTree.strawtubesPoint[i]]
    j=j+1

  if global_variables.debug:
    print("Nbr of digitized hits", j)
  return StrawRaw,StrawRawLink

def PatRec(firsttwo,zlayer,zlayerv2,StrawRaw,StrawRawLink,ReconstructibleMCTracks):
  global reconstructiblehorizontalidsfound12,reconstructiblestereoidsfound12,reconstructiblehorizontalidsfound34,reconstructiblestereoidsfound34
  global reconstructibleidsfound12,reconstructibleidsfound34,rawhits,totalaftermatching

  hits={}
  rawhits={}
  stereohits={}
  hitids={}
  ytan={}
  ycst={}
  horpx={}
  horpy={}
  horpz={}
  stereomom={}
  stereotan={}
  stereocst={}
  fraction={}
  trackid={}
  duplicates=[]
  j=0
  resolution=ShipGeo.strawtubes.sigma_spatial

  for item in StrawRaw:
     #y hits for horizontal straws
     rawhits[j]=copy.deepcopy(((StrawRaw[item][1]+StrawRaw[item][4])/2,(StrawRaw[item][2]+StrawRaw[item][5])/2,StrawRaw[item][6]))
     if firsttwo==True:
       if global_variables.debug:
	 print(
	     "rawhits[", j, "]=", rawhits[j],
	     "trackid", StrawRawLink[item][0].GetTrackID(),
	     "strawname", StrawRawLink[item][0].GetDetectorID(),
	     "true x", StrawRawLink[item][0].GetX(),
	     "true y", StrawRawLink[item][0].GetY(),
	     "true z", StrawRawLink[item][0].GetZ()
	     )
     j=j+1

  sortedrawhits=OrderedDict(sorted(rawhits.items(),key=lambda t:t[1][1]))
  if global_variables.debug:
     print(" ")
     print("horizontal view (y) hits ordered by plane: plane nr, zlayer, hits")

  y2=[]
  y3=[]
  yother=[]
  ymin2=[]
  z2=[]
  z3=[]
  zother=[]
  zmin2=[]
  for i in range(i1,i2+1):
    a=[] #the hits
    c=[] #the keys pointing to the raw hits
    d=[] #the distance to the wire
    for item in sortedrawhits:
      if (float(sortedrawhits[item][1])==float(zlayer[i][0])) :
        #difference with previous version: make each hit a dictionary so we can later get back the mc trackid
	if sortedrawhits[item][0] not in a:
	   a.append(float(sortedrawhits[item][0]))
	else:
	   #This should never happen - duplicate hits are already removed at digitization
	   if global_variables.debug:
	     print(" wire hit again", sortedrawhits[item], "strawname=", StrawRawLink[item][0].GetDetectorID())
	   a.append(float(sortedrawhits[item][0]))
	   duplicates.append(float(zlayer[i][0]))
    a.sort()
    #find the key of the sorted hit
    for value in a:
       for item in sortedrawhits:
          if ((float(sortedrawhits[item][0])==value) & (float(sortedrawhits[item][1])==float(zlayer[i][0]))) :
            if item not in c :
	      c.append(item)
	      d.append(float(sortedrawhits[item][2]))
	    else :
	       continue
	    break
    #indicate which hit has been used
    b=len(a)*[0]
    hits[i]=[a,b,c,d]
    if global_variables.debug:
      print(i, zlayer[i], hits[i])

    # split hits up by trackid for debugging

    for item in range(len(hits[i][0])):
	if StrawRawLink[hits[i][2][item]][0].GetTrackID() == 3:
	    y3.append(float(hits[i][0][item]))
	    z3.append(float(zlayer[i][0]))
	else:
	    if StrawRawLink[hits[i][2][item]][0].GetTrackID() == 2:
	       y2.append(float(hits[i][0][item]))
	       z2.append(float(zlayer[i][0]))
	    else:
	       if StrawRawLink[hits[i][2][item]][0].GetTrackID() == -2:
	          ymin2.append(float(hits[i][0][item]))
		  zmin2.append(float(zlayer[i][0]))
	       else:
	          yother.append(float(hits[i][0][item]))
		  zother.append(float(zlayer[i][0]))

  if cheated==True :
      if threeprong==1 : nrtrcandv1,trcandv1=ptrack(zlayer,hits,6,0.6)
      else : nrtrcandv1,trcandv1=ptrack(zlayer,hits,7,0.5)
  else :
      if threeprong==1 : nrtrcandv1,trcandv1=ptrack(zlayer,hits,6,0.6)
      else: nrtrcandv1,trcandv1=ptrack(zlayer,hits,7,0.7)

  foundhorizontaltrackids=[]
  horizontaltrackids=[]
  removetrackids=[]
  for t in trcandv1:
    trackids=[]
    if global_variables.debug:
       print(' ')
       print('track found in Y view:',t,' indices of hits in planes',trcandv1[t])
    for ipl in range(len(trcandv1[t])):
      indx= trcandv1[t][ipl]
      if indx>-1:
 	if global_variables.debug:
	  print(
	      '   plane nr, z-position, y of hit, trackid:',
	      ipl, zlayer[ipl], hits[ipl][0][indx],
	      StrawRawLink[hits[ipl][2][indx]][0].GetTrackID()
	  )
	trackids.append(StrawRawLink[hits[ipl][2][indx]][0].GetTrackID())
    if global_variables.debug:
      print(
	  "   Largest fraction of hits in Y view:", fracMCsame(trackids)[0],
	  "on MC track with id",fracMCsame(trackids)[1]
	  )
    if firsttwo==True:
       h['fracsame12-y'].Fill(fracMCsame(trackids)[0])
    else:
       h['fracsame34-y'].Fill(fracMCsame(trackids)[0])
    if monitor==1:
       if fracMCsame(trackids)[1] in ReconstructibleMCTracks:
          horizontaltrackids.append(fracMCsame(trackids)[1])
          if fracMCsame(trackids)[1] not in foundhorizontaltrackids:
             foundhorizontaltrackids.append(fracMCsame(trackids)[1])
       else:
          #this track is not reconstructible, remove it
          if global_variables.debug:
	    print("Y view track with trackid", fracMCsame(trackids)[1], "is not reconstructible. Removing it.")
          removetrackids.append(t)

       if (len(foundhorizontaltrackids) == 0 or len(horizontaltrackids)==0 ):
          if global_variables.debug:
	    print("No reconstructible Y view tracks found.")
          if monitor==True : return 0,[],[],[],[],[],[],{},{},{},{},{}

  for i in range(0,len(removetrackids)):
      del trcandv1[removetrackids[i]]
      nrtrcandv1=nrtrcandv1-1

  #reorder trcandv1 after removing tracks
  if len(removetrackids)>0:
     j=0
     for key in trcandv1:
        j=j+1
        if key!=j:
	   trcandv1[j]=trcandv1[key]
	   del trcandv1[key]

  if monitor==1:
     if len(ReconstructibleMCTracks)>0:
        if firsttwo==True:
          if len(foundhorizontaltrackids)>=len(ReconstructibleMCTracks) : reconstructiblehorizontalidsfound12+=1
          else :
             if global_variables.debug:
	       print("!!!!!!!!!!!!!!!! Difference between Y-view tracks found and reconstructible tracks (station 1&2). Quitting patrec.")
               debugevent(iEvent,False,y2,y3,ymin2,yother,z2,z3,zmin2,zother,foundhorizontaltrackids)
	     return 0,[],[],[],[],[],[],{},{},{},{},{}
        else:
          if len(foundhorizontaltrackids)>=len(ReconstructibleMCTracks) : reconstructiblehorizontalidsfound34+=1
          else :
             if global_variables.debug:
	       print("!!!!!!!!!!!!!!!! Difference between Y-view tracks found and reconstructible tracks (station 3&4). Quitting patrec.")
	       debugevent(iEvent,False,y2,y3,ymin2,yother,z2,z3,zmin2,zother,foundhorizontaltrackids)
	     return 0,[],[],[],[],[],[],{},{},{},{},{}

     if len(foundhorizontaltrackids) != reconstructiblerequired :
       if global_variables.debug:
	 print(len(foundhorizontaltrackids), "Y view tracks found, but ", reconstructiblerequired, "required.")
       return 0,[],[],[],[],[],[],{},{},{},{},{}
  else:
     if firsttwo==True: reconstructiblehorizontalidsfound12+=1
     else: reconstructiblehorizontalidsfound34+=1


  if nrtrcandv1==0 :
    if global_variables.debug:
      print("0 tracks found in Y view. Reconstructible:", len(ReconstructibleMCTracks))
    if monitor==True: return 0,[],[],[],[],[],[],{},{},{},{},{}
  else :
    if global_variables.debug:
      print(nrtrcandv1, "tracks found in Y view. Reconstructible:", len(ReconstructibleMCTracks))

  if global_variables.debug:
    print("***************** Start of Stereo PatRec **************************")

  v2hits={}
  v2hitsMC={}

  uvview={}
  j=0
  rawxhits={}
  for item in StrawRaw:
     rawxhits[j]=copy.deepcopy((StrawRaw[item][0],StrawRaw[item][1],StrawRaw[item][3],StrawRaw[item][4],StrawRaw[item][2],StrawRaw[item][6]))
     if firsttwo==True:
       if global_variables.debug:
	 print(
	     "rawxhits[", j, "]=", rawxhits[j],
	     "trackid", StrawRawLink[item][0].GetTrackID(),
	     "true x", StrawRawLink[item][0].GetX(),
	     "true y",StrawRawLink[item][0].GetY()
	     )
     j=j+1

  sortedrawxhits=OrderedDict(sorted(rawxhits.items(),key=lambda t:t[1][4]))

  if global_variables.debug:
    print("stereo view hits ordered by plane:")
  for i in range(i1,i2+1):
    xb=[]
    yb=[]
    xt=[]
    yt=[]
    c=[]
    d=[]
    for item in sortedrawxhits:
      if (float(sortedrawxhits[item][4])==float(zlayerv2[i][0])) :
        xt.append(float(sortedrawxhits[item][0]))
        yt.append(float(sortedrawxhits[item][1]))
        xb.append(float(sortedrawxhits[item][2]))
        yb.append(float(sortedrawxhits[item][3]))
	#c is the rawxhits hit number
	c.append(item)
	#d is the distance to the wire
	d.append(float(sortedrawxhits[item][5]))
    uvview[i]=[xb,yb,xt,yt,c,d]

    if global_variables.debug:
      print(
	  '   uv hits, z,xb,yb,xt,yt,dist    ',
	  i, zlayerv2[i], uvview[i][0], uvview[i][1], uvview[i][2],
	  uvview[i][3], uvview[i][4], uvview[i][5]
	  )

  # now do pattern recognition in view perpendicular to first search view
  # loop over tracks found in Y view, and intersect this "plane"
  # with hits in other views, and project in "x", then ptrack in "x", etc..

  #loop over tracks found in Y view
  ntracks=0
  trackkey=0
  tracks={}
  if global_variables.debug:
    if (firsttwo==True) :
      print('Loop over tracks found in Y view, stations 1&2')
    else :
      print('Loop over tracks found in Y view, stations 3&4')

  foundstereotrackids=[]
  foundtrackids=[]

  for t in trcandv1:
    alltrackids=[]
    y11trackids=[]
    y12trackids=[]
    y21trackids=[]
    y22trackids=[]
    y11hitids=[]
    y12hitids=[]
    y21hitids=[]
    y22hitids=[]
    trackkey+=1

    #linear "fit" to track found in this view

    fitt,fitc=fitline(trcandv1[t],hits,zlayer,resolution)
    if global_variables.debug:
      print('   Track nr', t, 'in Y view: tangent, constant=', fitt, fitc)

    tan=0.
    cst=0.
    px=0.
    py=0.
    pz=0.
    m=0
    if firsttwo==True: looplist=reversed(list(range(len(trcandv1[t]))))
    else: looplist=list(range(len(trcandv1[t])))
    for ipl in looplist:
      indx= trcandv1[t][ipl]
      if indx>-1:
 	if global_variables.debug:
	  print('      Plane nr, z-position, y of hit:', ipl, zlayer[ipl], hits[ipl][0][indx])
        hitpoint=[zlayer[ipl],hits[ipl][0][indx]]
	rc=h['disthittoYviewtrack'].Fill(dist2line(fitt,fitc,hitpoint))
	#if px==0. : px=StrawRawLink[hits[ipl][2][indx]][0].GetPx()
	#if py==0. : py=StrawRawLink[hits[ipl][2][indx]][0].GetPy()
	#if pz==0. : pz=StrawRawLink[hits[ipl][2][indx]][0].GetPz()
	px=StrawRawLink[hits[ipl][2][indx]][0].GetPx()
	py=StrawRawLink[hits[ipl][2][indx]][0].GetPy()
	pz=StrawRawLink[hits[ipl][2][indx]][0].GetPz()
	ptmp=math.sqrt(px**2+py**2+pz**2)
	if global_variables.debug:
	    print("      p",ptmp,"px",px,"py",py,"pz",pz)
	if tan==0. : tan=py/pz
	if cst==0. : cst=StrawRawLink[hits[ipl][2][indx]][0].GetY()-tan*zlayer[ipl][0]
	rc=h['disthittoYviewMCtrack'].Fill(dist2line(tan,cst,hitpoint))

    if global_variables.debug:
      print('   Track nr', t, 'in Y view: MC tangent, MC constant=', tan, cst)

    for ipl in range(len(trcandv1[t])):
      indx= trcandv1[t][ipl]
      if indx>-1:
        diffy=hits[ipl][0][indx]-StrawRawLink[hits[ipl][2][indx]][0].GetY()
	h['digi-truevstruey'].Fill(diffy)
        if ipl<5:
	    y11trackids.append(StrawRawLink[hits[ipl][2][indx]][0].GetTrackID())
	    y11hitids.append([hits[ipl][2][indx]][0])
	if (ipl>4 and ipl<9):
	    y12trackids.append(StrawRawLink[hits[ipl][2][indx]][0].GetTrackID())
	    y12hitids.append([hits[ipl][2][indx]][0])
	if (ipl>9 and ipl<13):
	    y21trackids.append(StrawRawLink[hits[ipl][2][indx]][0].GetTrackID())
	    y21hitids.append([hits[ipl][2][indx]][0])
	if ipl>12:
	    y22trackids.append(StrawRawLink[hits[ipl][2][indx]][0].GetTrackID())
	    y22hitids.append([hits[ipl][2][indx]][0])
      else:
        if ipl<5:
	    y11trackids.append(999)
	    y11hitids.append(999)
	if (ipl>4 and ipl<9):
	    y12trackids.append(999)
	    y12hitids.append(999)
	if (ipl>9 and ipl<13):
	    y21trackids.append(999)
	    y21hitids.append(999)
	if ipl>12:
	    y22trackids.append(999)
	    y22hitids.append(999)

    #intersect this "plane", with all hits in all other views...

    v2y2=[]
    v2y3=[]
    v2yother=[]
    v2ymin2=[]
    v2z2=[]
    v2z3=[]
    v2zother=[]
    v2zmin2=[]
    for ipl in range(1,len(zlayerv2)+1):
      items=[]
      xclean=[]
      distances=[]
      if cheated==False:
	 xclean,items=line2plane(fitt,fitc,uvview[ipl],zlayerv2[ipl][0])

      else:
         xclean=copy.deepcopy(uvview[ipl][0])
         items=copy.deepcopy(uvview[ipl][4])

      distances=copy.deepcopy(uvview[ipl][5])
      xcleanunsorted=[]
      xcleanunsorted=list(xclean)

      xclean.sort()
      b=len(xclean)*[0]
      d=[]
      e=[]
      for item in xclean:
          d.append(items[xcleanunsorted.index(item)])
	  e.append(distances[xcleanunsorted.index(item)])
      #fill hits info for ptrack, "b" records if hit has been used in ptrack
      v2hits[ipl]=[xclean,b,d,e]
      if global_variables.debug:
	print('      Plane,z, projected hits:', ipl , zlayerv2[ipl], v2hits[ipl])

      for item in range(len(v2hits[ipl][0])):
	if StrawRawLink[v2hits[ipl][2][item]][0].GetTrackID() == 3:
	    v2y3.append(float(v2hits[ipl][0][item]))
	    v2z3.append(float(zlayerv2[ipl][0]))
	else:
	    if StrawRawLink[v2hits[ipl][2][item]][0].GetTrackID() == 2:
	       v2y2.append(float(v2hits[ipl][0][item]))
	       v2z2.append(float(zlayerv2[ipl][0]))
	    else:
	       if StrawRawLink[v2hits[ipl][2][item]][0].GetTrackID() == -2:
	          v2ymin2.append(float(v2hits[ipl][0][item]))
		  v2zmin2.append(float(zlayerv2[ipl][0]))
	       else:
	          v2yother.append(float(v2hits[ipl][0][item]))
		  v2zother.append(float(zlayerv2[ipl][0]))

    #pattern recognition for this track, blow up y-window, maybe make dependend of stereo angle,
    #constant now, should be 5*error/sin(alpha) :-), i.e. variable/plane if different "alphas"
    #Hence, for "real" y-view, should be small.
    if cheated==True:
       nrtrcandv2,trcandv2=ptrack(zlayerv2,v2hits,7,0.7)
    else:
       nrtrcandv2,trcandv2=ptrack(zlayerv2,v2hits,6,15.)
    if len(trcandv2)>1:
      if global_variables.debug:
	print("   len(trcandv2) in stereo", len(trcandv2))

    nstereotracks=0
    if nrtrcandv2==0 :
      if global_variables.debug:
	print("   0 tracks found in stereo view, for Y-view track nr", t)


    #if firsttwo==True: totalstereo12=reconstructiblestereoidsfound12
    #else: totalstereo34==reconstructiblestereoidsfound34

    for t1 in trcandv2:
      if global_variables.debug:
	print('   Track belonging to Y-view view track', t, 'found in stereo view:', t1, trcandv2[t1])

      stereofitt,stereofitc=fitline(trcandv2[t1],v2hits,zlayerv2,resolution)

      pxMC=0.
      pzMC=0.
      stereotanMCv=0.
      stereocstMCv=0.
      if firsttwo==True: looplist=reversed(list(range(len(trcandv2[t1]))))
      else: looplist=list(range(len(trcandv2[t1])))
      for ipl in looplist:
        indx= trcandv2[t1][ipl]
        if indx>-1:
          hitpointx=[zlayerv2[ipl],v2hits[ipl][0][indx]]
          rc=h['disthittostereotrack'].Fill(dist2line(stereofitt,stereofitc,hitpointx))
	  if pxMC==0. :  pxMC=StrawRawLink[v2hits[ipl][2][indx]][0].GetPx()
	  if pzMC ==0. : pzMC=StrawRawLink[v2hits[ipl][2][indx]][0].GetPz()
	  if stereotanMCv==0. : stereotanMCv=pxMC/pzMC
	  if stereocstMCv==0. : stereocstMCv=StrawRawLink[v2hits[ipl][2][indx]][0].GetX()-stereotanMCv*zlayerv2[ipl][0]
	  rc=h['disthittostereoMCtrack'].Fill(dist2line(stereotanMCv,stereocstMCv,hitpointx))


      stereotrackids=[]

      stereo11trackids=[]
      stereo12trackids=[]
      stereo21trackids=[]
      stereo22trackids=[]
      stereo11hitids=[]
      stereo12hitids=[]
      stereo21hitids=[]
      stereo22hitids=[]
      nstereotracks+=1


      for ipl in range(len(trcandv2[t1])):
        indx= trcandv2[t1][ipl]
        if indx>-1:
	  stereotrackids.append(StrawRawLink[v2hits[ipl][2][indx]][0].GetTrackID())
	  if global_variables.debug:
	    print(
		"      plane nr, zpos, x of hit, hitid, trackid",
		ipl, zlayerv2[ipl], v2hits[ipl][0][indx], v2hits[ipl][2][indx],
		StrawRawLink[v2hits[ipl][2][indx]][0].GetTrackID()
		)
	  xdiff=v2hits[ipl][0][indx]-StrawRawLink[v2hits[ipl][2][indx]][0].GetX()
	  h['digi-truevstruex'].Fill(xdiff)
	if ipl<5:
             if indx>-1:
	        stereo11trackids.append(StrawRawLink[v2hits[ipl][2][indx]][0].GetTrackID())
		stereo11hitids.append(v2hits[ipl][2][indx])
	     else:
	        stereo11trackids.append(999)
	        stereo11hitids.append(999)
	if (ipl>4 and ipl<9):
	     if indx>-1:
	        stereo12trackids.append(StrawRawLink[v2hits[ipl][2][indx]][0].GetTrackID())
		stereo12hitids.append(v2hits[ipl][2][indx])
	     else:
	        stereo12trackids.append(999)
	        stereo12hitids.append(999)
	if (ipl>9 and ipl<13):
	     if indx>-1:
	        stereo21trackids.append(StrawRawLink[v2hits[ipl][2][indx]][0].GetTrackID())
		stereo21hitids.append(v2hits[ipl][2][indx])
	     else:
	        stereo21trackids.append(999)
	        stereo21hitids.append(999)
	if ipl>12:
	     if indx>-1:
	        stereo22trackids.append(StrawRawLink[v2hits[ipl][2][indx]][0].GetTrackID())
		stereo22hitids.append(v2hits[ipl][2][indx])
             else:
	        stereo22trackids.append(999)
	        stereo22hitids.append(999)

      if firsttwo==True: h['fracsame12-stereo'].Fill(fracMCsame(stereotrackids)[0])
      else: h['fracsame34-stereo'].Fill(fracMCsame(stereotrackids)[0])

      if global_variables.debug:
         print("      Largest fraction of hits in stereo view:",fracMCsame(stereotrackids)[0],"on MC track with id",fracMCsame(stereotrackids)[1])
         #check if this trackid is the same as the track from the Y-view it belongs to
         if monitor==True: print("      fracMCsame(stereotrackids)[1]", fracMCsame(stereotrackids)[1],"foundhorizontaltrackids[",t-1,"]",foundhorizontaltrackids[t-1])

      if monitor==True:
         if fracMCsame(stereotrackids)[1] != horizontaltrackids[t-1] :
            if global_variables.debug:
	      print(
		  "      Stereo track with trackid",
		  fracMCsame(stereotrackids)[1],
		  "does not belong to the Y-view track with id=",
		  horizontaltrackids[t-1]
		  )
            continue

         #check if this trackid belongs to a reconstructible track
         if fracMCsame(stereotrackids)[1] in ReconstructibleMCTracks:
            if fracMCsame(stereotrackids)[1] not in foundstereotrackids:
	       foundstereotrackids.append(fracMCsame(stereotrackids)[1])
         else:
            if global_variables.debug:
	      print(
		  "      Stereo track with trackid",
		  fracMCsame(stereotrackids)[1],
		  "is not reconstructible. Removing it."
		  )
	    continue
      else:
          if fracMCsame(stereotrackids)[1] not in foundstereotrackids:
	     foundstereotrackids.append(fracMCsame(stereotrackids)[1])

      ntracks=ntracks+1
      alltrackids=y11trackids+stereo11trackids+stereo12trackids+y12trackids+y21trackids+stereo21trackids+stereo22trackids+y22trackids
      if firsttwo==True: h['fracsame12'].Fill(fracMCsame(alltrackids)[0])
      else: h['fracsame34'].Fill(fracMCsame(alltrackids)[0])
      if global_variables.debug:
	print(
	    "      Largest fraction of hits in horizontal and stereo view:", fracMCsame(alltrackids)[0],
	    "on MC track with id", fracMCsame(alltrackids)[1]
	    )

      #calculate efficiency after joining horizontal and stereo tracks
      if monitor==True:
         if fracMCsame(alltrackids)[1] in ReconstructibleMCTracks:
	   if fracMCsame(alltrackids)[1] not in foundtrackids:
	     foundtrackids.append(fracMCsame(alltrackids)[1])

	     tracks[trackkey*1000+nstereotracks]=alltrackids
	     hitids[trackkey*1000+nstereotracks]=y11hitids+stereo11hitids+stereo12hitids+y12hitids+y21hitids+stereo21hitids+stereo22hitids+y22hitids
	     if cheated==False :
               ytan[trackkey*1000+nstereotracks]=fitt
               ycst[trackkey*1000+nstereotracks]=fitc
	     else:
               ytan[trackkey*1000+nstereotracks]=tan
               ycst[trackkey*1000+nstereotracks]=cst


	     fraction[trackkey*1000+nstereotracks]=fracMCsame(alltrackids)[0]
	     trackid[trackkey*1000+nstereotracks]=fracMCsame(alltrackids)[1]


	     horpx[trackkey*1000+nstereotracks]=px
	     horpy[trackkey*1000+nstereotracks]=py
	     horpz[trackkey*1000+nstereotracks]=pz

	     if cheated==False:
               stereotan[trackkey*1000+nstereotracks]=stereofitt
               stereocst[trackkey*1000+nstereotracks]=stereofitc
	     else:
               stereotan[trackkey*1000+nstereotracks]=stereotanMCv
               stereocst[trackkey*1000+nstereotracks]=stereocstMCv
         else:
            if global_variables.debug:
	      print("Track with trackid", fracMCsame(alltrackids)[1], "is not reconstructible. Removing it.")
	    continue
      else:
	   if fracMCsame(alltrackids)[1] not in foundtrackids:
	     foundtrackids.append(fracMCsame(alltrackids)[1])

	     tracks[trackkey*1000+nstereotracks]=alltrackids
	     hitids[trackkey*1000+nstereotracks]=y11hitids+stereo11hitids+stereo12hitids+y12hitids+y21hitids+stereo21hitids+stereo22hitids+y22hitids
	     if cheated==False :
               ytan[trackkey*1000+nstereotracks]=fitt
               ycst[trackkey*1000+nstereotracks]=fitc
	     else:
               ytan[trackkey*1000+nstereotracks]=tan
               ycst[trackkey*1000+nstereotracks]=cst


	     fraction[trackkey*1000+nstereotracks]=fracMCsame(alltrackids)[0]
	     trackid[trackkey*1000+nstereotracks]=fracMCsame(alltrackids)[1]


	     horpx[trackkey*1000+nstereotracks]=px
	     horpy[trackkey*1000+nstereotracks]=py
	     horpz[trackkey*1000+nstereotracks]=pz

	     if cheated==False:
               stereotan[trackkey*1000+nstereotracks]=stereofitt
               stereocst[trackkey*1000+nstereotracks]=stereofitc
	     else:
               stereotan[trackkey*1000+nstereotracks]=stereotanMCv
               stereocst[trackkey*1000+nstereotracks]=stereocstMCv

  if monitor==True:
    if len(foundstereotrackids)>=len(ReconstructibleMCTracks) :
      if firsttwo==True: reconstructiblestereoidsfound12+=1
      else: reconstructiblestereoidsfound34+=1
    else:
      if global_variables.debug:
         debugevent(iEvent,True,v2y2,v2y3,v2ymin2,v2yother,v2z2,v2z3,v2zmin2,v2zother,foundstereotrackids)
         print("Nbr of reconstructible tracks after stereo",len(foundstereotrackids)," but ",len(ReconstructibleMCTracks)," reconstructible tracks in this event. Quitting.")
      return 0,[],[],[],[],[],[],{},{},{},{},{}

    if len(foundtrackids)>=len(ReconstructibleMCTracks):
      if firsttwo==True: reconstructibleidsfound12+=1
      else: reconstructibleidsfound34+=1
    else:
      if global_variables.debug:
         debugevent(iEvent,True,v2y2,v2y3,v2ymin2,v2yother,v2z2,v2z3,v2zmin2,v2zother,foundstereotrackids)
         print("Nbr of reconstructed tracks ",len(foundtrackids)," but",len(ReconstructibleMCTracks)," reconstructible tracks in this event. Quitting.")
      return 0,[],[],[],[],[],[],{},{},{},{},{}
  else:
    if firsttwo==True: reconstructiblestereoidsfound12+=1
    else: reconstructiblestereoidsfound34+=1
    if firsttwo==True: reconstructibleidsfound12+=1
    else: reconstructibleidsfound34+=1

  #now Kalman fit, collect "all hits" around fitted track, outlier removal etc..
  return ntracks,tracks,hitids,ytan,ycst,stereotan,stereocst,horpx,horpy,horpz,fraction,trackid

def TrackFit(hitPosList,theTrack,charge,pinv):
   global theTracks
   if global_variables.debug:
     fitter.setDebugLvl(1)
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
   if not global_variables.debug:
     return # leave track fitting to shipDigiReco
#check
   if not theTrack.checkConsistency():
     print('Problem with track before fit, not consistent', theTrack)
     return
# do the fit
   try:  fitter.processTrack(theTrack)
   except:
     print("genfit failed to fit track")
     return
#check
   if not theTrack.checkConsistency():
     print('Problem with track after fit, not consistent', theTrack)
     return


   fitStatus   = theTrack.getFitStatus()

   nmeas = fitStatus.getNdf()
   pval = fitStatus.getPVal()

   #pval close to 0 indicates a bad fit
   chi2        = fitStatus.getChi2()/nmeas

   rc=h['chi2fittedtracks'].Fill(chi2)
   rc=h['pvalfittedtracks'].Fill(pval)


   fittedState = theTrack.getFittedState()
   fittedMom = fittedState.getMomMag()
   fittedMom = fittedMom*int(charge)

   if math.fabs(pinv) > 0.0 : rc=h['pvspfitted'].Fill(1./pinv,fittedMom)
   fittedtrackDir = fittedState.getDir()
   fittedx=math.degrees(math.acos(fittedtrackDir[0]))
   fittedy=math.degrees(math.acos(fittedtrackDir[1]))
   fittedz=math.degrees(math.acos(fittedtrackDir[2]))
   fittedmass = fittedState.getMass()
   rc=h['momentumfittedtracks'].Fill(fittedMom)
   rc=h['xdirectionfittedtracks'].Fill(fittedx)
   rc=h['ydirectionfittedtracks'].Fill(fittedy)
   rc=h['zdirectionfittedtracks'].Fill(fittedz)
   rc=h['massfittedtracks'].Fill(fittedmass)

   return

def ptrack(zlayer,ptrackhits,nrwant,window):

# basic pattern recognition in one view
# zlayer= dictionary with z-position of planes: zlayer[iplane][0]==z-position (list of length 1 :-).
# ptrackhits is dictionary with hits in a projection:  ptrackhits[plane number][0]=list-of-hits
# ndrop= nr of hits that can be missing in this projection
# nrwant= min nr of hits on a track in this projection
# window: is the size of the search window

# get first and last plane number (needs to be consecutive, and also contains empty planes
# should be included in the list!
 planes=list(zlayer.keys())
 planes.sort()
 i_1=planes[0]
 i_2=planes[len(planes)-1]
 ndrop=len(planes)-nrwant
 #print 'ptrack input: planes=',i_1,i_2,ndrop,window,"   ptrackhits ",ptrackhits

 nrtracks=0
 tracks={}

 #loop over maxnr hits, to max-ndrop
 for nhitw in range(i_2-i_1+1,i_2-i_1-ndrop,-1):
  # nhitw: wanted number of hits when looking for a track
  for idrop in range(ndrop):
    #only start if wanted nr hits <= the nr of planes
    nrhitmax=i_2-i_1-idrop+1
    if nhitw<=nrhitmax:
     for k in range(idrop+1):
        #calculate the id of the first and last plane for this try.
        ifirst=i_1+k
        ilast=i_2-(idrop-k)
        #now loop over hits in first/last planes, and construct line
        dz=zlayer[ilast][0]-zlayer[ifirst][0]
        #hits in first plane
        for ifr in range(len(ptrackhits[ifirst][0])):
	  #for ifr in range(len(ptrackhits[ifirst][0])):
          #has this hit been used already for a track: skip
	  if  ptrackhits[ifirst][1][ifr]==0:
           xfirst= ptrackhits[ifirst][0][ifr]
	   #hits in last plane
           for il in range(len(ptrackhits[ilast][0])):
            #has this hit been used already for a track: skip
            if  ptrackhits[ilast][1][il]==0:
             xlast= ptrackhits[ilast][0][il]
             nrhitsfound=2
             tancand=(xlast-xfirst)/dz
             #fill temporary hit list for track-candidate with -1
             trcand=(i_2-i_1+2)*[-1]
             #loop over in between planes
             for inbetween in range(ifirst+1,ilast):
              #can wanted number of hits be satisfied?
              if nrhitsfound+ilast-inbetween>=nhitw:
               #calculate candidate hit
               xwinlow=xfirst+tancand*(zlayer[inbetween][0]-zlayer[ifirst][0])-window
               for im in range(len(ptrackhits[inbetween][0])):
                #has this hit been used?
                if  ptrackhits[inbetween][1][im]==0:
                 xin= ptrackhits[inbetween][0][im]
                 #hit belwo window, try next one
                 if xin>xwinlow:
                  #if hit larger than upper edge of window: goto next plane
                  if xin>xwinlow+2*window:
		     break
                  #hit found, do administation
                  if trcand[inbetween]==-1:
		    nrhitsfound+=1
                  trcand[inbetween]=im
             #looped over in between planes, collected enough hits?
             if nrhitsfound==nhitw:
               #mark used hits
               trcand[ifirst]=ifr
               trcand[ilast]=il
               for i in range(ifirst,ilast+1):
                  if trcand[i]>=0:
		     ptrackhits[i][1][trcand[i]]=1
               #store the track
               nrtracks+=1
	       #print "ptrack nrtracks",nrtracks
               tracks[nrtracks]=trcand
 #print "ptrack: tracks",tracks
 return nrtracks,tracks

def dorot(x,y,xc,yc,alpha):
    #rotate x,y around xc,yc over angle alpha
    ca=cos(alpha)
    sa=sin(alpha)
    xout=ca*(x-xc)-sa*(y-yc)+xc
    yout=sa*(x-xc)+ca*(y-yc)+yc
    return xout,yout

def line2plane(fitt,fitc,uvview,zuv):
  #intersect horizontal plane, defined by tangent, constant in yz plane, with
  #stereo hits given in uvview,zuv with top/bottom hits of "straw"
  xb=uvview[0]
  yb=uvview[1]
  xt=uvview[2]
  yt=uvview[3]
  x=[]
  items=[]
  term=fitc+zuv*fitt
  #loop over all hits in this view
  for i in range(len(yb)):
    #f2=(term-yb[i])/(yt[i]-yb[i])
    #xint=xb[i]+f2*(xt[i]-xb[i])
    f2=(term-yb[i])/(yb[i]-yt[i])
    xint=xb[i]+f2*(xb[i]-xt[i])
    c=uvview[4][i]
    #do they cross inside sensitive volume defined by top/bottom of straw?
    if xint<max(xt[i],xb[i]) and xint>min(xb[i],xt[i]):
      x.append(xint)
      items.append(c)
  return x,items

def fitline(indices,xhits,zhits,resolution):
   #fit linear function (y=fitt*x+fitc) to list of hits,
   #"x" is the z-coordinate, "y" is the cSoordinate in tracking plane perp to z
   #use equal weights for the time being, and outlier removal (yet)?

   n=0
   sumx=0.
   sumx2=0
   sumxy=0.
   sumy=0.
   sumweight=0.
   sumweightx=0.
   sumweighty=0.
   Dw=0.
   term=0.
   for ipl in range(1,len(indices)):
      indx= indices[ipl]
      if indx>-1:
         #n+=1
	 #weigh points accordint to their distance to the wire
	 weight=1/math.sqrt(xhits[ipl][3][indx]**2+resolution**2)
	 x=zhits[ipl][0]
	 y=xhits[ipl][0][indx]
	 sumweight+=weight
	 sumweightx+=weight*x
	 sumweighty+=weight*y
   xmean=sumweightx/sumweight
   ymean=sumweighty/sumweight
   for ipl in range(1,len(indices)):
      indx= indices[ipl]
      if indx>-1:
         n+=1
	 weight=1/math.sqrt(xhits[ipl][3][indx]**2+resolution**2)
	 x=zhits[ipl][0]
	 y=xhits[ipl][0][indx]
	 Dw+=weight*(x-xmean)**2
	 term+=weight*(x-xmean)*y
         sumx+=zhits[ipl][0]
         sumx2+=zhits[ipl][0]**2
         sumxy+=xhits[ipl][0][indx]*zhits[ipl][0]
         sumy+=xhits[ipl][0][indx]
   fitt=(1/Dw)*term
   fitc=ymean-fitt*xmean
   unweightedfitt=(sumxy-sumx*sumy/n)/(sumx2-sumx**2/n)
   unweightedfitc=(sumy-fitt*sumx)/n
   return fitt,fitc

def IP(s, t, b):
     #some vector manipulations to get impact point of t-b to s
     dir=ROOT.TVector3(t-b)
     udir = ROOT.TVector3(dir.Unit())
     sep = ROOT.TVector3(t-s)
     ip = ROOT.TVector3(udir.Cross(sep.Cross(udir) ))
     return ip.Mag()

def fracMCsame(trackids):
# determine largest fraction of hits which have benn generated by the same # MC true track
#hits: list of pointers to true MC TrackingHits
#return: fraction of hits from same track, and its track-ID
    track={}
    nh=len(trackids)
    for tid in trackids:
       if tid==999:
         nh-=1
         continue
       if tid in track:
          track[tid]+=1
       else:
        track[tid]=1
    #now get track with largest number of hits
    tmax=max(track, key=track.get)

    frac=0.
    if nh>0: frac=float(track[tmax])/float(nh)
    return frac,tmax

def match_tracks(t1,t2,zmagnet,Bdl):
# match tracks before to after magnet
# t1,t2: x,y,z,tgx,tgy of two input tracks
# zmagnet: middle of the magnet
# BdL: Bdl in Tm
# returns:
#     dx,dy: distance between tracks at zmagnet
#     1./pmom:  innverse momentum*q estimated

#linear extrapoaltion to centre of the magnet
   dz1=zmagnet-t1[2]
   x1m=t1[0]+dz1*t1[3]
   y1m=t1[1]+dz1*t1[4]
   dz2=zmagnet-t2[2]
   x2m=t2[0]+dz2*t2[3]
   y2m=t2[1]+dz2*t2[4]
   dx=x1m-x2m
   dy=y1m-y2m

   alpha=math.atan(t1[4])-math.atan(t2[4])
   pinv=math.sin(alpha)/(Bdl*0.3)
   return dx,dy,alpha,pinv

def dist2line(tan,cst,points):
  #points = (x,y)
  #tan, cst are the tangens & constant of the fitted track
  dist = tan*points[0][0] + cst - points[1]
  return dist

def hit2wire(ahit,bot,top,no_amb=None):
     detID = ahit.GetDetectorID()
     ex = ahit.GetX()
     ey = ahit.GetY()
     ez = ahit.GetZ()
   #distance to wire, and smear it.
     dw  = ahit.dist2Wire()
     smear = dw
     if not no_amb: smear = ROOT.fabs(random.Gaus(dw,ShipGeo.strawtubes.sigma_spatial))
     smearedHit = {'mcHit':ahit,'xtop':top.x(),'ytop':top.y(),'z':top.z(),'xbot':bot.x(),'ybot':bot.y(),'z':bot.z(),'dist':smear}
     return smearedHit

def debugevent(stereo,y2,y3,ymin2,yother,z2,z3,zmin2,zother,foundtrackids):
     c = ROOT.TCanvas("c","c",600, 400)
     if stereo==False:
        coord="y"
     else:
        coord="projected x"
     mg=ROOT.TMultiGraph(coord+"-hit coord vs z",coord+"-hit coord vs z; evtnb="+str(iEvent))
     y3vector=ROOT.TVector(len(y3))
     z3vector=ROOT.TVector(len(z3))
     for i in range(len(z3)):
        y3vector[i]=y3[i]
        z3vector[i]=z3[i]
     y2vector=ROOT.TVector(len(y2))
     z2vector=ROOT.TVector(len(z2))
     for i in range(len(z2)):
        y2vector[i]=y2[i]
        z2vector[i]=z2[i]
     ymin2vector=ROOT.TVector(len(ymin2))
     zmin2vector=ROOT.TVector(len(zmin2))
     for i in range(len(zmin2)):
        ymin2vector[i]=ymin2[i]
        zmin2vector[i]=zmin2[i]
     yothervector=ROOT.TVector(len(yother))
     zothervector=ROOT.TVector(len(zother))
     for i in range(len(zother)):
        yothervector[i]=yother[i]
        zothervector[i]=zother[i]
     if len(z3)>0:
        g3=ROOT.TGraph(z3vector,y3vector)
        g3.SetName("g3")
        g3.SetTitle("TrackID=3")
        g3.SetMarkerStyle(3)
        g3.SetDrawOption("AP")
        g3.SetFillStyle(0)
        mg.Add(g3)
     if len(z2)>0:
        g2=ROOT.TGraph(z2vector,y2vector)
        g2.SetName("g2")
        g2.SetTitle("TrackID=2")
        g2.SetMarkerStyle(2)
        g2.SetDrawOption("AP")
        g2.SetFillStyle(0)
        mg.Add(g2)
     if len(zmin2)>0:
        gmin2=ROOT.TGraph(zmin2vector,ymin2vector)
        gmin2.SetName("gmin2")
        gmin2.SetMarkerStyle(4)
        gmin2.SetTitle("TrackID=-2")
        gmin2.SetDrawOption("AP")
        gmin2.SetFillStyle(0)
        mg.Add(gmin2)
     if len(zother) > 0:
        gother=ROOT.TGraph(zothervector,yothervector)
	gother.SetName("gother")
        gother.SetMarkerStyle(5)
        gother.SetDrawOption("AP")
	gother.SetTitle("TrackID=Other")
	gother.SetFillStyle(0)
	mg.Add(gother)
     mg.Draw("A P")
     c.BuildLegend(0.6,0.3,0.99,0.5,"Recble TrackIDs="+str(ReconstructibleMCTracks)+"Found TrackIDs:"+str(foundtrackids))
     c.Write()
     return

def execute(SmearedHits,sTree,ReconstructibleMCTracks):
 global totalaftermatching,morethan500,falsepositive,falsenegative,totalafterpatrec
 global reconstructibleevents,morethan100tracks,theTracks

 fittedtrackids=[]
 reconstructibles12=0
 reconstructibles34=0
 theTracks=[]

 if global_variables.debug:
   print("************* PatRect START **************")

 nShits=sTree.strawtubesPoint.GetEntriesFast()
 nMCTracks = sTree.MCTrack.GetEntriesFast()

 #if nMCTracks < 100:
 if nShits < 500:

     StrawRaw,StrawRawLink=Digitization(sTree,SmearedHits)
     reconstructibleevents+=1
     nr12tracks,tracks12,hitids12,xtan12,xcst12,stereotan12,stereocst12,px12,py12,pz12,fraction12,trackid12=PatRec(True,zlayer,zlayerv2,StrawRaw,StrawRawLink,ReconstructibleMCTracks)
     tracksfound=[]
     if monitor==True:
       for item in ReconstructibleMCTracks:
	 for value in trackid12.values():
	    if item == value and item not in tracksfound:
	        reconstructibles12+=1
		tracksfound.append(item)

       if global_variables.debug:
	 print(
	     "tracksfound", tracksfound,
	     "reconstructibles12", reconstructibles12,
	     "ReconstructibleMCTracks", ReconstructibleMCTracks
	     )
       if len(tracksfound)==0 and len(ReconstructibleMCTracks)>0:
         if global_variables.debug:
	   print("No tracks found in event after stations 1&2. Rejecting event.")
         return

     nr34tracks,tracks34,hitids34,xtan34,xcst34,stereotan34,stereocst34,px34,py34,pz34,fraction34,trackid34=PatRec(False,z34layer,z34layerv2,StrawRaw,StrawRawLink,ReconstructibleMCTracks)

     tracksfound=[]
     if monitor==True:
      for item in ReconstructibleMCTracks:
	for value in trackid34.values():
	    if item == value and item not in tracksfound:
	        reconstructibles34+=1
		tracksfound.append(item)
      if len(tracksfound)==0 and len(ReconstructibleMCTracks)>0:
        if global_variables.debug:
	  print("No tracks found in event after stations 3&4. Rejecting event.")
        return
      MatchedReconstructibleMCTracks=len(ReconstructibleMCTracks)*[0]


     if global_variables.debug:
      if (nr12tracks>0) :
       print(nr12tracks,"tracks12  ",tracks12)
       print("hitids12  ",hitids12)
       print("xtan  ",xtan12,"xcst",xcst12)
       print("stereotan  ",stereotan12,"stereocst  ",stereocst12)
       print("fraction12",fraction12,"trackid12",trackid12)
      else :
       print("No tracks found in stations 1&2.")

      if (nr34tracks>0) :
       print(nr34tracks,"tracks34  ",tracks34)
       print("hitids34  ",hitids34)
       print("xtan34 ",xtan34,"xcst34 ",xcst34)
       print("stereotan34  ",stereotan34,"stereocst34  ",stereocst34)
       print("px34",px34)
      else :
       print("No tracks found in stations 3&4.")

     if monitor==False: totalafterpatrec+=1

     zmagnet=ShipGeo.Bfield.z
     tracksfound=[]
     matches=0

     for item in xtan12:
      z1=0.
      tgy1=xtan12[item]
      tgx1=stereotan12[item]
      y1=xcst12[item]
      x1=stereocst12[item]
      t1=[x1,y1,z1,tgx1,tgy1]
      for ids in hitids12[item]:
         #cheated
         if ids != 999 :
            #loop until we get the particle of this track
	    particle12   = PDG.GetParticle(StrawRawLink[ids][0].PdgCode())
	    try:
	       charge12=particle12.Charge()/3.
	       break
	    except:
	       continue

      falsenegativethistrack=0
      falsepositivethistrack=0
      for item1 in xtan34:
         if monitor==True:  totalafterpatrec+=1
         for k,v in enumerate(ReconstructibleMCTracks):
	    if v not in tracksfound:
	      tracksfound.append(v)
         rawlinkindex=0
         for ids in hitids34[item1]:
            if ids != 999 :
	       particle34   = PDG.GetParticle(StrawRawLink[ids][0].PdgCode())
	       try:
	         charge34=particle34.Charge()/3.
	         break
	       except:
	         continue
         z2=0.
         tgx2=stereotan34[item1]
         tgy2=xtan34[item1]
         y2=xcst34[item1]
         x2=stereocst34[item1]
         t2=[x2,y2,z2,tgx2,tgy2]

         dx,dy,alpha,pinv=match_tracks(t1,t2,zmagnet,-0.75)
         p2x=px34[item1]
         p2y=py34[item1]
         p2z=pz34[item1]
         p2true=1./math.sqrt(p2x**2+p2y**2+p2z**2)
         if global_variables.debug:
	   print(
	       "Matching 1&2 track", item,
	       "with 3&4 track", item1,
	       "dx", dx, "dy", dy, "alpha", alpha, "pinv", pinv, "1/p2true", p2true
	       )
         rc=h['dx-matchedtracks'].Fill(dx)
         rc=h['dy-matchedtracks'].Fill(dy)
         if ((abs(dx)<20) & (abs(dy)<2)) :
            #match found between track nr item in stations 12 & item1 in stations 34
	    #get charge from deflection and check if it corresponds to the MC truth
 	    #field is horizontal (x) hence deflection in y
	    tantheta=(tgy1-tgy2)/(1+tgy1*tgy2)
	    if tantheta>0 :
	       charge="-1"
	       if charge34>0:
	         falsenegative+=1
	         falsenegativethistrack=1
	    else:
	       charge="1"
	       if charge34<0:
	          falsepositive+=1
	     	  falsepositivethistrack=1

            #reject track (and event) if it doesn't correspond to MC truth
	    if monitor==True:
	      if (falsepositivethistrack==0 & falsenegativethistrack==0):
	        totalaftermatching+=1
	      else:
	        if global_variables.debug:
		  print("Charge from track deflection doesn't match MC truth. Rejecting it.")
	        break
	    else:
	      if matches==0:
	        matches==1
	        totalaftermatching+=1

	    if global_variables.debug:
	       print("******* MATCH FOUND stations 12 track id",trackid12[item],"(fraction",fraction12[item]*100,"%) and stations 34 track id",trackid34[item1],"(fraction",fraction34[item1]*100,"%)")
	       print("******* Reconstructible tracks ids",ReconstructibleMCTracks)

	    rc=h['matchedtrackefficiency'].Fill(fraction12[item],fraction34[item1])
	    for k,v in enumerate(ReconstructibleMCTracks):
	      if global_variables.debug:
		print("MatchedReconstructibleMCTracks", MatchedReconstructibleMCTracks, "k", k, "v", v)
	      if v not in MatchedReconstructibleMCTracks:
	        if global_variables.debug:
		  print("ReconstructibleMCTracks", ReconstructibleMCTracks, "trackid34[item1]", trackid34[item1])
	        if v==trackid34[item1]: MatchedReconstructibleMCTracks[k]=v
	    p2true=p2true*int(charge)
	    rc=h['pinvvstruepinv'].Fill(p2true,pinv)
	    if math.fabs(pinv) > 0.0 : rc=h['ptrue-p/ptrue'].Fill((pinv-p2true)/pinv)

	    if cheated==False:
	       hitPosList=[]
               for ids in range(0,len(hitids12[item])):
	         #print "hitids12[",item,"][",ids,"]",hitids12[item][ids]
                 if hitids12[item][ids]!=999 :
                    m=[]
	            if ids in range(0,32):
	              for z in range(0,7):
	               m.append(StrawRaw[hitids12[item][ids]][z])
	            hitPosList.append(m)
               for ids in range(0,len(hitids34[item1])):
                 if hitids34[item1][ids]!=999 :
	            m=[]
	            if ids in range(0,32):
	              for z in range(0,7):
	                m.append(StrawRaw[hitids34[item1][ids]][z])
	            hitPosList.append(m)
               nM = len(hitPosList)
               if nM<25:
                 if global_variables.debug:
		   print("Only", nM, "hits on this track. Insufficient for fitting.")
                 return
	       #all particles are assumed to be muons
               if int(charge)<0:
                 pdg=13
               else:
                 pdg=-13
               rep = ROOT.genfit.RKTrackRep(pdg)
               posM = ROOT.TVector3(0, 0, 0)
               #would be the correct way but due to uncertainties on small angles the sqrt is often negative
               if math.fabs(pinv) > 0.0 : momM = ROOT.TVector3(0,0,int(charge)/pinv)
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
	       TrackFit(hitPosList,theTrack,charge,pinv)
               fittedtrackids.append(trackid34[item1])
         else :
	    if global_variables.debug:
	      print(
		  "******* MATCH NOT FOUND stations 12 track id", trackid12[item],
		  "(fraction", fraction12[item]*100, "%) and stations 34 track id", trackid34[item1],
		  "(fraction", fraction34[item1]*100, "%)"
		  )
            if trackid12[item]==trackid34[item1] :
	       if global_variables.debug:
		 print("trackids the same, but not matched.")

 else:
      #remove events with >500 hits
      morethan500+=1
      return

 #else:
    #morethan100tracks+=1
    #return
 return fittedtrackids


def finalize():
   if global_variables.debug:
     ut.writeHists(h,"recohists_patrec.root")
