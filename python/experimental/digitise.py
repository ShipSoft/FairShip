#!/usr/bin/env python3

import ROOT
import argparse

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inputfiles",
        nargs="+",
        help="""List of input files to use.\n"""
        """Supports retrieving file from EOS via the XRootD protocol.""",
        required=True,
    )
    parser.add_argument(
        "-g",
        "--geofile",
        help="""Geometry file to use."""
        """Supports retrieving files from EOS via the XRootD protocol.""",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--outputfile",
        help="""File to write the output tree to."""
        """Will be recreated if it already exists.""",
    )
    parser.add_argument(
        "-j",
        "--num_cpu",
        default=1,
        type=int,
        help="""Number of threads to use.""",
    )

    args = parser.parse_args()
    ROOT.EnableImplicitMT(args.num_cpu)
    df = ROOT.ROOT.RDataFrame("cbmsim", args.inputfiles)

    ROOT.gInterpreter.Declare(
        """
        std::vector<strawtubesHit> digitise_strawtubesc(const TClonesArray& points) {
             std::vector<strawtubesHit> hits{};
             for (auto* pointer: points) {
                 auto* point = dynamic_cast<strawtubesPoint*>(pointer);
                 strawtubesHit hit{point, t0};
                 hits.push_back(hit);
                 // TODO check that hit is valid
             }
        }
        """
    )

    df = df.Define("Digi_StrawTubesHits", "digitise_strawtubes(strawtubePoint)")
    df.Snapshot(
        "df", args.outputfile
    )

if __name__ == "__main__":
    main()
