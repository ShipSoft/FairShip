import ROOT
import rootUtils as ut

hdataV={}
hP8V={}
hMC={}
hP8={}
hP6={}
results = {}

ut.readHists(hP8V,'myVertex-P8.root')
for x in hP8V:
   obj = hP8V[x]
   if obj.Class().GetName().find('TH')==0:
       obj.SetLineColor(ROOT.kMagenta)
       obj.SetName('MCP8V'+x)
ut.readHists(hdataV,'myVertex-data.root')
for x in hdataV:
   obj = hdataV[x]
   if obj.Class().GetName().find('TH')==0:
       obj.SetLineColor(ROOT.kBlue)
       obj.SetName('hdataV'+x)
hv ={'P8':hP8V,'data':hdataV}

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
h['data'] = hMC
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
hMC['MSfun'].SetLineColor(ROOT.kCyan)

dEdx = "(7.63907+0.0315131*x-0.000168569*x*x)*(1-0.085)"
function = "sqrt((13.6/1000.*sqrt([0])/(x+[2])*(1.+0.038*log([0])))**2+[1]**2)"
hMC['MSfunR'] = ROOT.TF1('MSfunR',function,0,400)

sqrt2pi = ROOT.TMath.Sqrt(2*ROOT.TMath.Pi())
def foldedGaus(x,par):
   return par[0]/(par[2]*sqrt2pi)*(ROOT.TMath.Exp(-(par[1]-x)**2/(2*par[2]**2))+ROOT.TMath.Exp(-(par[1]-x)**2/(2*par[2]**2)))
absGaus = "[0]/([2]*sqrt(2*3.1414))*(exp(-([1]-x)**2/(2*[2]**2))+exp(-([1]+x)**2/(2*[2]**2)))"
hMC['absGaus'] = ROOT.TF1('absGaus',absGaus,0,0.2)
hMC['absGaus'].SetParName(0,'N')
hMC['absGaus'].SetParName(1,'mean')
hMC['absGaus'].SetParName(2,'sig')

ut.bookCanvas(hMC,'dummy',' ',900,600,1,1)
ut.bookCanvas(hMC,'2d',' ',900,1200,1,2)

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

def makeMomSlice(h,x,cat='',CL=1.0,exampleBin=-1,method='gaus'):
     h[x+'_p']=h[x].ProjectionX(cat+x+'_p')
     h[x+'_m']=h[x].ProjectionX(cat+x+'_m')
     G = hMC['DG'].Clone('G')
     G.FixParameter(3,0)
     G.FixParameter(4,0)
     G.FixParameter(5,1)
     for n in range(1,h[x+'_p'].GetNbinsX()+1):
        tmp=h[x].ProjectionY('tmp',n,n)
        if method=='mean':
            mean,err = truncatedMean(tmp,CL)
        if method=='RMS':
            mean,err = tmp.GetRMS(),tmp.GetRMSError()
        if method=='gaus':
            tmp.Rebin(1000)
            G.SetParameter(0,tmp.GetMaximum())
            G.SetParameter(1,0.)
            G.SetParameter(2,0.001)
            G.SetParameter(6,0)
            rc = tmp.Fit(G,'LSQ')
            fitresult = rc.Get()
            sigma  = min(0.1,5*abs(fitresult.Parameter(2)))
            rc = tmp.Fit(G,'LSQ','',-sigma,sigma)
            fitresult = rc.Get()
            mean,err = 9999.,1.
            if fitresult:
              mean,err = abs(fitresult.Parameter(2)),fitresult.ParError(2)
              h[x+'_m'].SetBinContent(n,fitresult.Parameter(1))
              h[x+'_m'].SetBinError(n,fitresult.ParError(1))
        h[x+'_p'].SetBinContent(n,mean)
        h[x+'_p'].SetBinError(n,err)
        if n==exampleBin:
           tmp.Rebin(10)
           tmp.GetXaxis().SetRangeUser(0.0,0.1)
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
def primVertexResol():
  normPi = ROOT.TMath.Sqrt(2*ROOT.TMath.Pi())
  ut.bookCanvas(hMC,'primV','primary vertex',1800,900,3,1)
  tc=hMC['dummy'].cd()
  hv ={'P8':hP8V,'data':hdataV}
  for X in hv:
       hv[X]["primVx_X"]= hv[X]['targetXYZ'].Project3D('z')
       hv[X]["primVx_X"].SetName(X+"primVx_X")
       hv[X]["primVx_Y"]= hv[X]['targetXYZ'].Project3D('y')
       hv[X]["primVx_Y"].SetName(X+"primVx_Y")
       hv[X]["primVx_Z"]= hv[X]['targetXYZ'].Project3D('x')
       hv[X]["primVx_Z"].SetName(X+"primVx_Z")
       results[X] = {}
       for p in ['X','Y','Z']:
        results[X][p] = {}
        hist = "primVx_"
        hv[X][hist+p+'_w']=hv[X][hist+p].Clone(hist+p+'_w')
        hv[X][hist+p+'_w'].Scale(1./hv[X][hist+p].GetEntries())
        hv[X][hist+p+'_w'].SetStats(0)
        fun = hMC['DG'].Clone()
        fun.SetParameter(0,hv[X][hist+p].GetMaximum())
        if p=='Z':
          fun.SetParameter(1,-400.)
          fun.SetParameter(2,50.)
          fun.FixParameter(3,0.)
          fun.FixParameter(4,-400.)
          fun.FixParameter(5,150.)
          fun.SetParameter(6,0.)
        else:
          fun.SetParameter(1,0)
          fun.SetParameter(2,1.)
          fun.FixParameter(3,0.)
          fun.FixParameter(4,0.)
          fun.FixParameter(5,10.)
          fun.SetParameter(6,0.)
        if p=='Z': 
          rc = hv[X][hist+p].Fit(fun,'SQL','',-700.,0.)
          for i in range(3,6): fun.ReleaseParameter(i)
          fun.FixParameter(4,fun.GetParameter(1))
          rc = hv[X][hist+p].Fit(fun,'SQL','',-700.,0.)
        else: "bJpsi_Dalpha"+p+"_p"
          rc = hv[X][hist+p].Fit(fun,'SQL','',-10.,10.)
          for i in range(3,6): fun.ReleaseParameter(i)
          fun.FixParameter(4,fun.GetParameter(1))
          rc = hv[X][hist+p].Fit(fun,'SQL','',-4.,4.)
          rc = hv[X][hist+p].Fit(fun,'SQL','',-10.,10.)
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
        bw = hv[X][hist+p].GetBinWidth(1)
        s1 = abs(fitResult.Parameter(2))
        s2 = abs(fitResult.Parameter(5))
        n1 = abs(fitResult.Parameter(0))*(normPi*s1)/bw
        n2 = abs(fitResult.Parameter(3))*(normPi*s2)/bw
        m1 = fitResult.Parameter(1)
        m2 = fitResult.Parameter(4)
        mean = (m1*n1+m2*n2)/(n1+n2)
        sigma = ROOT.TMath.Sqrt((n1*s1*s1+n2*s2*s2)/(n1+n2))
        results[X][p]['sigmaCor'] = [min(s1,s2),fitResult.ParError(2)]
        results[X][p]['sigma'] = [sigma,fitResult.ParError(2)]
        results[X][p]['mean']  = [mean,fitResult.ParError(1)]
        results[X][p]['RMS']  = hv[X][hist+p].GetRMS()
  for X in results:
    for p in results[X]:
         print "%10s %10s mean=%6.2F+/-%6.2F  sigma=%6.2F+/-%6.2F core=%6.2F   RMS=%6.2F cm"%(X,
             p,results[X][p]['mean'][0],results[X][p]['mean'][1],
             results[X][p]['sigma'][0],results[X][p]['sigma'][1],results[X][p]['sigmaCor'][0],results[X][p]['RMS'])
  j=1
  for p in ['X','Y','Z']:
    hMC['primV'].cd(j)
    j+=1
    hname = 'primVx_'+p
    X = 'data'
    hist = hv[X][hname+'_w']
    hist.SetMaximum(hist.GetMaximum()*1.3)
    hist.SetTitle('primary vertex ;'+p+' [cm];arbitrary units')
    hist.SetLineColor(ROOT.kBlue)
    hist.Draw()
    histo = hv[X][hname]
    W = histo.GetSumOfWeights()
    hv[X]['F'+hname] = histo.GetFunction('DG').Clone('F'+hname)
    hv[X]['F'+hname].SetLineColor(hist.GetLineColor())
    hv[X]['F'+hname].SetParameter(0,hv[X]['F'+hname].GetParameter(0)/W)
    hv[X]['F'+hname].SetParameter(3,hv[X]['F'+hname].GetParameter(3)/W)
    hv[X]['F'+hname].SetParameter(6,hv[X]['F'+hname].GetParameter(6)/W)
    hv[X]['F'+hname].Draw('same')
    X='P8'
    hv[X][hname+'_w'].Draw('histsame')
  myPrint(hMC['primV'],'primaryVertex')
def targetResol(pmin=29,pmax=75):
 # projx = momentum, projz = X, projy = y
  normPi = ROOT.TMath.Sqrt(2*ROOT.TMath.Pi())
  ut.bookCanvas(hMC,'targetR','target',1800,1200,2,2)
  tc=hMC['dummy'].cd()
  # select high momentum 100GeV - 300GeV
  interval = [pmin,pmax]
  for hname in ['targetXY','targetZ','targetIP']:
     for X in h:
        if X!='data': hn = 'mc'+hname
        else: hn=hname
        for j in ['','Jpsi_']:
           if j=='' and X=='data': continue
           hnn = j+hn
           if hname.find('XY')>0:
             h[X][j+hn].GetXaxis().SetRange(interval[0],interval[1])
             h[X][j+hn+'_highMom'] = h[X][j+hn].Project3D('yz')
             h[X][j+hn+'_highMom'].SetName(X+j+hn+'_highMom')
             h[X][j+hn+'_projx']=h[X][j+hn+'_highMom'].ProjectionY(X+j+hn+'_projx')
             h[X][j+hn+'_projy']=h[X][j+hn+'_highMom'].ProjectionX(X+j+hn+'_projy')
           else:
             h[X][j+hn+'_highMom'] = h[X][j+hn].ProjectionY(X+j+hn+'_highMom',interval[0],interval[1])
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
      fun.SetParameter(0,hist.GetMaximum())
      fun.SetParameter(1,0)
      fun.SetParameter(2,1.)
      fun.FixParameter(3,0.)
      fun.FixParameter(4,0.)
      fun.FixParameter(5,10.)
      fun.SetParameter(6,0.)
      rc = hist.Fit(fun,'SQL','',-10.,10.)
      for i in range(3,6): fun.ReleaseParameter(i)
      fun.FixParameter(4,fun.GetParameter(1))
      rc = hist.Fit(fun,'SQL','',-4.,4.)
      rc = hist.Fit(fun,'SQL','',-10.,10.)
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
      bw = hist.GetBinWidth(1)
      s1 = abs(fitResult.Parameter(2))
      s2 = abs(fitResult.Parameter(5))
      n1 = abs(fitResult.Parameter(0))*(normPi*s1)/bw
      n2 = abs(fitResult.Parameter(3))*(normPi*s2)/bw
      m1 = fitResult.Parameter(1)
      m2 = fitResult.Parameter(4)
      mean = (m1*n1+m2*n2)/(n1+n2)
      sigma = ROOT.TMath.Sqrt((n1*s1*s1+n2*s2*s2)/(n1+n2))
      results[proj][x]['sigmaCor'] = [min(s1,s2),fitResult.ParError(2)]
      results[proj][x]['sigma'] = [sigma,fitResult.ParError(2)]
      results[proj][x]['mean']  = [mean,fitResult.ParError(1)]
      results[proj][x]['RMS ']  = hist.GetRMS()
  for proj in ['Z','IP']:
    results[proj]={}
    for x in h:
      results[proj][x]={}
      tag = 'Jpsi_mctarget'
      if x=='data': tag = 'Jpsi_target'
      hist =  h[x][tag+proj+'_highMom']
      h[x][tag+proj+'_w']=hist.Clone(hist.GetName()+'_w')
      h[x][tag+proj+'_w'].Scale(1./hist.GetEntries())
      h[x][tag+proj+'_w'].SetStats(0)
      if proj=='Z':
         fun = hMC['DG'].Clone()
         fun.SetParameter(0,hist.GetMaximum())
         fun.SetParameter(1,-400.)
         fun.SetParameter(2,50.)
         fun.SetParameter(3,hist.GetMaximum()*0.10)
         fun.FixParameter(4,-400.)
         fun.SetParameter(5,200.)
         rc = hist.Fit(fun,'SQL','',-700.,0.)
         fun.ReleaseParameter(4)
         rc = hist.Fit(fun,'SQL','',-700.,0.)
         fitResult = rc.Get()
         bw = hist.GetBinWidth(1)
         s1 = abs(fitResult.Parameter(2))
         s2 = abs(fitResult.Parameter(5))
         n1 = abs(fitResult.Parameter(0))*(normPi*s1)/bw
         n2 = abs(fitResult.Parameter(3))*(normPi*s1)/bw
         m1 = fitResult.Parameter(1)
         m2 = fitResult.Parameter(4)
         mean = (m1*n1+m2*n2)/(n1+n2)
         sigma = ROOT.TMath.Sqrt((n1*s1*s1+n2*s2*s2)/(n1+n2))
         results[proj][x]['sigmaCor'] = [min(s1,s2),fitResult.ParError(2)]
         results[proj][x]['sigma'] = [sigma,fitResult.ParError(2)]
         results[proj][x]['mean']  = [mean,fitResult.ParError(1)]
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
         results[proj][x]['sigmaCor'] = [0,0]
         results[proj][x]['sigma'] = [hist.GetRMS(),hist.GetRMSError()]
         results[proj][x]['mean']  = [hist.GetMean(),hist.GetMeanError()]
         results[proj][x]['RMS ']  = hist.GetRMS()
  for proj in results:
     for x in results[proj]:
         print "%10s %10s mean=%5.2F+/-%5.2F  sigma=%5.2F+/-%5.2F core=%5.2F   RMS=%5.2F cm"%(x,
             proj,results[proj][x]['mean'][0],results[proj][x]['mean'][1],
             results[proj][x]['sigma'][0],results[proj][x]['sigma'][1],results[proj][x]['sigmaCor'][0],results[proj][x]['RMS '])
  hMC['targetR'].cd(1)
  hname = 'Jpsi_targetXY_projx'
  hist = hMC[hname+'_w']
  hist.SetMaximum(hist.GetMaximum()*1.4)
  hist.SetTitle('extrapolation to target;X [cm];arbitrary units')
  hist.SetLineColor(ROOT.kBlue)
  hist.Draw()
  histo = hMC[hname]
  W = histo.GetSumOfWeights()
  hMC['F'+hname] = histo.GetFunction('DG').Clone('F'+hname)
  hMC['F'+hname].SetLineColor(hist.GetLineColor())
  hMC['F'+hname].SetParameter(0,hMC['F'+hname].GetParameter(0)/W)
  hMC['F'+hname].SetParameter(3,hMC['F'+hname].GetParameter(3)/W)
  hMC['F'+hname].SetParameter(6,hMC['F'+hname].GetParameter(6)/W)
  hMC['F'+hname].Draw('same')
  for x in h:
      if x=='data':continue
      h[x]['Jpsi_mctargetXY_projx_w'].Draw('histsame')
  hMC['targetR'].cd(2)
  hname = 'Jpsi_targetXY_projy'
  hist = hMC[hname+'_w']
  hist.SetMaximum(hist.GetMaximum()*1.4)
  hist.SetTitle('extrapolation to target;Y [cm];arbitrary units')
  hist.SetLineColor(ROOT.kBlue)
  hist.Draw()
  histo = hMC[hname]
  W = histo.GetSumOfWeights()
  hMC['F'+hname] = histo.GetFunction('DG').Clone('F'+hname)
  hMC['F'+hname].SetLineColor(hist.GetLineColor())
  hMC['F'+hname].SetParameter(0,hMC['F'+hname].GetParameter(0)/W)
  hMC['F'+hname].SetParameter(3,hMC['F'+hname].GetParameter(3)/W)
  hMC['F'+hname].SetParameter(6,hMC['F'+hname].GetParameter(6)/W)
  hMC['F'+hname].SetLineColor(hist.GetLineColor())
  hMC['F'+hname].Draw('same')  
  for x in h:
      if x=='data':continue
      hist = h[x]['Jpsi_mctargetXY_projy_w']
      hist.Draw('histsame')
  hMC['targetR'].cd(3)
  hname = 'Jpsi_targetZ'
  hist = hMC[hname+'_w']
  hist.SetTitle('extrapolation to target;Z [cm];arbitrary units')
  hist.SetLineColor(ROOT.kBlue)
  rebin = 5
  hist.Rebin(rebin)
  hist.SetMaximum(hist.GetMaximum()*1.4)
  hist.Draw()
  histo = hMC[hname+'_highMom']
  W = histo.GetSumOfWeights()/float(rebin)
  hMC['F'+hname] = histo.GetFunction('DG').Clone('F'+hname)
  hMC['F'+hname].SetLineColor(hist.GetLineColor())
  hMC['F'+hname].SetParameter(0,hMC['F'+hname].GetParameter(0)/W)
  hMC['F'+hname].SetParameter(3,hMC['F'+hname].GetParameter(3)/W)
  hMC['F'+hname].SetParameter(6,hMC['F'+hname].GetParameter(6)/W)
  hMC['F'+hname].Draw('same')
  for x in h:
      if x=='data':continue
      hist = h[x]['Jpsi_mctargetZ_w']
      hist.Rebin(rebin)
      hist.Draw('histsame')
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
def hitResol(CL=1.0):
# distance from measured state to true point.
  MC = {'P6':'same', 'P8':'same', 'incl':''}
  for j in ['','Jpsi_']:
    for X in MC:
      for p in ['_x','_y']:
        hname = j+'hitResol'+p
        hnamep = hname+'_p'
        makeMomSlice(h[X],hname,cat=X,CL=CL,exampleBin=-1,method='RMS')
        h[X][hnamep].SetStats(0)
        h[X][hnamep].SetMinimum(0.0)
        h[X][hnamep].SetMaximum(0.2)
        h[X][hnamep].SetTitle(' ;P_{true}  [GeV/c]; distance to true point [cm]')
        h[X][hnamep].GetXaxis().SetRangeUser(0.,200.)
  k=1
  for p in ['_x','_y']:
     tc=hMC['2d'].cd(k)
     tc.SetLogy(0)
     k+=1
     h['P6']['Jpsi_hitResol'+p+'_p'].Draw()
     for j in ['Jpsi_']:
       for X in MC:
         h[X][hnamep].Draw()
         hname = j+'hitResol'+p
         hnamep = hname+'_p'
         h[X][hnamep].Draw('same')
  myPrint(hMC['2d'],'hitResolution')

def momDirResol(CL=1.0):
# angle between reconstructed momentum and true momentum at first state
  MC = {'P6':'same', 'P8':'same', 'incl':''}
  P  = {'_x':0.002,'_y':0.005}
  PS = P.keys()
  PS.sort()
  for X in MC:
    for p in P:
      hname = 'alpha_pDTpRec'+p
      h[X][hname].GetYaxis().SetRangeUser(-0.02,0.02)
      makeMomSlice(h[X],hname,cat=X,CL=CL,exampleBin=-1,method='RMS')
  for X in MC:
    k=1
    for p in PS:
      tc=hMC['2d'].cd(k)
      tc.SetLogy(0)
      k+=1
      hname = 'alpha_pDTpRec'+p
      hnamep = hname+'_p'
      h[X][hnamep].SetStats(0)
      h[X][hnamep].SetMaximum(P[p])
      h[X][hnamep].SetMinimum(0.000)
      h[X][hnamep].GetXaxis().SetRangeUser(0.,200.)
      h[X][hnamep].GetYaxis().SetMaxDigits(2)
      h[X][hnamep].SetTitle(' ;P_{true}  [GeV/c]; #Delta#Theta reco-true mom [rad]')
      h[X][hnamep].Draw(MC[X])
  myPrint(hMC['2d'],'dirResolution')
def MS(CL=1.0):
  MC = {'P6':'same', 'P8':'same', 'incl':''}
  P  = {'_x':0.15,'_y':0.15}
  PS = P.keys()
  PS.sort()
  k=1
  for p in PS:
     tc=hMC['2d'].cd(k)
     k+=1
     tc.SetLogy(1)
     for hname in ['alpha_p0pDT']:
        hMC['L'+hname+p] = ROOT.TLegend(0.21,0.79,0.83,0.97)
        for X in MC:
          makeMomSlice(h[X],hname+p,cat=X,CL=CL,exampleBin=-1)
          hnamep = hname+p+'_p'
          h[X][hnamep].SetStats(0)
          h[X][hnamep].SetMaximum(P[p])
          h[X][hnamep].SetMinimum(0.001)
          h[X][hnamep].SetTitle(' ;P_{true}  [GeV/c]; angle true-reco mom [rad]')
          h[X][hnamep].GetXaxis().SetRangeUser(0.,200.)
          fun = hMC['MSfun'].Clone()
          fun.SetLineColor(h[X][hnamep].GetLineColor())
          fun.FixParameter(1,0.)
          rc = h[X][hnamep].Fit(fun,'SQ','',10,200.)
          fitResult = rc.Get()
          rc = hMC['L'+hname+p].AddEntry(h[X][hnamep],"%s: equivalent rad. length %5.1F +/-%5.1F X0"%(X,fitResult.Parameter(0),fitResult.ParError(0)),'PL')
        h[X][hnamep].Draw()
        for X in MC:
          hnamep = hname+p+'_p'
          h[X][hnamep].Draw('same')
        hMC['L'+hname+p].Draw()
  myPrint(hMC['2d'],'MS_'+str(int(100*CL)))

def MSwithReco(CL=1.0):
  MC = {'P6':'same'}
  P  = {'_x':0.15,'_y':0.15}
  PS = P.keys()
  PS.sort()
  k=1
  for p in PS:
     tc=hMC['2d'].cd(k)
     k+=1
     tc.SetLogy(1)
     for hname in ['alpha_p0pRec']:
        for X in MC:
           makeMomSlice(h[X],hname+p,cat=X,CL=CL,exampleBin=-1)
           hMC['L'+hname+p] = ROOT.TLegend(0.19,0.66,0.94,0.73)
           hnamep = hname+p+'_p'
           h[X][hnamep].SetStats(0)
           h[X][hnamep].SetMaximum(P[p])
           h[X][hnamep].SetMinimum(0.001)
           h[X][hnamep].SetTitle(' ;P_{true}  [GeV/c]; angle true-reco mom [rad]')
           h[X][hnamep].GetXaxis().SetRangeUser(0.,200.)
           fun = hMC['MSfun'].Clone()
           fun.SetLineColor(h[X][hnamep].GetLineColor())
           rc = h[X][hnamep].Fit(fun,'SQ','',10,200.)
           fitResult = rc.Get()
           hMC['Tline'+hname+p]=ROOT.TLine(0,fitResult.Parameter(1),200,fitResult.Parameter(1))
           hMC['Tline'+hname+p].SetLineColor(ROOT.kGreen)
           txt1 = "%s: equivalent rad. length %5.1F +/-%5.1F X0"%(X,fitResult.Parameter(0),fitResult.ParError(0))
           txt2 = ", const: %5.1F +/-%5.1F mrad"%(fitResult.Parameter(1)*1000,fitResult.ParError(1)*1000)
           rc = hMC['L'+hname+p].AddEntry(h[X][hnamep],txt1+txt2,'PL')
           rc.SetTextColor(hMC['Tline'+hname+p].GetLineColor())
           h[X][hnamep].Draw()
           h[X]['alpha_p0pDT'+p+'_p'].SetLineColor(ROOT.kMagenta)
           h[X]['alpha_p0pDT'+p+'_p'].GetFunction("MSfun").SetLineColor(ROOT.kMagenta)
           h[X]['alpha_p0pDT'+p+'_p'].Draw('same')
           hMC['Tline'+hname+p].Draw('same')
           hMC['L'+hname+p].Draw()
  myPrint(hMC['2d'],'MSwithReco_'+str(CL))

def MSCor(CL=1.0):
  MC = {'P6':'same', 'P8':'same', 'incl':''}
  hnames = {'alpha_p0pcor':[ROOT.kRed,''],"alpha_p0pcorRec":[ROOT.kBlue,'same'],"alpha_zTarget_pcorRec":[ROOT.kGreen,'same']}
  P  = {'_x':0.15,'_y':0.15}
  PS = P.keys()
  PS.sort()
  k=1
  for p in PS:
     tc=hMC['2d'].cd(k)
     k+=1
     tc.SetLogy(1)
     for hname in hnames:
        for X in MC:
          makeMomSlice(h[X],hname+p,cat=X,CL=CL,exampleBin=-1)
     hMC['LMScor'+p] = ROOT.TLegend(0.14,0.69,0.88,0.86)
     X='P6'
     for hname in ['alpha_p0pcor',"alpha_p0pcorRec","alpha_zTarget_pcorRec"]:
       hnamep = hname+p+'_p'
       h[X][hnamep].SetLineColor(hnames[hname][0])
       h[X][hnamep].SetStats(0)
       h[X][hnamep].SetMaximum(0.1)
       h[X][hnamep].SetMinimum(0.001)
       h[X][hnamep].SetTitle(' ;P_{true}  [GeV/c]; angle true-cor mom [rad]')
       h[X][hnamep].GetXaxis().SetRangeUser(0.,200.)
       funR = hMC['MSfunR'].Clone()
       funR.SetParameter(0,100.)
       funR.SetParameter(1,0)
       funR.SetParLimits(1,0.,9999.)
       funR.SetParameter(2,3.)
       funR.SetLineColor(h[X][hnamep].GetLineColor())
       rc = h[X][hnamep].Fit(funR,'SQ','',10,200.)
       fitResult = rc.Get()
       txt1 = "%s: eq.rad. length %5.1F +/-%5.1F X0  "%(hname,fitResult.Parameter(0),fitResult.ParError(0))
       txt2 = " const: %5.1F +/-%5.1F mrad"%(fitResult.Parameter(1)*1000,fitResult.ParError(1)*1000)
       txt3 = " dE %5.1F +/-%5.1F GeV"%(fitResult.Parameter(2),fitResult.ParError(2))
       rc = hMC['LMScor'+p].AddEntry(h[X][hnamep],txt1+txt2+txt3,'PL')
     for hname in ['alpha_p0pcor',"alpha_p0pcorRec","alpha_zTarget_pcorRec"]:
        hnamep = hname+p+'_p'
        h[X][hnamep].Draw(hnames[hname][1])
     hMC['LMScor'+p].Draw()
  myPrint(hMC['2d'],'MSCor_'+str(CL))

def MSCor2(CL=1.0,rebin=2):
  P  = {'_x':0.05,'_y':0.1}
  PS = P.keys()
  PS.sort()
  k=1
  for p in PS:
     tc=hMC['2d'].cd(k)
     k+=1
     tc.SetLogy(1)
     hname = "Jpsi_mcDalpha"+p
     hMC['LMScor2'+p] = ROOT.TLegend(0.21,0.80,0.95,0.97)
     h['data'] = hMC
     for X in h:
         if X=='data': hn = hname.replace('mc','')
         else:         hn = hname
         if X!='data':
             makeMomSlice(h[X],'mcDalpha'+p,cat=X,CL=CL,exampleBin=-1)
             makeMomSlice(h[X],'mcDalphaDT'+p,cat=X,CL=CL,exampleBin=-1)
         h[X]['b'+hn] = h[X][hn].Clone('b'+hn)
         hn = 'b'+hn
         hnamep = hn+'_p'
         h[X][hn].Rebin(rebin)
         makeMomSlice(h[X],hn,cat=X,CL=CL,exampleBin=-1)
         if X=='data': h[X][hnamep].SetLineColor(ROOT.kBlue)
         h[X][hnamep].SetStats(0)
         h[X][hnamep].SetMaximum(P[p])
         h[X][hnamep].SetMinimum(0.001)
         h[X][hnamep].SetTitle(' ;P_{rec}  [GeV/c]; angle reco-cor mom [rad]')
         h[X][hnamep].GetXaxis().SetRangeUser(0.,200.)
         funR = hMC['MSfunR'].Clone()
         funR.SetParameter(0,100.)
         funR.SetParameter(1,2E-3)
         funR.SetParameter(2,3.)
         funR.SetLineColor(h[X][hnamep].GetLineColor())
         rc = h[X][hnamep].Fit(funR,'SQ','',13,200.)
         fitResult = rc.Get()
         txt1 = "%s: eq.rad. length %5.1F +/-%5.1F X0  "%(X,fitResult.Parameter(0),fitResult.ParError(0))
         txt2 = " const: %5.1F +/-%5.1F mrad"%(fitResult.Parameter(1)*1000,fitResult.ParError(1)*1000)
         txt3 = " dE %5.1F +/-%5.1F GeV"%(fitResult.Parameter(2),fitResult.ParError(2))
         rc = hMC['LMScor2'+p].AddEntry(h[X][hnamep],txt1+txt2+txt3,'PL')
     h['data']["bJpsi_Dalpha"+p+"_p"].SetMaximum(0.02)
     h['data']["bJpsi_Dalpha"+p+"_p"].Draw()
     for X in h:
         if X=='data': continue
         h[X]["bJpsi_mcDalpha"+p+"_p"].Draw('same')
     hMC['LMScor2'+p].Draw()
  myPrint(hMC['2d'],'MSCor2_'+str(CL))
def compareWithJpsi(CL=0.9):
  tc = hMC['dummy'].cd()
  tc.SetLogy(1)
  P  = {'_x':0.15,'_y':0.15}
  PS = P.keys()
  PS.sort()
  k=1
  fitResults = {}
  for p in PS:
     tc=hMC['2d'].cd(k)
     k+=1
     tc.SetLogy(1)
     for X in h:
         if X=='data': continue
         fitResults[X+p]={}
         for j in ['','Jpsi_']:
            fitResults[X+p][j]={}
            for hname in [j+"mcDalpha"+p,j+"alpha_p0pRec"+p,j+"alpha_p0pcorRec"+p]:
               makeMomSlice(h[X],hname,cat=X,CL=CL,exampleBin=-1)
               funR=hMC['MSfunR'].Clone()
               funR.SetParameter(0,100.)
               funR.SetParameter(1,1E-3)
               funR.SetParameter(2,0.)
               if not hname.find('p0')<0: funR.FixParameter(2,0)
               rc = h[X][hname+'_p'].Fit(funR,'SQ','',25,200.)
               if hname.find('p0')<0:  rc = h[X][hname+'_p'].Fit(funR,'SQ','',10,200.)
               F = rc.Get()
               fitResults[X+p][j][hname]={'lam':[F.Parameter(0),F.ParError(0)],
               'res':[F.Parameter(1),F.ParError(1)],
                'dE':[F.Parameter(2),F.ParError(2)]}
     makeMomSlice(h['incl'],'Jpsi_Dalpha'+p,cat='incl',CL=CL,exampleBin=-1)
     funR=hMC['MSfunR'].Clone()
     funR.SetParameter(0,100.)
     funR.SetParameter(1,1E-3)
     funR.SetParameter(2,0.)
     rc = h['incl']['Jpsi_Dalpha'+p+'_p'].Fit(funR,'SQ','',10,200.)
     F = rc.Get()
     fitResults['data'+p]={}
     fitResults['data'+p]['Jpsi']={}
     fitResults['data'+p]['Jpsi']['Jpsi_Dalpha']={'lam':[F.Parameter(0),F.ParError(0)],
             'res':[F.Parameter(1),F.ParError(1)],
              'dE':[F.Parameter(2),F.ParError(2)]}
     print "    MC          histo: lambda          resol       dE"  
     for j in ['','Jpsi_']:
       for hname in [j+"alpha_p0pRec"+p,j+"alpha_p0pcorRec"+p,j+"mcDalpha"+p]:
         for X in h:
           if X=='data': continue
           F = fitResults[X+p][j][hname]
           print "%6s  %20s: %5.2F+/-%5.2F  %5.2F+/-%5.2F  %5.2F+/-%5.2F   "%(X,hname,F['lam'][0],F['lam'][1],F['res'][0]*1000.,F['res'][1]*1000.,F['dE'][0],F['res'][1])
     X='data'
     j='Jpsi'
     hname = 'Jpsi_Dalpha'+p
     F = fitResults[X+p][j][hname]
     print "%6s  %20s: %5.2F+/-%5.2F  %5.2F+/-%5.2F  %5.2F+/-%5.2F   "%(X,hname,F['lam'][0],F['lam'][1],F['res'][0]*1000.,F['res'][1]*1000.,F['dE'][0],F['res'][1])
  
  return fitResults
def momDistribution():
  tc=hMC['dummy'].cd()
  tc.SetLogy(0)
  p='_x'
  hname = "Jpsi_mcDalpha"+p
  hMC['LPdis'+p] = ROOT.TLegend(0.5,0.6,0.72,0.76)
  h['data'] = hMC
  for X in h:
        hn = hname
        if X=='data':hn = hname.replace('mc','')
        h[X][hn+'P']=h[X][hn].ProjectionX(X+hn+'P')
        h[X][hn+'P'].SetTitle('')
        h[X][hn+'P'].SetStats(0)
        h[X][hn+'P'].Scale(1./h[X][hn+'P'].GetEntries())
  h['P6'][hname+'P'].Draw()
  for X in h:
        hn=hname
        if X=='data':
             hn = hname.replace('mc','')
             h[X][hn+'P'].SetLineColor(ROOT.kBlue)
        h[X][hn+'P'].Draw('same')
        rc = hMC['LPdis'+p].AddEntry(h[X][hn+'P'],X,'PL')
  hMC['LPdis'+p].Draw()
  myPrint(hMC['dummy'],'MSPdis')
def test():
   hnames = ['mcDalpha','mcDalphaDT']
   for hname in hnames:
      for X in h:
         makeMomSlice(h[X],hname,cat=X,exampleBin=-1)
def Gaus3D(N=100000,mean=0,sigma=1):
     ut.bookHist(h,'X','X',100,-10.,10.)
     ut.bookHist(h,'Y','Y',100,-10.,10.)
     ut.bookHist(h,'R','R',100,0.,10.)
     ut.bookCanvas(h,'gaus',1200,900,3,1)
     rnr = ROOT.TRandom()
     funR = ROOT.TF1('funR','x*[0]/[2]**2*[1]*exp(-x*x/(2*[2]**2))')
     for n in range(N):
        X=rnr.Gaus()*sigma+mean
        Y=rnr.Gaus()*sigma+mean
        Z=ROOT.TMath.Sqrt(X*X+Y*Y)
        rc = h['X'].Fill(X)
        rc = h['Y'].Fill(Y)
        rc = h['R'].Fill(Z)
     rc = h['R'].Fit(funR,'S','',0.,10.)
     tc=h['gaus'].cd(1)
     h['X'].Draw()
     tc=h['gaus'].cd(2)
     h['Y'].Draw()
     tc=h['gaus'].cd(3)
     h['R'].Draw()
     print h['R'].GetMean(),h['gaus3d'].GetRMS()

def newInvMass():
   M = 3.1
