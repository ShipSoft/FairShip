import ROOT,os
import shipunit as u
import rootUtils as ut
pdg = ROOT.TDatabasePDG.Instance()
mPi0 = pdg.GetParticle(111).Mass()
L = ROOT.TLorentzVector()
V = ROOT.TVector3()
top = ROOT.gGeoManager.GetTopVolume()


def findPi0(sTree,secVertex):
 recoGammas = {}
 pi0List = []
 listOfGammas = None
 for aClu in  sTree.EcalReconstructed:
  mc = aClu.MCTrack()
  if mc<0: continue
  gamma = sTree.MCTrack[mc]
  if gamma.GetPdgCode()!=22: continue
  if gamma.GetMotherId()<0: continue
  P = aClu.RecoE()
  norm = direction.Mag()
  recoGammas[gamma] = ROOT.TLorentzVector(direction.X()/norm*P,direction.Y()/norm*P,direction.Z()/norm*P,P)
  sTree.MCTrack[mc].GetStartVertex(V)
 if len(recoGammas)==0: return []
 listOfGammas=list(recoGammas.values())
 for g1 in range(len(listOfGammas)-1):
  for g2 in range(g1+1,len(listOfGammas)):
    pi0 = listOfGammas[g1] + listOfGammas[g2]
    pi0List.append(pi0)
 return pi0List
