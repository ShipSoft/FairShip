import os,subprocess,ROOT,time
ncpus = 7
pathToMacro = '$SHIPBUILD/FairShip/charmdet/'
def count_python_processes(macroName):
# only works if screen is wide enough to print full name!
 status = subprocess.check_output('ps -f -u truf',shell=True)
 n=0
 for x in status.split('\n'):
   if not x.find(macroName)<0: n+=1
 return n

# list of files
f=open('RTfile.txt')
fileList=[]
for x in f.readlines():
 fileList.append(x.replace('\n',''))

for fname in fileList:
  cmd = "python -i "+pathToMacro+"drifttubeMonitoring.py -c anaResiduals  -f "+fname
  os.system(cmd+" &")
  while 1>0:
   if count_python_processes('drifttubeMonitoring')<ncpus: break
   time.sleep(30)
def finalize():
 cmd = "hadd -f residuals.root "
 for fname in fileList:
   hname = 'histos-residuals-'+fname
   if os.path.exists(hname):   cmd += hname+' '
 os.system(cmd)
 

