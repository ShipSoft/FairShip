#!/usr/bin/env python

import ROOT
import rootUtils as ut

reconstructiblehorizontalidsfound12=0
reconstructiblestereoidsfound12=0
reconstructiblehorizontalidsfound34=0
reconstructiblestereoidsfound34=0
reconstructibleidsfound12=0
reconstructibleidsfound34=0

ReconstructibleMCTracks=[]

cheated = 0
debug = 0
fn = ''
geofile = ''
monitor = 0
printhelp = 0
reconstructiblerequired = 2
threeprong = 0

fGenFitArray = ROOT.TClonesArray("genfit::Track") 
fGenFitArray.BypassStreamer(ROOT.kFALSE)
fitTrack2MC  = ROOT.std.vector('int')()
#PatRecHits contain the hits on tracks found by the pattern recognition
PatRecHits  = ROOT.TClonesArray("TVectorD") 

random = ROOT.TRandom()
ROOT.gRandom.SetSeed(13)

fitter = ROOT.genfit.DAF()
if debug==1: fitter.setDebugLvl(1)

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
ut.bookHist(h,'nbrtracks','Number of tracks per reconstructible event',20,0.,20.)  
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
