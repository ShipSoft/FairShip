#!/usr/bin/env python
import ROOT,os,sys
import rootUtils as ut
from array import array

A,B  = ROOT.TVector3(),ROOT.TVector3()

class twod(ROOT.FairTask):
   " 2d event display X and Y projections"
   def Init(self,options,monitor):
       self.trans2local = False
       self.detSize = {}
       self.M = monitor
       self.systems = monitor.sdict
       run = ROOT.FairRunAna.Instance()
       self.trackTask = run.GetTask('simpleTracking')
       self.OT = run.GetSink().GetOutTree()
       si = self.M.snd_geo.snd_geo.Scifi
       self.detSize[0] =[si.channel_width, si.channel_width, si.scifimat_z]
       mi = self.M.snd_geo.snd_geo.MuFilter
       self.detSize[1] =[mi.VetoBarX/2,                   mi.VetoBarY/2,            mi.VetoBarZ/2]
       self.detSize[2] =[mi.UpstreamBarX/2,           mi.UpstreamBarY/2,    mi.UpstreamBarZ/2]
       self.detSize[3] =[mi.DownstreamBarX_ver/2,mi.DownstreamBarY/2,mi.DownstreamBarZ/2]
       self.options = options
       h = self.M.h
       if 'simpleDisplay' not in h: ut.bookCanvas(h,key='simpleDisplay',title='2d event display',nx=1200,ny=1600,cx=1,cy=2)
       h['simpleDisplay'].cd(1)
       zStart = 250. # TI18 coordinate system
       if self.M.snd_geo.snd_geo.Floor.z == 0: zStart = 60.
       ut.bookHist(h,'xz','X projection; z [cm]; x [cm]',500,zStart,zStart+320.,100,-100.,10.)
       ut.bookHist(h,'yz','Y projection; z [cm]; y [cm]',500,zStart,zStart+320.,100,0.,80.)
       h['xz'].SetStats(0)
       h['yz'].SetStats(0)
       self.proj = {1:'xz',2:'yz'}

   def ExecuteEvent(self,event):
       h = self.M.h
       proj = self.proj
       geo = self.M.snd_geo
       detSize = self.detSize
       N = self.M.EventNumber
       options = self.options
       nav = ROOT.gGeoManager.GetCurrentNavigator()
       if options.goodEvents and not self.goodEvent(event): return
       if options.withTrack:
              self.trackTask.ExecuteTask()
              ntracks = self.OT.Reco_MuonTracks.GetEntries()
              uniqueTracks = self.cleanTracks()
              if len(uniqueTracks)<options.nTracks: return

              for aTrack in self.OT.Reco_MuonTracks:
                   mom    = aTrack.getFittedState().getMom()
                   pos      = aTrack.getFittedState().getPos()
                   mom.Print()
                   pos.Print()

       digis = []
       if event.FindBranch("Digi_ScifiHits"): digis.append(event.Digi_ScifiHits)
       if event.FindBranch("Digi_MuFilterHits"): digis.append(event.Digi_MuFilterHits)
       if event.FindBranch("Digi_MuFilterHit"): digis.append(event.Digi_MuFilterHit)
       empty = True
       for x in digis:
          if x.GetEntries()>0: empty = False
       if empty: return
       h['hitCollectionX']= {'Scifi':[0,ROOT.TGraphErrors()],'DS':[0,ROOT.TGraphErrors()]}
       h['hitCollectionY']= {'Veto':[0,ROOT.TGraphErrors()],'Scifi':[0,ROOT.TGraphErrors()],'US':[0,ROOT.TGraphErrors()],'DS':[0,ROOT.TGraphErrors()]}

       for collection in ['hitCollectionX','hitCollectionY']:
          for c in h[collection]:
             rc=h[collection][c][1].SetName(c)
             rc=h[collection][c][1].Set(0)
       for p in proj:
           rc = h[ 'simpleDisplay'].cd(p)
           if p==1: h[proj[p]].SetTitle('event '+str(N))
           h[proj[p]].Draw('b')
       for D in digis:
          for digi in D:
             detID = digi.GetDetectorID()
             if digi.GetName()  == 'MuFilterHit':
                system = digi.GetSystem()
                geo.modules['MuFilter'].GetPosition(detID,A,B)
                if self.trans2local:
                    curPath = nav.GetPath()
                    tmp = curPath.rfind('/')
                    nav.cd(curPath[:tmp])
             else:
                geo.modules['Scifi'].GetSiPMPosition(detID,A,B)
                if self.trans2local:
                    curPath = nav.GetPath()
                    tmp = curPath.rfind('/')
                    nav.cd(curPath[:tmp])
                system = 0
             globA,locA = array('d',[A[0],A[1],A[2]]),array('d',[A[0],A[1],A[2]])
             if self.trans2local:   nav.MasterToLocal(globA,locA)
             Z = A[2]
             if digi.isVertical():
                   collection = 'hitCollectionX'
                   Y = locA[0]
                   sY = detSize[system][0]
             else:                         
                   collection = 'hitCollectionY'
                   Y = locA[1]
                   sY = detSize[system][1]
             c = h[collection][self.systems[system]]
             rc = c[1].SetPoint(c[0],Z,Y)
             rc = c[1].SetPointError(c[0],detSize[system][2],sY)
             c[0]+=1 
       h['hitCollectionY']['Veto'][1].SetMarkerColor(ROOT.kRed)
       h['hitCollectionY']['Scifi'][1].SetMarkerColor(ROOT.kBlue)
       h['hitCollectionX']['Scifi'][1].SetMarkerColor(ROOT.kBlue)
       h['hitCollectionY']['US'][1].SetMarkerColor(ROOT.kGreen)
       h['hitCollectionY']['DS'][1].SetMarkerColor(ROOT.kCyan)
       h['hitCollectionX']['DS'][1].SetMarkerColor(ROOT.kCyan)
       k = 1
       for collection in ['hitCollectionX','hitCollectionY']:
             h[ 'simpleDisplay'].cd(k)
             k+=1
             for c in h[collection]:
                 if h[collection][c][1].GetN()<1: continue
                 h[collection][c][1].SetMarkerStyle(20+k)
                 h[collection][c][1].SetMarkerSize(1.5)
                 rc=h[collection][c][1].Draw('sameP')
                 h['display:'+c]=h[collection][c][1]

       if options.withTrack: self.addTrack()

       h[ 'simpleDisplay'].Update()
       if options.save: h['simpleDisplay'].Print('event_'+"{:04d}".format(N)+'.png')
       if not options.auto:  rc = input("hit return for next event ")

   def Plot(self):
       if self.M.options.save: os.system("convert -delay 60 -loop 0 event*.png animated.gif")

   def goodEvent(self,event):
# can be replaced by any user selection
           maxScifiOcc = 25
           minScifi = 3
           minMufi = 5
           stations = {'Scifi':{},'Mufi':{}}
           if event.Digi_ScifiHits.GetEntries()>maxScifiOcc: return False
           for d in event.Digi_ScifiHits:
               stations['Scifi'][d.GetDetectorID()//1000000] = 1
           for d in event.Digi_MuFilterHits:
               plane = d.GetDetectorID()//1000
               stations['Mufi'][plane] = 1
           totalN = len(stations['Mufi'])+len(stations['Scifi'])
           if len(stations['Scifi'])>minScifi or len(stations['Mufi'])>minMufi: return True
           return False

   def addTrack(self):
      h = self.M.h
      xax = h['xz'].GetXaxis()
      nTrack = 0
      for   aTrack in self.OT.Reco_MuonTracks:
         for p in [0,1]:
            h['aLine'+str(nTrack*10+p)] = ROOT.TGraph()
         zEx = xax.GetBinCenter(1)
         mom    = aTrack.getFittedState().getMom()
         pos      = aTrack.getFittedState().getPos()
         lam      = (zEx-pos.z())/mom.z()
         Ex        = [pos.x()+lam*mom.x(),pos.y()+lam*mom.y()]
         for p in [0,1]:   h['aLine'+str(nTrack*10+p)].SetPoint(0,zEx,Ex[p])

         for i in range(aTrack.getNumPointsWithMeasurement()):
            state = aTrack.getFittedState(i)
            pos    = state.getPos()
            for p in [0,1]:
                h['aLine'+str(nTrack*10+p)].SetPoint(i+1,pos[2],pos[p])

         zEx = xax.GetBinCenter(xax.GetLast())
         mom    = aTrack.getFittedState().getMom()
         pos      = aTrack.getFittedState().getPos()
         lam      = (zEx-pos.z())/mom.z()
         Ex        = [pos.x()+lam*mom.x(),pos.y()+lam*mom.y()]
         for p in [0,1]:   h['aLine'+str(nTrack*10+p)].SetPoint(i+2,zEx,Ex[p])

         for p in [0,1]:
             tc = h[ 'simpleDisplay'].cd(p+1)
             h['aLine'+str(nTrack*10+p)].SetLineColor(ROOT.kRed)
             h['aLine'+str(nTrack*10+p)].SetLineWidth(2)
             h['aLine'+str(nTrack*10+p)].Draw('same')
             tc.Update()
             h[ 'simpleDisplay'].Update()
         nTrack+=1

   def cleanTracks(self):
      listOfDetIDs = {}
      n = 0
      for aTrack in self.OT.Reco_MuonTracks:
         listOfDetIDs[n] = []
         for i in range(aTrack.getNumPointsWithMeasurement()):
            M =  aTrack.getPointWithMeasurement(i)
            R =  M.getRawMeasurement()
            listOfDetIDs[n].append(R.getDetId())
            if R.getDetId()>0: listOfDetIDs[n].append(R.getDetId()-1)
            listOfDetIDs[n].append(R.getDetId()+1)
         n+=1
      uniqueTracks = []
      for n1 in range( len(listOfDetIDs) ):
         unique = True
         for n2 in range( len(listOfDetIDs) ):
             if n1==n2: continue
             I = set(listOfDetIDs[n1]).intersection(listOfDetIDs[n2])
             if len(I)>0:  unique = False
         if unique: uniqueTracks.append(n1)
      if len(uniqueTracks)>1: 
         for n1 in range( len(listOfDetIDs) ): print(listOfDetIDs[n1])
      return uniqueTracks
