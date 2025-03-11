import ROOT
import rootUtils as ut
from array import array
theSeed      = 0
h = {}
ROOT.gRandom.SetSeed(theSeed)
ROOT.gSystem.Load("libpythia8")

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-b", "--heartbeat",  dest="heartbeat", type=int,  help="progress report",  default=10000)
parser.add_argument("-n", "--pot",  dest="NPoT", type=int,  help="protons on target",          default=1000000)
parser.add_argument("-r", "--run",  dest="run",  type=int,  help="production sequence number", default=0)
parser.add_argument('-M', '--Emin', dest='Emin', type=float,help="cutOff",                     default=1.0)
parser.add_argument('-E', '--Beam', dest='fMom', type=float,help="beam momentum",              default=400.)
parser.add_argument('-J', '--Jpsi-mainly',  action='store_true', dest='JpsiMainly',  default=False)
parser.add_argument('-Y', '--DrellYan',     action='store_true', dest='DrellYan',  default=False)
parser.add_argument('-P', '--PhotonCollision',     action='store_true', dest='PhotonCollision',  default=False)
parser.add_argument('-C', '--charm',               action='store_true', dest='charm',  default=False)
parser.add_argument('-X', '--PDFpSet',dest="PDFpSet",  type=str,  help="PDF pSet to use", default="13")
parser.add_argument('-u', '--uOnly',        action='store_true', dest='uOnly',  default=False)

# for lhapdf, -X LHAPDF6:cteq6

options = parser.parse_args()
print("start IGNOREIGNOREIGNOREIGNOREIGNOREIGNOREIGNOREIGNOREIGNORE")
X=ROOT.FixedTargetGenerator()
print("end IGNOREIGNOREIGNOREIGNOREIGNOREIGNOREIGNOREIGNOREIGNORE")

def yBeam(Mproton = 0.938272081, pbeam = 400.):
    Ebeam   = ROOT.TMath.Sqrt(pbeam**2+Mproton**2)
    betaCM  = pbeam / (Ebeam + Mproton)
    y_beam  = 0.5*ROOT.TMath.Log( (1+betaCM)/(1-betaCM))   # https://arxiv.org/pdf/1604.02651.pdf
    return y_beam

generators = {'p':ROOT.Pythia8.Pythia(),'n':ROOT.Pythia8.Pythia()}
generators['p'].settings.mode("Beams:idB",  2212)
generators['n'].settings.mode("Beams:idB",  2112)

for g in generators:
   ut.bookHist(h, 'xsec_'+g,   ' total cross section',1,0.,1.)
   ut.bookHist(h, 'M_'+g,   ' N mu+mu-;M [GeV/c^{2}];y_{CM}',500,0.,10.,120,-3.,3.,100,0.,5.)
   ut.bookHist(h, 'cosCS_'+g,   ' N cosCS;cosCS;y_{CM}',100,-1.,1.,120,-3.,3.,100,0.,5.)
   ut.bookHist(h, 'cosCSJpsi_'+g,   ' N cosCS 2.9<M<4.5;cosCS;y_{CM}',100,-1.,1.,120,-3.,3.,100,0.,5.)
   generators[g].settings.mode("Next:numberCount",options.heartbeat)
   generators[g].settings.mode("Beams:idA",  2212)
   generators[g].settings.mode("Beams:frameType",  2)
   generators[g].settings.parm("Beams:eA",options.fMom)
   generators[g].settings.parm("Beams:eB",0.)
   generators[g].readString("PDF:pSet = "+options.PDFpSet)
   if options.DrellYan:
     generators[g].readString("WeakSingleBoson:ffbar2gmZ = on")
     if options.uOnly:
        generators[g].readString("23:onMode = off")
        generators[g].readString("23:onIfAll = 13 13")
     generators[g].readString("23:mMin = "+str(options.Emin))
     generators[g].readString("PhaseSpace:mHatMin = "+str(options.Emin))
     # generators[g].readString("BeamRemnants:primordialKThard = 0.8")
     generators[g].readString("PartonLevel:FSR = on")
   elif options.JpsiMainly:
# use this for all onia productions
     generators[g].readString("Onia:all(3S1) = on")
     if options.uOnly:
          generators[g].readString("443:onMode = off")
          generators[g].readString("443:onIfAll = 13 13")
          generators[g].readString("553:onMode = off")
          generators[g].readString("553:onIfAll = 13 13")
   elif options.PhotonCollision:
     generators[g].readString("PhotonCollision:gmgm2mumu = on")
     generators[g].readString("PhaseSpace:mHatMin = "+str(options.Emin))
   elif options.charm:
     generators[g].readString("HardQCD:hardccbar = on")
   else:
     generators[g].readString("SoftQCD:inelastic = on")
   generators[g].init()

rc = generators['p'].next()
processes = generators['p'].info.codesHard()
hname = 'pythia8_PDFpset'+options.PDFpSet+'_Emin'+str(options.Emin)+'_'+generators['p'].info.nameProc(processes[0])
hname = hname.replace('*','star')
hname = hname.replace('->','to')
hname = hname.replace('/','')

f = ROOT.TFile("ntuple-"+hname+".root","RECREATE")
signal = ROOT.TNtuple("ntuple","ntuple","M:P:Pt:y:p1x:p1y:p1z:p2x:p2y:p2z:cosCS")

timer = ROOT.TStopwatch()
timer.Start()

ntagged = {'p':0,'n':0}
ybeam = yBeam(pbeam = options.fMom)
for n in range(int(options.NPoT)):
  for g in generators:
    py = generators[g]
    rc = py.next()
    nmu = {}
    for ii in range(1,py.event.size()):
       if options.DrellYan and py.event[ii].id()!=23: continue
       if options.PhotonCollision and py.event[ii].id()!=22: continue
       for m in py.event.daughterList(ii):
         if abs(py.event[m].id())==13: nmu[m]=ii
    if len(nmu) == 2:
       ntagged[g]+=1
       ks = list(nmu)
       if options.DrellYan:
          Zstar = py.event[nmu[ks[0]]]
          rc=h['M_'+g].Fill(Zstar.m(),py.event[nmu[ks[0]]].y()-ybeam,py.event[nmu[ks[0]]].pT())
# what about polarization?
          ii = nmu[ks[0]]
          d0 = py.event.daughterList(ii)[0]
          d1 = py.event.daughterList(ii)[1]
          if py.event[d0].id() < 0:
              nlep      = py.event[d0]
              nantilep  = py.event[d1]
          else:
              nlep      = py.event[d1]
              nantilep  = py.event[d0]
          P1pl = nlep.e()+nlep.pz()
          P2pl = nantilep.e()+nantilep.pz()
          P1mi = nlep.e()-nlep.pz()
          P2mi = nantilep.e()-nantilep.pz()
          A = P1pl*P2mi-P2pl*P1mi
          cosCS = Zstar.pz()/abs(Zstar.pz()) * 1./Zstar.m()/ROOT.TMath.Sqrt(Zstar.m2()+Zstar.pT()**2)*A
          rc=h['cosCS_'+g].Fill(cosCS,Zstar.y()-ybeam,py.event[nmu[ks[0]]].pT())
          if Zstar.m()>2.9 and Zstar.m()<4.5: rc=h['cosCSJpsi_'+g].Fill(cosCS,py.event[nmu[ks[0]]].y()-ybeam,py.event[nmu[ks[0]]].pT())
          rc = signal.Fill(Zstar.m(),Zstar.pAbs(),Zstar.pT(),Zstar.y(),nlep.px(),nlep.py(),nlep.pz(),nantilep.px(),nantilep.py(),nantilep.pz(),cosCS)
       if options.PhotonCollision:
          M={}
          k=0
          for m in ks:
             M[k]=ROOT.TLorentzVector(py.event[m].px(),py.event[m].py(),py.event[m].pz(),py.event[m].e())
             k+=1
          G = M[0]+M[1]
          rc=h['M_'+g].Fill(G.M(),G.Rapidity()-ybeam,G.Pt())


print(">>>> proton statistics,  ntagged=",ntagged['p'])
generators['p'].stat()
print( ">>>> neutron statistics,  ntagged=",ntagged['n'])
generators['n'].stat()

timer.Stop()
rtime = timer.RealTime()
ctime = timer.CpuTime()
print("run ",options.run," PoT ",options.NPoT," Real time ",rtime, " s, CPU time ",ctime,"s")
signal.Write()
for g in generators:
   sigma = generators[g].info.sigmaGen(processes[0])
   h['xsec_'+g].SetBinContent(1,sigma)
ut.writeHists(h,hname+'.root')

def na50(online=True):
   for g in generators:
      if online:
        processes = generators[g].info.codesHard()
        name  = generators[g].info.nameProc(processes[0])
        sigma = generators[g].info.sigmaGen(processes[0])
      else:
        name = ''
        sigma = h['xsec_'+g].GetBinContent(1)
      yax = h['M_'+g].GetYaxis()
      xax = h['M_'+g].GetXaxis()
      Mmin = xax.FindBin(2.9)
      Mmax = xax.FindBin(4.5)
      Ymin = yax.FindBin(-0.425)
      Ymax = yax.FindBin(0.575)
      h['MA'] = h['M_'+g].ProjectionX('MA')
      h['M'] = h['M_'+g].ProjectionX('M',Ymin,Ymax)
      print("generator     sigma   mumu-ratio  in-mass-range  in-y-range")
      print("%s %s %6.2F nbarn, %5.2F, %5.2G, %5.2F    "%(g,name,sigma*1E6,\
            float(h['MA'].GetEntries())/options.NPoT,\
            h['MA'].Integral(Mmin,Mmax)/float(h['MA'].GetEntries()),\
            h['M'].GetEntries()/float(h['MA'].GetEntries())))
      fraction = h['M'].Integral(Mmin,Mmax)/options.NPoT
   # multiply with 0.5 assuming no polarization -0.5 < cosCS < 0.5
      print("cross section a la NA50 for : %s %5.2F pb"%(g,0.5*fraction*sigma*1E9))
   # via cosCS
   for g in generators:
      if online:
        processes = generators[g].info.codesHard()
        name  = generators[g].info.nameProc(processes[0])
        sigma = generators[g].info.sigmaGen(processes[0])
      else:
        name = ''
        sigma = h['xsec_'+g].GetBinContent(1)
      yax = h['cosCSJpsi_'+g].GetYaxis()
      xax = h['cosCSJpsi_'+g].GetXaxis()
      Mmin = xax.FindBin(-0.5)
      Mmax = xax.FindBin(0.5)
      Ymin = yax.FindBin(-0.425)
      Ymax = yax.FindBin(0.575)
      h['MA'] = h['cosCSJpsi_'+g].ProjectionX('MA')
      h['M']  = h['cosCSJpsi_'+g].ProjectionX('M',Ymin,Ymax)
      print("generator     sigma   mumu-in-mass-range% cosCS in-y-range")
      print("%s %s %6.2F nbarn, %5.2F, %5.2F, %5.2F   "%(g,name,sigma*1E6,\
            float(h['MA'].GetEntries())/options.NPoT*100.,\
            h['MA'].Integral(Mmin,Mmax)/float(h['MA'].GetEntries()),\
            h['M'].GetEntries()/float(h['MA'].GetEntries())))
      fraction = h['M'].Integral(Mmin,Mmax)/options.NPoT
   # taking polarization into account.
      print("cross section a la NA50, -0.5<cosCS<0.5: %5.2F pb"%(fraction*sigma*1E9))

def muflux():
   Z_Mo = 96.
   P_Mo = 42
   fraction = {}
   for g in generators:
      processes = generators[g].info.codesHard()
      name  = generators[g].info.nameProc(processes[0])
      sigma = generators[g].info.sigmaGen(processes[0])
      yax = h['M_'+g].GetYaxis()
      xax = h['M_'+g].GetXaxis()
      Mmin = xax.FindBin(0.)
      Mmax = xax.FindBin(5.)
      Ymin = yax.FindBin(0.3)
      Ymax = yax.FindBin(3.)
      h['MA'] = h['M_'+g].ProjectionX('MA')
      h['M'] = h['M_'+g].ProjectionX('M',Ymin,Ymax)
      print(g,name,sigma,float(h['MA'].GetEntries())/options.NPoT,h['MA'].Integral(Mmin,Mmax)/float(h['MA'].GetEntries()),h['M'].GetEntries()/float(h['MA'].GetEntries()))
      fraction[g] = h['M'].Integral(Mmin,Mmax)/options.NPoT
   meanFraction = (fraction['p']*P_Mo+fraction['n']*(Z_Mo-P_Mo))/Z_Mo * sigma
   print("cross section a la muflux: %5.2F pb"%(0.5*meanFraction*1E9))

def debugging(g):
   generators[g].settings.listAll()
