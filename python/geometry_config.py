# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import os
from typing import TypedDict

import shipunit as u
import yaml
from ship_geo_config_types import (
    BfieldConfig,
    CaveConfig,
    ChambersConfig,
    DecayVolumeConfig,
    HadronAbsorberConfig,
    MuonConfig,
    MuShieldConfig,
    ShipGeoConfig,
    SplitCalConfig,
    StrawtubesDigiConfig,
    TargetConfig,
    TauMudetConfig,
    TimeDetConfig,
    UpstreamTaggerConfig,
    ZPositionConfig,
)

# Parameters for geometry configuration are passed to create_config() function
# nuTargetPassive = 1  #0 = with active layers, 1 = only passive

# targetOpt      = 5  # 0=solid   >0 sliced, 5: 5 pieces of tungsten, 4 air slits, 17: molybdenum tungsten interleaved with H20
# strawOpt       = 0  # 4=aluminium frame 10=steel frame (default)

# Here you can select the MS geometry, if the MS design is using SC magnet change the hybrid to True
# The first row is the length of the magnets
# The other rows are the transverse dimensions of the magnets:  dXIn[i], dXOut[i] , dYIn[i], dYOut[i], gapIn[i], gapOut[i].


class _ShieldEntry(TypedDict):
    hybrid: bool
    WithConstField: bool
    params: list[list[float]]


shield_db: dict[str, _ShieldEntry] = {
    "TRY_2025": {
        "hybrid": False,
        "WithConstField": False,
        "params": [
            [
                0,
                115.5,
                50.00,
                50.00,
                119.00,
                119.00,
                2.00,
                2.00,
                1.00,
                1.00,
                50.00,
                50.00,
                0.00,
                0.00,
                1.90,
            ],
            [
                20,
                495.00,
                67.10,
                79.92,
                27.00,
                43.00,
                5.00,
                5.00,
                1.38,
                1.06,
                67.10,
                79.92,
                0.00,
                0.00,
                1.90,
            ],
            [
                10,
                280.48,
                53.12,
                49.56,
                43.00,
                56.00,
                5.03,
                5.00,
                2.11,
                2.40,
                53.12,
                49.56,
                0.00,
                0.00,
                1.90,
            ],
            [
                10,
                232.53,
                2.73,
                3.68,
                56.00,
                56.00,
                5.00,
                5.21,
                60.44,
                45.63,
                2.73,
                3.68,
                0.50,
                0.50,
                -1.91,
            ],
            [
                10,
                85.00,
                31.00,
                107.12,
                56.00,
                56.00,
                5.27,
                5.00,
                4.55,
                0.63,
                1.00,
                77.12,
                0.00,
                0.00,
                -1.91,
            ],
            [
                10,
                233.82,
                30.03,
                40.00,
                56.00,
                56.00,
                5.00,
                5.01,
                4.83,
                3.37,
                30.03,
                40.00,
                0.00,
                0.00,
                -1.91,
            ],
        ],
    },
}


def create_config(
    DecayVolumeMedium: str = "helium",
    Yheight: float = 6.0,
    strawDesign: int = 10,
    muShieldGeo=None,
    shieldName: str = "New_HA_Design",
    nuTargetPassive: int = 1,
    SND: bool = True,
    SND_design=None,
    TARGET_YAML=None,
) -> ShipGeoConfig:
    """
    Create geometry configuration with specified parameters.

    Args:
        DecayVolumeMedium: Medium in decay volume ("helium" or "vacuums"), default: "helium"
        Yheight: Height of vacuum tank in metres, default: 6.0
        strawDesign: Straw tube design (4=aluminium frame, 10=steel frame), default: 10
        muShieldGeo: Muon shield geometry file (for experts), default: None
        shieldName: Name of shield configuration, default: "New_HA_Design"
        nuTargetPassive: Target type (0=with active layers, 1=only passive), default: 1
        SND: Enable SND detector, default: True
        SND_design: SND design options (list of design numbers), default: [2]
        TARGET_YAML: Path to target YAML configuration file, default: "$FAIRSHIP/geometry/target_config.yaml"

    Returns:
        ShipGeoConfig: Typed geometry configuration object
    """
    # Set defaults for mutable parameters
    if SND_design is None:
        SND_design = [2]
    if TARGET_YAML is None:
        TARGET_YAML = os.path.expandvars("$FAIRSHIP/geometry/target_config.yaml")

    # Ensure SND_design is always a list
    if not isinstance(SND_design, list):
        SND_design = [SND_design]
    print("Info: Target using configuration:", TARGET_YAML)

    if not shieldName:
        raise ValueError("shieldName must not be empty!")

    shield_entry = shield_db[shieldName]
    sc_mag: bool = shield_entry["hybrid"]
    with_const_field: bool = shield_entry["WithConstField"]
    params: list[list[float]] = shield_entry["params"]
    yheight_cm = Yheight * u.m
    extraVesselLength = 10 * u.m
    windowBulge = 25 * u.cm
    magnetDesign = 4

    # --- Cave ---
    floorHeightMuonShield = 5 * u.m
    floorHeightTankA = 4.2 * u.m
    if strawDesign == 10:
        floorHeightMuonShield = floorHeightTankA  # avoid the gap, for 2018 geometry
    cave = CaveConfig(
        floorHeightMuonShield=floorHeightMuonShield,
        floorHeightTankA=floorHeightTankA,
        floorHeightTankB=2 * u.m,
    )

    # --- Target (from YAML) ---
    with open(TARGET_YAML) as file:
        targetconfig = yaml.safe_load(file)

    target_yaml_data = targetconfig["target"]
    slices_length: list[float] = []
    slices_gap: list[float] = []
    slices_material: list[str] = []

    for i in range(target_yaml_data["Nplates"]):
        for _j in range(target_yaml_data["N"][i]):
            if len(target_yaml_data["L"]) == 1:
                slices_length.append(target_yaml_data["L"][0])
            else:
                slices_length.append(target_yaml_data["L"][i])
            if len(target_yaml_data["G"]) == 1:
                slices_gap.append(target_yaml_data["G"][0])
            else:
                slices_gap.append(target_yaml_data["G"][i])
            if len(target_yaml_data["M"]) == 1:
                slices_material.append(target_yaml_data["M"][0])
            else:
                slices_material.append(target_yaml_data["M"][i])
    # Last gap should be 0
    slices_gap[target_yaml_data["nS"] - 1] = 0
    print(slices_material, slices_length, slices_gap)

    target_length: float = sum(w + g for w, g in zip(slices_length, slices_gap))
    target_z0: float = 0  # Origin of SHiP coordinate system
    target_z = target_z0 + target_length / 2.0

    target = TargetConfig(
        Nplates=target_yaml_data["Nplates"],
        M=target_yaml_data["M"],
        L=target_yaml_data["L"],
        G=target_yaml_data["G"],
        N=target_yaml_data["N"],
        nS=target_yaml_data["nS"],
        xy=target_yaml_data["xy"],
        HeT=target_yaml_data["HeT"],
        slices_length=slices_length,
        slices_gap=slices_gap,
        slices_material=slices_material,
        length=target_length,
        z0=target_z0,
        z=target_z,
    )

    # --- Hadron Absorber ---
    hadron_absorber_z = (
        target_z0
        + target_length
        + 96.1 * u.mm  # Distance between target and proximity shielding
        + 250 * u.mm  # Thickness of proximity shielding
        + 207.5 * u.mm  # Distance between hadron absorber and proximity shielding
        - 10 * u.cm  # Remove spacing internal to hadron absorber
    )
    hadronAbsorber = HadronAbsorberConfig(z=hadron_absorber_z, WithConstField=with_const_field)

    # --- Muon Shield ---
    mu_shield_length = sum(line[0] + line[1] * 2 for line in params)
    n_magnets = len(params)

    zgap_list: list[float] = []
    half_length_list: list[float] = []
    entrance_list: list[float] = []

    for line in params:
        zgap_list.append(line[0])
        half_length_list.append(line[1])

    # Compute Z position for each magnet
    for i in range(len(zgap_list)):
        if i == 0:
            entrance_list.append(hadron_absorber_z + zgap_list[i])
        else:
            entrance_list.append(entrance_list[i - 1] + half_length_list[i - 1] * 2 + zgap_list[i])

    # Flatten the params list for C++ interface
    flat_params = [item for sublist in params for item in sublist]

    muShield = MuShieldConfig(
        z=hadron_absorber_z,
        params=flat_params,
        length=mu_shield_length,
        nMagnets=n_magnets,
        Zgap=zgap_list,
        half_length=half_length_list,
        Entrance=entrance_list,
        WithConstField=with_const_field,
    )

    # --- Decay Volume ---
    decayVolume_length = 50 * u.m
    z_spec = 89.57 * u.m  # absolute position of spectrometer magnet
    decayVolume_z = z_spec - 31.450 * u.m  # Relative position of decay vessel centre to spectrometer magnet
    decayVolume_z0 = decayVolume_z - decayVolume_length / 2.0

    decayVolume = DecayVolumeConfig(length=decayVolume_length, z=decayVolume_z, z0=decayVolume_z0)

    # --- Chambers ---
    magnetIncrease = 100.0 * u.cm

    if strawDesign != 4 and strawDesign != 10:
        print("this design ", strawDesign, " is not supported, use strawDesign = 4 or 10")
        1 / 0

    chambers = ChambersConfig(
        Tub1length=2.5 * u.m,
        Tub2length=17.68 * u.m + extraVesselLength / 2.0,
        Tub3length=0.8 * u.m,
        Tub4length=2.0 * u.m + magnetIncrease / 2.0,
        Tub5length=0.8 * u.m,
        Tub6length=0.1 * u.m + windowBulge / 2.0,
        Rmin=245.0 * u.cm,
        Rmax=250.0 * u.cm,
    )

    xMax = 2 * u.m  # max horizontal width at T4
    TrGap = 2 * u.m  # Distance between Tr1/2 and Tr3/4
    TrMagGap = 3.5 * u.m  # Distance from spectrometer magnet centre to the next tracking stations

    z4 = z_spec + TrMagGap + TrGap
    z3 = z_spec + TrMagGap
    z2 = z_spec - TrMagGap
    z1 = z_spec - TrMagGap - TrGap

    # --- B-field ---
    bfield_x = 2.4 * u.m
    bfield_y = yheight_cm
    bfield_kwargs = dict(
        z=z_spec,
        max=0,
        y=bfield_y,
        x=bfield_x,
        fieldMap="files/MainSpectrometerField.root",
    )
    if magnetDesign > 3:  # MISIS design
        bfield_kwargs.update(
            YokeWidth=0.8 * u.m,
            YokeDepth=1.4 * u.m,
            CoilThick=25.0 * u.cm,
            x=2.2 * u.m,
            y=3.5 * u.m,
        )
    Bfield = BfieldConfig(**bfield_kwargs)

    # --- TimeDet ---
    dzBarRow = 1.2 * u.cm
    dzBarCol = 2.4 * u.cm
    zBar = 1 * u.cm
    timeDet_DZ = (dzBarRow + dzBarCol + zBar) / 2
    timeDet_DX = 225 * u.cm
    timeDet_DY = 325 * u.cm
    timeDet_z = 37.800 * u.m - dzBarRow * 3 / 2 + decayVolume_z

    TimeDet = TimeDetConfig(
        dzBarRow=dzBarRow,
        dzBarCol=dzBarCol,
        zBar=zBar,
        DZ=timeDet_DZ,
        DX=timeDet_DX,
        DY=timeDet_DY,
        z=timeDet_z,
    )

    # --- SplitCal ---
    sc_ZStart = 38.450 * u.m + decayVolume_z
    sc_XMax = 4 * u.m / 2
    sc_YMax = 6 * u.m / 2
    sc_BigGap = 100 * u.cm
    sc_ActiveECALThickness = 0.56 * u.cm
    sc_FilterECALThickness = 0.28 * u.cm
    sc_FilterECALThickness_first = 0.28 * u.cm
    sc_nECALSamplings = 50
    sc_NModulesInX = 2
    sc_NModulesInY = 3
    sc_NStripsPerModule = 50

    sc_StripHalfWidth = sc_XMax / (sc_NStripsPerModule * sc_NModulesInX)
    sc_StripHalfLength = sc_YMax / sc_NModulesInY
    sc_SplitCalThickness = (
        (sc_FilterECALThickness_first - sc_FilterECALThickness)
        + (sc_FilterECALThickness + sc_ActiveECALThickness) * sc_nECALSamplings
        + sc_BigGap
    )

    SplitCal = SplitCalConfig(
        ZStart=sc_ZStart,
        XMax=sc_XMax,
        YMax=sc_YMax,
        Empty=0 * u.cm,
        BigGap=sc_BigGap,
        ActiveECALThickness=sc_ActiveECALThickness,
        FilterECALThickness=sc_FilterECALThickness,
        FilterECALThickness_first=sc_FilterECALThickness_first,
        ActiveHCALThickness=90 * u.cm,
        FilterHCALThickness=90 * u.cm,
        nECALSamplings=sc_nECALSamplings,
        nHCALSamplings=0,
        ActiveHCAL=0,
        FilterECALMaterial=3,  # 1=scintillator 2=Iron 3=lead 4=Argon
        FilterHCALMaterial=2,
        ActiveECALMaterial=1,
        ActiveHCALMaterial=1,
        ActiveECAL_gas_Thickness=1.12 * u.cm,
        num_precision_layers=1,
        first_precision_layer=6,
        second_precision_layer=10,
        third_precision_layer=13,
        ActiveECAL_gas_gap=10 * u.cm,
        NModulesInX=sc_NModulesInX,
        NModulesInY=sc_NModulesInY,
        NStripsPerModule=sc_NStripsPerModule,
        StripHalfWidth=sc_StripHalfWidth,
        StripHalfLength=sc_StripHalfLength,
        SplitCalThickness=sc_SplitCalThickness,
    )

    # --- Muon Stations & Filters ---
    muonStation0_z = sc_ZStart + 10 * u.cm + sc_SplitCalThickness

    # --- Muon detector ---
    Muon = MuonConfig(
        XMax=250.0 * u.cm,
        YMax=325.0 * u.cm,
        ActiveThickness=0.5 * u.cm,
        FilterThickness=30.0 * u.cm,
    )

    # --- Straw tubes digitisation ---
    strawtubesDigi = StrawtubesDigiConfig(
        v_drift=1.0 / (30 * u.ns / u.mm),  # for baseline NA62 5mm radius straws
        sigma_spatial=0.012 * u.cm,  # according to Massi's TP section
    )

    # --- Tau/muon detector ---
    tauMudet_Ztot = 3 * u.m  # space allocated to Muon spectrometer
    tauMudet = TauMudetConfig(
        Ztot=tauMudet_Ztot,
        zMudetC=hadron_absorber_z + mu_shield_length / 2.0 - tauMudet_Ztot / 2.0 - 70 * u.cm,
    )

    # --- Upstream Tagger ---
    UpstreamTagger = UpstreamTaggerConfig(
        BoxX=4.4 * u.m,
        BoxY=6.4 * u.m,
        BoxZ=16.0 * u.cm,
        Z_Position=-25.400 * u.m + decayVolume_z,
        PositionResolution=1.0 * u.cm,
        TimeResolution=0.3,
    )

    # --- Assemble top-level config ---
    return ShipGeoConfig(
        DecayVolumeMedium=DecayVolumeMedium,
        SND=SND,
        SND_design=SND_design,
        target_yaml=TARGET_YAML,
        shieldName=shieldName,
        SC_mag=sc_mag,
        Yheight=yheight_cm,
        strawDesign=strawDesign,
        magnetDesign=magnetDesign,
        z=z_spec,
        xMax=xMax,
        HcalOption=-1,
        EcalOption=2,
        muShieldGeo=muShieldGeo,
        nuTargetPassive=nuTargetPassive,
        cave=cave,
        target=target,
        hadronAbsorber=hadronAbsorber,
        muShield=muShield,
        decayVolume=decayVolume,
        chambers=chambers,
        Bfield=Bfield,
        TimeDet=TimeDet,
        SplitCal=SplitCal,
        Muon=Muon,
        UpstreamTagger=UpstreamTagger,
        tauMudet=tauMudet,
        strawtubesDigi=strawtubesDigi,
        TrackStation1=ZPositionConfig(z=z1),
        TrackStation2=ZPositionConfig(z=z2),
        TrackStation3=ZPositionConfig(z=z3),
        TrackStation4=ZPositionConfig(z=z4),
        Chamber1=ZPositionConfig(z=z4 - 4666.0 * u.cm - magnetIncrease - extraVesselLength),
        Chamber6=ZPositionConfig(z=z4 + 30.0 * u.cm + windowBulge / 2.0),
        MuonStation0=ZPositionConfig(z=muonStation0_z),
        MuonStation1=ZPositionConfig(z=muonStation0_z + 1 * u.m),
        MuonStation2=ZPositionConfig(z=muonStation0_z + 2 * u.m),
        MuonStation3=ZPositionConfig(z=muonStation0_z + 3 * u.m),
        MuonFilter0=ZPositionConfig(z=muonStation0_z + 50.0 * u.cm),
        MuonFilter1=ZPositionConfig(z=muonStation0_z + 150.0 * u.cm),
        MuonFilter2=ZPositionConfig(z=muonStation0_z + 250.0 * u.cm),
    )
