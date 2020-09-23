import ROOT,time,os,sys,random,getopt,copy
from array import array
import rootUtils as ut
ROOT.gROOT.LoadMacro("$VMCWORKDIR/gconfig/basiclibs.C")
ROOT.basiclibs()
timer = ROOT.TStopwatch()
timer.Start()
#
R = 0   # run number
msel   = 0 
pbeamh = 400.
nevgen = 100000
#
target=['p+','n0']
#  Assume Molybdum target, fracp is the fraction of protons in nucleus, i.e. 42/98.
#  Used to average chi on p and n target in Pythia.
fracp=0.43
#
PDG      = ROOT.TDatabasePDG.Instance()
myPythia = {}
for p in target: myPythia[p] = ROOT.TPythia6()
#
# Pythia6 can only accept names below in pyinit, hence reset PDG table:
PDG.GetParticle(2212).SetName('p+')
PDG.GetParticle(-2212).SetName('pbar-')
PDG.GetParticle(2112).SetName('n0')
PDG.GetParticle(-2112).SetName('nbar0')
PDG.GetParticle(130).SetName('KL0')
PDG.GetParticle(310).SetName('KS0')
#
def LHCb_tune(P6):
# settings by LHCb for Pythia 6.427 
# https://twiki.cern.ch/twiki/bin/view/LHCb/SettingsSim08
  print ' '
  print '********** LHCb_tune **********'
  #P6.SetCKIN(41,3.0)
  P6.SetMSTP(2,2)         # second order alpha_S , default first-order
  P6.SetMSTP(33,3)        # K factor introduced, PARP(33)
  #P6.SetMSTP(128,2)      # store or not store 
  P6.SetMSTP(81,1)        # multiple interactions on
  P6.SetMSTP(82,3)
  P6.SetMSTP(52,2)        # D=1, PDFLIB, see MSTP 51
  P6.SetMSTP(51,	10042)# (ie CTEQ6 LO fit, with LOrder alpha_S PDF from LHAPDF)
  P6.SetMSTP(142,	0) #do not weigh events
  P6.SetPARP(67,	1.0)
  P6.SetPARP(82,	4.28)   # PARP(78) - PARP(90) : parameters for multiple interactions
  P6.SetPARP(89,	14000)  
  P6.SetPARP(90,	0.238)
  P6.SetPARP(85,	0.33)
  P6.SetPARP(86,	0.66)
  P6.SetPARP(91,	1.0)   # PARP(91) - PARP(100) : parameters for beam-remnant treatment
  P6.SetPARP(149,	0.02)  # PARP(141) - PARP(145) : (D = 10*1.) matrix elements for charmonium production in the non-relativistic QCD framework (NRQCD
  P6.SetPARP(150,	0.085) # PARP(146) - PARP(150) : bottomonium
  P6.SetPARJ(11,	0.4)   # PARJ(11) - PARJ(17) : parameters that determine the spin of mesons when formed in fragmentation or decays. 
  P6.SetPARJ(12,	0.4)
  P6.SetPARJ(13,	0.769)
  P6.SetPARJ(14,	0.09)
  P6.SetPARJ(15,	0.018)
  P6.SetPARJ(16,	0.0815)
  P6.SetPARJ(17,	0.0815)
  P6.SetMSTJ(26,	0) #  (D = 0.4) extra suppression factor for eta0 production in fragmentation
  P6.SetPARJ(33,	0.4) # PARJ(33) - PARJ(34):(D = 0.8 GeV, 1.5 GeV) are,#
                             # together with quark masses, used to define the remaining energy below which the fragmentation of a parton system is stopped and two final hadrons formed. 
  print '********** LHCb_tune **********'
  print ' '
def PoorE791_tune(P6):
# settings with default Pythia6 pdf, based on getting <pt> at 500 GeV pi-
# same as that of E791: http://arxiv.org/pdf/hep-ex/9906034.pdf
  print ' '
  print '********** PoorE791_tune **********'
  #change pt of D's to mimic E791 data.
  P6.SetPARP(91,1.6)  # 1.6  # default 2.0
  P6.SetPARP(92,P6.GetPARP(91)/ROOT.TMath.Sqrt(6.))
  print  'PARP(91)=',P6.GetPARP(91),P6.GetPARP(92)
  #what PDFs etc.. are being used:
  print 'MSTP PDF info, i.e. (51) and (52)=',P6.GetMSTP(51),P6.GetMSTP(52)
  #set multiple interactions equal to Fortran version, i.e.=1, default=4, and adapt parp(89) accordingly
  P6.SetMSTP(82,1)
  P6.SetPARP(89,1000.)
  print 'And corresponding multiple parton stuff, i.e. MSTP(82),PARP(81,89,90)=',P6.GetMSTP(82),P6.GetPARP(81),P6.GetPARP(89),P6.GetPARP(90)
  print '********** PoorE791_tune **********'
  print ' '
#choose the Pythia tune:
E791tuning = True
LHCbtuning = False
for p in target: 
 myPythia[p].SetMSEL(msel)
 if E791tuning:   PoorE791_tune(myPythia[p])
 elif LHCbtuning: LHCb_tune(myPythia[p])

 myPythia[p].SetMSUB(1,1) # qq->ll & qq->Z
 mumu=True
 if mumu:
   myPythia[p].SetMDME(174,1,0) # d      + dbar,        off
   myPythia[p].SetMDME(175,1,0) # u      + ubar,        off
   myPythia[p].SetMDME(176,1,0) # s      + sbar,        off
   myPythia[p].SetMDME(177,1,0) # c      + cbar,        off
   myPythia[p].SetMDME(178,1,0) # b      + bbar,        off
   myPythia[p].SetMDME(179,1,0) # t      + tbar,        off
   myPythia[p].SetMDME(182,1,0) # e-     + e+,          off
   myPythia[p].SetMDME(183,1,0) # nu_e   + nu_ebar,     off
   myPythia[p].SetMDME(184,1,1) # mu-    + mu+,         on
   myPythia[p].SetMDME(185,1,0) # nu_mu  + nu_mubar,    off
   myPythia[p].SetMDME(186,1,0) # tau-   + tau+,        off
   myPythia[p].SetMDME(187,1,0) # nu_tau + nu_taubar,   off
   myPythia[p].SetMDME(180,1,0) # not developed channel, cross section is 0
   myPythia[p].SetMDME(181,1,0) # not developed channel, cross section is 0
   myPythia[p].SetMDME(188,1,0) # not developed channel, cross section is 0
   myPythia[p].SetMDME(189,1,0) # not developed channel, cross section i
#start with different random number for each run...
 if R == '': R = int(time.time()*100000000%900000000)
 print 'Setting random number seed =',R
 myPythia[p].SetMRPY(1,R)
 myPythia[p].Initialize("FIXT",'p+',p,pbeamh)

if E791tuning:
 Fntuple='DrellYan-parp'+str(int(myPythia['p+'].GetPARP(91)*10))+'-MSTP82-'+str(myPythia['p+'].GetMSTP(1))+'-MSEL'+str(msel)+'-ntuple.root'
else:
 Fntuple='DrellYan-ntuple.root'

ftup = ROOT.TFile.Open(Fntuple, 'RECREATE')
Ntup = ROOT.TNtuple("pythia6","pythia6 DrellYan",\
       "id1:px1:py1:pz1:M1:id2:px2:py2:pz2:M2:M:P:Pt:Y")

for iev in range(nevgen):
   if iev%1000==0: print 'Generate event ',iev
   idpn='p+'
#   decide on p or n target in Mo
   if random.random > fracp: idpn='n0'
   p6 = myPythia[idpn]
   p6.GenerateEvent()
   p6.Pyedit(3)
   if iev < 10: p6.Pylist(2)
   p1 = ROOT.Math.PxPyPzMVector(p6.GetP(1,1),p6.GetP(1,2),p6.GetP(1,3),p6.GetP(1,5))
   p2 = ROOT.Math.PxPyPzMVector(p6.GetP(2,1),p6.GetP(2,2),p6.GetP(2,3),p6.GetP(2,5))
   P = p1+p2
   Ntup.Fill(p6.GetK(1,1),p6.GetP(1,1),p6.GetP(1,2),p6.GetP(1,3),p6.GetP(1,5),p6.GetK(2,1),p6.GetP(2,1),p6.GetP(2,2),p6.GetP(2,3),p6.GetP(2,5),P.M(),P.P(),P.Pt(),P.Rapidity())

print 'Now at Ntup.Write()'
Ntup.Write()
ftup.Close()

myPythia['n0'].Pystat(1)
myPythia['p+'].Pystat(1)

timer.Stop()
rtime = timer.RealTime()
ctime = timer.CpuTime()
print ' ' 
print "Macro finished succesfully." 
print "Output file is ",  ftup.GetName()
print "Real time ",rtime, " s, CPU time ",ctime,"s"

#yBeam = 3.3741642051118204
#lumi  = 30.7 # pb-1
#    x = 1.192 * 0.45 (0.3<ycms) * 0.5 (cosTheta) # pb
# f=ROOT.TFile('DrellYan-parp10-MSTP82-3-MSEL0-ntuple.root')
# nt=f.pythia6
# nt.Draw('M')

