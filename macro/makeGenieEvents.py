#!/usr/bin/env python
import ROOT,os,sys,time
from subprocess import call
import shipunit as u
import shipRoot_conf
import argparse
import logging
import genie_interface
shipRoot_conf.configure()


# IMPORTANT
# Before runnig this script please run this command in FairShip bash if you are dealing with the neutrino detector:
# export GXMLPATH='/eos/experiment/ship/user/aiuliano/GENIE_FNAL_nu_splines'
# this will disable Genie decays for charm particles and tau



xsec = "gxspl-FNAL-nuSHiP-minimal.xml"# new adapted splines from Genie site
hfile = "pythia8_Geant4_1.0_withCharm_nu.root" #2018 background generation
#xsec = "Nu_splines.xml"
#hfile = "pythia8_Geant4-withCharm_onlyNeutrinos.root"


defaultsplinedir   = '/eos/experiment/ship/user/aiuliano/GENIE_FNAL_nu_splines' #path of splines
defaultfiledir  = '/eos/experiment/ship/data/Mbias/background-prod-2018' #path of flux






def get_arguments(): #available options

  parser = argparse.ArgumentParser(
      description='Run GENIE neutrino" simulation')
  subparsers = parser.add_subparsers()
  ap = subparsers.add_parser('sim',help="make genie simulation file")

  ap.add_argument('-s', '--seed', type=int, dest='seed', default=65539) #default seed in $GENIE/src/Conventions/Controls.h
  ap.add_argument('-o','--output'    , type=str, help="output directory", dest='work_dir', default=None)
  ap.add_argument('-f','--filedir', type=str, help="directory with neutrino fluxes", dest='filedir', default=defaultfiledir)
  ap.add_argument('-c','--crosssectiondir', type=str, help="directory with neutrino splines crosssection", dest='splinedir', default=defaultsplinedir)
  ap.add_argument('-t', '--target', type=str, help="target material", dest='target', default='iron')
  ap.add_argument('-n', '--nevents', type=int, help="number of events", dest='nevents', default=100)
  ap.add_argument('-e', '--event-generator-list', type=str, help="event generator list", dest='evtype', default=None) # Possbile evtypes: CC, CCDIS, CCQE, CharmCCDIS, RES, CCRES, see other evtypes in $GENIE/config/EventGeneratorListAssembler.xml
  ap.add_argument("--nudet", dest="nudet", help="option for neutrino detector", required=False, action="store_true")

  ap1 = subparsers.add_parser('spline',help="make a new cross section spline file")
  ap1.add_argument('-t', '--target', type=str, help="target material", dest='target', default='iron')
  ap1.add_argument('-o','--output'    , type=str, help="output directory", dest='work_dir', default=None)
  args = parser.parse_args()
  return args

args = get_arguments() #getting options

print('Target type: ', args.target)

if args.target == 'iron':
 targetcode = '1000260560'
elif args.target == 'lead':
 targetcode = '1000822040[0.014],1000822060[0.241],1000822070[0.221],1000822080[0.524]'
elif args.target == 'tungsten':
 targetcode = '1000741840'
else:
 print('only iron, lead and tunsgten target options available')
 1/0

if os.path.exists(args.work_dir): #if the directory is already there, leave a warning, otherwise create it
    print('output directory already exists.')
else:
    os.makedirs(args.work_dir)

os.chdir(args.work_dir)

def makeSplines():
 '''first step, make cross section splines if not exist'''
 nupdglist = [16,-16,14,-14,12,-12]
 genie_interface.make_splines(nupdglist, targetcode, 400, nknots = 500, outputfile = "xsec_splines.xml")

def makeEvents(nevents = 100):
 run = 11
 for p in pDict:
  if p<0: print("scale number of "+sDict[p]+" events with %5.2F"%(1./nuOverNubar[abs(p)]))
  if not sDict[p] in os.listdir('.'): call('mkdir '+sDict[p],shell = True)
  os.chdir('./'+sDict[p])
  # stop at 350 GeV, otherwise strange warning about "Lower energy neutrinos have a higher probability of
  # interacting than those at higher energy. pmaxLow(E=386.715)=2.157e-13 and  pmaxHigh(E=388.044)=2.15623e-13"
  N = nevents
  if p<0: N = int(nevents / nuOverNubar[abs(p)])
  genie_interface.generate_genie_events(nevents = N, nupdg = p, targetcode = targetcode, emin = 0.5, emax = 350,\
                      inputflux = neutrinos, spline = splines, seed = args.seed, process = args.evtype, irun = run)
  run +=1
  os.chdir('../')
def makeNtuples():
 for p in pDict:
  os.chdir('./'+sDict[p])
  genie_interface.make_ntuples("gntp.0.ghep.root","genie-"+sDict[p]+".root")
  genie_interface.add_hists(neutrinos, "genie-"+sDict[p]+".root", p)
  os.chdir('../')

def addHists():
 for p in pDict:
  os.chdir('./'+sDict[p])
  genie_interface.add_hists(neutrinos, "genie-"+sDict[p]+".root", p)
  os.chdir('../')

if ("splinedir" not in args):
 makeSplines()

else:

 if args.nudet:
  if 'GXMLPATH' not in os.environ:
   logging.warn('GXMLPATH is not set: Genie will decay charm and tau particles, which is usually not the desired behaviour')
  else: logging.debug('GXMLPATH is set: Genie will not decay charm and tau particles')

 splines = args.splinedir+'/'+xsec #path of splines
 neutrinos = args.filedir+'/'+hfile #path of flux

 print('Seed used in this generation: ', args.seed)
 print('Splines file used', xsec)

 pdg  = ROOT.TDatabasePDG()
 pDict = {}
 sDict = {}
 nuOverNubar = {}
 f = ROOT.TFile(neutrinos)

 for x in [16, 14,12]:
  sDict[x] = pdg.GetParticle(x).GetName()
  sDict[-x] = pdg.GetParticle(-x).GetName()
  pDict[x]  = "10"+str(x)
  pDict[-x] = "20"+str(x)
  nuOverNubar[x] = f.Get(pDict[x]).GetSumOfWeights()/f.Get(pDict[-x]).GetSumOfWeights()
 f.Close()

 makeEvents(args.nevents)
 makeNtuples()
