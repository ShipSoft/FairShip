#!/usr/bin/env python
import ROOT,os,sys
import rootUtils as ut

A,B  = ROOT.TVector3(),ROOT.TVector3()

class Mufi_hitMaps(ROOT.FairTask):
   " produce hitmaps for MuFilter, Veto/US/DS"
   """
  veto system 2 layers with 7 bars and 8 sipm channels on both ends
  US system 5 layers with 10 bars and 8 sipm channels on both ends
  DS system horizontal(3) planes, 60 bars, readout on both sides, single channel
                          vertical(4) planes, 60 bar, readout on top, single channel
   """
   def Init(self,options,monitor):
       self.M = monitor
       sdict = self.M.sdict
       h = self.M.h
       run = ROOT.FairRunAna.Instance()
       self.trackTask = run.GetTask('simpleTracking')
       self.T = ROOT.FairRootManager.Instance().GetObject("Reco_MuonTracks")

       for s in monitor.systemAndPlanes:
            ut.bookHist(h,sdict[s]+'Mult','QDCs vs nr hits; #hits; QDC [a.u.]',200,0.,800.,200,0.,300.)
            for l in range(monitor.systemAndPlanes[s]):
                  ut.bookHist(h,'hitmult_'+str(s*10+l),'hit mult / plane '+str(s*10+l)+'; #hits',61,-0.5,60.5)
                  ut.bookHist(h,'hit_'+str(s*10+l),'channel map / plane '+str(s*10+l)+'; #channel',160,-0.5,159.5)
                  if s==3:  ut.bookHist(h,'bar_'+str(s*10+l),'bar map / plane '+str(s*10+l)+'; #bar',60,-0.5,59.5)
                  else:       ut.bookHist(h,'bar_'+str(s*10+l),'bar map / plane '+str(s*10+l)+'; #bar',10,-0.5,9.5)
                  ut.bookHist(h,'sig_'+str(s*10+l),'signal / plane '+str(s*10+l)+'; QDC [a.u.]',200,0.0,200.)
                  if s==2:    ut.bookHist(h,'sigS_'+str(s*10+l),'signal / plane '+str(s*10+l)+'; QDC [a.u.]',200,0.0,200.)
                  ut.bookHist(h,'sigL_'+str(s*10+l),'signal / plane '+str(s*10+l)+'; QDC [a.u.]',200,0.0,200.)
                  ut.bookHist(h,'sigR_'+str(s*10+l),'signal / plane '+str(s*10+l)+'; QDC [a.u.]',200,0.0,200.)
                  ut.bookHist(h,'Tsig_'+str(s*10+l),'signal / plane '+str(s*10+l)+'; QDC [a.u.]',200,0.0,200.)
                  # not used currently?
                  ut.bookHist(h,'occ_'+str(s*10+l),'channel occupancy '+str(s*10+l),100,0.0,200.)
                  ut.bookHist(h,'occTag_'+str(s*10+l),'channel occupancy '+str(s*10+l),100,0.0,200.)

                  ut.bookHist(h,'leftvsright_1','Veto hits in left / right; Left: # hits; Right: # hits',10,-0.5,9.5,10,-0.5,9.5)
                  ut.bookHist(h,'leftvsright_2','US hits in left / right; L: # hits; R: # hits',10,-0.5,9.5,10,-0.5,9.5)
                  ut.bookHist(h,'leftvsright_3','DS hits in left / right; L: # hits; R: # hits',2,-0.5,1.5,2,-0.5,1.5)
                  ut.bookHist(h,'leftvsright_signal_1','Veto signal in left / right; Left: QDC [a.u.]; Right: QDC [a.u.]',100,-0.5,200.,100,-0.5,200.)
                  ut.bookHist(h,'leftvsright_signal_2','US signal in left / right; L: QDC [a.u.]; R: QDC [a.u.]',100,-0.5,200.,100,-0.5,200.)
                  ut.bookHist(h,'leftvsright_signal_3','DS signal in left / right; L: QDC [a.u.]; R: QDC [a.u.]',100,-0.5,200.,100,-0.5,200.)

                  ut.bookHist(h,'dtime','delta event time; dt [ns]',100,0.0,1000.)
                  ut.bookHist(h,'dtimeu','delta event time; dt [us]',100,0.0,1000.)
                  ut.bookHist(h,'dtimem','delta event time; dt [ms]',100,0.0,1000.)

                  ut.bookHist(h,'bs','beam spot; x[cm]; y[cm]',100,-100.,10.,100,0.,80.)
                  ut.bookHist(h,'bsDS','beam spot, #bar X, #bar Y',60,-0.5,59.5,60,-0.5,59.5)
                  ut.bookHist(h,'slopes','track slopes; slope X [rad]; slope Y [rad]',100,-0.1,0.1,100,-0.1,0.1)

       self.listOfHits = {1:[],2:[],3:[]}
   def ExecuteEvent(self,event):
       systemAndPlanes =self.M.systemAndPlanes
       sdict = self.M.sdict
       h = self.M.h
       mult = {}
       withX = False
       planes = {}
       for i in self.listOfHits:  self.listOfHits[i].clear()
       for s in systemAndPlanes:
           for l in range(systemAndPlanes[s]):   mult[s*10+l]=0
       for aHit in event.Digi_MuFilterHits:
           if not aHit.isValid(): continue
           if aHit.isVertical():     withX = True
           Minfo = self.M.MuFilter_PlaneBars(aHit.GetDetectorID())
           s,l,bar = Minfo['station'],Minfo['plane'],Minfo['bar']
           mult[s*10+l]+=1
           key = s*100+l
           if not key in planes: planes[key] = {}
           sumSignal = self.M.map2Dict(aHit,'SumOfSignals')
           planes[key][bar] = [sumSignal['SumL'],sumSignal['SumR']]
           nSiPMs = aHit.GetnSiPMs()
           nSides  = aHit.GetnSides()
# check left/right
           allChannels = self.M.map2Dict(aHit,'GetAllSignals')
           for c in allChannels:
               self.listOfHits[s].append(allChannels[c])
           Nleft,Nright,Sleft,Sright = 0,0,0,0
           for c in allChannels:
              if  nSiPMs > c:  # left side
                    Nleft+=1
                    Sleft+=allChannels[c]
              else:
                    Nright+=1
                    Sright+=allChannels[c]
           rc = h['leftvsright_'+str(s)].Fill(Nleft,Nright)
           rc = h['leftvsright_signal_'+str(s)].Fill(Sleft,Sright)
#
           for c in allChannels:
               channel = bar*nSiPMs*nSides + c
               rc = h['hit_'+str(s)+str(l)].Fill( int(channel))
               rc = h['bar_'+str(s)+str(l)].Fill(bar)
               if s==2 and self.M.smallSiPMchannel(c) : rc  = h['sigS_'+str(s)+str(l)].Fill(allChannels[c])
               elif c<nSiPMs: rc  = h['sigL_'+str(s)+str(l)].Fill(allChannels[c])
               else             :             rc  = h['sigR_'+str(s)+str(l)].Fill(allChannels[c])
               rc  = h['sig_'+str(s)+str(l)].Fill(allChannels[c])
           allChannels.clear()
#
       for s in self.listOfHits:
           nhits = len(self.listOfHits[s])
           qcdsum = 0
           for i in range(nhits):
               rc = h[sdict[s]+'Mult'].Fill(nhits, self.listOfHits[s][i])
       for s in systemAndPlanes:
          for l in range(systemAndPlanes[s]):   
             rc = h['hitmult_'+str(s*10+l)].Fill(mult[s*10+l])

       maxOneBar = True
       for key in planes:
          if len(planes[key]) > 2: maxOneBar = False
       if withX and maxOneBar:  self.beamSpot(event)
    
   def beamSpot(self,event):
      h = self.M.h
      self.trackTask.ExecuteTask()
      Xbar = -10
      Ybar = -10
      for  aTrack in self.T:
         state = aTrack.getFittedState()
         pos    = state.getPos()
         rc = h['bs'].Fill(pos.x(),pos.y())
         points = aTrack.getPoints()
         keys     = ROOT.std.vector('int')()
         detIDs = ROOT.std.vector('int')()
         ROOT.fixRoot(points, detIDs,keys,True)
         for k in range(keys.size()):
             #                                     m = p.getRawMeasurement()
             detID =detIDs[k] # m.getDetId()
             key = keys[k]          # m.getHitId()//1000 # for mufi
             aHit = event.Digi_MuFilterHits[key]
             if aHit.GetDetectorID() != detID: continue # not a Mufi hit
             Minfo = self.M.MuFilter_PlaneBars(aHit.GetDetectorID())
             s,l,bar = Minfo['station'],Minfo['plane'],Minfo['bar']
             if s==3 and l%2==0: Ybar=bar
             if s==3 and l%2==1: Xbar=bar
             nSiPMs = aHit.GetnSiPMs()
             nSides  = aHit.GetnSides()
             for p in range(nSides):
                 c=bar*nSiPMs*nSides + p*nSiPMs
                 for i in range(nSiPMs):
                      signal = aHit.GetSignal(i+p*nSiPMs)
                      if signal > 0:
                           rc  = h['Tsig_'+str(s)+str(l)].Fill(signal)
         mom = state.getMom()
         slopeY= mom.X()/mom.Z()
         slopeX= mom.Y()/mom.Z()
         h['slopes'].Fill(slopeX,slopeY)
         if not Ybar<0 and not Xbar<0 and abs(slopeY)<0.01: rc = h['bsDS'].Fill(Xbar,Ybar)

   def Plot(self):
       h = self.M.h
       sdict = self.M.sdict
       systemAndPlanes =self.M.systemAndPlanes
       S = {1:[1800,800,2,1],2:[1800,1500,2,3],3:[1800,1800,2,4]}
       for s in S:
           ut.bookCanvas(h,'hitmaps' +str(s),'hitmaps' +str(s),S[s][0],S[s][1],S[s][2],S[s][3])
           ut.bookCanvas(h,'barmaps'+str(s),'barmaps'+str(s),S[s][0],S[s][1],S[s][2],S[s][3])
           ut.bookCanvas(h,'signal'    +str(s),'QDC'    +str(s),S[s][0],S[s][1],S[s][2],S[s][3])
           ut.bookCanvas(h,'Tsignal'   +str(s),'TDC'    +str(s),S[s][0],S[s][1],S[s][2],S[s][3])

           for l in range(systemAndPlanes[s]):
              n = l+1
              if s==3 and n==7: n=8
              tc = h['hitmaps'+str(s)].cd(n)
              tag = str(s)+str(l)
              h['hit_'+tag].Draw()
              tc = h['barmaps'+str(s)].cd(n)
              h['bar_'+tag].Draw()
              tc = h['signal'+str(s)].cd(n)
              h['sig_'+tag].Draw()
              tc = h['Tsignal'+str(s)].cd(n)
              h['Tsig_'+tag].Draw()

       ut.bookCanvas(h,'hitmult','hit multiplicities per plane',2000,1600,4,3)
       k=1
       for s in systemAndPlanes:
           for l in range(systemAndPlanes[s]):
              tc = h['hitmult'].cd(k)
              tc.SetLogy(1)
              k+=1
              rc = h['hitmult_'+str(s*10+l)].Draw()

       ut.bookCanvas(h,'VETO',' ',1200,1800,1,2)
       for l in range(2):
          tc = h['VETO'].cd(l+1)
          hname = 'hit_'+str(1)+str(l)
          h[hname].SetStats(0)
          h[hname].Draw()
          for n in range(7):
                x = (n+1)*16-0.5
                y = h['hit_'+str(1)+str(l)].GetMaximum()
                lname = 'L'+str(n)+hname
                h[lname] = ROOT.TLine(x,0,x,y)
                h[lname].SetLineColor(ROOT.kRed)
                h[lname].SetLineStyle(9)
                h[lname].Draw('same')

       ut.bookCanvas(h,'USBars',' ',1200,900,1,1)
       colours = {0:ROOT.kOrange,1:ROOT.kRed,2:ROOT.kGreen,3:ROOT.kBlue,4:ROOT.kMagenta,5:ROOT.kCyan,
                  6:ROOT.kAzure,7:ROOT.kPink,8:ROOT.kSpring}
       for i in range(5): 
           h['bar_2'+str(i)].SetLineColor(colours[i])
           h['bar_2'+str(i)].SetLineWidth(2)
           h['bar_2'+str(i)].SetStats(0)
       h['bar_20'].Draw()
       h['bar_21'].Draw('same')
       h['bar_22'].Draw('same')
       h['bar_23'].Draw('same')
       h['bar_24'].Draw('same')
       h['lbar2']=ROOT.TLegend(0.6,0.6,0.99,0.99)
       for i in range(5): 
            h['lbar2'].AddEntry(h['bar_2'+str(i)],'plane '+str(i+1),"f")
            h['lbar2'].Draw()
       for i in range(7): 
            h['hit_3'+str(i)].SetLineColor(colours[i])
            h['hit_3'+str(i)].SetLineWidth(2)
            h['hit_3'+str(i)].SetStats(0)
       h['hit_30'].Draw()
       for i in range(1,7):
           h['hit_3'+str(i)].Draw('same')
           h['lbar3']=ROOT.TLegend(0.6,0.6,0.99,0.99)
       for i in range(7): 
           h['lbar3'].AddEntry(h['hit_3'+str(i)],'plane '+str(i+1),"f")
           h['lbar3'].Draw()

       ut.bookCanvas(h,'LR',' ',1800,900,3,2)
       for i in range(1,4):
          h['LR'].cd(i)
          h['leftvsright_'+str(i)].Draw('textBox')
          h['LR'].cd(i+3)
          h['leftvsright_signal_'+str(i)].SetMaximum(h['leftvsright_signal_'+str(i)].GetBinContent(10,10))
          h['leftvsright_signal_'+str(i)].Draw('colz')

       ut.bookCanvas(h,'LRinEff',' ',1800,450,3,1)
       for s in range(1,4):
           h['lLRinEff'+str(s)]=ROOT.TLegend(0.6,0.54,0.99,0.93)
           name = 'leftvsright_signal_'+str(s)
           h[name+'0Y'] = h[name].ProjectionY(name+'0Y',1,1)
           h[name+'0X'] = h[name].ProjectionX(name+'0X',1,1)
           h[name+'1X'] = h[name].ProjectionY(name+'1Y')
           h[name+'1Y'] = h[name].ProjectionX(name+'1X')
           tc = h['LRinEff'].cd(s)
           tc.SetLogy()
           h[name+'0X'].SetStats(0)
           h[name+'0Y'].SetStats(0)
           h[name+'1X'].SetStats(0)
           h[name+'1Y'].SetStats(0)
           h[name+'0X'].SetLineColor(ROOT.kRed)
           h[name+'0Y'].SetLineColor(ROOT.kGreen)
           h[name+'1X'].SetLineColor(ROOT.kMagenta)
           h[name+'1Y'].SetLineColor(ROOT.kCyan)
           h[name+'0X'].SetMaximum(max(h[name+'1X'].GetMaximum(),h[name+'1Y'].GetMaximum()))
           h[name+'0X'].Draw()
           h[name+'0Y'].Draw('same')
           h[name+'1X'].Draw('same')
           h[name+'1Y'].Draw('same')
   # Fill(Sleft,Sright)
           h['lLRinEff'+str(s)].AddEntry(h[name+'0X'],'left with no signal right',"f")
           h['lLRinEff'+str(s)].AddEntry(h[name+'0Y'],'right with no signal left',"f")
           h['lLRinEff'+str(s)].AddEntry(h[name+'1X'],'left all',"f")
           h['lLRinEff'+str(s)].AddEntry(h[name+'1Y'],'right all',"f")
           h['lLRinEff'+str(s)].Draw()

           ut.bookCanvas(h,'signalUSVeto',' ',1200,1600,3,7)
           s = 1
           l = 1
           for plane in range(2):
                for side in ['L','R','S']:
                   tc = h['signalUSVeto'].cd(l)
                   l+=1
                   if side=='S': continue
                   h['sig'+side+'_'+str( s*10+plane)].Draw()
           s=2
           for plane in range(5):
               for side in ['L','R','S']:
                   tc = h['signalUSVeto'].cd(l)
                   l+=1
                   h['sig'+side+'_'+str( s*10+plane)].Draw()
           ut.bookCanvas(h,'signalDS',' ',900,1600,2,7)
           s = 3
           l = 1
           for plane in range(7):
               for side in ['L','R']:
                  tc = h['signalDS'].cd(l)
                  l+=1
                  h['sig'+side+'_'+str( s*10+plane)].Draw()

           for canvas in ['signalUSVeto','LR','USBars']:
              h[canvas].Update()
              self.M.myPrint(h[canvas],canvas)
           for canvas in ['hitmaps','barmaps','signal','Tsignal']:
              for s in range(1,4):
                  h[canvas+str(s)].Update()
                  self.M.myPrint(h[canvas+str(s)],canvas+sdict[s])


