import ROOT
import shipunit as u

def execute():
 canvas = ROOT.gROOT.FindObject('Root Canvas EnergyLoss')
 if not canvas:
  print "add particle flower not started!"
  return
 else:
  lsOfGlobals = ROOT.gROOT.GetListOfGlobals()
  sTree = lsOfGlobals.FindObject('cbmsim')
  c1 = canvas.cd(1)
  c1.Clear()
# collect hits
  fPos = ROOT.TVector3()
  fMom = ROOT.TVector3()
  nTrack=1
  fT   = sTree.MCTrack[nTrack]
  fT.GetStartVertex(fPos)
  hitlist = {}
  hitlist[fPos.Z()] = [fPos.X(),fPos.Y(),fT.GetP()]
# loop over all sensitive volumes to find hits
  n=0
  for P in ["vetoPoint","muonPoint","EcalPoint","HcalPoint","preshowerPoint","strawtubesPoint","ShipRpcPoint","TargetPoint"]:
    if not sTree.GetBranch(P): continue
    c=eval("sTree."+P)
    for p in c:
      if p.GetTrackID()==nTrack:
       p.Momentum(fMom)
       if hasattr(p, "LastPoint"): 
        lp = p.LastPoint()
        if lp.x()==lp.y() and lp.x()==lp.z() and lp.x()==0: 
# must be old data, don't expect hit at 0,0,0  
         hitlist[p.GetZ()] = [p.GetX(),p.GetY(),fMom.Mag()]
        else:   
         hitlist[lp.z()] = [lp.x(),lp.y(),p.LastMom().Mag()] 
         hitlist[2.*p.GetZ()-lp.z()] = [2.*p.GetX()-lp.x(),2.*p.GetY()-lp.y(),fMom.Mag()] 
       else:
        hitlist[p.GetZ()] = [p.GetX(),p.GetY(),fMom.Mag()]
      n+=1
  if len(hitlist)==1:
    zEx = 50*u.m
    fT.GetMomentum(fMom)
    lam = (zEx+fPos.Z())/fMom.Z()
    hitlist[zEx+fPos.Z()] = [fPos.X()+lam*fMom.X(),fPos.Y()+lam*fMom.Y(),fMom.Mag()]
# sort in z
  lz = hitlist.keys()
  lz.sort()
  traj = lsOfGlobals.FindObject('SHiP MuonTraj')
  if not traj:
    traj = ROOT.TGraph()
    traj.SetName('SHiP MuonTraj')
    traj.SetLineWidth(2)
    lsOfGlobals.Add(traj) 
  traj.Set(0)
  SHiPDisplay = lsOfGlobals.FindObject('SHiP Displayer')
# get zmin, zmax from graphic
  v = ROOT.gEve.GetViewers().FindChild('Bar Embedded Viewer ZnOX')
  vw = v.GetGLViewer()
  cam = vw.CurrentCamera()
  ed = v.GetEditorObject()
  co = ed.GetCameraOverlay()
  ax = co.GetAttAxis() 
  fr = vw.GetFrame()
  test = ROOT.TGLVertex3(0.,0.,0.)
  vtest = cam.ViewportToWorld(test)
  zmin = vtest.Z()
  test = ROOT.TGLVertex3(fr.GetWidth(),0.,0.)
  vtest = cam.ViewportToWorld(test)
  zmax = vtest.Z()
#
  emin,emax = 1E9,-1E9
  n=0 
  for z in lz:  
   E = hitlist[z][2]
   traj.SetPoint(n,z,E)
   if E>emax:emax=E
   if E<emin:emin=E
   n+=1
  emin,emax = emin*0.9,emax*1.1
  hist = c1.DrawFrame(zmin,emin,zmax,emax)
  hist.SetYTitle('p (GeV/c)')
  hist.SetXTitle('z cm')
  xaxis=hist.GetXaxis()
  xaxis.SetNdivisions(ax.GetNdivisions())
  traj.Draw()
  txt = ROOT.TLatex()
  txt.DrawLatexNDC(0.6,0.8,'event index:'+str(SHiPDisplay.n))
  c1.Update()
if __name__=="__main__":
  execute()
