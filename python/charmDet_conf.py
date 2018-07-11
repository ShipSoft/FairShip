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

def configure(run,ship_geo):
 latestCharmGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/charm-geometry_config.py")
# -----Create media-------------------------------------------------
 run.SetMaterials("media.geo")  # Materials
 
# -----Create geometry----------------------------------------------
 cave= ROOT.ShipCave("CAVE")
 cave.SetGeometryFileName("caveWithAir.geo")
 detectorList.append(cave)
    
 Box = ROOT.Box("Box",ship_geo.Box.BrX, ship_geo.Box.BrY, ship_geo.Box.BrZ, ship_geo.Box.zBox,ROOT.kTRUE)
 Box.SetEmulsionParam(ship_geo.Box.EmTh, ship_geo.Box.EmX, ship_geo.Box.EmY, ship_geo.Box.PBTh,ship_geo.Box.EPlW, ship_geo.Box.PasSlabTh, ship_geo.Box.AllPW);
 Box.SetBrickParam(ship_geo.Box.BrX, ship_geo.Box.BrY, ship_geo.Box.BrZ, ship_geo.Box.BrPackX, ship_geo.Box.BrPackY, ship_geo.Box.BrPackZ);
 Box.SetTargetParam(ship_geo.Box.TX, ship_geo.Box.TY, ship_geo.Box.TZ);
 Box.SetPassiveComposition(ship_geo.Box.Molblock1Z, ship_geo.Box.Molblock2Z, ship_geo.Box.Molblock3Z, ship_geo.Box.Molblock4Z, ship_geo.Box.Wblock1Z, ship_geo.Box.Wblock2Z, ship_geo.Box.Wblock3Z, ship_geo.Box.Wblock3_5Z, ship_geo.Box.Wblock4Z)
 Box.SetPassiveSampling(ship_geo.Box.Passive3mmZ, ship_geo.Box.Passive2mmZ, ship_geo.Box.Passive1mmZ)
 Box.SetCoolingParam(ship_geo.Box.CoolX, ship_geo.Box.CoolY, ship_geo.Box.CoolZ)
 Box.SetCoatingParam(ship_geo.Box.CoatX, ship_geo.Box.CoatY, ship_geo.Box.CoatZ)
 Box.SetGapGeometry(ship_geo.Box.GapPostTargetTh)
 Box.SetTargetDesign(ship_geo.Box.Julytarget)
 Box.SetRunNumber(ship_geo.Box.RunNumber)

 if (ship_geo.MufluxSpectrometer.muflux==False): 
    detectorList.append(Box)
   
 Spectrometer = ROOT.Spectrometer("Spectrometer",ship_geo.Spectrometer.DX, ship_geo.Spectrometer.DY, ship_geo.Spectrometer.DZ,ROOT.kTRUE)
 Spectrometer.SetTransverseSizes(ship_geo.Spectrometer.D1Short, ship_geo.Spectrometer.D1Long, ship_geo.Spectrometer.Sioverlap, ship_geo.Spectrometer.DSciFi1X, ship_geo.Spectrometer.DSciFi1Y, ship_geo.Spectrometer.DSciFi2X, ship_geo.Spectrometer.DSciFi2Y)   
 Spectrometer.SetSiliconDZ(ship_geo.Spectrometer.DimZSi)
 #Spectrometer.SetSiliconDetNumber(ship_geo.Spectrometer.nSiDet)
 Spectrometer.SetSiliconDetPositions(ship_geo.Spectrometer.zSi0,ship_geo.Spectrometer.zSi1, ship_geo.Spectrometer.zSi2,ship_geo.Spectrometer.zSi3,ship_geo.Spectrometer.zSi4, ship_geo.Spectrometer.zSi5, ship_geo.Spectrometer.PairSiDistance)
 Spectrometer.SetSciFiDetPositions(ship_geo.Spectrometer.zSciFi1, ship_geo.Spectrometer.zSciFi2)
# -----Goliath part by Annarita--------
 Spectrometer.SetGoliathSizes(ship_geo.Spectrometer.H, ship_geo.Spectrometer.TS, ship_geo.Spectrometer.LS, ship_geo.Spectrometer.BasisH);
 Spectrometer.SetCoilParameters(ship_geo.Spectrometer.CoilR, ship_geo.Spectrometer.UpCoilH, ship_geo.Spectrometer.LowCoilH,  ship_geo.Spectrometer.CoilD);
# --------------------------------------
 Spectrometer.SetBoxParam(ship_geo.Spectrometer.SX,ship_geo.Spectrometer.SY,ship_geo.Spectrometer.SZ,ship_geo.Spectrometer.zBox, ship_geo.Spectrometer.DimZpixelbox) 
 if (ship_geo.MufluxSpectrometer.muflux==False):
  MufluxSpectrometer = ROOT.MufluxSpectrometer("MufluxSpectrometer",ship_geo.MufluxSpectrometer.DX, ship_geo.MufluxSpectrometer.DY,   ship_geo.MufluxSpectrometer.DZ,ROOT.kTRUE)
 else:
  MufluxSpectrometer = ROOT.MufluxSpectrometer("MufluxSpectrometer",ship_geo.Spectrometer.DX, ship_geo.Spectrometer.DY, ship_geo.Spectrometer.DZ,ROOT.kTRUE)
 # -----Drift tube part --------
 
 MufluxSpectrometer.SetGoliathSizes(ship_geo.Spectrometer.H, ship_geo.Spectrometer.TS, ship_geo.Spectrometer.LS, ship_geo.Spectrometer.BasisH);
 MufluxSpectrometer.SetCoilParameters(ship_geo.Spectrometer.CoilR, ship_geo.Spectrometer.UpCoilH, ship_geo.Spectrometer.LowCoilH,  ship_geo.Spectrometer.CoilD);
# --------------------------------------
 MufluxSpectrometer.SetBoxParam(ship_geo.Spectrometer.SX,ship_geo.Spectrometer.SY,ship_geo.Spectrometer.SZ,ship_geo.Spectrometer.zBox)
 
 MufluxSpectrometer.ChooseDetector(ship_geo.MufluxSpectrometer.muflux)
 MufluxSpectrometer.SetDeltazView(ship_geo.MufluxSpectrometer.DeltazView)
 MufluxSpectrometer.SetInnerTubeDiameter(ship_geo.MufluxSpectrometer.InnerTubeDiameter)
 MufluxSpectrometer.SetOuterTubeDiameter(ship_geo.MufluxSpectrometer.OuterTubeDiameter)
 MufluxSpectrometer.SetTubePitch(ship_geo.MufluxSpectrometer.TubePitch)
 MufluxSpectrometer.SetDeltazLayer(ship_geo.MufluxSpectrometer.DeltazLayer)
 MufluxSpectrometer.SetDeltazPlane(ship_geo.MufluxSpectrometer.DeltazPlane)
 MufluxSpectrometer.SetTubesPerLayer(ship_geo.MufluxSpectrometer.TubesPerLayer)
 MufluxSpectrometer.SetStereoAngle(ship_geo.MufluxSpectrometer.ViewAngle)
 MufluxSpectrometer.SetWireThickness(ship_geo.MufluxSpectrometer.WireThickness)
 MufluxSpectrometer.SetTubeLength(ship_geo.MufluxSpectrometer.TubeLength)
 MufluxSpectrometer.SetTubeLength12(ship_geo.MufluxSpectrometer.TubeLength12) 
 MufluxSpectrometer.SetTr12YDim(ship_geo.MufluxSpectrometer.tr12ydim)
 MufluxSpectrometer.SetTr34YDim(ship_geo.MufluxSpectrometer.tr34ydim)
 MufluxSpectrometer.SetTr12XDim(ship_geo.MufluxSpectrometer.tr12xdim)
 MufluxSpectrometer.SetTr34XDim(ship_geo.MufluxSpectrometer.tr34xdim) 
 MufluxSpectrometer.SetDistStereo(ship_geo.MufluxSpectrometer.diststereo)
 MufluxSpectrometer.SetDistT1T2(ship_geo.MufluxSpectrometer.distT1T2)
 MufluxSpectrometer.SetDistT3T4(ship_geo.MufluxSpectrometer.distT3T4)    
       
 # for the digitizing step
 MufluxSpectrometer.SetTubeResolution(ship_geo.MufluxSpectrometer.v_drift,ship_geo.MufluxSpectrometer.sigma_spatial) 

 Scintillator = ROOT.Scintillator("Scintillator",ROOT.kTRUE)
 Scintillator.SetScoring1XY(ship_geo.MufluxSpectrometer.tr12xdim,ship_geo.MufluxSpectrometer.tr12ydim)
 Scintillator.SetDistT1(ship_geo.MufluxSpectrometer.DeltazView/2+ship_geo.MufluxSpectrometer.OuterTubeDiameter/2-ship_geo.Scintillator.DistT1)
 Scintillator.SetDistT2(ship_geo.Scintillator.DistT2)
 
 if (ship_geo.MufluxSpectrometer.muflux==False): 
    detectorList.append(Spectrometer)
    detectorList.append(MufluxSpectrometer)
 else:
    TargetStation = ROOT.MufluxTargetStation("MufluxTargetStation",ship_geo.target.length,ship_geo.hadronAbsorber.length, ship_geo.target.z,ship_geo.hadronAbsorber.z,ship_geo.targetOpt,ship_geo.target.sl)

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
 detectorList.append(MuonTagger)
 for x in detectorList:
  run.AddModule(x)
  
 fMagField = ROOT.ShipGoliathField()
 
 fieldfile = os.environ["FAIRSHIP"]+"/field/GoliathFieldMap.root"
 fMagField.Init(fieldfile)
 run.SetField(fMagField)   
 
# return list of detector elements
 detElements = {}
 for x in run.GetListOfModules(): detElements[x.GetName()]=x 
 
 return detElements
