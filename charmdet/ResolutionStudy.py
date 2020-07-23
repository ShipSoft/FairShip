import ROOT
import rootUtils as ut

hMC={}
hP8={}
hP6={}
results = {}

ut.readHists(hMC,'MSangleStudy_MS10.root')
for x in hMC:
   obj = hMC[x]
   if obj.Class().GetName().find('TH')==0:
       obj.SetLineColor(ROOT.kGreen)
       obj.SetName('MC10'+x)
ut.readHists(hP8,'MSangleStudy_MSP8.root')
for x in hP8:
   obj = hP8[x]
   if obj.Class().GetName().find('TH')==0:
       obj.SetLineColor(ROOT.kMagenta)
       obj.SetName('P8'+x)
ut.readHists(hP6,'MSangleStudy_MSP6.root')
for x in hP6:
   obj = hP6[x]
   if obj.Class().GetName().find('TH')==0:
       obj.SetLineColor(ROOT.kRed)
       obj.SetName('P6'+x)
h ={'P8':hP8,'incl':hMC,'P6':hP6}

hMC['DG'] = ROOT.TF1("DG", "abs(gaus(0)) + abs(gaus(3)) + abs(pol0(6))", -700, 300)
hMC['DG'].SetParName(0,'N1')
hMC['DG'].SetParName(1,'mean')
hMC['DG'].SetParName(2,'sigma1')
hMC['DG'].SetParName(3,'N2')
hMC['DG'].SetParName(4,'mean2')
hMC['DG'].SetParName(5,'sigma2')

# 13.6/P sqrt(L/x0)(1+0.038 log(L/x0)), L/X0 = 412
function = "sqrt((13.6/1000.*sqrt([0])/x*(1.+0.038*log([0])))**2+[1]**2)"
hMC['MSfun'] = ROOT.TF1('MSfun',function,0,400)

dEdx = "(7.63907+0.0315131*x-0.000168569*x*x)*(1-0.085)"
function = "sqrt((13.6/1000.*sqrt([0])/(x+[2])*(1.+0.038*log([0])))**2+[1]**2)"
hMC['MSfunR'] = ROOT.TF1('MSfunR',function,0,400)

ut.bookCanvas(hMC,'dummy',' ',900,600,1,1)

import os
def myPrint(obj,aname):
    name = aname.replace('/','')
    obj.Print(name+'.root')
    obj.Print(name+'.pdf')
    obj.Print(name+'.png')
def myCopy(x):
   if x.find('/')>0:
      template=x.replace('/','_')
      os.system('cp '+x+' '+template)
   else:
      template = x
   if template.find('.pdf')>0:
      os.system('cp '+template+' /mnt/hgfs/VMgate/Jpsi/AnalysisNote/figs/')
   else: os.system('cp '+template+' /mnt/hgfs/VMgate/Jpsi/AnalysisNote/png/')
   if x.find('/')>0: os.system('rm '+template)

def truncatedMean(histo,C=0.9):
# find highest bin for which integral = 90%
    t = C*histo.GetSumOfWeights()
    S=0
    for n in range(1,histo.GetNbinsX()+1):
      S+=histo.GetBinContent(n)
      if S>t: break
    histo.GetXaxis().SetRange(1,n)
    return histo.GetMean(),histo.GetMeanError()

def makeMomSlice(h,x,cat='',CL=1.0,exampleBin=-1):
     h[x+'_p']=h[x].ProjectionX(cat+x+'_p')
     for n in range(1,h[x+'_p'].GetNbinsX()+1):
        tmp=h[x].ProjectionY('tmp',n,n)
        mean,err = truncatedMean(tmp,CL)
        h[x+'_p'].SetBinContent(n,mean)
        h[x+'_p'].SetBinError(n,err)
        if n==exampleBin:
           tmp.Rebin(10)
           tmp.GetXaxis().SetRangeUser(0.0,02)
           tmp.SetTitle(x+'_distrib_'+str(exampleBin))
           tmp.Draw()
           myPrint(hMC['dummy'],x+'_distrib_'+str(exampleBin))
def dEdxCorrection():
  hname = 'dEdx'
  for X in h:
      makeMomSlice(h[X],'dEdx',cat=X)
      hnamep =  hname+'_p'
      rc = h[x][hnamep].Fit('pol3','S','',5.,250.)
def origin():
  ut.bookCanvas(hMC,'target','target',1800,1200,3,2)
  tc = hMC['target'].cd(1)
  tc.SetLogy(1)
  hname = 'Jpsi_originXYZ_projx'
  for X in h:
     print "mean z position for Jpsi origin, ",X,h[X][hname].GetMean(),h[X][hname].GetRMS()
     if h[X][hname].GetSumOfWeights()>1.1: h[X][hname].Scale(1./h[X][hname].GetEntries())
  hP6[hname].Draw('hist')
  hP8[hname].Draw('histsame')
  hMC[hname].Draw('histsame')
  hMC['target'].cd(2)
  hname = 'Jpsi_originXYZ_projy'
  for X in h:
     print "mean x position for Jpsi origin, ",X,h[X][hname].GetMean(),h[X][hname].GetRMS()
     if h[X][hname].GetSumOfWeights()>1.1: h[X][hname].Scale(1./h[X][hname].GetEntries())
  hMC[hname].Draw('hist')
  hP6[hname].Draw('histsame')
  hP8[hname].Draw('histsame')
  hMC['target'].cd(3)
  hname = 'Jpsi_originXYZ_projz'
  for X in h:
     print "mean y position for Jpsi origin, ",X,h[X][hname].GetMean(),h[X][hname].GetRMS()
     if h[X][hname].GetSumOfWeights()>1.1:h[X][hname].Scale(1./h[X][hname].GetEntries())
  hMC[hname].Draw()
  hP6[hname].Draw('same')
  hP8[hname].Draw('same')
  hMC['target'].cd(5)
  hname = 'Jpsi_originXY_Zfix_projx'
  for X in h:
     if h[X][hname].GetSumOfWeights()>1.1:h[X][hname].Scale(1./h[X][hname].GetEntries())
  hMC[hname].Draw()
  hP6[hname].Draw('same')
  hP8[hname].Draw('same')
  hMC['target'].cd(6)
  hname = 'Jpsi_originXY_Zfix_projy'
  for X in h:
     if h[X][hname].GetSumOfWeights()>1.1:h[X][hname].Scale(1./h[X][hname].GetEntries())
  hMC[hname].Draw()
  hP6[hname].Draw('same')
  hP8[hname].Draw('same')
  myPrint(hMC['target'],'ResStudy_origin')
def targetResol():
  normPi = ROOT.TMath.Sqrt(2*ROOT.TMath.Pi())
  h['data'] = hMC
  ut.bookCanvas(hMC,'targetR','target',1800,1200,2,2)
  tc=hMC['dummy'].cd()
  for proj in ['projx','projy']:
    results[proj]={}
    for x in h:
      results[proj][x]={}
      tag = 'Jpsi_mctargetXY_'
      if x=='data': tag = 'Jpsi_targetXY_'
      hist =  h[x][tag+proj]
      h[x][tag+proj+'_w']=hist.Clone(hist.GetName()+'_w')
      h[x][tag+proj+'_w'].Scale(1./hist.GetEntries())
      h[x][tag+proj+'_w'].SetStats(0)
      fun = hMC['DG'].Clone()
      fun.SetParameter(0,10000)
      fun.SetParameter(1,0)
      fun.SetParameter(2,1.) 
      fun.SetParameter(3,100.)
      fun.SetParameter(4,0.)
      fun.SetParameter(5,5.)
      rc = hist.Fit(fun,'S','',-10.,10.)
      rc = hist.Fit(fun,'S','',-10.,10.)
      tc.Update()
      stats = tc.GetPrimitive('stats')
      stats.SetOptStat(1000000001)
      stats.SetOptFit(1111)
      stats.SetFitFormat('5.4g')
      stats.SetX1NDC(0.60)
      stats.SetY1NDC(0.33)
      stats.SetX2NDC(0.98)
      stats.SetY2NDC(0.94)
      tc.Update()
      fitResult = rc.Get()
      s1 = abs(fitResult.Parameter(2))
      s2 = abs(fitResult.Parameter(5))
      n1 = abs(fitResult.Parameter(0))/(normPi*s1)
      n2 = abs(fitResult.Parameter(3))/(normPi*s2)
      m1 = fitResult.Parameter(1)
      m2 = fitResult.Parameter(4)
      mean = (m1*n1+m2*n2)/(n1+n2)
      sigma = (s1*n1+s2*n2)/(n1+n2)
      results[proj][x]['sigma'] = sigma
      results[proj][x]['mean']  = mean
      results[proj][x]['RMS ']  = hist.GetRMS()
  for proj in ['Z','IP']:
    results[proj]={}
    for x in h:
      results[proj][x]={}
      tag = 'Jpsi_mctarget'
      if x=='data': tag = 'Jpsi_target'
      hist =  h[x][tag+proj]
      h[x][tag+proj+'_w']=hist.Clone(hist.GetName()+'_w')
      h[x][tag+proj+'_w'].Scale(1./hist.GetEntries())
      h[x][tag+proj+'_w'].SetStats(0)
      if proj=='Z':
         fun = hMC['DG'].Clone()
         fun.SetParameter(0,1000.)
         fun.SetParameter(1,-400.)
         fun.SetParameter(2,50.)
         fun.SetParameter(3,100.)
         fun.SetParameter(4,-400.)
         fun.SetParameter(5,200.)
         rc = hist.Fit(fun,'S','',-700.,0.)
         rc = hist.Fit(fun,'S','',-700.,0.)
         fitResult = rc.Get()
         s1 = abs(fitResult.Parameter(2))
         s2 = abs(fitResult.Parameter(5))
         n1 = abs(fitResult.Parameter(0))/(normPi*s1)
         n2 = abs(fitResult.Parameter(3))/(normPi*s2)
         m1 = fitResult.Parameter(1)
         m2 = fitResult.Parameter(4)
         mean = (m1*n1+m2*n2)/(n1+n2)
         sigma = (s1*n1+s2*n2)/(n1+n2)
         results[proj][x]['sigma'] = sigma
         results[proj][x]['mean']  = mean
         results[proj][x]['RMS ']  = hist.GetRMS()
         tc.Update()
         stats = tc.GetPrimitive('stats')
         stats.SetOptStat(1000000001)
         stats.SetOptFit(1111)
         stats.SetFitFormat('5.4g')
         stats.SetX1NDC(0.60)
         stats.SetY1NDC(0.33)
         stats.SetX2NDC(0.98)
         stats.SetY2NDC(0.94)
         tc.Update()
      else:
         results[proj][x]['sigma'] = hist.GetRMS()
         results[proj][x]['mean']  = hist.GetMean()
         results[proj][x]['RMS ']  = hist.GetRMS()
  for proj in results:
     for x in results[proj]:
         print "%10s %10s mean=%5.2F  sigma=%5.2F   RMS=%5.2F cm"%(x,proj,results[proj][x]['mean'],results[proj][x]['sigma'],results[proj][x]['RMS '])
  hMC['targetR'].cd(1)
  hist = hMC['Jpsi_targetXY_projx_w']
  hist.SetMaximum(hist.GetMaximum()*1.4)
  hist.SetTitle('extrapolation to target;X [cm];arbitrary units')
  hist.SetLineColor(ROOT.kBlue)
  hist.Draw('hist')
  for x in h:
      if x=='data':continue
      h[x]['Jpsi_mctargetXY_projx_w'].Draw('histsame')
  hMC['targetR'].cd(2)
  hist = hMC['Jpsi_targetXY_projy_w']
  hist.SetTitle('extrapolation to target;Y [cm];arbitrary units')
  hist.SetMaximum(hist.GetMaximum()*1.4)
  hist.SetLineColor(ROOT.kBlue)
  hist.Draw('hist')
  for x in h:
      if x=='data':continue
      h[x]['Jpsi_mctargetXY_projy_w'].Draw('histsame')
  hMC['targetR'].cd(3)
  hist = hMC['Jpsi_targetZ_w']
  hist.SetTitle('extrapolation to target;Z [cm];arbitrary units')
  hist.SetMaximum(hist.GetMaximum()*1.4)
  hist.SetLineColor(ROOT.kBlue)
  hist.Draw('hist')
  for x in h:
      if x=='data':continue
      h[x]['Jpsi_mctargetZ_w'].Draw('histsame')
  hMC['targetR'].cd(4)
  hist = hMC['Jpsi_targetIP_w']
  hist.SetTitle('extrapolation to target;IP [cm];arbitrary units')
  hist.SetMaximum(hist.GetMaximum()*1.4)
  hist.SetLineColor(ROOT.kBlue)
  hist.Draw('hist')
  for x in h:
      if x=='data':continue
      h[x]['Jpsi_mctargetIP_w'].Draw('histsame')
  myPrint(hMC['targetR'],'ResStudy_resol')
def hitResol(CL=0.9):
# distance from measured state to true point.
  hname = 'hitResol'
  hnamep = hname+'_p'
  MC = {'P6':'same', 'P8':'same', 'incl':''}
  for X in MC:
      makeMomSlice(h[X],hname,cat=X,CL=CL,exampleBin=-1)
      h[X][hnamep].SetStats(0)
      h[X][hnamep].SetMaximum(0.25)
      h[X][hnamep].SetMinimum(0.15)
      h[X][hnamep].SetTitle(' ;P_{true}  [GeV/c]; distance to true point [cm]')
      h[X][hnamep].GetXaxis().SetRangeUser(0.,200.)
      h[X][hnamep].Draw(MC[X])
  myPrint(hMC['dummy'],'hitResolution')

def momDirResol():
# angle between reconstructed momentum and true momentum at first state
  hname = 'alpha_pDTpRec'
  hnamep = hname+'_p'
  MC = {'P6':'same', 'P8':'same', 'incl':''}
  for X in MC:
      makeMomSlice(h[X],hname,cat=X,exampleBin=-1)
      h[X][hnamep].SetStats(0)
      h[X][hnamep].SetMaximum(0.003)
      h[X][hnamep].SetMinimum(0.001)
      h[X][hnamep].GetXaxis().SetRangeUser(0.,200.)
      h[X][hnamep].GetYaxis().SetMaxDigits(2)
      h[X][hnamep].SetTitle(' ;P_{true}  [GeV/c]; #Delta#Theta reco-true mom [mrad]')
      h[X][hnamep].Draw(MC[X])
  myPrint(hMC['dummy'],'dirResolution')
def MS():
  tc = hMC['dummy'].cd()
  tc.SetLogy(1)
  for hname in ['alpha_p0pDT']:
    hMC['L'+hname] = ROOT.TLegend(0.21,0.79,0.83,0.97)
    MC = {'P6':'same', 'P8':'same', 'incl':''}
    for X in MC:
      makeMomSlice(h[X],hname,cat=X,exampleBin=-1)
      hnamep = hname+'_p'
      h[X][hnamep].SetStats(0)
      h[X][hnamep].SetMaximum(0.15)
      h[X][hnamep].SetMinimum(0.001)
      h[X][hnamep].SetTitle(' ;P_{true}  [GeV/c]; angle true-reco mom [rad]')
      h[X][hnamep].GetXaxis().SetRangeUser(0.,200.)
      fun = hMC['MSfun'].Clone()
      fun.SetLineColor(h[X][hnamep].GetLineColor())
      fun.FixParameter(1,0.)
      rc = h[X][hnamep].Fit(fun,'SQ','',10,200.)
      fitResult = rc.Get()
      rc = hMC['L'+hname].AddEntry(h[X][hnamep],"%s: equivalent rad. length %5.1F +/-%5.1F X0"%(X,fitResult.Parameter(0),fitResult.ParError(0)),'PL')
      h[X][hnamep].Draw(MC[X])
    hMC['L'+hname].Draw()
  myPrint(hMC['dummy'],'MS')

def MSwithReco():
  tc = hMC['dummy'].cd()
  tc.SetLogy(1)
  MC = {'P6':'same', 'P8':'same', 'incl':''}
  for hname in ['alpha_p0pRec']:
    for X in MC:
      makeMomSlice(h[X],hname,cat=X,exampleBin=-1)
    hMC['L'+hname] = ROOT.TLegend(0.21,0.79,0.83,0.97)
    X='P8'
    hnamep = hname+'_p'
    h[X][hnamep].SetStats(0)
    h[X][hnamep].SetMaximum(0.15)
    h[X][hnamep].SetMinimum(0.001)
    h[X][hnamep].SetTitle(' ;P_{true}  [GeV/c]; angle true-reco mom [rad]')
    h[X][hnamep].GetXaxis().SetRangeUser(0.,200.)
    fun = hMC['MSfun'].Clone()
    fun.SetLineColor(h[X][hnamep].GetLineColor())
    rc = h[X][hnamep].Fit(fun,'SQ','',10,200.)
    fitResult = rc.Get()
    rc = hMC['L'+hname].AddEntry(h[X][hnamep],"%s: equivalent rad. length %5.1F +/-%5.1F X0"%(X,fitResult.Parameter(0),fitResult.ParError(0)),'PL')
    rc = hMC['L'+hname].AddEntry(h[X][hnamep],"const: %5.1F +/-%5.1F mrad"%(fitResult.Parameter(1)*1000,fitResult.ParError(1)*1000),'PL')
    hMC['Tline'+hname]=ROOT.TLine(0,fitResult.Parameter(1),200,fitResult.Parameter(1))
    hMC['Tline'+hname].SetLineColor(ROOT.kGreen)
    h[X][hnamep].Draw()
    h[X]['alpha_p0pDT_p'].Draw('same')
    hMC['Tline'+hname].Draw('same')
    hMC['L'+hname].Draw()
  myPrint(hMC['dummy'],'MSwithReco')

def MSCor():
  tc = hMC['dummy'].cd()
  tc.SetLogy(1)
  MC = {'P6':'same', 'P8':'same', 'incl':''}
  hnames = {'alpha_p0pcor':[ROOT.kRed,''],"alpha_p0pcorRec":[ROOT.kBlue,'same'],"alpha_zTarget_pcorRec":[ROOT.kGreen,'same']}
  for hname in hnames:
    for X in MC:
      makeMomSlice(h[X],hname,cat=X,exampleBin=-1)
  hMC['LMScor'] = ROOT.TLegend(0.14,0.69,0.88,0.86)
  X='P8'
  for hname in ['alpha_p0pcor',"alpha_p0pcorRec","alpha_zTarget_pcorRec"]:
    hnamep = hname+'_p'
    h[X][hnamep].SetLineColor(hnames[hname][0])
    h[X][hnamep].SetStats(0)
    h[X][hnamep].SetMaximum(0.1)
    h[X][hnamep].SetMinimum(0.001)
    h[X][hnamep].SetTitle(' ;P_{true}  [GeV/c]; angle true-cor mom [rad]')
    h[X][hnamep].GetXaxis().SetRangeUser(0.,200.)
    fun = hMC['MSfun'].Clone()
    fun.SetLineColor(h[X][hnamep].GetLineColor())
    rc = h[X][hnamep].Fit(fun,'SQ','',10,200.)
    fitResult = rc.Get()
    txt1 = "%s: eq.rad. length %5.1F +/-%5.1F X0  "%(hname,fitResult.Parameter(0),fitResult.ParError(0))
    txt2 = " const: %5.1F +/-%5.1F mrad"%(fitResult.Parameter(1)*1000,fitResult.ParError(1)*1000)
    rc = hMC['LMScor'].AddEntry(h[X][hnamep],txt1+txt2,'PL')
  for hname in ['alpha_p0pcor',"alpha_p0pcorRec","alpha_zTarget_pcorRec"]:
    hnamep = hname+'_p'
    h[X][hnamep].Draw(hnames[hname][1])
  hMC['LMScor'].Draw()
  myPrint(hMC['dummy'],'MSCor')

def MSCor2():
  tc = hMC['dummy'].cd()
  tc.SetLogy(1)
  hname = "Jpsi_mcDalpha"
  hMC['LMScor2'] = ROOT.TLegend(0.21,0.80,0.95,0.97)
  h['data'] = hMC
  for X in h:
      if X=='data': hn = hname.replace('mc','')
      else:         hn = hname
      hnamep = hn+'_p'
      if not h[X].has_key(hnamep):
         if X!='data':
             makeMomSlice(h[X],'mcDalpha',cat=X,exampleBin=-1)
             makeMomSlice(h[X],'mcDalphaDT',cat=X,exampleBin=-1)
         makeMomSlice(h[X],hn,cat=X,exampleBin=-1)
      if X=='data': h[X][hnamep].SetLineColor(ROOT.kBlue)
      h[X][hnamep].SetStats(0)
      h[X][hnamep].SetMaximum(0.03)
      h[X][hnamep].SetMinimum(0.001)
      h[X][hnamep].SetTitle(' ;P_{rec}  [GeV/c]; angle reco-cor mom [rad]')
      h[X][hnamep].GetXaxis().SetRangeUser(0.,200.)
      funR = hMC['MSfunR'].Clone()
      funR.SetLineColor(h[X][hnamep].GetLineColor())
      rc = h[X][hnamep].Fit(funR,'SQ','',10,200.)
      fitResult = rc.Get()
      txt1 = "%s: eq.rad. length %5.1F +/-%5.1F X0  "%(X,fitResult.Parameter(0),fitResult.ParError(0))
      txt2 = " const: %5.1F +/-%5.1F mrad"%(fitResult.Parameter(1)*1000,fitResult.ParError(1)*1000)
      rc = hMC['LMScor2'].AddEntry(h[X][hnamep],txt1+txt2,'PL')
  h['data']["Jpsi_Dalpha_p"].Draw()
  for X in h:
      if X=='data': continue
      h[X]["Jpsi_mcDalpha_p"].Draw('same')
  hMC['LMScor2'].Draw()
  myPrint(hMC['dummy'],'MSCor')
def compareWithJpsi(CL=0.9):
  tc = hMC['dummy'].cd()
  tc.SetLogy(1)
  fitResults = {}
  for X in h:
      if X=='data': continue
      fitResults[X]={}
      for j in ['','Jpsi_']:
         fitResults[X][j]={}
         for hname in [j+"mcDalpha",j+"alpha_p0pRec",j+"alpha_p0pcorRec"]:
             makeMomSlice(h[X],hname,cat=X,CL=CL,exampleBin=-1)
             funR=hMC['MSfunR'].Clone()
             funR.SetParameter(0,100.)
             funR.SetParameter(1,1E-3)
             funR.SetParameter(2,0.)
             if not hname.find('p0')<0: funR.FixParameter(2,0)
             rc = h[X][hname+'_p'].Fit(funR,'SQ','',25,200.)
             if hname.find('p0')<0:  rc = h[X][hname+'_p'].Fit(funR,'SQ','',10,200.)
             F = rc.Get()
             fitResults[X][j][hname]={'lam':[F.Parameter(0),F.ParError(0)],
             'res':[F.Parameter(1),F.ParError(1)],
              'dE':[F.Parameter(2),F.ParError(2)]}
  makeMomSlice(h['incl'],'Jpsi_Dalpha',cat='incl',CL=CL,exampleBin=-1)
  funR=hMC['MSfunR'].Clone()
  funR.SetParameter(0,100.)
  funR.SetParameter(1,1E-3)
  funR.SetParameter(2,0.)
  rc = h['incl']['Jpsi_Dalpha_p'].Fit(funR,'SQ','',10,200.)
  F = rc.Get()
  fitResults['data']={}
  fitResults['data']['Jpsi']={}
  fitResults['data']['Jpsi']['Jpsi_Dalpha']={'lam':[F.Parameter(0),F.ParError(0)],
             'res':[F.Parameter(1),F.ParError(1)],
              'dE':[F.Parameter(2),F.ParError(2)]}
  print "    MC          histo: lambda          resol       dE"  
"
  for j in ['','Jpsi_']:
    for hname in [j+"alpha_p0pRec",j+"alpha_p0pcorRec",j+"mcDalpha"]:
      for X in h:
        if X=='data': continue
        F = fitResults[X][j][hname]
        print "%6s  %20s: %5.2F+/-%5.2F  %5.2F+/-%5.2F  %5.2F+/-%5.2F   "%(X,hname,F['lam'][0],F['lam'][1],F['res'][0]*1000.,F['res'][1]*1000.,F['dE'][0],F['res'][1])
  X='data'
  j='Jpsi'
  hname = 'Jpsi_Dalpha'
  F = fitResults[X][j][hname]
  print "%6s  %20s: %5.2F+/-%5.2F  %5.2F+/-%5.2F  %5.2F+/-%5.2F   "%(X,hname,F['lam'][0],F['lam'][1],F['res'][0]*1000.,F['res'][1]*1000.,F['dE'][0],F['res'][1])
  
  return fitResults


def test():
   hnames = ['mcDalpha','mcDalphaDT']
   for hname in hnames:
      for X in h:
         makeMomSlice(h[X],hname,cat=X,exampleBin=-1)
def newInvMass():
   M = 3.1
