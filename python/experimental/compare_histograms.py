# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Compare histograms for exact or statistical equality."""

import argparse
import sys

import ROOT


def histograms_identical(hist1: ROOT.TH1, hist2: ROOT.TH1) -> bool:
    """Return True if two histograms have identical binning, contents and errors.

    ``TH1`` does not override ``TObject::IsEqual`` (which compares addresses), so
    a content-based comparison is required. ``GetNcells`` covers the under- and
    overflow bins and works for 1/2/3-D histograms alike.
    """
    ncells = hist1.GetNcells()  # type: ignore[attr-defined]
    if ncells != hist2.GetNcells():  # type: ignore[attr-defined]
        return False
    for i in range(ncells):
        if hist1.GetBinContent(i) != hist2.GetBinContent(i):
            return False
        if hist1.GetBinError(i) != hist2.GetBinError(i):
            return False
    return True


def compare_histograms(
    hist1: ROOT.TH1, hist2: ROOT.TH1, use_ks_test: bool = False, significance_threshold: float = 0.05
) -> bool:
    """Compare two histograms for equality or statistical compatibility."""
    name = hist1.GetName()

    if not histograms_identical(hist1, hist2):
        print(f"Histograms '{name}' are different in terms of bin contents or errors.")

        if use_ks_test:
            p_value = hist1.KolmogorovTest(hist2)
            print(f"KS p-value: {p_value}")
            if p_value < significance_threshold:
                print(f"Histograms '{name}' are statistically different (p < {significance_threshold}).")
            else:
                print(f"Histograms '{name}' are statistically compatible (p >= {significance_threshold}).")
        return False

    print(f"Histograms '{name}' are equal.")
    return True


def main(file1_path: str, file2_path: str, use_ks_test: bool, significance_threshold: float) -> bool:
    """Compare histograms in two ROOT files.

    Returns True if every histogram is present in both files and identical,
    False otherwise (so the caller can propagate a non-zero exit status).
    """
    file1 = ROOT.TFile.Open(file1_path)
    file2 = ROOT.TFile.Open(file2_path)
    all_match = True

    histograms1 = {}
    for key in file1.GetListOfKeys():
        cls = ROOT.TClass.GetClass(key.GetClassName())
        if cls is not None and cls.InheritsFrom("TH1"):
            histograms1[key.GetName()] = file1.Get(key.GetName())

    histograms2 = {}
    for key in file2.GetListOfKeys():
        cls = ROOT.TClass.GetClass(key.GetClassName())
        if cls is not None and cls.InheritsFrom("TH1"):
            histograms2[key.GetName()] = file2.Get(key.GetName())

    for hist_name in histograms1:
        if hist_name in histograms2:
            if not compare_histograms(
                histograms1[hist_name], histograms2[hist_name], use_ks_test, significance_threshold
            ):
                all_match = False
        else:
            print(f"Histogram '{hist_name}' not found in file2.")
            all_match = False

    for hist_name in histograms2:
        if hist_name not in histograms1:
            print(f"Histogram '{hist_name}' not found in file1.")
            all_match = False

    return all_match


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare histograms in two ROOT files.")
    parser.add_argument("file1", help="Path to the first ROOT file.")
    parser.add_argument("file2", help="Path to the second ROOT file.")
    parser.add_argument(
        "--ks",
        action="store_true",
        help="Use Kolmogorov-Smirnov test for statistical comparison.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.05,
        help="Significance threshold for the KS test (default: 0.05).",
    )

    args = parser.parse_args()

    sys.exit(0 if main(args.file1, args.file2, args.ks, args.threshold) else 1)
