from __future__ import print_function
# setenv LD_LIBRARY_PATH ${LD_LIBRARY_PATH}:/media/ShipSoft/genfit-build/lib
#-----prepare python exit-----------------------------------------------
def pyExit():
 global fitter
 del fitter
import atexit
atexit.register(pyExit)

import ROOT
import shipunit as u
import ShipGeo

ROOT.gSystem.Load("libgenfit2.so")
geoMat =  ROOT.genfit.TGeoMaterialInterface()

PDG = ROOT.TDatabasePDG.Instance()

ROOT.gRandom.SetSeed(14)
# init MeasurementCreator
measurementCreator = ROOT.genfit.MeasurementCreator() 
# init geometry and mag. field
tgeom = ROOT.TGeoManager("Geometry", "Geane geometry")
tgeom.Import("/media/ShipSoft/genfit-build/bin/genfitGeom.root")
#
bfield = ROOT.genfit.ConstField(0.,0., 15.)  # 15 kGauss
ROOT.genfit.FieldManager.getInstance().init(bfield)
geoMat =  ROOT.genfit.TGeoMaterialInterface()
ROOT.genfit.MaterialEffects.getInstance().init(geoMat)
# init event display
display = ROOT.genfit.EventDisplay.getInstance()

# init fitter
fitter = ROOT.genfit.KalmanFitterRefTrack()
# main loop
for iEvent in range(0, 100):
 # true start values
 pos = ROOT.TVector3(0, 0, 0)
 mom = ROOT.TVector3(1.,0,0)
 mom.SetPhi(ROOT.gRandom.Uniform(0.,2*ROOT.TMath.Pi()))
 mom.SetTheta(ROOT.gRandom.Uniform(0.4*ROOT.TMath.Pi(),0.6*ROOT.TMath.Pi()))
 mom.SetMag(ROOT.gRandom.Uniform(0.2, 1.))
# helix track model
 pdg = 13 # particle pdg code
 charge = PDG.GetParticle(pdg).Charge()/(3.)
 helix = ROOT.genfit.HelixTrackModel(pos, mom, charge)
 ROOT.SetOwnership( helix, False )
 measurementCreator.setTrackModel(helix)
 nMeasurements = int(ROOT.gRandom.Uniform(5, 15))
# smeared start values
 smearPosMom = True # init the Reps with smeared pos and mom
 posSmear = 0.1 # cm
 momSmear = 3. /180.*ROOT.TMath.Pi() # rad
 momMagSmear = 0.1 # relative
 posM = ROOT.TVector3(pos)
 momM = ROOT.TVector3(mom)
 if smearPosMom:
  posM.SetX(ROOT.gRandom.Gaus(posM.X(),posSmear))
  posM.SetY(ROOT.gRandom.Gaus(posM.Y(),posSmear))
  posM.SetZ(ROOT.gRandom.Gaus(posM.Z(),posSmear))
  momM.SetPhi(ROOT.gRandom.Gaus(mom.Phi(),momSmear))
  momM.SetTheta(ROOT.gRandom.Gaus(mom.Theta(),momSmear))
  momM.SetMag(ROOT.gRandom.Gaus(mom.Mag(), momMagSmear*mom.Mag()))
# approximate covariance
 covM = ROOT.TMatrixDSym(6)
 resolution = 0.01
 for  i in range(3):   covM[i][i] = resolution*resolution
 for  i in range(3,6): covM[i][i] = ROOT.TMath.pow(resolution / nMeasurements / ROOT.TMath.sqrt(3), 2)
# trackrep
 rep = ROOT.genfit.RKTrackRep(pdg)
# smeared start state
 stateSmeared = ROOT.genfit.MeasuredStateOnPlane(rep)
 rep.setPosMomCov(stateSmeared, posM, momM, covM)
# create track
 seedState = ROOT.TVectorD(6)
 seedCov   = ROOT.TMatrixDSym(6)
 rep.get6DStateCov(stateSmeared, seedState, seedCov)
 fitTrack = ROOT.genfit.Track(rep, seedState, seedCov)
# create random measurement types
 eMeasurementType = ROOT.genfit.eMeasurementType
# measurementTypes = ROOT.std.vector(eMeasurementType)
 measurementTypes = ROOT.std.vector(int)()

 for i in range( nMeasurements ): 
  measurementTypes.push_back(int(ROOT.gRandom.Uniform(8)))
# create smeared measurements and add to track
  try:
   for  i in range( measurementTypes.size() ):
    measurements = measurementCreator.create(measurementTypes[i], i*5.)
    fitTrack.insertPoint(ROOT.genfit.TrackPoint(measurements,fitTrack))
  except:
   print("Exception, next track", e.what())

#check
  if not fitTrack.checkConsistency():
   print('Problem with track before fit, not consistent',fitTrack)
# do the fit
  fitter.processTrack(fitTrack)
#check
  if not fitTrack.checkConsistency():
   print('Problem with track after fit, not consistent',fitTrack)
  if (iEvent < 1000):
# add track to event display
   display.addEvent(fitTrack)

# end loop over events
# open event display
display.open() 

# tests
WireMeasurement = ROOT.genfit.WireMeasurement
aWireMeasurement = WireMeasurement()
