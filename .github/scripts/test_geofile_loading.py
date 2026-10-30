#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Test simulating on the geometry of a geometry file (run_simScript.py -g).

Builds two different geometries, then simulates again on each of them with -g
and the same seed:

* A: vacuum vessel, both SND designs, TRY_2026 muon shield. Muons from a
  particle gun cross the magnetised iron of the MTC, whose uniform field is
  not stored in geometry files and must be copied onto the stored volume.
* B: helium vessel, no SND, TRY_2026 muon shield, aluminium straw frames,
  HNL events from the test cascade file.

For each geometry, the run with -g must give the same hits as the run that
built it, must write the same geometry file, and must report no difference
between the stored and the built geometry. To show that particles are really
transported through the stored geometry and not through the one the run builds,
events on a copy of geometry B with tracking station 1 moved by 2 cm must give
other straw tube hits. A copy of geometry B without the corner ribs of the SBT
support, as from an SBT of another design, must be accepted with a warning that
names them. A copy of B made to look like a file from before the scintillator
UBT (no UBT volumes nor tile parameters) must be used with the UBT and its
scoring planes left out, and so must the geometry file written by that run. A
copy of B without the scoring-plane configuration and volumes must be used with
only the scoring planes left out, the UBT kept. A copy of A whose
configuration, as before 890cb34, gives the UBT only as Z_Position (the old SND
design of A is placed from it) must be used with the UBT and its scoring planes
left out. A copy of B without the LiScX cells of the SBT, as from an SBT with
fewer cells, must be used with a warning that names them, and record SBT points
in the other cells only. A copy of B whose SBT cells are moved one level down,
into a new assembly inside VetoLiSc, must be reported, as the SBT digitisation
(vetoHit::GetNode) would not find them. A copy of B with its LiScX cells
renamed must name the renamed cells as made of the medium of a missing
sensitive volume. With --FastMuon --FollowMuon, which make the concrete cavern
sensitive, an extra concrete box in a copy of B must be reported as passive
only. Finally, -g must be refused together with a geometry option, for a file
without a geometry, for a geometry that lacks a volume with a magnetic field (A
without the MTC iron, and B with the configuration of A), and for A without a
UBT configuration, from which its old SND design is placed.
"""

import argparse
import fnmatch
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
FAIRSHIP = os.environ.get("FAIRSHIP", os.path.dirname(os.path.dirname(HERE)))
SIM = os.path.join(FAIRSHIP, "macro", "run_simScript.py")
SEED = "42"
MOVED_NODE, MOVED_DZ = "Tr1_1", 2.0  # tracking station 1, cm
# Volumes to remove from copies of the geometry files (fnmatch patterns).
PASSIVE_VOLUMES = "CornerRib_*"  # assemblies of the SBT support (veto::GeoCornerRib), passive
SENSITIVE_VOLUMES = "LiScX_*"  # SBT cells, sensitive
FIELD_VOLUME = "MTC_iron"  # magnetised iron of the MTC, geometry A
# A geometry file from before the scintillator UBT: no UBT tiles or scoring
# planes, and a configuration without their parameters.
UBT_VOLUMES = "Upstream_Tagger,UpstreamTagger*"
UBT_CONFIG_KEYS = "UpstreamTaggerScoringPlane,UpstreamTagger.TileThickness,UpstreamTagger_geo"
# A configuration from before 890cb34 (October 2025) also has no UBT front
# face (z0) nor thickness (BoxZ), and gives the UBT centre as Z_Position,
# from which the old SND design of geometry A is placed.
OLD_UBT_CONFIG_KEYS = (
    UBT_CONFIG_KEYS + ",UpstreamTagger.z0,UpstreamTagger.BoxZ,UpstreamTagger.z>UpstreamTagger.Z_Position"
)


def muon_gun(n_events: int) -> list[str]:
    """Muons starting just upstream of the MTC of geometry A, towards +z."""
    import geometry_config

    ship_geo = geometry_config.create_config(DecayVolumeMedium="vacuums", shieldName="TRY_2026", SND=True)
    # The MTC fills the second-to-last magnet (M6), see shipDet_conf.configure_snd_mtc
    z_mtc_start = ship_geo.muShield.Entrance[-2]
    return [
        "-n", str(n_events),
        "PG", "--pID", "13", "--bothCharges",
        "--Estart", "5", "--Eend", "30",
        "--multiplePG", "--Dx", "40", "--Dy", "40", "--Vz", str(z_mtc_start - 5.0),
        "--thetaMax", "1",
    ]  # fmt: skip


def hnl_events(n_events: int) -> list[str]:
    return ["--test", "-n", str(n_events)]


def move_node(source: str, target: str, node_name: str, dz: float) -> None:
    """Copy a geometry file with one node of the top volume moved along z (run in its own process)."""
    import ROOT

    f = ROOT.TFile.Open(source)
    geometry = f.Get("FAIRGeom")
    ship_geo = str(f.Get("ShipGeo"))
    f.Close()
    node = geometry.GetTopVolume().GetNode(node_name)
    matrix = node.GetMatrix()
    matrix.SetDz(matrix.GetTranslation()[2] + dz)
    out = ROOT.TFile.Open(target, "RECREATE")
    out.WriteTObject(geometry, "FAIRGeom")
    out.WriteObject(ROOT.std.string(ship_geo), "ShipGeo")
    out.Close()


def nest_daughters(source: str, target: str, mother: str, assembly_name: str) -> None:
    """Copy a geometry file with the daughters of a volume moved one level down (run in its own process).

    The daughters of mother are placed, with the same copy numbers and
    matrices, in a new assembly assembly_name, which is placed in mother.
    Their paths then have one more element, as in a design that nests them.
    """
    import ROOT

    f = ROOT.TFile.Open(source)
    geometry = f.Get("FAIRGeom")
    ship_geo = str(f.Get("ShipGeo"))
    f.Close()
    volume = geometry.GetVolume(mother)
    if not volume or not volume.GetNdaughters():
        raise SystemExit(f"no volume {mother} with daughters in {source}")
    nodes = [volume.GetNode(i) for i in range(volume.GetNdaughters())]
    assembly = ROOT.TGeoVolumeAssembly(assembly_name)
    ROOT.SetOwnership(assembly, False)  # the geometry owns its volumes
    for node in nodes:
        assembly.AddNode(node.GetVolume(), node.GetNumber(), node.GetMatrix())
    for node in nodes:
        volume.RemoveNode(node)
    volume.AddNode(assembly, 1)
    assembly.Voxelize("")
    volume.Voxelize("")  # RemoveNode only marks the voxels for a rebuild
    print(f"moved the {len(nodes)} daughters of {mother} into {assembly_name}")
    out = ROOT.TFile.Open(target, "RECREATE")
    out.WriteTObject(geometry, "FAIRGeom")
    out.WriteObject(ROOT.std.string(ship_geo), "ShipGeo")
    out.Close()


def rename_volumes(source: str, target: str, pattern: str, prefix: str) -> None:
    """Copy a geometry file with the volumes matching pattern (fnmatch) renamed to prefix + name.

    Run in its own process. Node names are set when a volume is placed, so
    only the volume names change.
    """
    import ROOT

    f = ROOT.TFile.Open(source)
    geometry = f.Get("FAIRGeom")
    ship_geo = str(f.Get("ShipGeo"))
    f.Close()
    renamed = [volume for volume in geometry.GetListOfVolumes() if fnmatch.fnmatchcase(volume.GetName(), pattern)]
    if not renamed:
        raise SystemExit(f"no volume {pattern} in {source}")
    for volume in renamed:
        volume.SetName(prefix + volume.GetName())
    print(f"renamed {len(renamed)} volume(s) {pattern} to {prefix}...")
    out = ROOT.TFile.Open(target, "RECREATE")
    out.WriteTObject(geometry, "FAIRGeom")
    out.WriteObject(ROOT.std.string(ship_geo), "ShipGeo")
    out.Close()


def add_box(source: str, target: str, name: str, medium: str) -> None:
    """Copy a geometry file with a 10 cm box of medium added to the top volume (run in its own process)."""
    import ROOT

    f = ROOT.TFile.Open(source)
    geometry = f.Get("FAIRGeom")
    ship_geo = str(f.Get("ShipGeo"))
    f.Close()
    box = geometry.MakeBox(name, geometry.GetMedium(medium), 5.0, 5.0, 5.0)
    if not box:
        raise SystemExit(f"no medium {medium} in {source}")
    top = geometry.GetTopVolume()
    position = ROOT.TGeoTranslation(0.0, 0.0, -1000.0)  # in front of the target
    ROOT.SetOwnership(position, False)  # the node keeps it: Python must not delete it
    top.AddNode(box, 1, position)
    top.Voxelize("")
    out = ROOT.TFile.Open(target, "RECREATE")
    out.WriteTObject(geometry, "FAIRGeom")
    out.WriteObject(ROOT.std.string(ship_geo), "ShipGeo")
    out.Close()


def remove_volumes(source: str, target: str, pattern: str, config_keys: str = "") -> None:
    """Copy a geometry file without some volumes and their placements (run in its own process).

    pattern is a comma-separated list of fnmatch patterns of volume names.
    The daughter volumes of a removed volume are removed too, unless a volume
    that is kept places them, as a file written without the volume would not
    have them. config_keys is a comma-separated list of edits of the stored
    configuration (ShipGeo): a dotted key is removed, and "a.b>a.c" moves the
    value of a.b to a.c.
    """
    import json

    import ROOT

    patterns = pattern.split(",")

    f = ROOT.TFile.Open(source)
    geometry = f.Get("FAIRGeom")
    ship_geo = str(f.Get("ShipGeo"))
    f.Close()
    if config_keys:
        config = json.loads(ship_geo)

        def parent_of(key: str) -> tuple[dict, str]:
            *parents, last = key.split(".")
            node = config
            for parent in parents:
                node = node[parent]
            return node, last

        for edit in config_keys.split(","):
            source_key, _, target_key = edit.partition(">")
            node, last = parent_of(source_key)
            value = node.pop(last)
            if target_key:
                target_node, target_last = parent_of(target_key)
                target_node[target_last] = value
        ship_geo = json.dumps(config, indent=2)
        print(f"edited the stored configuration: {config_keys}")
    volumes = list(geometry.GetListOfVolumes())
    removed = {ROOT.addressof(v): v for v in volumes if any(fnmatch.fnmatchcase(v.GetName(), p) for p in patterns)}
    if not removed:
        raise SystemExit(f"no volume {pattern} in {source}")
    n_matched = len(removed)
    # Daughters of removed volumes that no kept volume places, until none is left.
    while True:
        placed_by_kept = {
            ROOT.addressof(v.GetNode(i).GetVolume())
            for v in volumes
            if ROOT.addressof(v) not in removed
            for i in range(v.GetNdaughters())
        }
        orphans = {
            ROOT.addressof(node.GetVolume()): node.GetVolume()
            for v in removed.values()
            for node in (v.GetNode(i) for i in range(v.GetNdaughters()))
            if ROOT.addressof(node.GetVolume()) not in removed
            and ROOT.addressof(node.GetVolume()) not in placed_by_kept
        }
        if not orphans:
            break
        removed.update(orphans)
    n_nodes = 0
    for mother in volumes:
        if ROOT.addressof(mother) in removed:
            continue  # its placements go with it
        nodes = [mother.GetNode(i) for i in range(mother.GetNdaughters())]
        gone = [node for node in nodes if ROOT.addressof(node.GetVolume()) in removed]
        for node in gone:
            mother.RemoveNode(node)
        if gone and mother.GetNdaughters():
            mother.Voxelize("")  # RemoveNode only marks the voxels for a rebuild
        n_nodes += len(gone)
    volume_list = geometry.GetListOfVolumes()
    for volume in removed.values():
        volume_list.Remove(volume)
    # The name lookup of a geometry read back is built from this list, which
    # must have no empty slots, and a volume's number is its index in it.
    volume_list.Compress()
    for i, volume in enumerate(volume_list):
        volume.SetNumber(i)
    print(
        f"removed {n_matched} volume(s) {pattern}, {len(removed) - n_matched} daughter volume(s) placed only in"
        f" them, and {n_nodes} placement(s) of them"
    )
    out = ROOT.TFile.Open(target, "RECREATE")
    out.WriteTObject(geometry, "FAIRGeom")
    out.WriteObject(ROOT.std.string(ship_geo), "ShipGeo")
    out.Close()


def replace_config(source: str, target: str, config_from: str) -> None:
    """Copy a geometry file with the configuration (ShipGeo) of another one."""
    import ROOT

    shutil.copy(source, target)
    with ROOT.TFile.Open(config_from) as f:
        ship_geo = str(f.Get("ShipGeo"))
    with ROOT.TFile.Open(target, "UPDATE") as f:
        f.Delete("ShipGeo;*")
        f.WriteObject(ROOT.std.string(ship_geo), "ShipGeo")


class Runner:
    def __init__(self, workdir: str):
        self.workdir = workdir
        self.failures: list[str] = []
        self.timings: dict[str, float] = {}

    def path(self, kind: str, tag: str) -> str:
        return os.path.join(self.workdir, f"{kind}_{tag}.root")

    def log(self, tag: str) -> str:
        return os.path.join(self.workdir, f"{tag}.log")

    def simulate(self, tag: str, geometry: list[str], generator: list[str]) -> bool:
        """Run run_simScript.py; the generator options come last (they may hold a subcommand)."""
        cmd = [sys.executable, SIM, "--seed", SEED, "--reproducible", "-o", self.workdir, "--tag", tag]
        cmd += geometry + generator
        print(f"\n=== {tag}: {' '.join(cmd[1:])}", flush=True)
        start = time.monotonic()
        with open(self.log(tag), "w") as log:
            rc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT).returncode
        self.timings[tag] = time.monotonic() - start
        if rc != 0:
            self.fail(f"{tag}: run_simScript.py failed with exit code {rc}, see {self.log(tag)}")
            with open(self.log(tag)) as log:
                print("".join(log.readlines()[-40:]))
            return False
        print(f"{tag}: done in {self.timings[tag]:.0f} s")
        return True

    def check(self, description: str, script: str, *args: str) -> None:
        print(f"\n--- {description}", flush=True)
        rc = subprocess.run([sys.executable, os.path.join(HERE, script), *args]).returncode
        if rc != 0:
            self.fail(description)

    def check_log(self, description: str, tag: str, expected: str | list[str]) -> None:
        """The log of tag must have a line with expected, or with every string in it."""
        print(f"\n--- {description}", flush=True)
        parts = [expected] if isinstance(expected, str) else expected
        with open(self.log(tag)) as log:
            lines = [line.strip() for line in log if all(part in line for part in parts)]
        if lines:
            print(f"OK: {lines[-1][:500]}")
        else:
            self.fail(f"{description}: no line with {' and '.join(repr(p) for p in parts)} in {self.log(tag)}")

    def check_log_absent(self, description: str, tag: str, unexpected: str) -> None:
        print(f"\n--- {description}", flush=True)
        with open(self.log(tag)) as log:
            lines = [line.strip() for line in log if unexpected in line]
        if lines:
            self.fail(f"{description}: {lines[0][:300]}")
        else:
            print(f"OK: no line with '{unexpected}'")

    def check_refused(self, description: str, args: list[str], expected: str) -> None:
        """run_simScript.py must stop with an error mentioning `expected`."""
        print(f"\n--- {description}", flush=True)
        result = subprocess.run([sys.executable, SIM, *args], capture_output=True, text=True)
        output = result.stdout + result.stderr
        if result.returncode != 0 and expected in output:
            line = next(line for line in output.splitlines() if expected in line)
            print(f"OK: refused: {line.strip()[:300]}")
        else:
            self.fail(f"{description} (exit code {result.returncode}, output: {output.strip()[-300:]})")

    def copy_without(self, source: str, tag: str, pattern: str, config_keys: str = "") -> str | None:
        """Copy of a geometry file without some volumes (see remove_volumes), None if it could not be written."""
        target = self.path("geo", tag)
        print(f"\n--- copy of {source} without the volumes {pattern}: {target}", flush=True)
        script = os.path.abspath(__file__)
        cmd = [sys.executable, script, "--remove-volumes", source, target, pattern, config_keys]
        rc = subprocess.run(cmd).returncode
        if rc != 0:
            self.fail(f"could not write {target}")
            return None
        return target

    def fail(self, message: str) -> None:
        print(f"FAILED: {message}", flush=True)
        self.failures.append(message)


def main() -> int:
    if len(sys.argv) == 6 and sys.argv[1] == "--move-node":
        move_node(sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5]))
        return 0
    if len(sys.argv) == 6 and sys.argv[1] == "--rename-volumes":
        rename_volumes(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
        return 0
    if len(sys.argv) == 6 and sys.argv[1] == "--add-box":
        add_box(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
        return 0
    if len(sys.argv) == 6 and sys.argv[1] == "--nest-daughters":
        nest_daughters(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
        return 0
    if len(sys.argv) == 6 and sys.argv[1] == "--remove-volumes":
        remove_volumes(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
        return 0
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-n", "--nEvents", type=int, default=20, help="events per run (default 20)")
    parser.add_argument("-w", "--workdir", default="geofile-loading-test", help="directory for the output files")
    args = parser.parse_args()

    os.makedirs(args.workdir, exist_ok=True)
    r = Runner(args.workdir)
    geometries = {
        "A": (["--vacuums", "--SND", "--SND_design", "all", "--shieldName", "TRY_2026"], muon_gun(args.nEvents)),
        "B": (["--helium", "--shieldName", "TRY_2026", "--strawDesign", "4"], hnl_events(args.nEvents)),
    }

    for name, (geometry, generator) in geometries.items():
        built, loaded = f"{name}_build", f"{name}_load"
        if not r.simulate(built, geometry, generator):
            continue
        if not r.simulate(loaded, ["-g", r.path("geo", built)], generator):
            continue
        r.check(
            f"{name}: same hits with -g",
            "compare_sim_hits.py",
            r.path("sim", built),
            r.path("sim", loaded),
        )
        r.check(
            f"{name}: same geometry written by the run with -g",
            "compare_geofiles.py",
            r.path("geo", built),
            r.path("geo", loaded),
        )
        r.check_log_absent(f"{name}: no geometry difference reported with -g", loaded, "WARNING in GeometrySwap")

    a_built, b_built = r.path("geo", "A_build"), r.path("geo", "B_build")
    if os.path.exists(r.path("sim", "A_load")):
        r.check_log(
            "A: the field of the MTC iron was copied onto the stored geometry",
            "A_load",
            "magnetic fields of volumes copied for: MTC_iron",
        )
        import ROOT

        with ROOT.TFile.Open(r.path("sim", "A_build")) as f:
            n_mtc = sum(len(event.MTCDetPoint) for event in f["cbmsim"])
        print(f"A: {n_mtc} MTC points from the muon gun")
        if n_mtc == 0:
            r.fail("A: no MTC points, so the muons do not test the MTC field")

    if os.path.exists(a_built) and os.path.exists(b_built):
        r.check("the two geometries differ", "compare_geofiles.py", a_built, b_built, "--expect-different")

    if os.path.exists(b_built):
        moved = r.path("geo", "B_moved")
        print(f"\n--- copy of geometry B with {MOVED_NODE} moved by {MOVED_DZ} cm in z: {moved}", flush=True)
        rc = subprocess.run(
            [sys.executable, os.path.abspath(__file__), "--move-node", b_built, moved, MOVED_NODE, str(MOVED_DZ)]
        ).returncode
        if rc != 0:
            r.fail(f"could not write {moved}")
        elif r.simulate("B_moved_load", ["-g", moved], geometries["B"][1]):
            r.check(
                "particles go through the stored geometry: the moved station gives other straw hits",
                "compare_sim_hits.py",
                r.path("sim", "B_build"),
                r.path("sim", "B_moved_load"),
                "--expect-different",
                "strawtubesPoint",
            )
        # Like an SBT of another design: support missing, sensitive cells unchanged.
        no_ribs = r.copy_without(b_built, "B_no_ribs", PASSIVE_VOLUMES)
        if no_ribs and r.simulate("B_no_ribs_load", ["-g", no_ribs], geometries["B"][1]):
            r.check_log(
                "a geometry without passive volumes the code builds is used, with a warning that names them",
                "B_no_ribs_load",
                ["passive volume(s) that the current code builds", PASSIVE_VOLUMES.rstrip("*")],
            )
        # A detector that the current code cannot build from the stored configuration is left out.
        old_ubt = r.copy_without(b_built, "B_old_ubt", UBT_VOLUMES, UBT_CONFIG_KEYS)
        if old_ubt and r.simulate("B_old_ubt_load", ["-g", old_ubt], geometries["B"][1]):
            r.check_log(
                "the UBT of a geometry from before the scintillator tiles is left out, with a warning",
                "B_old_ubt_load",
                "UpstreamTagger, UpstreamTaggerScoringPlane left out of this run",
            )
            import ROOT

            with ROOT.TFile.Open(r.path("sim", "B_old_ubt_load")) as f:
                tree = f["cbmsim"]
                ubt_branches = [b for b in ("UpstreamTaggerPoint", "UpstreamTaggerScoringPoint") if tree.GetBranch(b)]
            if ubt_branches:
                r.fail(f"B_old_ubt_load: the left-out UBT still has branches {ubt_branches}")
            # The run keeps the stored configuration, so its own geometry file can be used with -g too.
            if r.simulate("B_old_ubt_reload", ["-g", r.path("geo", "B_old_ubt_load")], hnl_events(1)):
                r.check_log(
                    "the geometry file of that run is used with -g again, with the UBT left out again",
                    "B_old_ubt_reload",
                    "UpstreamTagger, UpstreamTaggerScoringPlane left out of this run",
                )

    if os.path.exists(a_built):
        r.check_refused(
            "-g is refused together with a geometry option",
            ["-g", a_built, "--vacuums", "-o", args.workdir, "--tag", "refused", "--dry-run"],
            "cannot be combined with geometry options",
        )
        r.check_refused(
            "-g is refused for a file without a geometry",
            ["-g", r.path("sim", "A_build"), "-o", args.workdir, "--tag", "refused", "--dry-run"],
            "has no geometry FAIRGeom",
        )
    if os.path.exists(a_built) and os.path.exists(b_built):
        mixed = r.path("geo", "B_with_config_A")
        replace_config(b_built, mixed, a_built)
        r.check_refused(
            "-g is refused when the stored geometry lacks the MTC iron of its configuration (B, configuration A)",
            ["-g", mixed, "-o", args.workdir, "--tag", "refused", "--dry-run", *hnl_events(1)],
            f"attaches a magnetic field ({FIELD_VOLUME})",
        )
    if os.path.exists(b_built):
        # Like an SBT design with fewer cells: the missing cells record no hits, the others as before.
        no_cells = r.copy_without(b_built, "B_no_cells", SENSITIVE_VOLUMES)
        if no_cells and r.simulate("B_no_cells_load", ["-g", no_cells], geometries["B"][1]):
            r.check_log(
                "a geometry without some sensitive SBT cells is used, with a warning that names them",
                "B_no_cells_load",
                ["that the current code registers as sensitive", SENSITIVE_VOLUMES.rstrip("*")],
            )
            import ROOT

            with ROOT.TFile.Open(r.path("sim", "B_no_cells_load")) as f:
                # Detector ID = ShapeType * 100000 + ...; LiScX cells have ShapeType 1 (veto::liscId).
                shape_types = [point.GetDetectorID() // 100000 for event in f["cbmsim"] for point in event.vetoPoint]
            print(f"B_no_cells_load: {len(shape_types)} SBT points, {shape_types.count(1)} of them in LiScX cells")
            if not shape_types or 1 in shape_types:
                r.fail("B_no_cells_load: expected SBT points, none of them in the removed LiScX cells")
        # Like an SBT design that nests its cells differently: the SBT digitisation would not find them.
        nested = r.path("geo", "B_nested_sbt_cells")
        rc = subprocess.run(
            [sys.executable, os.path.abspath(__file__), "--nest-daughters", b_built, nested, "VetoLiSc", "VetoCells"]
        ).returncode
        if rc != 0:
            r.fail(f"could not write {nested}")
        elif r.simulate("B_nested_sbt_cells_load", ["-g", nested, "--dry-run"], hnl_events(1)):
            r.check_log(
                "SBT cells one level deeper are reported, as vetoHit::GetNode does not find them",
                "B_nested_sbt_cells_load",
                ["where the SBT digitisation (vetoHit::GetNode) does not find them", "/VetoCells_1/LiSc"],
            )
        # Only the scoring planes cannot be built: the UBT itself is kept.
        no_planes = r.copy_without(
            b_built, "B_no_ubt_planes", "UpstreamTaggerScoringPlane*", "UpstreamTaggerScoringPlane"
        )
        if no_planes and r.simulate("B_no_ubt_planes_load", ["-g", no_planes, "--dry-run"], hnl_events(1)):
            r.check_log(
                "without a scoring-plane configuration, only the UBT scoring planes are left out",
                "B_no_ubt_planes_load",
                ["no configuration of the UBT scoring planes", "UpstreamTaggerScoringPlane left out of this run"],
            )
            r.check_log_absent(
                "the UBT is kept when only its scoring-plane configuration is missing",
                "B_no_ubt_planes_load",
                "UpstreamTagger, UpstreamTaggerScoringPlane left out",
            )
        # Like an SBT design that renamed its cells: the renamed cells are of the medium of the missing ones.
        renamed = r.path("geo", "B_renamed_cells")
        rc = subprocess.run(
            [sys.executable, os.path.abspath(__file__), "--rename-volumes", b_built, renamed, SENSITIVE_VOLUMES, "New"]
        ).returncode
        if rc != 0:
            r.fail(f"could not write {renamed}")
        elif r.simulate("B_renamed_cells_load", ["-g", renamed, "--dry-run"], hnl_events(1)):
            r.check_log(
                "renamed sensitive cells are named as made of the medium of a missing sensitive volume",
                "B_renamed_cells_load",
                [
                    "made of the medium of a missing sensitive volume and record no hits",
                    "New" + SENSITIVE_VOLUMES.rstrip("*"),
                ],
            )
        # --FastMuon --FollowMuon make the concrete cavern sensitive, but no sensitive volume is missing.
        concrete = r.path("geo", "B_extra_concrete")
        rc = subprocess.run(
            [sys.executable, os.path.abspath(__file__), "--add-box", b_built, concrete, "ExtraConcrete", "Concrete"]
        ).returncode
        muon_back = [
            "--MuonBack", "--FastMuon", "--FollowMuon",
            "-f", os.path.join(FAIRSHIP, "tests", "data", "muonback_smoke.root"), "-n", "1",
        ]  # fmt: skip
        if rc != 0:
            r.fail(f"could not write {concrete}")
        elif r.simulate("B_extra_concrete_load", ["-g", concrete, "--dry-run"], muon_back):
            r.check_log(
                "an extra concrete volume is reported with --FollowMuon",
                "B_extra_concrete_load",
                ["volume(s) that the current code does not build (ExtraConcrete)", "passive in this run"],
            )
            r.check_log_absent(
                "an extra concrete volume is not taken for a detector element with --FollowMuon",
                "B_extra_concrete_load",
                "record no hits (ExtraConcrete",
            )
    if os.path.exists(a_built):
        no_iron = r.copy_without(a_built, "A_no_iron", FIELD_VOLUME)
        if no_iron:
            r.check_refused(
                "-g is refused when the stored geometry lacks a volume with a magnetic field",
                ["-g", no_iron, "-o", args.workdir, "--tag", "refused", "--dry-run", *hnl_events(1)],
                f"attaches a magnetic field ({FIELD_VOLUME})",
            )
        # The old SND design is placed from Z_Position and a 16 cm UBT box when the configuration has no z0 or BoxZ.
        old_config = r.copy_without(a_built, "A_old_ubt_config", UBT_VOLUMES, OLD_UBT_CONFIG_KEYS)
        if old_config and r.simulate("A_old_ubt_config_load", ["-g", old_config, "--dry-run"], hnl_events(1)):
            r.check_log(
                "a configuration with only UpstreamTagger.Z_Position is used with -g, with the UBT left out",
                "A_old_ubt_config_load",
                "UpstreamTagger, UpstreamTaggerScoringPlane left out of this run",
            )
        # The old SND design is placed from the UBT, so a configuration without one is refused.
        no_ubt = r.copy_without(a_built, "A_no_ubt_config", UBT_VOLUMES, "UpstreamTagger,UpstreamTagger_geo")
        if no_ubt:
            r.check_refused(
                "-g is refused for SND design 1 without a UBT configuration",
                ["-g", no_ubt, "-o", args.workdir, "--tag", "refused", "--dry-run", *hnl_events(1)],
                "has SND design 1 but no UBT configuration (UpstreamTagger)",
            )

    print("\n=== Run times (s)")
    for tag, seconds in r.timings.items():
        print(f"{tag:>14}: {seconds:7.1f}")
    if r.failures:
        print(f"\n{len(r.failures)} FAILED:")
        for failure in r.failures:
            print(f"  - {failure}")
        return 1
    print("\nAll geometry loading checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
