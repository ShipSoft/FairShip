import os,subprocess,ROOT,time,multiprocessing
ncpus = multiprocessing.cpu_count() / 2.

pathToMacro = '' # $SHIPBUILD/FairShip/charmdet/
def count_python_processes(macroName):
# only works if screen is wide enough to print full name!
 status = subprocess.check_output('ps -f -u truf',shell=True)
 n=0
 for x in status.split('\n'):
   if not x.find(macroName)<0 and not x.find('python') <0: n+=1
 return n

fileList = {}
badFiles = []
eospath='/eos/experiment/ship/data/Mbias/background-prod-2018/'

def getFilesFromEOS():
# list of files
 temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospath,shell=True)
 for x in temp.split('\n'):
  if x.find('1.0')<0 or x.find('_mu')<0: continue # includes charm
  # if x.find('1.0_c')<0 or x.find('_mu')<0: continue   # take only mbias
  fname =  x[x.find('/eos'):]
  nentries = 0
  f=ROOT.TFile.Open(os.environ['EOSSHIP']+fname)
  nentries=f.cbmsim.GetEntries()
  fileList[fname]=nentries
 return fileList

def getFilesLocal():
# list of files
 fl = []
 temp = os.listdir('.')
 for x in temp:
  if os.path.isdir(x): fl.append(x)
 return fl

def simulationStep():
 fnames = getFilesFromEOS()
 Nfiles = len(fnames)
 print "fileList established ",Nfiles
 for fname in fnames:
    N = fileList[fname]-1
    odir = fname[fname.rfind('/')+1:].replace('.root','')
    cmd = "python $FAIRSHIP/macro/run_simScript.py -n "+str(N)+" --MuonBack --charm=1 --CharmdetSetup=0 --output "+odir+" -f "+fname+" &"
    print 'step 1:', cmd
    os.system(cmd)
    time.sleep(100)
    while 1>0:
        if count_python_processes('run_simScript')<ncpus: break 
        time.sleep(100)
 print "finished all the tasks."
def digiStep():
 fnames = getFilesLocal()
 Nfiles = len(fnames)
 print "fileList established ",Nfiles
 for fname in fnames:
    os.chdir(fname)
    mcFile = 'ship.conical.MuonBack-TGeant4.root'
    geoFile = 'geofile_full.conical.MuonBack-TGeant4.root'
    cmd = "python $FAIRSHIP/macro/runMufluxDigi.py -n 9999999 -f "+mcFile+" -g "+geoFile+" &"
    print 'step 2:', cmd
    os.system(cmd)
    os.chdir('../')
    while 1>0:
        if count_python_processes('runMufluxDigi')<ncpus: break 
        time.sleep(100)
 print "finished all the tasks."

def splitDigiFiles(splitFactor=10):
 fnames = getFilesLocal()
 Nfiles = len(fnames)
 print "fileList established ",Nfiles
 for fname in fnames:
   os.chdir(fname)
   ofile = 'ship.conical.MuonBack-TGeant4_dig.root'
   origin = ROOT.TFile(ofile)
   sTree = origin.cbmsim
   Nentries = sTree.GetEntries()
   N = 0
   deltaN = int(sTree.GetEntries()/float(splitFactor))
   for i in range(splitFactor):
     newFile = ROOT.TFile(ofile.replace('.root','-'+str(i)+'.root'),'RECREATE')
     newTree = sTree.CloneTree(0)
     for n in range(N,N+deltaN):
       rc = sTree.GetEntry(n)
       rc = newTree.Fill()
     newFile.Write()
     N+=deltaN
   os.chdir('../')

def recoStep(splitFactor=10):
 fnames = getFilesLocal()
 Nfiles = len(fnames)
 print "fileList established ",Nfiles
 for fname in fnames:
    os.chdir(fname)
    mcFile = 'ship.conical.MuonBack-TGeant4_dig_RT.root'
    ofile = 'ship.conical.MuonBack-TGeant4_dig.root'
    for i in range(splitFactor):
     recoFile = mcFile.replace('.root','-'+str(i)+'.root')
     if recoFile in os.listdir('.'):
      test = ROOT.TFile(recoFile)
      sTree = test.Get('cbmsim')
      if sTree:
       if sTree.GetBranch("FitTracks"): continue
      test.Close()
     os.system('cp '+ofile.replace('.root','-'+str(i)+'.root')+' '+recoFile)
     cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py -c recoStep1 -u 1 -f "+recoFile+' &'
     print 'step 2:', cmd
     os.system(cmd)
     while 1>0:
        if count_python_processes('drifttubeMonitoring')<ncpus: break 
        time.sleep(100)
    os.chdir('../')
 print "finished all the tasks."
def checkFilesWithTracks(D='.',splitFactor=10):
 fnames = getFilesLocal()
 Nfiles = len(fnames)
 fileList=[]
 for fname in fnames:
    os.chdir(fname)
    mcFile = 'ship.conical.MuonBack-TGeant4_dig_RT.root'
    for i in range(splitFactor):
     recoFile = mcFile.replace('.root','-'+str(i)+'.root')
     if recoFile in os.listdir('.'):
      print "check",fname,recoFile
      test = ROOT.TFile(recoFile)
      sTree = test.Get('cbmsim')
      if sTree:
       if sTree.GetBranch("FitTracks"): fileList.append(fname+'/'+recoFile)
    os.chdir('../')
 fileList.sort()
 return fileList

def makeMomDistributions(D='.',splitFactor=10):
 fileList=checkFilesWithTracks(D,splitFactor)
 print "fileList established ",len(fileList)
 for df in fileList:
   tmp = df.split('/')
   if len(tmp)>1: os.chdir(tmp[0])
   cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py -c anaResiduals -f "+tmp[1]+' &'
   print 'execute:', cmd
   os.system(cmd)
   while 1>0:
        if count_python_processes('drifttubeMonitoring')<ncpus: break 
        time.sleep(100)
   if len(tmp)>1: os.chdir('../')
 print "finished all the tasks."

def mergeHistos(case='residuals'):
 fileList=checkFilesWithTracks()
 if case == 'residuals':  cmd = 'hadd -f residuals.root '
 else:                    cmd = 'hadd -f momDistributions.root '
 for x in allFiles:
  if (case != 'residuals' and not x.find('analysis')<0 ):  histoFile = x.replace("/","/histos-analysis-")
  else:  histoFile = x.replace("/","/histos-")
  if not os.path.isfile(histoFile):continue
  cmd += x+" "

