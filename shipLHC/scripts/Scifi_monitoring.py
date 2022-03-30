#!/usr/bin/env python
import ROOT,os,sys
import rootUtils as ut

A,B  = ROOT.TVector3(),ROOT.TVector3()

class Scifi_hitMaps(ROOT.FairTask):
   " produce hitmaps for Scifi"
   def Init(self,options,monitor):
       self.M = monitor
       h = self.M.h
       for s in range(10):
          ut.bookHist(h,'posX_'+str(s),'x',2000,-100.,100.)
          ut.bookHist(h,'posY_'+str(s),'y',2000,-100.,100.)
          if s%2==1: ut.bookHist(h,'mult_'+str(s),'mult vertical station '+str(s//2+1),100,-0.5,99.5)
          else: ut.bookHist(h,'mult_'+str(s),'mult horizontal station '+str(s//2+1),100,-0.5,99.5)
       for mat in range(30):
          ut.bookHist(h,'mat_'+str(mat),'hit map / mat',512,-0.5,511.5)
          ut.bookHist(h,'sig_'+str(mat),'signal / mat',200,-50.0,150.)
          ut.bookHist(h,'tdc_'+str(mat),'tdc / mat',200,-1.,4.)
   def ExecuteEvent(self,event):
       h = self.M.h
       mult = [0]*10
       for aHit in event.Digi_ScifiHits:
          if not aHit.isValid(): continue
          X =  self.M.Scifi_xPos(aHit.GetDetectorID())
          rc = h['mat_'+str(X[0]*3+X[1])].Fill(X[2])
          rc = h['sig_'+str(X[0]*3+X[1])].Fill(aHit.GetSignal(0))
          rc = h['tdc_'+str(X[0]*3+X[1])].Fill(aHit.GetTime(0))
          self.M.Scifi.GetSiPMPosition(aHit.GetDetectorID(),A,B)
          if aHit.isVertical(): rc = h['posX_'+str(X[0])].Fill(A[0])
          else:                     rc = h['posY_'+str(X[0])].Fill(A[1])
          mult[X[0]]+=1
       for s in range(10):
          rc = h['mult_'+str(s)].Fill(mult[s])
   def Plot(self):
       h = self.M.h
       ut.bookCanvas(h,'hitmaps',' ',1024,768,6,5)
       ut.bookCanvas(h,'signal',' ',1024,768,6,5)
       ut.bookCanvas(h,'tdc',' ',1024,768,6,5)
       for mat in range(30):
           tc = self.M.h['hitmaps'].cd(mat+1)
           A = self.M.h['mat_'+str(mat)].GetSumOfWeights()/512.
           if self.M.h['mat_'+str(mat)].GetMaximum()>10*A: self.M.h['mat_'+str(mat)].SetMaximum(10*A)
           self.M.h['mat_'+str(mat)].Draw()
           tc = self.M.h['signal'].cd(mat+1)
           self.M.h['sig_'+str(mat)].Draw()
           tc = self.M.h['tdc'].cd(mat+1)
           self.M.h['tdc_'+str(mat)].Draw()

       ut.bookCanvas(h,'positions',' ',2048,768,5,2)
       ut.bookCanvas(h,'mult',' ',2048,768,5,2)
       for s in range(5):
           tc = self.M.h['positions'].cd(s+1)
           self.M.h['posY_'+str(2*s)].Draw()
           tc = self.M.h['positions'].cd(s+6)
           self.M.h['posX_'+str(2*s+1)].Draw()
           tc = self.M.h['mult'].cd(s+1)
           tc.SetLogy(1)
           self.M.h['mult_'+str(2*s)].Draw()
           tc = self.M.h['mult'].cd(s+6)
       tc.SetLogy(1)
       self.M.h['mult_'+str(2*s+1)].Draw()

       for canvas in ['hitmaps','signal','mult']:
           self.M.h[canvas].Update()
           self.M.myPrint(self.M.h[canvas],"Scifi-"+canvas)

class Scifi_residuals(ROOT.FairTask):
   " produce residuals for Scifi"
   def Init(self,options,monitor):
       NbinsRes = options.ScifiNbinsRes
       xmin        = options.Scifixmin
       alignPar   = options.ScifialignPar

       self.M = monitor
       h = self.M.h
       self.projs = {1:'V',0:'H'}
       self.parallelToZ = ROOT.TVector3(0., 0., 1.)
       run = ROOT.FairRunAna.Instance()
       self.trackTask = run.GetTask('simpleTracking')
       self.T = ROOT.FairRootManager.Instance().GetObject("Reco_MuonTracks")

       for s in range(1,6):
          for o in range(2):
             for p in self.projs:
               proj = self.projs[p]
               xmax = -xmin
               ut.bookHist(h,'res'+proj+'_Scifi'+str(s*10+o),'residual '+proj+str(s*10+o)+'; [#mum]',NbinsRes,xmin,xmax)
               ut.bookHist(h,'resX'+proj+'_Scifi'+str(s*10+o),'residual '+proj+str(s*10+o)+'; [#mum]',NbinsRes,xmin,xmax,100,-50.,0.)
               ut.bookHist(h,'resY'+proj+'_Scifi'+str(s*10+o),'residual '+proj+str(s*10+o)+'; [#mum]',NbinsRes,xmin,xmax,100,10.,60.)
               ut.bookHist(h,'resC'+proj+'_Scifi'+str(s*10+o),'residual '+proj+str(s*10+o)+'; [#mum]',NbinsRes,xmin,xmax,128*4*3,-0.5,128*4*3-0.5)
               ut.bookHist(h,'track_Scifi'+str(s*10+o),'track x/y '+str(s*10+o),80,-70.,10.,80,0.,80.)
               ut.bookHist(h,'trackChi2/ndof','track chi2/ndof vs ndof',100,0,100,20,0,20)
               ut.bookHist(h,'trackSlopes','track slope; x [mrad]; y [mrad]',1000,-100,100,1000,-100,100)

       if alignPar:
            for x in alignPar:
               self.M.Scifi.SetConfPar(x,alignPar[x])

   def ExecuteEvent(self,event):
       h = self.M.h
# select events with clusters in each plane
       theTrack = self.Scifi_track(nPlanes = 10, nClusters = 11)
       if not hasattr(theTrack,"getFittedState"): return
       theTrack.Delete()
       sortedClusters={}
       for aCl in eventTree.ScifiClusters:
           so = aCl.GetFirst()//100000
           if not so in sortedClusters: sortedClusters[so]=[]
           sortedClusters[so].append(aCl)

       for s in range(1,6):
# build trackCandidate
            hitlist = {}
            k=0
            for so in sortedClusters:
                    if so//10 == s: continue
                    for x in sortedClusters[so]:
                       hitlist[k] = x
                       k+=1
            theTrack = trackTask.fitTrack(hitlist)
            if not hasattr(theTrack,"getFittedState"): continue
# check residuals
            fitStatus = theTrack.getFitStatus()
            if not fitStatus.isFitConverged(): 
                 theTrack.Delete()
                 continue
            rc = h['trackChi2/ndof'].Fill(fitStatus.getChi2()/(fitStatus.getNdf()+1E-10),fitStatus.getNdf() )
            fstate =  theTrack.getFittedState()
            mom = fstate.getMom()
            rc = h['trackSlopes'].Fill(mom.X()/mom.Z()*1000,mom.Y()/mom.Z()*1000)
# test plane 
            for o in range(2):
                testPlane = s*10+o
                z = zPos['Scifi'][testPlane]
                rep     = ROOT.genfit.RKTrackRep(13)
                state  = ROOT.genfit.StateOnPlane(rep)
# find closest track state
                mClose = 0
                mZmin = 999999.
                for m in range(0,theTrack.getNumPointsWithMeasurement()):
                   st   = theTrack.getFittedState(m)
                   Pos = st.getPos()
                   if abs(z-Pos.z())<mZmin:
                      mZmin = abs(z-Pos.z())
                      mClose = m
                fstate =  theTrack.getFittedState(mClose)
                pos,mom = fstate.getPos(),fstate.getMom()
                rep.setPosMom(state,pos,mom)
                NewPosition = ROOT.TVector3(0., 0., z)   # assumes that plane in global coordinates is perpendicular to z-axis, which is not true for TI18 geometry.
                rep.extrapolateToPlane(state, NewPosition, parallelToZ )
                pos = state.getPos()
                xEx,yEx = pos.x(),pos.y()
                rc = h['track_Scifi'+str(testPlane)].Fill(xEx,yEx)
                for aCl in sortedClusters[testPlane]:
                   aCl.GetPosition(A,B)
                   if o==1 :   D = (A[0]+B[0])/2. - xEx
                   else:         D = (A[1]+B[1])/2. - yEx
                   detID = aCl.GetFirst()
                   channel = detID%1000 + ((detID%10000)//1000)*128 + (detID%100000//10000)*512
                   rc = h['res'+self.projs[o]+'_Scifi'+str(testPlane)].Fill(D/u.um)
                   rc = h['resX'+self.projs[o]+'_Scifi'+str(testPlane)].Fill(D/u.um,xEx)
                   rc = h['resY'+self.projs[o]+'_Scifi'+str(testPlane)].Fill(D/u.um,yEx)
                   rc = h['resC'+self.projs[o]+'_Scifi'+str(testPlane)].Fill(D/u.um,channel)

            theTrack.Delete()

# analysis and plots 
   def Plot(self):
       h = self.M.h
       P = {'':'','X':'colz','Y':'colz','C':'colz'}
       Par = {'mean':1,'sigma':2}
       h['globalPos'] = {'meanH':ROOT.TGraphErrors(),'sigmaH':ROOT.TGraphErrors(),'meanV':ROOT.TGraphErrors(),'sigmaV':ROOT.TGraphErrors()}
       h['globalPosM'] = {'meanH':ROOT.TGraphErrors(),'sigmaH':ROOT.TGraphErrors(),'meanV':ROOT.TGraphErrors(),'sigmaV':ROOT.TGraphErrors()}
       globalPos = h['globalPos']
       for proj in P:
           ut.bookCanvas(h,'scifiRes'+proj,'',1600,1900,2,5)
           k=1
           j = {0:0,1:0}
           for s in range(1,6):
               for o in range(2):
                  so = s*10+o
                  tc = h['scifiRes'+proj].cd(k)
                  k+=1
                  hname = 'res'+proj+self.projs[o]+'_Scifi'+str(so)
                  h[hname].Draw(P[proj])
                  if proj == '':
                     rc = h[hname].Fit('gaus','SQ')
                     fitResult = rc.Get()
                     for p in Par:
                          globalPos[p+self.projs[o]].SetPoint(s-1,s,fitResult.Parameter(Par[p]))
                          globalPos[p+self.projs[o]].SetPointError(s-1,0.5,fitResult.ParError(1))
                          globalPos[p+self.projs[o]].SetMarkerStyle(21)
                          globalPos[p+self.projs[o]].SetMarkerColor(ROOT.kBlue)
                     if proj == 'C':
                         for m in range(3):
                             h[hname+str(m)] = h[hname].ProjectionX(hname+str(m),m*512,m*512+512)
                             rc = h[hname+str(m)].Fit('gaus','SQ0')
                             fitResult = rc.Get()
                             for p in Par:
                                 h['globalPosM'][p+self.projs[o]].SetPoint(j[o], s*10+m,   fitResult.Parameter(Par[p]))
                                 h['globalPosM'][p+self.projs[o]].SetPointError(j[o],0.5,fitResult.ParError(1))
                                 j[o]+=1
                                 h['globalPosM'][p+self.projs[o]].SetMarkerStyle(21)
                                 h['globalPosM'][p+self.projs[o]].SetMarkerColor(ROOT.kBlue)
       
       S  = ctypes.c_double()
       M = ctypes.c_double()
       alignPar = {}
       for p in globalPos:
           ut.bookCanvas(h,p,p,750,750,1,1)
           tc = h[p].cd()
           globalPos[p].SetTitle(p+';station; offset [#mum]')
           globalPos[p].Draw("ALP")
           if p.find('mean')==0:
               for n in range(globalPos[p].GetN()):
                  rc = globalPos[p].GetPoint(n,S,M)
                  print("station %i: offset %s =  %5.2F um"%(S.value,p[4:5],M.value))
                  s = int(S.value*10)
                  if p[4:5] == "V": s+=1
                  alignPar["Scifi/LocD"+str(s)] = M.value

       for p in h['globalPosM']:
           ut.bookCanvas(h,p+'M',p,750,750,1,1)
           tc = h[p+'M'].cd()
           h['globalPosM'][p].SetTitle(p+';mat ; offset [#mum]')
           h['globalPosM'][p].Draw("ALP")
           if p.find('mean')==0:
              for n in range(h['globalPosM'][p].GetN()):
                 rc = h['globalPosM'][p].GetPoint(n,S,M)
                 print("station %i: offset %s =  %5.2F um"%(S.value,p[4:5],M.value))
                 s = int(S.value*10)
                 if p[4:5] == "V": s+=1
                 alignPar["Scifi/LocM"+str(s)] = M.value
       return alignPar
       
   def Scifi_track(self,nPlanes = 8, nClusters = 11):
# check for low occupancy and enough hits in Scifi
        clusters = self.trackTask.scifiCluster()
        stations = {}
        for s in range(1,6):
           for o in range(2):
              stations[s*10+o] = []
        for cl in clusters:
            detID = cl.GetFirst()
            s  = detID//1000000
            o = (detID//100000)%10
            stations[s*10+o].append(detID)
        nclusters = 0
        check = {}
        for s in range(1,6):
            for o in range(2):
                if len(stations[s*10+o]) > 0: check[s*10+o]=1
                nclusters+=len(stations[s*10+o])
        if len(check)<nPlanes or nclusters > nClusters: return -1
# build trackCandidate
        hitlist = {}
        for k in range(len(clusters)):
           hitlist[k] = clusters[k]
        theTrack = trackTask.fitTrack(hitlist)
        eventTree.ScifiClusters = clusters
        return theTrack


