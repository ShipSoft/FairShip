#python -i MufiScifi.py -r 46 -p /eos/experiment/sndlhc/testbeam/MuFilter/TB_data_commissioning/sndsw/ -g geofile_sndlhc_H6.root

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
Scifi          = geo.modules['Scifi']

A,B    = ROOT.TVector3(),ROOT.TVector3()
latex = ROOT.TLatex()


# MuFilter mapping of planes and bars 
systemAndPlanes = {1:2,2:5,3:7}
systemAndBars     = {1:7,2:10,3:60}
sdict                            = {1:'Veto',2:'US',3:'DS'}

freq = 160.E6

# some helper functions

def getAverageZpositions():
   zPos={'MuFilter':{},'Scifi':{}}
   for s in systemAndPlanes:
       for plane in range(systemAndPlanes[s]):
          bar = 4
          p = plane
          if s==3 and (plane%2==0 or plane==7): 
             bar = 90
             p = plane//2
          elif s==3 and plane%2==1:
             bar = 30
             p = plane//2
          MuFilter.GetPosition(s*10000+p*1000+bar,A,B)
          zPos['MuFilter'][s*10+plane] = (A.Z()+B.Z())/2.
   for s in range(1,6):
      mat   = 2
      sipm = 1
      channel = 64
      for o in range(2):
          Scifi.GetPosition(channel+1000*sipm+10000*mat+100000*o+1000000*s,A,B)
          zPos['Scifi'][s*10+o] = (A.Z()+B.Z())/2.
   return zPos

def smallSiPMchannel(i):
    if i==2 or i==5 or i==10 or i==13: return True
    else: return False

def fit_langau(hist,o,bmin,bmax):
   params = {0:'Width(scale)',1:'mostProbable',2:'norm',3:'sigma'}
   F = ROOT.TF1('langau',langaufun,0,200,4)
   for p in params: F.SetParName(p,params[p])
   rc = hist.Fit('landau','S'+o,'',bmin,bmax)
   res = rc.Get()
   if not res: return res
   F.SetParameter(2,res.Parameter(0))
   F.SetParameter(1,res.Parameter(1))
   F.SetParameter(0,res.Parameter(2))
   F.SetParameter(3,res.Parameter(2))
   F.SetParLimits(0,0,10)
   F.SetParLimits(1,0,100)
   F.SetParLimits(3,0,10)

   rc = hist.Fit(F,'S','',bmin,bmax)
   res = rc.Get()
   return res


def  langaufun(x,par):
   #Fit parameters:
   #par[0]=Width (scale) parameter of Landau density
   #par[1]=Most Probable (MP, location) parameter of Landau density
   #par[2]=Total area (integral -inf to inf, normalization constant)
   #par[3]=Width (sigma) of convoluted Gaussian function
   #
   #In the Landau distribution (represented by the CERNLIB approximation),
   #the maximum is located at x=-0.22278298 with the location parameter=0.
   #This shift is corrected within this function, so that the actual
   #maximum is identical to the MP parameter.
#
      # Numeric constants
      invsq2pi = 0.3989422804014   # (2 pi)^(-1/2)
      mpshift  = -0.22278298       # Landau maximum location
#
      # Control constants
      np = 100.0      # number of convolution steps
      sc =   5.0      # convolution extends to +-sc Gaussian sigmas
#
      # Variables
      summe = 0.0
#
      # MP shift correction
      mpc = par[1] - mpshift * par[0]
#
      # Range of convolution integral
      xlow = x[0] - sc * par[3]
      xupp = x[0] + sc * par[3]
#
      step = (xupp-xlow) / np
#
      # Convolution integral of Landau and Gaussian by sum
      i=1.0
      if par[0]==0 or par[3]==0: return 9999
      while i<=np/2:
         i+=1
         xx = xlow + (i-.5) * step
         fland = ROOT.TMath.Landau(xx,mpc,par[0]) / par[0]
         summe += fland * ROOT.TMath.Gaus(x[0],xx,par[3])
#
         xx = xupp - (i-.5) * step
         fland = ROOT.TMath.Landau(xx,mpc,par[0]) / par[0]
         summe += fland * ROOT.TMath.Gaus(x[0],xx,par[3])
#
      return (par[2] * step * summe * invsq2pi / par[3])

def myPrint(tc,name,withRootFile=False):
     tc.Print(name+'-run'+str(options.runNumber)+'.png')
     if withRootFile: tc.Print(name+'-run'+str(options.runNumber)+'.root')


# initialize 

zPos = getAverageZpositions()

if options.runNumber>0:
              f=ROOT.TFile.Open(path+'sndsw_raw_'+str(options.runNumber).zfill(6)+'.root')
              eventTree = f.rawConv
else:
# for MC data
              f=ROOT.TFile.Open(options.fname)
              eventTree = f.cbmsim

# backward compatbility for early converted events
eventTree.GetEvent(0)
if eventTree.GetBranch('Digi_MuFilterHit'): eventTree.Digi_MuFilterHits = eventTree.Digi_MuFilterHit

import SndlhcTracking
trackTask = SndlhcTracking.Tracking() 
trackTask.InitTask(eventTree)

# wait for user action 

def help():
    print(" following methods exist")
    print("     make and plot  hitmaps, signal distributions for MuFIlter and Scifi:")
    print("              Scifi_hitMaps(Nev) and Mufi_hitMaps(Nev)     if no number of events is given, loop over all events in file.")
    print(" ")
    print("     plot time between events and time since first event")
    print("              eventTime(Nev=-1)")
    print(" ")
    print("     MuFilter residuals, efficiency estimates with DS or Scifi tracks")
    print("              Mufi_Efficiency(Nev=-1,optionTrack='DS' or 'Scifi")
    print(" ")
    print("     analyze and plot historgams made withMufi_Efficiency ")
    print("              analyze_EfficiencyAndResiduals(readHists=False), with option True, histograms are read from file")
    print(" ")
    print("     analyze and plot historgams made withMufi_Efficiency ")
    print("              analyze_EfficiencyAndResiduals(readHists=False), with option True, histograms are read from file")
    print(" ")
    print("     first attempt to look at hadronic showers ")
    print("              USshower(Nev=-1)")
    print(" ")
    print("     make histograms with QDC distributions and fit all distributions with Langau ")
    print("              mips()")
    print("     plot the above distributions directly or reading from file ")
    print("              plotMips(readhisto=True)")
    print(" ")
    print("     beam illumination ")
    print("             scifi_beamSpot() and beamSpot() for MuFilter")
    print(" ")
    print("     rough estimate of Scifi resolution by comparing slopes  build with two stations, x and y projection")
    print("             Scifi_slopes(Nev=-1)")

print ('waiting for command. Enter help() for more infomation')

def Scifi_hitMaps(Nev=-1):
 for mat in range(30):
    ut.bookHist(h,'mat_'+str(mat),'hit map / mat',512,-0.5,511.5)
    ut.bookHist(h,'sig_'+str(mat),'signal / mat',150,0.0,150.)
 N=-1
 if Nev < 0 : Nev = eventTree.GetEntries()
 for event in eventTree:
    N+=1
    if N>Nev: break
    for aHit in event.Digi_ScifiHits:
        if not aHit.isValid(): continue
        X =  Scifi_xPos(aHit.GetDetectorID())
        rc = h['mat_'+str(X[0]*3+X[1])].Fill(X[2])
        rc  = h['sig_'+str(X[0]*3+X[1])].Fill(aHit.GetSignal(0))
 ut.bookCanvas(h,'hitmaps',' ',1024,768,6,5)
 ut.bookCanvas(h,'signal',' ',1024,768,6,5)
 for mat in range(30):
    tc = h['hitmaps'].cd(mat+1)
    A = h['mat_'+str(mat)].GetSumOfWeights()/512.
    if h['mat_'+str(mat)].GetMaximum()>10*A: h['mat_'+str(mat)].SetMaximum(10*A)
    h['mat_'+str(mat)].Draw()
    tc = h['signal'].cd(mat+1)
    h['sig_'+str(mat)].Draw()

def Mufi_hitMaps(Nev = -1):
 # veto system 2 layers with 7 bars and 8 sipm channels on both ends
 # US system 5 layers with 10 bars and 8 sipm channels on both ends
 # DS system horizontal(3) planes, 60 bars, readout on both sides, single channel
 #                         vertical(4) planes, 60 bar, readout on top, single channel
 for s in systemAndPlanes:
    for l in range(systemAndPlanes[s]):
       ut.bookHist(h,'hit_'+str(s*10+l),'channel map / plane '+str(s*10+l),160,-0.5,159.5)
       if s==3:  ut.bookHist(h,'bar_'+str(s*10+l),'hit map / plane '+str(s*10+l),60,-0.5,59.5)
       else:       ut.bookHist(h,'bar_'+str(s*10+l),'hit map / plane '+str(s*10+l),10,-0.5,9.5)
       ut.bookHist(h,'sig_'+str(s*10+l),'signal / plane '+str(s*10+l),200,0.0,200.)
       if s==2:    ut.bookHist(h,'sigS_'+str(s*10+l),'signal / plane '+str(s*10+l),200,0.0,200.)
       ut.bookHist(h,'sigL_'+str(s*10+l),'signal / plane '+str(s*10+l),200,0.0,200.)
       ut.bookHist(h,'sigR_'+str(s*10+l),'signal / plane '+str(s*10+l),200,0.0,200.)
       ut.bookHist(h,'Tsig_'+str(s*10+l),'signal / plane '+str(s*10+l),200,0.0,200.)
       ut.bookHist(h,'occ_'+str(s*10+l),'channel occupancy '+str(s*10+l),100,0.0,200.)
       ut.bookHist(h,'occTag_'+str(s*10+l),'channel occupancy '+str(s*10+l),100,0.0,200.)

 ut.bookHist(h,'leftvsright_1','Veto hits in left / right',10,-0.5,9.5,10,-0.5,9.5)
 ut.bookHist(h,'leftvsright_2','US hits in left / right',10,-0.5,9.5,10,-0.5,9.5)
 ut.bookHist(h,'leftvsright_3','DS hits in left / right',2,-0.5,1.5,2,-0.5,1.5)
 ut.bookHist(h,'leftvsright_signal_1','Veto signal in left / right',100,-0.5,200.,100,-0.5,200.)
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
    for aHit in event.Digi_MuFilterHits:
        if not aHit.isValid(): continue
        detID = aHit.GetDetectorID()
        if aHit.isVertical():     withX = True
        s = detID//10000
        l  = (detID%10000)//1000  # plane number
        bar = (detID%1000)
        key = s*100+l
        if s>2:
               l=2*l
               if bar>59:
                    bar=bar-60
                    l+=1
        if not key in planes: planes[key] = {}
        sumSignal = aHit.SumOfSignals()
        planes[key][bar] = [sumSignal['SumL'],sumSignal['SumR']]
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
            if s==2 and smallSiPMchannel(c[0]) : rc  = h['sigS_'+str(s)+str(l)].Fill(c[1])
            elif c[0]<nSiPMs: rc  = h['sigL_'+str(s)+str(l)].Fill(c[1])
            else             :             rc  = h['sigR_'+str(s)+str(l)].Fill(c[1])
            rc  = h['sig_'+str(s)+str(l)].Fill(c[1])
    maxOneBar = True
    for key in planes:
        if len(planes[key]) > 2: maxOneBar = False
    if withX and maxOneBar:  beamSpot()

 installed_stations = {}
 for  s in range(1,4):
   for l in range(systemAndPlanes[s]):
    if h['hit_'+str(s)+str(l)].GetEntries()>0:
         if not s in installed_stations: installed_stations[s]=0
         installed_stations[s]+=1
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
      n = S-1 + l*x
      tc = h['hitmaps'].cd(n)
      h['hit_'+str(S)+str(l)].Draw()
      tc = h['barmaps'].cd(n)
      h['bar_'+str(S)+str(l)].Draw()
      tc = h['signal'].cd(n)
      h['sig_'+str(S)+str(l)].Draw()
      tc = h['Tsignal'].cd(n)
      h['Tsig_'+str(S)+str(l)].Draw()

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

 ut.bookCanvas(h,'LR',' ',1800,900,3,2)
 h['LR'].cd(1)
 h['leftvsright_'+str(1)].Draw('textBox')
 h['LR'].cd(2)
 h['leftvsright_'+str(2)].Draw('textBox')
 h['LR'].cd(3)
 h['leftvsright_'+str(3)].Draw('textBox')
 h['LR'].cd(4)
 h['leftvsright_signal_1'].SetMaximum(h['leftvsright_signal_1'].GetBinContent(10,10))
 h['leftvsright_signal_2'].SetMaximum(h['leftvsright_signal_2'].GetBinContent(10,10))
 h['leftvsright_signal_3'].SetMaximum(h['leftvsright_signal_3'].GetBinContent(10,10))
 h['leftvsright_signal_'+str(1)].Draw('colz')
 h['LR'].cd(5)
 h['leftvsright_signal_'+str(2)].Draw('colz')
 h['LR'].cd(6)
 h['leftvsright_signal_'+str(3)].Draw('colz')

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


 for canvas in ['signalUSVeto','LR','hitmaps','barmaps','signal','Tsignal','USBars']:
      h[canvas].Update()
      myPrint(h[canvas],canvas)

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
 myPrint(h['T'],'time')

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
             aHit = eventTree.Digi_MuFilterHits[key]
             if aHit.GetDetectorID() != detID: continue # not a Mufi hit
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
    for aHit in eventTree.Digi_MuFilterHits:
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

def Scifi_track():
# check for low occupancy and enough hits in Scifi
    clusters = trackTask.scifiCluster()
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
    if len(check)<8 or nclusters > 15: return -1
# build trackCandidate
    hitlist = {}
    for k in range(len(clusters)):
           hitlist[k] = clusters[k]
    theTrack = trackTask.fitTrack(hitlist)
    return theTrack

def USshower(Nev=-1):
    for x in ['','-small']:
       ut.bookHist(h,'shower'+x,'energy vs z',200,0.,10000.,20,-250.,-100.)
       ut.bookHist(h,'showerX'+x,'energy vs z',200,0.,10000.,20,-250.,-100.)
       ut.bookHist(h,'wshower'+x,'z weighted energy ',100,-300.,0.)
       ut.bookHist(h,'zyshower'+x,'y vs z weighted energy ',20,-250.,-100.,11,-0.5,10.5)
    for p in range(systemAndPlanes[2]):
       ut.bookHist(h,'SvsL'+str(p),'small vs large Sipms plane' +str(p)+';large   [QCD]; small   [QCD] ',100,0.1,250.,100,0.1,100.)
    if Nev < 0 : Nev = eventTree.GetEntries()
    N=0
    for event in eventTree:
       N+=1
       if N>Nev: break
       UShits = {}
       UShitsBar = {}
       for aHit in eventTree.Digi_MuFilterHits:
           if not aHit.isValid(): continue
           detID = aHit.GetDetectorID()
           s = aHit.GetDetectorID()//10000
           if s!=2: continue
           p = (aHit.GetDetectorID()//1000)%10
           S = aHit.SumOfSignals()
           rc = h['SvsL'+str(p)].Fill(S['SumL'],S['SumS'])
           plane = (aHit.GetDetectorID()//1000)%10
           bar = aHit.GetDetectorID()%100
           if not plane in UShits: 
               UShits[plane]=0
               UShitsBar[plane]={}
               UShits[100+plane]=0
               UShitsBar[100+plane]={}
           if not bar in UShitsBar[plane]: 
                 UShitsBar[plane][bar]=0
                 UShitsBar[100+plane][bar]=0
           UShits[plane]+=S['Sum']
           UShitsBar[plane][bar]+=S['Sum']
           UShits[100+plane]+=S['SumS']
           UShitsBar[100+plane][bar]+=S['SumS']
       s = 2
       for plane in UShits:
           z = zPos['MuFilter'][s*10+plane%100]
           x = ''
           if plane > 99: x='-small'
           rc = h ['shower'+x].Fill(UShits[plane],z)
           if 0 in UShits:
               if UShits[0]>750: rc = h['showerX'+x].Fill(UShits[plane],z)
           rc = h ['wshower'+x].Fill(z,UShits[plane])
           for bar in UShitsBar[plane]:
                rc = h ['zyshower'+x].Fill(z,bar,UShitsBar[plane][bar])
    ut.bookCanvas(h,'lego','',900,1600,1,2)
    energy = {46:180,49:180,56:140,58:140,72:240,73:240,74:240,89:300,90:300,91:300}
    gain       = {46:2.5,49:3.65,52:3.65,54:2.5,56:2.5,58:3.65,72:1.0,73:2.5,74:3.65,86:3.65,87:2.5,88:1.0,89:3.65,90:2.5,91:1.0}
    tc = h['lego'].cd(1)
    tc.SetPhi(-20.5)
    tc.SetTheta(21.1)

    text = ""
    if options.runNumber in energy: text +="E=%5.1F"%(energy[options.runNumber])
    if options.runNumber in gain: text +="  with gain=%5.2F"%(gain[options.runNumber])
    h ['zyshower'].SetTitle(text+';z [cm]; y [bar number];QDC')
    h ['zyshower'].SetStats(0)
    h ['zyshower'].Draw('lego2')
    tc = h['lego'].cd(2)
    tc.SetPhi(-20.5)
    tc.SetTheta(21.1)
    h ['zyshower-small'].SetTitle('small sipms;z [cm]; y [bar number];QDC')
    h ['zyshower-small'].SetStats(0)
    h ['zyshower-small'].Draw('lego2')
    myPrint(h['lego'],'shower',withRootFile=True)
    
    ut.bookCanvas(h,'CorLS','',900,1200,1,5)
    h['SvsL'] =  h['SvsL0'].Clone('SvsL')
    h['SvsL'].SetTitle('small vs large Sipms all planes')
    for p in range(1,systemAndPlanes[2]):
        h['SvsL'].Add(h['SvsL'+str(p)])
    h['SvsL'].SetStats(0)
    for p in range(systemAndPlanes[2]):
        tc = h['CorLS'].cd(p+1)
        h['SvsL'+str(p)].SetStats(0)
        h['SvsL'+str(p)].Draw('colz')
    myPrint(h['CorLS'],'QCDsmallCSQCDlarge')

def Mufi_Efficiency(Nev=-1,optionTrack='DS',NbinsRes=100):
 for s in systemAndPlanes:
    for l in range(systemAndPlanes[s]):
        ut.bookHist(h,'dtLRvsX_'+sdict[s]+str(s*10+l),'dt vs x track '+str(s*10+l)+"X [cm] dt [ns]",70,-70.,0.,100,-10.,10.)
        if s==3:
             for bar in range(60):
                ut.bookHist(h,'signalL_'+sdict[s]+str(s*10+l)+'_'+str(bar),'signal',200,0.,100.,20,0.,100.)
                ut.bookHist(h,'signalR_'+sdict[s]+str(s*10+l)+'_'+str(bar),'signal',200,0.,100.,20,0.,100.)
    for l in range(systemAndPlanes[s]):
      for proj in ['X','Y']:
        xmin = -20.*NbinsRes/100.
        xmax = -xmin
        ut.bookHist(h,'res'+proj+'_'+sdict[s]+str(s*10+l),'residual  '+proj+str(s*10+l),NbinsRes,xmin,xmax)
        ut.bookHist(h,'res'+proj+'_'+sdict[s]+'L'+str(s*10+l),'residual '+proj+str(s*10+l),NbinsRes,xmin,xmax)
        ut.bookHist(h,'res'+proj+'_'+sdict[s]+'R'+str(s*10+l),'residual '+proj+str(s*10+l),NbinsRes,xmin,xmax)
        ut.bookHist(h,'res'+proj+'_'+sdict[s]+'S'+str(s*10+l),'residual '+proj+str(s*10+l),NbinsRes,xmin,xmax)
        ut.bookHist(h,'track_'+sdict[s]+str(s*10+l),'track x/y '+str(s*10+l),80,-70.,10.,80,0.,80.)
      for bar in range(systemAndBars[s]):
            ut.bookHist(h,'nSiPMsL_'+sdict[s]+str(s*10+l)+'_'+str(bar),'#sipms',16,-0.5,15.5,20,0.,100.)
            ut.bookHist(h,'nSiPMsR_'+sdict[s]+str(s*10+l)+'_'+str(bar),'#sipms',16,-0.5,15.5,20,0.,100.)
            ut.bookHist(h,'signalSL_'+sdict[s]+str(s*10+l)+'_'+str(bar),'signal',200,0.,100.,20,0.,100.)
            ut.bookHist(h,'signalSR_'+sdict[s]+str(s*10+l)+'_'+str(bar),'signal',200,0.,100.,20,0.,100.)
            ut.bookHist(h,'signalL_'+sdict[s]+str(s*10+l)+'_'+str(bar),'signal',200,0.,100.,20,0.,100.)
            ut.bookHist(h,'signalR_'+sdict[s]+str(s*10+l)+'_'+str(bar),'signal',200,0.,100.,20,0.,100.)
            ut.bookHist(h,'signalTL_'+sdict[s]+str(s*10+l)+'_'+str(bar),'signal',400,0.,400.,20,0.,100.)
            ut.bookHist(h,'signalTR_'+sdict[s]+str(s*10+l)+'_'+str(bar),'signal',400,0.,400.,20,0.,100.)

 if Nev < 0 : Nev = eventTree.GetEntries()
 N=0
 for event in eventTree:
    N+=1
    if N>Nev: break
    if optionTrack=='DS': theTrack = DS_track()
    else                                   : theTrack = Scifi_track()
    if not hasattr(theTrack,"getFittedState"): continue
# now extrapolate to US and check for hits.
    state = theTrack.getFittedState()
    pos    = state.getPos()
    mom = state.getMom()

    muHits = {}
    for s in systemAndPlanes:
       for p in range(systemAndPlanes[s]): muHits[s*10+p]=[]
    for aHit in eventTree.Digi_MuFilterHits:
         if not aHit.isValid(): continue
         s = aHit.GetDetectorID()//10000
         p = (aHit.GetDetectorID()//1000)%10
         bar = (aHit.GetDetectorID()%1000)%60
         plane = s*10+p
         if s==3:
           if aHit.isVertical(): plane = s*10+2*p+1
           else:                         plane = s*10+2*p
         muHits[plane].append(aHit)

    for s in sdict:
     name = str(s)
     for plane in range(systemAndPlanes[s]):
         z = zPos['MuFilter'][s*10+plane]
         lam = (z-pos.z())/mom.z()
         xEx,yEx = pos.x()+lam*mom.x(),pos.y()+lam*mom.y()
         # tag with station close by
         if plane ==0: tag = 1
         else: tag = plane -1
         tagged = False
         for aHit in muHits[s*10+tag]:
              detID = aHit.GetDetectorID()
              MuFilter.GetPosition(detID,A,B)
              if aHit.isVertical() : D = (A[0]+B[0])/2. - yEx
              else:                             D = (A[1]+B[1])/2. - yEx
              if abs(D)<5: tagged = True
         # if not tagged: continue
         rc = h['track_'+sdict[s]+str(s*10+plane)].Fill(xEx,yEx)
         for aHit in muHits[s*10+plane]:
              detID = aHit.GetDetectorID()
              bar = (detID%1000)%60
              nSiPMs = aHit.GetnSiPMs()
              nSides  = aHit.GetnSides()
              MuFilter.GetPosition(detID,A,B)
              dy = (A[1]+B[1])/2. - yEx
              dx = (A[0]+B[0])/2. - xEx
              rc = h['resY_'+sdict[s]+str(s*10+plane)].Fill(dy)
              rc = h['resX_'+sdict[s]+str(s*10+plane)].Fill(dx)
              S = aHit.GetAllSignals()
              # check for signal in left / right or small sipm
              left,right,smallL,smallR,Sleft,Sright = 0,0,0,0,0,0
              for x in S:
                  if x.first<nSiPMs: 
                       if smallSiPMchannel(x.first):  smallL+=1
                       else:    left+=1
                  else:           
                       if smallSiPMchannel(x.first):  smallR+=1
                       else:   right+=1
              if left>0:
                    rc = h['resY_'+sdict[s]+'L'+str(s*10+plane)].Fill(dy)
                    rc = h['resX_'+sdict[s]+'L'+str(s*10+plane)].Fill(dx)
              if right>0:
                    rc = h['resY_'+sdict[s]+'R'+str(s*10+plane)].Fill(dy)
                    rc = h['resX_'+sdict[s]+'R'+str(s*10+plane)].Fill(dx)
              if s==2 and (smallL>0 or smallR>0): 
                     rc = h['resY_'+sdict[s]+'S'+str(s*10+plane)].Fill(dy)
                     rc = h['resX_'+sdict[s]+'S'+str(s*10+plane)].Fill(dx)
              if abs(dy)<3.0:   # check channels
                  if aHit.isVertical():
                     dL  = A[1]- yEx
                     dR = yEx - B[1]
                  else:
                     dR  = A[0]- xEx
                     dL = xEx - B[0]
                  rc = h['nSiPMsL_'+sdict[s]+str(s*10+plane)+'_'+str(bar)].Fill(left,dL)
                  rc = h['nSiPMsR_'+sdict[s]+str(s*10+plane)+'_'+str(bar)].Fill(right,dR)
                  for x in S:
                      if x.first<nSiPMs: 
                         if s==2 and smallSiPMchannel(x.first): rc = h['signalSL_'+sdict[s]+str(s*10+plane)+'_'+str(bar)].Fill(x.second,dL)
                         else:                                    
                               rc = h['signalL_'+sdict[s]+str(s*10+plane)+'_'+str(bar)].Fill(x.second,dL)
                               Sleft+=x.second
                      else: 
                         if s==2 and smallSiPMchannel(x.first): rc = h['signalSR_'+sdict[s]+str(s*10+plane)+'_'+str(bar)].Fill(x.second,dR)
                         else:
                               rc = h['signalR_'+sdict[s]+str(s*10+plane)+'_'+str(bar)].Fill(x.second,dR)
                               Sright+=x.second
                  rc = h['signalTL_'+sdict[s]+str(s*10+plane)+'_'+str(bar)].Fill(Sleft,dL)
                  rc = h['signalTR_'+sdict[s]+str(s*10+plane)+'_'+str(bar)].Fill(Sright,dR)

#   look at delta time vs track X, works only for horizontal planes.
                  dt = aHit.GetDeltaT()
                  if aHit.isVertical(): h['dtLRvsX_'+sdict[s]+str(s*10+plane)].Fill(yEx,dt*1E9/freq)
                  else:                             h['dtLRvsX_'+sdict[s]+str(s*10+plane)].Fill(xEx,dt*1E9/freq)

    theTrack.Delete()
 ut.writeHists(h,'MuFilterEff_run'+str(options.runNumber)+'.root')

def mips(readHists=False):
# plot mean sipm channel fired vs X
    if readHists:
        for x in h: 
            if hasattr(x,'Reset'): x.Reset()
        ut.readHists(h,'LandauFits_run'+str(options.runNumber)+'.root')
    s = 2
    for plane in range(5):
        for bar in range(10):
           for p in ['L','R']:
               for T in ['','T']:
                    name = 'signal'+T+p+'_US'+str(s*10+plane)+'_'+str(bar)
                    histo = h[name]
                    for x in  ['M','W','S','eM','eW','eS']:
                      h[x+name]=histo.ProjectionY(x+name)
                      h[x+name].Reset()
                      h[x+name].SetTitle(histo.GetName()+';distance [cm]')
                    for n in range(1,h['M'+name].GetNbinsX()+1):
                              h[name+'-X'+str(n)] = h[name].ProjectionX(name+'-X'+str(n),n,n)
                              tmp = h[name+'-X'+str(n)]
                              if tmp.GetEntries()>10:
                                        print('Fit ',name,n)
                                        if T=='T': bmin,bmax = 0,150
                                        else: bmin,bmax = 0,30
                                        res = fit_langau(tmp,'L',bmin,bmax)
                                        if not res: continue
                                        h['M'+name].SetBinContent(n,res.Parameter(1))
                                        h['eM'+name].SetBinContent(n,res.ParError(1))
                                        h['W'+name].SetBinContent(n,res.Parameter(0))
                                        h['eW'+name].SetBinError(n,res.ParError(0))
                                        h['S'+name].SetBinContent(n,res.Parameter(3))
                                        h['eS'+name].SetBinError(n,res.ParError(3))
               name = 'nSiPMs'+p+'_US'+str(s*10+plane)+'_'+str(bar)
               histo = h[name]
               x='N'
               h[x+name]=histo.ProjectionY(x+name)
               h[x+name].Reset()
               h[x+name].SetTitle(histo.GetName()+';distance [cm]')
               for n in range(1,h[x+name].GetNbinsX()+1):
                      tmp = h[name].ProjectionX('tmp',n,n)
                      if tmp.GetEntries()<10: continue
                      h[x+name].SetBinContent(n,tmp.GetMean())
                      h[x+name].SetBinError(n,tmp.GetRMS())

# make DS
# add all bars in one plane
    s=3
    for plane in range(4):
       for p in ['L','R']:
          name = 'signal'+p+'_DS'+str(s*10+plane)
          h[name]=h[name+'_'+str(0)].Clone(name)
          for bar in range(60):
              h[name].Add(h[name+'_'+str(bar)])
#
          histo = h[name]
          for x in  ['M','W','S']:
                h[x+name]=histo.ProjectionY(x+name)
                h[x+name].Reset()
                h[x+name].SetTitle(histo.GetName()+';distance [cm]')
          for n in range(1,h['M'+name].GetNbinsX()+1):
                 h[name+'-X'+str(n)] = h[name].ProjectionX(name+'-X'+str(n),n,n)
                 tmp = h[name+'-X'+str(n)]
                 if tmp.GetEntries()>10:
                    print('Fit ',name,n)
                    bmin,bmax = 0,80
                    res = fit_langau(tmp,'L',bmin,bmax)
                    if not res: continue
                    h['M'+name].SetBinContent(n,res.Parameter(1))
                    h['M'+name].SetBinError(n,res.ParError(1))
                    h['W'+name].SetBinContent(n,res.Parameter(0))
                    h['W'+name].SetBinError(n,res.ParError(0))
                    h['S'+name].SetBinContent(n,res.Parameter(3))
                    h['S'+name].SetBinError(n,res.ParError(3))

    ut.writeHists(h,'LandauFits_run'+str(options.runNumber)+'.root')

def plotMips(readhisto=True):
    if readhisto:  ut.readHists(h,'LandauFits_run'+str(options.runNumber)+'.root')
    langau = ROOT.TF1('Langau',langaufun,0.,100.,4)
    ut.bookCanvas(h,'Msignal','',1200,2000,2,5)
    ut.bookCanvas(h,'WsignalT','',1200,2000,2,5)
    ut.bookCanvas(h,'SsignalT','',1200,2000,2,5)
    ut.bookCanvas(h,'Msignal1','',900,600,1,1)
    ut.bookCanvas(h,'MsignalT','',1200,2000,2,5)
    ut.bookCanvas(h,'MsignalT1','',900,600,1,1)
    ut.bookCanvas(h,'NnSiPMs1','',900,600,1,1)
    ut.bookCanvas(h,'NnSiPMs','',1200,2000,2,5)
#example plots:
    for T in ['','T']:
       name = 'signal'+T+'L_US22_5-X10'
       tc = h['Msignal'+T+'1'].cd()
       h[name].Draw()
       tc.Update()
       stats = h[name].FindObject('stats')
       stats.SetOptFit(1111111)
       stats.SetX1NDC(0.51)
       stats.SetY1NDC(0.54)
       stats.SetX2NDC(0.98)
       stats.SetY2NDC(0.94)
       tc.Update()
       myPrint(h['Msignal'+T+'1'],'signal'+T+'1')
    tc = h['NnSiPMs1'].cd(1)
    h['nSiPMs1'] = h['nSiPMsL_US21_5'].ProjectionX('nSiPMs1',1,9)
    h['nSiPMs1'].Draw('hist')
    tc.Update()
    myPrint(h['NnSiPMs1'],'nSiPMs1')

    s=2
    k=1
    for plane in range(5):
           for p in ['L','R']:
            for t in ['Msignal','MsignalT','NnSiPMs','WsignalT','SsignalT']:
                tc = h[t].cd(k)
                first = True
                for bar in range(10):
                     color = ROOT.kMagenta + (5-bar)
                     name = t+p+'_US'+str(s*10+plane)+'_'+str(bar)
                     h[name].SetStats(0)
                     h[name].SetLineColor(color)
                     if first:
                        h[name].SetMinimum(0.)
                        if name.find('MsignalT')==0:  
                                   h[name].SetMaximum(100.)
                                   h[name].SetMinimum(0.)
                                   h[name].SetTitle('QDC sum;d [cm]')
                        elif name.find('Msignal')==0:  
                                   h[name].SetMaximum(20.)
                                   h[name].SetMinimum(0.)
                                   h[name].SetTitle('QDC;d [cm]')
                        elif name.find('SsignalT')==0:  
                                   h[name].SetMaximum(20.)
                                   h[name].SetTitle('sigma;d [cm]')
                        elif name.find('WsignalT')==0: 
                                   h[name].SetMaximum(20.)
                                   h[name].SetTitle('width;d [cm]')
                        h[name].DrawCopy()
                        if  t == 'NnSiPMs' and k==1: 
                             tc = h['NnSiPMs1'].cd(1)
                             h[name].SetMinimum(3)
                             h[name].Draw()
                        first = False
                     h[name].DrawCopy('same')
                     if  t == 'NnSiPMs': 
                          tc = h['NnSiPMs1'].cd(1)
                          h[name].Draw('same')
            k+=1
    for t in ['Msignal','MsignalT','NnSiPMs','WsignalT','SsignalT']:             myPrint(h[t],t)
    myPrint(h['NnSiPMs1'],'nSiPMsAll')
# DS
    ut.bookCanvas(h,'Msignal1','',900,600,1,1)
#example plots:
    tc = h['Msignal1'].cd()
    name = 'signalR_DS31-X11'
    h[name].Draw()
    tc.Update()
    stats = h[name].FindObject('stats')
    stats.SetOptFit(1111111)
    stats.SetX1NDC(0.51)
    stats.SetY1NDC(0.54)
    stats.SetX2NDC(0.98)
    stats.SetY2NDC(0.94)
    tc.Update()
    myPrint(h['Msignal1'],'signalDS1')

    ut.bookCanvas(h,'MDsignal2d','',900,600,2,4)
    k=1
    for plane in range(4):
        for p in ['L','R']:
             tc = h['MDsignal2d'].cd(k)
             h['signal'+p+'_DS3'+str(plane)].SetTitle('; QDC ;d [cm]')
             h['signal'+p+'_DS3'+str(plane)].Draw('colz')
             k+=1
    myPrint(h['MDsignal2d'],'MDsignal2d')
    ut.bookCanvas(h,'MDSsignal','',1200,900,1,1)
    plColor={0:ROOT.kBlue,1:ROOT.kGreen,2:ROOT.kCyan,3:ROOT.kOrange}
    pMarker={'L':22,'R':23}
    slopes={}
    for p in ['L','R']:
         for plane in range(4):
              hist = h['Msignal'+p+'_DS3'+str(plane)]
              if hist.GetEntries()<1: continue
              hist.SetStats(0)
              hist.SetTitle(";distance [cm]")
              hist.SetMarkerStyle(pMarker[p])
              hist.SetMarkerColor(plColor[plane])
              hist.SetLineColor(plColor[plane])
              if p=='R' or plane%2==1: rc=hist.Fit('expo','S','',0,60)
              if p=='L' and plane%2==0:  rc=hist.Fit('expo','S','',20,80)
              res = rc.Get()
              if res:              slopes[str(plane)+p]=[res.Parameter(1),res.ParError(1)]
              hist.GetFunction('expo').SetLineColor(plColor[plane])

    h['MsignalR_DS30'].SetMaximum(60)
    h['MsignalR_DS30'].Draw()
    y=0.12
    for p in ['L','R']:
         for plane in range(4):
             hist = h['Msignal'+p+'_DS3'+str(plane)]
             if hist.GetEntries()<1: continue
             hist.Draw('same')
             pp = p
             if plane%2==1: pp='T'
             txt = "%i%s (%5.1F+/-%5.1F)cm"%(plane,pp,-1./slopes[str(plane)+p][0],slopes[str(plane)+p][1]/slopes[str(plane)+p][0]**2)
             latex.DrawLatexNDC(0.3,0+y,txt)
             y += 0.05
    myPrint(h['MDSsignal'],'DSattenuation')

def analyze_EfficiencyAndResiduals(readHists=False):
  if readHists:   ut.readHists(h,'MuFilterEff_run'+str(options.runNumber)+'.root')
  for proj in ['X','Y']:
   ut.bookCanvas(h,'EVetoUS'+proj,'',1200,2000,4,7)
   ut.bookCanvas(h,'EDS'+proj,'',1200,2000,3,7)
   k = 1
   for s in  [1,2,3]:
    if s==3: k=1
    sy = sdict[s]
    tname = 'EVetoUS'+proj
    if s==3: tname = 'EDS'+proj
    for plane in range(systemAndPlanes[s]):
     tc = h[tname].cd(k)
     h['track_'+sy+str(s*10+plane)].Draw('colz')
     k+=1
     for side in ['L','R','S']:
      if s==3 and side=='S': continue
      tc = h[tname].cd(k)
      k+=1
      res = h['res'+proj+'_'+sy+side+str(s*10+plane)]
      print(proj,sy,side,s,plane,res.GetEntries(),k-1,tname)
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
      tracks = h['track_'+sy+str(s*10+plane)].GetEntries()
      if tracks >0:
         eff = fitResult.Parameter(0)/tracks
         effErr = fitResult.ParError(0)/tracks
         latex.DrawLatexNDC(0.2,0.8,'eff=%5.2F+/-%5.2F%%'%(eff,effErr))
   myPrint(h['EVetoUS'+proj],'EVetoUS'+proj)
   myPrint(h['EDS'+proj],'EDS'+proj)

  ut.bookCanvas(h,'T','',800,1600,1,7)
  ut.bookCanvas(h,'TDS','',800,1600,1,7)
  latex.SetTextColor(ROOT.kRed)
  k=1
  for s in  [1,2,3]:
    sy = sdict[s]
    tname = 'T'
    if s==3: 
        tname = 'T'+sy
        k=1
    for plane in range(systemAndPlanes[s]):
     tc = h[tname].cd(k)
     k+=1
     hist = h['dtLRvsX_'+sy+str(s*10+plane)]
     hist.SetStats(0)
     hist.Draw('colz')
# get time x correlation, X = m*dt + b
     h['gdtLRvsX_'+sy+str(s*10+plane)] = ROOT.TGraph()
     g = h['gdtLRvsX_'+sy+str(s*10+plane)]
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
     if not result:continue
     if result.Parameter(1)>0:
        m = 1./result.Parameter(1)
        b = -result.Parameter(0) * m
        txt = 'dt X relation: X = #frac{dt}{%5.2F} +%5.2F '%(1./m,b)
        latex.DrawLatexNDC(0.2,0.8,txt)
  myPrint(h['T'],'dTvsX_VetoUS')
  myPrint(h['TDS'],'dTvsX_DS')

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
     if not result: continue
     if result.Parameter(1)>0:
         m = 1./result.Parameter(1)
         b = -result.Parameter(0) * m
         txt = 'dt X relation: X = #frac{dt}{%5.2F} +%5.2F '%(1./m,b)
         latex.DrawLatexNDC(0.2,0.8,txt)
  myPrint(h['TDS'],'dTvsXDS')

#  Scifi specific code
def Scifi_xPos(detID):
        orientation = (detID//100000)%10
        nStation = 2*(detID//1000000-1)+orientation
        mat   = (detID%100000)//10000
        X = detID%1000+(detID%10000)//1000*128
        return [nStation,mat,X]   # even numbers are Y (horizontal plane), odd numbers X (vertical plane)

def Scifi_slopes(Nev=-1):
    A,B = ROOT.TVector3(),ROOT.TVector3()
    ut.bookHist(h,'slopesX','slope diffs',1000,-1.0,1.0)
    ut.bookHist(h,'slopesY','slope diffs',1000,-1.0,1.0)
    ut.bookHist(h,'clX','cluster size',10,0.5,10.5)
    ut.bookHist(h,'clY','cluster size',10,0.5,10.5)
# assuming cosmics make straight line
    if Nev < 0 : Nev = eventTree.GetEntries()
    for event in eventTree:
        if Nev<0: break
        Nev=Nev-1
        clusters = []
        hitDict = {}
        for k in range(event.Digi_ScifiHits.GetEntries()):
            d = event.Digi_ScifiHits[k]
            if not d.isValid(): continue 
            hitDict[d.GetDetectorID()] = k
        hitList = list(hitDict.keys())
        if len(hitList)>0:
              hitList.sort()
              tmp = [ hitList[0] ]
              cprev = hitList[0]
              ncl = 0
              last = len(hitList)-1
              hitlist = ROOT.std.vector("sndScifiHit*")()
              for i in range(len(hitList)):
                   if i==0 and len(hitList)>1: continue
                   c=hitList[i]
                   if (c-cprev)==1: 
                        tmp.append(c)
                   if (c-cprev)!=1 or c==hitList[last]:
                        first = tmp[0]
                        N = len(tmp)
                        hitlist.clear()
                        for aHit in tmp: hitlist.push_back( event.Digi_ScifiHits[hitDict[aHit]])
                        aCluster = ROOT.sndCluster(first,N,hitlist,scifiDet)
                        clusters.append(aCluster)
                        if c!=hitList[last]:
                             ncl+=1
                             tmp = [c]
                   cprev = c
        xHits = {}
        yHits = {}
        for s in range(5):
             xHits[s]=[]
             yHits[s]=[]
        for aCl in clusters:
             aCl.GetPosition(A,B)
             vertical = int(aCl.GetFirst()/100000)%10==1
             s = int(aCl.GetFirst()/1000000)-1
             if vertical: 
                  xHits[s].append(ROOT.TVector3(A))
                  rc = h['clX'].Fill(aCl.GetN())
             else: 
                  yHits[s].append(ROOT.TVector3(A))
                  rc = h['clY'].Fill(aCl.GetN())
        proj = {'X':xHits,'Y':yHits}
        for p in proj:
          sls = []
          for  s1 in range(0,5):
             if len(proj[p][s1]) !=1: continue
             cl1 = proj[p][s1][0]
             for s2 in range(s1+1,5):
                if len(proj[p][s2]) !=1: continue
                cl2 = proj[p][s2][0]
                dz = abs(cl1[2]-cl2[2])
                if dz < 5: continue
                dzRep = 1./dz
                m =  dzRep*(cl2-cl1)
                sls.append( m )
          for ix1 in range(0,len(sls)-1):
             for ix2 in range(ix1+1,len(sls)):
                if p=="X": rc = h['slopes'+p].Fill( sls[ix2][0]-sls[ix1][0])
                if p=="Y": rc = h['slopes'+p].Fill( sls[ix2][1]-sls[ix1][1])
    ut.bookCanvas(h,'slopes',' ',1024,768,1,2)
    h['slopes'].cd(1)
    h['slopesX'].GetXaxis().SetRangeUser(-0.2,0.2)
    h['slopesX'].SetTitle('x projection; delta slope [rad]')
    h['slopesX'].Draw()
    h['slopesX'].Fit('gaus','S','',-0.02,0.02)
    h['slopes'].Update()
    stats = h['slopesX'].FindObject('stats')
    stats.SetOptFit(111)
    h['slopes'].cd(2)
    h['slopesY'].GetXaxis().SetRangeUser(-0.2,0.2)
    h['slopesY'].SetTitle('y projection; delta slope [rad]')
    h['slopesY'].Draw()
    h['slopesY'].Fit('gaus','S','',-0.02,0.02)
    h['slopes'].Update()
    stats = h['slopesY'].FindObject('stats')
    stats.SetOptFit(111)
    for event in eventTree:
        if Nev<0: break
        Nev=Nev-1
        clusters = []
        hitDict = {}
        for k in range(event.Digi_ScifiHits.GetEntries()):
            d = event.Digi_ScifiHits[k]
            if not d.isValid(): continue 
            hitDict[d.GetDetectorID()] = k
        hitList = list(hitDict.keys())
        if len(hitList)>0:
              hitList.sort()
              tmp = [ hitList[0] ]
              cprev = hitList[0]
              ncl = 0
              last = len(hitList)-1
              hitlist = ROOT.std.vector("sndScifiHit*")()
              for i in range(len(hitList)):
                   if i==0 and len(hitList)>1: continue
                   c=hitList[i]
                   if (c-cprev)==1: 
                        tmp.append(c)
                   if (c-cprev)!=1 or c==hitList[last]:
                        first = tmp[0]
                        N = len(tmp)
                        hitlist.clear()
                        for aHit in tmp: hitlist.push_back( event.Digi_ScifiHits[hitDict[aHit]])
                        aCluster = ROOT.sndCluster(first,N,hitlist,scifiDet)
                        clusters.append(aCluster)
                        if c!=hitList[last]:
                             ncl+=1
                             tmp = [c]
                   cprev = c
        xHits = {}
        yHits = {}
        for s in range(5):
             xHits[s]=[]
             yHits[s]=[]
        for aCl in clusters:
             aCl.GetPosition(A,B)
             vertical = int(aCl.GetFirst()/100000)%10==1
             s = int(aCl.GetFirst()/1000000)-1
             if vertical: 
                  xHits[s].append(ROOT.TVector3(A))
                  rc = h['clX'].Fill(aCl.GetN())
             else: 
                  yHits[s].append(ROOT.TVector3(A))
                  rc = h['clY'].Fill(aCl.GetN())
        proj = {'X':xHits,'Y':yHits}
        for p in proj:
          sls = []
          for  s1 in range(0,5):
             if len(proj[p][s1]) !=1: continue
             cl1 = proj[p][s1][0]
             for s2 in range(s1+1,5):
                if len(proj[p][s2]) !=1: continue

def mergeSignals(hstore):
  ut.bookHist(hstore,'signalAll','signal all mat',150,0.0,150.)
  for mat in range(30):
    hstore['signalAll'].Add(hstore['sig_'+str(mat)])
  hstore['signalAll'].Scale(1./hstore['signalAll'].GetSumOfWeights())

def signalZoom(smax):
  for mat in range(30):
    h['sig_'+str(mat)].GetXaxis().SetRangeUser(0.,smax)
    tc = h['signal'].cd(mat+1)
    tc.Update()

def scifi_beamSpot():
    A,B = ROOT.TVector3(),ROOT.TVector3()
    ut.bookHist(h,'bs','beam spot',100,-100.,10.,100,0.,80.)
    for event in eventTree:
        xMean = 0
        yMean = 0
        w=0
        for d in event.Digi_ScifiHits:
            detID = d.GetDetectorID()
            s = int(detID/1000000)
            modules['Scifi'].GetSiPMPosition(detID,A,B)
            vertical = int(detID/100000)%10==1
            if vertical: xMean+=A[0]
            else: yMean+=A[1]
            w+=1
        rc = h['bs'].Fill(xMean/w,yMean/w)

