
import os,subprocess,ROOT,time,multiprocessing
from rootpyPickler import Unpickler
from rootpyPickler import Pickler
import pwd
ncpus = int(multiprocessing.cpu_count()*3./4.)

pathToMacro = '$FAIRSHIP/charmdet/'
def count_python_processes(macroName):
 username = pwd.getpwuid(os.getuid()).pw_name
 callstring = "ps -f -u " + username
# only works if screen is wide enough to print full name!
 status = subprocess.check_output(callstring,shell=True)
 n=0
 for x in status.split('\n'):
   if not x.find(macroName)<0 and not x.find('python') <0: n+=1
 return n

fileList = {}
badFiles = []
run = "RUN_8000_2395" # "RUN_8000_2396"

eospath='/eos/experiment/ship/data/muflux/DATA_Rebuild_8000/rootdata/'+run 

def getFilesFromEOS():
# list of files
 temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospath,shell=True)
 for x in temp.split('\n'):
  if x.find('.root')<0: continue
  if not x.find('START')<0: continue
  fname =  x[x.find('/eos'):]
  nentries = 0
  try: 
   f=ROOT.TFile.Open(os.environ['EOSSHIP']+fname)
   nentries=f.cbmsim.GetEntries()
   fileList[fname]=nentries
  except:
   print "problem accessing file",fname
   badFiles.append(fname)

 Nfiles = len(fileList)

 tmp = {}
 for fname in fileList:
  newName = fname[fname.rfind('/')+1:]
  rc = os.system("xrdcp -f $EOSSHIP"+fname+" "+newName)
  tmp[newName]=fileList[fname]

 fnames = tmp.keys()
 fnames.sort()
 return tmp,fnames

def getFilesLocal():
# list of files
 for fname in os.listdir('.'):
  if fname.find('.root')<0: continue
  if not fname.find('_RT')<0: continue
  test = fname.replace('.root','_RT.root')
  if os.path.isfile(test): continue
  nentries = 0
  try: 
   f=ROOT.TFile.Open(fname)
   nentries=f.cbmsim.GetEntries()
   fileList[fname]=nentries
  except:
   print "problem accessing file",fname
   badFiles.append(fname)

 Nfiles = len(fileList)

 fnames = fileList.keys()
 fnames.sort()
 return fileList,fnames

def recoStep0(local=False):
 if local: tmp,fnames = getFilesLocal()
 else:     tmp,fnames = getFilesFromEOS()
 Nfiles = len(fnames)
 print "fileList established ",Nfiles
 Ndone = 0
 while Ndone < Nfiles:
  cmd = "python  "+pathToMacro+"drifttubeMonitoring.py -c recoStep0 -f "
# group files to get better stats
  Ntot = 0
  sample = []
  i = 0
  for k in range(Ndone,Nfiles):
    Ntot += tmp[fnames[k]]
    sample.append(fnames[k])
    i+=1
    if Ntot>350000: break
  Ndone += i
  # check that enough files remain
  Nextsample = []
  Ntot = 0
  for k in range(Ndone,Nfiles): 
    Ntot += tmp[fnames[k]]
    Nextsample.append(fnames[k])
    if Ntot>350000: break
  if Ntot < 350000:
    for s in Nextsample: sample.append(s)
    Ndone += len(Nextsample)
  if len(sample)==0: break
  for s in sample: cmd+=s+','
  print 'step 0:',cmd[:cmd.rfind(',')],Ndone,Nfiles
  os.system(cmd[:cmd.rfind(',')]+" &")
  while 1>0:
   if count_python_processes('drifttubeMonitoring')<ncpus: break
   time.sleep(200)
  if Ndone%100==0: cleanUp()
 while count_python_processes('drifttubeMonitoring')>0: time.sleep(200)
 print "files created with RT relations "
 cleanUp()

def checkFilesWithRT():
 fok = []
 fNotok = []
 fRaw = []
 for fname in os.listdir('.'):
   if not fname.find('histo')<0: continue
   if not fname.find('_RT')<0:
    f=ROOT.TFile(fname)
    RT = f.Get('tMinAndTmax')
    if RT:
     fok.append(fname)
    else:
     fNotok.append(fname)
   elif fname.find('root')>0 and not fname.find('SPILL')<0:
    fRaw.append(fname)
 print len(fok),len(fNotok),len(fRaw)
 return fok,fNotok,fRaw

def checkMinusTwo():
 fok,fNotok,fRaw = checkFilesWithRT()
 for fname in fRaw:
  if fname in fok: continue
  N=0
  f=ROOT.TFile(fname)
  sTree = f.cbmsim
  for n in range(sTree.GetEntries()):
   rc = sTree.GetEvent(n)
   for m in sTree.Digi_MufluxSpectrometerHits:
     if m.GetDetectorID()<0: N+=1
  print sTree.GetCurrentFile(),N


def recoStep1():
 fileList=[]
 # all RT files
 for x in os.listdir('.'):
  if x.find('_RT')>0 and x.find('histos')<0: 
    test = ROOT.TFile(x)
    if test.cbmsim.GetBranch("FitTracks"): continue
    fileList.append(x)
 fileList.sort()
 for fname in fileList:
    cmd = "python "+pathToMacro+"drifttubeMonitoring.py -c recoStep1 -u 1 -f "+fname+' &'
    print 'step 1:', cmd
    os.system(cmd)
    time.sleep(100)
    while 1>0:
        if count_python_processes('drifttubeMonitoring')<ncpus: break 
        time.sleep(100)
 print "finished all the tasks."

def checkAlignment(fileList=[]):
 # all RT files
 if len(fileList)==0:
  for x in os.listdir('.'):
   if x.find('_RT')>0 and x.find('histos-residuals')<0:
    fileList.append(x)
 fileList.sort()
 for fname in fileList:
    cmd = "python "+pathToMacro+"drifttubeMonitoring.py -c alignment -f "+fname+' &'
    print 'make residual plots:', cmd
    os.system(cmd)
    time.sleep(10)
    while 1>0:
        if count_python_processes('drifttubeMonitoring')<ncpus: break 
        time.sleep(100)
 print "finished all the tasks."

def runMC():
 # fast MC
 inputFile = "/eos/experiment/ship/data/Mbias/background-prod-2018/pythia8_Geant4_10.0_withCharmandBeauty0_mu.root" # entries 13450391L
 os.system("python $FAIRSHIP/macro/run_simScript.py -n 100000 --MuonBack --charm=1 --CharmdetSetup=0 -f "+inputFile) 
 # full simulation
 os.system("python $SHIPBUILD/FairShip/macro/run_simScript.py --Muflux -n 1000 --charm=1 --CharmdetSetup=0 --charm=1 --CharmdetSetup=0")

def checkFilesWithTracks(D='.'):
 fileList=[]
 rest=[]
 zombie=[]
 # all RT files
 if D.find('eos')<0:
  for x in os.listdir(D):
   if x.find('_RT')>0 and x.find('histos')<0: 
    test = ROOT.TFile(D+'/'+x)
    if not test.GetKey('cbmsim'):
       zombie.append(x)
    elif test.cbmsim.GetBranch("FitTracks"): fileList.append(x)
    else: rest.append(x)
 else:
  temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+D,shell=True)
  for x in temp.split('\n'):
   if x.find('.root')<0: continue
   fname =  x[x.find('/eos'):]
   try: 
    test=ROOT.TFile.Open(os.environ['EOSSHIP']+fname)
    if not test.GetKey('cbmsim'):
       zombie.append(fname)
    elif test.cbmsim.GetBranch("FitTracks"): fileList.append(fname)
    else: rest.append(fname)
   except:zombie.append(fname)
 fileList.sort()
 print "n with tracks",len(fileList),' rest:',len(rest),' zombies:',zombie
 return fileList

def checkFilesWithTracks2(D='.'):
 badFile=[]
 # all RT files
 for x in os.listdir(D):
  if x.find('_RT')>0 and x.find('histos')<0: 
   test = ROOT.TFile(D+'/'+x)
   sTree = test.cbmsim
   if not sTree: badFile.append(x+"?")
   elif sTree.GetBranch("FitTracks"): 
     prev = 0
     for n in range(min(20000,sTree.GetEntries())):
        rc = sTree.GetEvent(n)
        if sTree.FitTracks.GetEntries()>0:
         st = sTree.FitTracks[0].getFitStatus()
         if not st.isFitConverged(): continue
         if prev==st.getChi2():
          badFile.append(x)
          break
         else: prev=st.getChi2()
 return badFile
def checkFilesWithTracks3(D='.'):
 badFile={}
 # all RT files
 for x in os.listdir(D):
  if x.find('_RT')>0 and x.find('histos')<0: 
   test = ROOT.TFile(D+'/'+x)
   sTree = test.cbmsim
   if not sTree: 
    badFile.append(x+"?")
    continue
   b = sTree.GetBranch("FitTracks")
   if b:
    if b.GetZipBytes()/1.E6 < 1.: badFile[x]= b.GetZipBytes()/1.E6
 return badFile
# for f in bf: os.system('cp ../../ship-ubuntu-1710-64/RUN_8000_2395/'+f+' .')

def cleanUp(D='.'):
# remove raw data files for files with RT relations
   fok,fNotok,fRaw = checkFilesWithRT()
   for x in fok:
     r = x.replace('_RT','')
     cmd = 'rm '+r
     os.system(cmd)

def copyMissingFiles(remote="../../ship-ubuntu-1710-64/RUN_8000_2395",exclude=[]):
 toCopy=[]
 allFilesR = os.listdir(remote)
 allFilesL = os.listdir(".")
 for fname in allFilesR:
   if not fname.find('histos')<0: continue
   if fname.find('RT')<0: continue
   if fname in exclude: continue
   if not fname in allFilesL: toCopy.append(fname)
 print "len",len(toCopy)
 for fname in toCopy: os.system('cp '+remote+"/"+fname+' .')

def importRTFiles(local='.',remote='/home/truf/ship-ubuntu-1710-32/home/truf/muflux/Jan08'):
# mkdir /media/truf/disk2/home/truf/ShipSoft/ship-ubuntu-1710-32
# sshfs  ship-ubuntu-1710-32.cern.ch:/home/truf/muflux /media/truf/disk2/home/truf/ShipSoft/ship-ubuntu-1710-32
 fileWithTracks = checkFilesWithTracks(local)
 allFiles = os.listdir(remote)
 for x in allFiles:
  if x.find('_RT')>0 and x.find('histos')<0 and not x in fileWithTracks:
    os.system('cp '+remote+'/'+x+' .')

def importRecoFiles(local='.',remote='/media/truf/disk2/home/truf/ShipSoft/ship-ubuntu-1710-16/home/truf/muflux/Jan08'):
 fileWithTracks = checkFilesWithTracks(remote)
 for x in fileWithTracks:  os.system('cp '+remote+'/'+x+' .')

def mergeHistos(local='.',case='residuals'):
 allFiles = os.listdir(local)
 if case == 'residuals':  
     dest = 'residuals.root'
     tag = 'histos-residuals'
 else:  
     dest = 'momDistributions.root'
     tag = 'histos-analysis'
 cmd = "hadd -f "+dest+' '
 N=0
 for x in allFiles:
  if not x.find(tag)<0 : 
     cmd += (local+'/'+x+' ')
     N+=1
  if N>500:
    os.system(cmd)
    os.system('cp '+dest+' tmp.root')
    cmd = "hadd -f "+dest+' tmp.root '
    N=0
 os.system(cmd)

def checkRecoRun(eosLocation=eospath,local='.'):
 temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eosLocation,shell=True)
 for x in temp.split('\n'):
  if x.find('.root')<0: continue
  if not x.find('START')<0: continue
  fname      =  x[x.rfind('/')+1:]
  RTname     = fname.replace('.root','_RT.root')
  histosName = "histos-residuals-"+RTname
  if not os.path.isfile(RTname): 
     print "missing RT file",fname
  if not os.path.isfile(histosName): 
     print "missing histogram file",fname
def exportRunToEos(eosLocation="/eos/experiment/ship/user/truf/muflux-reco",run=run,local="."):
 temp = os.system("xrdfs "+os.environ['EOSSHIP']+" mkdir "+eosLocation+"/"+run)
 failures = []
 for x in os.listdir(local):
  if x.find('.root')<0: continue
  cmd = "xrdcp -f "+x+" $EOSSHIP/"+eosLocation+"/"+run+"/"+x
  rc = os.system(cmd)
  if rc != 0: failures.append(x)
 if len(failures)!=0: print failures

def makeMomDistributions(run=0):
 if run==0: fileList = checkFilesWithTracks(D='.')
 else:
  eospathReco = '/eos/experiment/ship/user/odurhan/muflux-recodata/'+run
  fileList = []
  temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathReco,shell=True)
  for x in temp.split('\n'):
   if x.find('.root')<0: continue
   fileList.append( os.environ['EOSSHIP'] + x[x.find('/eos'):])
 # all RT files with tracks
 for fname in fileList:
    if not fname.find('sys')<0: continue
    if os.path.isfile('histos-analysis-'+fname[fname.rfind('/')+1:]): continue
    cmd = "python "+pathToMacro+"drifttubeMonitoring.py -c anaResiduals -f "+fname+' &'
    print 'momentum analysis:', cmd
    os.system(cmd)
    time.sleep(10)
    while 1>0:
        if count_python_processes('drifttubeMonitoring')<ncpus: break 
        time.sleep(10)
 print "finished all the tasks."

zeroField = ['2199','2200','2201']
noRPC = ['2144','2154','2192','2210','2217','2218','2235','2236','2237','2240','2241','2243','2291','2345','2359']
def massProduction(keyword = 'RUN_8000_23',fnames=[],merge=False):
 pathToMacro = "$FAIRSHIP/charmdet/"
 eospathReco = '/eos/experiment/ship/user/odurhan/muflux-recodata/'
 if merge:
    for run in os.listdir('.'):
      if run.find(keyword)<0: continue
      os.chdir(run)
      mergeHistos(local='.',case='momDistributions')
      os.chdir('../')
 else:
  if len(fnames)==0:
   temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathReco,shell=True)
   fnames = temp.split('\n')
  for x in fnames:
   if x.find(keyword)<0: continue
   run = x[x.rfind('/')+1:]
   if not run in os.listdir('.'): os.system('mkdir '+run)
   temp2 = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathReco+run,shell=True)
   if temp2.find('.root')<0: continue
   skip = False
   for x in zeroField:
       if not run.find(x)<0: skip = True
   if skip: continue
   os.chdir(run)
   makeMomDistributions(run)
   os.chdir('../')
def massProductionAlignment(keyword = 'RUN_8000_2395',fnames=[],merge=False):
  pathToMacro = "$FAIRSHIP/charmdet/"
  eospathReco = '/eos/experiment/ship/user/odurhan/muflux-recodata/'
  if merge:
    for run in os.listdir('.'):
      if run.find(keyword)<0: continue
      os.chdir(run)
      mergeHistos(local='.')
      os.chdir('../')
  else:
   if len(fnames)==0:
    temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathReco,shell=True)
    fnames = temp.split('\n')
   for x in fnames:
    if x.find(keyword)<0: continue
    run = x[x.rfind('/')+1:]
    if not run in os.listdir('.'):
         print "directory for this run does not exist",run
         # os.system('mkdir '+run)
         continue
    temp2 = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathReco+run,shell=True)
    if temp2.find('.root')<0: continue
    os.chdir(run)
    fileList = []
    for x in temp2.split('\n'):
     if x.find('.root')<0: continue
     fileList.append( os.environ['EOSSHIP'] + x[x.find('/eos'):])
    checkAlignment(fileList)
    os.chdir('../')

def redoMuonTracks():
 fileList = checkFilesWithTracks(D='.')
 for fname in fileList:
    cmd = "python "+pathToMacro+"drifttubeMonitoring.py -c  recoMuonTaggerTracks -u 1 -f "+fname+' &'
    print 'redo muonTracks:', cmd
    os.system(cmd)
    time.sleep(10)
    while 1>0:
        if count_python_processes('drifttubeMonitoring')<ncpus: break 
        time.sleep(10)
 print "finished all the tasks."

def reRunReco(r,fname):
 fRT = fname.replace('.root','_RT2.root')
 os.system('xrdcp -f $EOSSHIP/eos/experiment/ship/data/muflux/DATA_Rebuild_8000/rootdata/'+r+'/'+fname+' '+fRT)
 f = ROOT.TFile.Open(os.environ['EOSSHIP']+'/eos/experiment/ship/user/odurhan/muflux-recodata/'+r+'/'+fname.replace('.root','_RT.root'))
 ftemp = ROOT.TFile(fRT,'update')
 ftemp.cd('')
 upkl    = Unpickler(f)
 tMinAndTmax = upkl.load('tMinAndTmax')
 pkl = Pickler(ftemp)
 pkl.dump(tMinAndTmax,'tMinAndTmax')
 ftemp.mkdir('histos')
 ftemp.histos.cd('')
 for tc in ['TDCMapsX','hitMapsX']:
    tmp = f.histos.Get(tc)
    X = tmp.Clone()
    X.Write()
 ftemp.Write("",ROOT.TFile.kOverwrite)
 ftemp.Close()
 cmd = "python "+pathToMacro+"drifttubeMonitoring.py -c recoStep1 -u 1 -f "+fRT+' &'
 os.system(cmd)
 print 'step 1:', cmd

def pot():
 fileList=[]
 # all RT files
 for x in os.listdir('.'):
  if x.find('_RT')>0 and x.find('histos')<0: 
    fileList.append(x)
 fileList.sort()
 scalerStat = {}
 for fname in fileList:
   f=ROOT.TFile(fname)
   if not f.FindKey("scalers"):
     print "no scalers in this file",fname
     continue
   scalers = f.scalers
   scalers.GetEntry(0)
   for x in scalers.GetListOfBranches():
    name = x.GetName()
    s = eval('scalers.'+name)
    if name!='slices':
     if not scalerStat.has_key(name):scalerStat[name]=0
     scalerStat[name]+=s
 keys = scalerStat.keys()
 keys.sort()
 for k in keys: print k,':',scalerStat[k]

def makeDTEfficiency(merge=False):
 cmd = "hadd -f DTEff.root "
 for fname in os.listdir('.'):
  if not merge and fname.find('SPILL')==0:
   cmd = "python "+pathToMacro+"drifttubeMonitoring.py -c DTeffWithRPCTracks -f "+fname+' &'
   os.system(cmd)
   time.sleep(10)
   while 1>0:
        if count_python_processes('drifttubeMonitoring')<ncpus: break 
        time.sleep(10)
  elif merge and fname.find('histos-DTEff')==0: 
   cmd+=fname+' '
 if merge: os.system(cmd)
 print "finished all the tasks."
 

def importMomDistr(keyword = 'RUN_8000_2'):
  pathHistos = '/media/truf/disk2/home/truf/ShipSoft/ship-ubuntu-1710-64/'
  temp = os.listdir(pathHistos)
  for x in temp:
   if x.find(keyword)<0: continue
   run = x
   if not run in os.listdir('.'):
     os.system('mkdir '+run)
   os.system('cp '+pathHistos+run+'/momDistributions.root '+run)


