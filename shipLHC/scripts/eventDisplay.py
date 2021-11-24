#!/usr/bin/env python -i
import ROOT,sys,os

from argparse import ArgumentParser
from ShipGeoConfig import ConfigRegistry
from rootpyPickler import Unpickler
from array import array
import shipunit as u
from decorators import *
import shipRoot_conf,shipDet_conf
shipRoot_conf.configure()
G = open('eveGlobal.py','w')
G.close()

fMan = None
fRun = None
pdg  = ROOT.TDatabasePDG.Instance()
g    = ROOT.gROOT 
gEnv = ROOT.gEnv
gEnv.SetValue('Eve.Viewer.HideMenus','off')

withMCTracks      = True
withAllMCTracks = False

transparentMaterials = {'air':99,'iron':99,'aluminium':90,'EmulsionFilmMixture':90,'Polycarbonate':90,
'CarbonComposite':90,'Aluminum':90,'rohacell':90,'Scintillator':90,'tungstenalloySND':99,'polyvinyltoluene':90}

parser = ArgumentParser()

parser.add_argument("-f", "--inputFile",    dest="InputFile", help="Input file", required=True)
parser.add_argument("-g", "--geoFile",      dest="geoFile",   help="ROOT geofile", required=True)
parser.add_argument("-p", "--paramFile",    dest="ParFile",   help="FairRoot param file", required=False, default=None)
parser.add_argument("--Debug",              dest="Debug", help="Switch on debugging", required=False, action="store_true")
parser.add_argument("-o", "--outFile",      dest="OutputFile", help="Output file", required=False,default=None)

options = parser.parse_args()

def printMCTrack(n,MCTrack):
   mcp = MCTrack[n]
   print(' %6i %7i %6.3F %6.3F %7.3F %7.3F %7.3F %7.3F %6i '%(n,mcp.GetPdgCode(),mcp.GetPx()/u.GeV,mcp.GetPy()/u.GeV,mcp.GetPz()/u.GeV, \
                      mcp.GetStartX()/u.m,mcp.GetStartY()/u.m,mcp.GetStartZ()/u.m,mcp.GetMotherId()   ))

def dump(pcut=0):
 print('   #         pid   px    py      pz     vx      vy       vz      mid')
 n=-1
 for mcp in sTree.MCTrack: 
   n+=1
   if mcp.GetP()/u.GeV < pcut :  continue
   printMCTrack(n,sTree.MCTrack)

class DrawDigi(ROOT.FairTask):
 " My Fair Task"
 def InitTask(self):
  self.comp  = ROOT.TEveCompound('Digis')
  gEve.AddElement(self.comp)
  sc    = gEve.GetScenes()
  self.evscene = sc.FindChild('Event scene')
 def FinishEvent(self):
  pass
 def ExecuteTask(self,option=''):
   self.comp.DestroyElements()
   self.comp.OpenCompound()
   nav = ROOT.gGeoManager.GetCurrentNavigator()
   digis = []
   if sTree.FindBranch("Digi_ScifiHits"): digis.append(sTree.Digi_ScifiHits)
   if sTree.FindBranch("Digi_MuFilterHits"): digis.append(sTree.Digi_MuFilterHits)
   for branch in digis:
    print('digis:',branch.GetName(),":",branch.GetEntries())
    for digi in branch:
     if not digi.isValid(): continue
     B=ROOT.TVector3()
     A=ROOT.TVector3()
     detID = digi.GetDetectorID()
     if digi.GetName()  == 'MuFilterHit':
         system = digi.GetSystem()
         modules['MuFilter'].GetPosition(detID,A,B)
         if system==1: vol = sGeo.GetVolume('volVetoBar')
         elif system==2: vol = sGeo.GetVolume('volMuUpstreamBar')
         elif system==3: 
             if digi.isVertical: vol = sGeo.GetVolume('volMuDownstreamBar_ver')
             else:                          vol = sGeo.GetVolume('volMuDownstreamBar_hor')
         color = ROOT.kGreen
         shape = vol.GetShape()
         dx,dy,dz = shape.GetDX(),shape.GetDY(),shape.GetDZ()
         origin = shape.GetOrigin()
     elif digi.GetName()  == 'sndScifiHit':
         modules['Scifi'].GetSiPMPosition(detID,A,B)
         p = nav.GetPath()
         nav.cd(p[:p.find('/Fi')])
         mPoint = 0.5*(A+B)
         master = array('d',[mPoint[0],mPoint[1],mPoint[2]])
         o = array('d',[0,0,0])
         nav.MasterToLocal(master,o)
         vol = sGeo.GetVolume('ChannelVol')
         color = ROOT.kWhite
         shape = vol.GetShape()
         if digi.isVertical(): 
              dy,dx,dz = shape.GetDX(),shape.GetDY(),shape.GetDZ()
                                   # fLengthScifiMat/2, fWidthChannel/2, fZEpoxyMat/2
         else:
              dx,dy,dz = shape.GetDX(),shape.GetDY(),shape.GetDZ()

     bx = ROOT.TEveBox( digi.GetName()+'_'+str(digi.GetDetectorID()) )
     bx.SetPickable(ROOT.kTRUE)
     bx.SetTitle(digi.__repr__())
     bx.SetMainColor(color)
     master = array('d',[0,0,0])
     n=0
     for edge in [ [-dx,-dy,-dz],[-dx,+dy,-dz],[+dx,+dy,-dz],[+dx,-dy,-dz],[-dx,-dy, dz],[-dx,+dy, dz],[+dx,+dy, dz],[+dx,-dy, dz]]:
      origin = array('d',[edge[0]+o[0],edge[1]+o[1],edge[2]+o[2]])
      nav.LocalToMaster(origin,master)
      bx.SetVertex(n,master[0],master[1],master[2])
      n+=1
     self.comp.AddElement(bx)
    self.comp.CloseCompound()
   gEve.ElementChanged(self.evscene,True,True)
#
class DrawTracks(ROOT.FairTask):
 " My Fair Task"
 def InitTask(self):
# prepare container for fitted tracks
  self.comp  = ROOT.TEveCompound('Tracks')
  gEve.AddElement(self.comp)
  self.niter = 100
  self.dz = (200.) / float(self.niter)
  self.parallelToZ = ROOT.TVector3(0., 0., 1.) 
  sc    = gEve.GetScenes()
  self.evscene = sc.FindChild('Event scene')
 def FinishEvent(self):
  pass
 def ExecuteTask(self,option=''):
  self.comp.DestroyElements()
  self.comp.OpenCompound()
  if sTree.MCTrack.GetEntries() > 0: 
    if globals()['withAllMCTracks']:  DrawSimpleMCTracks()   # for sndlhc, until more details are simulated 
    elif globals()['withMCTracks']:      self.DrawMCTracks()
  self.comp.CloseCompound()
  gEve.ElementChanged(self.evscene,True,True)

 def DrawFittedTracks(self,option=''):
  n,ntot = -1,0
  for fT in sTree.fittedTracks:
   n+=1
   fst = fT.getFitStatus()
   if not fst.isFitConverged(): continue
   DTrack = ROOT.TEveLine()
   DTrack.SetPickable(ROOT.kTRUE)
   DTrack.SetTitle(fT.__repr__())
   for n in range(fT.getNumPoints()):
       fstate = fT.getFittedState(n)
       fPos = fstate.getPos()
       DTrack.SetNextPoint(fPos.X(),fPos.Y(),fPos.Z())
   DTrack.SetName('FitTrack_'+str(n))
   c = ROOT.kOrange
   DTrack.SetMainColor(c)
   DTrack.SetLineWidth(3)
   self.comp.AddElement(DTrack)
   ntot+=1
  print("draw ",ntot," fitted tracks")

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
  gEve.ElementChanged(self.evscene,True,True)
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
   if abs(fT.GetPdgCode()) == options.HiddenParticleID:
    for da in sTree.MCTrack:
     if da.GetMotherId()==n: break
  # end vertex of HNL
    da.GetStartVertex(fPos)
    hitlist[fPos.Z()] = [fPos.X(),fPos.Y()]
  # loop over all sensitive volumes to find hits
   for P in ["EmulsionDetPoint","MuFilterPoint","ScifiPoint"]:
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
    if abs(sTree.MCTrack[fT.GetMotherId()].GetPdgCode()) == options.HiddenParticleID:
     # still would like to draw track stub
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
   lz = list(hitlist.keys())
   if len(lz)>1:
    lz.sort()
    for z in lz:  DTrack.SetNextPoint(hitlist[z][0],hitlist[z][1],z)
    p = pdg.GetParticle(fT.GetPdgCode()) 
    if p : pName = p.GetName()
    else:  pName =  str(fT.GetPdgCode())
    DTrack.SetName('MCTrack_'+str(n)+'_'+pName)
    c = ROOT.kYellow
    if abs(fT.GetPdgCode()) == options.HiddenParticleID:c = ROOT.kMagenta
    DTrack.SetMainColor(c)
    DTrack.SetLineWidth(3)
    self.comp.AddElement(DTrack)
    ntot+=1
  print("draw ",ntot," MC tracks")

#
class IO():
    def __init__(self):
# add actions to eve display
        gEve = ROOT.gEve
        slot = ROOT.TEveWindow.CreateWindowInTab(gEve.GetBrowser().GetTabLeft())
        slot.SetShowTitleBar(ROOT.kFALSE)
        packs = slot.MakePack();
        packs.SetShowTitleBar(ROOT.kFALSE);
        packs.SetElementName("ActionsX")
        packs.SetHorizontal()
        slot = packs.NewSlot()
        frame = slot.MakeFrame()
        frame.SetElementName("commands")
        frame.SetShowTitleBar(ROOT.kFALSE)
        cf = frame.GetGUICompositeFrame()
        hf = ROOT.TGVerticalFrame(cf)
        hf.SetCleanup(ROOT.kLocalCleanup)
        hf.SetWidth(150)
        cf.AddFrame(hf)
        guiFrame = ROOT.TGVerticalFrame(hf)
        hf.AddFrame(guiFrame, ROOT.TGLayoutHints(ROOT.kLHintsExpandX))
        guiFrame.SetCleanup(ROOT.kDeepCleanup)

        bnx = ROOT.TGTextButton(guiFrame, "next event")
        bnx.SetWidth(150)
        bnx.SetToolTipText('click for next event')
        bnx.SetCommand('TPython::Exec("import evdsnd_commands ;  rc=evdsnd_commands.nextEvent()")')
        bnx.SetTextColor(ROOT.kBlue)
        guiFrame.AddFrame(bnx, ROOT.TGLayoutHints(ROOT.kLHintsExpandX))

        bt = ROOT.TGTextButton(guiFrame, "switch transparent mode on/off")
        bt.SetWidth(150)
        bt.SetToolTipText('switch transparent mode on/off for better visibility of tracks')
        bt.SetCommand('TPython::Exec("import evdsnd_commands ;  rc=evdsnd_commands.transparentMode()")')
        guiFrame.AddFrame(bt, ROOT.TGLayoutHints(ROOT.kLHintsExpandX))

        blu = ROOT.TGTextButton(guiFrame, "more light")
        blu.SetWidth(150)
        blu.SetToolTipText('increase light power. Front, Side, Specular')
        blu.SetCommand('TPython::Exec("import evdsnd_commands ;  rc=evdsnd_commands.light(0.5)")')
        guiFrame.AddFrame(blu, ROOT.TGLayoutHints(ROOT.kLHintsExpandX))
        bld = ROOT.TGTextButton(guiFrame, "less light")
        bld.SetWidth(150)
        bld.SetToolTipText('decrease light power. Front, Side, Specular')
        bld.SetCommand('TPython::Exec("import evdsnd_commands ;  rc=evdsnd_commands.light(-0.5)")')
        guiFrame.AddFrame(bld, ROOT.TGLayoutHints(ROOT.kLHintsExpandX))

        bld = ROOT.TGTextButton(guiFrame, "fit track")
        bld.SetWidth(150)
        bld.SetToolTipText('simple PR, fit track')
        bld.SetCommand('TPython::Exec("import evdsnd_commands ;  rc=evdsnd_commands.fittrack")')
        guiFrame.AddFrame(bld, ROOT.TGLayoutHints(ROOT.kLHintsExpandX))

#
        cf.MapSubwindows()
        cf.Layout()
        cf.MapWindow()
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
          print("switch off ",x)
          v.SetVisibility(0)
          v.SetVisDaughters(0)
          self.lbut[x].var.set(0)
        else:
          print("switch on ",x)
          if assemb:  v.SetVisDaughters(1)
          else:       v.SetVisibility(1)
          self.lbut[x].var.set(1)
        gEve.ElementChanged(self.geoscene,True,True)
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
   rc = sTree.GetEvent(0)
   modules['Scifi'].SiPMmapping()
   self.digi = DrawDigi()
   self.digi.InitTask()
   self.tracks = DrawTracks()
   self.tracks.InitTask()
# create GUI
   self.ioBar = IO()
   self.TransparentMode = 0
   v1 = gEve.GetDefaultViewer()
   v1.GetEveFrame().HideAllDecorations()
   tr=gEve.GetBrowser().GetTabRight()
   t0 = tr.GetTabTab(0)
   t0.SetText(ROOT.TGString('3D'))
#
# some default setup
   SND = ['SciFi','Wall','volVetoBar ','volFeBlock',' volMuUpstreamBar ','volMuDownstreamBar_hor ','volMuDownstreamBar_ver ']
   tunnel = sGeo.GetVolume('Tunnel')
   tunnel.SetVisibility(0)
   tunnel.SetVisDaughters(0)
   br = gEve.GetBrowser()
   br.SetWindowName('SND@LHC Eve Window')
   br.SetWidth(1600)
   sc    = gEve.GetScenes()
   geoscene = sc.FindChild('Geometry scene')
   gEve.ElementChanged(geoscene,True,True)

   v = gEve.GetDefaultGLViewer()
   camera = v.CurrentCamera()
   for i in range(2):  # don't know why this needs to be executed twice to update the screen
     camera.Reset()
     center = array('d',[-9.,46.,28.])
     camera.Configure(1.6, 0, center, -1.57, 0)
     v.DoDraw()

   trackTask.InitTask(sTree)

 def update(self):
   sc    = gEve.GetScenes()
   geoscene = sc.FindChild('Geometry scene')
   gEve.ElementChanged(geoscene,True,True)

 def NextEvent(self,i=-1):
   if i<0: self.n+=1
   else  : self.n=i
   fRun.Run(self.n,self.n+1) # go for first event
   if sTree.FindBranch("Digi_MuFilterHits") or sTree.FindBranch("Digi_ScifiHits"):
      self.digi.ExecuteTask()
   print('Event %i ready'%(self.n))
# make pointsets pickable
   if isMC:
     for x in mcHits: 
       p = ROOT.gEve.GetCurrentEvent().FindChild(mcHits[x].GetName())
       if p: 
         p.SetPickable(ROOT.kTRUE)
         p.SetTitle(p.__repr__())
 def rotateView(self,hor=0,ver=0):
  v   = ROOT.gEve.GetDefaultGLViewer()
  cam  = v.CurrentCamera()
  cam.Reset()
  if hor!=0 or ver!=0:
   cam.RotateRad(hor,ver)
  v.DoDraw()
 def topView(self):
  self.rotateView(ROOT.TMath.Pi()/2.,0.) # rotation around z axis
 def bottomView(self):
  self.rotateView(-ROOT.TMath.Pi()/2.,0.) # rotation around z axis
 def frontView(self):
  self.rotateView(0.,ROOT.TMath.Pi()/2.) # rotation around y or x axis
 def backView(self):
  self.rotateView(0.,-ROOT.TMath.Pi()/2.) # rotation around y or x axis
 def leftView(self):
  self.rotateView(0.,ROOT.TMath.Pi()) # rotation around y or x axis
 def rightView(self):
  self.rotateView(0.,ROOT.TMath.Pi()) # rotation around y or x axis
 def transparentMode(self,mode='on'):
   for m in transparentMaterials:
     mat = ROOT.gGeoManager.GetMaterial(m)
     if not mat:continue
     if mode.lower()=='on' or mode==1:
       mat.SetTransparency(transparentMaterials[m])
       vol = sGeo.FindVolumeFast('HorMatVolume')
       vol.SetTransparency(99)
       vol = sGeo.FindVolumeFast('VertMatVolume')
       vol.SetTransparency(99)
       self.TransparentMode = 1
     else: 
       mat.SetTransparency("\x00")
       self.TransparentMode = 0  
   self.update()
 def light(self,step=0.2,source='all'):
   v1 = gEve.GetDefaultViewer()
   gl  = v1.GetGLViewer()
   status = {}
   sources = ["Side","Front","Specular"]
   ls = gl.GetLightSet()
   for s in sources:
       exec("status['"+s+"']=ls.Get"+s+"Power()")
   if source!='all': sources = [source]
   for s in sources:
       newPw = str(status[s]+step)
       exec("ls.Set"+s+"Power("+newPw+")")
   self.update()
 def fittrack(self):
   trackTask.ExecuteTask()
   print('tracks found',len(sTree.fittedTracks) )
   self.tracks.DrawFittedTracks()

# add projections DOES NOT WORK YET AS FORESEEN, under investigation. 30.11.2016
def projection():
#if 1>0:
   # camera
   s = ROOT.gEve.SpawnNewScene("Projected Event")
   ROOT.gEve.GetDefaultViewer().AddScene(s)
   v = ROOT.gEve.GetDefaultGLViewer()
   v.SetCurrentCamera(ROOT.TGLViewer.kCameraOrthoXOY)
   cam = v.CurrentCamera()
   cam.SetZoomMinMax(0.2, 20)
   # projections
   mng = ROOT.TEveProjectionManager(ROOT.TEveProjection.kPT_RPhi)
   s.AddElement(mng)
   axes = ROOT.TEveProjectionAxes(mng)
   axes.SetTitle("TEveProjections demo")
   s.AddElement(axes)
   ROOT.gEve.AddToListTree(axes, ROOT.kTRUE)
   ROOT.gEve.AddToListTree(mng, ROOT.kTRUE)

def projection_prescale():
#if 1>0:
   v = gEve.GetViewers()
   vw = v.FindChild('Viewer 1')
   if vw: vw.SetName('3d')
   sev = ROOT.gEve.SpawnNewViewer("Scaled 2D")
   smng = ROOT.TEveProjectionManager(ROOT.TEveProjection.kPP_Plane)
   sp = smng.GetProjection()
   sp.SetUsePreScale(ROOT.kTRUE)
   sp.AddPreScaleEntry(2, 100000000.,  0.1)
   ss = ROOT.gEve.SpawnNewScene("Scaled Geom")
   sev.AddScene(ss)
   ss.AddElement(smng)
   N = sGeo.GetTopNode()
   TNod=ROOT.TEveGeoTopNode(sGeo, N, 1, 3, 10)
   ss.AddElement(TNod)
   eventscene = ROOT.gEve.SpawnNewScene('Scaled event')
   eventscene.AddElement(ROOT.FairEventManager.Instance())
   sev.AddScene(eventscene)
   eventscene.AddElement(smng)
   ROOT.gEve.GetBrowser().GetTabRight().SetTab(1)
   ROOT.gEve.FullRedraw3D(ROOT.kTRUE)

def storeCameraSetting(fname='camSetting.root'):
 f = ROOT.TFile.Open(fname, "RECREATE");
 cam  = ROOT.gEve.GetDefaultGLViewer().CurrentCamera()
 cam.Write()
 f.Close()
def readCameraSetting(fname='camSetting.root'):
 f = ROOT.TFile.Open(fname)
 cam  = ROOT.gEve.GetDefaultGLViewer().CurrentCamera()
 f.GetKey(cam.ClassName()).Read(cam)
 cam.IncTimeStamp()
 gEve.GetDefaultGLViewer().RequestDraw()
 f.Close()

# set display properties for tau nu target


def switchOf(tag):
 sc    = gEve.GetScenes()
 geoscene = sc.FindChild('Geometry scene')
 for v in top.GetNodes():
   vname = v.GetName()
   if not vname.find(tag)<0:
     v.SetVisibility(0)
     v.SetVisDaughters(0)
 gEve.ElementChanged(geoscene,True,True)

def switchOn(tag):
 sc    = gEve.GetScenes()
 geoscene = sc.FindChild('Geometry scene')
 for v in top.GetNodes():
   vname = v.GetName()
   if not vname.find(tag)<0:
     print('switch on ',vname)
     v.SetVisibility(1)
     v.SetVisDaughters(1)
 gEve.ElementChanged(geoscene,True,True)


def switchOfAll(exc):
 sc    = gEve.GetScenes()
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
 gEve.ElementChanged(geoscene,True,True)

def switchOnAll(exc):
 sc    = gEve.GetScenes()
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
 gEve.ElementChanged(geoscene,True,True) 

def select(pattern):
 exc = []
 for v in sGeo.GetListOfVolumes():
   vname = v.GetName()
   if not vname.find(pattern) < 0 : exc.append(vname)
 return exc

def search(lvdict,tag):
  for x in lvdict: 
   if not x.find(tag)<0: print(x)

#----Load the default libraries------
from basiclibs import *  
# -----   Reconstruction run   -------------------------------------------
fRun = ROOT.FairRunAna()

if options.geoFile: 
 if options.geoFile[0:4] == "/eos": options.geoFile=ROOT.gSystem.Getenv("EOSSHIP")+options.geoFile
 fRun.SetGeomFile(options.geoFile)

if options.InputFile[0:4] == "/eos": options.InputFile=ROOT.gSystem.Getenv("EOSSHIP")+options.InputFile
inFile = ROOT.FairFileSource(options.InputFile)

isMC = True
if inFile.GetInFile().FindKey('rawConv'):
   inFile.Close()
   print('set name rawConv')
   isMC = False
   configFolder = os.environ["VMCWORKDIR"]+"/config"
   if not os.path.isdir(configFolder): rc = os.mkdir(configFolder)
   tmp = open(os.environ["VMCWORKDIR"]+"/config/rootmanager.dat",'w')
   tmp.write("treename=rawConv")
   tmp.close()
   inFile = ROOT.FairFileSource(options.InputFile,'rawConv')
   # os.system("rm "+configFolder+"/rootmanager.dat")
fRun.SetSource(inFile)

if options.OutputFile == None:
  options.OutputFile = ROOT.TMemFile('event_display_output', 'recreate')
fRun.SetOutputFile(options.OutputFile)

if options.ParFile:
 rtdb      = fRun.GetRuntimeDb()
 parInput1 = ROOT.FairParRootFileIo()
 parInput1.open(options.ParFile)
 rtdb.setFirstInput(parInput1)
   
fMan= ROOT.FairEventManager()
fMan.SetMaxEnergy(5000.) # default is 25 GeV only !
fMan.SetMinEnergy(0.1) #  100 MeV
fMan.SetEvtMaxEnergy(5000.) # what is the difference between EvtMaxEnergy and MaxEnergy ?
fMan.SetPriOnly(False)  # display everything

upkl    = Unpickler( fRun.GetGeoFile() )
ShipGeo = upkl.load('ShipGeo')

# -----Create geometry----------------------------------------------
import shipLHC_conf as sndDet_conf
modules = sndDet_conf.configure(fRun,ShipGeo)

if isMC:
   mcHits = {}
   mcHits['MuFilterPoints']  = ROOT.FairMCPointDraw("MuFilterPoint", ROOT.kBlue, ROOT.kFullSquare)  
   mcHits['ScifiPoints']  = ROOT.FairMCPointDraw("ScifiPoint", ROOT.kGreen, ROOT.kFullCircle)
   mcHits['EmulsionDetPoints'] = ROOT.FairMCPointDraw("EmulsionDetPoint", ROOT.kMagenta, ROOT.kFullDiamond)
   for x in mcHits: fMan.AddTask(mcHits[x])

fMan.Init(1,4,10) # default Init(visopt=1, vislvl=3, maxvisnds=10000)
#visopt, set drawing mode :
# option=0 (default) all nodes drawn down to vislevel
# option=1           leaves and nodes at vislevel drawn
# option=2           path is drawn
# vislvl
#
fRman = ROOT.FairRootManager.Instance()
sTree = fRman.GetInChain()
lsOfGlobals = ROOT.gROOT.GetListOfGlobals()
lsOfGlobals.Add(sTree)
lsOfGlobals.Add(modules['Scifi'])
lsOfGlobals.Add(modules['MuFilter'])

sGeo  = ROOT.gGeoManager 
top   = sGeo.GetTopVolume()
gEve  = ROOT.gEve

br = gEve.GetBrowser()
br.HideBottomTab() # make more space for graphics
br.SetWindowName('SND@LHC Eve Window')

SHiPDisplay = EventLoop()
import eveGlobal
eveGlobal.SHiPDisplay = SHiPDisplay
SHiPDisplay.SetName('SHiP Displayer')
lsOfGlobals.Add(SHiPDisplay) 

import SndlhcTracking
trackTask = SndlhcTracking.Tracking() 

SHiPDisplay.InitTask()

print('Help on GL viewer can be found by pressing Help button followed by help on GL viewer')
print('With the camera button, you can switch to different views.')
# short cuts
# w go to wire frame
# r smooth display
# t technical display
# e black<->white background
# j zoom in 
# k zoom out
# d GL debug mode

def DrawSimpleMCTracks():
  comp = SHiPDisplay.tracks.comp
  comp.OpenCompound()
  n = -1
  ntot = 0
  fPos = ROOT.TVector3()
  fMom = ROOT.TVector3()
  delZ = 10*u.m
  for fT in sTree.MCTrack:
   n+=1
   DTrack = ROOT.TEveLine()
   DTrack.SetPickable(ROOT.kTRUE)
   DTrack.SetTitle(fT.__repr__())
   fT.GetStartVertex(fPos)
   fT.GetMomentum(fMom)
   hitlist = {}
   hitlist[fPos.Z()] = [fPos.X(),fPos.Y()]
   z = fPos.Z() + delZ
   slx,sly = fMom.X()/fMom.Z(),fMom.Y()/fMom.Z()
   hitlist[z] = [fPos.X()+slx*delZ,fPos.Y()+sly*delZ]
   for z in hitlist.keys():
    DTrack.SetNextPoint(hitlist[z][0],hitlist[z][1],z)
   p = pdg.GetParticle(fT.GetPdgCode()) 
   if p : pName = p.GetName()
   else:  pName =  str(fT.GetPdgCode())
   DTrack.SetName('MCTrack_'+str(n)+'_'+pName)
   c = ROOT.kYellow
   DTrack.SetMainColor(c)
   DTrack.SetLineWidth(3)
   comp.AddElement(DTrack)
   ntot+=1
  comp.CloseCompound()
  gEve.ElementChanged(SHiPDisplay.tracks.evscene,True,True)




