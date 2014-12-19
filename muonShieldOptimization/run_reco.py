import os, subprocess,ROOT
import rootUtils as ut

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

def executeSimple(prefixes,reset=False):
 for prefix in prefixes:
  jobs = []
  for x in os.listdir('.'):
    if not x.find(prefix)<0: 
       if os.path.isdir(x) : 
         jobs.append(x)
  for x in jobs:
      print "change to directory ",x   
      os.chdir('./'+x) 
      for f in os.listdir('.'):
        if  not f.find("geofile_full")<0:
          inputfile = f.replace("geofile_full","ship")
          if not "logRec" in os.listdir('.') or reset:
           log  = open("logRec",'w')
           print 'launch',x
           process = subprocess.Popen(["python",cmd,"-n 9999999", "-f "+inputfile], stdout=log)
           process.wait()
           print 'finished ',process.returncode
           log.close() 
          log  = open("logAna",'w')
          process = subprocess.Popen(["python",cmdAna,"-n 9999999", "-f "+inputfile.replace('.root','_rec.root')], stdout=log)
          process.wait()          
          print 'finished ',process.returncode
          log.close() 
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

# cpus,log = execute()
if not len(os.sys.argv)>1: 
  if not os.path.abspath('.').find('neutrino')<0:
    executeSimple(['neutrino66'])
  else:  
    fullList = [] # ['muon59','muon60','muon61','muon62']
    for x in range(9,10): 
     fullList.append('muon61'+str(x))
     fullList.append('muon62'+str(x))
    executeSimple(fullList,reset=True)
else : 
 pl=[]
 for p in os.sys.argv[1].split(','):
   pref = 'muon'
   if not os.path.abspath('.').find('neutrino')<0: pref='neutrino'
   pl.append(pref+p) 
 mergeHistosMakePlots(pl)
#61,611,612,613,614,615,616,62,621,622,623,624,625,626
