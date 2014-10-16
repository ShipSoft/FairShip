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

 Chamber = ROOT.ShipChamber("Chamber")  # vacuum tank
 Chamber.SetZpositions(ship_geo.Chamber1.z,ship_geo.Chamber2.z,ship_geo.Chamber3.z,ship_geo.Chamber4.z,ship_geo.Chamber5.z,ship_geo.Chamber6.z);
 Chamber.SetTublengths(ship_geo.chambers.Tub1length.z,ship_geo.chambers.Tub2length.z,ship_geo.chambers.Tub3length.z,ship_geo.chambers.Tub4length.z,ship_geo.chambers.Tub5length.z,ship_geo.chambers.Tub6length.z);
 Chamber.SetRmin(ship_geo.chambers.Rmin.z);
 Chamber.SetRmax(ship_geo.chambers.Rmax.z);
 run.AddModule(Chamber)


 Strawtubes = ROOT.strawtubes("Strawtubes", ROOT.kTRUE)   # for the moment, contains all tracking stations / planes
 Strawtubes.SetZpositions(ship_geo.vetoStation.z, ship_geo.TrackStation1.z, ship_geo.TrackStation2.z, ship_geo.TrackStation3.z, ship_geo.TrackStation4.z)
 Strawtubes.SetDeltazView(ship_geo.strawtubes.DeltazView.z);
 Strawtubes.SetStrawLength(ship_geo.strawtubes.StrawLength.z);
 Strawtubes.SetInnerStrawDiameter(ship_geo.strawtubes.InnerStrawDiameter.z);
 Strawtubes.SetOuterStrawDiameter(ship_geo.strawtubes.OuterStrawDiameter.z);
 Strawtubes.SetStrawPitch(ship_geo.strawtubes.StrawPitch.z);
 Strawtubes.SetDeltazLayer(ship_geo.strawtubes.DeltazLayer.z);
 Strawtubes.SetDeltazPlane(ship_geo.strawtubes.DeltazPlane.z);
 Strawtubes.SetStrawsPerLayer(ship_geo.strawtubes.StrawsPerLayer.z);
 Strawtubes.SetStereoAngle(ship_geo.strawtubes.ViewAngle.z);
 Strawtubes.SetWireThickness(ship_geo.strawtubes.WireThickness.z);
 Strawtubes.SetVacBox_x(ship_geo.strawtubes.VacBox_x.z);
 Strawtubes.SetVacBox_y(ship_geo.strawtubes.VacBox_y.z);

 run.AddModule(Strawtubes)

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
