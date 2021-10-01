import ROOT
import rootUtils as ut
import shipunit as u
from array import array

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-f", "--inputFile", dest="inputFile", help="single input file", required=False, default="sndLHC.Ntuple-TGeant4_dig.root")
parser.add_argument("-g", "--geoFile", dest="geoFile", help="geofile", required=False, default="geofile_full.Ntuple-TGeant4.root")
parser.add_argument("-n", "--nEvents", dest="nEvents", help="number of events to process", default=100000)
parser.add_argument("-d", "--Debug", dest="debug", help="debug", default=False)
parser.add_argument("-s", "--start", dest="start", type=int,help="file name with $*$", required=False,default=False)
parser.add_argument("-e", "--end", dest="end", type=int,help="file name with $*$", required=False,default=False)

options = parser.parse_args()
debug = options.debug
h={}

fgeo = ROOT.TFile.Open(options.geoFile)
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
ut.bookHist(h,'E','dE',100,0.0,300.)
ut.bookHist(h,'Edigi_all','digitized signal',150,0.0,150.)
ut.bookHist(h,'Edigi','digitized valid signal',150,0.0,150.)
ut.bookHist(h,'Edigi_muon','digitized valid signal',150,0.0,150.)
ut.bookHist(h,'Ecluster','cluster energy',150,0.0,150.)
ut.bookHist(h,'clusterSize','cluster size',20,-0.5,19.5)
ut.bookHist(h,'clusterSize_muon','cluster size',20,-0.5,19.5)
ut.bookHist(h,'doca','closest distance;[micron]',100,-500.,500.)
ut.bookHist(h,'doca_muon','closest distance; [micron] ',100,-500.,500.)
ut.bookHist(h,'docaCl','closest distance;[micron]',100,-500.,500.)
ut.bookHist(h,'docaCl_muon','closest distance; [micron] ',100,-500.,500.)
ut.bookHist(h,'pangle','angle of particle entering;mrad',100,-10.,10.)
ut.bookHist(h,'pangle_muon','angle of particle entering;mrad',100,-10.,10.)

ut.bookHist(h,'pdoca_muon','closest distance',100,0.0,0.02)
ut.bookHist(h,'pdx_muon','closest distance',100,-0.02,0.02)

ut.bookHist(h,'nMCpoints','hits per event',5000,-0.5,4999.5)
ut.bookHist(h,'nDigihits','hits per event',5000,-0.5,4999.5)
ut.bookHist(h,'nDigihits_muon','hits per event directly from muon',100,-0.5,99.5)
ut.bookHist(h,'in_muon','p of incoming muon in Scifi',1000,0.0,2000.)

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

tchain = ROOT.TChain("cbmsim")
if options.inputFile.find("XXX")<0:
     tchain.Add(options.inputFile)
else:
    for i in range(options.start,options.end+1):
       aFile = options.inputFile.replace("XXX",str(i))
       tchain.Add(aFile)

for x in h: h[x].Reset()
for sTree in tchain:
   L = sTree.Digi_ScifiHits2MCPoints[0]
   w = sTree.MCTrack[0].GetWeight() # assume these are muon background events.
                                                                             # to be multiplied with normalization[1] = 5.83388*137.13/78.   = 10.26 to get rates in second.
   rc = h['nMCpoints'].Fill(sTree.ScifiPoint.GetEntries(),w)
   rc = h['nDigihits'].Fill(sTree.Digi_ScifiHits.GetEntries(),w)
#
   first = True
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
          if first:
               first = False
               P = ROOT.TVector3(p.GetPx(),p.GetPy(),p.GetPz())
               rc = h['in_muon'].Fill(P.Mag(),w)
#
   hitDict = {}
   for k in range(sTree.Digi_ScifiHits.GetEntries()):
      d = sTree.Digi_ScifiHits[k]
      rc = h['Edigi_all'].Fill(d.GetEnergy())
      if not d.isValid(): continue 
      rc = h['Edigi'].Fill(d.GetEnergy())
      hitDict[d.GetDetectorID()] = k
   NmuonHit = 0
   for cl in sTree.Cluster_Scifi:
        rc = h['Ecluster'].Fill(cl.GetEnergy())
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
        if isMuon:
             NmuonHit +=1
             rc = h['clusterSize_muon'].Fill(cl_size)
             for hitID in range(first,first+cl_size):
                 d = sTree.Digi_ScifiHits[hitDict[hitID]]
                 r = h['Edigi_muon'].Fill(d.GetEnergy())
        # goto local coordinates in detector plane
        vertical = int(first/100000)%10 == 1
        cl.GetPosition(A,B)
        locCluster = scifi.GetLocalPos(first,A)
        locPart       = scifi.GetLocalPos(first,meanImpact)
#
        if vertical: delta = locCluster[0]-locPart[0]
        else:           delta = locCluster[1]-locPart[1]
        rc = h['docaCl'].Fill(delta/u.um)
        if isMuon:     
               rc = h['docaCl_muon'].Fill(delta/u.um)
               if debug:
                   print('delta ',delta/u.um,cl_size)
                   locPart.Print()
                   locCluster.Print()
#
        docaMax = 0
        for aHit in range(first,cl_size+first):
                scifi.GetSiPMPosition(aHit, A, B)
                loc = scifi.GetLocalPos(aHit,A)
                if vertical: delta = loc[0]-locPart[0]
                else: delta = loc[1]-locPart[1]
                rc = h['doca'].Fill(delta/u.um)
                if isMuon:
                     rc = h['doca_muon'].Fill(delta/u.um)
                     if debug:
                         print('------------ ',aHit,delta/u.um)
                         loc.Print()
                         if abs(delta/u.um) > docaMax: docaMax = abs(delta/u.um)
        if debug:
           print(docaMax)
           if docaMax>300: 1/0
   rc = h['nDigihits_muon'].Fill(NmuonHit,w)

# test position
import SciFiMapping
from array import array
loc = array('d',[0,0,0])
glob = array('d',[0,0,0])

def testPosition()
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

from array import array
class Tracking(ROOT.FairTask):
 " Tracking "
 def InitTask(self,event):
   geoMat =  ROOT.genfit.TGeoMaterialInterface()
   bfield     = ROOT.genfit.ConstField(0,0,0)   # constant field of zero
   fM = ROOT.genfit.FieldManager.getInstance()
   fM.init(bfield)
   ROOT.genfit.MaterialEffects.getInstance().init(geoMat)
   ROOT.genfit.MaterialEffects.getInstance().setNoEffects()
   self.fitter = ROOT.genfit.KalmanFitter()
   self.fitter.setMaxIterations(50)
   self.sigma_spatial = 100.*u.mu
   self.Debug = True
   self.event = event

 def FinishEvent(self):
  pass

 def ExecuteTask(self,option=''):
    self.clusters = self.scifiCluster()
    self.trackCandidates = self.patternReco()
    self.event.fittedTracks = []
    for aTrack in self.trackCandidates:
           rc = self.fitTrack(aTrack)
           if type(rc)==type(1):
                print('trackfit failed',rc,aTrack)
           else:
                self.event.fittedTracks.append(aTrack)

 def scifiCluster(self):
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
       return clusters

 def patternReco():
# very simple for the moment, take all scifi clusters
    trackCandidates = []
    hitlist = {}
    for cl in self.clusters:
           hitlist.append(cl)
    trackCandidates.append(hitlist)
    return trackCandidates

 def fitTrack(hitlist):
# hitlist:  clusterID: [A,B] endpoints of scifiCluster
    hitPosLists={}
    trID = 0

    posM    = ROOT.TVector3(0, 0, 0.)
    momM = ROOT.TVector3(0,0,100.)  # default track with high momentum

# approximate covariance
    covM = ROOT.TMatrixDSym(6)
    res = self.sigma_spatial
    for  i in range(3):   covM[i][i] = res*res
    for  i in range(3,6): covM[i][i] = ROOT.TMath.Power(res / (4.*2.) / ROOT.TMath.Sqrt(3), 2)
    rep = ROOT.genfit.RKTrackRep(13)

# start state
    state = ROOT.genfit.MeasuredStateOnPlane(rep)
    rep.setPosMomCov(state, posM, momM, covM)

# create track
    seedState = ROOT.TVectorD(6)
    seedCov   = ROOT.TMatrixDSym(6)
    rep.get6DStateCov(state, seedState, seedCov)
    theTrack = ROOT.genfit.Track(rep, seedState, seedCov)

# make measurements sorted in z
    unSortedList = {}
    tmpList = {}
    A,B = ROOT.TVector3(),ROOT.TVector3()
    for k in range(hitlist):
        aCl = hitlist[k]
        detID = aHit.GetDetectorID()
        aCl.GetPosition(A,B)
        distance = 0
        tmp = array('d',[A[0],A[1],A[2],B[0],B[1],B[2],distance])
        unSortedList[A[2]] = [ROOT.TVectorD(7,tmp),detID,k]
    sorted_z=list(unSortedList.keys())
    sorted_z.sort()
    for z in sorted_z:
        tp = ROOT.genfit.TrackPoint() # note how the point is told which track it belongs to
        hitCov = ROOT.TMatrixDSym(7)
        hitCov[6][6] = resolution*resolution
        measurement = ROOT.genfit.WireMeasurement(unSortedList[z][0],hitCov,1,6,tp) # the measurement is told which trackpoint it belongs to
        measurement.setMaxDistance(0.1)
        measurement.setDetId(unSortedList[z][1])
        measurement.setHitId(unSortedList[z][2])
        tp.addRawMeasurement(measurement) # package measurement in the TrackPoint                                          
        theTrack.insertPoint(tp)  # add point to Track
    if not theTrack.checkConsistency():
        print("track not consistent")
        theTrack.Delete()
        return -2
# do the fit
    self.fitter.processTrack(theTrack) # processTrackWithRep(theTrack,rep,True)
    fitStatus   = theTrack.getFitStatus()
    if self.Debug: print("Fit result: converged chi2 Ndf",fitStatus.isFitConverged(),fitStatus.getChi2(),fitStatus.getNdf())
    if not fitStatus.isFitConverged():
        theTrack.Delete()
        return -1
    if self.Debug: 
        chi2 = fitStatus.getChi2()/fitStatus.getNdf()
        fittedState = theTrack.getFittedState()
        P = fittedState.getMomMag()
        print("track fitted Ndf #Meas P",fitStatus.getNdf(), theTrack.getNumPointsWithMeasurement(),P)
        for p in theTrack.getPointsWithMeasurement():
            rawM = p.getRawMeasurement()
            info = p.getFitterInfo()
            if not info: continue
            detID = rawM.getDetId()
            print(detID,"weights",info.getWeights()[0],info.getWeights()[1],fitStatus.getNdf())
    return theTrack


