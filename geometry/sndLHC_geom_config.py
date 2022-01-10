import ROOT as r
import shipunit as u
from ShipGeoConfig import AttrDict, ConfigRegistry


with ConfigRegistry.register_config("basic") as c:
# cave parameters
        c.cave = AttrDict(z=0*u.cm)

        # Antonia, 482000mm (FASER+2, P3) + 1017mm (DZ) + 245mm (centre emulsion),z=483262./10.*u.cm
        # centre emulsion now 326.2cm downstream from origin.
        c.EmulsionDet = AttrDict(z=326.2*u.cm)
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
        c.EmulsionDet.BrPackX = 2*0.05*u.cm
        c.EmulsionDet.BrPackY = 2*0.05*u.cm
        
        c.EmulsionDet.BrX = c.EmulsionDet.EmX + c.EmulsionDet.BrPackX
        c.EmulsionDet.BrY = c.EmulsionDet.EmY + c.EmulsionDet.BrPackY
        c.EmulsionDet.BrZ = c.EmulsionDet.n_plates * c.EmulsionDet.AllPW + c.EmulsionDet.EPlW + c.EmulsionDet.BrPackZ

        c.EmulsionDet.xdim = 42.2 *u.cm #external wall dimensions
        c.EmulsionDet.ydim = 42.2 *u.cm
        c.EmulsionDet.TotalWallZDim = 10.0 *u.cm #wall dimension along z, including border
        c.EmulsionDet.WallXDim = 38.6 *u.cm #internal wall dimensions
        c.EmulsionDet.WallYDim = 38.6 *u.cm
        c.EmulsionDet.WallZDim = 8.15 *u.cm
        c.EmulsionDet.WallZBorder_offset = 4.75 * u.mm
        c.EmulsionDet.TTz = 3.0*u.cm
        c.EmulsionDet.zdim = c.EmulsionDet.wall* c.EmulsionDet.TotalWallZDim + c.EmulsionDet.wall*c.EmulsionDet.TTz
        c.EmulsionDet.ShiftX = -8.0*u.cm - c.EmulsionDet.xdim/2.
        c.EmulsionDet.ShiftY = 15.5*u.cm + c.EmulsionDet.ydim/2.

        c.EmulsionDet.startpos =  -25.4750 * u.cm + c.EmulsionDet.z
        c.EmulsionDet.zC = c.EmulsionDet.startpos + c.EmulsionDet.zdim/2.
        
        # survey points in survey coordinate system!
        c.EmulsionDet.Xpos0,c.EmulsionDet.Ypos0,c.EmulsionDet.Zpos0 = 5.74*u.cm, 288.89*u.cm, 16.63*u.cm
        c.EmulsionDet.Xpos1,c.EmulsionDet.Ypos1,c.EmulsionDet.Zpos1 = 5.74*u.cm, 301.89*u.cm, 16.63*u.cm
        c.EmulsionDet.Xpos2,c.EmulsionDet.Ypos2,c.EmulsionDet.Zpos2 = 5.74*u.cm, 314.89*u.cm, 16.63*u.cm
        c.EmulsionDet.Xpos3,c.EmulsionDet.Ypos3,c.EmulsionDet.Zpos3 = 5.74*u.cm, 327.89*u.cm, 16.63*u.cm
        c.EmulsionDet.Xpos4,c.EmulsionDet.Ypos4,c.EmulsionDet.Zpos4 = 5.74*u.cm, 340.89*u.cm, 16.63*u.cm

        #SciFi parameters
        c.Scifi = AttrDict(z=0*u.cm)
        c.Scifi.xdim = 39.0 * u.cm #sensitive only
        c.Scifi.ydim = 39.0 * u.cm 
        c.Scifi.zdim = c.EmulsionDet.TTz
        c.Scifi.DZ = c.EmulsionDet.BrZ
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
        c.Scifi.scifimat_length = c.Scifi.ydim
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
        c.Scifi.plastbar_y = c.Scifi.ydim
        c.Scifi.plastbar_z = 0.195 *u.cm

        c.Scifi.scifi_separation = c.Scifi.zdim + c.EmulsionDet.BrZ  
        c.Scifi.offset_z = - c.EmulsionDet.zdim/2 + c.EmulsionDet.BrZ  #SciFi starts at the end of the first ECC
       
        c.Scifi.timeResol = 150.*u.picosecond

        # absolute edge point positions in survey coordinate system
        c.Scifi.Xpos0,c.Scifi.Ypos0,c.Scifi.Zpos0 = 4.34*u.cm, 298.94*u.cm, 15.22*u.cm
        c.Scifi.Xpos1,c.Scifi.Ypos1,c.Scifi.Zpos1 = 4.34*u.cm, 311.94*u.cm, 15.22*u.cm
        c.Scifi.Xpos2,c.Scifi.Ypos2,c.Scifi.Zpos2 = 4.34*u.cm, 324.94*u.cm, 15.22*u.cm
        c.Scifi.Xpos3,c.Scifi.Ypos3,c.Scifi.Zpos3 = 4.34*u.cm, 337.94*u.cm, 15.22*u.cm
        c.Scifi.Xpos4,c.Scifi.Ypos4,c.Scifi.Zpos4 = 4.34*u.cm, 350.94*u.cm, 15.22*u.cm

# Scifi technical drawing, distance from first channel on vertical / horizontal plane to edge point  225,225,0, xy plane z perpendicularc.Scifi.ydim
        c.Scifi.EdgeAX, c.Scifi.EdgeAY, c.Scifi.EdgeAZ =  225*u.mm, 225*u.mm, 0*u.mm

        c.Scifi.FirstChannelVX,c.Scifi.FirstChannelVY,c.Scifi.FirstChannelVZ = -195.28*u.mm, -200.0*u.mm, -12.92*u.mm

        c.Scifi.FirstChannelHX,c.Scifi.FirstChannelHY,c.Scifi.FirstChannelHZ = -200.0*u.mm, -195.28*u.mm, -7.07*u.mm

# Local Scifi position of first channel on a vertical scifi plane in software
        c.Scifi.LfirstChannelVX,c.Scifi.LfirstChannelVY,c.Scifi.LfirstChannelVZ = -195.135*u.mm, 195.0*u.mm, 11.85*u.mm   # sipm on top

# Local Scifi position of last channel (=first channel on technical drawing) on a horizontal scifi plane in software
        c.Scifi.LfirstChannelHX,c.Scifi.LfirstChannelHY,c.Scifi.LfirstChannelHZ = -195.0*u.mm, 195.178*u.mm,  6.25*u.mm  # sipm on the right side direction away from IP1

 # relative mat alignments
        c.Scifi.LocM100,c.Scifi.LocM101,c.Scifi.LocM102 =  0.0*u.um,     0.0*u.um,          0.0*u.um
        c.Scifi.LocM110,c.Scifi.LocM111,c.Scifi.LocM112=   0.0*u.um,     0.0*u.um,          0.0*u.um
        c.Scifi.LocM200,c.Scifi.LocM201,c.Scifi.LocM202=   0.0*u.um,     0.0*u.um,          0.0*u.um
        c.Scifi.LocM210,c.Scifi.LocM211,c.Scifi.LocM212 =  0.0*u.um,     0.0*u.um,          0.0*u.um
        c.Scifi.LocM300,c.Scifi.LocM301,c.Scifi.LocM302=   0.0*u.um,     0.0*u.um,          0.0*u.um
        c.Scifi.LocM310,c.Scifi.LocM311,c.Scifi.LocM312=   0.0*u.um,     0.0*u.um,          0.0*u.um
        c.Scifi.LocM400,c.Scifi.LocM401,c.Scifi.LocM402 =  0.0*u.um,     0.0*u.um,          0.0*u.um
        c.Scifi.LocM410,c.Scifi.LocM411,c.Scifi.LocM412=   0.0*u.um,     0.0*u.um,          0.0*u.um
        c.Scifi.LocM500,c.Scifi.LocM501,c.Scifi.LocM502=   0.0*u.um,     0.0*u.um,          0.0*u.um
        c.Scifi.LocM510,c.Scifi.LocM511,c.Scifi.LocM512=   0.0*u.um,     0.0*u.um,          0.0*u.um

        c.MuFilter = AttrDict(z=0*u.cm)
        #coordinates in local gravity based system
        c.MuFilter.Veto1Dx,c.MuFilter.Veto1Dy,c.MuFilter.Veto1Dz = 44.5*u.mm,    2798*u.mm, 185.9*u.mm
        c.MuFilter.Veto2Dx,c.MuFilter.Veto2Dy,c.MuFilter.Veto2Dz = 44.5*u.mm,    2839*u.mm, 165.9*u.mm
        c.MuFilter.Iron1Dx, c.MuFilter.Iron1Dy, c.MuFilter.Iron1Dz = -24.2*u.mm, 3579.6*u.mm, 146.6*u.mm
        # US1
        c.MuFilter.Muon1Dx,c.MuFilter.Muon1Dy,c.MuFilter.Muon1Dz = -47.1*u.mm, 3760.2*u.mm, 146.6*u.mm
        c.MuFilter.Iron2Dx,  c.MuFilter.Iron2Dy,   c.MuFilter.Iron2Dz   = -24.2*u.mm,  3804.6*u.mm, 136.6*u.mm
        # US2
        c.MuFilter.Muon2Dx,c.MuFilter.Muon2Dy,c.MuFilter.Muon2Dz = -47.1*u.mm, 3985.2*u.mm, 136.6*u.mm
        c.MuFilter.Iron3Dx,  c.MuFilter.Iron3Dy,   c.MuFilter.Iron3Dz    = -24.2*u.mm, 4029.6*u.mm, 126.6*u.mm
        # US3
        c.MuFilter.Muon3Dx,c.MuFilter.Muon3Dy,c.MuFilter.Muon3Dz = -47.1*u.mm, 4210.2*u.mm, 126.6*u.mm
        c.MuFilter.Iron4Dx,  c.MuFilter.Iron4Dy,   c.MuFilter.Iron4Dz    = -24.2*u.mm, 4254.6*u.mm, 116.7*u.mm
        # US4
        c.MuFilter.Muon4Dx,c.MuFilter.Muon4Dy,c.MuFilter.Muon4Dz = -47.1*u.mm, 4435.2*u.mm, 116.7*u.mm
        c.MuFilter.Iron5Dx,   c.MuFilter.Iron5Dy,  c.MuFilter.Iron5Dz    = -24.2*u.mm, 4479.6*u.mm, 127.7*u.mm    # 0 +225.0mm 0
        # US5
        c.MuFilter.Muon5Dx,c.MuFilter.Muon5Dy,c.MuFilter.Muon5Dz = -47.1*u.mm, 4660.2*u.mm, 127.7*u.mm
        c.MuFilter.Iron6Dx,   c.MuFilter.Iron6Dy,  c.MuFilter.Iron6Dz    = -24.2*u.mm, 4704.6*u.mm,127.7*u.mm     # 0 +225.0mm 0
        # DS1
        c.MuFilter.Muon6Dx,c.MuFilter.Muon6Dy,c.MuFilter.Muon6Dz = -47.1*u.mm, 4884.9*u.mm, 127.7*u.mm
        c.MuFilter.Iron7Dx,   c.MuFilter.Iron7Dy,  c.MuFilter.Iron7Dz    = -24.2*u.mm, 4943.6*u.mm, 127.7*u.mm       # 0 +239.0mm 0
        # DS2
        c.MuFilter.Muon7Dx,c.MuFilter.Muon7Dy,c.MuFilter.Muon7Dz = -47.1*u.mm, 5123.9*u.mm, 127.7*u.mm
        c.MuFilter.Iron8Dx,   c.MuFilter.Iron8Dy,  c.MuFilter.Iron8Dz    = -24.2*u.mm, 5183.9*u.mm, 127.7*u.mm        # 0 +240.3mm 0 
        # DS3
        c.MuFilter.Muon8Dx,c.MuFilter.Muon8Dy,c.MuFilter.Muon8Dz = -4.7*u.mm, 5383.7*u.mm, 127.7*u.mm

        c.MuFilter.DS4ZGap = 8.82*u.cm
        # DS4V
        c.MuFilter.Muon9Dx,c.MuFilter.Muon9Dy,c.MuFilter.Muon9Dz = -4.7*u.mm,    5383.7*u.mm + c.MuFilter.DS4ZGap, 127.7*u.mm
        c.MuFilter.Iron9Dx,  c.MuFilter.Iron9Dy,   c.MuFilter.Iron9Dz    = 175.8*u.mm, 5529.7*u.mm, 127.7*u.mm

        # relation between edge and bottom bar for VETO
        c.MuFilter.VETOLocX,c.MuFilter.VETOLocY,c.MuFilter.VETOLocZ = 20.0*u.mm,20.0*u.mm,46.7*u.mm

        # relation between edge and bottom bar for US and DS
        c.MuFilter.DSHLocX,c.MuFilter.DSHLocY,c.MuFilter.DSHLocZ      = 10.5*u.mm, 32.0*u.mm, 11.1*u.mm
        # relation between edge and right bar
        c.MuFilter.DSVLocX,c.MuFilter.DSVLocY,c.MuFilter.DSVLocZ       = 623.0*u.mm, 47.0*u.mm, 641.3*u.mm

        # offsets in Z of first US bar 
        c.MuFilter.USOffZ1 = 4.35*u.mm
        c.MuFilter.USOffZ2 = 5.0*u.mm
        c.MuFilter.USOffZ3 = 4.2*u.mm
        c.MuFilter.USOffZ4 = 5.21*u.mm
        c.MuFilter.USOffZ5 = 4.74*u.mm

        #Veto station parameters
        c.MuFilter.VetonSiPMs = 8
        c.MuFilter.VetonSides  = 2
        c.MuFilter.NVetoPlanes = 2
        c.MuFilter.NVetoBars    = 7

        c.MuFilter.VetoBarX,c.MuFilter.VetoBarY,c.MuFilter.VetoBarZ = 42 *u.cm, 6 * u.cm, 1 * u.cm
        c.MuFilter.VetoBarGap = 2*30*u.um  # wrapping material

        c.MuFilter.FeX,c.MuFilter.FeY,c.MuFilter.FeZ                  = 80*u.cm, 60*u.cm, 20*u.cm
        c.MuFilter.FeEndX,c.MuFilter.FeEndY,c.MuFilter.FeEndZ = 40*u.cm, 40*u.cm, 20*u.cm
        c.MuFilter.FeBotX,c.MuFilter.FeBotY,c.MuFilter.FeBotY   = 80*u.cm,   9*u.cm, 40*u.cm

        c.MuFilter.UpstreamDetZ = 2.6*u.cm
        c.MuFilter.UpstreamnSiPMs = 8
        c.MuFilter.UpstreamnSides = 2
        c.MuFilter.NUpstreamPlanes = 5
        c.MuFilter.DownstreamDetZ = 3.9*u.cm
        c.MuFilter.DownstreamnSiPMs = 1
        c.MuFilter.DownstreamnSides = 2   # only for horizontal, vertical only one side
        c.MuFilter.NDownstreamPlanes = 4
        #upstream bars configuration
        c.MuFilter.NUpstreamBars = 10
        c.MuFilter.UpstreamBarX,c.MuFilter.UpstreamBarY,c.MuFilter.UpstreamBarZ = 82.525*u.cm, 6.0*u.cm, 1.0*u.cm
        c.MuFilter.UpstreamBarGap = 0.1*u.mm

        #downstream bars configuration
        c.MuFilter.NDownstreamBars = 60 #n.d.r. both for x and y in this case
        c.MuFilter.DownstreamBarX,c.MuFilter.DownstreamBarY,c.MuFilter.DownstreamBarZ = 82.525*u.cm, 1*u.cm, 1*u.cm
        c.MuFilter.DownstreamBarGap = 0.1*u.mm
        c.MuFilter.DownstreamBarX_ver,c.MuFilter.DownstreamBarY_ver,c.MuFilter.DownstreamBarZ_ver = 1*u.cm, 63.525*u.cm, 1*u.cm

        # DS and US support box, inner, Z pointing upward
        c.MuFilter.SupportBoxD  = 0.5*u.mm  # empty space between bars and box
        c.MuFilter.SupportBoxW = 2*u.mm
        c.MuFilter.DSBoxX1        = c.MuFilter.DSHLocX - c.MuFilter.SupportBoxD
        c.MuFilter.DSBoxX2        = c.MuFilter.DSHLocX + c.MuFilter.DownstreamBarX + c.MuFilter.SupportBoxD
        c.MuFilter.DSBoxZ1        = c.MuFilter.DSHLocZ - c.MuFilter.DownstreamBarY/2 - c.MuFilter.SupportBoxD
        c.MuFilter.DSBoxZ2        = c.MuFilter.DSVLocZ + c.MuFilter.SupportBoxD
        c.MuFilter.DSBoxY1        = c.MuFilter.DSHLocY - c.MuFilter.DownstreamBarZ/2 - c.MuFilter.SupportBoxD
        c.MuFilter.DSBoxY2        = c.MuFilter.DSVLocY + c.MuFilter.DownstreamBarZ/2 + c.MuFilter.SupportBoxD

        c.MuFilter.USBoxY1        = c.MuFilter.DSHLocY - c.MuFilter.DownstreamBarZ/2 - c.MuFilter.SupportBoxD
        c.MuFilter.USBoxY2        = c.MuFilter.DSHLocY + c.MuFilter.DownstreamBarZ/2 + c.MuFilter.SupportBoxD

       # VETO support box
        c.MuFilter.SupportBoxVW = 4*u.mm
        c.MuFilter.VETOBoxX1        = c.MuFilter.VETOLocX - c.MuFilter.SupportBoxD
        c.MuFilter.VETOBoxX2        = c.MuFilter.VETOLocX + c.MuFilter.VetoBarX + c.MuFilter.SupportBoxD
        c.MuFilter.VETOBoxZ1        = c.MuFilter.VETOLocZ - c.MuFilter.VetoBarY/2 - c.MuFilter.SupportBoxD
        c.MuFilter.VETOBoxZ2        = c.MuFilter.VETOLocZ + (c.MuFilter.NVetoBars-1)*(c.MuFilter.VetoBarY+c.MuFilter.VetoBarGap) + c.MuFilter.VetoBarY/2 + c.MuFilter.SupportBoxD
        c.MuFilter.VETOBoxY1        = c.MuFilter.VETOLocY - c.MuFilter.VetoBarZ/2 - c.MuFilter.SupportBoxD
        c.MuFilter.VETOBoxY2        = c.MuFilter.VETOLocY + c.MuFilter.VetoBarZ/2 + c.MuFilter.SupportBoxD

       #digitization parameters
        c.MuFilter.DsAttenuationLength   =  350 * u.cm                #  values between 300 cm and 400cm observed for H6 testbeam
        c.MuFilter.DsTAttenuationLength =  700 * u.cm                # top readout with mirror on bottom
        c.MuFilter.VandUpAttenuationLength = 999 * u.cm        # no significante attenuation observed for H6 testbeam
        c.MuFilter.VandUpSiPMcalibrationL    = 25.*1000.       # 1.65 MeV = 41 qcd 
        c.MuFilter.VandUpSiPMcalibrationS    = 25.*1000.
        c.MuFilter.DsSiPMcalibration             = 25.*1000.
        c.MuFilter.timeResol = 150.*u.picosecond
        c.MuFilter.VandUpPropSpeed    = 12.5*u.cm/u.nanosecond
        c.MuFilter.DsPropSpeed        = 14.3*u.cm/u.nanosecond

        c.Floor = AttrDict(z=48000.*u.cm) # to place tunnel in SND_@LHC coordinate system
        c.Floor.DX = 1.0*u.cm 
        c.Floor.DY = -4.5*u.cm #  subtract 4.5cm to avoid overlaps 
        c.Floor.DZ = 0.
