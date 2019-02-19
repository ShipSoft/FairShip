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

def simulationStep(fnames=[]):
 if len(fnames)==0: fnames = getFilesFromEOS()
 Nfiles = len(fnames)
 print "fileList established ",Nfiles
 for fname in fnames:
    N = fnames[fname]-1
    odir = fname[fname.rfind('/')+1:].replace('.root','')
    cmd = "python $FAIRSHIP/macro/run_simScript.py -n "+str(N)+" --MuonBack --charm=1 --CharmdetSetup=0 --output "+odir+" -f "+fname+" &"
    print 'step 1:', cmd
    os.system(cmd)
    while 1>0:
        if count_python_processes('run_simScript')<ncpus: break 
        time.sleep(100)
 print "finished all the tasks."
def digiStep(fnames=[]):
 if len(fnames)==0: fnames = getFilesLocal()
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

def splitDigiFiles(splitFactor=10,fnames=[]):
 if len(fnames)==0: fnames = getFilesLocal()
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

def recoStep(splitFactor=10,fnames=[]):
 if len(fnames)==0: fnames = getFilesLocal()
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
     digiFile = ofile.replace('.root','-'+str(i)+'.root')
     if not digiFile in os.listdir('.'):
       print "digiFile missing",fname,digiFile
       continue
     os.system('cp '+ofile.replace('.root','-'+str(i)+'.root')+' '+recoFile)
     cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py -c recoStep1 -u 1 -f "+recoFile+' &'
     print 'step 2:', cmd,' in directory ',fname
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

def cleanUp():
 reco = checkFilesWithTracks()
 for f in reco:
  df = f.replace('_RT','')
  if os.path.isfile(df): os.system('rm ' +df)

def makeMomDistributions(D='.',splitFactor=10):
 fileList=checkFilesWithTracks(D,splitFactor)
 print "fileList established ",len(fileList)
 for df in fileList:
   tmp = df.split('/')
   if len(tmp)>1: os.chdir(tmp[0])
   if not "histos-analysis-"+tmp[1] in os.listdir('.'):
    cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py -c anaResiduals -f "+tmp[1]+' &'
    print 'execute:', cmd
    os.system(cmd)
   if len(tmp)>1: os.chdir('../')
   while 1>0:
        if count_python_processes('drifttubeMonitoring')<ncpus: break 
        time.sleep(100)
 print "finished all the tasks."

def mergeHistos(case='residuals'):
 dirList=getFilesLocal()
 cmd = {}
 for z in ['charm','mbias']:
  if case == 'residuals':  cmd[z] = 'hadd -f residuals-'+z+'.root '
  else:                    cmd[z] = 'hadd -f momDistributions-'+z+'.root '
 for d in dirList:
  for x in os.listdir(d):
   z='mbias'
   if d.find('charm')>0: z='charm'
   if (case != 'residuals' and not x.find('analysis')<0 ):  cmd[z] += d+'/'+x+" "
 for z in ['charm','mbias']: os.system(cmd[z])

def checkStatistics():
 # 1GeV mbias 1.8 Billion PoT charm 10.2 Billion PoT 
 simFiles = getFilesFromEOS()
 reco = checkFilesWithTracks()
 Nsim =  {'mbias':0,'charm':0}
 Nreco = {'mbias':0,'charm':0}
 for f in simFiles:
   if f.find('charm')>0: Nsim['charm']+=simFiles[f]
   else: Nsim['mbias'] += simFiles[f]
 allFiles = {}
 for a in simFiles.keys():
  x = a.split('/')
  allFiles[x[len(x)-1].replace('.root','')]=simFiles[a]
 for dname in allFiles:
  n = 0
  for x in reco:
    if  not x.find(dname)<0: n+=1
  fraction = n/float(splitFactor)
  if dname.find('charm')>0: Nreco['charm']+=fraction*allFiles[dname]
  else: Nreco['mbias'] += fraction*allFiles[dname]
 print "total statistics",Nsim
 print "                ",Nreco
 print "internal MC normalization, to be applied to charm", 10.2/1.8 * Nreco['charm']/Nsim['charm']*Nreco['mbias']/Nsim['mbias']
 # 1.218

