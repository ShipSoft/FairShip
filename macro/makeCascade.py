import ROOT,time,os,sys,random
import rootUtils as ut
import time

#generate ccbar (msel=4) or bbbar(msel=5)
mselcb=4
if len(sys.argv)>1: mselcb = int(sys.argv[1])
nevgen=10000
if len(sys.argv)>2: nevgen = int(sys.argv[2])
Fntuple='Cascade-parp16-MSTP82-1-MSEL'+str(mselcb)+'-ntuple.root'
Fhists='Cascade-parp16-MSTP82-1-MSEL'+str(mselcb)+'-hists.root'
if len(sys.argv)>3: Fntuple = int(sys.argv[3])
if len(sys.argv)>4: Fhists = int(sys.argv[4])
print 'Generate ',nevgen,' p.o.t. with msel=',mselcb
print 'Output ntuples written to: ',Fntuple
print 'Output checking hists written to: ',Fhists

#some parameters for generating the chi (sigma(signal)/sigma(total) as a function of momentum
# event/momentum, and number of momentum points taken to calculate sig/sigtot
nev=5000
nrpoints=20
# cascade beam particles, anti-particles are generated automatically if they exist.
idbeam=[2212,211,2112,321,130,310]
target=['p+','n0']
print 'Chi generation with ',nev,' events/point, nr points=',nrpoints
print 'Cascade beam particle: ',idbeam
print 'Target particles: ',target

# lower/upper momentum limit for beam, depends on msel..
# signal particles wanted (and their antis), which could decay semi-leptonically.
pbeamh=400.
if mselcb==4: 
   pbeaml=34.
   idsig=[411, 421, 431,4122,4132,4232,4332,4412,4414,4422,4424,4432,4434,4444]
elif mselcb==5:
   pbeaml=130.
   idsig=[511, 521, 531, 541,5122,5132,5142,5232,5242,5332,5342,5412,5414,5422,5424,5432,5434,5442,5444,5512,5514,5522,5524,5532,5534,5542,5544,5554]
else:
   print 'Error: msel is unknown',mselcb,' STOP program'
   sys.exit('ERROR on input, exit')

#  Assume Molybdum target, fracp is the fraction of protons in nucleus, i.e. 42/98.
#  Used to average chi on p and n target in Pythia.
fracp=0.43
#

PDG = ROOT.TDatabasePDG.Instance()
myPythia = ROOT.TPythia6()
tp = ROOT.tPythia6Generator()

#  Pythia output to dummy (11) file (to screen use 6)
#myPythia.SetMSTU(11, 11)

# Pythia6 can only accept names below in pyinit, hence reset PDG table:
PDG.GetParticle(2212).SetName('p+')
PDG.GetParticle(-2212).SetName('pbar-')
PDG.GetParticle(2112).SetName('n0')
PDG.GetParticle(-2112).SetName('nbar0')
PDG.GetParticle(130).SetName('KL0')
PDG.GetParticle(310).SetName('KS0')
#change pt of D's to mimic E791 data.
myPythia.SetPARP(91,1.6)
print  'PARP(91)=',myPythia.GetPARP(91)
#lower lowest sqrt(s) allowed for generating events
myPythia.SetPARP(2,2.)
#what PDFs etc.. are being used:
print 'MSTP PDF info, i.e. (51) and (52)=',myPythia.GetMSTP(51),myPythia.GetMSTP(52)
#set multiple interactions equal to Fortran version, i.e.=1, default=4, and adapt parp(89) accordingly
myPythia.SetMSTP(82,1)
myPythia.SetPARP(89,1000.)
print 'And correspondin multiple parton inetraction stuff, i.e. MSTP(82),PARP(81,89,90)=',myPythia.GetMSTP(82),myPythia.GetPARP(81),myPythia.GetPARP(89),myPythia.GetPARP(90)

def fillp1(hist):
# scan filled bins in hist, and fill intermediate bins with lineair interpolation
   nb=hist.GetNbinsX()
   i1=hist.FindBin(pbeaml,0.,0.)
   y1=hist.GetBinContent(i1)
   p1=hist.GetBinCenter(i1)
   for i in range(i1+1,nb+1):
      if hist.GetBinContent(i)>0.:
         y2=hist.GetBinContent(i)
         p2=hist.GetBinCenter(i)
         tg=(y2-y1)/(p2-p1)
         for ib in range(i1+1,i):
            px=hist.GetBinCenter(ib)
            yx=(px-p1)*tg+y1
            hist.Fill(px,yx)
            i1=i
            y1=y2
            p1=p2
 

#start with different random number for each run...
R = int(time.time()%900000000)
myPythia.SetMRPY(1,R)

#histogram helper
h={}

#  initalise phase, determine chi=sigma(signal)/sigma(total) for many beam momenta.
#  loop over beam particles
id=0
nb=400
t0=time.time()
idhist=len(idbeam)*4*[0]
for idp in range(0,len(idbeam)):
#  particle or antiparticle
   for idpm in range(-1,3,2):
      idw=idbeam[idp]*idpm
      if PDG.GetParticle(idw)<>None:
         name=PDG.GetParticle(idw).GetName()
#  particle exists, book hists etc..
         id=id+1
         ut.bookHist(h,str(id*10+1),'sigma vs p, '+name+'->p',nb,0.5,pbeamh+0.5)
         ut.bookHist(h,str(id*10+2),'sigma-tot vs p, '+name+'->p',nb,0.5,pbeamh+0.5)
         ut.bookHist(h,str(id*10+3),'chi vs p, '+name+'->p',nb,0.5,pbeamh+0.5)
         ut.bookHist(h,str(id*10+4),'sigma vs p, '+name+'->n',nb,0.5,pbeamh+0.5)
         ut.bookHist(h,str(id*10+5),'sigma-tot vs p, '+name+'->n',nb,0.5,pbeamh+0.5)
         ut.bookHist(h,str(id*10+6),'chi vs p, '+name+'->n',nb,0.5,pbeamh+0.5)
         ut.bookHist(h,str(id*10+7),'chi vs p, '+name+'->Mo',nb,0.5,pbeamh+0.5)
         ut.bookHist(h,str(id*10+8),'Prob(normalised) vs p, '+name+'->Mo',nb,0.5,pbeamh+0.5)
#  keep track of histogram<->Particle id relation.
         idhist[id]=idw
         print 'Get chi vs momentum for beam particle=',idw,name
#  target is proton or neutron
         for idpn in range(2):
            idadd=idpn*3
#  loop over beam momentum
            for ipbeam in range(nrpoints):
               pbw=ipbeam*(pbeamh-pbeaml)/(nrpoints-1)+pbeaml
#  convert to center of a bin
               ibin=h[str(id*10+1+idadd)].FindBin(pbw,0.,0.)
               pbw=h[str(id*10+1+idadd)].GetBinCenter(ibin)
#  new particle/momentum, init again, first signal run.
               myPythia.SetMSEL(mselcb)       # set forced ccbar or bbbar generation
               myPythia.Initialize('FIXT',name,target[idpn],pbw)
               for iev in range(nev): 
                  if iev%1000==0: print 'generated signal events',iev,' seconds:',time.time()-t0
                  myPythia.GenerateEvent()
#  signal run finished, get cross-section
               h[str(id*10+1+idadd)].Fill(pbw,tp.getPyint5_XSEC(2,0))
#  now total cross-section, i.e. msel=2
               myPythia.SetMSEL(2)       
               myPythia.Initialize('FIXT',name,target[idpn],pbw)
               for iev in range(nev/10): 
                  if iev%100==0: print 'generated mbias events',iev,' seconds:',time.time()-t0
                  myPythia.GenerateEvent()
#   get cross-section
               h[str(id*10+2+idadd)].Fill(pbw,tp.getPyint5_XSEC(2,0))
#   for this beam particle, do arithmetics to get chi.
            h[str(id*10+3+idadd)].Divide(h[str(id*10+1+idadd)],h[str(id*10+2+idadd)],1.,1.)
#   fill with lineair function between evaluated momentum points.
            fillp1(h[str(id*10+3+idadd)])          
#  combined p and n target with p/n ratio im Molyndium
         h[str(id*10+7)].Add(h[str(id*10+3)],h[str(id*10+6)],fracp,1.-fracp)

#  collected all, now re-scale to make max chi at 400 Gev==1.
chimx=0.
for i in range(1,id+1):
   ibh=h[str(i*10+7)].FindBin(pbeamh)
   print 'beam id, momentum,chi,chimx=',i,idhist[i],pbeamh,h[str(i*10+7)].GetBinContent(ibh),chimx
   if h[str(i*10+7)].GetBinContent(ibh)>chimx: chimx=h[str(i*10+7)].GetBinContent(ibh)
chimx=1./chimx
for i in range(1,id+1):
   h[str(i*10+8)].Add(h[str(i*10+7)],h[str(i*10+7)],chimx,0.)

# switch output printing OFF for generation pahse.
myPythia.SetMSTU(11, 11)
# Generate ccbar (or bbbar) pairs according to probability in hists i*10+8.
# some check histos 
ut.bookHist(h,str(1),'E of signals',100,0.,400.)
ut.bookHist(h,str(2),'nr signal per cascade depth',10,0.5,10.5)
ut.bookHist(h,str(3),'D0 pt**2',40,0.,4.)
ut.bookHist(h,str(4),'D0 pt**2',100,0.,18.)
ut.bookHist(h,str(5),'D0 pt',100,0.,10.)
ut.bookHist(h,str(6),'D0 XF',100,-1.,1.)

ftup = ROOT.TFile.Open(Fntuple, 'RECREATE')
Ntup = ROOT.TNtuple("pythia6","pythia6 heavy flavour","id:px:py:pz:E:M:mid:mpx:mpy:mpz:mE")

#make sure all particles for cascade production are stable
for kf in idbeam:
   kc = myPythia.Pycomp(kf)
   myPythia.SetMDCY(kc,1,0)

#declare the stack for the cascade particles
stack=1000*[0]
for iev in range(nevgen):
   if iev%1000==0: print 'Generate event ',iev
#put 400. GeV proton on the stack
   nstack=0
# stack: PID,px,py,pz,cascade depth
   stack[nstack]=[2212,0.,0.,pbeamh,1]
   while nstack>=0:
# generate a signal based on probabilities in hists i*10+8?
      ptot=ROOT.TMath.Sqrt(stack[nstack][1]**2+stack[nstack][2]**2+stack[nstack][3]**2)
      prbsig=0.
      for i in range(1,id+1):
#   get hist id for this beam particle
         if stack[nstack][0]==idhist[i]: 
            ib=h[str(i*10+8)].FindBin(ptot,0.,0.)
            prbsig=h[str(i*10+8)].GetBinContent(ib)
      if prbsig>random.random():
# last particle on the stack as beam particle
         for k in range(1,4):  
            myPythia.SetP(1,k,stack[nstack][k])
            myPythia.SetP(2,k,0.)
#   new particle/momentum, init again: signal run.
         myPythia.SetMSEL(mselcb)       # set forced ccbar or bbbar generation
         myPythia.Initialize('3MOM',PDG.GetParticle(stack[nstack][0]).GetName(),'p+',0.)
         myPythia.GenerateEvent()
#  look for the signal particles
         for itrk in range(1,myPythia.GetN()+1):
            idabs = ROOT.TMath.Abs(myPythia.GetK(itrk,2))
            for isig in range(len(idsig)):
               if idabs==idsig[isig]:
#                  print myPythia.GetK(itrk,2),myPythia.GetP(itrk,1),myPythia.GetP(itrk,2),myPythia.GetP(itrk,3),myPythia.GetK(1,2),myPythia.GetP(1,1),myPythia.GetP(1,2),myPythia.GetP(1,3)
                  Ntup.Fill(float(myPythia.GetK(itrk,2)),float(myPythia.GetP(itrk,1)),float(myPythia.GetP(itrk,2)),float(myPythia.GetP(itrk,3)),float(myPythia.GetP(itrk,4)),float(myPythia.GetP(itrk,5)),float(myPythia.GetK(1,2)),float(myPythia.GetP(1,1)),float(myPythia.GetP(1,2)),float(myPythia.GetP(1,3)),float(myPythia.GetP(1,4)),float(myPythia.GetP(1,5)))
                  h['1'].Fill(myPythia.GetP(itrk,4))
                  h['2'].Fill(stack[nstack][4])
                  if idabs==421 and stack[nstack][4]==1 :
# some checking hist to monitor pt**2, XF of prompt D^0 
                     pt2=myPythia.GetP(itrk,1)**2+myPythia.GetP(itrk,2)**2
                     h['3'].Fill(pt2)
                     h['4'].Fill(pt2)
                     h['5'].Fill(ROOT.TMath.Sqrt(pt2))
#   boost to Cm frame for XF ccalculation of D^0
                     beta=pbeamh/(myPythia.GetP(1,4)+myPythia.GetP(2,5))
                     gamma=(1-beta**2)**-0.5
                     pbcm=-gamma*beta*myPythia.GetP(1,4)+gamma*myPythia.GetP(1,3)
                     pDcm=-gamma*beta*myPythia.GetP(itrk,4)+gamma*myPythia.GetP(itrk,3)
                     xf=pDcm/pbcm
                     h['6'].Fill(xf)

#  now generate msel=2 to add new cascade particles to the stack
      for k in range(1,4):  
         myPythia.SetP(1,k,stack[nstack][k])
         myPythia.SetP(2,k,0.)
#   new particle/momentum, init again, generate total cross-section event
      myPythia.SetMSEL(2)       # mbias event
      myPythia.Initialize('3MOM',PDG.GetParticle(stack[nstack][0]).GetName(),'p+',0.)
      myPythia.GenerateEvent()
#  remove used particle from the stack, before adding new
      icas=stack[nstack][4]+1
      nstack=nstack-1  
      for itrk in range(1,myPythia.GetN()+1):
         if myPythia.GetK(itrk,1)==1:
            ptot=ROOT.TMath.Sqrt(myPythia.GetP(itrk,1)**2+myPythia.GetP(itrk,2)**2+myPythia.GetP(itrk,3)**2)
            if ptot>pbeaml:
#  produced particle is stable and has enough momentum, is it in the wanted list?
               for isig in range(len(idbeam)):
                  if ROOT.TMath.Abs(myPythia.GetK(itrk,2))==idbeam[isig] and nstack<999:
                     nstack=nstack+1
                     stack[nstack]=[myPythia.GetK(itrk,2),myPythia.GetP(itrk,1),myPythia.GetP(itrk,2),myPythia.GetP(itrk,3),icas]

print 'Now at Ntup.Write()'
Ntup.Write()
ftup.Close()
#
ut.writeHists(h,Fhists)


