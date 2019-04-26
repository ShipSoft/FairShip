import ROOT
import shipunit as u


def collect_hits(lsOfGlobals, checked_muons):
  MUON = 13
  sTree = lsOfGlobals.FindObject('cbmsim')

  fPos = ROOT.TVector3()
  fMom = ROOT.TVector3()
  
  muon_to_follow = -1
  for index, track in enumerate(sTree.MCTrack):
    if abs(track.GetPdgCode()) == MUON and index not in checked_muons:
      muon_to_follow = index
      checked_muons.add(muon_to_follow)
      break

  if muon_to_follow == -1:
    return {}

  fT = sTree.MCTrack[muon_to_follow]
  fT.GetStartVertex(fPos)
  hitlist = {}
  hitlist[fPos.Z()] = [fPos.X(), fPos.Y(), fT.GetP()]
# loop over all sensitive volumes to find hits
  for P in ["vetoPoint", "muonPoint", "EcalPoint", "HcalPoint", "preshowerPoint",
            "strawtubesPoint", "ShipRpcPoint", "TargetPoint"]:
    if not sTree.GetBranch(P):
      continue
    c = eval("sTree." + P)
    for p in c:
      if p.GetTrackID() == muon_to_follow:
        p.Momentum(fMom)
        if hasattr(p, "LastPoint"):
          lp = p.LastPoint()
          hitlist[lp.z()] = [lp.x(), lp.y(), p.LastMom().Mag()]
          hitlist[2. * p.GetZ() - lp.z()] = [2. * p.GetX() - lp.x(),
                                             2. * p.GetY() - lp.y(),
                                            fMom.Mag()]
        else:
          hitlist[p.GetZ()] = [p.GetX(), p.GetY(), fMom.Mag()]
  return hitlist


def trajectory_init(lsOfGlobals, name='SHiP MuonTraj'):
  traj = lsOfGlobals.FindObject(name)
  if not traj:
    traj = ROOT.TGraph()
    traj.SetName(name)
    traj.SetLineWidth(2)
    lsOfGlobals.Add(traj)
  traj.Set(0)
  return traj

def execute():
    N_MUONS = 2
    canvas = ROOT.gROOT.FindObject('Root Canvas EnergyLoss')
    if not canvas:
      print "add particle flower not started!"
      return
    lsOfGlobals = ROOT.gROOT.GetListOfGlobals()
    c1 = canvas.cd(1)
    c1.Clear()

# get zmin, zmax from graphic
    SHiPDisplay = lsOfGlobals.FindObject('SHiP Displayer')
    v = ROOT.gEve.GetViewers().FindChild('Bar Embedded Viewer side')
    vw = v.GetGLViewer()
    cam = vw.CurrentCamera()
    ed = v.GetEditorObject()
    co = ed.GetCameraOverlay()
    ax = co.GetAttAxis()
    fr = vw.GetFrame()
    test = ROOT.TGLVertex3(0., 0., 0.)
    vtest = cam.ViewportToWorld(test)
    zmin = vtest.Z()
    test = ROOT.TGLVertex3(fr.GetWidth(), 0., 0.)
    vtest = cam.ViewportToWorld(test)
    zmax = vtest.Z()


    checked_muons = set()
    all_muons_hitlist = [collect_hits(lsOfGlobals, checked_muons) for _ in range(N_MUONS)]
    all_muons_hitlist = list(filter(lambda x: x, all_muons_hitlist))
    trajectories = [trajectory_init(lsOfGlobals, "SHiP MuonTraj_" + str(index))
                    for index in range(len(all_muons_hitlist))]

    emin, emax = 1E9, -1E9
    for trajectory, hitlist in zip(trajectories, all_muons_hitlist):
      for index, z in enumerate(sorted(hitlist.keys())):
          E = hitlist[z][2]
          trajectory.SetPoint(index, z, E)
          emax = max(emax, E)
          emin = min(emin, E)

    emin, emax = emin * 0.9, emax * 1.1
    print "zmin/max", zmin, zmax
    hist = c1.DrawFrame(zmin, emin, zmax, emax)
    hist.SetYTitle('p (GeV/c)')
    hist.SetXTitle('z cm')
    xaxis = hist.GetXaxis()
    xaxis.SetNdivisions(ax.GetNdivisions())
    for trajectory in trajectories:
      trajectory.Draw()
    txt = ROOT.TLatex()
    txt.DrawLatexNDC(0.6, 0.8, 'event index:' + str(SHiPDisplay.n))
    c1.Update()


if __name__ == "__main__":
    execute()
