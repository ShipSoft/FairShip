#!/usr/bin/env python
# -*- coding: latin-1 -*-
import ROOT,os
import shipunit as u
from ShipGeoConfig import ConfigRegistry
detectorList = []

def getParameter(x,ship_geo,latestCharmGeo):
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
  a = getattr(latestCharmGeo,top)
  return getattr(a,last)

def configure(run,ship_geo,Gfield=''):
 latestCharmGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/charm-geometry_config.py")
# -----Create media-------------------------------------------------
 run.SetMaterials("media.geo")  # Materials
 
# -----Create geometry----------------------------------------------
 cave= ROOT.ShipCave("CAVE")
 cave.SetGeometryFileName("caveWithAir.geo")
 detectorList.append(cave)
    

 if (ship_geo.MufluxSpectrometer.muflux==False):
# === Emulsion Target 
    Box = ROOT.Box("Box",ship_geo.Box.BrX, ship_geo.Box.BrY, ship_geo.Box.BrZ, ship_geo.Box.zBox,ROOT.kTRUE)
    Box.SetEmulsionParam(ship_geo.Box.EmTh, ship_geo.Box.EmX, ship_geo.Box.EmY, ship_geo.Box.PBTh,ship_geo.Box.EPlW, ship_geo.Box.PasSlabTh, ship_geo.Box.AllPW);
    Box.SetBrickParam(ship_geo.Box.BrX, ship_geo.Box.BrY, ship_geo.Box.BrZ, ship_geo.Box.BrPackX, ship_geo.Box.BrPackY, ship_geo.Box.BrPackZ);
    Box.SetTargetParam(ship_geo.Box.TX, ship_geo.Box.TY, ship_geo.Box.TZ);
    Box.SetPassiveComposition(ship_geo.Box.Molblock1Z, ship_geo.Box.Molblock2Z, ship_geo.Box.Molblock3Z, ship_geo.Box.Molblock4Z, ship_geo.Box.Wblock1Z, ship_geo.Box.Wblock2Z, ship_geo.Box.Wblock3Z, ship_geo.Box.Wblock3_5Z, ship_geo.Box.Wblock4Z)
    Box.SetPassiveSampling(ship_geo.Box.Passive3mmZ, ship_geo.Box.Passive2mmZ, ship_geo.Box.Passive1mmZ)
    Box.SetCoolingParam(ship_geo.Box.CoolX, ship_geo.Box.CoolY, ship_geo.Box.CoolZ)
    Box.SetCoatingParam(ship_geo.Box.CoatX, ship_geo.Box.CoatY, ship_geo.Box.CoatZ)
    Box.SetGapGeometry(ship_geo.Box.distancePassive2ECC)
    Box.SetTargetDesign(ship_geo.Box.Julytarget)
    Box.SetRunNumber(ship_geo.Box.RunNumber)
    detectorList.append(Box)
# === SciFi modules
    SciFi = ROOT.SciFi("SciFi",ship_geo.SciFi.DX, ship_geo.SciFi.DY, ship_geo.SciFi.DZ,ROOT.kTRUE)
    SciFi.SetBoxParam(ship_geo.SciFi.DX,ship_geo.SciFi.DY,ship_geo.SciFi.DZ, ship_geo.SciFi.zBox)
    SciFi.SetStationNumber(ship_geo.SciFi.nstations)
    SciFi.SetStationDimensions(ship_geo.SciFi.StationDimX, ship_geo.SciFi.StationDimY, ship_geo.SciFi.StationDimZ)
    for i, (x, y, z) in enumerate(zip(ship_geo.SciFi.xSi,ship_geo.SciFi.ySi,ship_geo.SciFi.zSi)):
      SciFi.SetStationPositions(i, x, y, z)
# === Pixel modules
    PixelModules = ROOT.PixelModules("PixelModules", ship_geo.PixelModules.DX, ship_geo.PixelModules.DY,
                                         ship_geo.PixelModules.DZ, ROOT.kTRUE, ship_geo.PixelModules.nSlice)
    PixelModules.SetBoxParam(ship_geo.PixelModules.DX, ship_geo.PixelModules.DY, ship_geo.PixelModules.DZ, ship_geo.PixelModules.zBox, 
                                 ship_geo.PixelModules.DimZpixelbox, ship_geo.PixelModules.D1short, ship_geo.PixelModules.D1long, 
                                 ship_geo.PixelModules.DimZSithin, ship_geo.PixelModules.DimZSithick, ship_geo.PixelModules.z_offset)
# === SciFi modules
    detectorList.append(SciFi)
# === Pixel modules
    detectorList.append(PixelModules)
    for i, (x, y, z) in enumerate(zip(ship_geo.PixelModules.xSi,ship_geo.PixelModules.ySi,ship_geo.PixelModules.zSi)):
      PixelModules.SetSiliconStationPositions(i, x, y, z)

 Spectrometer = ROOT.Spectrometer("Spectrometer",ship_geo.Spectrometer.DX, ship_geo.Spectrometer.DY, ship_geo.Spectrometer.DZ,ROOT.kTRUE)
 Spectrometer.SetTransverseSizes(ship_geo.Spectrometer.D1Short, ship_geo.Spectrometer.D1Long)
# -----Goliath part by Annarita--------
 Spectrometer.SetGoliathSizes(ship_geo.Spectrometer.H, ship_geo.Spectrometer.TS, ship_geo.Spectrometer.LS, ship_geo.Spectrometer.BasisH);
 Spectrometer.SetCoilParameters(ship_geo.Spectrometer.CoilR, ship_geo.Spectrometer.UpCoilH, ship_geo.Spectrometer.LowCoilH,  ship_geo.Spectrometer.CoilD);
# --------------------------------------
 Spectrometer.SetBoxParam(ship_geo.Spectrometer.SX,ship_geo.Spectrometer.SY,ship_geo.Spectrometer.SZ,ship_geo.Spectrometer.zBox)
 if (ship_geo.MufluxSpectrometer.muflux==False):
  MufluxSpectrometer = ROOT.MufluxSpectrometer("MufluxSpectrometer",ship_geo.MufluxSpectrometer.DX, ship_geo.MufluxSpectrometer.DY,   ship_geo.MufluxSpectrometer.DZ,ROOT.kTRUE)
 else:
  MufluxSpectrometer = ROOT.MufluxSpectrometer("MufluxSpectrometer",ship_geo.Spectrometer.DX, ship_geo.Spectrometer.DY, ship_geo.Spectrometer.DZ,ROOT.kTRUE)
 # -----Drift tube part --------
 
 MufluxSpectrometer.SetGoliathSizes(ship_geo.Spectrometer.H, ship_geo.Spectrometer.TS, ship_geo.Spectrometer.LS, ship_geo.Spectrometer.BasisH);
 MufluxSpectrometer.SetCoilParameters(ship_geo.Spectrometer.CoilR, ship_geo.Spectrometer.UpCoilH, ship_geo.Spectrometer.LowCoilH,  ship_geo.Spectrometer.CoilD);
# --------------------------------------
 
 MufluxSpectrometer.ChooseDetector(ship_geo.MufluxSpectrometer.muflux)
 MufluxSpectrometer.SetDeltazView(ship_geo.MufluxSpectrometer.DeltazView)
 MufluxSpectrometer.SetInnerTubeDiameter(ship_geo.MufluxSpectrometer.InnerTubeDiameter)
 MufluxSpectrometer.SetOuterTubeDiameter(ship_geo.MufluxSpectrometer.OuterTubeDiameter)
 MufluxSpectrometer.SetTubePitch(ship_geo.MufluxSpectrometer.TubePitch)
 MufluxSpectrometer.SetTubePitch_T1u(ship_geo.MufluxSpectrometer.TubePitch_T1u,ship_geo.MufluxSpectrometer.T1u_const,ship_geo.MufluxSpectrometer.T1u_const_2,ship_geo.MufluxSpectrometer.T1u_const_3,ship_geo.MufluxSpectrometer.T1u_const_4)
 MufluxSpectrometer.SetTubePitch_T2v(ship_geo.MufluxSpectrometer.TubePitch_T2v,ship_geo.MufluxSpectrometer.T2v_const,ship_geo.MufluxSpectrometer.T2v_const_2,ship_geo.MufluxSpectrometer.T2v_const_3,ship_geo.MufluxSpectrometer.T2v_const_4) 
 MufluxSpectrometer.SetDeltazLayer(ship_geo.MufluxSpectrometer.DeltazLayer)
 MufluxSpectrometer.SetDeltazPlane(ship_geo.MufluxSpectrometer.DeltazPlane)
 MufluxSpectrometer.SetTubesPerLayer(ship_geo.MufluxSpectrometer.TubesPerLayer)
 MufluxSpectrometer.SetStereoAngle(ship_geo.MufluxSpectrometer.ViewAngle, ship_geo.MufluxSpectrometer.ViewvAngle)
 MufluxSpectrometer.SetWireThickness(ship_geo.MufluxSpectrometer.WireThickness)
 MufluxSpectrometer.SetTubeLength(ship_geo.MufluxSpectrometer.TubeLength)
 MufluxSpectrometer.SetTubeLength12(ship_geo.MufluxSpectrometer.TubeLength12) 
 MufluxSpectrometer.SetTr12YDim(ship_geo.MufluxSpectrometer.tr12ydim)
 MufluxSpectrometer.SetTr34YDim(ship_geo.MufluxSpectrometer.tr34ydim)
 MufluxSpectrometer.SetTr12XDim(ship_geo.MufluxSpectrometer.tr12xdim)
 MufluxSpectrometer.SetTr34XDim(ship_geo.MufluxSpectrometer.tr34xdim) 
 MufluxSpectrometer.SetDistStereo(ship_geo.MufluxSpectrometer.diststereoT1,ship_geo.MufluxSpectrometer.diststereoT2)
 MufluxSpectrometer.SetDistT1T2(ship_geo.MufluxSpectrometer.distT1T2)
 MufluxSpectrometer.SetDistT3T4(ship_geo.MufluxSpectrometer.distT3T4)    
 MufluxSpectrometer.SetGoliathCentre(ship_geo.MufluxSpectrometer.goliathcentre_to_beam)
 MufluxSpectrometer.SetGoliathCentreZ(ship_geo.MufluxSpectrometer.goliathcentre)
 MufluxSpectrometer.SetT3StationsZcorr(ship_geo.MufluxSpectrometer.T3z_1,ship_geo.MufluxSpectrometer.T3z_2,ship_geo.MufluxSpectrometer.T3z_3,ship_geo.MufluxSpectrometer.T3z_4) 
 MufluxSpectrometer.SetT4StationsZcorr(ship_geo.MufluxSpectrometer.T4z_1,ship_geo.MufluxSpectrometer.T4z_2,ship_geo.MufluxSpectrometer.T4z_3,ship_geo.MufluxSpectrometer.T4z_4) 
 MufluxSpectrometer.SetT3StationsXcorr(ship_geo.MufluxSpectrometer.T3x_1,ship_geo.MufluxSpectrometer.T3x_2,ship_geo.MufluxSpectrometer.T3x_3,ship_geo.MufluxSpectrometer.T3x_4) 
 MufluxSpectrometer.SetT4StationsXcorr(ship_geo.MufluxSpectrometer.T4x_1,ship_geo.MufluxSpectrometer.T4x_2,ship_geo.MufluxSpectrometer.T4x_3,ship_geo.MufluxSpectrometer.T4x_4)
 MufluxSpectrometer.SetTStationsZ(ship_geo.MufluxSpectrometer.T1z,ship_geo.MufluxSpectrometer.T1x_z,ship_geo.MufluxSpectrometer.T1u_z,ship_geo.MufluxSpectrometer.T2z,ship_geo.MufluxSpectrometer.T2v_z,ship_geo.MufluxSpectrometer.T2x_z,ship_geo.MufluxSpectrometer.T3z,ship_geo.MufluxSpectrometer.T4z) 
 MufluxSpectrometer.SetTStationsX(ship_geo.MufluxSpectrometer.T1x_x,ship_geo.MufluxSpectrometer.T1u_x,ship_geo.MufluxSpectrometer.T2x_x,ship_geo.MufluxSpectrometer.T2v_x,ship_geo.MufluxSpectrometer.T3x,ship_geo.MufluxSpectrometer.T4x) 
 MufluxSpectrometer.SetTStationsY(ship_geo.MufluxSpectrometer.T1x_y,ship_geo.MufluxSpectrometer.T1u_y,ship_geo.MufluxSpectrometer.T2x_y,ship_geo.MufluxSpectrometer.T2v_y,ship_geo.MufluxSpectrometer.T3y,ship_geo.MufluxSpectrometer.T4y) 

 if (ship_geo.MufluxSpectrometer.muflux==False):
 ##Survey Results from charm by daniel
  MufluxSpectrometer.SetT3(ship_geo.MufluxSpectrometer.SurveyCharm_T3ax,ship_geo.MufluxSpectrometer.SurveyCharm_T3ay,ship_geo.MufluxSpectrometer.SurveyCharm_T3az,0)
  MufluxSpectrometer.SetT3(ship_geo.MufluxSpectrometer.SurveyCharm_T3bx,ship_geo.MufluxSpectrometer.SurveyCharm_T3by,ship_geo.MufluxSpectrometer.SurveyCharm_T3bz,1)
  MufluxSpectrometer.SetT3(ship_geo.MufluxSpectrometer.SurveyCharm_T3cx,ship_geo.MufluxSpectrometer.SurveyCharm_T3cy,ship_geo.MufluxSpectrometer.SurveyCharm_T3cz,2)
  MufluxSpectrometer.SetT3(ship_geo.MufluxSpectrometer.SurveyCharm_T3dx,ship_geo.MufluxSpectrometer.SurveyCharm_T3dy,ship_geo.MufluxSpectrometer.SurveyCharm_T3dz,3)
  MufluxSpectrometer.SetT3(ship_geo.MufluxSpectrometer.SurveyCharm_T3tx,ship_geo.MufluxSpectrometer.SurveyCharm_T3ty,ship_geo.MufluxSpectrometer.SurveyCharm_T3tz,4)

  MufluxSpectrometer.SetT4(ship_geo.MufluxSpectrometer.SurveyCharm_T4ax,ship_geo.MufluxSpectrometer.SurveyCharm_T4ay,ship_geo.MufluxSpectrometer.SurveyCharm_T4az,0)
  MufluxSpectrometer.SetT4(ship_geo.MufluxSpectrometer.SurveyCharm_T4bx,ship_geo.MufluxSpectrometer.SurveyCharm_T4by,ship_geo.MufluxSpectrometer.SurveyCharm_T4bz,1)
  MufluxSpectrometer.SetT4(ship_geo.MufluxSpectrometer.SurveyCharm_T4cx,ship_geo.MufluxSpectrometer.SurveyCharm_T4cy,ship_geo.MufluxSpectrometer.SurveyCharm_T4cz,2)
  MufluxSpectrometer.SetT4(ship_geo.MufluxSpectrometer.SurveyCharm_T4dx,ship_geo.MufluxSpectrometer.SurveyCharm_T4dy,ship_geo.MufluxSpectrometer.SurveyCharm_T4dz,3)
  MufluxSpectrometer.SetT4(ship_geo.MufluxSpectrometer.SurveyCharm_T4tx,ship_geo.MufluxSpectrometer.SurveyCharm_T4ty,ship_geo.MufluxSpectrometer.SurveyCharm_T4tz,4)

 
 # for the digitizing step
 MufluxSpectrometer.SetTubeResolution(ship_geo.MufluxSpectrometer.v_drift,ship_geo.MufluxSpectrometer.sigma_spatial) 
  
 if (ship_geo.MufluxSpectrometer.muflux==False): 
    detectorList.append(MufluxSpectrometer)
 else:
 # Scintillator and Target Station classes for muflux configuration
    Scintillator = ROOT.Scintillator("Scintillator",ROOT.kTRUE)
    Scintillator.SetScoring1XY(ship_geo.MufluxSpectrometer.tr12xdim,ship_geo.MufluxSpectrometer.tr12ydim)
    Scintillator.SetDistT1(ship_geo.Scintillator.DistT1)
    Scintillator.SetDistT2(ship_geo.Scintillator.DistT2) 
    Scintillator.SetS_T1coords(ship_geo.MufluxSpectrometer.T1x_x,ship_geo.MufluxSpectrometer.T1x_y) 
    Scintillator.SetS_T2coords(ship_geo.MufluxSpectrometer.T2x_x,ship_geo.MufluxSpectrometer.T2x_y)  

    TargetStation = ROOT.MufluxTargetStation("MufluxTargetStation",ship_geo.target.length,ship_geo.hadronAbsorber.length, ship_geo.target.z,ship_geo.hadronAbsorber.z,ship_geo.targetOpt,ship_geo.target.sl)
    
    TargetStation.SetIronAbsorber(ship_geo.MufluxTargetStation.absorber_x,ship_geo.MufluxTargetStation.absorber_y)
    TargetStation.SetAbsorberCutout(ship_geo.MufluxTargetStation.absorbercutout_x, ship_geo.MufluxTargetStation.absorbercutout_y)
    TargetStation.SetIronShield(ship_geo.MufluxTargetStation.ironshield_x, ship_geo.MufluxTargetStation.ironshield_y, ship_geo.MufluxTargetStation.ironshield_z)
    TargetStation.SetConcreteShield(ship_geo.MufluxTargetStation.concreteshield_x, ship_geo.MufluxTargetStation.concreteshield_y, ship_geo.MufluxTargetStation.concreteshield_z)
    TargetStation.SetAboveTargetShield(ship_geo.MufluxTargetStation.abovetargetshield_x, ship_geo.MufluxTargetStation.abovetargetshield_y,ship_geo.MufluxTargetStation.abovetargetshield_z)
    TargetStation.SetAboveAbsorberShield(ship_geo.MufluxTargetStation.aboveabsorbershield_x, ship_geo.MufluxTargetStation.aboveabsorbershield_y,ship_geo.MufluxTargetStation.aboveabsorbershield_z)
    TargetStation.SetAboveAboveTargetShield(ship_geo.MufluxTargetStation.aboveabovetargetshield_y)
    TargetStation.SetFloor(ship_geo.MufluxTargetStation.floor_x,ship_geo.MufluxTargetStation.floor_y,ship_geo.MufluxTargetStation.floor_z)
    TargetStation.SetFloorT34(ship_geo.MufluxTargetStation.floorT34_x,ship_geo.MufluxTargetStation.floorT34_y,ship_geo.MufluxTargetStation.floorT34_z)
    TargetStation.SetFloorRPC(ship_geo.MufluxTargetStation.floorRPC_x, ship_geo.MufluxTargetStation.floorRPC_y,ship_geo.MufluxTargetStation.floorRPC_z)

    if ship_geo.targetOpt>10:
     slices_length=ROOT.std.vector('float')()     
     slices_material=ROOT.std.vector('string')()
     for i in range(1,ship_geo.targetOpt+1):
      slices_length.push_back(eval("ship_geo.target.L"+str(i)))
      slices_material.push_back(eval("ship_geo.target.M"+str(i)))

     TargetStation.SetLayerPosMat(ship_geo.target.xy,slices_length,slices_material)
     detectorList.append(TargetStation)
     
    detectorList.append(Scintillator)
    detectorList.append(MufluxSpectrometer)
   
 MuonTagger = ROOT.MuonTagger("MuonTagger", ship_geo.MuonTagger.BX, ship_geo.MuonTagger.BY, ship_geo.MuonTagger.BZ, ship_geo.MuonTagger.zBox, ROOT.kTRUE)
 MuonTagger.SetPassiveParameters(ship_geo.MuonTagger.PX, ship_geo.MuonTagger.PY, ship_geo.MuonTagger.PTh, ship_geo.MuonTagger.PTh1)
 MuonTagger.SetSensitiveParameters(ship_geo.MuonTagger.SX, ship_geo.MuonTagger.SY, ship_geo.MuonTagger.STh)
 MuonTagger.SetHoleDimensions(ship_geo.MuonTagger.HX, ship_geo.MuonTagger.HY)
 MuonTagger.SetRPCz(ship_geo.MuonTagger.RPC1z, ship_geo.MuonTagger.RPC2z, ship_geo.MuonTagger.RPC3z, ship_geo.MuonTagger.RPC4z, ship_geo.MuonTagger.RPC5z)
 MuonTagger.SetRPCThickness(ship_geo.MuonTagger.RPCthickness)
 MuonTagger.SetGapThickness(ship_geo.MuonTagger.Gapthickness)
 MuonTagger.SetElectrodeThickness(ship_geo.MuonTagger.Electrodethickness)
 MuonTagger.SetStripz(ship_geo.MuonTagger.Stripz, ship_geo.MuonTagger.Stripfoamz)
 MuonTagger.SetVStrip(ship_geo.MuonTagger.VStripx,ship_geo.MuonTagger.VStripx_L,ship_geo.MuonTagger.VStripx_R,ship_geo.MuonTagger.VStripoffset) 
 MuonTagger.SetHStrip(ship_geo.MuonTagger.HStripy,ship_geo.MuonTagger.HStripy_ext,ship_geo.MuonTagger.HStripoffset)  
 MuonTagger.SetNStrips(ship_geo.MuonTagger.NVstrips,ship_geo.MuonTagger.NHstrips) 
  
 detectorList.append(MuonTagger)
 for x in detectorList:
  run.AddModule(x)
  
 fMagField = ROOT.ShipGoliathField()
 if Gfield == '':  
  #default field map
  fieldfile = os.environ["FAIRSHIP"]+"/field/GoliathFieldMap.root"
 elif Gfield == 'inter': 
  fieldfile = os.environ["FAIRSHIP"]+"/field/GoliathFieldMap_2400A_1167A.root" 
 elif Gfield == 'noDavid':
  fieldfile = os.environ["FAIRSHIP"]+"/field/GoliathFieldMap_3600A_0A.root"  
 fMagField.Init(fieldfile)
 run.SetField(fMagField)
 
# return list of detector elements
 detElements = {}
 for x in run.GetListOfModules(): detElements[x.GetName()]=x 
 
 return detElements
