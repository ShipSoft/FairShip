#!/usr/bin/env python
# -*- coding: latin-1 -*-
import ROOT,os
import shipunit as u
def posHcal(z): 
 HcalZSize = 0
 sz = "hcalz"+str(z)+".geo"
 floc = os.environ["FAIRSHIP"]+"/geometry"
 f_hcal  = floc+"/hcal.geo"
 f_hcalz = floc+"/"+sz
 f = open(f_hcal) 
 rewrite = True
 if sz in os.listdir(floc):
  test = os.popen("diff "+ f_hcal+ " "+ f_hcalz).read()
  if len(test)<6: rewrite = False # only different is z position
 if rewrite: fn = open(f_hcalz,'w')
 for l in f.readlines():
   if rewrite:
    if not l.find("ZPos")<0:
      l ="ZPos="+str(z)+ "	#Position of Hcal  center	[cm]\n"
    fn.write(l)
   if not l.find("HcalZSize")<0:
     HcalZSize = float(l[len('HcalZSize')+1:].split('#')[0]) 
 f.close()
 if rewrite: fn.close()  
 hcal = ROOT.hcal("Hcal", ROOT.kTRUE, sz)
 return hcal,HcalZSize
def posEcal(z,efile):
 EcalZSize = 0
 sz = efile+"z"+str(z)+".geo"
 floc = os.environ["FAIRSHIP"]+"/geometry"
 f_ecal  = floc+"/"+efile
 f_ecalz = floc+"/"+sz
 f = open(f_ecal) 
 rewrite = True
 if sz in os.listdir(floc):
  test = os.popen("diff "+ f_ecal+ " "+ f_ecalz).read()
  if len(test)<6: rewrite = False # only different is z position
 if rewrite: fn = open(f_ecalz,'w')
 for l in f.readlines():
   if rewrite:
    if not l.find("ZPos")<0:
      l ="ZPos="+str(z)+ "	#Position of Ecal start		[cm]\n"
    fn.write(l)
   if not l.find("EcalZSize")<0:
     EcalZSize = float(l[len('EcalZSize')+1:].split('#')[0]) 
 f.close()
 if rewrite: fn.close()  
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
               ship_geo.muShield.dZ7,ship_geo.muShield.dZ8,ship_geo.muShield.dXgap,ship_geo.muShield.LE,ship_geo.Yheight*1.5/10.) 

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
  taumagneticspectrometer = ROOT.MagneticSpectrometer("MagneticSpectrometer", ship_geo.tauMS.zMSC, ship_geo.tauMS.zSize, ship_geo.tauMS.FeSlab, \
  ship_geo.tauMS.RpcW,ship_geo.tauMS.ArmW, ship_geo.tauMS.GapV, ship_geo.tauMS.MGap, ship_geo.tauMS.Mfield, ship_geo.tauMS.HPTW, ship_geo.tauMS.RetYokeH, ROOT.kTRUE)
  taumagneticspectrometer.SetCoilParameters(ship_geo.tauMS.CoilH, ship_geo.tauMS.CoilW, ship_geo.tauMS.N, ship_geo.tauMS.CoilG);
  run.AddModule(taumagneticspectrometer)
  
  NuTauTarget = ROOT.Target("NuTauTarget",ship_geo.NuTauTarget.zC, ship_geo.NuTauTarget.GapTS, ROOT.kTRUE)
 
  NuTauTarget.SetGoliathSizes(ship_geo.NuTauTarget.H, ship_geo.NuTauTarget.TS, ship_geo.NuTauTarget.LS, ship_geo.NuTauTarget.BasisH);
  NuTauTarget.SetCoilParameters(ship_geo.NuTauTarget.CoilR, ship_geo.NuTauTarget.UpCoilH, ship_geo.NuTauTarget.LowCoilH, ship_geo.NuTauTarget.CoilD);
 
  NuTauTarget.SetDetectorDimension(ship_geo.NuTauTarget.xdim, ship_geo.NuTauTarget.ydim, ship_geo.NuTauTarget.zdim);
  NuTauTarget.SetEmulsionParam(ship_geo.NuTauTarget.EmTh, ship_geo.NuTauTarget.EmX, ship_geo.NuTauTarget.EmY, ship_geo.NuTauTarget.PBTh,ship_geo.NuTauTarget.EPlW, ship_geo.NuTauTarget.LeadTh, ship_geo.NuTauTarget.AllPW);
  NuTauTarget.SetBrickParam(ship_geo.NuTauTarget.BrX, ship_geo.NuTauTarget.BrY, ship_geo.NuTauTarget.BrZ);
  NuTauTarget.SetCESParam(ship_geo.NuTauTarget.RohG, ship_geo.NuTauTarget.LayerCESW, ship_geo.NuTauTarget.CESW);
  NuTauTarget.SetCellParam(ship_geo.NuTauTarget.CellW);
  
  NuTauTarget.SetTargetTrackerParam(ship_geo.NuTauTarget.TTX, ship_geo.NuTauTarget.TTY, ship_geo.NuTauTarget.TTZ);
  
  run.AddModule(NuTauTarget)

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

 ecal,EcalZSize = posEcal(ship_geo.ecal.z,ship_geo.ecal.File)
 run.AddModule(ecal)

 if not ship_geo.HcalOption < 0:
  hcal,HcalZSize = posHcal(ship_geo.hcal.z)
  if abs(ship_geo.hcal.hcalSpace -  HcalZSize) > 10*u.cm:
    print 'mismatch between hcalsize in geo file and python configuration'
    print ship_geo.hcal.hcalSpace -  HcalZSize, ship_geo.hcal.hcalSpace , HcalZSize
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
 if ship_geo.strawDesign == 4: fMagField = ROOT.ShipBellField("wilfried", ship_geo.Bfield.max ,ship_geo.Bfield.z,2,ship_geo.Yheight/2.*u.m )  
 else :                        fMagField = ROOT.ShipBellField("wilfried", ship_geo.Bfield.max ,ship_geo.Bfield.z,1,ship_geo.Yheight/2.*u.m )  
 run.SetField(fMagField)

# return list of detector elements
 detElements = {}
 for x in run.GetListOfModules(): detElements[x.GetName()]=x
 return detElements
