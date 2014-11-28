import os, subprocess
prefix = 'muon58'
if len(os.sys.argv)>1 : prefix = os.sys.argv[1]
if prefix.find('muon')<0:prefix='muon'+prefix
print prefix

cmd  = os.environ["FAIRSHIP"]+"/macro/genfitShip.py"  
def execute( ncpu = 4 ):
  cpus = {}
  log  = {}
  for i in range(ncpu): cpus[i]={}
  jobs = []
  for x in os.listdir('.'):
    if not x.find(prefix)<0: 
       if os.path.isdir(x) : 
         jobs.append(x)
  k = 0
  print jobs
  for x in jobs:
      if k==ncpu: k = 0
      if cpus[k].has_key('child'):
        rc = child.communicate()[0]
        log[k]['log'].close() 
      print "change to directory ",k,x   
      os.chdir('./'+x) 
      for f in os.listdir('.'):
        if  not f.find("geofile_full")<0:
          inputfile = f.replace("geofile_full","ship")
          log[k]  = open("logRec",'w')
          cpus[k] = subprocess.Popen(["python",cmd,"-f "+inputfile], stdout=log[k],)
          k+=1
          os.chdir('../')
          break
  return cpus,log
# 581-584 test with replacing tungsten core with iron, 10m height
# 591-599 test with replacing tungsten core with iron, 6m height, display
# 601-609 replacing tungsten core with iron, 6m height, Yandex data, display
# 610-619 replacing tungsten core with iron, 10m height, display
# 620-629 replacing tungsten core with iron, 10m height, Yandex data, display
cpus,log = execute()
