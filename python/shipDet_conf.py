#!/usr/bin/env python
# -*- coding: latin-1 -*-
import ROOT
import shipunit as u

def configure(run,ship_geo):
# -----Create media-------------------------------------------------
 run.SetMaterials("media.geo")  # Materials
# ------------------------------------------------------------------------
  
# -----Create geometry----------------------------------------------
 cave= ROOT.ShipCave("CAVE")
 cave.SetGeometryFileName("cave.geo")
 run.AddModule(cave)

 if ship_geo.muShieldDesign==1:
  MuonShield = ROOT.ShipMuonShield("MuonShield",ship_geo.muShieldDesign,"ShipMuonShield",ship_geo.muShield.z,ship_geo.muShield.length) 
 elif ship_geo.muShieldDesign==2:
  MuonShield = ROOT.ShipMuonShield("MuonShield",ship_geo.muShieldDesign,"ShipMuonShield",ship_geo.muShield.z,ship_geo.muShield.dZ1,\
               ship_geo.muShield.dZ2,ship_geo.muShield.dZ3,ship_geo.muShield.dZ4,ship_geo.muShield.dZ5,ship_geo.muShield.dZ6,ship_geo.muShield.LE) 
 run.AddModule(MuonShield)

 TargetStation = ROOT.ShipTargetStation("TargetStation",ship_geo.target.length,ship_geo.hadronAbsorber.length,
                                                        ship_geo.target.z,ship_geo.hadronAbsorber.z,ship_geo.targetOpt,ship_geo.target.sl)
 run.AddModule(TargetStation)

 magnet = ROOT.ShipMagnet("Magnet")
 run.AddModule(magnet)

 magneticspectrometer = ROOT.ShipMagneticSpectrometer("MagneticSpectrometer")
 run.AddModule(magneticspectrometer)

 goliath = ROOT.ShipGoliath("Goliath")
 run.AddModule(goliath)

 Chamber = ROOT.ShipChamber("Chamber")  # vacuum tank
 run.AddModule(Chamber)
 
 Veto = ROOT.veto("Veto", ROOT.kTRUE)   # for the moment, contains all tracking stations / planes
 Veto.SetZpositions(ship_geo.vetoStation.z, ship_geo.TrackStation1.z, ship_geo.TrackStation2.z, ship_geo.TrackStation3.z, ship_geo.TrackStation4.z)
 run.AddModule(Veto)
 
 ecal = ROOT.ecal("Ecal", ROOT.kTRUE, "ecal.geo")
 run.AddModule(ecal)

 Muon = ROOT.muon("Muon", ROOT.kTRUE)
 run.AddModule(Muon)

#-----   Magnetic field   -------------------------------------------
    # Constant Field
 #fMagField = ROOT.ShipConstField()
 #fMagField.SetField(0., ship_geo.Bfield.max ,0. )  
 #fMagField.SetFieldRegion(-250*u.cm, 250*u.cm,-250*u.cm, 250*u.cm, ship_geo.Bfield.z-100*u.cm, ship_geo.Bfield.z+100*u.cm)    
 #run.SetField(fMagField)
 fMagField = ROOT.ShipBellField("wilfried", ship_geo.Bfield.max ,ship_geo.Bfield.z )  
 run.SetField(fMagField)
