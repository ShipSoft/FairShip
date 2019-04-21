import ROOT

RPCPositionsBotTop = {}

vbot = ROOT.TVector3()
vtop = ROOT.TVector3()

def correctAlignmentRPC(hit,v):
 hit.EndPoints(vtop,vbot)
 #if not sTree.GetBranch('MuonTaggerPoint'):
 if v==1:
   vbot[0] = -vbot[0] -1.21
   vtop[0] = -vtop[0] -1.21
 else:
   vbot[1] = vbot[1] -1.21
   vtop[1] = vtop[1] -1.21
 return vbot,vtop

def RPCPosition():
 for s in range(1,6):
  for v in range(2):
   for c in range(1,185):
    if v==0 and c>116: continue
    detID = s*10000+v*1000+c
    hit = ROOT.MuonTaggerHit(detID,0)
    a,b = correctAlignmentRPC(hit,v)
    RPCPositionsBotTop[detID] = [a.Clone(),b.Clone()]
    x = (a[0]+b[0])/2.
    y = (a[1]+b[1])/2.
    z = (a[2]+b[2])/2.
    #muflux_Reco.setRPCPositions(detID,x,y,z)

def GetRPCPosition(s,v,c):
    detID = s*10000+v*1000+c
    return RPCPositionsBotTop[detID]