import shipunit as u
import ROOT as r
from ShipGeoConfig import AttrDict, ConfigRegistry
# the following params should be passed through 'ConfigRegistry.loadpy' method
# muShieldDesign = 7  #  7 = short magnet design 9 = optimised with T4 as constraint, 8=requires config file
#                      10 = with field map for hadron absorber, 11 = 9 with field map for muon shield
# nuTargetPassive = 1  #0 = with active layers, 1 = only passive
# nuTauTargetDesign  =   #0 = TP, 1 = NEW with magnet, 2 = NEW without magnet, 3 = 2018 design

# targetOpt      = 5  # 0=solid   >0 sliced, 5: 5 pieces of tungsten, 4 air slits, 17: molybdenum tungsten interleaved with H20
# strawOpt       = 0  # 0=simplistic tracking stations defined in veto.cxx  1=detailed strawtube design 4=sophisticated straw tube design, horizontal wires (default) 10=2cm straw diameter for 2018 layout
# tankDesign = 5 #  4=TP elliptical tank design, 5 = optimized conical rectangular design, 6=5 without segment-1
shield_db = {
    'combi': [ 70.  , 170.  , 208.  , 207.  , 281.  , 172.82, 212.54, 168.64,
    40.  ,  40.  , 150.  , 150.  ,   2.  ,   2.  ,  80.  ,  80.  ,
    150.  , 150.  ,   2.  ,   2.  ,  72.  ,  51.  ,  29.  ,  46.  ,
    10.  ,   7.  ,  54.  ,  38.  ,  46.  , 192.  ,  14.  ,   9.  ,
    10.  ,  31.  ,  35.  ,  31.  ,  51.  ,  11.  ,   3.  ,  32.  ,
    54.  ,  24.  ,   8.  ,   8.  ,  22.  ,  32.  , 209.  ,  35.  ,
    8.  ,  13.  ,  33.  ,  77.  ,  85.  , 241.  ,   9.  ,  26.  ],
    'sc_v6': [70,170,0,353.078,125.083,184.834,150.193,186.812,40,40,150,150,2,2,80,80,150,150,2,2,72,51,29,46,10,7,45.6888,45.6888,22.1839,22.1839,27.0063,16.2448,10,31,35,31,51,11,24.7961,48.7639,8,104.732,15.7991,16.7793,3,100,192,192,2,4.8004,3,100,8,172.729,46.8285,2]
}
if "muShieldDesign" not in globals():
    muShieldDesign = 7
if "muShieldGeo" not in globals():
    muShieldGeo = None
if "nuTargetPassive" not in globals():
    nuTargetPassive = 1
if "nuTauTargetDesign" not in globals():
    nuTauTargetDesign = 4
if "targetOpt" not in globals():
    targetOpt = 18
if "strawDesign" not in globals():
    strawDesign = 4
if "tankDesign" not in globals():
    tankDesign = 6
if "CaloDesign" not in globals():
    CaloDesign = 0
if "Yheight" not in globals():
    Yheight = 10.
if "EcalGeoFile" not in globals():
    if tankDesign > 4:
        EcalGeoFile = "ecal_rect5x10m2.geo"
    else:
        EcalGeoFile = "ecal_ellipse5x10m2.geo"
if "HcalGeoFile" not in globals():
    if tankDesign > 4:
        HcalGeoFile = "hcal_rect.geo"
    else:
        HcalGeoFile = "hcal.geo"
if "muShieldStepGeo" not in globals():
    muShieldStepGeo = False
if "muShieldWithCobaltMagnet" not in globals():
    muShieldWithCobaltMagnet = 0
if "SC_mag" not in globals():
    SC_mag = False
if "shieldName" not in globals():
    shieldName = None
if "SND" not in globals():
    SND = True

with ConfigRegistry.register_config("basic") as c:

    c.DecayVolumeMedium = DecayVolumeMedium
    c.SND = SND

    c.SC_mag = SC_mag
    c.shieldName = shieldName
    # global muShieldDesign, targetOpt, strawDesign, Yheight
    c.Yheight = Yheight*u.m
    # decision by the SP
    totalLength       = 60 * u.m
    extraVesselLength = totalLength - 50*u.m
    windowBulge = 1*u.m
    if tankDesign > 5: windowBulge = 25*u.cm
#
    magnet_design = 2
    if tankDesign == 5: magnet_design = 3
    if tankDesign == 6: magnet_design = 4
#
    c.strawDesign = strawDesign
    c.tankDesign = tankDesign
    c.magnetDesign = magnet_design
# cave parameters
    c.cave = AttrDict(z=0*u.cm)
    c.cave.floorHeightMuonShield = 5*u.m
    c.cave.floorHeightTankA = 4.2*u.m
    if strawDesign == 10:
        c.cave.floorHeightMuonShield = c.cave.floorHeightTankA  # avoid the gap, for 2018 geometry
    c.cave.floorHeightTankB = 2*u.m
#
    #neutrino detector
    c.nuTauTargetDesign=nuTauTargetDesign

    c.chambers = AttrDict(z=0*u.cm)
    magnetIncrease    = 100.*u.cm
    # make z coordinates for the decay volume and tracking stations relative to T4z
    # eventually, the only parameter which needs to be changed when the active shielding lenght changes.
    z4=2438.*u.cm+magnetIncrease+extraVesselLength
    if strawDesign != 4 and strawDesign != 10:
     print("this design ",strawDesign," is not supported, use strawDesign = 4 or 10")
     1/0
    else:
     c.chambers.Length = totalLength
     c.chambers.Tub1length = 2.5 * u.m
     c.chambers.Tub2length = 17.68*u.m+extraVesselLength/2.
     c.chambers.Tub3length = 0.8*u.m
     c.chambers.Tub4length = 2.*u.m+magnetIncrease/2.
     c.chambers.Tub5length = 0.8*u.m
     c.chambers.Tub6length = 0.1*u.m+windowBulge/2.
     c.chambers.Rmin = 245.*u.cm
     c.chambers.Rmax = 250.*u.cm
     # positions and lenghts of vacuum tube segments
     zset=z4-4666.*u.cm-magnetIncrease-extraVesselLength
     c.Chamber1 = AttrDict(z=zset)
     zset=z4-2628.*u.cm-magnetIncrease-extraVesselLength/2.
     c.Chamber2 = AttrDict(z=zset)
     zset=z4-740.*u.cm-magnetIncrease
     c.Chamber3 = AttrDict(z=zset)
     zset=z4-420.*u.cm-magnetIncrease/2.
     c.Chamber4 = AttrDict(z=zset)
     zset=z4-100.*u.cm
     c.Chamber5 = AttrDict(z=zset)
     zset=z4+30.*u.cm+windowBulge/2.
     c.Chamber6 = AttrDict(z=zset)

     c.xMax = 2 * u.m  # max horizontal width at T4
     #
     c.TrackStation4 = AttrDict(z=z4)
     zset=z4-200.*u.cm
     c.TrackStation3 = AttrDict(z=zset)
     zset=z4-640.*u.cm-magnetIncrease
     c.TrackStation2 = AttrDict(z=zset)
     zset=z4-840.*u.cm-magnetIncrease
     c.TrackStation1 = AttrDict(z=zset)
     zset=z4-4406.*u.cm-magnetIncrease-extraVesselLength
     c.vetoStation   = AttrDict(z=zset)

    c.z = c.TrackStation2.z + 0.5 * (c.TrackStation3.z - c.TrackStation2.z)
    c.scintillator = AttrDict(z=0*u.cm)
    c.scintillator.Rmin = 251.*u.cm
    c.scintillator.Rmax = 260.*u.cm

    c.strawtubes = AttrDict(z=0*u.cm)
    if strawDesign==4:
     c.strawtubes.InnerStrawDiameter = 0.975*u.cm
     c.strawtubes.StrawPitch         = 1.76*u.cm
     c.strawtubes.DeltazLayer        = 1.1*u.cm
     c.strawtubes.DeltazPlane        = 2.6*u.cm
     c.strawtubes.YLayerOffset = c.strawtubes.StrawPitch  / 2.
     c.strawtubes.YPlaneOffset = c.strawtubes.StrawPitch  / 4.
     c.strawtubes.FrameMaterial      = "aluminium"
     c.strawtubes.FrameLateralWidth  = 1.*u.cm
     c.strawtubes.DeltazFrame        = 10.*u.cm
    elif strawDesign==10:  # 10 - baseline for 2018
     c.strawtubes.InnerStrawDiameter = 1.9928 * u.cm
     c.strawtubes.StrawPitch = 2. * u.cm
     c.strawtubes.DeltazLayer = 1.732 * u.cm
     c.strawtubes.DeltazPlane = 0 * u.cm
     c.strawtubes.YLayerOffset = 1. * u.cm
     c.strawtubes.YPlaneOffset = 0 * u.cm
     c.strawtubes.FrameMaterial = "steel"
     c.strawtubes.FrameLateralWidth = 0.17 * u.m
     c.strawtubes.DeltazFrame = 2.5 * u.cm

    c.strawtubes.WallThickness = 0.0036 * u.cm
    c.strawtubes.OuterStrawDiameter = (c.strawtubes.InnerStrawDiameter + 2 * c.strawtubes.WallThickness)

    c.strawtubes.StrawsPerLayer = int(c.Yheight/c.strawtubes.StrawPitch)
    c.strawtubes.ViewAngle = 4.57
    c.strawtubes.WireThickness = 0.003 * u.cm
    c.strawtubes.DeltazView = 5. * u.cm
    c.strawtubes.VacBox_x = 240. * u.cm
    c.strawtubes.VacBox_y = 600. * u.cm * c.Yheight / (10. * u.m)

    c.Bfield = AttrDict(z=c.z)
    c.Bfield.max = 0 # 1.4361*u.kilogauss  # was 1.15 in EOI
    c.Bfield.y   = c.Yheight
    c.Bfield.x   = 2.4 * u.m
    c.Bfield.fieldMap = "field/MainSpectrometerField.txt"
    if c.magnetDesign>3:                          # MISIS design
      c.Bfield.YokeWidth = 0.8 * u.m  # full width       200.*cm
      c.Bfield.YokeDepth = 1.4 * u.m  # half length      200 *cm;
      c.Bfield.CoilThick=25.*u.cm  # thickness
      c.Bfield.x = 2.2 * u.m # half apertures
      c.Bfield.y = 3.5 * u.m

# TimeDet
    c.TimeDet = AttrDict(z=0)
    c.TimeDet.dzBarRow = 1.2 * u.cm
    c.TimeDet.dzBarCol = 2.4 * u.cm
    c.TimeDet.zBar = 1 * u.cm
    c.TimeDet.DZ = (c.TimeDet.dzBarRow + c.TimeDet.dzBarCol + c.TimeDet.zBar) / 2
    c.TimeDet.DX = 225 * u.cm
    c.TimeDet.DY = 325 * u.cm
    c.TimeDet.z = c.Chamber6.z + c.chambers.Tub6length + c.TimeDet.DZ + 1*u.cm # safety margin

    if CaloDesign==0:
     c.HcalOption = 1
     c.EcalOption = 1
     c.splitCal = 0
    elif CaloDesign==3:
     c.HcalOption = 2
     c.EcalOption = 1
     c.splitCal = 0
    elif CaloDesign==2:
     c.HcalOption = -1
     c.EcalOption = 2
    else:
     print("CaloDesign option wrong -> ",CaloDesign)
     1/0

    c.SplitCal = AttrDict(z=0)
    c.SplitCal.ZStart = c.TimeDet.z + c.TimeDet.DZ + 5*u.cm
    c.SplitCal.XMax = 480.*u.cm/2. #290.*u.cm  #half length
    c.SplitCal.YMax = 720. * u.cm / 2. #510.*u.cm * c.Yheight / (10.*u.m)   #half length
    c.SplitCal.Empty = 0*u.cm
    c.SplitCal.BigGap = 100*u.cm
    c.SplitCal.ActiveECALThickness = 0.56*u.cm
    c.SplitCal.FilterECALThickness = 0.28*u.cm #  0.56*u.cm   1.757*u.cm
    c.SplitCal.FilterECALThickness_first = 0.28*u.cm
    c.SplitCal.ActiveHCALThickness = 90*u.cm
    c.SplitCal.FilterHCALThickness = 90*u.cm
    c.SplitCal.nECALSamplings = 50
    c.SplitCal.nHCALSamplings = 0
    c.SplitCal.ActiveHCAL = 0
    c.SplitCal.FilterECALMaterial= 3    # 1=scintillator 2=Iron 3 = lead  4 =Argon
    c.SplitCal.FilterHCALMaterial= 2
    c.SplitCal.ActiveECALMaterial= 1
    c.SplitCal.ActiveHCALMaterial= 1
    c.SplitCal.ActiveECAL_gas_Thickness=1.12*u.cm
    c.SplitCal.num_precision_layers=1
    c.SplitCal.first_precision_layer=6
    c.SplitCal.second_precision_layer=10
    c.SplitCal.third_precision_layer=13
    c.SplitCal.ActiveECAL_gas_gap=10*u.cm
    c.SplitCal.NModulesInX = 2
    c.SplitCal.NModulesInY = 4
    c.SplitCal.NStripsPerModule = 50
    c.SplitCal.StripHalfWidth = 3*u.cm # c.SplitCal.XMax/(c.SplitCal.NStripsPerModule*c.SplitCal.NModulesInX)
    c.SplitCal.StripHalfLength = 150*u.cm # c.SplitCal.YMax/c.SplitCal.NModulesInY
    c.SplitCal.SplitCalThickness=(c.SplitCal.FilterECALThickness_first-c.SplitCal.FilterECALThickness)+(c.SplitCal.FilterECALThickness+c.SplitCal.ActiveECALThickness)*c.SplitCal.nECALSamplings+c.SplitCal.BigGap

    c.ecal  =  AttrDict(z = c.TimeDet.z + c.TimeDet.DZ  + 5*u.cm)  #
    c.ecal.File = EcalGeoFile
    hcalThickness = 232*u.cm
    if  c.HcalOption == 2: hcalThickness = 110*u.cm  # to have same interaction length as before
    if not c.HcalOption < 0:
     c.hcal =  AttrDict(z=c.ecal.z + hcalThickness/2. + 45.*u.cm  )
     c.hcal.hcalSpace = hcalThickness + 5.5*u.cm
     c.hcal.File  =  HcalGeoFile
    else:
     c.hcal  =  AttrDict(z=c.ecal.z)
    if c.EcalOption == 1:
     c.MuonStation0 = AttrDict(z=c.hcal.z+hcalThickness/2.+20.5*u.cm)
    if c.EcalOption == 2:
     c.MuonStation0 = AttrDict(z=c.SplitCal.ZStart+10*u.cm+c.SplitCal.SplitCalThickness)

    c.MuonStation1 = AttrDict(z=c.MuonStation0.z+1*u.m)
    c.MuonStation2 = AttrDict(z=c.MuonStation0.z+2*u.m)
    c.MuonStation3 = AttrDict(z=c.MuonStation0.z+3*u.m)

    c.MuonFilter0 = AttrDict(z=c.MuonStation0.z+50.*u.cm)
    c.MuonFilter1 = AttrDict(z=c.MuonStation0.z+150.*u.cm)
    c.MuonFilter2 = AttrDict(z=c.MuonStation0.z+250.*u.cm)

    c.Muon = AttrDict(z=0)
    c.Muon.XMax = 250. * u.cm
    c.Muon.YMax = 325. * u.cm

    c.Muon.ActiveThickness = 0.5*u.cm
    c.Muon.FilterThickness = 30.*u.cm

    # target absorber muon shield setup, decayVolume.length = nominal EOI length, only kept to define z=0
    c.decayVolume            =  AttrDict(z=0*u.cm)
    c.decayVolume.length     =   50*u.m

    c.muShield       =  AttrDict(z=0*u.cm)
    c.muShieldDesign = muShieldDesign
    c.muShield.Field = 1.7 # in units of Tesla expected by ShipMuonShield
    c.muShield.LE = 7 * u.m     # - 0.5 m air - Goliath: 4.5 m - 0.5 m air - nu-tau mu-det: 3 m - 0.5 m air. finally 10m asked by Giovanni
    c.muShield.dZ0 = 1 * u.m

    c.muShieldStepGeo = muShieldStepGeo
    c.muShieldWithCobaltMagnet = muShieldWithCobaltMagnet

    # zGap to compensate automatic shortening of magnets
    zGap = 0.05 * u.m  # halflengh of gap
    if muShieldDesign == 7:
        c.muShield.Field = 1.8  # Tesla
        c.muShield.dZ1 = 0.7 * u.m + zGap
        c.muShield.dZ2 = 1.7 * u.m + zGap
        c.muShield.dZ3 = 2.0*u.m + zGap
        c.muShield.dZ4 = 2.0*u.m + zGap
        c.muShield.dZ5 = 2.75*u.m + zGap
        c.muShield.dZ6 = 2.4*u.m + zGap
        c.muShield.dZ7 = 3.0*u.m + zGap
        c.muShield.dZ8 = 2.35*u.m + zGap
        c.muShield.dXgap = 0.*u.m
    elif muShieldDesign == 9:
        c.muShield.dZ1 = 0.35 * u.m + zGap
        c.muShield.dZ2 = 2.26 * u.m + zGap
        c.muShield.dZ3 = 2.08 * u.m + zGap
        c.muShield.dZ4 = 2.07 * u.m + zGap
        c.muShield.dZ5 = 2.81 * u.m + zGap
        c.muShield.dZ6 = 2.48 * u.m + zGap
        c.muShield.dZ7 = 3.05 * u.m + zGap
        c.muShield.dZ8 = 2.42 * u.m + zGap
        c.muShield.dXgap = 0. * u.m
        c.muShield.half_X_max = 179 * u.cm
        c.muShield.half_Y_max = 317 * u.cm
    elif muShieldDesign == 8:
        assert shieldName
        params = shield_db[shieldName]
        c.muShield.params = params
        c.muShield.dZ1 = 0.35*u.m + zGap
        c.muShield.dZ2 = 2.26*u.m + zGap
        c.muShield.dZ3 = params[2]
        c.muShield.dZ4 = params[3]
        c.muShield.dZ5 = params[4]
        c.muShield.dZ6 = params[5]
        c.muShield.dZ7 = params[6]
        c.muShield.dZ8 = params[7]
        c.muShield.dXgap = 0.*u.m

        offset = 7
        c.muShield.half_X_max = 0
        c.muShield.half_Y_max = 0
        for index in range(2, 8):
            f_l = params[offset + index * 6 + 1]
            f_r = params[offset + index * 6 + 2]
            h_l = params[offset + index * 6 + 3]
            h_r = params[offset + index * 6 + 4]
            g_l = params[offset + index * 6 + 5]
            g_r = params[offset + index * 6 + 6]
            c.muShield.half_X_max = max(c.muShield.half_X_max, 2 * f_l + g_l, 2 * f_r + g_r)
            c.muShield.half_Y_max = max(c.muShield.half_Y_max, h_l + f_l, h_r + f_r)
        c.muShield.half_X_max += 15 * u.cm
        c.muShield.half_Y_max += 15 * u.cm
    else:
        raise NotImplementedError(f"muShieldDesign {muShieldDesign} not supported")

    c.muShield.length = 2 * (
            c.muShield.dZ1 + c.muShield.dZ2 +
            c.muShield.dZ3 + c.muShield.dZ4 +
            c.muShield.dZ5 + c.muShield.dZ6 +
            c.muShield.dZ7 + c.muShield.dZ8
    ) + c.muShield.LE
    c.muShield.z = -(c.decayVolume.length + c.muShield.length) / 2.

    c.hadronAbsorber              =  AttrDict(z=0*u.cm)
    c.hadronAbsorber.length =     0*u.m # magnetized, counted inside muonshield
    c.hadronAbsorber.z     =  c.muShield.z - c.muShield.length/2. - c.hadronAbsorber.length/2.

    c.hadronAbsorber.WithConstField = True
    c.muShield.WithConstField = True

    c.target               =  AttrDict(z=0*u.cm)
    c.targetOpt            =  targetOpt
    if targetOpt < 10:
     c.target.sl            =  1*u.cm  # air slit total length
     c.target.length        =  50*u.cm + c.target.sl * (targetOpt-1)
    else:
   #          material,length
     c.target.M1 = "molybdenum"
     c.target.L1 = 8.*u.cm
     c.target.M2 = "molybdenum"
     c.target.L2 = 2.5*u.cm
     c.target.M3 = "molybdenum"
     c.target.L3 = 2.5*u.cm
     c.target.M4 = "molybdenum"
     c.target.L4 = 2.5*u.cm
     c.target.M5 = "molybdenum"
     c.target.L5 = 2.5*u.cm
     c.target.M6 = "molybdenum"
     c.target.L6 = 2.5*u.cm
     c.target.M7 = "molybdenum"
     c.target.L7 = 2.5*u.cm
     c.target.M8 = "molybdenum"
     c.target.L8 = 2.5*u.cm
     c.target.M9 = "molybdenum"
     c.target.L9 = 5.0*u.cm
     c.target.M10 = "molybdenum"
     c.target.L10 = 5.0*u.cm
     c.target.M11 = "molybdenum"
     c.target.L11 = 6.5*u.cm
     c.target.M12 = "molybdenum"
     c.target.L12 = 8.*u.cm
     c.target.M13 = "molybdenum"
     c.target.L13 = 8.*u.cm
     c.target.M14 = "tungsten"
     c.target.L14 = 5.*u.cm
     c.target.M15 = "tungsten"
     c.target.L15 = 8.*u.cm
     c.target.M16 = "tungsten"
     c.target.L16 = 10.*u.cm
     c.target.M17 = "tungsten"
     c.target.L17 = 20.*u.cm
     c.target.M18 = "tungsten"
     c.target.L18 = 35.*u.cm
     c.target.sl  =  0.5*u.cm  # H20 slit *17 times
     c.target.xy  = 30.*u.cm   # full length in x and y
     c.target.length = 17*c.target.sl + c.target.L1 + 7*c.target.L2 + 3*c.target.L9 + c.target.L11 + 3*c.target.L12 + c.target.L16 + c.target.L17 + c.target.L18
    # interaction point, start of target
    c.target.z   =  c.hadronAbsorber.z - c.hadronAbsorber.length/2. - c.target.length/2.
    c.target.z0  =  c.target.z - c.target.length/2.

# for the digitizing step
    c.strawtubes.v_drift = 1./(30*u.ns/u.mm) # for baseline NA62 5mm radius straws)
    c.strawtubes.sigma_spatial = 0.012*u.cm # according to Massi's TP section
# size of straws
    c.strawtubes.StrawLength     = c.xMax
    if tankDesign == 5:
       zF = c.target.z0+c.zFocusX
       c.strawtubes.StrawLength12   = c.xMax*(c.TrackStation1.z-2*c.strawtubes.DeltazView-zF)/(z4-zF)
       c.strawtubes.StrawLengthVeto = c.xMax*(c.vetoStation.z-c.strawtubes.DeltazView-zF)/(z4-zF)
       zF = c.target.z0+c.zFocusY
       c.strawtubes.vetoydim           = c.Yheight/2.*(c.vetoStation.z-c.strawtubes.DeltazView-zF)/(z4-zF)
       c.strawtubes.tr12ydim           = c.Yheight/2.*(c.TrackStation1.z-2*c.strawtubes.DeltazView-zF)/(z4-zF)
       c.strawtubes.tr34ydim           = int(c.Yheight/2.)
    else:
       c.strawtubes.StrawLength12   = c.strawtubes.StrawLength
       c.strawtubes.StrawLengthVeto = c.strawtubes.StrawLength
       if tankDesign > 5: c.strawtubes.StrawLengthVeto = 0.5 # switch of veto strawtracker
       c.strawtubes.vetoydim           = int(c.Yheight/2.)
       c.strawtubes.tr12ydim           = int(c.Yheight/2.)
       c.strawtubes.tr34ydim           = int(c.Yheight/2.)


    #CAMM - For Nu tau detector, keep only these parameters which are used by others...
    c.tauMudet = AttrDict(z=0*u.cm)
    c.tauMudet.Ztot = 3 * u.m #space allocated to Muon spectrometer
    c.tauMudet.zMudetC = c.Chamber1.z -c.chambers.Tub1length - c.tauMudet.Ztot/2 -31*u.cm
    
    
    #Upstream Tagger
    UBT_x_crop = 113.4 * u.cm
    c.UpstreamTagger = AttrDict(z=0)
    c.UpstreamTagger.Z_Glass = 0.2 * u.cm
    c.UpstreamTagger.Y_Glass = 105 * u.cm
    c.UpstreamTagger.X_Glass = 223. * u.cm  - UBT_x_crop
    c.UpstreamTagger.Z_Glass_Border = 0.2 * u.cm
    c.UpstreamTagger.Y_Glass_Border = 1.0 * u.cm
    c.UpstreamTagger.X_Glass_Border = 1.0 * u.cm
    c.UpstreamTagger.Z_PMMA = 0.8 * u.cm
    c.UpstreamTagger.Y_PMMA = 108 * u.cm
    c.UpstreamTagger.X_PMMA = 226 * u.cm  - UBT_x_crop
    c.UpstreamTagger.DY_PMMA = 1.5 * u.cm
    c.UpstreamTagger.DX_PMMA = 1.5 * u.cm
    c.UpstreamTagger.DZ_PMMA = 0.1 * u.cm
    c.UpstreamTagger.Z_FreonSF6 = 0.1 * u.cm
    c.UpstreamTagger.Y_FreonSF6 = 107 * u.cm
    c.UpstreamTagger.X_FreonSF6 = 225 * u.cm  - UBT_x_crop
    c.UpstreamTagger.Z_FreonSF6_2 = 0.8 * u.cm
    c.UpstreamTagger.Y_FreonSF6_2 = 0.5 * u.cm
    c.UpstreamTagger.X_FreonSF6_2 = 0.5 * u.cm
    c.UpstreamTagger.Z_FR4 = 0.15 * u.cm
    c.UpstreamTagger.Y_FR4 = 111 * u.cm
    c.UpstreamTagger.X_FR4 = 229 * u.cm  - UBT_x_crop
    c.UpstreamTagger.Z_Aluminium = 1.1503 * u.cm
    c.UpstreamTagger.Y_Aluminium = 111 * u.cm
    c.UpstreamTagger.X_Aluminium = 233 * u.cm  - UBT_x_crop
    c.UpstreamTagger.DZ_Aluminium = 0.1 * u.cm
    c.UpstreamTagger.DY_Aluminium = 1 * u.cm
    c.UpstreamTagger.DX_Aluminium = 0.2 * u.cm
    c.UpstreamTagger.Z_Air = 1.1503 * u.cm
    c.UpstreamTagger.Y_Air = 0 * u.cm
    c.UpstreamTagger.X_Air = 2 * u.cm
    c.UpstreamTagger.Z_Strip = 0.0003 * u.cm
    c.UpstreamTagger.Y_Strip = 3.1 * u.cm
    c.UpstreamTagger.X_Strip = 229 * u.cm  - UBT_x_crop
    c.UpstreamTagger.X_Strip64 = 1.534 * u.cm
    c.UpstreamTagger.Y_Strip64 = 111 * u.cm
    c.UpstreamTagger.Z_Position = c.tauMudet.zMudetC + (c.tauMudet.Ztot)/2 + 12.0*u.cm
