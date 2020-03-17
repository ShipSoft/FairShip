from __future__ import print_function
import os,sys,subprocess,ROOT
listRuns='xrdfs root://eospublic.cern.ch/ ls /eos/experiment/ship/data/muflux/rawdata'
Npot=0

if len(sys.argv)<2:
  os.system(listRuns)
else:
  print('list spills in ',sys.argv[1])
  rc = os.system(listRuns.replace(' ls ',' ls -l ')+'/'+sys.argv[1])
  if rc!=0:
    print("listing failed. Did you provided a token? kinit yourUserNameOnLxplus@CERN.CH")
    if not len(sys.argv)<2:
      print("or wrong directory specified, should be of type RUN_8000_XXXX",sys.argv[1])
  if len(sys.argv)>2:
    tmp = subprocess.check_output(listRuns+'/'+sys.argv[1],shell=True)
    for fname in tmp.split('\n'):
      if fname.find('root')<0: continue
      try:
       f=ROOT.TFile.Open(os.environ['EOSSHIP']+fname)
       sc = f.scalers
       sc.GetEvent(0)
       Npot+=sc.SC00
      except:
       print("error with spill",fname)
    print("PoT=",Npot)

