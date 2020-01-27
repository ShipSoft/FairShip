import ROOT,time,os,sys,random,getopt,copy
from array import array
import rootUtils as ut
ROOT.gROOT.LoadMacro("$VMCWORKDIR/gconfig/basiclibs.C")
ROOT.basiclibs()
timer = ROOT.TStopwatch()
timer.Start()
#
R = 0   # run number
msel   = 61 # charmonimum production in the NRQCD framework
# msel   = 4 # heavy quark
pbeamh = 400.
nevgen = 5000000
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
for p in target: 
#lower lowest sqrt(s) allowed for generating events
 myPythia[p].SetPARP(2,2.)
 myPythia[p].SetMSEL(msel)
 if E791tuning:
  # PoorE791_tune(myPythia[p])
  LHCb_tune(myPythia[p])
#  Pythia output to dummy (11) file (to screen use 6)
 myPythia[p].OpenFortranFile(11, os.devnull)
 myPythia[p].SetMSTU(11, 11)
#start with different random number for each run...
 if R == '': R = int(time.time()*100000000%900000000)
 print 'Setting random number seed =',R
 myPythia[p].SetMRPY(1,R)
 myPythia[p].Initialize("FIXT",'p+',p,pbeamh)

if E791tuning:
 Fntuple='Jpsi-parp'+str(int(myPythia['p+'].GetPARP(91)*10))+'-MSTP82-'+str(myPythia['p+'].GetMSTP(1))+'-MSEL'+str(msel)+'-ntuple.root'
else:
 Fntuple='Jpsi-MSEL'+str(msel)+'-ntuple.root'

ftup = ROOT.TFile.Open(Fntuple, 'RECREATE')
Ntup = ROOT.TNtuple("pythia6","pythia6 Jpsi",\
       "id:px:py:pz:E:M:mid:mpx:mpy:mpz:mE:mM:k:a0:a1:a2:a3:a4:a5:a6:a7:a8:a9:a10:a11:a12:a13:a14:a15:\
s0:s1:s2:s3:s4:s5:s6:s7:s8:s9:s10:s11:s12:s13:s14:s15")

for iev in range(nevgen):
   if iev%1000==0: print 'Generate event ',iev
   idpn='p+'
#   decide on p or n target in Mo
   if random.random > fracp: idpn='n0'
   p6 = myPythia[idpn]
   p6.GenerateEvent()
   for ii in range(1,p6.GetN()+1):
    pid    = p6.GetK(ii,2)
    if pid != 443: continue
    px = p6.GetP(ii,1)
    py = p6.GetP(ii,2)
    pz = p6.GetP(ii,3)
    E  = p6.GetP(ii,4)
    M  = p6.GetP(ii,5)
    mii = p6.GetK(ii,3)
    mpid = p6.GetK(mii,2)
    mpx = p6.GetP(mii,1)
    mpy = p6.GetP(mii,2)
    mpz = p6.GetP(mii,3)
    mE  = p6.GetP(mii,4)
    mM  = p6.GetP(mii,5)
    Ntup.Fill(pid,px,py,pz,E,M,mpid,mpx,mpy,mpz,mE,mM)

print 'Now at Ntup.Write()'
Ntup.Write()
ftup.Close()

timer.Stop()
rtime = timer.RealTime()
ctime = timer.CpuTime()
print ' ' 
print "Macro finished succesfully." 
print "Output file is ",  ftup.GetName()
print "Real time ",rtime, " s, CPU time ",ctime,"s"

#nt.Draw('0.5*log((E+pz)/(E-pz))')
#nt.Draw('sqrt(px*px+py*py)')
