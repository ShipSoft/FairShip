#!/usr/bin/env python
import ROOT,os,sys,getopt
import ConvRawData

import rootUtils as ut
h={}

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-r", "--runNumber", dest="runNumber", help="run number", type=int,required=True)
parser.add_argument("-P", "--partition", dest="partition", help="partition of data", type=int,required=False,default=-1)
parser.add_argument("-p", "--path", dest="path", help="path to raw data", default='/mnt/hgfs/VMgate/')
parser.add_argument("-M", "--online", dest="online", help="online mode",default=False,action='store_true')
parser.add_argument("-n", "--nEvents", dest="nEvents", help="number of events to process", type=int,default=-1)
parser.add_argument("-t", "--nStart", dest="nStart", help="first event to process", type=int,default=0)
parser.add_argument("-d", "--Debug", dest="debug", help="debug", default=False)
parser.add_argument("-s",dest="stop", help="do not start running", default=False)
parser.add_argument("-zM",dest="minMuHits", help="noise suppresion min MuFi hits", default=-1, type=int)
parser.add_argument("-zS",dest="minScifiHits", help="noise suppresion min ScifFi hits", default=-1, type=int)
parser.add_argument("-b", "--heartBeat", dest="heartBeat", help="heart beat", type=int,default=100000)
parser.add_argument("-cpp", "--convRawCPP", action='store_true', dest="FairTask_convRaw", help="convert raw data using ConvRawData FairTask", default=False)

options = parser.parse_args()
options.chi2Max = 2000.
options.saturationLimit  = 0.95
options.withGeoFile = False
options.makeCalibration = False

converter = ConvRawData.ConvRawDataPY()
converter.Init(options)
converter.Run()
converter.Finalize()


