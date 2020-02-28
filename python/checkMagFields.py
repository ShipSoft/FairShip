from __future__ import division
import ROOT,sys
import rootUtils as ut
import shipunit as u

def run():
 fGeo = ROOT.gGeoManager
 run = sys.modules['__main__'].run
 if hasattr(sys.modules['__main__'],'h'): h =  sys.modules['__main__'].h
 else: h={} 
 grid = 120,100,1500
 xmin,ymin,zmin = -4*u.m,-5*u.m,-100*u.m
 xmax,ymax,zmax = 4*u.m,5*u.m,50*u.m
 dx,dy,dz = (xmax-xmin)/grid[0],(ymax-ymin)/grid[1],(zmax-zmin)/grid[2]
 ut.bookHist(h,'Bx-','Bx- component ;z [cm];x [cm];y [cm]',grid[2],zmin,zmax,grid[0],xmin,xmax,grid[1],ymin,ymax)
 ut.bookHist(h,'By-','By- component ;z [cm];x [cm];y [cm]',grid[2],zmin,zmax,grid[0],xmin,xmax,grid[1],ymin,ymax)
 ut.bookHist(h,'Bz-','Bz- component ;z [cm];x [cm];y [cm]',grid[2],zmin,zmax,grid[0],xmin,xmax,grid[1],ymin,ymax)
 ut.bookHist(h,'Bx+','Bx+ component ;z [cm];x [cm];y [cm]',grid[2],zmin,zmax,grid[0],xmin,xmax,grid[1],ymin,ymax)
 ut.bookHist(h,'By+','By+ component ;z [cm];x [cm];y [cm]',grid[2],zmin,zmax,grid[0],xmin,xmax,grid[1],ymin,ymax)
 ut.bookHist(h,'Bz+','Bz+ component ;z [cm];x [cm];y [cm]',grid[2],zmin,zmax,grid[0],xmin,xmax,grid[1],ymin,ymax)
 h['Bx-'].SetMarkerColor(ROOT.kGreen-3)
 h['Bx+'].SetMarkerColor(ROOT.kGreen+3)
 h['By-'].SetMarkerColor(ROOT.kBlue-3)
 h['By+'].SetMarkerColor(ROOT.kBlue+3)
 h['Bz-'].SetMarkerColor(ROOT.kCyan-2)
 h['Bz+'].SetMarkerColor(ROOT.kCyan+2)
 for ix in range(grid[0]):
  for iy in range(grid[1]):
   for iz in range(grid[2]):
    x,y,z = xmin + ix*dx,ymin + iy*dy,zmin + iz*dz
    n = fGeo.FindNode(x,y,z)
    f = n.GetVolume().GetField()
    if f: 
      if f.GetFieldValue()[0]<0:  rc=h['Bx-'].Fill(z,x,y,-f.GetFieldValue()[0]/u.tesla)     
      if f.GetFieldValue()[0]>0:  rc=h['Bx+'].Fill(z,x,y,f.GetFieldValue()[0]/u.tesla)     
      if f.GetFieldValue()[1]<0:  rc=h['By-'].Fill(z,x,y,-f.GetFieldValue()[1]/u.tesla)     
      if f.GetFieldValue()[1]>0:  rc=h['By+'].Fill(z,x,y,f.GetFieldValue()[1]/u.tesla)     
      if f.GetFieldValue()[2]<0:  rc=h['Bz-'].Fill(z,x,y,-f.GetFieldValue()[2]/u.tesla)   
      if f.GetFieldValue()[2]>0:  rc=h['Bz+'].Fill(z,x,y,f.GetFieldValue()[2]/u.tesla)   
    f = run.GetField()
    if f.GetBx(x,y,z)<0: rc=h['Bx-'].Fill(z,x,y,-f.GetBx(x,y,z)/u.tesla) 
    if f.GetBx(x,y,z)>0: rc=h['Bx+'].Fill(z,x,y,f.GetBx(x,y,z)/u.tesla) 
    if f.GetBy(x,y,z)<0: rc=h['By-'].Fill(z,x,y,-f.GetBy(x,y,z)/u.tesla)
    if f.GetBy(x,y,z)>0: rc=h['By+'].Fill(z,x,y,f.GetBy(x,y,z)/u.tesla) 
 for x in h.keys():
  hi = h[x]
  if hi.ClassName()=='TH3F':
   h[x+'_xz']=h[x].Project3D('xy')
   h[x+'_xz'].SetTitle(hi.GetTitle()+' top view')
   h[x+'_yz']=h[x].Project3D('xz')  
   h[x+'_yz'].SetTitle(hi.GetTitle()+' side view')
 for x in h: 
  h[x].SetStats(0)
  h[x].SetMarkerSize(3)
 txt = {'y':[' Up',' Down'],'x':[' Right',' Left']}
 for pol in ['y','x']:
  for p in ['_xz','_yz']:
   cn = 'c'+pol+p
   ut.bookCanvas(h,key=cn,title='field check',nx=1600,ny=1200,cx=1,cy=1)
   h[cn].cd(1)
   h['B'+pol+'+'+p].Draw()
   h['B'+pol+'-'+p].Draw('same')
   h['B'+pol+'L'+p] = ROOT.TLegend(0.79,0.72,0.91,0.87)
   h['B'+pol+'L'+p].AddEntry(h['B'+pol+'+'],'B'+pol+txt[pol][0],'PM')
   h['B'+pol+'L'+p].AddEntry(h['B'+pol+'-'],'B'+pol+txt[pol][1],'PM')
   h['B'+pol+'L'+p].Draw()
   h[cn].Update()
   h[cn].Print('FieldB'+pol+'Proj'+p+'.png')
