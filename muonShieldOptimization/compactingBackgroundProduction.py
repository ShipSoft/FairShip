import os,ROOT
globalPath="/afs/cern.ch/project/lbcern/vol2/truf/muonBackground"
runMin = 1000000
runMax = 1000200
ecut = '10.0'

ldir = ''
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
       if not t: continue
       if t.ReadKeys()==0: continue
       if t.FindObjectAny('cbmsim'):   ldir+=f
     except:
       continue

output = 'pythia8_Geant4_'+str(runMin)+'-'+str(runMax)+'_'+ecut+'.root'
os.system('hadd '+output+' '+ldir)
# make a check
f=ROOT.TFile(output)
sTree = f.cbmsim
nTot = 0
for k in f.GetListOfKeys():
  if k.GetName() == 'FileHeader':
   nTot += int(k.GetTitle().split('=')[1])
print "POT = ",nTot," number of events:",sTree.GetEntries()
# particle statistics

pdg   = ROOT.TDatabasePDG()
pDict = {}
for n in range(sTree.GetEntries()):
 rc = sTree.GetEvent(n)
 for p in sTree.vetoPoint:
   t = sTree.MCTrack[p.GetTrackID()]
   pid = t.GetPdgCode()
   if not pDict.has_key(pid): pDict[pid]=0
   pDict[pid]+=1
import operator
sorted_p = sorted(pDict.items(), key=operator.itemgetter(1))
for p in sorted_p:
 print "%20s : %i "%(pdg.GetParticle(p[0]).GetName(),p[1])
 
