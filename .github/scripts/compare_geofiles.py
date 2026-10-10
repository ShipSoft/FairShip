#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Check that two geometry files hold the same geometry.

Compares the geometry (materials, media, every volume with its shape, medium
and placed daughters with their transformations) and the geometry
configuration (ShipGeo, without the FairShip versions that wrote the file).

With --expect-different, the volumes of the two geometries must differ instead.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile

# Keys of ShipGeo that record which FairShip wrote the file, not the geometry
PROVENANCE_KEYS = {"FairShip", "FairRoot", "geometryBuiltWithFairShip"}


def rounded(values) -> list[float]:
    return [round(v, 9) for v in values]


def summarise(path: str) -> dict:
    """Everything compared, as plain data. Each file is read in its own process."""
    import ROOT

    f = ROOT.TFile.Open(path)
    geometry = f.Get("FAIRGeom")
    summary: dict = {}
    stored = f.Get("ShipGeo")
    summary["ShipGeo"] = json.loads(str(stored)) if stored else None
    if summary["ShipGeo"]:
        summary["ShipGeo"] = {k: v for k, v in summary["ShipGeo"].items() if k not in PROVENANCE_KEYS}
    summary["materials"] = [
        [m.GetName(), round(m.GetA(), 9), round(m.GetZ(), 9), round(m.GetDensity(), 9)]
        for m in geometry.GetListOfMaterials()
    ]
    summary["media"] = [
        [m.GetName(), m.GetId(), m.GetMaterial().GetName(), rounded(m.GetParam(i) for i in range(20))]
        for m in geometry.GetListOfMedia()
    ]
    volumes = []
    for volume in geometry.GetListOfVolumes():
        shape = volume.GetShape()
        medium = volume.GetMedium()
        daughters = []
        for i in range(volume.GetNdaughters()):
            node = volume.GetNode(i)
            matrix = node.GetMatrix()
            daughters.append(
                [
                    node.GetName(),
                    node.GetVolume().GetName(),
                    rounded(matrix.GetTranslation()[k] for k in range(3)),
                    rounded(matrix.GetRotationMatrix()[k] for k in range(9)),
                ]
            )
        volumes.append(
            [
                volume.GetName(),
                volume.ClassName(),
                shape.ClassName() if shape else None,
                rounded([shape.GetDX(), shape.GetDY(), shape.GetDZ(), *(shape.GetOrigin()[k] for k in range(3))])
                if shape
                else None,
                medium.GetName() if medium else None,
                daughters,
            ]
        )
    summary["volumes"] = volumes
    summary["top"] = geometry.GetTopVolume().GetName()
    f.Close()
    return summary


def summarise_in_subprocess(path: str) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "summary.json")
        subprocess.run([sys.executable, __file__, "--summarise", path, out], check=True, stdout=subprocess.DEVNULL)
        with open(out) as fh:
            return json.load(fh)


def compare(a: dict, b: dict, max_report: int = 20) -> list[str]:
    differences = []
    for section in a:
        x, y = a[section], b.get(section)
        if x == y:
            continue
        if isinstance(x, list) and isinstance(y, list):
            if len(x) != len(y):
                differences.append(f"{section}: {len(x)} entries in the first file, {len(y)} in the second")
            for i, (u, v) in enumerate(zip(x, y)):
                if u != v:
                    differences.append(f"{section}[{i}]: {str(u)[:200]} != {str(v)[:200]}")
        elif isinstance(x, dict) and isinstance(y, dict):
            for key in sorted(x.keys() | y.keys()):
                if x.get(key) != y.get(key):
                    differences.append(f"{section}.{key}: {str(x.get(key))[:200]} != {str(y.get(key))[:200]}")
        else:
            differences.append(f"{section}: {str(x)[:200]} != {str(y)[:200]}")
    for line in differences[:max_report]:
        print(line)
    if len(differences) > max_report:
        print(f"... and {len(differences) - max_report} more")
    return differences


def main() -> int:
    if len(sys.argv) == 4 and sys.argv[1] == "--summarise":
        with open(sys.argv[3], "w") as fh:
            json.dump(summarise(sys.argv[2]), fh)
        return 0
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("first", help="geometry file")
    parser.add_argument("second", help="geometry file to compare with it")
    parser.add_argument("--expect-different", action="store_true", help="fail if the geometries are the same")
    args = parser.parse_args()

    a = summarise_in_subprocess(args.first)
    b = summarise_in_subprocess(args.second)
    n_nodes = sum(len(v[-1]) for v in a["volumes"])
    print(f"{args.first}: {len(a['volumes'])} volumes, {n_nodes} placed daughters, {len(a['media'])} media")
    differences = compare(a, b)
    if args.expect_different:
        # The geometries themselves must differ, not only their configuration
        if a["volumes"] != b["volumes"]:
            print(f"OK: the volumes of {args.first} and {args.second} differ, as expected")
            return 0
        print(f"ERROR: {args.first} and {args.second} have the same volumes, but should differ")
        return 1
    if differences:
        print(f"ERROR: {len(differences)} differences between {args.first} and {args.second}")
        return 1
    print("OK: same geometry and configuration")
    return 0


if __name__ == "__main__":
    sys.exit(main())
