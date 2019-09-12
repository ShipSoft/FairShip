from __future__ import print_function
import sys,os,ROOT
ncpus = 20
msel = "4"
# msel = "5"

if msel == "4":
 nev   = 2000000  # 0.1s / event
 path  = "/afs/cern.ch/project/lbcern/vol1/truf/charm/"
else:
 nev   = 1000000 
 path  = "/afs/cern.ch/project/lbcern/vol1/truf/beauty/"

# path = "/home/truf/charm/"

# store only charm

# story about weights, run_fixedTarget puts into file header: pot = nrpotspill / wspill
# with wspill = nrpotspill*chicc/nrcpot*nEvents/nev -> pot =  nev * nrcpot / (chicc * nEvents)
# nEvents nr of events in input file, number of events requested for job, ratio should be 1
# pot =  nrcpot / chicc 
# nrcpot=((TH1F*)fin->Get("2"))->GetBinContent(1)/2.;  // pot are counted double, i.e. for each signal, i.e. pot/2.

def makeHadrons(run):
 for n in range(ncpus):
  s = x.Rndm()*1000000000.
  os.system('mkdir run'+str(run))
  os.chdir('run'+str(run))
  cmd = "python $FAIRSHIP/macro/makeCascade.py -m "+msel+" -n " + str(nev) + " -t  Cascade-run"+str(run)+"-parp16-MSTP82-1-MSEL"+msel+".root"
  # if not run in runList: 
  os.system(cmd+ " >log"+str(run)+" &")
  os.chdir('../')
  run+=1

def makeBackground(run,cycle=0):
 for n in range(ncpus):
  orun = run+cycle*1000
  os.chdir('run'+str(run))
  inputFile = path+"run"+str(run)+"/Cascade-run"+str(run)+"-parp16-MSTP82-1-MSEL"+msel+".root"
  f=ROOT.TFile(inputFile)
  nt = f.pythia6
  N = nt.GetEntries()
  f.Close()
  if msel == "4":
   cmd = "python $FAIRSHIP/muonShieldOptimization/run_fixedTarget.py --force --charm -V -e 10 -P -n "+str(N)+" -r "+str(orun)+" -b 100 -X 100 -I "+inputFile
  else:
   cmd = "python $FAIRSHIP/muonShieldOptimization/run_fixedTarget.py --force --beauty -V -e 10 -P -n "+str(N)+" -r "+str(orun)+" -b 100 -X 100 -I "+inputFile
  os.system(cmd+ " >logFT"+str(orun)+" &")
  os.chdir('../')
  run+=1

cycle = 2
runList = [20,28,30,33]
def makeBackgroundX(runList,cycle=0):
 for run in runList:
  orun = run+cycle*1000
  os.chdir('run'+str(run))
  inputFile = path+"run"+str(run)+"/Cascade-run"+str(run)+"-parp16-MSTP82-1-MSEL"+msel+".root"
  f=ROOT.TFile(inputFile)
  nt = f.pythia6
  N = nt.GetEntries()
  f.Close()
  cmd = "python $FAIRSHIP/muonShieldOptimization/run_fixedTarget.py --force --charm -V -e 10 -P -n "+str(N)+" -r "+str(orun)+" -b 100 -X 100 -I "+inputFile
  if run in runList: os.system(cmd+ " >logFT"+str(orun)+" &")
  os.chdir('../')

def merge(run,cycle=0):
 fname = "pythia8_Geant4_XX_10.0.root"
 cmd = " " 
 for n in range(ncpus):
  for x in os.listdir(path+'/run'+str(run+n)):
   orun = run+cycle*1000
   if not x.find('run_fixedTarget_'+str(orun+n)) < 0:
     if cycle == 0 and run == 0 and not x.find('1001') < 0: continue
     if cycle == 0 and run == 0 and not x.find('1010') < 0: continue
     cmd += path+'/run'+str(run+n)+'/'+x+'/'+fname.replace('XX',str(orun+n))+' '
 if msel == "4": outFile = fname.replace('XX', 'charm_'+str(orun)+'-'+str(orun+ncpus-1) )
 else:           outFile = fname.replace('XX', 'beauty_'+str(orun)+'-'+str(orun+ncpus-1) )
 rc = os.system("hadd -O "+outFile + " " +cmd)
 if rc != 0: 
    print("hadd failed, stop",outFile) 
 else:
   rc = os.system("xrdcp "+outFile+" $EOSSHIP/eos/experiment/ship/data/Mbias/background-prod-2018/"+outFile)
   if rc != 0: 
    print("copy to EOS failed, stop",outFile) 
   else:
    rc = os.system("rm "+outFile)

def mergeAll():
 cmd = "hadd pythia8_Geant4_charm_153.3B_10.0_mu.root "
 tmp = "/eos/experiment/ship/data/Mbias/background-prod-2018/pythia8_Geant4_charm_XX_10.0_mu.root" 
 for x in ["0-19","20-39","40-59","60-79","80-99",\
           "1000-1019","1020-1039","1040-1059","1060-1079","1080-1099",\
           "2000-2019","2020-2039","2040-2059","2060-2079","2080-2099"]:
  cmd+=tmp.replace('XX',x)+" "
 os.system(cmd)

def compactifyCascade(run):
 ncpus = 20
 cmd = ''
 Ntot = 0
 NperJob = nev
 for i in range(run,+ncpus):
   fName = path+"run"+str(i)+"/Cascade-run"+str(i)+"-parp16-MSTP82-1-MSEL"+msel+".root"
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
  outFile = "Cascade-run"+str(run)+"-"+str(run+ncpus-1)+"-parp16-MSTP82-1-MSEL"+msel+"-"+stat+".root"
  rc = os.system("hadd -O "+outFile + " " +cmd)
  f = ROOT.TFile(outFile) 
  Npot = f.Get("2").GetBinContent(1)/2./chicc
  f.Close()
  stat = str( int(Npot/1E9))+'Bpot'
  oldOutFile = outFile
  outFile = "Cascade-run"+str(run)+"-"+str(run+ncpus-1)+"-parp16-MSTP82-1-MSEL"+msel+"-"+stat+".root"
  os.system("mv "+oldOutFile+" "+outFile)
  rc = os.system("xrdcp "+outFile+" $EOSSHIP/eos/experiment/ship/data/Mbias/background-prod-2018/"+outFile)
  if rc != 0: 
    print("copy to EOS failed, stop",outFile) 
  else:
    rc = os.system("rm "+outFile)

def statistics():
 chicc=1.7e-3
 if msel=='5': chicc = 1.6e-7
 path = os.environ['EOSSHIP']+"/eos/experiment/ship/data/Mbias/background-prod-2018/"
 fname =  "Cascade-runAA-BB-parp16-MSTP82-1-MSEL4-40Mpot.root"
 nPot = 0
 nhadrons = 0
 for x in [0,20,40,60,80]:
  fn = fname.replace('AA',str(x)).replace('BB',str(x+19))
  f=ROOT.TFile.Open(path+fn)
  nPot += f.Get("2").GetBinContent(1)/2.
  nhadrons += f.Get('pythia6').GetEntries()
 print("total nr of hadrons:",nhadrons,nPot/chicc/1.E9,'Billion')

def potFromFileHeader():
 pot = 0
 for x in f.GetListOfKeys():
  if x.GetName()=='FileHeader':
   pot += float(x.GetTitle().split(' ')[3])
 print("PoT = ",pot)

x=ROOT.TRandom3()
x.SetSeed(0)

run = int(sys.argv[1])

print("following functions exist")
print(" - makeHadrons(run): will run makeCascade")
print(" - makeBackground(run): will run fixedTarget generator")


