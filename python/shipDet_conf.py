#!/usr/bin/env python
# -*- coding: latin-1 -*-
from __future__ import print_function
from __future__ import division
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
    
def posHcal(z,hfile,HcalOption): 
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
 if HcalOption==2: hcal = ROOT.hcal("Hcal", ROOT.kFALSE, sz)
 else:                      hcal = ROOT.hcal("Hcal", ROOT.kTRUE, sz)
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
 if not hasattr(ship_geo,"tankDesign"): ship_geo.tankDesign = 5
 if not hasattr(ship_geo,"muShieldGeo"): ship_geo.muShieldGeo = None
 if not hasattr(ship_geo.hcal,"File"):  ship_geo.hcal.File = "hcal.geo"
 if not hasattr(ship_geo.Bfield,'x') :  ship_geo.Bfield.x   = 3.*u.m
 if not hasattr(ship_geo,'cave') :       
   ship_geo.cave = AttrDict(z=0*u.cm)
   ship_geo.cave.floorHeightMuonShield = 5*u.m
   ship_geo.cave.floorHeightTankA   = 4.5*u.m
   ship_geo.cave.floorHeightTankB   = 2.*u.m
 if not hasattr(ship_geo,'NuTauTT') : ship_geo.NuTauTT= AttrDict(z=0*u.cm)
 if not hasattr(ship_geo.NuTauTT,'design') : ship_geo.NuTauTT.design = 0
 if not hasattr(ship_geo,'EcalOption'):     ship_geo.EcalOption = 1      
 latestShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py",Yheight = ship_geo.Yheight/u.m, tankDesign = ship_geo.tankDesign, muShieldDesign = ship_geo.muShieldDesign, nuTauTargetDesign = ship_geo.nuTauTargetDesign, muShieldGeo = ship_geo.muShieldGeo)
# -----Create media-------------------------------------------------
 run.SetMaterials("media.geo")  # Materials
# ------------------------------------------------------------------------
  
# -----Create geometry----------------------------------------------
 cave= ROOT.ShipCave("CAVE")
 if ship_geo.tankDesign < 5: cave.SetGeometryFileName("cave.geo")
 else: cave.SetGeometryFileName("caveWithAir.geo")
 detectorList.append(cave)

 if ship_geo.muShieldDesign in [6, 7, 8, 9,10]:  # magnetized hadron absorber defined in ShipMuonShield 
  TargetStation = ROOT.ShipTargetStation("TargetStation",ship_geo.target.length,
                                                        ship_geo.target.z,ship_geo.targetOpt,ship_geo.target.sl)
 else:
  TargetStation = ROOT.ShipTargetStation("TargetStation",ship_geo.target.length,ship_geo.hadronAbsorber.length,
                                                        ship_geo.target.z,ship_geo.hadronAbsorber.z,ship_geo.targetOpt,ship_geo.target.sl)
   
 if ship_geo.targetOpt>10:
  slices_length   = ROOT.std.vector('float')()
  slices_material = ROOT.std.vector('std::string')()
  for i in range(1,ship_geo.targetOpt+1):
   slices_length.push_back(  eval("ship_geo.target.L"+str(i)))
   slices_material.push_back(eval("ship_geo.target.M"+str(i)))
  TargetStation.SetLayerPosMat(ship_geo.target.xy,slices_length,slices_material)
 detectorList.append(TargetStation)

 if ship_geo.muShieldDesign==1:
  MuonShield = ROOT.ShipMuonShield("MuonShield",ship_geo.muShieldDesign,"ShipMuonShield",ship_geo.muShield.z,ship_geo.muShield.dZ0,ship_geo.muShield.length,\
                                   ship_geo.muShield.LE) 
 elif ship_geo.muShieldDesign==2:
  MuonShield = ROOT.ShipMuonShield("MuonShield",ship_geo.muShieldDesign,"ShipMuonShield",ship_geo.muShield.z,ship_geo.muShield.dZ0,ship_geo.muShield.dZ1,\
               ship_geo.muShield.dZ2,ship_geo.muShield.dZ3,ship_geo.muShield.dZ4,ship_geo.muShield.dZ5,ship_geo.muShield.dZ6,ship_geo.muShield.LE) 
 elif ship_geo.muShieldDesign in [3, 4, 5, 6, 7, 9,10]:
  if not hasattr(ship_geo.muShield,"Field"):
        MuonShield = ROOT.ShipMuonShield(
            "MuonShield", ship_geo.muShieldDesign, "ShipMuonShield",
            ship_geo.muShield.z, ship_geo.muShield.dZ0, ship_geo.muShield.dZ1,
            ship_geo.muShield.dZ2, ship_geo.muShield.dZ3,
            ship_geo.muShield.dZ4, ship_geo.muShield.dZ5,
            ship_geo.muShield.dZ6, ship_geo.muShield.dZ7,
            ship_geo.muShield.dZ8, ship_geo.muShield.dXgap,
            ship_geo.muShield.LE, ship_geo.Yheight * 4. / 10.,
            ship_geo.cave.floorHeightMuonShield,
            ship_geo.muShieldWithCobaltMagnet, ship_geo.muShieldStepGeo)
  else:
        MuonShield = ROOT.ShipMuonShield(
            "MuonShield", ship_geo.muShieldDesign, "ShipMuonShield",
            ship_geo.muShield.z, ship_geo.muShield.dZ0, ship_geo.muShield.dZ1,
            ship_geo.muShield.dZ2, ship_geo.muShield.dZ3,
            ship_geo.muShield.dZ4, ship_geo.muShield.dZ5,
            ship_geo.muShield.dZ6, ship_geo.muShield.dZ7,
            ship_geo.muShield.dZ8, ship_geo.muShield.dXgap,
            ship_geo.muShield.LE, ship_geo.Yheight * 4. / 10.,
            ship_geo.cave.floorHeightMuonShield,ship_geo.muShield.Field,
            ship_geo.muShieldWithCobaltMagnet, ship_geo.muShieldStepGeo) 
 elif ship_geo.muShieldDesign == 8:
  MuonShield = ROOT.ShipMuonShield(ship_geo.muShieldGeo,
                                   ship_geo.muShieldWithCobaltMagnet,
                                   ship_geo.muShieldStepGeo)
 
 detectorList.append(MuonShield)

 if not hasattr(ship_geo,"magnetDesign"):
 # backward compatibility
  magnet_design = 2
  if ship_geo.tankDesign == 5: magnet_design = 3
  if ship_geo.tankDesign == 6: magnet_design = 4
  ship_geo.magnetDesign = magnet_design
  ship_geo.Bfield.YokeWidth = 200.*u.cm 
  ship_geo.Bfield.YokeDepth = 200.*u.cm
  ship_geo.Bfield.CoilThick = 25.*u.cm
# sanity check, 2018 layout ship_geo.tankDesign == 6 has to be together with ship_geo.nuTauTargetDesign == 3
 if (ship_geo.tankDesign == 6 and ship_geo.nuTauTargetDesign != 3) or (ship_geo.tankDesign != 6 and ship_geo.nuTauTargetDesign == 3):
   print("version of tankDesign and nuTauTargetDesign are not compatible, should be 6 and 3, it is ",ship_geo.tankDesign, ship_geo.nuTauTargetDesign) 
   exit()
 if ship_geo.strawDesign > 1 : 
  if ship_geo.magnetDesign>3:
   B = ship_geo.Bfield
   magnet = ROOT.ShipMagnet("Magnet","SHiP Magnet",B.z, ship_geo.magnetDesign, B.x, B.y, ship_geo.cave.floorHeightTankB, B.YokeWidth, B.YokeDepth, B.CoilThick)
#                                                               xaperture,  yaperture 
  else: 
   magnet = ROOT.ShipMagnet("Magnet","SHiP Magnet",ship_geo.Bfield.z, ship_geo.magnetDesign, ship_geo.Bfield.x, ship_geo.Bfield.y, ship_geo.cave.floorHeightTankB)
 else: magnet = ROOT.ShipMagnet("Magnet","SHiP Magnet",ship_geo.Bfield.z)
 detectorList.append(magnet)
  
 Veto = ROOT.veto("Veto", ROOT.kTRUE)   # vacuum tank
 Veto.SetLiquidVeto(1)  # liquid scintillator
 Veto.SetPlasticVeto(1) # plastic scintillator

 Veto.SetZpositions(ship_geo.vetoStation.z, ship_geo.TrackStation1.z, ship_geo.TrackStation2.z, \
                    ship_geo.TrackStation3.z, ship_geo.TrackStation4.z,ship_geo.tankDesign)
 Veto.SetTubZpositions(ship_geo.Chamber1.z,ship_geo.Chamber2.z,ship_geo.Chamber3.z,ship_geo.Chamber4.z,ship_geo.Chamber5.z,ship_geo.Chamber6.z)
 Veto.SetTublengths(ship_geo.chambers.Tub1length,ship_geo.chambers.Tub2length,ship_geo.chambers.Tub3length, \
                    ship_geo.chambers.Tub6length)
 Veto.SetB(ship_geo.Yheight/2.)
 Veto.SetFloorHeight(ship_geo.cave.floorHeightTankA,ship_geo.cave.floorHeightTankB)
 if ship_geo.tankDesign > 4: 
    dzX = ship_geo.zFocusX+ship_geo.target.z0    
    x1  = ship_geo.xMax/(ship_geo.Chamber1.z -ship_geo.chambers.Tub1length-dzX)*(ship_geo.TrackStation4.z-dzX)
    dzY = ship_geo.zFocusY+ship_geo.target.z0    
    y1  = ship_geo.Yheight/(ship_geo.Chamber1.z -ship_geo.chambers.Tub1length-dzY)*(ship_geo.TrackStation4.z-dzY)
    Veto.SetXYstart(x1,dzX,y1,dzY)
    Veto.SetVesselStructure(ship_geo.Veto.innerSupport,ship_geo.Veto.sensitiveThickness,ship_geo.Veto.outerSupport,\
                            ship_geo.Veto.innerSupportMed,ship_geo.Veto.lidThickness,ship_geo.Veto.sensitiveMed,\
                            ship_geo.Veto.outerSupportMed,ship_geo.Veto.decayMed,\
                            ship_geo.Veto.rib)

 detectorList.append(Veto)
 if hasattr(ship_geo,'tauMudet'): # don't support old designs

  if ship_geo.muShieldDesign not in [2,3,4] and hasattr(ship_geo.tauMudet,'Xtot'):
   taumuondetector = ROOT.NuTauMudet("NuTauMudet", ship_geo.tauMudet.zMudetC,  ROOT.kTRUE)
   taumuondetector.SetDesign(ship_geo.nuTauTargetDesign)
   taumuondetector.SetTotDimensions(ship_geo.tauMudet.Xtot,ship_geo.tauMudet.Ytot, ship_geo.tauMudet.Ztot )
   if hasattr(ship_geo.tauMudet,'ZFethin'):
      taumuondetector.SetFeDimensions(ship_geo.tauMudet.XFe,ship_geo.tauMudet.YFe, ship_geo.tauMudet.ZFethick,ship_geo.tauMudet.ZFethin)
      taumuondetector.SetNFeInArm(ship_geo.tauMudet.NFethick, ship_geo.tauMudet.NFethin)
      taumuondetector.SetLateralCutSize(ship_geo.tauMudet.CutHeight, ship_geo.tauMudet.CutLength)
      taumuondetector.SetSupportTransverseDimensions(ship_geo.tauMudet.UpperSupportX,ship_geo.tauMudet.UpperSupportY, \
                                                     ship_geo.tauMudet.LowerSupportX, ship_geo.tauMudet.LowerSupportY, \
                                                     ship_geo.tauMudet.LateralSupportX, ship_geo.tauMudet.LateralSupportY, ship_geo.tauMudet.YSpacing)
   else: #geometry used before new iron sampling
      taumuondetector.SetFeDimensions(ship_geo.tauMudet.XFe,ship_geo.tauMudet.YFe, ship_geo.tauMudet.ZFe)
      taumuondetector.SetNFeInArm(ship_geo.tauMudet.NFe)
   taumuondetector.SetRpcDimensions(ship_geo.tauMudet.XRpc,ship_geo.tauMudet.YRpc, ship_geo.tauMudet.ZRpc)
   taumuondetector.SetRpcGasDimensions(ship_geo.tauMudet.XGas,ship_geo.tauMudet.YGas, ship_geo.tauMudet.ZGas)
   taumuondetector.SetRpcStripDimensions(ship_geo.tauMudet.XStrip,ship_geo.tauMudet.YStrip, ship_geo.tauMudet.ZStrip)
   taumuondetector.SetRpcElectrodeDimensions(ship_geo.tauMudet.XEle,ship_geo.tauMudet.YEle, ship_geo.tauMudet.ZEle)
   taumuondetector.SetRpcPETDimensions(ship_geo.tauMudet.XPet,ship_geo.tauMudet.YPet, ship_geo.tauMudet.ZPet)
   taumuondetector.SetNRpcInArm(ship_geo.tauMudet.NRpc)
   taumuondetector.SetUpperCoverDimensions(ship_geo.tauMudet.XCov, ship_geo.tauMudet.YCov, ship_geo.tauMudet.ZCov)
   taumuondetector.SetLateralCoverDimensions(ship_geo.tauMudet.XLateral, ship_geo.tauMudet.YLateral, ship_geo.tauMudet.ZLateral)
   taumuondetector.SetCrossDimensions(ship_geo.tauMudet.XCross, ship_geo.tauMudet.YCross, ship_geo.tauMudet.ZCross, ship_geo.tauMudet.WidthArm)
   taumuondetector.SetRpcOuterDimensions(ship_geo.tauMudet.XRpc_outer, ship_geo.tauMudet.YRpc_outer, ship_geo.tauMudet.ZRpc_outer)
   taumuondetector.SetRpcInnerDimensions(ship_geo.tauMudet.XRpc_inner, ship_geo.tauMudet.YRpc_inner, ship_geo.tauMudet.ZRpc_inner)
   taumuondetector.SetRpcGapDimensions(ship_geo.tauMudet.XRpcGap, ship_geo.tauMudet.YRpcGap, ship_geo.tauMudet.ZRpcGap)
   taumuondetector.SetPillarDimensions(ship_geo.tauMudet.PillarX,ship_geo.tauMudet.PillarY, ship_geo.tauMudet.PillarZ)
   detectorList.append(taumuondetector)
   if ship_geo.nuTauTargetDesign==3:
    if hasattr(ship_geo.tauMudet, "deltax"): #now replaced with veto taggers
     taumuondetector.SetRpcDimDifferences(ship_geo.tauMudet.deltax, ship_geo.tauMudet.deltay)
   if ship_geo.nuTauTargetDesign<3:
    taumuondetector.SetReturnYokeDimensions(ship_geo.tauMudet.XRyoke,ship_geo.tauMudet.YRyoke, ship_geo.tauMudet.ZRyoke)
    taumuondetector.SetSmallerYokeDimensions(ship_geo.tauMudet.XRyoke_s,ship_geo.tauMudet.YRyoke_s, ship_geo.tauMudet.ZRyoke_s)
    taumuondetector.SetZDimensionArm(ship_geo.tauMudet.ZArm)
    taumuondetector.SetGapDownstream(ship_geo.tauMudet.GapD)
    taumuondetector.SetGapMiddle(ship_geo.tauMudet.GapM)
    taumuondetector.SetMagneticField(ship_geo.tauMudet.B)
    taumuondetector.SetCoilParameters(ship_geo.tauMudet.CoilH, ship_geo.tauMudet.CoilW, ship_geo.tauMudet.N, ship_geo.tauMudet.CoilG)

   if ship_geo.nuTauTargetDesign==0 or ship_geo.nuTauTargetDesign==1 or ship_geo.nuTauTargetDesign==3:
    EmuMagnet = ROOT.EmulsionMagnet("EmuMagnet",ship_geo.EmuMagnet.zC,"EmulsionMagnet")
    EmuMagnet.SetDesign(ship_geo.EmuMagnet.Design)
    EmuMagnet.SetGaps(ship_geo.EmuMagnet.GapUp, ship_geo.EmuMagnet.GapDown)
    EmuMagnet.SetMagneticField(ship_geo.EmuMagnet.B)
    EmuMagnet.SetConstantField(ship_geo.EmuMagnet.WithConstField)
    EmuMagnet.SetMagnetSizes(ship_geo.EmuMagnet.X, ship_geo.EmuMagnet.Y, ship_geo.EmuMagnet.Z)
    if ship_geo.nuTauTargetDesign==0 or ship_geo.nuTauTargetDesign==1:
      EmuMagnet.SetCoilParameters(ship_geo.EmuMagnet.Radius, ship_geo.EmuMagnet.Height1, ship_geo.EmuMagnet.Height2, ship_geo.EmuMagnet.Distance)
    if ship_geo.nuTauTargetDesign==3:
      EmuMagnet.SetCoilParameters(ship_geo.EmuMagnet.CoilX,ship_geo.EmuMagnet.CoilY,ship_geo.EmuMagnet.Height1, ship_geo.EmuMagnet.Height2, ship_geo.EmuMagnet.Thickness) 
      EmuMagnet.SetCutDimensions(ship_geo.EmuMagnet.CutLength, ship_geo.EmuMagnet.CutHeight)
    EmuMagnet.SetMagnetColumn(ship_geo.EmuMagnet.ColX, ship_geo.EmuMagnet.ColY, ship_geo.EmuMagnet.ColZ)
    EmuMagnet.SetBaseDim(ship_geo.EmuMagnet.BaseX, ship_geo.EmuMagnet.BaseY, ship_geo.EmuMagnet.BaseZ)
    EmuMagnet.SetPillarDimensions(ship_geo.EmuMagnet.PillarX, ship_geo.EmuMagnet.PillarY, ship_geo.EmuMagnet.PillarZ)
    detectorList.append(EmuMagnet)
   if ship_geo.nuTauTargetDesign==2:
     EmuMagnet = ROOT.EmulsionMagnet()

   NuTauTarget = ROOT.Target("NuTauTarget",ship_geo.NuTauTarget.Ydist,ROOT.kTRUE)
   NuTauTarget.MakeNuTargetPassive(ship_geo.NuTauTarget.nuTargetPassive)
   if hasattr(ship_geo.NuTauTarget,"SingleEmFilm"): #for backward compatibility
    NuTauTarget.MergeTopBot(ship_geo.NuTauTarget.SingleEmFilm)
   NuTauTarget.SetDetectorDesign(ship_geo.NuTauTarget.Design)
   if ship_geo.nuTauTargetDesign!=3:
    NuTauTarget.SetCenterZ(ship_geo.NuTauTarget.zC)
   if ship_geo.nuTauTargetDesign==3:
    NuTauTarget.SetCenterZ(ship_geo.EmuMagnet.zC) #now the centers of emumagnet and nutautarget are different (target does not include HPT)
    NuTauTarget.SetNumberTargets(ship_geo.NuTauTarget.target)
    NuTauTarget.SetHpTParam(ship_geo.tauHPT.nHPT, ship_geo.tauHPT.distHPT, ship_geo.tauHPT.DZ) 
   NuTauTarget.SetNumberBricks(ship_geo.NuTauTarget.col,ship_geo.NuTauTarget.row,ship_geo.NuTauTarget.wall)
   NuTauTarget.SetDetectorDimension(ship_geo.NuTauTarget.xdim, ship_geo.NuTauTarget.ydim, ship_geo.NuTauTarget.zdim)
   if hasattr(ship_geo.NuTauTarget,"WallXDim") and hasattr(ship_geo.NuTauTarget,"WallYDim") and hasattr(ship_geo.NuTauTarget,"WallZDim"):
    NuTauTarget.SetTargetWallDimension(ship_geo.NuTauTarget.WallXDim, ship_geo.NuTauTarget.WallYDim, ship_geo.NuTauTarget.WallZDim)
   NuTauTarget.SetEmulsionParam(ship_geo.NuTauTarget.EmTh, ship_geo.NuTauTarget.EmX, ship_geo.NuTauTarget.EmY, ship_geo.NuTauTarget.PBTh,ship_geo.NuTauTarget.EPlW, ship_geo.NuTauTarget.LeadTh, ship_geo.NuTauTarget.AllPW)
##
   if not hasattr(ship_geo.NuTauTarget,"n_plates"): #for backward compatibility
    ship_geo.NuTauTarget.n_plates = 56
   NuTauTarget.SetBrickParam(ship_geo.NuTauTarget.BrX, ship_geo.NuTauTarget.BrY, ship_geo.NuTauTarget.BrZ, ship_geo.NuTauTarget.BrPackX, ship_geo.NuTauTarget.BrPackY, ship_geo.NuTauTarget.BrPackZ, ship_geo.NuTauTarget.n_plates)

   NuTauTarget.SetCESParam(ship_geo.NuTauTarget.RohG, ship_geo.NuTauTarget.LayerCESW, ship_geo.NuTauTarget.CESW, ship_geo.NuTauTarget.CESPack)
   NuTauTarget.SetCellParam(ship_geo.NuTauTarget.CellW)
   if ship_geo.nuTauTargetDesign==0 or ship_geo.nuTauTargetDesign==1:
    NuTauTarget.SetMagnetHeight(ship_geo.EmuMagnet.Y)
    NuTauTarget.SetColumnHeight(ship_geo.EmuMagnet.ColY)
    NuTauTarget.SetBaseHeight(ship_geo.EmuMagnet.BaseY)
    NuTauTarget.SetCoilUpHeight(ship_geo.EmuMagnet.Height1)
    NuTauTarget.SetCoilDownHeight(ship_geo.EmuMagnet.Height2)
   if ship_geo.nuTauTargetDesign!=2:
    NuTauTarget.SetMagneticField(ship_geo.EmuMagnet.B)
   if ship_geo.nuTauTargetDesign==2:
    NuTauTarget.SetPillarDimension(ship_geo.NuTauTarget.PillarX,ship_geo.NuTauTarget.PillarY,ship_geo.NuTauTarget.PillarZ)
    NuTauTarget.SetBaseDimension(ship_geo.NuTauTarget.BaseX, ship_geo.NuTauTarget.BaseY, ship_geo.NuTauTarget.BaseZ)
    
# Target Tracker 
   NuTauTT = ROOT.TargetTracker("TargetTrackers", ship_geo.NuTauTT.TTX, ship_geo.NuTauTT.TTY, ship_geo.NuTauTT.TTZ, ROOT.kTRUE)
   NuTauTT.SetDesign(ship_geo.NuTauTT.design)
   if hasattr(ship_geo.NuTauTT, "scifimat_width"):#for backward compatibility
    NuTauTT.SetSciFiParam(ship_geo.NuTauTT.scifimat_width, ship_geo.NuTauTT.scifimat_hor, ship_geo.NuTauTT.scifimat_vert, ship_geo.NuTauTT.scifimat_z, ship_geo.NuTauTT.support_z, ship_geo.NuTauTT.honeycomb_z)
    NuTauTT.SetNumberSciFi(ship_geo.NuTauTT.n_hor_planes, ship_geo.NuTauTT.n_vert_planes)
   NuTauTT.SetTargetTrackerParam(ship_geo.NuTauTT.TTX, ship_geo.NuTauTT.TTY, ship_geo.NuTauTT.TTZ)
   NuTauTT.SetBrickParam(ship_geo.NuTauTarget.CellW)
   NuTauTT.SetTotZDimension(ship_geo.NuTauTarget.zdim)
   NuTauTT.SetNumberTT(ship_geo.NuTauTT.n)
   # method of nutau target that must be called after TT parameter definition
   NuTauTarget.SetTTzdimension(ship_geo.NuTauTT.TTZ)
   detectorList.append(NuTauTarget)
   detectorList.append(NuTauTT)

# High Precision Tracker
   tauHpt = ROOT.Hpt("HighPrecisionTrackers",ship_geo.tauHPT.DX, ship_geo.tauHPT.DY, ship_geo.tauHPT.DZ, ROOT.kTRUE)
   tauHpt.SetZsize(ship_geo.tauMudet.Ztot)
   tauHpt.SetDesign(ship_geo.NuTauTarget.Design)
   if hasattr(ship_geo.tauHPT, "scifimat_width"):#for backward compatibility
    tauHpt.SetSciFiParam(ship_geo.tauHPT.scifimat_width, ship_geo.tauHPT.scifimat_hor, ship_geo.tauHPT.scifimat_vert, ship_geo.tauHPT.scifimat_z, ship_geo.tauHPT.support_z, ship_geo.tauHPT.honeycomb_z)
    tauHpt.SetNumberSciFi(ship_geo.tauHPT.n_hor_planes, ship_geo.tauHPT.n_vert_planes)
    tauHpt.SetHPTrackerParam(ship_geo.tauHPT.TX, ship_geo.tauHPT.TY, ship_geo.tauHPT.TZ)
   if ship_geo.nuTauTargetDesign<3:
    tauHpt.SetConcreteBaseDim(ship_geo.tauHPT.ConcreteX,ship_geo.tauHPT.ConcreteY,ship_geo.tauHPT.ConcreteZ)
   if ship_geo.nuTauTargetDesign==3:
    tauHpt.SetHPTNumber(ship_geo.tauHPT.nHPT)
    tauHpt.SetDistanceHPTs(ship_geo.tauHPT.distHPT)
    if hasattr(ship_geo.tauHPT, "SRDY"):
     tauHpt.SetSurroundingDetHeight(ship_geo.tauHPT.SRDY)
    tauHpt.GetMagnetGeometry(ship_geo.EmuMagnet.zC, ship_geo.EmuMagnet.Y)
    tauHpt.GetNumberofTargets(ship_geo.NuTauTarget.target)
   detectorList.append(tauHpt)

 # for backward compatibility
 if not hasattr(ship_geo.strawtubes, "YPlaneOffset"):
   ship_geo.strawtubes.YLayerOffset = ship_geo.strawtubes.StrawPitch  / 2.
   ship_geo.strawtubes.YPlaneOffset = ship_geo.strawtubes.StrawPitch  / 4.
 if ship_geo.strawDesign > 1 :
  # for backward compatibility
  if ship_geo.strawDesign == 10 and not hasattr(ship_geo.strawtubes, "DeltazFrame"):
   ship_geo.strawtubes.DeltazFrame = 2.5*u.cm
   ship_geo.strawtubes.FrameLateralWidth = 1.2*u.m
   ship_geo.strawtubes.FrameMaterial = "steel"
  elif not hasattr(ship_geo.strawtubes, "DeltazFrame"):
   ship_geo.strawtubes.DeltazFrame = 10.*u.cm
   ship_geo.strawtubes.FrameLateralWidth = 1.*u.cm
   ship_geo.strawtubes.FrameMaterial = "aluminium"

  Strawtubes = ROOT.strawtubes("Strawtubes", ROOT.kTRUE)    
  Strawtubes.SetZpositions(ship_geo.vetoStation.z, ship_geo.TrackStation1.z, ship_geo.TrackStation2.z, ship_geo.TrackStation3.z, ship_geo.TrackStation4.z)
  Strawtubes.SetDeltazFrame(ship_geo.strawtubes.DeltazFrame)
  Strawtubes.SetFrameLateralWidth(ship_geo.strawtubes.FrameLateralWidth)
  Strawtubes.SetFrameMaterial(ship_geo.strawtubes.FrameMaterial)
  Strawtubes.SetDeltazView(ship_geo.strawtubes.DeltazView)
  Strawtubes.SetInnerStrawDiameter(ship_geo.strawtubes.InnerStrawDiameter)
  Strawtubes.SetOuterStrawDiameter(ship_geo.strawtubes.OuterStrawDiameter)
  Strawtubes.SetStrawPitch(ship_geo.strawtubes.StrawPitch,ship_geo.strawtubes.YLayerOffset,ship_geo.strawtubes.YPlaneOffset)
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

 if ship_geo.EcalOption == 1:  # shashlik design TP 
  if ship_geo.preshowerOption > 0 :
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

 if ship_geo.EcalOption == 2:  # splitCal with pointing information
  SplitCal = ROOT.splitcal("SplitCal", ROOT.kTRUE)
  x = ship_geo.SplitCal 
  SplitCal.SetThickness(x.ActiveECALThickness,x.ActiveHCALThickness,x.FilterECALThickness,x.FilterECALThickness_first,x.FilterHCALThickness,x.ActiveECAL_gas_Thickness)
  SplitCal.SetMaterial(x.ActiveECALMaterial,x.ActiveHCALMaterial,x.FilterECALMaterial ,x.FilterHCALMaterial)
  SplitCal.SetNSamplings(x.nECALSamplings,x.nHCALSamplings,x.ActiveHCAL)
  SplitCal.SetZStart(x.ZStart)
  SplitCal.SetXMax(x.XMax)
  SplitCal.SetYMax(x.YMax)
  SplitCal.SetEmpty(x.Empty,x.BigGap,x.ActiveECAL_gas_gap,x.first_precision_layer,x.second_precision_layer,x.third_precision_layer,x.num_precision_layers)
  SplitCal.SetNModules(x.NModulesInX, x.NModulesInY)
  SplitCal.SetNStrips(x.NStripsPerModule)
  SplitCal.SetStripSize(x.StripHalfWidth, x.StripHalfLength)
  detectorList.append(SplitCal)

 if not ship_geo.HcalOption < 0:
  hcal,HcalZSize = posHcal(ship_geo.hcal.z,ship_geo.hcal.File,ship_geo.HcalOption)
  if ship_geo.HcalOption!=2 and abs(ship_geo.hcal.hcalSpace -  HcalZSize) > 10*u.cm:
    print('mismatch between hcalsize in geo file and python configuration')
    print(ship_geo.hcal.hcalSpace -  HcalZSize, ship_geo.hcal.hcalSpace , HcalZSize)
  detectorList.append(hcal)
 Muon = ROOT.muon("Muon", ROOT.kTRUE)
 Muon.SetZStationPositions(ship_geo.MuonStation0.z, ship_geo.MuonStation1.z,ship_geo.MuonStation2.z,ship_geo.MuonStation3.z)
 Muon.SetZFilterPositions(ship_geo.MuonFilter0.z, ship_geo.MuonFilter1.z,ship_geo.MuonFilter2.z)
 Muon.SetXMax(ship_geo.Muon.XMax)
 Muon.SetYMax(ship_geo.Muon.YMax)
 Muon.SetActiveThickness(ship_geo.Muon.ActiveThickness)
 Muon.SetFilterThickness(ship_geo.Muon.FilterThickness)
 detectorList.append(Muon)

 upstreamTagger = ROOT.UpstreamTagger("UpstreamTagger", ROOT.kTRUE)
 upstreamTagger.SetZposition(ship_geo.UpstreamTagger.Z_Position)
 upstreamTagger.SetSizeX_Glass(ship_geo.UpstreamTagger.X_Glass)
 upstreamTagger.SetSizeY_Glass(ship_geo.UpstreamTagger.Y_Glass)
 upstreamTagger.SetSizeZ_Glass(ship_geo.UpstreamTagger.Z_Glass)
 upstreamTagger.SetSizeX_Glass_Border(ship_geo.UpstreamTagger.X_Glass_Border)
 upstreamTagger.SetSizeY_Glass_Border(ship_geo.UpstreamTagger.Y_Glass_Border)
 upstreamTagger.SetSizeZ_Glass_Border(ship_geo.UpstreamTagger.Z_Glass_Border)
 upstreamTagger.SetSizeX_PMMA(ship_geo.UpstreamTagger.X_PMMA)
 upstreamTagger.SetSizeY_PMMA(ship_geo.UpstreamTagger.Y_PMMA)
 upstreamTagger.SetSizeZ_PMMA(ship_geo.UpstreamTagger.Z_PMMA)
 upstreamTagger.SetSizeDX_PMMA(ship_geo.UpstreamTagger.DX_PMMA)
 upstreamTagger.SetSizeDY_PMMA(ship_geo.UpstreamTagger.DY_PMMA)
 upstreamTagger.SetSizeDZ_PMMA(ship_geo.UpstreamTagger.DZ_PMMA)
 upstreamTagger.SetSizeX_FreonSF6(ship_geo.UpstreamTagger.X_FreonSF6)
 upstreamTagger.SetSizeY_FreonSF6(ship_geo.UpstreamTagger.Y_FreonSF6)
 upstreamTagger.SetSizeZ_FreonSF6(ship_geo.UpstreamTagger.Z_FreonSF6)
 upstreamTagger.SetSizeX_FreonSF6_2(ship_geo.UpstreamTagger.X_FreonSF6_2)
 upstreamTagger.SetSizeY_FreonSF6_2(ship_geo.UpstreamTagger.Y_FreonSF6_2)
 upstreamTagger.SetSizeZ_FreonSF6_2(ship_geo.UpstreamTagger.Z_FreonSF6_2)
 upstreamTagger.SetSizeX_FR4(ship_geo.UpstreamTagger.X_FR4)
 upstreamTagger.SetSizeY_FR4(ship_geo.UpstreamTagger.Y_FR4)
 upstreamTagger.SetSizeZ_FR4(ship_geo.UpstreamTagger.Z_FR4)
 upstreamTagger.SetSizeX_Al(ship_geo.UpstreamTagger.X_Aluminium)
 upstreamTagger.SetSizeY_Al(ship_geo.UpstreamTagger.Y_Aluminium)
 upstreamTagger.SetSizeZ_Al(ship_geo.UpstreamTagger.Z_Aluminium)
 upstreamTagger.SetSizeDX_Al(ship_geo.UpstreamTagger.DX_Aluminium)
 upstreamTagger.SetSizeDY_Al(ship_geo.UpstreamTagger.DY_Aluminium)
 upstreamTagger.SetSizeDZ_Al(ship_geo.UpstreamTagger.DZ_Aluminium)
 upstreamTagger.SetSizeX_Air(ship_geo.UpstreamTagger.X_Air)
 upstreamTagger.SetSizeY_Air(ship_geo.UpstreamTagger.Y_Air)
 upstreamTagger.SetSizeZ_Air(ship_geo.UpstreamTagger.Z_Air)
 upstreamTagger.SetSizeX_Strip(ship_geo.UpstreamTagger.X_Strip)
 upstreamTagger.SetSizeY_Strip(ship_geo.UpstreamTagger.Y_Strip)
 upstreamTagger.SetSizeX_Strip64(ship_geo.UpstreamTagger.X_Strip64)
 upstreamTagger.SetSizeY_Strip64(ship_geo.UpstreamTagger.Y_Strip64)
 upstreamTagger.SetSizeZ_Strip(ship_geo.UpstreamTagger.Z_Strip)
 detectorList.append(upstreamTagger)

 timeDet = ROOT.TimeDet("TimeDet", ROOT.kTRUE)
 timeDet.SetZposition(ship_geo.TimeDet.z)
 timeDet.SetBarZspacing(ship_geo.TimeDet.dzBarRow, ship_geo.TimeDet.dzBarCol)
 timeDet.SetBarZ(ship_geo.TimeDet.zBar)
 timeDet.SetSizeX(2 * ship_geo.TimeDet.DX)
 timeDet.SetSizeY(2 * ship_geo.TimeDet.DY)
 detectorList.append(timeDet)

#-----   Magnetic field   -------------------------------------------
 if not hasattr(ship_geo.Bfield,"fieldMap"):
  if ship_geo.strawDesign == 4 or ship_geo.strawDesign == 10 : fMagField = ROOT.ShipBellField("wilfried", ship_geo.Bfield.max ,ship_geo.Bfield.z,2,ship_geo.Yheight/2.*u.m )  
  else :                                                      fMagField = ROOT.ShipBellField("wilfried", ship_geo.Bfield.max ,ship_geo.Bfield.z,1,ship_geo.Yheight/2.*u.m )  
  if ship_geo.muShieldDesign==6: fMagField.IncludeTarget(ship_geo.target.xy, ship_geo.target.z0, ship_geo.target.length)
  run.SetField(fMagField)
#
 exclusionList = []
 #exclusionList = ["Muon","Ecal","Hcal","Strawtubes","TargetTrackers","NuTauTarget","HighPrecisionTrackers",\
 #                 "Veto","Magnet","MuonShield","TargetStation","NuTauMudet","EmuMagnet", "TimeDet", "UpstreamTagger"]

 for x in detectorList:
   if x.GetName() in exclusionList: continue
   run.AddModule(x)
# return list of detector elements
 detElements = {}
 for x in run.GetListOfModules(): detElements[x.GetName()]=x
 return detElements
