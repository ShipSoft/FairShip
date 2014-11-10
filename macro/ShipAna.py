# example for accessing smeared hits and fitted tracks
import ROOT,os,sys,getopt
import rootUtils as ut
import shipunit as u
from ShipGeoConfig import ConfigRegistry

PDG = ROOT.TDatabasePDG.Instance()
inputFile = 'ship.Pythia8-TGeant4_rec.root'

try:
        opts, args = getopt.getopt(sys.argv[1:], "f:A", [])
except getopt.GetoptError:
        # print help information and exit:
        print ' enter file name'
        sys.exit()
for o, a in opts:
        print o, a
        if o in ("-f"):
            inputFile = a
f     = ROOT.TFile(inputFile)
sTree = f.cbmsim

# init geometry and mag. field
ShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py",strawDesign=4,muShieldDesign=5,targetOpt=5)
# -----Create geometry----------------------------------------------
import shipDet_conf
run = ROOT.FairRunSim()
modules = shipDet_conf.configure(run,ShipGeo)

tgeom = ROOT.TGeoManager("Geometry", "Geane geometry")
geofile = inputFile.replace('ship.','geofile_full.').replace('_rec.','.')
gMan  = tgeom.Import(geofile)
geoMat =  ROOT.genfit.TGeoMaterialInterface()
ROOT.genfit.MaterialEffects.getInstance().init(geoMat)

bfield = ROOT.genfit.BellField(ShipGeo.Bfield.max, ShipGeo.Bfield.z,2)
fM = ROOT.genfit.FieldManager.getInstance()
fM.init(bfield)

ev     = ut.PyListOfLeaves()
leaves = sTree.GetListOfLeaves()
names  = ut.setAttributes(ev, leaves)

h = {}
ut.bookHist(h,'delPOverP','delP / P',100,0.,50.,100,-0.2,0.2)
ut.bookHist(h,'delPOverP2','delP / P chi2<25',100,0.,50.,100,-0.2,0.2)
ut.bookHist(h,'chi2','chi2 after trackfit',100,0.,1000.)
ut.bookHist(h,'IP','Impact Parameter',100,0.,10.)
ut.bookHist(h,'Doca','Doca between two tracks',100,0.,10.)
ut.bookHist(h,'IP0','Impact Parameter to target',100,0.,100.)
ut.bookHist(h,'IP0/mass','Impact Parameter to target vs mass',100,0.,2.,100,0.,100.)
ut.bookHist(h,'HNL','reconstructed Mass',100,0.,2.)
ut.bookHist(h,'meas','number of measurements',25,-0.5,24.5)
ut.bookHist(h,'distu','distance to wire',100,0.,1.)
ut.bookHist(h,'distv','distance to wire',100,0.,1.)
ut.bookHist(h,'disty','distance to wire',100,0.,1.)

def makePlots():
   ut.bookCanvas(h,key='strawanalysis',title='Distance to wire',nx=800,ny=600,cx=1,cy=1)
   cv = h['strawanalysis'].cd(1)
   h['disty'].Draw()
   h['distu'].Draw('same')
   h['distv'].Draw('same')
   ut.bookCanvas(h,key='fitresults',title='Fit Results',nx=1600,ny=1200,cx=2,cy=2)
   cv = h['fitresults'].cd(1)
   h['delPOverP'].Draw('box')
   cv = h['fitresults'].cd(2)
   cv.SetLogy(1)
   h['chi2'].Draw()
   cv = h['fitresults'].cd(3)
   h['delPOverP_proj'] = h['delPOverP'].ProjectionY()
   ROOT.gStyle.SetOptFit(11111)
   h['delPOverP_proj'].Draw()
   h['delPOverP_proj'].Fit('gaus')
   cv = h['fitresults'].cd(4)
   h['delPOverP2_proj'] = h['delPOverP2'].ProjectionY()
   h['delPOverP2_proj'].Draw()
   h['delPOverP2_proj'].Fit('gaus')
   h['fitresults'].Print('fitresults.gif')
   ut.bookCanvas(h,key='fitresults2',title='Fit Results',nx=1600,ny=1200,cx=2,cy=2)
   print 'finished with first canvas'
   cv = h['fitresults2'].cd(1)
   h['Doca'].Draw()
   cv = h['fitresults2'].cd(2)
   h['IP0'].Draw()
   cv = h['fitresults2'].cd(3)
   h['HNL'].Draw()
   h['HNL'].Fit('gaus')
   cv = h['fitresults2'].cd(4)
   h['IP0/mass'].Draw('box')
   h['fitresults2'].Print('fitresults2.gif')
   print 'finished making plots'


def myVertex(t1,t2,PosDir):
 # closest distance between two tracks
   V=0
   for i in range(3):   V += PosDir[t1][1](i)*PosDir[t2][1](i)
   S1=0
   for i in range(3):   S1 += (PosDir[t1][0](i)-PosDir[t2][0](i))*PosDir[t1][1](i)
   S2=0
   for i in range(3):   S2 += (PosDir[t1][0](i)-PosDir[t2][0](i))*PosDir[t2][1](i)
   l = (S2-S1*V)/(1-V*V)
   x2 = PosDir[t2][0](0)+l*PosDir[t2][1](0)
   y2 = PosDir[t2][0](1)+l*PosDir[t2][1](1)
   z2 = PosDir[t2][0](2)+l*PosDir[t2][1](2)
   x1 = PosDir[t1][0](0)+l*PosDir[t1][1](0)
   y1 = PosDir[t1][0](1)+l*PosDir[t1][1](1)
   z1 = PosDir[t1][0](2)+l*PosDir[t1][1](2)
   dist = ROOT.TMath.Sqrt((x1-x2)**2+(y1-y2)**2+(z1-z2)**2)
   return (x1+x2)/2.,(y1+y2)/2.,(z1+z2)/2.,dist


# start event loop
def myEventLoop():
 nEvents = sTree.GetEntries()
 for n in range(nEvents):
  rc = sTree.GetEntry(n)
# make some straw hit analysis
  for ahit in sTree.strawtubesPoint:
     detID = ahit.GetDetectorID()
     top = ROOT.TVector3()
     bot = ROOT.TVector3()
     modules["Strawtubes"].StrawEndPoints(detID,bot,top)
   #distance to wire, and smear it.
     dw  = ahit.dist2Wire()
     if abs(top.y())==abs(bot.y()): h['disty'].Fill(dw)
     if abs(top.y())>abs(bot.y()): h['distu'].Fill(dw)
     if abs(top.y())<abs(bot.y()): h['distv'].Fill(dw)
#
  key = 0
  fittedTracks = {}
  for atrack in ev.FitTracks.GetObject():
   fitStatus   = atrack.getFitStatus()
   h['meas'].Fill(atrack.getNumPoints())
   if not fitStatus.isFitConverged() : continue
   fittedTracks[key] = atrack
# needs different study why fit has not converged, continue with fitted tracks
   chi2        = fitStatus.getChi2()
   fittedState = atrack.getFittedState()
   h['chi2'].Fill(chi2)
   P = fittedState.getMomMag()
   mcPartKey = sTree.fitTrack2MC[key]
   mcPart    = sTree.MCTrack[mcPartKey]
   if not mcPart : continue
   Ptruth    = mcPart.GetP()
   delPOverP = (Ptruth - P)/Ptruth
   h['delPOverP'].Fill(Ptruth,delPOverP)
   if chi2>30: continue
   h['delPOverP2'].Fill(Ptruth,delPOverP)
# try measure impact parameter
   trackDir = fittedState.getDir()
   trackPos = fittedState.getPos()
   vx = ROOT.TVector3()
   mcPart.GetStartVertex(vx)
   t = 0
   for i in range(3):   t += trackDir(i)*(vx(i)-trackPos(i)) 
   dist = 0
   for i in range(3):   dist += (vx(i)-trackPos(i)-t*trackDir(i))**2
   dist = ROOT.TMath.Sqrt(dist)
   h['IP'].Fill(dist) 
   key+= 1  
# ---
# go for 2-track combinations
  if len(fittedTracks) == 2:
     LV  = {}
     PosDir = {} 
     for tr in fittedTracks:
      xx  = fittedTracks[tr].getFittedState()
      PosDir[tr] = [xx.getPos(),xx.getDir()]
     keys = fittedTracks.keys()
     t1,t2 = keys[0],keys[1] 
     xv,yv,zv,doca = myVertex(t1,t2,PosDir)
     h['Doca'].Fill(dist)  
     HNLPos = ROOT.TVector3(xv,yv,zv)
     for tr in fittedTracks:
      xx  = fittedTracks[tr].getFittedState()
      # make a new rep
      rep = ROOT.genfit.RKTrackRep(xx.getPDG())
      pos = xx.getPos()
      mom = xx.getMom()
      state = ROOT.genfit.StateOnPlane(rep)
      rep.setPosMom(state, pos, mom)
      origPlane = state.getPlane()
      origState = ROOT.genfit.StateOnPlane(state)
      point = ROOT.TVector3(1.,5.,3.)
      try:
       rep.extrapolateToPoint(state, HNLPos, False)
      except:
        print 'extrap did not worked'
      LV[tr] = ROOT.TLorentzVector()
      mass = PDG.GetParticle(xx.getPDG()).Mass()
      mom = rep.getMom(state)  
      E = ROOT.TMath.Sqrt( mass*mass + mom.Mag2() )
      LV[tr].SetPxPyPzE(mom.x(),mom.y(),mom.z(),E)
     HNL = LV[t1]+LV[t2]
     tr = ROOT.TVector3(0,0,ShipGeo.target.z0)
     t = 0
     for i in range(3):   t += HNL(i)/HNL.P()*(tr(i)-HNLPos(i)) 
     dist = 0
     for i in range(3):   dist += (tr(i)-HNLPos(i)-t*HNL(i)/HNL.P())**2
     dist = ROOT.TMath.Sqrt(dist)
     h['IP0'].Fill(dist)  
     h['IP0/mass'].Fill(HNL.M(),dist)
     h['HNL'].Fill(HNL.M())


def access2SmearedHits():
 key = 0
 for ahit in ev.SmearedHits.GetObject():
   print ahit[0],ahit[1],ahit[2],ahit[3],ahit[4],ahit[5],ahit[6]
   # follow link to true MCHit
   mchit   = TrackingHits[key]
   mctrack =  MCTracks[mchit.GetTrackID()]
   print mchit.GetZ(),mctrack.GetP(),mctrack.GetPdgCode()
   key+=1

myEventLoop()
makePlots()
