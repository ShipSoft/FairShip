import ROOT,os
import rootUtils as ut
h={}
from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-r", "--runNumber", dest="runNumber", help="run number", type=int,required=True)
parser.add_argument("-g", "--geoFile", dest="geoFile", help="geofile", required=True)
options = parser.parse_args()

fgeo = ROOT.TFile.Open(options.geoFile)
from ShipGeoConfig import ConfigRegistry
from rootpyPickler import Unpickler
#load geo dictionary
upkl    = Unpickler(fgeo)
snd_geo = upkl.load('ShipGeo')
# -----Create geometry----------------------------------------------
import shipLHC_conf as sndDet_conf
run = ROOT.FairRunSim()
modules = sndDet_conf.configure(run,snd_geo)
sGeo = fgeo.FAIRGeom
modules['Scifi'].SiPMmapping()

f=ROOT.TFile('sndsw_raw_'+str(options.runNumber).zfill(6)+'.root')

def slopes(Nev=-1):
    A,B = ROOT.TVector3(),ROOT.TVector3()
    ut.bookHist(h,'slopesX','slope diffs',1000,-1.0,1.0)
    ut.bookHist(h,'slopesY','slope diffs',1000,-1.0,1.0)
# assuming cosmics make straight line
    if Nev < 0 : Nev = f.rawConv.GetEntries()
    for sTree in f.rawConv:
        if Nev<0: break
        Nev=Nev-1
        clusters = []
        hitDict = {}
        for k in range(sTree.Digi_ScifiHits.GetEntries()):
            d = sTree.Digi_ScifiHits[k]
            if not d.isValid(): continue 
            hitDict[d.GetDetectorID()] = k
        hitList = list(hitDict.keys())
        if len(hitList)>0:
              hitList.sort()
              tmp = [ hitList[0] ]
              cprev = hitList[0]
              ncl = 0
              last = len(hitList)-1
              hitlist = ROOT.std.vector("sndScifiHit*")()
              for i in range(len(hitList)):
                   if i==0 and len(hitList)>1: continue
                   c=hitList[i]
                   if (c-cprev)==1: 
                        tmp.append(c)
                   if (c-cprev)!=1 or c==hitList[last]:
                        first = tmp[0]
                        N = len(tmp)
                        hitlist.clear()
                        for aHit in tmp: hitlist.push_back( sTree.Digi_ScifiHits[hitDict[aHit]])
                        aCluster = ROOT.sndCluster(first,N,hitlist)
                        clusters.append(aCluster)
                        if c!=hitList[last]:
                             ncl+=1
                             tmp = [c]
                   cprev = c
        xHits = {}
        yHits = {}
        for s in range(5):
             xHits[s]=[]
             yHits[s]=[]
        for aCl in clusters:
             aCl.GetPosition(A,B)
             vertical = int(aCl.GetFirst()/100000)%10==1
             s = int(aCl.GetFirst()/1000000)-1
             if vertical: xHits[s].append(ROOT.TVector3(A))
             else: yHits[s].append(ROOT.TVector3(A))
        proj = {'X':xHits,'Y':yHits}
        for p in proj:
          sls = []
          for  s1 in range(0,5):
             if len(proj[p][s1]) !=1: continue
             cl1 = proj[p][s1][0]
             for s2 in range(s1+1,5):
                if len(proj[p][s2]) !=1: continue
                cl2 = proj[p][s2][0]
                dz = abs(cl1[2]-cl2[2])
                if dz < 5: continue
                dzRep = 1./dz
                m =  dzRep*(cl2-cl1)
                sls.append( m )
          for ix1 in range(0,len(sls)-1):
             for ix2 in range(ix1+1,len(sls)):
                if p=="X": rc = h['slopes'+p].Fill( sls[ix2][0]-sls[ix1][0])
                if p=="Y": rc = h['slopes'+p].Fill( sls[ix2][1]-sls[ix1][1])


def hitMaps(Nev=-1):
 for mat in range(30):
    ut.bookHist(h,'mat_'+str(mat),'hit map / mat',512,-0.5,511.5)
    ut.bookHist(h,'sig_'+str(mat),'signal / mat',150,0.0,150.)
 N=-1
 if Nev < 0 : Nev = f.rawConv.GetEntries()
 for sTree in f.rawConv:
    N+=1
    if N>Nev: break
    for aHit in sTree.Digi_ScifiHits:
        X =  xPos(aHit.GetDetectorID())
        rc = h['mat_'+str(X[0]*3+X[1])].Fill(X[2])
        rc  = h['sig_'+str(X[0]*3+X[1])].Fill(aHit.GetSignal(0))
 ut.bookCanvas(h,'hitmaps',' ',1024,768,6,5)
 ut.bookCanvas(h,'signal',' ',1024,768,6,5)
 for mat in range(30):
    tc = h['hitmaps'].cd(mat+1)
    A = h['mat_'+str(mat)].GetSumOfWeights()/512.
    if h['mat_'+str(mat)].GetMaximum()>10*A: h['mat_'+str(mat)].SetMaximum(10*A)
    h['mat_'+str(mat)].Draw()
    tc = h['signal'].cd(mat+1)
    h['sig_'+str(mat)].Draw()
def eventTime():
 Tprev = -1
 ut.bookHist(h,'Etime','delta event time',100,0.0,1.)
 ut.bookCanvas(h,'E',' ',1024,768,1,1)
 for sTree in f.rawConv:
    T = sTree.EventHeader.GetEventTime()
    dT = 0
    if Tprev >0: dT = T-Tprev
    Tprev = T
    rc = h['Etime'].Fill(dT/160.E6)
 tc = h['E'].cd()
 rc = h['Etime'].Fit('expo')
 stats = h['Etime'].FindObject("stats")
 stats.SetOptFit(111)



