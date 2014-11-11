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
  MuonShield = ROOT.ShipMuonShield("MuonShield",ship_geo.muShieldDesign,"ShipMuonShield",ship_geo.muShield.z,ship_geo.muShield.dZ0,ship_geo.muShield.length) 
 elif ship_geo.muShieldDesign==2:
  MuonShield = ROOT.ShipMuonShield("MuonShield",ship_geo.muShieldDesign,"ShipMuonShield",ship_geo.muShield.z,ship_geo.muShield.dZ0,ship_geo.muShield.dZ1,\
               ship_geo.muShield.dZ2,ship_geo.muShield.dZ3,ship_geo.muShield.dZ4,ship_geo.muShield.dZ5,ship_geo.muShield.dZ6,ship_geo.muShield.LE) 
 elif ship_geo.muShieldDesign==3 or ship_geo.muShieldDesign==4 or ship_geo.muShieldDesign==5 :
  MuonShield = ROOT.ShipMuonShield("MuonShield",ship_geo.muShieldDesign,"ShipMuonShield",ship_geo.muShield.z,ship_geo.muShield.dZ0,ship_geo.muShield.dZ1,\
               ship_geo.muShield.dZ2,ship_geo.muShield.dZ3,ship_geo.muShield.dZ4,ship_geo.muShield.dZ5,ship_geo.muShield.dZ6,\
               ship_geo.muShield.dZ7,ship_geo.muShield.dZ8,ship_geo.muShield.dXgap,ship_geo.muShield.LE) 

 run.AddModule(MuonShield)

 TargetStation = ROOT.ShipTargetStation("TargetStation",ship_geo.target.length,ship_geo.hadronAbsorber.length,
                                                        ship_geo.target.z,ship_geo.hadronAbsorber.z,ship_geo.targetOpt,ship_geo.target.sl)
 run.AddModule(TargetStation)

 
 if ship_geo.strawDesign > 1 : magnet = ROOT.ShipMagnet("Magnet","SHiP Magnet",ship_geo.Bfield.z, 2)
 else: magnet = ROOT.ShipMagnet("Magnet","SHiP Magnet",ship_geo.Bfield.z)
 run.AddModule(magnet)
 
 # this is now included in veto.cxx
 #Chamber = ROOT.ShipChamber("Chamber")  # vacuum tank
 #run.AddModule(Chamber)
 
 Veto = ROOT.veto("Veto", ROOT.kTRUE)   # vacuum tank, liquid scintillator, simplistic tracking stations
 Veto.SetZpositions(ship_geo.vetoStation.z, ship_geo.TrackStation1.z, ship_geo.TrackStation2.z, \
                    ship_geo.TrackStation3.z, ship_geo.TrackStation4.z,ship_geo.strawDesign)
 Veto.SetTubZpositions(ship_geo.Chamber1.z,ship_geo.Chamber2.z,ship_geo.Chamber3.z,ship_geo.Chamber4.z,ship_geo.Chamber5.z,ship_geo.Chamber6.z);
 Veto.SetTublengths(ship_geo.chambers.Tub1length.z,ship_geo.chambers.Tub2length.z,ship_geo.chambers.Tub3length.z, \
                    ship_geo.chambers.Tub4length.z,ship_geo.chambers.Tub5length.z,ship_geo.chambers.Tub6length.z);
 Veto.SetRminRmax(ship_geo.chambers.Rmin.z,ship_geo.chambers.Rmax.z);
 Veto.SetVminVmax(ship_geo.scintillator.Rmin.z,ship_geo.scintillator.Rmax.z);
 run.AddModule(Veto)

 if ship_geo.muShieldDesign==5:
  taumagneticspectrometer = ROOT.ShipTAUMagneticSpectrometer("TAUMagneticSpectrometer", ship_geo.tauMS.zLS, ship_geo.tauMS.FeL, ship_geo.tauMS.AirL,
                                                            ship_geo.tauMS.SpectroL,ship_geo.tauMS.GapV, ship_geo.tauMS.DGap, ship_geo.tauMS.MGap, ship_geo.tauMS.mf)
  run.AddModule(taumagneticspectrometer)

  goliath = ROOT.ShipGoliath("Goliath", ship_geo.Goliath.zC, ship_geo.Goliath.LS, ship_geo.Goliath.TS, ship_geo.Goliath.GapTS)
  run.AddModule(goliath)

 #for now Rpc are scintillator planes
  Rpc = ROOT.ShipRpc("Rpc",ship_geo.Rpc.zRpcL, ship_geo.Rpc.zDriftL, ship_geo.Rpc.DriftL, ship_geo.Rpc.IronL, ship_geo.Rpc.ScintL, ship_geo.Rpc.MiddleG, ROOT.kTRUE)
  run.AddModule(Rpc)

 if ship_geo.strawDesign > 1 :
  Strawtubes = ROOT.strawtubes("Strawtubes", ROOT.kTRUE)    
  Strawtubes.SetZpositions(ship_geo.vetoStation.z, ship_geo.TrackStation1.z, ship_geo.TrackStation2.z, ship_geo.TrackStation3.z, ship_geo.TrackStation4.z)
  Strawtubes.SetDeltazView(ship_geo.strawtubes.DeltazView.z)
  Strawtubes.SetStrawLength(ship_geo.strawtubes.StrawLength.z)
  Strawtubes.SetInnerStrawDiameter(ship_geo.strawtubes.InnerStrawDiameter.z)
  Strawtubes.SetOuterStrawDiameter(ship_geo.strawtubes.OuterStrawDiameter.z)
  Strawtubes.SetStrawPitch(ship_geo.strawtubes.StrawPitch.z)
  Strawtubes.SetDeltazLayer(ship_geo.strawtubes.DeltazLayer.z)
  Strawtubes.SetDeltazPlane(ship_geo.strawtubes.DeltazPlane.z)
  Strawtubes.SetStrawsPerLayer(ship_geo.strawtubes.StrawsPerLayer.z)
  Strawtubes.SetStereoAngle(ship_geo.strawtubes.ViewAngle.z)
  Strawtubes.SetWireThickness(ship_geo.strawtubes.WireThickness.z)
  Strawtubes.SetVacBox_x(ship_geo.strawtubes.VacBox_x.z)
  Strawtubes.SetVacBox_y(ship_geo.strawtubes.VacBox_y.z)
  run.AddModule(Strawtubes) 

 if ship_geo.strawDesign == 4: ecal = ROOT.ecal("Ecal", ROOT.kTRUE, "ecal_ellipse6x12m2.geo")
 else:                         ecal = ROOT.ecal("Ecal", ROOT.kTRUE, "ecal.geo")
 run.AddModule(ecal)

 Muon = ROOT.muon("Muon", ROOT.kTRUE)
 Muon.SetZStationPositions(ship_geo.MuonStation0.z, ship_geo.MuonStation1.z,ship_geo.MuonStation2.z,ship_geo.MuonStation3.z)
 Muon.SetZFilterPositions(ship_geo.MuonFilter0.z, ship_geo.MuonFilter1.z,ship_geo.MuonFilter2.z)
 Muon.SetXMax(ship_geo.MuonXMax.x)
 Muon.SetYMax(ship_geo.MuonYMax.y)
 Muon.SetActiveThickness(ship_geo.ActiveThickness.z)
 Muon.SetFilterThickness(ship_geo.FilterThickness.z)
 run.AddModule(Muon)

#-----   Magnetic field   -------------------------------------------
    # Constant Field
 #fMagField = ROOT.ShipConstField()
 #fMagField.SetField(0., ship_geo.Bfield.max ,0. )  
 #fMagField.SetFieldRegion(-250*u.cm, 250*u.cm,-250*u.cm, 250*u.cm, ship_geo.Bfield.z-100*u.cm, ship_geo.Bfield.z+100*u.cm)    
 #run.SetField(fMagField)
 if ship_geo.strawDesign == 4: fMagField = ROOT.ShipBellField("wilfried", ship_geo.Bfield.max ,ship_geo.Bfield.z,2 )  
 else :                        fMagField = ROOT.ShipBellField("wilfried", ship_geo.Bfield.max ,ship_geo.Bfield.z,1 )  
 run.SetField(fMagField)

# return list of detector elements
 detElements = {}
 for x in run.GetListOfModules(): detElements[x.GetName()]=x
 return detElements
