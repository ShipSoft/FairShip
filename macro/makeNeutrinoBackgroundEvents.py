#Generation of an arbitrary number of different neutrino-types events, according to several GENIE models (Elastic, QE, DIS, RES)
#Used to generate bkg for LDM studies


#!/usr/bin/env python 
import ROOT,os,sys,getopt,time
import shipunit as u
import shipRoot_conf
shipRoot_conf.configure()

# location of these files on eos: eos/ship/data/
xsec = "NuCCDis_splines.xml"
hfile = "pythia8_Geant4-withCharm_onlyNeutrinos.root"

pdg  = ROOT.TDatabasePDG()
pDict = {}
sDict = {}
nuOverNubar = {}
f = ROOT.TFile(hfile)

x=12 #nu_e
#x=-12 #nu_e_bar
#x=14 #nu_mu
#x=-14 #nu_mu_bar
#x=16 #nu_tau
#x=-16 #nu_tau_bar

sDict[x] = pdg.GetParticle(x).GetName()
pDict[x]  = "10"+str(x)  #this works for particles
#pDict[x] = "20"+str(-x)   #this works for anti-particles
f.Close()

#evtype = "CCRES"
evtype = "CCQE"
#evtype = "CCDIS"
#evtype = "NuEElastic"



def makeEvents(nevents = 100, nutype = 12, evtype = "CCRES"):

 splines   = os.path.abspath('.')+'/NuCCDis_splines.xml'
 neutrinos = os.path.abspath('.')+'/'+hfile
 for p in pDict:
  if not sDict[p] in os.listdir('.'): os.system('mkdir '+sDict[p])
  os.chdir('./'+sDict[p])
  #os.system('rm '+hfile)
  #os.system('rm '+xsec)
  #os.system('ln -s  ../'+hfile+' '+hfile)
  #os.system('ln -s  ../'+xsec+' '+xsec)
  # stop at 350 GeV, otherwise strange warning about "Lower energy neutrinos have a higher probability of 
  # interacting than those at higher energy. pmaxLow(E=386.715)=2.157e-13 and  pmaxHigh(E=388.044)=2.15623e-13"
  N = nevents
  cmd = "gevgen -n "+str(N)+"  -p "+str(nutype)+" -t 1000822040[0.014],1000822060[0.241],1000822070[0.221],1000822080[0.524] -e  0.5,350"+" -f "+neutrinos+","+pDict[p]+ " --cross-sections "+splines+ " --event-generator-list "+evtype+" --message-thresholds $GENIE/config/Messenger_laconic.xml"
  print "start genie ",cmd
  os.system(cmd+" > log"+sDict[p]+" &")
  os.chdir('../')
def makeNtuples():
 print os.getcwd()
 for p in pDict:
  os.chdir('./'+sDict[p])
  print os.getcwd()
  os.system("gntpc -i gntp.0.ghep.root -f gst --message-thresholds $GENIE/config/Messenger_laconic.xml")
# add p/pt histogram
  fp = ROOT.TFile('../'+hfile) 
  fn = ROOT.TFile("gntp.0.gst.root","update")
  fp.Get(pDict[p].replace('0','2')).Write()
  fn.Close()
  os.system("mv gntp.0.gst.root genie-"+sDict[p]+"_"+evtype+".root")
  os.chdir('../')
def addHists():
 fp = ROOT.TFile(hfile) 
 for p in pDict:
  os.chdir('./'+sDict[p])
  fn = ROOT.TFile("genie-"+sDict[p]+".root","update")
  fp.Get(pDict[p].replace('0','2')).Write()
  fn.Close()
  os.chdir('../')
