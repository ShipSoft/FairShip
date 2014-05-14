import ROOT,ShipGeo
import shipunit as u

def configure(run):
# -----Create media-------------------------------------------------
 run.SetMaterials("media.geo")  # Materials
# ------------------------------------------------------------------------
  
# -----Create geometry----------------------------------------------
 cave= ROOT.ShipCave("CAVE")
 cave.SetGeometryFileName("cave.geo")
 run.AddModule(cave)

 TargetStation = ROOT.ShipTargetStation("TargetStation",ShipGeo.target.length,ShipGeo.hadronAbsorber.length,
                                                        ShipGeo.target.z,ShipGeo.hadronAbsorber.z)
 run.AddModule(TargetStation)
 MuonShield = ROOT.ShipMuonShield("MuonShield",1)
 run.AddModule(MuonShield)

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

