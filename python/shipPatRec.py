#!/usr/bin/env python
#module with functions for digitization & pattern recognition
#configuration, histograms etc done in shipPatRec_config
#for documentation, see CERN-SHiP-NOTE-2015-002, https://cds.cern.ch/record/2005715/files/main.pdf
#17-04-2015 comments to EvH
import ROOT, os
import shipunit  as u
import math
import ShipGeoConfig
import copy
from collections import OrderedDict
from ROOT import TVector3
from ROOT import gStyle
from ROOT import TParticlePDG
from ROOT import TGraph
from ROOT import TMultiGraph
from array import array
import operator, sys
import shipPatRec_config



  
def SetupLayers(ship_geo):
   #creates a dictionary with z coordinates of layers
   #and variables with station start/end coordinates
   #to be called once at the beginning of the eventloop
   
   zlayer={} #dictionary with z coordinates of station1,2 layers
   z34layer={} #dictionary with z coordinates of station3,4 layers

   i1=1 #1st layer
   i2=16 #last layer
   #z-positions of Y-view tracking
   #4 stations, 4 views (Y,u,v,Y); each view has 2 planes and each plane has 2 layers
   for i in range(i1,i2+1):
     TStationz = ship_geo.TrackStation1.z
     if (i>8) : 
        TStationz = ship_geo.TrackStation2.z  
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
     Zpos = TStationz+(vnb-3./2.)*ship_geo.strawtubes.DeltazView+(float(pnb)-1./2.)*ship_geo.strawtubes.DeltazPlane+(float(lnb)-1./2.)*ship_geo.strawtubes.DeltazLayer 
     zlayer[i]=[Zpos]

   #z-positions for stereo views
   zlayerv2={}
   z34layerv2={}
   for i in range(i1,i2+1):
     TStationz = ship_geo.TrackStation1.z
     if (i>8) : 
        TStationz = ship_geo.TrackStation2.z   
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
     Zpos_u = TStationz+(vnb-3./2.)*ship_geo.strawtubes.DeltazView+(float(pnb)-1./2.)*ship_geo.strawtubes.DeltazPlane+(float(lnb)-1./2.)*ship_geo.strawtubes.DeltazLayer 
     zlayerv2[i]=[Zpos_u]


   for i in range(i1,i2+1):
     TStationz = ship_geo.TrackStation3.z
     if (i>8) : 
        TStationz = ship_geo.TrackStation4.z  
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
     Zpos = TStationz+(vnb-3./2.)*ship_geo.strawtubes.DeltazView+(float(pnb)-1./2.)*ship_geo.strawtubes.DeltazPlane+(float(lnb)-1./2.)*ship_geo.strawtubes.DeltazLayer 
     z34layer[i]=[Zpos]


   for i in range(i1,i2+1):
     #zlayerv2[i]=[i*100.+50.]
     TStationz = ship_geo.TrackStation3.z
     if (i>8) : 
        TStationz = ship_geo.TrackStation4.z   
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
     Zpos_u = TStationz+(vnb-3./2.)*ship_geo.strawtubes.DeltazView+(float(pnb)-1./2.)*ship_geo.strawtubes.DeltazPlane+(float(lnb)-1./2.)*ship_geo.strawtubes.DeltazLayer 
     z34layerv2[i]=[Zpos_u]

   VetoStationz = ship_geo.vetoStation.z
   if shipPatRec_config.debug==1: print "VetoStation midpoint z=",VetoStationz
   VetoStationEndZ=VetoStationz+(ship_geo.strawtubes.DeltazView+ship_geo.strawtubes.OuterStrawDiameter)/2
   for i in range(1,5):   
     if i==1: TStationz = ship_geo.TrackStation1.z
     if i==2: TStationz = ship_geo.TrackStation2.z  
     if i==3: TStationz = ship_geo.TrackStation3.z  
     if i==4: TStationz = ship_geo.TrackStation4.z 
     if shipPatRec_config.debug==1:
       print "TrackStation",i," midpoint z=",TStationz 
       for vnb in range(0,4):
         for pnb in range (0,2):
           for lnb in range (0,2):
              Zpos = TStationz+(vnb-3./2.)*ship_geo.strawtubes.DeltazView+(float(pnb)-1./2.)*ship_geo.strawtubes.DeltazPlane+(float(lnb)-1./2.)*ship_geo.strawtubes.DeltazLayer 
              print "TStation=",i,"view=",vnb,"plane=",pnb,"layer=",lnb,"z=",Zpos

   TStation1StartZ=zlayer[1][0]-ship_geo.strawtubes.OuterStrawDiameter/2
   TStation4EndZ=z34layer[16][0]+ship_geo.strawtubes.OuterStrawDiameter/2
   return i1,i2,zlayer,zlayerv2,z34layer,z34layerv2,TStation1StartZ,TStation4EndZ,VetoStationz,VetoStationEndZ
             
def getReconstructibleTracks(eventnb,TStation1StartZ,TStation4EndZ,VetoStationz,VetoStationEndZ,sTree,fGeo,TrackingHits,pdgdbase):
  #returns a list of reconstructible tracks for this event
  #call this routine once for each event before smearing
  MCTrackIDs=[]
  rc = sTree.GetEvent(eventnb) 
  nMCTracks = sTree.MCTrack.GetEntriesFast()   

  if shipPatRec_config.debug==1: print "event nbr",eventnb,"has",nMCTracks,"tracks"

  #1. MCTrackIDs: list of tracks decaying after the last tstation and originating before the first
  for i in reversed(range(nMCTracks)):
     atrack = sTree.MCTrack.At(i) 
     #for 3 prong decays check if its a nu
     if shipPatRec_config.threeprong == 1:    
       if pdgdbase.GetParticle(atrack.GetPdgCode()):          
         if pdgdbase.GetParticle(atrack.GetPdgCode()).GetName()[:5]=="nu_mu":
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
  if shipPatRec_config.debug==1: print "Tracks with origin in decay volume",MCTrackIDs	 
    
  #2. hitsinTimeDet: list of tracks with hits in TimeDet	   
  nVetoHits = sTree.vetoPoint.GetEntriesFast() 
  hitsinTimeDet=[]
  for i in range(nVetoHits):
     avetohit = sTree.vetoPoint.At(i)
     #hit in TimeDet?
     if fGeo.FindNode(avetohit.GetX(),avetohit.GetY(),avetohit.GetZ()).GetName() == 'TimeDet_1':
        if avetohit.GetTrackID() not in hitsinTimeDet:
	   hitsinTimeDet.append(avetohit.GetTrackID())
	 
  #3. Remove tracks from MCTrackIDs that are not in hitsinTimeDet 	
  itemstoremove=[]
  for item in MCTrackIDs:
      if shipPatRec_config.threeprong==1:
        #don't remove the nu
        if pdgdbase.GetParticle(sTree.MCTrack.At(item).GetPdgCode()).GetName()[:5]!="nu_mu" and item not in hitsinTimeDet:  
       	  itemstoremove.append(item)       
      else :
        if item not in hitsinTimeDet:
          itemstoremove.append(item)
  for item in itemstoremove:
      MCTrackIDs.remove(item)	   	  	  

  if shipPatRec_config.debug==1: print "Tracks with hits in timedet",MCTrackIDs 
  #4. Find straws that have multiple hits
  nHits = TrackingHits.GetEntriesFast()  
  hitstraws={}
  duplicatestrawhit=[]
  if shipPatRec_config.debug==1: print "Nbr of Rawhits=",nHits
  #rc=shipPatRec_config.h['nbrhits'].Fill(nHits)
  for i in range(nHits):
    ahit = TrackingHits.At(i)
    if (str(ahit.GetDetectorID())[:1]=="5") : continue
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
       if shipPatRec_config.debug==1: print "Duplicate hit",i,"not reconstructible, rejecting."
       continue  
    ahit = TrackingHits.At(i) 
    #is hit inside acceptance? if not mark the track as bad   
    if (((ahit.GetX()/245.)**2 + (ahit.GetY()/495.)**2) >= 1.): 
       if ahit.GetTrackID() not in trackoutsidestations:
          trackoutsidestations.append(ahit.GetTrackID())
    if ahit.GetTrackID() not in MCTrackIDs:
       #hit on not reconstructible track
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
      if shipPatRec_config.threeprong==1:
        #don't remove the nu
        if pdgdbase.GetParticle(sTree.MCTrack.At(item).GetPdgCode()).GetName()[:5]!="nu_mu" and item not in tracks_with_hits_in_all_stations:  
       	  itemstoremove.append(item)      
      else:
        if item not in tracks_with_hits_in_all_stations:
          itemstoremove.append(item)
  for item in itemstoremove:
      MCTrackIDs.remove(item)	

  if shipPatRec_config.debug==1: 
     print "tracks_with_hits_in_all_stations",tracks_with_hits_in_all_stations
     print "Tracks with hits in all stations & inside acceptance ellipse",MCTrackIDs      
  nbrechits=0	    
  for i in range(nHits):
    if i in  duplicatestrawhit: 
       continue 
    nbrechits+=1    
    ahit = TrackingHits.At(i) 	
    if ahit.GetTrackID()>-1 and ahit.GetTrackID() in MCTrackIDs:   	   	   
      atrack = sTree.MCTrack.At(ahit.GetTrackID())
      for j in range(ahit.GetTrackID()+1,nMCTracks) :
        childtrack = sTree.MCTrack.At(j)
        if childtrack.GetMotherId() == ahit.GetTrackID():	   
	    trackmomentum=atrack.GetP()
	    trackweight=atrack.GetWeight()
	    rc=shipPatRec_config.h['reconstructiblemomentum'].Fill(trackmomentum,trackweight)
	    motherId=atrack.GetMotherId() 
	    if motherId==1 :
		HNLmomentum=sTree.MCTrack.At(1).GetP()
		rc=shipPatRec_config.h['HNLmomentumvsweight'].Fill(trackweight,HNLmomentum) 
	        if j==nMCTracks :
 		     trackmomentum=atrack.GetP()
		     trackweight=atrack.GetWeight()
		     rc=shipPatRec_config.h['reconstructiblemomentum'].Fill(trackmomentum,trackweight)
		     if atrack.GetMotherId()==1 :
		       HNLmomentum=sTree.MCTrack.At(1).GetP()
		       rc=shipPatRec_config.h['HNLmomentumvsweight'].Fill(trackweight,HNLmomentum)
  itemstoremove=[]
  for item in MCTrackIDs:	       
    atrack = sTree.MCTrack.At(item)
    motherId=atrack.GetMotherId() 
    if motherId != 1:
        itemstoremove.append(item)
  for item in itemstoremove:
      MCTrackIDs.remove(item)	
      if shipPatRec_config.debug==1: print "MCtrackIDs",MCTrackIDs
  if shipPatRec_config.debug==1: print "Tracks with HNL mother",MCTrackIDs 
  
  #8. check if the tracks are HNL children 
  mufound=0
  pifound=0 
  nu_mufound=0
  itemstoremove=[]
  if MCTrackIDs:
    for item in MCTrackIDs: 
      try: 
        if pdgdbase.GetParticle(sTree.MCTrack.At(item).GetPdgCode()).GetName()[:2]=="mu"   : mufound+=1	
        if pdgdbase.GetParticle(sTree.MCTrack.At(item).GetPdgCode()).GetName()[:2]=="pi"   : pifound+=1 
        if pdgdbase.GetParticle(sTree.MCTrack.At(item).GetPdgCode()).GetName()[:5]=="nu_mu": 
	   nu_mufound+=1  
	   itemstoremove.append(item)
      except:
        if shipPatRec_config.debug==1: print "Unknown particle with pdg code:",sTree.MCTrack.At(item).GetPdgCode()	
    if shipPatRec_config.reconstructiblerequired == 1 :
      if mufound!=1  and pifound!=1: 
          if shipPatRec_config.debug==1: print "No reconstructible pion or muon." 
	  MCTrackIDs=[]   
    if shipPatRec_config.reconstructiblerequired == 2 : 
      if shipPatRec_config.threeprong == 1 :       
          if mufound!=2 or nu_mufound!=1 : 
            if shipPatRec_config.debug==1: print "No reconstructible mu-mu-nu."  
	    MCTrackIDs=[]
	  else:
	    #remove the neutrino from MCTrackIDs for the rest
	    for item in itemstoremove:
               MCTrackIDs.remove(item)	
      else:         
          if mufound!=1 or pifound!=1 : 
            if shipPatRec_config.debug==1: print "No reconstructible pion and muon."  
	    MCTrackIDs=[]     

  if shipPatRec_config.debug==1: print "Tracks with required HNL decay particles",MCTrackIDs 	     
  return MCTrackIDs

def SmearHits(eventnb,sTree,TrackingHits,modules,ship_geo):
  #smears hits (when not cheated) 
  #apply cuts for >500 hits, duplicate straw hits and acceptance
  #call this routine once for each event, before the digitization
  
  top=ROOT.TVector3()
  bot=ROOT.TVector3()
  random = ROOT.TRandom()
  ROOT.gRandom.SetSeed(13)
  
  rc = sTree.GetEvent(eventnb) 
  nHits = TrackingHits.GetEntriesFast()
  withNoStrawSmearing=None
  hitstraws={}
  duplicatestrawhit=[]
  SmearedHits=[]
  for i in range(nHits):
    ahit = TrackingHits.At(i)
    if (str(ahit.GetDetectorID())[:1]=="5") : continue
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
          
  #the following code prints some histograms related to the MC hits  
  strawname=''
  if shipPatRec_config.debug==1: print "nbr of hits=",nHits,"in event",eventnb
  station1hits={}
  station12xhits={}
  station12yhits={}
  station2hits={}
  station3hits={}
  station4hits={}  
  
  for i in range(nHits):
    ahit = TrackingHits.At(i)
    strawname=str(ahit.GetDetectorID())
    #is it a duplicate hit? if so, ignore it	   
    if i in duplicatestrawhit: 
      continue
    #only look at hits in the strawtracking stations
    if (str(ahit.GetDetectorID())[:1]=="5") : continue
    #is hit inside acceptance?  
    if (((ahit.GetX()/245.)**2 + (ahit.GetY()/495.)**2) >= 1.): continue
    
    modules["Strawtubes"].StrawEndPoints(ahit.GetDetectorID(),bot,top)    
    if shipPatRec_config.cheated==False : 
       #this is where the smearing takes place. the hit coordinates can also be read from somewhere else.
       sm   = hit2wire(ahit,bot,top,ship_geo,withNoStrawSmearing)
       m = array('d',[i,sm['xtop'],sm['ytop'],sm['z'],sm['xbot'],sm['ybot'],sm['z'],sm['dist'],ahit.GetDetectorID()])
    else :   
       #for MC truth 
       m = array('d',[i,ahit.GetX(),ahit.GetY(),top[2],ahit.GetX(),ahit.GetY(),top[2],ahit.dist2Wire(),ahit.GetDetectorID()])
    SmearedHits.append(m)
   
    angle=0.    
    if (str(ahit.GetDetectorID())[1:2]=="1"): angle=ship_geo.strawtubes.ViewAngle
    if (str(ahit.GetDetectorID())[1:2]=="2"): angle=ship_geo.strawtubes.ViewAngle*-1.
    if (str(ahit.GetDetectorID())[:1]=="1") :  
       if station1hits.has_key(ahit.GetTrackID()):
          station1hits[ahit.GetTrackID()]+=1
	  rc=shipPatRec_config.h['hits1xy'].Fill(ahit.GetX(),ahit.GetY())    	  
       else:
          station1hits[ahit.GetTrackID()]=1
    if (str(ahit.GetDetectorID())[:1]=="2") :  
       if station2hits.has_key(ahit.GetTrackID()):
          station2hits[ahit.GetTrackID()]+=1
       else:
          station2hits[ahit.GetTrackID()]=1
    if (str(ahit.GetDetectorID())[:1]=="3") :  
       if station3hits.has_key(ahit.GetTrackID()):
          station3hits[ahit.GetTrackID()]+=1
       else:
          station3hits[ahit.GetTrackID()]=1
    if (str(ahit.GetDetectorID())[:1]=="4") :	
       if station4hits.has_key(ahit.GetTrackID()):
          station4hits[ahit.GetTrackID()]+=1
       else:
          station4hits[ahit.GetTrackID()]=1
	  
    if ((str(ahit.GetDetectorID())[:2]=="11" or str(ahit.GetDetectorID())[:2]=="12") or (str(ahit.GetDetectorID())[:2]=="21" or str(ahit.GetDetectorID())[:2]=="22")):
       if station12xhits.has_key(ahit.GetTrackID()):
	  station12xhits[ahit.GetTrackID()]+=1  	  
       else:
          station12xhits[ahit.GetTrackID()]=1
	  
    if ((str(ahit.GetDetectorID())[:2]=="10" or str(ahit.GetDetectorID())[:2]=="13") or (str(ahit.GetDetectorID())[:2]=="20" or str(ahit.GetDetectorID())[:2]=="23")):
       if station12yhits.has_key(ahit.GetTrackID()):
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
     if shipPatRec_config.monitor==True:
       if items in shipPatRec_config.ReconstructibleMCTracks: total1hits=total1hits+station1hits[items]     
     else : total1hits=total1hits+station1hits[items]
  if len(station1hits) > 0 : 
     hits1pertrack=total1hits/len(station1hits)
  for items in station12xhits:
     if shipPatRec_config.monitor==True:
        if items in shipPatRec_config.ReconstructibleMCTracks: total12xhits=total12xhits+station12xhits[items]     
     else: total12xhits=total12xhits+station12xhits[items]
  if len(station12xhits) > 0 : hits12xpertrack=total12xhits/len(station12xhits)
  for items in station12yhits:
     if shipPatRec_config.monitor==True:
        if items in shipPatRec_config.ReconstructibleMCTracks: total12yhits=total12yhits+station12yhits[items]        
     else: total12yhits=total12yhits+station12yhits[items]
  if len(station12yhits) > 0 : hits12ypertrack=total12yhits/len(station12yhits)
  for items in station2hits:
     if shipPatRec_config.monitor==True:
        if items in shipPatRec_config.ReconstructibleMCTracks: total2hits=total2hits+station2hits[items]
     else: total2hits=total2hits+station2hits[items]
  if len(station2hits) > 0 : 
     hits2pertrack=total2hits/len(station2hits)
  for items in station3hits:
     if shipPatRec_config.monitor==True:
        if items in shipPatRec_config.ReconstructibleMCTracks: total3hits=total3hits+station3hits[items]     
     else: total3hits=total3hits+station3hits[items]
  if len(station3hits) > 0 : 
     hits3pertrack=total3hits/len(station3hits)
  for items in station4hits:
     if shipPatRec_config.monitor==True:
        if items in shipPatRec_config.ReconstructibleMCTracks: total4hits=total4hits+station4hits[items]  
     else:  total4hits=total4hits+station4hits[items]
  if len(station4hits) > 0 : 
     hits4pertrack=total4hits/len(station4hits)  
  
  rc=shipPatRec_config.h['hits1-4'].Fill(hits1pertrack+hits2pertrack+hits3pertrack+hits4pertrack)  
  rc=shipPatRec_config.h['hits1'].Fill(hits1pertrack)  
  rc=shipPatRec_config.h['hits12x'].Fill(hits12xpertrack)  
  rc=shipPatRec_config.h['hits12y'].Fill(hits12ypertrack)  
  rc=shipPatRec_config.h['hits2'].Fill(hits2pertrack)    
  rc=shipPatRec_config.h['hits3'].Fill(hits3pertrack)    
  rc=shipPatRec_config.h['hits4'].Fill(hits4pertrack)        
  return SmearedHits
  
def Digitization(eventnb,SmearedHits,shipPatRec_config,sTree,TrackingHits):
  #digitization
  #input: Smeared TrackingHits 
  #output: StrawRaw, StrawRawLink
      
  StrawRaw={} #raw hit dictionary: key=hit number, values=xtop,ytop,ztop,xbot,ybot,zbot,dist2Wire,strawname
  StrawRawLink={} #raw hit dictionary: key=hit number, value=the hit object
    
  rc = sTree.GetEvent(eventnb) 
  nHits = len(SmearedHits)
  j=0
  for i in range(len(SmearedHits)):	  
    xtop=SmearedHits[i][1]
    xbot=SmearedHits[i][4]
    ytop=SmearedHits[i][2]
    ybot=SmearedHits[i][5]
    ztop=SmearedHits[i][3] 
    zbot=SmearedHits[i][6]
    distance=SmearedHits[i][7]
    strawname=SmearedHits[i][8]
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
    StrawRawLink[j]=[TrackingHits.At(i)]
    j=j+1 

  if shipPatRec_config.debug==1: print "Nbr of digitized hits",j  
  return j,StrawRaw,StrawRawLink
         
def PatRec(i1,i2,zlayer,zlayerv2,firsttwo,eventnb,StrawRaw,StrawRawLink,ship_geo): 

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

  for item in StrawRaw:  
     #y hits for horizontal straws
     rawhits[j]=copy.deepcopy(((StrawRaw[item][1]+StrawRaw[item][4])/2,(StrawRaw[item][2]+StrawRaw[item][5])/2,StrawRaw[item][6]))
     if firsttwo==True: 
       if shipPatRec_config.debug==1: print "rawhits[",j,"]=",rawhits[j],"trackid",StrawRawLink[item][0].GetTrackID(),"strawname",StrawRawLink[item][0].GetDetectorID(),"true x",StrawRawLink[item][0].GetX(),"true y",StrawRawLink[item][0].GetY(),"true z",StrawRawLink[item][0].GetZ()
     j=j+1    
      
  sortedrawhits=OrderedDict(sorted(rawhits.items(),key=lambda t:t[1][1])) 
  if shipPatRec_config.debug==1: 
     print " "
     print "horizontal view (y) hits ordered by plane: plane nr, zlayer, hits"

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
	   if shipPatRec_config.debug==1: print " wire hit again",sortedrawhits[item],"strawname=", StrawRawLink[item][0].GetDetectorID()
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
    if shipPatRec_config.debug==1: print i,zlayer[i],hits[i] 
    
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

  if shipPatRec_config.cheated==True :
      if shipPatRec_config.threeprong==1 : nrtrcandv1,trcandv1=ptrack(zlayer,hits,6,0.6)  
      else : nrtrcandv1,trcandv1=ptrack(zlayer,hits,7,0.5) 
  else :
      if shipPatRec_config.threeprong==1 : nrtrcandv1,trcandv1=ptrack(zlayer,hits,6,0.6)  
      else: nrtrcandv1,trcandv1=ptrack(zlayer,hits,7,0.7) 
  
  foundhorizontaltrackids=[]
  horizontaltrackids=[]
  removetrackids=[]
  for t in trcandv1:
    trackids=[]
    if shipPatRec_config.debug==1: 
       print ' '
       print 'track found in Y view:',t,' indices of hits in planes',trcandv1[t]
    for ipl in range(len(trcandv1[t])):      
      indx= trcandv1[t][ipl]
      if indx>-1:     
 	if shipPatRec_config.debug==1: print '   plane nr, z-position, y of hit, trackid:',ipl,zlayer[ipl],hits[ipl][0][indx],StrawRawLink[hits[ipl][2][indx]][0].GetTrackID()
	trackids.append(StrawRawLink[hits[ipl][2][indx]][0].GetTrackID())				
    if shipPatRec_config.debug==1: print "   Largest fraction of hits in Y view:",fracMCsame(trackids)[0],"on MC track with id",fracMCsame(trackids)[1]
    if firsttwo==True: 
       shipPatRec_config.h['fracsame12-y'].Fill(fracMCsame(trackids)[0])
    else: 
       shipPatRec_config.h['fracsame34-y'].Fill(fracMCsame(trackids)[0])
    if shipPatRec_config.monitor==1:   
       if fracMCsame(trackids)[1] in shipPatRec_config.ReconstructibleMCTracks:
          horizontaltrackids.append(fracMCsame(trackids)[1])
          if fracMCsame(trackids)[1] not in foundhorizontaltrackids:
             foundhorizontaltrackids.append(fracMCsame(trackids)[1])
       else:
          #this track is not reconstructible, remove it
          if shipPatRec_config.debug==1: print "Y view track with trackid",fracMCsame(trackids)[1],"is not reconstructible. Removing it."
          removetrackids.append(t) 

       if (len(foundhorizontaltrackids) == 0 or len(horizontaltrackids)==0 ): 
          if shipPatRec_config.debug==1: print "No reconstructible Y view tracks found."
          if shipPatRec_config.monitor==True : return 0,[],[],[],[],[],[],{},{},{},{},{},h
  
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
  
  if shipPatRec_config.monitor==1:          
     if len(shipPatRec_config.ReconstructibleMCTracks)>0:    
        if firsttwo==True: 
          if len(foundhorizontaltrackids)>=len(shipPatRec_config.ReconstructibleMCTracks) : shipPatRec_config.reconstructiblehorizontalidsfound12+=1
          else : 
             if shipPatRec_config.debug==1: 
	       print "!!!!!!!!!!!!!!!! Difference between Y-view tracks found and reconstructible tracks (station 1&2). Quitting patrec."
               debugevent(eventnb,False,y2,y3,ymin2,yother,z2,z3,zmin2,zother,shipPatRec_config,foundhorizontaltrackids)	  
	     return 0,[],[],[],[],[],[],{},{},{},{},{}
        else: 
          if len(foundhorizontaltrackids)>=len(shipPatRec_config.ReconstructibleMCTracks) : shipPatRec_config.reconstructiblehorizontalidsfound34+=1
          else : 
             if shipPatRec_config.debug==1: 
	       print "!!!!!!!!!!!!!!!! Difference between Y-view tracks found and reconstructible tracks (station 3&4). Quitting patrec."
	       debugevent(eventnb,False,y2,y3,ymin2,yother,z2,z3,zmin2,zother,shipPatRec_config,foundhorizontaltrackids)
	     return 0,[],[],[],[],[],[],{},{},{},{},{}

     if len(foundhorizontaltrackids) != shipPatRec_config.reconstructiblerequired :
       if shipPatRec_config.debug==1: print len(foundhorizontaltrackids),"Y view tracks found, but ",shipPatRec_config.reconstructiblerequired,"required."
       return 0,[],[],[],[],[],[],{},{},{},{},{} 
  else:
     if firsttwo==True: shipPatRec_config.reconstructiblehorizontalidsfound12+=1
     else: shipPatRec_config.reconstructiblehorizontalidsfound34+=1


  if nrtrcandv1==0 : 
    if shipPatRec_config.debug==1: print "0 tracks found in Y view. Reconstructible:",len(shipPatRec_config.ReconstructibleMCTracks)
    if shipPatRec_config.monitor==True: return 0,[],[],[],[],[],[],{},{},{},{},{}
  else : 
    if shipPatRec_config.debug==1: print nrtrcandv1,"tracks found in Y view. Reconstructible:",len(shipPatRec_config.ReconstructibleMCTracks)
   
  if shipPatRec_config.debug==1: print "***************** Start of Stereo PatRec **************************"  

  v2hits={}
  v2hitsMC={}

  uvview={}
  j=0
  rawxhits={}
  for item in StrawRaw:  
     rawxhits[j]=copy.deepcopy((StrawRaw[item][0],StrawRaw[item][1],StrawRaw[item][3],StrawRaw[item][4],StrawRaw[item][2],StrawRaw[item][6]))
     if firsttwo==True: 
       if shipPatRec_config.debug==1: print "rawxhits[",j,"]=",rawxhits[j],"trackid",StrawRawLink[item][0].GetTrackID(),"true x",StrawRawLink[item][0].GetX(),"true y",StrawRawLink[item][0].GetY()
     j=j+1  
 
  sortedrawxhits=OrderedDict(sorted(rawxhits.items(),key=lambda t:t[1][4])) 

  if shipPatRec_config.debug==1: print "stereo view hits ordered by plane:"
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

    if shipPatRec_config.debug==1: print '   uv hits, z,xb,yb,xt,yt,dist    ',i,zlayerv2[i],uvview[i][0],uvview[i][1],uvview[i][2],uvview[i][3],uvview[i][4],uvview[i][5]

  # now do pattern recognition in view perpendicular to first search view
  # loop over tracks found in Y view, and intersect this "plane"
  # with hits in other views, and project in "x", then ptrack in "x", etc..

  #loop over tracks found in Y view view 
  ntracks=0 
  trackkey=0 
  tracks={}
  if shipPatRec_config.debug==1:
    if (firsttwo==True) :  
      print 'Loop over tracks found in Y view, stations 1&2'
    else :  
      print 'Loop over tracks found in Y view, stations 3&4'
 
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
    fitt,fitc=fitline(trcandv1[t],hits,zlayer,ship_geo)
    if shipPatRec_config.debug==1: print '   Track nr',t,'in Y view: tangent, constant=',fitt,fitc

    tan=0.
    cst=0.
    px=0.
    py=0.
    pz=0.
    m=0
    if firsttwo==True: looplist=reversed(range(len(trcandv1[t]))) 
    else: looplist=range(len(trcandv1[t])) 
    for ipl in looplist:      
      indx= trcandv1[t][ipl]
      if indx>-1: 
 	if shipPatRec_config.debug==1: print '      Plane nr, z-position, y of hit:',ipl,zlayer[ipl],hits[ipl][0][indx]
        hitpoint=[zlayer[ipl],hits[ipl][0][indx]]
	rc=shipPatRec_config.h['disthittoYviewtrack'].Fill(dist2line(fitt,fitc,hitpoint))
	#if px==0. : px=StrawRawLink[hits[ipl][2][indx]][0].GetPx()
	#if py==0. : py=StrawRawLink[hits[ipl][2][indx]][0].GetPy()
	#if pz==0. : pz=StrawRawLink[hits[ipl][2][indx]][0].GetPz()
	px=StrawRawLink[hits[ipl][2][indx]][0].GetPx()
	py=StrawRawLink[hits[ipl][2][indx]][0].GetPy()
	pz=StrawRawLink[hits[ipl][2][indx]][0].GetPz()
	ptmp=math.sqrt(px**2+py**2+pz**2)
	if shipPatRec_config.debug==1:
	    print "      p",ptmp,"px",px,"py",py,"pz",pz
	if tan==0. : tan=py/pz
	if cst==0. : cst=StrawRawLink[hits[ipl][2][indx]][0].GetY()-tan*zlayer[ipl][0]
	rc=shipPatRec_config.h['disthittoYviewMCtrack'].Fill(dist2line(tan,cst,hitpoint))

    if shipPatRec_config.debug==1: print '   Track nr',t,'in Y view: MC tangent, MC constant=',tan,cst	
    
    for ipl in range(len(trcandv1[t])):      
      indx= trcandv1[t][ipl]
      if indx>-1:   
        diffy=hits[ipl][0][indx]-StrawRawLink[hits[ipl][2][indx]][0].GetY()
	shipPatRec_config.h['digi-truevstruey'].Fill(diffy)
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
      if shipPatRec_config.cheated==False:          
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
      if shipPatRec_config.debug==1: print '      Plane,z, projected hits:',ipl,zlayerv2[ipl],v2hits[ipl]
      
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
    if shipPatRec_config.cheated==True:
       nrtrcandv2,trcandv2=ptrack(zlayerv2,v2hits,7,0.7)
    else:
       nrtrcandv2,trcandv2=ptrack(zlayerv2,v2hits,6,15.)
    if len(trcandv2)>1: 
      if shipPatRec_config.debug==1: print "   len(trcandv2) in stereo",len(trcandv2)
    
    nstereotracks=0
    if nrtrcandv2==0 : 
      if shipPatRec_config.debug==1: print "   0 tracks found in stereo view, for Y-view track nr",t
    

    #if firsttwo==True: totalstereo12=shipPatRec_config.reconstructiblestereoidsfound12
    #else: totalstereo34==shipPatRec_config.reconstructiblestereoidsfound34
    
    for t1 in trcandv2:
      if shipPatRec_config.debug==1: print '   Track belonging to Y-view view track',t,'found in stereo view:',t1,trcandv2[t1]      
      
      stereofitt,stereofitc=fitline(trcandv2[t1],v2hits,zlayerv2,ship_geo)

      pxMC=0.
      pzMC=0.
      stereotanMCv=0.
      stereocstMCv=0.
      if firsttwo==True: looplist=reversed(range(len(trcandv2[t1]))) 
      else: looplist=range(len(trcandv2[t1]))  
      for ipl in looplist:      
        indx= trcandv2[t1][ipl]
        if indx>-1:       
          hitpointx=[zlayerv2[ipl],v2hits[ipl][0][indx]]
          rc=shipPatRec_config.h['disthittostereotrack'].Fill(dist2line(stereofitt,stereofitc,hitpointx)) 
	  if pxMC==0. :  pxMC=StrawRawLink[v2hits[ipl][2][indx]][0].GetPx()
	  if pzMC ==0. : pzMC=StrawRawLink[v2hits[ipl][2][indx]][0].GetPz()
	  if stereotanMCv==0. : stereotanMCv=pxMC/pzMC
	  if stereocstMCv==0. : stereocstMCv=StrawRawLink[v2hits[ipl][2][indx]][0].GetX()-stereotanMCv*zlayerv2[ipl][0]
	  rc=shipPatRec_config.h['disthittostereoMCtrack'].Fill(dist2line(stereotanMCv,stereocstMCv,hitpointx))
                 

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
	  if shipPatRec_config.debug==1: print "      plane nr, zpos, x of hit, hitid, trackid",ipl,zlayerv2[ipl],v2hits[ipl][0][indx],v2hits[ipl][2][indx],StrawRawLink[v2hits[ipl][2][indx]][0].GetTrackID()	
	  xdiff=v2hits[ipl][0][indx]-StrawRawLink[v2hits[ipl][2][indx]][0].GetX()
	  shipPatRec_config.h['digi-truevstruex'].Fill(xdiff)
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
      
      if firsttwo==True: shipPatRec_config.h['fracsame12-stereo'].Fill(fracMCsame(stereotrackids)[0])
      else: shipPatRec_config.h['fracsame34-stereo'].Fill(fracMCsame(stereotrackids)[0])
      
      if shipPatRec_config.debug==1: 
         print "      Largest fraction of hits in stereo view:",fracMCsame(stereotrackids)[0],"on MC track with id",fracMCsame(stereotrackids)[1]    
         #check if this trackid is the same as the track from the Y-view it belongs to
         if shipPatRec_config.monitor==True: print "      fracMCsame(stereotrackids)[1]", fracMCsame(stereotrackids)[1],"foundhorizontaltrackids[",t-1,"]",foundhorizontaltrackids[t-1]
      
      if shipPatRec_config.monitor==True: 
         if fracMCsame(stereotrackids)[1] != horizontaltrackids[t-1] :
            if shipPatRec_config.debug==1: print "      Stereo track with trackid",fracMCsame(stereotrackids)[1] ,"does not belong to the Y-view track with id=",horizontaltrackids[t-1]
            continue
      
         #check if this trackid belongs to a reconstructible track
         if fracMCsame(stereotrackids)[1] in shipPatRec_config.ReconstructibleMCTracks:         
            if fracMCsame(stereotrackids)[1] not in foundstereotrackids: 
	       foundstereotrackids.append(fracMCsame(stereotrackids)[1])
         else:
            if shipPatRec_config.debug==1: print "      Stereo track with trackid",fracMCsame(stereotrackids)[1] ,"is not reconstructible. Removing it."
	    continue
      else:
          if fracMCsame(stereotrackids)[1] not in foundstereotrackids: 
	     foundstereotrackids.append(fracMCsame(stereotrackids)[1])	 
	 
      ntracks=ntracks+1     
      alltrackids=y11trackids+stereo11trackids+stereo12trackids+y12trackids+y21trackids+stereo21trackids+stereo22trackids+y22trackids 
      if firsttwo==True: shipPatRec_config.h['fracsame12'].Fill(fracMCsame(alltrackids)[0])
      else: shipPatRec_config.h['fracsame34'].Fill(fracMCsame(alltrackids)[0])      
      if shipPatRec_config.debug==1: print "      Largest fraction of hits in horizontal and stereo view:",fracMCsame(alltrackids)[0],"on MC track with id",fracMCsame(alltrackids)[1]
      
      #calculate efficiency after joining horizontal and stereo tracks
      if shipPatRec_config.monitor==True: 
         if fracMCsame(alltrackids)[1] in shipPatRec_config.ReconstructibleMCTracks:
	   if fracMCsame(alltrackids)[1] not in foundtrackids:
	     foundtrackids.append(fracMCsame(alltrackids)[1])
                     
	     tracks[trackkey*1000+nstereotracks]=alltrackids
	     hitids[trackkey*1000+nstereotracks]=y11hitids+stereo11hitids+stereo12hitids+y12hitids+y21hitids+stereo21hitids+stereo22hitids+y22hitids 	
	     if shipPatRec_config.cheated==False :
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
	            
	     if shipPatRec_config.cheated==False:
               stereotan[trackkey*1000+nstereotracks]=stereofitt
               stereocst[trackkey*1000+nstereotracks]=stereofitc 
	     else:
               stereotan[trackkey*1000+nstereotracks]=stereotanMCv
               stereocst[trackkey*1000+nstereotracks]=stereocstMCv 
         else:
            if shipPatRec_config.debug==1: print "Track with trackid",fracMCsame(alltrackids)[1] ,"is not reconstructible. Removing it."
	    continue
      else:
	   if fracMCsame(alltrackids)[1] not in foundtrackids:
	     foundtrackids.append(fracMCsame(alltrackids)[1])
                     
	     tracks[trackkey*1000+nstereotracks]=alltrackids
	     hitids[trackkey*1000+nstereotracks]=y11hitids+stereo11hitids+stereo12hitids+y12hitids+y21hitids+stereo21hitids+stereo22hitids+y22hitids 	
	     if shipPatRec_config.cheated==False :
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
	            
	     if shipPatRec_config.cheated==False:
               stereotan[trackkey*1000+nstereotracks]=stereofitt
               stereocst[trackkey*1000+nstereotracks]=stereofitc 
	     else:
               stereotan[trackkey*1000+nstereotracks]=stereotanMCv
               stereocst[trackkey*1000+nstereotracks]=stereocstMCv
	        
  if shipPatRec_config.monitor==True: 
    if len(foundstereotrackids)>=len(shipPatRec_config.ReconstructibleMCTracks) :
      if firsttwo==True: shipPatRec_config.reconstructiblestereoidsfound12+=1
      else: shipPatRec_config.reconstructiblestereoidsfound34+=1    
    else:     
      if shipPatRec_config.debug==1:
         debugevent(eventnb,True,v2y2,v2y3,v2ymin2,v2yother,v2z2,v2z3,v2zmin2,v2zother,shipPatRec_config,foundstereotrackids)
         print "Nbr of reconstructible tracks after stereo",len(foundstereotrackids)," but ",len(shipPatRec_config.ReconstructibleMCTracks)," reconstructible tracks in this event. Quitting."
      return 0,[],[],[],[],[],[],{},{},{},{},{}
     
    if len(foundtrackids)>=len(shipPatRec_config.ReconstructibleMCTracks):
      if firsttwo==True: shipPatRec_config.reconstructibleidsfound12+=1
      else: shipPatRec_config.reconstructibleidsfound34+=1  
    else: 
      if shipPatRec_config.debug==1: 
         debugevent(eventnb,True,v2y2,v2y3,v2ymin2,v2yother,v2z2,v2z3,v2zmin2,v2zother,shipPatRec_config,foundstereotrackids)
         print "Nbr of reconstructed tracks ",len(foundtrackids)," but",len(shipPatRec_config.ReconstructibleMCTracks)," reconstructible tracks in this event. Quitting."
      return 0,[],[],[],[],[],[],{},{},{},{},{}
  else:
    if firsttwo==True: shipPatRec_config.reconstructiblestereoidsfound12+=1
    else: shipPatRec_config.reconstructiblestereoidsfound34+=1  
    if firsttwo==True: shipPatRec_config.reconstructibleidsfound12+=1
    else: shipPatRec_config.reconstructibleidsfound34+=1      
 
  #now Kalman fit, collect "all hits" around fitted track, outlier removal etc..  
  return ntracks,tracks,hitids,ytan,ycst,stereotan,stereocst,horpx,horpy,horpz,fraction,trackid

def TrackFit(n,trackid,hitids12,hitids34,pinv,charge,StrawRaw,patrecbranch,fitTracks,mcLink,ship_geo):
   
   hitPosList=[]
   
   for item in range(0,len(hitids12)):
     if hitids12[item]!=999 : 
        m=[]
	if item in range(0,32):
	  for z in range(0,7):
	    m.append(StrawRaw[hitids12[item]][z])
	hitPosList.append(m)
   for item in range(0,len(hitids34)):
     if hitids34[item]!=999 : 
	m=[]
	if item in range(0,32):
	  for z in range(0,7):
	    m.append(StrawRaw[hitids34[item]][z])
	hitPosList.append(m)
	
   nM = len(hitPosList)
   if nM<25:
     if debug==1: print "Only",nM,"hits on this track. Insufficient for fitting."
     return

   #all particles are assumed to be muons
   if int(charge)<0:
      pdg=13
   else:
      pdg=-13   
   rep = ROOT.genfit.RKTrackRep(pdg)
   
   posM = ROOT.TVector3(0, 0, 0)
   #would be the correct way but due to uncertainties on small angles the sqrt is often negative
   momM = ROOT.TVector3(0,0,int(charge)/pinv)
   
   covM = ROOT.TMatrixDSym(6)
   resolution = ship_geo.straw.resol 
   for  i in range(3):   covM[i][i] = resolution*resolution
   covM[0][0]=resolution*resolution*100.
   for  i in range(3,6): covM[i][i] = ROOT.TMath.pow(resolution / nM / ROOT.TMath.sqrt(3), 2)
   # smeared start state  
   stateSmeared = ROOT.genfit.MeasuredStateOnPlane(rep)
   rep.setPosMomCov(stateSmeared, posM, momM, covM)
   # create track
   seedState = ROOT.TVectorD(6)
   seedCov   = ROOT.TMatrixDSym(6)
   rep.get6DStateCov(stateSmeared, seedState, seedCov)
   theTrack=ROOT.genfit.Track(rep, seedState, seedCov) 
   
   hitCov = ROOT.TMatrixDSym(7)
   hitCov[6][6] = resolution*resolution
   for item in hitPosList:
     itemarray=array('d',[item[0],item[1],item[2],item[3],item[4],item[5],item[6]])
     ms=ROOT.TVectorD(7,itemarray) 
     nHits = shipPatRec_config.PatRecHits.GetEntries()
     if shipPatRec_config.PatRecHits.GetSize() == nHits: shipPatRec_config.PatRecHits.Expand(nHits+1000)
     shipPatRec_config.PatRecHits[nHits] = ms
     tp = ROOT.genfit.TrackPoint(theTrack) # note how the point is told which track it belongs to 
     measurement = ROOT.genfit.WireMeasurement(ms,hitCov,1,6,tp) # the measurement is told which trackpoint it belongs to
     measurement.setMaxDistance(0.5*u.cm)     
     tp.addRawMeasurement(measurement) # package measurement in the TrackPoint                                          
     theTrack.insertPoint(tp)  # add point to Track	      
#check
   if not theTrack.checkConsistency():
     if shipPatRec_config.debug==1: print 'Problem with track before fit, not consistent',theTrack
     return
# do the fit

   try:  shipPatRec_config.fitter.processTrack(theTrack)
   except: 
     if shipPatRec_config.debug==1: print "genfit failed to fit track"
     return
#check
   if not theTrack.checkConsistency():
     if shipPatRec_config.debug==1: print 'Problem with track after fit, not consistent',theTrack
     return  
       
   fitStatus   = theTrack.getFitStatus()

   nmeas = fitStatus.getNdf()
   pval = fitStatus.getPVal()
   
   #pval close to 0 indicates a bad fit
   chi2        = fitStatus.getChi2()/nmeas

   rc=shipPatRec_config.h['chi2fittedtracks'].Fill(chi2)
   rc=shipPatRec_config.h['pvalfittedtracks'].Fill(pval) 

   
   fittedState = theTrack.getFittedState()
   fittedMom = fittedState.getMomMag()
   
   fittedMom = fittedMom*int(charge) 
   
   rc=shipPatRec_config.h['pvspfitted'].Fill(1./pinv,fittedMom) 
   fittedtrackDir = fittedState.getDir()
   fittedx=math.degrees(math.acos(fittedtrackDir[0]))
   fittedy=math.degrees(math.acos(fittedtrackDir[1]))
   fittedz=math.degrees(math.acos(fittedtrackDir[2]))      
   fittedmass = fittedState.getMass()
   rc=shipPatRec_config.h['momentumfittedtracks'].Fill(fittedMom)
   rc=shipPatRec_config.h['xdirectionfittedtracks'].Fill(fittedx)
   rc=shipPatRec_config.h['ydirectionfittedtracks'].Fill(fittedy)
   rc=shipPatRec_config.h['zdirectionfittedtracks'].Fill(fittedz)
   rc=shipPatRec_config.h['massfittedtracks'].Fill(fittedmass)   
      
   #print "track chi2/ndof",chi2,"pval",pval
   # make track persistent
   nTrack   = shipPatRec_config.fGenFitArray.GetEntries()
   if shipPatRec_config.debug==0: theTrack.prune("CFL")  #  http://sourceforge.net/p/genfit/code/HEAD/tree/trunk/core/include/Track.h#l280 
   shipPatRec_config.fGenFitArray[nTrack] = theTrack
   shipPatRec_config.fitTrack2MC.push_back(trackid)
   fitTracks.Fill()
   patrecbranch.Fill()
   mcLink.Fill()

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
 planes=zlayer.keys()
 planes.sort()
 i1=planes[0]
 i2=planes[len(planes)-1]
 ndrop=len(planes)-nrwant
 #print 'ptrack input: planes=',i1,i2,ndrop,window,"   ptrackhits ",ptrackhits

 nrtracks=0
 tracks={}

 #loop over maxnr hits, to max-ndrop
 for nhitw in range(i2-i1+1,i2-i1-ndrop,-1):
  # nhitw: wanted number of hits when looking for a track
  for idrop in range(ndrop):
    #only start if wanted nr hits <= the nr of planes 
    nrhitmax=i2-i1-idrop+1
    if nhitw<=nrhitmax:
     for k in range(idrop+1):
        #calculate the id of the first and last plane for this try.
        ifirst=i1+k
        ilast=i2-(idrop-k)
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
             trcand=(i2-i1+2)*[-1]
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

def fitline(indices,xhits,zhits,ship_geo):
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
	 weight=1/math.sqrt(xhits[ipl][3][indx]**2+ship_geo.straw.resol**2)
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
	 weight=1/math.sqrt(xhits[ipl][3][indx]**2+ship_geo.straw.resol**2)
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
       if track.has_key(tid):
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

def hit2wire(ahit,bot,top,ship_geo,no_amb=None):
     detID = ahit.GetDetectorID()
     #modules["Strawtubes"].StrawEndPoints(detID,bot,top)
     ex = ahit.GetX()
     ey = ahit.GetY()
     ez = ahit.GetZ()
   #distance to wire, and smear it.
     dw  = ahit.dist2Wire()
     smear = dw
     if not no_amb: smear = ROOT.fabs(shipPatRec_config.random.Gaus(dw,ship_geo.straw.resol))
     smearedHit = {'mcHit':ahit,'xtop':top.x(),'ytop':top.y(),'z':top.z(),'xbot':bot.x(),'ybot':bot.y(),'z':bot.z(),'dist':smear}
     return smearedHit

def debugevent(eventnb,stereo,y2,y3,ymin2,yother,z2,z3,zmin2,zother,shipPatRec_config,foundtrackids):   
     c = ROOT.TCanvas("c","c",600, 400)
     if stereo==False:
        coord="y"
     else:
        coord="projected x"	
     mg=ROOT.TMultiGraph(coord+"-hit coord vs z",coord+"-hit coord vs z; evtnb="+str(eventnb))
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
     c.BuildLegend(0.6,0.3,0.99,0.5,"Recble TrackIDs="+str(shipPatRec_config.ReconstructibleMCTracks)+"Found TrackIDs:"+str(foundtrackids))
     c.Write()
     return
   
