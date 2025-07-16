#!/usr/bin/env python3
"""Standalone script to check for overlaps quickly."""

import argparse

import ROOT


def main():
    """Check for overlaps quickly."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-g",
        "--geofile",
        help="""Geometry file to use."""
        """Supports retrieving files from EOS via the XRootD protocol.""",
        required=True,
    )
    args = parser.parse_args()
    with ROOT.TFile.Open(args.geofile) as geofile:
        geo_manager = geofile.Get("FAIRGeom")
        geo_manager.SetNmeshPoints(10000)
        geo_manager.CheckOverlaps(0.1)  # 1 micron takes 5minutes
        geo_manager.PrintOverlaps()
        # check subsystems in more detail
        for node in geo_manager.GetTopNode().GetNodes():
            node.CheckOverlaps(0.0001)
            geo_manager.PrintOverlaps()


if __name__ == "__main__":
    main()
