import os,sys
listRuns='xrdfs root://eospublic.cern.ch/ ls /eos/experiment/ship/data/muflux/rawdata'

if len(sys.argv)<2:
  os.system(listRuns)
else:
  print 'list spills in ',sys.argv[1]
  rc = os.system(listRuns+'/'+sys.argv[1])
  if rc!=0:
    print "listing failed. Did you provided a token? kinit yourUserNameOnLxplus@CERN.CH"
    if not len(sys.argv)<2:
      print "or wrong directory specified, should be of type RUN_8000_XXXX",sys.argv[1]
