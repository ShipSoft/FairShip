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
        c.EmulsionDet.TTz = 1.81 *u.cm   
        c.EmulsionDet.zdim = c.EmulsionDet.wall* c.EmulsionDet.WallZDim + c.EmulsionDet.wall*c.EmulsionDet.TTz
        c.EmulsionDet.ShiftX = -8.0*u.cm - c.EmulsionDet.xdim/2.
        c.EmulsionDet.ShiftY = 15.5*u.cm + c.EmulsionDet.ydim/2.

        c.EmulsionDet.startpos =  -25.4750 * u.cm
        c.EmulsionDet.zC = c.EmulsionDet.startpos + c.EmulsionDet.zdim/2.
        
        #SciFi parameters
        c.Scifi = AttrDict(z=0*u.cm)
        c.Scifi.xdim    = 40 *u.cm
        c.Scifi.ydim    = 40 *u.cm
        c.Scifi.zdim    = 1.81 *u.cm
        c.Scifi.nmats = 3
        c.Scifi.nscifi   = 5

        #SiPM parameters
        c.Scifi.channel_width     = 0.25 *u.mm
        c.Scifi.sipm_edge = 0.17*u.mm    # on both ends
        c.Scifi.charr_gap = 0.2 *u.mm
        c.Scifi.charr_width = 64 * c.Scifi.channel_width
        c.Scifi.sipm_diegap     = 0.06*u.mm
        c.Scifi.SiPMarray_width = c.Scifi.sipm_edge+c.Scifi.charr_width+c.Scifi.charr_gap+c.Scifi.charr_width+c.Scifi.sipm_edge
        c.Scifi.nsipm_channels  = 128
        c.Scifi.nsipm_mat             = 4
        c.Scifi.nsipms = c.Scifi.nsipm_mat *  c.Scifi.nmats  # 12 per SciFi plane
        c.Scifi.sipmarr_width  = c.Scifi.charr_gap + 2.*c.Scifi.charr_width
        c.Scifi.firstChannelX = -19.528*u.cm  # to agree with SiPM positions of engineering design

        c.Scifi.nfibers_shortrow = 471
        c.Scifi.nfibers_longrow  = 472
        c.Scifi.nfibers_z = 6
        
# Guido: Fibre mat total width 500um less wide than 4 SiPM arrays mounted on a single bar, therefore 32.6mm x 4 -0.5=129.9mm 
        c.Scifi.scifimat_width = (c.Scifi.SiPMarray_width+c.Scifi.sipm_diegap)*c.Scifi.nsipm_mat -0.5*u.mm
        c.Scifi.scifimat_length = 40 *u.cm
        c.Scifi.scifimat_z = 0.135 *u.cm
        c.Scifi.epoxymat_z = 0.17 *u.cm
        c.Scifi.scifimat_gap = 0.05 *u.cm
        
        c.Scifi.fiber_length = c.Scifi.scifimat_length
        c.Scifi.scintcore_rmax = 0.011 *u.cm  
        c.Scifi.clad1_rmax = 0.01175 *u.cm    
        c.Scifi.clad2_rmax = 0.0125 *u.cm

        c.Scifi.horizontal_pitch = 0.0275 *u.cm
        c.Scifi.vertical_pitch = 0.021 *u.cm
        c.Scifi.rowlong_offset = 0.035 *u.cm 
        c.Scifi.rowshort_offset = 0.0215 *u.cm 

        c.Scifi.carbonfiber_z = 0.02 *u.cm
        c.Scifi.honeycomb_z = 0.5 *u.cm
        
        c.Scifi.plastbar_x = 1.5 *u.cm
        c.Scifi.plastbar_y = 40 *u.cm
        c.Scifi.plastbar_z = 0.195 *u.cm

        c.Scifi.scifi_separation = c.Scifi.zdim + c.EmulsionDet.BrZ  
        c.Scifi.offset_z = - c.EmulsionDet.zdim/2 + c.EmulsionDet.BrZ  #SciFi starts at the end of the first ECC
        
        c.Scifi.timeResol = 150.*u.picosecond

        c.MuFilter = AttrDict(z=0*u.cm)
        #Veto station parameters
        c.MuFilter.VetonSiPMs = 8
        c.MuFilter.VetonSides = 2
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
        c.MuFilter.UpstreamnSiPMs = 8
        c.MuFilter.UpstreamnSides = 2
        c.MuFilter.NUpstreamPlanes = 5
        c.MuFilter.DownstreamDetX = c.MuFilter.X
        c.MuFilter.DownstreamDetY = c.MuFilter.FeY
        c.MuFilter.DownstreamDetZ = 3.9*u.cm
        c.MuFilter.DownstreamnSiPMs = 1
        c.MuFilter.DownstreamnSides = 2   # only for horizontal, vertical only one side
        c.MuFilter.NDownstreamPlanes = 4
        c.MuFilter.DS4ZGap = 8.82*u.cm
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
        c.MuFilter.DownstreamBarY_ver = 63.5*u.cm 
        c.MuFilter.DownstreamBarZ_ver = 1*u.cm

        #total z thickness and position
        c.MuFilter.Z = c.MuFilter.NUpstreamPlanes*(c.MuFilter.FeZ+c.MuFilter.UpstreamDetZ) + (c.MuFilter.NDownstreamPlanes - 1)*(c.MuFilter.FeZ+c.MuFilter.DownstreamDetZ) + c.MuFilter.DS4ZGap + c.MuFilter.DownstreamDetZ/2 #doesn't include veto
        c.MuFilter.Zcenter = c.EmulsionDet.zC+c.EmulsionDet.zdim/2+c.MuFilter.Z/2
        c.MuFilter.ShiftX = -2.8 * u.cm - c.MuFilter.X/2.
        
        c.MuFilter.Slope = -3.2 #in degrees
        c.MuFilter.ShiftY = 9.6 * u.cm + c.MuFilter.Y/2. #shift of first block of upstream section
        c.MuFilter.ShiftYEnd= 7.5*u.cm + c.MuFilter.Y/2. #shift for downstream section

# soft alignment
        c.MuFilter.USShiftX     = 0
        c.MuFilter.USShiftY     = 0
        c.MuFilter.USShiftZ     = 0
        c.MuFilter.DSHShiftX = 0
        c.MuFilter.DSHShiftY = 0
        c.MuFilter.DSVShiftX  = 0
        c.MuFilter.DSVShiftY  = 0
        c.MuFilter.DSShiftZ     = 0

        #digitization parameters
        c.MuFilter.DsAttenuationLength   =  350 * u.cm                #  values between 300 cm and 400cm observed for H6 testbeam
        c.MuFilter.DsTAttenuationLength =  700 * u.cm                # top readout with mirror on bottom
        c.MuFilter.VandUpAttenuationLength = 999 * u.cm        # no significante attenuation observed for H6 testbeam
        c.MuFilter.VandUpSiPMcalibrationL         = 25.*1000.       # 1.65 MeV = 41 qcd 
        c.MuFilter.VandUpSiPMcalibrationS         = 25.*1000.
        c.MuFilter.DsSiPMcalibration                       = 25.*1000.
        c.MuFilter.timeResol = 150.*u.picosecond
        c.MuFilter.VandUpPropSpeed    = 12.5*u.cm/u.nanosecond
        c.MuFilter.DsPropSpeed        = 14.3*u.cm/u.nanosecond

        c.Floor = AttrDict(z=483262./10.*u.cm)   # Antonia, 482000mm (FASER+2, P3) + 1017mm (DZ) + 245mm (centre emulsion)
