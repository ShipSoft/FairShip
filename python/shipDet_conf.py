#!/usr/bin/env python
import ROOT
import os
import shipunit as u
from ShipGeoConfig import AttrDict, ConfigRegistry
from ShieldUtils import find_shield_center
from array import array
import yaml

detectorList = []


def getParameter(x, ship_geo, latestShipGeo):
    lv = x.split(".")
    last = lv[len(lv) - 1]
    top = ""
    for l in range(len(lv) - 1):
        top += lv[l]
        if l < len(lv) - 2:
            top += "."
    a = getattr(ship_geo, top)
    if hasattr(a, last):
        return getattr(a, last)
        # not in the list of recorded parameteres. probably added after
        # creation of file. Check newest geometry_config:
    a = getattr(latestShipGeo, top)
    return getattr(a, last)


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
                      snd_tauMu_zTot,
                      snd_tauMu_zMudetC,
                      cave_floorHeightMuonShield):

    with open(yaml_file) as file:
        config = yaml.safe_load(file)

    tauMu_geo = AttrDict(config['tauMu'])
    nuTarget_geo = AttrDict(config['nuTarget'])
    nuTauTT_geo = AttrDict(config['nuTauTT'])

    #specific parameters
    #tauMu det
    snd_tauMu_Xtot = tauMu_geo.XRpc + 2*tauMu_geo.XRyoke
    snd_tauMu_Ytot = tauMu_geo.YRpc + 2*(tauMu_geo.CoilH+tauMu_geo.YRyoke)
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

    snd_nuTarget_zC = snd_tauMu_zMudetC - snd_tauMu_zTot/2 - 20*u.cm - snd_nuTarget_zdim/2.

    snd_nuTarget_PillarY = 10*u.m - snd_nuTarget_ydim/2 -nuTarget_geo.BaseY- 0.1*u.mm - cave_floorHeightMuonShield

    taumuondetector = ROOT.NuTauMudet(
        "NuTauMudet", snd_tauMu_zMudetC, ROOT.kTRUE
    )
    taumuondetector.SetDesign(4)
    taumuondetector.SetTotDimensions(
        snd_tauMu_Xtot, snd_tauMu_Ytot, snd_tauMu_zTot
    )
    taumuondetector.SetRpcDimensions(
        tauMu_geo.XRpc,
        tauMu_geo.YRpc,
        tauMu_geo.ZRpc,
    )
    taumuondetector.SetGapMiddle(tauMu_geo.GapM)
    taumuondetector.SetMagneticField(tauMu_geo.B)
    taumuondetector.SetReturnYokeDimensions(
        tauMu_geo.XRyoke,
        tauMu_geo.YRyoke,
        snd_tauMu_zTot,
    )
    taumuondetector.SetCoilParameters(
        tauMu_geo.CoilH, tauMu_geo.CoilW, 1, 0.0
    )  # for now, only containers
    detectorList.append(taumuondetector)


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
    NuTauTarget.SetCESParam(
        nuTarget_geo.RohG,
        nuTarget_geo.LayerCESW,
        nuTarget_geo.CESW,
        nuTarget_geo.CESPack,
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

    mtc_geo = AttrDict(config['MTC'])
    # Initialize detector
    if mtc_geo.zPosition == "auto":
        # Get the the center of the *last* magnet
        mtc_geo.zPosition = find_shield_center(ship_geo)[2][-1]
        print("MTC zPosition set to ", mtc_geo.zPosition)
    mtc = ROOT.MTCDetector("MTC", ROOT.kTRUE)
    mtc.SetMTCParameters(
        mtc_geo.width,
        mtc_geo.height,
        mtc_geo.ironThick,
        mtc_geo.sciFiThick,
        mtc_geo.scintThick,
        mtc_geo.nLayers,
        mtc_geo.zPosition,
        mtc_geo.fieldY
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


def configure(run, ship_geo):
    # ---- for backward compatibility ----
    if not hasattr(ship_geo, "DecayVolumeMedium"):
        raise ValueError(
            "DecayVolumeMedium is not defined, possibly old (incompatible) geometry!"
        )
    if not hasattr(ship_geo, "tankDesign"):
        ship_geo.tankDesign = 5
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

    latestShipGeo = ConfigRegistry.loadpy(
        "$FAIRSHIP/geometry/geometry_config.py",
        Yheight=ship_geo.Yheight / u.m,
        tankDesign=ship_geo.tankDesign,
        nuTauTargetDesign=ship_geo.nuTauTargetDesign,
        muShieldGeo=ship_geo.muShieldGeo,
        SC_mag=ship_geo.SC_mag,
        shieldName=ship_geo.shieldName,
        DecayVolumeMedium=ship_geo.DecayVolumeMedium,
    )
    # -----Create media-------------------------------------------------
    run.SetMaterials("media.geo")  # Materials
    # ------------------------------------------------------------------------

    # -----Create geometry----------------------------------------------
    cave = ROOT.ShipCave("CAVE")
    if ship_geo.tankDesign < 5:
        cave.SetGeometryFileName("cave.geo")
    else:
        cave.SetGeometryFileName("caveWithAir.geo")
    detectorList.append(cave)

    # magnetized hadron absorber defined in ShipMuonShield
    with open(ship_geo.target_yaml) as file:
        targetconfig = yaml.safe_load(file)
        target_geo = AttrDict(targetconfig['target'])


    TargetStation = ROOT.ShipTargetStation(
        "TargetStation",
        ship_geo.target.length,
        ship_geo.target.z,
        targetconfig['targetOpt'],
        target_geo.sl,
    )

    if targetconfig['targetOpt'] > 10:
        slices_length = ROOT.std.vector("float")()
        slices_material = ROOT.std.vector("std::string")()
        for i in range(target_geo.Nplates):
            for j in range(target_geo.N[i]):
                slices_length.push_back(target_geo.L[i])
                slices_material.push_back(target_geo.M[i])
        print(slices_material,slices_length)
        TargetStation.SetLayerPosMat(target_geo.xy, slices_length, slices_material)
    detectorList.append(TargetStation)


    in_params = list(ship_geo.muShield.params)

    MuonShield = ROOT.ShipMuonShield(
        in_params,
        ship_geo.cave.floorHeightMuonShield,
        ship_geo.muShield.z,
        ship_geo.muShield.WithConstField,
        ship_geo.SC_mag
    )
    detectorList.append(MuonShield)

    if not hasattr(ship_geo, "magnetDesign"):
        # backward compatibility
        magnet_design = 2
        if ship_geo.tankDesign == 5:
            magnet_design = 3
        if ship_geo.tankDesign == 6:
            magnet_design = 4
        ship_geo.magnetDesign = magnet_design
        ship_geo.Bfield.YokeWidth = 200.0 * u.cm
        ship_geo.Bfield.YokeDepth = 200.0 * u.cm
        ship_geo.Bfield.CoilThick = 25.0 * u.cm
    # sanity check, 2018 layout ship_geo.tankDesign == 6 has to be together with ship_geo.nuTauTargetDesign == 3
    if ship_geo.tankDesign != 6 and ship_geo.nuTauTargetDesign == 3:
        print(
            "version of tankDesign and nuTauTargetDesign are not compatible, should be 6 and 3, it is ",
            ship_geo.tankDesign,
            ship_geo.nuTauTargetDesign,
        )
        exit()
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

    # For SND
    if ship_geo.SND:
        if ship_geo.SND_design == 2:
            # SND design 2 -- MTC
            configure_snd_mtc(
                os.path.join(fairship, "geometry", "MTC_config.yaml"),
                ship_geo
            )
        else:
            configure_snd_old(
            os.path.join(fairship, "geometry", "snd_config_old.yaml"),
            ship_geo.tauMudet.Ztot,
            ship_geo.tauMudet.zMudetC,
            ship_geo.cave.floorHeightMuonShield,
            )


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
        ship_geo.strawtubes.medium = "vacuums" if ship_geo.DecayVolumeMedium == "vacuums" else "air"

        Strawtubes = ROOT.strawtubes(ship_geo.strawtubes.medium)
        Strawtubes.SetZpositions(
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

        Strawtubes.SetStrawLength12(ship_geo.strawtubes.StrawLength12)
        Strawtubes.SetTr12YDim(ship_geo.strawtubes.tr12ydim)
        Strawtubes.SetTr34YDim(ship_geo.strawtubes.tr34ydim)
        # for the digitizing step
        Strawtubes.SetStrawResolution(
            getParameter("strawtubes.v_drift", ship_geo, latestShipGeo),
            getParameter("strawtubes.sigma_spatial", ship_geo, latestShipGeo),
        )
        detectorList.append(Strawtubes)

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
    # exclusionList = ["Muon","Ecal","Hcal","Strawtubes","TargetTrackers","NuTauTarget","HighPrecisionTrackers",\
    #                 "Veto","Magnet","MuonShield","TargetStation","NuTauMudet","EmuMagnet", "TimeDet", "UpstreamTagger"]

    for x in detectorList:
        if x.GetName() in exclusionList:
            continue
        run.AddModule(x)
    # return list of detector elements
    detElements = {}
    for x in run.GetListOfModules():
        detElements[x.GetName()] = x
    return detElements
