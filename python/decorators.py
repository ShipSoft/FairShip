from ctypes import c_double
import ROOT
import shipunit as u

def MCPointPrintOut(x):
  p = ROOT.TDatabasePDG.Instance().GetParticle(x.PdgCode())
  n=''
  if p: n = p.GetName()
  txt = '("%s") X:%6.3Fcm Y:%6.3Fcm Z:%6.3Fcm dE/dx:%6.2FMeV %s'%(\
    x.Class_Name(),x.GetX(),x.GetY(),x.GetZ(),x.GetEnergyLoss()/u.MeV,n)
  return txt
def MCTrackPrintOut(x):
  c = x.GetPdgCode()
  p = ROOT.TDatabasePDG.Instance().GetParticle(c)
  n=''
  if p: n = p.GetName()
  m = x.GetMotherId()
  txt = '("ShipMCTrack") pdgCode: %7i(%10s)  Z=%6.1F m P=%6.3F GeV/c mother=%i %s'%(c,n,x.GetStartZ()/u.m,x.GetP(),m,x.GetProcName())
  return txt
def vetoHitPrintOut(x):
  txt = '("vetoHit") detID:%7i  ADC:%5.2F TDC:%5.2F'%(x.GetDetectorID(),x.GetADC(),x.GetTDC())
  return txt
def muonHitPrintOut(x):
  txt = '("muonHit") detID:%7i  TDC:%5.2F  isValid:%r'%(x.GetDetectorID(),x.GetDigi(),x.isValid())
  return txt
def TimeDetHitPrintOut(x):
  t = x.GetMeasurements()
  txt = '("TimeDetHit") detID:%7i  TDC1:%5.2F TDC2:%5.2F  isValid:%r'%(x.GetDetectorID(),t[0],t[1],x.isValid())
  return txt
def FitTrackPrintOut(x):
  st = x.getFitStatus()
  if st.isFitConverged():
   chi2DoF = st.getChi2()/st.getNdf()
   sta = x.getFittedState()
   P = sta.getMomMag()
   txt = '("FitTrack") chi2/dof:%3.1F  P:%5.2FGeV/c pdg:%i'%(chi2DoF,P,sta.getPDG())
  else:
   txt = '("FitTrack") fit not converged'
  return txt
def TParticlePrintOut(x):
  txt = '("TParticle") %s  P:%5.2FGeV/c VxZ:%5.2Fm'%(x.GetName(),x.P(),x.Vz()/u.m)
  return txt
def ShipParticlePrintOut(x):
  txt = '("ShipParticle") %s M:%5.2FGeV/c2 P:%5.2FGeV/c VxZ:%5.2Fm'%(x.GetName(),x.GetMass(),x.P(),x.Vz()/u.m)
  return txt
def ecalReconstructedPrintOut(cl):
  txt = '("EcalCluster") E:%5.2FGeV/c X:%5.2Fm Y:%5.2Fm'%(cl.RecoE(),cl.X()/u.m,cl.Y()/u.m)
  return txt
def ecalClusterPrintOut(cl):
  txt = '("EcalCluster") E:%5.2FGeV/c X:%5.2Fm Y:%5.2Fm'%(cl.Energy(),cl.X()/u.m,cl.Y()/u.m)
  return txt
def Dump(x):
  k=0
  for obj in x:
    print(k,obj.__repr__())
    k+=1

def TVector3PrintOut(x):
  txt = '%9.5F,%9.5F,%9.5F'%(x.X(),x.Y(),x.Z())
  return txt

def TLorentzVectorPrintOut(x):
  txt = '%9.5F,%9.5F,%9.5F,%9.5F,%9.5F'%(x.Px(),x.Py(),x.Pz(),x.E(),x.Mag())
  return txt

def TEvePointSetPrintOut(P):
 x, y, z = c_double(), c_double(), c_double()
 txt = ''
 if P.GetN()==0: txt = '<ROOT.TEvePointSet object>'
 for n in range(P.GetN()):
  rc = P.GetPoint(n,x,y,z)
  txt += f'{n:6d} {x.value:7.1f}, {y.value:7.1f}, {z.value:9.1f} x, y, z cm\n'

 return txt


ROOT.FairMCPoint.__repr__ = MCPointPrintOut
ROOT.ShipMCTrack.__repr__ = MCTrackPrintOut
ROOT.genfit.Track.__repr__ = FitTrackPrintOut
ROOT.TClonesArray.Dump = Dump
ROOT.TVector3.__repr__ = TVector3PrintOut
ROOT.TParticle.__repr__ = TParticlePrintOut
ROOT.ShipParticle.__repr__ = ShipParticlePrintOut
ROOT.ecalReconstructed.__repr__ = ecalReconstructedPrintOut
ROOT.ecalCluster.__repr__ = ecalClusterPrintOut
ROOT.TEvePointSet.__repr__ = TEvePointSetPrintOut
ROOT.vetoHit.__repr__ = vetoHitPrintOut
ROOT.muonHit.__repr__ = muonHitPrintOut
ROOT.TimeDetHit.__repr__ = TimeDetHitPrintOut
ROOT.TLorentzVector.__repr__ = TLorentzVectorPrintOut
