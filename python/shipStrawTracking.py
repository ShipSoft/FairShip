#!/usr/bin/env python
#first version of digitization & pattern recognition
#for documentation, see CERN-SHiP-NOTE-2015-002, https://cds.cern.ch/record/2005715/files/main.pdf
#17-04-2015 comments to EvH
import shipPatRec_config
from shipPatRec import *
        
import shipDet_conf

from optparse import OptionParser
parser = OptionParser()
parser.add_option("-c","--cheated", dest="chtd", help="cheated=1 to use MC hit x,y instead of wire left&right coordinates",default=0)
parser.add_option("-d","--debug", dest="dbg", help="debug=1 to print debug information",default=0)
parser.add_option("-f","--file", dest="input", help="input file", default="$FAIRSHIP/ship.10.0.Pythia8-TGeant4.root")
parser.add_option("-g","--geometry", dest="geometry", help="input geometry file", default='$FAIRSHIP/geofile_full.10.0.Pythia8-TGeant4.root')
parser.add_option("-m","--monitor", dest="mntr", help="monitor=1 to obtain the PatRec efficiency wrt MC truth",default=0)
parser.add_option("-o","--options", dest="helptext", help="Available options:",default=0)
parser.add_option("-r","--reconstructible", dest="rectracks", help="number of reconstructible tracks required",default=2)
parser.add_option("-t","--threeprong", dest="tp", help="threeprong=1 mumunu decay",default=0)

(options,args)=parser.parse_args()

shipPatRec_config.cheated=bool(options.chtd)
shipPatRec_config.debug = int(options.dbg)
shipPatRec_config.fn = options.input
shipPatRec_config.geofile = options.geometry
shipPatRec_config.monitor=bool(options.mntr)
shipPatRec_config.printhelp=bool(options.helptext)
shipPatRec_config.reconstructiblerequired = int(options.rectracks)
shipPatRec_config.threeprong = int(options.tp)

if (shipPatRec_config.printhelp==True or args==[]):
   print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
   print "shipStrawTracking runs the straw tracker pattern recognition and fits the resulting tracks with DAF. Available options:" 
   print "-c 1                      : uses MC true hit x,y instead of wire left&right coordinates and stereo projections. default 0"
   print "-d 1                      : print a lot of debug messages. default 0"
   print "-g name_of_geometry_file  : input geometry file. default='$FAIRSHIP/geofile_full.10.0.Pythia8-TGeant4.root'"
   print "-i name_of_input_file     : input file name.default='$FAIRSHIP/ship.10.0.Pythia8-TGeant4.root'"
   print "-m 1                      : obtain the PatRec efficiency wrt MC truth. default 0"
   print "-o 1                      : prints this message."
   print "-r reconstructible tracks : number of reconstructible tracks required when monitoring. default 2"
   print "-t 1                      : to be used when monitoring the threeprong mumunu decay. default 0"
   print "runing example            : "
   print "python python/shipStrawTracking.py -i ship.10.0.Pythia8-TGeant4-1000.root -g geofile_full.10.0.Pythia8-TGeant4-1000.root"
   print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
   sys.exit()

ship_geo = ShipGeoConfig.ConfigRegistry().loadpy("$FAIRSHIP/geometry/geometry_config.py",strawDesign=4,muShieldDesign=5,targetOpt=5)


run = ROOT.FairRunSim()
shipDet_conf.configure(run,ship_geo)
modules = {}
for x in run.GetListOfModules(): modules[x.GetName()]=x

angle=ship_geo.strawtubes.ViewAngle

gf   = ROOT.TFile(shipPatRec_config.geofile)
fGeo = gf.Get("FAIRGeom")
listofvolumes = fGeo.GetListOfVolumes()

bfield = ROOT.genfit.BellField(ship_geo.Bfield.max ,ship_geo.Bfield.z,2,ship_geo.Yheight/2.*u.m)
fM = ROOT.genfit.FieldManager.getInstance()
fM.init(bfield)
 
geoMat =  ROOT.genfit.TGeoMaterialInterface()
ROOT.genfit.MaterialEffects.getInstance().init(geoMat)

f = ROOT.TFile(shipPatRec_config.fn)
sTree   = f.FindObjectAny('cbmsim')
nEvents = sTree.GetEntries()
sFol  = f.FindObjectAny('cbmroot')
MCTracks   = ROOT.TClonesArray("FairMCTrack")
TrackingHits   = ROOT.TClonesArray("strawtubesPoint")

if sTree.GetBranch("GeoTracks"): sTree.SetBranchStatus("GeoTracks",0)

outfile=shipPatRec_config.fn.replace('.root','_patrec.root')
os.system('cp '+shipPatRec_config.fn+' '+outfile)
fout=ROOT.TFile(outfile,'update')

outsTree = fout.FindObjectAny('cbmsim')
 
patrecbranch    = outsTree.Branch( "PatRecHits",shipPatRec_config.PatRecHits,32000,-1)
fitTracks   = outsTree.Branch( "FitTracks",shipPatRec_config.fGenFitArray,32000,-1)  
mcLink      = outsTree.Branch( "fitTrack2MC",shipPatRec_config.fitTrack2MC,32000,-1)  

totalaftermatching=0
totalafterpatrec=0
reconstructibleevents=0


pdgdbase=ROOT.TDatabasePDG().Instance()
   

if shipPatRec_config.debug==1:
  print "Straw tracker geometry parameters (cm)"
  print "--------------------------------------"
  print "Strawlength            :",2*ship_geo.strawtubes.StrawLength
  print "Inner straw diameter   :",ship_geo.strawtubes.InnerStrawDiameter
  print "Straw wall thickness   :",ship_geo.strawtubes.WallThickness 
  print "Outer straw diameter   :",ship_geo.strawtubes.OuterStrawDiameter
  print "Wire thickness         :",ship_geo.strawtubes.WireThickness
  print "Straw pitch            :",ship_geo.strawtubes.StrawPitch
  print "z-offset between layers:",ship_geo.strawtubes.DeltazLayer
  print "z-offset between planes:",ship_geo.strawtubes.DeltazPlane
  print "Straws per layer       :",ship_geo.strawtubes.StrawsPerLayer
  print "z-offset between planes:",ship_geo.strawtubes.DeltazPlane
  print "Stereo angle           :",ship_geo.strawtubes.ViewAngle
  print "z-offset between views :",ship_geo.strawtubes.DeltazView
   
def EventLoop():
 global StrawRaw,StrawRawLink,totalaftermatching
 global totalafterpatrec,reconstructibleevents,reconstructibles12,reconstructibles34
 
 i1,i2,zlayer,zlayerv2,z34layer,z34layerv2,TStation1StartZ,TStation4EndZ,VetoStationz,VetoStationEndZ=SetupLayers(ship_geo)
 
 #number of false negative/positive charge matches wrt mc truth
 falsepositive=0
 falsenegative=0
 
 #nbr of events with more than 500 hits
 morethan500=0
 
 #loop over events
 for n in range(nEvents):
  reconstructibles12=0
  reconstructibles34=0
  if shipPatRec_config.debug==1: print "************* START OF  EVENT",n,"**************"  
  
  shipPatRec_config.ReconstructibleMCTracks=[]
  sTree.SetBranchAddress("strawtubesPoint", TrackingHits)  
  rc = sTree.GetEvent(n)    
  
  if shipPatRec_config.monitor==True: 
     shipPatRec_config.ReconstructibleMCTracks=getReconstructibleTracks(n,TStation1StartZ,TStation4EndZ,VetoStationz,VetoStationEndZ,sTree,fGeo,TrackingHits,pdgdbase)
     if len(shipPatRec_config.ReconstructibleMCTracks)!=shipPatRec_config.reconstructiblerequired : 
        if shipPatRec_config.debug==1: print "Number of reconstructible tracks =",len(shipPatRec_config.ReconstructibleMCTracks),"but number of reconstructible required=",shipPatRec_config.reconstructiblerequired,". Rejecting event."
        continue
     MatchedReconstructibleMCTracks=len(shipPatRec_config.ReconstructibleMCTracks)*[0]
     if shipPatRec_config.debug==1: print "Reconstructible track ids",shipPatRec_config.ReconstructibleMCTracks,"MatchedReconstructibleMCTracks",MatchedReconstructibleMCTracks
     
  #n = current event number, False=wire endpoints, True=MC truth
  StrawRaw={}
  StrawRawLink={}
  rc = sTree.GetEvent(n) 
  nHits = TrackingHits.GetEntriesFast()
  if nHits < 500: 
     SmearedHits=SmearHits(n,sTree,TrackingHits,modules,ship_geo)
     nbrofhits,StrawRaw,StrawRawLink=Digitization(n,SmearedHits,shipPatRec_config,sTree,TrackingHits)
  else: 
    #remove events with >500 hits
    morethan500+=1
    continue
  if (nbrofhits < 500) : 
   reconstructibleevents+=1
   
   shipPatRec_config.PatRecHits.Delete()
   shipPatRec_config.fGenFitArray.Delete()
   shipPatRec_config.fitTrack2MC.clear()
   
   nMCTracks=[]
   for i in range(nHits):
     ahit=TrackingHits.At(i)
     if ahit.GetTrackID() not in nMCTracks:
        nMCTracks.append(ahit.GetTrackID())
   
   rc=shipPatRec_config.h['nbrtracks'].Fill(len(nMCTracks))
   rc=shipPatRec_config.h['nbrhits'].Fill(nHits)
   
   if shipPatRec_config.debug==1: print "************* PATREC OF EVENT",n,"**************"  

   if shipPatRec_config.debug==1: print "Starting pattern recognition in stations 1&2."
   #n=current event number, False=wire endpoints, True=MC truth, cheated pattern reco
   #12 refers to stations 1&2, 34 to stations 3&4
   nr12tracks,tracks12,hitids12,xtan12,xcst12,stereotan12,stereocst12,px12,py12,pz12,fraction12,trackid12=PatRec(i1,i2,zlayer,zlayerv2,True,n,StrawRaw,StrawRawLink,ship_geo)
   
   tracksfound=[]
   if shipPatRec_config.monitor==True:
     for item in shipPatRec_config.ReconstructibleMCTracks:
	for value in trackid12.values():  
	    if item == value and item not in tracksfound:
	        reconstructibles12+=1
		tracksfound.append(item)
		
     if shipPatRec_config.debug==1: print "tracksfound",tracksfound,"reconstructibles12",reconstructibles12,"ReconstructibleMCTracks",shipPatRec_config.ReconstructibleMCTracks	
     if len(tracksfound)==0 and len(shipPatRec_config.ReconstructibleMCTracks)>0: 
       if shipPatRec_config.debug==1: print "No tracks found in event after stations 1&2. Rejecting event."
       continue
   
   if shipPatRec_config.debug==1: print "Starting pattern recognition in stations 3&4."
   nr34tracks,tracks34,hitids34,xtan34,xcst34,stereotan34,stereocst34,px34,py34,pz34,fraction34,trackid34=PatRec(i1,i2,z34layer,z34layerv2,False,n,StrawRaw,StrawRawLink,ship_geo)
   
   tracksfound=[]      
   if shipPatRec_config.monitor==True:
     for item in shipPatRec_config.ReconstructibleMCTracks:
	for value in trackid34.values():  
	    if item == value and item not in tracksfound:
	        reconstructibles34+=1
		tracksfound.append(item)
    
     if len(tracksfound)==0 and len(shipPatRec_config.ReconstructibleMCTracks)>0: 
        if shipPatRec_config.debug==1: print "No tracks found in event after stations 3&4. Rejecting event."
        continue

   if shipPatRec_config.debug==1:
     if (nr12tracks>0) : 
       print nr12tracks,"tracks12  ",tracks12
       print "hitids12  ",hitids12
       print "xtan  ",xtan12,"xcst",xcst12
       print "stereotan  ",stereotan12,"stereocst  ",stereocst12
       print "fraction12",fraction12,"trackid12",trackid12
     else : 
       print "No tracks found in stations 1&2."
	 
     if (nr34tracks>0) : 
       print nr34tracks,"tracks34  ",tracks34
       print "hitids34  ",hitids34   
       print "xtan34 ",xtan34,"xcst34 ",xcst34
       print "stereotan34  ",stereotan34,"stereocst34  ",stereocst34
       print "px34",px34
     else : 
       print "No tracks found in stations 3&4."

   if shipPatRec_config.monitor==False: totalafterpatrec+=1

   zmagnet=ship_geo.Bfield.z
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
	  particle12   = pdgdbase.GetParticle(StrawRawLink[ids][0].PdgCode())
	  try:
	     charge12=particle12.Charge()/3.
	     break
	  except:
	     continue   
	     
    falsenegativethistrack=0
    falsepositivethistrack=0
    for item1 in xtan34:  
       if shipPatRec_config.monitor==True:  totalafterpatrec+=1 	     
       for k,v in enumerate(shipPatRec_config.ReconstructibleMCTracks):
	  if v not in tracksfound: 
	      tracksfound.append(v)      
       rawlinkindex=0            
       for ids in hitids34[item1]:
          if ids != 999 :  
	     particle34   = pdgdbase.GetParticle(StrawRawLink[ids][0].PdgCode())
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
       if shipPatRec_config.debug==1: print "Matching 1&2 track",item,"with 3&4 track",item1,"dx",dx,"dy",dy,"alpha",alpha,"pinv",pinv,"1/p2true",p2true
       rc=shipPatRec_config.h['dx-matchedtracks'].Fill(dx)
       rc=shipPatRec_config.h['dy-matchedtracks'].Fill(dy)
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
	  if shipPatRec_config.monitor==True:
	    if (falsepositivethistrack==0 & falsenegativethistrack==0):
	      totalaftermatching+=1
	    else: 
	      if shipPatRec_config.debug==1: print "Charge from track deflection doesn't match MC truth. Rejecting it."
	      break
	  else:
	    if matches==0: 
	      matches==1
	      totalaftermatching+=1

	  if shipPatRec_config.debug==1: 
	     print "******* MATCH FOUND stations 12 track id",trackid12[item],"(fraction",fraction12[item]*100,"%) and stations 34 track id",trackid34[item1],"(fraction",fraction34[item1]*100,"%)"
	     print "******* Reconstructible tracks ids",shipPatRec_config.ReconstructibleMCTracks
	    
	  rc=shipPatRec_config.h['matchedtrackefficiency'].Fill(fraction12[item],fraction34[item1])
	  for k,v in enumerate(shipPatRec_config.ReconstructibleMCTracks):
	    if shipPatRec_config.debug==1: print "MatchedReconstructibleMCTracks",MatchedReconstructibleMCTracks,"k",k,"v",v
	    if v not in MatchedReconstructibleMCTracks:
	        if shipPatRec_config.debug==1: print "ReconstructibleMCTracks",shipPatRec_config.ReconstructibleMCTracks,"trackid34[item1]",trackid34[item1]
	        if v==trackid34[item1]: MatchedReconstructibleMCTracks[k]=v
	  p2true=p2true*int(charge)
	  rc=shipPatRec_config.h['pinvvstruepinv'].Fill(p2true,pinv)
	  rc=shipPatRec_config.h['ptrue-p/ptrue'].Fill((pinv-p2true)/pinv)
	  
	  if shipPatRec_config.cheated==False: TrackFit(n,trackid34[item1],hitids12[item],hitids34[item1],pinv,charge,StrawRaw,patrecbranch,fitTracks,mcLink,ship_geo)

       else :
	  if shipPatRec_config.debug==1: print "******* MATCH NOT FOUND stations 12 track id",trackid12[item],"(fraction",fraction12[item]*100,"%) and stations 34 track id",trackid34[item1],"(fraction",fraction34[item1]*100,"%)"
          if trackid12[item]==trackid34[item1] : 
	     if shipPatRec_config.debug==1: print "trackids the same, but not matched."

   if len(shipPatRec_config.ReconstructibleMCTracks) > 0 :
	if shipPatRec_config.debug==1: print "len(shipPatRec_config.ReconstructibleMCTracks)",len(shipPatRec_config.ReconstructibleMCTracks),"MatchedReconstructibleMCTracks",MatchedReconstructibleMCTracks
	for k,v in enumerate(MatchedReconstructibleMCTracks):
	   if v==0 : 
	     if shipPatRec_config.debug==1: print "Unmatched trackid",shipPatRec_config.ReconstructibleMCTracks[k],"particle",pdgdbase.GetParticle(sTree.MCTrack.At(shipPatRec_config.ReconstructibleMCTracks[k]).GetPdgCode()).GetName() 
	     if pdgdbase.GetParticle(sTree.MCTrack.At(shipPatRec_config.ReconstructibleMCTracks[k]).GetPdgCode()).GetName() in shipPatRec_config.particles:
	        rc=shipPatRec_config.h['unmatchedparticles'].Fill(str(pdgdbase.GetParticle(sTree.MCTrack.At(shipPatRec_config.ReconstructibleMCTracks[k]).GetPdgCode()).GetName()),1)
             else:
	        rc=shipPatRec_config.h['unmatchedparticles'].Fill("other",1)
             unmatchedtrackmomentum=sTree.MCTrack.At(shipPatRec_config.ReconstructibleMCTracks[k]).GetP()		
	     rc=shipPatRec_config.h['reconstructibleunmmatchedmomentum'].Fill(unmatchedtrackmomentum,sTree.MCTrack.At(shipPatRec_config.ReconstructibleMCTracks[k]).GetWeight())    
  else:
    if shipPatRec_config.debug==1: print "Event has >500 hits and is not reconstructible. Rejecting."
    
 if shipPatRec_config.debug==1: 
   print morethan500,"events with more than 500 hits."   
   print falsenegative,"matched tracks with wrong negative charge from deflection."
   print falsepositive,"matched tracks with wrong positive charge from deflection."
 return   
            
if shipPatRec_config.debug==1:
  if shipPatRec_config.threeprong==1:
    debugrootfile = ROOT.TFile(str(shipPatRec_config.reconstructiblerequired)+"track-debug-mumunu-"+str(nEvents)+".root","RECREATE")   
  else:  
    debugrootfile = ROOT.TFile(str(shipPatRec_config.reconstructiblerequired)+"track-debug-"+str(nEvents)+".root","RECREATE")       
EventLoop()

#1/0
shipPatRec_config.h['pinvvstruepinv'].Draw('box')
scale=1.
if shipPatRec_config.h['fracsame12'].Integral() <>0 : scale=1/shipPatRec_config.h['fracsame12'].Integral()
shipPatRec_config.h['fracsame12'].Scale(scale)
scale=1.
if shipPatRec_config.h['fracsame12-y'].Integral() <>0 : scale=1/shipPatRec_config.h['fracsame12-y'].Integral()
shipPatRec_config.h['fracsame12-y'].Scale(scale)
scale=1.
if shipPatRec_config.h['fracsame12-stereo'].Integral() <>0 : scale=1/shipPatRec_config.h['fracsame12-stereo'].Integral()
shipPatRec_config.h['fracsame12-stereo'].Scale(scale)
scale=1.
if shipPatRec_config.h['fracsame34'].Integral() <>0 : scale=1/shipPatRec_config.h['fracsame34'].Integral()
shipPatRec_config.h['fracsame34'].Scale(scale)
scale=1.
if shipPatRec_config.h['fracsame34-y'].Integral() <>0 : scale=1/shipPatRec_config.h['fracsame34-y'].Integral()
shipPatRec_config.h['fracsame34-y'].Scale(scale)
scale=1.
if shipPatRec_config.h['fracsame34-stereo'].Integral() <>0 : scale=1/shipPatRec_config.h['fracsame34-stereo'].Integral()
shipPatRec_config.h['fracsame34-stereo'].Scale(scale)

scale=1.

if shipPatRec_config.monitor==1: 
  totalafterpatrec=totalafterpatrec/(shipPatRec_config.reconstructiblerequired**2)
  totalaftermatching=totalaftermatching/shipPatRec_config.reconstructiblerequired
  
rc=shipPatRec_config.h['eventspassed'].SetBinContent(1,reconstructibleevents)
rc=shipPatRec_config.h['eventspassed'].SetBinContent(2,shipPatRec_config.reconstructiblehorizontalidsfound12)
rc=shipPatRec_config.h['eventspassed'].SetBinContent(3,shipPatRec_config.reconstructiblestereoidsfound12)
rc=shipPatRec_config.h['eventspassed'].SetBinContent(4,shipPatRec_config.reconstructibleidsfound12)
rc=shipPatRec_config.h['eventspassed'].SetBinContent(5,shipPatRec_config.reconstructiblehorizontalidsfound34)
rc=shipPatRec_config.h['eventspassed'].SetBinContent(6,shipPatRec_config.reconstructiblestereoidsfound34)
rc=shipPatRec_config.h['eventspassed'].SetBinContent(7,shipPatRec_config.reconstructibleidsfound34)
rc=shipPatRec_config.h['eventspassed'].SetBinContent(8,totalafterpatrec)
rc=shipPatRec_config.h['eventspassed'].SetBinContent(9,totalaftermatching)

outsTree.Write()
fout.Close()
if shipPatRec_config.threeprong==1:
  shipPatRec_config.ut.writeHists(shipPatRec_config.h,"patrec-"+str(shipPatRec_config.reconstructiblerequired)+"track-mumunu-"+str(nEvents)+".root")
else:
  shipPatRec_config.ut.writeHists(shipPatRec_config.h,"patrec-"+str(shipPatRec_config.reconstructiblerequired)+"track-"+str(nEvents)+".root")
