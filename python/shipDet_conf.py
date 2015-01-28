#!/usr/bin/env python
# -*- coding: latin-1 -*-
import ROOT,os
import shipunit as u
def posHcal(z): 
 HcalZSize = 0
 sz = "hcalz"+str(z)+".geo"
 floc = os.environ["FAIRSHIP"]+"/geometry"
 if not sz in os.listdir(floc):
  f =  open(floc+"/hcal.geo",'r')
  fn = open(floc+"/"+sz,'w')
  for l in f.readlines():
   if not l.find("ZPos")<0:
      l ="ZPos="+str(z)+ "	#Position of Hcal  center	[cm]\n"
   fn.write(l)
   if not l.find("HcalZSize")<0:
     HcalZSize = float(l[len('HcalZSize')+1:].split('#')[0]) 
  f.close()
  fn.close()  
 hcal=ROOT.hcal("Hcal", ROOT.kTRUE, sz)
 return hcal,HcalZSize
def posEcal(z):
 EcalZSize = 0
 sz = "ecal_ellipse6x12m2z"+str(z)+".geo"
 floc = os.environ["FAIRSHIP"]+"/geometry"
 if not sz in os.listdir(floc):
  f =  open(floc+"/ecal_ellipse6x12m2.geo",'r')
  fn = open(floc+"/"+sz,'w')
  for l in f.readlines():
   if not l.find("ZPos")<0:
      l ="ZPos="+str(z)+ "	#Position of Ecal start		[cm]\n"
   fn.write(l)
   if not l.find("EcalZSize")<0:
     EcalZSize = float(l[len('EcalZSize')+1:].split('#')[0]) 
  f.close()
  fn.close()  
 ecal = ROOT.ecal("Ecal", ROOT.kTRUE, sz)
 return ecal,EcalZSize

def configure(run,ship_geo):
# -----Create media-------------------------------------------------
 run.SetMaterials("media.geo")  # Materials
# ------------------------------------------------------------------------
  
# -----Create geometry----------------------------------------------
 cave= ROOT.ShipCave("CAVE")
 cave.SetGeometryFileName("cave.geo")
 run.AddModule(cave)

 if ship_geo.muShieldDesign==1:
  MuonShield = ROOT.ShipMuonShield("MuonShield",ship_geo.muShieldDesign,"ShipMuonShield",ship_geo.muShield.z,ship_geo.muShield.dZ0,ship_geo.muShield.length,\
                                   ship_geo.muShield.LE) 
 elif ship_geo.muShieldDesign==2:
  MuonShield = ROOT.ShipMuonShield("MuonShield",ship_geo.muShieldDesign,"ShipMuonShield",ship_geo.muShield.z,ship_geo.muShield.dZ0,ship_geo.muShield.dZ1,\
               ship_geo.muShield.dZ2,ship_geo.muShield.dZ3,ship_geo.muShield.dZ4,ship_geo.muShield.dZ5,ship_geo.muShield.dZ6,ship_geo.muShield.LE) 
 elif ship_geo.muShieldDesign==3 or ship_geo.muShieldDesign==4 or ship_geo.muShieldDesign==5 :
  MuonShield = ROOT.ShipMuonShield("MuonShield",ship_geo.muShieldDesign,"ShipMuonShield",ship_geo.muShield.z,ship_geo.muShield.dZ0,ship_geo.muShield.dZ1,\
               ship_geo.muShield.dZ2,ship_geo.muShield.dZ3,ship_geo.muShield.dZ4,ship_geo.muShield.dZ5,ship_geo.muShield.dZ6,\
               ship_geo.muShield.dZ7,ship_geo.muShield.dZ8,ship_geo.muShield.dXgap,ship_geo.muShield.LE,ship_geo.Yheight*4./10.) 

 run.AddModule(MuonShield)

 TargetStation = ROOT.ShipTargetStation("TargetStation",ship_geo.target.length,ship_geo.hadronAbsorber.length,
                                                        ship_geo.target.z,ship_geo.hadronAbsorber.z,ship_geo.targetOpt,ship_geo.target.sl)
 if ship_geo.targetOpt>10:
  TargetStation.SetLayerPosMat(ship_geo.target.xy,ship_geo.target.L1,ship_geo.target.M1,ship_geo.target.L2,ship_geo.target.M2,\
  ship_geo.target.L3,ship_geo.target.M3,ship_geo.target.L4,ship_geo.target.M4,ship_geo.target.L5,ship_geo.target.M5,\
  ship_geo.target.L6,ship_geo.target.M6,ship_geo.target.L7,ship_geo.target.M7,ship_geo.target.L8,ship_geo.target.M8,\
  ship_geo.target.L9,ship_geo.target.M9,ship_geo.target.L10,ship_geo.target.M10,ship_geo.target.L11,ship_geo.target.M11,\
  ship_geo.target.L12,ship_geo.target.M12,ship_geo.target.L13,ship_geo.target.M13,ship_geo.target.L14,ship_geo.target.M14,\
  ship_geo.target.L15,ship_geo.target.M15,ship_geo.target.L16,ship_geo.target.M16,ship_geo.target.L17,ship_geo.target.M17)
 run.AddModule(TargetStation)

 
 if ship_geo.strawDesign > 1 : magnet = ROOT.ShipMagnet("Magnet","SHiP Magnet",ship_geo.Bfield.z, 2, ship_geo.Bfield.y)
 else: magnet = ROOT.ShipMagnet("Magnet","SHiP Magnet",ship_geo.Bfield.z)
 run.AddModule(magnet)
  
 Veto = ROOT.veto("Veto", ROOT.kTRUE)   # vacuum tank, liquid scintillator, simplistic tracking stations
 Veto.SetZpositions(ship_geo.vetoStation.z, ship_geo.TrackStation1.z, ship_geo.TrackStation2.z, \
                    ship_geo.TrackStation3.z, ship_geo.TrackStation4.z,ship_geo.strawDesign)
 Veto.SetTubZpositions(ship_geo.Chamber1.z,ship_geo.Chamber2.z,ship_geo.Chamber3.z,ship_geo.Chamber4.z,ship_geo.Chamber5.z,ship_geo.Chamber6.z);
 Veto.SetTublengths(ship_geo.chambers.Tub1length,ship_geo.chambers.Tub2length,ship_geo.chambers.Tub3length, \
                    ship_geo.chambers.Tub4length,ship_geo.chambers.Tub5length,ship_geo.chambers.Tub6length);
 Veto.SetRminRmax(ship_geo.chambers.Rmin,ship_geo.chambers.Rmax);
 Veto.SetVminVmax(ship_geo.scintillator.Rmin,ship_geo.scintillator.Rmax);
 Veto.SetB(ship_geo.Yheight/2.)
 run.AddModule(Veto)

 if ship_geo.muShieldDesign==5 or ship_geo.muShieldDesign==1:
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
  Strawtubes.SetDeltazView(ship_geo.strawtubes.DeltazView)
  Strawtubes.SetStrawLength(ship_geo.strawtubes.StrawLength)
  Strawtubes.SetInnerStrawDiameter(ship_geo.strawtubes.InnerStrawDiameter)
  Strawtubes.SetOuterStrawDiameter(ship_geo.strawtubes.OuterStrawDiameter)
  Strawtubes.SetStrawPitch(ship_geo.strawtubes.StrawPitch)
  Strawtubes.SetDeltazLayer(ship_geo.strawtubes.DeltazLayer)
  Strawtubes.SetDeltazPlane(ship_geo.strawtubes.DeltazPlane)
  Strawtubes.SetStrawsPerLayer(ship_geo.strawtubes.StrawsPerLayer)
  Strawtubes.SetStereoAngle(ship_geo.strawtubes.ViewAngle)
  Strawtubes.SetWireThickness(ship_geo.strawtubes.WireThickness)
  Strawtubes.SetVacBox_x(ship_geo.strawtubes.VacBox_x)
  Strawtubes.SetVacBox_y(ship_geo.strawtubes.VacBox_y)
  run.AddModule(Strawtubes) 

 if ship_geo.strawDesign == 4: 
  ecal,EcalZSize = posEcal(ship_geo.ecal.z)
 else:   ecal = ROOT.ecal("Ecal", ROOT.kTRUE, "ecal.geo")
 run.AddModule(ecal)

 if not ship_geo.HcalOption < 0:
  hcal,HcalZSize = posHcal(ship_geo.hcal.z)
  if abs(ship_geo.hcal.hcalSpace -  HcalZSize) > 1*u.cm:
    print 'mismatch between hcalsize in geo file and python configuration'
  run.AddModule(hcal)
 Muon = ROOT.muon("Muon", ROOT.kTRUE)
 Muon.SetZStationPositions(ship_geo.MuonStation0.z, ship_geo.MuonStation1.z,ship_geo.MuonStation2.z,ship_geo.MuonStation3.z)
 Muon.SetZFilterPositions(ship_geo.MuonFilter0.z, ship_geo.MuonFilter1.z,ship_geo.MuonFilter2.z)
 Muon.SetXMax(ship_geo.Muon.XMax)
 Muon.SetYMax(ship_geo.Muon.YMax)
 Muon.SetActiveThickness(ship_geo.Muon.ActiveThickness)
 Muon.SetFilterThickness(ship_geo.Muon.FilterThickness)
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
