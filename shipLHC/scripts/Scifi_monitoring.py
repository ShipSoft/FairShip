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
