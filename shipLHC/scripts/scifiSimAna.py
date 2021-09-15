import ROOT
import rootUtils as ut
h={}

geoFile = "geofile_full.Ntuple-TGeant4.root"
fgeo = ROOT.TFile.Open(geoFile)
from ShipGeoConfig import ConfigRegistry
from rootpyPickler import Unpickler
#load geo dictionary
upkl    = Unpickler(fgeo)
snd_geo = upkl.load('ShipGeo')
 
# -----Create geometry----------------------------------------------
import shipLHC_conf as sndDet_conf

run = ROOT.FairRunSim()
run.SetName("TGeant4")  # Transport engine
run.SetOutputFile(ROOT.TMemFile('output', 'recreate'))  # Output file
run.SetUserConfig("g4Config_basic.C") # geant4 transport not used
rtdb = run.GetRuntimeDb()
modules = sndDet_conf.configure(run,snd_geo)
sGeo = fgeo.FAIRGeom
top = sGeo.GetTopVolume()
scifi = modules['Scifi']
scifi.SiPMmapping()

ut.bookHist(h,'S','stations',7,-0.5,6.5)
ut.bookHist(h,'O','orientation',7,-0.5,6.5)
ut.bookHist(h,'M','mat',7,-0.5,6.5)
ut.bookHist(h,'R','row',7,-0.5,6.5)
ut.bookHist(h,'N','fibre',1000,-0.5,999.5)

for s in range(1,6):
    ut.bookHist(h,'Sxy'+str(s),'XY',50,-50.,0.,50,10.,60.)
    for o in range(2):
      for m in range(1,4):
          for r in range(1,7):
               ut.bookHist(h,'N'+str(s)+str(o)+str(m)+str(r),'fibre',1000,-0.5,999.5)
ut.bookHist(h,'E','dE',100,0.0,1000.)
ut.bookHist(h,'Edigi','digitized signal',100,0.0,1.E-2)
ut.bookHist(h,'clusterSize','cluster size',20,-0.5,19.5)
ut.bookHist(h,'clusterSize_muon','cluster size',20,-0.5,19.5)
ut.bookHist(h,'doca','closest distance',100,0.0,0.2)
ut.bookHist(h,'doca_muon','closest distance',100,0.0,0.05)
ut.bookHist(h,'dx_muon','closest distance;[mu]',100,-250.,250.)
ut.bookHist(h,'pangle','angle of particle entering;mrad',100,-10.,10.)
ut.bookHist(h,'pangle_muon','angle of particle entering;mrad',100,-10.,10.)

ut.bookHist(h,'pdoca_muon','closest distance',100,0.0,0.02)
ut.bookHist(h,'pdx_muon','closest distance',100,-0.02,0.02)

ut.bookHist(h,'nhits','hits per event',100,0.0,1000.)

def siPMPosCPP(scifi):
    P=scifi.GetSiPMPos()
    Pos = {}
    for x in P:
         Pos[x.first]=x.second
    return Pos

def docaLinePoint(A,B,p):
   n = B-A
   tmp = (A-p).Cross(n)
   return tmp.Mag()/n.Mag()

A=ROOT.TVector3()
B=ROOT.TVector3()

f = ROOT.TFile.Open("sndLHC.Ntuple-TGeant4_dig.root")
for x in h: h[x].Reset()
for sTree in f.cbmsim:
   rc = h['nhits'].Fill(sTree.ScifiPoint.GetEntries())
   w = sTree.MCTrack[0].GetWeight() # assume these are muon background events.
   for p in sTree.ScifiPoint:
      if p.GetDetectorID()==0: 
            print('?')
            continue
      rc = h['S'].Fill(p.station(),w)
      rc = h['O'].Fill(p.orientation(),w)
      rc = h['M'].Fill(p.mat(),w)
      rc = h['R'].Fill(p.row(),w)
      rc = h['N'].Fill(p.fibreN(),w)
      rc = h['Sxy'+str(p.station())].Fill(p.GetX(),p.GetY(),w)
      rc = h['N'+str(p.GetDetectorID()//1000)].Fill(p.fibreN(),w)
      rc = h['E'].Fill(p.GetEnergyLoss()*1E6,w)
      if p.GetTrackID()==0:  # incoming muon
          scifi.GetPosition(p.GetDetectorID(),A,B)
          impactPoint = ROOT.TVector3(p.GetX(),p.GetY(),p.GetZ())
          D = docaLinePoint(A,B,impactPoint)
          rc = h['pdoca_muon'].Fill(D)
          if p.orientation()==1:
              rc = h['pdx_muon'].Fill(A[0]-impactPoint[0])
          else:
              rc = h['pdx_muon'].Fill(A[1]-impactPoint[1])

   hitMap = {}
   for d in sTree.Digi_ScifiHits:
      rc = h['Edigi'].Fill(d.GetEnergy())
      hitMap[d.GetDetectorID()]=d
   hitList = list(hitMap.keys())
   if len(hitList)<1: continue
   hitList.sort()
   L = sTree.Digi_ScifiHits2MCPoints[0]
   clusters = {0:[ [hitList[0]],[] ]}
   cprev = hitList[0]
   ncl = 0
   last = len(hitList)-1
   for i in range(1,len(hitList)):
        c=hitList[i]
        if (c-cprev)==1: 
             clusters[ncl][0].append(c)
        if (c-cprev)!=1 or c==hitList[last]:
# make clusterCentre:
            weight = 0
            meanPosA=ROOT.TVector3(0,0,0)
            meanPosB=ROOT.TVector3(0,0,0)
            for aHit in clusters[ncl][0]:
                 scifi.GetSiPMPosition(aHit, A, B)
                 w = hitMap[aHit].GetEnergy()
                 weight+=w
                 meanPosA+=w*ROOT.TVector3(A)
                 meanPosB+=w*ROOT.TVector3(B)
            winv = 1./weight
            meanPosA=meanPosA*winv
            meanPosB=meanPosB*winv
            clusters[ncl][1].append(ROOT.TVector3(meanPosA))
            clusters[ncl][1].append(ROOT.TVector3(meanPosB))
            if c!=hitList[last]:
                ncl+=1
                clusters[ncl]=[[c],[]]
        cprev = c
   # if len(hitList)>50: 1/0
   for x in clusters:
        cl = clusters[x]
       # cl[0]: list of hits, cl[1]:A,B
        isMuon = True
        meanImpact = ROOT.TVector3(0,0,0)
        nPoints = 0
        for c in cl[0]:
        # origin of digis:
            points = L.wList(c)
            for p in points:
                scifiPoint = sTree.ScifiPoint[p[0]]
                trackKey = scifiPoint.GetTrackID()
                pid = -1
                if not trackKey<0: pid = sTree.MCTrack[trackKey].GetPdgCode()
                rc = h['pangle'].Fill(ROOT.TMath.ATan2(scifiPoint.GetPx(),scifiPoint.GetPz())*1000)
                if abs(pid)==13:  rc = h['pangle_muon'].Fill(ROOT.TMath.ATan2(scifiPoint.GetPx(),scifiPoint.GetPz())*1000)
                if abs(pid)!=13: isMuon = False
                meanImpact+=ROOT.TVector3(scifiPoint.GetX(),scifiPoint.GetY(),scifiPoint.GetZ())
                nPoints+=1
        w = 1./nPoints
        meanImpact=meanImpact*w
        cl_size = len(cl[0])
        rc = h['clusterSize'].Fill(cl_size)
        if isMuon: rc = h['clusterSize_muon'].Fill(cl_size)
        D = docaLinePoint(cl[1][0],cl[1][1],meanImpact)
        aHit =   cl[0][0]
        meanPosA = cl[1][0]
        meanPosB = cl[1][1]
        if hitMap[aHit].isVertical(): dx = meanPosA[0]-meanImpact[0]
        else: dx =  meanPosA[1]-meanImpact[1]
        rc = h['doca'].Fill(D)
        if isMuon:
            rc = h['doca_muon'].Fill(D)
            rc = h['dx_muon'].Fill(dx*10000.)
            if  len(cl[0])<3:
                 print(cl[0],D,dx,scifiPoint.GetDetectorID(),hitMap[aHit].isVertical())
                 meanImpact.Print(),scifi.GetPosition(scifiPoint.GetDetectorID(),A,B)
                 meanPosA.Print()
                 meanPosB.Print()
                 A.Print()
                 B.Print()

# test position
import SciFiMapping
from array import array
loc = array('d',[0,0,0])
glob = array('d',[0,0,0])
nav = sGeo.GetCurrentNavigator()
F = SciFiMapping.getFibre2SiPMCPP(modules)
Finv = SciFiMapping.getSiPM2FibreCPP(modules)
print("================================================")
scifi.GetPosition(1011001,A,B)
print("horizontal mat")
A.Print()
B.Print()
print("vertical mat")
scifi.GetPosition(1111001,A,B)
A.Print()
B.Print()

