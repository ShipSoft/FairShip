#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Test simulating on the geometry of a geometry file (run_simScript.py -g).

Builds two different geometries, then simulates again on each of them with -g
and the same seed:

* A: vacuum vessel, both SND designs, TRY_2026 muon shield. Muons from a
  particle gun cross the magnetised iron of the MTC, whose uniform field is
  not stored in geometry files and must be copied onto the stored volume.
* B: helium vessel, no SND, TRY_2025 muon shield, aluminium straw frames,
  HNL events from the test cascade file.

For each geometry, the run with -g must give the same hits as the run that
built it, must write the same geometry file, and must report no difference
between the stored and the built geometry. To show that particles are
really transported through the stored geometry and not through the one the
run builds, events on a copy of geometry B with tracking station 1 moved by
2 cm must give other straw tube hits. A copy of geometry B without the corner
ribs of the SBT support, as from an SBT of another design, must be accepted
with a warning that names them. A copy of B made to look like a file from
before the scintillator UBT (no UBT volumes nor tile parameters) must be used
with the UBT and its scoring planes left out, and so must the geometry file
written by that run. Finally, -g must be refused together with a
geometry option, for a file without a geometry, for a geometry that lacks
sensitive volumes the code builds from the stored configuration (geometry B
with the configuration of A, and B without the LiScX cells of the SBT), and for
a geometry that lacks a volume with a magnetic field (A without the MTC iron).
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


def remove_volumes(source: str, target: str, pattern: str, config_keys: str = "") -> None:
    """Copy a geometry file without some volumes and their placements (run in its own process).

    pattern is a comma-separated list of fnmatch patterns of volume names;
    config_keys a comma-separated list of dotted keys removed from the stored
    configuration (ShipGeo).
    """
    import json

    import ROOT

    patterns = pattern.split(",")

    def matches(name: str) -> bool:
        return any(fnmatch.fnmatchcase(name, p) for p in patterns)

    f = ROOT.TFile.Open(source)
    geometry = f.Get("FAIRGeom")
    ship_geo = str(f.Get("ShipGeo"))
    f.Close()
    if config_keys:
        config = json.loads(ship_geo)
        for key in config_keys.split(","):
            *parents, last = key.split(".")
            node = config
            for parent in parents:
                node = node[parent]
            del node[last]
        ship_geo = json.dumps(config, indent=2)
        print(f"removed {config_keys} from the stored configuration")
    volumes = geometry.GetListOfVolumes()
    removed = [volume for volume in volumes if matches(volume.GetName())]
    if not removed:
        raise SystemExit(f"no volume {pattern} in {source}")
    n_nodes = 0
    for mother in volumes:
        nodes = [mother.GetNode(i) for i in range(mother.GetNdaughters())]
        gone = [node for node in nodes if matches(node.GetVolume().GetName())]
        for node in gone:
            mother.RemoveNode(node)
        if gone and mother.GetNdaughters():
            mother.Voxelize("")  # RemoveNode only marks the voxels for a rebuild
        n_nodes += len(gone)
    for volume in removed:
        volumes.Remove(volume)
    # The name lookup of a geometry read back is built from this list, which
    # must have no empty slots, and a volume's number is its index in it.
    volumes.Compress()
    for i, volume in enumerate(volumes):
        volume.SetNumber(i)
    print(f"removed {len(removed)} volume(s) {pattern} and {n_nodes} placement(s) of them")
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

    def check_log(self, description: str, tag: str, expected: str) -> None:
        print(f"\n--- {description}", flush=True)
        with open(self.log(tag)) as log:
            lines = [line.strip() for line in log if expected in line]
        if lines:
            print(f"OK: {lines[-1]}")
        else:
            self.fail(f"{description}: no line with '{expected}' in {self.log(tag)}")

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
        "B": (["--helium", "--shieldName", "TRY_2025", "--strawDesign", "4"], hnl_events(args.nEvents)),
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
                f"passive volume(s) that the current code builds ({PASSIVE_VOLUMES[:-1]}",
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
            "-g is refused when the stored geometry lacks sensitive volumes the code builds (B, configuration A)",
            ["-g", mixed, "-o", args.workdir, "--tag", "refused", "--dry-run", *hnl_events(1)],
            "that the current code registers as sensitive",
        )
    if os.path.exists(b_built):
        no_cells = r.copy_without(b_built, "B_no_cells", SENSITIVE_VOLUMES)
        if no_cells:
            r.check_refused(
                "-g is refused when the stored geometry lacks sensitive SBT cells",
                ["-g", no_cells, "-o", args.workdir, "--tag", "refused", "--dry-run", *hnl_events(1)],
                f"that the current code registers as sensitive ({SENSITIVE_VOLUMES[:-1]}",
            )
    if os.path.exists(a_built):
        no_iron = r.copy_without(a_built, "A_no_iron", FIELD_VOLUME)
        if no_iron:
            r.check_refused(
                "-g is refused when the stored geometry lacks a volume with a magnetic field",
                ["-g", no_iron, "-o", args.workdir, "--tag", "refused", "--dry-run", *hnl_events(1)],
                f"attaches a magnetic field ({FIELD_VOLUME})",
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
