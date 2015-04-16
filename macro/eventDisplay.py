#!/usr/bin/env python -i
import ROOT,sys,getopt,os,Tkinter
from ShipGeoConfig import ConfigRegistry
import shipunit as u

fMan = None
fRun = None
pdg  = ROOT.TDatabasePDG()
g    = ROOT.gROOT 

#-----prepare python exit-----------------------------------------------
def pyExit():
 global fMan,fRun
 del fMan
 del fRun
import atexit
atexit.register(pyExit)

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
        opts, args = getopt.getopt(sys.argv[1:], "o:D:FHPu:f:p:g:x:c:hqv:sl:A:Y:i",["Pythia6","Pythia8","Genie","Ntuple","MuonBack","Cosmics","paramFile=","geoFile="])
except getopt.GetoptError:
        # print help information and exit:
        print ' enter --Pythia8/6 to generate events with Pythia8/6 or --Genie for reading and processing neutrino interactions'  
        print '       --MuonBack to generate events from muon background file, --Cosmics for cosmic generator data'  
        sys.exit()
for o, a in opts:
        if o in ("--Pythia6"):
            simEngine = "Pythia6"
        if o in ("--Pythia8"):
            simEngine = "Pythia8"
        if o in ("--Genie"):
            simEngine = "Genie"
        if o in ("--Ntuple"):
            simEngine = "Ntuple"
        if o in ("--MuonBack"):
            simEngine = "MuonBack"
        if o in ("--Cosmics"):
            simEngine = "Cosmics"
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

if not ParFile: 
  tmp = InputFile.split('.')
  tag = str(dy)+'.'+tmp[3]
  ParFile       ="ship.params."+tag.replace('_rec','')+".root"  
OutFile	      = "tst."+InputFile
if InputFile.find('_D')>0: withGeo = True
#
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
class DrawTracks(ROOT.FairTask):
 " My Fair Task"
 def InitTask(self):
# prepare container for fitted tracks
  self.comp  = ROOT.TEveCompound('Fitted tracks')
  evmgr.AddElement(self.comp)
  self.trackColors = {13:ROOT.kGreen,211:ROOT.kRed,11:ROOT.kOrange,321:ROOT.kMagenta}
  ShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", Yheight = int(float(dy)))
  self.bfield = ROOT.genfit.BellField(ShipGeo.Bfield.max ,ShipGeo.Bfield.z,2, ShipGeo.Yheight/2.*u.m)
  self.fM = ROOT.genfit.FieldManager.getInstance()
  self.fM.init(self.bfield)
  self.geoMat =  ROOT.genfit.TGeoMaterialInterface()
  ROOT.genfit.MaterialEffects.getInstance().init(self.geoMat)
  dv = top.GetNode('DecayVolume_1')
  ns = dv.GetNodes()
  T1Lid = ns.FindObject("T1Lid_1").GetMatrix()
  self.z_start = T1Lid.GetTranslation()[2]
  mv = top.GetNode('MuonDetector_1').GetMatrix()
  self.z_end = mv.GetTranslation()[2]
  mM = top.GetNode('MCoil_1').GetMatrix()
  self.z_mag = mM.GetTranslation()[2]
  mE = top.GetNode('Ecal_1').GetMatrix()
  self.z_ecal = mE.GetTranslation()[2]
  self.niter = 100
  self.dz = (self.z_end - self.z_start) / float(self.niter)
  self.parallelToZ = ROOT.TVector3(0., 0., 1.) 
  sc    = evmgr.GetScenes()
  self.evscene = sc.FindChild('Event scene')

 def FinishEvent(self):
  pass
 def ExecuteTask(self,option=''):
  self.comp.DestroyElements()
  self.comp.OpenCompound()
  if sTree.FitTracks.GetEntries() > 0: 
    self.DrawFittedTracks()
  if not sTree.FindBranch("GeoTracks") and sTree.MCTrack.GetEntries() > 0: 
    if globals()['withMCTracks']: self.DrawMCTracks()
  self.comp.CloseCompound()
  evmgr.ElementChanged(self.evscene,True,True)
 def DrawMCTracks(self,option=''):
  n = 0
  ntot = 0
  fPos = ROOT.TVector3()
  for fT in sTree.MCTrack:
   DTrack = ROOT.TEveLine()
   fT.GetStartVertex(fPos)
   hitlist = {}
   hitlist[fPos.Z()] = [fPos.X(),fPos.Y()]
  # loop over all sensitive volumes to find hits
   for c in [sTree.vetoPoint,sTree.muonPoint,sTree.EcalPoint,sTree.HcalPoint,sTree.strawtubesPoint,sTree.ShipRpcPoint]:
    for p in c:
      if p.GetTrackID()==n:
       hitlist[p.GetZ()] = [p.GetX(),p.GetY()]
# sort in z
   lz = hitlist.keys()
   if len(lz)>1:
    lz.sort()
    for z in lz:  DTrack.SetNextPoint(hitlist[z][0],hitlist[z][1],z)
    DTrack.SetName('MCTrack_'+str(n))
    c = ROOT.kYellow
    DTrack.SetMainColor(c)
    DTrack.SetLineWidth(3)
    self.comp.AddElement(DTrack)
    ntot+=1
   n+=1
  print "draw ",ntot," MC tracks"
 def DrawFittedTracks(self,option=''):
  n,ntot = 0,0
  for fT in sTree.FitTracks:
   n+=1
   fst = fT.getFitStatus()
   if not fst.isFitConverged(): continue
   if fst.getNdf() < 20: continue
   DTrack = ROOT.TEveLine()
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
#
class IO():
    def __init__(self):
        self.master = Tkinter.Tk()
        self.master.title('SHiP Event Display GUI')
        self.master.geometry(u'320x530+165+820')  
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
   speedUp()
   self.drawer = DrawTracks()
   self.drawer.InitTask()
# create SHiP GUI
   self.ioBar = IO()
 def NextEvent(self,i=-1):
   if i<0: self.n+=1
   else  : self.n=i
   fRun.Run(self.n) # go for first event
   self.drawer.ExecuteTask()
   print 'Event %i ready'%(self.n)
#
def speedUp():
 for x in ["wire","gas","rockD","rockS"]:  
   xvol = fGeo.GetVolume(x)
   xvol.SetVisibility(0) 
# 
 for x in ["Ecal","Hcal"]:
  xvol = fGeo.GetVolume(x)
  xvol.SetVisDaughters(0)
  xvol.SetVisibility(1)
  if x=="Ecal": xvol.SetLineColor(ROOT.kYellow) 
  else:        xvol.SetLineColor(ROOT.kOrange+3) 
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
def access2Branches():
 MCTracks = ROOT.TClonesArray("ShipMCTrack")
 sTree = g.FindObjectAny('cbmsim')
 sTree.SetBranchAddress("MCTrack", MCTracks)
 TrackingHits   = ROOT.TClonesArray("vetoPoint")
 sTree.SetBranchAddress("vetoPoint", TrackingHits)
 Ecals = ROOT.TClonesArray("ecalPoint")
 sTree.SetBranchAddress("EcalPoint", Ecals)
 sTree.MCTrack   = MCTracks
 sTree.vetoPoint = TrackingHits
 sTree.EcalPoint = Ecals
 sTree.GetEntry(1)
 return sTree 

#----Load the default libraries------
from basiclibs import *  
# -----   Reconstruction run   -------------------------------------------
fRun = ROOT.FairRunAna()
if geoFile: fRun.SetGeomFile(geoFile)
fRun.SetInputFile(InputFile)
fRun.SetOutputFile(OutFile)

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
VetoPoints  = ROOT.FairMCPointDraw("vetoPoint", ROOT.kBlue, ROOT.kFullDiamond)
StrawPoints = ROOT.FairMCPointDraw("strawtubesPoint", ROOT.kGreen, ROOT.kFullCircle)
EcalPoints  = ROOT.FairMCPointDraw("EcalPoint", ROOT.kRed, ROOT.kFullSquare)
HcalPoints  = ROOT.FairMCPointDraw("HcalPoint", ROOT.kMagenta, ROOT.kFullSquare)
MuonPoints  = ROOT.FairMCPointDraw("muonPoint", ROOT.kYellow, ROOT.kFullSquare)
RpcPoints   = ROOT.FairMCPointDraw("ShipRpcPoint", ROOT.kOrange, ROOT.kFullSquare)

fMan.AddTask(VetoPoints)
fMan.AddTask(MuonPoints)
fMan.AddTask(EcalPoints)
fMan.AddTask(HcalPoints)
fMan.AddTask(StrawPoints)
fMan.AddTask(RpcPoints)

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
# switchOfAll('RockD')

SHiPDisplay = EventLoop()
SHiPDisplay.InitTask()
SHiPDisplay.NextEvent()
