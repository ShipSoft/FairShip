import os,subprocess,time,multiprocessing,socket
ncpus = multiprocessing.cpu_count() - 2

def count_python_processes(macroName):
# only works if screen is wide enough to print full name!
    status = subprocess.check_output('ps -f -u truf',shell=True)
    n=0
    for x in status.split('\n'):
        if not x.find(macroName)<0 and not x.find('python') <0: n+=1
    return n

pminRange  = [10.0,20.0]
ptCutRange = [0.0,0.5,0.8,0.9,1.0,1.1,1.2,1.5]

def run(cmd = "JpsiYield"):
# JpsiYield or JpsiKinematicsReco 
 for fitMethod in ['CB','B','G']:
   for muID in [0,1,2,11,12]:
      for ptCut in ptCutRange:
        for pmin in pminRange:
          cuts = str(ptCut)+","+str(pmin)+","+str(muID)+","+fitMethod
          while 1>0:
            if count_python_processes('MufluxNtuple')<ncpus: break
            time.sleep(100)
          os.system("python $FAIRSHIP/charmdet/MufluxNtuple.py -r -c "+cmd+ " --JpsiCuts "+cuts+ " & ")

def runPol(cmd = "JpsiPolarization"):
 for fitMethod in ['CB','B']:
   for muID in [1,2]:
      for ptCut in ptCutRange:
        for pmin in pminRange:
          for ptinterval in [ [0.,5.],[0.0,0.8],[0.8,1.6],[1.6,2.4],[2.4,3.2]]:
            cuts = str(ptCut)+","+str(pmin)+","+str(muID)+","+fitMethod+","+str(ptinterval[0])+","+str(ptinterval[1])
            while 1>0:
              if count_python_processes('MufluxNtuple')<ncpus: break
              time.sleep(100)
            os.system("python $FAIRSHIP/charmdet/MufluxNtuple.py -r -c "+cmd+ " --JpsiCuts "+cuts+ " & ")

def testrun(cmd = "JpsiYield"):
# JpsiYield or JpsiKinematicsReco 
 for fitMethod in ['CB','B','G']:
   for muID in [0,1,2,11,12]:
      for ptCut in [1.0]:
        for pmin in [20.]:
          cuts = str(ptCut)+","+str(pmin)+","+str(muID)+","+fitMethod
          while 1>0:
            if count_python_processes('MufluxNtuple')<ncpus: break
            time.sleep(100)
          os.system("python $SHIPBUILD/FairShip/charmdet/MufluxNtuple.py -r -c "+cmd+ " --JpsiCuts "+cuts+ " & ")
