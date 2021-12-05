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
 floor.SetSND_Z(ship_geo.Floor.z)
 detectorList.append(floor)
 
 EmulsionDet = ROOT.EmulsionDet("EmulsionDet",ROOT.kTRUE)
 EmulsionDet.SetCenterZ(ship_geo.EmulsionDet.zC)
 EmulsionDet.SetNumberTargets(ship_geo.EmulsionDet.target)
 EmulsionDet.SetNumberBricks(ship_geo.EmulsionDet.col,ship_geo.EmulsionDet.row,ship_geo.EmulsionDet.wall)
 EmulsionDet.SetDetectorDimension(ship_geo.EmulsionDet.xdim, ship_geo.EmulsionDet.ydim, ship_geo.EmulsionDet.zdim)
 EmulsionDet.SetTargetWallDimension(ship_geo.EmulsionDet.WallXDim, ship_geo.EmulsionDet.WallYDim, ship_geo.EmulsionDet.WallZDim)
 EmulsionDet.SetEmulsionParam(ship_geo.EmulsionDet.EmTh, ship_geo.EmulsionDet.EmX, ship_geo.EmulsionDet.EmY, ship_geo.EmulsionDet.PBTh,ship_geo.EmulsionDet.EPlW, ship_geo.EmulsionDet.PassiveTh, ship_geo.EmulsionDet.AllPW)
 EmulsionDet.SetBrickParam(ship_geo.EmulsionDet.BrX, ship_geo.EmulsionDet.BrY, ship_geo.EmulsionDet.BrZ, ship_geo.EmulsionDet.BrPackX, ship_geo.EmulsionDet.BrPackY, ship_geo.EmulsionDet.BrPackZ, ship_geo.EmulsionDet.n_plates)
 EmulsionDet.SetTTzdimension(ship_geo.EmulsionDet.TTz)
 EmulsionDet.SetDisplacement(ship_geo.EmulsionDet.ShiftX, ship_geo.EmulsionDet.ShiftY)
 EmulsionDet.SetEmulsionPassiveOption(ship_geo.EmulsionDet.PassiveOption)
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
