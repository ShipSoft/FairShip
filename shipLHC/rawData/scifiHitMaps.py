import ROOT,os
import rootUtils as ut
h={}
from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-r", "--runNumber", dest="runNumber", help="run number", type=int,required=True)
parser.add_argument("-f", "--inputFile", dest="fname", help="file name for MC", type=str,default=None,required=False)
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

def xPos(detID):
        orientation = (detID//100000)%10
        nStation = 2*(detID//1000000-1)+orientation
        mat   = (detID%100000)//10000
        X = detID%1000+(detID%10000)//1000*128
        return [nStation,mat,X]   # even numbers are Y (horizontal plane), odd numbers X (vertical plane)

if options.runNumber>0: 
              f=ROOT.TFile.Open('sndsw_raw_'+str(options.runNumber).zfill(6)+'.root')
              eventTree = f.rawConv
else:
              f=ROOT.TFile.Open(options.fname)
              eventTree = f.cbmsim

def slopes(Nev=-1):
    A,B = ROOT.TVector3(),ROOT.TVector3()
    ut.bookHist(h,'slopesX','slope diffs',1000,-1.0,1.0)
    ut.bookHist(h,'slopesY','slope diffs',1000,-1.0,1.0)
    ut.bookHist(h,'clX','cluster size',10,0.5,10.5)
    ut.bookHist(h,'clY','cluster size',10,0.5,10.5)
# assuming cosmics make straight line
    if Nev < 0 : Nev = eventTree.GetEntries()
    for event in eventTree:
        if Nev<0: break
        Nev=Nev-1
        clusters = []
        hitDict = {}
        for k in range(event.Digi_ScifiHits.GetEntries()):
            d = event.Digi_ScifiHits[k]
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
                        for aHit in tmp: hitlist.push_back( event.Digi_ScifiHits[hitDict[aHit]])
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
             if vertical: 
                  xHits[s].append(ROOT.TVector3(A))
                  rc = h['clX'].Fill(aCl.GetN())
             else: 
                  yHits[s].append(ROOT.TVector3(A))
                  rc = h['clY'].Fill(aCl.GetN())
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
    ut.bookCanvas(h,'slopes',' ',1024,768,1,2)
    h['slopes'].cd(1)
    h['slopesX'].GetXaxis().SetRangeUser(-0.2,0.2)
    h['slopesX'].SetTitle('x projection; delta slope [rad]')
    h['slopesX'].Draw()
    h['slopesX'].Fit('gaus','S','',-0.02,0.02)
    h['slopes'].Update()
    stats = h['slopesX'].FindObject('stats')
    stats.SetOptFit(111)
    h['slopes'].cd(2)
    h['slopesY'].GetXaxis().SetRangeUser(-0.2,0.2)
    h['slopesY'].SetTitle('y projection; delta slope [rad]')
    h['slopesY'].Draw()
    h['slopesY'].Fit('gaus','S','',-0.02,0.02)
    h['slopes'].Update()
    stats = h['slopesY'].FindObject('stats')
    stats.SetOptFit(111)
    for event in eventTree:
        if Nev<0: break
        Nev=Nev-1
        clusters = []
        hitDict = {}
        for k in range(event.Digi_ScifiHits.GetEntries()):
            d = event.Digi_ScifiHits[k]
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
                        for aHit in tmp: hitlist.push_back( event.Digi_ScifiHits[hitDict[aHit]])
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
             if vertical: 
                  xHits[s].append(ROOT.TVector3(A))
                  rc = h['clX'].Fill(aCl.GetN())
             else: 
                  yHits[s].append(ROOT.TVector3(A))
                  rc = h['clY'].Fill(aCl.GetN())
        proj = {'X':xHits,'Y':yHits}
        for p in proj:
          sls = []
          for  s1 in range(0,5):
             if len(proj[p][s1]) !=1: continue
             cl1 = proj[p][s1][0]
             for s2 in range(s1+1,5):
                if len(proj[p][s2]) !=1: continue

def hitMaps(Nev=-1):
 for mat in range(30):
    ut.bookHist(h,'mat_'+str(mat),'hit map / mat',512,-0.5,511.5)
    ut.bookHist(h,'sig_'+str(mat),'signal / mat',150,0.0,150.)
 N=-1
 if Nev < 0 : Nev = eventTree.GetEntries()
 for event in eventTree:
    N+=1
    if N>Nev: break
    for aHit in event.Digi_ScifiHits:
        if not aHit.isValid(): continue
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
 for event in eventTree:
    T = event.EventHeader.GetEventTime()
    dT = 0
    if Tprev >0: dT = T-Tprev
    Tprev = T
    rc = h['Etime'].Fill(dT/160.E6)
 tc = h['E'].cd()
 rc = h['Etime'].Fit('expo')
 stats = h['Etime'].FindObject("stats")
 stats.SetOptFit(111)

def mergeSignals(hstore):
  ut.bookHist(hstore,'signalAll','signal all mat',150,0.0,150.)
  for mat in range(30):
    hstore['signalAll'].Add(hstore['sig_'+str(mat)])
  hstore['signalAll'].Scale(1./hstore['signalAll'].GetSumOfWeights())

def signalZoom(smax):
  for mat in range(30):
    h['sig_'+str(mat)].GetXaxis().SetRangeUser(0.,smax)
    tc = h['signal'].cd(mat+1)
    tc.Update()

def beamSpot():
    A,B = ROOT.TVector3(),ROOT.TVector3()
    ut.bookHist(h,'bs','beam spot',100,-100.,10.,100,0.,80.)
    for event in eventTree:
        xMean = 0
        yMean = 0
        w=0
        for d in event.Digi_ScifiHits:
            detID = d.GetDetectorID()
            s = int(detID/1000000)
            modules['Scifi'].GetSiPMPosition(detID,A,B)
            vertical = int(detID/100000)%10==1
            if vertical: xMean+=A[0]
            else: yMean+=A[1]
            w+=1
        rc = h['bs'].Fill(xMean/w,yMean/w)



            
