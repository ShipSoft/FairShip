import ROOT,os
import rootUtils as ut
import shipunit as u
h={}
from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-r", "--runNumber", dest="runNumber", help="run number", type=int,required=True)
parser.add_argument("-p", "--path", dest="path", help="run number",required=False,default="")
parser.add_argument("-f", "--inputFile", dest="fname", help="file name for MC", type=str,default=None,required=False)
parser.add_argument("-g", "--geoFile", dest="geoFile", help="geofile", required=True)
options = parser.parse_args()

path = options.path
if path.find('eos')>0: path = os.environ['EOSSHIP']+options.path

import SndlhcGeo
geo = SndlhcGeo.GeoInterface(path+options.geoFile)
MuFilter = geo.modules['MuFilter']

A,B = ROOT.TVector3(),ROOT.TVector3()
zPos={}
systemAndPlanes = {1:2,2:5,3:7}

freq = 160.E6

for s in systemAndPlanes:
       for plane in range(systemAndPlanes[s]):
          bar = 4
          p = plane
          if s==3 and plane%2==0: 
             bar = 90
             p = plane//2
          if s==3 and plane%2==1:
             bar = 30
             p = plane//2
          MuFilter.GetPosition(s*10000+p*1000+bar,A,B)
          zPos[s*10+plane] = (A.Z()+B.Z())/2.

def smallSiPMchannel(i):
    if i==2 or i==5 or i==10 or i==13: return True
    else: return False

if options.runNumber>0:
              f=ROOT.TFile.Open(path+'sndsw_raw_'+str(options.runNumber).zfill(6)+'.root')
              eventTree = f.rawConv
else:
              f=ROOT.TFile.Open(options.fname)
              eventTree = f.cbmsim

import SndlhcTracking
trackTask = SndlhcTracking.Tracking() 
trackTask.InitTask(eventTree)

def hitMaps(Nev = -1):
 # veto system 2 layers with 7 bars and 8 sipm channels on both ends
 # US system 5 layers with 10 bars and 8 sipm channels on both ends
 # DS system horizontal(3) planes, 60 bars, readout on both sides, single channel
 #                         vertical(4) planes, 60 bar, readout on top, single channel
 for s in systemAndPlanes:
    for l in range(systemAndPlanes[s]):
       ut.bookHist(h,'hit_'+str(s*10+l),'channel map / plane '+str(s*10+l),160,-0.5,159.5)
       if s==3:  ut.bookHist(h,'bar_'+str(s*10+l),'hit map / plane '+str(s*10+l),60,-0.5,59.5)
       else:       ut.bookHist(h,'bar_'+str(s*10+l),'hit map / plane '+str(s*10+l),10,-0.5,9.5)
       ut.bookHist(h,'sig_'+str(s*10+l),'signal / plane '+str(s*10+l),150,0.0,150.)
       if s==2: 
               ut.bookHist(h,'sigS_'+str(s*10+l),'signal / plane '+str(s*10+l),150,0.0,150.)
               ut.bookHist(h,'sigL_'+str(s*10+l),'signal / plane '+str(s*10+l),150,0.0,150.)
               ut.bookHist(h,'sigR_'+str(s*10+l),'signal / plane '+str(s*10+l),150,0.0,150.)
       ut.bookHist(h,'Tsig_'+str(s*10+l),'signal / plane '+str(s*10+l),150,0.0,150.)
       ut.bookHist(h,'occ_'+str(s*10+l),'channel occupancy '+str(s*10+l),100,0.0,200.)
       ut.bookHist(h,'occTag_'+str(s*10+l),'channel occupancy '+str(s*10+l),100,0.0,200.)

 ut.bookHist(h,'leftvsright_2','US hits in left / right',8,-0.5,7.5,8,-0.5,7.5)
 ut.bookHist(h,'leftvsright_3','DS hits in left / right',2,-0.5,1.5,2,-0.5,1.5)
 ut.bookHist(h,'leftvsright_signal_2','US signal in left / right',100,-0.5,200.,100,-0.5,200.)
 ut.bookHist(h,'leftvsright_signal_3','DS signal in left / right',100,-0.5,200.,100,-0.5,200.)

 ut.bookHist(h,'dtime','delta event time; dt [ns]',100,0.0,1000.)
 ut.bookHist(h,'dtimeu','delta event time; dt [us]',100,0.0,1000.)
 ut.bookHist(h,'dtimem','delta event time; dt [ms]',100,0.0,1000.)

 ut.bookHist(h,'bs','beam spot',100,-100.,10.,100,0.,80.)
 ut.bookHist(h,'bsDS','beam spot',60,-0.5,59.5,60,-0.5,59.5)
 ut.bookHist(h,'slopes','track slopes',100,-0.1,0.1,100,-0.1,0.1)

 N=-1
 Tprev = 0
 if Nev < 0 : Nev = eventTree.GetEntries()
 eventTree.GetEvent(0)
 t0 =  eventTree.EventHeader.GetEventTime()/freq
 for event in eventTree:
    N+=1
    if N>Nev: break
    withX = False
    planes = {}
    for aHit in event.Digi_MuFilterHit:
        if not aHit.isValid(): continue
        detID = aHit.GetDetectorID()
        if aHit.isVertical():     withX = True
        s = detID//10000
        l  = (detID%10000)//1000  # plane number
        bar = (detID%1000)
        key = s*100+l
        if not key in planes: planes[key] = {}
        planes[key][bar] = 1
        if s>2: 
               l=2*l
               if bar>59:
                    bar=bar-60
                    l+=1
        nSiPMs = aHit.GetnSiPMs()
        nSides  = aHit.GetnSides()

# check left/right
        allChannels = aHit.GetAllSignals(False)  # masking not yet correctly done in the raw conversion
        if nSides==2:
           Nleft    = 0
           Nright = 0
           Sleft    = 0
           Sright = 0
           for c in allChannels:
              if  nSiPMs > c[0]:  # left side
                    Nleft+=1
                    Sleft+=c[1]
              else:
                    Nright+=1
                    Sright+=c[1]
           rc = h['leftvsright_'+str(s)].Fill(Nleft,Nright)
           rc = h['leftvsright_signal_'+str(s)].Fill(Sleft,Sright)
        for c in allChannels:
            channel = bar*nSiPMs*nSides + c[0]
            rc = h['hit_'+str(s)+str(l)].Fill( int(channel))
            rc = h['bar_'+str(s)+str(l)].Fill(bar)
            if s==2:
                if smallSiPMchannel(c[0]) : rc  = h['sigS_'+str(s)+str(l)].Fill(c[1])
                elif c[0]<8: rc  = h['sigL_'+str(s)+str(l)].Fill(c[1])
                else             : rc  = h['sigR_'+str(s)+str(l)].Fill(c[1])
            rc  = h['sig_'+str(s)+str(l)].Fill(c[1])
    maxOneBar = True
    for key in planes:
        if len(planes[key]) > 2: maxOneBar = False
    if withX and maxOneBar:  beamSpot()

 installed_stations = {0:0,1:5,2:4}
 x = 0
 y = 0
 for s in installed_stations: 
    if installed_stations[s]>0: x+=1
    if installed_stations[s]>y: y = installed_stations[s]
 ut.bookCanvas(h,'hitmaps',' ',1200,1600,x,y)
 ut.bookCanvas(h,'barmaps',' ',1200,1600,x,y)
 ut.bookCanvas(h,'signal',' ',1200,1600,x,y)
 ut.bookCanvas(h,'Tsignal',' ',1200,1600,x,y)

 for S in installed_stations:
   for l in range(installed_stations[S]):
      n = S + l*x
      tc = h['hitmaps'].cd(n)
      h['hit_'+str(S+1)+str(l)].Draw()
      tc = h['barmaps'].cd(n)
      h['bar_'+str(S+1)+str(l)].Draw()
      tc = h['signal'].cd(n)
      h['sig_'+str(S+1)+str(l)].Draw()
      tc = h['Tsignal'].cd(n)
      h['Tsig_'+str(S+1)+str(l)].Draw()

 ut.bookCanvas(h,'USBars',' ',1200,900,1,1)
 colours = {0:ROOT.kOrange,1:ROOT.kRed,2:ROOT.kGreen,3:ROOT.kBlue,4:ROOT.kMagenta}
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
 for i in range(4): 
       h['hit_3'+str(i)].SetLineColor(colours[i])
       h['hit_3'+str(i)].SetLineWidth(2)
       h['hit_3'+str(i)].SetStats(0)
 h['hit_30'].Draw()
 h['hit_31'].Draw('same')
 h['hit_32'].Draw('same')
 h['hit_33'].Draw('same')
 h['lbar3']=ROOT.TLegend(0.6,0.6,0.99,0.99)
 for i in range(4): 
    h['lbar3'].AddEntry(h['hit_3'+str(i)],'plane '+str(i+1),"f")
 h['lbar3'].Draw()

 ut.bookCanvas(h,'LR',' ',1200,900,2,2)
 h['LR'].cd(1)
 h['leftvsright_'+str(3)].Draw('textBox')
 h['LR'].cd(2)
 h['leftvsright_'+str(2)].Draw('textBox')
 h['LR'].cd(3)
 h['leftvsright_signal_2'].SetMaximum(h['leftvsright_signal_2'].GetBinContent(10,10))
 h['leftvsright_signal_3'].SetMaximum(h['leftvsright_signal_3'].GetBinContent(10,10))
 h['leftvsright_signal_'+str(3)].Draw('colz')
 h['LR'].cd(4)
 h['leftvsright_signal_'+str(2)].Draw('colz')

# check US, left/right/small
 ut.bookCanvas(h,'signalUS',' ',1200,1600,3,5)
 s=2
 for plane in range(5):
     l = 1
     for side in ['L','R','S']:
         tc = h['signalUS'].cd(3*plane+l)
         l+=1
         h['sig'+side+'_'+str( s*10+plane)].Draw()

 for canvas in ['signalUS','LR','hitmaps','barmaps','signal','Tsignal','USBars']:
      h[canvas].Update()
      h[canvas].Print(canvas+'-run'+str(options.runNumber)+'.png')

def eventTime(Nev=-1):
 Tprev = -1
 if Nev < 0 : Nev = eventTree.GetEntries()
 ut.bookHist(h,'Etime','delta event time; dt [s]',100,0.0,1.)
 ut.bookHist(h,'EtimeZ','delta event time; dt [ns]',1000,0.0,10000.)
 ut.bookCanvas(h,'T',' ',1024,2*768,1,2)
 eventTree.GetEvent(0)
 t0 =  eventTree.EventHeader.GetEventTime()/160.E6
 eventTree.GetEvent(Nev-1)
 tmax = eventTree.EventHeader.GetEventTime()/160.E6
 ut.bookHist(h,'time','elapsed time; t [s]',1000,0,tmax-t0)

 N=-1
 for event in eventTree:
    N+=1
    if N>Nev: break
    T = event.EventHeader.GetEventTime()
    dT = 0
    if Tprev >0: dT = T-Tprev
    Tprev = T
    rc = h['Etime'].Fill(dT/freq)
    rc = h['EtimeZ'].Fill(dT*1E9/160.E6)
    rc = h['time'].Fill( (T/freq-t0))
 tc = h['T'].cd(1)
 tc.SetLogy(1)
 h['EtimeZ'].Draw()
 tc.Update()
 tc = h['T'].cd(2)
 h['time'].Draw()
 h['T'].Update()
 h['T'].Print('time-run'+str(options.runNumber)+'.png')

def beamSpot():
   trackTask.ExecuteTask()
   Xbar = -10
   Ybar = -10
   for  aTrack in eventTree.fittedTracks:
         state = aTrack.getFittedState()
         pos    = state.getPos()
         rc = h['bs'].Fill(pos.x(),pos.y())
         points = aTrack.getPoints()
         for p in points:
             m = p.getRawMeasurement()
             detID = m.getDetId()
             key = m.getHitId()//1000 # for mufi
             aHit = eventTree.Digi_MuFilterHit[key]
             s = detID//10000
             l  = (detID%10000)//1000  # plane number
             bar = (detID%1000)
             if s>2: 
               l=2*l
               if bar>59:
                    bar=bar-60
                    l+=1
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

         aTrack.Delete()

def DS_track():
# check for low occupancy and enough hits in DS stations
    stations = {}
    for s in systemAndPlanes:
       for plane in range(systemAndPlanes[s]): 
          stations[s*10+plane] = {}
    k=-1
    for aHit in eventTree.Digi_MuFilterHit:
         k+=1
         if not aHit.isValid(): continue
         s = aHit.GetDetectorID()//10000
         p = (aHit.GetDetectorID()//1000)%10
         bar = aHit.GetDetectorID()%1000
         plane = s*10+p
         if s==3:
           if bar<60: plane = s*10+2*p
           else:  plane = s*10+2*p+1
         stations[plane][k] = aHit
    if not len(stations[30])*len(stations[31])*len(stations[32])*len(stations[33]) == 1: return -1
# build trackCandidate
    hitlist = {}
    for p in range(30,34):
         k = list(stations[p].keys())[0]
         hitlist[k] = stations[p][k]
    theTrack = trackTask.fitTrack(hitlist)
    return theTrack

def deltaTime(aHit):
        allChannels = aHit.GetAllTimes(False)  # masking not yet correctly done in the raw conversion
        meanL, meanR = 0,0
        nL,nR = 0,0
        for c in allChannels:
              if  aHit.GetnSiPMs() > c[0]:  # left side
                  nL+=1
                  meanL+=c[1]
              else:  # right side
                  nR+=1
                  meanR+=c[1]
        if nL >1:        meanL = meanL/nL * 1E9/freq
        if nR >1:        meanR = meanR/nR  * 1E9/freq
        return meanL-meanR

def USEfficiency(Nev=-1):
 name = {1:'Veto',2:'US',3:'DS'}
 for s in systemAndPlanes:
    for l in range(systemAndPlanes[s]):
        if s==3: ut.bookHist(h,'dtLRvsX_'+name[s]+str(s*10+l),'dt vs x track '+str(s*10+l)+";X [cm]; dt [ns]",80,-70.,10.,100,-1.,1.)
        else:      ut.bookHist(h,'dtLRvsX_'+name[s]+str(s*10+l),'dt vs x track '+str(s*10+l)+";X [cm]; dt [ns]",80,-70.,10.,100,-10.,10.)
    if s!=2 : continue
    for l in range(systemAndPlanes[s]):
        ut.bookHist(h,'resY_'+name[s]+str(s*10+l),'residual Y '+str(s*10+l),100,-20.,20.)
        ut.bookHist(h,'resY_'+name[s]+'L'+str(s*10+l),'residual Y '+str(s*10+l),100,-20.,20.)
        ut.bookHist(h,'resY_'+name[s]+'R'+str(s*10+l),'residual Y '+str(s*10+l),100,-20.,20.)
        ut.bookHist(h,'resY_'+name[s]+'S'+str(s*10+l),'residual Y '+str(s*10+l),100,-20.,20.)
        ut.bookHist(h,'track_'+name[s]+str(s*10+l),'track x/y '+str(s*10+l),80,-70.,10.,80,0.,80.)
        for bar in range(10):
            ut.bookHist(h,'nSiPMs_'+name[s]+str(s*10+l)+'_'+str(bar),'#sipms',16,-0.5,15.5)
            ut.bookHist(h,'signalS_'+name[s]+str(s*10+l)+'_'+str(bar),'signal',100,0.,200.)
            ut.bookHist(h,'signalL_'+name[s]+str(s*10+l)+'_'+str(bar),'signal',100,0.,200.)

 if Nev < 0 : Nev = eventTree.GetEntries()
 N=0
 for event in eventTree:
    N+=1
    if N>Nev: break
    theTrack = DS_track()
    if not hasattr(theTrack,"getFittedState"): continue
# now extrapolate to US and check for hits.
    state = theTrack.getFittedState()
    pos    = state.getPos()
    mom = state.getMom()

    dsHits = {}
    for s in range(2,4):
       for p in range(5): dsHits[s*10+p]=[]
    for aHit in eventTree.Digi_MuFilterHit:
         if not aHit.isValid(): continue
         plane = (aHit.GetDetectorID()//1000)
         dsHits[plane].append(aHit)
    s = 2
    for plane in range(5):
         z = zPos[s*10+plane]
         lam = (z-pos.z())/mom.z()
         xEx,yEx = pos.x()+lam*mom.x(),pos.y()+lam*mom.y()
         # tag with station close by
         if plane ==0: tag = 1
         else: tag = plane -1
         tagged = False
         for aHit in dsHits[s*10+tag]:
              detID = aHit.GetDetectorID()
              MuFilter.GetPosition(detID,A,B)
              dy = (A[1]+B[1])/2. - yEx
              if abs(dy)<5: tagged = True
         if not tagged: continue
         rc = h['track_US'+str(s*10+plane)].Fill(xEx,yEx)
         for aHit in dsHits[s*10+plane]:
              detID = aHit.GetDetectorID()
              bar = detID%1000
              MuFilter.GetPosition(detID,A,B)
              dy = (A[1]+B[1])/2. - yEx
              rc = h['resY_US'+str(s*10+plane)].Fill(dy)
              S = aHit.GetAllSignals()
              # check for signal in left / right or small sipm
              left,right,small = False,False,False
              for x in S:
                  if x.first<8: left = True
                  else:           right = True
                  if smallSiPMchannel(x.first): small = True
              if left:    rc = h['resY_USL'+str(s*10+plane)].Fill(dy)
              if right: rc = h['resY_USR'+str(s*10+plane)].Fill(dy)
              if small: rc = h['resY_USS'+str(s*10+plane)].Fill(dy)
              if abs(dy)<2.0:   # check channels
                  rc = h['nSiPMs_US'+str(s*10+plane)+'_'+str(bar)].Fill(S.size())
                  for x in S:
                      if smallSiPMchannel(x.first): rc = h['signalS_US'+str(s*10+plane)+'_'+str(bar)].Fill(x.second)
                      else:                                    rc = h['signalL_US'+str(s*10+plane)+'_'+str(bar)].Fill(x.second)
#   look at delta time vs track X
                  dt = deltaTime(aHit)
                  h['dtLRvsX_US'+str(s*10+plane)].Fill(xEx,dt)
# check DS
    s = 3
    for plane in range(4):
         z = zPos[s*10+plane]
         lam = (z-pos.z())/mom.z()
         xEx,yEx = pos.x()+lam*mom.x(),pos.y()+lam*mom.y()
         for aHit in dsHits[s*10+plane]:
              # only horizontal layers have two sides
              if not aHit.GetnSides()==2: continue
              detID = aHit.GetDetectorID()
              MuFilter.GetPosition(detID,A,B)
              dt = deltaTime(aHit)
              h['dtLRvsX_DS'+str(s*10+plane)].Fill(xEx,dt)

    theTrack.Delete()

latex = ROOT.TLatex()
def analyze_USefficiency():
  ut.bookCanvas(h,'E','',1200,2000,4,5)
  ut.bookCanvas(h,'T','',800,1600,1,5)
  ut.bookCanvas(h,'TDS','',800,900,1,2)
  s=2
  for plane in range(5):
     tc = h['E'].cd(4*plane+1)
     h['track_US'+str(s*10+plane)].Draw('colz')
     l = 0
     for side in ['L','R','S']:
      tc = h['E'].cd(4*plane+2+l)
      l+=1
      res = h['resY_US'+side+str(s*10+plane)]
      res.Draw()
      binw = res.GetBinWidth(1)
      myGauss = ROOT.TF1('gauss','abs([0])*'+str(binw)+'/(abs([2])*sqrt(2*pi))*exp(-0.5*((x-[1])/[2])**2)+abs([3])',4)
      myGauss.SetParameter(0,res.GetEntries())
      myGauss.SetParameter(1,0)
      myGauss.SetParameter(2,2.)
      rc = res.Fit(myGauss,'SL','',-15.,15.)
      fitResult = rc.Get()
      tc.Update()
      stats = res.FindObject('stats')
      stats.SetOptFit(111111)
      stats.SetX1NDC(0.63)
      stats.SetY1NDC(0.25)
      stats.SetX2NDC(0.98)
      stats.SetY2NDC(0.94)
      tracks = h['track_US'+str(s*10+plane)].GetEntries()
      eff = fitResult.Parameter(0)/tracks
      effErr = fitResult.ParError(0)/tracks
      latex.DrawLatexNDC(0.2,0.8,'eff=%5.2F+/-%5.2F%%'%(eff,effErr))
  h['E'].Print('Eff'+'-run'+str(options.runNumber)+'.png')

  latex.SetTextColor(ROOT.kRed)
  for plane in range(5):
     tc = h['T'].cd(plane+1)
     hist = h['dtLRvsX_US'+str(s*10+plane)]
     hist.SetStats(0)
     hist.Draw('colz')
# get time x correlation, X = m*dt + b
     h['gdtLRvsX_US'+str(s*10+plane)] = ROOT.TGraph()
     g = h['gdtLRvsX_US'+str(s*10+plane)]
     xproj = hist.ProjectionX('tmpx')
     for nx in range(1,hist.GetNbinsX()+1):
            tmp = hist.ProjectionY('tmp',nx,nx)
            X   = xproj.GetBinCenter(nx)
            dt = tmp.GetMean()
            g.SetPoint(nx-1,X,dt)
     g.SetLineColor(ROOT.kBlue)
     g.SetLineWidth(2)
     g.Draw('same')
     rc = g.Fit('pol1','S','',-50.,-10.)
     result = rc.Get()
     m = 1./result.Parameter(1)
     b = -result.Parameter(0) * m
     txt = 'dt X relation: X = #frac{dt}{%5.2F} +%5.2F '%(1./m,b)
     latex.DrawLatexNDC(0.2,0.8,txt)
  h['T'].Print('dTvsX'+'-run'+str(options.runNumber)+'.png')

  # for DS
  s = 3
  for plane in range(2):
     tc = h['TDS'].cd(plane+1)
     hist = h['dtLRvsX_DS'+str(s*10+plane)]
     hist.SetStats(0)
     hist.Draw('colz')
# get time x correlation, X = m*dt + b
     h['gdtLRvsX_DS'+str(s*10+plane)] = ROOT.TGraph()
     g = h['gdtLRvsX_DS'+str(s*10+plane)]
     xproj = hist.ProjectionX('tmpx')
     for nx in range(1,hist.GetNbinsX()+1):
            tmp = hist.ProjectionY('tmp',nx,nx)
            X   = xproj.GetBinCenter(nx)
            dt = tmp.GetMean()
            g.SetPoint(nx-1,X,dt)
     g.SetLineColor(ROOT.kBlue)
     g.SetLineWidth(2)
     g.Draw('same')
     rc = g.Fit('pol1','S','',-50.,-10.)
     result = rc.Get()
     m = 1./result.Parameter(1)
     b = -result.Parameter(0) * m
     txt = 'dt X relation: X = #frac{dt}{%5.2F} +%5.2F '%(1./m,b)
     latex.DrawLatexNDC(0.2,0.8,txt)
  h['TDS'].Print('dTvsXDS'+'-run'+str(options.runNumber)+'.png')

def timing(Nev = -1):
 binning = {1:50,2:50,3:5}
 for s in systemAndPlanes:
    for l in range(systemAndPlanes[s]):
       ut.bookHist(h,'timeDiffsL_'+str(s*10+l),' deviation from mean'+str(s*10+l)+'; [ns]',100,-binning[s],binning[s])
       ut.bookHist(h,'timeDiffsR_'+str(s*10+l),' deviation from mean'+str(s*10+l)+'; [ns]',100,-binning[s],binning[s])
       ut.bookHist(h,'timeDiffsLR_'+str(s*10+l),' mean left - mean right'+str(s*10+l)+'; [ns]',100,-binning[s],binning[s])

 N=-1
 if Nev < 0 : Nev = eventTree.GetEntries()
 for event in eventTree:
    N+=1
    if N>Nev: break
    for aHit in event.Digi_MuFilterHit:
        if not aHit.isValid(): continue
        detID = aHit.GetDetectorID()
        s = detID//10000
        l  = (detID%10000)//1000  # plane number
        bar = (detID%1000)
        if s>2: 
               l=2*l
               if bar>59:
                    bar=bar-60
                    l+=1
        nSides  = aHit.GetnSides()
        nSiPMs = aHit.GetnSiPMs()

        allChannels = aHit.GetAllTimes(False)  # masking not yet correctly done in the raw conversion
        meanL, meanR = 0,0
        nL,nR = 0,0
        for c in allChannels:
              if  nSiPMs > c[0]:  # left side
                  nL+=1
                  meanL+=c[1]
              else:  # right side
                  nR+=1
                  meanR+=c[1]
        if nL >1:        meanL = meanL/nL * 1E9/freq
        if nR >1:        meanR = meanR/nR  * 1E9/freq
        if nL>0 and nR>0:  rc = h['timeDiffsLR_'+str(s*10+l)].Fill(meanL-meanR)
        for c in allChannels:
              if  nSiPMs > c[0]:  # left side
                  dt = c[1]* 1E9/freq - meanL
                  rc = h['timeDiffsL_'+str(s*10+l)].Fill(dt)
              else:
                  dt = c[1]* 1E9/freq - meanR
                  rc = h['timeDiffsR_'+str(s*10+l)].Fill(dt)

 installed_stations = {0:0,1:5,2:4}
 x = 0
 y = 0
 for s in installed_stations: 
    if installed_stations[s]>0: x+=1
    if installed_stations[s]>y: y = installed_stations[s]
 ut.bookCanvas(h,'dt',' ',800,1600,1,5)
 ut.bookCanvas(h,'dtLR',' ',1200,1600,x,y)

 for S in installed_stations:
   for l in range(installed_stations[S]):
     if S==1:
         n = 1+ l
         tc = h['dt'].cd(n)
         tc.SetLogy(1)
         h['timeDiffsL_'+str(S+1)+str(l)].SetLineColor(ROOT.kRed)
         h['timeDiffsL_'+str(S+1)+str(l)].Draw()
         h['timeDiffsR_'+str(S+1)+str(l)].SetLineColor(ROOT.kGreen)
         h['timeDiffsR_'+str(S+1)+str(l)].Draw('same')
     n = S + l*x
     tc = h['dtLR'].cd(n)
     h['timeDiffsLR_'+str(S+1)+str(l)].Draw()
 h['dt'].Print('dt'+'-run'+str(options.runNumber)+'.png')
 h['dtLR'].Print('dtLR'+'-run'+str(options.runNumber)+'.png')



