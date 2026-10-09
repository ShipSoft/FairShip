#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Filter prepareEvents.py output, retaining selected DIS interactions."""

import argparse
import logging
import math
import os
import time
from pathlib import Path
from types import SimpleNamespace

import ROOT

ROOT.gROOT.SetBatch(True)


def load_spectrometer_field(geometry_file, field_map=None, field_z=None):
    """Use ShipReco's non-VMC field setup, restricted to the SST map.

    Return the field maker as well as the map: the maker owns its fields.
    """
    import geomGeant4
    from ShipGeoConfig import load_from_root_file

    if field_map is None or field_z is None:
        with ROOT.TFile.Open(geometry_file) as source:
            ship_geo = load_from_root_file(source, "ShipGeo")
        if field_map is None:
            # Geometry map paths follow ShipFieldMaker's VMCWORKDIR convention.
            field_map = Path(os.environ["VMCWORKDIR"]) / ship_geo.Bfield.fieldMap
        if field_z is None:
            field_z = float(ship_geo.Bfield.z)
    field_path = Path(field_map).expanduser().resolve()
    if not field_path.is_file():
        raise ValueError(f"Field map does not exist: {field_path}")
    if not math.isfinite(field_z):
        raise ValueError("Field z offset must be finite")
    # ShipFieldMaker prefixes even absolute names with VMCWORKDIR, so pass a
    # relative path. No geometry or muon-shield configuration is modified.
    field_config = SimpleNamespace(
        Bfield=SimpleNamespace(fieldMap=os.path.relpath(field_path, os.environ["VMCWORKDIR"]), z=field_z),
        muShield=SimpleNamespace(WithConstField=True),
    )
    field_maker = geomGeant4.addVMCFields(field_config, "", False, withVirtualMC=False)
    field = field_maker.getField("MainSpecMap")
    if not field or not isinstance(field, ROOT.ShipBFieldMap):
        raise RuntimeError("MainSpecMap is not a ShipBFieldMap")
    return field_maker, field, field_path


def load_muon_shield_field(field_maker, geometry_file, field_map=None, field_z=None):
    """Load the shield map with the same placement and symmetry as geomGeant4.

    geomGeant4.addVMCFields uses the map only when muShield.WithConstField is
    false; otherwise the shield has constant per-volume fields, which the
    propagator does not model. Refuse that case instead of silently using a
    map the simulation never used.
    """
    from ShipGeoConfig import load_from_root_file

    with ROOT.TFile.Open(geometry_file) as source:
        ship_geo = load_from_root_file(source, "ShipGeo")
    if getattr(getattr(ship_geo, "muShield", None), "WithConstField", False):
        raise ValueError(
            "the geometry uses constant muon shield fields (muShield.WithConstField), "
            "which the field-map propagator cannot reproduce"
        )
    if field_map is None or field_z is None:
        if field_map is None:
            field_map = Path(os.environ["VMCWORKDIR"]) / "files" / f"{ship_geo.shieldName}.root"
        if field_z is None:
            field_z = float(ship_geo.muShield.Entrance[0])
    field_path = Path(field_map).expanduser().resolve()
    if not field_path.is_file():
        raise ValueError(f"Muon shield field map does not exist: {field_path}")
    if not math.isfinite(field_z):
        raise ValueError("Muon shield field z offset must be finite")
    field_maker.defineFieldMap(
        "muonShieldField",
        os.path.relpath(field_path, os.environ["VMCWORKDIR"]),
        ROOT.TVector3(0.0, 0.0, field_z),
        ROOT.TVector3(),
        True,
    )
    field = field_maker.getField("muonShieldField")
    if not field or not isinstance(field, ROOT.ShipBFieldMap):
        raise RuntimeError("muonShieldField is not a ShipBFieldMap")
    return field, field_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-f",
        "--inputfile",
        nargs="+",
        required=True,
        help="Input file(s) or directories to search recursively for .root files",
    )
    parser.add_argument(
        "--ignore-input-containing",
        action="append",
        default=None,
        metavar="STRING",
        help="Ignore discovered input files whose filename contains STRING (repeatable; default: filtered)",
    )
    parser.add_argument("-o", "--outputfile", required=True, help="New ROOT file (must not exist)")
    parser.add_argument(
        "-n",
        "--n_events",
        type=int,
        default=-1,
        help="Number of input events to process (-1: all remaining events; default: -1)",
    )
    parser.add_argument(
        "-s", "--start_event", type=int, default=0, help="First input event to process (zero-based; default: 0)"
    )
    parser.add_argument(
        "--filter-option",
        type=int,
        choices=(0, 1, 2),
        default=0,
        help="0: charged hits at Tr1; 1: two charged tracks at tracking and timing planes; "
        "2: any non-neutrino daughter entering the Tr1-to-calorimeter volume",
    )
    parser.add_argument(
        "--detailed-histograms",
        action="store_true",
        help="Also store redundant projections and per-cell z efficiency inputs",
    )
    parser.add_argument("--min-charged", type=int, default=2, help="Minimum charged daughters for filter option 0")
    parser.add_argument("--exclude-muons", action="store_true")
    parser.add_argument("-g", "--geoFile", help="ROOT geometry containing the first SST station (Tr1)")
    parser.add_argument(
        "--field-map", "--field_map", dest="field_map", help="Override geometry ShipGeo.Bfield.fieldMap"
    )
    parser.add_argument("--detector-z", type=float, help="Acceptance plane z in cm (default: Tr1 centre)")
    parser.add_argument("--field-z", type=float, help="Map z offset in cm (default: geometry ShipGeo.Bfield.z)")
    parser.add_argument("--muon-shield-field-map", help="Override files/<ShipGeo.shieldName>.root for the shield")
    parser.add_argument(
        "--muon-shield-field-z", type=float, help="Shield map z offset in cm (default: ShipGeo.muShield.Entrance[0])"
    )
    parser.add_argument(
        "--filter-efficiency-x-bounds",
        type=float,
        nargs=2,
        metavar=("MIN", "MAX"),
        default=(-200.0, 200.0),
        help="X-axis bounds in cm (default: -200 200)",
    )
    parser.add_argument(
        "--filter-efficiency-x-bins", type=int, default=5, help="Odd number of X bins, centred on zero (default: 5)"
    )
    parser.add_argument(
        "--filter-efficiency-y-bounds",
        type=float,
        nargs=2,
        metavar=("MIN", "MAX"),
        default=(-300.0, 300.0),
        help="Y-axis bounds in cm (default: -300 300)",
    )
    parser.add_argument(
        "--filter-efficiency-y-bins", type=int, default=5, help="Odd number of Y bins, centred on zero (default: 5)"
    )
    parser.add_argument(
        "--filter-efficiency-z-bounds",
        type=float,
        nargs=2,
        metavar=("MIN", "MAX"),
        default=(2500.0, 9500.0),
        help="Z-axis bounds in cm (default: 2500 9500)",
    )
    parser.add_argument("--filter-efficiency-z-bins", type=int, default=70, help="Number of Z bins (default: 70)")
    parser.add_argument("--no-detector-acceptance", action="store_true", help="Use charged multiplicity alone")
    parser.add_argument(
        "--pythia-decays", action="store_true", help="Decay daughters upstream of Tr1 with Pythia8 before filtering"
    )
    parser.add_argument(
        "--pythia-decay-seed", type=int, default=0, help="Pythia8 daughter-decay random seed (0: time-based, default)"
    )
    parser.add_argument(
        "--debug",
        help="Control FairLogger verbosity: 0=info (default), 1=+debug, 2=+debug1, 3=+debug2",
        default=0,
        type=int,
        choices=range(0, 4),
    )
    args = parser.parse_args()
    if args.min_charged < 0 or args.start_event < 0 or args.n_events < -1:
        parser.error("Counts must be nonnegative, except -n -1 for all entries")
    if args.ignore_input_containing is None:
        args.ignore_input_containing = ["filtered"]
    if any(not pattern for pattern in args.ignore_input_containing):
        parser.error("--ignore-input-containing must not be empty")
    if not 0 <= args.pythia_decay_seed <= 900000000:
        parser.error("--pythia-decay-seed must be in [0, 900000000]")
    for axis, bounds, bins, centered in (
        ("x", args.filter_efficiency_x_bounds, args.filter_efficiency_x_bins, True),
        ("y", args.filter_efficiency_y_bounds, args.filter_efficiency_y_bins, True),
        ("z", args.filter_efficiency_z_bounds, args.filter_efficiency_z_bins, False),
    ):
        if not all(math.isfinite(value) for value in bounds) or bounds[0] >= bounds[1] or bins <= 0:
            parser.error(f"Filter-efficiency {axis} axis requires finite increasing bounds and positive bins")
        if centered and (bins % 2 == 0 or not math.isclose(bounds[0], -bounds[1], rel_tol=1.0e-12, abs_tol=1.0e-12)):
            parser.error(f"Filter-efficiency {axis} axis requires symmetric bounds and an odd bin count to centre zero")
    if (not args.no_detector_acceptance or args.pythia_decays) and not args.geoFile:
        parser.error("Detector acceptance requires -g/--geoFile")
    if args.pythia_decays and args.no_detector_acceptance:
        parser.error("--pythia-decays requires detector acceptance to determine the Tr1 position")
    if args.filter_option != 0 and args.no_detector_acceptance:
        parser.error("Filter options 1 and 2 require detector acceptance")
    if args.filter_option != 0 and args.detector_z is not None:
        parser.error("--detector-z applies only to filter option 0; options 1 and 2 use geometry extents")
    for value in (args.detector_z, args.field_z, args.muon_shield_field_z):
        if value is not None and not math.isfinite(value):
            parser.error("Detector and field z positions must be finite")
    auxiliary_paths = {
        Path(p).expanduser().resolve() for p in (args.geoFile, args.field_map, args.muon_shield_field_map) if p
    }
    # Keep these owners alive until filtering finishes, as in ShipReco.py.
    _field_maker = field = shield_field = geometry = None
    if not args.no_detector_acceptance:
        geometry_path = str(Path(args.geoFile).expanduser().resolve())
        if not Path(geometry_path).is_file():
            parser.error(f"Geometry does not exist: {geometry_path}")
        geometry = ROOT.TGeoManager.Import(geometry_path)
        if not geometry:
            parser.error(f"Cannot load geometry: {geometry_path}")
        try:
            _field_maker, field, field_path = load_spectrometer_field(geometry_path, args.field_map, args.field_z)
        except (AttributeError, KeyError, ValueError, RuntimeError, OSError) as error:
            parser.error(
                f"Cannot configure SST field (use --field-map/--field-z to override geometry settings): {error}"
            )
        auxiliary_paths.add(field_path)
        if geometry.GetVolume("MuonShieldArea") or args.muon_shield_field_map or args.muon_shield_field_z is not None:
            try:
                shield_field, shield_path = load_muon_shield_field(
                    _field_maker,
                    geometry_path,
                    args.muon_shield_field_map,
                    args.muon_shield_field_z,
                )
            except (AttributeError, IndexError, KeyError, ValueError, RuntimeError, OSError) as error:
                parser.error(
                    f"Cannot configure muon shield field (use --muon-shield-field-map/"
                    f"--muon-shield-field-z to override geometry settings): {error}"
                )
            auxiliary_paths.add(shield_path)
    file_names = []
    seen = set()
    output_path = Path(args.outputfile).resolve()
    for name in args.inputfile:
        path = Path(name).expanduser()
        if path.is_dir():
            candidates = sorted(
                p
                for p in path.rglob("*.root")
                if p.is_file() and not any(pattern in p.name for pattern in args.ignore_input_containing)
            )
        elif path.is_file():
            candidates = [path]
        else:
            parser.error(f"Input does not exist or is not a file/directory: {name}")
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved in auxiliary_paths:
                continue
            if resolved == output_path:
                parser.error(f"Output file is also an input: {candidate}")
            if resolved not in seen:
                seen.add(resolved)
                file_names.append(str(candidate))
    if not file_names:
        parser.error("No ROOT input files found")
    print(f"Found {len(file_names)} input file(s): ", file_names, flush=True)

    # Measure library initialization and filtering, excluding input discovery.
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    if ROOT.gSystem.Load("libShipMuDIS.so") < 0:
        raise RuntimeError("Cannot load libShipMuDIS.so")
    if args.debug == 0:
        ROOT.gErrorIgnoreLevel = ROOT.kWarning
    ROOT.gInterpreter.ProcessLine('#include "FairLogger.h"')
    if args.debug == 0:
        ROOT.gInterpreter.ProcessLine('fair::Logger::SetConsoleSeverity("info");')
        logging.basicConfig(level=logging.INFO)
    elif args.debug == 1:
        ROOT.gInterpreter.ProcessLine('fair::Logger::SetConsoleSeverity("debug");')
        logging.basicConfig(level=logging.DEBUG)
    elif args.debug == 2:
        ROOT.gInterpreter.ProcessLine('fair::Logger::SetConsoleSeverity("debug1");')
    else:
        ROOT.gInterpreter.ProcessLine('fair::Logger::SetConsoleSeverity("debug2");')
    selection = ROOT.MuDISFilter()
    selection.init(args.n_events, args.start_event)
    selection.SetFilterOption(args.filter_option)
    selection.SetDetailedHistograms(args.detailed_histograms)
    selection.SetMinChargedDaughters(args.min_charged)
    selection.SetIncludeMuons(not args.exclude_muons)
    selection.SetFilterEfficiencyBinning(
        args.filter_efficiency_x_bounds[0],
        args.filter_efficiency_x_bounds[1],
        args.filter_efficiency_x_bins,
        args.filter_efficiency_y_bounds[0],
        args.filter_efficiency_y_bounds[1],
        args.filter_efficiency_y_bins,
        args.filter_efficiency_z_bounds[0],
        args.filter_efficiency_z_bounds[1],
        args.filter_efficiency_z_bins,
    )
    if args.no_detector_acceptance:
        selection.SetUseDetectorAcceptance(False)
    else:
        assert geometry is not None  # Loaded above when detector acceptance is enabled.
        detector_z = args.detector_z if args.detector_z is not None else float("nan")
        selection.SetDetectorAcceptance(field, geometry, detector_z, shield_field or ROOT.nullptr)
        if args.filter_option == 0:
            print(f"Detector acceptance: |x| <= 200 cm, |y| <= 300 cm at z = {selection.GetDetectorZ():g} cm")
        elif args.filter_option == 1:
            print("Detector acceptance: filter option 1, individual tracking/TD geometry bounds")
        else:
            print("Detector acceptance: filter option 2, |x| <= 200 cm, |y| <= 300 cm")
    if args.pythia_decays:
        selection.SetPythiaDecaySeed(args.pythia_decay_seed)
        selection.SetUsePythiaDecays(True)
    inputs = ROOT.std.vector("string")()
    for name in file_names:
        inputs.push_back(name)
    selection.process_file(inputs, args.outputfile)
    wall_seconds = time.perf_counter() - wall_start
    cpu_seconds = time.process_time() - cpu_start
    cpu_percent = 100.0 * cpu_seconds / wall_seconds if wall_seconds else 0.0
    print(
        f"Performance (initialization + filtering): wall time {wall_seconds:.3f} s, "
        f"CPU time {cpu_seconds:.3f} s, average CPU utilization {cpu_percent:.1f}%"
    )


if __name__ == "__main__":
    main()
