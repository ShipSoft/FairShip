#!/usr/bin/env python
#first version of digitization & pattern recognition
#for documentation, see CERN-SHiP-NOTE-2015-002, https://cds.cern.ch/record/2005715/files/main.pdf
#17-04-2015 comments to EvH

import shipPatRec_prev 
import ROOT,os,sys,getopt
import shipDet_conf
import shipunit  as u

nEvents    = 999999

from optparse import OptionParser
parser = OptionParser()
parser.add_option("-c","--cheated", dest="chtd", help="cheated=1 to use MC hit x,y instead of wire left&right coordinates",default=0)
parser.add_option("-d","--debug", dest="dbg", help="debug=1 to print debug information",default=0)
parser.add_option("-f","--inputFile", dest="input", help="input file", default="$FAIRSHIP/ship.10.0.Pythia8-TGeant4.root")
parser.add_option("-g","--geoFile", dest="geometry", help="input geometry file", default='$FAIRSHIP/geofile_full.10.0.Pythia8-TGeant4.root')
parser.add_option("-m","--monitor", dest="mntr", help="monitor=1 to obtain the PatRec efficiency wrt MC truth",default=0)
parser.add_option("-o","--options", dest="helptext", help="Available options:",default=0)
parser.add_option("-r","--reconstructible", dest="rectracks", help="number of reconstructible tracks required",default=2)
parser.add_option("-s","--saveDisk", dest="saveDisk", help="save file to disk",default=0)
parser.add_option("-t","--threeprong", dest="tp", help="threeprong=1 mumunu decay",default=0)

(options,args)=parser.parse_args()

shipPatRec_prev.cheated=bool(options.chtd)
shipPatRec_prev.debug = int(options.dbg)
inputFile = options.input
shipPatRec_prev.geoFile = options.geometry
shipPatRec_prev.monitor=bool(options.mntr)
shipPatRec_prev.printhelp=bool(options.helptext)
shipPatRec_prev.reconstructiblerequired = int(options.rectracks)
shipPatRec_prev.threeprong = int(options.tp)
saveDisk = options.saveDisk

if (shipPatRec_prev.printhelp==True or len(sys.argv)==1):
   print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
   print "shipStrawTracking runs the straw tracker pattern recognition and fits the resulting tracks with DAF. Available options:" 
   print "-c 1                      : uses MC true hit x,y instead of wire left&right coordinates and stereo projections. default 0"
   print "-d 1                      : print a lot of debug messages. default 0"
   print "-g name_of_geometry_file  : input geometry file. default='$FAIRSHIP/geofile_full.10.0.Pythia8-TGeant4.root'"
   print "-f name_of_input_file     : input file name.default='$FAIRSHIP/ship.10.0.Pythia8-TGeant4.root'"
   print "-m 1                      : obtain the PatRec efficiency wrt MC truth. default 0"
   print "-o 1                      : prints this message."
   print "-r reconstructible tracks : number of reconstructible tracks required when monitoring. default 2"
   print "-s 1                      : to save output to disk. default 0"
   print "-t 1                      : to be used when monitoring the threeprong mumunu decay. default 0"
   print "runing example            : "
   print "python python/shipStrawTracking.py -i ship.10.0.Pythia8-TGeant4-1000.root -g geofile_full.10.0.Pythia8-TGeant4-1000.root"
   print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
   sys.exit()

if not inputFile.find('_patrec.root') < 0: 
  outFile   = inputFile
  inputFile = outFile.replace('_patrec.root','.root') 
else:
  outFile = inputFile.replace('.root','_patrec.root') 
  if saveDisk: os.system('mv '+inputFile+' '+outFile)
  else :       os.system('cp '+inputFile+' '+outFile)

if not shipPatRec_prev.geoFile:
 tmp = inputFile.replace('ship.','geofile_full.')
 shipPatRec_prev.geoFile = tmp.replace('_rec','')

run = ROOT.FairRunSim()
shipDet_conf.configure(run,shipPatRec_prev.ship_geo)
modules = {}
for x in run.GetListOfModules(): modules[x.GetName()]=x

fgeo   = ROOT.TFile(shipPatRec_prev.geoFile)
sGeo   = fgeo.FAIRGeom


bfield = ROOT.genfit.BellField(shipPatRec_prev.ship_geo.Bfield.max ,shipPatRec_prev.ship_geo.Bfield.z,2,shipPatRec_prev.ship_geo.Yheight/2.*u.m)
fM = ROOT.genfit.FieldManager.getInstance()
fM.init(bfield)
 
geoMat =  ROOT.genfit.TGeoMaterialInterface()
ROOT.genfit.MaterialEffects.getInstance().init(geoMat)


fn=ROOT.TFile(outFile,'update')
sTree     = fn.cbmsim
fout=outFile

if sTree.GetBranch("FitTracks_PR"):
  print "remove RECO branches and rerun reconstruction"
  fn.Close()
  f=ROOT.TFile(fout,'update')
  sTree=f.cbsim
  sTree.SetBranchStatus("FitTracks_PR",0)
  sTree.SetBranchStatus("SmearedHits",0)
  sTree.SetBranchStatus("Particles",0)
  sTree.SetBranchStatus("fitTrack2MC_PR",0)
  sTree.SetBranchStatus("EcalClusters",0)       
  rawFile = fout.replace("_patrec.root","_raw.root")
  recf = ROOT.TFile(rawFile,"recreate")
  newTree = sTree.CloneTree(0)
  for n in range(sTree.GetEntries()):
      sTree.GetEntry(n)
      rc = newTree.Fill()
  sTree.Clear()
  newTree.AutoSave()
  f.Close() 
  recf.Close() 
  os.system('cp '+rawFile +' '+fout)
  fn = ROOT.TFile(fout,'update')
  sTree     = fn.cbmsim   
  
if sTree.GetBranch("GeoTracks"): sTree.SetBranchStatus("GeoTracks",0)

nEvents   = min(sTree.GetEntries(),nEvents)

fPartArray_PR     = ROOT.TClonesArray("TParticle") 
fGenFitArray_PR   = ROOT.TClonesArray("genfit::Track") 
fGenFitArray_PR.BypassStreamer(ROOT.kFALSE)
fitTrack2MC_PR = ROOT.std.vector('int')()
SmearedHits    = ROOT.TClonesArray("TVectorD")  

Particles_PR      = sTree.Branch("Particles_PR",  fPartArray_PR,32000,-1) 
SHbranch       = sTree.Branch("SmearedHits",SmearedHits,32000,-1)
fitTracks_PR      = sTree.Branch("FitTracks_PR",  fGenFitArray_PR,32000,-1) 
mcLink_PR      = sTree.Branch("fitTrack2MC_PR",fitTrack2MC_PR,32000,-1)
 
if shipPatRec_prev.debug==1:
  print "Straw tracker geometry parameters (cm)"
  print "--------------------------------------"
  print "Strawlength            :",2*shipPatRec_prev.ship_geo.strawtubes.StrawLength
  print "Inner straw diameter   :",shipPatRec_prev.ship_geo.strawtubes.InnerStrawDiameter
  print "Straw wall thickness   :",shipPatRec_prev.ship_geo.strawtubes.WallThickness 
  print "Outer straw diameter   :",shipPatRec_prev.ship_geo.strawtubes.OuterStrawDiameter
  print "Wire thickness         :",shipPatRec_prev.ship_geo.strawtubes.WireThickness
  print "Straw pitch            :",shipPatRec_prev.ship_geo.strawtubes.StrawPitch
  print "z-offset between layers:",shipPatRec_prev.ship_geo.strawtubes.DeltazLayer
  print "z-offset between planes:",shipPatRec_prev.ship_geo.strawtubes.DeltazPlane
  print "Straws per layer       :",shipPatRec_prev.ship_geo.strawtubes.StrawsPerLayer
  print "z-offset between planes:",shipPatRec_prev.ship_geo.strawtubes.DeltazPlane
  print "z-offset between views :",shipPatRec_prev.ship_geo.strawtubes.DeltazView

shipPatRec_prev.initialize(fgeo)
     
def EventLoop(SmearedHits):
 #loop over events
 for n in range(nEvents):
  fittedtrackids=[]
  SmearedHits.Delete()
  fGenFitArray_PR.Delete()
  fitTrack2MC_PR.clear()
  fPartArray_PR.Delete()
  
  rc = sTree.GetEvent(n)    
  
  if shipPatRec_prev.monitor==True: 
     shipPatRec_prev.ReconstructibleMCTracks=shipPatRec_prev.getReconstructibleTracks(n,sTree,sGeo)
     if len(shipPatRec_prev.ReconstructibleMCTracks)!=shipPatRec_prev.reconstructiblerequired : 
        if shipPatRec_prev.debug==1: print "Number of reconstructible tracks =",len(shipPatRec_prev.ReconstructibleMCTracks),"but number of reconstructible required=",shipPatRec_prev.reconstructiblerequired,". Rejecting event."
        continue

     if shipPatRec_prev.debug==1: print "Reconstructible track ids",shipPatRec_prev.ReconstructibleMCTracks
     
     
  #n = current event number, False=wire endpoints, True=MC truth
    
  SmearedHits  = shipPatRec_prev.SmearHits(n,sTree,modules,SmearedHits,shipPatRec_prev.ReconstructibleMCTracks)  

  fittedtrackids=shipPatRec_prev.execute(n,SmearedHits,sTree,shipPatRec_prev.ReconstructibleMCTracks)
  if fittedtrackids:
     tracknbr=0
     for ids in fittedtrackids:
	nTrack   = fGenFitArray_PR.GetEntries()
        fGenFitArray_PR[nTrack] = shipPatRec_prev.theTracks[tracknbr]
        fitTrack2MC_PR.push_back(ids) 
	tracknbr+=1  
  
  Particles_PR.Fill()
  fitTracks_PR.Fill()
  mcLink_PR.Fill()    
  SHbranch.Fill()  
    
    
 if shipPatRec_prev.debug==1: 
   print shipPatRec_prev.falsenegative,"matched tracks with wrong negative charge from deflection."
   print shipPatRec_prev.falsepositive,"matched tracks with wrong positive charge from deflection."
   print shipPatRec_prev.morethan500,"events with more than 500 hits."  
   print shipPatRec_prev.morethan100tracks,"events with more than 100 tracks." 
  
 return   
            
if shipPatRec_prev.debug==1:
  if shipPatRec_prev.threeprong==1:
    debugrootfile = ROOT.TFile(str(shipPatRec_prev.reconstructiblerequired)+"track-debug-mumunu-"+str(nEvents)+".root","RECREATE")   
  else:  
    debugrootfile = ROOT.TFile(str(shipPatRec_prev.reconstructiblerequired)+"track-debug-"+str(nEvents)+".root","RECREATE")   
        
EventLoop(SmearedHits)

#1/0
shipPatRec_prev.h['pinvvstruepinv'].Draw('box')
scale=1.
if shipPatRec_prev.h['fracsame12'].Integral() <>0 : scale=1/shipPatRec_prev.h['fracsame12'].Integral()
shipPatRec_prev.h['fracsame12'].Scale(scale)
scale=1.
if shipPatRec_prev.h['fracsame12-y'].Integral() <>0 : scale=1/shipPatRec_prev.h['fracsame12-y'].Integral()
shipPatRec_prev.h['fracsame12-y'].Scale(scale)
scale=1.
if shipPatRec_prev.h['fracsame12-stereo'].Integral() <>0 : scale=1/shipPatRec_prev.h['fracsame12-stereo'].Integral()
shipPatRec_prev.h['fracsame12-stereo'].Scale(scale)
scale=1.
if shipPatRec_prev.h['fracsame34'].Integral() <>0 : scale=1/shipPatRec_prev.h['fracsame34'].Integral()
shipPatRec_prev.h['fracsame34'].Scale(scale)
scale=1.
if shipPatRec_prev.h['fracsame34-y'].Integral() <>0 : scale=1/shipPatRec_prev.h['fracsame34-y'].Integral()
shipPatRec_prev.h['fracsame34-y'].Scale(scale)
scale=1.
if shipPatRec_prev.h['fracsame34-stereo'].Integral() <>0 : scale=1/shipPatRec_prev.h['fracsame34-stereo'].Integral()
shipPatRec_prev.h['fracsame34-stereo'].Scale(scale)

scale=1.

if shipPatRec_prev.monitor==1: 
  shipPatRec_prev.totalafterpatrec=shipPatRec_prev.totalafterpatrec/(shipPatRec_prev.reconstructiblerequired**2)
  shipPatRec_prev.totalaftermatching=shipPatRec_prev.totalaftermatching/shipPatRec_prev.reconstructiblerequired
  
rc=shipPatRec_prev.h['eventspassed'].SetBinContent(1,shipPatRec_prev.reconstructibleevents)
rc=shipPatRec_prev.h['eventspassed'].SetBinContent(2,shipPatRec_prev.reconstructiblehorizontalidsfound12)
rc=shipPatRec_prev.h['eventspassed'].SetBinContent(3,shipPatRec_prev.reconstructiblestereoidsfound12)
rc=shipPatRec_prev.h['eventspassed'].SetBinContent(4,shipPatRec_prev.reconstructibleidsfound12)
rc=shipPatRec_prev.h['eventspassed'].SetBinContent(5,shipPatRec_prev.reconstructiblehorizontalidsfound34)
rc=shipPatRec_prev.h['eventspassed'].SetBinContent(6,shipPatRec_prev.reconstructiblestereoidsfound34)
rc=shipPatRec_prev.h['eventspassed'].SetBinContent(7,shipPatRec_prev.reconstructibleidsfound34)
rc=shipPatRec_prev.h['eventspassed'].SetBinContent(8,shipPatRec_prev.totalafterpatrec)
rc=shipPatRec_prev.h['eventspassed'].SetBinContent(9,shipPatRec_prev.totalaftermatching)

sTree.Write()

if shipPatRec_prev.threeprong==1:
  shipPatRec_prev.ut.writeHists(shipPatRec_prev.h,"patrec-"+str(shipPatRec_prev.reconstructiblerequired)+"track-mumunu-"+str(nEvents)+".root")
else:
  shipPatRec_prev.ut.writeHists(shipPatRec_prev.h,"patrec-"+str(shipPatRec_prev.reconstructiblerequired)+"track-"+str(nEvents)+".root")
