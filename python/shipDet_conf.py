import ROOT,ShipGeo
import shipunit as u

def configure(run,muShieldDesign):
# -----Create media-------------------------------------------------
 run.SetMaterials("media.geo")  # Materials
# ------------------------------------------------------------------------
  
# -----Create geometry----------------------------------------------
 cave= ROOT.ShipCave("CAVE")
 cave.SetGeometryFileName("cave.geo")
 run.AddModule(cave)

 MuonShield = ROOT.ShipMuonShield("MuonShield",muShieldDesign)
 run.AddModule(MuonShield)
 zS = MuonShield.GetStartZ()

# overwrite z positions with new muon shield position:
 hadronAbsorberZ     =  zS  - ShipGeo.hadronAbsorber.length/2.
 targetZ             =  hadronAbsorberZ  - ShipGeo.hadronAbsorber.length/2. -  ShipGeo.target.length/2. 
 TargetStation = ROOT.ShipTargetStation("TargetStation",ShipGeo.target.length,ShipGeo.hadronAbsorber.length,
                                                        targetZ,hadronAbsorberZ)
 run.AddModule(TargetStation)

 magnet = ROOT.ShipMagnet("Magnet")
 run.AddModule(magnet)
 
 Chamber = ROOT.ShipChamber("Chamber")  # vacuum tank
 run.AddModule(Chamber)
 
 Veto = ROOT.veto("Veto", ROOT.kTRUE)   # for the moment, contains all tracking stations / planes
 Veto.SetZpositions(ShipGeo.vetoStation.z, ShipGeo.TrackStation1.z, ShipGeo.TrackStation2.z, ShipGeo.TrackStation3.z, ShipGeo.TrackStation4.z)

 run.AddModule(Veto)
 
 ecal = ROOT.ecal("Ecal", ROOT.kTRUE)
 run.AddModule(ecal)

 Muon = ROOT.muon("Muon", ROOT.kTRUE)
 run.AddModule(Muon)

#-----   Magnetic field   -------------------------------------------
    # Constant Field
 #fMagField = ROOT.ShipConstField()
 #fMagField.SetField(0., ShipGeo.Bfield.max ,0. )  
 #fMagField.SetFieldRegion(-250*u.cm, 250*u.cm,-250*u.cm, 250*u.cm, ShipGeo.Bfield.z-100*u.cm, ShipGeo.Bfield.z+100*u.cm)    
 #run.SetField(fMagField)
 fMagField = ROOT.ShipBellField("wilfried", ShipGeo.Bfield.max ,ShipGeo.Bfield.z )  
 run.SetField(fMagField)
