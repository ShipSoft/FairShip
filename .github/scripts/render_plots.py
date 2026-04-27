#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Render ROOT histogram objects to PNG images for CI visualisation."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(111111)
ROOT.gStyle.SetOptFit(1111)

DRAWABLE_TYPES = (ROOT.TH1, ROOT.TGraph, ROOT.TMultiGraph, ROOT.TEfficiency)


def render_object(obj: Any, output_path: Path) -> dict[str, str] | None:
    """Render a single ROOT object to PNG.

    Returns metadata dict or None if not drawable.
    """
    if isinstance(obj, ROOT.TCanvas):
        obj.SaveAs(str(output_path))
        return {"type": obj.ClassName()}

    if not isinstance(obj, DRAWABLE_TYPES):
        return None

    canvas = ROOT.TCanvas("c", "", 800, 600)

    if isinstance(obj, ROOT.TH2):
        canvas.SetRightMargin(0.15)
        obj.Draw("COLZ")
    elif isinstance(obj, ROOT.TEfficiency):
        obj.Draw("AP")
    else:
        obj.Draw()

    canvas.SaveAs(str(output_path))
    return {"type": obj.ClassName()}


def render_directory(
    directory: Any,
    output_dir: Path,
    path: str = "",
    max_depth: int = 3,
) -> list[dict[str, str]]:
    """Recursively render all drawable objects in a ROOT directory."""
    if max_depth <= 0:
        return []

    rendered = []

    for key in directory.GetListOfKeys():
        obj_name = key.GetName()
        obj = directory.Get(obj_name)
        current_path = f"{path}/{obj_name}" if path else obj_name

        if isinstance(obj, ROOT.TDirectory):
            rendered.extend(render_directory(obj, output_dir, current_path, max_depth - 1))
            continue

        safe_name = current_path.replace("/", "_")
        png_path = output_dir / f"{safe_name}.png"

        try:
            meta = render_object(obj, png_path)
        except Exception as e:
            print(f"WARNING: Failed to render {current_path}: {e}", file=sys.stderr)
            continue

        if meta:
            rendered.append({"name": obj_name, "root_path": current_path, "file": png_path.name, **meta})

    return rendered


def main() -> int:
    """Render ROOT objects to PNG images."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", help="ROOT files to render")
    parser.add_argument("--output-dir", required=True, help="Directory for output PNGs")
    parser.add_argument("--job", required=True, help="Job name for manifest")
    parser.add_argument("--config", required=True, help="Configuration label")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_rendered: list[dict[str, str]] = []

    for input_path in args.inputs:
        root_file = ROOT.TFile.Open(input_path)
        if not root_file or root_file.IsZombie():
            print(f"WARNING: Cannot open {input_path}", file=sys.stderr)
            continue

        rendered = render_directory(root_file, output_dir)
        all_rendered.extend(rendered)
        root_file.Close()

    manifest = {
        "job": args.job,
        "config": args.config,
        "files": all_rendered,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"Rendered {len(all_rendered)} plots to {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
