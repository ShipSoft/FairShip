import ROOT,os
import rootUtils as ut
import shipunit as u
h={}
from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-r", "--runNumber", dest="runNumber", help="run number", type=int,required=True)
parser.add_argument("-f", "--inputFile", dest="fname", help="file name for MC", type=str,default=None,required=False)
parser.add_argument("-g", "--geoFile", dest="geoFile", help="geofile", required=True)
options = parser.parse_args()

fgeo = ROOT.TFile.Open(options.geoFile)
from ShipGeoConfig import ConfigRegistry
from rootpyPickler import Unpickler
#load geo dictionary
upkl    = Unpickler(fgeo)
snd_geo = upkl.load('ShipGeo')
# -----Create geometry----------------------------------------------
import shipLHC_conf as sndDet_conf
run = ROOT.FairRunSim()
modules = sndDet_conf.configure(run,snd_geo)
sGeo = fgeo.FAIRGeom
modules['Scifi'].SiPMmapping()

if options.runNumber>0: 
              f=ROOT.TFile.Open('sndsw_raw_'+str(options.runNumber).zfill(6)+'.root')
              eventTree = f.rawConv
else:
              f=ROOT.TFile.Open(options.fname)
              eventTree = f.cbmsim

def hitMaps(Nev=-1):
 # veto system 2 layers with 7 bars and 8 sipm channels on both ends
 # US system 5 layers with 10 bars and 8 sipm channels on both ends
 for l in range(0,2):
    ut.bookHist(h,'hit_1'+str(l),'hit map / plane',160,-0.5,159.5)
    ut.bookHist(h,'bar_1'+str(l),'hit map / plane',10,-0.5,9.5)
    ut.bookHist(h,'sig_1'+str(l),'signal / plane',150,0.0,150.)
 for l in range(0,5):
    ut.bookHist(h,'hit_2'+str(l),'hit map / plane',160,-0.5,159.5)
    ut.bookHist(h,'bar_2'+str(l),'hit map / plane',10,-0.5,9.5)
    ut.bookHist(h,'sig_2'+str(l),'signal / plane',150,0.0,150.)
 # DS system horizontal(3) planes, 60 bars, readout on both sides, single channel
#                         vertical(4) planes, 60 bar, readout on top, single channel
 for l in range(0,10):
    ut.bookHist(h,'hit_3'+str(l),'hit map / plane',120,-0.5,119.5)
    ut.bookHist(h,'bar_3'+str(l),'hit map / plane',60,-0.5,59.5)
    ut.bookHist(h,'sig_3'+str(l),'signal / plane',150,0.0,150.)

 N=-1
 if Nev < 0 : Nev = eventTree.GetEntries()
 for event in eventTree:
    N+=1
    if N>Nev: break
    for aHit in event.Digi_MuFilterHit:
        if not aHit.isValid(): continue
        detID = aHit.GetDetectorID()
        s = detID//10000
        l  = (detID%10000)//1000
        bar = (detID%1000)
        if s>2: 
               l=2*l
               if bar>59:
                    bar=bar-60
                    l+=1
        nSiPMs = aHit.GetnSiPMs()
        nSides  = aHit.GetnSides()

# check left/right
        if nSides==2 and 0>1:
                for i in range(nSiPMs):
                      print( "%i  %5.2F   %5.2F"%(i,aHit.GetSignal(i),aHit.GetSignal(i+nSiPMs)) )
        for p in range(nSides):
            c=bar*nSiPMs*nSides + p*nSiPMs
            for i in range(nSiPMs):
               signal = aHit.GetSignal(i+p*nSiPMs)
               #print(detID,s,l,bar,c,i,signal),c+i
               if signal > 0:
                  rc = h['hit_'+str(s)+str(l)].Fill(c+i)
                  rc = h['bar_'+str(s)+str(l)].Fill(bar)
                  rc  = h['sig_'+str(s)+str(l)].Fill(signal)
 ut.bookCanvas(h,'hitmaps',' ',1200,1600,3,10)
 ut.bookCanvas(h,'barmaps',' ',1200,1600,3,10)
 ut.bookCanvas(h,'signal',' ',1200,1600,3,10)

 system = {1:2,2:5,3:10}
 for S in system:
   for l in range(system[S]):
      n = S + l*3
      tc = h['hitmaps'].cd(n)
      h['hit_'+str(S)+str(l)].Draw()
      tc = h['barmaps'].cd(n)
      h['bar_'+str(S)+str(l)].Draw()
      tc = h['signal'].cd(n)
      h['sig_'+str(S)+str(l)].Draw()

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

def eventTime():
 Tprev = -1
 freq = 160.E6
 ut.bookHist(h,'Etime','delta event time; dt [s]',100,0.0,1.)
 ut.bookHist(h,'EtimeZ','delta event time; dt',100,0.0,10.)
 ut.bookCanvas(h,'E',' ',1024,2*768,1,2)
 eventTree.GetEvent(0)
 t0 =  eventTree.EventHeader.GetEventTime()/160.E6
 eventTree.GetEvent(eventTree.GetEntries()-1)
 tmax = eventTree.EventHeader.GetEventTime()/160.E6
 ut.bookHist(h,'time','elapsed time; t [s]',1000,0,tmax-t0)
 for event in eventTree:
    T = event.EventHeader.GetEventTime()
    dT = 0
    if Tprev >0: dT = T-Tprev
    Tprev = T
    rc = h['Etime'].Fill(dT/freq)
    rc = h['EtimeZ'].Fill(dT)
    rc = h['time'].Fill( (T/freq-t0))
 tc = h['E'].cd(1)
 h['Etime'].Draw()
 tc.Update()
 tc = h['E'].cd(2)
 h['time'].Draw()
