#!/usr/bin/env python
#first version of digitization & pattern recognition
#for documentation, see CERN-SHiP-NOTE-2015-002, https://cds.cern.ch/record/2005715/files/main.pdf
#17-04-2015 comments to EvH

import shipPatRec 
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

shipPatRec.cheated=bool(options.chtd)
shipPatRec.debug = int(options.dbg)
inputFile = options.input
shipPatRec.geoFile = options.geometry
shipPatRec.monitor=bool(options.mntr)
shipPatRec.printhelp=bool(options.helptext)
shipPatRec.reconstructiblerequired = int(options.rectracks)
shipPatRec.threeprong = int(options.tp)
saveDisk = options.saveDisk

if (shipPatRec.printhelp==True or len(sys.argv)==1):
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

if not shipPatRec.geoFile:
 tmp = inputFile.replace('ship.','geofile_full.')
 shipPatRec.geoFile = tmp.replace('_rec','')

run = ROOT.FairRunSim()
shipDet_conf.configure(run,shipPatRec.ship_geo)
modules = {}
for x in run.GetListOfModules(): modules[x.GetName()]=x

fgeo   = ROOT.TFile(shipPatRec.geoFile)
sGeo   = fgeo.FAIRGeom


bfield = ROOT.genfit.BellField(shipPatRec.ship_geo.Bfield.max ,shipPatRec.ship_geo.Bfield.z,2,shipPatRec.ship_geo.Yheight/2.*u.m)
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
 
if shipPatRec.debug==1:
  print "Straw tracker geometry parameters (cm)"
  print "--------------------------------------"
  print "Strawlength            :",2*shipPatRec.ship_geo.strawtubes.StrawLength
  print "Inner straw diameter   :",shipPatRec.ship_geo.strawtubes.InnerStrawDiameter
  print "Straw wall thickness   :",shipPatRec.ship_geo.strawtubes.WallThickness 
  print "Outer straw diameter   :",shipPatRec.ship_geo.strawtubes.OuterStrawDiameter
  print "Wire thickness         :",shipPatRec.ship_geo.strawtubes.WireThickness
  print "Straw pitch            :",shipPatRec.ship_geo.strawtubes.StrawPitch
  print "z-offset between layers:",shipPatRec.ship_geo.strawtubes.DeltazLayer
  print "z-offset between planes:",shipPatRec.ship_geo.strawtubes.DeltazPlane
  print "Straws per layer       :",shipPatRec.ship_geo.strawtubes.StrawsPerLayer
  print "z-offset between planes:",shipPatRec.ship_geo.strawtubes.DeltazPlane
  print "z-offset between views :",shipPatRec.ship_geo.strawtubes.DeltazView

shipPatRec.initialize(fgeo)
     
def EventLoop(SmearedHits):
 #loop over events
 for n in range(nEvents):
  fittedtrackids=[]
  SmearedHits.Delete()
  fGenFitArray_PR.Delete()
  fitTrack2MC_PR.clear()
  fPartArray_PR.Delete()
  
  rc = sTree.GetEvent(n)    
  
  if shipPatRec.monitor==True: 
     shipPatRec.ReconstructibleMCTracks=shipPatRec.getReconstructibleTracks(n,sTree,sGeo)
     if len(shipPatRec.ReconstructibleMCTracks)!=shipPatRec.reconstructiblerequired : 
        if shipPatRec.debug==1: print "Number of reconstructible tracks =",len(shipPatRec.ReconstructibleMCTracks),"but number of reconstructible required=",shipPatRec.reconstructiblerequired,". Rejecting event."
        continue

     if shipPatRec.debug==1: print "Reconstructible track ids",shipPatRec.ReconstructibleMCTracks
     
     
  #n = current event number, False=wire endpoints, True=MC truth
    
  SmearedHits  = shipPatRec.SmearHits(n,sTree,modules,SmearedHits,shipPatRec.ReconstructibleMCTracks)  

  fittedtrackids=shipPatRec.execute(n,SmearedHits,sTree,shipPatRec.ReconstructibleMCTracks)
  if fittedtrackids:
     tracknbr=0
     for ids in fittedtrackids:
	nTrack   = fGenFitArray_PR.GetEntries()
        fGenFitArray_PR[nTrack] = shipPatRec.theTracks[tracknbr]
        fitTrack2MC_PR.push_back(ids) 
	tracknbr+=1  
  
  Particles_PR.Fill()
  fitTracks_PR.Fill()
  mcLink_PR.Fill()    
  SHbranch.Fill()  
    
    
 if shipPatRec.debug==1: 
   print shipPatRec.falsenegative,"matched tracks with wrong negative charge from deflection."
   print shipPatRec.falsepositive,"matched tracks with wrong positive charge from deflection."
   print shipPatRec.morethan500,"events with more than 500 hits."  
   print shipPatRec.morethan100tracks,"events with more than 100 tracks." 
  
 return   
            
if shipPatRec.debug==1:
  if shipPatRec.threeprong==1:
    debugrootfile = ROOT.TFile(str(shipPatRec.reconstructiblerequired)+"track-debug-mumunu-"+str(nEvents)+".root","RECREATE")   
  else:  
    debugrootfile = ROOT.TFile(str(shipPatRec.reconstructiblerequired)+"track-debug-"+str(nEvents)+".root","RECREATE")   
        
EventLoop(SmearedHits)

#1/0
shipPatRec.h['pinvvstruepinv'].Draw('box')
scale=1.
if shipPatRec.h['fracsame12'].Integral() <>0 : scale=1/shipPatRec.h['fracsame12'].Integral()
shipPatRec.h['fracsame12'].Scale(scale)
scale=1.
if shipPatRec.h['fracsame12-y'].Integral() <>0 : scale=1/shipPatRec.h['fracsame12-y'].Integral()
shipPatRec.h['fracsame12-y'].Scale(scale)
scale=1.
if shipPatRec.h['fracsame12-stereo'].Integral() <>0 : scale=1/shipPatRec.h['fracsame12-stereo'].Integral()
shipPatRec.h['fracsame12-stereo'].Scale(scale)
scale=1.
if shipPatRec.h['fracsame34'].Integral() <>0 : scale=1/shipPatRec.h['fracsame34'].Integral()
shipPatRec.h['fracsame34'].Scale(scale)
scale=1.
if shipPatRec.h['fracsame34-y'].Integral() <>0 : scale=1/shipPatRec.h['fracsame34-y'].Integral()
shipPatRec.h['fracsame34-y'].Scale(scale)
scale=1.
if shipPatRec.h['fracsame34-stereo'].Integral() <>0 : scale=1/shipPatRec.h['fracsame34-stereo'].Integral()
shipPatRec.h['fracsame34-stereo'].Scale(scale)

scale=1.

if shipPatRec.monitor==1: 
  shipPatRec.totalafterpatrec=shipPatRec.totalafterpatrec/(shipPatRec.reconstructiblerequired**2)
  shipPatRec.totalaftermatching=shipPatRec.totalaftermatching/shipPatRec.reconstructiblerequired
  
rc=shipPatRec.h['eventspassed'].SetBinContent(1,shipPatRec.reconstructibleevents)
rc=shipPatRec.h['eventspassed'].SetBinContent(2,shipPatRec.reconstructiblehorizontalidsfound12)
rc=shipPatRec.h['eventspassed'].SetBinContent(3,shipPatRec.reconstructiblestereoidsfound12)
rc=shipPatRec.h['eventspassed'].SetBinContent(4,shipPatRec.reconstructibleidsfound12)
rc=shipPatRec.h['eventspassed'].SetBinContent(5,shipPatRec.reconstructiblehorizontalidsfound34)
rc=shipPatRec.h['eventspassed'].SetBinContent(6,shipPatRec.reconstructiblestereoidsfound34)
rc=shipPatRec.h['eventspassed'].SetBinContent(7,shipPatRec.reconstructibleidsfound34)
rc=shipPatRec.h['eventspassed'].SetBinContent(8,shipPatRec.totalafterpatrec)
rc=shipPatRec.h['eventspassed'].SetBinContent(9,shipPatRec.totalaftermatching)

sTree.Write()

if shipPatRec.threeprong==1:
  shipPatRec.ut.writeHists(shipPatRec.h,"patrec-"+str(shipPatRec.reconstructiblerequired)+"track-mumunu-"+str(nEvents)+".root")
else:
  shipPatRec.ut.writeHists(shipPatRec.h,"patrec-"+str(shipPatRec.reconstructiblerequired)+"track-"+str(nEvents)+".root")
