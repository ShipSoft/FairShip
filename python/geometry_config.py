# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import os

import shipunit as u
import yaml
from ShipGeoConfig import AttrDict, Config

# Parameters for geometry configuration are passed to create_config() function
# nuTargetPassive = 1  #0 = with active layers, 1 = only passive

# targetOpt      = 5  # 0=solid   >0 sliced, 5: 5 pieces of tungsten, 4 air slits, 17: molybdenum tungsten interleaved with H20
# strawOpt       = 0  # 4=aluminium frame 10=steel frame (default)

# Here you can select the MS geometry, if the MS design is using SC magnet change the hybrid to True
# The first row is the length of the magnets
# The other rows are the transverse dimensions of the magnets:  dXIn[i], dXOut[i] , dYIn[i], dYOut[i], gapIn[i], gapOut[i].
shield_db = {
    "warm_opt": {
        "hybrid": False,
        "WithConstField": True,
        "params": [
            231.0,
            208.0,
            207.0,
            281.0,
            172.82,
            212.54,
            168.64,
            50.0,
            50.0,
            119.0,
            119.0,
            2.0,
            2.0,
            1.0,
            1.0,
            50.0,
            50.0,
            0.0,
            0.0,
            1.6,
            72.0,
            51.0,
            29.0,
            46.0,
            10.0,
            7.0,
            1.0,
            1.0,
            72.0,
            51.0,
            0.0,
            0.0,
            1.7,
            54.0,
            38.0,
            46.0,
            122.0,
            14.0,
            9.0,
            1.0,
            1.0,
            54.0,
            38.0,
            0.0,
            0.0,
            1.7,
            10.0,
            31.0,
            35.0,
            31.0,
            51.0,
            11.0,
            1.0,
            1.0,
            0.0,
            31.0,
            0.0,
            0.0,
            1.7,
            3.0,
            32.0,
            54.0,
            24.0,
            8.0,
            8.0,
            3.0,
            1.0,
            1.0,
            32.0,
            0.0,
            0.0,
            1.7,
            22.0,
            32.0,
            209.0,
            35.0,
            8.0,
            13.0,
            1.0,
            1.0,
            22.0,
            32.0,
            0.0,
            0.0,
            1.7,
            33.0,
            77.0,
            85.0,
            241.0,
            9.0,
            26.0,
            1.0,
            1.0,
            33.0,
            77.0,
            0.0,
            0.0,
            1.7,
        ],
    },
    "New_HA_Design": {
        "hybrid": False,
        "WithConstField": True,
        "params": [
            231.0 / 2,
            208.0 + 231.0 / 2,
            207.0,
            281.0,
            172.82,
            212.54,
            168.64,
            50.0,
            50.0,
            119.0,
            119.0,
            2.0,
            2.0,
            1.0,
            1.0,
            50.0,
            50.0,
            0.0,
            0.0,
            1.9,
            72.0,
            51.0,
            29.0,
            46.0,
            10.0,
            7.0,
            1.0,
            1.0,
            72.0,
            51.0,
            0.0,
            0.0,
            1.7,
            54.0,
            38.0,
            46.0,
            122.0,
            14.0,
            9.0,
            1.0,
            1.0,
            54.0,
            38.0,
            0.0,
            0.0,
            1.7,
            10.0,
            31.0,
            35.0,
            31.0,
            51.0,
            11.0,
            1.0,
            1.0,
            0.0,
            31.0,
            0.0,
            0.0,
            1.7,
            3.0,
            32.0,
            54.0,
            24.0,
            8.0,
            8.0,
            3.0,
            1.0,
            1.0,
            32.0,
            0.0,
            0.0,
            1.7,
            22.0,
            32.0,
            209.0,
            35.0,
            8.0,
            13.0,
            1.0,
            1.0,
            22.0,
            32.0,
            0.0,
            0.0,
            1.7,
            33.0,
            77.0,
            85.0,
            241.0,
            9.0,
            26.0,
            1.0,
            1.0,
            33.0,
            77.0,
            0.0,
            0.0,
            1.7,
        ],
    },
}


def create_config(
    DecayVolumeMedium="helium",
    Yheight=6.0,
    strawDesign=10,
    muShieldGeo=None,
    shieldName="New_HA_Design",
    nuTargetPassive=1,
    SND=True,
    SND_design=None,
    TARGET_YAML=None,
):
    """
    Create geometry configuration with specified parameters.

    Args:
        DecayVolumeMedium: Medium in decay volume ("helium" or "vacuums"), default: "helium"
        Yheight: Height of vacuum tank in meters, default: 6.0
        strawDesign: Straw tube design (4=aluminium frame, 10=steel frame), default: 10
        muShieldGeo: Muon shield geometry file (for experts), default: None
        shieldName: Name of shield configuration ("warm_opt" or "New_HA_Design"), default: "New_HA_Design"
        nuTargetPassive: Target type (0=with active layers, 1=only passive), default: 1
        SND: Enable SND detector, default: True
        SND_design: SND design options (list of design numbers), default: [2]
        TARGET_YAML: Path to target YAML configuration file, default: "$FAIRSHIP/geometry/target_config_old.yaml"

    Returns:
        Config: Geometry configuration object
    """
    # Set defaults for mutable parameters
    if SND_design is None:
        SND_design = [2]
    if TARGET_YAML is None:
        TARGET_YAML = os.path.expandvars("$FAIRSHIP/geometry/target_config_old.yaml")

    # Create configuration object
    c = Config()
    c.DecayVolumeMedium = DecayVolumeMedium
    c.SND = SND
    # Ensure SND_design is always a list
    if not isinstance(SND_design, list):
        SND_design = [SND_design]
    c.SND_design = SND_design
    c.target_yaml = TARGET_YAML
    print("Info: Target using configuration:", c.target_yaml)

    if not shieldName:
        raise ValueError("shieldName must not be empty!")

    c.shieldName = shieldName
    c.SC_mag = shield_db[shieldName]["hybrid"]

    # global targetVersion, strawDesign, Yheight
    c.Yheight = Yheight * u.m
    extraVesselLength = 10 * u.m
    windowBulge = 25 * u.cm
    c.strawDesign = strawDesign
    c.magnetDesign = 4
    # cave parameters
    c.cave = AttrDict()
    c.cave.floorHeightMuonShield = 5 * u.m
    c.cave.floorHeightTankA = 4.2 * u.m
    if strawDesign == 10:
        c.cave.floorHeightMuonShield = (
            c.cave.floorHeightTankA
        )  # avoid the gap, for 2018 geometry
    c.cave.floorHeightTankB = 2 * u.m

    with open(c.target_yaml) as file:
        targetconfig = yaml.safe_load(file)
        c.target = AttrDict(targetconfig["target"])

    c.target.slices_length = []
    c.target.slices_gap = []
    c.target.slices_material = []

    for i in range(c.target.Nplates):
        for j in range(c.target.N[i]):
            if len(c.target.L) == 1:
                c.target.slices_length.append(c.target.L[0])
            else:
                c.target.slices_length.append(c.target.L[i])
            if len(c.target.G) == 1:
                c.target.slices_gap.append(c.target.G[0])
            else:
                c.target.slices_gap.append(c.target.G[i])
            if len(c.target.M) == 1:
                c.target.slices_material.append(c.target.M[0])
            else:
                c.target.slices_material.append(c.target.M[i])
    # Last gap should be 0...
    c.target.slices_gap[c.target.nS - 1] = 0
    print(c.target.slices_material, c.target.slices_length, c.target.slices_gap)

    target_length = 0
    for width, gap in zip(c.target.slices_length, c.target.slices_gap):
        target_length += width + gap
    c.target.length = target_length
    c.targetVersion = targetconfig["targetVersion"]
    # interaction point, start of target

    c.target.z0 = 0  # Origin of SHiP coordinate system
    c.target.z = c.target.z0 + c.target.length / 2.0
    c.chambers = AttrDict()
    magnetIncrease = 100.0 * u.cm
    c.muShield = AttrDict()
    c.muShield.Field = 1.7  # in units of Tesla expected by ShipMuonShield
    c.muShield.LE = (
        7 * u.m
    )  # - 0.5 m air - Goliath: 4.5 m - 0.5 m air - nu-tau mu-det: 3 m - 0.5 m air. finally 10m asked by Giovanni
    c.muShield.dZ0 = 1 * u.m

    # zGap to compensate automatic shortening of magnets
    zGap = 0.05 * u.m  # halflengh of gap

    params = shield_db[shieldName]["params"]
    c.muShield.params = params
    c.muShield.dZ1 = params[0]
    c.muShield.dZ2 = params[1]
    c.muShield.dZ3 = params[2]
    c.muShield.dZ4 = params[3]
    c.muShield.dZ5 = params[4]
    c.muShield.dZ6 = params[5]
    c.muShield.dZ7 = params[6]
    c.muShield.dXgap = 0.0 * u.m

    c.muShield.length = (
        2
        * (
            c.muShield.dZ1
            + c.muShield.dZ2
            + c.muShield.dZ3
            + c.muShield.dZ4
            + c.muShield.dZ5
            + c.muShield.dZ6
            + c.muShield.dZ7
        )
        + c.muShield.LE
    )

    c.hadronAbsorber = AttrDict()

    c.hadronAbsorber.z = (
        c.target.z0
        + c.target.length
        + 96.1 * u.mm  # Distance between target and proximity shielding
        + 250 * u.mm  # Thickness of proximity shielding
        + 207.5 * u.mm  # Distance between hadron absorber and proximity shielding
        - 10 * u.cm  # Remove spacing internal to hadron absorber
    )
    c.muShield.z = c.hadronAbsorber.z
    c.decayVolume = AttrDict()

    # target absorber muon shield setup, decayVolume.length = nominal EOI length, only kept to define z=0
    c.decayVolume.length = 50 * u.m

    # make z coordinates for the decay volume and tracking stations relative to T4z
    # eventually, the only parameter which needs to be changed when the active shielding length changes.
    c.z = 89.57 * u.m  # absolute position of spectrometer magnet
    c.decayVolume.z = (
        c.z - 31.450 * u.m
    )  # Relative position of decay vessel centre to spectrometer magnet
    c.decayVolume.z0 = c.decayVolume.z - c.decayVolume.length / 2.0
    if strawDesign != 4 and strawDesign != 10:
        print(
            "this design ", strawDesign, " is not supported, use strawDesign = 4 or 10"
        )
        1 / 0
    else:
        c.chambers.Tub1length = 2.5 * u.m
        c.chambers.Tub2length = 17.68 * u.m + extraVesselLength / 2.0
        c.chambers.Tub3length = 0.8 * u.m
        c.chambers.Tub4length = 2.0 * u.m + magnetIncrease / 2.0
        c.chambers.Tub5length = 0.8 * u.m
        c.chambers.Tub6length = 0.1 * u.m + windowBulge / 2.0
        c.chambers.Rmin = 245.0 * u.cm
        c.chambers.Rmax = 250.0 * u.cm

        c.xMax = 2 * u.m  # max horizontal width at T4
        TrGap = 2 * u.m  # Distance between Tr1/2 and Tr3/4
        TrMagGap = (
            3.5 * u.m
        )  # Distance from spectrometer magnet centre to the next tracking stations
        #
        z4 = c.z + TrMagGap + TrGap
        c.TrackStation4 = AttrDict(z=z4)
        z3 = c.z + TrMagGap
        c.TrackStation3 = AttrDict(z=z3)
        z2 = c.z - TrMagGap
        c.TrackStation2 = AttrDict(z=z2)
        z1 = c.z - TrMagGap - TrGap
        c.TrackStation1 = AttrDict(z=z1)

        # positions and lengths of vacuum tube segments (for backward compatibility)
        c.Chamber1 = AttrDict(z=z4 - 4666.0 * u.cm - magnetIncrease - extraVesselLength)
        c.Chamber6 = AttrDict(z=z4 + 30.0 * u.cm + windowBulge / 2.0)

    c.Bfield = AttrDict()
    c.Bfield.z = c.z
    c.Bfield.max = 0  # 1.4361*u.kilogauss  # was 1.15 in EOI
    c.Bfield.y = c.Yheight
    c.Bfield.x = 2.4 * u.m
    c.Bfield.fieldMap = "files/MainSpectrometerField.root"
    if c.magnetDesign > 3:  # MISIS design
        c.Bfield.YokeWidth = 0.8 * u.m  # full width       200.*cm
        c.Bfield.YokeDepth = 1.4 * u.m  # half length      200 *cm;
        c.Bfield.CoilThick = 25.0 * u.cm  # thickness
        c.Bfield.x = 2.2 * u.m  # half apertures
        c.Bfield.y = 3.5 * u.m

    # TimeDet
    c.TimeDet = AttrDict()
    c.TimeDet.dzBarRow = 1.2 * u.cm
    c.TimeDet.dzBarCol = 2.4 * u.cm
    c.TimeDet.zBar = 1 * u.cm
    c.TimeDet.DZ = (c.TimeDet.dzBarRow + c.TimeDet.dzBarCol + c.TimeDet.zBar) / 2
    c.TimeDet.DX = 225 * u.cm
    c.TimeDet.DY = 325 * u.cm
    c.TimeDet.z = (
        37.800 * u.m - c.TimeDet.dzBarRow * 3 / 2 + c.decayVolume.z
    )  # Relative position of first layer of timing detector to decay vessel centre

    c.HcalOption = -1
    c.EcalOption = 2

    c.SplitCal = AttrDict()
    c.SplitCal.ZStart = (
        38.450 * u.m + c.decayVolume.z
    )  # Relative start z of split cal to decay vessel centre
    c.SplitCal.XMax = 4 * u.m / 2  # half length
    c.SplitCal.YMax = 6 * u.m / 2  # half length
    c.SplitCal.Empty = 0 * u.cm
    c.SplitCal.BigGap = 100 * u.cm
    c.SplitCal.ActiveECALThickness = 0.56 * u.cm
    c.SplitCal.FilterECALThickness = 0.28 * u.cm  #  0.56*u.cm   1.757*u.cm
    c.SplitCal.FilterECALThickness_first = 0.28 * u.cm
    c.SplitCal.ActiveHCALThickness = 90 * u.cm
    c.SplitCal.FilterHCALThickness = 90 * u.cm
    c.SplitCal.nECALSamplings = 50
    c.SplitCal.nHCALSamplings = 0
    c.SplitCal.ActiveHCAL = 0
    c.SplitCal.FilterECALMaterial = 3  # 1=scintillator 2=Iron 3 = lead  4 =Argon
    c.SplitCal.FilterHCALMaterial = 2
    c.SplitCal.ActiveECALMaterial = 1
    c.SplitCal.ActiveHCALMaterial = 1
    c.SplitCal.ActiveECAL_gas_Thickness = 1.12 * u.cm
    c.SplitCal.num_precision_layers = 1
    c.SplitCal.first_precision_layer = 6
    c.SplitCal.second_precision_layer = 10
    c.SplitCal.third_precision_layer = 13
    c.SplitCal.ActiveECAL_gas_gap = 10 * u.cm
    c.SplitCal.NModulesInX = 2
    c.SplitCal.NModulesInY = 3
    c.SplitCal.NStripsPerModule = 50
    c.SplitCal.StripHalfWidth = c.SplitCal.XMax / (
        c.SplitCal.NStripsPerModule * c.SplitCal.NModulesInX
    )
    c.SplitCal.StripHalfLength = c.SplitCal.YMax / c.SplitCal.NModulesInY
    c.SplitCal.SplitCalThickness = (
        (c.SplitCal.FilterECALThickness_first - c.SplitCal.FilterECALThickness)
        + (c.SplitCal.FilterECALThickness + c.SplitCal.ActiveECALThickness)
        * c.SplitCal.nECALSamplings
        + c.SplitCal.BigGap
    )


    c.HCAL = AttrDict()
    c.HCAL.ZStart = (
        38.450 * u.m + c.decayVolume.z
    )  # Relative start z of split cal to decay vessel centre
    c.HCAL.TotalXDim = 4.32 * u.m / 2  # half length
    c.HCAL.TotalYDim = 6.48 * u.m / 2  # half length
    c.HCAL.ScintBarX = 216 * u.cm #For horizontal bars
    c.HCAL.ScintBarY = 6 * u.cm
    c.HCAL.ScintBarZ = 1. * u.cm
    c.HCAL.PassiveLayerZ = 17. * u.cm
    c.HCAL.nSamplings = 5
    c.HCAL.ActiveHCALMaterial = 1
    c.HCAL.NBarsPerLayer = 36 
    c.HCAL.NmodulesX = 2
    c.HCAL.NmodulesY = 3

    c.MuonStation0 = AttrDict(
        z=c.SplitCal.ZStart + 10 * u.cm + c.SplitCal.SplitCalThickness
    )

    c.MuonStation1 = AttrDict(z=c.MuonStation0.z + 1 * u.m)
    c.MuonStation2 = AttrDict(z=c.MuonStation0.z + 2 * u.m)
    c.MuonStation3 = AttrDict(z=c.MuonStation0.z + 3 * u.m)

    c.MuonFilter0 = AttrDict(z=c.MuonStation0.z + 50.0 * u.cm)
    c.MuonFilter1 = AttrDict(z=c.MuonStation0.z + 150.0 * u.cm)
    c.MuonFilter2 = AttrDict(z=c.MuonStation0.z + 250.0 * u.cm)

    c.Muon = AttrDict()
    c.Muon.XMax = 250.0 * u.cm
    c.Muon.YMax = 325.0 * u.cm

    c.Muon.ActiveThickness = 0.5 * u.cm
    c.Muon.FilterThickness = 30.0 * u.cm

    c.hadronAbsorber.WithConstField = shield_db[shieldName][
        "WithConstField"
    ]  # TO BE CHECKED: NOT SURE IT IS NEEDED
    c.muShield.WithConstField = shield_db[shieldName]["WithConstField"]

    # for the digitizing step
    c.strawtubesDigi = AttrDict()
    c.strawtubesDigi.v_drift = 1.0 / (
        30 * u.ns / u.mm
    )  # for baseline NA62 5mm radius straws)
    c.strawtubesDigi.sigma_spatial = 0.012 * u.cm  # according to Massi's TP section

    # CAMM - For Nu tau detector, keep only these parameters which are used by others...
    c.tauMudet = AttrDict()
    c.tauMudet.Ztot = 3 * u.m  # space allocated to Muon spectrometer
    c.tauMudet.zMudetC = (
        c.muShield.z + c.muShield.length / 2.0 - c.tauMudet.Ztot / 2.0 - 70 * u.cm
    )

    # Upstream Tagger
    # UpstreamTagger (UBT) - Simplified scoring plane
    # Note: UBT is implemented as a simple vacuum box
    # Legacy RPC parameters have been removed as they are not used in the current implementation
    c.UpstreamTagger = AttrDict()
    c.UpstreamTagger.BoxX = 4.4 * u.m  # X dimension (width)
    c.UpstreamTagger.BoxY = 6.4 * u.m  # Y dimension (height)
    c.UpstreamTagger.BoxZ = 16.0 * u.cm  # Z dimension (thickness)
    c.UpstreamTagger.Z_Position = (
        -25.400 * u.m + c.decayVolume.z
    )  # Relative position of UBT to decay vessel centre
    c.UpstreamTagger.PositionResolution = 1.0 * u.cm  # Position smearing resolution
    c.UpstreamTagger.TimeResolution = 0.3  # Time resolution in ns

    # Store parameters that might be needed for reference
    c.muShieldGeo = muShieldGeo
    c.nuTargetPassive = nuTargetPassive

    return c
