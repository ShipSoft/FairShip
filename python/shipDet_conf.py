#!/usr/bin/env python
import ROOT
import os
import shipunit as u
from ShipGeoConfig import AttrDict
from ShieldUtils import find_shield_center
from array import array
import yaml

detectorList = []


def configure_snd_old(yaml_file,
                      emulsion_target_z_end,
                      cave_floorHeightMuonShield):

    with open(yaml_file) as file:
        config = yaml.safe_load(file)
    nuTarget_geo = AttrDict(config['nuTarget'])
    nuTauTT_geo = AttrDict(config['nuTauTT'])

    #specific parameters
    # nu Target Tracker
    snd_nuTauTT_TTX = nuTauTT_geo.n_hor_planes * nuTauTT_geo.scifimat_width + 2.9 * u.cm  # endpieces (~2.9cm from previous geom)
    snd_nuTauTT_TTY = nuTauTT_geo.n_vert_planes * nuTauTT_geo.scifimat_width + 2.9 # u.cm  # endpieces (~2.9cm from previous geom)

    snd_nuTauTT_TTZ = 2 * nuTauTT_geo.support_z + 2 * nuTauTT_geo.scifimat_z + nuTauTT_geo.honeycomb_z

    # nuTau target
    snd_nuTarget_BrZ = nuTarget_geo.n_plates * nuTarget_geo.LeadTh + (nuTarget_geo.n_plates+1) * (2* nuTarget_geo.EmTh + nuTarget_geo.PBTh) + nuTarget_geo.BrPackZ
    snd_nuTarget_BrX = nuTarget_geo.BrPackX + nuTarget_geo.EmX
    snd_nuTarget_BrY = nuTarget_geo.BrPackY + nuTarget_geo.EmY

    snd_nuTarget_zdim = nuTarget_geo.wall* snd_nuTarget_BrZ + (nuTarget_geo.wall+1)*snd_nuTauTT_TTZ
    snd_nuTarget_xdim = snd_nuTauTT_TTX
    snd_nuTarget_ydim = snd_nuTauTT_TTY

    snd_nuTarget_zC = emulsion_target_z_end - snd_nuTarget_zdim / 2.

    snd_nuTarget_PillarY = 10*u.m - snd_nuTarget_ydim/2 -nuTarget_geo.BaseY- 0.1*u.mm - cave_floorHeightMuonShield
    NuTauTarget = ROOT.Target(
        "NuTauTarget", nuTarget_geo.Ydist, ROOT.kTRUE
    )
    NuTauTarget.MakeNuTargetPassive(nuTarget_geo.nuTargetPassive)
    NuTauTarget.MergeTopBot(nuTarget_geo.SingleEmFilm)
    NuTauTarget.SetDetectorDesign(nuTarget_geo.Design)
    NuTauTarget.SetCenterZ(snd_nuTarget_zC)
    NuTauTarget.SetNumberBricks(
        nuTarget_geo.col,
        nuTarget_geo.row,
        nuTarget_geo.wall,
    )
    NuTauTarget.SetDetectorDimension(
        snd_nuTarget_xdim,
        snd_nuTarget_ydim,
        snd_nuTarget_zdim,
    )
    NuTauTarget.SetTargetWallDimension(
        nuTarget_geo.col*snd_nuTarget_BrX,
        nuTarget_geo.row*snd_nuTarget_BrY+(nuTarget_geo.row-1)*nuTarget_geo.Ydist,
        snd_nuTarget_BrZ
    )
    NuTauTarget.SetEmulsionParam(
        nuTarget_geo.EmTh,
        nuTarget_geo.EmX,
        nuTarget_geo.EmY,
        nuTarget_geo.PBTh,
        2* nuTarget_geo.EmTh + nuTarget_geo.PBTh,
        nuTarget_geo.LeadTh,
        nuTarget_geo.LeadTh +2* nuTarget_geo.EmTh + nuTarget_geo.PBTh,
    )
    NuTauTarget.SetBrickParam(
        snd_nuTarget_BrX,
        snd_nuTarget_BrY,
        snd_nuTarget_BrZ,
        nuTarget_geo.BrPackX,
        nuTarget_geo.BrPackY,
        nuTarget_geo.BrPackZ,
        nuTarget_geo.n_plates,
    )
    NuTauTarget.SetCellParam(snd_nuTarget_BrZ)
    NuTauTarget.SetPillarDimension(
        nuTarget_geo.PillarX,
        snd_nuTarget_PillarY,
        nuTarget_geo.PillarZ
    )
    NuTauTarget.SetBaseDimension(
        snd_nuTarget_xdim+20,
        nuTarget_geo.BaseY,
        snd_nuTarget_zdim+10
    )
    # Target Tracker
    NuTauTT = ROOT.TargetTracker(
        "TargetTrackers",
        snd_nuTauTT_TTX,
        snd_nuTauTT_TTY,
        snd_nuTauTT_TTZ,
        ROOT.kTRUE,
    )
    NuTauTT.SetDesign(nuTauTT_geo.design)
    NuTauTT.SetSciFiParam(
        nuTauTT_geo.scifimat_width,
        snd_nuTauTT_TTX,
        snd_nuTauTT_TTY,
        nuTauTT_geo.scifimat_z,
        nuTauTT_geo.support_z,
        nuTauTT_geo.honeycomb_z,
    )
    NuTauTT.SetNumberSciFi(
        nuTauTT_geo.n_hor_planes, nuTauTT_geo.n_vert_planes
    )
    NuTauTT.SetTargetTrackerParam(
        snd_nuTauTT_TTX, snd_nuTauTT_TTY, snd_nuTauTT_TTZ
    )
    NuTauTT.SetBrickParam(snd_nuTarget_BrZ)
    NuTauTT.SetTotZDimension(snd_nuTarget_zdim)
    NuTauTT.SetNumberTT(nuTarget_geo.wall+1)
    # method of nutau target that must be called after TT parameter definition
    NuTauTarget.SetTTzdimension(snd_nuTauTT_TTZ)

    detectorList.append(NuTauTarget)
    detectorList.append(NuTauTT)


def configure_snd_mtc(yaml_file, ship_geo):
    with open(yaml_file) as file:
        config = yaml.safe_load(file)

    ship_geo.mtc_geo = AttrDict(config['MTC'])
    # Initialize detector
    if ship_geo.mtc_geo.zPosition == "auto":
        # Get the the center of the *last* magnet
        ship_geo.mtc_geo.zPosition = find_shield_center(ship_geo)[2][-1]
        print("MTC zPosition set to ", ship_geo.mtc_geo.zPosition)
    mtc = ROOT.MTCDetector("MTC", ROOT.kTRUE)
    mtc.SetMTCParameters(
        ship_geo.mtc_geo.width,
        ship_geo.mtc_geo.height,
        ship_geo.mtc_geo.angle,
        ship_geo.mtc_geo.ironThick,
        ship_geo.mtc_geo.sciFiThick,
        ship_geo.mtc_geo.num_of_agg_channels,
        ship_geo.mtc_geo.scintThick,
        ship_geo.mtc_geo.nLayers,
        ship_geo.mtc_geo.zPosition,
        ship_geo.mtc_geo.fieldY
    )
    detectorList.append(mtc)

def configure_snd_siliconTarget(yaml_file, ship_geo):
    with open(yaml_file) as file:
        config = yaml.safe_load(file)

    ship_geo.SiliconTarget_geo = AttrDict(config['SiliconTarget'])
    # Initialize detector
    if ship_geo.SiliconTarget_geo.zPosition == "auto":
        # Get the the center of the next to last magnet (temporary placement)
        # Offset placement of detector by 140 cm, magnet is 2* 212.54 cm,
        # 120 layers at 132 cm will fit, with 140 cm offset final layer within 10 cm of MTC.
        ship_geo.SiliconTarget_geo.zPosition = find_shield_center(ship_geo)[2][-2] + 140
        print("SiliconTarget zPosition set to ", ship_geo.SiliconTarget_geo.zPosition)
    SiliconTarget = ROOT.SiliconTarget("SiliconTarget", ROOT.kTRUE)
    SiliconTarget.SetSiliconTargetParameters(
        ship_geo.SiliconTarget_geo.targetWidth,
        ship_geo.SiliconTarget_geo.targetHeight,
        ship_geo.SiliconTarget_geo.sensorWidth,
        ship_geo.SiliconTarget_geo.sensorLength,
        ship_geo.SiliconTarget_geo.nLayers,
        ship_geo.SiliconTarget_geo.zPosition,
        ship_geo.SiliconTarget_geo.targetThickness,
        ship_geo.SiliconTarget_geo.targetSpacing,
        ship_geo.SiliconTarget_geo.moduleOffset
    )
    detectorList.append(SiliconTarget)

def configure_veto(yaml_file, z0):
    with open(yaml_file) as file:
        config = yaml.safe_load(file)

    veto_geo = AttrDict(config)

    Veto = ROOT.veto()
    Veto.SetVesselDimensions(
        veto_geo.xstartInner,
        veto_geo.xendInner,
        veto_geo.ystartInner,
        veto_geo.yendInner,
        z0,
    )

    Veto.SetLiquidVeto(1)

    Veto.SetVesselStructure(
        veto_geo.innerSupport,
        veto_geo.sensitiveThickness,
        veto_geo.outerSupport,
        veto_geo.innerSupportMed,
        veto_geo.lidThickness,
        veto_geo.sensitiveMed,
        veto_geo.outerSupportMed,
        veto_geo.decayMed,
        veto_geo.rib,
    )

    detectorList.append(Veto)

def configure_strawtubes(yaml_file, ship_geo):
    with open(yaml_file) as file:
        config = yaml.safe_load(file)

    ship_geo.strawtubes_geo = AttrDict(config['SST'])

    # Straw tubes in decay vessel if vacuum, otherwise outside in air
    ship_geo.strawtubes_geo.medium = "vacuums" if ship_geo.DecayVolumeMedium == "vacuums" else "air"

    # Choose frame material
    if ship_geo.strawDesign == 4:
        ship_geo.strawtubes_geo.frame_material = "aluminium"
    elif ship_geo.strawDesign == 10:
        ship_geo.strawtubes_geo.frame_material = "steel"

    strawtubes = ROOT.strawtubes(ship_geo.strawtubes_geo.medium)
    strawtubes.SetzPositions(
        ship_geo.TrackStation1.z,
        ship_geo.TrackStation2.z,
        ship_geo.TrackStation3.z,
        ship_geo.TrackStation4.z,
    )
    strawtubes.SetApertureArea(
        ship_geo.strawtubes_geo.width,
        ship_geo.strawtubes_geo.height,
    )
    strawtubes.SetStrawDiameter(
        ship_geo.strawtubes_geo.outer_straw_diameter,
        ship_geo.strawtubes_geo.wall_thickness,
    )
    strawtubes.SetStrawPitch(
        ship_geo.strawtubes_geo.straw_pitch,
        ship_geo.strawtubes_geo.y_layer_offset,
    )
    strawtubes.SetDeltazLayer(ship_geo.strawtubes_geo.delta_z_layer)
    strawtubes.SetStereoAngle(ship_geo.strawtubes_geo.view_angle)
    strawtubes.SetWireThickness(ship_geo.strawtubes_geo.wire_thickness)
    strawtubes.SetDeltazView(ship_geo.strawtubes_geo.delta_z_view)
    strawtubes.SetFrameMaterial(ship_geo.strawtubes_geo.frame_material)
    strawtubes.SetStationEnvelope(
        ship_geo.strawtubes_geo.station_width,
        ship_geo.strawtubes_geo.station_height,
        ship_geo.strawtubes_geo.station_length,
    )

    #For digitization
    strawtubes.SetStrawResolution(
        ship_geo.strawtubesDigi.v_drift,
        ship_geo.strawtubesDigi.sigma_spatial,
    )

    detectorList.append(strawtubes)


def configure(run, ship_geo):
    # ---- for backward compatibility ----
    if not hasattr(ship_geo, "DecayVolumeMedium"):
        raise ValueError(
            "DecayVolumeMedium is not defined, possibly old (incompatible) geometry!"
        )
    if not hasattr(ship_geo, "muShieldGeo"):
        ship_geo.muShieldGeo = None
    if not hasattr(ship_geo.Bfield, "x"):
        ship_geo.Bfield.x = 3.0 * u.m
    if not hasattr(ship_geo, "cave"):
        ship_geo.cave = AttrDict(z=0 * u.cm)
        ship_geo.cave.floorHeightMuonShield = 5 * u.m
        ship_geo.cave.floorHeightTankA = 4.5 * u.m
        ship_geo.cave.floorHeightTankB = 2.0 * u.m
    if not hasattr(ship_geo, "SND"):
        ship_geo.SND = True

    # -----Create media-------------------------------------------------
    run.SetMaterials("media.geo")  # Materials
    # ------------------------------------------------------------------------

    # -----Create geometry----------------------------------------------
    cave = ROOT.ShipCave(ship_geo.muShield.z)
    cave.SetGeometryFileName("caveWithAir.geo")
    detectorList.append(cave)

    TargetStation = ROOT.ShipTargetStation(
        "TargetStation",
        ship_geo.target.length,
        ship_geo.target.z,
        ship_geo.targetVersion,
        ship_geo.target.nS,
        ship_geo.target.HeT
    )

    TargetStation.SetLayerPosMat(ship_geo.target.xy, ship_geo.target.slices_length, ship_geo.target.slices_gap, ship_geo.target.slices_material)
    detectorList.append(TargetStation)


    # For SND: support multiple designs
    if ship_geo.SND:
        for design in ship_geo.SND_design:
            if design == 2:
                # SND design 2 -- MTC/SiliconTarget
                configure_snd_mtc(
                    os.path.join(os.environ["FAIRSHIP"], "geometry", "MTC_config.yaml"),
                    ship_geo
                )
                configure_snd_siliconTarget(
                    os.path.join(os.environ["FAIRSHIP"], "geometry", "SiliconTarget_config.yaml"),
                    ship_geo
                )
            elif design == 1:
                configure_snd_old(
                    os.path.join(os.environ["FAIRSHIP"], "geometry", "snd_config_old.yaml"),
                    ship_geo.UpstreamTagger.Z_Position - 8 *u.cm - 5 *u.cm, #16 cm width of UpstreamTagger (8 cm half-width)
                    ship_geo.cave.floorHeightMuonShield,
                )
            else:
                print(f"Warning: SND design {design} is not recognized.")


    in_params = list(ship_geo.muShield.params)

    MuonShield = ROOT.ShipMuonShield(
        in_params,
        ship_geo.muShield.z,
        ship_geo.muShield.WithConstField,
        ship_geo.SC_mag,
    )

    if ship_geo.SND:
        # If any SND design is 2 (MTC), set SNDSpace for MuonShield
        if 2 in getattr(ship_geo, 'SND_design', []):
            MuonShield.SetSNDSpace(
                hole = True,
                hole_dx = (ship_geo.mtc_geo.width + 5. * u.cm) / 2.,
                hole_dy = (ship_geo.mtc_geo.height + 5. * u.cm) / 2.
            )
    detectorList.append(MuonShield)

    if not hasattr(ship_geo, "magnetDesign"):
        # backward compatibility
        ship_geo.magnetDesign = 4
        ship_geo.Bfield.YokeWidth = 200.0 * u.cm
        ship_geo.Bfield.YokeDepth = 200.0 * u.cm
        ship_geo.Bfield.CoilThick = 25.0 * u.cm
    if ship_geo.strawDesign > 1:
        if ship_geo.magnetDesign > 3:
            B = ship_geo.Bfield
            magnet = ROOT.ShipMagnet(
                "Magnet",
                "SHiP Magnet",
                B.z,
                ship_geo.magnetDesign,
                B.x,
                B.y,
                ship_geo.cave.floorHeightTankB,
                B.YokeWidth,
                B.YokeDepth,
                B.CoilThick,
            )
        #                                                               xaperture,  yaperture
        else:
            magnet = ROOT.ShipMagnet(
                "Magnet",
                "SHiP Magnet",
                ship_geo.Bfield.z,
                ship_geo.magnetDesign,
                ship_geo.Bfield.x,
                ship_geo.Bfield.y,
                ship_geo.cave.floorHeightTankB,
            )
    else:
        magnet = ROOT.ShipMagnet("Magnet", "SHiP Magnet", ship_geo.Bfield.z)
    detectorList.append(magnet)

    fairship = os.environ["FAIRSHIP"]

    configure_veto(
        os.path.join(
            fairship, f"geometry/veto_config_{ship_geo.DecayVolumeMedium}.yaml"
        ),
        ship_geo.decayVolume.z0,
    )

    configure_strawtubes(
        os.path.join(os.environ["FAIRSHIP"], "geometry", "strawtubes_config.yaml"),
        ship_geo,
    )

    if ship_geo.EcalOption == 2:  # splitCal with pointing information
        SplitCal = ROOT.splitcal("SplitCal", ROOT.kTRUE)
        x = ship_geo.SplitCal
        SplitCal.SetThickness(
            x.ActiveECALThickness,
            x.ActiveHCALThickness,
            x.FilterECALThickness,
            x.FilterECALThickness_first,
            x.FilterHCALThickness,
            x.ActiveECAL_gas_Thickness,
        )
        SplitCal.SetMaterial(
            x.ActiveECALMaterial,
            x.ActiveHCALMaterial,
            x.FilterECALMaterial,
            x.FilterHCALMaterial,
        )
        SplitCal.SetNSamplings(x.nECALSamplings, x.nHCALSamplings, x.ActiveHCAL)
        SplitCal.SetZStart(x.ZStart)
        SplitCal.SetXMax(x.XMax)
        SplitCal.SetYMax(x.YMax)
        SplitCal.SetEmpty(
            x.Empty,
            x.BigGap,
            x.ActiveECAL_gas_gap,
            x.first_precision_layer,
            x.second_precision_layer,
            x.third_precision_layer,
            x.num_precision_layers,
        )
        SplitCal.SetNModules(x.NModulesInX, x.NModulesInY)
        SplitCal.SetNStrips(x.NStripsPerModule)
        SplitCal.SetStripSize(x.StripHalfWidth, x.StripHalfLength)
        detectorList.append(SplitCal)

    Muon = ROOT.muon("Muon", ROOT.kTRUE)
    Muon.SetZStationPositions(
        ship_geo.MuonStation0.z,
        ship_geo.MuonStation1.z,
        ship_geo.MuonStation2.z,
        ship_geo.MuonStation3.z,
    )
    Muon.SetZFilterPositions(
        ship_geo.MuonFilter0.z, ship_geo.MuonFilter1.z, ship_geo.MuonFilter2.z
    )
    Muon.SetXMax(ship_geo.Muon.XMax)
    Muon.SetYMax(ship_geo.Muon.YMax)
    Muon.SetActiveThickness(ship_geo.Muon.ActiveThickness)
    Muon.SetFilterThickness(ship_geo.Muon.FilterThickness)
    detectorList.append(Muon)

    upstreamTagger = ROOT.UpstreamTagger("UpstreamTagger", ROOT.kTRUE)
    upstreamTagger.SetZposition(ship_geo.UpstreamTagger.Z_Position)
    upstreamTagger.SetBoxDimensions(
        ship_geo.UpstreamTagger.BoxX,
        ship_geo.UpstreamTagger.BoxY,
        ship_geo.UpstreamTagger.BoxZ
    )
    detectorList.append(upstreamTagger)

    timeDet = ROOT.TimeDet("TimeDet", ROOT.kTRUE)
    timeDet.SetZposition(ship_geo.TimeDet.z)
    timeDet.SetBarZspacing(ship_geo.TimeDet.dzBarRow, ship_geo.TimeDet.dzBarCol)
    timeDet.SetBarZ(ship_geo.TimeDet.zBar)
    timeDet.SetSizeX(2 * ship_geo.TimeDet.DX)
    timeDet.SetSizeY(2 * ship_geo.TimeDet.DY)
    detectorList.append(timeDet)

    # -----   Magnetic field   -------------------------------------------
    if not hasattr(ship_geo.Bfield, "fieldMap"):
        if ship_geo.strawDesign == 4 or ship_geo.strawDesign == 10:
            fMagField = ROOT.ShipBellField(
                "wilfried",
                ship_geo.Bfield.max,
                ship_geo.Bfield.z,
                2,
                ship_geo.Yheight / 2.0 * u.m,
            )
        else:
            fMagField = ROOT.ShipBellField(
                "wilfried",
                ship_geo.Bfield.max,
                ship_geo.Bfield.z,
                1,
                ship_geo.Yheight / 2.0 * u.m,
            )
        run.SetField(fMagField)

    exclusionList = []
    # exclusionList = ["Muon","Ecal","Hcal","strawtubes","TargetTrackers","NuTauTarget",\
    #                 "SiliconTarget","Veto","Magnet","MuonShield","TargetStation", "TimeDet", "UpstreamTagger"]

    for x in detectorList:
        if x.GetName() in exclusionList:
            continue
        run.AddModule(x)
    # return list of detector elements
    detElements = {}
    for x in run.GetListOfModules():
        detElements[x.GetName()] = x
    return detElements
