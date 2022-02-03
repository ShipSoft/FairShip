#python -i MufiScifi.py -r 46 -p /eos/experiment/sndlhc/testbeam/MuFilter/TB_data_commissioning/sndsw/ -g geofile_sndlhc_H6.root

import ROOT,os
import time
import ctypes
from array import array
# for fixing a root bug,  will be solved in the forthcoming 6.26 release.
ROOT.gInterpreter.Declare("""
#include "MuFilterHit.h"
#include "AbsMeasurement.h"
#include "TrackPoint.h"

void fixRoot(MuFilterHit& aHit,std::vector<int>& key,std::vector<float>& value) {
   std::map<int,float> m = aHit.GetAllSignals();
   std::map<int, float>::iterator it = m.begin();
   while (it != m.end())
    {
        key.push_back(it->first);
        value.push_back(it->second);
        it++;
    }
}
void fixRoot(MuFilterHit& aHit, std::vector<TString>& key,std::vector<float>& value) {
   std::map<TString, float> m = aHit.SumOfSignals();
   std::map<TString, float>::iterator it = m.begin();
   while (it != m.end())
    {
        key.push_back(it->first);
        value.push_back(it->second);
        it++;
    }
}

void fixRoot(std::vector<genfit::TrackPoint*>& points, std::vector<int>& d,std::vector<int>& k) {
      for(std::size_t i = 0; i < points.size(); ++i) {
        genfit::AbsMeasurement*  m = points[i]->getRawMeasurement();
        d.push_back( m->getDetId() );
        k.push_back( int(m->getHitId()/1000) );
    }
}
""")


Tkey  = ROOT.std.vector('TString')()
Ikey   = ROOT.std.vector('int')()
Value = ROOT.std.vector('float')()

def map2Dict(aHit,T='GetAllSignals'):
     if T=="SumOfSignals":
        key = Tkey
     elif T=="GetAllSignals":
        key = Ikey
     else: 
           print('use case not known',T)
           1/0
     key.clear()
     Value.clear()
     ROOT.fixRoot(aHit,key,Value)
     theDict = {}
     for k in range(key.size()):
         if T=="SumOfSignals": theDict[key[k].Data()] = Value[k]
         else: theDict[key[k]] = Value[k]
     return theDict

import rootUtils as ut
import shipunit as u
h={}
from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-r", "--runNumber", dest="runNumber", help="run number", type=int,required=True)
parser.add_argument("-p", "--path", dest="path", help="run number",required=False,default="")
parser.add_argument("-f", "--inputFile", dest="fname", help="file name for MC", type=str,default=None,required=False)
parser.add_argument("-g", "--geoFile", dest="geoFile", help="geofile", required=True)
parser.add_argument("-b", "--heartBeat", dest="heartBeat", help="heart beat", default=10000,type=int)
parser.add_argument("-c", "--command", dest="command", help="command", default="")
parser.add_argument("-n", "--nEvents", dest="nEvents", help="number of events", default=-1,type=int)
parser.add_argument("-t", "--trackType", dest="trackType", help="DS or Scifi", default="DS")
options = parser.parse_args()

path = options.path
if path.find('eos')>0: path = os.environ['EOSSHIP']+options.path

import SndlhcGeo
if (options.geoFile).find('../')<0: geo = SndlhcGeo.GeoInterface(path+options.geoFile)
else:                                         geo = SndlhcGeo.GeoInterface(options.geoFile[3:])
MuFilter = geo.modules['MuFilter']
Scifi       = geo.modules['Scifi']
nav = ROOT.gGeoManager.GetCurrentNavigator()

A,B,locA,locB,globA,globB    = ROOT.TVector3(),ROOT.TVector3(),ROOT.TVector3(),ROOT.TVector3(),ROOT.TVector3(),ROOT.TVector3()
latex = ROOT.TLatex()


# MuFilter mapping of planes and bars 
systemAndPlanes  = {1:2,2:5,3:7}
systemAndBars     = {1:7,2:10,3:60}
def systemAndOrientation(s,plane):
   if s==1 or s==2: return "horizontal"
   if plane%2==1 or plane == 6: return "vertical"
   return "horizontal"

systemAndChannels     = {1:[8,0],2:[6,2],3:[1,0]}
sdict                     = {1:'Veto',2:'US',3:'DS'}

freq      = 160.E6
TDC2ns = 1E9/freq

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

def fit_langau(hist,o,bmin,bmax,opt=''):
   if opt == 2:
     params = {0:'Width(scale)',1:'mostProbable',2:'norm',3:'sigma',4:'N2'}
     F = ROOT.TF1('langau',langaufun,0,200,len(params))
   else:
     params = {0:'Width(scale)',1:'mostProbable',2:'norm',3:'sigma'}
     F = ROOT.TF1('langau',twoLangaufun,0,200,len(params))
   for p in params: F.SetParName(p,params[p])
   rc = hist.Fit('landau','S'+o,'',bmin,bmax)
   res = rc.Get()
   if not res: return res
   F.SetParameter(2,res.Parameter(0))
   F.SetParameter(1,res.Parameter(1))
   F.SetParameter(0,res.Parameter(2))
   F.SetParameter(3,res.Parameter(2))
   F.SetParameter(4,0)
   F.SetParLimits(0,0,100)
   F.SetParLimits(1,0,100)
   F.SetParLimits(3,0,10)
   rc = hist.Fit(F,'S'+o,'',bmin,bmax)
   res = rc.Get()
   return res

def twoLangaufun(x,par):
   N1 = langaufun(x,par)
   par2 = [par[0],par[1]*2,par[4],par[3]]
   N2 = langaufun(x,par2)
   return N1+abs(N2)

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
      xlow = max(0,x[0] - sc * par[3])
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
     tc.Update()
     tc.Print(name+'-run'+str(options.runNumber)+'.png')
     if withRootFile: tc.Print(name+'-run'+str(options.runNumber)+'.root')

def makeAnimation(histname,j0=1,j1=2,animated=True, findMinMax=True, lim = 50):
    ut.bookCanvas(h,'ani','',900,800,1,1)
    tc = h['ani'].cd()
    jmin,jmax = j0,j1
    if findMinMax:
       jmin,jmax = 0,0
       for j in range(j0,j1):
            tmp = histname.replace('$$$',str(j))
            if tmp in h:
                  if h[tmp].GetEntries()>lim:
                       jmin = j
                       print(j,tmp,h[tmp].GetEntries())
                       break
       for j in range(j1,j0,-1):
            tmp = histname.replace('$$$',str(j))
            if tmp in h:
                  if h[tmp].GetEntries()>lim:
                       jmax = j
                       break
    for j in range(jmin,jmax):
            tmp = histname.replace('$$$',str(j))
            h[tmp].Draw()
            tc.Update()
            stats = h[tmp].FindObject('stats')
            stats.SetOptFit(1111111)
            h[tmp].Draw()
            if animated: 
               h['ani'].Print('picAni'+str(j)+'.png')
            else:
               rc = input("hit return for next event or q for quit: ")
               if rc=='q': break
    if animated and jmax > jmin: 
           os.system("convert -delay 60 -loop 0 picAni*.png "+histname+".gif")
           os.system('rm picAni*.png')



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
    print("     Scifi unbiased residuals for an optional set of alignment constants")
    print("              Scifi_residuals(Nev=-1,NbinsRes=100,xmin=-500.,alignPar=False), xmin = low edge of residual histos in microns")
    print(" ")
    print("     Minimization of Scifi alignment constants")
    print("              minimizeAlignScifi(first=True,level=1,minuit=False)")
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

def Scifi_hitMaps(Nev=options.nEvents):
 scifi = geo.modules['Scifi']
 A=ROOT.TVector3()
 B=ROOT.TVector3()
 for s in range(10):
    ut.bookHist(h,'posX_'+str(s),'x',2000,-100.,100.)
    ut.bookHist(h,'posY_'+str(s),'y',2000,-100.,100.)
 for mat in range(30):
    ut.bookHist(h,'mat_'+str(mat),'hit map / mat',512,-0.5,511.5)
    ut.bookHist(h,'sig_'+str(mat),'signal / mat',150,0.0,150.)
 N=-1
 if Nev < 0 : Nev = eventTree.GetEntries()
 for event in eventTree:
    N+=1
    if N%options.heartBeat == 0: print('event ',N,' ',time.ctime())
    if N>Nev: break
    for aHit in event.Digi_ScifiHits:
        if not aHit.isValid(): continue
        X =  Scifi_xPos(aHit.GetDetectorID())
        rc = h['mat_'+str(X[0]*3+X[1])].Fill(X[2])
        rc  = h['sig_'+str(X[0]*3+X[1])].Fill(aHit.GetSignal(0))
        scifi.GetSiPMPosition(aHit.GetDetectorID(),A,B)
        if aHit.isVertical(): rc = h['posX_'+str(X[0])].Fill(A[0])
        else:                     rc = h['posY_'+str(X[0])].Fill(A[1])

 ut.bookCanvas(h,'hitmaps',' ',1024,768,6,5)
 ut.bookCanvas(h,'signal',' ',1024,768,6,5)
 for mat in range(30):
    tc = h['hitmaps'].cd(mat+1)
    A = h['mat_'+str(mat)].GetSumOfWeights()/512.
    if h['mat_'+str(mat)].GetMaximum()>10*A: h['mat_'+str(mat)].SetMaximum(10*A)
    h['mat_'+str(mat)].Draw()
    tc = h['signal'].cd(mat+1)
    h['sig_'+str(mat)].Draw()

def Mufi_hitMaps(Nev = options.nEvents):
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
    if N%options.heartBeat == 0: print('event ',N,' ',time.ctime())
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
                    if l<3: l+=1
        if not key in planes: planes[key] = {}
        sumSignal = map2Dict(aHit,'SumOfSignals')
        planes[key][bar] = [sumSignal['SumL'],sumSignal['SumR']]
        nSiPMs = aHit.GetnSiPMs()
        nSides  = aHit.GetnSides()
# check left/right
        allChannels = map2Dict(aHit,'GetAllSignals')
        if nSides==2:
           Nleft    = 0
           Nright = 0
           Sleft    = 0
           Sright = 0
           for c in allChannels:
              if  nSiPMs > c:  # left side
                    Nleft+=1
                    Sleft+=allChannels[c]
              else:
                    Nright+=1
                    Sright+=allChannels[c]
           rc = h['leftvsright_'+str(s)].Fill(Nleft,Nright)
           rc = h['leftvsright_signal_'+str(s)].Fill(Sleft,Sright)

        for c in allChannels:
            channel = bar*nSiPMs*nSides + c
            rc = h['hit_'+str(s)+str(l)].Fill( int(channel))
            rc = h['bar_'+str(s)+str(l)].Fill(bar)
            if s==2 and smallSiPMchannel(c) : rc  = h['sigS_'+str(s)+str(l)].Fill(allChannels[c])
            elif c<nSiPMs: rc  = h['sigL_'+str(s)+str(l)].Fill(allChannels[c])
            else             :             rc  = h['sigR_'+str(s)+str(l)].Fill(allChannels[c])
            rc  = h['sig_'+str(s)+str(l)].Fill(allChannels[c])
        allChannels.clear()
    maxOneBar = True
    for key in planes:
        if len(planes[key]) > 2: maxOneBar = False
    if withX and maxOneBar:  beamSpot()
    
 S = {1:[1800,800,2,1],2:[1800,1500,2,3],3:[1800,1800,2,4]}
 for s in S:
   ut.bookCanvas(h,'hitmaps' +str(s),' ',S[s][0],S[s][1],S[s][2],S[s][3])
   ut.bookCanvas(h,'barmaps'+str(s),' ',S[s][0],S[s][1],S[s][2],S[s][3])
   ut.bookCanvas(h,'signal'    +str(s),' ',S[s][0],S[s][1],S[s][2],S[s][3])
   ut.bookCanvas(h,'Tsignal'   +str(s),' ',S[s][0],S[s][1],S[s][2],S[s][3])

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


 for canvas in ['signalUSVeto','LR','USBars']:
      h[canvas].Update()
      myPrint(h[canvas],canvas)
 for canvas in ['hitmaps','barmaps','signal','Tsignal']:
      for s in range(1,4):
         h[canvas+str(s)].Update()
         myPrint(h[canvas+str(s)],canvas+sdict[s])

def eventTime(Nev=options.nEvents):
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

def TimeStudy(Nev=options.nEvents,withDisplay=False):
 if Nev < 0 : Nev = eventTree.GetEntries()
 ut.bookHist(h,'Vetotime','time',1000,0.,50.)
 ut.bookHist(h,'UStime','time',1000,0.,50.)
 ut.bookHist(h,'DStime','time',1000,0.,50.)
 ut.bookHist(h,'Stime','time',1000,0.,50.)
 ut.bookHist(h,'SvsDStime','; mean Scifi time [ns];mean Mufi time [ns]',100,0.,50.,100,0.,50.)
 ut.bookHist(h,'VEvsUStime','; mean US time [ns];mean VE time [ns]',100,0.,50.,100,0.,50.)
 ut.bookCanvas(h,'T','',900,1200,1,2)
 tc = h['T'].cd(1)
 h['Vetotime'].SetLineColor(ROOT.kOrange)
 h['UStime'].SetLineColor(ROOT.kGreen)
 h['DStime'].SetLineColor(ROOT.kRed)
 N=-1
 for event in eventTree:
   N+=1
   if N>Nev: break
   h['UStime'].Reset()
   h['DStime'].Reset()
   h['Vetotime'].Reset()
   h['Stime'].Reset()
   for aHit in eventTree.Digi_MuFilterHits:
     T = aHit.GetAllTimes()
     s = aHit.GetDetectorID()//10000
     for x in T:
       t = x.second*TDC2ns
       if t>0: 
           if s==1: rc = h['Vetotime'].Fill(t)
           if s==2: rc = h['UStime'].Fill(t)
           if s==3: rc = h['DStime'].Fill(t)
   stations = {}
   for aHit in eventTree.Digi_ScifiHits:
      t = aHit.GetTime()*TDC2ns
      rc = h['Stime'].Fill(t)
      stations[aHit.GetDetectorID()//1000000] = 1
   if len(stations)>3:
       rc = h['SvsDStime'].Fill(h['Stime'].GetMean(),h['DStime'].GetMean())
       rc = h['VEvsUStime'].Fill(h['UStime'].GetMean(),h['Vetotime'].GetMean())
   if withDisplay:
     tc = h['T'].cd(1)
     h['UStime'].Draw()
     h['DStime'].Draw('same')
     h['Vetotime'].Draw('same')
     tc = h['T'].cd(2)
     h['Stime'].Draw()
     rc = input("hit return for next event or q for quit: ")
     if rc=='q': break
 tc = h['T'].cd(1)
 h['SvsDStime'].Draw('colz')
 tc = h['T'].cd(2)
 h['SvsDStime_mufi'] = h['SvsDStime'].ProjectionY('SvsDStime_mufi')
 h['SvsDStime_scifi'] = h['SvsDStime'].ProjectionX('SvsDStime_scifi')
 h['Vetime'] = h['VEvsUStime'].ProjectionY('Vetime')
 h['UStime'] = h['VEvsUStime'].ProjectionX('UStime')
 h['SvsDStime_mufi'].SetLineColor(ROOT.kRed)
 h['SvsDStime_scifi'].SetLineColor(ROOT.kGreen)
 h['UStime'].SetLineColor(ROOT.kBlue)
 h['Vetime'].SetLineColor(ROOT.kOrange)
 h['UStime'].SetStats(0)
 h['Vetime'].SetStats(0)
 h['SvsDStime_mufi'].SetStats(0)
 h['SvsDStime_scifi'].SetStats(0)
 h['SvsDStime_mufi'].Draw()
 h['SvsDStime_scifi'].Draw('same')
 h['UStime'].Draw('same')
 h['Vetime'].Draw('same')

def beamSpot():
   trackTask.ExecuteTask()
   Xbar = -10
   Ybar = -10
   for  aTrack in eventTree.fittedTracks:
         state = aTrack.getFittedState()
         pos    = state.getPos()
         rc = h['bs'].Fill(pos.x(),pos.y())
         points = aTrack.getPoints()
         keys     = ROOT.std.vector('int')()
         detIDs = ROOT.std.vector('int')()
         ROOT.fixRoot(points, detIDs,keys)
         for k in range(keys.size()):
             #                                     m = p.getRawMeasurement()
             detID =detIDs[k] # m.getDetId()
             key = keys[k]          # m.getHitId()//1000 # for mufi
             aHit = eventTree.Digi_MuFilterHits[key]
             if aHit.GetDetectorID() != detID: continue # not a Mufi hit
             s = detID//10000
             l  = (detID%10000)//1000  # plane number
             bar = (detID%1000)
             if s>2: 
               l=2*l
               if bar>59:
                    bar=bar-60
                    if l<6: l+=1
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
           if bar<60 or p==3: plane = s*10+2*p
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

def Scifi_track(nPlanes = 8, nClusters = 11):
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
    if len(check)<nPlanes or nclusters > nClusters: return -1
# build trackCandidate
    hitlist = {}
    for k in range(len(clusters)):
           hitlist[k] = clusters[k]
    theTrack = trackTask.fitTrack(hitlist)
    eventTree.ScifiClusters = clusters
    return theTrack

def USshower(Nev=options.nEvents):
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
           S = map2Dict(aHit,'SumOfSignals')
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

def Mufi_Efficiency(Nev=options.nEvents,optionTrack=options.trackType,NbinsRes=100,X=10.):
 
 projs = {1:'Y',0:'X'}
 for s in range(1,6):
    for o in range(2):
       for p in projs:
         ut.bookHist(h,'dtScifivsX_'+str(s)+projs[o],'dt vs x track '+projs[o]+";X [cm]; dt [ns]",100,-10.,40.,260,-8.,5.)
    ut.bookHist(h,'dtScifivsdL_'+str(s),'dt vs dL '+str(s)+";X [cm]; dt [ns]",100,-40.,0.,100,-2.,8.)

 for s in systemAndPlanes:
    for l in range(systemAndPlanes[s]):
      ut.bookHist(h,'dtLRvsX_'+sdict[s]+str(s*10+l),'dt vs x track '+str(s*10+l)+";X [cm]; dt [ns]",100,-70.,30.,260,-8.,5.)
      ut.bookHist(h,'atLRvsX_'+sdict[s]+str(s*10+l),'mean time - T0track vs x '+str(s*10+l)+";X [cm]; dt [ns]",20,-70.,30.,250,-10.,15.0)
      ut.bookHist(h,'VetoatLRvsX_'+sdict[s]+str(s*10+l),'mean time - T0Veto vs x '+str(s*10+l)+";X [cm]; dt [ns]",20,-70.,30.,250,-10.,15.0)

      scale = 1.
      if s==3: scale = 0.4
      for proj in ['X','Y']:
        xmin = -X*NbinsRes/100. * scale
        xmax = -xmin
        for side in ['','L','R','S']:
          ut.bookHist(h,'res'+proj+'_'+sdict[s]+side+str(s*10+l),'residual  '+proj+str(s*10+l),NbinsRes,xmin,xmax,40,-20.,100.)
          ut.bookHist(h,'gres'+proj+'_'+sdict[s]+side+str(s*10+l),'residual  '+proj+str(s*10+l),NbinsRes,xmin,xmax,40,-20.,100.)
          if side=='S': continue
          if side=='':
             if s==1: ut.bookHist(h,'resBar'+proj+'_'+sdict[s]+str(s*10+l),'residual '+proj+str(s*10+l),NbinsRes,xmin,xmax,7,-0.5,6.5)
             ut.bookHist(h,'track_'+sdict[s]+str(s*10+l),'track x/y '+str(s*10+l)+';X [cm];Y [cm]',100,-90.,10.,100,-20.,80.)
             ut.bookHist(h,'locBarPos_'+sdict[s]+str(s*10+l),'bar sizes;X [cm];Y [cm]',100,-100,100,100,-100,100)
             ut.bookHist(h,'locEx_'+sdict[s]+str(s*10+l),'loc track pos;X [cm];Y [cm]',100,-100,100,100,-100,100)
          for bar in range(systemAndBars[s]):
             key = sdict[s]+str(s*10+l)+'_'+str(bar)
             if side=="":
                ut.bookHist(h,'dtLRvsX_'+key,'dt vs x track '+str(s*10+l)+";X [cm]; dt [ns]",100,-70.,30.,260,-8.,5.)
                ut.bookHist(h,'dtF12LRvsX_'+key,'dt vs x track '+str(s*10+l)+";X [cm]; dt [ns]",100,-70.,30.,260,-8.,5.)
                ut.bookHist(h,'dtfastLRvsX_'+key,'dt vs x track '+str(s*10+l)+";X [cm]; dt [ns]",100,-70.,30.,260,-8.,5.)
                ut.bookHist(h,'atLRvsX_'+key,'dt vs x track '+str(s*10+l)+";X [cm]; dt [ns]",100,-70.,30.,260,-8.,5.)
             else:
                ut.bookHist(h,'nSiPMs'+side+'_'+key,'#sipms',16,-0.5,15.5,20,0.,100.)
                for i in range(systemAndChannels[s][1]+systemAndChannels[s][0]):
                        if s==2 and smallSiPMchannel(i):
                            ut.bookHist(h,'signalS'+side+'_'+key+'-c'+str(i),'signal',200,0.,100.,20,0.,100.)
                        else:
                            ut.bookHist(h,'signal'+side+'_'+key+'-c'+str(i),'signal',200,0.,100.,20,0.,100.)
                ut.bookHist(h,'signalT'+side+'_'+key,'signal',400,0.,400.,20,0.,100.)
                ut.bookHist(h,'signalTS'+side+'_'+key,'signal',400,0.,400.,20,0.,100.)
        
                ut.bookHist(h,'signal'+side+'_'+key,'signal',200,0.,100.,20,0.,100.)

 ut.bookHist(h,'resVETOY_1','channel vs residual  1',NbinsRes,xmin,xmax,112,-0.5,111.5)
 ut.bookHist(h,'resVETOY_2','channel vs residual  2',NbinsRes,xmin,xmax,112,-0.5,111.5)

 ut.bookHist(h,'trackslxy','track direction',200,-0.1,0.1,200,-0.1,0.1)
 ut.bookHist(h,'trackslxy_badChi2','track direction',200,-0.1,0.1,200,-0.1,0.1)
 ut.bookHist(h,'tracksChi2Ndof','chi2/ndof',100,0.0,100.,10,-0.5,9.5)
 ut.bookHist(h,'NdofvsNMeas','ndof Nmeas',20,-0.5,19.5,20,-0.5,19.5)

 v = 15.* u.cm/u.ns # signal propagation in fibre, assumption
 if Nev < 0 : Nev = eventTree.GetEntries()
 N=0
 for event in eventTree:
    N+=1
    if N>Nev: break
    if optionTrack=='DS': theTrack = DS_track()
    else                                   : theTrack = Scifi_track()
    if not hasattr(theTrack,"getFittedState"): continue
    if not theTrack.getFitStatus().isFitConverged() and optionTrack!='DS':   # for H8 where only two planes / proj were avaiable
                 theTrack.Delete()
                 continue
# now extrapolate to US and check for hits.
    state = theTrack.getFittedState(0)
    pos   = state.getPos()
    mom = state.getMom()
    fitStatus = theTrack.getFitStatus()
    chi2Ndof = fitStatus.getChi2()/(fitStatus.getNdf()+1E-10)
    rc = h['tracksChi2Ndof'].Fill(chi2Ndof,fitStatus.getNdf())
    rc = h['NdofvsNMeas'].Fill(fitStatus.getNdf(),theTrack.getNumPointsWithMeasurement())
# map clusters to hit keys
    DetID2Key={}
    if event.FindBranch("ScifiClusters") or hasattr(eventTree,'ScifiClusters'):
     for aCluster in event.ScifiClusters:
        for nHit in range(event.Digi_ScifiHits.GetEntries()):
            if event.Digi_ScifiHits[nHit].GetDetectorID()==aCluster.GetFirst():
               DetID2Key[aCluster.GetFirst()] = nHit

    if chi2Ndof> 9 and optionTrack!='DS': 
       rc = h['trackslxy_badChi2'].Fill(mom.x()/mom.Mag(),mom.y()/mom.Mag())
       theTrack.Delete()
       continue
    rc = h['trackslxy'].Fill(mom.x()/mom.Mag(),mom.y()/mom.Mag())
# get T0 from Track
    if optionTrack=='DS':
       # don't know yet what to do
         T0track = 0
         Z0track = 0
    else:
         M = theTrack.getPointWithMeasurement(0)
         W = M.getRawMeasurement()
         detID = W.getDetId()
         hkey  = W.getHitId()
         aHit = event.Digi_ScifiHits[ DetID2Key[detID] ]
         geo.modules['Scifi'].GetSiPMPosition(detID,A,B)
         X = B-pos
         L0 = X.Mag()/v
         # need to correct for signal propagation along fibre
         T0track = aHit.GetTime()*TDC2ns - L0
         TZero = aHit.GetTime()*TDC2ns
         Z0track = pos[2]
         times = {}
         for nM in range(theTrack.getNumPointsWithMeasurement()):
            state   = theTrack.getFittedState(nM)
            posM   = state.getPos()
            M = theTrack.getPointWithMeasurement(nM)
            W = M.getRawMeasurement()
            detID = W.getDetId()
            hkey  = W.getHitId()
            aHit = event.Digi_ScifiHits[ DetID2Key[detID] ]
            geo.modules['Scifi'].GetSiPMPosition(detID,A,B)
            if aHit.isVertical(): X = B-posM
            else: X = A-posM
            L = X.Mag()/v
         # need to correct for signal propagation along fibre
            dT = aHit.GetTime()*TDC2ns - L - T0track - (posM[2] -Z0track)/u.speedOfLight
            ss = str(aHit.GetStation())
            prj = 'X'
            l = posM[0]
            if aHit.isVertical(): 
                 prj='Y'
                 l = posM[1]
            rc = h['dtScifivsX_'+ss+prj].Fill(X.Mag(),dT)
            times[ss+prj]=[aHit.GetTime()*TDC2ns,L*v,detID,l]
         for s in range(1,6):
            if str(s)+'X' in times and  str(s)+'Y' in times:
               deltaT = times[str(s)+'X'][0] - times[str(s)+'Y'][0]
               deltaL = times[str(s)+'X'][1] - times[str(s)+'Y'][1]
               rc = h['dtScifivsdL_'+str(s)].Fill(deltaL,deltaT)
            #print(detID,aHit.GetDetectorID(),aHit.GetTime()*TDC2ns-TZero,dT,L,aHit.GetTime()*TDC2ns - L,T0)

    muHits = {}
    for s in systemAndPlanes:
       for p in range(systemAndPlanes[s]): muHits[s*10+p]=[]
    for aHit in event.Digi_MuFilterHits:
         if not aHit.isValid(): continue
         s = aHit.GetDetectorID()//10000
         p = (aHit.GetDetectorID()//1000)%10
         bar = (aHit.GetDetectorID()%1000)%60
         plane = s*10+p
         if s==3:
           if aHit.isVertical(): plane = s*10+2*p+1
           else:                         plane = s*10+2*p
         muHits[plane].append(aHit)

# get T0 from VETO
    s = 1
    Z0Veto = zPos['MuFilter'][1*10+0]
    dZ = zPos['MuFilter'][1*10+1] - zPos['MuFilter'][1*10+0]
    avT = {}
    for p in range(systemAndPlanes[s]): 
         plane = s*10+p
         if len(muHits[plane])!=1: continue
         aHit = muHits[plane][0]
# check if hit within track extrapolation
         zEx = zPos['MuFilter'][s*10+plane]
         lam = (zEx-pos.z())/mom.z()
         xEx,yEx = pos.x()+lam*mom.x(),pos.y()+lam*mom.y()
         detID = aHit.GetDetectorID()
         MuFilter.GetPosition(detID,A,B)
         D = (A[1]+B[1])/2. - yEx
         if abs(D)>5: continue
         avT[plane] = aHit.GetImpactT()
    T0Veto = -999
    if len(avT)==2:
         T0Veto = (avT[10]+(avT[11]-dZ/u.speedOfLight))/2.

    vetoHits = {0:[],1:[]}
    for s in sdict:
     name = str(s)
     for plane in range(systemAndPlanes[s]):
         zEx = zPos['MuFilter'][s*10+plane]
         lam = (zEx-pos.z())/mom.z()
         xEx,yEx = pos.x()+lam*mom.x(),pos.y()+lam*mom.y()
         # tag with station close by
         if plane ==0: tag = 1
         else: tag = plane -1
         tagged = False
         for aHit in muHits[s*10+tag]:
              detID = aHit.GetDetectorID()
              MuFilter.GetPosition(detID,A,B)
              if aHit.isVertical() : D = (A[0]+B[0])/2. - xEx
              else:                      D = (A[1]+B[1])/2. - yEx
              if abs(D)<5: tagged = True
         #if not tagged: continue
         rc = h['track_'+sdict[s]+str(s*10+plane)].Fill(xEx,yEx)
         for aHit in muHits[s*10+plane]:
              detID = aHit.GetDetectorID()
              bar = (detID%1000)%60
              nSiPMs = aHit.GetnSiPMs()
              nSides  = aHit.GetnSides()
              MuFilter.GetPosition(detID,globA,globB)
              MuFilter.GetLocalPosition(detID,locA,locB)
              globEx = array('d',[xEx,yEx,zEx])
              locEx   = array('d',[0,0,0])
              nav.MasterToLocal(globEx,locEx)
              locPos   = 0.5*  (locA+locB)
              globPos = 0.5 * (globA+globB)
              dy = locPos[1] - locEx[1]
              dx = locPos[0] - locEx[0]
              gdy = globPos[1] - globEx[1]
              gdx = globPos[0] - globEx[0]
              rc = h['locBarPos_'+sdict[s]+str(s*10+plane)].Fill( locPos[0],locPos[1])
              rc = h['locEx_'+sdict[s]+str(s*10+plane)].Fill( locEx[0],locEx[1])
              rc = h['resY_'+sdict[s]+str(s*10+plane)].Fill(dy,locEx[0])
              rc = h['resX_'+sdict[s]+str(s*10+plane)].Fill(dx,locEx[1])
              rc = h['gresY_'+sdict[s]+str(s*10+plane)].Fill(gdy,globEx[0])
              rc = h['gresX_'+sdict[s]+str(s*10+plane)].Fill(gdx,globEx[1])
              S = map2Dict(aHit,'GetAllSignals')
              # check for signal in left / right or small sipm
              left,right,smallL,smallR,Sleft,Sright,SleftS,SrightS = 0,0,0,0,0,0,0,0
              if  s==1:        
                    vetoHits[plane].append( [gdy,bar] )
                    rc = h['resBarY_'+sdict[s]+str(s*10+plane)].Fill(gdy,bar)
              for x in S:
                  if  s==1:
                      nc = x + 2*nSiPMs*bar
                      h['resVETOY_'+str(plane+1)].Fill(dy,nc)
                  if x<nSiPMs: 
                       if smallSiPMchannel(x):  smallL+=1
                       else:    left+=1
                  else:           
                       if smallSiPMchannel(x):  smallR+=1
                       else:   right+=1
              if left>0:
                    rc = h['resY_'+sdict[s]+'L'+str(s*10+plane)].Fill(dy,locEx[1])
                    rc = h['resX_'+sdict[s]+'L'+str(s*10+plane)].Fill(dx,locEx[0])
                    rc = h['gresY_'+sdict[s]+'L'+str(s*10+plane)].Fill(gdy,globEx[1])
                    rc = h['gresX_'+sdict[s]+'L'+str(s*10+plane)].Fill(gdx,globEx[0])
              if right>0:
                    rc = h['resY_'+sdict[s]+'R'+str(s*10+plane)].Fill(dy,locEx[1])
                    rc = h['resX_'+sdict[s]+'R'+str(s*10+plane)].Fill(dx,locEx[0])
                    rc = h['gresY_'+sdict[s]+'R'+str(s*10+plane)].Fill(gdy,globEx[1])
                    rc = h['gresX_'+sdict[s]+'R'+str(s*10+plane)].Fill(gdx,globEx[0])
              if s==2 and (smallL>0 or smallR>0): 
                     rc = h['resY_'+sdict[s]+'S'+str(s*10+plane)].Fill(dy,locEx[1])
                     rc = h['resX_'+sdict[s]+'S'+str(s*10+plane)].Fill(dx,locEx[0])
                     rc = h['gresY_'+sdict[s]+'S'+str(s*10+plane)].Fill(gdy,globEx[1])
                     rc = h['gresX_'+sdict[s]+'S'+str(s*10+plane)].Fill(gdx,globEx[0])
              dist = abs(dy)
              if aHit.isVertical() : dist = abs(dx)
              if dist<3.0:   # check channels
                  if aHit.isVertical():
                     dL  = locA[1]- locEx[1]
                     dR = locEx[1] - locB[1]
                  else:
                     dR = locA[0] - locEx[0]
                     dL =  locEx[0] - locB[0]
                  barName = sdict[s]+str(s*10+plane)+'_'+str(bar)
                  rc = h['nSiPMsL_'+barName].Fill(left,dL)
                  rc = h['nSiPMsR_'+barName].Fill(right,dR)
                  for x in S:
                      qcd = S[x]
                      if x<nSiPMs:
                         if s==2 and smallSiPMchannel(x): 
                               rc = h['signalSL_'+barName+'-c'+str(x)].Fill(qcd,dL)
                               SleftS+=qcd
                         else:
                               rc = h['signalL_'+barName+'-c'+str(x)].Fill(qcd,dL)
                               Sleft+=qcd
                      else: 
                         if s==2 and smallSiPMchannel(x): 
                               rc = h['signalSR_'+barName+'-c'+str(x-nSiPMs)].Fill(qcd,dR)
                               SrightS+=qcd
                         else:
                               rc = h['signalR_'+barName+'-c'+str(x-nSiPMs)].Fill(qcd,dR)
                               Sright+=qcd
                  rc = h['signalTL_'+barName].Fill(Sleft,dL)
                  rc = h['signalTR_'+barName].Fill(Sright,dR)
                  rc = h['signalTSL_'+barName].Fill(SleftS,dL)
                  rc = h['signalTSR_'+barName].Fill(SrightS,dR)

#   look at delta time vs track X, works only for horizontal planes.
                  if not aHit.isVertical():
                     dt    = aHit.GetDeltaT()
                     dtF  = aHit.GetFastDeltaT()
                     mtTrack = aHit.GetImpactT() - T0track - (globPos[2] - Z0track)/u.speedOfLight
                     mtVeto  = aHit.GetImpactT() - T0Veto - (globPos[2] - Z0Veto)/u.speedOfLight
                     h['dtLRvsX_'+sdict[s]+str(s*10+plane)].Fill(xEx,dt*TDC2ns)
                     h['dtLRvsX_'+barName].Fill(xEx,dt*TDC2ns)
                     if left==6 and right==6:  h['dtF12LRvsX_'+barName].Fill(xEx,dt*TDC2ns)
                     h['dtfastLRvsX_'+barName].Fill(xEx,dtF*TDC2ns)
                     h['atLRvsX_'+sdict[s]+str(s*10+plane)].Fill(xEx,mtTrack)
                     h['VetoatLRvsX_'+sdict[s]+str(s*10+plane)].Fill(xEx,mtVeto)
                     h['atLRvsX_'+barName].Fill(xEx,mtTrack)

    theTrack.Delete()
 ut.writeHists(h,'MuFilterEff_run'+str(options.runNumber)+'.root')

def mips(readHists=True,option=0):
# plot mean sipm channel fired vs X
    if readHists:
        for x in h: 
            if hasattr(x,'Reset'): x.Reset()
        ut.readHists(h,'MuFilterEff_run'+str(options.runNumber)+'.root')
    s = 2
    for plane in range(5):
        for bar in range(10):
           for p in ['L','R']:
               for T in ['T','']:
                    if T=='T': nloop = 1
                    else: nloop = systemAndChannels[s][1]+systemAndChannels[s][0]
                    for i in range(nloop):
                        if s==2 and smallSiPMchannel(i): continue
                        name = 'signal'+T+p+'_US'+str(s*10+plane)+'_'+str(bar)
                        if nloop>1: name += '-c'+str(i)
                        histo = h[name]
                        for x in  ['M','C','W','S','E']:
                          h[x+name]=histo.ProjectionY(x+name)
                          h[x+name].Reset()
                          h[x+name].SetTitle(histo.GetName()+';distance [cm]')
                        for n in range(1,h['M'+name].GetNbinsX()+1):
                              h[name+'-X'+str(n)] = h[name].ProjectionX(name+'-X'+str(n),n,n)
                              tmp = h[name+'-X'+str(n)]
                              h['C'+name].SetBinContent(n,-1)
                              h['E'+name].SetBinContent(n,tmp.GetEntries())
                              if tmp.GetEntries()>50:
                                        print('Fit ',options.runNumber,name,n)
                                        if T=='T': bmin,bmax = 10,tmp.GetMaximumBin()
                                        else: bmin,bmax = 0,30
                                        for k in range(tmp.GetMaximumBin(),1,-1):
                                              if tmp.GetBinContent(k)<2:
                                                 bmin = k
                                                 break
                                        for k in range(tmp.GetMaximumBin(),tmp.GetNbinsX()):
                                              if tmp.GetBinContent(k) + tmp.GetBinContent(k+1)<2:
                                                 bmax = k
                                                 break
                                        res = fit_langau(tmp,'LQ',0.8*tmp.GetBinCenter(bmin),1.5*tmp.GetBinCenter(bmax))
                                        if not res: continue
                                        if not res.IsValid(): continue
                                        h['C'+name].SetBinContent(n,res.Chi2()/res.Ndf())
                                        h['M'+name].SetBinContent(n,res.Parameter(1))
                                        h['M'+name].SetBinError(n,res.ParError(1))
                                        h['W'+name].SetBinContent(n,res.Parameter(0))
                                        h['W'+name].SetBinError(n,res.ParError(0))
                                        h['S'+name].SetBinContent(n,res.Parameter(3))
                                        h['S'+name].SetBinError(n,res.ParError(3))
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
                 if tmp.GetEntries()>50:
                    print('Fit ',options.runNumber,name,n)
                    bmin,bmax = 0,80
                    for k in range(tmp.GetMaximumBin(),1,-1):
                          if tmp.GetBinContent(k)<2:
                              bmin = k
                              break
                    res = fit_langau(tmp,'LQ',0.8*tmp.GetBinCenter(bmin),1.5*tmp.GetBinCenter(bmax))
                    if not res: continue
                    if not res.IsValid(): continue
                    h['M'+name].SetBinContent(n,res.Parameter(1))
                    h['M'+name].SetBinError(n,res.ParError(1))
                    h['W'+name].SetBinContent(n,res.Parameter(0))
                    h['W'+name].SetBinError(n,res.ParError(0))
                    h['S'+name].SetBinContent(n,res.Parameter(3))
                    h['S'+name].SetBinError(n,res.ParError(3))

    ut.writeHists(h,'LandauFits_run'+str(options.runNumber)+'.root')
def mipsAfterBurner(readhisto=True):
    if readhisto:  ut.readHists(h,'LandauFits_run'+str(options.runNumber)+'.root')
    s=2
    for plane in range(5):
           for p in ['L','R']:
                for bar in range(10):
                     name = 'signalT'+p+'_US'+str(s*10+plane)+'_'+str(bar)
                     for nb in range(1,h['M'+name].GetNbinsX()+1):
                          tmp = h[name+'-X'+str(nb)]
                          N = tmp.GetEntries()
                          if N>50 and h['M'+name].GetBinContent(nb)==0: 
                               fg  =  tmp.GetFunction('langau')
                               bmin,bmax = fg.GetXmin(),fg.GetXmax()
                               res = fit_langau(tmp,'LQ',bmin,bmax)
                               if res.IsValid():
                                    print(name,nb,N,'fixed')
                                    h['M'+name].SetBinContent(nb,res.Parameter(1))
                                    h['M'+name].SetBinError(nb,res.ParError(1))
                                    h['W'+name].SetBinContent(nb,res.Parameter(0))
                                    h['W'+name].SetBinError(nb,res.ParError(0))
                                    h['S'+name].SetBinContent(nb,res.Parameter(3))
                                    h['S'+name].SetBinError(nb,res.ParError(3))
                               else:
                                    print(name,nb,N,'problem')
barColor = [ROOT.kRed,ROOT.kRed-7,ROOT.kMagenta,ROOT.kMagenta-6,ROOT.kBlue,ROOT.kBlue-9,
                      ROOT.kCyan,ROOT.kAzure-4,ROOT.kGreen,ROOT.kGreen+3]

def plotMips(readhisto=True):
    if readhisto:  ut.readHists(h,'LandauFits_run'+str(options.runNumber)+'.root')
    langau = ROOT.TF1('Langau',langaufun,0.,100.,4)
    ut.bookCanvas(h,'CsignalT','',1200,2000,2,5)
    ut.bookCanvas(h,'WsignalT','',1200,2000,2,5)
    ut.bookCanvas(h,'SsignalT','',1200,2000,2,5)
    ut.bookCanvas(h,'Msignal1','',900,600,1,1)
    ut.bookCanvas(h,'MsignalT','',1200,2000,2,5)
    ut.bookCanvas(h,'MsignalT1','',900,600,1,1)
    ut.bookCanvas(h,'NnSiPMs1','',900,600,1,1)
    ut.bookCanvas(h,'NnSiPMs','',1200,2000,2,5)
#example plots:
    for T in ['T']:
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
# make summary of mpv and att length
    ut.bookCanvas(h,'Mpvs','',2400,1200,1,2)
    ut.bookCanvas(h,'attLs','',2400,1200,1,2)
    tc = h['Mpvs'].cd(1)
    h['attLengthL'],h['attLengthR'],h['attLengthLC'],h['attLengthRC']= ROOT.TGraph(),ROOT.TGraph(),ROOT.TGraph(),ROOT.TGraph()
    h['mpv0L'],h['mpv0R'],h['mpv0LC'],h['mpv0RC'] = ROOT.TGraph(),ROOT.TGraph(),ROOT.TGraph(),ROOT.TGraph()
    for t in ['T','']:
     for p in ['L','R']:
       nk = 0
       for plane in range(5):
            for bar in range(10):
                    if t=='T': nloop = 1
                    else: nloop = systemAndChannels[s][1]+systemAndChannels[s][0]
                    for i in range(nloop):
                        if s==2 and smallSiPMchannel(i): continue
                        name = 'Msignal'+t+p+'_US'+str(s*10+plane)+'_'+str(bar)
                        chi2N = 'Csignal'+t+p+'_US'+str(s*10+plane)+'_'+str(bar)
                        if nloop>1: 
                              name += '-c'+str(i)
                              chi2N += '-c'+str(i)
                     # find fit limits
                        limits = []
                        for i in range(1,h[chi2N].GetNbinsX()+1):
                            funL = h[name[1:]+'-X'+str(i)].GetFunction('langau')
                            if not funL: continue
                            if not funL.GetParameter(2)>0: continue
                            mpvRelErr = funL.GetParError(1)/funL.GetParameter(1)*ROOT.TMath.Sqrt(h[name[1:]+'-X'+str(i)].GetEntries())
                            if mpvRelErr < 0.1: 
                                    print('exclude bin ',name,i,mpvRelErr,h[name[1:]+'-X'+str(i)].GetEntries())
                                    continue
                            if len(limits)==0 and h[chi2N].GetBinContent(i)>0 and h[chi2N].GetBinContent(i)<9:
                               limits.append(h[chi2N].GetBinCenter(i))
                               break
                        for i in range(h[chi2N].GetNbinsX(),1,-1):
                            funL = h[name[1:]+'-X'+str(i)].GetFunction('langau')
                            if not funL: continue
                            if not funL.GetParameter(2)>0: continue
                            mpvRelErr = funL.GetParError(1)/funL.GetParameter(1)*ROOT.TMath.Sqrt(h[name[1:]+'-X'+str(i)].GetEntries())
                            if mpvRelErr < 0.1: 
                                    print('exclude bin ',name,i,mpvRelErr,h[name[1:]+'-X'+str(i)].GetEntries())
                                    continue
                            if len(limits)==1 and h[chi2N].GetBinContent(i)>0 and h[chi2N].GetBinContent(i)<9:
                               limits.append(h[chi2N].GetBinCenter(i))
                               break
                        if len(limits)<2:
                           X = nk+0.5
                           tag = p
                           if nloop>1: 
                               tag = p+'C'
                               X = nk/6.
                           h['mpv0'+tag].SetPoint(nk,X,-1)
                           h['attLength'+tag].SetPoint(nk,X,0)
                           nk+=1
                           continue 
                        rc = h[name].Fit('expo','SQ','',limits[0],limits[1])
                        fun = h[name].GetFunction('expo')
                        fun.SetLineColor(barColor[bar%10])
                        res = rc.Get()
                        tag = p
                        X = nk+0.5
                        val = fun.Eval(40)
                        if nloop>1: 
                               tag = p+'C'
                               X = nk/6.
                               val = fun.Eval(0)
                        h['mpv0'+tag].SetPoint(nk,X,val)
                        h['attLength'+tag].SetPoint(nk,X,-1./res.Parameter(1))
                        nk+=1

    ut.bookHist(h,'hMpvs',';stations with bars; MPV [QCD]',101,-0.5,50.5)
    ut.bookHist(h,'hAttl',';plane number; att length [cm]',101,-0.5,50.5)
    params = {'hMpvs':['Mpvs',20,'mpv0',0.], 'hAttl':['attLs',0.,'attLength',-2000.]}
    side = {'L':[ROOT.kBlue,''], 'R':[ROOT.kRed,'same']}
    for P in params:
       h[P].SetStats(0)
       h[P].SetMaximum(params[P][1])
       h[P].SetMinimum(params[P][3])
       X = h[P].GetXaxis()
       X.SetTitleFont(42)
       X.SetNdivisions(51)
       for tag in ['','C']:
         tc = h[params[P][0]].cd(1)
         if tag == 'C': tc = h[params[P][0]].cd(2)
         tc.SetGridx(1)
         h[P].DrawClone()
         for S in side:
           h[params[P][2]+S+tag].SetMarkerStyle(92)
           if tag=='C': 
              h[params[P][2]+S+tag].SetMarkerSize(1)
              h[params[P][2]+S+tag].SetMarkerStyle(71)
           else: h[params[P][2]+S+tag].SetMarkerSize(2)
           h[params[P][2]+S+tag].SetMarkerColor(side[S][0])
           h[params[P][2]+S+tag].Draw('P'+side[S][1])

    myPrint(h['Mpvs'],'Mpvs')
    myPrint(h['attLs'],'AttLength')

    k=1
    tMax = {'CsignalT':0,'MsignalT':0,'NnSiPMs':0,'WsignalT':0,'SsignalT':0}
    for plane in range(5):
           for p in ['L','R']:
            for t in tMax:
              for bar in range(10):
                name = t+p+'_US'+str(s*10+plane)+'_'+str(bar)
                nmax = h[name].GetBinContent(h[name].GetMaximumBin())
                err = h[name].GetBinError(h[name].GetMaximumBin())
                if err/nmax > 0.2: continue
                if nmax > tMax[t]: tMax[t]=nmax
    for plane in range(5):
           for p in ['L','R']:
            for t in tMax:
                tc = h[t].cd(k)
                for bar in range(10):
                     color = barColor[bar%10]
                     name = t+p+'_US'+str(s*10+plane)+'_'+str(bar)
                     h[name].SetStats(0)
                     h[name].SetMarkerStyle(34)
                     h[name].SetMarkerColor(color)
                     h[name].SetLineColor(color)
                     dropt = ''
                     if len(tc.GetListOfPrimitives())>0: dropt='same'
                     h[name].SetMinimum(0.)
                     h[name].SetMaximum(tMax[t]*1.1)
                     if name.find('CsignalT')==0:  
                                   h[name].SetTitle('station '+p+' '+str(plane+1)+';chi2/nDoF')
                     if name.find('MsignalT')==0:  
                                   h[name].SetTitle('QDC sum station '+p+' '+str(plane+1)+';d [cm];QDC')
                     elif name.find('SsignalT')==0:  
                                   h[name].SetTitle('sigma '+p+' '+str(plane+1)+';d [cm];QDC')
                     elif name.find('WsignalT')==0: 
                                   h[name].SetTitle('width '+p+' '+str(plane+1)+';d [cm];QDC')
                     if t== 'MsignalT':  rc = h[name].Draw('P'+dropt)
                     else:                     rc = h[name].Draw('PL'+dropt)
                     if  t == 'NnSiPMs' : 
                             tc = h['NnSiPMs1'].cd(1)
                             h[name].SetMinimum(3)
                             if k>1: dropt = 'same'
                             h[name].Draw(dropt)
            k+=1
    for t in ['MsignalT','NnSiPMs','WsignalT','SsignalT']:             myPrint(h[t],t)
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
def plotMipsGainRatio():
    t = 'MsignalT'
    for run in [89,90,91]:
        h[run] = {}
        f = ROOT.TFile('LandauFits_run'+str(run)+'.root')
        for plane in range(5):
           for p in ['L','R']:
              for bar in range(10):
                  name = t+p+'_US'+str(s*10+plane)+'_'+str(bar)
                  h[run][name] = f.FindObjectAny(name).Clone()
                  h[run][name].SetDirectory(ROOT.gROOT)
    nRef = 90    # 90 is with gain 2.5 and stable
    for run in [89,91]:   
        ut.bookCanvas(h,'MsignalN'+str(run),'',1200,2000,2,5)
        k = 1
        for plane in range(5):
           for p in ['L','R']:
              nMax = 0
              for bar in range(10):
                  name = t+p+'_US'+str(s*10+plane)+'_'+str(bar)
                  h[run]['N'+name] = h[run][name].Clone('N'+name)
                  h[run]['N'+name].Divide(h[nRef][name])
                  tc = h['MsignalN'+str(run)].cd(k)
                  color = barColor[bar]
                  h[run]['N'+name].SetStats(0)
                  h[run]['N'+name].SetMarkerStyle(34)
                  h[run]['N'+name].SetMarkerColor(color)
                  h[run]['N'+name].SetLineColor(color)
                  M = h[run]['N'+name].GetBinContent(h[run]['N'+name].GetMaximumBin())
                  if M>nMax and M<20: nMax = M
              for bar in range(10):
                  name = t+p+'_US'+str(s*10+plane)+'_'+str(bar)
                  h[run]['N'+name].SetMaximum(1.2*nMax)
                  h[run]['N'+name].SetMinimum(0)
                  opt = 'P'
                  if bar>0: opt+='same'
                  h[run]['N'+name].Draw(opt)
              k+=1
        h['MsignalN'+str(run)].Print('MPVgainRatio_'+str(run)+'_'+str(nRef)+'.png')

def plotMipsTimeRes(readHists=True):
    maxRes = {1:0.6,2:1.0,3:0.6}
    if readHists:
        for x in h: 
            if hasattr(x,'Reset'): x.Reset()
        ut.readHists(h,'MuFilterEff_run'+str(options.runNumber)+'.root')
    ut.bookCanvas(h,'dummy','',900,800,1,1)
    S = [1,2,3]
    if options.runNumber<100:  S = [2,3]
    for mode in ['','fast','F12']:
     for s in S:
       if s==1: ut.bookCanvas(h,mode+'TimeLR-'+str(s),'',1800,800,2,1)
       if s==2: ut.bookCanvas(h,mode+'TimeLR-'+str(s),'',1800,1500,2,3)
       if s==3: ut.bookCanvas(h,mode+'TimeLR-'+str(s),'',900,1500,1,3)
       nbars = 0
       for plane in range(systemAndPlanes[s]):
          if  systemAndOrientation(s,plane) == "vertical": continue
          nbars += systemAndBars[s]
       ut.bookHist(h,mode+'tsigma_'+str(s),';'+str(systemAndBars[s])+'*station + bar number;#sigma_{t} [ns]',nbars,-0.5,nbars-0.5)
       k = 1
       for plane in range(systemAndPlanes[s]):
        if  systemAndOrientation(s,plane) == "vertical": continue
        for bar in range(systemAndBars[s]):
           tc = h['dummy'].cd()
           name0 = 'dt'+mode+'LRvsX_'+sdict[s]+str(s*10+plane)+'_'+str(bar)
           name   = 'Rdt'+mode+'LRvsX_'+sdict[s]+str(s*10+plane)+'_'+str(bar)
           tname  = mode+'TimeRes_'+sdict[s]+str(s*10+plane)+'_'+str(bar)
           h[name] = h[name0].Clone(name)
           rc = h[name].RebinX(2)
           h[tname] = h[name].ProjectionX(tname)
           h[tname].Reset()
           xax = h[tname].GetXaxis()
           yax = h[tname].GetYaxis()
           yax.SetTitle('#sigma_{t} [ns]')
           ymin = h[name].GetYaxis().GetBinCenter(1)
           ymax = h[name].GetYaxis().GetBinCenter(h[name].GetYaxis().GetNbins())
           minContent = max(50,h[name].GetEntries()*0.02)  # remove tails from bad track reconstruction and extrapolation.)
           for j in range(1,xax.GetNbins()+1):
                jname = name+'-X'+str(j)
                h[jname] = h[name].ProjectionY(jname,j,j)
                if h[jname].GetEntries()<minContent: continue
                xx =  h[jname].GetBinCenter(h[jname].GetMaximumBin())
                xmin  = max(ymin,xx-2.)
                xmax = min(ymax,xx+2.)
                rc = h[jname].Fit('gaus','SQL','',xmin,xmax)
                res = rc.Get()
                h[tname].SetBinContent(j,res.Parameter(2))
                h[tname].SetBinError(j,res.ParError(2))
           A = weightedY(h[tname])
           if A[1]<100:
              h[mode+'tsigma_'+str(s)].SetBinContent(plane*10+bar,A[0])
              h[mode+'tsigma_'+str(s)].SetBinError(plane*10+bar,A[1])
           if bar==0: opt=''
           else:         opt='same'
           color = barColor[bar%10]
           h[tname].SetMaximum(maxRes[s])
           h[tname].SetStats(0)
           h[tname].SetMarkerStyle(34)
           h[tname].SetMarkerColor(color)
           h[tname].SetLineColor(color)
           tc = h[mode+'TimeLR-'+str(s)].cd(k)
           h[tname].Draw('P'+opt)
           h[tname].Draw('HISTLSAME')
        k+=1

       ut.bookCanvas(h,mode+'dummy'+sdict[s],'',900,800,1,1)
       tc = h[mode+'dummy'+sdict[s]].cd()
       tc.SetGridx(1)
       name = mode+'tsigma_'+str(s)
       h[name].SetStats(0)
       h[name].SetMarkerColor(ROOT.kBlue)
       h[name].SetMarkerStyle(34)
       h[name].SetMarkerSize(2)
       X = h[name].GetXaxis()
       X.SetTitleFont(42)
       X.SetNdivisions(505)
       h[name].Draw('P')
       myPrint(h[mode+'dummy'+sdict[s]],mode+'TimeResol-'+sdict[s])
       myPrint(h[mode+'TimeLR-'+str(s)],mode+'TimeResol-'+sdict[s]+'vsX')
def weightedY(aHist):
    xax = aHist.GetXaxis()
    nx = xax.GetNbins()
    W = 1E-20
    mean = 0
    for j in range(1,nx+1):
             N = aHist.GetBinContent(j)
             if not N>0: continue
             E = aHist.GetBinError(j)
             if E>0:
                mean+=N/E**2
                W+= 1/E**2
    return [mean/W,1./W]


def makeDetPrints():
  for s in range(1,4):
     drawArea(s,p=0,opt='',color=ROOT.kGreen)
     myPrint(h['area'],'areaDet_'+sdict[s])
def drawArea(s=3,p=0,opt='',color=ROOT.kGreen):
 ut.bookCanvas(h,'area','',900,900,1,1)
 hname = 'track_'+sdict[s]+str(s)+str(p)
 barw = 1.0
 if s<3: barw=3.
 h[hname].SetStats(0)
 h[hname].SetTitle('')
 h[hname].Draw('colz'+opt)
 mufi = geo.modules['MuFilter']
 if opt=='': h['lines'] = []
 lines = h['lines'] 
 latex.SetTextColor(ROOT.kRed)
 latex.SetTextSize(0.03)
 for bar in range(systemAndBars[s]):
    mufi.GetPosition(s*10000+p*1000+bar,A,B)
    barName = str(bar)
    botL = ROOT.TVector3(A.X(),A.Y()-barw,0)
    botR = ROOT.TVector3(B.X(),B.Y()-barw,0)
    topL = ROOT.TVector3(A.X(),A.Y()+barw,0)
    topR = ROOT.TVector3(B.X(),B.Y()+barw,0)
    lines.append(ROOT.TLine(topL.X(),topL.Y(),topR.X(),topR.Y()))
    lines.append(ROOT.TLine(botL.X(),botL.Y(),botR.X(),botR.Y()))
    lines.append(ROOT.TLine(botL.X(),botL.Y(),topL.X(),topL.Y()))
    lines.append(ROOT.TLine(botR.X(),botR.Y(),topR.X(),topR.Y()))
    if s<3 or (s==3 and bar%5==0): latex.DrawLatex(botR.X()-5.,botR.Y()+0.3,barName)
    N = len(lines)
    for n in range(N-4,N):
      l=lines[n]
      l.SetLineColor(color)
      l.SetLineWidth(4)
 for l in lines:  l.Draw('same')
 latex.DrawLatexNDC(0.2,0.2,"Right")
 latex.DrawLatexNDC(0.8,0.2,"Left")
 if s<3: return
 h['linesV'] = []
 linesV = h['linesV'] 
 for bar in range(systemAndBars[s]):
    mufi.GetPosition(s*10000+(p+1)*1000+bar+60,A,B)
    topL = ROOT.TVector3(A.X()+barw,A.Y(),0)
    botL = ROOT.TVector3(B.X()+barw,B.Y(),0)
    topR = ROOT.TVector3(A.X()-barw,A.Y(),0)
    botR = ROOT.TVector3(B.X()-barw,B.Y(),0)
    linesV.append(ROOT.TLine(topL.X(),topL.Y(),topR.X(),topR.Y()))
    linesV.append(ROOT.TLine(topR.X(),topR.Y(),botR.X(),botR.Y()))
    linesV.append(ROOT.TLine(botR.X(),botR.Y(),botL.X(),botL.Y()))
    linesV.append(ROOT.TLine(botL.X(),botL.Y(),topL.X(),topL.Y()))
    barName = str(bar)
    if bar%5==0: latex.DrawLatex(topR.X(),topR.Y()+2,barName)
 for l in linesV:
     l.SetLineColor(ROOT.kRed)
     l.SetLineWidth(4)
     l.Draw('same')

def analyze_EfficiencyAndResiduals(readHists=False,mode='S',local=True,zoom=False):
  if readHists:   ut.readHists(h,'MuFilterEff_run'+str(options.runNumber)+'.root')
# start with tracks
  ut.bookCanvas(h,'Tracks','',900,1600,1,2)
  h['Tracks'].cd(1)
  h['tracksChi2Ndof'].Draw('colz')
  h['Tracks'].cd(2)
  h['trackslxy'].Draw('colz')

  if local:  res = 'res'
  else: res='gres'
  for proj in ['X','Y']:
   if mode == "S":
      if proj=="Y": ut.bookCanvas(h,'EVetoUS'+proj,'',1200,2000,2,7)
      if proj=="Y": ut.bookCanvas(h,'EDS'+proj,'',1200,2000,2,3)
      if proj=="X": ut.bookCanvas(h,'EDS'+proj,'',1200,2000,2,4)
   else:
      ut.bookCanvas(h,'EVetoUS'+proj,'',1200,2000,4,7)
      ut.bookCanvas(h,'EDS'+proj,'',1200,2000,3,7)
   k = 1
   residualsAndSigma = {}
   for s in  [1,2,3]:
    if mode == "S" and s<3 and proj=="X": continue
    if s==3: k=1
    sy = sdict[s]
    if s<3: tname = 'EVetoUS'+proj
    else: tname = 'EDS'+proj
    for plane in range(systemAndPlanes[s]):
     if s==3 and proj=="X" and (plane%2==0 and plane<5): continue
     if s==3 and proj=="Y" and (plane%2==1 or plane==6): continue
     tc = h[tname].cd(k)
     key = sy+str(s*10+plane)
     h['track_' + key].Draw('colz')
     k+=1
     for side in ['L','R','S']:
      if side=='S' and (s==3 or mode=='S') : continue
      if side=='R' and (mode=='S') : continue
      tc = h[tname].cd(k)
      k+=1
      if mode=="S":
         hname = res+proj+'_'+key
      else:
         hname = res+proj+'_'+sy+side+str(s*10+plane)
      resH = h[hname].ProjectionX(hname+'_proj')
      if zoom:
           if s==3: resH.GetXaxis().SetRangeUser(-4.,4.)
           else:      resH.GetXaxis().SetRangeUser(-10.,10.)
      resH.Draw()
      binw = resH.GetBinWidth(1)
      if resH.GetEntries()>10:
         myGauss = ROOT.TF1('gauss','abs([0])*'+str(binw)+'/(abs([2])*sqrt(2*pi))*exp(-0.5*((x-[1])/[2])**2)+abs([3])',4)
         myGauss.SetParameter(0,resH.GetEntries())
         myGauss.SetParameter(1,0)
         myGauss.SetParameter(2,2.)
         rc = resH.Fit(myGauss,'SL','',-15.,15.)
         fitResult = rc.Get()
         if not (s*10+plane) in residualsAndSigma:
             residualsAndSigma[s*10+plane] = [fitResult.Parameter(1)/u.mm,fitResult.ParError(1)/u.mm,abs(fitResult.Parameter(2)/u.cm),fitResult.ParError(2)/u.cm]
         tc.Update()
         stats = resH.FindObject('stats')
         stats.SetOptFit(111111)
         stats.SetX1NDC(0.63)
         stats.SetY1NDC(0.25)
         stats.SetX2NDC(0.98)
         stats.SetY2NDC(0.94)
         tracks = h['track_'+key].GetEntries()
         if tracks >0:
             eff = fitResult.Parameter(0)/tracks
             effErr = fitResult.ParError(0)/tracks
             latex.DrawLatexNDC(0.2,0.8,'eff=%5.2F+/-%5.2F%%'%(eff,effErr))
   if 'EVetoUS'+proj in h: myPrint(h['EVetoUS'+proj],'EVetoUS'+proj)
   if 'EDS'+proj in h:        myPrint(h['EDS'+proj],'EDS'+proj)
# summary plot of residuals
   h['gResiduals'], h['gSigma'] = ROOT.TGraphErrors(), ROOT.TGraphErrors()
   k = 0 
   for sp in residualsAndSigma:
       h['gResiduals'].SetPoint(k,sp,residualsAndSigma[sp][0])
       h['gResiduals'].SetPointError(k,0.5,residualsAndSigma[sp][1])
       h['gSigma'].SetPoint(k,sp,residualsAndSigma[sp][2])
       h['gSigma'].SetPointError(k,0.5,residualsAndSigma[sp][3])
       k+=1
   h['gResiduals'].SetLineWidth(2)
   h['gSigma'].SetLineWidth(2)
   ut.bookCanvas(h,'MufiRes','Mufi residuals',750,750,1,1)
   tc = h['MufiRes'].cd()
   h['gResiduals'].SetTitle(';station; offset [mm]')
   h['gResiduals'].Draw("AP")
   ut.bookCanvas(h,'MufiSigm','Mufi sigma',750,750,1,1)
   tc = h['MufiSigm'].cd()
   h['gSigma'].SetTitle(';station; #sigma [cm]')
   h['gSigma'].Draw("AP")
   myPrint(h['MufiRes'],'MufiResiduals')
   myPrint(h['MufiSigm'],'MufiSigma')

  ut.bookCanvas(h,'TVE','',800,900,1,2)
  ut.bookCanvas(h,'TUS','',800,2000,1,5)
  ut.bookCanvas(h,'TDS','',800,1200,1,3)
  latex.SetTextColor(ROOT.kRed)

  S = {1:'TVE',2:'TUS',3:'TDS'}
  for s in  S:
    sy = sdict[s]
    tname = S[s]
    k=1
    for plane in range(systemAndPlanes[s]):
     if s==3 and proj=="X" and (plane%2==0 and plane<5): continue
     if s==3 and proj=="Y" and (plane%2==1 or plane==6): continue
     tc = h[tname].cd(k)
     k+=1
     key = sy+str(s*10+plane)
     hist = h['dtLRvsX_'+key]
     if hist.GetSumOfWeights()==0:   continue
# find beam spot
     tmp = h['track_'+key].ProjectionX()
     rc = tmp.Fit('gaus','S')
     res = rc.Get()
     fmin = res.Parameter(1)  -  3*res.Parameter(2)
     fmax = res.Parameter(1) + 3*res.Parameter(2)
     hist.SetStats(0)
     xmin = max( hist.GetXaxis().GetBinCenter(1), fmin)
     xmax = min( hist.GetXaxis().GetBinCenter(hist.GetNbinsX()), fmax)
     hist.GetXaxis().SetRangeUser(xmin,xmax)
     hist.GetYaxis().SetRange(1,hist.GetNbinsY())
     rc = hist.ProjectionY().Fit('gaus','S')
     res = rc.Get()
     ymin = max( hist.GetYaxis().GetBinCenter(1), -5*res.Parameter(2))
     ymax = min( hist.GetYaxis().GetBinCenter(hist.GetNbinsY()), 5*res.Parameter(2))
     hist.GetYaxis().SetRangeUser(ymin,ymax)
     hist.Draw('colz')
# get time x correlation, X = m*dt + b
     h['gdtLRvsX_'+key] = ROOT.TGraph()
     g = h['gdtLRvsX_'+key]
     xproj = hist.ProjectionX('tmpx')
     if xproj.GetSumOfWeights()==0:   continue
     np = 0
     Lmin = hist.GetSumOfWeights() * 0.005
     for nx in range(hist.GetXaxis().FindBin(xmin),hist.GetXaxis().FindBin(xmax)):
            tmp = hist.ProjectionY('tmp',nx,nx)
            if tmp.GetEntries()<Lmin:continue
            X   = hist.GetXaxis().GetBinCenter(nx)
            rc = tmp.Fit('gaus','NQS')
            res = rc.Get()
            if not res: dt = tmp.GetMean()
            else:   dt = res.Parameter(1)
            g.SetPoint(np,X,dt)
            np+=1
     g.SetLineColor(ROOT.kRed)
     g.SetLineWidth(2)
     g.Draw('same')
     rc = g.Fit('pol1','SQ','',xmin,xmax)
     g.GetFunction('pol1').SetLineColor(ROOT.kGreen)
     g.GetFunction('pol1').SetLineWidth(2)
     result = rc.Get()
     if not result:   continue
     m = 1./result.Parameter(1)
     b = -result.Parameter(0) * m
     sign = '+'
     if b<0: sign = '-'
     txt = 'X = %5.1F #frac{cm}{ns} #times #frac{1}{2}#Deltat %s %5.1F '%(m*2,sign,abs(b))
     latex.SetTextSize(0.07)
     latex.DrawLatexNDC(0.2,0.8,txt)
  myPrint(h['TVE'],'dTvsX_Veto')
  myPrint(h['TUS'],'dTvsX_US')
  myPrint(h['TDS'],'dTvsX_DS')

# timing relative to Scifi tracks
  colors = {1:ROOT.kGreen,2:ROOT.kRed,3:ROOT.kBlue}
  ut.bookCanvas(h,'relT','',800,1000,1,7)
  for s in systemAndPlanes:
     for plane in range(systemAndPlanes[s]):
       hname = 'atLRvsX_'+sdict[s]+str(s*10+plane)
       h[hname+'_proj'] = h[hname].ProjectionY(hname+'_proj')
       h[hname+'_proj'].SetLineColor(colors[s])
       h[hname+'_proj'].SetStats(0)
       h[hname+'_proj'].SetTitle('; #Deltat [ns]')
       if s==1 and plane == 0: h[hname+'_proj'] .Draw()
       else: h[hname+'_proj'] .Draw('same')


#for VETO
  ut.bookCanvas(h,'veto','',800,1600,1,7)
  s=1
  for plane in [0,1]:
    hname = 'resBarY_'+sdict[s]+str(s*10+plane)
    for nbar in range(1,h[hname].GetNbinsY()+1):
        vname = 'veto'+str(s*10+plane)+'_'+str(nbar)
        h[vname] = h[hname].ProjectionX(vname,nbar+1,nbar+1)
        binw = h[vname].GetBinWidth(1)
        myGauss = ROOT.TF1('gauss','abs([0])*'+str(binw)+'/(abs([2])*sqrt(2*pi))*exp(-0.5*((x-[1])/[2])**2)+abs([3])',4)
        myGauss.SetParameter(0,resH.GetEntries())
        myGauss.SetParameter(1,0)
        myGauss.SetParameter(2,2.)
        rc = h[vname].Fit(myGauss,'SL','',-15.,15.)
        fitResult = rc.Get()

#  Scifi specific code
def TimeCalibrationNtuple(Nev=options.nEvents,nStart=0):
    if Nev < 0 : Nev = eventTree.GetEntries()
    maxD = 100
    fNtuple = ROOT.TFile("scifi_timing_"+str(options.runNumber)+".root",'recreate')
    tTimes  = ROOT.TTree('tTimes','Scifi time calib') 
    nChannels    = array('i',1*[0])
    detIDs          = array('i',maxD*[0])
    tdc               = array('f',maxD*[0.])
    qdc              = array('f',maxD*[0.])
    dL                = array('f',maxD*[0.])
    D                 = array('f',maxD*[0.])
    tTimes.Branch('nChannels',nChannels,'nChannels/I')
    tTimes.Branch('detIDs',detIDs,'detIDs[nChannels]/I')
    tTimes.Branch('tdc',tdc,'tdc[nChannels]/F') 
    tTimes.Branch('qdc',tdc,'qdc[nChannels]/F') 
    tTimes.Branch('D',D,'D[nChannels]/F')
    tTimes.Branch('dL',dL,'dL[nChannels]/F')

    for n_ in range(nStart,nStart+Nev):
       rc = eventTree.GetEvent(n_)
       event = eventTree
       n_+=1
       if n_%100000==0: print("now at event ",n_)
       theTrack = Scifi_track()
       if not hasattr(theTrack,"getFittedState"): continue
       status = theTrack.getFitStatus()
       if status.isFitConverged():
          DetID2Key={}
          for nHit in range(event.Digi_ScifiHits.GetEntries()):
            DetID2Key[event.Digi_ScifiHits[nHit].GetDetectorID()] = nHit
          nHit = 0
          for nM in range(theTrack.getNumPointsWithMeasurement()):
            state   = theTrack.getFittedState(nM)
            posM   = state.getPos()
            M = theTrack.getPointWithMeasurement(nM)
            W = M.getRawMeasurement()
            clkey  = W.getHitId()
            aCl = eventTree.ScifiClusters[clkey]
            for nh in range(aCl.GetN()):
                 detID = aCl.GetFirst() + nh
                 aHit = event.Digi_ScifiHits[ DetID2Key[detID] ]
                 geo.modules['Scifi'].GetSiPMPosition(detID,A,B)
                 if aHit.isVertical(): X = B-posM
                 else:  X = A-posM
                 dL[nHit] = X.Mag()
                 detIDs[nHit] = detID
                 tdc[nHit] = aHit.GetTime()*TDC2ns
                 qdc[nHit] = aHit.GetSignal()
                 N = B-A
                 X = posM-A
                 V = X.Cross(N)
                 D[nHit] = 0
                 if abs(V.Z())>0: D[nHit] = V.Mag()/N.Mag()*V.Z()/abs(V.Z())
                 nHit += 1
                 if nHit==maxD: 
                     print('too many hits:',n_)
                     break
            if nHit==maxD: break
          nChannels[0] = nHit
          tTimes.Fill()
       theTrack.Delete()
    fNtuple.Write() 
    fNtuple.Close()

def analyzeTimings(c='',vsignal = 15., args={},opt=0):
  print('-->',c)
  if c=='':
       analyzeTimings(c='findMax',vsignal = 15.)
       new_list = sorted(h['mult'].items(), key=lambda x: x[1], reverse=True)
       args = {"detID0":new_list[0][0]}
       print(args)
       analyzeTimings(c='firstIteration',vsignal = 15., args=args,opt=0)
       h['dTtwin'].Draw()
       return
  fNtuple = ROOT.TFile("scifi_timing_"+str(options.runNumber)+".root")
  tTimes  = fNtuple.tTimes
  if c=="findMax":
     h['mult'] = {}
     for nt in tTimes:
          for nHit in range(nt.nChannels):
              detID = nt.detIDs[nHit]
              if not detID in h['mult']: h['mult'][detID] = 0
              h['mult'][detID] += 1
     new_list = sorted(h['mult'].items(), key=lambda x: x[1], reverse=True)
     detID0 = new_list[0][0]  #   args = {"detID0":new_list[0][0]}
  if c=="firstIteration":
     ut.bookHist(h,'dTtwin','dt between neighbours',100,-5,5)
     ut.bookHist(h,'dTtwinMax','dt between neighbours',100,-5,5)
     for x in h:
         if x[0]=='c':h[x].Reset()

     for nt in tTimes:
          tag = False
          for nHit in range(nt.nChannels):
              if nt.detIDs[nHit] == args["detID0"]:
                   tag = nHit
                   break
          if not tag: continue
          for nHit in range(nt.nChannels):
               detID = nt.detIDs[nHit]
               dLL    = (nt.dL[nHit] - nt.dL[tag]) / vsignal  # light propagation in cm/ns
               dtdc   = nt.tdc[nHit] - nt.tdc[tag]
               if opt>0:
                  hname = 'c'+str(detID)
                  if not hname in h: ut.bookHist(h,hname,";dt [ns]",200,-10.,10.)
                  rc = h[hname].Fill(dtdc-dLL)
               for nHit2 in range(nHit+1,nt.nChannels):
                  detID2 = nt.detIDs[nHit2]
                  if abs(detID-detID2)==1:
                     dt = nt.tdc[nHit] - nt.tdc[nHit2]
                     if detID2>detID: dt=-dt
                     if nt.qdc[nHit] < 15 or  nt.qdc[nHit2] < 15: continue
                     rc = h['dTtwin'].Fill(dt)
                     if detID == args["detID0"]: rc = h['dTtwinMax'].Fill(dt)

# h['c'+str(new_list[3][0])].Draw()
def ScifiChannel_residuals():
   for s in range(1,6):
     for o in range(2):
           ut.bookHist(h,'res_Scifi'+str(s*10+o),'residual  '+str(s*10+o)+';channel; [#mum]',
                              512*3,-0.5,512*3-0.5,100,-2500.,2500.)
   fNtuple = ROOT.TFile("scifi_timing.root")
   tTimes  = fNtuple.tTimes
   for nt in tTimes:
      for nHit in range(nt.nChannels):
          detID = nt.detIDs[nHit]
          X = Scifi_xPos(detID)
          s = X[0]//2+1
          o = X[0]%2
          n = X[1]*512+X[2]
          rc = h['res_Scifi'+str(s*10+o)].Fill(n,nt.D[nHit]*10000)

def SciFiPropSpeed():
  ut.bookCanvas(h,'v','',1600,1200,5,1)
  for s in range(1,6):
     tc = h['v'].cd(s)
     hname = 'dtScifivsdL_'+str(s)
     hist = h[hname]
     if hist.GetSumOfWeights()==0:   continue
# find beam spot
     tmp = hist.ProjectionX()
     rc = tmp.Fit('gaus','S')
     res = rc.Get()
     fmin = res.Parameter(1)  -  3*res.Parameter(2)
     fmax = res.Parameter(1) + 3*res.Parameter(2)
     hist.SetStats(0)
     xmin = max( hist.GetXaxis().GetBinCenter(1), fmin)
     xmax = min( hist.GetXaxis().GetBinCenter(hist.GetNbinsX()), fmax)
     hist.GetXaxis().SetRangeUser(xmin,xmax)
     hist.GetYaxis().SetRange(1,hist.GetNbinsY())
     rc = hist.ProjectionY().Fit('gaus','S')
     res = rc.Get()
     ymin = max( hist.GetYaxis().GetBinCenter(1), -5*res.Parameter(2))
     ymax = min( hist.GetYaxis().GetBinCenter(hist.GetNbinsY()), 5*res.Parameter(2))
     hist.GetYaxis().SetRangeUser(ymin,ymax)
     hist.Draw('colz')
# get time x correlation, X = m*dt + b
     h['g'+hname] = ROOT.TGraph()
     g = h['g'+hname]
     xproj = hist.ProjectionX('tmpx')
     if xproj.GetSumOfWeights()==0:   continue
     np = 0
     Lmin = hist.GetSumOfWeights() * 0.005
     for nx in range(hist.GetXaxis().FindBin(xmin),hist.GetXaxis().FindBin(xmax)):
            tmp = hist.ProjectionY('tmp',nx,nx)
            if tmp.GetEntries()<Lmin:continue
            X   = hist.GetXaxis().GetBinCenter(nx)
            rc = tmp.Fit('gaus','NQS')
            res = rc.Get()
            if not res: dt = tmp.GetMean()
            else:   dt = res.Parameter(1)
            g.SetPoint(np,X,dt)
            np+=1
     g.SetLineColor(ROOT.kRed)
     g.SetLineWidth(2)
     g.Draw('same')
     rc = g.Fit('pol1','SQ','',xmin,xmax)
     g.GetFunction('pol1').SetLineColor(ROOT.kGreen)
     g.GetFunction('pol1').SetLineWidth(2)
     result = rc.Get()
     if not result:   continue
     m = 1./result.Parameter(1)
     b = -result.Parameter(0) * m
     sign = '+'
     if b<0: sign = '-'
     txt = 'X = %5.1F #frac{cm}{ns} #times #frac{1}{2}#Deltat %s %5.1F '%(m,sign,abs(b))
     latex.SetTextSize(0.07)
     latex.DrawLatexNDC(0.2,0.8,txt)

#  Scifi specific code
def Scifi_xPos(detID):
        orientation = (detID//100000)%10
        nStation = 2*(detID//1000000-1)+orientation
        mat   = (detID%100000)//10000
        X = detID%1000+(detID%10000)//1000*128
        return [nStation,mat,X]   # even numbers are Y (horizontal plane), odd numbers X (vertical plane)

def Scifi_slopes(Nev=options.nEvents):
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
                        aCluster = ROOT.sndCluster(first,N,hitlist,Scifi)
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

def Scifi_residuals(Nev=options.nEvents,NbinsRes=100,xmin=-500.,alignPar=False):
    projs = {1:'V',0:'H'}
    for s in range(1,6):
     for o in range(2):
        for p in projs:
           proj = projs[p]
           xmax = -xmin
           ut.bookHist(h,'res'+proj+'_Scifi'+str(s*10+o),'residual '+proj+str(s*10+o)+'; [#mum]',NbinsRes,xmin,xmax)
           ut.bookHist(h,'resX'+proj+'_Scifi'+str(s*10+o),'residual '+proj+str(s*10+o)+'; [#mum]',NbinsRes,xmin,xmax,100,-50.,0.)
           ut.bookHist(h,'resY'+proj+'_Scifi'+str(s*10+o),'residual '+proj+str(s*10+o)+'; [#mum]',NbinsRes,xmin,xmax,100,10.,60.)
           ut.bookHist(h,'resC'+proj+'_Scifi'+str(s*10+o),'residual '+proj+str(s*10+o)+'; [#mum]',NbinsRes,xmin,xmax,128*4*3,-0.5,128*4*3-0.5)
           ut.bookHist(h,'track_Scifi'+str(s*10+o),'track x/y '+str(s*10+o),80,-70.,10.,80,0.,80.)
    ut.bookHist(h,'trackChi2/ndof','track chi2/ndof vs ndof',100,0,100,20,0,20)
    ut.bookHist(h,'trackSlopes','track slope; x [mrad]; y [mrad]',1000,-100,100,1000,-100,100)
    parallelToZ = ROOT.TVector3(0., 0., 1.)

    if Nev < 0 : Nev = eventTree.GetEntries()
    N=0
# set alignment parameters
    if alignPar:
       for x in alignPar:
             Scifi.SetConfPar(x,alignPar[x])
    for event in eventTree:
       N+=1
       if N>Nev: break
# select events with clusters in each plane
       theTrack = Scifi_track(nPlanes = 10, nClusters = 11)
       if not hasattr(theTrack,"getFittedState"): continue
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
                   rc = h['res'+projs[o]+'_Scifi'+str(testPlane)].Fill(D/u.um)
                   rc = h['resX'+projs[o]+'_Scifi'+str(testPlane)].Fill(D/u.um,xEx)
                   rc = h['resY'+projs[o]+'_Scifi'+str(testPlane)].Fill(D/u.um,yEx)
                   rc = h['resC'+projs[o]+'_Scifi'+str(testPlane)].Fill(D/u.um,channel)

            theTrack.Delete()
# analysis and plots 
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
            hname = 'res'+proj+projs[o]+'_Scifi'+str(so)
            h[hname].Draw(P[proj])
            if proj == '':
                rc = h[hname].Fit('gaus','SQ')
                fitResult = rc.Get()
                for p in Par:
                   globalPos[p+projs[o]].SetPoint(s-1,s,fitResult.Parameter(Par[p]))
                   globalPos[p+projs[o]].SetPointError(s-1,0.5,fitResult.ParError(1))
                globalPos[p+projs[o]].SetMarkerStyle(21)
                globalPos[p+projs[o]].SetMarkerColor(ROOT.kBlue)
            if proj == 'C':
                for m in range(3):
                     h[hname+str(m)] = h[hname].ProjectionX(hname+str(m),m*512,m*512+512)
                     rc = h[hname+str(m)].Fit('gaus','SQ0')
                     fitResult = rc.Get()
                     for p in Par:
                        h['globalPosM'][p+projs[o]].SetPoint(j[o], s*10+m,   fitResult.Parameter(Par[p]))
                        h['globalPosM'][p+projs[o]].SetPointError(j[o],0.5,fitResult.ParError(1))
                     j[o]+=1
                     h['globalPosM'][p+projs[o]].SetMarkerStyle(21)
                     h['globalPosM'][p+projs[o]].SetMarkerColor(ROOT.kBlue)

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
             print("station %i: offset %s =  %5.2F"%(S.value,p[4:5],M.value))
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
             print("station %i: offset %s =  %5.2F"%(S.value,p[4:5],M.value))
             s = int(S.value*10)
             if p[4:5] == "V": s+=1
             alignPar["Scifi/LocM"+str(s)] = M.value

    return alignPar

def printScifi_residuals(tag='v0'):
    P = {'':'','X':'colz','Y':'colz','C':'colz'}
    for proj in P:
      myPrint(h['scifiRes'+proj],tag+'-scifiRes'+proj)
    for p in h['globalPos']:
      myPrint(h[p],tag+'-scifiRes'+p)
    for p in h['globalPosM']:
      myPrint(h[p+'M'],tag+'-scifiResM'+p)
# make report about alignment constants
    for s in range(1,6):
        for o in range(2):
             mean = [] 
             for m in range(3):
                  x = "Scifi/LocM"+str(s*100+o*10+m)
                  mean.append(Scifi.GetConfParF(x)/u.um)
             XM = (mean[0]+mean[1]+mean[2])/3.
             print("      mean value %8.2F            delta s: %8.2F  %8.2F  %8.2F"%(XM,mean[0]-XM,mean[1]-XM,mean[2]-XM))
# for H6 beam
    h['trackSlopes'].GetYaxis().SetRangeUser(-20,20)
    h['trackSlopes'].GetXaxis().SetRangeUser(-40,0)
    ut.bookCanvas(h,'beamSpot','track slopes',750,750,1,1)
    tc = h['beamSpot'].cd()
    h['trackSlopes'].Draw('colz')
    myPrint(h['beamSpot'],tag+'-beamSpot')

def minimizeAlignScifi(first=True,level=1,minuit=False):
    h['chisq'] = []
    npar = 30
    vstart  = array('d',[0]*npar)
    h['Nevents'] = 10000
    if first:
       h['xmin'] =-5000.
       X = Scifi_residuals(Nev=10000,NbinsRes=100,xmin=h['xmin'])
       for m in range(3):
          vstart[m]     = -X["Scifi/LocD10"]
          vstart[3+m] = -X["Scifi/LocD11"]
       errr = 1000.*u.um
    else:
# best guess from first round
       if level==1:
        for m in range(3):
          vstart[m] = 0.0537
          vstart[1*3+m] = 0.1190
          vstart[2*3+m] = 0.0113
          vstart[3*3+m] = 0.0810
          vstart[4*3+m] = 0.0022
          vstart[5*3+m] = -0.1572
          vstart[6*3+m] = 0.0125
          vstart[7*3+m] = 0.0326
          vstart[8*3+m] = 0.0229
          vstart[9*3+m] = 0.0075
          err = 25.*u.um
          h['xmin'] =-2000.
          h['npar'] = 10
       if level==2:
          vstart[0] =  0.0537
          vstart[1] =  0.0537     
          vstart[2] =  0.0537     
          vstart[3] =  0.1190     
          vstart[4] =  0.1153     
          vstart[5] =  0.1190     
          vstart[6] =  0.0113     
          vstart[7] =  0.0113     
          vstart[8] =  0.0113     
          vstart[9] =  0.0810     
          vstart[10] = 0.0810     
          vstart[11] = 0.0810     
          vstart[12] = 0.0022     
          vstart[13] = 0.0022     
          vstart[14] = 0.0022     
          vstart[15] = -0.1572    
          vstart[16] = -0.1673    
          vstart[17] = -0.1572    
          vstart[18] = 0.0097     
          vstart[19] = 0.0125     
          vstart[20] = 0.0262     
          vstart[21] = 0.0333     
          vstart[22] = 0.0306     
          vstart[23] = 0.0361     
          vstart[24] = 0.0229     
          vstart[25] = 0.0221     
          vstart[26] = 0.0257     
          vstart[27] = -0.0112
          vstart[28] = 0.0405
          vstart[29] = 0.0099
          err = 25.*u.um
          h['xmin'] =-2000.
          h['npar'] = 30
       if level==3:
          h['Nevents'] = 100000
          p = 0
          for s in range(1,6):
             for o in range(2):
                for m in range(3):
                  x = "Scifi/LocM"+str(s*100+o*10+m)
                  vstart[p] = Scifi.GetConfParF(x)
                  p+=1
          err = 25.*u.um
          h['xmin'] =-2000.
          h['npar'] = 30

    ierflg    = ctypes.c_int(0)
    gMinuit = ROOT.TMinuit(npar) # https://root.cern.ch/download/minuit.pdf
    gMinuit.SetFCN(FCN)
    gMinuit.SetErrorDef(1.0)

    p=0
    for s in range(1,6):
        for o in range(2):
             name = "Scifi/LocM"
             for m in range(3):
                 if level==1: gMinuit.mnparm(p, name+str(s*10+o), vstart[p], err, 0.,0.,ierflg)
                 if level==2 or level==3: gMinuit.mnparm(p, name+str(s*100+o*10+m), vstart[p], err, 0.,0.,ierflg)
                 p+=1
    if level == 1:
        for m in range(3):
          gMinuit.FixParameter(m)
          gMinuit.FixParameter(1*3+m)
          if m!=0: 
            for s in range(1,10): gMinuit.FixParameter(s*3+m)
    if level == 2 or level == 3:
# station 1 H
       gMinuit.FixParameter(0)
       gMinuit.FixParameter(1)
       gMinuit.FixParameter(2)
# station 1 V
       gMinuit.FixParameter(3)
       #gMinuit.FixParameter(4)
       gMinuit.FixParameter(5)
# station 2 H
       gMinuit.FixParameter(6)
       gMinuit.FixParameter(7)
       gMinuit.FixParameter(8)
# station 2 V
       gMinuit.FixParameter(9)
       gMinuit.FixParameter(10)
       gMinuit.FixParameter(11)
# station 3 H
       gMinuit.FixParameter(12)
       gMinuit.FixParameter(13)
       gMinuit.FixParameter(14)
# station 3 V
       gMinuit.FixParameter(15)
       #gMinuit.FixParameter(16)
       gMinuit.FixParameter(17)
# station 4 H
       #gMinuit.FixParameter(18)
       gMinuit.FixParameter(19)
       #gMinuit.FixParameter(20)
# station 4 V
       #gMinuit.FixParameter(21)
       #gMinuit.FixParameter(22)
       #gMinuit.FixParameter(23)
# station 5 H
       gMinuit.FixParameter(24)
       #gMinuit.FixParameter(25)
       #gMinuit.FixParameter(26)
# station 5 V
       #gMinuit.FixParameter(27)
       #gMinuit.FixParameter(28)
       #gMinuit.FixParameter(29)

    strat = array('d',[0])
    gMinuit.mnexcm("SET STR",strat,1,ierflg) # 0 faster, 2 more reliable
    gMinuit.mnexcm("SIMPLEX",vstart,npar,ierflg)
    if minuit: gMinuit.mnexcm("MIGRAD",vstart,npar,ierflg)

    h['gChisq']=ROOT.TGraph()
    for n in range(len(h['chisq'])):
           h['gChisq'].SetPoint(n,n,h['chisq'][n])
    p = 'C2'
    ut.bookCanvas(h,p,p,750,750,1,1)
    tc = h[p].cd()
    h['gChisq'].Draw("ALP")

def FCN(npar, gin, f, par, iflag):
#calculate chisquare
   chisq  = 0
   alignPar = {}
   for p in range(h['npar']):
       if h['npar']  == 10:
          s = p//2+1
          o = p%2
          name = "Scifi/LocD"+str(s*10+o)
       if h['npar'] == 30:
          s =  p//6+1
          o = (p%6)//3
          m = p%3
          name = "Scifi/LocM"+str(s*100+o*10+m)
       alignPar[name]  = par[p]
       print('minuit %s %6.4F'%(name,par[p]))
   X = Scifi_residuals(Nev=h['Nevents'],NbinsRes=100,xmin=h['xmin'],alignPar=alignPar)
   for name in X:
       chisq += abs(X[name])
   print('chisq=',chisq,iflag)
   f.value = int(chisq)
   h['chisq'].append(chisq)
   return

def plotsForCollabMeeting():
   drawArea(s=3,p=0,opt='',color=ROOT.kGreen)
   h['track_DS30'].Draw('colzsame')
   myPrint(h['area'],'Extrap2DS30')
   name = 'track_DS30_projx'
   h[name] = h['track_DS30'].ProjectionX(name)
   h[name] .Fit('gaus')
   h['area'].Update()
   stats = h[name].FindObject('stats')
   stats.SetOptStat(1000000000)
   stats.SetOptFit(1111111)
   stats.SetX1NDC(0.62)
   stats.SetY1NDC(0.66)
   stats.SetX2NDC(0.98)
   stats.SetY2NDC(0.94)
   h['area'].Update()
   myPrint(h['area'],'Extrap2DS30_projx')
#
   drawArea(s=1,p=0,opt='',color=ROOT.kGreen)
   myPrint(h['area'],'Extrap2Veto10')
#
   ut.bookCanvas(h,'DSXRes','',2000,600,4,1)
   L = {1:31,2:33,3:35,4:36}
   for n in L:
     tc = h['DSXRes'].cd(n)
     histo = ROOT.gROOT.FindObject('resX_DS'+str(L[n])+'_proj')
     histo.SetTitle('DS'+str(L[n])+';X [cm]')
     histo.Draw()
     tc.Update()
     stats = histo.FindObject('stats')
     stats.SetOptStat(1000000000)
   myPrint(h['DSXRes'],'resDSX')
   ut.bookCanvas(h,'DSYRes','',1500,600,3,1)
   L = {1:30,2:32,3:34}
   for n in L:
     tc = h['DSYRes'].cd(n)
     histo = ROOT.gROOT.FindObject('resY_DS'+str(L[n])+'_proj')
     histo.SetTitle('DS'+str(L[n])+';Y [cm]')
     histo.Draw()
     tc.Update()
     stats = histo.FindObject('stats')
     stats.SetOptStat(1000000000)
     if n==4:
          rc = histo.Fit('gaus','SQ','',-2.,2.)
   myPrint(h['DSYRes'],'resDSY')
#
   ut.bookCanvas(h,'USYRes','',2000,600,5,1)
   L = {1:20,2:21,3:22,4:23,5:24}
   for n in L:
     tc = h['USYRes'].cd(n)
     histo = ROOT.gROOT.FindObject('resY_US'+str(L[n])+'_proj')
     histo.SetTitle('US'+str(L[n])+';Y [cm]')
     histo.Draw()
     tc.Update()
     if n==3 or n==4:
          histo.SetStats(0)
     else:
        stats = histo.FindObject('stats')
        stats.SetOptStat(1000000000)
        stats.SetX1NDC(0.54)
        stats.SetY1NDC(0.77)
        stats.SetX2NDC(0.98)
        stats.SetY2NDC(0.94)
   myPrint(h['USYRes'],'resUSY')
#
   ut.bookCanvas(h,'VEYRes','',800,600,2,1)
   L = {1:10,2:11}
   for n in L:
     tc = h['VEYRes'].cd(n)
     histo = ROOT.gROOT.FindObject('resY_Veto'+str(L[n])+'_proj')
     histo.SetTitle('Veto'+str(L[n])+';Y [cm]')
     histo.Draw()
     tc.Update()
     stats = histo.FindObject('stats')
     stats.SetOptStat(1000000000)
     stats.SetX1NDC(0.54)
     stats.SetY1NDC(0.77)
     stats.SetX2NDC(0.98)
     stats.SetY2NDC(0.94)
     tc.Update()
   myPrint(h['VEYRes'],'resVetoY')
#
   S = {1:'TVE',2:'TUS',3:'TDS'}
   proj = 'X'
   for s in  S:
    sy = sdict[s]
    tname = S[s]
    k=1
    for plane in range(systemAndPlanes[s]):
     if s==3 and (plane%2==1 or plane>5): continue
     tc = h[tname].cd(k)
     k+=1
     key = sy+str(s*10+plane)
     hist = h['dtLRvsX_'+key]
     hist.SetTitle(key+';X [cm];#Deltat  [ns]')
     hist.Draw('colz')
     if hist.GetSumOfWeights()==0:   continue
     g = h['gdtLRvsX_'+key]
     g.Draw('same')
     xmin = hist.GetXaxis().GetXmin()
     xmax = hist.GetXaxis().GetXmax()
     rc = g.Fit('pol1','SQ','',xmin,xmax)
     g.GetFunction('pol1').SetLineColor(ROOT.kGreen)
     g.GetFunction('pol1').SetLineWidth(2)
     result = rc.Get()
     if not result:   continue
     m = 1./result.Parameter(1)
     b = -result.Parameter(0) * m
     sign = '+'
     if b<0: sign = '-'
     txt = 'X = %5.1F #frac{cm}{ns} #times #frac{1}{2}#Deltat %s %5.1F '%(m*2,sign,abs(b))
     latex.SetTextSize(0.07)
     latex.DrawLatexNDC(0.2,0.8,txt)
   myPrint(h['TVE'],'dTvsX_Veto')
   myPrint(h['TUS'],'dTvsX_US')
   myPrint(h['TDS'],'dTvsX_DS')
#
if options.command:
    tmp = options.command.split(';')
    command = tmp[0]+"("
    for i in range(1,len(tmp)):
         command+=tmp[i]
         if i<len(tmp)-1: command+=","
    command+=")"
    print('executing ' + command + "for run ",options.runNumber)
    eval(command)
    print('finished ' + command + "for run ",options.runNumber)
    exit()
else:
    print ('waiting for command. Enter help() for more infomation')

