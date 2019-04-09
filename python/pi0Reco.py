import ROOT,os
import shipunit as u
import rootUtils as ut
pdg = ROOT.TDatabasePDG.Instance()
mPi0 = pdg.GetParticle(111).Mass()
L = ROOT.TLorentzVector()
V = ROOT.TVector3()
top = ROOT.gGeoManager.GetTopVolume()
z_ecal = top.GetNode('Ecal_1').GetMatrix().GetTranslation()[2]


def findPi0(sTree,secVertex):
 recoGammas = {}
 pi0List = []
 listOfGammas = None
 for aClu in  sTree.EcalReconstructed:
# short cut to exclude ecal clusters of charged tracks
# would need another routine to extrapolate tracks to ecal and exclude matched showers
  mc = aClu.MCTrack()
  if mc<0: continue
  gamma = sTree.MCTrack[mc]
  if gamma.GetPdgCode()!=22: continue
  if gamma.GetMotherId()<0: continue
  P = aClu.RecoE()
  direction = ROOT.TVector3(aClu.X()-secVertex.X(),aClu.Y()-secVertex.Y(),z_ecal-secVertex.Z())
  norm = direction.Mag()
  recoGammas[gamma] = ROOT.TLorentzVector(direction.X()/norm*P,direction.Y()/norm*P,direction.Z()/norm*P,P)
  sTree.MCTrack[mc].GetStartVertex(V)
 if len(recoGammas)==0: return []
 listOfGammas=recoGammas.values()
 for g1 in range(len(listOfGammas)-1):
  for g2 in range(g1+1,len(listOfGammas)):
    pi0 = listOfGammas[g1] + listOfGammas[g2]
    pi0List.append(pi0)
 return pi0List
