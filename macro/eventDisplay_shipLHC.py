#!/usr/bin/env python -i
from __future__ import print_function
from __future__ import division
from future import standard_library
standard_library.install_aliases()
import ROOT,sys,os,tkinter,atexit
from argparse import ArgumentParser
from ShipGeoConfig import ConfigRegistry
from rootpyPickler import Unpickler
from array import array
import shipunit as u
from decorators import *
import shipRoot_conf,shipLHC_conf
shipRoot_conf.configure()

def evExit():
 if ROOT.gROOT.FindObject('Root Canvas EnergyLoss'):
  print("make suicide before framework makes seg fault") 
  os.kill(os.getpid(),9)
# apperantly problem disappeared in more recent root versions
if float(ROOT.gROOT.GetVersion().split('/')[0])>6.07: atexit.register(evExit)

fMan = None
fRun = None
pdg  = ROOT.TDatabasePDG.Instance()
g    = ROOT.gROOT 
gEnv = ROOT.gEnv
gEnv.SetValue('Eve.Viewer.HideMenus','off')

mcEngine   = "TGeant4"
simEngine  = "Pythia8"
withGeo    = False
withMCTracks = True

#                        muon shield  strawtube                     decay vessel  
transparentMaterials = {'iron':80,'aluminium':80,'mylar':60,'STTmix9010_2bar':95,'steel':80,'Aluminum':80,'Scintillator':80,
#                        tau nu detector  
                        'CoilCopper':70,'copper':90,'HPTgas':70,'Bakelite':70,'RPCgas':70,
#                        charm detector  
                        'CoilAluminium':70,'molybdenum':80,'PlasticBase':70,'tantalum':70}
#

parser = ArgumentParser()

parser.add_argument("-f", "--inputFile",    dest="InputFile", help="Input file", required=True)
parser.add_argument("-g", "--geoFile",      dest="geoFile",   help="ROOT geofile", required=True)
parser.add_argument("-p", "--paramFile",    dest="ParFile",   help="FairRoot param file", required=False, default=None)
parser.add_argument("--Debug",              dest="Debug", help="Switch on debugging", required=False, action="store_true")
parser.add_argument("-o", "--outFile",      dest="OutputFile", help="Output file", required=False,default=None)
parser.add_argument("-i",                   dest="HiddenParticleID", help="HiddenParticle ID", required=False,default=9900015)

options = parser.parse_args()
if options.InputFile.find('_D')>0: withGeo = True

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
def printFittedTracks():
  print('  # converged Ndf chi2/Ndf    P      Pt      MCid')
  n=-1
  for ft in sTree.FitTracks:
   n+=1
   fitStatus = ft.getFitStatus()
   fitState  = ft.getFittedState()
   mom = fitState.getMom()
   print('%3i %6i   %4i %6.3F   %6.3F %6.3F %6i '%(n,fitStatus.isFitConverged(),\
            fitStatus.getNdf(),fitStatus.getChi2()/fitStatus.getNdf(),\
            mom.Mag()/u.GeV,mom.Pt()/u.GeV,sTree.fitTrack2MC[n] ))
def printParticles():
  print('  #    P    Pt[GeV/c]   DOCA[mm]    Rsq    Vz[m]    d1    d2')
  n=-1
  for aP in sTree.Particles:
   n+=1
   doca = -1.
   if aP.GetMother(1)==99: # DOCA is set
      doca = aP.T()
   Rsq = (aP.Vx()/(2.45*u.m) )**2 + (aP.Vy()/((10./2.-0.05)*u.m) )**2
   print('%3i %6.3F  %6.3F  %9.3F    %6.3F   %6.3F %4i  %4i '%(n,aP.P()/u.GeV,aP.Pt()/u.GeV,\
            doca/u.mm,Rsq,aP.Vz()/u.m,aP.GetDaughter(0),aP.GetDaughter(1) ))

class DrawTracks(ROOT.FairTask):
 " My Fair Task"
 def InitTask(self):
# prepare container for fitted tracks
  self.comp  = ROOT.TEveCompound('Tracks')
  gEve.AddElement(self.comp)
  self.trackColors = {13:ROOT.kGreen,211:ROOT.kRed,11:ROOT.kOrange,321:ROOT.kMagenta}
  self.z_start = 0
  sc    = gEve.GetScenes()
  self.evscene = sc.FindChild('Event scene')
 
 def FinishEvent(self):
  pass
 def ExecuteTask(self,option=''):
  self.comp.DestroyElements()
  self.comp.OpenCompound()
  if sTree.FindBranch('FitTracks') or sTree.FindBranch('FitTracks_PR'):
   if sTree.FitTracks.GetEntries() > 0: 
     self.DrawFittedTracks()
  if not sTree.FindBranch("GeoTracks") and sTree.MCTrack.GetEntries() > 0: 
    if globals()['withMCTracks']: 
       self.DrawMCTracks()
       #self.DrawSimpleMCTracks()
  self.comp.CloseCompound()
  gEve.ElementChanged(self.evscene,True,True)
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
   for P in ["EmulsionDetPoint","ScifiPoint"]:
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
 def DrawSimpleMCTracks(self):
  comp = self.comp
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
    rc,newpos,newmom = TrackExtrapolateTool.extrapolateToPlane(fT,zs)
    if rc:
      DTrack.SetNextPoint(newpos.X(),newpos.Y(),newpos.Z())
    else: 
      print('error with extrapolation: z=',zs)
      # use linear extrapolation
      px,py,pz  = mom.X(),mom.Y(),mom.Z() 
      lam = (zs-pos.Z())/pz
      DTrack.SetNextPoint(pos.X()+lam*px,pos.Y()+lam*py,zs)
    zs+=self.dz
   DTrack.SetName('FitTrack_'+str(n))
   c = ROOT.kWhite
   if abs(pid) in self.trackColors : c = self.trackColors[abs(pid)]
   DTrack.SetMainColor(c)
   DTrack.SetLineWidth(3)
   self.comp.AddElement(DTrack)
   ntot+=1
  print("draw ",ntot," fitted tracks")
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
import evd_fillEnergy
class IO():
    def __init__(self):
        self.master = tkinter.Tk()
        self.master.title('SHiP Event Display GUI')
        self.master.geometry(u'320x580+165+820')  
        self.fram1 = tkinter.Frame(self.master)
        b = tkinter.Button(self.fram1, text="Next Event",command=self.nextEvent)
        b.pack(fill=tkinter.BOTH, expand=1) 
        label = tkinter.Label(self.fram1, text='Event number:')
        label["relief"] = tkinter.RAISED
        entry = tkinter.Entry(self.fram1)
        entry["foreground"] = "blue"
        label.pack(side=tkinter.LEFT)
        entry.pack(side=tkinter.RIGHT)
        self.contents = tkinter.IntVar()
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
        a = tkinter.IntVar()
        if globals()['withMCTracks']: a.set(1)
        else: a.set(0)
        self.lbut[x] = tkinter.Checkbutton(self.master,text="with MC Tracks",compound=tkinter.LEFT,variable=a)
        self.lbut[x].var = a
        self.lbut[x]['command'] = self.toogleMCTracks
        self.lbut[x].pack(side=tkinter.TOP)
        self.geoscene = ROOT.gEve.GetScenes().FindChild("Geometry scene")
        for v in top.GetNodes():
         x=v.GetName()
         cmd = 'toogle("'+x+'")' 
         a = tkinter.IntVar()
         assemb = "Assembly" in v.GetVolume().__str__() 
         if v.IsVisible() or (assemb and v.IsVisDaughters()): a.set(1)
         else : a.set(0)
         self.lbut[x]  = tkinter.Checkbutton(self.master,text=x.replace('_1',''),compound=tkinter.LEFT,variable=a)
         self.lbut[x].var = a
         self.lbut[x]['command'] = lambda j=x: self.toogle(j)
         self.lbut[x].pack(side=tkinter.BOTTOM)
        self.fram1.pack()
# add ship actions to eve display
        gEve = ROOT.gEve
        slot = ROOT.TEveWindow.CreateWindowInTab(gEve.GetBrowser().GetTabLeft())
        slot.SetShowTitleBar(ROOT.kFALSE)
        packs = slot.MakePack();
        packs.SetShowTitleBar(ROOT.kFALSE);
        packs.SetElementName("SHiP actions")
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
        b = ROOT.TGTextButton(guiFrame, "Add particle follower")
        b.SetWidth(150)
        b.SetToolTipText('start new window with top projection and energy loss')
        b.SetCommand('TPython::ExecScript("'+os.environ['FAIRSHIP']+'/macro/evd_addParticleFollower.py")')
        guiFrame.AddFrame(b, ROOT.TGLayoutHints(ROOT.kLHintsExpandX))
        bn = ROOT.TGTextButton(guiFrame, "fill histogram")
        bn.SetWidth(150)
        bn.SetToolTipText('Fill histogram with energy along flight path')
        bn.SetCommand('TPython::ExecScript("'+os.environ['FAIRSHIP']+'/macro/evd_fillEnergy.py")')
        guiFrame.AddFrame(bn, ROOT.TGLayoutHints(ROOT.kLHintsExpandX))
        bt = ROOT.TGTextButton(guiFrame, "switch transparent mode on/off")
        bt.SetWidth(150)
        bt.SetToolTipText('switch transparent mode on/off for better visibility of tracks')
        bt.SetCommand('TPython::ExecScript("'+os.environ['FAIRSHIP']+'/macro/evd_transparentMode.py")')
        guiFrame.AddFrame(bt, ROOT.TGLayoutHints(ROOT.kLHintsExpandX))
        bnx = ROOT.TGTextButton(guiFrame, "next event")
        bnx.SetWidth(150)
        bnx.SetToolTipText('click for next event')
        bnx.SetCommand('TPython::ExecScript("'+os.environ['FAIRSHIP']+'/macro/evd_nextEvent.py")')
        guiFrame.AddFrame(bnx, ROOT.TGLayoutHints(ROOT.kLHintsExpandX))
        bzt = ROOT.TGTextButton(guiFrame, "synch zoom top->side")
        bzt.SetWidth(150)
        bzt.SetToolTipText('synchronize zoom top with side')
        bzt.SetCommand('TPython::ExecScript("'+os.environ['FAIRSHIP']+'/macro/evd_synchZoomt.py")')
        guiFrame.AddFrame(bzt, ROOT.TGLayoutHints(ROOT.kLHintsExpandX))
        bzs = ROOT.TGTextButton(guiFrame, "synch zoom side->top")
        bzs.SetWidth(150)
        bzs.SetToolTipText('synchronize zoom side with top')
        bzs.SetCommand('TPython::ExecScript("'+os.environ['FAIRSHIP']+'/macro/evd_synchZooms.py")')
        guiFrame.AddFrame(bzs, ROOT.TGLayoutHints(ROOT.kLHintsExpandX))
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
   if sGeo.GetVolume('EmulsionDet'): DisplayNuDetector()
   self.tracks = DrawTracks()
   self.tracks.InitTask()
# create SHiP GUI
   self.ioBar = IO()
   self.TransparentMode = 0
   v1 = gEve.GetDefaultViewer()
   v1.GetEveFrame().HideAllDecorations()
   tr=gEve.GetBrowser().GetTabRight()
   t0 = tr.GetTabTab(0)
   t0.SetText(ROOT.TGString('3D'))
 def NextEvent(self,i=-1):
   if i<0: self.n+=1
   else  : self.n=i
   fRun.Run(self.n,self.n+1) # go for first event
# check if tracks are made from real pattern recognition
   if sTree.GetBranch("FitTracks_PR"):    sTree.FitTracks = sTree.FitTracks_PR
   if sTree.GetBranch("fitTrack2MC_PR"):  sTree.fitTrack2MC = sTree.fitTrack2MC_PR
   if sTree.GetBranch("Particles_PR"):    sTree.Particles   = sTree.Particles_PR
   if hasattr(self,"tracks"): self.tracks.ExecuteTask()
   if ROOT.gROOT.FindObject('Root Canvas EnergyLoss'): evd_fillEnergy.execute()
   print('Event %i ready'%(self.n))
# make pointsets pickable
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
       self.TransparentMode = 1
     else: 
       mat.SetTransparency("\x00")
       self.TransparentMode = 0  
   sc    = gEve.GetScenes()
   geoscene = sc.FindChild('Geometry scene')
   if geoscene:   gEve.ElementChanged(geoscene,True,True)
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
def speedUp():
 for x in ["wire","gas","rockD","rockS","rockSFe"]:  
   xvol = sGeo.GetVolume(x)
   if xvol: xvol.SetVisibility(0) 
 for k in range(1,7):
     va = sGeo.GetVolume("T"+str(k))
     if not va: continue
     for x in va.GetNodes():
       nm = x.GetName()
       if not nm.find("Inner")<0 and k < 3: 
          x.SetVisDaughters(False)
          x.SetVisibility(False)
       if not nm.find("LiSc")<0: x.SetVisDaughters(False)
       if not nm.find("RibPhi")<0: x.SetVisDaughters(False)
# 
 for x in ["Ecal","Hcal"]:
  xvol = sGeo.GetVolume(x)
  if not xvol: continue
  xvol.SetVisDaughters(0)
  xvol.SetVisibility(1)
  if x=="Ecal": xvol.SetLineColor(ROOT.kYellow) 
  else:        xvol.SetLineColor(ROOT.kOrange+3) 

# set display properties for tau nu target
def DisplayNuDetector():
 for x in ["Wall"]:
  xvol = sGeo.GetVolume(x)
  if not xvol: continue
  xvol.SetVisDaughters(0)
  xvol.SetVisibility(1)
 sc    = gEve.GetScenes()
 geoscene = sc.FindChild('Geometry scene')
 gEve.ElementChanged(geoscene,True,True)
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

# switch of drawing of rock
def switchOfRock():
 sc    = gEve.GetScenes()
 geoscene = sc.FindChild('Geometry scene')
 for x in [ 'rockD', 'rockS']:
  v = sGeo.FindVolumeFast(x)
  v.SetVisibility(0)
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
  gEve.AddElement(self.ruler)
 def show(self,xy=0,ticks=5):
  self.ruler.DestroyElements()
  self.ruler.OpenCompound()
  xpos,ypos = -500., -1500.
  zstart  = ShipGeo.target.z0
  zlength = ShipGeo.MuonStation3.z - zstart + 10*u.m
  a1 = ROOT.TEveLine()
  a1.SetNextPoint(xpos,ypos, zstart)
  a1.SetNextPoint(xpos,ypos, zstart+zlength)
  a1.SetMainColor(ROOT.kAzure-9)
  a1.SetLineWidth(30)
  #self.ruler.AddElement(a1)
  z=zstart
  for i in range(int(zlength/100/ticks)):
   m = ROOT.TEveLine()
   m.SetNextPoint(xpos,ypos, z)
   m.SetNextPoint(xpos-1*u.m,ypos,z)
   m.SetMainColor(ROOT.kRed)
   m.SetLineWidth(5)
   self.ruler.AddElement(m)
   t1 = ROOT.TEveText(str(i*ticks)+'m')
   t1.SetMainColor(ROOT.kGray+3)
   t1.SetFontSize(5)
   t1.RefMainTrans().SetPos(xpos-0.1*u.m,ypos+0.2*u.m,z)
   self.ruler.AddElement(t1)
   z+=ticks*u.m
  xpos,ypos = 0., 0.
  if xy==0:  z = ShipGeo.MuonStation3.z+6*u.m
  else: z=xy 
  ylength = 7*u.m
  a2 = ROOT.TEveLine()
  a2.SetNextPoint(xpos,-ylength, z)
  a2.SetNextPoint(xpos,ylength, z)
  a2.SetMainColor(ROOT.kAzure-9)
  a2.SetLineWidth(30)
  #self.ruler.AddElement(a2)
  ypos=-ylength
  for i in range(-int(ylength/100),int(ylength/100),1):
   m = ROOT.TEveLine()
   m.SetNextPoint(xpos,ypos, z)
   m.SetNextPoint(xpos+0.05*u.m,ypos,z)
   m.SetMainColor(ROOT.kRed)
   m.SetLineWidth(3)
   self.ruler.AddElement(m)
   t1 = ROOT.TEveText(str(i)+'m')
   t1.SetMainColor(ROOT.kGray+3)
   t1.SetFontSize(5)
   t1.RefMainTrans().SetPos(xpos-0.5*u.m,ypos,z)
   self.ruler.AddElement(t1)
   ypos+=1*u.m
  ty = ROOT.TEveText("y-axis")
  ty.SetFontSize(10)
  ty.RefMainTrans().SetPos(0.,ypos+1*u.m,z)
  ty.SetMainColor(ROOT.kRed-2)
  self.ruler.AddElement(ty)
  xpos,ypos = 0., 0.
  if xy==0:  z = ShipGeo.MuonStation3.z+10*u.m
  xlength = 3*u.m
  a3 = ROOT.TEveLine()
  a3.SetNextPoint(-xlength,0, z)
  a3.SetNextPoint(xlength,0, z)
  a3.SetMainColor(ROOT.kAzure-9)
  a3.SetLineWidth(30)
  #self.ruler.AddElement(a3)
  xpos=-xlength
  for i in range(-int(xlength/100),int(xlength/100),1):
   m = ROOT.TEveLine()
   m.SetNextPoint(xpos,ypos, z)
   m.SetNextPoint(xpos,ypos-0.05*u.m,z)
   m.SetMainColor(ROOT.kRed)
   m.SetLineWidth(3)
   self.ruler.AddElement(m)
   t1 = ROOT.TEveText(str(i)+'m')
   t1.SetMainColor(ROOT.kGray+3)
   t1.SetFontSize(5)
   t1.RefMainTrans().SetPos(xpos,ypos-0.1*u.m,z)
   self.ruler.AddElement(t1)
   xpos+=1*u.m 
  tx = ROOT.TEveText("x-axis")
  tx.SetFontSize(10)
  tx.RefMainTrans().SetPos(xpos+1*u.m,0.,z)
  tx.SetMainColor(ROOT.kRed-2)
  self.ruler.AddElement(tx)
  t1 = ROOT.TEveText("SHiP")
  t1.SetFontSize(200)
  t1.RefMainTrans().SetPos(0.,600.,ShipGeo.TrackStation1.z-10*u.m)
  t1.PtrMainTrans().RotateLF(1, 3, ROOT.TMath.PiOver2())
  t1.SetMainColor(ROOT.kOrange-2)
  t1.SetFontMode(ROOT.TGLFont.kExtrude)
  t1.SetLighting(ROOT.kTRUE)
  self.ruler.AddElement(t1)
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
    print('xyz E pxpypz',gTr.GetPoint(0)[0],gTr.GetPoint(0)[1] ,gTr.GetPoint(0)[2],lorv.E(),lorv.Px(),lorv.Py(),lorv.Pz())
# Loop over MC tracks  
 for i in range( min(5,nev) ) :
   t.GetEntry(i)
   for gMCTr in t.MCTrack: 
    gMCTr.Print()
    print(gMCTr.GetPdgCode(),gMCTr.GetMass(),gMCTr.GetP())
# MC event header  
 for i in range( nev ) :
   t.GetEntry(i)
   print(t.MCEventHeader.GetEventID(),t.MCEventHeader.GetRunID(),t.MCEventHeader.GetZ())
# geometrie
 sGeo = ROOT.gGeoManager
 cave = sGeo.GetTopVolume()
 cave.Draw('ogl')
# eve
 gEve = ROOT.gEve
#
 sc    = gEve.GetScenes()
 geoscene = sc.FindChild('Geometry scene')
 topnode  = geoscene.FindChild('cave_1')
 topnode.SetVisLevel(4)
 gEve.ElementChanged(geoscene,True,True)
def debugStraw(n):
 sGeo = ROOT.gGeoManager  
 vols = sGeo.GetListOfVolumes()
 sTree = g.FindObjectAny('cbmsim')
 sTree.GetEntry(n)
 for s in sTree.strawtubesPoint:
  print(vols[s.GetDetectorID()-1].GetName())


#----Load the default libraries------
from basiclibs import *  
# -----   Reconstruction run   -------------------------------------------
fRun = ROOT.FairRunAna()
if options.geoFile: 
 if options.geoFile[0:4] == "/eos": options.geoFile=ROOT.gSystem.Getenv("EOSSHIP")+options.geoFile
 fRun.SetGeomFile(options.geoFile)

if options.InputFile[0:4] == "/eos": options.InputFile=ROOT.gSystem.Getenv("EOSSHIP")+options.InputFile
if hasattr(fRun,'SetSource'):
 inFile = ROOT.FairFileSource(options.InputFile)
 fRun.SetSource(inFile)
else:
 fRun.SetInputFile(options.InputFile)
if options.OutputFile == None:
  options.OutputFile = ROOT.TMemFile('event_display_output', 'recreate')
fRun.SetOutputFile(options.OutputFile)

if options.ParFile:
 rtdb      = fRun.GetRuntimeDb()
 parInput1 = ROOT.FairParRootFileIo()
 parInput1.open(options.ParFile)
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

if not fRun.GetGeoFile().FindKey('ShipGeo'):
 # old geofile, missing Shipgeo dictionary
 # try to figure out which ecal geo to load
  ShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", Yheight = float(dy), EcalGeoFile = ecalGeoFile)
else: 
 # new geofile, load Shipgeo dictionary written by run_simScript.py
  upkl    = Unpickler( fRun.GetGeoFile() )
  ShipGeo = upkl.load('ShipGeo')

mcHits = {}
mcHits['EmulsionDetPoints']  = ROOT.FairMCPointDraw("EmulsionDetPoint", ROOT.kGreen, ROOT.kFullSquare)
mcHits['ScifiPoints']  = ROOT.FairMCPointDraw("ScifiPoint", ROOT.kBlue, ROOT.kFullSquare)
mcHits['MuFilterPoints']  = ROOT.FairMCPointDraw("MuFilterPoint", ROOT.kRed, ROOT.kFullSquare)

for x in mcHits: fMan.AddTask(mcHits[x])

fMan.Init(1,4,10) # default Init(visopt=1, vislvl=3, maxvisnds=10000), ecal display requires vislvl=4
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
sGeo  = ROOT.gGeoManager 
top   = sGeo.GetTopVolume()
# manipulate colors and transparency before scene created
speedUp()
gEve  = ROOT.gEve

geoMat =  ROOT.genfit.TGeoMaterialInterface()
ROOT.genfit.MaterialEffects.getInstance().init(geoMat)
fM = ROOT.genfit.FieldManager.getInstance()
#fM.init(bfield)

import TrackExtrapolateTool
br = gEve.GetBrowser()
br.HideBottomTab() # make more space for graphics
br.SetWindowName('SHiP Eve Window')

#switchOf('RockD')
if sGeo.FindVolumeFast('T2LiSc'): hidePlasticScintillator()
rulers = Rulers()
SHiPDisplay = EventLoop()
SHiPDisplay.SetName('SHiP Displayer')
lsOfGlobals.Add(SHiPDisplay) 
SHiPDisplay.InitTask()
#DrawSimpleMCTracks()
# SHiPDisplay.NextEvent(0)

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

# fGeo.SetNsegments(10) # can help a bit in case of performance problems
def DrawCharmTracks():
  i = -1
  for aTrack in sTree.MCTrack:
    i+=1
    if i<2: continue
    if aTrack.GetMotherId()==1:
      pa = pdg.GetParticle(sTree.MCTrack[i] .GetPdgCode())
      if pa.Lifetime()>1.E-12: 
       print(sTree.MCTrack[i])
       SHiPDisplay.tracks.DrawMCTrack(i)

def DrawMuonTrack():
  i = -1
  for aTrack in sTree.MCTrack:
    i+=1
    if abs(aTrack.GetPdgCode())==13:
      print(sTree.MCTrack[i])
      SHiPDisplay.tracks.DrawMCTrack(i)

def positionText(r,x,y,z,angle,txt,size=200,color=ROOT.kBlue,mode=ROOT.TGLFont.kExtrude,light=ROOT.kTRUE):
 tt = ROOT.TEveText(txt)
 tt.SetFontSize(size)
 tt.RefMainTrans().SetPos(x,y,z)
 tt.PtrMainTrans().RotateLF(1, 3, angle)
 tt.SetMainColor(color)
 tt.SetFontMode(mode)
 tt.SetLighting(light)
 r.AddElement(tt)
def PRVersion():
 readCameraSetting()
 for x in ['moreShieldingSide', 'moreShieldingTopBot','CoatWall','CoatVol','AbsorberVol']:
  vol = ROOT.gGeoManager.FindVolumeFast(x)
  vol.SetVisibility(0)
 ROOT.gGeoManager.GetMaterial('Concrete').SetTransparency(0)
 r = rulers.ruler
 ticks = 5
 r.DestroyElements()
 r.OpenCompound()
 xpos,ypos = -500., -1500.
 zstart  = ShipGeo.target.z0
 zlength = ShipGeo.MuonStation3.z - zstart + 10*u.m
 z=zstart
 for i in range(int(zlength/100/ticks)):
   m = ROOT.TEveLine()
   m.SetNextPoint(xpos,ypos, z)
   m.SetNextPoint(xpos-1*u.m,ypos,z)
   m.SetMainColor(ROOT.kRed)
   m.SetLineWidth(5)
   r.AddElement(m)
   t1 = ROOT.TEveText(str(i*ticks)+'m')
   t1.SetMainColor(ROOT.kGray+3)
   t1.SetFontSize(5)
   t1.RefMainTrans().SetPos(xpos-0.1*u.m,ypos+0.2*u.m,z)
   r.AddElement(t1)
   z+=ticks*u.m
 xpos,ypos = 0., 0.
 z = ShipGeo.MuonStation3.z+6*u.m
 ylength = 7*u.m
 ypos=-ylength
 for i in range(-int(ylength/100),int(ylength/100),1):
   m = ROOT.TEveLine()
   m.SetNextPoint(xpos,ypos, z)
   m.SetNextPoint(xpos+0.05*u.m,ypos,z)
   m.SetMainColor(ROOT.kRed)
   m.SetLineWidth(3)
   r.AddElement(m)
   t1 = ROOT.TEveText(str(i)+'m')
   t1.SetMainColor(ROOT.kGray+3)
   t1.SetFontSize(5)
   t1.RefMainTrans().SetPos(xpos-0.5*u.m,ypos,z)
   r.AddElement(t1)
   ypos+=1*u.m
 ty = ROOT.TEveText("y-axis")
 ty.SetFontSize(10)
 ty.RefMainTrans().SetPos(0.,ypos+1*u.m,z)
 ty.SetMainColor(ROOT.kRed-2)
 r.AddElement(ty)
 xpos,ypos = 0., 0.
 z = ShipGeo.MuonStation3.z+10*u.m
 xlength = 3*u.m
 xpos=-xlength
 for i in range(-int(xlength/100),int(xlength/100),1):
   m = ROOT.TEveLine()
   m.SetNextPoint(xpos,ypos, z)
   m.SetNextPoint(xpos,ypos-0.05*u.m,z)
   m.SetMainColor(ROOT.kRed)
   m.SetLineWidth(3)
   r.AddElement(m)
   t1 = ROOT.TEveText(str(i)+'m')
   t1.SetMainColor(ROOT.kGray+3)
   t1.SetFontSize(5)
   t1.RefMainTrans().SetPos(xpos,ypos-0.1*u.m,z)
   r.AddElement(t1)
   xpos+=1*u.m 
 tx = ROOT.TEveText("x-axis")
 tx.SetFontSize(10)
 tx.RefMainTrans().SetPos(xpos+1*u.m,0.,z)
 tx.SetMainColor(ROOT.kRed-2)
 r.AddElement(tx)
 rotAngle = ROOT.TMath.Pi()+ROOT.TMath.PiOver2()*5./2.
 positionText(r,0.,900.,ShipGeo.TrackStation1.z-20*u.m,rotAngle,"SHiP",200,ROOT.kOrange-2)
 positionText(r,0.,750.,ShipGeo.TrackStation1.z-40*u.m,rotAngle,"Vacuum decay vessel",200,ROOT.kGray+1)
 positionText(r,0.,100.,ShipGeo.target.z-6*u.m,rotAngle,"Target",200,ROOT.kBlue)
 positionText(r,0.,600.,ShipGeo.muShield.z-10*u.m,rotAngle,"Active muon shield",200,ROOT.kGreen-2)
 positionText(r,0.,600.,ShipGeo.tauMudet.zMudetC-10*u.m,rotAngle,"Tau neutrino detector",200,ROOT.kRed-2)
 positionText(r,0.,900.,ShipGeo.Bfield.z-5*u.m,rotAngle,"Dipole Magnet",200,ROOT.kBlue+2)
 positionText(r,-1500.,-800.,ShipGeo.TrackStation3.z-2*u.m,rotAngle,"Strawtracker",200,ROOT.kRed+2)
 positionText(r,0.,730.,ShipGeo.ecal.z-1*u.m,rotAngle,"Ecal",200,ROOT.kOrange)
 positionText(r,0.,700.,ShipGeo.MuonFilter2.z,rotAngle,"Muon",200,ROOT.kGreen+2)
 r.CloseCompound()
 sc    = gEve.GetScenes()
 geoscene = sc.FindChild('Geometry scene')
 gEve.ElementChanged(geoscene,True,True)


