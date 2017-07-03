#!/usr/bin/env python
# -*- coding: latin-1 -*-
import ROOT,os
import shipunit as u
from ShipGeoConfig import AttrDict,ConfigRegistry
detectorList = []

def getParameter(x,ship_geo,latestShipGeo):
  lv = x.split('.')
  last = lv[len(lv)-1]
  top = ''
  for l in range(len(lv)-1): 
    top += lv[l]
    if l<len(lv)-2: top +='.' 
  a = getattr(ship_geo,top)
  if hasattr(a,last): return getattr(a,last)
# not in the list of recorded parameteres. probably added after
# creation of file. Check newest geometry_config:
  a = getattr(latestShipGeo,top)
  return getattr(a,last)
    
def posHcal(z,hfile): 
 HcalZSize = 0
 sz = hfile+"z"+str(z)+".geo"
 floc = os.environ["FAIRSHIP"]+"/geometry"
 f_hcal  = floc+"/"+hfile
 f_hcalz = floc+"/"+sz
 f = open(f_hcal) 
 rewrite = True
 if sz in os.listdir(floc):
  test = os.popen("diff "+ f_hcal+ " "+ f_hcalz).read()
  if str.count(test,'---')==1 and not test.find('Position')<0: rewrite = False # only different is z position
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
def makeEcalGeoFile(z,efile):
 EcalZSize = 0
 sz = efile+"z"+str(z)+".geo"
 floc = os.environ["FAIRSHIP"]+"/geometry"
 f_ecal  = floc+"/"+efile
 f_ecalz = floc+"/"+sz
 f = open(f_ecal) 
 rewrite = True
 if sz in os.listdir(floc):
  test = os.popen("diff "+ f_ecal+ " "+ f_ecalz).read()
  if str.count(test,'---')==1 and not test.find('Position')<0: rewrite = False # only different is z position
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
 return EcalZSize,sz
def posEcal(z,efile):
 EcalZSize,sz = makeEcalGeoFile(z,efile)
 ecal = ROOT.ecal("Ecal", ROOT.kTRUE, sz)
 return ecal,EcalZSize

def configure(run,ship_geo):
# ---- for backward compatibility ----
 if not hasattr(ship_geo,"tankDesign"): ship_geo.tankDesign = 4
 if not hasattr(ship_geo.hcal,"File"): ship_geo.hcal.File = "hcal.geo"
 if not hasattr(ship_geo.Bfield,'x') :  ship_geo.Bfield.x   = 3.*u.m
 if not hasattr(ship_geo,'cave') :       
   ship_geo.cave = AttrDict(z=0*u.cm)
   ship_geo.cave.floorHeightMuonShield = 5*u.m
   ship_geo.cave.floorHeightTankA   = 4.5*u.m
   ship_geo.cave.floorHeightTankB   = 2.*u.m
 latestShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py",Yheight = ship_geo.Yheight/u.m, tankDesign = ship_geo.tankDesign, muShieldDesign = ship_geo.muShieldDesign, nuTauTargetDesign = ship_geo.nuTauTargetDesign)
# -----Create media-------------------------------------------------
 run.SetMaterials("media.geo")  # Materials
# ------------------------------------------------------------------------
  
# -----Create geometry----------------------------------------------
 cave= ROOT.ShipCave("CAVE")
 if ship_geo.tankDesign < 5: cave.SetGeometryFileName("cave.geo")
 else: cave.SetGeometryFileName("caveWithAir.geo")
 detectorList.append(cave)

 if ship_geo.muShieldDesign==6 or ship_geo.muShieldDesign==7: # magnetized hadron absorber defined in ShipMuonShield 
  TargetStation = ROOT.ShipTargetStation("TargetStation",ship_geo.target.length,
                                                        ship_geo.target.z,ship_geo.targetOpt,ship_geo.target.sl)
 else:
  TargetStation = ROOT.ShipTargetStation("TargetStation",ship_geo.target.length,ship_geo.hadronAbsorber.length,
                                                        ship_geo.target.z,ship_geo.hadronAbsorber.z,ship_geo.targetOpt,ship_geo.target.sl)
   
 if ship_geo.targetOpt>10:
  TargetStation.SetLayerPosMat(ship_geo.target.xy,ship_geo.target.L1,ship_geo.target.M1,ship_geo.target.L2,ship_geo.target.M2,\
  ship_geo.target.L3,ship_geo.target.M3,ship_geo.target.L4,ship_geo.target.M4,ship_geo.target.L5,ship_geo.target.M5,\
  ship_geo.target.L6,ship_geo.target.M6,ship_geo.target.L7,ship_geo.target.M7,ship_geo.target.L8,ship_geo.target.M8,\
  ship_geo.target.L9,ship_geo.target.M9,ship_geo.target.L10,ship_geo.target.M10,ship_geo.target.L11,ship_geo.target.M11,\
  ship_geo.target.L12,ship_geo.target.M12,ship_geo.target.L13,ship_geo.target.M13,ship_geo.target.L14,ship_geo.target.M14,\
  ship_geo.target.L15,ship_geo.target.M15,ship_geo.target.L16,ship_geo.target.M16,ship_geo.target.L17,ship_geo.target.M17)
 detectorList.append(TargetStation)

 if ship_geo.muShieldDesign==1:
  MuonShield = ROOT.ShipMuonShield("MuonShield",ship_geo.muShieldDesign,"ShipMuonShield",ship_geo.muShield.z,ship_geo.muShield.dZ0,ship_geo.muShield.length,\
                                   ship_geo.muShield.LE) 
 elif ship_geo.muShieldDesign==2:
  MuonShield = ROOT.ShipMuonShield("MuonShield",ship_geo.muShieldDesign,"ShipMuonShield",ship_geo.muShield.z,ship_geo.muShield.dZ0,ship_geo.muShield.dZ1,\
               ship_geo.muShield.dZ2,ship_geo.muShield.dZ3,ship_geo.muShield.dZ4,ship_geo.muShield.dZ5,ship_geo.muShield.dZ6,ship_geo.muShield.LE) 
 elif ship_geo.muShieldDesign==3 or ship_geo.muShieldDesign==4 or ship_geo.muShieldDesign==5 or ship_geo.muShieldDesign==6 or ship_geo.muShieldDesign==7 :
  if not hasattr(ship_geo.muShield,"Field"):
   MuonShield = ROOT.ShipMuonShield("MuonShield",ship_geo.muShieldDesign,"ShipMuonShield",ship_geo.muShield.z,ship_geo.muShield.dZ0,ship_geo.muShield.dZ1,\
               ship_geo.muShield.dZ2,ship_geo.muShield.dZ3,ship_geo.muShield.dZ4,ship_geo.muShield.dZ5,ship_geo.muShield.dZ6,\
               ship_geo.muShield.dZ7,ship_geo.muShield.dZ8,ship_geo.muShield.dXgap,ship_geo.muShield.LE,ship_geo.Yheight*4./10., ship_geo.cave.floorHeightMuonShield) 
  else:
   MuonShield = ROOT.ShipMuonShield("MuonShield",ship_geo.muShieldDesign,"ShipMuonShield",ship_geo.muShield.z,ship_geo.muShield.dZ0,ship_geo.muShield.dZ1,\
               ship_geo.muShield.dZ2,ship_geo.muShield.dZ3,ship_geo.muShield.dZ4,ship_geo.muShield.dZ5,ship_geo.muShield.dZ6,\
               ship_geo.muShield.dZ7,ship_geo.muShield.dZ8,ship_geo.muShield.dXgap,ship_geo.muShield.LE,ship_geo.Yheight*4./10.,\
               ship_geo.cave.floorHeightMuonShield,ship_geo.muShield.Field) 
 
 detectorList.append(MuonShield)


 magnet_design = 2
 if ship_geo.tankDesign == 5: magnet_design = 3
 if ship_geo.strawDesign > 1 : 
   magnet = ROOT.ShipMagnet("Magnet","SHiP Magnet",ship_geo.Bfield.z, magnet_design, ship_geo.Bfield.x, ship_geo.Bfield.y, ship_geo.cave.floorHeightTankB)
 else: magnet = ROOT.ShipMagnet("Magnet","SHiP Magnet",ship_geo.Bfield.z)
 detectorList.append(magnet)
  
 Veto = ROOT.veto("Veto", ROOT.kTRUE)   # vacuum tank
 Veto.SetLiquidVeto(1)  # liquid scintillator
 Veto.SetPlasticVeto(1) # plastic scintillator

 Veto.SetZpositions(ship_geo.vetoStation.z, ship_geo.TrackStation1.z, ship_geo.TrackStation2.z, \
                    ship_geo.TrackStation3.z, ship_geo.TrackStation4.z,ship_geo.tankDesign)
 Veto.SetTubZpositions(ship_geo.Chamber1.z,ship_geo.Chamber2.z,ship_geo.Chamber3.z,ship_geo.Chamber4.z,ship_geo.Chamber5.z,ship_geo.Chamber6.z);
 Veto.SetTublengths(ship_geo.chambers.Tub1length,ship_geo.chambers.Tub2length,ship_geo.chambers.Tub3length, \
                    ship_geo.chambers.Tub4length,ship_geo.chambers.Tub5length,ship_geo.chambers.Tub6length);
 Veto.SetB(ship_geo.Yheight/2.)
 Veto.SetFloorHeight(ship_geo.cave.floorHeightTankA,ship_geo.cave.floorHeightTankB);
 if ship_geo.tankDesign == 5: 
    dzX = ship_geo.zFocusX+ship_geo.target.z0    
    x1  = ship_geo.xMax/(ship_geo.Chamber1.z -ship_geo.chambers.Tub1length-dzX)*(ship_geo.TrackStation4.z-dzX)
    dzY = ship_geo.zFocusY+ship_geo.target.z0    
    y1  = ship_geo.Yheight/(ship_geo.Chamber1.z -ship_geo.chambers.Tub1length-dzY)*(ship_geo.TrackStation4.z-dzY)
    Veto.SetXYstart(x1,dzX,y1,dzY)
    Veto.SetVesselStructure(ship_geo.Veto.innerSupport,ship_geo.Veto.sensitiveThickness,ship_geo.Veto.outerSupport,\
                            ship_geo.Veto.innerSupportMed,ship_geo.Veto.lidThickness,ship_geo.Veto.sensitiveMed,\
                            ship_geo.Veto.outerSupportMed,ship_geo.Veto.decayMed,\
                            ship_geo.Veto.rib,ship_geo.Veto.ribMed)

 detectorList.append(Veto)

 if ship_geo.muShieldDesign not in [2,3,4] and hasattr(ship_geo.tauMS,'Xtot'):
  taumagneticspectrometer = ROOT.MagneticSpectrometer("MagneticSpectrometer", ship_geo.tauMS.zMSC,  ROOT.kTRUE)
  taumagneticspectrometer.SetTotDimensions(ship_geo.tauMS.Xtot,ship_geo.tauMS.Ytot, ship_geo.tauMS.Ztot )
  taumagneticspectrometer.SetFeDimensions(ship_geo.tauMS.XFe,ship_geo.tauMS.YFe, ship_geo.tauMS.ZFe)
  taumagneticspectrometer.SetRpcDimensions(ship_geo.tauMS.XRpc,ship_geo.tauMS.YRpc, ship_geo.tauMS.ZRpc)
  taumagneticspectrometer.SetRpcGasDimensions(ship_geo.tauMS.XGas,ship_geo.tauMS.YGas, ship_geo.tauMS.ZGas)
  taumagneticspectrometer.SetRpcStripDimensions(ship_geo.tauMS.XStrip,ship_geo.tauMS.YStrip, ship_geo.tauMS.ZStrip)
  taumagneticspectrometer.SetRpcElectrodeDimensions(ship_geo.tauMS.XEle,ship_geo.tauMS.YEle, ship_geo.tauMS.ZEle)
  taumagneticspectrometer.SetRpcPETDimensions(ship_geo.tauMS.XPet,ship_geo.tauMS.YPet, ship_geo.tauMS.ZPet)
  taumagneticspectrometer.SetReturnYokeDimensions(ship_geo.tauMS.XRyoke,ship_geo.tauMS.YRyoke, ship_geo.tauMS.ZRyoke)
  taumagneticspectrometer.SetSmallerYokeDimensions(ship_geo.tauMS.XRyoke_s,ship_geo.tauMS.YRyoke_s, ship_geo.tauMS.ZRyoke_s)
  taumagneticspectrometer.SetZDimensionArm(ship_geo.tauMS.ZArm)
  taumagneticspectrometer.SetGapDownstream(ship_geo.tauMS.GapD)
  taumagneticspectrometer.SetGapMiddle(ship_geo.tauMS.GapM)
  taumagneticspectrometer.SetNFeInArm(ship_geo.tauMS.NFe)
  taumagneticspectrometer.SetNRpcInArm(ship_geo.tauMS.NRpc)
  taumagneticspectrometer.SetMagneticField(ship_geo.tauMS.B)
  taumagneticspectrometer.SetCoilParameters(ship_geo.tauMS.CoilH, ship_geo.tauMS.CoilW, ship_geo.tauMS.N, ship_geo.tauMS.CoilG)
  taumagneticspectrometer.SetPillarDimensions(ship_geo.tauMS.PillarX,ship_geo.tauMS.PillarY, ship_geo.tauMS.PillarZ)
  detectorList.append(taumagneticspectrometer)

  tauHpt = ROOT.Hpt("HighPrecisionTrackers",ship_geo.tauHPT.DX, ship_geo.tauHPT.DY, ship_geo.tauHPT.DZ, ROOT.kTRUE)
  tauHpt.SetZsize(ship_geo.tauMS.Ztot)
  tauHpt.SetConcreteBaseDim(ship_geo.tauHPT.ConcreteX,ship_geo.tauHPT.ConcreteY,ship_geo.tauHPT.ConcreteZ)
  detectorList.append(tauHpt)

  if ship_geo.nuTauTargetDesign==0 or ship_geo.nuTauTargetDesign==1:
    EmuMagnet = ROOT.EmulsionMagnet("EmuMagnet",ship_geo.EmuMagnet.zC,"EmulsionMagnet")
    EmuMagnet.SetDesign(ship_geo.EmuMagnet.Design)
    EmuMagnet.SetGaps(ship_geo.EmuMagnet.GapUp, ship_geo.EmuMagnet.GapDown)
    EmuMagnet.SetMagneticField(ship_geo.EmuMagnet.B)
    EmuMagnet.SetMagnetSizes(ship_geo.EmuMagnet.X, ship_geo.EmuMagnet.Y, ship_geo.EmuMagnet.Z)
    EmuMagnet.SetCoilParameters(ship_geo.EmuMagnet.Radius, ship_geo.EmuMagnet.Height1, ship_geo.EmuMagnet.Height2, ship_geo.EmuMagnet.Distance)
    EmuMagnet.SetMagnetColumn(ship_geo.EmuMagnet.ColX, ship_geo.EmuMagnet.ColY, ship_geo.EmuMagnet.ColZ)
    EmuMagnet.SetBaseDim(ship_geo.EmuMagnet.BaseX, ship_geo.EmuMagnet.BaseY, ship_geo.EmuMagnet.BaseZ)
    EmuMagnet.SetPillarDimensions(ship_geo.EmuMagnet.PillarX, ship_geo.EmuMagnet.PillarY, ship_geo.EmuMagnet.PillarZ)
    detectorList.append(EmuMagnet)
  if ship_geo.nuTauTargetDesign==2:
     EmuMagnet = ROOT.EmulsionMagnet()

  NuTauTarget = ROOT.Target("NuTauTarget",ship_geo.NuTauTarget.Ydist,ROOT.kTRUE)
  NuTauTarget.MakeNuTargetPassive(ship_geo.NuTauTarget.nuTargetPassive)
  NuTauTarget.SetDetectorDesign(ship_geo.NuTauTarget.Design)
  NuTauTarget.SetCenterZ(ship_geo.NuTauTarget.zC)
  NuTauTarget.SetNumberBricks(ship_geo.NuTauTarget.col,ship_geo.NuTauTarget.row,ship_geo.NuTauTarget.wall) 
  NuTauTarget.SetDetectorDimension(ship_geo.NuTauTarget.xdim, ship_geo.NuTauTarget.ydim, ship_geo.NuTauTarget.zdim)
  NuTauTarget.SetEmulsionParam(ship_geo.NuTauTarget.EmTh, ship_geo.NuTauTarget.EmX, ship_geo.NuTauTarget.EmY, ship_geo.NuTauTarget.PBTh,ship_geo.NuTauTarget.EPlW, ship_geo.NuTauTarget.LeadTh, ship_geo.NuTauTarget.AllPW)
 
  NuTauTarget.SetBrickParam(ship_geo.NuTauTarget.BrX, ship_geo.NuTauTarget.BrY, ship_geo.NuTauTarget.BrZ, ship_geo.NuTauTarget.BrPackX, ship_geo.NuTauTarget.BrPackY, ship_geo.NuTauTarget.BrPackZ)
  NuTauTarget.SetCESParam(ship_geo.NuTauTarget.RohG, ship_geo.NuTauTarget.LayerCESW, ship_geo.NuTauTarget.CESW, ship_geo.NuTauTarget.CESPack)
  NuTauTarget.SetCellParam(ship_geo.NuTauTarget.CellW)
  if ship_geo.nuTauTargetDesign==0 or ship_geo.nuTauTargetDesign==1:
    NuTauTarget.SetMagneticField(ship_geo.EmuMagnet.B)
    NuTauTarget.SetMagnetHeight(ship_geo.EmuMagnet.Y)
    NuTauTarget.SetColumnHeight(ship_geo.EmuMagnet.ColY)
    NuTauTarget.SetBaseHeight(ship_geo.EmuMagnet.BaseY)
    NuTauTarget.SetCoilUpHeight(ship_geo.EmuMagnet.Height1)
    NuTauTarget.SetCoilDownHeight(ship_geo.EmuMagnet.Height2)
  if ship_geo.nuTauTargetDesign==2:
    NuTauTarget.SetPillarDimension(ship_geo.NuTauTarget.PillarX,ship_geo.NuTauTarget.PillarY,ship_geo.NuTauTarget.PillarZ)
    NuTauTarget.SetBaseDimension(ship_geo.NuTauTarget.BaseX, ship_geo.NuTauTarget.BaseY, ship_geo.NuTauTarget.BaseZ)
  
  NuTauTT = ROOT.TargetTracker("TargetTrackers",ROOT.kTRUE)
  NuTauTT.SetNumberTT(ship_geo.NuTauTT.n)
  NuTauTT.SetTargetTrackerParam(ship_geo.NuTauTT.TTX, ship_geo.NuTauTT.TTY, ship_geo.NuTauTT.TTZ)
  NuTauTT.SetBrickParam(ship_geo.NuTauTarget.CellW)
  NuTauTT.SetTotZDimension(ship_geo.NuTauTarget.zdim)

  #method of nutau target that must be called after TT parameter definition
  NuTauTarget.SetTTzdimension(ship_geo.NuTauTT.TTZ)
 
  detectorList.append(NuTauTarget)
  detectorList.append(NuTauTT)

 if ship_geo.strawDesign > 1 :
  Strawtubes = ROOT.strawtubes("Strawtubes", ROOT.kTRUE)    
  Strawtubes.SetZpositions(ship_geo.vetoStation.z, ship_geo.TrackStation1.z, ship_geo.TrackStation2.z, ship_geo.TrackStation3.z, ship_geo.TrackStation4.z)
  Strawtubes.SetDeltazView(ship_geo.strawtubes.DeltazView)
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
  Strawtubes.SetStrawLength(ship_geo.strawtubes.StrawLength)
 
  if hasattr(ship_geo.strawtubes,"StrawLengthVeto"):
   Strawtubes.SetStrawLengthVeto(ship_geo.strawtubes.StrawLengthVeto) 
   Strawtubes.SetStrawLength12(ship_geo.strawtubes.StrawLength12)
   Strawtubes.SetVetoYDim(ship_geo.strawtubes.vetoydim)  
   Strawtubes.SetTr12YDim(ship_geo.strawtubes.tr12ydim)
   Strawtubes.SetTr34YDim(ship_geo.strawtubes.tr34ydim)    
  else:
   Strawtubes.SetStrawLengthVeto(ship_geo.strawtubes.StrawLength) 
   Strawtubes.SetStrawLength12(ship_geo.strawtubes.StrawLength)
   Strawtubes.SetVetoYDim(ship_geo.Yheight/2.)  
   Strawtubes.SetTr12YDim(ship_geo.Yheight/2.)
   Strawtubes.SetTr34YDim(ship_geo.Yheight/2.)    
  # for the digitizing step
  Strawtubes.SetStrawResolution(getParameter("strawtubes.v_drift",ship_geo,latestShipGeo),getParameter("strawtubes.sigma_spatial",ship_geo,latestShipGeo) )
  detectorList.append(Strawtubes)

 if ship_geo.preshowerOption > 0:
  Preshower = ROOT.preshower("Preshower", ROOT.kTRUE)
  Preshower.SetZStationPosition2(ship_geo.PreshowerStation0.z,ship_geo.PreshowerStation1.z)
  Preshower.SetZFilterPosition2(ship_geo.PreshowerFilter0.z,ship_geo.PreshowerFilter1.z)
  Preshower.SetXMax(ship_geo.Preshower.XMax)
  Preshower.SetYMax(ship_geo.Preshower.YMax)
  Preshower.SetActiveThickness(ship_geo.Preshower.ActiveThickness)
  Preshower.SetFilterThickness2(ship_geo.Preshower.FilterThickness0,ship_geo.Preshower.FilterThickness1)
  detectorList.append(Preshower)

 ecal,EcalZSize = posEcal(ship_geo.ecal.z,ship_geo.ecal.File)
 detectorList.append(ecal)

 if not ship_geo.HcalOption < 0:
  hcal,HcalZSize = posHcal(ship_geo.hcal.z,ship_geo.hcal.File)
  if abs(ship_geo.hcal.hcalSpace -  HcalZSize) > 10*u.cm:
    print 'mismatch between hcalsize in geo file and python configuration'
    print ship_geo.hcal.hcalSpace -  HcalZSize, ship_geo.hcal.hcalSpace , HcalZSize
  detectorList.append(hcal)
 Muon = ROOT.muon("Muon", ROOT.kTRUE)
 Muon.SetZStationPositions(ship_geo.MuonStation0.z, ship_geo.MuonStation1.z,ship_geo.MuonStation2.z,ship_geo.MuonStation3.z)
 Muon.SetZFilterPositions(ship_geo.MuonFilter0.z, ship_geo.MuonFilter1.z,ship_geo.MuonFilter2.z)
 Muon.SetXMax(ship_geo.Muon.XMax)
 Muon.SetYMax(ship_geo.Muon.YMax)
 Muon.SetActiveThickness(ship_geo.Muon.ActiveThickness)
 Muon.SetFilterThickness(ship_geo.Muon.FilterThickness)
 detectorList.append(Muon)

#-----   Magnetic field   -------------------------------------------
 if ship_geo.strawDesign == 4: fMagField = ROOT.ShipBellField("wilfried", ship_geo.Bfield.max ,ship_geo.Bfield.z,2,ship_geo.Yheight/2.*u.m )  
 else :                        fMagField = ROOT.ShipBellField("wilfried", ship_geo.Bfield.max ,ship_geo.Bfield.z,1,ship_geo.Yheight/2.*u.m )  
 if ship_geo.muShieldDesign==6: fMagField.IncludeTarget(ship_geo.target.xy, ship_geo.target.z0, ship_geo.target.length)
 run.SetField(fMagField)
#
 exclusionList = []
 #exclusionList = ["Muon","Ecal","Hcal","Strawtubes","TargetTrackers","NuTauTarget","HighPrecisionTrackers",\
 #                 "Veto","Magnet","MuonShield","TargetStation","MagneticSpectrometer","EmuMagnet"]
 for x in detectorList:
   if x.GetName() in exclusionList: continue
   run.AddModule(x)
# return list of detector elements
 detElements = {}
 for x in run.GetListOfModules(): detElements[x.GetName()]=x
 return detElements
