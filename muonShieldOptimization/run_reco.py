import os, subprocess,ROOT,time,getpass,multiprocessing
import rootUtils as ut
ncores = min(multiprocessing.cpu_count(),9)
user   = getpass.getuser()
# support for eos, assume: eosmount $HOME/eos

h = {}

def fitSingleGauss(x,ba=None,be=None):
    name    = 'myGauss_'+x 
    myGauss = h[x].GetListOfFunctions().FindObject(name)
    if not myGauss:
       if not ba : ba = h[x].GetBinCenter(1) 
       if not be : be = h[x].GetBinCenter(h[x].GetNbinsX()) 
       bw    = h[x].GetBinWidth(1) 
       mean  = h[x].GetMean()
       sigma = h[x].GetRMS()
       norm  = h[x].GetEntries()*0.3
       myGauss = ROOT.TF1(name,'[0]*'+str(bw)+'/([2]*sqrt(2*pi))*exp(-0.5*((x-[1])/[2])**2)+[3]',4)
       myGauss.SetParameter(0,norm)
       myGauss.SetParameter(1,mean)
       myGauss.SetParameter(2,sigma)
       myGauss.SetParameter(3,1.)
       myGauss.SetParName(0,'Signal')
       myGauss.SetParName(1,'Mean')
       myGauss.SetParName(2,'Sigma')
       myGauss.SetParName(3,'bckgr')
    h[x].Fit(myGauss,'','',ba,be) 

cmd     = os.environ["FAIRSHIP"]+"/macro/ShipReco.py"  
cmdAna  = os.environ["FAIRSHIP"]+"/macro/ShipAna.py"
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
          cpus[k] = subprocess.Popen(["python",cmd,"-n 9999999 -f "+inputfile], stdout=log[k],)
          k+=1
          os.chdir('../')
          break
  return cpus,log

def getJobs(prefix):
 jobs = []
 for x in os.listdir('.'):
    if not x.find(prefix)<0: 
       if os.path.isdir(x) : 
         jobs.append(x)
 return jobs 
def checkRunningProcesses():
 processoutput = os.popen("ps -u "+user).read()
 nproc = 0
 for x in  processoutput.split('\n'):
    if not x.find('python')<0 and x.find('defunct')<0 : 
      nproc+=1
 return nproc
def killAll():
 processoutput = os.popen("ps -u "+user).read()
 for x in  processoutput.split('\n'):
    if not x.find('python')<0:
       pid = int(x[:5])
       print 'kill '+str(pid)
       os.system('kill '+str(pid))
def executeSimple(prefixes,reset=False):
 proc = {}
 for prefix in prefixes:
  jobs = getJobs(prefix)
  for x in jobs:
      print "change to directory ",x   
      os.chdir('./'+x) 
      geofile = None
      for f in os.listdir('.'):
        if not f.find("geofile_full")<0:
          geofile = f
          break
      if not geofile:
         print "ERROR: no geofile found"
         continue
      else:  
          inputfile = geofile.replace("geofile_full","ship")
          nproc = 100
          while nproc > ncores : 
            nproc = checkRunningProcesses()
            if nproc > ncores: 
               print 'wait a minute'
               time.sleep(100)
          print 'launch reco',x
          proc[x] = 1
          os.system("python "+cmd+" -n 9999999 -f "+inputfile + " >> logRec &")
          os.chdir('../')
 nJobs = len(proc)
 while nJobs > 0:
  procAna = proc.keys()
  nJobs = len(proc)
  procAna.sort()
  print 'debug ',nJobs
  for p in procAna: 
    os.chdir('./'+p) 
    nproc = 100
    while nproc > ncores : 
      nproc = checkRunningProcesses()
      if nproc > ncores: 
       print 'wait a minute'
       time.sleep(100)
    log = open('logRec')
    completed = False
    rl = log.readlines()
    log.close()       
    if "finishing" in rl[len(rl)-1] : completed = True
    if completed:
     print 'analyze ',p,nproc
     os.system("python "+cmdAna+" -n 9999999 -f "+inputfile.replace('.root','_rec.root')+ " >> logAna &")
     rc = proc.pop(p) 
    else:
     print 'Rec job not finished yet',p
     time.sleep(100)
    os.chdir('../')
     
def executeAna(prefixes):
 cpus = {}
 log  = {} 
 for prefix in prefixes:
  jobs = getJobs(prefix)
  for x in jobs:
    print "change to directory ",x   
    os.chdir('./'+x) 
    for f in os.listdir('.'):
      if  not f.find("geofile_full")<0:
        inputfile = f.replace("geofile_full","ship")
        log[x] = open("logAna",'w')
        process = subprocess.Popen(["python",cmdAna,"-n 9999999", "-f "+inputfile.replace('.root','_rec.root')], stdout=log[x])
        process.wait()          
        print 'finished ',process.returncode
        log[x].close() 
        os.chdir('../')
        break

h={} 
def mergeHistosMakePlots(p):
 if not type(p)==type([]): pl=[p]
 else: pl = p
 hlist = ''
 for p in pl:
   prefix = str(p) 
   for x in os.listdir('.'):
    if not x.find(prefix)<0: 
       if os.path.isdir(x) : 
         hlist += x+'/ShipAna.root '
 print "-->",hlist
 os.system('hadd -f ShipAna.root '+hlist)
 ut.readHists(h,"ShipAna.root")
 print h['meanhits'].GetEntries()
 if 1>0: 
   ut.bookCanvas(h,key='strawanalysis',title='Distance to wire and mean nr of hits',nx=1200,ny=600,cx=2,cy=1)
#
   cv = h['strawanalysis'].cd(1)
   h['disty'].DrawCopy()
   h['distu'].DrawCopy('same')
   h['distv'].DrawCopy('same')
   cv = h['strawanalysis'].cd(2)
   h['meanhits'].DrawCopy()
   print h['meanhits'].GetEntries()

   ut.bookCanvas(h,key='fitresults',title='Fit Results',nx=1600,ny=1200,cx=2,cy=2)
   cv = h['fitresults'].cd(1)
   h['delPOverP'].Draw('box')
   cv = h['fitresults'].cd(2)
   cv.SetLogy(1)
   h['chi2'].Draw()
   cv = h['fitresults'].cd(3)
   h['delPOverP_proj'] = h['delPOverP'].ProjectionY()
   ROOT.gStyle.SetOptFit(11111)
   h['delPOverP_proj'].Draw()
   h['delPOverP_proj'].Fit('gaus')
   cv = h['fitresults'].cd(4)
   h['delPOverP2_proj'] = h['delPOverP2'].ProjectionY()
   h['delPOverP2_proj'].Draw()
   fitSingleGauss('delPOverP2_proj')
   h['fitresults'].Print('fitresults.gif')
   ut.bookCanvas(h,key='fitresults2',title='Fit Results',nx=1600,ny=1200,cx=2,cy=2)
   print 'finished with first canvas'
   cv = h['fitresults2'].cd(1)
   h['Doca'].Draw()
   cv = h['fitresults2'].cd(2)
   h['IP0'].Draw()
   cv = h['fitresults2'].cd(3)
   h['HNL'].Draw()
   fitSingleGauss('HNL',0.,2.)
   cv = h['fitresults2'].cd(4)
   h['IP0/mass'].Draw('box')
   h['fitresults2'].Print('fitresults2.gif')
   h['strawanalysis'].Print('strawanalysis.gif')
   print 'finished making plots'

def mergeNtuples(prefixes):
 for prefix in prefixes:
  jobs = getJobs(prefix)
  haddCommand = ''
  for x in jobs:
      for f in os.listdir(x):
        if  not f.find("geofile_full")<0:
          inputfile = (f.replace("geofile_full","ship")).replace('.root','_rec.root')
          haddCommand+= ' '+ x + '/' + inputfile    
          break
  cmd = 'hadd -f '+inputfile.replace('.root','_'+prefix+'.root') + haddCommand  
  os.system(cmd)
def checkProd(prefixes):
 for prefix in prefixes:
  jobs = getJobs(prefix)
  for x in jobs:
    try:    log = open( x+'/log')
    except: 
      print 'no log file for ',x 
      continue
    rl = log.readlines()
    log.close()       
    if "Real time" in rl[len(rl)-1] : 
      print 'simulation step OK ',x
    else:  
      print "simulation failed ",x 
      continue
    try:    log = open( x+'/logRec')
    except: 
      print 'no logRec file for ',x 
      continue
    rl = log.readlines()
    log.close()       
    if "finishing" in rl[len(rl)-1] : 
      print 'reconstruction step OK ',x
    else:  
      print "reconstruction failed ",x 
      continue
    try:    log = open( x+'/logAna')
    except: 
      print 'no logAna file for ',x 
      continue
    rl = log.readlines()
    log.close()       
    if "finished" in rl[len(rl)-1] : 
      print 'analysis step OK ',x
    else:  
      print "analysis failed ",x 
      continue    
     

def execute():
 executeSimple(pl,reset=True)
 mergeHistosMakePlots(pl)
 mergeNtuples(pl)
def removeIntermediateFiles(prefixes):
 for prefix in prefixes:
  jobs = getJobs(prefix)
  for x in jobs:
      for f in os.listdir(x):
        if  not f.find("geofile_full")<0:
          inputfile = (f.replace("geofile_full","ship")).replace('.root','_rec.root')
          os.system('rm '+x+'/' + inputfile ) 

pl=[]
for p in os.sys.argv[1].split(','):
   pref = 'muon'
   if not os.path.abspath('.').find('neutrino')<0: pref='neutrino'
   if not os.path.abspath('.').find('dis')<0: pref='dis'
   pl.append(pref+p) 
print " execute()  input comma separated production nr, performs Simple/mergeHistos/mergeNtuples "
print " executeSimple(pl,reset=True) "
print " checkProd(pl)"
print " executeAna(pl) "
print " mergeNtuples(pl) "
print " removeIntermediateFiles(pl) only _rec "
#61,611,612,613,614,615,616,62,621,622,623,624,625,626
