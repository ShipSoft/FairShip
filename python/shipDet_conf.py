import ROOT
import shipunit as u

def configure(run,muShieldLength,targetHadronAbsorber,decayVolumeLength):
# -----Create media-------------------------------------------------
 run.SetMaterials("media.geo")  # Materials
# ------------------------------------------------------------------------
  
# -----Create geometry----------------------------------------------
 cave= ROOT.ShipCave("CAVE")
 cave.SetGeometryFileName("cave.geo")
 run.AddModule(cave)

 TargetStation = ROOT.ShipTargetStation("TargetStation",muShieldLength)
 run.AddModule(TargetStation)
 MuonShield = ROOT.ShipMuonShield("MuonShield",1)
 run.AddModule(MuonShield)

 magnet = ROOT.ShipMagnet("Magnet")
 run.AddModule(magnet)
 
 Chamber = ROOT.ShipChamber("Chamber")
 run.AddModule(Chamber)

 Veto = ROOT.veto("Veto", ROOT.kTRUE)
 run.AddModule(Veto)
 
 ecal = ROOT.ecal("Ecal", ROOT.kTRUE)
 run.AddModule(ecal)

 Muon = ROOT.muon("Muon", ROOT.kTRUE)
 run.AddModule(Muon)

#-----   Magnetic field   -------------------------------------------
    # Constant Field
 fMagField = ROOT.ShipConstField()
 fMagField.SetField(0., 2. ,0. ) # values are in kG
 fMagField.SetFieldRegion(-160*u.cm, 160*u.cm,-160*u.cm, 160*u.cm, 1940*u.cm, 125*u.cm); # values are in cm  (xmin,xmax,ymin,ymax,zmin,zmax)
 run.SetField(fMagField)

