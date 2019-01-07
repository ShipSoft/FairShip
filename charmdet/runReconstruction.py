import os,subprocess,ROOT,time
ncpus = 8
pathToMacro = '' # $SHIPBUILD/FairShip/charmdet/
def count_python_processes(macroName):
# only works if screen is wide enough to print full name!
 status = subprocess.check_output('ps -f -u truf',shell=True)
 n=0
 for x in status.split('\n'):
   if not x.find(macroName)<0: n+=1
 return n

fileList = {}
badFiles = []
eospath='/eos/experiment/ship/user/olantwin/muon_flux/root_conversion/'


def getFilesFromEOS():
# list of files
 temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospath,shell=True)
 for x in temp.split('\n'):
  if x.find('.root')<0: continue
  if x.find('2018-09-21')<0: continue
  if not x.find('16777216')<0: continue
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

def recoStep0():
 tmp,fnames = getFilesFromEOS()
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
   if count_python_processes('drifttubeMonitoring')<3: break
   time.sleep(200)
 while count_python_processes('drifttubeMonitoring')>0: time.sleep(200)
 print "files created with RT relations "


def recoStep1():
 fileList=[]
 # all RT files
 for x in os.listdir('.'):
  if x.find('_RT')>0 and x.find('histos')<0: fileList.append(x)
  fileList.sort()
 for fname in fileList:
    cmd = "python "+pathToMacro+"drifttubeMonitoring.py -c recoStep1 -u 1 -f "+fname+' &'
    print 'step 1:', cmd
    os.system(cmd)
    while 1>0:
        if count_python_processes('drifttubeMonitoring')<ncpus: break 
        time.sleep(200)

def runMC():
 # fast MC
 inputFile = "/eos/experiment/ship/data/Mbias/background-prod-2018/pythia8_Geant4_10.0_withCharmandBeauty0_mu.root" # entries 13450391L
 os.system("python $FAIRSHIP/macro/run_simScript.py -n 100000 --MuonBack --charm=1 --CharmdetSetup=0 -f "+inputFile) 
 # full simulation
 os.system("python $SHIPBUILD/FairShip/macro/run_simScript.py --Muflux -n 1000 --charm=1 --CharmdetSetup=0 --charm=1 --CharmdetSetup=0")
