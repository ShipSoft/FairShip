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

    # Choose frame material
    if ship_geo.strawDesign == 4:
        ship_geo.strawtubes_geo.frame_material = "aluminium"
    elif ship_geo.strawDesign == 10:
        ship_geo.strawtubes_geo.frame_material = "steel"

    Strawtubes = ROOT.strawtubes(ship_geo.strawtubes_geo.medium)
    Strawtubes.SetzPositions(
        ship_geo.TrackStation1.z,
        ship_geo.TrackStation2.z,
        ship_geo.TrackStation3.z,
        ship_geo.TrackStation4.z,
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
        ship_geo.strawtubesDigi.v_drift,
        ship_geo.strawtubesDigi.sigma_spatial,
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

<<<<<<< HEAD
    configure_strawtubes(
        os.path.join(os.environ["FAIRSHIP"], "geometry", "strawtubes_config.yaml"),
        ship_geo,
    )
=======
    if hasattr(ship_geo, "tauMudet") and ship_geo.SND:  # don't support old designs
        if ship_geo.muShieldDesign >= 7 and hasattr(ship_geo.tauMudet, "Xtot"):
            taumuondetector = ROOT.NuTauMudet(
                "NuTauMudet", ship_geo.tauMudet.zMudetC, ROOT.kTRUE
            )
            taumuondetector.SetDesign(ship_geo.nuTauTargetDesign)
            taumuondetector.SetTotDimensions(
                ship_geo.tauMudet.Xtot, ship_geo.tauMudet.Ytot, ship_geo.tauMudet.Ztot
            )
            if ship_geo.nuTauTargetDesign < 4:  # muon filter design
                if hasattr(ship_geo.tauMudet, "ZFethin"):
                    taumuondetector.SetFeDimensions(
                        ship_geo.tauMudet.XFe,
                        ship_geo.tauMudet.YFe,
                        ship_geo.tauMudet.ZFethick,
                        ship_geo.tauMudet.ZFethin,
                    )
                    taumuondetector.SetNFeInArm(
                        ship_geo.tauMudet.NFethick, ship_geo.tauMudet.NFethin
                    )
                    taumuondetector.SetLateralCutSize(
                        ship_geo.tauMudet.CutHeight, ship_geo.tauMudet.CutLength
                    )
                    taumuondetector.SetSupportTransverseDimensions(
                        ship_geo.tauMudet.UpperSupportX,
                        ship_geo.tauMudet.UpperSupportY,
                        ship_geo.tauMudet.LowerSupportX,
                        ship_geo.tauMudet.LowerSupportY,
                        ship_geo.tauMudet.LateralSupportX,
                        ship_geo.tauMudet.LateralSupportY,
                        ship_geo.tauMudet.YSpacing,
                    )
                else:  # geometry used before new iron sampling
                    taumuondetector.SetFeDimensions(
                        ship_geo.tauMudet.XFe,
                        ship_geo.tauMudet.YFe,
                        ship_geo.tauMudet.ZFe,
                    )
                    taumuondetector.SetNFeInArm(ship_geo.tauMudet.NFe)
                taumuondetector.SetRpcDimensions(
                    ship_geo.tauMudet.XRpc,
                    ship_geo.tauMudet.YRpc,
                    ship_geo.tauMudet.ZRpc,
                )
                taumuondetector.SetRpcGasDimensions(
                    ship_geo.tauMudet.XGas,
                    ship_geo.tauMudet.YGas,
                    ship_geo.tauMudet.ZGas,
                )
                taumuondetector.SetRpcStripDimensions(
                    ship_geo.tauMudet.XStrip,
                    ship_geo.tauMudet.YStrip,
                    ship_geo.tauMudet.ZStrip,
                )
                taumuondetector.SetRpcElectrodeDimensions(
                    ship_geo.tauMudet.XEle,
                    ship_geo.tauMudet.YEle,
                    ship_geo.tauMudet.ZEle,
                )
                taumuondetector.SetRpcPETDimensions(
                    ship_geo.tauMudet.XPet,
                    ship_geo.tauMudet.YPet,
                    ship_geo.tauMudet.ZPet,
                )
                taumuondetector.SetNRpcInArm(ship_geo.tauMudet.NRpc)
                if ship_geo.nuTauTargetDesign == 3:
                    taumuondetector.SetUpperCoverDimensions(
                        ship_geo.tauMudet.XCov,
                        ship_geo.tauMudet.YCov,
                        ship_geo.tauMudet.ZCov,
                    )
                    taumuondetector.SetLateralCoverDimensions(
                        ship_geo.tauMudet.XLateral,
                        ship_geo.tauMudet.YLateral,
                        ship_geo.tauMudet.ZLateral,
                    )
                    taumuondetector.SetCrossDimensions(
                        ship_geo.tauMudet.XCross,
                        ship_geo.tauMudet.YCross,
                        ship_geo.tauMudet.ZCross,
                        ship_geo.tauMudet.WidthArm,
                    )
                    taumuondetector.SetRpcOuterDimensions(
                        ship_geo.tauMudet.XRpc_outer,
                        ship_geo.tauMudet.YRpc_outer,
                        ship_geo.tauMudet.ZRpc_outer,
                    )
                    taumuondetector.SetRpcInnerDimensions(
                        ship_geo.tauMudet.XRpc_inner,
                        ship_geo.tauMudet.YRpc_inner,
                        ship_geo.tauMudet.ZRpc_inner,
                    )
                    taumuondetector.SetRpcGapDimensions(
                        ship_geo.tauMudet.XRpcGap,
                        ship_geo.tauMudet.YRpcGap,
                        ship_geo.tauMudet.ZRpcGap,
                    )
                    taumuondetector.SetPillarDimensions(
                        ship_geo.tauMudet.PillarX,
                        ship_geo.tauMudet.PillarY,
                        ship_geo.tauMudet.PillarZ,
                    )
                if ship_geo.nuTauTargetDesign == 3:
                    if hasattr(
                        ship_geo.tauMudet, "deltax"
                    ):  # now replaced with veto taggers
                        taumuondetector.SetRpcDimDifferences(
                            ship_geo.tauMudet.deltax, ship_geo.tauMudet.deltay
                        )
                if ship_geo.nuTauTargetDesign < 3:
                    taumuondetector.SetReturnYokeDimensions(
                        ship_geo.tauMudet.XRyoke,
                        ship_geo.tauMudet.YRyoke,
                        ship_geo.tauMudet.ZRyoke,
                    )
                    taumuondetector.SetSmallerYokeDimensions(
                        ship_geo.tauMudet.XRyoke_s,
                        ship_geo.tauMudet.YRyoke_s,
                        ship_geo.tauMudet.ZRyoke_s,
                    )
                    taumuondetector.SetZDimensionArm(ship_geo.tauMudet.ZArm)
                    taumuondetector.SetGapDownstream(ship_geo.tauMudet.GapD)
                    taumuondetector.SetGapMiddle(ship_geo.tauMudet.GapM)
                    taumuondetector.SetMagneticField(ship_geo.tauMudet.B)
                    taumuondetector.SetCoilParameters(
                        ship_geo.tauMudet.CoilH,
                        ship_geo.tauMudet.CoilW,
                        ship_geo.tauMudet.N,
                        ship_geo.tauMudet.CoilG,
                    )

            if (
                ship_geo.nuTauTargetDesign == 4
            ):  # magnetic field is back in taumuondetector for mufilter
                taumuondetector.SetRpcDimensions(
                    ship_geo.tauMudet.XRpc,
                    ship_geo.tauMudet.YRpc,
                    ship_geo.tauMudet.ZRpc,
                )
                taumuondetector.SetGapMiddle(ship_geo.tauMudet.GapM)
                taumuondetector.SetMagneticField(ship_geo.tauMudet.B)
                taumuondetector.SetReturnYokeDimensions(
                    ship_geo.tauMudet.XRyoke,
                    ship_geo.tauMudet.YRyoke,
                    ship_geo.tauMudet.ZRyoke,
                )
                taumuondetector.SetCoilParameters(
                    ship_geo.tauMudet.CoilH, ship_geo.tauMudet.CoilW, 1, 0.0
                )  # for now, only containers
            detectorList.append(taumuondetector)
            if (
                ship_geo.nuTauTargetDesign == 0
                or ship_geo.nuTauTargetDesign == 1
                or ship_geo.nuTauTargetDesign == 3
            ):
                EmuMagnet = ROOT.EmulsionMagnet(
                    "EmuMagnet", ship_geo.EmuMagnet.zC, "EmulsionMagnet"
                )
                EmuMagnet.SetDesign(ship_geo.EmuMagnet.Design)
                EmuMagnet.SetGaps(ship_geo.EmuMagnet.GapUp, ship_geo.EmuMagnet.GapDown)
                EmuMagnet.SetMagneticField(ship_geo.EmuMagnet.B)
                EmuMagnet.SetConstantField(ship_geo.EmuMagnet.WithConstField)
                EmuMagnet.SetMagnetSizes(
                    ship_geo.EmuMagnet.X, ship_geo.EmuMagnet.Y, ship_geo.EmuMagnet.Z
                )
                if ship_geo.nuTauTargetDesign == 0 or ship_geo.nuTauTargetDesign == 1:
                    EmuMagnet.SetCoilParameters(
                        ship_geo.EmuMagnet.Radius,
                        ship_geo.EmuMagnet.Height1,
                        ship_geo.EmuMagnet.Height2,
                        ship_geo.EmuMagnet.Distance,
                    )
                if ship_geo.nuTauTargetDesign == 3:
                    EmuMagnet.SetCoilParameters(
                        ship_geo.EmuMagnet.CoilX,
                        ship_geo.EmuMagnet.CoilY,
                        ship_geo.EmuMagnet.Height1,
                        ship_geo.EmuMagnet.Height2,
                        ship_geo.EmuMagnet.Thickness,
                    )
                    EmuMagnet.SetCutDimensions(
                        ship_geo.EmuMagnet.CutLength, ship_geo.EmuMagnet.CutHeight
                    )
                EmuMagnet.SetMagnetColumn(
                    ship_geo.EmuMagnet.ColX,
                    ship_geo.EmuMagnet.ColY,
                    ship_geo.EmuMagnet.ColZ,
                )
                EmuMagnet.SetBaseDim(
                    ship_geo.EmuMagnet.BaseX,
                    ship_geo.EmuMagnet.BaseY,
                    ship_geo.EmuMagnet.BaseZ,
                )
                EmuMagnet.SetPillarDimensions(
                    ship_geo.EmuMagnet.PillarX,
                    ship_geo.EmuMagnet.PillarY,
                    ship_geo.EmuMagnet.PillarZ,
                )
                detectorList.append(EmuMagnet)
            if ship_geo.nuTauTargetDesign == 2 or ship_geo.nuTauTargetDesign == 4:
                EmuMagnet = ROOT.EmulsionMagnet()

            NuTauTarget = ROOT.Target(
                "NuTauTarget", ship_geo.NuTauTarget.Ydist, ROOT.kTRUE
            )
            NuTauTarget.MakeNuTargetPassive(ship_geo.NuTauTarget.nuTargetPassive)
            if hasattr(
                ship_geo.NuTauTarget, "SingleEmFilm"
            ):  # for backward compatibility
                NuTauTarget.MergeTopBot(ship_geo.NuTauTarget.SingleEmFilm)
            NuTauTarget.SetDetectorDesign(ship_geo.NuTauTarget.Design)
            if ship_geo.nuTauTargetDesign != 3:
                NuTauTarget.SetCenterZ(ship_geo.NuTauTarget.zC)
            if ship_geo.nuTauTargetDesign == 3:
                NuTauTarget.SetCenterZ(
                    ship_geo.EmuMagnet.zC
                )  # now the centers of emumagnet and nutautarget are different (target does not include HPT)
                NuTauTarget.SetNumberTargets(ship_geo.NuTauTarget.target)
                NuTauTarget.SetHpTParam(
                    ship_geo.tauHPT.nHPT, ship_geo.tauHPT.distHPT, ship_geo.tauHPT.DZ
                )
            NuTauTarget.SetNumberBricks(
                ship_geo.NuTauTarget.col,
                ship_geo.NuTauTarget.row,
                ship_geo.NuTauTarget.wall,
            )
            NuTauTarget.SetDetectorDimension(
                ship_geo.NuTauTarget.xdim,
                ship_geo.NuTauTarget.ydim,
                ship_geo.NuTauTarget.zdim,
            )
            if (
                hasattr(ship_geo.NuTauTarget, "WallXDim")
                and hasattr(ship_geo.NuTauTarget, "WallYDim")
                and hasattr(ship_geo.NuTauTarget, "WallZDim")
            ):
                NuTauTarget.SetTargetWallDimension(
                    ship_geo.NuTauTarget.WallXDim,
                    ship_geo.NuTauTarget.WallYDim,
                    ship_geo.NuTauTarget.WallZDim,
                )
            NuTauTarget.SetEmulsionParam(
                ship_geo.NuTauTarget.EmTh,
                ship_geo.NuTauTarget.EmX,
                ship_geo.NuTauTarget.EmY,
                ship_geo.NuTauTarget.PBTh,
                ship_geo.NuTauTarget.EPlW,
                ship_geo.NuTauTarget.LeadTh,
                ship_geo.NuTauTarget.AllPW,
            )
            ##
            if not hasattr(
                ship_geo.NuTauTarget, "n_plates"
            ):  # for backward compatibility
                ship_geo.NuTauTarget.n_plates = 56
            NuTauTarget.SetBrickParam(
                ship_geo.NuTauTarget.BrX,
                ship_geo.NuTauTarget.BrY,
                ship_geo.NuTauTarget.BrZ,
                ship_geo.NuTauTarget.BrPackX,
                ship_geo.NuTauTarget.BrPackY,
                ship_geo.NuTauTarget.BrPackZ,
                ship_geo.NuTauTarget.n_plates,
            )

            NuTauTarget.SetCESParam(
                ship_geo.NuTauTarget.RohG,
                ship_geo.NuTauTarget.LayerCESW,
                ship_geo.NuTauTarget.CESW,
                ship_geo.NuTauTarget.CESPack,
            )
            NuTauTarget.SetCellParam(ship_geo.NuTauTarget.CellW)
            if ship_geo.nuTauTargetDesign == 0 or ship_geo.nuTauTargetDesign == 1:
                NuTauTarget.SetMagnetHeight(ship_geo.EmuMagnet.Y)
                NuTauTarget.SetColumnHeight(ship_geo.EmuMagnet.ColY)
                NuTauTarget.SetBaseHeight(ship_geo.EmuMagnet.BaseY)
                NuTauTarget.SetCoilUpHeight(ship_geo.EmuMagnet.Height1)
                NuTauTarget.SetCoilDownHeight(ship_geo.EmuMagnet.Height2)
            if ship_geo.nuTauTargetDesign != 2 and ship_geo.nuTauTargetDesign != 4:
                NuTauTarget.SetMagneticField(ship_geo.EmuMagnet.B)
            if ship_geo.nuTauTargetDesign == 2 or ship_geo.nuTauTargetDesign == 4:
                NuTauTarget.SetPillarDimension(
                    ship_geo.NuTauTarget.PillarX,
                    ship_geo.NuTauTarget.PillarY,
                    ship_geo.NuTauTarget.PillarZ,
                )
                NuTauTarget.SetBaseDimension(
                    ship_geo.NuTauTarget.BaseX,
                    ship_geo.NuTauTarget.BaseY,
                    ship_geo.NuTauTarget.BaseZ,
                )

            # Target Tracker
            NuTauTT = ROOT.TargetTracker(
                "TargetTrackers",
                ship_geo.NuTauTT.TTX,
                ship_geo.NuTauTT.TTY,
                ship_geo.NuTauTT.TTZ,
                ROOT.kTRUE,
            )
            NuTauTT.SetDesign(ship_geo.NuTauTT.design)
            if hasattr(
                ship_geo.NuTauTT, "scifimat_width"
            ):  # for backward compatibility
                NuTauTT.SetSciFiParam(
                    ship_geo.NuTauTT.scifimat_width,
                    ship_geo.NuTauTT.scifimat_hor,
                    ship_geo.NuTauTT.scifimat_vert,
                    ship_geo.NuTauTT.scifimat_z,
                    ship_geo.NuTauTT.support_z,
                    ship_geo.NuTauTT.honeycomb_z,
                )
                NuTauTT.SetNumberSciFi(
                    ship_geo.NuTauTT.n_hor_planes, ship_geo.NuTauTT.n_vert_planes
                )
            NuTauTT.SetTargetTrackerParam(
                ship_geo.NuTauTT.TTX, ship_geo.NuTauTT.TTY, ship_geo.NuTauTT.TTZ
            )
            NuTauTT.SetBrickParam(ship_geo.NuTauTarget.CellW)
            NuTauTT.SetTotZDimension(ship_geo.NuTauTarget.zdim)
            NuTauTT.SetNumberTT(ship_geo.NuTauTT.n)
            # method of nutau target that must be called after TT parameter definition
            NuTauTarget.SetTTzdimension(ship_geo.NuTauTT.TTZ)
            detectorList.append(NuTauTarget)
            detectorList.append(NuTauTT)

            # High Precision Tracker
            if ship_geo.nuTauTargetDesign < 4:
                tauHpt = ROOT.Hpt(
                    "HighPrecisionTrackers",
                    ship_geo.tauHPT.DX,
                    ship_geo.tauHPT.DY,
                    ship_geo.tauHPT.DZ,
                    ROOT.kTRUE,
                )
                tauHpt.SetZsize(ship_geo.tauMudet.Ztot)
                tauHpt.SetDesign(ship_geo.NuTauTarget.Design)
                if hasattr(
                    ship_geo.tauHPT, "scifimat_width"
                ):  # for backward compatibility
                    tauHpt.SetSciFiParam(
                        ship_geo.tauHPT.scifimat_width,
                        ship_geo.tauHPT.scifimat_hor,
                        ship_geo.tauHPT.scifimat_vert,
                        ship_geo.tauHPT.scifimat_z,
                        ship_geo.tauHPT.support_z,
                        ship_geo.tauHPT.honeycomb_z,
                    )
                    tauHpt.SetNumberSciFi(
                        ship_geo.tauHPT.n_hor_planes, ship_geo.tauHPT.n_vert_planes
                    )
                    tauHpt.SetHPTrackerParam(
                        ship_geo.tauHPT.TX, ship_geo.tauHPT.TY, ship_geo.tauHPT.TZ
                    )
                if ship_geo.nuTauTargetDesign < 3:
                    tauHpt.SetConcreteBaseDim(
                        ship_geo.tauHPT.ConcreteX,
                        ship_geo.tauHPT.ConcreteY,
                        ship_geo.tauHPT.ConcreteZ,
                    )
                if ship_geo.nuTauTargetDesign == 3:
                    tauHpt.SetHPTNumber(ship_geo.tauHPT.nHPT)
                    tauHpt.SetDistanceHPTs(ship_geo.tauHPT.distHPT)
                    if hasattr(ship_geo.tauHPT, "SRDY"):
                        tauHpt.SetSurroundingDetHeight(ship_geo.tauHPT.SRDY)
                    tauHpt.GetMagnetGeometry(
                        ship_geo.EmuMagnet.zC, ship_geo.EmuMagnet.Y
                    )
                    tauHpt.GetNumberofTargets(ship_geo.NuTauTarget.target)
                detectorList.append(tauHpt)

    # for backward compatibility
    if not hasattr(ship_geo.strawtubes, "YPlaneOffset"):
        ship_geo.strawtubes.YLayerOffset = ship_geo.strawtubes.StrawPitch / 2.0
        ship_geo.strawtubes.YPlaneOffset = ship_geo.strawtubes.StrawPitch / 4.0
    if ship_geo.strawDesign > 1:
        # for backward compatibility
        if ship_geo.strawDesign == 10 and not hasattr(
            ship_geo.strawtubes, "DeltazFrame"
        ):
            ship_geo.strawtubes.DeltazFrame = 2.5 * u.cm
            ship_geo.strawtubes.FrameLateralWidth = 1.2 * u.m
            ship_geo.strawtubes.FrameMaterial = "steel"
        elif not hasattr(ship_geo.strawtubes, "DeltazFrame"):
            ship_geo.strawtubes.DeltazFrame = 10.0 * u.cm
            ship_geo.strawtubes.FrameLateralWidth = 1.0 * u.cm
            ship_geo.strawtubes.FrameMaterial = "aluminium"
        ship_geo.strawtubes.medium = "vacuums" if ship_geo.DecayVolumeMedium == "vaccums" else "air"


        Prestrawdetector = ROOT.prestrawdetector('Prestrawdetector', True)
        Prestrawdetector.SetZ(ship_geo.psd)
        detectorList.append(Prestrawdetector)

        print(ship_geo)
        Strawtubes = ROOT.strawtubes(ship_geo.strawtubes.medium)
        Strawtubes.SetZpositions(
            ship_geo.vetoStation.z,
            ship_geo.TrackStation1.z,
            ship_geo.TrackStation2.z,
            ship_geo.TrackStation3.z,
            ship_geo.TrackStation4.z,
        )
        Strawtubes.SetDeltazFrame(ship_geo.strawtubes.DeltazFrame)
        Strawtubes.SetFrameLateralWidth(ship_geo.strawtubes.FrameLateralWidth)
        Strawtubes.SetFrameMaterial(ship_geo.strawtubes.FrameMaterial)
        Strawtubes.SetDeltazView(ship_geo.strawtubes.DeltazView)
        Strawtubes.SetInnerStrawDiameter(ship_geo.strawtubes.InnerStrawDiameter)
        Strawtubes.SetOuterStrawDiameter(ship_geo.strawtubes.OuterStrawDiameter)
        Strawtubes.SetStrawPitch(
            ship_geo.strawtubes.StrawPitch,
            ship_geo.strawtubes.YLayerOffset,
            ship_geo.strawtubes.YPlaneOffset,
        )
        Strawtubes.SetDeltazLayer(ship_geo.strawtubes.DeltazLayer)
        Strawtubes.SetDeltazPlane(ship_geo.strawtubes.DeltazPlane)
        Strawtubes.SetStrawsPerLayer(ship_geo.strawtubes.StrawsPerLayer)
        Strawtubes.SetStereoAngle(ship_geo.strawtubes.ViewAngle)
        Strawtubes.SetWireThickness(ship_geo.strawtubes.WireThickness)
        Strawtubes.SetVacBox_x(ship_geo.strawtubes.VacBox_x)
        Strawtubes.SetVacBox_y(ship_geo.strawtubes.VacBox_y)
        Strawtubes.SetStrawLength(ship_geo.strawtubes.StrawLength)

        if hasattr(ship_geo.strawtubes, "StrawLengthVeto"):
            Strawtubes.SetStrawLengthVeto(ship_geo.strawtubes.StrawLengthVeto)
            Strawtubes.SetStrawLength12(ship_geo.strawtubes.StrawLength12)
            Strawtubes.SetVetoYDim(ship_geo.strawtubes.vetoydim)
            Strawtubes.SetTr12YDim(ship_geo.strawtubes.tr12ydim)
            Strawtubes.SetTr34YDim(ship_geo.strawtubes.tr34ydim)
        else:
            Strawtubes.SetStrawLengthVeto(ship_geo.strawtubes.StrawLength)
            Strawtubes.SetStrawLength12(ship_geo.strawtubes.StrawLength)
            Strawtubes.SetVetoYDim(ship_geo.Yheight / 2.0)
            Strawtubes.SetTr12YDim(ship_geo.Yheight / 2.0)
            Strawtubes.SetTr34YDim(ship_geo.Yheight / 2.0)
        # for the digitizing step
        Strawtubes.SetStrawResolution(
            getParameter("strawtubes.v_drift", ship_geo, latestShipGeo),
            getParameter("strawtubes.sigma_spatial", ship_geo, latestShipGeo),
        )
        detectorList.append(Strawtubes)
>>>>>>> bbdec75e (decoupling implementation, generator fix)

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
<<<<<<< HEAD
    # exclusionList = ["Muon","Ecal","Hcal","Strawtubes","TargetTrackers","NuTauTarget",\
    #                 "Veto","Magnet","MuonShield","TargetStation", "TimeDet", "UpstreamTagger"]
=======
    if ship_geo.decouple:
        exclusionList = ["Muon","Ecal","Hcal","TargetTrackers","NuTauTarget","HighPrecisionTrackers",\
                 "Veto","MuonShield","TargetStation","NuTauMudet","EmuMagnet", "TimeDet", "UpstreamTagger"]
>>>>>>> bbdec75e (decoupling implementation, generator fix)

    for x in detectorList:
        if x.GetName() in exclusionList:
            continue
        run.AddModule(x)
    # return list of detector elements
    detElements = {}
    for x in run.GetListOfModules():
        detElements[x.GetName()] = x
    return detElements
