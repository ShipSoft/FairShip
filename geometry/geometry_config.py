import os
import shipunit as u
import ROOT as r
from ShipGeoConfig import AttrDict, ConfigRegistry
import yaml

# the following params should be passed through 'ConfigRegistry.loadpy' method
# nuTargetPassive = 1  #0 = with active layers, 1 = only passive
# nuTauTargetDesign  =   #0 = TP, 1 = NEW with magnet, 2 = NEW without magnet, 3 = 2018 design

# targetOpt      = 5  # 0=solid   >0 sliced, 5: 5 pieces of tungsten, 4 air slits, 17: molybdenum tungsten interleaved with H20
# strawOpt       = 0  # 0=simplistic tracking stations defined in veto.cxx  1=detailed strawtube design 4=sophisticated straw tube design, horizontal wires 10=2 cm straw diameter for compact layout (default)
# tankDesign = 5 #  4=TP elliptical tank design, 5 = optimized conical rectangular design, 6=5 without segment-1

# Here you can select the MS geometry, if the MS design is using SC magnet change the hybrid to True
# The first row is the length of the magnets
# The other rows are the transverse dimensions of the magnets:  dXIn[i], dXOut[i] , dYIn[i], dYOut[i], gapIn[i], gapOut[i].
shield_db = {
    "warm_opt": {
        "hybrid": False,
        "params": [
            231.0, 208.0, 207.0, 281.0, 172.82, 212.54, 168.64,
            50.0, 50.0, 119.0, 119.0, 2.0, 2.0, 1.0, 1.0, 50.0, 50.0, 0.0, 0.0, 0.0,
            72.0, 51.0, 29.0, 46.0, 10.0, 7.0,  1.0, 1.0,72.0, 51.0, 0.0, 0.0, 0.0,
            54.0, 38.0, 46.0, 122.0, 14.0, 9.0,  1.0, 1.0,54.0, 38.0, 0.0, 0.0, 0.0,
            10.0, 31.0, 35.0, 31.0, 51.0, 11.0, 1.0, 1.0,0.0, 31.0, 0.0, 0.0, 0.0,
            3.0, 32.0, 54.0, 24.0, 8.0, 8.0, 3.0, 1.0, 1.0,32.0,  0.0, 0.0, 0.0,
            22.0, 32.0, 209.0, 35.0, 8.0, 13.0, 1.0, 1.0,22.0, 32.0, 0.0, 0.0, 0.0,
            33.0, 77.0, 85.0, 241.0, 9.0, 26.0, 1.0, 1.0,33.0, 77.0, 0.0, 0.0, 0.0,
        ]
    },
    "sc_v6": {
        "hybrid": True,
        "params": [
            231.0, 0.0, 353.1, 125.1, 184.8, 150.2, 186.8,
            50.0, 50.0, 119.0, 119.0, 2.0, 2.0, 1.0, 1.0, 50.0, 50.0, 0.0, 0.0, 0.0,
            72.0, 51.0, 29.0, 46.0, 10.0, 7.0, 1.0, 1.0, 72.0, 51.0, 0.0, 0.0, 0.0,
            45.7, 45.7, 22.2, 22.2, 27.0, 16.3, 1.0, 1.0, 45.7, 45.7, 0.0, 0.0, 0.0,
            10.0, 31.0, 35.0, 31.0, 51.0, 11.0, 1.0, 1.0, 10.0, 31.0, 0.0, 0.0, 0.0,
            24.8, 48.8, 8.0, 104.8, 15.8, 16.8, 1.0, 1.0, 24.8, 48.8, 0.0, 0.0, 0.0,
            3.0, 100.0, 192.0, 192.0, 2.0, 4.8, 1.0, 1.0, 3.0, 100.0, 0.0, 0.0, 0.0,
            3.0, 100.0, 8.0, 172.7, 46.8, 2.0, 1.0, 1.0, 3.0, 100.0, 0.0, 0.0, 0.0,
        ]
    }
}
if "muShieldGeo" not in globals():
    muShieldGeo = None
if "nuTargetPassive" not in globals():
    nuTargetPassive = 1
if "nuTauTargetDesign" not in globals():
    nuTauTargetDesign = 4
if "TARGET_YAML" not in globals():
    TARGET_YAML = os.path.expandvars("$FAIRSHIP/geometry/target_config_old.yaml")
if "strawDesign" not in globals():
    strawDesign = 10
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
if "shieldName" not in globals():
    shieldName = None
if "SND" not in globals():
    SND = True
if "SND_design" not in globals():
    SND_design = 1

with ConfigRegistry.register_config("basic") as c:

    c.DecayVolumeMedium = DecayVolumeMedium
    c.SND = SND
    c.SND_design = SND_design
    c.target_yaml = TARGET_YAML

    if not shieldName:
        raise ValueError("shieldName must not be empty!")

    c.shieldName = shieldName
    c.SC_mag = shield_db[shieldName]['hybrid']

    # global targetOpt, strawDesign, Yheight
    c.Yheight = Yheight*u.m
    extraVesselLength = 10 * u.m
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
    c.cave = AttrDict()
    c.cave.floorHeightMuonShield = 5*u.m
    c.cave.floorHeightTankA = 4.2*u.m
    if strawDesign == 10:
        c.cave.floorHeightMuonShield = c.cave.floorHeightTankA  # avoid the gap, for 2018 geometry
    c.cave.floorHeightTankB = 2*u.m
#
    #neutrino detector
    c.nuTauTargetDesign=nuTauTargetDesign

    with open(c.target_yaml) as file:
        config = yaml.safe_load(file)
        c.target = AttrDict(config['target'])

    target_length = (c.target.Nplates - 1) * c.target.sl
    for width, n in zip(c.target.L, c.target.N):
        target_length += width * n
    c.target.length = target_length
    # interaction point, start of target

    c.target.z0 = 0  # Origin of SHiP coordinate system
    c.target.z = c.target.z0 + c.target.length / 2.

    c.chambers = AttrDict()
    magnetIncrease    = 100.*u.cm
    c.muShield = AttrDict()
    c.muShield.Field = 1.7 # in units of Tesla expected by ShipMuonShield
    c.muShield.LE = 7 * u.m     # - 0.5 m air - Goliath: 4.5 m - 0.5 m air - nu-tau mu-det: 3 m - 0.5 m air. finally 10m asked by Giovanni
    c.muShield.dZ0 = 1 * u.m


    # zGap to compensate automatic shortening of magnets
    zGap = 0.05 * u.m  # halflengh of gap


    params = shield_db[shieldName]['params']
    c.muShield.params = params
    c.muShield.dZ1 = params[0]
    c.muShield.dZ2 = params[1]
    c.muShield.dZ3 = params[2]
    c.muShield.dZ4 = params[3]
    c.muShield.dZ5 = params[4]
    c.muShield.dZ6 = params[5]
    c.muShield.dZ7 = params[6]
    c.muShield.dXgap = 0. *u.m


    c.muShield.length = 2 * (
            c.muShield.dZ1 + c.muShield.dZ2 +
            c.muShield.dZ3 + c.muShield.dZ4 +
            c.muShield.dZ5 + c.muShield.dZ6 +
            c.muShield.dZ7
    ) + c.muShield.LE

    c.hadronAbsorber = AttrDict()
    c.hadronAbsorber.length = 0 * u.m  # magnetized, counted inside muonshield
    c.hadronAbsorber.z = c.target.z + c.hadronAbsorber.length / 2. + c.target.length / 2.
    c.muShield.z = c.hadronAbsorber.z + c.muShield.length / 2. + c.hadronAbsorber.length / 2.

    c.decayVolume = AttrDict()

    # target absorber muon shield setup, decayVolume.length = nominal EOI length, only kept to define z=0
    c.decayVolume.length = 50 * u.m

    c.decayVolume.z = c.muShield.z + c.decayVolume.length / 2. + c.muShield.length / 2.
    c.decayVolume.z0 = c.decayVolume.z - c.decayVolume.length / 2.

    # make z coordinates for the decay volume and tracking stations relative to T4z
    # eventually, the only parameter which needs to be changed when the active shielding lenght changes.
    c.z = 31.450 * u.m + c.decayVolume.z # Relative position of spectrometer magnet to decay vessel centre
    if strawDesign != 4 and strawDesign != 10:
     print("this design ",strawDesign," is not supported, use strawDesign = 4 or 10")
     1/0
    else:
     c.chambers.Tub1length = 2.5 * u.m
     c.chambers.Tub2length = 17.68*u.m+extraVesselLength/2.
     c.chambers.Tub3length = 0.8*u.m
     c.chambers.Tub4length = 2.*u.m+magnetIncrease/2.
     c.chambers.Tub5length = 0.8*u.m
     c.chambers.Tub6length = 0.1*u.m+windowBulge/2.
     c.chambers.Rmin = 245.*u.cm
     c.chambers.Rmax = 250.*u.cm


     c.xMax = 2 * u.m  # max horizontal width at T4
     TrGap = 2 * u.m  # Distance between Tr1/2 and Tr3/4
     TrMagGap = 3.5 * u.m  # Distance from spectrometer magnet centre to the next tracking stations
     #
     z4 = c.z + TrMagGap + TrGap
     c.TrackStation4 = AttrDict(z=z4)
     z3 = c.z + TrMagGap
     c.TrackStation3 = AttrDict(z=z3)
     z2 = c.z - TrMagGap
     c.TrackStation2 = AttrDict(z=z2)
     z1 = c.z - TrMagGap - TrGap
     c.TrackStation1 = AttrDict(z=z1)

     # positions and lenghts of vacuum tube segments (for backward compatibility)
     c.Chamber1 = AttrDict(z=z4 - 4666. * u.cm - magnetIncrease - extraVesselLength)
     c.Chamber6 = AttrDict(z=z4 + 30. * u.cm + windowBulge / 2.)

    c.strawtubes = AttrDict()
    if strawDesign == 4:
     c.strawtubes.InnerStrawDiameter = 0.975*u.cm
     c.strawtubes.StrawPitch         = 1.76*u.cm
     c.strawtubes.DeltazLayer        = 1.1*u.cm
     c.strawtubes.DeltazPlane        = 2.6*u.cm
     c.strawtubes.YLayerOffset = c.strawtubes.StrawPitch  / 2.
     c.strawtubes.YPlaneOffset = c.strawtubes.StrawPitch  / 4.
     c.strawtubes.FrameMaterial      = "aluminium"
     c.strawtubes.FrameLateralWidth  = 1.*u.cm
     c.strawtubes.DeltazFrame        = 10.*u.cm
    elif strawDesign == 10:  # 10 - baseline
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

    c.Bfield = AttrDict()
    c.Bfield.z = c.z
    c.Bfield.max = 0 # 1.4361*u.kilogauss  # was 1.15 in EOI
    c.Bfield.y   = c.Yheight
    c.Bfield.x   = 2.4 * u.m
    c.Bfield.fieldMap = "files/MainSpectrometerField.root"
    if c.magnetDesign>3:                          # MISIS design
      c.Bfield.YokeWidth = 0.8 * u.m  # full width       200.*cm
      c.Bfield.YokeDepth = 1.4 * u.m  # half length      200 *cm;
      c.Bfield.CoilThick=25.*u.cm  # thickness
      c.Bfield.x = 2.2 * u.m # half apertures
      c.Bfield.y = 3.5 * u.m

# TimeDet
    c.TimeDet = AttrDict()
    c.TimeDet.dzBarRow = 1.2 * u.cm
    c.TimeDet.dzBarCol = 2.4 * u.cm
    c.TimeDet.zBar = 1 * u.cm
    c.TimeDet.DZ = (c.TimeDet.dzBarRow + c.TimeDet.dzBarCol + c.TimeDet.zBar) / 2
    c.TimeDet.DX = 225 * u.cm
    c.TimeDet.DY = 325 * u.cm
    c.TimeDet.z = 37.800 * u.m - c.TimeDet.dzBarRow * 3 / 2 + c.decayVolume.z # Relative position of first layer of timing detector to decay vessel centre

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

    c.SplitCal = AttrDict()
    c.SplitCal.ZStart = 38.450 * u.m + c.decayVolume.z # Relative start z of split cal to decay vessel centre
    c.SplitCal.XMax = 4 * u.m / 2  # half length
    c.SplitCal.YMax = 6 * u.m / 2  # half length
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
    c.SplitCal.NModulesInY = 3
    c.SplitCal.NStripsPerModule = 50
    c.SplitCal.StripHalfWidth = c.SplitCal.XMax / (c.SplitCal.NStripsPerModule * c.SplitCal.NModulesInX)
    c.SplitCal.StripHalfLength = c.SplitCal.YMax / c.SplitCal.NModulesInY
    c.SplitCal.SplitCalThickness=(c.SplitCal.FilterECALThickness_first-c.SplitCal.FilterECALThickness)+(c.SplitCal.FilterECALThickness+c.SplitCal.ActiveECALThickness)*c.SplitCal.nECALSamplings+c.SplitCal.BigGap

    zecal = 38.450 * u.m + c.decayVolume.z # Relative start z of ECAL to decay vessel centre
    c.ecal = AttrDict(z=zecal)
    c.ecal.File = EcalGeoFile
    hcalThickness = 232*u.cm
    if  c.HcalOption == 2: hcalThickness = 110*u.cm  # to have same interaction length as before
    if not c.HcalOption < 0:
     zhcal = 40.850 * u.m + c.decayVolume.z # Relative position of HCAL to decay vessel centre
     c.hcal = AttrDict(z=zhcal)
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

    c.Muon = AttrDict()
    c.Muon.XMax = 250. * u.cm
    c.Muon.YMax = 325. * u.cm

    c.Muon.ActiveThickness = 0.5*u.cm
    c.Muon.FilterThickness = 30.*u.cm

    c.hadronAbsorber.WithConstField = True
    c.muShield.WithConstField = True


# for the digitizing step
    c.strawtubes.v_drift = 1./(30*u.ns/u.mm) # for baseline NA62 5mm radius straws)
    c.strawtubes.sigma_spatial = 0.012*u.cm # according to Massi's TP section
# size of straws
    c.strawtubes.StrawLength     = c.xMax
    if tankDesign == 5:
       zF = c.target.z0 + c.zFocusX
       c.strawtubes.StrawLength12   = c.xMax*(c.TrackStation1.z-2*c.strawtubes.DeltazView-zF)/(z4-zF)
       zF = c.target.z0 + c.zFocusY

       c.strawtubes.tr12ydim           = c.Yheight/2.*(c.TrackStation1.z-2*c.strawtubes.DeltazView-zF)/(z4-zF)
       c.strawtubes.tr34ydim           = int(c.Yheight/2.)
    else:
       c.strawtubes.StrawLength12   = c.strawtubes.StrawLength
       c.strawtubes.tr12ydim           = int(c.Yheight/2.)
       c.strawtubes.tr34ydim           = int(c.Yheight/2.)


    #CAMM - For Nu tau detector, keep only these parameters which are used by others...
    c.tauMudet = AttrDict()
    c.tauMudet.Ztot = 3 * u.m #space allocated to Muon spectrometer
    c.tauMudet.zMudetC = c.muShield.z + c.muShield.length / 2. - c.tauMudet.Ztot / 2. - 70 * u.cm


    #Upstream Tagger
    UBT_x_crop = 113.4 * u.cm
    c.UpstreamTagger = AttrDict()
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
    c.UpstreamTagger.Z_Position = -25.400 * u.m + c.decayVolume.z # Relative position of UBT to decay vessel centre
