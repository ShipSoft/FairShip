import os,subprocess,ROOT,time,multiprocessing
ncpus = multiprocessing.cpu_count()

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
eospath='/eos/experiment/ship/data/muflux/DATA_Rebuild_8000' # RUN_8000_2395

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

def checkAlignment():
 fileList=[]
 # all RT files
 for x in os.listdir('.'):
  if x.find('_RT')>0 and x.find('histos')<0:
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
 # all RT files
 for x in os.listdir(D):
  if x.find('_RT')>0 and x.find('histos')<0: 
    test = ROOT.TFile(D+'/'+x)
    if test.cbmsim.GetBranch("FitTracks"): fileList.append(x)
 fileList.sort()
 return fileList

def cleanUp(D='.'):
# remove raw data files for files with RT relations
   for x in os.listdir(D):
    if not x.find('_RT')<0 and x.find('histos')<0:
     test = ROOT.TFile(D+'/'+x)
     if test.cbmsim.GetBranch("FitTracks"): # it is safe to delete the local raw file
        r = x.replace('_RT','')
        cmd = 'rm '+r
        os.system(cmd)


def importRTFiles(local='.',remote='/home/truf/ship-ubuntu-1710-32/home/truf/muflux/Jan08'):
# mkdir /media/truf/disk2/home/truf/ShipSoft/ship-ubuntu-1710-32
# sshfs  ship-ubuntu-1710-32.cern.ch:/ /media/truf/disk2/home/truf/ShipSoft/ship-ubuntu-1710-32
 fileWithTracks = checkFilesWithTracks(local)
 allFiles = os.listdir(remote)
 for x in allFiles:
  if x.find('_RT')>0 and x.find('histos')<0 and not x in fileWithTracks:
    os.system('cp '+remote+'/'+x+' .')

def importRecoFiles(local='.',remote='/media/truf/disk2/home/truf/ShipSoft/ship-ubuntu-1710-16/home/truf/muflux/Jan08'):
 fileWithTracks = checkFilesWithTracks(remote)
 for x in fileWithTracks:  os.system('cp '+remote+'/'+x+' .')

def mergeHistos(local='.'):
 allFiles = os.listdir(local)
 cmd = 'hadd -f residuals.root '
 for x in allFiles:
  if not x.find('histos')<0 : cmd += x+' '
 os.system(cmd)
 
def checkRecoRun(eosLocation="/eos/experiment/ship/user/olantwin/muflux/DATA_Rebuild_8000/RUN_8000_2395/",local='.'):
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
def exportRunToEos(eosLocation="/eos/experiment/ship/user/truf/muflux-reco",run="RUN_8000_2395",local="."):
 temp = os.system("xrdfs "+os.environ['EOSSHIP']+" mkdir "+eosLocation+"/"+run)
 failures = []
 for x in os.listdir(local):
  if x.find('.root')<0: continue
  cmd = "xrdcp -f "+x+" $EOSSHIP/"+eosLocation+"/"+run+"/"+x
  rc = os.system(cmd)
  if rc != 0: failures.append(x)
 if len(failures)!=0: print failures

