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
        c.EmulsionDet.Xpos0 = 5.74
        c.EmulsionDet.Xpos1 = 5.74
        c.EmulsionDet.Xpos2 = 5.74
        c.EmulsionDet.Xpos3 = 5.74
        c.EmulsionDet.Xpos4 = 5.74
        c.EmulsionDet.Ypos0 = 288.89
        c.EmulsionDet.Ypos1 = 301.89
        c.EmulsionDet.Ypos2 = 314.89
        c.EmulsionDet.Ypos3 = 327.89
        c.EmulsionDet.Ypos4 = 340.89
        c.EmulsionDet.Zpos0 = 16.63
        c.EmulsionDet.Zpos1 = 16.63
        c.EmulsionDet.Zpos2 = 16.63
        c.EmulsionDet.Zpos3 = 16.63
        c.EmulsionDet.Zpos4 = 16.63

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
        c.Scifi.Xpos0 = 4.34*u.cm
        c.Scifi.Xpos1 = 4.34*u.cm
        c.Scifi.Xpos2 = 4.34*u.cm
        c.Scifi.Xpos3 = 4.34*u.cm
        c.Scifi.Xpos4 = 4.34*u.cm
        c.Scifi.Ypos0 = 298.94*u.cm
        c.Scifi.Ypos1 = 311.94*u.cm
        c.Scifi.Ypos2 = 324.94*u.cm
        c.Scifi.Ypos3 = 337.94*u.cm
        c.Scifi.Ypos4 = 350.94*u.cm
        c.Scifi.Zpos0 = 15.22*u.cm
        c.Scifi.Zpos1 = 15.22*u.cm
        c.Scifi.Zpos2 = 15.22*u.cm
        c.Scifi.Zpos3 = 15.22*u.cm
        c.Scifi.Zpos4 = 15.22*u.cm

# Scifi technical drawing, distance from first channel on vertical / horizontal plane to edge point  225,225,0, xy plane z perpendicularc.Scifi.ydim
        c.Scifi.EdgeAX =  225*u.mm
        c.Scifi.EdgeAY =  225*u.mm
        c.Scifi.EdgeAZ =  0*u.mm

        c.Scifi.FirstChannelVX = -195.28*u.mm
        c.Scifi.FirstChannelVY = -200.0*u.mm
        c.Scifi.FirstChannelVZ = -12.92*u.mm

        c.Scifi.FirstChannelHX = -200.0*u.mm
        c.Scifi.FirstChannelHY = -195.28*u.mm
        c.Scifi.FirstChannelHZ = -7.07*u.mm

# Local Scifi position of first channel on a vertical scifi plane in software
        c.Scifi.LfirstChannelVX = -195.135*u.mm
        c.Scifi.LfirstChannelVY = 195.0*u.mm   # sipm on top
        c.Scifi.LfirstChannelVZ = 11.85*u.mm

# Local Scifi position of last channel (=first channel on technical drawing) on a horizontal scifi plane in software
        c.Scifi.LfirstChannelHX = -195.0*u.mm   # sipm on the right side direction away from IP1
        c.Scifi.LfirstChannelHY = 195.178*u.mm
        c.Scifi.LfirstChannelHZ = 6.25*u.mm
 
        c.MuFilter = AttrDict(z=0*u.cm)
        #coordinates in local gravity based system
        c.MuFilter.Veto1Dx = 44.5*u.mm
        c.MuFilter.Veto1Dy = 2798*u.mm
        c.MuFilter.Veto1Dz = 185.9*u.mm
        c.MuFilter.Veto2Dx = 44.5*u.mm
        c.MuFilter.Veto2Dy = 2839*u.mm
        c.MuFilter.Veto2Dz = 165.9*u.mm

        c.MuFilter.Iron1Dx = -24.2*u.mm
        c.MuFilter.Iron1Dy = 3579.6*u.mm
        c.MuFilter.Iron1Dz = 146.6*u.mm
        # US1
        c.MuFilter.Muon1Dx = -47.1*u.mm
        c.MuFilter.Muon1Dy = 3760.2*u.mm
        c.MuFilter.Muon1Dz = 146.6*u.mm

        c.MuFilter.Iron2Dx = -24.2*u.mm
        c.MuFilter.Iron2Dy = 3804.6*u.mm
        c.MuFilter.Iron2Dz = 136.6*u.mm
        # US2
        c.MuFilter.Muon2Dx = -47.1*u.mm
        c.MuFilter.Muon2Dy = 3985.2*u.mm
        c.MuFilter.Muon2Dz = 136.6*u.mm

        c.MuFilter.Iron3Dx = -24.2*u.mm
        c.MuFilter.Iron3Dy = 4029.6*u.mm
        c.MuFilter.Iron3Dz = 126.6*u.mm
        # US3
        c.MuFilter.Muon3Dx = -47.1*u.mm
        c.MuFilter.Muon3Dy = 4210.2*u.mm
        c.MuFilter.Muon3Dz = 126.6*u.mm

        c.MuFilter.Iron4Dx = -24.2*u.mm
        c.MuFilter.Iron4Dy = 4254.6*u.mm
        c.MuFilter.Iron4Dz = 116.7*u.mm
        # US4
        c.MuFilter.Muon4Dx = -47.1*u.mm
        c.MuFilter.Muon4Dy = 4435.2*u.mm
        c.MuFilter.Muon4Dz = 116.7*u.mm

        c.MuFilter.Iron5Dx = -24.2*u.mm
        c.MuFilter.Iron5Dy = 4479.6*u.mm    # +225.0mm
        c.MuFilter.Iron5Dz = 127.7*u.mm
        # US5
        c.MuFilter.Muon5Dx = -47.1*u.mm
        c.MuFilter.Muon5Dy = 4660.2*u.mm
        c.MuFilter.Muon5Dz = 127.7*u.mm

        c.MuFilter.Iron6Dx = -24.2*u.mm
        c.MuFilter.Iron6Dy = 4704.6*u.mm     # +225.0mm
        c.MuFilter.Iron6Dz = 127.7*u.mm
        # DS1
        c.MuFilter.Muon6Dx = -47.1*u.mm
        c.MuFilter.Muon6Dy = 4884.9*u.mm
        c.MuFilter.Muon6Dz = 127.7*u.mm

        c.MuFilter.Iron7Dx = -24.2*u.mm
        c.MuFilter.Iron7Dy = 4943.6*u.mm       # +239.0mm
        c.MuFilter.Iron7Dz = 127.7*u.mm
        # DS2
        c.MuFilter.Muon7Dx = -47.1*u.mm
        c.MuFilter.Muon7Dy = 5123.9*u.mm
        c.MuFilter.Muon7Dz = 127.7*u.mm

        c.MuFilter.Iron8Dx = -24.2*u.mm
        c.MuFilter.Iron8Dy = 5183.9*u.mm        # +240.3mm
        c.MuFilter.Iron8Dz = 127.7*u.mm
        # DS3
        c.MuFilter.Muon8Dx = -4.7*u.mm
        c.MuFilter.Muon8Dy = 5383.7*u.mm
        c.MuFilter.Muon8Dz = 127.7*u.mm

        c.MuFilter.DS4ZGap = 8.82*u.cm
        # DS4V
        c.MuFilter.Muon9Dx = -4.7*u.mm
        c.MuFilter.Muon9Dy = 5383.7*u.mm + c.MuFilter.DS4ZGap
        c.MuFilter.Muon9Dz = 127.7*u.mm
        c.MuFilter.Iron9Dx = 175.8*u.mm
        c.MuFilter.Iron9Dy = 5529.7*u.mm
        c.MuFilter.Iron9Dz = 127.7*u.mm

        # relation between edge and bottom bar for VETO
        c.MuFilter.VETOLocX = 20.0*u.mm
        c.MuFilter.VETOLocY = 20.0*u.mm
        c.MuFilter.VETOLocZ = 46.7*u.mm

        # relation between edge and bottom bar for US and DS
        c.MuFilter.DSHLocX = 10.5*u.mm
        c.MuFilter.DSHLocY = 32.0*u.mm
        c.MuFilter.DSHLocZ = 11.1*u.mm
        # relation between edge and right bar
        c.MuFilter.DSVLocX = 623.0*u.mm
        c.MuFilter.DSVLocY = 47.0*u.mm
        c.MuFilter.DSVLocZ = 641.3*u.mm

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

        c.MuFilter.VetoBarX = 42 *u.cm
        c.MuFilter.VetoBarY = 6 * u.cm
        c.MuFilter.VetoBarZ = 1 * u.cm
        c.MuFilter.VetoBarGap = 2*30*u.um  # wrapping material

        c.MuFilter.FeX = 80*u.cm
        c.MuFilter.FeY = 60*u.cm
        c.MuFilter.FeZ = 20*u.cm
        c.MuFilter.FeEndX = 40*u.cm
        c.MuFilter.FeEndY = 40*u.cm
        c.MuFilter.FeEndZ = 20*u.cm
        c.MuFilter.FeBotX = 80*u.cm
        c.MuFilter.FeBotY =   9*u.cm
        c.MuFilter.FeBotZ = 40*u.cm

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
        c.MuFilter.UpstreamBarX = 82.525*u.cm
        c.MuFilter.UpstreamBarY = 6.0*u.cm
        c.MuFilter.UpstreamBarZ = 1.0*u.cm
        c.MuFilter.UpstreamBarGap = 0.1*u.mm

        #downstream bars configuration
        c.MuFilter.NDownstreamBars = 60 #n.d.r. both for x and y in this case
        c.MuFilter.DownstreamBarX = 82.525*u.cm
        c.MuFilter.DownstreamBarY = 1*u.cm
        c.MuFilter.DownstreamBarZ = 1*u.cm
        c.MuFilter.DownstreamBarGap = 0.1*u.mm
        c.MuFilter.DownstreamBarX_ver = 1*u.cm 
        c.MuFilter.DownstreamBarY_ver = 63.525*u.cm  #the vertical bars cover a region only 60 x 60 cm2
        c.MuFilter.DownstreamBarZ_ver = 1*u.cm

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

# for H6 / H8 testbeam and commissioning
        H6 = True
        if H6:
           c.Floor.z = 0   # no tunnel, no slope
           c.MuFilter.Iron9Dy = 0*u.mm # move iron blocks at the end out of the way
# scifi moved 46cm behind the iron block of second DS station and lifted by 10-15 cm.
# equal to move MuFilter in front of target and lower by 10-15cm, from 289 to 538+46, delta = -295
           c.MuFilter.ShiftX =   4.5*u.cm
           c.MuFilter.ShiftY =   -15.5*u.cm
           c.MuFilter.ShiftZ = -275.0*u.cm            # -295cm was 20cm too much
# for H6, Veto  placed directly in front of first US
           c.MuFilter.VetoShiftZ = 70*u.cm + c.MuFilter.ShiftZ
           c.MuFilter.VetoShiftX = -13.5*u.cm
           c.MuFilter.VetoShiftY = -17.7*u.cm
# fine adjustements
           c.MuFilter.Muon8Dx = -4.7*u.mm - 4*u.cm
           c.MuFilter.Muon7Dx = -47.1*u.mm + 0.74*u.cm
           c.MuFilter.Muon1Dz = 146.6*u.mm - 2.3*u.cm
           c.MuFilter.Muon2Dz = 136.6*u.mm - 1.5*u.cm
           c.MuFilter.Muon5Dz = 127.7*u.mm + 0.25*u.cm
           c.MuFilter.Muon7Dz = 127.7*u.mm + 0.25*u.cm
           c.MuFilter.Muon8Dz = 127.7*u.mm + 0.56*u.cm
