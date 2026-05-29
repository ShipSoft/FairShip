#!/usr/bin/env python
"""Script to collect muons hitting either the UBT extended plane, or the SBT, including soft interaction products, and DIS events, to a ROOT file."""
"""Created May 2026 A.-M. Magnan"""

import argparse
import logging
import os

import ROOT as r
import shipunit as u
from tabulate import tabulate
import time

pdg = r.TDatabasePDG.Instance()

logging.basicConfig(level=logging.INFO)

r.gSystem.Load("libShipMuDIS.so")

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--inputfile",help="full path to muon background files")
parser.add_argument("-o", "--outputfile",help="custom outputfile name",default="muonsProduction_wsoft.root",)
parser.add_argument("-n", "--n_events", type=int, default=-1)
#parser.add_argument("-g","--generator",help="type of generator, options are: MuonBack or PG",default="MuonBack")
#parser.add_argument("-i","--firstEvent",help="First event of muon file to use",
#                    required=False,default=0,type=int)
parser.add_argument("-d","--nDIS",help="Number of DIS per muon to generate",
                    required=False,default=1000,type=int)


args = parser.parse_args()


logging.info(f"Path to MuonBackground : {args.inputfile}")

theseed=int(time.time())
print(theseed)

muDis = r.MuDISProcessor()
muDis.init(args.n_events,args.nDIS,theseed)
muDis.process_file(args.inputfile,
                   args.outputfile)

