#!/usr/bin/env python
# -*- coding: latin-1 -*-

import ROOT,os
import shipunit as u
from ShipGeoConfig import ConfigRegistry
detectorList = []

def configure(run,ship_geo,Gfield=''):
# -----Create media-------------------------------------------------
 if hasattr(run,'SetMaterials'):  run.SetMaterials("media.geo")  # Materials
 
# -----Create geometry----------------------------------------------
 cave= ROOT.ShipCave("CAVE")
 cave.SetGeometryFileName("caveWithAir.geo")
 detectorList.append(cave)

 floor = ROOT.Floor()
 for parName in ship_geo.Floor:
    parValue = eval('ship_geo.Floor.'+parName)
    floor.SetConfPar("Floor/"+parName, parValue)
 detectorList.append(floor)
 
 EmulsionDet = ROOT.EmulsionDet("EmulsionDet",ROOT.kTRUE)
 for parName in ship_geo.EmulsionDet:
    parValue = eval('ship_geo.EmulsionDet.'+parName)
    EmulsionDet.SetConfPar("EmulsionDet/"+parName, parValue)
 detectorList.append(EmulsionDet)

 Scifi = ROOT.Scifi("Scifi", ROOT.kTRUE)
 for parName in ship_geo.Scifi:
    parValue = eval('ship_geo.Scifi.'+parName)
    Scifi.SetConfPar("Scifi/"+parName, parValue)
 detectorList.append(Scifi)

 MuFilter = ROOT.MuFilter("MuFilter",ROOT.kTRUE)
 for parName in ship_geo.MuFilter:
    parValue = eval('ship_geo.MuFilter.'+parName)
    MuFilter.SetConfPar("MuFilter/"+parName, parValue)
 detectorList.append(MuFilter)

 detElements = {}
 if hasattr(run,'SetMaterials'):  
  for x in detectorList:
    run.AddModule(x)
# return list of detector elements
  for x in run.GetListOfModules(): detElements[x.GetName()]=x
 else:
  for x in detectorList: detElements[x.GetName()]=x
 return detElements
