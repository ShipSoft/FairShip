#!/usr/bin/env python
# -*- coding: latin-1 -*-

import ROOT,os
import shipunit as u
from ShipGeoConfig import ConfigRegistry
detectorList = []

def getParameter(x,ship_geo,latestGeo):
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
  a = getattr(latestGeo,top)
  return getattr(a,last)

def configure(run,ship_geo,Gfield=''):
 #latestCharmGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/charm-geometry_config.py")
 latestGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/shipLHC_geom_config.py")
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

 Scifi = ROOT.Scifi("Scifi", ship_geo.Scifi.xdim, ship_geo.Scifi.ydim, ship_geo.Scifi.zdim, ROOT.kTRUE)
 Scifi.SetScifiParam(ship_geo.Scifi.xdim, ship_geo.Scifi.ydim, ship_geo.Scifi.zdim) 
 Scifi.SetMatParam(ship_geo.Scifi.scifimat_width, ship_geo.Scifi.scifimat_length, ship_geo.Scifi.scifimat_z, ship_geo.Scifi.epoxymat_z, ship_geo.Scifi.scifimat_gap)
 Scifi.SetFiberParam(ship_geo.Scifi.fiber_length, ship_geo.Scifi.scintcore_rmax, ship_geo.Scifi.clad1_rmax, ship_geo.Scifi.clad2_rmax)
 Scifi.SetFiberPosParam(ship_geo.Scifi.horizontal_pitch, ship_geo.Scifi.vertical_pitch, ship_geo.Scifi.rowlong_offset, ship_geo.Scifi.rowshort_offset)
 Scifi.SetPlaneParam(ship_geo.Scifi.carbonfiber_z, ship_geo.Scifi.honeycomb_z)
 Scifi.SetPlastBarParam(ship_geo.Scifi.plastbar_x, ship_geo.Scifi.plastbar_y, ship_geo.Scifi.plastbar_z)
 Scifi.SetNFibers(ship_geo.Scifi.nfibers_shortrow, ship_geo.Scifi.nfibers_longrow, ship_geo.Scifi.nfibers_z)
 Scifi.SetScifiSep(ship_geo.Scifi.scifi_separation)
 Scifi.SetZOffset(ship_geo.Scifi.offset_z)
 Scifi.SetNMats(ship_geo.Scifi.nmats)
 Scifi.SetNScifi(ship_geo.Scifi.nscifi)
 Scifi.SiPMParams(ship_geo.Scifi.channel_width, ship_geo.Scifi.charr_width, ship_geo.Scifi.sipm_edge,
                                      ship_geo.Scifi.charr_gap, ship_geo.Scifi.sipm_diegap, ship_geo.Scifi.nsipm_channels, ship_geo.Scifi.nsipm_mat,ship_geo.Scifi.firstChannelX )
 detectorList.append(Scifi)

 MuFilter = ROOT.MuFilter("MuFilter",ROOT.kTRUE)
 mu = ship_geo.MuFilter
 #upstream veto section
 MuFilter.SetVetoCenterPosition(mu.VetozC)
 MuFilter.SetVetoShift(mu.VetoShiftX, mu.VetoShiftY)
 MuFilter.SetVetoPlaneShiftY(mu.VetoPlaneShiftY)
 MuFilter.SetNVetoPlanes(mu.NVetoPlanes)
 MuFilter.SetNVetoBars(mu.NVetoBars)
 MuFilter.SetVetoPlanesDimensions(mu.VetoPlaneX, mu.VetoPlaneY, mu.VetoPlaneZ)
 MuFilter.SetVetoBarsDimensions(mu.VetoBarX, mu.VetoBarY, mu.VetoBarZ)
 MuFilter.SetMuFilterDimensions(mu.X, mu.Y, mu.Z)
 MuFilter.SetIronBlockDimensions(mu.FeX, mu.FeY, mu.FeZ)
 #upstream section
 MuFilter.SetUpstreamPlanesDimensions(mu.UpstreamDetX, mu.UpstreamDetY, mu.UpstreamDetZ)
 MuFilter.SetNUpstreamPlanes(mu.NUpstreamPlanes)
 MuFilter.SetUpstreamBarsDimensions(mu.UpstreamBarX, mu.UpstreamBarY, mu.UpstreamBarZ)
 MuFilter.SetNUpstreamBars(mu.NUpstreamBars)
 #downstream section
 MuFilter.SetDownstreamPlanesDimensions(mu.DownstreamDetX, mu.DownstreamDetY, mu.DownstreamDetZ)
 MuFilter.SetNDownstreamPlanes(mu.NDownstreamPlanes)
 MuFilter.SetDownstreamBarsDimensions(mu.DownstreamBarX, mu.DownstreamBarY, mu.DownstreamBarZ)
 MuFilter.SetDownstreamVerticalBarsDimensions(mu.DownstreamBarX_ver, mu.DownstreamBarY_ver, mu.DownstreamBarZ_ver)
 MuFilter.SetNDownstreamBars(mu.NDownstreamBars)
 MuFilter.SetDS4ZGap(mu.DS4ZGap)

 MuFilter.SetCenterZ(mu.Zcenter)
 MuFilter.SetXYDisplacement(mu.ShiftX, mu.ShiftY)
 MuFilter.SetSlope(mu.Slope)
 MuFilter.SetYPlanesDisplacement(mu.ShiftYEnd)

 MuFilter.SetReadout(mu.VetonSiPMs,mu.UpstreamnSiPMs,mu.DownstreamnSiPMs,mu.VetonSides,mu.UpstreamnSides,mu.DownstreamnSides )
 MuFilter.SetDigiParameters(mu.AttenuationLength,mu.VandUpAttenuationLength,mu.SiPMcalibration,mu.DynRangeLow,mu.DynRangeHigh)

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
