#!/usr/bin/env python 
import ROOT,os,sys,getopt,time
import shipunit as u
import shipRoot_conf
shipRoot_conf.configure()
# location of these files on eos: eos/ship/data/
# 
xsec = "xsec_splines-iron-nu_e-nu_mu.xml"
hfile = "pythia8_Geant4-withCharm_onlyNeutrinos.root"

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

def makeSplines():
# first step, make cross section splines if not exist
 if not xsec in os.listdir('.'):
  os.system("gmkspl -p 14,-14,12,-12 -t 1000260560 -n 500 -e 400") 
  os.system("mv xsec_splines.xml xsec_splines-iron-nu_e-nu_mu.xml") 

def makeEvents(nevents = 100):
 run = 11
 for p in pDict:
  if p<0: print "scale number of "+sDict[p]+" events with %5.2F"%(1./nuOverNubar[abs(p)])
  if not sDict[p] in os.listdir('.'): os.system('mkdir '+sDict[p])
  os.chdir('./'+sDict[p])
  os.system('rm '+hfile)
  os.system('rm '+xsec)
  os.system('ln -s  ../'+hfile+' '+hfile)
  os.system('ln -s  ../'+xsec+' '+xsec)
  # stop at 350 GeV, otherwise strange warning about "Lower energy neutrinos have a higher probability of 
  # interacting than those at higher energy. pmaxLow(E=386.715)=2.157e-13 and  pmaxHigh(E=388.044)=2.15623e-13"
  N = nevents
  if p<0: N = int(nevents / nuOverNubar[abs(p)])
  cmd = "gevgen -n "+str(N)+"  -p "+str(p)+" -t 1000260560 -e  0.5,350  --run "+str(run)+" -f "+hfile+","+pDict[p]+ \
            " --cross-sections xsec_splines-iron-nu_e-nu_mu.xml --message-thresholds $GENIE/config/Messenger_laconic.xml"
  print "start genie ",cmd
  os.system(cmd+" > log"+sDict[p]+" &")
  run +=1
  os.chdir('../')
def makeNtuples():
 for p in pDict:
  os.chdir('./'+sDict[p])
  os.system("gntpc -i gntp.0.ghep.root -f gst --message-thresholds $GENIE/config/Messenger_laconic.xml")
# add p/pt histogram
  fp = ROOT.TFile(hfile) 
  fn = ROOT.TFile("gntp.0.gst.root","update")
  fp.Get(pDict[p].replace('0','2')).Write()
  fn.Close()
  os.system("mv gntp.0.gst.root genie-"+sDict[p]+".root")
  os.chdir('../')
def addHists():
 fp = ROOT.TFile(hfile) 
 for p in pDict:
  os.chdir('./'+sDict[p])
  fn = ROOT.TFile("genie-"+sDict[p]+".root","update")
  fp.Get(pDict[p].replace('0','2')).Write()
  fn.Close()
  os.chdir('../')
