import ROOT
gEve=ROOT.gEve
if not gEve.GetViewers().FindChild('Bar Embedded Viewer'):   
 slot = ROOT.TEveWindow.CreateWindowInTab(gEve.GetBrowser().GetTabRight())
 pack1 = slot.MakePack()
 pack1.SetShowTitleBar(ROOT.kFALSE)
 pack1.SetElementName("Top/Side View")
 pack1.SetVertical()
# Embedded viewer.
 cams = ['ZnOX','ZOY']
 if not hasattr(ROOT.TGLViewer,'kCameraOrthoZnOX'):
   cams = ['XOZ','ZOY']
   print "You are not using the patched ROOT6, switch back to OrthoXOZ camera, with Z vertical"
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
  vw.SetCurrentCamera(eval("ROOT.TGLViewer.kCameraOrtho"+c))
  cam = vw.CurrentCamera()
# problems with light, Camera home
  cam.SetExternalCenter(ROOT.kTRUE)
  ls = vw.GetLightSet()
  ls.SetFrontPower(0)
  ls.SetSidePower(0.4)
  ls.SetSpecularPower(0.2)
  m = cam.GetCamBase()
  s = ROOT.TGLVector3(1,1,0.1)
  m.Scale(s)
  vw.ResetCurrentCamera()
  vw.DoDraw()
#
 slot = pack1.NewSlot()
 slot.StartEmbedding()
 can = ROOT.TCanvas("Root Canvas") # ROOT.gROOT.FindObject('Root Canvas')
 can.ToggleEditor()
 slot.StopEmbedding()
 ls = ROOT.gROOT.GetListOfGlobals()
 ls.Add(can) 
 SHiPDisplay = lsOfGlobals.FindObject('SHiP Displayer')
 SHiPDisplay.transparentMode()
