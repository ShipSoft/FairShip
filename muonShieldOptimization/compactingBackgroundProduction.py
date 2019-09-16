from __future__ import print_function
import os,ROOT,sys,subprocess,pickle,time,datetime
import rootUtils as ut

pdg   = ROOT.TDatabasePDG()
charm = False

# functions, PoT: statistics per file
#            TotStat: total statistics in given directory
#            GetGoodAndBadRuns: list of good and bad runs within given dates
#            addRuns: concatenate good runs
#            YandexProd(): specify start end date, select good runs, write to pickle file, concatenate runs requires start number !

# prod = ''
# globalPath="/eos/experiment/ship/skygrid/background-prod-2018/"
# fnames = 'pythia8_Geant4_1_10.0.root'
# ecut = '10.0'

# final statistics: 65041000000 pot  -> weight 768.75

prod = '1GeV'
globalPath="/eos/experiment/ship/skygrid/background-prod-2018-1gev/"
fnames = 'pythia8_Geant4_1_1.0.root'
ecut = '1.0'

def GetGoodAndBadRuns(startDate,endDate):
# find bad runs, try to recover
 goodRuns=[]
 badRuns=[]
 fileName = "pythia8_Geant4_1_"+ecut+".root"
 os.system("ls -l --full-time "+globalPath+" >inventory.lst")
 f=open("inventory.lst")
 runs = f.readlines()
 f.close()
 N=0
 for r in runs:
   tmp = r.split(' ')
   if len(tmp) != 9: 
      print("wrong format",tmp)
      continue
   date = tmp[5].split('-')
   time = tmp[6].split(':')
   fileDate = datetime.datetime(int(date[0]),int(date[1]),int(date[2]),int(time[0]),int(time[1]),int(time[2].split('.')[0]))
   if fileDate < startDate or fileDate>endDate: continue
   theRun = int(tmp[8].replace('\n',''))
   test = os.listdir(globalPath+str(theRun))
   if len(test)<2:continue
   N+=1
   rc = os.system('grep -q "Number of events produced with activity after hadron absorber" '+globalPath+str(theRun)+"/stdout")
   if rc!=0:
    badRuns.append(theRun)
    continue
   for x in test:
     if x.find('run_fixedTarget')>0:
      test2 = os.listdir(globalPath+str(theRun)+'/'+x)
      bad  = True
      tmpF = False
      f = globalPath+str(theRun)+"/"+x+"/"+fileName
      if fnames+"tmp" in test2:
        tmpF = True 
        f = f+"tmp"
      elif fnames in test2:
        f = f
      else:
        badRuns.append(theRun)
        continue
      try:
         t = ROOT.TFile.Open(os.environ["EOSSHIP"]+f)
         if not t: 
           badRuns.append(theRun)
           continue
         if N%1000 == 0: print(N,t.GetName())
         if t.ReadKeys()==0:
           t.Close()
           badRuns.append(theRun)
           continue
         if t.FindObjectAny('cbmsim'):
            bad = False
            goodRuns.append(f)
            t.Close()
      except:
         badRuns.append(theRun)
         continue
 return goodRuns,badRuns

def addRuns(goodRuns,Nstart=0):
 N=0
 while(1>0):
  cmd = ""
  for i in range(N,min(N+1000,len(goodRuns))):
    cmd += " $EOSSHIP"+goodRuns[i]
  tmpFile = "pythia8_Geant4_"+ecut+"_c"+str(N+Nstart)+".root"
  rc = os.system("hadd -j 10 -O "+tmpFile + " " +cmd)
  if rc != 0: 
    print("hadd failed, stop",N)
    return
  rc = os.system("xrdcp "+tmpFile+" $EOSSHIP/eos/experiment/ship/data/Mbias/background-prod-2018/"+tmpFile)
  if rc != 0: 
    print("copy to EOS failed, stop",N,N+Nstart) 
  else:
    rc = os.system("rm "+tmpFile)
  N+=1000
  if N > len(goodRuns): break
def YandexProd():
 #startDate = datetime.datetime(2018, 1, 1, 0, 0)  # N=0
 #endDate   = datetime.datetime(2018, 2, 1, 0, 0)
 #startDate = datetime.datetime(2018, 2, 1, 0, 0)  # N=23000
 #endDate   = datetime.datetime(2018, 2, 6, 0, 0)
 #startDate = datetime.datetime(2018, 2, 6,  0, 0) # N=33000
 #endDate   = datetime.datetime(2018, 2, 12, 0, 0)
 #startDate = datetime.datetime(2018, 2, 12,  0, 0) # N=45000
 #endDate   = datetime.datetime(2018, 2, 15, 0, 0)
 #startDate = datetime.datetime(2018, 2, 15,  0, 0) # N=51000
 #endDate   = datetime.datetime(2018, 2, 21, 0, 0)
 #startDate = datetime.datetime(2018, 2, 21,  0, 0) # N=63000
 #endDate   = datetime.datetime(2018, 2, 2, 0, 0)
 #startDate = datetime.datetime(2018, 1, 1,  0, 0) #  start with 1 GeV production
 #endDate   = datetime.datetime(2018, 2, 27, 0, 0) # N=0
 #startDate = datetime.datetime(2018, 2, 27,  0, 0) #   
 #endDate   = datetime.datetime(2018, 3, 6, 0, 0) # N=3000
 #startDate = datetime.datetime(2018, 3, 6,  0, 0) #   
 #endDate   = datetime.datetime(2018, 3, 12, 0, 0) # N=9000
 goodRuns,badRuns = GetGoodAndBadRuns(startDate,endDate)
 pName = 'goodAndBadRuns'+prod+'_'+startDate.__str__().split(' ')[0]+'_'+endDate.__str__().split(' ')[0]+'.pkl'
 fpi=open(pName,'w')
 database = {}
 database['goodruns']=goodRuns
 database['badRuns']=badRuns
 pickle.dump(database,fpi)
 fpi.close()
 fpi=open(pName)
 database = pickle.load(fpi)
 addRuns(database['goodruns'],20000)  # next cycle

def addAllHistograms():
 h={}
 ecut = '10.0'
 Nmax=45000
 path = os.environ['EOSSHIP']+"/eos/experiment/ship/data/Mbias/background-prod-2018/"
 ut.bookCanvas(h,key='canvas',title='debug',nx=1600,ny=1200,cx=1,cy=1)
 h['canvas'].SetLogy(1)
 for i in range(0,Nmax,1000):
  fname = "pythia8_Geant4_"+ecut+"_c"+str(i)+".root"
  ut.readHists(h,path+fname)
  if i==0:
    h[1012].Draw()
 for x in h.keys():
   if h[x].GetName().find('proj')>0: rc = h.pop(x)
 ut.writeHists(h,"pythia8_Geant4_"+ecut+"_c"+str(Nmax)+"-histos.root")
 
def compactifyCascade(cycle):
 ncpus = 20
 path = "/afs/cern.ch/project/lbcern/vol1/truf/charm/"
 cmd = ''
 Ntot = 0
 NperJob = 2000000
 for i in range(cycle,cycle+ncpus):
   fName = path+"run"+str(i)+"/Cascade-run"+str(i)+"-parp16-MSTP82-1-MSEL4.root"
   f=open(path+"run"+str(i)+"/log"+str(i))
   success = False
   for l in f.readlines():
    if not l.find('Macro finished succesfully')<0: success = True
   if not success:
     print("job not finished properly",fName)
     continue  
   cmd += fName +" "
   f.close()
   Ntot+= NperJob
 if cmd.find('root')<0:
  print('no file found, exit')
 else:
  stat = str( int(Ntot/1E6))+'Mpot'
  outFile = "Cascade-run"+str(cycle)+"-"+str(cycle+ncpus-1)+"-parp16-MSTP82-1-MSEL4-"+stat+".root"
  rc = os.system("hadd -O "+outFile + " " +cmd)
  rc = os.system("xrdcp "+outFile+" $EOSSHIP/eos/experiment/ship/data/Mbias/background-prod-2018/"+outFile)
  if rc != 0: 
    print("copy to EOS failed, stop",outFile) 
  else:
    rc = os.system("rm "+outFile)



# some old stuff
def compactify(charm):
 globalPath="/afs/cern.ch/project/lbcern/vol2/truf/muonBackground"
 ecut = '10.0'
 if charm:
  allDirs =  os.listdir(globalPath+"/charm")
  allFiles = []
  for r in range(int(runMin),int(runMax)+1):
# collect the 20 subdirectories connected to a run
   nr = '9000'+str(r)
   subruns = []
   badFiles = []
   for x in allDirs:
     for k in range(20):
       sr = "{0:0>2}".format(k)
       if not x.find(nr+sr)<0:
         if not x.find('log')<0: continue 
         fn = 'pythia8_Geant4_'+nr+sr+'_'+ecut+'.root'
         aFile = globalPath+"/charm/"+x+'/'+fn
         if os.path.exists(aFile): 
          try:
           t = ROOT.TFile.Open(aFile)
           if not t:
            badFiles.append(d)
            continue
           if t.ReadKeys()==0: 
            badFiles.append(d)
            continue
           if t.FindObjectAny('cbmsim'):
            subruns.append(aFile)
          except: 
           badFiles.append(aFile)
           continue
   ldir = ' '
   for x in subruns: ldir+= (x+" ")
   outputr = 'pythia8_Geant4_charm_'+nr+'_'+ecut+'.root'
   allFiles += (outputr+" ")
   os.system('hadd ' + outputr +' '+ldir)
  output = 'pythia8_Geant4_charm_'+str(runMin)+'_'+str(runMax)+'_'+ecut+'.root'
  os.system('hadd ' + output +' '+allFiles)
  makeHistos(output)
 else:
  output = 'pythia8_Geant4_'+str(runMin)+'-'+str(runMax)+'_'+ecut+'.root'
  if not checkOnly:
   ldir = ''
   badFiles = []
   for d in os.listdir(globalPath):
    if d.find( 'run_fixedTarget') < 0 : continue
    srun = d.split('run_fixedTarget_')[1]
    run = int(srun)
    if not run > runMax and not run < runMin:
     f =  globalPath+'/'+d+'/pythia8_Geant4_'+srun+'_'+ecut+'.root '
     ftmp = f.replace('.root ','.roottmp')
     if os.path.exists(ftmp):f=ftmp+' '
     try:
       t = ROOT.TFile.Open(f)
       if not t: 
        badFiles.append(d)
        continue
       if t.ReadKeys()==0: 
        badFiles.append(d)
        continue
       if t.FindObjectAny('cbmsim'):
         ldir+=f
     except:
       badFiles.append(d) 
       continue
   os.system('hadd '+output+' '+ldir)
   makeHistos(output)

def makeHistos(rfile):
 f=ROOT.TFile.Open(rfile)
 sTree = f.cbmsim
 nTot = 0
 for k in f.GetListOfKeys():
  if k.GetName() == 'FileHeader':
   tmp =  k.GetTitle().split('=')[1]
   tmp2 = tmp.split('with')[0]
   if tmp2.find('E')<0: nTot += int(tmp2)
   else: nTot += float(tmp2)
 print("POT = ",nTot," number of events:",sTree.GetEntries())
# particle statistics
 h={}
 ut.bookHist(h,'pids','pid',19999,-9999.5,9999.5)
 ut.bookHist(h,'test','muon p/pt',100,0.,400.,100,0.,5.)
 diMuonDecays = [221, 223, 113, 331, 333]
 pDict = {}
 procDict = {}
 for n in range(sTree.GetEntries()):
  rc = sTree.GetEvent(n)
  for p in sTree.vetoPoint:
   t = sTree.MCTrack[p.GetTrackID()]
   pid = t.GetPdgCode()
   rc = h['pids'].Fill(pid)
   if abs(pid)==13:
     procID = t.GetProcName().Data()
     mother = t.GetMotherId()
     if not mother < 0:
         moPid = sTree.MCTrack[mother].GetPdgCode()
         name = pdg.GetParticle(moPid).GetName()
         name = procID+' '+name
         if name not in h:  h[name]=h['test'].Clone(name)
         rc=h[name].Fill(t.GetP(),t.GetPt())
     if procID not in h:  h[procID]=h['test'].Clone(procID)
     rc=h[procID].Fill(t.GetP(),t.GetPt())
 for x in h:
  h[x].Scale(1./nTot)
 tmp = rfile.split('/')
 hname = tmp[len(tmp)-1].replace('pythia8_Geant4','Histos')
 ut.writeHists(h,hname)

hunbiased = {}
hbiased   = {}
import operator
def makePrintout():
 # Histos_2000000-2001500_10.0.root
 ut.readHists(hunbiased,'/media/microdisk/HNL/muonBackground/Histos_1000000-1000600_10.0.root')
 ut.readHists(hbiased,'hadded_Histos_1_10.0.root')

 unbiased = {}
 biased = {}
 for l in hunbiased:
  unbiased[l]=hunbiased[l].GetSumOfWeights()
 for l in hbiased:
  if l.find('proj') < 0 and l.find('test') < 0 and l.find('pids') < 0 : biased[l]=hbiased[l].GetSumOfWeights()
 p={}
 for i in range( 1,hbiased['pids'].GetNbinsX() + 1 ):
   c = hbiased['pids'].GetBinContent(i)
   if c>0: p[int(hbiased['pids'].GetBinCenter(i))]=c
 
 sorted_p = sorted(p.items(), key=operator.itemgetter(1))
 for p in sorted_p:
  print("%25s : %5.2G"%(pdg.GetParticle(p[0]).GetName(),float(p[1])))
 sorted_pr = sorted(biased.items(), key=operator.itemgetter(1))
 print("origin of muons")
 for p in sorted_pr:
  if not p[0].find('Hadronic inelastic')<0:
     if len(p[0])>len( 'Hadronic inelastic' ): continue
  denom = 0
  if p[0] in unbiased: denom = unbiased[p[0]]
  if denom >0:
   fac = float(p[1])/denom
   print("%40s : %5.2G %5.1F"%(p[0],float(p[1]),fac))
  else:
   print("%40s : %5.2G "%(p[0],float(p[1])))

if len(sys.argv)>1: 
 runMin=sys.argv[1]
 runMax=sys.argv[2]
 if len(sys.argv)>3: charm=sys.argv[3]
 compactify(charm)
else:  
# production without boost factor
#runMin = 1000000
#runMax = 1000600
# production with boost factor 100
# runMin = 2001001
# runMax = 2001500 # more does not work, maybe limit of hadd? 2001359
# charm run_fixedTarget_9000119/pythia8_Geant4_9000219_10.0.root
 print("methods to run: makeHistos(rfile),makePrintout()")

# yandex compactification, Feb 8
#...  startDate = datetime.datetime(2018, 1, 1, 0, 0)
#...  endDate   = datetime.datetime(2018, 2, 1, 0, 0)
# ...  goodAndBadRuns_2018-01-01_2018-02-01.pkl
# hadd Source file 339: root://eospublic.cern.ch//eos/experiment/ship/skygrid/background-prod-2018/424121/80eefea19104_run_fixedTarget_1/pythia8_Geant4_1_10.0.root
# hadd Target path: pythia8_Geant4_10.0_c22000.root:/
# len(database['goodruns'])  .22339
# database['goodruns'][22338] '/eos/experiment/ship/skygrid/background-prod-2018/424121/80eefea19104_run_fixedTarget_1/pythia8_Geant4_1_10.0.root'
#...  startDate = datetime.datetime(2018, 2, 1, 0, 0)
#...  endDate   = datetime.datetime(2018, 2, 6, 0, 0)

# for charm
# chicc=1.7e-3;     //prob to produce primary ccbar pair/pot
# 20*2000000 are equal to 23.5E9
# for beauty
# chibb=1.6e-7; 

# something went wrong Yandex2018Prod-23000.root onwards up to 43000, only have of yield, 44000 ok !!!
def removeStupidFiles():
 path = '/eos/experiment/ship/data/Mbias/background-prod-2018'
 for f in os.listdir(path):
   ff = path+'/'+f
   x = os.path.getsize(ff)
   if x < 500 : os.remove(ff)


def check4DoubleRuns():
 allRuns = ['goodAndBadRuns_2018-01-01_2018-02-01.pkl','goodAndBadRuns_2018-02-01_2018-02-06.pkl','goodAndBadRuns_2018-02-06_2018-02-12.pkl',\
           'goodAndBadRuns_2018-02-12_2018-02-15.pkl','goodAndBadRuns_2018-02-15_2018-02-21.pkl','goodAndBadRuns_2018-02-21_2018-02-26.pkl']
 Nruns=0
 for x in allRuns:
  fn = open(x)
  dn = pickle.load(fn)
  Nruns += len(dn['goodruns'])
 print("Total number of runs:",Nruns)
 
 for n in range( len(allRuns)-1 ):
  fn = open(allRuns[n])
  dn = pickle.load(fn)
  for m in range( n+1, len(allRuns)  ):
   fm = open(allRuns[m])
   dm = pickle.load(fm)
   for rn in dn['goodruns']: 
    for rm in dm['goodruns']: 
     if rn == rm : 
       print("double entry found",rn,allRuns[n],allRuns[m])



