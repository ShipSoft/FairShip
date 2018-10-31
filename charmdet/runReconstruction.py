import os,subprocess,ROOT
ncpus = 8
pathToMacro = '' # $SHIPBUILD/FairShip/charmdet/
def count_python_processes(macroName):
# only works if screen is wide enough to print full name!
 status = subprocess.check_output('ps -f -u truf',shell=True)
 n=0
 for x in status.split('\n'):
   if not x.find(macroName)<0: n+=1
 return n

# list of files
eospath='/eos/experiment/ship/user/olantwin/muon_flux/root_conversion/'
temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospath,shell=True)
fileList = {}
badFiles = []
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
  print "problem with file",fname
  badFiles.append(fname)

Nfiles = len(fileList)
fnames = fileList.keys()
fnames.sort()

Ndone = 0
print "fileList established"
while Ndone < Nfiles:
  cmd = "python  "+pathToMacro+"drifttubeMonitoring.py --eos 1 -c recoStep0 -f "
# group four files to get better
  Ntot = 0
  sample = []
  i = 0
  for k in range(Ndone,Nfiles): 
    Ntot += fileList[fnames[k]]
    sample.append(fnames[k])
    i+=1
    if Ntot>350000: break
  Ndone += i
  # check that enough files remain
  Nextsample = []
  Ntot = 0
  for k in range(Ndone,Nfiles): 
    Ntot += fileList[fnames[k]]
    Nextsample.append(fnames[k])
    if Ntot>350000: break
  if Ntot < 350000:
    for s in Nextsample: sample.append(s)
    Ndone += len(Nextsample)
  for s in sample: cmd+=s+','
  print cmd[:cmd.rfind(',')]
  os.system(cmd[:cmd.rfind(',')])
  while 1>0:
   if count_python_processes('drifttubeMonitoring')<ncpus: break
  for fname in sample:
    rname = fname[fname.rfind('/')+1:].replace('.root','_RT.root')
    cmd = "python "+pathToMacro+"drifttubeMonitoring.py -c recoStep1 -u 1 -f "+rname+' &'
    print cmd
    os.system(cmd)
