"""
Utitlity for TDC calibration
 --- step 1: produce plots from MuFilterEff root file: makeCalibrationHistos(r,readHists=True,t0_channel=4)
                 histograms are in  /eos/experiment/sndlhc/calibration/commissioning/MuFilterEff_runXXX.root
 --- step 2: fill dictionary with calibration parameters per run: getCalibrationParameters(runList=options.runNumbers)
                 location of TDC plots/TCanvas /eos/experiment/sndlhc/calibration/commissioning/TDC
 --- getRunStatistics(r): returns number of fitted tracks for run r, useful to check if enough statistics
"""

import ROOT,os
import rootUtils as ut
import shipunit as u

h={}

eosroot = os.environ['EOSSHIP']
systemAndChannels     = {1:[8,0],2:[6,2],3:[1,0]}
systemAndPlanes  = {1:2,2:5,3:7}
systemAndBars     = {1:7,2:10,3:60}
sdict                     = {1:'Veto',2:'US',3:'DS'}
barColor = [ROOT.kRed,ROOT.kRed-7,ROOT.kMagenta,ROOT.kMagenta-6,ROOT.kBlue,ROOT.kBlue-9,
                      ROOT.kCyan,ROOT.kAzure-4,ROOT.kGreen,ROOT.kGreen+3]
def smallSiPMchannel(i):
    if i==2 or i==5 or i==10 or i==13: return True
    else: return False

def myPrint(tc,name,withRootFile=True):
     tc.Update()
     tc.Print(name+'-run'+str(options.runNumber)+'.png')
     tc.Print(name+'-run'+str(options.runNumber)+'.pdf')
     if withRootFile: tc.Print(name+'-run'+str(options.runNumber)+'.root')

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-p", "--Path", dest="path", help="path to histograms",default="/eos/experiment/sndlhc/calibration/commissioning/")
parser.add_argument("-r", "--runNumbers", dest="runNumbers", help="list of run numbers, comma separated",default=None,required=True)
parser.add_argument("-c", "--command", dest="command", help="command", default="")

h = {}
gain={'H8':{}}
gain['H8'][3.65] = [49,50,51,52,53,58,59,71,74,80,86,89]
gain['H8'][2.5]   =[46,47,54,55,56,60,72,81,87,90]
gain['H8'][1.0]   =[73,82,88,91]
gain={'H6':{}}
gain['H6'][3.65] =[247,248,249,250,251,252,253,254,255,284,290]
gain['H6'][2.5]   =[286,292,298,301]
gain['H6'][1.0]   =[288,300,302]

options = parser.parse_args()
if options.path.find("/eos")==0: options.path= eosroot+options.path

def getRunStatistics(r):
    F = ROOT.TFile.Open(options.path+"MuFilterEff_run"+str(r)+".root")
    X = F.GetKey('trackslxy').ReadObj()
    ntracks = X.GetEntries()
    F.Close()
    return ntracks

def extractMeanAndSigma(tdcCanvas,s):
    C = {}
    f = ROOT.TFile.Open(tdcCanvas)
    tTDCcalib = f.Get('tTDCcalib_'+sdict[s]).Clone()
    for pad in tTDCcalib.GetListOfPrimitives():
        for z in pad.GetListOfPrimitives():
             if z.Class_Name() == 'TH1D':     tag = z.GetName()
             if z.Class_Name() == 'TGraphErrors': graph = z
        station = tag.split('_')[1]
        if not station in C: C[station]={}
        case = 'sigma'
        if tag.find('Mean')>0: case='mean'
        if not case in C[station]: C[station][case]={}
        for n in range(graph.GetN()):
           C[station][case][ int(z.GetPointX(n)) ]=[ z.GetPointY(n),z.GetErrorY(n)]
    return C

def overlayMean(tdcCanvas,s):
   f = ROOT.TFile.Open(tdcCanvas)
   tTDCcalib = f.Get('tTDCcalib_'+sdict[s]).Clone()
   names = []
   for pad in tTDCcalib.GetListOfPrimitives():
        for z in pad.GetListOfPrimitives():
             if z.Class_Name().find('TH1')==0:  tag = z.GetName()
        if tag.find('Mean')<0: continue
        for z in pad.GetListOfPrimitives():
             if z.Class_Name().find('TH1')==0:
                 h[tag] = z.Clone('h'+tag)
                 h[tag].SetDirectory(ROOT.gROOT)
                 Ltag = tag
             if z.Class_Name() == 'TGraphErrors': 
                  h['g'+tag] = z.Clone()
                  names.append('g'+tag)
   # split in left and right TGraphs
   for  g in names: 
      h['L'+g] = ROOT.TGraphErrors()
      h['R'+g] = ROOT.TGraphErrors()
      for x in ['L','R']:
           h[x+g].SetLineColor(h[g].GetLineColor())
           h[x+g].SetMarkerStyle(h[g].GetMarkerStyle())
      for n in range(h[g].GetN()):
          if h[g].GetPointX(n)<80:
             nl = h['L'+g].GetN()
             h['L'+g].SetPoint(nl,h[g].GetPointX(n),h[g].GetPointY(n))
             h['L'+g].SetPointError(nl,h[g].GetErrorX(n),h[g].GetErrorY(n))
          else:
             nr = h['R'+g].GetN()
             h['R'+g].SetPoint(nr,h[g].GetPointX(n)-80,h[g].GetPointY(n))
             h['R'+g].SetPointError(nr,h[g].GetErrorX(n)-80,h[g].GetErrorY(n))
   ROOT.gROOT.cd()
   h[Ltag].SetStats(0)
   h['T'] = ROOT.TCanvas('T',sdict[s],1,1,1200,900)
   h['T'].cd()
   h[Ltag].GetXaxis().SetRange(1,81)
   h[Ltag].Draw()
   for  g in names: 
        h['L'+g].Draw('same')
        h['R'+g].Draw('same')
   return

def getTDCdelays(path="TDCdelays.txt"):
  f = open(path)
  L = f.readlines()
  delays = {}
  lstart = 0
  if len(L)>20: lstart = 21
  for l in range(lstart,len(L)):
       tmp = L[l].split(',')
       for z in tmp:
           x = z.split('=')
           if len(x)<2: continue
           value = float(x[1])
           name = int(x[0].split('_')[1])
           delays[name]=value
  h['D'] = ROOT.TGraph()
  h['D'].SetLineWidth(2)
  n = 0
  for bar_number in range(systemAndBars[2]):
      for channel in range(8):
          h['D'].SetPoint(n,n,delays[10*bar_number+channel]/1000.)
          n+=1
  

def getCalibrationParameters(runList=options.runNumbers):
   C = {}
   for r in runList.split(','):
          C[int(r)]={1:{},2:{}}
          for s in [1,2]:
             if int(r)<100 and s==1: continue   # no veto in H8
             tdcCanvas = options.path+"TDC/TDCcalibration_"+sdict[s]+"-run"+r+'.root'
             C[int(r)][s] = extractMeanAndSigma(tdcCanvas,s)
   return C
          
def runStability(C=None):
    if not C: C = getCalibrationParameters(options.runNumbers)
    runEvol = {1:{},2:{}}
    badChannels = {1:{},2:{}}
    for r in C:
       for s in C[r]:
          for l in C[r][s]:
            for i in C[r][s][l]['mean']:
               value = C[r][s][l]['mean'][i]
               key = l+'_'+str(i)
               rError = value[1] / value[0]
               if rError > 0.05: continue # remove distributions with low statistics
               if not key in runEvol[s]: runEvol[s][key] = ROOT.TGraph()
               n = runEvol[s][key].GetN()
               runEvol[s][key].SetPoint(n,value[0],1.)
          ut.bookHist(h,'rms'+sdict[s],'rms',1000,-1.,1.)
          ut.bookCanvas(h,sdict[s],'',900,600,1,1)
          h[sdict[s]].cd()
          for key in runEvol[s]:
            x = runEvol[s][key].GetRMS()/runEvol[s][key].GetMean()
            rc = h['rms'+sdict[s]].Fill(x)
            if abs(x)>0.2: badChannels[key]=x
            print("%s : %5.2F  %5.2F  %5.2F"%(key,x,runEvol[s][key].GetRMS(),runEvol[s][key].GetMean()))
          h['rms'+sdict[s]+'100']=h['rms'+sdict[s]].Rebin(10,'rms'+sdict[s]+'100')
          h['rms'+sdict[s]+'100'].Draw()
    return runEvol,badChannels

def makeCalibrationHistos(X=options.runNumbers,readHists=True,t0_channel=4):
 for r in X.split(','):
    if readHists:
       F = ROOT.TFile.Open(options.path+"MuFilterEff_run"+str(r)+".root")
    options.runNumber = r
    for s in [1,2]:
      if s==1 and int(r)<100: continue       # no Veto in H8
      h['tdcCalib'+sdict[s]] = {}
      for l in range(systemAndPlanes[s]):
        for bar in range(systemAndBars[s]):
           for side in ['L','R']:
              key = sdict[s]+str(s*10+l)+'_'+str(bar)
              for i in range(systemAndChannels[s][1]+systemAndChannels[s][0]):
                  if i==t0_channel: continue
                  j = side+'_'+key+'-c'+str(i)
                  x = 'TDCcalib'+j
                  # get TDC calibration constants:
                  h['tdcCalib'+sdict[s]][j] =[0,0,0,0]
                  h[x] = F.GetKey(x).ReadObj()
                  if h[x].GetEntries()>10: 
                       rc =  h[x].Fit('gaus','SNQ')
                       rc =  h[x].Fit('gaus','SNQ')
                       if rc:
                          res = rc.Get()
                          h['tdcCalib'+sdict[s]][j] =[res.Parameter(1),res.ParError(1),res.Parameter(2),res.ParError(2)]
#
      for l in range(systemAndPlanes[s]):
        tag = sdict[s]+str(l)
        ut.bookCanvas(h,'sigmaTDC_'+tag,'TDC RMS '+tag,2000,600,systemAndBars[s],2)
        ut.bookCanvas(h,  'TDCcalib_'+tag,'TDC TDCi-T0 '+tag,2000,600,systemAndBars[s],2)
        k=1
        for bar in range(systemAndBars[s]):
           for side in ['L','R']:
              key = sdict[s]+str(10*s+l)+'_'+str(bar)
              for i in range(systemAndChannels[s][1]+systemAndChannels[s][0]):
                  j = side+'_'+key+'-c'+str(i)
                  for x in ['sigmaTDC_'+tag,'TDCcalib_'+tag]:
                     if x.find('calib')>0 and (i==t0_channel):  continue
                     tc=h[x].cd(k)
                     opt='same'
                     if i==0 and x.find('calib')<0: opt=""
                     if i==1 and x.find('calib')>0: opt=""
                     aHist = x.split('_')[0]+j
                     h[aHist] = F.GetKey(aHist).ReadObj()
                     h[aHist].SetLineColor(barColor[i])
                     h[aHist].GetXaxis().SetRangeUser(-5,5)
                     h[aHist].Draw(opt)
                     h[aHist].Draw(opt+'HIST')
              k+=1
        myPrint(h['sigmaTDC_'+tag],'TDC/TDCrms_'+tag)
        myPrint(h['TDCcalib_'+tag],'TDC/TDCcalib_'+tag)
#
        ut.bookHist(h,'TDCcalibMean_'+tag,';SiPM channel ; [ns]',160,0.,160.)
        ut.bookHist(h,'TDCcalibSigma_'+tag,';SiPM channel ; [ns]',160,0.,160.)
        h['gTDCcalibMean_'+tag]=ROOT.TGraphErrors()
        h['gTDCcalibSigma_'+tag]=ROOT.TGraphErrors()
#
      for x in h['tdcCalib'+sdict[s]]:
               tmp =  h['tdcCalib'+sdict[s]][x]
               side = 0
               z = x.split('_')
               if z[0]=='R': side = 1
               l = z[1][len(z[1])-1]
               bar = z[2][0]
               c = z[2].split('c')[1]
               xbin = int(bar)*16+side*8+int(c)
               tag = sdict[s]+str(l)
               rc = h['TDCcalibMean_'+tag].SetBinContent(xbin+1,tmp[0])
               rc = h['TDCcalibMean_'+tag].SetBinError(xbin+1,tmp[1])
               rc = h['TDCcalibSigma_'+tag].SetBinContent(xbin+1,tmp[2])
               rc = h['TDCcalibSigma_'+tag].SetBinError(xbin+1,tmp[3])
               #print("%s %5.2F+/-%5.2F  %5.2F+/-%5.2F"%(x,tmp[0],tmp[1],tmp[2],tmp[3]))
      ut.bookCanvas(h,'tTDCcalib_'+sdict[s],'TDC calib '+sdict[s],2400,1800,2,systemAndPlanes[s])
      for l in range(systemAndPlanes[s]):
           tag = sdict[s]+str(l)
           aHistS  = h['TDCcalibSigma_'+tag]
           aHistM = h['TDCcalibMean_'+tag]
           k=0
           for i in range(1,aHistS.GetNbinsX()):
               if aHistS.GetBinContent(i)>0:
                 h['gTDCcalibSigma_'+tag].SetPoint(k,i-1,aHistS.GetBinContent(i))
                 h['gTDCcalibSigma_'+tag].SetPointError(k,0.5,aHistS.GetBinError(i))
                 h['gTDCcalibMean_'+tag].SetPoint(k,i-1,aHistM.GetBinContent(i))
                 h['gTDCcalibMean_'+tag].SetPointError(k,0.5,aHistM.GetBinError(i))
                 k+=1
#
      planeColor = {0:ROOT.kBlue,1:ROOT.kRed,2:ROOT.kGreen,3:ROOT.kCyan,4:ROOT.kMagenta}
      for l in range(systemAndPlanes[s]):
                tag = sdict[s]+str(l)
                tc = h['tTDCcalib_'+sdict[s]].cd(2*l+1)
                aHistS = h['TDCcalibSigma_'+tag]
                aHistS.Reset()
                aHistS.SetMaximum(2.0)
                aHistS.Draw()
                h['gTDCcalibSigma_'+tag].SetLineColor(planeColor[l])
                h['gTDCcalibSigma_'+tag].Draw('same')
#
      for l in range(systemAndPlanes[s]):
                tag = sdict[s]+str(l)
                tc = h['tTDCcalib_'+sdict[s]].cd(2*l+2)
                aHistM = h['TDCcalibMean_'+tag]
                aHistM.Reset()
                aHistM.SetMaximum(2.0)
                aHistM.SetMinimum(-2.0)
                aHistM.Draw()
                h['gTDCcalibMean_'+tag].SetLineColor(planeColor[l])
                h['gTDCcalibMean_'+tag].Draw('same')
      myPrint(h['tTDCcalib_'+sdict[s]],'TDC/TDCcalibration_'+sdict[s])


def checkPattern(C):
   for r in C:
    for system in C[r]:
       for plane in C[r][sytem]:
         for channel in C[r][sytem]['mean']:
             continue

if options.command:
    tmp = options.command.split(';')

    if tmp[0].find('.C')>0:    # execute a C macro
        ROOT.gROOT.LoadMacro(tmp[0])
        ROOT.Execute()
        exit()
    command = tmp[0]+"("
    for i in range(1,len(tmp)):
         command+=tmp[i]
         if i<len(tmp)-1: command+=","
    command+=")"
    print('executing ' + command + "for run ",options.runNumbers)
    eval(command)
    print('finished ' + command + "for run ",options.runNumbers)

