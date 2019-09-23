from __future__ import print_function
from __future__ import division
#Use Pythia8 to decay the signals (Charm/Beauty) as produced by makeCascade.
#Output is an ntuple with muon/neutrinos 
import ROOT,time,os,sys,random,getopt
import rootUtils as ut
ROOT.gROOT.LoadMacro("$VMCWORKDIR/gconfig/basiclibs.C")
ROOT.basiclibs()

# latest production May 2016,76 M pot which produce a charm event equivalent,roughly 150 M charm hadrons
fname='/eos/experiment/ship/data/Charm/Cascade-parp16-MSTP82-1-MSEL4-76Mpot_1'

nrpotspill=5.e13  #number of pot/spill
chicc=1.7e-3      #prob to produce primary ccbar pair/pot
chibb=1.6e-7      #prob to produce primary bbbar pair/pot
setByHand = False

print("usage: python $FAIRSHIP/macro/makeDecay.py -f ")

try:
        opts, args = getopt.getopt(sys.argv[1:], "f:p:c:",[\
                                   "pot=","chicc="])
except getopt.GetoptError:
        # print help information and exit:
        print(' enter -f: input file with charm hadrons')
        print(' for experts: p pot= number of protons on target per spill to normalize on')
        print('            : c chicc= ccbar over mbias cross section')
        sys.exit()
for o, a in opts:
        if o in ("-f",):
            fname = a.replace('.root','')
        if o in ("-p","--pot"):
            nrpotspill = float(a)
        if o in ("-c","--chicc"):
            chicc = float(a)
            setByHand = True

FIN =fname+'.root'
tmp = os.path.abspath(FIN).split('/')
FOUT='Decay-'+tmp[len(tmp)-1]
if FIN.find('eos')<0: fin = ROOT.TFile(FIN)
else:                 fin = ROOT.TFile.Open(ROOT.gSystem.Getenv("EOSSHIP")+FIN)
sTree = fin.FindObjectAny("pythia6")
nEvents = sTree.GetEntries()

#Calculate weights, for the whole file.
#get histogram with number of pot to normalise
hc={}
if fin.GetKey("2") : 
 hc['2']=fin.Get("2")
else: 
 fhin = ROOT.TFile(FIN.replace('ntuple','hists'))
 hc['2']=fhin.Get("2")

#pot are counted double, i.e. for each signal, i.e. pot/2.
nrcpot=hc['2'].GetBinContent(1)/2.
print('Input file: ',FIN,' with ',nEvents,' entries, corresponding to nr-pot=',nrcpot)
#nEvents=100
print('Output ntuples written to: ',FOUT)

P8gen = ROOT.TPythia8()
P8=P8gen.Pythia8()
P8.readString("ProcessLevel:all = off")

# let strange particle decay in Geant4
n=1
while n!=0:
  n = p8.particleData.nextId(n)
  p = p8.particleData.particleDataEntryPtr(n)
  if p.tau0()>1: 
    command = str(n)+":mayDecay = false"
    p8.readString(command)
    print("Pythia8 configuration: Made %s stable for Pythia, should decay in Geant4",p.name())
P8.init()


#output ntuple:
ftup = ROOT.TFile.Open(FOUT, 'RECREATE')
Ntup = ROOT.TNtuple("Decay","pythia8 heavy flavour decays","id:px:py:pz:E:M:weight:mid:mpx:mpy:mpz:mE:pot:ptGM:pzGM")

h={}
#book hists for Genie neutrino momentum distrubition, just as check
# type of neutrino
PDG = ROOT.TDatabasePDG.Instance()
for idnu in range(12,18,2):
#nu or anti-nu
  for idadd in range(-1,3,2):
   idhnu=1000+idnu
   idw=idnu
   if idadd==-1: 
    idhnu+=1000
    idw=-idnu
   name=PDG.GetParticle(idw).GetName()
   ut.bookHist(h,str(idhnu),name+' momentum (GeV)',400,0.,400.)
   ut.bookHist(h,str(idhnu+100),name+' log10-p vs log10-pt',100,-0.3,1.7,100,-2.,0.5)
   ut.bookHist(h,str(idhnu+200),name+' log10-p vs log10-pt',25,-0.3,1.7,100,-2.,0.5)

pot=0.
#Determine fDs on this file for primaries
nDsprim=0
ntotprim=0

for n in range(nEvents):
  rc = sTree.GetEvent(n)
# check if we deal with charm or beauty:
  if n == 0: 
   if not setByHand and sTree.M>5: 
     chicc = chibb
     print("automatic detection of beauty, configured for beauty")
     print('bb cross section / mbias ',chicc)
   else:
     print('cc cross section / mbias ',chicc)
   #convert pot to weight corresponding to one spill of 5e13 pot
   print('weights: ',nrpotspill,' p.o.t. per spill')
   print('    ')
   wspill=nrpotspill*chicc/nrcpot
  #sanity check, count number of p.o.t. on input file.
  pt=ROOT.TMath.Sqrt(sTree.mpx**2+sTree.mpy**2)
  #every event appears twice, i.e.
  if pt<1.e-5 and int(sTree.mid)==2212: 
    pot=pot+0.5
    ntotprim+=1
    idabs=int(abs(sTree.id))
    if idabs==431: nDsprim+=1
  P8.event.reset()
  P8.event.append(int(sTree.id),1,0,0,sTree.px,sTree.py,sTree.pz,sTree.E,sTree.M,0.,9.)
  next(P8)
  #P8.event.list()
  for n in range(P8.event.size()):
    #ask for stable particles
    if P8.event[n].isFinal():
      #select neutrinos and mu
      idabs=int(abs(P8.event[n].id()))
      if idabs>11 and idabs<17:
       par= P8.event[n]
       ptGM = ROOT.TMath.Sqrt(sTree.mpx*sTree.mpx+sTree.mpy*sTree.mpy)
       Ntup.Fill(par.id(),par.px(),par.py(),par.pz(),par.e(),par.m(),wspill,sTree.id,sTree.px,sTree.py,sTree.pz,sTree.E,sTree.M,ptGM,sTree.mpz)
       #count total muons from charm/spill, and within some angluar range..
       if idabs==16 or idabs==14 or idabs==12:
         idhnu=idabs+1000
         if par.id()<0: idhnu+=1000
         pt2=par.px()**2+par.py()**2
         ptot=ROOT.TMath.Sqrt(pt2+par.pz()**2)
         l10ptot=min(max(ROOT.TMath.Log10(ptot),-0.3),1.69999)
         l10pt=min(max(ROOT.TMath.Log10(ROOT.TMath.Sqrt(pt2)),-2.),0.4999)
         h[str(idhnu)].Fill(ptot,wspill)                     
         h[str(idhnu+100)].Fill(l10ptot,l10pt,wspill)
         h[str(idhnu+200)].Fill(l10ptot,l10pt,wspill)
       
print('Now at Ntup.Write() for pot=',pot,nrcpot)
if (1.-pot/nrcpot)<1.e-2:
  print('write ntuple, weight/event=',nrpotspill,'x',chicc,'/',nrcpot,'=',wspill)
  Ntup.Write()
  for akey in h: h[akey].Write()
  ftup.Close()
  print('Neutrino statistics/spill of 5.e15 pot:')
  for idnu in range(12,18,2):
  #nu or anti-nu
    for idadd in range(-1,3,2):
     idhnu=1000+idnu
     idw=idnu
     if idadd==-1: 
      idhnu+=1000
      idw=-idnu
     print(idhnu,h[str(idhnu)].GetTitle(),("%8.3E "%(h[str(idhnu)].Integral())))

  fDsP6=1.*nDsprim/ntotprim
  fDs=0.077 #Used in TP..
  print(' ')
  print('fDs of primary proton interactions in P6=',fDsP6, ' should be ',fDs)

else:
  print('*********** WARNING ***********')  
  print('number of POT does not agree between ntuple and hists, i.e.:',pot,'<>',nrcpot)
  print('mu/neutrino ntuple has NOT been written')
#



