#!/usr/bin/env python
import ROOT
import os
import shipunit as u
from ShipGeoConfig import AttrDict, ConfigRegistry
from ShieldUtils import find_shield_center
from array import array
import yaml

detectorList = []


def posHcal(z, hfile, HcalOption):
    HcalZSize = 0
    sz = hfile + "z" + str(z) + ".geo"
    floc = os.environ["FAIRSHIP"] + "/geometry"
    f_hcal = floc + "/" + hfile
    f_hcalz = floc + "/" + sz
    f = open(f_hcal)
    rewrite = True
    if sz in os.listdir(floc):
        test = os.popen("diff " + f_hcal + " " + f_hcalz).read()
        if str.count(test, "---") == 1 and not test.find("Position") < 0:
            rewrite = False  # only different is z position
    if rewrite:
        fn = open(f_hcalz, "w")
    for l in f.readlines():
        if rewrite:
            if not l.find("ZPos") < 0:
                l = "ZPos=" + str(z) + "	#Position of Hcal  center	[cm]\n"
            fn.write(l)
        if not l.find("HcalZSize") < 0:
            HcalZSize = float(l[len("HcalZSize") + 1 :].split("#")[0])
    f.close()
    if rewrite:
        fn.close()
    if HcalOption == 2:
        hcal = ROOT.hcal("Hcal", ROOT.kFALSE, sz)
    else:
        hcal = ROOT.hcal("Hcal", ROOT.kTRUE, sz)
    return hcal, HcalZSize


def makeEcalGeoFile(z, efile):
    EcalZSize = 0
    sz = efile + "z" + str(z) + ".geo"
    floc = os.environ["FAIRSHIP"] + "/geometry"
    f_ecal = floc + "/" + efile
    f_ecalz = floc + "/" + sz
    f = open(f_ecal)
    rewrite = True
    if sz in os.listdir(floc):
        test = os.popen("diff " + f_ecal + " " + f_ecalz).read()
        if str.count(test, "---") == 1 and not test.find("Position") < 0:
            rewrite = False  # only different is z position
    if rewrite:
        fn = open(f_ecalz, "w")
    for l in f.readlines():
        if rewrite:
            if not l.find("ZPos") < 0:
                l = "ZPos=" + str(z) + "	#Position of Ecal start		[cm]\n"
            fn.write(l)
        if not l.find("EcalZSize") < 0:
            EcalZSize = float(l[len("EcalZSize") + 1 :].split("#")[0])
    f.close()
    if rewrite:
        fn.close()
    return EcalZSize, sz


def posEcal(z, efile):
    EcalZSize, sz = makeEcalGeoFile(z, efile)
    ecal = ROOT.ecal("Ecal", ROOT.kTRUE, sz)
    return ecal, EcalZSize

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
        ship_geo.mtc_geo.scintThick,
        ship_geo.mtc_geo.nLayers,
        ship_geo.mtc_geo.zPosition,
        ship_geo.mtc_geo.fieldY
    )
    detectorList.append(mtc)

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
    Strawtubes = ROOT.strawtubes(ship_geo.strawtubes_geo.medium)
    Strawtubes.SetzPositions(
        ship_geo.strawtubes_geo.z1Position,
        ship_geo.strawtubes_geo.z2Position,
        ship_geo.strawtubes_geo.z3Position,
        ship_geo.strawtubes_geo.z4Position,
    )
    Strawtubes.SetApertureArea(
        ship_geo.strawtubes_geo.width,
        ship_geo.strawtubes_geo.height,
    )
    Strawtubes.SetStrawDiameter(
        ship_geo.strawtubes_geo.outer_straw_diameter,
        ship_geo.strawtubes_geo.wall_thickness,
    )
    Strawtubes.SetStrawPitch(
        ship_geo.strawtubes_geo.straw_pitch,
        ship_geo.strawtubes_geo.y_layer_offset,
    )
    Strawtubes.SetDeltazLayer(ship_geo.strawtubes_geo.delta_z_layer)
    Strawtubes.SetStereoAngle(ship_geo.strawtubes_geo.view_angle)
    Strawtubes.SetWireThickness(ship_geo.strawtubes_geo.wire_thickness)
    Strawtubes.SetDeltazView(ship_geo.strawtubes_geo.delta_z_view)
    Strawtubes.SetFrameMaterial(ship_geo.strawtubes_geo.frame_material)
    Strawtubes.SetStationEnvelope(
        ship_geo.strawtubes_geo.station_width,
        ship_geo.strawtubes_geo.station_height,
        ship_geo.strawtubes_geo.station_length,
    )

    #For digitization
    Strawtubes.SetStrawResolution(
        ship_geo.strawtubes.v_drift,
        ship_geo.strawtubes.sigma_spatial,
    )

    detectorList.append(Strawtubes)


def configure(run, ship_geo):
    # ---- for backward compatibility ----
    if not hasattr(ship_geo, "DecayVolumeMedium"):
        raise ValueError(
            "DecayVolumeMedium is not defined, possibly old (incompatible) geometry!"
        )
    if not hasattr(ship_geo, "muShieldGeo"):
        ship_geo.muShieldGeo = None
    if not hasattr(ship_geo.hcal, "File"):
        ship_geo.hcal.File = "hcal.geo"
    if not hasattr(ship_geo.Bfield, "x"):
        ship_geo.Bfield.x = 3.0 * u.m
    if not hasattr(ship_geo, "cave"):
        ship_geo.cave = AttrDict(z=0 * u.cm)
        ship_geo.cave.floorHeightMuonShield = 5 * u.m
        ship_geo.cave.floorHeightTankA = 4.5 * u.m
        ship_geo.cave.floorHeightTankB = 2.0 * u.m
    if not hasattr(ship_geo, "EcalOption"):
        ship_geo.EcalOption = 1
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
                # SND design 2 -- MTC
                configure_snd_mtc(
                    os.path.join(os.environ["FAIRSHIP"], "geometry", "MTC_config.yaml"),
                    ship_geo
                )
            elif design == 1:
                configure_snd_old(
                    os.path.join(os.environ["FAIRSHIP"], "geometry", "snd_config_old.yaml"),
                    ship_geo.UpstreamTagger.Z_Position - 8 *u.cm - 5 *u.cm, #8 cm width of UpstreamTagger
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

    if ship_geo.EcalOption == 1:  # shashlik design TP
        ecal, EcalZSize = posEcal(ship_geo.ecal.z, ship_geo.ecal.File)
        detectorList.append(ecal)

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

    if not ship_geo.HcalOption < 0:
        hcal, HcalZSize = posHcal(
            ship_geo.hcal.z, ship_geo.hcal.File, ship_geo.HcalOption
        )
        if (
            ship_geo.HcalOption != 2
            and abs(ship_geo.hcal.hcalSpace - HcalZSize) > 10 * u.cm
        ):
            print("mismatch between hcalsize in geo file and python configuration")
            print(
                ship_geo.hcal.hcalSpace - HcalZSize, ship_geo.hcal.hcalSpace, HcalZSize
            )
        detectorList.append(hcal)
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
    # exclusionList = ["Muon","Ecal","Hcal","Strawtubes","TargetTrackers","NuTauTarget",\
    #                 "Veto","Magnet","MuonShield","TargetStation", "TimeDet", "UpstreamTagger"]

    for x in detectorList:
        if x.GetName() in exclusionList:
            continue
        run.AddModule(x)
    # return list of detector elements
    detElements = {}
    for x in run.GetListOfModules():
        detElements[x.GetName()] = x
    return detElements
