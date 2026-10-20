#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import math
import os
from typing import Any

import geometry_config
import geometry_from_file
import ROOT
import shipunit as u
import yaml
from ShipGeoConfig import AttrDict

# Holds heterogeneous FairModule subclasses (Target, MTC, ShipCave, …); annotate
# as list[Any] so pyrefly doesn't lock the element type to the first append.
detectorList: list[Any] = []


def configure_snd_old(yaml_file: str, emulsion_target_z_end, cave_floorHeightMuonShield) -> None:
    with open(yaml_file) as file:
        config = yaml.safe_load(file)
    nuTarget_geo = AttrDict(config["nuTarget"])
    nuTauTT_geo = AttrDict(config["nuTauTT"])

    # specific parameters
    # nu Target Tracker
    snd_nuTauTT_TTX = (
        nuTauTT_geo.n_hor_planes * nuTauTT_geo.scifimat_width + 2.9 * u.cm
    )  # endpieces (~2.9cm from previous geom)
    snd_nuTauTT_TTY = (
        nuTauTT_geo.n_vert_planes * nuTauTT_geo.scifimat_width + 2.9 * u.cm
    )  # endpieces (~2.9cm from previous geom)

    snd_nuTauTT_TTZ = 2 * nuTauTT_geo.support_z + 2 * nuTauTT_geo.scifimat_z + nuTauTT_geo.honeycomb_z

    # nuTau target
    snd_nuTarget_BrZ = (
        nuTarget_geo.n_plates * nuTarget_geo.LeadTh
        + (nuTarget_geo.n_plates + 1) * (2 * nuTarget_geo.EmTh + nuTarget_geo.PBTh)
        + nuTarget_geo.BrPackZ
    )
    snd_nuTarget_BrX = nuTarget_geo.BrPackX + nuTarget_geo.EmX
    snd_nuTarget_BrY = nuTarget_geo.BrPackY + nuTarget_geo.EmY

    snd_nuTarget_zdim = nuTarget_geo.wall * snd_nuTarget_BrZ + (nuTarget_geo.wall + 1) * snd_nuTauTT_TTZ
    snd_nuTarget_xdim = snd_nuTauTT_TTX
    snd_nuTarget_ydim = snd_nuTauTT_TTY

    snd_nuTarget_zC = emulsion_target_z_end - snd_nuTarget_zdim / 2.0

    snd_nuTarget_PillarY = (
        10 * u.m - snd_nuTarget_ydim / 2 - nuTarget_geo.BaseY - 0.1 * u.mm - cave_floorHeightMuonShield
    )
    NuTauTarget = ROOT.Target("NuTauTarget", nuTarget_geo.Ydist, ROOT.kTRUE)
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
        nuTarget_geo.col * snd_nuTarget_BrX,
        nuTarget_geo.row * snd_nuTarget_BrY + (nuTarget_geo.row - 1) * nuTarget_geo.Ydist,
        snd_nuTarget_BrZ,
    )
    NuTauTarget.SetEmulsionParam(
        nuTarget_geo.EmTh,
        nuTarget_geo.EmX,
        nuTarget_geo.EmY,
        nuTarget_geo.PBTh,
        2 * nuTarget_geo.EmTh + nuTarget_geo.PBTh,
        nuTarget_geo.LeadTh,
        nuTarget_geo.LeadTh + 2 * nuTarget_geo.EmTh + nuTarget_geo.PBTh,
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
    NuTauTarget.SetPillarDimension(nuTarget_geo.PillarX, snd_nuTarget_PillarY, nuTarget_geo.PillarZ)
    NuTauTarget.SetBaseDimension(snd_nuTarget_xdim + 20, nuTarget_geo.BaseY, snd_nuTarget_zdim + 10)
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
    NuTauTT.SetNumberSciFi(nuTauTT_geo.n_hor_planes, nuTauTT_geo.n_vert_planes)
    NuTauTT.SetTargetTrackerParam(snd_nuTauTT_TTX, snd_nuTauTT_TTY, snd_nuTauTT_TTZ)
    NuTauTT.SetBrickParam(snd_nuTarget_BrZ)
    NuTauTT.SetTotZDimension(snd_nuTarget_zdim)
    NuTauTT.SetNumberTT(nuTarget_geo.wall + 1)
    # method of nutau target that must be called after TT parameter definition
    NuTauTarget.SetTTzdimension(snd_nuTauTT_TTZ)

    detectorList.append(NuTauTarget)
    detectorList.append(NuTauTT)


def configure_snd_mtc(yaml_file: str, ship_geo) -> None:
    with open(yaml_file) as file:
        config = yaml.safe_load(file)

    ship_geo.mtc_geo = AttrDict(config["MTC"])
    # Initialize detector
    if ship_geo.mtc_geo.zPosition == "auto":
        # Centre of the second-to-last magnet (M6 in the 2026 layout), see configure_snd_siliconTarget
        mtc_total_length = (
            ship_geo.mtc_geo.ironThick + ship_geo.mtc_geo.sciFiThick + ship_geo.mtc_geo.scintThick
        ) * ship_geo.mtc_geo.nLayers
        ship_geo.mtc_geo.zPosition = ship_geo.muShield.Entrance[-2] + ship_geo.muShield.half_length[-2]
        if mtc_total_length > 2 * ship_geo.muShield.half_length[-2]:
            print("Warning: MTC is longer than the magnet it is placed in")
    mtc = ROOT.MTCDetector("MTC", ROOT.kTRUE)
    mtc.SetMTCParameters(
        ship_geo.mtc_geo.width,
        ship_geo.mtc_geo.height,
        ship_geo.mtc_geo.angle,
        ship_geo.mtc_geo.ironThick,
        ship_geo.mtc_geo.sciFiThick,
        ship_geo.mtc_geo.num_of_agg_channels,
        ship_geo.mtc_geo.scint_cell_size,
        ship_geo.mtc_geo.scintThick,
        ship_geo.mtc_geo.nLayers,
        ship_geo.mtc_geo.zPosition,
        ship_geo.mtc_geo.fieldY,
    )
    detectorList.append(mtc)


def configure_snd_siliconTarget(yaml_file: str, ship_geo) -> None:
    with open(yaml_file) as file:
        config = yaml.safe_load(file)

    ship_geo.SiliconTarget_geo = AttrDict(config["SiliconTarget"])
    # Initialize detector
    if ship_geo.SiliconTarget_geo.zPosition == "auto":
        # auto: the last layer ends at the downstream face of the third-to-last
        # magnet (S5 in the 2026 layout), one magnet Z-gap upstream of the
        # magnet that holds the MTC. This follows the integration layout
        # 2026-0.1, where the scattering detector occupies the end of S5 and
        # the whole of M6.
        SiliconTarget_total_length = ship_geo.SiliconTarget_geo.targetSpacing * ship_geo.SiliconTarget_geo.nLayers
        ship_geo.SiliconTarget_geo.zPosition = (
            ship_geo.muShield.Entrance[-2] - ship_geo.muShield.Zgap[-2] - SiliconTarget_total_length / 2
        )
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
        ship_geo.SiliconTarget_geo.moduleOffset,
    )
    detectorList.append(SiliconTarget)


def configure_veto(yaml_file: str, z0) -> None:
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
        veto_geo.he_balloon_thickness,
        veto_geo.he_balloon_med,
    )

    detectorList.append(Veto)


def configure_strawtubes(yaml_file: str, ship_geo) -> None:
    with open(yaml_file) as file:
        config = yaml.safe_load(file)

    ship_geo.strawtubes_geo = AttrDict(config["SST"])

    # Straw tubes in decay vessel if vacuum, otherwise outside in air
    ship_geo.strawtubes_geo.medium = "vacuums" if ship_geo.DecayVolumeMedium == "vacuums" else "air"

    # Choose frame material
    if ship_geo.strawDesign == 4:
        ship_geo.strawtubes_geo.frame_material = "Aluminium"
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

    # For digitization
    strawtubes.SetStrawResolution(
        ship_geo.strawtubesDigi.v_drift,
        ship_geo.strawtubesDigi.sigma_spatial,
    )

    detectorList.append(strawtubes)


def check_upstream_tagger_map(ubt_map, ubt_geo) -> None:
    """Check that the UBT map covers exactly the UBT box of the geometry configuration.

    A generated map does by construction; this also checks a map stored with a
    geometry, against the box stored with it. A box larger than the map would
    leave a strip without tiles, a smaller one would stop ConstructGeometry.
    """
    tolerance = 1.0e-6  # cm
    box = {
        "x": (ubt_geo.BoxCenterX - ubt_geo.BoxX / 2.0, ubt_geo.BoxCenterX + ubt_geo.BoxX / 2.0),
        "y": (ubt_geo.BoxCenterY - ubt_geo.BoxY / 2.0, ubt_geo.BoxCenterY + ubt_geo.BoxY / 2.0),
    }
    bounds = {axis: tuple(bound * u.cm for bound in ubt_map["bounds"][axis]) for axis in ("x", "y")}
    for axis in ("x", "y"):
        if any(abs(b - e) > tolerance * u.cm for b, e in zip(bounds[axis], box[axis])):
            raise ValueError(
                f"The UBT map bounds in {axis}, {bounds[axis]} cm, differ from the UBT box of the geometry"
                f" configuration, {box[axis]} cm"
            )

    # The regions must tile the bounds: each inside them, no two overlapping,
    # and together as large as them.
    rectangles = []
    for region in ubt_map["regions"]:
        half_x, half_y = region["size_x"] * u.cm / 2.0, region["size_y"] * u.cm / 2.0
        x, y = region["x"] * u.cm, region["y"] * u.cm
        rectangle = (x - half_x, x + half_x, y - half_y, y + half_y)
        if (
            rectangle[0] < bounds["x"][0] - tolerance
            or rectangle[1] > bounds["x"][1] + tolerance
            or rectangle[2] < bounds["y"][0] - tolerance
            or rectangle[3] > bounds["y"][1] + tolerance
        ):
            raise ValueError(f"UBT region {region['id']} extends outside the map bounds")
        rectangles.append((region["id"], rectangle))
    for i, (id_a, a) in enumerate(rectangles):
        for id_b, b in rectangles[i + 1 :]:
            if (
                a[0] < b[1] - tolerance
                and b[0] < a[1] - tolerance
                and a[2] < b[3] - tolerance
                and b[2] < a[3] - tolerance
            ):
                raise ValueError(f"UBT regions {id_a} and {id_b} overlap")
    covered = sum((r[1] - r[0]) * (r[3] - r[2]) for _, r in rectangles)
    area = (bounds["x"][1] - bounds["x"][0]) * (bounds["y"][1] - bounds["y"][0])
    if abs(covered - area) > tolerance * area:
        raise ValueError(f"The UBT regions cover {covered} cm2 of the {area} cm2 map: some of it has no tiles")


def _axis_cells(low: float, high: float, size: float) -> list[tuple[float, float]]:
    """(centre, size) of the cells of ``size`` centred on the beam axis, cut at [low, high]."""
    first = math.floor((low + size / 2.0) / size + 1.0e-9)
    last = math.ceil((high - size / 2.0) / size - 1.0e-9)
    cells = []
    for k in range(first, last + 1):
        cell_low, cell_high = max(k * size - size / 2.0, low), min(k * size + size / 2.0, high)
        if cell_high - cell_low > 1.0e-9:
            cells.append(((cell_low + cell_high) / 2.0, cell_high - cell_low))
    return cells


def _small_tile_areas(rule) -> list[tuple[float, float, float, float]]:
    """The areas of small tiles of the UBT rule, as (x low, x high, y low, y high) in cm."""
    areas = []
    for area in rule.get("small_tile_areas", []):
        (x_low, x_high), (y_low, y_high) = (float(v) for v in area["x"]), (float(v) for v in area["y"])
        if not (x_low < x_high and y_low < y_high):
            raise ValueError(f"The UBT small-tile area {area} must have x and y ranges [low, high] with low < high")
        areas.append((x_low, x_high, y_low, y_high))
    return areas


def generate_upstream_tagger_map(rule, ubt_geo) -> dict[str, Any]:
    """Generate the UBT regions on the UBT box of the geometry configuration.

    See the note in geometry/UpstreamTagger_config.yaml for the rule. The map
    has the same form as the one stored with the geometry: kind, units, the
    bounds of the box and the regions, all in cm.
    """
    if rule["kind"] != "simulation" or rule["units"] != "cm":
        raise ValueError("The UBT map must be a simulation map expressed in cm")
    bounds = {
        "x": [(ubt_geo.BoxCenterX - ubt_geo.BoxX / 2.0) / u.cm, (ubt_geo.BoxCenterX + ubt_geo.BoxX / 2.0) / u.cm],
        "y": [(ubt_geo.BoxCenterY - ubt_geo.BoxY / 2.0) / u.cm, (ubt_geo.BoxCenterY + ubt_geo.BoxY / 2.0) / u.cm],
    }
    size = rule["region_size"]
    areas = _small_tile_areas(rule)
    tolerance = 1.0e-9  # cm
    regions = []
    for y, size_y in _axis_cells(bounds["y"][0], bounds["y"][1], size):
        for x, size_x in _axis_cells(bounds["x"][0], bounds["x"][1], size):
            # A region lying inside a small-tile area has small tiles; an area
            # covering only part of a region would cut it in two.
            low_x, high_x, low_y, high_y = x - size_x / 2.0, x + size_x / 2.0, y - size_y / 2.0, y + size_y / 2.0
            in_area = False
            for area in areas:
                overlap_x = min(high_x, area[1]) - max(low_x, area[0])
                overlap_y = min(high_y, area[3]) - max(low_y, area[2])
                if overlap_x <= tolerance or overlap_y <= tolerance:
                    continue
                if overlap_x < size_x - tolerance or overlap_y < size_y - tolerance:
                    raise ValueError(
                        f"The UBT small-tile area x {list(area[:2])}, y {list(area[2:])} cm covers only part of the"
                        f" region at ({x}, {y}) cm: its edges must lie on region edges"
                    )
                in_area = True
            tile = rule["small_tile_size"] if in_area else rule["large_tile_size"]
            for centre, extent, axis in ((x, size_x, "x"), (y, size_y, "y")):
                for edge in (centre - extent / 2.0, centre + extent / 2.0):
                    tiles = (edge - rule["tile_edge_offset"]) / tile
                    if abs(tiles - round(tiles)) > 1.0e-6:
                        raise ValueError(
                            f"The UBT region at ({x}, {y}) cm has an edge at {axis} = {edge} cm, off the grid of its"
                            f" {tile} cm tiles: the UBT box, {bounds} cm, must end on a tile edge"
                        )
            regions.append(
                {
                    "id": len(regions),
                    "x": x,
                    "y": y,
                    "size_x": size_x,
                    "size_y": size_y,
                    "constituent_tile_size": tile,
                }
            )
    return {"kind": rule["kind"], "units": rule["units"], "bounds": bounds, "regions": regions}


def configure_upstream_tagger(yaml_file: str, upstream_tagger, ship_geo) -> None:
    """Configure the UBT regions and their digitization parameters.

    The regions are generated from the rule in ``yaml_file`` on the UBT box of
    ``ship_geo``, and the resulting map is kept in ``ship_geo.UpstreamTagger_geo``,
    so that it is saved with the geometry. A configuration read back from a
    geometry file (reconstruction, analysis, ``-g``) already has it: then the
    stored map is used, so that the regions and tile IDs are those of the
    simulation, whatever the rule in the checkout says.
    """
    with open(yaml_file) as file:
        rule = yaml.safe_load(file)

    stored_map = ship_geo.get("UpstreamTagger_geo")
    if stored_map is None:
        ubt_map = generate_upstream_tagger_map(rule, ship_geo.UpstreamTagger)
        ship_geo.UpstreamTagger_geo = AttrDict(ubt_map)
    else:
        # The rule of the checkout is only compared with the stored map: it may
        # have changed since the simulation and no longer fit the stored box.
        try:
            differs = dict(stored_map) != generate_upstream_tagger_map(rule, ship_geo.UpstreamTagger)
        except ValueError:
            differs = True
        if differs:
            print(
                f"Warning: the UBT map generated from {yaml_file} differs from the one stored with the"
                " geometry; the stored map, used in the simulation, is used."
            )
        ubt_map = stored_map

    check_upstream_tagger_map(ubt_map, ship_geo.UpstreamTagger)

    regions = ubt_map["regions"]
    region_ids = [region["id"] for region in regions]
    if len(region_ids) != len(set(region_ids)):
        raise ValueError("The UBT detector map contains duplicate region IDs")

    # Kept in ShipGeo for digitization: detector ID -> constituent tile side
    # in FairShip internal length units.  This distinguishes 2x2 and 4x4 cm2.
    ship_geo.UpstreamTagger.RegionTileSize = {
        region["id"]: region["constituent_tile_size"] * u.cm for region in regions
    }
    ship_geo.UpstreamTagger.TileGridOriginX, ship_geo.UpstreamTagger.TileGridEndX = (
        bound * u.cm for bound in ubt_map["bounds"]["x"]
    )
    ship_geo.UpstreamTagger.TileGridOriginY, ship_geo.UpstreamTagger.TileGridEndY = (
        bound * u.cm for bound in ubt_map["bounds"]["y"]
    )
    # TH2D maps of ADC counts per MeV vs local hit position (mm) in a tile,
    # named adc_per_mev_<tile side in mm>mm.
    ship_geo.UpstreamTagger.ADCResponseMapFile = os.path.join(
        os.environ["FAIRSHIP"], "geometry", "UpstreamTagger_adc_response.root"
    )

    # Tile side (cm) -> thickness. A configuration read back from a file has
    # the keys as strings, and one written before TileThickness has the
    # thicknesses of the 20 and 40 mm tiles in SmallTileZ and LargeTileZ.
    ubt_geo = ship_geo.UpstreamTagger
    if "TileThickness" not in ubt_geo:
        ubt_geo.TileThickness = {2: ubt_geo.SmallTileZ, 4: ubt_geo.LargeTileZ}
    thicknesses = {float(size): thickness for size, thickness in ubt_geo.TileThickness.items()}
    for region in regions:
        thickness = thicknesses.get(float(region["constituent_tile_size"]))
        if thickness is None:
            raise ValueError(
                f"UBT region {region['id']} has {region['constituent_tile_size']} cm tiles, which have no thickness in"
                f" UpstreamTagger.TileThickness (tile sides {sorted(thicknesses)} cm)"
            )
        upstream_tagger.AddRegion(
            region["id"],
            region["x"] * u.cm,
            region["y"] * u.cm,
            region["size_x"] * u.cm,
            region["size_y"] * u.cm,
            region["constituent_tile_size"],
            thickness,
        )


def configure(run, ship_geo, geofile: str | None = None):
    """Configure the modules of the run and add them to it.

    With ``geofile``, particles are transported through the geometry stored in
    that geometry file: the modules build their geometry as usual, and a last
    module replaces it by the stored one (see geometry_from_file). ``ship_geo``
    must then be the configuration stored in the same file.
    """
    stored_yaml_configs = geometry_from_file.stored_yaml_configs(ship_geo) if geofile else {}
    # ---- for backward compatibility ----
    if not hasattr(ship_geo, "DecayVolumeMedium"):
        raise ValueError("DecayVolumeMedium is not defined, possibly old (incompatible) geometry!")
    if not hasattr(ship_geo.Bfield, "x"):
        ship_geo.Bfield.x = 3.0 * u.m
    if not hasattr(ship_geo, "cave"):
        ship_geo.cave = AttrDict(z=0 * u.cm)
        ship_geo.cave.floorHeightMuonShield = 5 * u.m
        ship_geo.cave.floorHeightTankA = 4.5 * u.m
        ship_geo.cave.floorHeightTankB = 2.0 * u.m
    if not hasattr(ship_geo, "SND"):
        ship_geo.SND = True
    if not hasattr(ship_geo.cave, "ECN3FloorY"):
        # Placing the UBT needs the ECN3 floor and side walls: use those of the
        # cavern that ShipCave builds.
        geometry_config.set_ecn3_cavern(ship_geo)
    ubt_geo = getattr(ship_geo, "UpstreamTagger", None)
    if not hasattr(ship_geo, "UpstreamTaggerScoringPlane") or not (
        hasattr(ubt_geo, "TileThickness") or hasattr(ubt_geo, "SmallTileZ")
    ):
        # A geometry from before the scintillator UBT: its UBT was a vacuum box,
        # which can no longer be built.
        if geofile:
            raise ValueError(
                f"{geofile} has the UBT of before the scintillator tiles (a vacuum box), which cannot be built"
                " any more, so it cannot be used with -g: write a new geometry file"
            )
        # Use the current UBT and scoring planes, placed from this geometry's
        # decay vessel and muon shield, so that the other detectors can be
        # used; the UBT points of such a file are not digitized (see
        # UpstreamTaggerDetector.validate_stored_geometry).
        geometry_config.set_upstream_tagger(ship_geo)

    # -----Create media-------------------------------------------------
    run.SetMaterials("media.geo")  # Materials
    # ------------------------------------------------------------------------

    # -----Create geometry----------------------------------------------
    cave = ROOT.ShipCave("Cave", "ShipCave")
    cave.SetGeometryFileName("caveWithAir.geo")
    if hasattr(ship_geo.cave, "ECN3_length"):
        cave.SetCavernDimensions(
            ship_geo.cave.TCC8_length,
            ship_geo.cave.ECN3_length,
            ship_geo.cave.stair_step_length,
            ship_geo.cave.z_transition,
        )
    cave.SetSpectrometerZ(ship_geo.z)
    detectorList.append(cave)

    TargetStation = ROOT.ShipTargetStation(
        "TargetStation",
        ship_geo.target.length,
        ship_geo.target.z,
        ship_geo.target.nS,
        ship_geo.target.HeT,
    )

    TargetStation.SetLayerPosMat(
        ship_geo.target.xy, ship_geo.target.slices_length, ship_geo.target.slices_gap, ship_geo.target.slices_material
    )
    target_version = getattr(ship_geo.target, "version", 1)
    TargetStation.SetDesign(target_version)
    if target_version >= 2:
        TargetStation.SetLastDiskDiameter(ship_geo.target.xy2)
    TargetStation.SetShieldingReferenceLength(ship_geo.target.length_fixed)
    detectorList.append(TargetStation)

    # For SND: support multiple designs
    if ship_geo.SND:
        for design in ship_geo.SND_design:
            if design == 2:
                # SND design 2 -- MTC/SiliconTarget
                configure_snd_mtc(os.path.join(os.environ["FAIRSHIP"], "geometry", "MTC_config.yaml"), ship_geo)
                configure_snd_siliconTarget(
                    os.path.join(os.environ["FAIRSHIP"], "geometry", "SiliconTarget_config.yaml"), ship_geo
                )
            elif design == 1:
                configure_snd_old(
                    os.path.join(os.environ["FAIRSHIP"], "geometry", "snd_config_old.yaml"),
                    ship_geo.UpstreamTagger.z0 - 5 * u.cm,
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
        if 2 in getattr(ship_geo, "SND_design", []):
            # The SND sits in the third-to-last and second-to-last magnets
            # (S5 and M6 in the 2026 layout), see configure_snd_mtc.
            n_magnets = ship_geo.muShield.nMagnets
            MuonShield.SetSNDSpace(
                hole=True,
                hole_dx=(ship_geo.mtc_geo.width + 5.0 * u.cm) / 2.0,
                hole_dy=(ship_geo.mtc_geo.height + 5.0 * u.cm) / 2.0,
                first_magnet=n_magnets - 3,
                last_magnet=n_magnets - 2,
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
        os.path.join(fairship, f"geometry/veto_config_{ship_geo.DecayVolumeMedium}.yaml"),
        ship_geo.decayVolume.z0,
    )

    configure_strawtubes(
        os.path.join(os.environ["FAIRSHIP"], "geometry", "strawtubes_config.yaml"),
        ship_geo,
    )

    if hasattr(ship_geo, "CaloScoringPlane"):  # absent in geometry files made before SplitCal removal
        caloScoringPlane = ROOT.CaloScoringPlane("CaloScoringPlane", ROOT.kTRUE)
        caloScoringPlane.SetZposition(ship_geo.CaloScoringPlane.z)
        caloScoringPlane.SetBoxDimensions(
            ship_geo.CaloScoringPlane.DX, ship_geo.CaloScoringPlane.DY, ship_geo.CaloScoringPlane.DZ
        )
        detectorList.append(caloScoringPlane)
    else:
        print("Warning: no CaloScoringPlane in this geometry configuration; not building it.")

    upstreamTagger = ROOT.UpstreamTagger("UpstreamTagger", ROOT.kTRUE)
    upstreamTagger.SetZposition(ship_geo.UpstreamTagger.z)
    upstreamTagger.SetBoxDimensions(
        ship_geo.UpstreamTagger.BoxX, ship_geo.UpstreamTagger.BoxY, ship_geo.UpstreamTagger.BoxZ
    )
    upstreamTagger.SetBoxCenter(ship_geo.UpstreamTagger.BoxCenterX, ship_geo.UpstreamTagger.BoxCenterY)
    configure_upstream_tagger(
        os.path.join(os.environ["FAIRSHIP"], "geometry", "UpstreamTagger_config.yaml"),
        upstreamTagger,
        ship_geo,
    )
    detectorList.append(upstreamTagger)

    sp = ship_geo.UpstreamTaggerScoringPlane
    ubt_scoring_plane = ROOT.UpstreamTaggerScoringPlane("UpstreamTaggerScoringPlane", ROOT.kTRUE)
    # Planes 1 and 2, in this order: the plane number is the point detector ID.
    for number, plane in enumerate((sp.DecayVessel, sp.MuonShield), start=1):
        ubt_scoring_plane.AddPlane(
            f"UpstreamTaggerScoringPlane{number}",
            plane.CenterX,
            plane.CenterY,
            plane.z,
            plane.X,
            plane.Y,
            sp.Z,
            [13] if plane.MuonsOnly else [],
        )
    detectorList.append(ubt_scoring_plane)

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
        ROOT.SetOwnership(fMagField, False)  # C++ FairRunSim takes ownership

    exclusionList: list[str] = []
    # exclusionList = ["strawtubes","TargetTrackers","NuTauTarget",\
    #                 "SiliconTarget","Veto","Magnet","MuonShield","TargetStation", "TimeDet", "UpstreamTagger"]

    # Heterogeneous module dict: keys are GetName() strings, values are
    # FairModule subclasses (Target/MTC/strawtubes/...). Annotate as Any to
    # match the heterogeneous detectorList type.
    detElements: dict[str, Any] = {}
    if geofile:
        geometry_from_file.check_yaml_configs(stored_yaml_configs, ship_geo)
    for x in detectorList:
        if x.GetName() in exclusionList:
            continue
        run.AddModule(x)
        ROOT.SetOwnership(x, False)  # C++ FairRunSim takes ownership
        detElements[x.GetName()] = x
    if geofile:
        # Last, so that every module has built its geometry, registered its
        # sensitive volumes and attached its fields before the swap. The
        # caller must keep the returned dict: C++ calls back into this object.
        swap = geometry_from_file.make_swap(geofile)
        run.AddModule(swap)
        ROOT.SetOwnership(swap, False)  # C++ FairRunSim takes ownership
        detElements[geometry_from_file.SWAP_NAME] = swap
    return detElements
