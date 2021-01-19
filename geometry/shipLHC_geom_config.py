import ROOT as r
import shipunit as u
from ShipGeoConfig import AttrDict, ConfigRegistry


with ConfigRegistry.register_config("basic") as c:
# cave parameters
        c.cave = AttrDict(z=0*u.cm)

        c.EmulsionDet = AttrDict(z=0*u.cm)
        c.EmulsionDet.PassiveOption = 1 #0 makes emulsion volumes active, 1 makes all emulsion volumes passive
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
        c.EmulsionDet.zdim = c.EmulsionDet.wall* c.EmulsionDet.WallZDim + c.EmulsionDet.wall*c.EmulsionDet.TTz
        c.EmulsionDet.ShiftX = -8.0*u.cm - c.EmulsionDet.xdim/2.
        c.EmulsionDet.ShiftY = 15.5*u.cm + c.EmulsionDet.ydim/2.

        c.EmulsionDet.startpos =  -25.4750 * u.cm
        c.EmulsionDet.zC = c.EmulsionDet.startpos + c.EmulsionDet.zdim/2.

        c.Scifi = AttrDict(z=0*u.cm)
        c.Scifi.xdim = c.EmulsionDet.xdim
        c.Scifi.ydim = c.EmulsionDet.ydim
        c.Scifi.zdim = c.EmulsionDet.TTz
        c.Scifi.DZ = c.EmulsionDet.BrZ
        c.Scifi.nplanes = c.EmulsionDet.wall

        c.MuFilter = AttrDict(z=0*u.cm)
        #Veto station parameters
        c.MuFilter.NVetoPlanes = 2
        c.MuFilter.VetoShiftX = c.EmulsionDet.ShiftX
        c.MuFilter.VetoShiftY = c.EmulsionDet.ShiftY
        c.MuFilter.VetoPlaneShiftY = 1*u.cm
        
        c.MuFilter.VetoPlaneX = 42 *u.cm
        c.MuFilter.VetoPlaneY = 42 *u.cm
        c.MuFilter.VetoPlaneZ = 4 * u.cm

        c.MuFilter.NVetoBars = 7

        c.MuFilter.VetoBarX = c.MuFilter.VetoPlaneX
        c.MuFilter.VetoBarY = c.MuFilter.VetoPlaneY / c.MuFilter.NVetoBars
        c.MuFilter.VetoBarZ = 1 * u.cm

        #veto should end at the start of first ECC target
        c.MuFilter.VetozC = c.EmulsionDet.zC - c.EmulsionDet.zdim/2. - (c.MuFilter.NVetoPlanes * c.MuFilter.VetoPlaneZ)/2.

        #c.MuFilter.X = c.EmulsionDet.xdim + 20*u.cm
        c.MuFilter.X = 80.0*u.cm
        #c.MuFilter.Y = c.EmulsionDet.ydim + 20*u.cm+10.0*u.cm
        c.MuFilter.Y = 60.0*u.cm
        c.MuFilter.FeX = c.MuFilter.X
        #c.MuFilter.FeY = c.EmulsionDet.ydim + 20*u.cm
        c.MuFilter.FeY = c.MuFilter.Y
        c.MuFilter.FeZ = 20*u.cm
        c.MuFilter.UpstreamDetX = c.MuFilter.X
        c.MuFilter.UpstreamDetY = c.MuFilter.FeY
        c.MuFilter.UpstreamDetZ = 2.6*u.cm
        c.MuFilter.NUpstreamPlanes = 5
        c.MuFilter.DownstreamDetX = c.MuFilter.X
        c.MuFilter.DownstreamDetY = c.MuFilter.FeY
        c.MuFilter.DownstreamDetZ = 3.9*u.cm
        c.MuFilter.NDownstreamPlanes=3

        #upstream bars configuration
        c.MuFilter.NUpstreamBars = 10
        c.MuFilter.UpstreamBarX = c.MuFilter.UpstreamDetX
        c.MuFilter.UpstreamBarY = c.MuFilter.UpstreamDetY/c.MuFilter.NUpstreamBars #computed for staggering
        c.MuFilter.UpstreamBarZ = 1*u.cm

        #downstream bars configuration
        c.MuFilter.NDownstreamBars = 60 #n.d.r. both for x and y in this case
        c.MuFilter.DownstreamBarX = c.MuFilter.DownstreamDetX
        c.MuFilter.DownstreamBarY = c.MuFilter.DownstreamDetY/c.MuFilter.NDownstreamBars #computed for staggering
        c.MuFilter.DownstreamBarZ = 1*u.cm

        c.MuFilter.DownstreamBarX_ver = c.MuFilter.DownstreamDetY/c.MuFilter.NDownstreamBars #the vertical bars cover a region only 60 x 60 cm2
        c.MuFilter.DownstreamBarY_ver = c.MuFilter.DownstreamDetY
        c.MuFilter.DownstreamBarZ_ver = 1*u.cm

        #total z thickness and position
        c.MuFilter.Z = c.MuFilter.NUpstreamPlanes*(c.MuFilter.FeZ+c.MuFilter.UpstreamDetZ) + c.MuFilter.NDownstreamPlanes*(c.MuFilter.FeZ+c.MuFilter.DownstreamDetZ) 
        c.MuFilter.Zcenter = c.EmulsionDet.zC+c.EmulsionDet.zdim/2+c.MuFilter.Z/2
        c.MuFilter.ShiftX = -2.8 * u.cm - c.MuFilter.X/2.
        
        c.MuFilter.Slope = -3.2 #in degrees
        c.MuFilter.ShiftY = 9.6 * u.cm + c.MuFilter.Y/2. #shift of first block of upstream section
        c.MuFilter.ShiftYEnd= 7.5*u.cm + c.MuFilter.Y/2. #shift for downstream section

        c.Floor = AttrDict(z=483262./10.*u.cm)   # Antonia, 482000mm (FASER+2, P3) + 1017mm (DZ) + 24.5mm (centre emulsion)
