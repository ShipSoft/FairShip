#!/usr/bin/env python 
from __future__ import print_function
from __future__ import division
import ROOT,os,sys,time
import shipunit as u
import shipRoot_conf
import argparse
shipRoot_conf.configure()
# 
xsec = "xsec_splines-iron-nu_e-nu_mu.xml"
hfile = "pythia8_Geant4_1.0_withCharm_nu.root" #2018 background generation
#xsec = "Nu_splines.xml"
#hfile = "pythia8_Geant4-withCharm_onlyNeutrinos.root"
#put the above files in folder linked by the environment variables GENIEXSECPATH and NUFLUXPATH

splines   = os.environ['XSECPATH']+'/'+xsec #path of splines
neutrinos = os.environ['NUFLUXPATH']+'/'+hfile #path of flux

def init(): #available options  

  ap = argparse.ArgumentParser(
      description='Run GENIE neutrino" simulation')
  ap.add_argument('-s', '--seed', type=int, dest='seed', default=65539) #default seed in $GENIE/src/Conventions/Controls.h
  ap.add_argument('-o','--output'    , type=str, help="output directory", dest='work_dir', default=None)
  ap.add_argument('-t', '--target', type=str, help="target material", dest='target', default='iron')
  args = ap.parse_args()
  return args

args = init() #getting options

work_dir = args.work_dir
target = args.target
seed = args.seed

print('Target type: ', target)
print('Seed used in this generation: ', seed)
print('Splines file used', xsec) 

if target == 'iron':
 targetcode = '1000260560'
elif target == 'lead':
 targetcode = '1000822040[0.014],1000822060[0.241],1000822070[0.221],1000822080[0.524]'
else:
 print('only iron and lead target available')
 1/0

pdg  = ROOT.TDatabasePDG()
pDict = {}
sDict = {}
nuOverNubar = {}
f = ROOT.TFile(hfile)

for x in [14,12]:
 sDict[x] = pdg.GetParticle(x).GetName()
 sDict[-x] = pdg.GetParticle(-x).GetName()
 pDict[x]  = "10"+str(x)
 pDict[-x] = "20"+str(x)
 nuOverNubar[x] = f.Get(pDict[x]).GetSumOfWeights()/f.Get(pDict[-x]).GetSumOfWeights()
f.Close()

work_dir = args.work_dir 

if os.path.exists(work_dir): #if the directory is already there, leave a warning, otherwise create it
    print('output directory already exists.')
else:
    os.makedirs(work_dir)

os.chdir(work_dir)

def makeSplines():
# first step, make cross section splines if not exist
 if not xsec in os.listdir('.'):
  os.system("gmkspl -p 14,-14,12,-12 -t 1000260560 -n 500 -e 400") 
  os.system("mv xsec_splines.xml xsec_splines-iron-nu_e-nu_mu.xml") 

def makeEvents(nevents = 100):
 run = 11
 for p in pDict:
  if p<0: print("scale number of "+sDict[p]+" events with %5.2F"%(1./nuOverNubar[abs(p)]))
  if not sDict[p] in os.listdir('.'): os.system('mkdir '+sDict[p])
  os.chdir('./'+sDict[p])
  #os.system('rm '+hfile)
  #os.system('rm '+xsec)
  #os.system('ln -s  ../'+hfile+' '+hfile)
  #os.system('ln -s  ../'+xsec+' '+xsec)
  # stop at 350 GeV, otherwise strange warning about "Lower energy neutrinos have a higher probability of 
  # interacting than those at higher energy. pmaxLow(E=386.715)=2.157e-13 and  pmaxHigh(E=388.044)=2.15623e-13"
  N = nevents
  if p<0: N = int(nevents / nuOverNubar[abs(p)])
  cmd = "gevgen -n "+str(N)+" -p "+str(p)+" -t "+targetcode +" -e  0.5,350  --run "+str(run)+" -f "+neutrinos+","+pDict[p]+ \
            " --cross-sections "+splines+" --message-thresholds $GENIE/config/Messenger_laconic.xml" +" --seed "+str(seed)
  print("start genie ",cmd)
  os.system(cmd+" > log"+sDict[p]+" &")
  run +=1
  os.chdir('../')
def makeNtuples():
 for p in pDict:
  os.chdir('./'+sDict[p])
  os.system("gntpc -i gntp.0.ghep.root -f gst --message-thresholds $GENIE/config/Messenger_laconic.xml")
# add p/pt histogram
  fp = ROOT.TFile(neutrinos) 
  fn = ROOT.TFile("gntp.0.gst.root","update")
  fp.Get(pDict[p].replace('0','2')).Write()
  fn.Close()
  os.system("mv gntp.0.gst.root genie-"+sDict[p]+".root")
  os.chdir('../')
def addHists():
 fp = ROOT.TFile(neutrinos) 
 for p in pDict:
  os.chdir('./'+sDict[p])
  fn = ROOT.TFile("genie-"+sDict[p]+".root","update")
  fp.Get(pDict[p].replace('0','2')).Write()
  fn.Close()
  os.chdir('../')
