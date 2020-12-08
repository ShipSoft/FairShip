import ROOT as r
import shipunit as u
from ShipGeoConfig import AttrDict, ConfigRegistry


with ConfigRegistry.register_config("basic") as c:
# cave parameters
        c.cave = AttrDict(z=0*u.cm)

        c.EmulsionDet = AttrDict(z=0*u.cm)
        c.EmulsionDet.PassiveOption = 1 #0 makes emulsion volumes active, 1 makes all emulsion volumes passive
        c.EmulsionDet.zC = 0*u.m
        c.EmulsionDet.row = 2
        c.EmulsionDet.col = 2
        c.EmulsionDet.wall= 5
        c.EmulsionDet.target = 1  #number of neutrino target volumes
        c.EmulsionDet.n_plates = 59
        c.EmulsionDet.EmTh = 0.0070 * u.cm
        c.EmulsionDet.EmX = 19.2 * u.cm
        c.EmulsionDet.EmY = 19.2 * u.cm
        c.EmulsionDet.PBTh = 0.0175 * u.cm
        c.EmulsionDet.PassiveTh = 0.1 * u.cm
        c.EmulsionDet.EPlW = 2* c.EmulsionDet.EmTh + c.EmulsionDet.PBTh
        c.EmulsionDet.AllPW = c.EmulsionDet.PassiveTh + c.EmulsionDet.EPlW

        c.EmulsionDet.BrPackZ = 0.*u.cm
        c.EmulsionDet.BrPackX = 2*0.3*u.cm
        c.EmulsionDet.BrPackY = 2*0.3*u.cm
        
        c.EmulsionDet.BrX = c.EmulsionDet.EmX + c.EmulsionDet.BrPackX
        c.EmulsionDet.BrY = c.EmulsionDet.EmY + c.EmulsionDet.BrPackY
        c.EmulsionDet.BrZ = c.EmulsionDet.n_plates * c.EmulsionDet.AllPW + c.EmulsionDet.EPlW + c.EmulsionDet.BrPackZ

        c.EmulsionDet.xdim = c.EmulsionDet.BrX * c.EmulsionDet.col
        c.EmulsionDet.ydim = c.EmulsionDet.BrY * c.EmulsionDet.row
        c.EmulsionDet.WallXDim = c.EmulsionDet.xdim
        c.EmulsionDet.WallYDim = c.EmulsionDet.ydim
        c.EmulsionDet.WallZDim = c.EmulsionDet.BrZ
        c.EmulsionDet.TTz = 3.0*u.cm
        c.EmulsionDet.zdim = c.EmulsionDet.wall* c.EmulsionDet.WallZDim + (c.EmulsionDet.wall+1)*c.EmulsionDet.TTz
        c.EmulsionDet.ShiftX = -8.0*u.cm
        c.EmulsionDet.ShiftY = 15.5*u.cm

        c.Scifi = AttrDict(z=0*u.cm)
        c.Scifi.xdim = c.EmulsionDet.xdim
        c.Scifi.ydim = c.EmulsionDet.ydim
        c.Scifi.zdim = c.EmulsionDet.TTz
        c.Scifi.DZ = c.EmulsionDet.BrZ
        c.Scifi.nplanes = c.EmulsionDet.wall+1

        c.MuFilter = AttrDict(z=0*u.cm)
        c.MuFilter.ShiftDY = 2.0*u.cm
        c.MuFilter.ShiftDYTot = 6.0*u.cm
        #c.MuFilter.X = c.EmulsionDet.xdim + 20*u.cm
        c.MuFilter.X = 62.0*u.cm
        #c.MuFilter.Y = c.EmulsionDet.ydim + 20*u.cm+10.0*u.cm
        c.MuFilter.Y = 60.5*u.cm+c.MuFilter.ShiftDYTot
        c.MuFilter.FeX = c.MuFilter.X
        #c.MuFilter.FeY = c.EmulsionDet.ydim + 20*u.cm
        c.MuFilter.FeY = c.MuFilter.Y - c.MuFilter.ShiftDYTot
        c.MuFilter.FeZ = 20*u.cm
        c.MuFilter.UpstreamDetX = c.MuFilter.X
        c.MuFilter.UpstreamDetY = c.MuFilter.FeY
        c.MuFilter.UpstreamDetZ = 2*u.cm
        c.MuFilter.NUpstreamPlanes = 5
        c.MuFilter.DownstreamDetX = c.MuFilter.X
        c.MuFilter.DownstreamDetY = c.MuFilter.FeY
        c.MuFilter.DownstreamDetZ = 4*u.cm
        c.MuFilter.NDownstreamPlanes=3

        #upstream bars configuration
        c.MuFilter.NUpstreamBars = 11
        c.MuFilter.OverlapUpstreamBars = 0.5*u.cm
        c.MuFilter.UpstreamBarX = c.MuFilter.UpstreamDetX
        c.MuFilter.UpstreamBarY = (c.MuFilter.UpstreamDetY + c.MuFilter.OverlapUpstreamBars * (c.MuFilter.NUpstreamBars - 1))/c.MuFilter.NUpstreamBars #computed for staggering
        c.MuFilter.UpstreamBarZ = 1*u.cm

        #downstream bars configuration
        c.MuFilter.NDownstreamBars = 77 #n.d.r. both for x and y in this case
        c.MuFilter.OverlapDownstreamBars = 0.2*u.cm
        c.MuFilter.DownstreamBarX = c.MuFilter.DownstreamDetX
        c.MuFilter.DownstreamBarY = (c.MuFilter.DownstreamDetY + c.MuFilter.OverlapDownstreamBars * (c.MuFilter.NDownstreamBars - 1))/c.MuFilter.NDownstreamBars #computed for staggering
        c.MuFilter.DownstreamBarZ = 1*u.cm

        c.MuFilter.DownstreamBarX_ver = (c.MuFilter.DownstreamDetX + c.MuFilter.OverlapDownstreamBars * (c.MuFilter.NDownstreamBars - 1))/c.MuFilter.NDownstreamBars
        c.MuFilter.DownstreamBarY_ver = c.MuFilter.DownstreamDetY
        c.MuFilter.DownstreamBarZ_ver = 1*u.cm

        #total z thickness and position
        c.MuFilter.Z = c.MuFilter.NUpstreamPlanes*(c.MuFilter.FeZ+c.MuFilter.UpstreamDetZ) + c.MuFilter.NDownstreamPlanes*(c.MuFilter.FeZ+c.MuFilter.DownstreamDetZ) 
        c.MuFilter.Zcenter = c.EmulsionDet.zC+c.EmulsionDet.zdim/2+c.MuFilter.Z/2
        c.MuFilter.ShiftX = c.EmulsionDet.ShiftX-c.EmulsionDet.xdim/2
        c.MuFilter.ShiftY = 3.55*u.cm #since y size increased of 0.5, we need to increase this shift from 3.3 to 3.55
