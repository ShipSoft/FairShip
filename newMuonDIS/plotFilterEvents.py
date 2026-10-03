#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Plot filterEvents.py histograms in a multipage PDF using YAML settings."""

import argparse
import math
import tempfile
from pathlib import Path

import ROOT
import yaml

ROOT.gROOT.SetBatch(True)

DEFAULTS = {
    "x_range": None, "y_range": None, "z_range": None,
    "log_x": False, "log_y": False, "log_z": False,
    "rebin": 1, "enabled": True,
}


def histogram_paths(directory, prefix="", include_counts=False):
    """Discover latest histogram cycles without keeping all histograms in memory."""
    paths = []
    for name in sorted({key.GetName() for key in directory.GetListOfKeys()}):
        key = directory.GetKey(name)
        cls = ROOT.TClass.GetClass(key.GetClassName())
        path = f"{prefix}{name}"
        if cls and cls.InheritsFrom("TDirectory"):
            paths.extend(histogram_paths(directory.GetDirectory(name), path + "/", include_counts))
        elif cls and cls.InheritsFrom("TH1") and not cls.InheritsFrom("TH3"):
            if include_counts or name != "filter_counts":
                paths.append(path)
    return paths


def read_histogram(source, path):
    histogram = source.Get(path)
    if not histogram or not histogram.InheritsFrom("TH1"):
        raise ValueError(f"Histogram not found: {path}")
    histogram.SetDirectory(0)
    ROOT.SetOwnership(histogram, True)
    return histogram


def efficiency_inputs(paths):
    """Map display paths to matched denominator/numerator paths."""
    pairs = {}
    available = set(paths)
    for path in paths:
        directory, _, name = path.rpartition("/")
        if directory != "filter_efficiency":
            continue
        for prefix in ("filter_efficiency_", "filter_efficiency_z_"):
            for sample in ("all", "passed"):
                marker = f"{prefix}{sample}_"
                if not name.startswith(marker):
                    continue
                tag = name[len(marker):]
                inputs = tuple(f"{directory}/{prefix}{kind}_{tag}" for kind in ("all", "passed"))
                if not all(item in available for item in inputs):
                    raise ValueError(f"Incomplete efficiency histogram pair: {path}")
                pairs[f"{directory}/{prefix}{tag}"] = inputs
    return pairs


def rebin_histogram(histogram, value):
    factors = rebin_factors(histogram, value)
    if histogram.GetDimension() == 2:
        histogram.Rebin2D(*factors)
    elif factors[0] != 1:
        histogram.Rebin(factors[0])


def read_plot_histogram(source, path, efficiencies, rebin=1):
    if path not in efficiencies:
        histogram = read_histogram(source, path)
        rebin_histogram(histogram, rebin)
        return histogram
    all_path, passed_path = efficiencies[path]
    denominator = read_histogram(source, all_path)
    numerator = read_histogram(source, passed_path)
    if histogram_signature(denominator) != histogram_signature(numerator):
        raise ValueError(f"Incompatible efficiency histogram pair: {path}")
    rebin_histogram(denominator, rebin)
    rebin_histogram(numerator, rebin)
    # Passed events are a subset of all events, including their weights.
    numerator.Divide(numerator, denominator, 1., 1., "B")
    numerator.SetName(path.rsplit("/", 1)[-1])
    numerator.SetEntries(denominator.GetEntries())
    if numerator.GetDimension() == 1:
        numerator.GetXaxis().SetTitle("z_{DIS} [cm]")
        numerator.GetYaxis().SetTitle("Weighted filter efficiency")
    else:
        numerator.GetZaxis().SetTitle("Weighted filter efficiency")
    return numerator


def input_files(input_path, name_contains, excluded=(), limit=None):
    if limit is not None:
        if limit < 1:
            raise ValueError("--test must be a positive number of files")
        if not input_path.is_dir():
            raise ValueError("--test requires directory input")
    if not input_path.is_dir():
        return [input_path]
    excluded = {path.resolve() for path in excluded if path is not None}
    files = sorted({path.resolve() for path in input_path.rglob("*")
                    if path.is_file() and path.suffix.lower() == ".root"
                    and name_contains in path.name and path.resolve() not in excluded})
    if not files:
        raise ValueError(f"No ROOT files containing {name_contains!r} found in {input_path}")
    return files if limit is None else files[:limit]


def histogram_signature(histogram):
    axes = [histogram.GetXaxis(), histogram.GetYaxis()][:histogram.GetDimension()]
    return (histogram.ClassName(), tuple(
        (tuple(axis.GetBinLowEdge(i) for i in range(1, axis.GetNbins() + 2)),
         tuple(axis.GetBinLabel(i) for i in range(1, axis.GetNbins() + 1)))
        for axis in axes))


def merge_files(files, destination, include_tree=False):
    """Check compatible distributions, then stream the merge through ROOT."""
    if destination.exists():
        raise ValueError(f"Merged output already exists: {destination}")
    if include_tree:
        particle_class = ROOT.TClass.GetClass("DISparticle", False)
        if not particle_class or not particle_class.IsLoaded():
            if ROOT.gSystem.Load("libShipMuDIS.so") < 0:
                raise ValueError("Cannot load libShipMuDIS.so; run in the FairShip environment")
        particle_class = ROOT.TClass.GetClass("DISparticle")
        if not particle_class or not particle_class.IsLoaded():
            raise ValueError("DISparticle dictionary is missing; rebuild libShipMuDIS.so")
    reference = None
    for path in files:
        source = ROOT.TFile.Open(str(path), "READ")
        if not source or source.IsZombie():
            raise ValueError(f"Cannot open {path}")
        try:
            signatures = {}
            for name in histogram_paths(source, include_counts=True):
                histogram = read_histogram(source, name)
                signatures[name] = histogram_signature(histogram)
            if not signatures:
                raise ValueError(f"No histograms found in {path}")
            if reference is None:
                reference = signatures
            elif signatures != reference:
                different = sorted(name for name in signatures.keys() | reference.keys()
                                   if signatures.get(name) != reference.get(name))
                raise ValueError(f"Incompatible histogram names/binning/labels in {path}: {', '.join(different)}")
            if include_tree:
                tree = source.Get("MuonDIS")
                if not tree or not tree.InheritsFrom("TTree"):
                    raise ValueError(f"MuonDIS tree not found in {path}")
        finally:
            source.Close()
    merger = ROOT.TFileMerger(False, False)
    merger.SetNotrees(not include_tree)
    merger.SetMaxOpenedFiles(20)
    if not merger.OutputFile(str(destination), "CREATE"):
        raise ValueError(f"Cannot create merged output: {destination}")
    try:
        for path in files:
            print(f"Merging input: {path}")
            if not merger.AddFile(str(path)):
                raise ValueError(f"Cannot add merge input: {path}")
        if not merger.Merge():
            raise ValueError("ROOT file merge failed")
    finally:
        merger.CloseOutputFile()


def settings_for(config, path):
    settings = DEFAULTS | config.get("defaults", {}) | config.get("histograms", {}).get(path, {})
    unknown = settings.keys() - DEFAULTS.keys()
    if unknown:
        raise ValueError(f"{path}: unknown settings: {', '.join(sorted(unknown))}")
    for key in ("enabled", "log_x", "log_y", "log_z"):
        if not isinstance(settings[key], bool):
            raise ValueError(f"{path}: {key} must be true or false")
    for axis in "xyz":
        value = settings[f"{axis}_range"]
        if value is not None:
            if (not isinstance(value, list) or len(value) != 2
                    or any(isinstance(v, bool) or not isinstance(v, (int, float))
                           or not math.isfinite(v) for v in value)
                    or value[0] >= value[1]):
                raise ValueError(f"{path}: {axis}_range must be null or [minimum, maximum]")
            if settings[f"log_{axis}"] and value[0] <= 0:
                raise ValueError(f"{path}: a logarithmic {axis} range must start above zero")
    return settings


def rebin_factors(histogram, value):
    factors = value if isinstance(value, list) else [value] * histogram.GetDimension()
    if (len(factors) != histogram.GetDimension()
            or any(type(factor) is not int or factor < 1 for factor in factors)):
        raise ValueError("rebin must be a positive integer, or [x_factor, y_factor] for 2D")
    axes = [histogram.GetXaxis(), histogram.GetYaxis()]
    for axis, factor in zip(axes, factors):
        if axis.GetNbins() % factor:
            raise ValueError("Rebin factors must divide the bin counts to preserve the full range")
        if factor != 1 and any(axis.GetBinLabel(i) for i in range(1, axis.GetNbins() + 1)):
            raise ValueError("Rebinning labelled category axes would merge different species")
    return factors


def validate_plot(histogram, settings):
    rebin_factors(histogram, settings["rebin"])
    for axis, getter in (("x", histogram.GetXaxis), ("y", histogram.GetYaxis)):
        if axis == "y" and histogram.GetDimension() == 1:
            continue
        if settings[f"log_{axis}"]:
            limits = settings[f"{axis}_range"]
            low = limits[0] if limits else getter().GetXmin()
            if low <= 0:
                raise ValueError(f"log_{axis} requires an explicit positive {axis}_range for this histogram")
    if histogram.GetDimension() == 1 and (settings["log_z"] or settings["z_range"] is not None):
        raise ValueError("z_range/log_z apply only to 2D histograms")


def draw_histogram(canvas, histogram, settings, path):
    dimension = histogram.GetDimension()
    rebin_histogram(histogram, settings["rebin"])
    canvas.Clear()
    canvas.SetLeftMargin(0.14)
    canvas.SetRightMargin(0.22 if dimension == 2 else 0.06)
    labelled = any(histogram.GetXaxis().GetBinLabel(i) for i in range(1, histogram.GetNbinsX() + 1))
    canvas.SetBottomMargin(0.20 if labelled else 0.14)
    canvas.SetTopMargin(0.09)
    canvas.SetLogx(settings["log_x"])
    canvas.SetLogy(settings["log_y"])
    canvas.SetLogz(settings["log_z"])
    histogram.SetStats(False)
    histogram.SetTitle(f"{path}: {histogram.GetTitle()}")
    histogram.GetXaxis().SetTitleOffset(1.2)
    histogram.GetYaxis().SetTitleOffset(1.45)
    if settings["x_range"] is not None:
        histogram.GetXaxis().SetRangeUser(*settings["x_range"])
    if dimension == 2:
        if settings["y_range"] is not None:
            histogram.GetYaxis().SetRangeUser(*settings["y_range"])
        if not histogram.GetZaxis().GetTitle():
            histogram.GetZaxis().SetTitle("Entries")
        histogram.GetZaxis().SetTitleOffset(1.35)
        content_axis = "z"
    else:
        content_axis = "y"
    limits = settings[f"{content_axis}_range"]
    if limits is not None:
        histogram.SetMinimum(limits[0])
        histogram.SetMaximum(limits[1])
    # Give empty histograms a drawable positive scale on log-count axes.
    if settings[f"log_{content_axis}"] and limits is None and histogram.GetMaximum() <= 0:
        histogram.SetMinimum(0.1)
        histogram.SetMaximum(1.)
    histogram.Draw("COLZ" if dimension == 2 else "HIST")
    canvas.Update()
    if dimension == 2:
        palette = histogram.GetListOfFunctions().FindObject("palette")
        if palette:
            palette.SetX1NDC(0.80)
            palette.SetX2NDC(0.84)
    canvas.Modified()
    canvas.Update()


def write_default_config(source, paths, destination, efficiencies=None):
    histograms = {}
    for path in paths:
        histogram = read_plot_histogram(source, path, efficiencies or {})
        limits = {"x_range": [float(histogram.GetXaxis().GetXmin()), float(histogram.GetXaxis().GetXmax())]}
        if histogram.GetDimension() == 2:
            limits["y_range"] = [float(histogram.GetYaxis().GetXmin()), float(histogram.GetYaxis().GetXmax())]
        histograms[path] = limits
    config = {"defaults": DEFAULTS.copy(), "histograms": histograms}
    with destination.open("x") as output:
        output.write("# null uses the full stored axis range, or automatic limits for bin contents.\n")
        yaml.safe_dump(config, output, sort_keys=False)


def latex_escape(value):
    replacements = {"\\": r"\textbackslash{}", "_": r"\_", "%": r"\%", "&": r"\&",
                    "#": r"\#", "$": r"\$", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
                    "^": r"\textasciicircum{}"}
    return "".join(replacements.get(char, char) for char in value)


def write_table(source, paths, destination):
    materials = sorted({path.rsplit("/", 1)[0] for path in paths if "/" in path})
    rows = []
    for material in materials:
        summary = source.Get(f"{material}/filter_counts")
        counts = {}
        if summary:
            counts = {summary.GetXaxis().GetBinLabel(i): summary.GetBinContent(i)
                      for i in range(1, summary.GetNbinsX() + 1)}
        else:
            # Old files have exact raw counts, but no joint multiplicity/weight sums.
            for sample, suffix in (("processed", ""), ("selected", "filtered")):
                for kind, name in (("muons", "muon_p_"), ("dis", "n_daughters_")):
                    histogram = source.Get(f"{material}/{name}{suffix}")
                    if histogram:
                        counts[f"{kind}_{sample}_raw"] = histogram.GetEntries()
        if not counts:
            continue
        for kind, label in (("muons", "Muons"), ("dis", "DIS")):
            values = []
            for sample in ("processed", "selected"):
                for weighting in ("raw", "weighted"):
                    value = counts.get(f"{kind}_{sample}_{weighting}")
                    values.append("---" if value is None else
                                  (f"{value:.0f}" if weighting == "raw" else f"{value:.8g}"))
            rows.append(" & ".join([latex_escape(material), label, *values]) + r" \\")
    if not rows:
        raise ValueError("No per-material filter counts or validation histograms found")
    lines = [r"\begin{tabular}{llrrrr}", r"\hline",
             r"Material & Sample & Processed raw & Processed weighted & Selected raw & Selected weighted \\",
             r"\hline", *rows, r"\hline", r"\end{tabular}",
             "% Processed counts exclude unreadable/malformed entries. Selected muons are counted per material.",
             "% Muon weights sum wDIS; DIS weights sum nDIS * wDIS. --- means unavailable in older files."]
    destination.write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-f", "--inputfile", required=True, type=Path, help="ROOT file or directory (searched recursively)")
    parser.add_argument("--name-contains", default="_filtered.root",
                        help="Substring required in directory input ROOT filenames (default: _filtered.root)")
    parser.add_argument("--test", type=int, metavar="N",
                        help="Process only the first N matching directory files in sorted order")
    parser.add_argument("--merge-tree", type=Path, metavar="OUTPUT_ROOT",
                        help="Save merged histograms and MuonDIS trees to a new ROOT file")
    parser.add_argument("-c", "--config", type=Path, default=Path(__file__).with_name("plotFilterEvents.yaml"))
    parser.add_argument("-o", "--output", type=Path, help="Multipage PDF (default: input filename with .pdf)")
    parser.add_argument("--latex", type=Path, help="Also write a LaTeX count table")
    parser.add_argument("--write-config", type=Path, help="Write YAML with actual histogram ranges and exit")
    args = parser.parse_args()
    output = args.output or (args.inputfile / "merged.pdf" if args.inputfile.is_dir()
                             else args.inputfile.with_suffix(".pdf"))
    source = None
    temporary = None
    try:
        if args.write_config and args.merge_tree:
            raise ValueError("--write-config cannot be combined with --merge-tree")
        files = input_files(args.inputfile, args.name_contains, [args.merge_tree], limit=args.test)
        destinations = [args.write_config] if args.write_config else [output, args.latex, args.merge_tree]
        resolved = [path.resolve() for path in destinations if path is not None]
        protected = {path.resolve() for path in files} | {args.inputfile.resolve(), args.config.resolve()}
        if len(set(resolved)) != len(resolved) or any(path in protected for path in resolved):
            raise ValueError("Output paths must differ from each other and from the input/config files")
        if not args.write_config and output.suffix.lower() != ".pdf":
            raise ValueError("The plot output must have a .pdf extension")
        if args.merge_tree and args.merge_tree.suffix.lower() != ".root":
            raise ValueError("The merged output must have a .root extension")
        print(f"Found {len(files)} input file(s).")
        if args.test is not None:
            print(f"Test mode: using at most the first {args.test} matching files in sorted order.")
        merged_path = files[0]
        if args.inputfile.is_dir() or args.merge_tree:
            if args.merge_tree:
                merged_path = args.merge_tree
            else:
                temporary = tempfile.TemporaryDirectory(prefix="filter-histograms-")
                merged_path = Path(temporary.name) / "merged.root"
            merge_files(files, merged_path, include_tree=bool(args.merge_tree))
            if args.merge_tree:
                print(f"Saved merged histograms and trees to {merged_path}")
        source = ROOT.TFile.Open(str(merged_path), "READ")
        if not source or source.IsZombie():
            raise ValueError(f"Cannot open {merged_path}")
        paths = histogram_paths(source)
        if not paths:
            raise ValueError("No 1D or 2D histograms found")
        efficiencies = efficiency_inputs(paths)
        components = {component for pair in efficiencies.values() for component in pair}
        paths = sorted((set(paths) - components) | efficiencies.keys())
        if args.write_config:
            write_default_config(source, paths, args.write_config, efficiencies)
            print(f"Wrote settings for {len(paths)} histograms to {args.write_config}")
            return
        config = yaml.safe_load(args.config.read_text()) or {}
        if not isinstance(config, dict) or config.keys() - {"defaults", "histograms"}:
            raise ValueError("YAML must contain only defaults and histograms mappings")
        if not isinstance(config.get("defaults", {}), dict) or not isinstance(config.get("histograms", {}), dict):
            raise ValueError("defaults and histograms must be mappings")
        if any(not isinstance(value, dict) for value in config.get("histograms", {}).values()):
            raise ValueError("Each histogram override must be a mapping")
        unknown = config.get("histograms", {}).keys() - set(paths)
        if unknown:
            raise ValueError(f"Unknown histogram paths: {', '.join(sorted(unknown))}")
        plots = []
        empty_count = 0
        for path in paths:
            settings = settings_for(config, path)
            if settings["enabled"]:
                histogram = read_plot_histogram(source, path, efficiencies)
                if histogram.GetEntries() == 0:
                    print(f"Skipping empty histogram: {path}")
                    empty_count += 1
                    continue
                try:
                    validate_plot(histogram, settings)
                except ValueError as error:
                    raise ValueError(f"{path}: {error}") from error
                plots.append((path, settings))
        if not plots and not empty_count:
            raise ValueError("No histograms enabled")
        if args.latex:
            write_table(source, paths, args.latex)
            print(f"Saved count table to {args.latex}")
        if not plots:
            print("All enabled histograms are empty; no PDF created.")
            return
        canvas = ROOT.TCanvas("filter_plots", "Filter validation", 1000, 800)
        canvas.Print(str(output) + "[")
        try:
            for path, settings in plots:
                histogram = read_plot_histogram(source, path, efficiencies, settings["rebin"])
                draw_histogram(canvas, histogram, settings | {"rebin": 1}, path)
                canvas.Print(str(output), f"Title:{path}")
                canvas.Clear()
        finally:
            canvas.Print(str(output) + "]")
            canvas.Close()
        print(f"Saved {len(plots)} pages to {output}")
    except (OSError, ValueError, yaml.YAMLError) as error:
        parser.error(str(error))
    finally:
        if source:
            source.Close()
        if temporary:
            temporary.cleanup()


if __name__ == "__main__":
    main()
