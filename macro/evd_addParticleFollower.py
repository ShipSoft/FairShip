import ROOT,evd_fillEnergy
gEve=ROOT.gEve
def execute():
 if not gEve.GetViewers().FindChild('Bar Embedded Viewer side'):   
  slot = ROOT.TEveWindow.CreateWindowInTab(gEve.GetBrowser().GetTabRight())
  pack1 = slot.MakePack()
  pack1.SetShowTitleBar(ROOT.kFALSE)
  pack1.SetElementName("Top/Side View")
  pack1.SetVertical()
# Embedded viewer.
  cams = ['side','top']
  for c in cams:
   slot = pack1.NewSlot()
   v = ROOT.TEveViewer("BarViewer"+c)
   v.SpawnGLEmbeddedViewer(gEve.GetEditor())
   slot.ReplaceWindow(v)
   v.SetElementName("Bar Embedded Viewer "+c)  # gEve.GetViewers().FindChild('Bar Embedded Viewer')
   v.SetShowTitleBar(ROOT.kFALSE)
   gEve.GetViewers().AddElement(v)
   v.AddScene(gEve.GetEventScene())
   v.AddScene(gEve.GetScenes().FindChild('Geometry scene'))
   vw = v.GetGLViewer()
   if c=='top': 
    vw.SetCurrentCamera(ROOT.TGLViewer.kCameraOrthoZnOX)
   else:
    vw.SetCurrentCamera(ROOT.TGLViewer.kCameraOrthoZOY)
   vw.ResetCameras()
   cam = vw.CurrentCamera()
   cam.Reset()
   ed = v.GetEditorObject()
   co = ed.GetCameraOverlay()
   center = array('d',[0,0,0])
   if c=='topxxx': 
    cam.Configure(1.0,0.,center,-ROOT.TMath.Pi()/2.,0.)
   else:  
    cam.Configure(1.0,0.,center,0,0)
    co.SetShowOrthographic(True)
    co.SetOrthographicMode(ROOT.TGLCameraOverlay.kAll) # ROOT.TGLCameraOverlay.kAxis
# problems with light, Camera home
  #cam.SetExternalCenter(ROOT.kTRUE)
   ls = vw.GetLightSet()
   ls.SetFrontPower(0.2)
   ls.SetSidePower(0.4)
   ls.SetSpecularPower(1.1)
   vw.DoDraw()
#
  slot = pack1.NewSlot()
  slot.StartEmbedding()
  can = ROOT.TCanvas("Root Canvas EnergyLoss") # ROOT.gROOT.FindObject('Root Canvas')
  can.SetTitle('Energy as function of z')
  can.ToggleEditor()
  slot.StopEmbedding()
  ls = ROOT.gROOT.GetListOfGlobals()
  ls.Add(can)
  SHiPDisplay = ls.FindObject('SHiP Displayer')
  SHiPDisplay.transparentMode('on')
if __name__=="__main__":
  execute()
  v = ROOT.gEve.GetViewers().FindChild('Bar Embedded Viewer side')
  vw = v.GetGLViewer()
  cam = vw.CurrentCamera()
  fr = vw.GetFrame()
  test = ROOT.TGLVertex3(0.,0.,0.)
  vtest = cam.ViewportToWorld(test)
  zmin = vtest.Z()
  test = ROOT.TGLVertex3(fr.GetWidth(),0.,0.)
  vtest = cam.ViewportToWorld(test)
  zmax = vtest.Z()
  print "?",zmin,zmax
  evd_fillEnergy.execute()

