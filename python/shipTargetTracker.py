
import ROOT

#import os
#import shipVertex, shipDet_conf
#import argparse
#import numpy as np
#from collections import defaultdict
#import math
#import sys
#if realPR == "Prev": import shipPatRec_prev as shipPatRec # The previous version of the pattern recognition
#else: import shipPatRec
#import shipunit as u
#import rootUtils as ut
#from array import array
#import sys 
#from math import fabs
#stop  = ROOT.TVector3()
#start = ROOT.TVector3()

myfile = ROOT.TFile("/home/ki/SHiPBuild/ship.conical.Pythia8-TGeant4.root")

tree = myfile.Get("cbmsim")
print("Total events:{}".format(tree.GetEntries() ) )

#tree.Print()
tree.Show()

#tt = tree.cbmsim
#tt = ROOT.TTPoint()

#for index, event in enumerate(tree):
#  for hit in event.TTPoint
#    print(
#      hit.GetDetectorID()
#    )
