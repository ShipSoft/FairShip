#!/usr/bin/env python -i
import ROOT,sys,getopt,os,Tkinter
from ShipGeoConfig import ConfigRegistry
from rootpyPickler import Unpickler
import shipunit as u
from decorators import *
import shipRoot_conf
shipRoot_conf.configure()

fMan = None
fRun = None
pdg  = ROOT.TDatabasePDG.Instance()
g    = ROOT.gROOT 

ParFile    = None
geoFile    = None
#-----User Settings:-----------------------------------------------
mcEngine  = "TGeant4"
simEngine = "Pythia8"
InputFile = None 
withGeo   = False
dy = str(10.)
withMCTracks = True
# simEngine = "Genie"
#
try:
        opts, args = getopt.getopt(sys.argv[1:], "o:D:FHPu:f:p:g:x:c:hqv:sl:A:Y:i",["paramFile=","geoFile="])
except getopt.GetoptError:
        # print help information and exit:
        print ' enter -f filename -g geofile (-p param file  not needed if geofile present)'  
        sys.exit()
for o, a in opts:
        if o in ("-Y"): 
            dy = float(a)
        if o in ("-p", "--paramFile"):
            ParFile = a
        if o in ("-g", "--geoFile"):
            geoFile = a
        if o in ("-f"):
            InputFile = a

print "FairShip setup for",simEngine

if not InputFile:
 tag = simEngine+"-"+mcEngine+'_D'
 if dy: tag = str(dy)+'.'+tag 
 InputFile     ="ship."+tag+".root" 
if not dy:
 try:
 # try to extract from input file name
   tmp = InputFile.split('.')
   dy  = float( tmp[1]+'.'+tmp[2] )
   tag = str(dy)+'.'+tmp[3]
 except:
   tmp = None

OutFile	      = "tst."+InputFile.split('/')[-1]
if InputFile.find('_D')>0: withGeo = True

def printMCTrack(n,MCTrack):
   mcp = MCTrack[n]
   print ' %6i %7i %6.3F %6.3F %7.3F %7.3F %7.3F %7.3F %6i '%(n,mcp.GetPdgCode(),mcp.GetPx()/u.GeV,mcp.GetPy()/u.GeV,mcp.GetPz()/u.GeV, \
                      mcp.GetStartX()/u.m,mcp.GetStartY()/u.m,mcp.GetStartZ()/u.m,mcp.GetMotherId()   )
def dump(pcut=0):
 print '   #         pid   px    py      pz     vx      vy       vz      mid'
 n=-1
 for mcp in sTree.MCTrack: 
   n+=1
   if mcp.GetP()/u.GeV < pcut :  continue
   printMCTrack(n,sTree.MCTrack)
def printFittedTracks():
  print '  # converged Ndf chi2/Ndf    P      Pt      MCid'
  n=-1
  for ft in sTree.FitTracks:
   n+=1
   fitStatus = ft.getFitStatus()
   fitState  = ft.getFittedState()
   mom = fitState.getMom()
   print '%3i %6i   %4i %6.3F   %6.3F %6.3F %6i '%(n,fitStatus.isFitConverged(),\
            fitStatus.getNdf(),fitStatus.getChi2()/fitStatus.getNdf(),\
            mom.Mag()/u.GeV,mom.Pt()/u.GeV,sTree.fitTrack2MC[n] )
def printParticles():
  print '  #    P    Pt[GeV/c]   DOCA[mm]    Rsq    Vz[m]    d1    d2'
  n=-1
  for aP in sTree.Particles:
   n+=1
   doca = -1.
   if aP.GetMother(1)==99: # DOCA is set
      doca = aP.T()
   Rsq = (aP.Vx()/(2.45*u.m) )**2 + (aP.Vy()/((10./2.-0.05)*u.m) )**2
   print '%3i %6.3F  %6.3F  %9.3F    %6.3F   %6.3F %4i  %4i '%(n,aP.P()/u.GeV,aP.Pt()/u.GeV,\
            doca/u.mm,Rsq,aP.Vz()/u.m,aP.GetDaughter(0),aP.GetDaughter(1) )
class DrawEcalCluster(ROOT.FairTask):
 " My Fair Task"
 def InitTask(self,ecalStructure):
# prepare ecal structure
  self.comp  = ROOT.TEveCompound('Ecal Clusters')
  evmgr.AddElement(self.comp)
  sc    = evmgr.GetScenes()
  self.evscene = sc.FindChild('Event scene')
  mE = top.GetNode('Ecal_1').GetMatrix()
  self.z_ecal = mE.GetTranslation()[2]
  self.ecalStructure = ecalStructure
 def FinishEvent(self):
  pass
 def ExecuteTask(self,option=''):
   self.comp.DestroyElements()
   self.comp.OpenCompound()
   cl=-1
   for aClus in sTree.EcalClusters:
# ecal cell dx=dy=2cm, dz=21.84cm
     cl+=1 
     for i in range( aClus.Size() ):
      mccell = self.ecalStructure.GetHitCell(aClus.CellNum(i))  # Get i'th cell of the cluster.
      if not mccell: continue 
      x1,y1,x2,y2,dz = mccell.X1(),mccell.Y1(),mccell.X2(),mccell.Y2(),mccell.GetEnergy()/u.GeV*0.5*u.m
      if mccell.GetEnergy()/u.MeV < 4. : continue
# ADC noise simulated Guassian with \sigma=1 MeV
      DClus = ROOT.TEveBox()
      DClus.SetName('EcalCluster_'+str(cl)+'_'+str(i)) 
      DClus.SetPickable(ROOT.kTRUE)
      DClus.SetTitle(aClus.__repr__())
      DClus.SetMainColor(ROOT.kRed-4)
      DClus.SetMainTransparency("\x10")
      DClus.SetVertex(0,x1,y1,self.z_ecal)
      DClus.SetVertex(1,x1,y1,self.z_ecal+dz)
      DClus.SetVertex(2,x2,y1,self.z_ecal+dz)
      DClus.SetVertex(3,x2,y1,self.z_ecal)
      DClus.SetVertex(4,x1,y2,self.z_ecal)
      DClus.SetVertex(5,x1,y2,self.z_ecal+dz)
      DClus.SetVertex(6,x2,y2,self.z_ecal+dz)
      DClus.SetVertex(7,x2,y2,self.z_ecal)
      self.comp.AddElement(DClus)
   self.comp.CloseCompound()
   evmgr.ElementChanged(self.evscene,True,True)
 def DrawParticle(self,n):
  self.comp.OpenCompound()
  DTrack = ROOT.TEveLine()
  DTrack.SetPickable(ROOT.kTRUE)
  DTrack.SetMainColor(ROOT.kCyan)
  DTrack.SetLineWidth(4)
  aP=sTree.Particles[n]
  DTrack.SetTitle(aP.__repr__())
  DTrack.SetName('Prtcle_'+str(n))
  DTrack.SetNextPoint(aP.Vx(),aP.Vy(),aP.Vz())
  lam = (self.Targetz - aP.Vz())/aP.Pz()
  DTrack.SetNextPoint(aP.Vx()+lam*aP.Px(),aP.Vy()+lam*aP.Py(),self.Targetz)
  self.comp.AddElement(DTrack)
  self.comp.CloseCompound()
  evmgr.ElementChanged(self.evscene,True,True)
#
class DrawTracks(ROOT.FairTask):
 " My Fair Task"
 def InitTask(self):
# prepare container for fitted tracks
  self.comp  = ROOT.TEveCompound('Tracks')
  evmgr.AddElement(self.comp)
  self.trackColors = {13:ROOT.kGreen,211:ROOT.kRed,11:ROOT.kOrange,321:ROOT.kMagenta}
  self.bfield = ROOT.genfit.BellField(ShipGeo.Bfield.max ,ShipGeo.Bfield.z,2, ShipGeo.Yheight/2.*u.m)
  self.fM = ROOT.genfit.FieldManager.getInstance()
  self.fM.init(self.bfield)
  self.geoMat =  ROOT.genfit.TGeoMaterialInterface()
  ROOT.genfit.MaterialEffects.getInstance().init(self.geoMat)
  dv = top.GetNode('DecayVolume_1')
  ns = dv.GetNodes()
  T1Lid = ns.FindObject("T1Lid_1").GetMatrix()
  self.z_start = T1Lid.GetTranslation()[2]
  muonDet = top.GetNode('MuonDetector_1')
  if muonDet: self.z_end = muonDet.GetMatrix().GetTranslation()[2]+muonDet.GetVolume().GetShape().GetDZ()
  else:       self.z_end = ShipGeo['MuonStation3'].z
  magNode = top.GetNode('MCoil_1')
  if magNode: self.z_mag = magNode.GetMatrix().GetTranslation()[2]
  else:       self.z_mag = ShipGeo['Bfield'].z
  ecalDet = top.GetNode('Ecal_1')
  if ecalDet: self.z_ecal = ecalDet.GetMatrix().GetTranslation()[2]
  else:       self.z_ecal = ShipGeo['ecal'].z
  self.niter = 100
  self.dz = (self.z_end - self.z_start) / float(self.niter)
  self.parallelToZ = ROOT.TVector3(0., 0., 1.) 
  sc    = evmgr.GetScenes()
  self.evscene = sc.FindChild('Event scene')
  targetNode = top.GetNode("TargetArea_1")
  if targetNode:  self.Targetz = targetNode.GetMatrix().GetTranslation()[2]
  else:           self.Targetz = ShipGeo['target'].z
 def FinishEvent(self):
  pass
 def ExecuteTask(self,option=''):
  self.comp.DestroyElements()
  self.comp.OpenCompound()
  if sTree.FindBranch('FitTracks') or sTree.FindBranch('FitTracks_PR'):
   if sTree.FitTracks.GetEntries() > 0: 
     self.DrawFittedTracks()
  if not sTree.FindBranch("GeoTracks") and sTree.MCTrack.GetEntries() > 0: 
    if globals()['withMCTracks']: self.DrawMCTracks()
  self.comp.CloseCompound()
  evmgr.ElementChanged(self.evscene,True,True)
 def DrawParticle(self,n):
  self.comp.OpenCompound()
  DTrack = ROOT.TEveLine()
  DTrack.SetPickable(ROOT.kTRUE)
  DTrack.SetMainColor(ROOT.kCyan)
  DTrack.SetLineWidth(4)
  aP=sTree.Particles[n]
  DTrack.SetTitle(aP.__repr__())
  DTrack.SetName('Prtcle_'+str(n))
  DTrack.SetNextPoint(aP.Vx(),aP.Vy(),aP.Vz())
  lam = (self.Targetz - aP.Vz())/aP.Pz()
  DTrack.SetNextPoint(aP.Vx()+lam*aP.Px(),aP.Vy()+lam*aP.Py(),self.Targetz)
  self.comp.AddElement(DTrack)
 def DrawMCTrack(self,n):
  self.comp.OpenCompound()
  fT = sTree.MCTrack[n]
  DTrack = ROOT.TEveLine()
  DTrack.SetPickable(ROOT.kTRUE)
  DTrack.SetTitle(fT.__repr__())
  p = pdg.GetParticle(fT.GetPdgCode()) 
  if p : pName = p.GetName()
  else:  pName =  str(fT.GetPdgCode())
  DTrack.SetName('MCTrck_'+str(n)+'_'+pName)
  fPos = ROOT.TVector3()
  fMom = ROOT.TVector3()
  fT.GetStartVertex(fPos)
  fT.GetMomentum(fMom)
# check for end vertex
  evVx = False
  for da in sTree.MCTrack:
    if da.GetMotherId()==n: 
       evVx = True
       break
  DTrack.SetNextPoint(fPos.X(),fPos.Y(),fPos.Z())
  if evVx and abs( da.GetStartZ()-fPos.Z() )>1*u.cm : 
    DTrack.SetNextPoint(da.GetStartX(),da.GetStartY(),da.GetStartZ())
  else:
    zEx = 10*u.m
    if evVx : zEx = -10*u.m
    lam = (zEx+fPos.Z())/fMom.Z()
    DTrack.SetNextPoint(fPos.X()+lam*fMom.X(),fPos.Y()+lam*fMom.Y(),zEx+fPos.Z())
  c = ROOT.kYellow
  DTrack.SetMainColor(c)
  DTrack.SetLineWidth(3)
  self.comp.AddElement(DTrack)
  self.comp.CloseCompound()
  evmgr.ElementChanged(self.evscene,True,True)
 def DrawMCTracks(self,option=''):
  n = -1
  ntot = 0
  fPos = ROOT.TVector3()
  fMom = ROOT.TVector3()
  for fT in sTree.MCTrack:
   n+=1
   DTrack = ROOT.TEveLine()
   DTrack.SetPickable(ROOT.kTRUE)
   DTrack.SetTitle(fT.__repr__())
   fT.GetStartVertex(fPos)
   hitlist = {}
   hitlist[fPos.Z()] = [fPos.X(),fPos.Y()]
  # look for HNL 
   if abs(fT.GetPdgCode()) == 9900015:
    for da in sTree.MCTrack:
     if da.GetMotherId()==n: break
  # end vertex of HNL
    da.GetStartVertex(fPos)
    hitlist[fPos.Z()] = [fPos.X(),fPos.Y()]
  # loop over all sensitive volumes to find hits
   for P in ["vetoPoint","muonPoint","EcalPoint","HcalPoint","preshowerPoint","strawtubesPoint","ShipRpcPoint","TargetPoint"]:
    if not sTree.GetBranch(P): continue
    c=eval("sTree."+P)
    for p in c:
      if p.GetTrackID()==n:
       if hasattr(p, "LastPoint"): 
        lp = p.LastPoint()
        if lp.x()==lp.y() and lp.x()==lp.z() and lp.x()==0: 
# must be old data, don't expect hit at 0,0,0  
         hitlist[p.GetZ()] = [p.GetX(),p.GetY()]
        else:   
         hitlist[lp.z()] = [lp.x(),lp.y()] 
         hitlist[2.*p.GetZ()-lp.z()] = [2.*p.GetX()-lp.x(),2.*p.GetY()-lp.y()] 
       else:
        hitlist[p.GetZ()] = [p.GetX(),p.GetY()]
   if len(hitlist)==1:
    if fT.GetMotherId()<0: continue
    if abs(sTree.MCTrack[fT.GetMotherId()].GetPdgCode()) == 9900015:
     # still would like to draw track stumb
     # check for end vertex
     evVx = False
     for da in sTree.MCTrack:
       if da.GetMotherId()==n: 
          evVx = True
          break
     if evVx : hitlist[da.GetStartZ()] = [da.GetStartX(),da.GetStartY()]
     else    : 
      zEx = 10*u.m
      fT.GetMomentum(fMom)
      lam = (zEx+fPos.Z())/fMom.Z()
      hitlist[zEx+fPos.Z()] = [fPos.X()+lam*fMom.X(),fPos.Y()+lam*fMom.Y()]
# sort in z
   lz = hitlist.keys()
   if len(lz)>1:
    lz.sort()
    for z in lz:  DTrack.SetNextPoint(hitlist[z][0],hitlist[z][1],z)
    p = pdg.GetParticle(fT.GetPdgCode()) 
    if p : pName = p.GetName()
    else:  pName =  str(fT.GetPdgCode())
    DTrack.SetName('MCTrack_'+str(n)+'_'+pName)
    c = ROOT.kYellow
    if abs(fT.GetPdgCode()) == 9900015:c = ROOT.kMagenta
    DTrack.SetMainColor(c)
    DTrack.SetLineWidth(3)
    self.comp.AddElement(DTrack)
    ntot+=1
  print "draw ",ntot," MC tracks"
 def DrawFittedTracks(self,option=''):
  n,ntot = -1,0
  for fT in sTree.FitTracks:
   n+=1
   fst = fT.getFitStatus()
   if not fst.isFitConverged(): continue
   if fst.getNdf() < 20: continue
   DTrack = ROOT.TEveLine()
   DTrack.SetPickable(ROOT.kTRUE)
   DTrack.SetTitle(fT.__repr__())
   fstate = fT.getFittedState(0) 
   fPos = fstate.getPos()
   fMom = fstate.getMom()
   pos = fPos
   mom = fMom
   pid = fstate.getPDG()
   zs = self.z_start
   before = True
   for i in range(self.niter):
    NewPosition = ROOT.TVector3(0., 0., zs) 
    if zs>self.z_mag and before:
       before = False
       fstate  = fT.getFittedState(1) 
       fPos = fstate.getPos()
       fMom = fstate.getMom() 
    rc = True     
    if zs < self.z_ecal:  
    # extrapolation through ecal fails, maybe problem with material?
     rep    = ROOT.genfit.RKTrackRep(pid) 
     state  = ROOT.genfit.StateOnPlane(rep) 
     rep.setPosMom(state,fPos,fMom) 
     try:    
      rep.extrapolateToPlane(state, NewPosition, self.parallelToZ)
      pos = state.getPos()
      mom = state.getMom()
      DTrack.SetNextPoint(pos.X(),pos.Y(),pos.Z())
     except: 
      print 'error with extrapolation: z=',zs
      rc = False
    if not rc or zs > self.z_ecal: # use linear extrapolation
     px,py,pz  = mom.X(),mom.Y(),mom.Z() 
     lam = (zs-pos.Z())/pz
     DTrack.SetNextPoint(pos.X()+lam*px,pos.Y()+lam*py,zs)
    zs+=self.dz
   DTrack.SetName('FitTrack_'+str(n))
   c = ROOT.kWhite
   if self.trackColors.has_key(abs(pid)) : c = self.trackColors[abs(pid)]
   DTrack.SetMainColor(c)
   DTrack.SetLineWidth(3)
   self.comp.AddElement(DTrack)
   ntot+=1
  print "draw ",ntot," fitted tracks"
  n=-1
  for aP in sTree.Particles:
   n+=1
# check fitted tracks
   tracksOK = True
   if aP.GetMother(1)==99: # DOCA is set
     if aP.T()>3*u.cm : continue
   for k in range(aP.GetNDaughters()):
    if k>1: break # we don't have more than 2tracks/vertex yet, no idea why ROOT sometimes comes up with 4!
    fT = sTree.FitTracks[aP.GetDaughter(k)]
    fst = fT.getFitStatus()
    if not fst.isFitConverged(): tracksOK=False
    if fst.getNdf() < 20: tracksOK=False
   if not tracksOK: continue
   DTrack = ROOT.TEveLine()
   DTrack.SetPickable(ROOT.kTRUE)
   DTrack.SetMainColor(ROOT.kCyan)
   DTrack.SetLineWidth(4)
   DTrack.SetName('Particle_'+str(n))
   DTrack.SetTitle(aP.__repr__())
   DTrack.SetNextPoint(aP.Vx(),aP.Vy(),aP.Vz())
   lam = (self.Targetz - aP.Vz())/aP.Pz()
   DTrack.SetNextPoint(aP.Vx()+lam*aP.Px(),aP.Vy()+lam*aP.Py(),self.Targetz)
   self.comp.AddElement(DTrack)
#
class IO():
    def __init__(self):
        self.master = Tkinter.Tk()
        self.master.title('SHiP Event Display GUI')
        self.master.geometry(u'320x580+165+820')  
        self.fram1 = Tkinter.Frame(self.master)
        b = Tkinter.Button(self.fram1, text="Next Event",command=self.nextEvent)
        b.pack(fill=Tkinter.BOTH, expand=1) 
        label = Tkinter.Label(self.fram1, text='Event number:')
        label["relief"] = Tkinter.RAISED
        entry = Tkinter.Entry(self.fram1)
        entry["foreground"] = "blue"
        label.pack(side=Tkinter.LEFT)
        entry.pack(side=Tkinter.RIGHT)
        self.contents = Tkinter.IntVar()
        # set it to some value
        self.n = 0
        self.contents.set(self.n)
        # tell the entry widget to watch this variable
        entry["textvariable"] = self.contents
        # and here we get a callback when the user hits return.
        # we will have the program print out the value of the
        # application variable when the user hits return
        entry.bind('<Key-Return>', self.nextEvent)
        self.lbut   = {}
        x = 'withMC'
        a = Tkinter.IntVar()
        if globals()['withMCTracks']: a.set(1)
        else: a.set(0)
        self.lbut[x] = Tkinter.Checkbutton(self.master,text="with MC Tracks",compound=Tkinter.LEFT,variable=a)
        self.lbut[x].var = a
        self.lbut[x]['command'] = self.toogleMCTracks
        self.lbut[x].pack(side=Tkinter.TOP)
        self.geoscene = evmgr.GetScenes().FindChild("Geometry scene")
        for v in top.GetNodes():
         x=v.GetName()
         cmd = 'toogle("'+x+'")' 
         a = Tkinter.IntVar()
         assemb = "Assembly" in v.GetVolume().__str__() 
         if v.IsVisible() or (assemb and v.IsVisDaughters()): a.set(1)
         else : a.set(0)
         self.lbut[x]  = Tkinter.Checkbutton(self.master,text=x.replace('_1',''),compound=Tkinter.LEFT,variable=a)
         self.lbut[x].var = a
         self.lbut[x]['command'] = lambda j=x: self.toogle(j)
         self.lbut[x].pack(side=Tkinter.BOTTOM)
        self.fram1.pack()
    def nextEvent(self,event=None):
        i = int(self.contents.get())
        if i==self.n: self.n+=1
        else  : self.n=i
        self.contents.set(self.n)
        SHiPDisplay.NextEvent(self.n)
    def toogleMCTracks(self):
        tl = fRun.GetMainTask().GetListOfTasks()
        geoTask =  tl.FindObject("GeoTracks")
        if globals()['withMCTracks']: 
           globals()['withMCTracks'] = False
           self.lbut['withMC'].var.set(1)
           if geoTask: geoTask.SetActive(0)
        else: 
           globals()['withMCTracks'] = True
           self.lbut['withMC'].var.set(0)
           if geoTask: geoTask.SetActive(1)
    def toogle(self,x):
        v = top.GetNode(x)
        assemb = "Assembly" in v.GetVolume().__str__()
        if v.IsVisible()>0  or assemb and v.IsVisDaughters()>0 : 
          print "switch off ",x
          v.SetVisibility(0)
          v.SetVisDaughters(0)
          self.lbut[x].var.set(0)
        else:
          print "switch on ",x
          if assemb:  v.SetVisDaughters(1)
          else:       v.SetVisibility(1)
          self.lbut[x].var.set(1)
        evmgr.ElementChanged(self.geoscene,True,True)
        for v in top.GetNodes():
          x = v.GetName()
          if x in self.lbut:  
           assemb = "Assembly" in v.GetVolume().__str__()
           if v.IsVisible()>0 or assemb and v.IsVisDaughters()>0 : self.lbut[x].var.set(1)
           else : self.lbut[x].var.set(0)
#
class EventLoop(ROOT.FairTask):
 " My Fair Task"
 def InitTask(self):
   self.n = 0
   self.first = True
   if fGeo.GetVolume('volTarget'): DisplayNuDetector()
   if fGeo.GetVolume('Ecal'):
 # initialize ecalStructure
    ecalGeo = ecalGeoFile+'z'+str(ShipGeo.ecal.z)+".geo" 
    if not ecalGeo in os.listdir(os.environ["FAIRSHIP"]+"/geometry"): shipDet_conf.makeEcalGeoFile(ShipGeo.ecal.z,ShipGeo.ecal.File)
    self.ecalFiller = ROOT.ecalStructureFiller("ecalFiller", 0,ecalGeo)
    if ecalGeoFile.find("5x10")<0:   
          self.ecalFiller.SetUseMCPoints(ROOT.kFALSE)
          print "ecal cluster display disabled, seems only to work with 5x10m ecal geofile"
    else:  self.ecalFiller.SetUseMCPoints(ROOT.kTRUE)
    self.ecalFiller.StoreTrackInformation()
    rc = sTree.GetEvent(0)
    self.ecalStructure = self.ecalFiller.InitPython(sTree.EcalPointLite)
    speedUp()
    self.calos  = DrawEcalCluster()
    self.calos.InitTask(self.ecalStructure)
   self.tracks = DrawTracks()
   self.tracks.InitTask()
# create SHiP GUI
   self.ioBar = IO()
 def NextEvent(self,i=-1):
   if i<0: self.n+=1
   else  : self.n=i
   fRun.Run(self.n,self.n+1) # go for first event
# check if tracks are made from real pattern recognition
   if sTree.GetBranch("FitTracks_PR"):    sTree.FitTracks = sTree.FitTracks_PR
   if sTree.GetBranch("fitTrack2MC_PR"):  sTree.fitTrack2MC = sTree.fitTrack2MC_PR
   if sTree.GetBranch("Particles_PR"):    sTree.Particles   = sTree.Particles_PR
   self.tracks.ExecuteTask()
   if sTree.FindBranch("EcalClusters"):
     if sTree.EcalClusters.GetEntries()>0:
      self.ecalFiller.Exec('start',sTree.EcalPointLite)
     self.calos.ExecuteTask()
   print 'Event %i ready'%(self.n)
# make pointsets pickable
   for x in mcHits: 
     p = ROOT.gEve.GetCurrentEvent().FindChild(mcHits[x].GetName())
     if p: 
      p.SetPickable(ROOT.kTRUE)
      p.SetTitle(p.__repr__())
 def defaultView(self):
  v   = ROOT.gEve.GetDefaultGLViewer()
  cam  = v.CurrentCamera()
  cam.Reset()
  return cam,v
 def topView(self):
  cam,v = self.defaultView()
  cam.RotateRad(ROOT.TMath.Pi()/2.,0.) # rotation around z axis
  v.DoDraw()
 def bottomView(self):
  cam,v = self.defaultView()
  cam.RotateRad(-ROOT.TMath.Pi()/2.,0.) # rotation around z axis
  v.DoDraw()
 def frontView(self):
  cam,v = self.defaultView()
  cam.RotateRad(0.,ROOT.TMath.Pi()/2.) # rotation around y or x axis
  v.DoDraw()
 def backView(self):
  cam,v = self.defaultView()
  cam.RotateRad(0.,-ROOT.TMath.Pi()/2.) # rotation around y or x axis
  v.DoDraw()
 def sideView(self):
  cam,v = self.defaultView()
  cam.RotateRad(0.,ROOT.TMath.Pi()) # rotation around y or x axis
  v.DoDraw()
#
def speedUp():
 for x in ["wire","gas","rockD","rockS","rockSFe"]:  
   xvol = fGeo.GetVolume(x)
   if xvol: xvol.SetVisibility(0) 
# 
 for x in ["Ecal","Hcal"]:
  xvol = fGeo.GetVolume(x)
  if not xvol: continue
  xvol.SetVisDaughters(0)
  xvol.SetVisibility(1)
  if x=="Ecal": xvol.SetLineColor(ROOT.kYellow) 
  else:        xvol.SetLineColor(ROOT.kOrange+3) 
 sc    = evmgr.GetScenes()
 geoscene = sc.FindChild('Geometry scene')
 evmgr.ElementChanged(geoscene,True,True)

# set display properties for tau nu target
def DisplayNuDetector():
 for x in ["Wall"]:
  xvol = fGeo.GetVolume(x)
  if not xvol: continue
  xvol.SetVisDaughters(0)
  xvol.SetVisibility(1)
 sc    = evmgr.GetScenes()
 geoscene = sc.FindChild('Geometry scene')
 evmgr.ElementChanged(geoscene,True,True)

# draw Ecal yellow instead of black
def ecalYellow():
 sc    = evmgr.GetScenes()
 geoscene = sc.FindChild('Geometry scene')
 ecal = top.GetNode("Ecal_1")
 if ecal : 
   ecal.GetVolume().SetLineColor(ROOT.kYellow) 
 hcal = top.GetNode("Hcal_1")
 if hcal : 
   hcal.GetVolume().SetLineColor(ROOT.kOrange+3) 
 if ecal or hcal: evmgr.ElementChanged(geoscene,True,True)
def switchOf(tag):
 sc    = evmgr.GetScenes()
 geoscene = sc.FindChild('Geometry scene')
 for v in top.GetNodes():
   vname = v.GetName()
   if not vname.find(tag)<0:
     v.SetVisibility(0)
     v.SetVisDaughters(0)
def switchOn(tag):
 sc    = evmgr.GetScenes()
 geoscene = sc.FindChild('Geometry scene')
 for v in top.GetNodes():
   vname = v.GetName()
   if not vname.find(tag)<0:
     print 'switch on ',vname
     v.SetVisibility(1)
     v.SetVisDaughters(1)
 evmgr.ElementChanged(geoscene,True,True)

# switch of drawing of rock
def switchOfRock():
 sc    = evmgr.GetScenes()
 geoscene = sc.FindChild('Geometry scene')
 for x in [ 'rockD', 'rockS']:
  v = fGeo.FindVolumeFast(x)
  v.SetVisibility(0)
 evmgr.ElementChanged(geoscene,True,True)
def switchOfAll(exc):
 sc    = evmgr.GetScenes()
 geoscene = sc.FindChild('Geometry scene')
 for v in top.GetNodes():
   vname = v.GetName()
   if not vname.find('cave')< 0 : continue
   todo = True
   for tag in exc: 
    if not tag.find(vname)<0: todo = False 
   if todo:
    v.SetVisibility(0)
    v.SetVisDaughters(0)
 evmgr.ElementChanged(geoscene,True,True) 
def switchOnAll(exc):
 sc    = evmgr.GetScenes()
 geoscene = sc.FindChild('Geometry scene')
 for v in top.GetNodes():
   vname = v.GetName()
   if not vname.find('cave')< 0 : continue
   todo = True
   for tag in exc: 
    if not tag.find(vname)<0: todo = False 
   if todo:
    v.SetVisibility(1)
    v.SetVisDaughters(1)
 evmgr.ElementChanged(geoscene,True,True) 

def select(pattern):
 exc = []
 for v in fGeo.GetListOfVolumes():
   vname = v.GetName()
   if not vname.find(pattern) < 0 : exc.append(vname)
 return exc
def search(lvdict,tag):
  for x in lvdict: 
   if not x.find(tag)<0: print x
def rename(name='ship.TGeant4.root'):
 f = ROOT.TFile(name,'UPDATE')
 t = f.Get('cbmsim')
 for x in t.GetListOfBranches():
  nm = x.GetName().replace('_1','')
  x.SetName(nm)
 t.Write()
 f.Close() 

class Rulers(ROOT.FairTask):
 " add Ruler"
 def __init__(self):
  self.ruler  = ROOT.TEveCompound('Rulers')
  evmgr.AddElement(self.ruler)
 def show(self,xy=0):
  self.ruler.DestroyElements()
  self.ruler.OpenCompound()
  xpos,ypos = -500., 0.
  zstart  = ShipGeo.target.z0
  zlength = ShipGeo.MuonStation3.z - zstart + 10*u.m
  a1 = ROOT.TEveLine()
  a1.SetNextPoint(xpos,ypos, zstart)
  a1.SetNextPoint(xpos,ypos, zstart+zlength)
  a1.SetMainColor(ROOT.kBlue)
  a1.SetLineWidth(50)
  self.ruler.AddElement(a1)
  z=zstart
  for i in range(int(zlength/100)):
   m = ROOT.TEveLine()
   m.SetNextPoint(xpos,ypos, z)
   m.SetNextPoint(xpos-0.5*u.m,ypos,z)
   m.SetMainColor(ROOT.kRed)
   m.SetLineWidth(3)
   a1.AddElement(m)
   m = ROOT.TEveLine()
   m.SetNextPoint(xpos,ypos, z+0.5*u.m )
   m.SetNextPoint(xpos-0.2*u.m,ypos,z+0.5*u.m )
   m.SetMainColor(ROOT.kRed)
   m.SetLineWidth(2)
   a1.AddElement(m)
   t1 = ROOT.TEveText(str(i)+'m')
   t1.SetFontSize(5)
   t1.RefMainTrans().SetPos(xpos-0.1*u.m,ypos+0.2*u.m,z)
   a1.AddElement(t1)
   z+=1*u.m
  xpos,ypos = 0., 0.
  if xy==0:  z = ShipGeo.MuonStation3.z+2*u.m
  else: z=xy 
  ylength = 7*u.m
  a2 = ROOT.TEveLine()
  a2.SetNextPoint(xpos,-ylength, z)
  a2.SetNextPoint(xpos,ylength, z)
  a2.SetMainColor(ROOT.kBlue)
  a2.SetLineWidth(50)
  self.ruler.AddElement(a2)
  ypos=-ylength
  for i in range(-int(ylength/100),int(ylength/100),1):
   m = ROOT.TEveLine()
   m.SetNextPoint(xpos,ypos, z)
   m.SetNextPoint(xpos+0.05*u.m,ypos,z)
   m.SetMainColor(ROOT.kRed)
   m.SetLineWidth(3)
   a2.AddElement(m)
   m = ROOT.TEveLine()
   m.SetNextPoint(xpos,         ypos+0.5*u.m, z )
   m.SetNextPoint(xpos+0.02*u.m,ypos+0.5*u.m,z)
   m.SetMainColor(ROOT.kRed)
   m.SetLineWidth(1)
   a2.AddElement(m)
   t1 = ROOT.TEveText(str(i)+'m')
   t1.SetFontSize(5)
   t1.RefMainTrans().SetPos(xpos-0.5*u.m,ypos,z)
   a2.AddElement(t1)
   ypos+=1*u.m
  ty = ROOT.TEveText("y-axis")
  ty.SetFontSize(10)
  ty.RefMainTrans().SetPos(0.,ypos+1*u.m,z)
  ty.SetMainColor(ROOT.kRed-2);
  a2.AddElement(ty)
  xpos,ypos = 0., 0.
  xlength = 3*u.m
  a3 = ROOT.TEveLine()
  a3.SetNextPoint(-xlength,0, z)
  a3.SetNextPoint(xlength,0, z)
  a3.SetMainColor(ROOT.kBlue)
  a3.SetLineWidth(50)
  self.ruler.AddElement(a3)
  xpos=-xlength
  for i in range(-int(xlength/100),int(xlength/100),1):
   m = ROOT.TEveLine()
   m.SetNextPoint(xpos,ypos, z)
   m.SetNextPoint(xpos,ypos-0.05*u.m,z)
   m.SetMainColor(ROOT.kRed)
   m.SetLineWidth(3)
   a3.AddElement(m)
   m = ROOT.TEveLine()
   m.SetNextPoint(xpos+0.5*u.m,ypos, z )
   m.SetNextPoint(xpos+0.5*u.m,ypos-0.02*u.m,z)
   m.SetMainColor(ROOT.kRed)
   m.SetLineWidth(2)
   a3.AddElement(m)
   t1 = ROOT.TEveText(str(i)+'m')
   t1.SetFontSize(5)
   t1.RefMainTrans().SetPos(xpos,ypos-0.1*u.m,z)
   a3.AddElement(t1)
   xpos+=1*u.m 
  tx = ROOT.TEveText("x-axis")
  tx.SetFontSize(10)
  tx.RefMainTrans().SetPos(xpos+1*u.m,0.,z)
  tx.SetMainColor(ROOT.kRed-2);
  a3.AddElement(tx)

  t1 = ROOT.TEveText("SHiP")
  t1.SetFontSize(200)
  t1.RefMainTrans().SetPos(0.,600.,ShipGeo.TrackStation1.z-10*u.m)
  t1.PtrMainTrans().RotateLF(1, 3, ROOT.TMath.PiOver2());
  t1.SetMainColor(ROOT.kOrange-2);
  t1.SetFontMode(ROOT.TGLFont.kExtrude);
  t1.SetLighting(ROOT.kTRUE);
  a1.AddElement(t1)
  self.ruler.CloseCompound()
  sc    = ROOT.gEve.GetScenes()
  geoscene = sc.FindChild('Geometry scene')
  ROOT.gEve.ElementChanged(geoscene,True,True)
 def remove(self):
  self.ruler.DestroyElements()

def mydebug():               
 t = g.FindObjectAny('cbmsim')
 nev = t.GetEntriesFast()
 t.GetEntry(0)
# Loop over Geo tracks  
 for i in range( min(5,nev) ) :
   t.GetEntry(i)
   for gTr in t.GeoTracks: 
    gTr.Print()
    part = gTr.GetParticle()
    lorv = ROOT.TLorentzVector()
    print 'xyz E pxpypz',gTr.GetPoint(0)[0],gTr.GetPoint(0)[1] ,gTr.GetPoint(0)[2],lorv.E(),lorv.Px(),lorv.Py(),lorv.Pz()
# Loop over MC tracks  
 for i in range( min(5,nev) ) :
   t.GetEntry(i)
   for gMCTr in t.MCTrack: 
    gMCTr.Print()
    print  gMCTr.GetPdgCode(),gMCTr.GetMass(),gMCTr.GetP()
# MC event header  
 for i in range( nev ) :
   t.GetEntry(i)
   print t.MCEventHeader.GetEventID(),t.MCEventHeader.GetRunID(),t.MCEventHeader.GetZ()
# geometrie
 fGeo = g.FindObjectAny("FAIRGeom")
 cave = fGeo.GetTopVolume()
 cave.Draw('ogl')
# eve
 evmgr = ROOT.gEve
#
 sc    = evmgr.GetScenes()
 geoscene = sc.FindChild('Geometry scene')
 topnode  = geoscene.FindChild('cave_1')
 topnode.SetVisLevel(4)
 evmgr.ElementChanged(geoscene,True,True)
def debugStraw(n):
 fGeo = ROOT.gGeoManager  
 vols = fGeo.GetListOfVolumes()
 sTree = g.FindObjectAny('cbmsim')
 sTree.GetEntry(n)
 for s in sTree.strawtubesPoint:
  print vols[s.GetDetectorID()-1].GetName()

#----Load the default libraries------
from basiclibs import *  
# -----   Reconstruction run   -------------------------------------------
fRun = ROOT.FairRunAna()
if geoFile: 
 if geoFile[0:4] == "/eos": geoFile="root://eoslhcb.cern.ch/"+geoFile
 fRun.SetGeomFile(geoFile)

if InputFile[0:4] == "/eos": InputFile="root://eoslhcb.cern.ch/"+InputFile
if hasattr(fRun,'SetSource'):
 inFile = ROOT.FairFileSource(InputFile)
 fRun.SetSource(inFile)
else:
 fRun.SetInputFile(InputFile)
fRun.SetOutputFile(OutFile)

if ParFile:
 rtdb      = fRun.GetRuntimeDb()
 parInput1 = ROOT.FairParRootFileIo()
 parInput1.open(ParFile)
 rtdb.setFirstInput(parInput1)
   
fMan= ROOT.FairEventManager()
fMan.SetMaxEnergy(400.) # default is 25 GeV only !
fMan.SetMinEnergy(0.1) #  100 MeV
fMan.SetEvtMaxEnergy(400.) # what is the difference between EvtMaxEnergy and MaxEnergy ?
fMan.SetPriOnly(False)  # display everything

#----------------------Tracks and points -------------------------------------
verbose = 0  # 3 lot of output
if withGeo: 
  Track       = ROOT.FairMCTracks("Monte-Carlo Tracks",verbose)
  GTrack      = ROOT.FairMCTracks("GeoTracks",verbose)
  fMan.AddTask(GTrack)
  fMan.AddTask(Track)

mcHits = {}
mcHits['VetoPoints']  = ROOT.FairMCPointDraw("vetoPoint", ROOT.kBlue, ROOT.kFullDiamond)
mcHits['StrawPoints'] = ROOT.FairMCPointDraw("strawtubesPoint", ROOT.kGreen, ROOT.kFullCircle)
mcHits['EcalPoints']  = ROOT.FairMCPointDraw("EcalPoint", ROOT.kRed, ROOT.kFullSquare)
mcHits['HcalPoints']  = ROOT.FairMCPointDraw("HcalPoint", ROOT.kMagenta, ROOT.kFullSquare)
mcHits['MuonPoints']  = ROOT.FairMCPointDraw("muonPoint", ROOT.kYellow, ROOT.kFullSquare)
mcHits['RpcPoints']   = ROOT.FairMCPointDraw("ShipRpcPoint", ROOT.kOrange, ROOT.kFullSquare)
mcHits['TargetPoints']   = ROOT.FairMCPointDraw("TargetPoint", ROOT.kRed, ROOT.kFullSquare)

for x in mcHits: fMan.AddTask(mcHits[x])

fMan.Init(1,5,10) # default Init(visopt=1, vislvl=3, maxvisnds=10000), ecal display requires vislvl=4
#visopt, set drawing mode :
# option=0 (default) all nodes drawn down to vislevel
# option=1           leaves and nodes at vislevel drawn
# option=2           path is drawn
# vislvl
#
fRman = ROOT.FairRootManager.Instance()
sTree = fRman.GetInChain()
fGeo  = ROOT.gGeoManager 
top   = fGeo.GetTopVolume()
evmgr = ROOT.gEve

if not fRun.GetGeoFile().FindKey('ShipGeo'):
 # old geofile, missing Shipgeo dictionary
 # try to figure out which ecal geo to load
  if fGeo.GetVolume('EcalModule3') :  ecalGeoFile = "ecal_ellipse6x12m2.geo"
  else: ecalGeoFile = "ecal_ellipse5x10m2.geo" 
  ShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", Yheight = float(dy), EcalGeoFile = ecalGeoFile)
else: 
 # new geofile, load Shipgeo dictionary written by run_simScript.py
  upkl    = Unpickler( fRun.GetGeoFile() )
  ShipGeo = upkl.load('ShipGeo')
  ecalGeoFile = ShipGeo.ecal.File
if hasattr(ShipGeo,'preshowerOption'): 
 if ShipGeo.preshowerOption >0: 
  mcHits['preshowerPoints']  = ROOT.FairMCPointDraw("preshowerPoint", ROOT.kYellow, ROOT.kFullCircle)
  fMan.AddTask(mcHits['preshowerPoints'])
# switchOfAll('RockD')
rulers = Rulers()
SHiPDisplay = EventLoop()
SHiPDisplay.InitTask()
SHiPDisplay.NextEvent()


