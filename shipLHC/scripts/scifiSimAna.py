import ROOT
import rootUtils as ut
import shipunit as u
from array import array
debug = False
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
nav = sGeo.GetCurrentNavigator()
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
ut.bookHist(h,'Edigi','digitized signal',100,0.0,150.)
ut.bookHist(h,'clusterSize','cluster size',20,-0.5,19.5)
ut.bookHist(h,'clusterSize_muon','cluster size',20,-0.5,19.5)
ut.bookHist(h,'doca','closest distance;[micron]',100,-500.,500.)
ut.bookHist(h,'doca_muon','closest distance; [micron] ',100,-500.,500.)
ut.bookHist(h,'docaCl','closest distance;[micron]',100,-500.,500.)
ut.bookHist(h,'docaCl_muon','closest distance; [micron] ',100,-200.,200.)
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
def docaLine(a,b,c,d):
   u = b-a
   v = d-c
   n = u.Cross(v)
   ac = a-c
   if n.Mag()==0:
       dist = ROOT.TMath.Sqrt(ac.Mag2()+3*(ac.Dot(u))**2/u.Mag2())
   else:
       dist = n.Dot(ac)/n.Mag()
   return dist
   

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

   hitDict = {}
   for k in range(sTree.Digi_ScifiHits.GetEntries()):
      d = sTree.Digi_ScifiHits[k]
      if not d.isValid(): continue 
      rc = h['Edigi'].Fill(d.GetEnergy())
      hitDict[d.GetDetectorID()] = k
   L = sTree.Digi_ScifiHits2MCPoints[0]
   for cl in sTree.Cluster_Scifi:
        isMuon = True
        meanImpact = ROOT.TVector3(0,0,0)
        nPoints = 0
        first = cl.GetFirst()
        cl_size = cl.GetN()
        for c in range(first,cl_size+first):
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
        rc = h['clusterSize'].Fill(cl_size)
        if isMuon: rc = h['clusterSize_muon'].Fill(cl_size)
        # goto local coordinates in detector plane
        vertical = int(first/100000)%10 == 1
        cl.GetPosition(A,B)
        locCluster = scifi.GetLocalPos(first,A)
        locPart       = scifi.GetLocalPos(first,meanImpact)

        if vertical: delta = locCluster[0]-locPart[0]
        else:           delta = locCluster[1]-locPart[1]
        rc = h['docaCl'].Fill(delta/u.um)
        if isMuon:     rc = h['docaCl_muon'].Fill(delta/u.um)

        for aHit in range(first,cl_size+first):
                scifi.GetSiPMPosition(aHit, A, B)
                loc = scifi.GetLocalPos(aHit,A)
                if vertical: delta = loc[0]-locPart[0]
                else: delta = loc[1]-locPart[1]
                rc = h['doca'].Fill(delta/u.um)
                if isMuon:
                     rc = h['doca_muon'].Fill(delta/u.um)


# test position
import SciFiMapping
from array import array
loc = array('d',[0,0,0])
glob = array('d',[0,0,0])

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

