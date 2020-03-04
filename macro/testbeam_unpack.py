#!/usr/bin/env python
import argparse
import ROOT

# Fix https://root-forum.cern.ch/t/pyroot-hijacks-help/15207 :
ROOT.PyConfig.IgnoreCommandLineOptions = True


def main():
    source = ROOT.ShipTdcSource(args.input)

    source.AddUnpacker(0xc00, ROOT.DriftTubeUnpack(args.charm))
    source.AddUnpacker(0xb00, ROOT.RPCUnpack())
    source.AddUnpacker(0x8100, ROOT.ScalerUnpack())

    if args.charm:
        pixelUnpack = ROOT.PixelUnpack(0x800)
        source.AddUnpacker(0x800, pixelUnpack)
        source.AddUnpacker(0x801, pixelUnpack)
        source.AddUnpacker(0x802, pixelUnpack)
        source.AddUnpacker(0x900, ROOT.SciFiUnpack(0x900))

    run = ROOT.FairRunOnline(source)
    run.SetOutputFile(args.output)
    run.SetAutoFinish(True)
    run.SetRunId(args.run)

    run.Init()

    run.Run(-1, 0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f", "--input", required=True, help="Input file (can be on EOS)"
    )
    parser.add_argument("-o", "--output", required=True, help="Output file")
    parser.add_argument("-n", "--run", default=0, type=int, help="Run number")
    parser.add_argument(
        "--charm", action="store_true", help="Unpack charm data (default: muon flux)"
    )
    args = parser.parse_args()
    ROOT.gROOT.SetBatch(True)
    main()
