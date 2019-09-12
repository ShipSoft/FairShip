from __future__ import print_function
import os,subprocess,ROOT,time,multiprocessing,socket
ncpus = multiprocessing.cpu_count() - 2
interactive = not socket.gethostname().find('ubuntu')<0

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

def run_FixedTarget(start):
 N = 10000
 for n in range(start,start+ncpus):
   cmd = "python $FAIRSHIP/muonShieldOptimization/run_MufluxfixedTarget.py -n "+str(N)+" -e 1 -P -o run-"+str(n)+" &"
   os.system(cmd)
   while 1>0:
     if count_python_processes('run_MufluxfixedTarget')<ncpus: break
     time.sleep(100)
 print("finished all the tasks.")
def mergeFiles():
 N = 0
 cmd = 'hadd -f pythia8_Geant4_1000_1.0-XXX.root '
 for d in os.listdir('.'):
   if d.find('run')<0:continue
   if os.path.isdir(d):
     fname = d+'/pythia8_Geant4_1000_1.0.root'
     if  not os.path.isfile(fname): continue
     f = ROOT.TFile(fname)
     if f.Get('cbmsim'):
      cmd += fname+' '
      N+=1
 os.system(cmd.replace('XXX',str(N)))

def submit2Condor(eospath,directory,filename):
 sub = filename.replace('root','sub')
 f = open(sub,'w')
 f.write("executable            = /afs/cern.ch/user/t/trufship/muflux/runDriftTubeScript.sh\n")
 f.write("arguments             = "+command+" "+eospath+directory+"/"+filename+"\n")
 f.write("output                = "+filename.replace('root','out')+"\n")
 f.write("error                 = "+filename.replace('root','error')+"\n")
 f.write("log                   = "+filename.replace('root','log')+"\n")
 f.write("queue\n")
 f.close()
 os.system("condor_submit "+sub)

def getFilesFromEOS(E="10.0_withCharmandBeauty"):   # E="1.0"
# list of files
 temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospath,shell=True)
 for x in temp.split('\n'):
  if x.find(E)<0 or x.find('_mu')<0: continue # includes charm
  fname =  x[x.find('/eos'):]
  nentries = 0
  f=ROOT.TFile.Open(os.environ['EOSSHIP']+fname)
  nentries=f.cbmsim.GetEntries()
  fileList[fname]=nentries
 return fileList

def getFilesLocal(d='.'):
# list of files
 fl = []
 temp = os.listdir(d)
 for x in temp:
  if os.path.isdir(d+'/'+x): fl.append(x)
 return fl

def getFilesEOS(D):
 eospathSim = '/eos/experiment/ship/user/truf/muflux-sim/'+D
 temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathSim,shell=True)
 fl = []
 for x in temp.split('\n'):
   if x.find('pythia8_Geant4')<0: continue
   d = x[x.rfind('/')+1:]
   fl.append(eospathSim+'/'+d)
 return fl

def simulationStep(fnames=[]):
 if len(fnames)==0: fnames = getFilesFromEOS()
 Nfiles = len(fnames)
 print("fileList established ",Nfiles)
 for fname in fnames:
    N = fnames[fname]-1
    odir = fname[fname.rfind('/')+1:].replace('.root','')
    if odir in os.listdir('.'): continue
    cmd = "python $FAIRSHIP/macro/run_simScript.py -n "+str(N)+" --MuonBack --charm=1 --CharmdetSetup=0 --output "+odir+" -f "+fname+" &"
    print('step 1:', cmd)
    os.system(cmd)
    while 1>0:
        if count_python_processes('run_simScript')<ncpus: break
        time.sleep(100)
 print("finished all the tasks.")
def digiStep(fnames=[]):
 if len(fnames)==0: fnames = getFilesLocal()
 Nfiles = len(fnames)
 print("fileList established ",Nfiles)
 for fname in fnames:
    os.chdir(fname)
    mcFile = 'ship.conical.MuonBack-TGeant4.root'
    geoFile = 'geofile_full.conical.MuonBack-TGeant4.root'
    cmd = "python $FAIRSHIP/macro/runMufluxDigi.py -n 9999999 -f "+mcFile+" -g "+geoFile+" &"
    print('step 2:', cmd)
    os.system(cmd)
    os.chdir('../')
    while 1>0:
        if count_python_processes('runMufluxDigi')<ncpus: break 
        time.sleep(100)
 print("finished all the tasks.")

def findDirWithSim():
 fnames = getFilesLocal()
 stats = {'simOnly':[],'tmp':[],'failed':[],'digi':[],'digireco':{}}
 for fname in fnames:
   geo  = False
   digi = False
   tmp  = False
   digiSplit = 0
   reco = 0
   for x in os.listdir(fname):
      if not x.find('geofile_full.conical.MuonBack-TGeant4')<0: geo = True
      if not x.find('roottmp')<0: tmp  = True
      if not x.find('dig.root')<0:       digi    = True
      if not x.find('dig_RT')<0:         reco+=1
      if not x.find('dig-')<0:         digiSplit+=1
   if tmp: stats['tmp'].append(fname)
   elif digi: stats['digi'].append(fname)
   elif geo: 
      if reco==0 and digiSplit==0: stats['simOnly'].append(fname)
   else : stats['failed'].append(fname)
   stats['digireco'][fname]=[digiSplit,reco]
 for x in stats['tmp']:
   f = ROOT.TFile(x+'/ship.conical.MuonBack-TGeant4.roottmp')
   try: 
    if f.cbmsim.GetEntries()>0: 
       print('tmp file ok, replace root file',x)
       os.system('mv '+x+'/ship.conical.MuonBack-TGeant4.roottmp '+x+'/ship.conical.MuonBack-TGeant4.root')
   except:
    print('tmp file not ok',x)
 return stats

def splitDigiFiles(splitFactor=5,fnames=[]):
 if len(fnames)==0: fnames = getFilesLocal()
 Nfiles = len(fnames)
 print("fileList established ",Nfiles)
 for fname in fnames:
   os.chdir(fname)
   ofile = 'ship.conical.MuonBack-TGeant4_dig.root'
   if not ofile in os.listdir('.'): 
     os.chdir('../')
     continue
   origin = ROOT.TFile(ofile)
   if not origin.GetKey('cbmsim'):
     print("corrupted file",fname)
     os.chdir('../')
     continue
   sTree = origin.cbmsim
   Nentries = sTree.GetEntries()
   N = 0
   deltaN = int(sTree.GetEntries()/float(splitFactor))
   for i in range(splitFactor):
    nf = ofile.replace('.root','-'+str(i)+'.root')
    if nf in os.listdir('.'): 
       print("file exists",fname,nf)
    else:
     newFile = ROOT.TFile(nf,'RECREATE')
     newTree = sTree.CloneTree(0)
     for n in range(N,N+deltaN):
       rc = sTree.GetEntry(n)
       rc = newTree.Fill()
     newFile.Write()
    N+=deltaN
   os.chdir('../')

def recoStep(splitFactor=5,fnames=[],eospath=False):
 if len(fnames)==0: fnames = getFilesLocal()
 Nfiles = len(fnames)
 print("fileList established ",Nfiles)
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
     if digiFile in os.listdir('.'): 
        os.system('cp '+ofile.replace('.root','-'+str(i)+'.root')+' '+recoFile)
     elif not recoFile in os.listdir('.'):
       if eospath:
        os.system('xrdcp  $EOSSHIP'+eospath+'/'+fname+'/'+digiFile+ ' '+recoFile)
       else:
        print("digiFile missing",fname,digiFile)
        continue
     cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py -c recoStep1 -u 1 -f "+recoFile+' &'
     print('step 2:', cmd,' in directory ',fname)
     os.system(cmd)
     while 1>0:
        if count_python_processes('drifttubeMonitoring')<ncpus: break 
        time.sleep(100)
    os.chdir('../')
 print("finished all the tasks.")

def checkFilesWithTracks(D='.',splitFactor=5,dimuon=False):
 eos = ''
 if D=='.': fnames = getFilesLocal()
 elif D.find('1GeV')==0 or D.find('10GeV')==0: 
   fnames = getFilesEOS(D)
   eos = os.environ['EOSSHIP']
 Nfiles = len(fnames)
 fileList=[]
 fileListPer={}
 failedList = []
 for fname in fnames:
    fileListPer[fname]={}
    mcFile = 'ship.conical.MuonBack-TGeant4_dig_RT.root'
    for i in range(splitFactor):
     recoFile = fname+'/'+mcFile.replace('.root','-'+str(i)+'.root')
     if dimuon: recoFile = recoFile.replace('.root','_dimuon99.root')
     if D=='.': dirList = os.listdir(fname)
     else: dirList = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls "+fname,shell=True)
     if recoFile.replace(fname+'/','') in dirList:
      test = ROOT.TFile.Open(eos+recoFile)
      if not test: continue
      sTree = test.Get('cbmsim')
      if sTree:
       if sTree.GetBranch("FitTracks"): 
        fileList.append(recoFile)
        size = sTree.GetBranch('FitTracks').GetTotalSize()/float(sTree.GetEntries())
        fileListPer[fname][recoFile.replace(D+'.'+fname+'/','')]=size
        # print "check",fname,recoFile,size
      else:
        failedList.append(fname+'/'+recoFile)
 fileList.sort()
 return fileList,fileListPer,failedList

def cleanUp():
 reco,x,y = checkFilesWithTracks()
 for f in reco:
  df = f.replace('_RT','')
  if os.path.isfile(df): os.system('rm ' +df)

def makeHistos(D='.',splitFactor=5,command="anaResiduals"):
 commandToHist = {"anaResiduals":"histos-analysis-","momResolution":"histos-momentumResolution-","plotDTPoints":"histos-DTPoints-"}
 if D=='.':
  fileList,x,y = checkFilesWithTracks(D,splitFactor)
  print("fileList established ",len(fileList))
  for df in fileList:
   tmp = df.split('/')
   if len(tmp)>1: os.chdir(tmp[0])
   if not commandToHist[command]+tmp[1] in os.listdir('.'):
    cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py -c "+command+" -f "+tmp[1]+' &'
    print('execute:', cmd)
    os.system(cmd)
   if len(tmp)>1: os.chdir('../')
   while 1>0:
        if count_python_processes('drifttubeMonitoring')<ncpus: break 
        time.sleep(100)
 elif D.find('1GeV')==0 or D.find('10GeV')==0:
  eospathSim = '/eos/experiment/ship/user/truf/muflux-sim/'+D
  temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathSim,shell=True)
  for x in temp.split('\n'):
   if x.find('pythia8_Geant4')<0: continue
   d = x[x.rfind('/')+1:]
   if not d in os.listdir('.'): os.system('mkdir '+d)
   os.chdir(d)
   temp2 = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathSim+'/'+d,shell=True)
   fileList = []
   for y in temp2.split('\n'):
    f = os.environ['EOSSHIP'] + y[y.find('/eos'):]
    if not f.find('histos')<0: continue
    if  f.find('RT')<0: continue
    histFile = commandToHist[command]+y[y.rfind('/')+1:]
    if histFile in os.listdir('.') : continue
    if interactive:
     cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py -c "+command+" -f "+f+' &'
     print('execute:', cmd)
     os.system(cmd)
     while 1>0:
        if count_python_processes('drifttubeMonitoring')<ncpus: break 
        time.sleep(100)
    else: submit2Condor(eospathSim,d,y[y.rfind('/')+1:])
   os.chdir('../')
 else:
  eospathSim10GeV = '/eos/experiment/ship/data/muflux/MC/19feb2019'
  fileList = []
  temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathSim10GeV,shell=True)
  for x in temp.split('\n'):
   if x.find('RT.root')<0: continue
   fileList.append( os.environ['EOSSHIP'] + x[x.find('/eos'):])
  for fname in fileList:
    if os.path.isfile(commandToHist[command]+fname[fname.rfind('/')+1:]): continue
    cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py -c "+command+" -f "+fname+' &'
    print('command:', cmd)
    os.system(cmd)
    while 1>0:
        if count_python_processes('drifttubeMonitoring')<ncpus: break 
        time.sleep(10)
 print("finished all the tasks.")

def makeMomResolutions(D='.',splitFactor=5):
 if D=='.':
  fileList,x,y = checkFilesWithTracks(D,splitFactor)
  print("fileList established ",len(fileList))
  for df in fileList:
   tmp = df.split('/')
   if len(tmp)>1: os.chdir(tmp[0])
   if not "histos-momentumResolution-"+tmp[1] in os.listdir('.'):
    cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py -c momResolution -f "+tmp[1]+' &'
    print('execute:', cmd)
    os.system(cmd)
   if len(tmp)>1: os.chdir('../')
   while 1>0:
        if count_python_processes('drifttubeMonitoring')<ncpus: break 
        time.sleep(100)
 elif D=='1GeV' or D=='10GeV':
  eospathSim = '/eos/experiment/ship/user/truf/muflux-sim/'+D
  temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathSim,shell=True)
  for x in temp.split('\n'):
   if x.find('pythia8_Geant4')<0: continue
   d = x[x.rfind('/')+1:]
   if not d in os.listdir('.'): os.system('mkdir '+d)
   os.chdir(d)
   temp2 = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathSim+'/'+d,shell=True)
   fileList = []
   for y in temp2.split('\n'):
    f = os.environ['EOSSHIP'] + y[y.find('/eos'):]
    if not f.find('histos')<0: continue
    if  f.find('RT')<0: continue
    histFile = 'histos-momentumResolution-'+y[y.rfind('/')+1:]
    if histFile in os.listdir('.') : continue
    cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py --c momResolution -f "+f+' &'
    print('execute:', cmd)
    os.system(cmd)
    while 1>0:
        if count_python_processes('drifttubeMonitoring')<ncpus: break 
        time.sleep(100)
   os.chdir('../')
 print("finished all the tasks.")


def checkAlignment(D='.',splitFactor=5):
 if D=='.':
  fileList,x,y = checkFilesWithTracks(D,splitFactor)
  print("fileList established ",len(fileList))
  for df in fileList:
   tmp = df.split('/')
   if len(tmp)>1: os.chdir(tmp[0])
   if not "histos-residuals-"+tmp[1] in os.listdir('.'):
    cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py -c alignment -f "+tmp[1]+' &'
    print('execute:', cmd)
    os.system(cmd)
   if len(tmp)>1: os.chdir('../')
   while 1>0:
        if count_python_processes('drifttubeMonitoring')<ncpus: break 
        time.sleep(100)
 elif D=='1GeV':
  eospathSim1GeV = '/eos/experiment/ship/user/truf/muflux-sim/1GeV'
  temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathSim1GeV,shell=True)
  for x in temp.split('\n'):
   if x.find('pythia8_Geant4')<0: continue
   d = x[x.rfind('/')+1:]
   if not d in os.listdir('.'): os.system('mkdir '+d)
   os.chdir(d)
   temp2 = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathSim1GeV+'/'+d,shell=True)
   fileList = []
   for y in temp2.split('\n'):
    f = os.environ['EOSSHIP'] + y[y.find('/eos'):]
    if not f.find('histos')<0: continue
    if  f.find('RT')<0: continue
    histFile = 'histos-residuals-'+y[y.rfind('/')+1:]
    if histFile in os.listdir('.') : continue
    cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py -c alignment -f "+f+' &'
    print('execute:', cmd)
    os.system(cmd)
    while 1>0:
        if count_python_processes('drifttubeMonitoring')<ncpus: break 
        time.sleep(100)
   os.chdir('../')
 print("finished all the tasks.")


def exportToEos(destination="/eos/experiment/ship/user/truf/muflux-sim/1GeV",update=True):
  remote = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+destination,shell=True).split('\n')
  fnames = getFilesLocal()
  for D in fnames:
    if not D in remote:
       os.system("xrdfs "+os.environ['EOSSHIP']+" mkdir  "+destination+"/"+D)
    remoteD = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+destination+'/'+D,shell=True).split('\n')
    for f in os.listdir(D):
      if f in remoteD and update: continue
      fname = D+'/'+f
      cmd = "xrdcp -f "+fname+" $EOSSHIP/"+destination+"/"+fname
      os.system(cmd)

def mergeHistos(command="anaResiduals"):
 commandToHist = {"anaResiduals":"histos-analysis-","momResolution":"histos-momentumResolution-","plotDTPoints":"histos-DTPoints-"}
 commandToSum  = {"anaResiduals":"momDistributions-","momResolution":"momentumResolution-","plotDTPoints":"DTPoints-","alignment":"residuals-"}
 dirList=getFilesLocal()
 cmd = {}
 for z in ['charm','mbias']:
  cmd[z] = 'hadd -f '+commandToSum[command]+z+'.root '
 for d in dirList:
  for x in os.listdir(d):
   z='mbias'
   if d.find('charm')>0: z='charm'
   if (not x.find(commandToHist[command])<0 ):  cmd[z] += d+'/'+x+" "
 for z in ['charm','mbias']:
     os.system(cmd[z])

import rootUtils as ut
def checkHistos():
 dirList=getFilesLocal()
 Ntot = 0
 shit = []
 for d in dirList:
  nfailed = 0
  for x in os.listdir(d):
    if not x.find('histos-analysis-')<0:
        h={}
        ut.readHists(h,d+'/'+x,['p/pt'])
        N = h['p/pt'].GetEntries()
        if N == 0: nfailed+=1
        print(d+'/'+x,N)
        Ntot+=N
  print(nfailed)
  if nfailed == 10: shit.append(d)
 print(Ntot)
 return shit



def checkForFilesWithTracks():
  eospathSim10GeV = '/eos/experiment/ship/data/muflux/MC/19feb2019'
  fileList = []
  trList = []
  temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathSim10GeV,shell=True)
  for x in temp.split('\n'):
   if x.find('RT.root')<0: continue
   fname = os.environ['EOSSHIP'] + x[x.find('/eos'):]
   fileList.append( fname )
   test = ROOT.TFile.Open(fname)
   if test.GetKey('cbmsim'): 
     if test.cbmsim.GetBranch('FitTracks'): trList.append(fname)
  print(len(fileList),len(trList))

def mergeHistos10(case='residuals'):
 N = 1
 n = 0
 for x in os.listdir('.'):
  if n==0:
   if case == 'residuals':  cmd = 'hadd -f residuals-'+str(N)+'.root '
   elif case == 'momResolution':  cmd = 'hadd -f momentumResolution-'+str(N)+'.root '
   else:                    cmd = 'hadd -f momDistributions-'+str(N)+'.root '
  if (case == 'residuals' and not x.find('histos-residuals')<0 ):  cmd += x+" "
  elif (case == 'momResolution' and not x.find('momentumResolution')<0 ):  cmd += x+" "
  elif (case == 'momDistribution' and not x.find('analysis')<0 ):  cmd += x+" "
  n+=1
  if n==500:
   os.system(cmd)
   n=0
   N+=1
 if case == 'residuals':        histname = 'residuals.root '
 elif case == 'momResolution':  histname = 'momentumResolution.root '
 else:                          histname = 'momDistributions.root '
 cmd = 'hadd -f '+histname
 for n in range(1,N+1):
    cmd += histname.replace('.','-'+str(N)+'.')
 os.system(cmd)
def redoMuonTracks():
 fileList,x,y = checkFilesWithTracks(D='.')
 for df in fileList:
   tmp = df.split('/')
   if len(tmp)>1: 
    os.chdir(tmp[0])
    cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py -c  recoMuonTaggerTracks -u 1 -f "+tmp[1]+' &'
    print('execute:', cmd)
    os.system(cmd)
    os.chdir('../')
   while 1>0:
        if count_python_processes('drifttubeMonitoring')<ncpus: break 
        time.sleep(100)
 print("finished all the tasks.")

def splitOffBoostedEvents(splitFactor=5,check=False):
 remote = "/home/truf/ship-ubuntu-1710-32/muflux/simulation/"
 dirList=getFilesLocal(remote)
 for d in dirList:
   if not os.path.isdir(d): os.system('mkdir '+d)
   os.chdir(d)
   for f in os.listdir(remote+'/'+d):
    if f.find('histo')<0 and not f.find('ship.conical')<0:
     if not check:
      os.system('cp '+remote+'/'+d+'/'+f+' .')
      cmd = "python /home/truf/muflux/simulation/drifttubeMonitoring.py -c  splitOffBoostedEvents -f "+f+' &'
      print('execute:', cmd)
      os.system(cmd)
      while 1>0:
        if count_python_processes('drifttubeMonitoring')<ncpus: break 
        time.sleep(100)
     else:
      # check
      f99 = f.replace('.root','_dimuon99.root')
      f1 = f.replace('.root','_dimuon1.root')
      l = os.listdir('.')
      if not f in l or not f99 in l or f1 in l:
        print('something wrong',d,f)
        print(f,f in l) 
        print(f99,f99 in l) 
        print(f1,f1 in l) 
   os.chdir('../')


def checkStatistics(splitFactor=5):
 # 1GeV mbias 1.8 Billion PoT charm 10.2 Billion PoT 
 simFiles = getFilesFromEOS()  # input data
 reco,x,y = checkFilesWithTracks()  # 
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
  print("fraction:",dname,fraction)
  if dname.find('charm')>0: Nreco['charm']+=fraction*allFiles[dname]
  else: Nreco['mbias'] += fraction*allFiles[dname]
 print("total statistics, simulated     ",Nsim)
 print("                , reconstructed ",Nreco)
 # mbias statistics = 1.8 * Nreco/Nsim, charm statistics = 10.2 * Nreco/Nsim
 # norm factor = 1/charm statistics * mbias statistics
 print("internal MC normalization, to be applied to charm", 1.8*Nreco['mbias']/Nsim['mbias'] /(10.2*Nreco['charm']/Nsim['charm']))
