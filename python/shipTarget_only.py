#!/usr/bin/env python
import ROOT,os
import shipunit as u

def configure(run,ship_geo):
# -----Create media-------------------------------------------------
 run.SetMaterials("media.geo")  # Materials
# ------------------------------------------------------------------------

# -----Create geometry----------------------------------------------
 cave= ROOT.ShipCave("CAVE")
 cave.SetGeometryFileName("cave.geo")
 run.AddModule(cave)

 TargetStation = ROOT.ShipTargetStation("TargetStation",ship_geo.target.length,ship_geo.hadronAbsorber.length,
                                                        ship_geo.target.z,ship_geo.hadronAbsorber.z,ship_geo.targetVersion)
 if ship_geo.targetVersion>10:
  TargetStation.SetLayerPosMat(ship_geo.target.xy, ship_geo.target.slices_length, ship_geo.target.slices_gap, ship_geo.target.slices_material)

 run.AddModule(TargetStation)


# return list of detector elements
 detElements = {}
 for x in run.GetListOfModules(): detElements[x.GetName()]=x
 return detElements
