import ROOT,os,time,operator,subprocess
import ctypes
import rootUtils as ut
from argparse import ArgumentParser
from decorators import *
PDG = ROOT.TDatabasePDG.Instance()
cuts = {}
cuts['muTrackMatchX']= 5.
cuts['muTrackMatchY']= 10.
zTarget = -377. # for Jpsi # -370. all muons      # start of target: -394.328, mean z for mu from Jpsi in MC = -375cm, for all muons: -353cm
 # for improved resolution
ycor1C = "0.5*log( (sqrt(pcor*pcor+3.0969*3.0969)+sqrt(pcor*pcor-ptcor*ptcor))/(sqrt(pcor*pcor+3.0969*3.0969)-sqrt(pcor*pcor-ptcor*ptcor)))"

cuts['zRPC1']  = 878.826706
cuts['xLRPC1'] =-97.69875
cuts['xRRPC1'] = 97.69875
cuts['yBRPC1'] =-41.46045
cuts['yTRPC1'] = 80.26905

MCStats = {'1GeV': 1.806E9,'10GeV':66.02E9}
dataStats      = 324.75E9
simpleEffCorMu = 0.021
simpleEffCor   = 0.024

muonMass = 0.105658

DYfactor = MCStats['10GeV']/(2*20000*99.) * (42*26.1+(96-42)*23.5)/96.*1E-6/10.5 # adjusted for PDF set 4, rescaled mass distribution
#DYfactor = MCStats['10GeV']/1940000 * (42*73.0+(96-42)*66.2)/96.*1E-6/10.5 # adjusted for PDF set 13
DYfactor4NA50 = 1.51

# counting primary interactions
Charmfactor = MCStats['10GeV']/(285.3828E9)  # for 14 cycles

NA50crossSection = [3.994,0.148]
lumi    = 30.7 # pb-1
elumi   = 0.7

mcSysError = 0.03
daSysError = 0.021

hData   = {}
hMC     = {}

fGlobal = {}
fGlobal['etaNA50'] = ROOT.TF1('etaNA50','abs([0])*exp(-0.5*((x-[1])/[2])**2)',-2.,2.)
fGlobal['etaNA50'].SetParameter(0,1.)
fGlobal['etaNA50'].SetParameter(1,-0.2)
fGlobal['etaNA50'].SetParameter(2,0.85)


sqrt2 = ROOT.TMath.Sqrt(2.)

Debug = False

host = os.uname()[1]
if host=="ubuntu":
    gPath = "/media/truf/disk2/home/truf/ShipSoft/ship-ubuntu-1710-32/"
elif host=='ship-ubuntu-1710-32':
    gPath = "/home/truf/muflux/"
else:
    gPath = "/home/truf/ship-ubuntu-1710-32/"
topDir =  os.path.abspath('.')


h0 = {}
h  = {}

parser = ArgumentParser()
parser.add_argument("-b", "--batch", dest="batch", help="run in batch mode",action="store_true", default=False)
parser.add_argument("-f", "--files", dest="listOfFiles", help="list of files comma separated", default=False)
parser.add_argument("-d", "--dir",   dest="directory", help="directory", default=False)
parser.add_argument("-c", "--cmd",   dest="command", help="command to execute", default="")
parser.add_argument("-p", "--path",  dest="path", help="path to ntuple", default="")
parser.add_argument("-t", "--type",  dest="MCType", help="version of MC", default="final") # other versions: "0", "multHits", "noDeadChannels", "withDeadChannels"
parser.add_argument("-A", "--with1GeV",    dest="with1GeV", help="1GeV MC",              default="False")
parser.add_argument("-C", "--withcharm",   dest="withCharm", help="charm 1GeV MC",       default="False")
parser.add_argument("-X", "--withcharm2",  dest="withCharm2", help="coherent charm",    default="False")
parser.add_argument("-B", "--with10GeV",   dest="with10GeV", help="10GeV MC",            default="False")
parser.add_argument("-D", "--withData",    dest="withData", help="use default data set", default="False")
parser.add_argument("-J", "--withJpsi",    dest="withJpsi", help="use Jpsi data set",    default="False")
parser.add_argument("-8", "--withJpsiP8",  dest="withJpsiP8", help="use Jpsi pythia8 data set",    default="False")
parser.add_argument("-Y", "--withDrellYan",  dest="withDrellYan", help="use Drell Yan data set",   default="False")
parser.add_argument("-x", dest="ncpus", help="number of parallel jobs", default=False)
parser.add_argument("-s", dest="nseq", help="sequence of parallel job", default=0)
parser.add_argument("-r", dest="refit", help="use refitted ntuples", required=False, action="store_true")
parser.add_argument("--JpsiCuts", dest="JpsiCuts", help="ptCut,pmin,muID,fitMethod",    default="False")
parser.add_argument("-F", dest="fitMethod", help="which fitmethod, CB, B or G", default="B")
parser.add_argument("-S", dest="DYxsec",   type=float, help="scaling of DYxsec", default=2.0)

options = parser.parse_args()

MCType        =  options.MCType
with1GeV      =  options.with1GeV  == "True"
withCharm     =  options.withCharm == "True"
withCharm2    =  options.withCharm2 == "True"
with10GeV     =  options.with10GeV == "True"
withData      =  options.withData  == "True"
withJpsi      =  options.withJpsi  == "True"
withJpsiP8    =  options.withJpsiP8  == "True"
withDrellYan  =  options.withDrellYan  == "True"
if options.path != "": gPath = options.path+'/'
fdir = options.directory

Nfiles = 0
if not fdir:
    Nfiles = 2000
    fdir   = "/eos/experiment/ship/user/truf/muflux-reco/RUN_8000_2352"
elif withData and options.listOfFiles:
    sTreeData = ROOT.TChain('tmuflux')
    countFiles=[]
    for aRun in options.listOfFiles.split(','):
       temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls "+fdir+'/RUN_8000_'+aRun,shell=True)
       for x in temp.split('\n'):
            if x.find('ntuple-SPILL')<0: continue
            if x.find('refit')<0 and options.refit or x.find('refit')>0 and not options.refit: continue
            countFiles.append(os.environ["EOSSHIP"]+"/"+x)
    for x in countFiles:
        tmp = ROOT.TFile.Open(x)
        if not tmp.Get('tmuflux'):
           print "Problematic file:",x
           continue
        sTreeData.Add(x)
if not options.listOfFiles:
    sTreeData = ROOT.TChain('tmuflux')
    if withData:
     path = gPath + fdir
     countFiles=[]
     if fdir.find('eos')<0:
        for x in os.listdir(path):
            if x.find('ntuple-SPILL')<0: continue
            if x.find('refit')<0 and options.refit or x.find('refit')>0 and not options.refit: continue
            countFiles.append(path+'/'+x)
     else:
        temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls "+fdir,shell=True)
        for x in temp.split('\n'):
            if x.find('ntuple-SPILL')<0: continue
            if x.find('refit')<0 and options.refit or x.find('refit')>0 and not options.refit: continue
            countFiles.append(os.environ["EOSSHIP"]+"/"+x)
     for x in countFiles:
        tmp = ROOT.TFile.Open(x)
        if not tmp.Get('tmuflux'):
           print "Problematic file:",x
           continue
        sTreeData.Add(x)
        Nfiles-=1
        if Nfiles==0: break

    sTreeMC = ROOT.TChain('tmuflux')

    if with1GeV:
        path = os.environ["EOSSHIP"]+"/eos/experiment/ship/user/truf/muflux-sim/1GeV-"+MCType+"/pythia8_Geant4_1.0_cXXXX_mu/"
        for k in range(0,20000,1000):
            for m in range(5):
                fname = path.replace('XXXX',str(k))+"ntuple-ship.conical.MuonBack-TGeant4_dig_RT_mu-"+str(m)+".root"
                try:
                    test = ROOT.TFile.Open(fname)
                    if test.tmuflux.GetEntries()>0:   sTreeMC.Add(fname)
                except:
                    print "file not found",fname
                    continue
    if withCharm:
        fdir = fdir+'-charm'
        path = os.environ["EOSSHIP"]+"/eos/experiment/ship/user/truf/muflux-sim/1GeV-"+MCType+"/pythia8_Geant4_charm_0-19_1.0_mu/"
        for m in range(5):
            fname = path+"ntuple-ship.conical.MuonBack-TGeant4_dig_RT_mu-"+str(m)+".root"
            try:
                test = ROOT.TFile.Open(fname)
                if test.tmuflux.GetEntries()>0:   sTreeMC.Add(fname)
            except:
                print "file not found",fname
                continue

    if with10GeV:
        path = os.environ["EOSSHIP"]+"/eos/experiment/ship/user/truf/muflux-sim/10GeV-"+MCType+"/pythia8_Geant4_10.0_withCharmandBeautyXXXX_mu/"
        for k in range(0,67000,1000):
            for m in range(10):
                fname = path.replace('XXXX',str(k))+"ntuple-ship.conical.MuonBack-TGeant4_dig_RT_mu-"+str(m)+".root"
                try:
                    test = ROOT.TFile.Open(fname)
                    if test.tmuflux.GetEntries()>0:   sTreeMC.Add(fname)
                except:
                    print "file not found",fname
                    continue

    if withJpsi:
        path = os.environ["EOSSHIP"]+"/eos/experiment/ship/user/truf/muflux-sim/JpsiProduction/"
        for k in range(16):
            fname = "ntuple-pythia8_Geant4_"+str(k)+"_10.0_dig_RT_mu.root"
            sTreeMC.Add(path+fname)
    if withJpsiP8:
        path = os.environ["EOSSHIP"]+"/eos/experiment/ship/user/truf/muflux-sim/JpsiProduction_P8/"
        for k in range(16):
            fname = "ntuple-pythia8_Geant4_"+str(k)+"_10.0_dig_RT_mu.root"
            sTreeMC.Add(path+fname)
    if withDrellYan:
        path = os.environ["EOSSHIP"]+"/eos/experiment/ship/user/truf/muflux-sim/DrellYan/ship-ubuntu-1710-48_run_MufluxfixedTarget_XXX"
        for k in range(401,600):
            if k==500: continue
            fname = path.replace('XXX',str(k))+"/ntuple-pythia8_Geant4_"+str(k)+"_10.0_dig_RT.root"
            try:
                test = ROOT.TFile.Open(fname)
                if test.tmuflux.GetEntries()>0:   sTreeMC.Add(fname)
            except:
                print "file not found",fname
                continue
    if withCharm2:
        path ={0:os.environ["EOSSHIP"]+"/eos/experiment/ship/user/truf/muflux-sim/CharmProduction/runYYY/ship-ubuntu-1710-32_run_MufluxfixedTarget_XXX",
               1:os.environ["EOSSHIP"]+"/eos/experiment/ship/user/truf/muflux-sim/CharmProduction/runYYY/ship-ubuntu-1710-48_run_MufluxfixedTarget_XXX",
               2:os.environ["EOSSHIP"]+"/eos/experiment/ship/user/truf/muflux-sim/CharmProduction/runYYY/ship-ubuntu-1710-64_run_MufluxfixedTarget_XXX",
               3:os.environ["EOSSHIP"]+"/eos/experiment/ship/user/truf/muflux-sim/CharmProduction/runYYY/ship-ubuntu-1710-16_run_MufluxfixedTarget_XXX",
               4:os.environ["EOSSHIP"]+"/eos/experiment/ship/user/truf/muflux-sim/CharmProduction/runYYY/ship-ubuntu-1710-32_run_MufluxfixedTarget_XXX",
               5:os.environ["EOSSHIP"]+"/eos/experiment/ship/user/truf/muflux-sim/CharmProduction/runYYY/ship-ubuntu-1710-64_run_MufluxfixedTarget_XXX",
               6:os.environ["EOSSHIP"]+"/eos/experiment/ship/user/truf/muflux-sim/CharmProduction/runYYY/ship-ubuntu-1710-16_run_MufluxfixedTarget_XXX",
               7:os.environ["EOSSHIP"]+"/eos/experiment/ship/user/truf/muflux-sim/CharmProduction/runYYY/ship-ubuntu-1710-32_run_MufluxfixedTarget_XXX",
               8:os.environ["EOSSHIP"]+"/eos/experiment/ship/user/truf/muflux-sim/CharmProduction/runYYY/ship-ubuntu-1710-64_run_MufluxfixedTarget_XXX",
               9:os.environ["EOSSHIP"]+"/eos/experiment/ship/user/truf/muflux-sim/CharmProduction/runYYY/ship-ubuntu-1710-16_run_MufluxfixedTarget_XXX",
              10:os.environ["EOSSHIP"]+"/eos/experiment/ship/user/truf/muflux-sim/CharmProduction/runYYY/ship-ubuntu-1710-48_run_MufluxfixedTarget_XXX",
              11:os.environ["EOSSHIP"]+"/eos/experiment/ship/user/truf/muflux-sim/CharmProduction/runYYY/ship-ubuntu-1710-64_run_MufluxfixedTarget_XXX",
              12:os.environ["EOSSHIP"]+"/eos/experiment/ship/user/truf/muflux-sim/CharmProduction/runYYY/ship-ubuntu-1710-32_run_MufluxfixedTarget_XXX",
              13:os.environ["EOSSHIP"]+"/eos/experiment/ship/user/truf/muflux-sim/CharmProduction/runYYY/ship-ubuntu-1710-16_run_MufluxfixedTarget_XXX"}
        for cycle in path:
          for run in range(0,20):
             for k in range(10):
                xrun = run+cycle*1000 + k*100
                fname = path[cycle].replace('YYY',str(run)).replace('XXX',str(xrun))+"/ntuple-pythia8_Geant4_"+str(xrun)+"_10.0_dig_RT.root"
                try:
                   test = ROOT.TFile.Open(fname)
                   if test.tmuflux.GetEntries()>0:   sTreeMC.Add(fname)
                except:
                   print "file not found",fname
                   continue

# small problem here when merging 1GeV and 10GeV, due to different p cutoff, px and pt cannot be used directly. 

# temp hack
#nfile = "/media/truf/disk2/home/truf/ShipSoft/ship-ubuntu-1710-48/simulation1GeV-withDeadChannels/pythia8_Geant4_1.0_c3000_mu/ship.conical.MuonBack-TGeant4_dig_RT-0.root"
#sTreeMC.Add("ntuple-ship.conical.MuonBack-TGeant4_dig_RT-0.root")
    case = {'MC':[sTreeMC,hMC,ROOT.kRed,'hist same'],'Data':[sTreeData,hData,ROOT.kBlue,'hist']}

def printHistoEntries(histo,formating=None):
  for n in range(1,histo.GetNbinsX()+1):
     if formating == None: 
       print n,':',histo.GetBinCenter(n),histo.GetBinContent(n),histo.GetBinError(n)
     else:
       txt = "%i4 : %"+formating+"  %"+formating+"  %"+formating
       print txt%(n,histo.GetBinCenter(n),histo.GetBinContent(n),histo.GetBinError(n))
def getNxNy(C):
  first = True
  for p in C.GetListOfPrimitives():
    if first: 
       X,Y = p.GetXlowNDC(),p.GetYlowNDC()
       first = False
       nx,ny = 1,1
    else:
       if p.GetXlowNDC() > X: 
         nx+=1
         X = p.GetXlowNDC()
       if p.GetYlowNDC() < Y: 
         ny+=1
         Y = p.GetYlowNDC()
  return nx,ny
def readCanvasAndSplit(cfile):
   f = ROOT.TFile(cfile)
   for x in f.GetListOfKeys():
      if x.GetClassName()=='TCanvas':
         c = f.Get(x.GetName())
         printPads(c,ytitle=None,nr=False)

def printPads(c1,ytitle=None,nr=False):
   for n in range(len(c1.GetListOfPrimitives())):
       if nr:
           if nr!=n: continue
       c0 = ROOT.TCanvas("c0","c0",900,600)
       c0.Divide(1,1)
       pad = c1.GetListOfPrimitives()[n]
       newpad = c0.GetPad(1)
       tc  = c1.cd(n+1)
       B = []
       drawOption=''
       for p in pad.GetListOfPrimitives():
          name = p.GetName()
          if name in B: continue
          else: B.append(name)
          clone = p.Clone()
          opt = p.GetDrawOption()
          if p.ClassName().find('TH')==0: opt = drawOption
          newpad.GetListOfPrimitives().Add(clone,opt)
          if p.ClassName().find('TH')==0 and drawOption=='':drawOption='same'
       newpad.SetLogy(pad.GetLogy())
       newpad.SetLogx(pad.GetLogx())
       newpad.Modified()
       newpad.Update()
       if ytitle:
           for x in newpad.GetListOfPrimitives():
             if x.ClassName().find('TH1')<0: continue
             x.GetYaxis().SetTitle(ytitle)
       newpad.Update()
       c0.Print(c1.GetName()+'_'+str(n)+'.pdf')
       c0.Print(c1.GetName()+'_'+str(n)+'.png')

def rapidity(E,pz):
   return 0.5*ROOT.TMath.Log( (E+pz)/(E-pz) )
s_SQRT2i = 1./ROOT.TMath.Sqrt( 2.0 )
sqrt2pi  = ROOT.TMath.Sqrt( 2*ROOT.TMath.Pi() )

def TwoCrystalBall(x,par):
   bw = par[0] # should be fixed
   fGlobal['cb'].SetParameters(abs(par[1])*bw,par[2],abs(par[3]),par[4],par[5])
   highMass = fGlobal['cb'].Eval(x[0])
   if x[0]>par[7] and par[14]>0:
    fGlobal['cb'].SetParameters(abs(par[6])*bw,par[7],abs(par[8]),-par[14],par[15])
    lowMass = fGlobal['cb'].Eval(x[0])
   else:
    fGlobal['cb'].SetParameters(abs(par[6])*bw,par[7],abs(par[8]),par[9],par[10])
    lowMass = fGlobal['cb'].Eval(x[0])
   Psi2s = 0
   if abs(par[13])>0:
     fGlobal['cb'].SetParameters(par[13]*bw,3.6871+par[2]- 3.0969,par[3],abs(par[4]),par[5])
     Psi2s = fGlobal['cb'].Eval(x[0])
   elif par[13] < -999:
     # fix psi2s to NA50 Ag, 1.6% of 1S
     fGlobal['cb'].SetParameters(0.016*par[6]*bw,3.6871+par[2]- 3.0969,par[3],abs(par[4]),par[5])
   background = abs(par[11] + par[12]*x[0])
   #background = abs(par[11])*ROOT.TMath.Exp(par[12])*x[0]
   Ndy = 0
   if not hMC.has_key("GDYmctagk") and  par[17]!=0:
      print "missing Drell Yan model",par[17]
   elif hMC.has_key("GDYmctagk"):
      if hMC["GDYmctagk"]:
          Ndy = abs(par[17])*hMC["GDYmctagk"].Eval(x[0])
   if par[16] == 1: return highMass
   if par[16] == 2: return lowMass+Ndy
   if par[16] == 3: return background
   if par[16] == 4: return Psi2s
   Y = highMass + lowMass + Ndy + background + Psi2s
   return Y

def norm_myGauss(B,im='',sLow=2.0,sHigh=5.0,bLow=0.3,bHigh=3.0):
  N1   = B.GetParameter(1)
  N2   = B.GetParameter(7)
  pol0 = B.GetParameter(10)
  pol1 = B.GetParameter(11)
  bw   = B.GetParameter(0)
  dy   = B.GetParameter(14)
  signalNormalized      = B.GetParameter(7)
  err_signalNormalized  = B.GetParError(7)
  B.SetParameter(10,0.)
  B.SetParameter(11,0.)
  B.SetParameter(7,0.)
  B.SetParameter(14,0.)
  if im=='s': integral = simpleIntegral(B,bLow,bHigh)
  else:       integral = B.Integral(bLow,bHigh)
  lowMassNormalized = integral / bw
  B.SetParameter(7,N2)
  B.SetParameter(10,pol0)
  B.SetParameter(11,pol1)
  B.SetParameter(14,dy)
  err_lowMassNormalized = 0
  if N1>0: err_lowMassNormalized = lowMassNormalized/N1*B.GetParError(1)
  return [lowMassNormalized,err_lowMassNormalized],[signalNormalized,err_signalNormalized]

def gausAndBukinPdf(x,par):
# bukin for low mass and gaus for signal
  Nlow  = RooBukinPdf(x,par,0) # 6 parameters
  fGlobal['gausN'].SetParameter(0,par[7]*par[0])
  fGlobal['gausN'].SetParameter(1,par[8])
  fGlobal['gausN'].SetParameter(2,par[9]) # +3  parameters
  Nhigh = fGlobal['gausN'].Eval(x[0])
  Nback = abs(par[10]+par[11]*x[0])   # +2  parameters
  N2S = 0
  fGlobal['gausN'].SetParameter(1,par[8]+3.6871 - 3.0969)
  if par[12] > 0:
     fGlobal['gausN'].SetParameter(0,par[12]*par[0])
     N2S = abs(fGlobal['gausN'].Eval(x[0]))
  elif par[12] < -999:
     # fix psi2s to NA50 Ag, 1.6% of 1S
     fGlobal['gausN'].SetParameter(0,0.016*par[7]*par[0])
     N2S = abs(fGlobal['gausN'].Eval(x[0]))
  Ndy = 0 # not implemented
  if par[13]==1: return Nhigh
  if par[13]==2: return Nlow*par[0]
  if par[13]==3: return Nback*par[0]
  if par[13]==4: return N2S
  if par[13]==5: return Ndy
  return (Nlow+Nback)*par[0]+N2S+Nhigh+Ndy

def init_gausAndBukinPdf(B,bw):
  B.FixParameter(0,bw)
  B.SetParameter(1,3.0)
  B.SetParLimits(1,0.0,1E6)
  B.SetParameter(2,1.0)
  B.SetParameter(3,0.27)
  B.SetParameter(4,0.008)
  B.SetParameter(5,-0.06)
  B.SetParameter(6,+0.06)
  B.SetParameter(7,500.)
  B.SetParLimits(7,0.0,1E6)
  B.SetParameter(8,3.1)
  B.SetParameter(9,0.35)
  B.SetParameter(10,0.008)
  B.SetParameter(11,0.0)
  B.SetParameter(12,-1.0)
  B.FixParameter(13,0)
  B.FixParameter(14,0.)
  B.SetParName(1,'SignalLow')
  B.SetParName(2,'MeanLow')
  B.SetParName(3,'SigmaLow')
  B.SetParName(4,'pAsymLow')
  B.SetParName(5,'r1Low')
  B.SetParName(6,'r2Low')
  B.SetParName(7,'psi(1S)')
  B.SetParName(8,'Mass')
  B.SetParName(9,'Sigma')
  B.SetParName(10,'pol0')
  B.SetParName(11,'pol1')
  B.SetParName(12,'psi(2S)')

def GaussDoubleSidedExp(x,par,c):
   t = (x[0] - par[2+c])/par[3+c]
   if t<-par[4+c]:
     exp =  ROOT.TMath.Exp(par[4+c]*par[4+c]/2.+par[4+c]*t)
   elif t>par[5+c]:
     exp = ROOT.TMath.Exp(par[5+c]*par[5+c]/2.-par[5+c]*t)
   else:
     exp = ROOT.TMath.Exp(-0.5*t*t)
   return par[1+c]*exp
def twoGDEPdf(x,par):
  Nlow  = GaussDoubleSidedExp(x,par,0)
  Nhigh = GaussDoubleSidedExp(x,par,5)
  par2S = [par[0],par[14]]
  N2S = 0
  if par2S[1] > -999:
    for n in range(1,5):
      par2S.append(par[n+6])
    N2S = GaussDoubleSidedExp(x,par2S,0)
  Nback = abs(par[11]+par[12]*x[0])
  #Nback = abs(par[13])*ROOT.TMath.Exp(par[14])*x[0]
  if par[13]==1: return Nhigh*par[0]
  if par[13]==2: return Nlow*par[0]
  if par[13]==3: return Nback*par[0]
  if par[13]==4: return N2S*par[0]
  return (Nlow+Nhigh+Nback+N2S)*par[0]
def init_twoGDE(B,bw):
  B.FixParameter(0,bw)
  B.SetParameter(1,1E4)
  B.SetParLimits(1,0.0,1E6)
  B.SetParameter(2,1.0)
  B.SetParameter(3,0.27)
  B.SetParameter(4,1.0)
  B.SetParameter(5,1.0)
  B.SetParameter(6,1E4)
  B.SetParLimits(6,0.0,1E6)
  B.SetParameter(7,3.1)
  B.SetParameter(8,0.27)
  B.SetParameter(9,1.0)
  B.SetParameter(10,1.0)
  B.SetParameter(11,1.)
  B.FixParameter(12,0.)
  B.FixParameter(13,0.)
  B.FixParameter(14,-1000.)
  B.SetParName(6,'psi(1S)')
  B.SetParName(7,'Mass')
  B.SetParName(8,'Sigma')
  B.SetParName(9,'alphaLo')
  B.SetParName(10,'alphaHi')
  B.SetParName(11,'pol0')
  B.SetParName(12,'pol1')
  B.SetParName(13,'psi(2S)')
  B.SetParName(1,'SignalLow')
  B.SetParName(2,'MeanLow')
  B.SetParName(3,'SigmaLow')
  B.SetParName(4,'alphaLoLow')
  B.SetParName(5,'alphaHiLow')
def RooBukinPdf(x,par,c=0):
#Xp	The peak position.
#_sigp	The peak width as FWHM divided by 2*sqrt(2*log(2))=2.35
#_xi	Peak asymmetry. Use values around 0.
#_rho1	Left tail. Use slightly negative starting values.
#_rho2	Right tail. Use slightly positive starting values.
  bw = par[0] # should be fixed
  N     = par[1+c]
  _Xp   = par[2+c]
  _sigp = par[3+c]
  _xi   = par[4+c]
  _rho1 = -abs(par[5+c])
  _rho2 = abs(par[6+c])
  r1=0
  r2=0
  r3=0
  r4=0
  r5=0
  hp=0
  x1 = 0
  x2 = 0
  fit_result = 0.
  if abs(_sigp)>100: return 0.
  r3 = ROOT.TMath.Log(2.)
  consts = 2.*ROOT.TMath.Sqrt(2.*r3)
  hp = _sigp*consts
  r4 = ROOT.TMath.Sqrt(_xi*_xi+1)
  r1 = _xi/r4
  if ROOT.TMath.Abs(_xi) > ROOT.TMath.Exp(-6.):
    r5=_xi/ROOT.TMath.Log(r4+_xi)
  else:
    r5 = 1
  x1 = _Xp + (hp / 2.) * (r1-1)
  x2 = _Xp + (hp / 2.) * (r1+1)
  if (_Xp-x1)==0 or (r4-_xi)==0: return 0.
  if (_Xp-x2)==0 or (r4+_xi)==0: return 0.
  #--- Left Side
  if x[0] < x1:
    r2 = _rho1*ROOT.TMath.Power((x[0]-x1)/(_Xp-x1),2)-r3 + 4 * r3 * (x[0]-x1)/hp * r5 * r4/ROOT.TMath.Power((r4-_xi),2)
  #--- Center
  elif x[0] < x2:
    if ROOT.TMath.Abs(_xi) > ROOT.TMath.Exp(-6.): 
      r2=ROOT.TMath.Log(1 + 4 * _xi * r4 * (x[0]-_Xp)/hp)/ROOT.TMath.Log(1+2*_xi*(_xi-r4))
      r2=-r3*r2*r2
    else:
      r2=-4*r3*ROOT.TMath.Power(((x[0]-_Xp)/hp),2)
  #--- Right Side
  else:
    r2=_rho2*ROOT.TMath.Power((x[0]-x2)/(_Xp-x2),2)-r3 - 4 * r3 * (x[0]-x2)/hp * r5 * r4/ROOT.TMath.Power((r4+_xi),2)
  if ROOT.TMath.Abs(r2) > 100:
    fit_result = 0
  else:
    #---- Normalize the result
    fit_result = ROOT.TMath.Exp(r2)
  return N*fit_result
def my2BukinPdf(x,par):
  Nlow  = RooBukinPdf(x,par,0)
  Nhigh = RooBukinPdf(x,par,6)
  N2S = 0
  if par[16] > 0:
    par2S = [par[0],par[16],par[2] + 3.6871 - 3.0969]
    for n in range(2,6):
      par2S.append(par[n+7])
    N2S = RooBukinPdf(x,par2S,0)
  elif par[16]<-999: # take 1.6% of 1S  NA50 Ag
    par2S = [par[0],0.016*par[1],par[2] + 3.6871 - 3.0969]
    for n in range(2,6):
      par2S.append(par[n+7])
    N2S = RooBukinPdf(x,par2S,0)
  Nback = abs(par[13]+par[14]*x[0])
  # Nback = abs(par[13])*ROOT.TMath.Exp(par[14])*x[0]
  Ndy = 0
  if not hMC.has_key("GDYmctagk") and  par[17]!=0:
      print "missing Drell Yan model",par[17]
  elif hMC.has_key("GDYmctagk"):
      if hMC["GDYmctagk"]:
         parDY = [hMC["GDYmctagk"].GetParameters()[0],par[17]]
         for n in range(2,7):    parDY.append(par[n])
         Ndy = RooBukinPdf(x,parDY,0)
  N2S = abs(N2S)
  if par[15]==1: return Nhigh*par[0]
  if par[15]==2: return Nlow*par[0]
  if par[15]==3: return Nback*par[0]
  if par[15]==4: return N2S*par[0]
  if par[15]==5: return Ndy
  return (Nlow+Nhigh+Nback+N2S)*par[0]+Ndy
def init_twoBukin(B,bw):
  B.FixParameter(0,bw)
  B.SetParameter(1,3.000)
  B.SetParLimits(1,0.0,1E6)
  B.SetParameter(2,1.0)
  B.SetParameter(3,0.27)
  B.SetParameter(4,0.008)
  B.SetParameter(5,-0.06)
  B.SetParameter(6,+0.06)
  B.SetParameter(7,500.)
  B.SetParLimits(7,0.0,1E6)
  B.SetParameter(8,3.1)
  B.SetParameter(9,0.27)
  B.SetParameter(10,0.008)
  B.SetParameter(11,-0.6)
  B.SetParameter(12,-0.06)
  B.SetParameter(13,1.)
  B.FixParameter(14,0.)
  B.FixParameter(15,0.)
  B.FixParameter(16,-1000.)
  B.SetParName(1,'SignalLow')
  B.SetParName(2,'MeanLow')
  B.SetParName(3,'SigmaLow')
  B.SetParName(4,'pAsymLow')
  B.SetParName(5,'r1Low')
  B.SetParName(6,'r2Low')
  B.SetParName(7,'psi(1S)')
  B.SetParName(8,'Mass')
  B.SetParName(9,'Sigma')
  B.SetParName(10,'pAsym')
  B.SetParName(11,'r1')
  B.SetParName(12,'r2')
  B.SetParName(13,'pol0')
  B.SetParName(14,'pol1')
  B.SetParName(16,'psi(2S)')
  B.SetParName(17,'DY')
def simpleIntegral(B,x0,x1,N=10000):
  dx = (x1-x0)/float(N)
  x = x0
  integral = 0
  for n in range(N):
    integral+=B.Eval(x)
    x+=dx
  return integral*dx

def norm_twoBukin(B,im='',sLow=2.0,sHigh=5.0,bLow=0.3,bHigh=3.0):
  N1 = B.GetParameter(1)
  N2 = B.GetParameter(7)
  pol0 = B.GetParameter(13)
  pol1 = B.GetParameter(14)
  bw   = B.GetParameter(0)
  dy   = B.GetParameter(17)
  B.SetParameter(13,0.)
  B.SetParameter(14,0.)
  B.SetParameter(1,0.)
  B.SetParameter(17,0.)
  if im=='s': integral = simpleIntegral(B,sLow,sHigh)
  else:       integral = B.Integral(sLow,sHigh)
  signalNormalized = integral / bw
  B.SetParameter(1,N1)
  B.SetParameter(7,0)
  if im=='s': integral = simpleIntegral(B,bLow,bHigh)
  else:       integral = B.Integral(bLow,bHigh)
  lowMassNormalized = integral / bw
  B.SetParameter(1,N1)
  B.SetParameter(7,N2)
  B.SetParameter(13,pol0)
  B.SetParameter(14,pol1)
  B.SetParameter(17,dy)
  err_lowMassNormalized = 0
  if N1>0: err_lowMassNormalized = lowMassNormalized/N1*B.GetParError(1)
  err_signalNormalized  = 0
  if N2>0:  err_signalNormalized = signalNormalized/N2*B.GetParError(7)
  return [lowMassNormalized,err_lowMassNormalized],[signalNormalized,err_signalNormalized]
def norm_twoGDE(B,im='',sLow=2.0,sHigh=5.0,bLow=0.3,bHigh=3.0):
  N1 = B.GetParameter(1)
  N2 = B.GetParameter(6)
  pol0 = B.GetParameter(11)
  pol1 = B.GetParameter(12)
  bw   = B.GetParameter(0)
  B.SetParameter(11,0.)
  B.SetParameter(12,0.)
  B.SetParameter(1,0.)
  if im=='s': integral = simpleIntegral(B,sLow,sHigh)
  else:       integral = B.Integral(sLow,sHigh)
  signalNormalized = integral / bw
  B.SetParameter(1,N1)
  B.SetParameter(6,0)
  if im=='s': integral = simpleIntegral(B,bLow,bHigh)
  else:       integral = B.Integral(bLow,bHigh)
  lowMassNormalized = integral / bw
  B.SetParameter(1,N1)
  B.SetParameter(6,N2)
  B.SetParameter(11,pol0)
  B.SetParameter(12,pol1)
  err_lowMassNormalized = 0
  if N1>0: err_lowMassNormalized = lowMassNormalized/N1*B.GetParError(1)
  err_signalNormalized  = 0
  if N2>0:  err_signalNormalized = signalNormalized/N2*B.GetParError(6)
  return [lowMassNormalized,err_lowMassNormalized],[signalNormalized,err_signalNormalized]

def twoBukinYieldFit(proj,projMin,projMax,projName,theCut,nBins=9,printout=2):
   ROOT.gROOT.cd()
   hData['FitResults-'+proj]={}
   y_beam = yBeam()
   v='mcor'
   fitOption = 'SQL'
   if printout==2: fitOption='SL'
   if hMC.has_key('MCbinsB'+proj):
      hMC.pop('MCbinsB'+proj)
      hData.pop('binsB'+proj)
   for z in ['mc-B'+proj,'mcLowMass-B'+proj,'mcHighMass-B'+proj]:
       if hMC.has_key(z):
          hMC.pop(z).Delete()
       ut.bookHist(hMC, z, ' N J/#psi ;'+projName, nBins,projMin,projMax,InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
   if hData.has_key('B'+proj): hData.pop('B'+proj).Delete()
   ut.bookHist(hData,'B'+proj,    ' N J/#psi ;'+projName, nBins,projMin,projMax,InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
   hData['BJpsi'+proj]  = hData['B'+proj].ProjectionX('BJpsi'+proj)
   hMC['mc-BJpsi'+proj] = hMC['mc-B'+proj].ProjectionX('mc-BJpsi'+proj)
   N1 = int(ROOT.TMath.Sqrt(nBins))
   N2 = N1
   while(N2*N1<nBins): N2+=1
   ut.bookCanvas(hMC,'MCbinsB'+proj,'mass in bins '+projName,1800,1200,N1,N2)
   ut.bookCanvas(hData,'binsB'+proj,'mass in bins '+projName,1800,1200,N1,N2)
   hMC['dummy'].cd()
   if proj=='ycor': cutExp = "ycor-"+str(y_beam)
   elif proj=='ycor1C': cutExp = ycor1C+"-"+str(y_beam)
   else:            cutExp = proj
   myDraw(v+':'+cutExp+'>>mc-B'+proj,theCut,ntName)
   myDraw(v+':'+cutExp+'>>mcLowMass-B'+proj,theCut+"&&Jpsi!=443",ntName)
   myDraw(v+':'+cutExp+'>>mcHighMass-B'+proj,theCut+"&&Jpsi==443",ntName)
   sTreeData  = hData['f'].nt
   sTreeData.Draw(v+':'+cutExp+'>>B'+proj,theCut)
   pmin = projMin
   delp = (projMax-projMin)/float(nBins)
   for k in range(nBins):
      pmax = pmin+delp
      for z in ['mc-B'+proj,'mcLowMass-B'+proj,'mcHighMass-B'+proj]:
        hMC[z+str(k)]=hMC[z].ProjectionY(z+str(k),k+1,k+1)
        hMC[z+str(k)].SetTitle('inv mass MC '   +str(pmin)+'<'+proj+'<'+str(pmax)+';M [GeV/c^{2}]')
      hData['B'+proj+str(k)]=hData['B'+proj].ProjectionY('B'+proj+str(k),k+1,k+1)
      hData['B'+proj+str(k)].SetTitle('inv mass DATA ' +str(pmin)+'<'+proj+'<'+str(pmax)+';M [GeV/c^{2}]')
      pmin=pmax
      init_twoBukin(hData['B'+proj+str(k)].GetBinWidth(1))
      BF = hData['B']
      BF.FixParameter(7,0.)
      BF.FixParameter(8,3.1)
      BF.FixParameter(9,0.27)
      BF.FixParameter(10,0.008)
      BF.FixParameter(11,-0.6)
      BF.FixParameter(12,-0.06)
      BF.FixParameter(13,0.)
      if hMC['mc-B'+proj+str(k)].GetMaximum()>4:   # if entries too low, makes no sense to fit
         hMC['dummy'].cd()
         x='mcLowMass-B'+proj+str(k)
         BF.SetParameter(1,hMC[x].GetMaximum())
         if hMC[x].GetMaximum()>4:
            rc = hMC[x].Fit(BF,fitOption,'',0.5,2.5)
            hData['FitResults-'+x]=rc.Get().Clone(x)
         else:
            hData['FitResults-'+x]=None
         BF.FixParameter(1,0)
         if hData['FitResults-'+x]:
           for n in range(2,7):   BF.FixParameter(n,hData['FitResults-'+x].Parameter(n))
         else:
           for n in range(2,7):   BF.FixParameter(n,0)
         for n in range(7,13):  BF.ReleaseParameter(n)
         x='mcHighMass-B'+proj+str(k)
         BF.SetParameter(7,hMC[x].GetMaximum())
         if hMC[x].GetMaximum()>4:
            rc = hMC[x].Fit(BF,fitOption,'',2.0,5.)
            hData['FitResults-'+x]=rc.Get().Clone(x)
         else:
            hData['FitResults-'+x]=None
         if hData['FitResults-'+x]:
            for n in range(8,13):  BF.FixParameter(n,hData['FitResults-'+x].Parameter(n))
         else:
            for n in range(7,13):  BF.FixParameter(n,0)
         if hData['FitResults-mcLowMass-B'+proj+str(k)]: 
            BF.ReleaseParameter(1)
         cases = ['mc-B'+proj+str(k),'B'+proj+str(k)]
         for x in cases:
          if x.find('mc')==0: 
             h  = hMC
             tc = hMC['MCbinsB'+proj].cd(k+1)
          else: 
             h  = hData
             tc = hData['binsB'+proj].cd(k+1)
          h[x].GetXaxis().SetRange(h[x].FindBin(0.5),h[x].FindBin(1.5))
          BF.SetParameter(1,h[x].GetMaximum())
          h[x].GetXaxis().SetRange(h[x].FindBin(2.6),h[x].FindBin(3.6))
          BF.SetParameter(7,h[x].GetMaximum())
          h[x].GetXaxis().SetRange(1,InvMassPlots[0])
          rc = h[x].Fit(BF,fitOption,'',0.5,5.)
          if hData['FitResults-mcLowMass-B'+proj+str(k)]:
             BF.ReleaseParameter(2)
             BF.ReleaseParameter(3)
          else:
            if x.find('mc')<0: continue
          if hData['FitResults-mcHighMass-B'+proj+str(k)]:
             N = hData['FitResults-mcHighMass-B'+proj+str(k)].Parameter(7)/5.
             BF.SetParameter(7,N)
             BF.ReleaseParameter(8)
             BF.ReleaseParameter(9)
          rc = h[x].Fit(BF,fitOption,'',0.5,5.)
          if rc.Get().Parameter(8)<3. and hData['FitResults-mcHighMass-B'+proj+str(k)]:
             BF.FixParameter(8,hData['FitResults-mcHighMass-B'+proj+str(k)].Parameter(8))
             BF.FixParameter(9,hData['FitResults-mcHighMass-B'+proj+str(k)].Parameter(9))
             rc = h[x].Fit(BF,fitOption,'',0.5,5.)
          if hData['FitResults-mcLowMass-B'+proj+str(k)]:
             BF.ReleaseParameter(4)
             BF.ReleaseParameter(5)
             BF.ReleaseParameter(6)
             rc = h[x].Fit(BF,fitOption,'',0.5,5.)
          if hData['FitResults-mcHighMass-B'+proj+str(k)]:
             BF.ReleaseParameter(10)
             BF.ReleaseParameter(11)
             BF.ReleaseParameter(12)
             rc = h[x].Fit(BF,fitOption,'',0.5,5.)
          hData['FitResults-'+x]=rc.Get().Clone(x)
          tmp = norm_twoBukin(BF) # lowMass Jpsi
          N = tmp[1][0]
          E = tmp[1][1]
          if abs(N) > 1E6 :  # unphysical result
             N = 0
             E = 0
          if x.find('mc')==0:
             hMC['mc-BJpsi'+proj].SetBinContent(k+1,N)
             hMC['mc-BJpsi'+proj].SetBinError(k+1,E)
          else: 
             hData['BJpsi'+proj].SetBinContent(k+1,N)
             hData['BJpsi'+proj].SetBinError(k+1,E)
          if tmp[0][0]/(tmp[1][0]+1E-10) > 10.: tc.SetLogy(1)
          else: tc.SetLogy(0)
          tc.Update()
          stats = tc.GetPrimitive('stats')
          stats.SetOptFit(10111)
          stats.SetFitFormat('5.4g')
          stats.SetX1NDC(0.68)
          stats.SetY1NDC(0.01)
          stats.SetX2NDC(0.99)
          stats.SetY2NDC(0.84)
          tc.Update()
      else:
          N=0
          E=0
          hMC['mc-BJpsi'+proj].SetBinContent(k+1,N)
          hMC['mc-BJpsi'+proj].SetBinError(k+1,E)
          hData['BJpsi'+proj].SetBinContent(k+1,N)
          hData['BJpsi'+proj].SetBinError(k+1,E)
   if printout>0:
     myPrint(hData['binsB'+proj],'diMuonBinsB'+proj)
     myPrint(hMC['MCbinsB'+proj],'MC-diMuonBinsB'+proj+ntName)
     hMC['dummy'].cd()
     hMC['mc-BJpsi'+proj].SetLineColor(ROOT.kMagenta)
     hmax = 1.1*max(hMC['mc-BJpsi'+proj].GetMaximum(),hData['BJpsi'+proj].GetMaximum())
     hMC['mc-BJpsi'+proj].SetMaximum(hmax)
     hMC['mc-BJpsi'+proj].Draw()
     hData['BJpsi'+proj].Draw('same')
     myPrint(hMC['dummy'],'diMuonBinsB'+proj+ntName+'Summary')
def myFit(histo,fun,fitOption,xmin,xmax):
   rc = histo.Fit(fun,fitOption,'',xmin,xmax)
   fitResult = rc.Get()
   return fitResult.Status() and fitResult.IsValid(),fitResult.Chi2()/fitResult.Ndf(),fitResult.Clone(histo.GetName())
def getFitDictionary(fitMethod):
   if fitMethod=='CB':
   # high mass [1,2,3,4,5]  low mass [6,7,8,9,10]
     params = {'signal':1,   'highMass':2,'highSigma':3,'highTails':{4:1.,5:10.},
               'signalLow':6,'lowMass':7, 'lowSigma':8, 'lowTails':{9:1.,10:10.},
               'pol':[11,12],'highTailsOff':{4:1000.,5:10.},'highTailsLimits':{4:[0.,10.],5:[0.,100.]},
                           'lowTailsOff':{9:1000.,10:10.},'lowTailsLimits':{9:[-1.5,-0.5],10:[1.,50.]},  # alphaLow 9 with -0.5, -1.5, nLow 10  3. - 50.
               'switch':16,'psi(2s)':13,'DY':17,'fixParams':{}}
     funTemplate = {'F':TwoCrystalBall,'N':18,'Init':init_twoCB0}
   if fitMethod=='B':
   # high mass [7,8,9,10,11,12]  low mass [1,2,3,4,5,6]
     params = {'signal':7,   'highMass':8,'highSigma':9,'highTails':{10:0.008,11:-0.01,12:0.01},
               'signalLow':1,'lowMass':2, 'lowSigma':3, 'lowTails':{4:0.008,   5:-0.01, 6:0.01},
               'pol':[13,14],'highTailsOff':{10:0.008,11:-0.01},'highTailsLimits':{},
                              'lowTailsOff':{4:0.008,5:-0.01,6:0.01},  'lowTailsLimits':{4:[0.,0.2],5:[-1.,0.],6:[0.,50.]},
               'switch':15,'psi(2s)':16, 'DY':17, 'fixParams':{12:0.0,15:0.0}}
     funTemplate = {'F':my2BukinPdf,'N':18,'Init':init_twoBukin}
   if fitMethod=='GE':
   # high mass [6,7,8,9,10]  low mass [1,2,3,4,5]
     params = {'signal':6,   'highMass':7,'highSigma':8,'highTails':{9:1.0,10:1.0},
               'signalLow':1,'lowMass':2, 'lowSigma':3, 'lowTails':{4:1.0,   5:1.0},
               'pol':[11,12],'highTailsOff':{},'highTailsLimits':{},
                              'lowTailsOff':{},  'lowTailsLimits':{},
               'fixParams':{11:0.0}}
     funTemplate = {'F':twoGDEPdf,'N':15,'Init':init_twoGDE}
   if fitMethod=='G':
   # logic for psi2s, par[11] > 0: free N, par[11] < -999: fixed to 1.6% of Jpsi else 0
   # high mass [6,7,8]  low mass [1,2,3,4,5]
     params = {'signal':7,   'highMass':8,'highSigma':9,'highTails':{},
               'signalLow':1,'lowMass':2, 'lowSigma':3, 'lowTails':{4:0.008,   5:-0.01, 6:0.01},
               'pol':[10,11],'highTailsOff':{},'highTailsLimits':{},
               'lowTailsOff':{4:0.008,5:-0.01,6:0.01},  'lowTailsLimits':{4:[0.,0.2],5:[-1.,0.],6:[0.,50.]},
               'switch':13,'DY':14,'psi(2s)':12,'fixParams':{12:-1000,14:0}}
     funTemplate = {'F':gausAndBukinPdf,'N':15,'Init':init_gausAndBukinPdf}
   return params,funTemplate


def twoCBYieldFit(fitMethod,proj,projMin,projMax,projName,theCut,withFreeTails=False,nBins=9,withWeight=False,printout=2,v='mcor',withDY=False,DYxsec=2.,withPsi2s=False):
   ROOT.gROOT.cd()
   tag = (fitMethod+"_"+proj).replace(',','').replace(')','').replace('(','')
   hData['FitResults-'+tag]={}
   y_beam = yBeam()
   fitOption = 'SQL'
   if printout==2: fitOption='SL'
   minX = 0.5
   maxX = 8.0
   highMassLowLimit = 2.5
   highMassSigmaLimit = 0.8
   if v!='mcor': 
      highMassLowLimit = 2.0
      highMassSigmaLimit = 1.2
   mcNtuples = ['Jpsi','JpsiP8','10GeV']
# canvases
   if hData.has_key('bins'+tag):
      for m in mcNtuples:
         for z in ['','LowMass-','HighMass-']:
            hMC.pop('MCbins'+z+tag+m)
      hData.pop('bins'+tag)
   N1 = int(ROOT.TMath.Sqrt(nBins))
   N2 = N1
   while(N2*N1<nBins): N2+=1
   for m in mcNtuples:
      for z in ['','LowMass-','HighMass-']:
         ut.bookCanvas(hMC,'MCbins'+z+tag+m,'mass in bins '+projName,1800,1200,N1,N2)
   ut.bookCanvas(hData,'bins'+tag,'mass in bins '+projName,1800,1200,N1,N2)
# histos
   if hData.has_key(tag): hData.pop(tag).Delete()
   ut.bookHist(hData,tag,       ' N J/#psi ;'+projName, nBins,projMin,projMax,InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
   for m in mcNtuples:
      for z in ['','LowMass-','HighMass-']:
         mctag = 'mc-'+tag+z+m
         if hMC.has_key(mctag):  hMC.pop(mctag).Delete()
         ut.bookHist(hMC, mctag, ' N J/#psi ;'+projName, nBins,projMin,projMax,InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
# for the final results
   hData[tag+'-Jpsi']  = hData[tag].ProjectionX(tag+'-Jpsi')
   for m in mcNtuples:
      for z in ['','LowMass-','HighMass-']:
         mctag = 'mc-'+tag+z+m
         hMC[mctag+'-Jpsi'] = hMC[mctag].ProjectionX(mctag+'-Jpsi')
#
   hMC['dummy'].cd()
   if proj=='ycor':     cutExp = "ycor-"+str(y_beam)
   elif proj=='ycor1C': cutExp = ycor1C+"-"+str(y_beam)
   else:                cutExp = proj
   for m in mcNtuples: 
     if withWeight and m=='Jpsi':
      if not hMC.has_key('fp6w'): weight4Pythia6()
      w = "("+str(hMC['fp6w'].GetParameter(0))
      for n in range(1,10):
         p = hMC['fp6w'].GetParameter(n)
         if p<0: w+=str(p)+'*PtTRUE**'+str(n)
         else:   w+="+"+str(p)+'*PtTRUE**'+str(n)
      w+=")"
      myDraw(v+':'+cutExp+'>>mc-'+tag+'HighMass-'+m,w+'*('+theCut+"&&Jpsi==443"+')',m)
     elif withWeight and m=='JpsiP8':
      if not hMC.has_key('fp8w'): weight4Pythia6()
      w = "("+str(hMC['fp8w'].GetParameter(0))
      for n in range(1,10):
         p = hMC['fp8w'].GetParameter(n)
         if p<0: w+=str(p)+'*(ycor-'+str(y_beam)+')**'+str(n)
         else:   w+="+"+str(p)+'*(ycor-'+str(y_beam)+')**'+str(n)
      w+=")"
      myDraw(v+':'+cutExp+'>>mc-'+tag+'HighMass-'+m,w+'*('+theCut+"&&Jpsi==443"+')',m)
     else:
      if m=='10GeV':  
        myDraw(v+':'+cutExp+'>>mc-'+tag+m,theCut,m,DYxsec)
        myDraw(v+':'+cutExp+'>>mc-'+tag+'LowMass-'+m, theCut+"&&Jpsi%100000!=443",m,DYxsec)
      myDraw(v+':'+cutExp+'>>mc-'+tag+'HighMass-'+m,theCut+"&&Jpsi==443",m)
   rc = hData['f'].nt.Draw(v+':'+cutExp+'>>'+tag,theCut)
#
   pmin = projMin
   delp = (projMax-projMin)/float(nBins)
# make slices
   for k in range(nBins+1):
      if k==nBins:
        pmin = projMin
        pmax = projMax
        hData[tag+str(k)] = hData[tag].ProjectionY(tag+str(k))
      else:
        pmax = pmin+delp
        hData[tag+str(k)] = hData[tag].ProjectionY(tag+str(k),k+1,k+1)
      hData[tag+str(k)].SetTitle('inv mass DATA ' +str(pmin)+'<'+proj+'<'+str(pmax)+';M [GeV/c^{2}]')
      for m in mcNtuples:
         for z in ['','LowMass-','HighMass-']:
             mctag = 'mc-'+tag+z+m
             mctagk = mctag+str(k)
             if k==nBins:  hMC[mctagk]=hMC[mctag].ProjectionY(mctagk)
             else:         hMC[mctagk]=hMC[mctag].ProjectionY(mctagk,k+1,k+1)
             hMC[mctagk].SetTitle('inv mass MC '   +str(pmin)+'<'+proj+'<'+str(pmax)+';M [GeV/c^{2}]')
             if m == "10GeV":
                if k==nBins:  hMC["DY"+mctagk]=hMC["DY"+mctag].ProjectionY("DY"+mctagk) # with full statistics
                else:         hMC["DY"+mctagk]=hMC["DY"+mctag].ProjectionY("DY"+mctagk,k+1,k+1) # with full statistics
                hMC["GDYmctagk"]=None
                histo = hMC["DY"+mctagk]
                bw = histo.GetBinWidth(1)
                params,funTemplate = getFitDictionary('B')   # always use bukin with two tails
                F = ROOT.TF1('DY',funTemplate['F'],0,10,funTemplate['N'])
                funTemplate['Init'](F,bw)
                for l in params['fixParams']: F.FixParameter(l,params['fixParams'][l])
                F.SetParameter(params['signalLow'],histo.GetEntries())
                F.FixParameter(params['signal'],0.)
                F.FixParameter(params['highMass'],3.1)
                F.FixParameter(params['highSigma'],0.3)
                for l in params['highTails']: F.FixParameter(l,params['highTails'][l])
                for l in params['pol']:       F.FixParameter(l,0.)
                F.FixParameter(params['DY'],0.)
                rc = myFit(histo,F,'SQL',0.5,6.)
      pmin=pmax
   bw = hData[tag+str(0)].GetBinWidth(1)
   params,funTemplate = getFitDictionary(fitMethod)
# start with fitting MC high mass
   for m in mcNtuples:
      z = 'HighMass-'
      Jpsi = 'mc-'+tag+z+m+'-Jpsi'
      for k in range(nBins+1):
         tc = hMC['MCbins'+z+tag+m].cd(k+1)
         mctag = 'mc-'+tag+z+m+str(k)
         fname = 'mc-Fun'+tag+z+m+str(k)
         hMC[fname] = ROOT.TF1(fname,funTemplate['F'],0,10,funTemplate['N'])
         CB = hMC[fname]
         funTemplate['Init'](CB,bw)
         for l in params['fixParams']: CB.FixParameter(l,params['fixParams'][l])
         CB.SetParameter(params['signal'],hMC[mctag].GetEntries())
   # fix low mass to 0
         CB.FixParameter(params['signalLow'],0.)
         CB.FixParameter(params['lowMass'],1.1)
         CB.FixParameter(params['lowSigma'],0.3)
         for l in params['lowTails']: CB.FixParameter(l,params['lowTails'][l])
         for l in params['pol']:      CB.FixParameter(l,0.)
   # no Drell Yan
         CB.FixParameter(params['DY'],0.)
         hMC["GDYmctagk"]=None
   # start with alpha large, no power law
         for l in params['highTailsOff']: CB.FixParameter(l,params['highTailsOff'][l])
         rc = myFit(hMC[mctag],CB,fitOption,1.,maxX)
         if rc[0]!=0:
           print mctag
           break
         for l in params['highTails']: 
             CB.ReleaseParameter(l)
             CB.SetParameter(l,params['highTails'][l])
         for l in params['highTailsLimits']: 
             CB.SetParLimits(l,params['highTailsLimits'][l][0],params['highTailsLimits'][l][1])
         rc = myFit(hMC[mctag],CB,fitOption,1.,maxX)
         CB.SetParLimits(params['signalLow'],0.,1E9)
         CB.SetParLimits(params['signal'],0.,1E9)
         if rc[0]!=0:
           print mctag
           break
         hMC['FitResults-'+mctag] = rc[2]
         hMC[mctag].Draw()
         tc.Update()
         stats = tc.GetPrimitive('stats')
         if not stats: 
           print "something wrong", mctag
           continue
         stats.SetOptFit(10111)
         stats.SetFitFormat('5.4g')
         stats.SetX1NDC(0.68)
         stats.SetY1NDC(0.15)
         stats.SetX2NDC(0.99)
         stats.SetY2NDC(0.98)
         tc.Update()
         if fitMethod=='CB': tmp = norm_twoCB(hMC['FitResults-'+mctag])
         if fitMethod=='B':  tmp = norm_twoBukin(CB)
         if fitMethod=='G':  tmp = norm_myGauss(CB)
         if fitMethod=='GE':  tmp = norm_twoGDE(CB)
         N = tmp[1][0]
         E = tmp[1][1]
         if N > 1E6:  # unphysical result
             N = 0
             E = 0
         hMC[Jpsi].SetBinContent(k+1,N)
         hMC[Jpsi].SetBinError(k+1,E)
      if printout>0: myPrint(hMC['MCbins'+z+tag+m],'MCbins'+z+tag+m)
# next fitting MC low mass, only possible for 10GeV
   m = "10GeV"
   z = 'LowMass-'
   for k in range(nBins+1):
         tc = hMC['MCbins'+z+tag+m].cd(k+1)
         mctag = 'mc-'+tag+z+m+str(k)
         fname = 'mc-Fun'+tag+z+m+str(k)
         hMC[fname] = ROOT.TF1(fname,funTemplate['F'],0,10,funTemplate['N'])
         CB = hMC[fname]
         funTemplate['Init'](CB,bw)
         for l in params['fixParams']: CB.FixParameter(l,params['fixParams'][l])
   # high mass [1,2,3,4,5]  low mass [6,7,8,9,10]
         CB.SetParameter(params['signalLow'],hMC[mctag].GetEntries())
   # fix high mass to 0
         CB.FixParameter(params['signal'],0.)
         CB.FixParameter(params['highMass'],3.1)
         CB.FixParameter(params['highSigma'],0.3)
         for l in params['highTails']: CB.FixParameter(l,params['highTails'][l])
         for l in params['pol']:       CB.FixParameter(l,0.)
         if withDY:
            CB.ReleaseParameter(params['DY'])
            CB.SetParameter(params['DY'],0.5)
            hMC["GDYmctagk"]=hMC["DY"+mctag].GetFunction('DY')
         else:
   # no Drell Yan
            CB.FixParameter(params['DY'],0.)
            hMC["GDYmctagk"]=None
         for l in params['lowTailsOff']: CB.FixParameter(l,params['lowTailsOff'][l])
         rc = myFit(hMC[mctag],CB,fitOption,minX,maxX)
         if rc[0]!=0:
           print mctag
           break
         for l in params['lowTails']: 
             CB.ReleaseParameter(l)
             CB.SetParameter(l,params['lowTails'][l])
         for l in params['lowTailsLimits']: 
             CB.SetParLimits(l,params['lowTailsLimits'][l][0],params['lowTailsLimits'][l][1])
         for l in params['pol']:       CB.ReleaseParameter(l)
         rc = myFit(hMC[mctag],CB,fitOption,minX,maxX)
         rc = myFit(hMC[mctag],CB,fitOption,minX,maxX)
         if rc[0]!=0:
           print mctag
           break
         hMC['FitResults-'+mctag] = rc[2]
         hMC[mctag].Draw()
         tc.Update()
         stats = tc.GetPrimitive('stats')
         if not stats: 
           print "something wrong", mctag
           continue
         stats.SetOptFit(10111)
         stats.SetFitFormat('5.4g')
         stats.SetX1NDC(0.68)
         stats.SetY1NDC(0.15)
         stats.SetX2NDC(0.99)
         stats.SetY2NDC(0.98)
         tc.Update()
         if fitMethod=='CB': tmp = norm_twoCB(hMC['FitResults-'+mctag])
         if fitMethod=='B':  tmp = norm_twoBukin(CB)
         if fitMethod=='G':  tmp = norm_myGauss(CB)
         if fitMethod=='GE':  tmp = norm_twoGDE(CB)
         N = tmp[1][0]
         E = tmp[1][1]
         if N > 1E6:  # unphysical result
             N = 0
             E = 0
         hMC[Jpsi].SetBinContent(k+1,N)
         hMC[Jpsi].SetBinError(k+1,E)
   if printout>0: myPrint(hMC['MCbins'+z+tag+m],'MCbins'+z+tag+m)
# now we fit simultaneously low and high mass for MC 10GeV and Data
   m = '10GeV'
   z = ''
   case = {}
   case[m]={}
   case[m]['Canvas'] = hMC['MCbins'+z+tag+m]
   case[m]['htag']   =  'mc-'+tag+z+m
   case[m]['store']  =  hMC
   case[m]['fun']    = 'mc-Fun'+tag+z+m
   case[m]['Jpsi']   = 'mc-'+tag+z+m+'-Jpsi'
#
   m = 'Data'
   case[m]={}
   case[m]['Canvas'] = hData['bins'+z+tag]
   case[m]['htag']   =  tag
   case[m]['store']  =  hData
   case[m]['fun']    = 'Fun'+tag+z
   case[m]['Jpsi']   =  tag+z+'-Jpsi'
   for c in case: 
      for k in range(nBins+1):
         tc = case[c]['Canvas'].cd(k+1)
         hk = case[c]['htag']+str(k)
         h  = case[c]['store']
         fk = case[c]['fun']+str(k)
         Jpsi = case[c]['Jpsi']
         h[fk] = ROOT.TF1(fk,funTemplate['F'],0,10,funTemplate['N'])
         CB = h[fk]
         funTemplate['Init'](CB,bw)
         for l in params['fixParams']: CB.FixParameter(l,params['fixParams'][l])
   # get parameters from "Jpsi (Cascade)"
         Nguess = h[hk].Integral(h[hk].FindBin(2.6),h[hk].FindBin(3.5))
         highMass = hMC['FitResults-'+'mc-'+tag+'HighMass-Jpsi'+str(k)]
         CB.SetParameter(params['signal'],Nguess)
         L = params['highTails'].keys()+[params['highMass'],params['highSigma']]
         for n in L: CB.FixParameter(n,highMass.Parameter(n))
         Nguess = h[hk].Integral(h[hk].FindBin(0.5),h[hk].FindBin(2.0))
         lowMass = hMC['FitResults-'+'mc-'+tag+'LowMass-10GeV'+str(k)]
# find xlow
         xlow = minX
         for o in range(h[hk].FindBin(minX),2,-1):
            if h[hk].GetBinContent(o-1)<h[hk].GetBinContent(o): xlow = h[hk].GetBinCenter(o)
            else: break
         L = params['lowTails'].keys()+[params['lowMass'],params['lowSigma']]
         for n in L: CB.FixParameter(n,lowMass.Parameter(n))
         CB.FixParameter(params['pol'][1],0)
   # no Drell Yan
         hMC["GDYmctagk"]=None
         CB.FixParameter(params['DY'],0)
         CB.FixParameter(params['signalLow'],0)
# fit first signal part
         rc = myFit(h[hk],CB,fitOption,2.9,maxX)
         L = [params['signal'],params['highMass'],params['highSigma']]
         if rc[2].Parameter(params['signal'])>25:
            for n in L: CB.ReleaseParameter(n)
            CB.SetParLimits(params['signal'],0.,1E6)
         else: 
            print "too small signal",hk,rc[2].Parameter(params['signal'])
         rc = myFit(h[hk],CB,fitOption,2.9,maxX)
# safety checks
         safetyNet = False
         if rc[2].Parameter(params['highSigma'])<0.1 or rc[2].Parameter(params['highSigma'])>0.8:
             print "sigma out of norm",hk,rc[2].Parameter(params['highSigma'])
             for n in [params['highMass'],params['highSigma']]: CB.FixParameter(n,highMass.Parameter(n))
             rc = myFit(h[hk],CB,fitOption,2.9,maxX)
             safetyNet = True
         for n in L: CB.FixParameter(n,rc[2].Parameter(n))
# then low mass with signal fixed
         CB.ReleaseParameter(params['signalLow'])
         CB.SetParLimits(params['signalLow'],0.,1E6)
         CB.SetParameter(params['signalLow'],Nguess)
         if withDY:
            CB.ReleaseParameter(params['DY'])
            CB.SetParameter(params['DY'],0.5)
            hMC["GDYmctagk"] = hMC["DYmc-"+tag+z+'10GeV'+str(k)].GetFunction('DY')
         else:
   # no Drell Yan
            CB.FixParameter(params['DY'],0.)
            hMC["GDYmctagk"]=None
         rc = myFit(h[hk],CB,fitOption,xlow,2.0)
         if rc[2].Parameter(params['signalLow'])>25:
            CB.ReleaseParameter(params['lowMass'])
            CB.ReleaseParameter(params['lowSigma'])
            CB.FixParameter(params['pol'][1],0)
            rc = myFit(h[hk],CB,fitOption,xlow,maxX)
            if withFreeTails:
              for l in params['lowTails']: 
                 CB.ReleaseParameter(l)
              for l in params['lowTailsLimits']: 
                 CB.SetParLimits(l,params['lowTailsLimits'][l][0],params['lowTailsLimits'][l][1])
              rcTest = myFit(h[hk],CB,fitOption,xlow,maxX)
              if rcTest[2].Prob()>rc[2].Prob():
                 rc = rcTest
              else:
                 L = params['lowTails'].keys()+[params['lowMass'],params['lowSigma']]
                 L += params['highTails'].keys()+[params['highMass'],params['highSigma']]
                 for n in L:  CB.SetParameter(n,rc[2].Parameter(n))
                 for n in params['lowTails']:  CB.FixParameter(n,rc[2].Parameter(n))
         for n in params['pol']:CB.ReleaseParameter(n)
         rc = myFit(h[hk],CB,fitOption,xlow,maxX)
         if safetyNet: L = [params['signal']]
         else:         L = [params['signal'],params['highMass'],params['highSigma']]
         for n in L:  CB.ReleaseParameter(n)
         rc = myFit(h[hk],CB,fitOption,xlow,maxX)
         if rc[2].Parameter(params['highMass'])<highMassLowLimit or rc[2].Parameter(params['highSigma'])>highMassSigmaLimit or safetyNet:
           print "sigma or mass out of norm",hk,rc[2].Parameter(params['highSigma']),rc[2].Parameter(params['highMass'])
           L = params['highTails'].keys()+[params['highMass'],params['highSigma']]
           for n in L: CB.FixParameter(n,highMass.Parameter(n))
           rc = myFit(h[hk],CB,fitOption,xlow,maxX)
         elif withFreeTails:
           for l in params['highTails']: 
             CB.ReleaseParameter(l)
           for l in params['highTailsLimits']: 
             CB.SetParLimits(l,params['highTailsLimits'][l][0],params['highTailsLimits'][l][1])
           rcTest = myFit(h[hk],CB,fitOption,xlow,maxX)
           if rcTest[2].Prob()>rc[2].Prob():
             rc = rcTest
           else: 
             for n in range(CB.GetNpar()):
                 CB.SetParameter(n,rc[2].Parameter(n))
         h['FitResults-'+hk] = rc[2]
         h[fk+'highMass'] = ROOT.TF1(fk+'highMass',funTemplate['F'],xlow,maxX,funTemplate['N'])
         for n in range(funTemplate['N']): h[fk+'highMass'].FixParameter(n,CB.GetParameter(n))
         h[fk+'highMass'].FixParameter(params['switch'],1)
         h[fk+'highMass'].SetLineColor(ROOT.kMagenta)
         h[fk+'highMass'].Draw('same')
         h[fk+'lowMass'] = ROOT.TF1(fk+'lowMass',funTemplate['F'],xlow,maxX,funTemplate['N'])
         for n in range(funTemplate['N']): h[fk+'lowMass'].FixParameter(n,CB.GetParameter(n))
         h[fk+'lowMass'].FixParameter(params['switch'],2)
         h[fk+'lowMass'].SetLineColor(ROOT.kCyan)
         h[fk+'lowMass'].Draw('same')
         h[fk+'back'] = ROOT.TF1(fk+'back',funTemplate['F'],xlow,maxX,funTemplate['N'])
         for n in range(funTemplate['N']): h[fk+'back'].FixParameter(n,CB.GetParameter(n))
         h[fk+'back'].FixParameter(params['switch'],3)
         h[fk+'back'].SetLineColor(ROOT.kGray)
         h[fk+'back'].Draw('same')
         if not fitMethod=='G' and withDY:
             DYparams,DYfunTemplate = getFitDictionary('B')   # always use bukin with two tails
             h[fk+'DY'] = ROOT.TF1('DY',funTemplate['F'],0,10,DYfunTemplate['N'])
             DYfunTemplate['Init'](h[fk+'DY'],bw)
             for n in range(DYfunTemplate['N']): h[fk+'DY'].FixParameter(n,CB.GetParameter(n))
             h[fk+'DY'].FixParameter(params['switch'],5)
             h[fk+'DY'].SetLineColor(ROOT.kOrange)
             h[fk+'DY'].Draw('same')
         h[hk].Draw('same')
         if fitMethod=='CB': tmp = norm_twoCB(h['FitResults-'+hk])
         if fitMethod=='GE': tmp = norm_twoGDE(CB)
         if fitMethod=='B':  tmp = norm_twoBukin(CB)
         if fitMethod=='G':  tmp = norm_myGauss(CB)
         N = tmp[1][0]
         E = tmp[1][1]
         if N > 1E6:  # unphysical result
             N = 0
             E = 0
         h[Jpsi].SetBinContent(k+1,N)
         h[Jpsi].SetBinError(k+1,E)
         if tmp[1][0]<500*tmp[0][0]: tc.SetLogy(1)
         else: tc.SetLogy(0)
         tc.Update()
         stats = tc.GetPrimitive('stats')
         stats.SetOptFit(10111)
         stats.SetFitFormat('5.4g')
         stats.SetX1NDC(0.68)
         stats.SetY1NDC(0.15)
         stats.SetX2NDC(0.99)
         stats.SetY2NDC(0.98)
         tc.Update()
      if printout>0: myPrint(case[c]['Canvas'],c+'-diMuonBins_'+tag)
   hMC['dummy'].cd()
   mc = hMC[case['10GeV']['Jpsi']]
   da = hData[case['Data']['Jpsi']]
   mc.SetLineColor(ROOT.kMagenta)
   hmax = 1.1*max(mc.GetMaximum(),da.GetMaximum())
   mc.SetMaximum(hmax)
   mc.Draw()
   da.Draw('same')
   for m in mcNtuples:
     z = 'HighMass-'
     Jpsi = 'mc-'+tag+z+m+'-Jpsi'
     hMC[Jpsi].Draw('same')
   if printout>0: myPrint(hMC['dummy'],'diMuonBins'+tag+'Summary')

def IP(OnlyDraw = False):
    if not OnlyDraw:
        for c in case:
            sTree = case[c][0]
            h = case[c][1]
            ut.bookHist(h,'IP','transv distance to z-axis at target',100,0.,250.)
            ut.bookHist(h,'IPx','x distance to z-axis at target',100,-100.,100.)
            ut.bookHist(h,'IPmu','transv distance to z-axis at target',100,0.,250.)
            ut.bookHist(h,'IPxmu','x distance to z-axis at target',100,-100.,100.)
            ut.bookHist(h,'IPxy','xy distance to z-axis at target',100,-100.,100.,100,-100.,100.)
            for n in range(sTree.GetEntries()):
                rc = sTree.GetEvent(n)
                for t in range(sTree.nTr):
                    if sTree.GoodTrack[t]<0: continue
                    P = ROOT.TMath.Sqrt(sTree.Px[t]**2+sTree.Py[t]**2+sTree.Pz[t]**2)
                    if P<5. : continue
                    l = (sTree.z[t] - zTarget)/sTree.Pz[t]
                    x = sTree.x[t]+l*sTree.Px[t]
                    y = sTree.y[t]+l*sTree.Py[t]
                    r = ROOT.TMath.Sqrt(x*x+y*y)
                    rc = h['IP'].Fill(r)
                    rc = h['IPx'].Fill(x)
                    rc = h['IPxy'].Fill(x,y)
                    if abs(sTree.Delx[t])<cuts['muTrackMatchX']:
                        rc = h['IPxmu'].Fill(x)
                    if abs(sTree.Delx[t])<cuts['muTrackMatchX'] and abs(sTree.Dely[t])<cuts['muTrackMatchY']:
                        rc = h['IPmu'].Fill(r)
    for proj in ['','x']:
        ut.bookCanvas(hData,'TIP'+proj,'IP'+proj,1600,1200,2,2)
        ic = 1
        for mu in ['','mu']:
            tc = hData['TIP'+proj].cd(ic)
            tc.SetLogy()
            hData['MCIP'+proj+mu]=hMC['IP'+proj+mu].Clone('MCIP'+proj+mu)
            hData['MCIP'+proj+mu].Scale( hData['IP'+proj+mu].GetEntries()/hMC['IP'+proj+mu].GetEntries())
            for k in [0,2]:
                if proj=='x':      hData['leg'+proj+str(ic+k)]=ROOT.TLegend(0.33,0.17,0.67,0.24)
                else:             hData['leg'+proj+str(ic+k)]=ROOT.TLegend(0.43,0.77,0.88,0.88)
            for c in case:
                x = ''
                if c=='MC': x=c
                for k in [0,2]:
                    tc = hData['TIP'+proj].cd(ic+k)
                    hData[x+'IP'+proj+mu].SetLineColor(case[c][2])
                    hData[x+'IP'+proj+mu].Draw(case[c][3])
                    hData[x+'IP'+proj+mu].SetLineColor(case[c][2])
                    hData[x+'IP'+proj+mu].Draw(case[c][3])
                    mean = hData[x+'IP'+proj+mu].GetMean()
                    rms = hData[x+'IP'+proj+mu].GetRMS()
                    hData[x+'IP'+proj+mu].SetStats(0)
                    txt = "%s  Mean=%5.2F  Std Dev=%5.2F"%(c,mean,rms)
                    rc = hData['leg'+proj+str(ic+k)].AddEntry(hData[x+'IP'+proj+mu],txt,'PL')
            for k in [0,2]:
                tc = hData['TIP'+proj].cd(ic+k)
                hData['leg'+proj+str(ic+k)].Draw()
            ic+=1
        myPrint(hData['TIP'+proj],'IP'+proj)

def RPCextrap(OnlyDraw = False,pxMin=3.,pMin=10.,station1Occ=100,station1OccLow=0):
    if not OnlyDraw:
        for c in case:
            sTree = case[c][0]
            h = case[c][1]
            for l in range(1,7):
                if l<5:  txt ="x station "+str(l)+" Occupancy"
                if l==5: txt ="u station 1 Occupancy"
                if l==6: txt ="v station 2 Occupancy"
                ut.bookHist(h,'stationOcc'+str(l),txt,50,-0.5,49.5)
            ut.bookHist(h,'upStreamOcc',"station 1&2",200,-0.5,199.5)
            ut.bookHist(h,'upStreamOccwithTrack',"station 1&2",200,-0.5,199.5)
            ut.bookHist(h,'upStreamOccMuonTagged',"station 1&2",200,-0.5,199.5)
            ut.bookHist(h,'xy',   'xy at RPC',100,-150.,150.,100,-150.,150.)
            ut.bookHist(h,'xyIn', 'xy at RPC in acceptance',100,-150.,150.,100,-150.,150.)
            ut.bookHist(h,'xyInX','xy at RPC in acceptance',100,-150.,150.,100,-150.,150.)
            ut.bookHist(h,'xyTagged', 'xy at RPC for muons',100,-150.,150.,100,-150.,150.)
            ut.bookHist(h,'xyTaggedX','xy at RPC for muons',100,-150.,150.,100,-150.,150.)
            for x in ['-Tagged','-nonTagged']:
                ut.bookHist(h,'chi2Dof'+x,'chi2 per DoF',100,0.,10.)
                ut.bookHist(h,'p/pt'+x,'momentum vs Pt (GeV);#it{p} [GeV/c]; #it{p}_{T} [GeV/c]',500,0.,500.,100,0.,10.)
                ut.bookHist(h,'pz/Abspx'+x,'Pz vs Px (GeV);#it{p} [GeV/c]; #it{p}_{X} [GeV/c]',500,0.,500.,100,0.,10.)
            for n in range(sTree.GetEntries()):
                rc = sTree.GetEvent(n)
                upStreamOcc = sTree.stationOcc[1]+sTree.stationOcc[5]+sTree.stationOcc[2]+sTree.stationOcc[6]
                rc = h['upStreamOcc'].Fill(upStreamOcc)
                if sTree.nTr>0:
                    for l in range(1,7):
                        rc = h['stationOcc'+str(l)].Fill(sTree.stationOcc[l])
                        if sTree.stationOcc[l]>40: print l,sTree.stationOcc[l],sTree.evtnr,sTree.spillnrA,sTree.spillnrB,sTree.spillnrC ,sTree.GetCurrentFile().GetName()
                    rc = h['upStreamOccwithTrack'].Fill(upStreamOcc)
                if sTree.stationOcc[1] > station1Occ or sTree.stationOcc[1] < station1OccLow: continue
                for t in range(sTree.nTr):
                    if sTree.GoodTrack[t]<0: continue
                    Pvec = ROOT.TVector3(sTree.Px[t],sTree.Py[t],sTree.Pz[t])
                    P = Pvec.Mag()
                    if abs(sTree.Px[t])<pxMin : continue
                    if P<pMin                 : continue
                    rc = h['xy'].Fill(sTree.RPCx[t],sTree.RPCy[t])
                    if sTree.RPCx[t]>cuts['xLRPC1'] and sTree.RPCx[t]<cuts['xRRPC1']: 
                        rc = h['xyInX'].Fill(sTree.RPCx[t],sTree.RPCy[t])
                        if abs(sTree.Delx[t])<cuts['muTrackMatchX']:
                            rc = h['xyTaggedX'].Fill(sTree.RPCx[t],sTree.RPCy[t])
                            rc = h['pz/Abspx-Tagged'].Fill(Pvec[2],Pvec[0])
                        else:
                            rc = h['pz/Abspx-nonTagged'].Fill(Pvec[2],Pvec[0])
                        if sTree.RPCy[t]>cuts['yBRPC1'] and sTree.RPCy[t]<cuts['yTRPC1']:
                            rc = h['xyIn'].Fill(sTree.RPCx[t],sTree.RPCy[t])
                        if abs(sTree.Delx[t])<cuts['muTrackMatchX'] and abs(sTree.Dely[t])<cuts['muTrackMatchY']:
                            rc = h['xyTagged'].Fill(sTree.RPCx[t],sTree.RPCy[t])
                            rc = h['chi2Dof-Tagged'].Fill(sTree.Chi2[t])
                            rc = h['p/pt-Tagged'].Fill(P,Pvec.Pt())
                            rc = h['upStreamOccMuonTagged']
                        else:
                            rc = h['chi2Dof-nonTagged'].Fill(sTree.Chi2[t])
                            rc = h['p/pt-nonTagged'].Fill(P,Pvec.Pt())
    effDataIn = hData['xyTagged'].GetEntries()/hData['xyIn'].GetEntries()*100.
    effMCIn   = hMC['xyTagged'].GetEntries()/hMC['xyIn'].GetEntries()*100.
    effData = hData['xyTagged'].GetEntries()/hData['xy'].GetEntries()*100.
    effMC   = hMC['xyTagged'].GetEntries()/hMC['xy'].GetEntries()*100.
    print "eff xy data: %5.2F (%5.2F)  MC: %5.2F (%5.2F)"%(effDataIn,effData,effMCIn,effMC)
    effDataIn = hData['xyTaggedX'].GetEntries()/hData['xyInX'].GetEntries()*100.
    effMCIn   = hMC['xyTaggedX'].GetEntries()/hMC['xyInX'].GetEntries()*100.
    effData = hData['xyTaggedX'].GetEntries()/hData['xy'].GetEntries()*100.
    effMC   = hMC['xyTaggedX'].GetEntries()/hMC['xy'].GetEntries()*100.
    print "eff x  data: %5.2F (%5.2F)  MC: %5.2F (%5.2F)"%(effDataIn,effData,effMCIn,effMC)
    keys = ['upStreamOcc','upStreamOccwithTrack','upStreamOccMuonTagged']
    for l in range(1,7):
        keys.append('stationOcc'+str(l))
    for key in keys:
        hData['MC'+key] = hMC[key].Clone('MC'+key)
        hData['MC'+key].SetLineColor(ROOT.kRed)
        if key.find('upStreamOcc')==0:
            norm = (hMC[key].GetBinContent(15))/(hData[key].GetBinContent(15))
        else:  
            norm = (hMC[key].GetBinContent(4)+hMC[key].GetBinContent(5))/(hData[key].GetBinContent(4)+hData[key].GetBinContent(5))
        hData['MC'+key].Scale(1./norm)

def MCRPCextrap(OnlyDraw = False):
    if not OnlyDraw:
        c = 'MC'
        sTree = case[c][0]
        h = case[c][1]
        ut.bookHist(h,'P','true momentum muReconstructible;[GeV/c]',400,0.,400.)
        ut.bookHist(h,'Pt','true momentum muReconstructible;[GeV/c]',80,0.,4.)
        ut.bookHist(h,'Px','true momentum muReconstructible;[GeV/c]',80,0.,4.)
        ut.bookHist(h,'Preco1','true momentum reco track matched;[GeV/c]',400,0.,400.)
        ut.bookHist(h,'Ptreco1','true momentum reco track matched;[GeV/c]',100,0.,10.)
        ut.bookHist(h,'Pxreco1','true momentum reco track matched;[GeV/c]',100,0.,10.)
        ut.bookHist(h,'Preco2','true momentum reco track matched, good track p/pt;[GeV/c]',400,0.,400.)
        ut.bookHist(h,'Preco3','true momentum reco track matched, good track pz/px;[GeV/c]',400,0.,400.)
        for x in ['','mu']:
            ut.bookHist(h,'delP'+x,'true momentum - reco vs true P;[GeV/c]',100,-10.,10.,80,0.,400.)
            ut.bookHist(h,'delPx'+x,'true Px - reco vs true P;[GeV/c]',100,-2.,2.,80,0.,400.)
            ut.bookHist(h,'delPt'+x,'true Pt - reco vs true P;[GeV/c]',100,-2.,2.,80,0.,400.)
        for n in range(sTree.GetEntries()):
            rc = sTree.GetEvent(n)
            if sTree.MCRecoDT.size() != 1: continue # look at simple events for the moment 
            for m in sTree.MCRecoRPC:
                i = -1
                for d in sTree.MCRecoDT:
                    i+=1
                    if m!=d: continue  # require same MCTrack
                    P  = ROOT.TVector3(sTree.MCRecoDTpx[i],sTree.MCRecoDTpy[i],sTree.MCRecoDTpz[i])
                    rc = h['P'].Fill(P.Mag())
                    rc = h['Px'].Fill(abs(P.X()))
                    rc = h['Pt'].Fill(P.Pt())
                    for t in range(sTree.nTr):
                        if sTree.nTr>1: continue
                        Preco  = ROOT.TVector3(sTree.Px[t],sTree.Py[t],sTree.Pz[t])
                        delP = P.Mag()-Preco.Mag()
                        delPx = P.X()-Preco.X()
                        delPt = P.Pt()-Preco.Pt()
                        rc = h['delP'].Fill(delP,P.Mag())
                        rc = h['delPx'].Fill(delPx,P.Mag())
                        rc = h['delPt'].Fill(delPt,P.Mag())
                        if abs(sTree.Delx[t])<cuts['muTrackMatchX'] and abs(sTree.Dely[t])<cuts['muTrackMatchY']:
                            rc = h['Preco1'].Fill(P.Mag())
                            rc = h['Pxreco1'].Fill(abs(P.X()))
                            rc = h['Ptreco1'].Fill(P.Pt())
                            rc = h['delPmu'].Fill(delP,P.Mag())
                            rc = h['delPxmu'].Fill(delPx,P.Mag())
                            rc = h['delPtmu'].Fill(delPt,P.Mag())
        for x in ['P','Pt','Px']:
            h['tagEff'+x]=ROOT.TEfficiency(h[x+'reco1'],h[x])

def makeProjectionRMS(h,hname,proj):
    pname = hname+proj
    if not proj.find('x')<0: h[pname] = h[hname].ProjectionX(pname)
    else:                    h[pname] = h[hname].ProjectionY(pname)
    for n in range(1,h[pname].GetNbinsX()+1):
        if not proj.find('x')<0: temp = h[hname].ProjectionY('p'+str(n),n,n)
        else:                    temp = h[hname].ProjectionX('p'+str(n),n,n)
        RMS = temp.GetRMS()
        h[pname].SetBinContent(n,RMS)

def clones(OnlyDraw = False,noClones=False):
    if not OnlyDraw:
        for c in case:
            sTree = case[c][0]
            h = case[c][1]
            ut.bookHist(h,'cos alpha','cosine of angle between two tracks;cos[#alpha]',10000,0.95,1.01)
            for n in range(sTree.GetEntries()):
                rc = sTree.GetEvent(n)
                for a in range(sTree.nTr-1):
                    if sTree.GoodTrack[a]<0: continue
                    if noClones and sTree.GoodTrack[a]>1000: continue
                    A = ROOT.TVector3(sTree.Px[a],sTree.Py[a],sTree.Pz[a])
                    for b in range(a,sTree.nTr):
                        if sTree.GoodTrack[b]<0: continue
                        if noClones and sTree.GoodTrack[b]>1000: continue
                        if sTree.Sign[b]*sTree.Sign[a]>0: continue
                        B = ROOT.TVector3(sTree.Px[b],sTree.Py[b],sTree.Pz[b])
                        rc = h['cos alpha'].Fill(A.Dot(B)/(A.Mag()*B.Mag()))
    hData['cos alpha'].GetXaxis().SetRangeUser(0.999,1.0001)
    hMC['cos alpha'].SetLineColor(ROOT.kRed)
    hData['MCcos alpha'] = hMC['cos alpha'].Clone('MCcos alpha')
    hData['MCcos alpha'].Scale(hData['cos alpha'].GetEntries()/hMC['cos alpha'].GetEntries())
    hData['MCcos alpha'].SetStats(0)
    hData['cos alpha'].SetStats(0)
    ut.bookCanvas(hData,'clones','Clones',1200,900,1,1)
    hData['cos alpha'].Draw()
    hData['MCcos alpha'].Draw('same')
    hData['leg']=ROOT.TLegend(0.24,0.50,0.54,0.61)
    rc = hData['leg'].AddEntry(hData["cos alpha"],"Data",'PL')
    rc = hData['leg'].AddEntry(hData["MCcos alpha"],"MC",'PL')
    hData['leg'].Draw()
    lmax = hData['cos alpha'].GetMaximum()
    h['lcut'] =  ROOT.TArrow(0.99995,0.,0.99995,lmax*0.2,0.05,"<")
    h['lcut'].SetLineColor(ROOT.kMagenta)
    h['lcut'].SetLineWidth(2)
    h['lcut'].Draw()
    myPrint(hData['clones'],'MC-Comparison-Clones') 
    ff = ROOT.TFile('Clones.root','recreate')
    hData['clones'].Write('Clones.root')

def tails(OnlyDraw = False):
    if not OnlyDraw:
        for c in case:
            sTree = case[c][0]
            h = case[c][1]
            ut.bookHist(h,'momentum','momentum',1000,0.0,1000.)
            for n in range(sTree.GetEntries()):
                rc = sTree.GetEvent(n)
                for t in range(sTree.nTr):
                    if sTree.GoodTrack[t]<0: continue
                    P = ROOT.TVector3(sTree.Px[t],sTree.Py[t],sTree.Pz[t])
                    rc = h['momentum'].Fill(P.Mag())
        hData['MCmomentum'] = hMC['momentum'].Clone('MCmomentum')
        norm = hData['momentum'].Integral(5,100)/hMC['momentum'].Integral(5,100)
        hData['MCmomentum'].SetLineColor(ROOT.kRed)
        hData['MCmomentum'].Scale(norm)

deadChannels4MC = [10112001,11112012,20112003,30002042,30012026,30102021,30102025,30112013,30112018,40012014]

def reconstructible(OnlyDraw = False):
    if not OnlyDraw:
        #for c in case:
        c = 'MC'
        sTree = case[c][0]
        h = case[c][1]
        ut.bookHist(h,'reconstructibleP',"reconstructible P",400,0.0,400.)
        ut.bookHist(h,'reconstructedP',"reconstructed P",400,0.0,400.)
        for x in ['','_mu']:
            ut.bookHist(h,'delPzR'+x,"reconstructed Pz - true / true",1000,-5.,5.)
            ut.bookHist(h,'delPtR'+x,"reconstructed Pt - true / true",1000,-5.,5.)
            ut.bookHist(h,'delPz'+x,"reconstructed Pz - true ",1000,-50.,50.)
            ut.bookHist(h,'delPx'+x,"reconstructed Px - true ",1000,-1.,1.)
            ut.bookHist(h,'delPt'+x,"reconstructed Pt - true ",1000,-1.,1.)
        ut.bookHist(h,'upStreamOcc',"station 1&2",200,-0.5,199.5)
        ut.bookHist(h,'upStreamOcc-nonReco',"station 1&2",200,-0.5,199.5)
        ut.bookHist(h,'upStreamOcc-badRecoP',"station 1&2",200,-0.5,199.5)
        ut.bookHist(h,'upStreamOcc-badRecoPx',"station 1&2",200,-0.5,199.5)
        ut.bookHist(h,'upStreamOcc-reconstructible',"station 1&2",200,-0.5,199.5)
        ut.bookHist(h,'stationOcc1x1u',"station 1",50,-0.5,49.5,50,-0.5,49.5)
        ut.bookHist(h,'stationOcc2x2v',"station 2",50,-0.5,49.5,50,-0.5,49.5)
        for n in range(sTree.GetEntries()):
            rc = sTree.GetEvent(n)
            rc = h['stationOcc1x1u'].Fill(sTree.stationOcc[1],sTree.stationOcc[5])
            rc = h['stationOcc2x2v'].Fill(sTree.stationOcc[2],sTree.stationOcc[6])
            upStreamOcc = sTree.stationOcc[1]+sTree.stationOcc[5]+sTree.stationOcc[2]+sTree.stationOcc[6]
            rc = h['upStreamOcc'].Fill(upStreamOcc)
            if sTree.MCRecoDT.size()==1:
                rc = h['upStreamOcc-reconstructible'].Fill(upStreamOcc)
                m = 0
                P  = ROOT.TVector3(sTree.MCRecoDTpx[m],sTree.MCRecoDTpy[m],sTree.MCRecoDTpz[m])
                rc = h['reconstructibleP'].Fill(P.Mag())
                if sTree.nTr==1: 
                    rc = h['reconstructedP'].Fill(P.Mag())
                    Preco  = ROOT.TVector3(sTree.Px[0],sTree.Py[0],sTree.Pz[0])
                    delPz  = (sTree.Pz[0]-sTree.MCRecoDTpz[0])
                    delPx = (sTree.Px[0]-sTree.MCRecoDTpx[0])
                    delPzR = (sTree.Pz[0]-sTree.MCRecoDTpz[0])/sTree.MCRecoDTpz[0]
                    rc = h['delPz'].Fill(delPz)
                    rc = h['delPx'].Fill(delPx)
                    rc = h['delPzR'].Fill(delPzR)
                    delPt  = Preco.Pt()-P.Pt()
                    delPtR = (Preco.Pt()-P.Pt()/P.Pt())
                    rc = h['delPt'].Fill(delPt)
                    rc = h['delPtR'].Fill(delPtR)
                    if abs(sTree.Delx[0])<cuts['muTrackMatchX'] and abs(sTree.Dely[0])<cuts['muTrackMatchY']:
                        x='_mu'
                        rc = h['delPz'+x].Fill(delPz)
                        rc = h['delPx'+x].Fill(delPx)
                        rc = h['delPzR'+x].Fill(delPzR)
                        rc = h['delPt'+x].Fill(delPt)
                        rc = h['delPtR'+x].Fill(delPtR)
                    if abs(delPz)>10.: rc = h['upStreamOcc-badRecoP'].Fill(upStreamOcc)
                    if abs(delPx)>2.: rc = h['upStreamOcc-badRecoPx'].Fill(upStreamOcc)
#        if abs(delPt)>2. :                                        print "bad reco pt",n,upStreamOcc,sTree.MCRecoDT.size(),delPt,P.Pt()
#        if abs( abs(sTree.Px[0])-abs(sTree.MCRecoDTpx[0]))>2. :   print "bad reco px",n,upStreamOcc,sTree.MCRecoDT.size(),delPx,sTree.MCRecoDTpx[0]
                if sTree.nTr <1:
                    rc = h['upStreamOcc-nonReco'].Fill(upStreamOcc)
                    # print "non reco",n,upStreamOcc,sTree.MCRecoDT.size(),sTree.MCRecoDTpx[0],sTree.MCRecoDTpy[0],sTree.MCRecoDTpz[0]
        h['ineff-upStreamOcc-reconstructible']=ROOT.TEfficiency(h['upStreamOcc-nonReco'],h['upStreamOcc-reconstructible'])
        h['effP']=ROOT.TEfficiency(h['reconstructedP'],h['reconstructibleP'])
from array import array
def RecoEffFunOfOcc(OnlyDraw = False,Nevents = -1):
    pMin = 5.
    if not OnlyDraw:
        c = 'Data'
        sTree = case[c][0]
        h = case[c][1]
        if Nevents<0: Nevents=sTree.GetEntries()
        ut.bookHist(h,'Occ','N',50,0.,200.)
        ut.bookHist(h,'OccAllEvents','N',50,0.,200.)
        for n in range(Nevents):
            rc = sTree.GetEvent(n)
            upStreamOcc = sTree.stationOcc[1]+sTree.stationOcc[5]+sTree.stationOcc[2]+sTree.stationOcc[6]
            if sTree.nTr>0: rc = h['OccAllEvents'].Fill(upStreamOcc)
            for t in range(sTree.nTr):
                if sTree.GoodTrack[t]<0: continue
                Pvec = ROOT.TVector3(sTree.Px[t],sTree.Py[t],sTree.Pz[t])
                P = Pvec.Mag()
                if P<pMin                 : continue
                if abs(sTree.Delx[t])<cuts['muTrackMatchX'] and abs(sTree.Dely[t])<cuts['muTrackMatchY']:
                    rc = h['Occ'].Fill(upStreamOcc)
        ut.writeHists(h,'histos-DataOcc.root')
        c = 'MC'
        sTree = case[c][0]
        h = case[c][1]
# variable bin size
        paxis = []
        xv = 0.
        for x in range(100): 
            paxis.append(xv)
            xv+=1.
        for x in range(20): 
            paxis.append(xv)
            xv+=5.
        for x in range(5): 
            paxis.append(xv)
            xv+=50.
        dpaxis = array('d',paxis)
        ut.bookHist(h,'Ptrue', 'true momentum muReconstructible;[GeV/c];N',500,0.,500.)
        ut.bookHist(h,'P', 'true momentum muReconstructible;[GeV/c];N',dpaxis,50,0.,200.)
        ut.bookHist(h,'Pz','true momentum muReconstructible;[GeV/c];N',dpaxis,50,0.,200.)
        ut.bookHist(h,'Preco', 'true momentum reconstructed;[GeV/c];N',dpaxis,50,0.,200.)
        ut.bookHist(h,'Pfailed', 'true momentum no reco;[GeV/c];N',dpaxis,50,0.,200.)
        ut.bookHist(h,'Pzreco','true momentum reconstructed;[GeV/c];N',dpaxis,50,0.,200.)
        ut.bookHist(h,'Pt','true momentum muReconstructible;[GeV/c];N',80,0.,4.,50,0.,200.)
        ut.bookHist(h,'Px','true momentum muReconstructible;[GeV/c];N',80,0.,4.,50,0.,200.)
        ut.bookHist(h,'Ptreco','true momentum reconstructed;[GeV/c];N',80,0.,4.,50,0.,200.)
        ut.bookHist(h,'Pxreco','true momentum reconstructed;[GeV/c];N',80,0.,4.,50,0.,200.)
        ut.bookHist(h,'delx/y','delx vs dely;cm;cm',100,0.,20,100,0.,50.)
        ut.bookHist(h,'OccAllEvents','N',50,0.,200.)
        for x in ['','_mu']:
            ut.bookHist(h,'delP'+x,"reconstructed P - true ",1000,-50.,50.)
            ut.bookHist(h,'delPt'+x,"reconstructed Pt - true ",1000,-1.,1.)
            ut.bookHist(h,'delPx'+x,"reconstructed Px - true ",1000,-1.,1.)
        for n in range(sTree.GetEntries()):
            rc = sTree.GetEvent(n)
            upStreamOcc = sTree.stationOcc[1]+sTree.stationOcc[5]+sTree.stationOcc[2]+sTree.stationOcc[6]
            if sTree.nTr>0: rc = h['OccAllEvents'].Fill(upStreamOcc)
            if sTree.MCRecoDT.size() != 1: continue # look at 1 Track events for the moment 
            # require reco RPC tracks, otherwise cannot compare to zero field data which starts with RPC tracks
            if sTree.nRPC%10 == 0 or sTree.nRPC/10 == 0 : continue
            # starting with reconstructible RPC track, check that same MCTrack is reconstructible in DT
            for m in sTree.MCRecoRPC:
                i = -1
                for d in sTree.MCRecoDT:
                    i+=1
                    if m!=d: continue  # require same MCTrack
                    P  = ROOT.TVector3(sTree.MCRecoDTpx[i],sTree.MCRecoDTpy[i],sTree.MCRecoDTpz[i])
                    rc = h['P'].Fill(P.Mag(),upStreamOcc)
                    rc = h['Ptrue'].Fill(P.Mag())
                    rc = h['Px'].Fill(abs(P.X()),upStreamOcc)
                    rc = h['Pz'].Fill(P.Z(),upStreamOcc)
                    rc = h['Pt'].Fill(P.Pt(),upStreamOcc)
                    found = False  # avoid double counting
                    if sTree.nTr<1:
                        rc = h['Pfailed'].Fill(P.Mag(),upStreamOcc)
                        if Debug: print "no reco track  event nr ",n,sTree.GetCurrentFile().GetName(),P.Mag(),upStreamOcc
                    for t in range(sTree.nTr):
                        Preco  = ROOT.TVector3(sTree.Px[t],sTree.Py[t],sTree.Pz[t])
                        delP   = P.Mag() - Preco.Mag()
                        delPx  = P.X() -   Preco.X()
                        delPt  = P.Pt() -  Preco.Pt()
                        rc = h['delP'].Fill(delP,P.Mag())
                        rc = h['delPx'].Fill(delPx,P.Mag())
                        rc = h['delPt'].Fill(delPt,P.Mag())
                        rc = h['delx/y'].Fill(sTree.Delx[t],sTree.Dely[t])
                        # if there is no muon track in event, sTree.Delx[t] = 9999. and sTree.Dely[t] = 9999.
                        if Debug and (sTree.Delx[t]>9998 or sTree.Dely[t] > 9998): print "no reco RPC track in RPC reconstructible event" 
                        if abs(sTree.Delx[t])<cuts['muTrackMatchX'] and abs(sTree.Dely[t])<cuts['muTrackMatchY']:
                            if found: continue
                            rc = h['delP_mu'].Fill(delP,P.Mag())
                            rc = h['delPx_mu'].Fill(delPx,P.Mag())
                            rc = h['delPt_mu'].Fill(delPt,P.Mag())
                            rc = h['Preco'].Fill(P.Mag(),upStreamOcc)
                            rc = h['Pxreco'].Fill(abs(P.X()),upStreamOcc)
                            rc = h['Pzreco'].Fill(P.Z(),upStreamOcc)
                            rc = h['Ptreco'].Fill(P.Pt(),upStreamOcc)
                            found = True
                    if not found and sTree.nTr==1 and Debug:
                        dec = abs(sTree.Delx[t])<cuts['muTrackMatchX'] and abs(sTree.Dely[t])<cuts['muTrackMatchY']
                        print "event nr ",n,P.Mag(),sTree.nTr,upStreamOcc,abs(sTree.Delx[t]),abs(sTree.Dely[t]),dec
        ut.writeHists(h,'histos-MCRecoEffFunOfOcc'+'-'+fdir+'.root')
        return
    if not hMC.has_key('P'): 
        ut.readHists(hMC,'histos-MCRecoEffFunOfOcc.root')
    if not hData.has_key('Occ'): 
        ut.readHists(hData,'histos-DataOcc.root')
        hData['Occ'].Scale(1./hData['Occ'].GetMaximum())
    # now take occupancy from zero field
    if not hMC.has_key("hDTEff"):
        hMC["hDTEff"] = {}
        hDTEff=hMC["hDTEff"]
        interestingHistos=[]
        for k in range(1,5):
            interestingHistos.append("upStreamOccWithTrack"+str(k))
            interestingHistos.append("upStreamOcc"+str(k))
        ut.readHists(hDTEff,'DTEff.root',interestingHistos)
        hDTEff['upStreamOccWithTrack']=hDTEff['upStreamOccWithTrack1'].Clone('upStreamOccWithTrack')
        hDTEff['upStreamOccWithTrack'].Add(hDTEff['upStreamOccWithTrack2'])
        hDTEff['upStreamOccWithTrack'].Add(hDTEff['upStreamOccWithTrack3'])
        hDTEff['upStreamOccWithTrack'].Add(hDTEff['upStreamOccWithTrack4'])

        hDTEff['upStreamOcc']=hDTEff['upStreamOcc1'].Clone('upStreamOcc')
        hDTEff['upStreamOcc'].Add(hDTEff['upStreamOcc2'])
        hDTEff['upStreamOcc'].Add(hDTEff['upStreamOcc3'])
        hDTEff['upStreamOcc'].Add(hDTEff['upStreamOcc4'])

        hMC['zeroFieldOcc']=hDTEff['upStreamOccWithTrack'].Rebin(4,'zeroFieldOcc')
        hMC['zeroFieldOcc'].Scale(1./hMC['zeroFieldOcc'].GetMaximum())
        hMC['zeroFieldOcc'].SetLineColor(ROOT.kGreen)
        hMC['zeroFieldOcc'].SetMarkerColor(ROOT.kGreen)
        hMC['zeroFieldOcc'].SetMarkerStyle(24)
    h = hMC
    tmp = h['P'].ProjectionY()
    T = ROOT.TLatex()
    T.SetTextColor(ROOT.kMagenta)
    ut.bookCanvas(h,'upStreamOcc','upstream occupancy',900,600,1,1)
    tc = hMC['upStreamOcc'].cd(1)
    tc.SetLogy(1)
    hData['OccAllEvents'].SetTitle('upstream occupancy;Number of hits;arbitrary scale')
    hData['OccAllEvents'].SetStats(0)
    hData['OccAllEvents'].Draw()
    hmax = hData['OccAllEvents'].GetMaximum()
    hMC['OccAllEvents'].SetLineColor(ROOT.kMagenta)
    hMC['OccAllEvents_scaled']=hMC['OccAllEvents'].Clone('OccAllEvents_scaled')
    hMC['OccAllEvents_scaled'].Scale(hmax/hMC['OccAllEvents'].GetMaximum())
    hMC['OccAllEvents_scaled'].SetStats(0)
    hMC['OccAllEvents_scaled'].Draw('same hist')
    myPrint(h['upStreamOcc'],'upstreamOcc')
    variables = ['P','Px','Pz','Pt']
    fun = {}
    for var in variables:
        xmin = tmp.GetBinLowEdge(1)
        xmax = tmp.GetBinLowEdge(tmp.GetNbinsX())+tmp.GetBinWidth(tmp.GetNbinsX())
        ut.bookHist(h,'effFun'+var,'eff as function of occupancy '+var,tmp.GetNbinsX(),xmin,xmax)
        ut.bookCanvas(h,'eff'+var,'Efficiencies '+var,1200,900,5,4)
        if var=='P' or var=='Pz': fun[var] = ROOT.TF1('pol0'+var,'[0]',12.,200.)
        else:                     fun[var] = ROOT.TF1('pol0'+var,'[0]',0.,2.5)
        j=1
        for o in range(1,tmp.GetNbinsX()+1):
            h[var+'eff'+str(o)] =  ROOT.TEfficiency(h[var+'reco'].ProjectionX(var+'reco'+str(o),o,o),h[var].ProjectionX(var+str(o),o,o))
            if j<20:
                tc = h['eff'+var].cd(j)
                j+=1
                h[var+'eff'+str(o)].Draw()
                tc.Update()
                if h[var+'eff'+str(o)].GetTotalHistogram().GetEntries() == 0: continue
                g = h[var+'eff'+str(o)].GetPaintedGraph()
                x = h[var+'eff'+str(o)].GetEfficiency(20) # just to have a decent scale
                g.SetMinimum(x*0.8)
                g.SetMaximum(1.02)
                if var=='P' or var=='Pz':
                    g.GetXaxis().SetRangeUser(0.,200.)
                t = str(int(tmp.GetBinLowEdge(o)))+"-"+str(int(tmp.GetBinLowEdge(o)+tmp.GetBinWidth(o)))
                rc = T.DrawLatexNDC(0.5,0.9,t)
                rc = h[var+'eff'+str(o)].Fit(fun[var],'SRQ')
                fitResult = rc.Get()
                if fitResult:
                    eff = fitResult.Parameter(0)
                    rc = T.DrawLatexNDC(0.2,0.9,"eff=%5.2F%%"%(eff*100.))
                    h['effFun'+var].SetBinContent(o,eff)
                tc.Update()
        myPrint(h['eff'+var],'MCEfficienciesOcc'+var)
    ut.bookCanvas(h,'eff final','Efficiencies ',1200,900,2,2)
    j=1
    h['occ']=hMC['OccAllEvents'].Clone('occ') # want to have MC efficiency for all events, not only 1 track
    h['occ'].Scale(1./h['occ'].GetMaximum())
    h['occ'].SetLineColor(ROOT.kMagenta)
    for var in variables:
        h['eff final'].cd(j)
        j+=1
        h['effFun'+var].SetStats(0)
        h['effFun'+var].SetMarkerStyle(20)
        h['effFun'+var].SetMarkerColor(h['effFun'+var].GetLineColor())
        h['effFun'+var].GetXaxis().SetRangeUser(0.,100.)
        h['effFun'+var].Draw('P')
        h['effFun'+var].Draw('hist same')
        h['occ'].SetMarkerStyle(8)
        h['occ'].SetMarkerColor(h['occ'].GetLineColor())
        h['occ'].Draw('same P')
        h['occ'].Draw('same hist')
    var = 'P'
    ut.bookCanvas(h,'eff final P','Efficiencies ',900,600,1,1)
    h['eff final P'].cd(1)
    h['effFun'+var].SetTitle('Tracking efficiency as function of occupancy; N hits in upstream stations;efficiency')
    h['effFun'+var].GetXaxis().SetRangeUser(0.,100.)
    h['effFun'+var].Draw('P')
    h['effFun'+var].Draw('hist same')
    h['occ'].Draw('same P') 
    h['occ'].Draw('same hist')
    h['zeroFieldOcc'].Draw('P same')
    h['zeroFieldOcc'].Draw('same hist')
    hData['Occ'].Draw('same hist')
    hData['Occ'].Draw('P same')
    rc = T.DrawLatexNDC(0.28,0.40,"upstream station occupancy MC")
    T.SetTextColor(h['zeroFieldOcc'].GetLineColor())
    rc = T.DrawLatexNDC(0.28,0.28,"upstream station occupancy zero field Data")
    T.SetTextColor(hData['Occ'].GetLineColor())
    rc = T.DrawLatexNDC(0.28,0.34,"upstream station occupancy Data")
    T.SetTextColor(ROOT.kBlue)
    rc = T.DrawLatexNDC(0.35,0.8,"tracking efficiency")
    myPrint(h['eff final P'],"MCTrackEffFunOcc")
    finalEff  = 0
    sumEvents = 0
    for o in range(1,h['occ'].GetNbinsX()+1):
        finalEff+=h['occ'].GetBinContent(o)*h['effFun'+var].GetBinContent(o)
        sumEvents+=h['occ'].GetBinContent(o)
    finalEff=finalEff/sumEvents
    print "and the final answer is for MC: %5.2F%%"%(finalEff*100)
    finalEff  = 0
    sumEvents = 0
    for o in range(1,hData['Occ'].GetNbinsX()+1):
        finalEff+=hData['Occ'].GetBinContent(o)*h['effFun'+var].GetBinContent(o)
        sumEvents+=hData['Occ'].GetBinContent(o)
    finalEff=finalEff/sumEvents
    print "and the prediction for Data: %5.2F%%"%(finalEff*100)
    finalEff  = 0
    sumEvents = 0
    for o in range(1,h['zeroFieldOcc'].GetNbinsX()+1):
        finalEff+=h['zeroFieldOcc'].GetBinContent(o)*h['effFun'+var].GetBinContent(o)
        sumEvents+=h['zeroFieldOcc'].GetBinContent(o)
    finalEff=finalEff/sumEvents
    print "and the prediction for zeroField Data: %5.2F%%"%(finalEff*100)

def plotOccExample():
    ut.bookCanvas(h,'Occexample',' ',1200,600,1,1)
    for n in range(3,7):
        x = hMC['effP'].GetListOfPrimitives()[n]
        x.GetListOfPrimitives()[1].Draw()
        t = x.GetListOfPrimitives()[2].Clone('t2'+str(n))
        tmp = t.GetTitle().split('-')
        t.SetTitle(tmp[0]+'-'+str(int(tmp[1])-1))
        t.SetTextSize(0.09)
        t.Draw()
        t2 = x.GetListOfPrimitives()[3].Clone('t3'+str(n))
        t2.SetTextSize(0.09)
        t2.Draw()
        myPrint(h['Occexample'],x.GetName())

def trueMomPlot(Nevents=-1,onlyPlotting=False):
    ROOT.gStyle.SetTitleStyle(0)
    h     = hMC
    sTree = sTreeMC
    sim10fact  = MCStats['1GeV']/MCStats['10GeV'] # normalize 10GeV to 1GeV stats
    charmNorm  = {1:0.176,10:0.424}
    beautyNorm = {1:0.,   10:0.01218}
    if not onlyPlotting:
        for x in ['charm','10GeV','1GeV']:
            for c in ['','charm','beauty']:
                ut.bookHist(h,'trueMom-'+x+c,'true MC momentum;#it{p} [GeV/c];#it{p}_{T} [GeV/c]',500,0.,500.,200,0.,10.)
                ut.bookHist(h,'recoMom-'+x+c,'reco MC momentum;#it{p} [GeV/c];#it{p}_{T} [GeV/c]',500,0.,500.,200,0.,10.)
        if Nevents<0: Nevents = sTree.GetEntries()
        for n in range(Nevents):
            rc = sTree.GetEvent(n)  
            fname = sTree.GetCurrentFile().GetName()
            x = '1GeV'
            if not fname.find('charm')<0: x = 'charm'
            elif not fname.find('pythia8_Geant4_10.0')<0: 
              x = '10GeV'
              if sTree.channel==5: x+='charm'
              if sTree.channel==6: x+='beauty'
            if sTree.MCRecoDT.size() != 1: continue # look at 1 Track events for the moment
            for d in sTree.MCRecoDT:
                i = 0
                P  = ROOT.TVector3(sTree.MCRecoDTpx[i],sTree.MCRecoDTpy[i],sTree.MCRecoDTpz[i])
                found = False
                for t in range(sTree.nTr):
                    Preco  = ROOT.TVector3(sTree.Px[t],sTree.Py[t],sTree.Pz[t])
                    if abs(sTree.Delx[t])<cuts['muTrackMatchX'] and abs(sTree.Dely[t])<cuts['muTrackMatchY']:
                        rc = h['trueMom-'+x].Fill(P.Mag(),P.Pt())
                        rc = h['recoMom-'+x].Fill(Preco.Mag(),Preco.Pt())
                        break
        for x in ['trueMom-','recoMom-']:
            h[x+'10GeVnorm']=h[x+'10GeV'].Clone(x+'10GeVnorm')
            h[x+'10GeVnorm'].Add(h[x+'10GeVcharm'],charmNorm[10])
            h[x+'10GeVnorm'].Add(h[x+'10GeVbeauty'],beautyNorm[10])
            h[x+'10GeVnorm'].Scale(sim10fact)
            h[x+'1GeVnorm']=h[x+'1GeV'].Clone(x+'1GeVnorm')
            h[x+'1GeVnorm'].Add(h[x+'charm'],charmNorm[1])
            h[x+'P1GeVnorm'] =h[x+'1GeVnorm'].ProjectionX(x+'P1GeVnorm')
            h[x+'P10GeVnorm']=h[x+'10GeVnorm'].ProjectionX(x+'P10GeVnorm')
            h[x+'P']=h[x+'P10GeVnorm'].Clone(x+'P')
            for i in range(1,20): 
                h[x+'P'].SetBinContent(i,h[x+'P1GeVnorm'].GetBinContent(i))
                h[x+'P'].SetBinError(i,h[x+'P1GeVnorm'].GetBinError(i))
            for i in range(20,401): 
                h[x+'P'].SetBinContent(i,h[x+'P10GeVnorm'].GetBinContent(i))
                h[x+'P'].SetBinError(i,h[x+'P10GeVnorm'].GetBinError(i))
            h[x+'Pt1GeVnorm'] =h[x+'1GeVnorm'].ProjectionY(x+'Pt1GeVnorm',1,20)
            h[x+'Pt10GeVnorm']=h[x+'10GeVnorm'].ProjectionY(x+'Pt10GeVnorm',21,400)
            h[x+'Pt']=h[x+'Pt10GeVnorm'].Clone(x+'Pt')
            h[x+'Pt'].Add(h[x+'Pt1GeVnorm'])
        ut.writeHists(h,'trueMoms-'+MCType+'.root')
    else:
        ut.readHists(h,'trueMoms-repro.root')
        ut.readHists(h0,'trueMoms-0.root')
        for k in ['P','Pt']:
            t = "true Mom "+k
            if not h.has_key(t): ut.bookCanvas(h,t,'true and reco momentum',900,600,1,1)
            tc=h[t].cd(1)
            tc.SetLogy()
            h['trueMom-'+k].SetStats(0)
            #h['trueMom-'+k].Draw()
            h['rebinned-trueMom-'+k]=h['trueMom-'+k].Clone('rebinned-trueMom-'+k)
            h['rebinned-trueMom-'+k].Rebin(5)
            h['rebinned-trueMom-'+k].Scale(1./5.)
            h['rebinned-trueMom-'+k].SetMarkerStyle(21)
            h['rebinned-trueMom-'+k].SetMarkerColor(h['rebinned-trueMom-'+k].GetLineColor())
            if k=='P': 
                 h['rebinned-trueMom-'+k].GetXaxis().SetRangeUser(5.,400.)
                 h['rebinned-trueMom-'+k].SetTitle(';#it{p} [GeV/c]' )
            else: 
                 h['rebinned-trueMom-'+k].SetTitle(';#it{p}_{T} [GeV/c]' )
            h['rebinned-trueMom-'+k].Draw()
            h['recoMom-'+k].SetLineColor(ROOT.kMagenta)
            h['recoMom-'+k].SetStats(0)
            #h['recoMom-'+k].Draw('same')
            h['rebinned-recoMom-'+k]=h['recoMom-'+k].Clone('rebinned-recoMom-'+k)
            h['rebinned-recoMom-'+k].Rebin(5)
            h['rebinned-recoMom-'+k].Scale(1./5.)
            h['rebinned-recoMom-'+k].SetMarkerStyle(23)
            h['rebinned-recoMom-'+k].SetMarkerColor(h['rebinned-recoMom-'+k].GetLineColor())
            h['rebinned-recoMom-'+k].Draw('P same')
            h0['recoMom-'+k].SetLineColor(ROOT.kGreen)
            h0['recoMom-'+k].SetStats(0)
            #h0['recoMom-'+k].Draw('same')
            h0['0rebinned-recoMom-'+k]=h0['recoMom-'+k].Clone('0rebinned-recoMom-'+k)
            # bypass issue with different number of tracks in sim files with 270mu, -0 and 350mu -repro
            rescale = h['recoMom-'+k].GetSumOfWeights()/h0['recoMom-'+k].GetSumOfWeights()
            print "rescale ",'0rebinned-recoMom-'+k,rescale,h['recoMom-'+k].GetSumOfWeights(),h0['recoMom-'+k].GetSumOfWeights()
            h0['0rebinned-recoMom-'+k].Scale( rescale )
            h0['0rebinned-recoMom-'+k].Rebin(5)
            h0['0rebinned-recoMom-'+k].Scale(1./5.)
            h0['0rebinned-recoMom-'+k].SetMarkerStyle(22)
            h0['0rebinned-recoMom-'+k].SetMarkerColor(h0['0rebinned-recoMom-'+k].GetLineColor())
            h0['0rebinned-recoMom-'+k].Draw('P same')
            h['leg'+t]=ROOT.TLegend(0.31,0.67,0.85,0.85)
            h['leg'+t].SetEntrySeparation(0.35)
            h['leg'+t].AddEntry(h['rebinned-trueMom-'+k],'true momentum ','PL')
            h['leg'+t].AddEntry(h0['0rebinned-recoMom-'+k],'reconstructed momentum #sigma_{hit}=270#mum','PL')
            h['leg'+t].AddEntry(h['rebinned-recoMom-'+k],'reconstructed momentum #sigma_{hit}=350#mum','PL')
            h['leg'+t].Draw()
            myPrint(h[t],'True-Reco'+k)
def yBeam2(Mproton = 0.938272081, pbeam = 400.):
   # Carlos Lourenco, private communication
   # this is an approximation, with Ebeam ~ pbeam and Ebeam/Mpr >> 1
    Ebeam   = ROOT.TMath.Sqrt(pbeam**2+Mproton**2)
    beta    = pbeam/Ebeam # p/E 
    sqrtS   = ROOT.TMath.Sqrt(2*Mproton**2+2*Ebeam*Mproton)
    y_beam  = ROOT.TMath.Log(sqrtS/Mproton)   
    return y_beam
def yBeam(Mproton = 0.938272081, pbeam = 400.):
    Ebeam   = ROOT.TMath.Sqrt(pbeam**2+Mproton**2)
    betaCM  = pbeam / (Ebeam + Mproton)
    y_beam  = 0.5*ROOT.TMath.Log( (1+betaCM)/(1-betaCM))   # https://arxiv.org/pdf/1604.02651.pdf 
    return y_beam
def mufluxReco(sTree,h,nseq=0,ncpus=False):
    y_beam = yBeam()
    cuts = {'':0,'Chi2<':0.7,'Dely<':5,'Delx<':2,'All':1}
    ut.bookHist(h,'Trscalers','scalers for track counting',20,0.5,20.5)
    for c in cuts:
        for x in ['','mu']:
            for s in ["","Decay","Hadronic inelastic","Lepton pair","Positron annihilation","charm","beauty","Di-muon P8","invalid"]:
                ut.bookHist(h,c+'p/pt'+x+s,'momentum vs Pt (GeV);#it{p} [GeV/c]; #it{p}_{T} [GeV/c]',500,0.,500.,100,0.,10.)
                ut.bookHist(h,c+'y'+x+s,'rapidity cm; y_{CM}',500,-1.,5.,100,0.,500.,50,0.,10.)
                ut.bookHist(h,c+'p/px'+x+s,'momentum vs Px (GeV);#it{p} [GeV/c]; #it{p}_{X}[GeV/c]',500,0.,500.,200,-10.,10.)
                ut.bookHist(h,c+'p/Abspx'+x+s,'momentum vs Px (GeV);#it{p}_{T} [GeV/c]; #it{p}_{X} [GeV/c]',500,0.,500.,100,0.,10.)
                ut.bookHist(h,c+'pz/Abspx'+x+s,'Pz vs Px (GeV);#it{p} [GeV/c]; #it{p}_{X} [GeV/c]',500,0.,500.,100,0.,10.)
                ut.bookHist(h,c+'p/pxy'+x+s,'momentum vs Px (GeV);#it{p} [GeV/c]; #it{p}_{X} [GeV/c]',500,0.,500.,200,-10.,10.)
                ut.bookHist(h,c+'p/Abspxy'+x+s,'momentum vs Px (GeV) tagged RPC X;#it{p} [GeV/c]; #it{p}_{X} [GeV/c]',500,0.,500.,100,0.,10.)
                ut.bookHist(h,c+'pz/Abspxy'+x+s,'Pz vs Px (GeV) tagged RPC X;#it{p} [GeV/c]; #it{p}_{X} [GeV/c]',500,0.,500.,100,0.,10.)
                ut.bookHist(h,c+'TrackMult'+x+s,'track multiplicity',10,-0.5,9.5)
                ut.bookHist(h,c+'chi2'+x+s,'chi2/nDoF',100,0.,10.)
                ut.bookHist(h,c+'Nmeasurements'+x+s,'number of measurements used',25,-0.5,24.5)
                ut.bookHist(h,c+'xy'+x+s,'xy of first state;x [cm];y [cm]',100,-30.,30.,100,-30.,30.)
                ut.bookHist(h,c+'pxpy'+x+s,'px/pz py/pz of first state',100,-0.2,0.2,100,-0.2,0.2)
                ut.bookHist(h,c+'p1/p2'+x+s,'momentum p1 vs p2;#it{p} [GeV/c]; #it{p} [GeV/c]',500,0.,500.,500,0.,500.)
                ut.bookHist(h,c+'pt1/pt2'+x+s,'P_{T} 1 vs P_{T} 2;#it{p} [GeV/c]; #it{p} [GeV/c]',100,0.,10.,100,0.,10.)
                ut.bookHist(h,c+'p1/p2s'+x+s,'momentum p1 vs p2 same sign;#it{p} [GeV/c]; #it{p} [GeV/c]',500,0.,500.,500,0.,500.)
                ut.bookHist(h,c+'pt1/pt2s'+x+s,'P_{T} 1 vs P_{T} 2 same sign;#it{p} [GeV/c]; #it{p} [GeV/c]',100,0.,10.,100,0.,10.)
                ut.bookHist(h,c+'Chi2/DoF'+x+s,'Chi2/DoF',100,0.,5.,100,0.,500.)
                ut.bookHist(h,c+'DoF'+x+s,     'DoF'     ,30,0.5,30.5,100,0.,500.)
                ut.bookHist(h,c+'R'+x+s,'rpc match',100,0.,10.,100,0.,500.)
                ut.bookHist(h,c+'RPCResX/Y'+x+s,'RPC residuals',200,0.,200.,200,0.,200.)
                ut.bookHist(h,c+'RPCMatch'+x+s,'RPC matching',100,0.,10.,100,0.,10.)
                ut.bookHist(h,c+'trueMom'+x+s,'true MC momentum;#it{p} [GeV/c];#it{p}_{T} [GeV/c]',500,0.,500.,100,0.,10.)
                ut.bookHist(h,c+'recoMom'+x+s,'reco MC momentum;#it{p} [GeV/c];#it{p}_{T} [GeV/c]',500,0.,500.,100,0.,10.)
                ut.bookHist(h,c+'truePz/Abspx'+x+s,'true MC momentum;#it{p} [GeV/c];#it{p}_{X} [GeV/c]',500,0.,500.,100,0.,10.)
                ut.bookHist(h,c+'recoPz/Abspx'+x+s,'reco MC momentum;#it{p} [GeV/c];#it{p}_{X} [GeV/c]',500,0.,500.,100,0.,10.)
                ut.bookHist(h,c+'momResol'+x+s,'momentum resolution function of momentum;#it{p} [GeV/c];#sigma P/P', 200,-0.5,0.5,40,0.,400.)
#
    MCdata = False
    if sTree.FindBranch("MCRecoDT"): MCdata = True
#
    Ntotal = sTree.GetEntries()
    nStart = 0
    if ncpus:
      ncpus = int(ncpus)
      nseq = int(nseq)
      deltaN = (sTree.GetEntries()+0.5)//ncpus
      nStart = int(nseq*deltaN)
      Ntotal = int(min(sTree.GetEntries(),nStart+deltaN))
    for n in range(nStart,Ntotal):
        rc = sTree.GetEvent(n)
        if n%500000==0: print 'now at event ',n,'of',Ntotal,time.ctime()
        h['Trscalers'].Fill(1)
        if len(sTree.GoodTrack)>0: h['Trscalers'].Fill(2)
        tchannel = sTree.channel
        source = ''
        if MCdata:
            if (tchannel == 1):  source = "Decay"
            if (tchannel == 7):  source = "Di-muon P8"
            if (tchannel == 2):  source = "Hadronic inelastic"
            if (tchannel == 3):  source = "Lepton pair"
            if (tchannel == 4):  source = "Positron annihilation"
            if (tchannel == 5):  source = "charm"
            if (tchannel == 6):  source = "beauty"
            if (tchannel == 13): source = "invalid"
        muonTaggedTracks = {}
        for k in range(len(sTree.GoodTrack)):
            h['Trscalers'].Fill(3)
            if sTree.GoodTrack[k]<0: continue
            h['Trscalers'].Fill(4)
            muTagged  = False
            muTaggedX = False
            clone     = False
            if sTree.GoodTrack[k]%2==1: 
                muTaggedX = True
                if int(sTree.GoodTrack[k]/10)%2==1: muTagged = True
            if sTree.GoodTrack[k]>999:  clone = True
            if clone: continue
            R = (sTree.Dely[k]/3.)**2+(sTree.Delx[k]/1.5)**2
            p = ROOT.TVector3(sTree.Px[k],sTree.Py[k],sTree.Pz[k])
            rc = h['R'].Fill(R,p.Mag())
            rc = h['RPCMatch'].Fill(sTree.Delx[k],sTree.Dely[k])
            okCuts = ['']
            muonTaggedTracks['']=[]
            if sTree.Chi2[k]<cuts['Chi2<']: okCuts.append('Chi2<')
            if sTree.Dely[k]<cuts['Dely<']: okCuts.append('Dely<')
            if sTree.Delx[k]<cuts['Delx<']: okCuts.append('Delx<')
            if sTree.Chi2[k]<cuts['Chi2<'] and sTree.Dely[k]<cuts['Dely<'] and sTree.Delx[k]<cuts['Delx<']: okCuts.append('All')
            for c in okCuts:
                LV = ROOT.Math.PxPyPzMVector(p.X(),p.Y(),p.Z(),muonMass)
                y  = LV.Rapidity()-y_beam
                h[c+"p/pt"].Fill(p.Mag(),p.Pt())
                h[c+"y"].Fill(y,p.Mag(),p.Pt())
                h[c+"p/Abspx"].Fill(p.Mag(),abs(p.x()))
                h[c+"pz/Abspx"].Fill(p.z(),abs(p.x()))
                h[c+"xy"].Fill(sTree.x[k],sTree.y[k])
                h[c+"pxpy"].Fill(p.x()/p.z(),p.y()/p.z())
                h[c+'Chi2/DoF'].Fill(sTree.Chi2[k],p.Mag())
                h[c+'DoF'].Fill(sTree.nDoF[k],p.Mag())
                if p.Mag()>300. and Debug: 
                    occ = sTree.stationOcc[1]+sTree.stationOcc[2]+sTree.stationOcc[5]+sTree.stationOcc[6]
                    print n, p.Mag(),occ,sTree.GoodTrack[k],sTree.Chi2[k],sTree.nDoF[k]
                if source != '':
                    h[c+"p/pt"+source].Fill(p.Mag(),p.Pt())
                    h[c+"y"+source].Fill(y,p.Mag(),p.Pt())
                    h[c+"p/px"+source].Fill(p.Mag(),p.x())
                    h[c+"p/Abspx"+source].Fill(p.Mag(),abs(p.x()))
                    h[c+"pz/Abspx"+source].Fill(p.z(),abs(p.x()))
                    h[c+"xy"+source].Fill(sTree.x[k],sTree.y[k])
                    h[c+"pxpy"+source].Fill(p.x()/p.z(),p.y()/p.z())
                    h[c+'R'+source].Fill(R,p.Mag())
                    h[c+'Chi2/DoF'+source].Fill(sTree.Chi2[k],p.Mag())
                    h[c+'DoF'+source].Fill(sTree.nDoF[k],p.Mag())
                h[c+'RPCResX/Y'].Fill(sTree.Delx[k],sTree.Dely[k])
                if (muTaggedX): # within ~3sigma  X from mutrack
                    h[c+"p/pxmu"].Fill(p.Mag(),p.x())
                    h[c+"p/Abspxmu"].Fill(p.Mag(),abs(p.x()))
                    h[c+"pz/Abspxmu"].Fill(p.z(),abs(p.x()))
                    if source != '':
                        h[c+"p/pxmu"+source].Fill(p.Mag(),p.x())
                        h[c+"p/Abspxmu"+source].Fill(p.Mag(),abs(p.x()))
                        h[c+"pz/Abspxmu"+source].Fill(p.z(),abs(p.x()))
                if (muTagged): #  within ~3sigma  X,Y from mutrack
                    if c=='': muonTaggedTracks[''].append(k)
                    h[c+"p/ptmu"].Fill(p.Mag(),p.Pt())
                    h[c+"ymu"].Fill(y,p.Mag(),p.Pt())
                    h[c+"p/pxymu"].Fill(p.Mag(),p.x())
                    h[c+"p/Abspxymu"].Fill(p.Mag(),abs(p.x()))
                    h[c+"pz/Abspxymu"].Fill(p.z(),abs(p.x()))
                    h[c+"xymu"].Fill(sTree.x[k],sTree.y[k])
                    h[c+"pxpymu"].Fill(p.x()/p.z(),p.y()/p.z())
                    h[c+'Rmu'].Fill(R,p.Mag())
                    h[c+'Chi2/DoFmu'].Fill(sTree.Chi2[k],p.Mag())
                    h[c+'DoFmu'].Fill(sTree.nDoF[k],p.Mag())
                    if source != '':
                        h[c+"p/ptmu"+source].Fill(p.Mag(),p.Pt())
                        h[c+"ymu"+source].Fill(y,p.Mag(),p.Pt())
                        h[c+"p/pxymu"+source].Fill(p.Mag(),p.x())
                        h[c+"p/Abspxymu"+source].Fill(p.Mag(),abs(p.x()))
                        h[c+"pz/Abspxymu"+source].Fill(p.z(),abs(p.x()))
                        h[c+"xymu"+source].Fill(sTree.x[k],sTree.y[k])
                        h[c+"pxpymu"+source].Fill(p.x()/p.z(),p.y()/p.z())
                        h[c+'Rmu'+source].Fill(R,p.Mag())
                        h[c+'Chi2/DoFmu'+source].Fill(sTree.Chi2[k],p.Mag())
                        h[c+'DoFmu'+source].Fill(sTree.nDoF[k],p.Mag())
#
                if len(muonTaggedTracks[''])==2:
                    a,b=muonTaggedTracks[''][0],muonTaggedTracks[''][1]
                    pA=ROOT.TVector3(sTree.Px[a],sTree.Py[a],sTree.Pz[a])
                    pB=ROOT.TVector3(sTree.Px[b],sTree.Py[b],sTree.Pz[b])
                    prodSign = sTree.Sign[a]*sTree.Sign[b]
                    if prodSign<0:
                        h["p1/p2"].Fill(pA.Mag(),pB.Mag())
                        h["pt1/pt2"].Fill(pA.Pt(),pB.Pt())
                        if source != '':
                            h["p1/p2"+source].Fill(pA.Mag(),pB.Mag())
                            h["pt1/pt2"+source].Fill(pA.Pt(),pB.Pt())
                    else:
                        h["p1/p2s"].Fill(pA.Mag(),pB.Mag())
                        h["pt1/pt2s"].Fill(pA.Pt(),pB.Pt())
                        if source != '':
                            h["p1/p2s"+source].Fill(pA.Mag(),pB.Mag())
                            h["pt1/pt2s"+source].Fill(pA.Pt(),pB.Pt())
# mom resolution
                if MCdata and len(sTree.GoodTrack)==1 and len(sTree.MCRecoDTpx)==1:
                    trueMom = ROOT.TVector3(sTree.MCRecoDTpx[0],sTree.MCRecoDTpy[0],sTree.MCRecoDTpz[0])
                    h["trueMom"].Fill(trueMom.Mag(),trueMom.Pt())
                    h["recoMom"].Fill(p.Mag(),p.Pt())
                    h["truePz/Abspx"].Fill(trueMom[2],ROOT.TMath.Abs(trueMom[0]))
                    h["recoPz/Abspx"].Fill(p[2],ROOT.TMath.Abs(p[0]))
                    h["momResol"].Fill((p.Mag()-trueMom.Mag())/trueMom.Mag(),trueMom.Mag())
                    if source != '':
                        h["trueMom"+source].Fill(trueMom.Mag(),trueMom.Pt());
                        h["recoMom"+source].Fill(p.Mag(),p.Pt());
                        h["truePz/Abspx"+source].Fill(trueMom[2],ROOT.TMath.Abs(trueMom[0]));
                        h["recoPz/Abspx"+source].Fill(p[2],ROOT.TMath.Abs(p[0]));
                        h["momResol"+source].Fill((p.Mag()-trueMom.Mag())/trueMom.Mag(),trueMom.Mag());
    if not MCdata : tmp = 'RUN_8000'+fdir.split('RUN_8000')[1]
    else : 
      tmp = fdir
      if withCharm : tmp+='-charm'
    outFile = 'sumHistos-'+'-'+tmp+'.root'
    if options.refit: outFile = 'sumHistos-'+'-'+tmp+'_refit.root'
    if ncpus:
       outFile=outFile.replace('.root','-'+str(nseq)+'.root')
    ut.writeHists( h,outFile)
    print "I have finished. ",outFile
def dEdxCorrection(p):
 # +7.3    # most probably ~7.5, mean 6.9.
 # -8.1 - 0.045 *p + 0.00017 *p*p fit without cut
 dE = -7.63907  -0.0315131  * p + 0.000168569 * p*p
 return -dE*(1-0.085)  # fudge factor reversed engineering
#
def DrellYan(ptCut = 1.0, pmin = 20.,pmax  = 300.,BDTCut=None,muID=2):
   tag  = 'muID'+str(muID)+'_'+'DrellYan-'+str(ptCut)+'_'+str(pmin)
   if BDTCut: tag += '_BDT'
   theCut = theJpsiCut('mcor',True,ptCut,pmin,pmax,muID,False)
   ut.bookHist(hMC,'DY_M','Drell Yan',100,0.0,5.0,100,0.,10.)
   ROOT.gROOT.cd()
   hMC['10GeV'].Draw('mcor:ptcor>>DY_M',theCut+"&&Jpsi<-21&&Jpsi>-23")

def trueMass():
   ut.bookHist(h,'M','M',100,-2.,3.,1000,0.,100.)
   ut.bookHist(h,'zM','M',100,-2.,3.,1000,0.,5.)
   for x in h:
     if x.find('M')<0: continue
     h[x].Reset()
   for nt in hMC['10GeV']:
     #if nt.Jpsi!=223: continue
     #if nt.Jpsi!=113: continue
     #if abs(nt.Jpsi)<10: continue
     if abs(nt.p1x-nt.p2x)<0.001: continue 
     if not h.has_key('M_'+str(nt.procID)):
           h['M_'+str(nt.procID)]=h['M'].Clone('M_'+str(nt.procID))
           h['zM_'+str(nt.procID)]=h['zM'].Clone('zM_'+str(nt.procID))
     m0 = ROOT.Math.PxPyPzMVector(nt.p1x,nt.p1y,nt.p1z,muonMass)
     m1 = ROOT.Math.PxPyPzMVector(nt.p2x,nt.p2y,nt.p2z,muonMass)
     G = m0+m1
     rc=h['M_'+str(nt.procID)].Fill(G.Rapidity()-3.3741642051118204,G.M())
     rc=h['zM_'+str(nt.procID)].Fill(G.Rapidity()-3.3741642051118204,G.M())
     rc=h['M'].Fill(G.Rapidity()-3.3741642051118204,G.M())
     rc=h['zM'].Fill(G.Rapidity()-3.3741642051118204,G.M())

def invMass(sTree,h,nseq=0,ncpus=False):
    ut.bookHist(h,'invMassSS','inv mass ',100,0.0,10.0)
    ut.bookHist(h,'invMassOS','inv mass ',100,0.0,10.0)
    ut.bookHist(h,'invMassJ','inv mass from Jpsi',100,0.0,10.0)
    ut.bookHist(h,'p/pt','p/pt',100,0.0,400.0,100,0.0,10.0)
    ut.bookHist(h,'p/ptJ','p/pt of Jpsi',100,0.0,400.0,100,0.0,10.0)
    ut.bookHist(h,'p/ptmu','p/pt of mu',100,0.0,400.0,100,0.0,10.0)
    ut.bookHist(h,'p/ptmuJ','p/pt of mu from Jpsi',100,0.0,400.0,100,0.0,10.0)
    MCdata = False
    if sTree.FindBranch("MCRecoDT"): MCdata = True
    if MCdata:
       name = "ntuple-invMass-MC.root"
       if ncpus:
          name = name.replace('.root','-'+str(nseq)+'.root')
    else:      
       name = "ntuple-invMass-"+fdir.split('/')[7]+'.root'
    if options.refit: name = name.replace('.root','_refit.root')
    h['fntuple']  = ROOT.TFile.Open(name, 'RECREATE')
    variables = "mult:m:mcor:mcor2:y:ycor:p:pcor:pt:ptcor:muID1:p1:pt1:p1cor:pt1cor:muID2:p2:pt2:p2cor:pt2cor:Ip1:Ip2:chi21:chi22:cosTheta:cosCSraw:cosCScor:\
    prec1x:prec1y:prec1z:prec2x:prec2y:prec2z:rec1x:rec1y:rec1z:rec2x:rec2y:rec2z:RPCx1:RPCy1:Delx1:Dely1:RPCx2:RPCy2:Delx2:Dely2"
    if MCdata:
      variables += ":Jpsi:procID:procID2:PTRUE:PtTRUE:YTRUE:p1True:p2True:dTheta1:dTheta2:dMults1:dMults2:originZ1:originZ2:p1x:p1y:p1z:p2x:p2y:p2z:ox:oy:oz:Pmother"
    h['nt']  = ROOT.TNtuple("nt","dimuon",variables) 
#
    sTreeFullMC = None
    Ntotal = sTree.GetEntries()
    nStart = 0
    if ncpus:
      ncpus = int(ncpus)
      nseq = int(nseq)
      deltaN = (sTree.GetEntries()+0.5)//ncpus
      nStart = int(nseq*deltaN)
      Ntotal = int(min(sTree.GetEntries(),nStart+deltaN))
    currentFile = ''
    for n in range(0,Ntotal):
        rc = sTree.GetEvent(n)
        # if n%500000==0: print 'now at event ',n,'of',Ntotal,time.ctime()
        if sTree.GetCurrentFile().GetName()!=currentFile:
            currentFile = sTree.GetCurrentFile().GetName()
            nInFile = n
        if n<nStart: continue
        tchannel = sTree.channel
        source = ''
        if MCdata:
            if (tchannel == 1):  source = "Decay"
            if (tchannel == 7):  source = "Di-muon P8"
            if (tchannel == 2):  source = "Hadronic inelastic"
            if (tchannel == 3):  source = "Lepton pair"
            if (tchannel == 4):  source = "Positron annihilation"
            if (tchannel == 5):  source = "charm"
            if (tchannel == 6):  source = "beauty"
            if (tchannel == 13): source = "invalid"
        P     = {-1:ROOT.Math.PxPyPzMVector()}
        IP    = {-1:-999.}
        Pcor  = {-1:ROOT.Math.PxPyPzMVector()}
        Pcor2 = {-1:ROOT.Math.PxPyPzMVector()}
        muID  = {-1:0}
        for k in range(len(sTree.GoodTrack)):
            if sTree.GoodTrack[k]<0:    continue
            if sTree.GoodTrack[k]>999:  continue
            muID[k] = sTree.GoodTrack[k]
            P[k] = ROOT.Math.PxPyPzMVector(sTree.Px[k],sTree.Py[k],sTree.Pz[k],muonMass)
            l = (sTree.z[k] - zTarget)/(sTree.Pz[k]+ 1E-19)
            x = sTree.x[k]+l*sTree.Px[k]
            y = sTree.y[k]+l*sTree.Py[k]
            IP[k] = ROOT.TMath.Sqrt(x*x+y*y)
# make dE correction plus direction from measured point
            dline   = ROOT.TVector3(sTree.x[k],sTree.y[k],sTree.z[k]-zTarget)
            Ecor = P[k].E()+dEdxCorrection(P[k].P())
            norm = dline.Mag()
            Pcor[k]  = ROOT.Math.PxPyPzMVector(Ecor*dline.X()/norm,Ecor*dline.Y()/norm,Ecor*dline.Z()/norm,muonMass)
            Pcor2[k] = ROOT.Math.PxPyPzMVector(P[k].P()*dline.X()/norm,P[k].P()*dline.Y()/norm,P[k].P()*dline.Z()/norm,muonMass)
# now we have list of selected tracks, P.keys()
        if len(P)<2 and not withJpsi: continue
        X      =  {0:ROOT.Math.PxPyPzMVector()}
        Xcor   =  {0:ROOT.Math.PxPyPzMVector()}
        Xcor2  =  {0:ROOT.Math.PxPyPzMVector()}
        jpsi   =  {0:-1}
        pTrue  =  {0:[ROOT.TVector3(0,0,-9999.),ROOT.TVector3(0,0,-9999.)]}
        dTheta =  {0:[-9999.,-9999.]}
        dMults =  {0:[-9999.,-9999.]}
        originZ = {0:[-9999.,-9999.]}
        PTRUE  =  {0:-1}
        PtTRUE =  {0:-1}
        YTRUE  =  {0:-999}
        costheta = {0:-999.}
        chi2     = {0:[-999.,-999.]}
        nComb    = {0:[-1,-1]}
        Pmother  = {0:0}
        j = 0
        pDict = P.keys()
        pDict.remove(-1)
        for l1 in range(len(pDict)-1):
         for l2 in range(l1+1,len(pDict)):
          n1 = pDict[l1]
          n2 = pDict[l2]
# for jpsi MC only take truth matched combinations
          if withJpsi:
            if sTreeMC.MCID[n1]<0 or sTreeMC.MCID[n2]<0: continue
          X[j]    = P[n1]+P[n2]
          Xcor[j] = Pcor[n1]+Pcor[n2]
          Xcor2[j] = Pcor2[n1]+Pcor2[n2]
# angle between two tracks in Jpsi rest frame
          b = X[j].BoostToCM()
          moth_boost = ROOT.Math.Boost(b.x(),b.y(),b.z())
          Pcms = moth_boost*P[n1]
          v0=ROOT.TVector3(Pcms.X(),Pcms.Y(),Pcms.Z())
          v1=ROOT.TVector3(X[j].X(),X[j].Y(),X[j].Z())
          costheta[j] = v0.Dot(v1)/( v0.Mag()*v1.Mag() + 1E-19)
          if sTree.Sign[n1]*sTree.Sign[n2]<0:  rc = h["invMassOS"].Fill(X[j].M())
          else:                                rc = h["invMassSS"].Fill(X[j].M())
          chi2[j] = [sTree.Sign[n1]*sTree.Chi2[n1],sTree.Sign[n2]*sTree.Chi2[n2]]
          if X[j].M()>2.5 and X[j].M()<4.0:
             rc = h["p/pt"].Fill(X[j].P(),X[j].Pt())
             rc = h["p/ptmu"].Fill(P[n1].P(),P[n2].Pt())
             rc = h["p/ptmu"].Fill(P[n1].P(),P[n2].Pt())
          jpsi[j] = -1
          originZ[j]  = [-9999.,-9999.]
          pTrue[j]    = [ROOT.TVector3(0,0,-9999.),ROOT.TVector3(0,0,-9999.)]
          dTheta[j] = [-9999.,-9999.]
          dMults[j] = [-9999.,-9999.]
          PTRUE[j]  = -1.
          PtTRUE[j] = -1.
          YTRUE[j]  = -999.
          nComb[j]=[n1,n2]
          j+=1
#check truth
        if MCdata:
          eospathSim = os.environ['EOSSHIP']+'/eos/experiment/ship/user/truf/muflux-sim/'
          fname = sTree.GetCurrentFile().GetName().replace('ntuple-','')
          if sTreeFullMC:
            if sTreeFullMC.GetCurrentFile().GetName().find(fname)<0:
                fMC = ROOT.TFile.Open(fname)
                sTreeFullMC = fMC.cbmsim
          else: 
            fMC = ROOT.TFile.Open(fname)
            sTreeFullMC = fMC.cbmsim
          rc = sTreeFullMC.GetEvent(n-nInFile)

          for j in nComb:
            mothers = []
            mJpsi  =  -1
            if withJpsi:
               for m in sTreeFullMC.MCTrack:
                  mJpsi += 1
                  if m.GetPdgCode()==443:
                     PTRUE[j]  = m.GetP()
                     PtTRUE[j] = m.GetPt()
                     YTRUE[j]  = m.GetRapidity()
                     Pmother[j]  = sTreeFullMC.MCTrack[m.GetMotherId()].GetP()
            if nComb[j][0]<0: continue  # no reco Jpsi
            kx = 0
            for k in [nComb[j][0],nComb[j][1]]:
                if sTreeMC.MCID[k]<0: continue
                if sTreeMC.MCID[k] > sTreeFullMC.MCTrack.GetEntries()-1:
                   print "ERROR: wrong MC track index",sTreeFullMC.GetCurrentFile().GetName(),k,sTreeMC.MCID[k],n-nInFile
                   print "                           ",sTreeMC.GetCurrentFile().GetName(),n
                   continue
                trueMu = sTreeFullMC.MCTrack[sTreeMC.MCID[k]]
                mother = sTreeFullMC.MCTrack[trueMu.GetMotherId()]
                mothers.append(mother.GetPdgCode())
                if withJpsi and mJpsi != mother and j==0:
# mu mu combination does not point to correct Jpsi, don't overwrite true one
                    PTRUE[j]=-PTRUE[j]
                else:
                    PTRUE[j]  = mother.GetP()
                    PtTRUE[j] = mother.GetPt()
                    YTRUE[j]  = mother.GetRapidity()
                    if not mother.GetMotherId()<0:
                        Pmother[j]  = sTreeFullMC.MCTrack[mother.GetMotherId()].GetP()
# check multiple scattering
                trueMu.GetMomentum(pTrue[j][kx])
                originZ[j][kx] = trueMu.GetStartZ()
                dline   = ROOT.TVector3(sTree.x[k],sTree.y[k],sTree.z[k]-zTarget)
                dTheta[j][kx]  = pTrue[j][kx].Dot(dline)/(pTrue[j][kx].Mag()*dline.Mag())
                prec = ROOT.TVector3(P[k].Px(),P[k].Py(),P[k].Pz())
                dMults[j][kx]  = pTrue[j][kx].Dot(prec)/(pTrue[j][kx].Mag()*prec.Mag())
                kx+=1
            if len(mothers)==2: 
             if mothers[0]==mothers[1]:
                 jpsi[j] = mothers[0]
             if abs(mothers[0]) == abs(mothers[1]) and abs(mothers[0])==13:
                 mu0  = sTreeMC.MCID[nComb[j][0]]
                 while abs(sTreeFullMC.MCTrack[mu0].GetPdgCode()) == 13:
                    mu0=sTreeFullMC.MCTrack[mu0].GetMotherId()
                 mu1  = sTreeMC.MCID[nComb[j][1]]
                 while abs(sTreeFullMC.MCTrack[mu1].GetPdgCode()) == 13:
                    mu1=sTreeFullMC.MCTrack[mu1].GetMotherId()
                 if mu1==mu0:
                    jpsi[j] = -sTreeFullMC.MCTrack[mu0].GetPdgCode()
            if jpsi[j] == 443:
                rc = h["invMassJ"].Fill(X[j].M())
                rc = h["p/ptJ"].Fill(X[j].P(),X[j].Pt())
                rc = h["p/ptmuJ"].Fill(P[n1].P(),P[n1].Pt())
                rc = h["p/ptmuJ"].Fill(P[n2].P(),P[n2].Pt())
                if Debug:
                 trueMu = sTreeFullMC.MCTrack[sTreeMC.MCID[n1]]
                 mother = sTreeFullMC.MCTrack[trueMu.GetMotherId()]
                 print X[j].M(),n,n-nInFile,sTree.GetCurrentFile()
                 print 'origin',mother.GetStartX(),mother.GetStartY(),mother.GetStartZ()
# now we have all combinations, j
        for j in nComb:
          n1 = nComb[j][0]
          n2 = nComb[j][1]
          if n1<0:
            cosCSraw,cosCScor       = -999.,-999.
            Y,Ycor                  = -999.,-999.
            xn1,yn1,zn1,xn2,yn2,zn2 = 0,0,0,0,0,0
            RPCx1,RPCy1,Delx1,Dely1,RPCx2,RPCy2,Delx2,Dely2 = -999.,-999.,-999.,-999.,-999.,-999.,-999.,-999.
          else:
            if chi2[j][0] < 0: 
              nlep      = n1
              nantilep  = n2
            else: 
              nlep = n2
              nantilep  = n1
            P1pl = P[nlep].E()+P[nlep].Pz()
            P2pl = P[nantilep].E()+P[nantilep].Pz()
            P1mi = P[nlep].E()-P[nlep].Pz()
            P2mi = P[nantilep].E()-P[nantilep].Pz()
            cosCSraw = X[j].Pz()/abs(X[j].Pz()) * 1./X[j].M()/ROOT.TMath.Sqrt(X[j].M2()+X[j].Pt()**2)*(P1pl*P2mi-P2pl*P1mi)
            P1pl = Pcor[nlep].E()+Pcor[nlep].Pz()
            P2pl = Pcor[nantilep].E()+Pcor[nantilep].Pz()
            P1mi = Pcor[nlep].E()-Pcor[nlep].Pz()
            P2mi = Pcor[nantilep].E()-Pcor[nantilep].Pz()
            cosCScor = Xcor[j].Pz()/abs(Xcor[j].Pz()) * 1./Xcor[j].M()/ROOT.TMath.Sqrt(Xcor[j].M2()+Xcor[j].Pt()**2)*(P1pl*P2mi-P2pl*P1mi)
            Y    = X[j].Rapidity()
            Ycor = Xcor[j].Rapidity()
            xn1 = sTree.x[n1]
            yn1 = sTree.y[n1]
            zn1 = sTree.z[n1]
            xn2 = sTree.x[n2]
            yn2 = sTree.y[n2]
            zn2 = sTree.z[n2]
            RPCx1 = sTree.RPCx[n1]
            RPCx2 = sTree.RPCx[n2]
            RPCy1 = sTree.RPCy[n1]
            RPCy2 = sTree.RPCy[n2]
            Delx1 = sTree.Delx[n1]
            Delx2 = sTree.Delx[n2]
            Dely1 = sTree.Dely[n1]
            Dely2 = sTree.Dely[n2]
          nrOfComb = float(len(nComb))
          if nComb[j][0]<0 : nrOfComb-=1
          if nrOfComb==0: continue
          theArray = [nrOfComb,X[j].M(),Xcor[j].M(),Xcor2[j].M(),Y,Ycor,X[j].P(),Xcor[j].P(),X[j].Pt(),Xcor[j].Pt(),muID[n1],\
                     P[n1].P(),P[n1].Pt(),Pcor[n1].P(),Pcor[n1].Pt(),muID[n2],P[n2].P(),P[n2].Pt(),Pcor[n2].P(),Pcor[n2].Pt(),\
                     IP[n1],IP[n2],chi2[j][0],chi2[j][1],costheta[j],cosCSraw,cosCScor,\
                     P[n1].X(),P[n1].Y(),P[n1].Z(),P[n2].X(),P[n2].Y(),P[n2].Z(),\
                     xn1,yn1,zn1,xn2,yn2,zn2,RPCx1,RPCy1,Delx1,Dely1,RPCx2,RPCy2,Delx2,Dely2]
          if MCdata:
             if n1<0: procID2 = 99
             else:
               m1 = mcTrackID2(sTreeFullMC,n1)
               m2 = mcTrackID2(sTreeFullMC,n2)
               if m1<0 or m2<0: procID2 = 99
               else: procID2 = muonEventCategory(sTreeFullMC,[sTreeFullMC.MCTrack[m1],sTreeFullMC.MCTrack[m2]])
             if 0>1:
              tchannel = {1:"Decay",
                          2:"Hadronic inelastic",
                          3:"Lepton pair",
                          4:"Positron annihilation",
                          5:"charm",
                          6:"beauty",
                          7:"Di-muon P8",
                          8:"Photo nuclear interaction",
                          9:"Decay mixed",
                         10:"clone",
                         11:"Drell Yan",
                         12:"prompt photon",
                         13:"prompt quark",
                         98:"no muon",
                         99:"invalid"}
             if n1<0: kTrueMu = -1
             else:    kTrueMu = sTreeMC.MCID[n1]
             if kTrueMu>0 and kTrueMu<sTreeFullMC.MCTrack.GetEntries():
              ox,oy,oz = sTreeFullMC.MCTrack[kTrueMu].GetStartX(),sTreeFullMC.MCTrack[kTrueMu].GetStartY(),sTreeFullMC.MCTrack[kTrueMu].GetStartZ()
             else:
              ox,oy,oz = -9999.,9999.,-9999.
              Pmother[j] = -111.
             theArray += [float(jpsi[j]),float(tchannel),float(procID2),PTRUE[j],PtTRUE[j],YTRUE[j],pTrue[j][0].Mag(),pTrue[j][1].Mag(),\
                     dTheta[j][0],dTheta[j][1],dMults[j][0],dMults[j][1],originZ[j][0],originZ[j][1],\
                     pTrue[j][0].X(),pTrue[j][0].Y(),pTrue[j][0].Z(),pTrue[j][1].X(),pTrue[j][1].Y(),pTrue[j][1].Z(),ox,oy,oz,Pmother[j]]
             if Debug:
                 if (P[n1].P() > 20 and muID[n1]%100!=11) or (P[n2].P() > 20 and muID[n2]%100!=11):
                    print sTreeFullMC.GetCurrentFile().GetName(),n-nInFile,P[n1].P(),muID[n1],P[n2].P(),muID[n2]
          theTuple = array('f',theArray)
          h['nt'].Fill(theTuple)
    h['fntuple'].cd()
    h['nt'].Write()
    hname = name.replace('ntuple-','')
    ut.writeHists(h,hname)
    print "I have finished. ",hname
def myDraw(variable,cut,ntName='10GeV',DYxsec=1.):
 if ntName!='10GeV':
    hMC[ntName].Draw(variable,cut)
    return
 hMC[ntName].Draw(variable,cut+"&&(procID2<4||procID2>6)")   # exclude charm
 var   = variable.split('>>')[0]
 histo = variable.split('>>')[1]
# dirty trick:
 lowMassFudgeFactor = DYxsec%1000/100.
 dyFudgeFactor      = (DYxsec-DYxsec%1000)%1000000/100000.
 charmFudgeFactor   = int(DYxsec/1000000.)/100.
#
 hMC[histo].Scale(lowMassFudgeFactor)
# charm
 if not hMC.has_key('Charm'+histo): hMC['Charm'+histo]=hMC[histo].Clone('Charm'+histo)
 charmCut = cut+""
 hMC['Charm2'].Draw(var+">>Charm"+histo,charmCut)
 if DYxsec>0.0:
# now add distribution to lowMass with correct normalization
    hMC[histo].Add(hMC['Charm'+histo],Charmfactor)
# Drell Yan
 if not hMC.has_key('DY'+histo): hMC['DY'+histo]    = hMC[histo].Clone('DY'+histo)
 DYCut = cut+""
 hMC['DY'].Draw(var+">>DY"+histo,DYCut)
 if DYxsec>0.0: 
# now add distribution to lowMass with correct normalization
    hMC[histo].Add(hMC['DY'+histo],DYfactor * DYxsec)
 # too complicated to combine 1GeV
 # hMC['10GeV'].Draw(variable,str(hMC['weights']['1GeV'])+'*('+cut+')')
 # hMC['10eV'].Draw(variable.replace(">>",">>+"),str(hMC['weights']['1GeV'])+'*('+cut+')')
 
jpsiCascadeContr = 7./33.
InvMassPlots = [160,0.,8.]
bw = (InvMassPlots[2]-InvMassPlots[1])/InvMassPlots[0]
fGlobal['myGauss'] = ROOT.TF1('gauss','abs([0])*'+str(bw)+'/(abs([2])*sqrt(2*pi))*exp(-0.5*((x-[1])/[2])**2)\
            +abs([3])*'+str(bw)+'/(abs([5])*sqrt(2*pi))*exp(-0.5*((x-[4])/[5])**2)+abs( [6]+[7]*x+[8]*x**2 )\
            +abs([9])*'+str(bw)+'/(abs([2])*sqrt(2*pi))*exp(-0.5*((x-(3.6871 + [1] - 3.0969))/[2])**2)',10)
fGlobal['TwoGauss'] = ROOT.TF1('TwoGauss','abs([0])*'+str(bw)+'/(abs([2])*sqrt(2*pi))*exp(-0.5*((x-[1])/[2])**2)\
            +abs([3])*'+str(bw)+'/(abs([5])*sqrt(2*pi))*exp(-0.5*((x-[1])/[5])**2)',6)
fGlobal['gausN'] = ROOT.TFormula('gausN','gausn')
fGlobal['cb']    = ROOT.TF1("cb","crystalball",0,6.)

# The elastic proton proton cross section at ~27GeV is about 7mbar. The inelastic cross section is about 33mbar. 
# Since we have a thick target, any proton from the elastic scattering will interact inelastic somewhere else.
# last cascade production of Eric shows even larger contribution, but momentum distribution not clear.
def loadNtuples(BDT='BDT-',ext='_mu',eos=False):
 simpath  = ''
 recopath = ''
 if eos: 
    simpath  = os.environ['EOSSHIP']+"/eos/experiment/ship/user/truf/muflux-sim/"
    recopath = os.environ['EOSSHIP']+"/eos/experiment/ship/user/truf/muflux-reco/"
 if options.refit :
  hData['f']     = ROOT.TFile.Open(recopath+'ntuple-InvMass-refitted.root')       # changed 4.4.2020, before ntuple-InvMass-refitted_0.root ROOT.TFile('ntuple-InvMass-refitted_intermediateField.root')
  hMC['f1']      = ROOT.TFile.Open(simpath+'ntuple-invMass-MC-1GeV-repro'+ext+'.root')  # changed 7.4.2020, before ntuple-invMass-MC-1GeV-repro_0.root
  hMC['f10']     = ROOT.TFile.Open(simpath+'ntuple-invMass-MC-10GeV-repro'+ext+'.root') # changed 7.4.2020, before BDT+'ntuple-invMass-MC-10GeV-repro_0.root'
  hMC['fJpsi']   = ROOT.TFile.Open(simpath+'ntuple-invMass-MC-Jpsi'+ext+'.root')        # changed 6.4.2020, before  ntuple-invMass-MC-JpsiP8_0.root
  hMC['fJpsiP8'] = ROOT.TFile.Open(simpath+'ntuple-invMass-MC-JpsiP8'+ext+'.root')      # changed 6.4.2020, before  ntuple-invMass-MC-JpsiP8_0.root
  hMC['fJpsiP8_Primary']   = ROOT.TFile.Open(simpath+'Jpsi-Pythia8_21788000000_0-3074.root')
  hMC['fJpsiP8_PrimaryMu'] = ROOT.TFile.Open(simpath+'Jpsi-Pythia8_385000000_10000-11000.root')
  hMC['fJpsiCascade']      = ROOT.TFile.Open(simpath+'cascade_MSEL61_20M.root')
  hMC['fDY']               = ROOT.TFile.Open(simpath+'ntuple-invMass-MC_DrellYanPDF4_refit.root')
  hMC['fCharm2']           = ROOT.TFile.Open(simpath+'ntuple-invMass-MC_10GeVCharm2_refit.root')
  # hMC['fJpsiCascade'] needs to be scaled by 0.9375, since 1 file not being used in simulation, fixed in reprocessing
  hMC['scalingFactor']={}
  hMC['scalingFactor']['fJpsiCascade']=1.0
  hMC['fJpsi10GeV'] = ROOT.TFile.Open(simpath+'JpsifromBackground.root')
  hMC['fJpsi1GeV']  = ROOT.TFile.Open(simpath+'JpsifromBackground-1GeV.root')
 else:
  hData['f'] = ROOT.TFile('ntuple-InvMass.root')
  hMC['f1']  = ROOT.TFile('ntuple-invMass-MC-1GeV.root')
  hMC['f10'] = ROOT.TFile('ntuple-invMass-MC-10GeV.root')
# ------------------------------------------------------------
 hMC['1GeV']        = hMC['f1'].nt           # inv mass ntuple from 1GeV muon background
 hMC['10GeV']       = hMC['f10'].nt          # inv mass ntuple from 10GeV muon background
 hMC['Jpsi']        = hMC['fJpsi'].nt        # inv mass ntuple from Cascade, Pythia6, Eric
 hMC['JpsiP8']      = hMC['fJpsiP8'].nt      # inv mass ntuple from primary, Pythia8, me
 hMC['DY']          = hMC['fDY'].nt      # inv mass ntuple from Drell Yan, Pythia8, me
 hMC['Charm2']      = hMC['fCharm2'].nt      # inv mass ntuple from CharmProduction, Pythia6 Cascade, Pythia8, me
 hMC['JpsiCascade'] = hMC['fJpsiCascade'].pythia6              # original input file from Eric
 hMC['JpsiP8_Primary'] = hMC['fJpsiP8_Primary'].pythia6        # first Pythia8 production with intermediate Jpsis 
 hMC['JpsiP8_PrimaryMu'] = hMC['fJpsiP8_PrimaryMu'].pythia6    # second Pythia8 production with above ussue fixed, I think. 
 hMC['Jpsi10GeV']   = hMC['fJpsi10GeV'].pythia8                # JpsifromBackground ??
 hMC['Jpsi1GeV']   = hMC['fJpsi1GeV'].pythia8
 ROOT.gROOT.cd()
 ut.bookCanvas(hMC,'dummy',' ',900,600,1,1)

def applyEfficiencCorrections(cases, category,colors):
   effMin = 0.0001
   for c in cases:
     for z in category:
       hname = cases[c].GetName()+"_effCorrected"+z
       hMC[hname]  = cases[c].Clone(hname)
       hMC[hname].SetLineColor(colors[z])
       if c.find('MC')==0: 
          hMC[hname].SetMarkerStyle(23)
          hMC[hname].SetMarkerColor(colors[z])
       for n in range(1,cases[c].GetNbinsX()+1): 
          x = cases[c].GetBinCenter(n)
          y = cases[c].GetBinContent(n)
          yerr = cases[c].GetBinError(n)
          e = hMC['YEff'+z+'_graph'].Eval(x)
          if e>effMin:
           hMC[hname].SetBinContent(n,y/e)
           hMC[hname].SetBinError(n,yerr/e)
          else:
           hMC[hname].SetBinContent(n,0.)
           hMC[hname].SetBinError(n,0.)
       unconvolute(z,cases[c],effMin) # will make hMC[cases[c].GetName()+"_effAndResolCorrected_"+z]
     htag = "_effAndResolCorrected"
     mixname = cases[c].GetName()+htag+'_mix'
     hMC[mixname]=hMC[cases[c].GetName()+htag+"_P8prim"].Clone(mixname)
     hMC[mixname].Add(hMC[cases[c].GetName()+htag+"_Cascade"])
     hMC[mixname].Scale(0.5)
   hMC['dummy'].cd()
   for c in cases:
     ut.bookCanvas(hMC,c+'YieldsEffCorrectedCanvas',' ',900,600,1,1)
     hMC[c+'YieldsEffCorrectedCanvas'].cd()
     theMax = 0
     for z in category:
       hjpsi   = hMC[cases[c].GetName()+"_effCorrected"+z]
       hjpsi.SetStats(0)
       hjpsi.SetLineColor(colors[z])
       hjpsi.SetMarkerStyle(24)
       hjpsi.SetMarkerColor(colors[z])
       minMax = ut.findMaximumAndMinimum(hjpsi)
       if minMax[1]>theMax: theMax = minMax[1]
       hjpsi.SetMaximum(theMax)
       hjpsi.Draw()
       hjpsi = hMC[cases[c].GetName()+"_effAndResolCorrected"+z]
       hjpsi.SetLineColor(colors[z])
       hjpsi.SetStats(0)
       hjpsi.SetMarkerStyle(20)
       hjpsi.SetMarkerColor(colors[z])
       minMax = ut.findMaximumAndMinimum(hjpsi)
       if minMax[1]>theMax: theMax = minMax[1]
       hjpsi.SetMaximum(theMax*1.2)
       hjpsi.Draw()
     for z in category:
         hMC[cases[c].GetName()+"_effCorrected"+z].Draw('same')
         hMC[cases[c].GetName()+"_effAndResolCorrected"+z].Draw('same')
     if c.find('10GeV')<0 and c.find('Data')<0:
       if c.find('P8')>0:   z="_P8prim"
       elif c.find('Cascade')>0:   z="_Cascade"
       else: 
          print "should not happen",c,z
       hMC['Y'+z+'_scaled'+c]=hMC['Y'+z].Clone('Y'+z+'_scaled'+c)
       hMC['Y'+z+'_scaled'+c].Scale(hjpsi.GetBinWidth(1)/hMC['Y_P8prim'].GetBinWidth(1))
       hMC['Y'+z+'_scaled'+c].SetLineColor(colors[z])
       hMC['Y'+z+'_scaled'+c].Draw('same')
     myPrint(hMC[c+'YieldsEffCorrectedCanvas'],c+'YieldsEffCorrected')
# pull distributions
   for c in ['HighMass-Cascade','HighMass-P8']:
      for z in category:
         hname = cases[c].GetName()+"_effAndResolCorrected"+z
         ut.bookHist(hMC,"Pull"+hname,'pull',1000,-1.,1.)
         for n in range(1,hMC[hname].GetNbinsX()+1):
           Nrec = hMC[hname].GetBinContent(n)
           if Nrec < 1: continue
           xx = 'Cascade'
           if c.find("P8")>0: xx="P8prim"
           k    = hMC['Y_'+xx+'_scaled'+c].FindBin(hMC[hname].GetBinCenter(n))
           Ngen = hMC['Y_'+xx+'_scaled'+c].GetBinContent(k)
           delta = ( Ngen - Nrec ) / float(Ngen) 
           rc = hMC["Pull"+hname].Fill(delta)

def determineEfficiencies(theCut,category,colors,withCosCSCut,withWeight):
   y_beam = yBeam()
   for z in category:
     ut.bookHist(hMC,'PandPt'+z,'P and Pt Jpsi '                     ,60,0.,300.,60,0.,5.)
     ut.bookHist(hMC,'PandPt'+z+'_rec','P and Pt Jpsi reconstructed' ,60,0.,300.,60,0.,5.)
     ut.bookHist(hMC,'YandPt'+z,'rapidity of original ',              200,-2.,2., 60, 0.,5.)
     ut.bookHist(hMC,'YandPt'+z+'_rec','rapidity of reconstructed ',  200,-2.,2., 60, 0.,5.)
     ut.bookHist(hMC,'YM'+z,'Y migration;ycor;ytrue', 40,-2.,2., 40,-2.,2.)
   ut.bookHist(hMC,'YM_10GeV','Y migration;ycor;ytrue', 40,-2.,2., 40,-2.,2.)
   ROOT.gROOT.cd()
   hMC['dummy'].cd()
   variables = {'Ypt':'sqrt(px*px+py*py):0.5*log((E+pz)/(E-pz))-'+str(y_beam),
                'ppt':'sqrt(px*px+py*py):sqrt(px*px+py*py+pz*pz)'}
   for z in category:
     if withWeight and (z=='_Cascade' or z=='_P8prim'):
      if z=='_Cascade':
       pt = "sqrt(px*px+py*py)"
       if not hMC.has_key('fp6w'): weight4Pythia6()
       w = "("+str(hMC['fp6w'].GetParameter(0))
       for n in range(1,10):
         p = hMC['fp6w'].GetParameter(n)
         if p<0: w+=str(p)+'*'+pt+'**'+str(n)
         else:   w+="+"+str(p)+'*'+pt+'**'+str(n)
       w+=")"
       wrec = w.replace(pt,'(PtTRUE)')
      if z=='_P8prim':
       y = "(0.5*log((E+pz)/(E-pz))-"+str(y_beam)+")"
       if not hMC.has_key('fp8w'): weight4Pythia6()
       w = "("+str(hMC['fp8w'].GetParameter(0))
       for n in range(1,10):
         p = hMC['fp8w'].GetParameter(n)
         if p<0: w+=str(p)+'*'+y+'**'+str(n)
         else:   w+="+"+str(p)+'*'+y+'**'+str(n)
       w+=")"
       wrec = w.replace(y,'(YTRUE-'+str(y_beam)+')')
      category[z]['ntOriginal'].Draw(variables['ppt']+'>>PandPt'+z,                w+'*('+category[z]['cut']+')')
      category[z]['nt'].Draw('PtTRUE:PTRUE>>PandPt'+z+'_rec',wrec+'*('+theCut+category[z]['cutrec']+')')
      category[z]['ntOriginal'].Draw(variables['Ypt']+'>>YandPt'+z,                w+'*('+category[z]['cut']+')')
      category[z]['nt'].Draw('PtTRUE:(YTRUE-'+str(y_beam)+')>>YandPt'+z+'_rec',wrec+'*('+theCut+category[z]['cutrec']+')')
     else: 
      category[z]['ntOriginal'].Draw(variables['ppt']+'>>PandPt'+z,                category[z]['cut'])
      category[z]['nt'].Draw('PtTRUE:PTRUE>>PandPt'+z+'_rec',theCut+category[z]['cutrec'])
      category[z]['ntOriginal'].Draw(variables['Ypt']+'>>YandPt'+z,                category[z]['cut'])
      category[z]['nt'].Draw('PtTRUE:(YTRUE-'+str(y_beam)+')>>YandPt'+z+'_rec',theCut+category[z]['cutrec'])
#
     # divide all MC true distributions by factor 0.5 due to cosCS cut only applied at reco level
     # TEfficiency does not like weights, change entries and errors by hand
     if withCosCSCut:
        for x in [hMC['PandPt'+z],hMC['YandPt'+z]]:
           for nx in range(1,x.GetNbinsX()+1):
              for ny in range(1,x.GetNbinsY()+1):
                if withWeight:  x.SetBinContent(nx,ny,x.GetBinContent(nx,ny)/2.)
                else:           x.SetBinContent(nx,ny,int(x.GetBinContent(nx,ny)/2.+0.5))
             # x.SetBinError(nx,ny,x.GetBinError(nx,ny)/2.)
# make projections
     hMC['P'+z]        = hMC['PandPt'+z].ProjectionX('P'+z)
     hMC['P'+z+'_rec'] = hMC['PandPt'+z+'_rec'].ProjectionX('P'+z+'_rec')
     print "make eff ",'PEff'+z
     hMC['PEff'+z]=ROOT.TEfficiency(hMC['P'+z+'_rec'],hMC['P'+z])
     hMC['Pt'+z]        = hMC['YandPt'+z].ProjectionY('Pt'+z,115,200)
     hMC['Pt'+z+'_rec'] = hMC['YandPt'+z+'_rec'].ProjectionY('Pt'+z+'_rec',115,200)
     print "make eff ",'PtEff'+z
     hMC['PtEff'+z]=ROOT.TEfficiency(hMC['Pt'+z+'_rec'],hMC['Pt'+z])
     hMC['Y'+z]     = hMC['YandPt'+z].ProjectionX('Y'+z)
     hMC['Y'+z+'_rec'] = hMC['YandPt'+z+'_rec'].ProjectionX('Y'+z+'_rec')
     print "make eff ",'YEff'+z
     hMC['YEff'+z]=ROOT.TEfficiency(hMC['Y'+z+'_rec'],hMC['Y'+z])
     hMC['YEff'+z].Draw()
     hMC['dummy'].Update()
     hMC['YEff'+z+'_graph']= hMC['YEff'+z].GetPaintedGraph()
     hMC['YEff'+z+'_graph'].GetXaxis().SetRangeUser(0.,2.)
     hMC['YEff'+z+'_graph'].GetYaxis().SetRangeUser(0.,0.6)
     hMC['YEff'+z].SetTitle(';y_{CMS};efficiency')
     hMC['YEff'+z+'_histo'] = hMC['Y'+z].Clone('YEff'+z+'_histo')
     X=hMC['YEff'+z+'_histo']
     X.Reset()
     X.SetTitle(';y_{CMS};efficiency')
     X.SetLineColor(hMC['YEff'+z+'_graph'].GetLineColor())
     for n in range(X.GetNbinsX()):
       y=hMC['YEff'+z+'_graph'].GetY()[n]
       e=hMC['YEff'+z+'_graph'].GetErrorY(n)
       if y==0: e=0
       X.SetBinContent(n+1,y)
       X.SetBinError(n+1,e)
     X.Draw()
# now we have efficiencies as function of YTRUE. This ignores the resolution.
     category[z]['nt'].Draw('(YTRUE-'+str(y_beam)+'):('+ycor1C+'-'+str(y_beam)+')>>YM'+z,theCut+category[z]['cutrec'])
   hMC['10GeV'].Draw('(YTRUE-'+str(y_beam)+'):('+ycor1C+'-'+str(y_beam)+')>>YM_10GeV',theCut+"&&Jpsi==443")
   hMC['lYEff']=ROOT.TLegend(0.7,0.7,0.95,0.95)
   for z in category:
        hMC['YEff'+z].SetLineColor(colors[z])
        hMC['YEff'+z].Draw('same')
        hMC['lYEff'].AddEntry(hMC['YEff'+z],z,'PL')
   myPrint(hMC['dummy'],'JpsiEfficiencies')
def theJpsiCut(v,withCosCSCut,ptCut,pmin,pmax,muID,BDTCut,sameSign=False):
   sptCut = str(ptCut)
   theCut =  'mult<3&&max(pt1,pt2)>'+sptCut+'&&chi21*chi22<0&&max(abs(chi21),abs(chi22))<0.9&&\
                max(p1,p2)<'+str(pmax)+'&&min(p1,p2)>'+str(pmin)+'&&mcor>0.00'
   if sameSign:
      theCut =  'mult<3&&max(pt1,pt2)>'+sptCut+'&&chi21*chi22>0&&max(abs(chi21),abs(chi22))<0.9&&\
                max(p1,p2)<'+str(pmax)+'&&min(p1,p2)>'+str(pmin)+'&&mcor>0.00'
   if v=='mcor':
      theCut = theCut.replace('pt1','pt1cor')
      theCut = theCut.replace('pt2','pt2cor')
      # theCut+="&&abs(m/mcor-1)<1"
   if withCosCSCut: theCut+='&&abs(cosCScor)<0.5'
   if muID == 1: theCut+='&&(muID1%100==11||muID2%100==11)'
   if muID == 2: theCut+='&&(muID1%100==11&&muID2%100==11)'
   if muID == 11: theCut+='&&(muID1%2==1||muID2%2==1)'
   if muID == 12: theCut+='&&(muID1%2==1&&muID2%2==1)'
#### BDT
   if BDTCut: theCut += "&&BDT>0."
   return theCut.replace(' ','')

def runAll(ptCut=1.0,pmin=20.,muID=2,wW=True,fM=None,withDY=False,DY=[0.,1.,2.,4.],withPsi2s=False):
   proj = 'ycor1C'
   loadNtuples()
   if not type(DY)==type([]): DY = [DY]
   for DYxsec in DY:
     for fitMethod in ['B','CB','G']:
         if fM:
             if fitMethod != fM: continue
         JpsiAcceptance(withCosCSCut=True, ptCut = ptCut, pmin = pmin, pmax = 300., BDTCut=None, muID=muID, fitMethod=fitMethod,withWeight=wW,withDY=withDY,DYxsec=DYxsec,withPsi2s=withPsi2s)

def JpsiAcceptance(withCosCSCut=True, ptCut = 1.4, pmin = 10., pmax = 300., BDTCut=None, muID=0, fitMethod='gaus',withWeight=False,withDY=False,DYxsec=2.,withPsi2s=False):
   # with twoBukin fit usually ptCut = 0.
   # muID = 0: no muon confirmed
   # muID = 1: at least one muon confirmed
   # muID = 2: both muons confirmed, previous default
   ycor = 'ycor1C'
   category = {}
   category['_Cascade']     = {'nt':hMC['Jpsi'],  'ntOriginal':hMC['JpsiCascade'],   'cut':'id==443',            'cutrec':'&&Jpsi==443&&originZ1<-100&&p1x!=p2x'}
   category['_P8prim']      = {'nt':hMC['JpsiP8'],'ntOriginal':hMC['JpsiP8_Primary'],'cut':'id==443',            'cutrec':'&&Jpsi==443&&originZ1<-100&&p1x!=p2x'}
   # category['_Cascadeprim'] = {'nt':hMC['Jpsi'],  'ntOriginal':hMC['JpsiCascade'],   'cut':'id==443&&mE>399.999','cutrec':'&&Jpsi==443&&Pmother>399.999'}
   colors = {}
   colors['_Cascade']    = ROOT.kMagenta
   colors['_Cascadeprim']= ROOT.kCyan
   colors['_P8prim']     = ROOT.kRed
   colors['Data']        = ROOT.kBlue
#  
   if BDTCut: 
      ptCut = 0.
      pmin  = 0.
      pmax  = 1000.
   theCutcosCS = theJpsiCut('mcor',withCosCSCut,ptCut,pmin,pmax,muID,BDTCut)
   tag = 'muID'+str(muID)+'_'+fitMethod+'-'+str(ptCut)+'_'+str(pmin)+'_DY'+str(DYxsec)
   if BDTCut: tag += '_BDT'
   if withWeight: tag += '_wp6'
   os.chdir(topDir)
   print "debug ---",tag,os.path.isdir(tag)
   if not os.path.isdir(tag): os.system('mkdir '+tag)
   os.chdir(tag)

   determineEfficiencies(theCutcosCS,category,colors,withCosCSCut,withWeight)
   print "---> efficiencies determined"
# 
   proj = 'ycor1C'
   fM = 'Jpsi'
   fR=[0.2,2.,18]
   if fitMethod=='gaus':
      makeProjection(proj,fR[0],fR[1],'y_{CMS}',theCutcosCS,nBins=fR[2],ntName='JpsiP8',printout=1,fixSignal=False,secondGaussian=False)
      hMC["MCJpsiP8-ycor"]=hMC["mc-Jpsi"+proj].Clone("MCJpsiP8-ycor")
      makeProjection(proj,fR[0],fR[1],'y_{CMS}',theCutcosCS,nBins=fR[2],ntName='Jpsi',printout=1,fixSignal=False,secondGaussian=False)
      hMC["MCJpsiCascade-ycor"]=hMC["mc-Jpsi"+proj].Clone("MCJpsiCascade-ycor")
      makeProjection(proj,fR[0],fR[1],'y_{CMS}',theCutcosCS,nBins=fR[2],ntName='10GeV',printout=1,fixSignal=False,secondGaussian=True)
      hMC["MCJpsi10GeV-ycor"]=hMC["mc-Jpsi"+proj].Clone("MCJpsi10GeV-ycor")
      hData['Jpsi-ycor']   = hData['Jpsi'+proj].Clone('Jpsi-ycor')
   elif fitMethod=='twoBukin':
# for Jpsi cascade large stat
      twoBukinYieldFit(proj,fR[0],fR[1],'y_{CMS}',theCutcosCS,nBins=fR[2],ntName='Jpsi',printout=1)
      hMC['MCBJpsiCascade-ycor'] = hMC['mc-BJpsi'+proj].Clone('MCBJpsiCascade-ycor')
# for Jpsi P8prim large stat
      twoBukinYieldFit(proj,fR[0],fR[1],'y_{CMS}',theCutcosCS,nBins=fR[2],ntName='JpsiP8',printout=1)
      hMC['MCBJpsiP8-ycor']      = hMC['mc-BJpsi'+proj].Clone('MCBJpsiP8-ycor')
# for data
      twoBukinYieldFit(proj,fR[0],fR[1],'y_{CMS}',theCutcosCS,nBins=fR[2],ntName='10GeV',printout=1)
      hMC['MCBJpsi10GeV-ycor']   = hMC['mc-BJpsi'+proj].Clone('MCBJpsi10GeV-ycor')
      hData['BJpsi-ycor']   = hData['BJpsi'+proj].Clone('BJpsi-ycor')
      fM = 'BJpsi'
   elif fitMethod=='CB' or fitMethod=='B'  or fitMethod=='G'   or fitMethod=='GE' :
# for Jpsi cascade large stat
      twoCBYieldFit(fitMethod,proj,fR[0],fR[1],'y_{CMS}',theCutcosCS,nBins=fR[2],printout=1,withDY=withDY,DYxsec=DYxsec,withPsi2s=withPsi2s)
   else:
      print "method not known, exit."
      exit()

   cases   = {}
   cases['HighMass-10GeV']   = hMC['mc-'+fitMethod+'_'+proj+'HighMass-10GeV-Jpsi']
   cases['HighMass-Cascade'] = hMC['mc-'+fitMethod+'_'+proj+'HighMass-Jpsi-Jpsi']
   cases['HighMass-P8']      = hMC['mc-'+fitMethod+'_'+proj+'HighMass-JpsiP8-Jpsi']
   cases['10GeV']            = hMC['mc-'+fitMethod+'_'+proj+'10GeV-Jpsi']
   cases['Data']             = hData[fitMethod+'_'+proj+'-Jpsi']

   applyEfficiencCorrections(cases, category,colors)
   print "---> efficiencies applied"
#
   tc = hMC['dummy'].cd()
   theMax = 0
   hfitted = fitMethod+'_'+proj+'-Jpsi'
   for z in category:
      for x in [hfitted+"_effCorrected"+z,hfitted+"_effAndResolCorrected"+z]:
         minMax = ut.findMaximumAndMinimum(hMC[x])
         if minMax[1]>theMax: theMax = minMax[1]
   for z in category:
     hMC["Y"+z+"_scaled"] = hMC["Y"+z].Clone("Y"+z+"_scaled")
     scale(hMC["Y"+z+"_scaled"],hMC[hfitted+"_effAndResolCorrected_mix"],R=[0.4,1.6])
     hMC["Y"+z+"_scaled"].SetLineColor(colors[z])
   hMC["Y_Cascade_scaled"].SetMaximum(theMax*1.2)
   hMC["Y_Cascade_scaled"].Draw()
   hMC["Y_P8prim_scaled"].Draw('same')
   hMC[hfitted+"_effCorrected_P8prim"].Draw('same')
   hMC[hfitted+"_effCorrected_Cascade"].Draw('same')
   hMC[hfitted+"_effAndResolCorrected_P8prim"].Draw('same')
   hMC[hfitted+"_effAndResolCorrected_Cascade"].Draw('same')
#
   lumi  = 30.7 # pb-1
   elumi = 0.7
   ylimits = [0.4,0.6]
   epsilon = 0.01
   frac = fGlobal['etaNA50'].Integral(ylimits[0],ylimits[1])/fGlobal['etaNA50'].Integral(-0.425,0.575)
   crossSection = 3.994
   NA50fraction  = frac * crossSection
   eNA50fraction = frac * 0.148 # 2.1% sys + 3% lumi + 0.022 stat
   mix = 0
   for m in [hfitted+"_effCorrected",hfitted+"_effAndResolCorrected"]:
     print "with method --->",m.split('_eff')[1]+'eff',' fit:',fitMethod
     for z in category:
        print "     results with --->"+z
        hjpsi = hMC[m+z]
        binMin = hjpsi.FindBin(ylimits[0])
        binMax = hjpsi.FindBin(ylimits[1]-epsilon)
        NsignalNA50 = hjpsi.Integral(binMin,binMax)
        Nsignal     = hjpsi.Integral(binMin,hjpsi.FindBin(1.8))
        print "N in "+str(ylimits[0])+"<y<1.8: %5.1F   Xsection=%5.2Fnb"%(Nsignal,Nsignal/lumi/1000.)
        print "N in "+str(ylimits[0])+"<y<0.6: %5.1F   Xsection=%5.2Fnb  Muflux/NA50=%5.2F"%(
        NsignalNA50,NsignalNA50/lumi/1000.,NsignalNA50/lumi/1000./NA50fraction)
   N = lumi * 1000. * crossSection
   fGlobal['etaNA50'].SetParameter(0,1.)
   fGlobal['etaNA50'].SetParameter(0,N/fGlobal['etaNA50'].Integral(-0.425,0.575)*hjpsi.GetBinWidth(1))
   fGlobal['etaNA50'].DrawF1(0.,2.0,'same')
   hMC["Y_Cascade_scaled"].SetMaximum(max(hMC["Y_Cascade_scaled"].GetMaximum(),fGlobal['etaNA50'].GetMaximum()*1.2))
   tc.Update()
   myPrint(hMC['dummy'],"data_YieldsEffCorrectedWithNA50")
   ut.writeHists(hData,'Data-histos.root')
   ut.writeHists(hMC,'MC-histos.root')
#
def detectorAcceptance(ptCut = 1.0, pmin = 20.,pmax  = 300.,BDTCut=None,muID=0,singlePads=False):
   tag = '_mID'+str(muID)
   print "tag = '"+tag+"'"
   ut.bookHist(hMC,'mc-XY'+tag,'first measured point',100,-30.,30.,100,-30.,30.)
   ut.bookHist(hData,'XY'+tag,'first measured point',100,-30.,30.,100,-30.,30.)
   ut.bookHist(hMC,'mc-Z'+tag,'first measured point',100,0.,50.)
   ut.bookHist(hData,'Z'+tag,'first measured point',100,0.,50.)
   ut.bookHist(hMC,'mc-LXY'+tag,'last state',100,-100.,100.,100,-100.,100.)
   ut.bookHist(hData,'LXY'+tag,'last state', 100,-100.,100.,100,-100.,100.)
   ut.bookHist(hMC,'mc-DXY'+tag,'dist to muon track',100,0.,20.,100,0.,20.)
   ut.bookHist(hData,'DXY'+tag,'dist to muon track',100,0.,20.,100,0.,20.)
   ROOT.gROOT.cd()
   theCut = theJpsiCut('mcor','True',ptCut,pmin,pmax,muID,False) + "&&2.5<mcor&&3.5>mcor"
   hMC['Jpsi'].Draw('rec1y:rec1x>>mc-XY'+tag,theCut)
   hMC['Jpsi'].Draw('rec2y:rec2x>>+mc-XY'+tag,theCut)
   hMC['Jpsi'].Draw('rec1z>>mc-Z'+tag,theCut)
   hMC['Jpsi'].Draw('rec2z>>+mc-Z'+tag,theCut)
   hMC['Jpsi'].Draw('RPCy1:RPCx1>>mc-LXY'+tag,theCut)
   hMC['Jpsi'].Draw('RPCy2:RPCx2>>+mc-LXY'+tag,theCut)
   hMC['Jpsi'].Draw('Dely1:Delx1>>mc-DXY'+tag,theCut)
   hMC['Jpsi'].Draw('Dely2:Delx2>>+mc-DXY'+tag,theCut)
#
   hData['f'].nt.Draw('rec1y:rec1x>>XY'+tag,theCut)
   hData['f'].nt.Draw('rec2y:rec2x>>+XY'+tag,theCut)
   hData['f'].nt.Draw('rec1z>>Z'+tag,theCut)
   hData['f'].nt.Draw('rec2z>>+Z'+tag,theCut)
   hData['f'].nt.Draw('RPCy1:RPCx1>>LXY'+tag,theCut)
   hData['f'].nt.Draw('RPCy2:RPCx2>>+LXY'+tag,theCut)
   hData['f'].nt.Draw('Dely1:Delx1>>DXY'+tag,theCut)
   hData['f'].nt.Draw('Dely2:Delx2>>+DXY'+tag,theCut)
#
   for X in ['mc-','mc-L','mc-D']:
     for p in ['X','Y']:
      hn = X+p+tag
      hMC[hn] = eval('hMC["'+X+'XY'+tag+'"].Projection'+p+'(hn)')
      hMC[hn].SetLineColor(ROOT.kMagenta)
      hMC[hn].Scale(1./hMC[hn].GetEntries())
      mcmax = hMC[hn].GetMaximum()
      hn = hn.replace('mc-','')
      hData[hn] = eval('hData["'+X.replace('mc-','')+'XY'+tag+'"].Projection'+p+'(hn)')
      hData[hn].Scale(1./hData[hn].GetEntries())
      if mcmax > hData[hn].GetMaximum(): hData[hn].SetMaximum(1.1*mcmax)
   hMC['mc-Z'+tag].SetLineColor(ROOT.kMagenta)
   hMC['mc-Z'+tag].Scale(1./hMC['mc-Z'+tag].GetEntries())
   hData['Z'+tag].Scale(1./hData['Z'+tag].GetEntries())
   ut.bookCanvas(hMC,'detAcc','detector acceptance',1800,2400,2,5)
   hMC['detAcc'].cd(1)
   hData['X'+tag].Draw()
   hMC['mc-X'+tag].Draw('same')
   if singlePads:
        tc=hMC['dummy'].cd()
        hData['X'+tag].Draw()
        hMC['mc-X'+tag].Draw('same')
        myPrint(hMC['dummy'],'detAcc'+tag+'_1')
   hMC['detAcc'].cd(2)
   hData['Y'+tag].Draw()
   hMC['mc-Y'+tag].Draw('same')
   if singlePads:
        tc=hMC['dummy'].cd()
        hData['Y'+tag].Draw()
        hMC['mc-Y'+tag].Draw('same')
        myPrint(hMC['dummy'],'detAcc'+tag+'_2')
   hMC['detAcc'].cd(3)
   hData['LX'+tag].Draw( )
   hMC['mc-LX'+tag].Draw('same')
   if singlePads:
        tc=hMC['dummy'].cd()
        hData['LX'+tag].Draw()
        hMC['mc-LX'+tag].Draw('same')
        myPrint(hMC['dummy'],'detAcc'+tag+'_3')
   hMC['detAcc'].cd(4)
   hData['LY'+tag].Draw()
   hMC['mc-LY'+tag].Draw('same')
   if singlePads:
        tc=hMC['dummy'].cd()
        hData['LY'+tag].Draw()
        hMC['mc-LY'+tag].Draw('same')
        myPrint(hMC['dummy'],'detAcc'+tag+'_4')
   tc = hMC['detAcc'].cd(5)
   tc.SetLogy(1)
   hData['DX'+tag].Draw()
   hMC['mc-DX'+tag].Draw('same')
   tc = hMC['detAcc'].cd(6)
   tc.SetLogy(1)
   hData['DY'+tag].Draw()
   hMC['mc-DY'+tag].Draw('same')
   tc = hMC['detAcc'].cd(7)
   hMC['mc-XY'+tag].Draw('colz')
   tc = hMC['detAcc'].cd(8)
   hMC['mc-LXY'+tag].Draw('colz')
   tc = hMC['detAcc'].cd(9)
   hData['XY'+tag].Draw('colz')
   tc = hMC['detAcc'].cd(10)
   hData['LXY'+tag].Draw('colz')
   hMC['dummy'].cd()
   hData['Z'+tag].Draw()
   hMC['mc-Z'+tag].Draw('same')
   myPrint(hMC['detAcc'],'detAcc'+tag)
def detectorAcceptance_reload():
   for muID in range(3):
       for c in range(1,5):
           f=ROOT.TFile('detAcc_mID'+str(muID)+'_'+str(c)+'.root')
           dummy = f.Get('dummy').Clone('dummy')
           dummy.Draw()
           for x in dummy.GetListOfPrimitives():
                if x.ClassName().find('TH')==0:
                   x.SetStats(0)
                   x.GetYaxis().SetTitle('N events')
                   if c==1 or c==3: x.GetXaxis().SetTitle('x [cm]')
                   else: x.GetXaxis().SetTitle('y [cm]')
           dummy.Draw()
           f.Close()
           myPrint(dummy,'reloaded-detAcc_mID'+str(muID)+'_'+str(c))

def JpsiPolarization(ptCut = 1.0, pmin = 20., pmax = 300., BDTCut=None, muID=1, fitMethod='B',nBins=20, pTJpsiMin=0.0, pTJpsiMax=5.,withWeight=True):
   colors = {}
   colors['10GeV-Jpsi']               = ROOT.kMagenta
   colors['HighMass-Jpsi-Jpsi']       = ROOT.kCyan
   colors['HighMass-JpsiP8-Jpsi']     = ROOT.kRed
   colors['Data']        = ROOT.kBlue
   theCut = theJpsiCut('mcor',False,ptCut,pmin,pmax,muID,BDTCut)
   y_beam = str(yBeam())
   theCut+='&&'+ycor1C+"-"+y_beam+'>0.4&&'+ycor1C+"-"+y_beam+'<1.6&&ptcor>'+str(pTJpsiMin)+'&&ptcor<'+str(pTJpsiMax)
   tag = 'muID'+str(muID)+'_'+fitMethod+'-'+str(ptCut)+'_'+str(pmin)+'JpsiPt'+str(pTJpsiMin)+'-'+str(pTJpsiMax)
   if BDTCut: tag += '_BDT'
   if withWeight: tag += '_wp6'
   os.chdir(topDir)
   if not os.path.isdir(tag): os.system('mkdir '+tag)
   os.chdir(tag)
   print tag
   proj = 'cosCScor'
   for z in ['_Cascade','_P8prim']:
     ntname = 'Jpsi'
     if z=='_P8prim': ntname = 'JpsiP8'
     ROOT.gROOT.cd()
     twoCBYieldFit(fitMethod,proj,-1.,1.,'cosCS',theCut,nBins=nBins,withWeight=withWeight,printout=1)
   hMC['dummy'].cd()
   hData[fitMethod+'_cosCScor-Jpsi'].SetLineColor(colors['Data'])
   hData[fitMethod+'_cosCScor-Jpsi'].Draw()
   for z in ['10GeV-Jpsi','HighMass-Jpsi-Jpsi','HighMass-JpsiP8-Jpsi']:
      hx = 'mc-'+fitMethod+'_cosCScor'+z
      scale(hMC[hx],hData[fitMethod+'_cosCScor-Jpsi'])
      hMC[hx].SetLineColor(colors[z])
      hMC[hx].Draw('same')
      hxe = 'JpsicosCScorEffcorrected_'+z
      hMC[hxe]=hData[fitMethod+'_cosCScor-Jpsi'].Clone(hxe)
      hMC[hxe].Divide(hMC[hx])
      hMC[hxe].SetLineColor(colors[z])
      hMC[hxe].SetMinimum(0.)
   myPrint(hMC['dummy'],'cosCScorDataMC')
   hData['polFun'] = ROOT.TF1('polFun','[0]*(1+x**2*[1])',2)
   T = ROOT.TLatex()
   dy = 0.15
   for z in ['10GeV-Jpsi','HighMass-Jpsi-Jpsi','HighMass-JpsiP8-Jpsi']:
       if dy < 0.2: hMC['JpsicosCScorEffcorrected_'+z].Draw()
       else:        hMC['JpsicosCScorEffcorrected_'+z].Draw('same')
       rc = hMC['JpsicosCScorEffcorrected_'+z].Fit(hData['polFun'],'S','',-0.6,0.6)
       fitResult = rc.Get()
       txt  = "%s: polarization CS #Lambda=%5.2F +/- %5.2F"%(z,fitResult.Parameter(1),fitResult.ParError(1))
       T.SetTextColor(colors[z])
       T.DrawLatexNDC(0.2,dy,txt)
       hMC['JpsicosCScorEffcorrected_'+z].GetFunction('polFun').SetLineColor(colors[z])
       dy+=0.08
   hMC['dummy'].Update()
   myPrint(hMC['dummy'],'cosCScorDataEffCorrected')

def JpsiPolarizationPlots(ptCut = 1.0, pmin = 20., pmax = 300., BDTCut=None, muID=1, fitMethod='B',nBins=20, pTJpsiMin=0.0, pTJpsiMax=5.,withWeight=True,no10GeV=True):
   colors = {}
   colors['10GeV-Jpsi']               = [ROOT.kMagenta,24,'MC inclusive']
   colors['HighMass-Jpsi-Jpsi']       = [ROOT.kCyan,26,'MC Pythia6']
   colors['HighMass-JpsiP8-Jpsi']     = [ROOT.kRed,32,'MC Pythia8']
   colors['Data']                     = [ROOT.kBlue,21,'Data']
   tag = 'muID'+str(muID)+'_'+fitMethod+'-'+str(ptCut)+'_'+str(pmin)+'JpsiPt'+str(pTJpsiMin)+'-'+str(pTJpsiMax)
   if withWeight: tag += '_wp6'
   print "tag = ",tag
   proj = 'cosCScor'
   MC =  ['10GeV-Jpsi','HighMass-Jpsi-Jpsi','HighMass-JpsiP8-Jpsi']
   if no10GeV: MC =  ['HighMass-Jpsi-Jpsi','HighMass-JpsiP8-Jpsi']
   f = ROOT.TFile(tag+'/cosCScorDataMC.root')
   ROOT.gROOT.cd()
   ut.readHistsFromCanvas(hMC,f.dummy)
   ut.bookCanvas(hMC,'cosCSreco','cosCSreco',1200,900,1,1)
   hMC['cosCSreco'].cd()
   hMC[fitMethod+'_cosCScor-Jpsi'].SetStats(0)
   hMC[fitMethod+'_cosCScor-Jpsi'].SetMarkerStyle(colors['Data'][1])
   hMC[fitMethod+'_cosCScor-Jpsi'].SetMarkerColor(colors['Data'][0])
   hMC[fitMethod+'_cosCScor-Jpsi'].SetTitle(';cosCS;arbitrary units')
   hMC[fitMethod+'_cosCScor-Jpsi'].Draw()
   hMC['L'+fitMethod+'_cosCScor-Jpsi']=ROOT.TLegend(0.36,0.17,0.66,0.35)
   rc = hMC['L'+fitMethod+'_cosCScor-Jpsi'].AddEntry(hMC[fitMethod+'_cosCScor-Jpsi'],colors['Data'][2],'PL' )
   rc.SetTextColor(hMC['L'+fitMethod+'_cosCScor-Jpsi'].GetLineColor())
   for z in MC:
      hx = 'mc-'+fitMethod+'_cosCScor'+z
      hMC[hx].SetMarkerStyle(colors[z][1])
      hMC[hx].SetMarkerColor(colors[z][0])
      hMC[hx].SetStats(0)
      hMC[hx].Draw('same')
      rc = hMC['L'+fitMethod+'_cosCScor-Jpsi'].AddEntry(hMC[hx],colors[z][2],'PL')
      rc.SetTextColor(hMC[hx].GetLineColor())
   hMC['L'+fitMethod+'_cosCScor-Jpsi'].Draw()
#
   f = ROOT.TFile(tag+'/cosCScorDataEffCorrected.root')
   ROOT.gROOT.cd()
   ut.readHistsFromCanvas(hMC,f.dummy)
   ut.bookCanvas(hMC,'cosCSEffCor','cosCSEffCor',1200,900,1,1)
   hMC['cosCSEffCor'].cd()
   total={}
   for z in MC:
       rc = hMC['JpsicosCScorEffcorrected_'+z].Fit('pol0','SQ','',-0.1,0.1)
       fitResult = rc.Get()
       fun = hMC['JpsicosCScorEffcorrected_'+z].GetFunction('pol0')
       total[z] = fun.Integral(-0.6,0.6)
   hData['polFun'] = ROOT.TF1('polFun','[0]*(1+x**2*[1])',2)
   T = ROOT.TLatex()
   T.SetTextSize(0.03)
   dy = 0.35
   cosCSMax = 0.6
   for z in MC:
       hMC['JpsicosCScorEffcorrected_'+z].GetXaxis().SetRangeUser(-cosCSMax,cosCSMax)
       hMC['JpsicosCScorEffcorrected_'+z].SetStats(0)
       hMC['JpsicosCScorEffcorrected_'+z].SetTitle(';efficiency corrected     cosCS;arbitrary units')
       if dy < 0.2: hMC['JpsicosCScorEffcorrected_'+z].Draw()
       else:        hMC['JpsicosCScorEffcorrected_'+z].Draw('same')
       rc = hMC['JpsicosCScorEffcorrected_'+z].Fit(hData['polFun'],'SQ','',-cosCSMax,cosCSMax)
       fun = hMC['JpsicosCScorEffcorrected_'+z].GetFunction('polFun')
       fitResult = rc.Get()
       fun.SetLineColor(hMC['JpsicosCScorEffcorrected_'+z].GetLineColor())
       effLoss = fun.Integral(-0.5,0.5) / (fun.GetParameter(0)*(0.5+0.5)) # total[z]
       txt  = "%s: #Lambda=%5.2F +/- %5.2F   %5.2F%%  "%(colors[z][2],fitResult.Parameter(1),fitResult.ParError(1),effLoss*100)
       T.SetTextColor(hMC['JpsicosCScorEffcorrected_'+z].GetLineColor())
       T.DrawLatexNDC(0.2,dy,txt)
       dy+=0.06
   myPrint(hMC['cosCSEffCor'],tag+'_cosCScorDataEffCorrected')
   myPrint(hMC['cosCSreco'],tag+'_cosCScorDataRec')
def JpsiFitComparison(proj = 'ycor1C',ptCut=0.0,pmin=20.,BDTCut=None):
# compare B and CB fits on data
   fM = {'CB':{'signal':1,'mass':2,'sigma':3},'B':{'signal':7,'mass':8,'sigma':9}}
   tag = '-'+str(ptCut)+'_'+str(pmin)
   if BDTCut: tag += '_BDT'
   os.chdir(topDir)
   hData.clear()
   results = {}
   for M in fM:
      ut.readHists(hData,M+tag+'/Data-histos.root')
      results[M]={}
   for M in results:
     print "==========   Here the results for fit method ",M
     k=0
     while k<100:
        hk = M+'_'+proj+str(k)
        if not hData.has_key(hk): break
        hz    = hData[hk]
        fName = 'Fun'+hk
        hFun = hz.GetFunction(fName)
        mass = [hFun.GetParameter(fM[M]['mass']), hFun.GetParError(fM[M]['mass'])]
        sigm = [hFun.GetParameter(fM[M]['sigma']),hFun.GetParError(fM[M]['sigma'])]
        prob = hFun.GetProb()
        hS =  hData[M+'_'+proj+'-Jpsi']
        NS   = [hS.GetBinContent(k+1), hS.GetBinError(k+1)]
        prob = hFun.GetProb()
        ybin = hz.GetName().split(proj)[1]
        tmp = hz.GetTitle().split(' ')
        yrange = tmp[len(tmp)-1]
        print "%20s : %5.2F +/- %5.2F   %5.2F +/- %5.2F |   %10.2F +/- %5.2F "%(\
        yrange,mass[0],mass[1],sigm[0],sigm[1],NS[0],NS[1])
        results[M][yrange]={'signal':NS,'mass':mass,'sigma':sigm,'fitProb':prob}
        k+=1
   # now compare each parameter directly
   ybins = results[M].keys()
   ybins.sort()
   for p in results[M][ybins[0]]:
       print "==== compare ",p, ' B                                   CB'
       for yrange in ybins:
          if p=='fitProb':
            txt =  "%20s : %5.2F   |  %5.2F  "%(yrange,results['CB'][yrange][p]*100,results['B'][yrange][p]*100)
          elif p=='signal':
            pull = (results['B'][yrange][p][0]-results['CB'][yrange][p][0])/(1E-9 + (results['CB'][yrange][p][1]+results['B'][yrange][p][1])/2.)
            txt = "%20s : %8.2F +/- %8.2F |  %8.2F +/- %8.2F    %5.2F "%(yrange,results['CB'][yrange][p][0],results['CB'][yrange][p][1],
                 results['B'][yrange][p][0],results['B'][yrange][p][1],pull)
          else:
            pull = (results['B'][yrange][p][0]-results['CB'][yrange][p][0])/(1E-9 + (results['CB'][yrange][p][1]+results['B'][yrange][p][1])/2.)
            txt = "%20s : %5.2F +/- %5.2F |  %5.2F +/- %5.2F    %5.2F "%(yrange,results['CB'][yrange][p][0],results['CB'][yrange][p][1],
                 results['B'][yrange][p][0],results['B'][yrange][p][1],pull)
          print txt

def JpsiFitSystematics(fitMethod='CB',proj = 'ycor1C',withFitResult=False,ptCut=1.0,pmin=20.,BDTCut=None,muID=2,withWeight=True,DYxsec=1.0):
   unit={'ycor1C':'y_{cm}'}
   if muID < 0: tag = fitMethod+'-'+str(ptCut)+'_'+str(pmin)
   else:        tag = 'muID'+str(muID)+'_'+fitMethod+'-'+str(ptCut)+'_'+str(pmin)
   tag+='_DY'+str(DYxsec)
   if BDTCut: tag += '_BDT'
   if withWeight: tag += '_wp6'
   print tag
   os.chdir(topDir)
   os.chdir(tag)
   if not withFitResult:
      hMC.clear()
      hData.clear()
      ut.readHists(hMC,'MC-histos.root')
      ut.readHists(hData,'Data-histos.root')
# plot mass and sigma of Jpsi as function of y for data and MC 
   results = {}
   cases   = {}
   cases['HighMass-10GeV']   = [hMC,  'mc-'+fitMethod+'_'+proj+'HighMass-10GeV']
   cases['HighMass-Cascade'] = [hMC,  'mc-'+fitMethod+'_'+proj+'HighMass-Jpsi']
   cases['HighMass-P8']      = [hMC,  'mc-'+fitMethod+'_'+proj+'HighMass-JpsiP8']
   cases['10GeV']            = [hMC,  'mc-'+fitMethod+'_'+proj+'10GeV']
   cases['Data']             = [hData, fitMethod+'_'+proj]
#
   colors = {}
   colors['HighMass-10GeV']      = [ROOT.kCyan-2,24]
   colors['HighMass-Cascade']    = [ROOT.kMagenta,23]
   colors['HighMass-P8']         = [ROOT.kRed,22]
   colors['10GeV']               = [ROOT.kCyan,24]
   colors['Data']                = [ROOT.kBlue,21]
   fM = {'CB':{'signal':1,'mass':2,'sigma':3},'B':{'signal':7,'mass':8,'sigma':9},'G':{'signal':7,'mass':8,'sigma':9}}
   params,funTemplate = getFitDictionary(fitMethod)
   for c in cases:
       print "high mass position and width for ",c
       b = 'MCbins'
       if c=='Data': b='bins'
       fName = b
       tmp = c.split('-')
       if len(tmp)>1: 
           fName+=tmp[0]
           xx = cases[c][1].split('-')[2]
           fName += '-'
       else:
           fName=c+'-diMuonBins_'
           xx=''
       fName += fitMethod+'_'+proj+xx
       print "--> opening ",fName+'.root'
       fx = ROOT.TFile(fName+'.root')
       ROOT.gROOT.cd()
       if c.find('High') == 0:
          cName = fName
       else:
          if c=='Data': cName = 'bins'+fitMethod+'_'+proj
          else:         cName = 'MCbins'+fitMethod+'_'+proj+c
       hMC[cName] = fx.Get(cName).Clone(cName)
       hMC[cName].SetTitle(cName)
       hMC[cName].Draw()
       nx,ny = getNxNy(hMC[cName])
       ut.bookCanvas(hMC,'res_'+cName,'res-'+cName,hMC[cName].GetWw(),hMC[cName].GetWh(),nx,ny)
       print " canvas ",cName,nx,ny,hMC[cName].GetWw(),hMC[cName].GetWh(),getNxNy(hMC['res_'+cName])
       if c=='HighMass-10GeV':
              lName = cName.replace('HighMass','LowMass')
              print "--> opening ",lName+'.root'
              fx = ROOT.TFile(lName+'.root')
              ROOT.gROOT.cd()
              hMC[lName] = fx.Get(lName).Clone(lName)
              hMC[lName].SetTitle(lName)
              hMC[lName].Draw()
              print " canvas ",lName
       results[c]={}
       k=0
       while k<100:
         hk = cases[c][1]+str(k)
         if not cases[c][0].has_key(hk): break
         hz = cases[c][0][cases[c][1]+str(k)]
         N  = hz.GetEntries()
         if withFitResult: 
          fr = cases[c][0]['FitResults-'+hk]
          mass = [fr.Parameter(fM[fitMethod]['mass']), fr.ParError(fM[fitMethod]['mass'])]
          sigm = [fr.Parameter(fM[fitMethod]['sigma']),fr.ParError(fM[fitMethod]['sigma'])]
          prob = fr.Prob()
         else:
          if cases[c][1].find('mc')==0: fName = 'mc-Fun'+cases[c][1].replace('mc-','')+str(k)
          else: fName = 'Fun'+cases[c][1]+str(k)
          hFun = hz.GetFunction(fName)
          mass = [hFun.GetParameter(fM[fitMethod]['mass']), hFun.GetParError(fM[fitMethod]['mass'])]
          sigm = [hFun.GetParameter(fM[fitMethod]['sigma']),hFun.GetParError(fM[fitMethod]['sigma'])]
          prob = hFun.GetProb()
          hMC[fName] = ROOT.TF1(fitMethod,funTemplate['F'],0,10,funTemplate['N'])
          for j in range(funTemplate['N']):
            hMC[fName].SetParameter(j,hFun.GetParameter(j))
            hMC[fName].SetParError(j,hFun.GetParError(j))
# make pull plot
          hr = 'res_'+cases[c][1]+str(k)
          hMC[hr] = hz.Clone(hr)
          hMC[hr].Reset()
          hMC[hr].SetStats(0)
          hMC[hr].SetMinimum(-5.)
          hMC[hr].SetMaximum(5.)
          hMC[hr].SetMarkerStyle(29)
          hMC[hr].SetMarkerSize(1.3)
          bw = hz.GetBinWidth(1)
          for n in range(1,hMC[hr].GetNbinsX()+1):
             N = hz.GetBinContent(n)
             mu = hMC[fName].Integral(hz.GetBinCenter(n)-bw/2.,hz.GetBinCenter(n)+bw/2.)/bw
             res =  N - mu
             #logL = 2*(mu-N+N*ROOT.TMath.Log(N/mu))
             #print hz.GetName(),fName,n,mu,N,logL,res
             pull = -9999.
             if N>0: pull = res/(hz.GetBinError(n))
             hMC[hr].SetBinContent(n,pull)
             hMC[hr].SetBinError(n,0)
          hMC['res_'+cName].cd(k+1)
          hMC[hr].Draw('P')
         hS =  cases[c][0][cases[c][1]+'-Jpsi']
         NS   = [hS.GetBinContent(k+1), hS.GetBinError(k+1)]
         ybin = hz.GetName().split(proj)[1]
         tmp = hz.GetTitle().split(' ')
         yrange = tmp[len(tmp)-1]
         print "%20s : %5.2F +/- %5.2F   %5.2F +/- %5.2F |   %10.2F +/- %5.2F  %10.2F +/- %5.2F"%(\
         yrange,mass[0],mass[1],sigm[0],sigm[1],NS[0],NS[1],N,ROOT.TMath.Sqrt(N))
         if c=='10GeV':
           y =  cases[c][1]+str(k)
           hz = cases[c][0][y.replace('10GeV','HighMass-10GeV')]
           N  = hz.GetEntries()
           pull = (NS[0]-N) / (N+1E-9)
         else:
           pull = (NS[0]-N) / (N+1E-9)
         results[c][yrange]=[mass[0],mass[1],sigm[0],sigm[1],prob,pull]
         k+=1
       myPrint(hMC['res_'+cName],'pullPlot_'+cName)
       keys = results[c].keys()
       keys.sort()
       xmin = float(keys[0].split('<')[0])
       xmax = float(keys[len(keys)-1].split('<')[2])
       ut.bookHist(hMC,'massVs'+cases[c][1],'fitted mass as function of '     +proj+';'+unit[proj]+';M [GeV/c^{2}]', len(keys),xmin,xmax)
       ut.bookHist(hMC,'sigVs'+cases[c][1], 'fitted sigma as function of '    +proj+';'+unit[proj]+';#sigma [GeV/c^{2}]',len(keys),xmin,xmax)
       ut.bookHist(hMC,'probVs'+cases[c][1], 'fit probability as function of '+proj+';'+unit[proj]+';prob',len(keys),xmin,xmax)
       ut.bookHist(hMC,'pullSignalVs'+cases[c][1], 'fitted Signal - MC truth '+proj+';'+unit[proj]+';#Delta',len(keys),xmin,xmax)
       n=1
       for yrange in keys:
            hMC['massVs'+cases[c][1]].SetBinContent(n,results[c][yrange][0])
            hMC['massVs'+cases[c][1]].SetBinError(n,results[c][yrange][1])
            hMC['sigVs' +cases[c][1]].SetBinContent(n,results[c][yrange][2])
            hMC['sigVs' +cases[c][1]].SetBinError(n,results[c][yrange][3])
            hMC['probVs'+cases[c][1]].SetBinContent(n,results[c][yrange][4])
            hMC['pullSignalVs'+cases[c][1]].SetBinContent(n,results[c][yrange][5])
            n+=1
   ut.bookCanvas(hMC,'Fitsystematics-'+tag+'_'+proj,'Fitsystematics-'+tag+'_'+proj,1200,2400,1,4)
   l = 1
   ptype = {'mass':'','sig':'','prob':'PL','pullSignal':'P'}
   hMC['Line1']=ROOT.TLine(0.2,0.0,2.0,0.0)
   hMC['Line31']=ROOT.TLine(0.2,3.097,2.0,3.1)
   canvas = hMC['Fitsystematics-'+tag+'_'+proj]
   for x in ptype:
      tc = canvas.cd(l)
      l+=1
      if x=='prob':
        hMC[x+'Vs'+cases['Data'][1]].SetMinimum(0.01)
        hMC[x+'Vs'+cases['Data'][1]].SetMaximum(1.5)
        tc.SetLogy(1)
      elif x=='sig':
        hMC[x+'Vs'+cases['Data'][1]].SetMinimum(0.08)
        hMC[x+'Vs'+cases['Data'][1]].SetMaximum(0.7)
      elif x=='pullSignal':
        hMC[x+'Vs'+cases['10GeV'][1]].SetMinimum(-0.1)
        hMC[x+'Vs'+cases['10GeV'][1]].SetMaximum(0.1)
        hMC[x+'Vs'+cases['10GeV'][1]].Draw(ptype[x])
      else:
        hMC[x+'Vs'+cases['Data'][1]].SetMinimum(2.8)
        hMC[x+'Vs'+cases['Data'][1]].SetMaximum(3.4)
      if x!='pullSignal' : hMC[x+'Vs'+cases['Data'][1]].Draw(ptype[x])
      if x=='prob': hMC['L'+x+'Vs'+proj]=ROOT.TLegend(0.71,0.19,0.88,0.47)
      else: hMC['L'+x+'Vs'+proj]=ROOT.TLegend(0.36,0.17,0.66,0.42)
      for c in cases:
        if x=='prob' and c.find('Mass')>0: continue 
        if x=='pullSignal' and  not c.find('Data')<0: continue
        if x=='pullSignal':   hMC['Line1'].Draw('same')
        if x=='mass':   hMC['Line31'].Draw('same')
        hMC[x+'Vs'+cases[c][1]].SetLineColor(colors[c][0])
        hMC[x+'Vs'+cases[c][1]].SetMarkerStyle(colors[c][1])
        hMC[x+'Vs'+cases[c][1]].SetMarkerColor(colors[c][0])
        hMC[x+'Vs'+cases[c][1]].SetStats(0)
        hMC[x+'Vs'+cases[c][1]].Draw(ptype[x]+'same')
        hMC['L'+x+'Vs'+proj].AddEntry( hMC[x+'Vs'+cases[c][1]],c,'PL' )
      hMC['L'+x+'Vs'+proj].Draw()
   os.chdir(topDir)
   myPrint(canvas,'Fitsystematics-'+tag+'_'+proj)
# plot 10GeV low mass normalized with data
   trackEffFudgeFactor = 1+2*simpleEffCorMu
   MCnorm = dataStats/MCStats['10GeV'] / trackEffFudgeFactor
   nx,ny = getNxNy(hMC[lName])
   ut.bookCanvas(hMC,'norm-'+lName,'norm-'+lName,hMC[lName].GetWw(),hMC[lName].GetWh(),nx,ny)
   cName = 'bins'+fitMethod+'_'+proj
   ROOT.gROOT.cd()
   for j in range(len(hMC[lName].GetListOfPrimitives())):
      tc = hMC['norm-'+lName].cd(j+1)
      p = hMC[lName].GetListOfPrimitives()[j]
      hp = 'mc-'+fitMethod+'_'+proj+'LowMass-10GeV'+str(j)
      if not p.FindObject(hp): continue
      hMC['norm-'+hp] = p.FindObject(hp).Clone('norm-'+hp)
      hMC['norm-'+hp].Scale(MCnorm)
      hMC['norm-'+hp].SetStats(0)
      hMC['norm-'+hp].SetLineColor(ROOT.kMagenta)
      hMC['norm-'+hp].GetFunction("mc-Fun"+fitMethod+"_"+proj+"LowMass-10GeV"+str(j)).SetBit(ROOT.TF1.kNotDraw)
      p = hMC[cName].GetListOfPrimitives()[j]
      hd = fitMethod+'_'+proj+str(j)
      hMC['norm-'+hd] = p.FindObject(hd).Clone('norm-'+hd)
      hMC['norm-'+hd].Draw()
      hMC['norm-'+hp].Draw('same')
   myPrint(hMC['norm-'+lName],'DataWithLowMassMC-'+tag+'_'+proj)

def JpsiSysIncludingDY(ptCut=1.0,pmin=20.,BDTCut=None, muID=2,withWeight=True,dyMean=2.0):
   formating='5.3F'
   tmplate = 'muID'+str(muID)+'_'+'XXX-'+str(ptCut)+'_'+str(pmin)+'_DY'+str(dyMean)
   if BDTCut: tmplate += '_BDT'
   if withWeight: tmplate += '_wp6'

   hData['results'] = {}
   dyRange = [0.0,1.0,2.0,4.0]
   for dy in dyRange:
      hData['results'][dy] =  JpsiAcceptanceSys(ptCut,pmin,BDTCut,muID,withWeight,DYxsec=dy)
   fitMethod = 'B'
   keys = hData['results'][0.0]["xSec"]['av'+fitMethod].keys()
   keys.sort()
   print "    bin        xsec   stat   sys   newsys      xsec0  xsec1  xsec4 "
   newSys={}
   for k in keys:
     xsec={}
     for dy in dyRange:
         R = hData['results'][dy]["xSec"]['av'+fitMethod][k]
         xsec[dy] = [R[2],R[3],R[4]]
     txt = "%3.2F - %3.2F : %"+formating+"  %"+formating+"  %"+formating+"  %"+formating+"       %"+formating+"  %"+formating+"  %"+formating
     newSys[k] = abs(xsec[1.0][0]-xsec[4.0][0])/4.
     print txt%(R[0],R[1],xsec[dyMean][0],xsec[dyMean][1],xsec[dyMean][2],newSys[k],xsec[0.0][0],xsec[1.0][0],xsec[4.0][0])
#
   tag = tmplate.replace('XXX',fitMethod)
   f = ROOT.TFile(tag+'/data_YieldsEffCorrectedWithNA50.root')
   ut.bookCanvas(hMC,'Final',' ',1200,900,1,1)
   hMC['dummy']=f.Get('dummy').Clone('dummy')
   ROOT.gROOT.cd()
   for x in hMC['dummy'].GetListOfPrimitives():
      if x.ClassName().find('TH1')<0: continue
      hMC[x.GetName()] = hMC['dummy'].FindObject(x.GetName()).Clone(x.GetName())
   hMC['B_ycor1C-Jpsi_effCorrected_average']=hMC['B_ycor1C-Jpsi_effCorrected_P8prim'].Clone('B_ycor1C-Jpsi_effCorrected_average')
   hMC['B_ycor1C-Jpsi_effCorrected_average'].Reset()
   av = hMC['B_ycor1C-Jpsi_effCorrected_average']
   av.SetTitle(';y_{CMS};#sigma nb/%4.2F'%(av.GetBinWidth(1)))
   print 'Cross section results'
   integratedNumber = [0,0,0]
   Ilow = 0.35
   Imax = 0.65
   j=1
   for k in keys:
       R = hData['results'][2.0]["xSec"]['av'+fitMethod][k]
       binMin,binMax = R[0],R[1]
       Xsec = R[2]
       statErrXsec = R[3]
       sysErrXsec  = ROOT.TMath.Sqrt(R[4]**2+newSys[k]**2)
       totalError  = ROOT.TMath.Sqrt(statErrXsec**2+sysErrXsec**2)
       av.SetBinContent(j,Xsec)
       av.SetBinError(j,totalError)
       NXsecNA50   = R[5]
       EXsecNA50   = R[6]
       ratio       = (Xsec/NXsecNA50)
       ratioError  = ROOT.TMath.Sqrt(  (statErrXsec**2+sysErrXsec**2)/NXsecNA50**2  + ratio**2*EXsecNA50**2/NXsecNA50**2   )
       print '%5.2F - %5.2F | %5.2F +/- %5.2F +/-%5.2F | %5.2F +/-%5.2F'%(av.GetBinLowEdge(j),av.GetBinLowEdge(j)+av.GetBinWidth(j),Xsec*1000,statErrXsec*1000,sysErrXsec*1000,ratio,ratioError)
       if  binMax>Ilow and binMax<Imax :
            integratedNumber[0]+=Xsec
            integratedNumber[1]+=statErrXsec**2
            integratedNumber[2]+=sysErrXsec**2
       j+=1
   frac = fGlobal['etaNA50'].Integral(0.3,0.6)/fGlobal['etaNA50'].Integral(-0.425,0.575)
   NXsecNA50 = frac * NA50crossSection[0]
   EXsecNA50 = frac * NA50crossSection[1]
   print "integrated result %5.2F - %5.2F | %5.2F +/- %5.2F +/-%5.2F | NA50 %5.2F +/-%5.2F"%(Ilow,Imax,integratedNumber[0],
         ROOT.TMath.Sqrt(integratedNumber[1]),ROOT.TMath.Sqrt(integratedNumber[2]),NXsecNA50,EXsecNA50)
   for x in ['Y_Cascade_scaled','Y_P8prim_scaled']:
     hMC[x].SetStats(0)
     hMC[x].Scale(1./(lumi*1000.))
   crossSection = 3.994
   fGlobal['etaNA50'].SetParameter(0,1.)
   norm = fGlobal['etaNA50'].Integral(-0.425,0.575)
   fGlobal['etaNA50'].SetParameter(0,crossSection/norm*av.GetBinWidth(1))
   av.SetMaximum(0.9)
   av.SetMinimum(0.001)
   av.SetLineWidth(2)
   av.SetMarkerStyle(20)
   av.SetLineColor(ROOT.kBlue)
   av.SetMarkerColor(ROOT.kBlue)
   av.SetStats(0)
   tc = hMC['Final'].cd()
   tc.SetLogy(1)
   av.Draw()
   hMC['Y_Cascade_scaled'].Draw('same')
   hMC['Y_P8prim_scaled'].Draw('same')
   fGlobal['etaNA50'].DrawF1(0.,2.0,'same')
   hMC['Lfinal']=ROOT.TLegend(0.25,0.3,0.51,0.55)
   hMC['Lfinal'].AddEntry( hMC["Y_P8prim_scaled"],'Pythia8 primary scaled','PL' )
   hMC['Lfinal'].AddEntry( hMC["Y_Cascade_scaled"],'Pythia6 cascade scaled','PL' )
   hMC['Lfinal'].AddEntry( av,'muflux measurement','PL' )
   hMC['Lfinal'].AddEntry( hMC["etaNA50"],'NA50 parametrization','PL' )
   hMC['Lfinal'].Draw()
   hMC['Final'].Update()
   myPrint(hMC['Final'],'FinalResultJpsi_'+tmplate)
   myCopy('FinalResultJpsi_'+tmplate+'.png')
   myCopy('FinalResultJpsi_'+tmplate+'.pdf')
# max y for J/psi:
   pz = 400.
   E = ROOT.TMath.Sqrt(PDG.GetParticle(443).Mass()**2+pz**2)
   print "max ycm for Jpsi =", rapidity(E,pz)-yBeam()

def JpsiAcceptanceSys(ptCut=1.0,pmin=20.,BDTCut=None, muID=2,withWeight=True,DYxsec=2.):
   formating='5.2F'
   hname = "data_YieldsEffCorrectedWithNA50.root"
   results = {}
   results["xSec"] = {}
   fM = ['CB', 'B', 'G'] #,'GE']
   tmplate = 'muID'+str(muID)+'_'+'XXX-'+str(ptCut)+'_'+str(pmin)+'_DY'+str(DYxsec)
   if BDTCut: tmplate += '_BDT'
   if withWeight: tmplate += '_wp6'
   for fitMethod in fM:
      tag = tmplate.replace('XXX',fitMethod)
      results[tag]={'Cascade':{},'P8prim':{}}
      print "ptCut = %5.2F, yields for fit with %s"%(ptCut,fitMethod)
      f = ROOT.TFile(tag+'/'+hname)
      print "open ",tag+'/'+hname
      for x in f.dummy.GetListOfPrimitives():
         if x.GetName().find("effAndResolCorrected_Cascade")>0: c='Cascade'
         elif x.GetName().find("effAndResolCorrected_P8prim")>0: c='P8prim'
         else: continue
         for n in range(1,x.GetNbinsX()+1):
             if x.GetBinCenter(n) < 0.2: continue
             results[tag][c][x.GetBinCenter(n)] = [x.GetBinContent(n),x.GetBinError(n)]
# difference between using Cascade or P8prim for eff correction
# use fitMethod 'B' as default
   fitMethod = 'B'
   tag = tmplate.replace('XXX',fitMethod)
   results[tag]['sysError_effAndResolCorrection']={}
   for n in results[tag]['Cascade']:
      NCascade = results[tag]['Cascade'][n][0]
      NP8prim  = results[tag]['P8prim'][n][0]
      results[tag]['sysError_effAndResolCorrection'][n] =  ROOT.TMath.Sqrt(2.)*abs(NCascade-NP8prim)/(NCascade+NP8prim+1E-10)
      # sys error = standard deviation
   ikeys = results[tag]['sysError_effAndResolCorrection'].keys()
   ikeys.sort()
   ut.bookHist(hMC,'sysErrorMCgenerator','sysError MC generator',100,0.,50.)
   for i in ikeys:
       print "sysError MC generator  %5.3F  %5.2F  %5.2F  %5.2F%%"%(i,results[tag]['Cascade'][i][0],results[tag]['P8prim'][i][0]
            ,results[tag]['sysError_effAndResolCorrection'][i]*100 )
       rc = hMC['sysErrorMCgenerator'].Fill(results[tag]['sysError_effAndResolCorrection'][i]*100)
   print "sysErrorMCgenerator: Average difference between true and wrong MC model: %5.2F%% +/- %5.2F%%"%(hMC['sysErrorMCgenerator'].GetMean(),hMC['sysErrorMCgenerator'].GetRMS())
# difference between fitMethods
# use 'Cascade' as default
   results[tag]['sysError_fitMethod']={}
   fM = ['CB', 'B']
   ut.bookHist(hMC,'sysErrorfitMethod','sysError fitMethod',100,0.,50.)
   for i in ikeys:
       mean = 0
       for fitMethod in fM: mean += results[tmplate.replace('XXX',fitMethod)]['Cascade'][i][0]
       mean = mean/len(fM)
       rms = 0
       for fitMethod in fM: rms += (results[tmplate.replace('XXX',fitMethod)]['Cascade'][i][0] - mean)**2
       rms = ROOT.TMath.Sqrt(rms / (len(fM)-1.))
       results[tag]['sysError_fitMethod'][i] = rms / (mean+1E-10)
       rc = hMC['sysErrorfitMethod'].Fill(results[tag]['sysError_fitMethod'][i]*100)
       print "sysError_fitMethod %5.3F  %5.2F  %5.2F  %5.2F"%(i,results[tmplate.replace('XXX','B')]['Cascade'][i][0],
            results[tmplate.replace('XXX','CB')]['Cascade'][i][0],results[tmplate.replace('XXX','G')]['Cascade'][i][0])
   for i in ikeys: print "%5.3F  %5.2F%%  %5.2F%%"%(i,results[tag]['sysError_effAndResolCorrection'][i]*100,
                      results[tag]['sysError_fitMethod'][i]*100)
   results[tag]['sysError']={}
   for i in ikeys: results[tag]['sysError'][i]=ROOT.TMath.Sqrt(results[tag]['sysError_fitMethod'][i]**2+
                                results[tag]['sysError_effAndResolCorrection'][i]**2)
   print "sysError_fitMethod: Average difference between Bukin and CB fit model: %5.2F%% +/- %5.2F%%"%(hMC['sysErrorfitMethod'].GetMean(),hMC['sysErrorfitMethod'].GetRMS())
# track efficiency correction, MC events are deweighted by 2%. 
   simpleEffCorMu = 0.021
   trackEffFudgeFactor = 1+2*simpleEffCorMu
   trackEffSysError    = 2*0.033
   epsilon = 0.01
   ybinWidth = 0.1
   formating='5.3F'
   Nsignal = {}
   crossSection={}
   for fitMethod in ['B','CB']:
     crossSection[fitMethod]={}
     tag  = tmplate.replace('XXX',fitMethod)
     tagB = tmplate.replace('XXX','B')
     Nsignal[fitMethod]={}
     for MC in ['Cascade','P8prim']:
      print "results for ",fitMethod,' using ',MC
      Nsignal[fitMethod][MC]={}
      crossSection[fitMethod][MC]={}
      for i in ikeys:
       Nsignal[fitMethod][MC][i]= [results[tag][MC][i][0]*trackEffFudgeFactor  + 1E-10, results[tag][MC][i][1]*trackEffFudgeFactor]
       systematicErrors  = [elumi/lumi,trackEffSysError,results[tagB]['sysError'][i]]
       sysErr  = 0
       for x in systematicErrors: sysErr+=x**2
       sysErr = ROOT.TMath.Sqrt(sysErr)
       Xsec = Nsignal[fitMethod][MC][i][0] / lumi / 1000.
       statErrXsec = Nsignal[fitMethod][MC][i][1]/Nsignal[fitMethod][MC][i][0] * Xsec
       sysErrXsec  = Xsec * sysErr
       binMin = i-ybinWidth/2.
       binMax = i+ybinWidth/2.
       frac = fGlobal['etaNA50'].Integral(binMin,binMax)/fGlobal['etaNA50'].Integral(-0.425,0.575)
       NXsecNA50 = frac * NA50crossSection[0]
       EXsecNA50 = frac * NA50crossSection[1]
       txt = "%3.2F - %3.2F : %"+formating+"  %"+formating+"  %"+formating+"        %"+formating+"  %"+formating+" | %5.2F"
       totalError=ROOT.TMath.Sqrt(statErrXsec**2+sysErrXsec**2+EXsecNA50**2)
       sigmaPull = (Xsec-NXsecNA50)/totalError
       print txt%(binMin,binMax,Xsec,statErrXsec,sysErrXsec,NXsecNA50,EXsecNA50,sigmaPull)
       crossSection[fitMethod][MC][i]=[binMin,binMax,Xsec,statErrXsec,sysErrXsec,NXsecNA50,EXsecNA50]
     print "average between P8prim and Cascade"
     results["xSec"]['av'+fitMethod]={}
     for i in ikeys:
       txt = "%3.2F - %3.2F : %"+formating+"  %"+formating+"  %"+formating+"        %"+formating+"  %"+formating+" | %5.2F"
       binMin,binMax = crossSection[fitMethod]['Cascade'][i][0],crossSection[fitMethod]['Cascade'][i][1]
       Xsec = (crossSection[fitMethod]['Cascade'][i][2]+crossSection[fitMethod]['P8prim'][i][2])/2.
       statErrXsec = (crossSection[fitMethod]['Cascade'][i][3]+crossSection[fitMethod]['P8prim'][i][3])/2.
       sysErrXsec  = (crossSection[fitMethod]['Cascade'][i][4]+crossSection[fitMethod]['P8prim'][i][4])/2.
       NXsecNA50   = (crossSection[fitMethod]['Cascade'][i][5]+crossSection[fitMethod]['P8prim'][i][5])/2.
       EXsecNA50   = (crossSection[fitMethod]['Cascade'][i][6]+crossSection[fitMethod]['P8prim'][i][6])/2.
       totalError  = ROOT.TMath.Sqrt(statErrXsec**2+sysErrXsec**2+EXsecNA50**2)
       sigmaPull   = (Xsec-NXsecNA50)/totalError
       print txt%(binMin,binMax,Xsec,statErrXsec,sysErrXsec,NXsecNA50,EXsecNA50,sigmaPull)
       results["xSec"]['av'+fitMethod][int(binMin*10)]=[binMin,binMax,Xsec,statErrXsec,sysErrXsec,NXsecNA50,EXsecNA50,sigmaPull]
#
   print " cross check, sys error from MC"
   for i in ikeys:
     binMin = i-ybinWidth/2.
     binMax = i+ybinWidth/2.
     S = ROOT.TGraph()
     n=0
     for fitMethod in ['B','CB']:
       for MC in ['Cascade','P8prim']:
          S.SetPoint(n,Nsignal[fitMethod][MC][i][0],1.)
          n+=1
     print "%3.2F - %3.2F :    MC: %5.2F  Data: %5.2F "%(binMin,binMax, results[tagB]['sysError'][i],S.GetRMS()/S.GetMean())
   if 1>0:    return results
   fitMethod = 'B'
   tag = tmplate.replace('XXX',fitMethod)
   f = ROOT.TFile(tag+'/data_YieldsEffCorrectedWithNA50.root')
   ut.bookCanvas(hMC,'Final',' ',1200,900,1,1)
   hMC['dummy']=f.Get('dummy').Clone('dummy')
   ROOT.gROOT.cd()
   for x in hMC['dummy'].GetListOfPrimitives():
      if x.ClassName().find('TH1')<0: continue
      hMC[x.GetName()] = hMC['dummy'].FindObject(x.GetName()).Clone(x.GetName())
   hMC['B_ycor1C-Jpsi_effCorrected_average']=hMC['B_ycor1C-Jpsi_effCorrected_P8prim'].Clone('B_ycor1C-Jpsi_effCorrected_average')
   hMC['B_ycor1C-Jpsi_effCorrected_average'].Reset()
   j=1
   av = hMC['B_ycor1C-Jpsi_effCorrected_average']
   av.SetTitle(';y_{CMS};#sigma nb/%4.2F'%(av.GetBinWidth(1)))
   print 'Cross section results'
   integratedNumber = [0,0,0]
   Ilow = 0.35
   Imax = 0.65
   for i in ikeys:
       binMin,binMax = crossSection[fitMethod]['Cascade'][i][0],crossSection[fitMethod]['Cascade'][i][1]
       c = av.GetBinCenter(j)
       if c < av.GetBinLowEdge(j) or c>av.GetBinLowEdge(j)+av.GetBinWidth(j): print "error, entry out of bin",i,j,binMin,binMax,av.GetBinLowEdge(j)
       Xsec = (crossSection[fitMethod]['Cascade'][i][2]+crossSection[fitMethod]['P8prim'][i][2])/2.
       statErrXsec = (crossSection[fitMethod]['Cascade'][i][3]+crossSection[fitMethod]['P8prim'][i][3])/2.
       sysErrXsec  = (crossSection[fitMethod]['Cascade'][i][4]+crossSection[fitMethod]['P8prim'][i][4])/2.
       totalError  = ROOT.TMath.Sqrt(statErrXsec**2+sysErrXsec**2)
       av.SetBinContent(j,Xsec)
       av.SetBinError(j,totalError)
       NXsecNA50   = (crossSection[fitMethod]['Cascade'][i][5]+crossSection[fitMethod]['P8prim'][i][5])/2.
       EXsecNA50   = (crossSection[fitMethod]['Cascade'][i][6]+crossSection[fitMethod]['P8prim'][i][6])/2.
       ratio       = (Xsec/NXsecNA50)
       ratioError  = ROOT.TMath.Sqrt(  (statErrXsec**2+sysErrXsec**2)/NXsecNA50**2  + ratio**2*EXsecNA50**2/NXsecNA50**2   )
       print '%5.2F - %5.2F | %5.2F +/- %5.2F +/-%5.2F | %5.2F +/-%5.2F'%(av.GetBinLowEdge(j),av.GetBinLowEdge(j)+av.GetBinWidth(j),Xsec*1000,statErrXsec*1000,sysErrXsec*1000,ratio,ratioError)
       if  binMax>Ilow and binMax<Imax :
            integratedNumber[0]+=Xsec
            integratedNumber[1]+=statErrXsec**2
            integratedNumber[2]+=sysErrXsec**2
       j+=1
   frac = fGlobal['etaNA50'].Integral(0.3,0.6)/fGlobal['etaNA50'].Integral(-0.425,0.575)
   NXsecNA50 = frac * NA50crossSection[0]
   EXsecNA50 = frac * NA50crossSection[1]
   print "integrated result %5.2F - %5.2F | %5.2F +/- %5.2F +/-%5.2F | NA50 %5.2F +/-%5.2F"%(Ilow,Imax,integratedNumber[0],
         ROOT.TMath.Sqrt(integratedNumber[1]),ROOT.TMath.Sqrt(integratedNumber[2]),NXsecNA50,EXsecNA50)
   for x in ['Y_Cascade_scaled','Y_P8prim_scaled']:
     hMC[x].SetStats(0)
     hMC[x].Scale(1./(lumi*1000.))
   crossSection = 3.994
   fGlobal['etaNA50'].SetParameter(0,1.)
   norm = fGlobal['etaNA50'].Integral(-0.425,0.575)
   fGlobal['etaNA50'].SetParameter(0,crossSection/norm*av.GetBinWidth(1))
   av.SetMaximum(0.9)
   av.SetMinimum(0.001)
   av.SetLineWidth(2)
   av.SetMarkerStyle(20)
   av.SetLineColor(ROOT.kBlue)
   av.SetMarkerColor(ROOT.kBlue)
   av.SetStats(0)
   tc = hMC['Final'].cd()
   tc.SetLogy(1)
   av.Draw()
   hMC['Y_Cascade_scaled'].Draw('same')
   hMC['Y_P8prim_scaled'].Draw('same')
   fGlobal['etaNA50'].DrawF1(0.,2.0,'same')
   hMC['Lfinal']=ROOT.TLegend(0.25,0.3,0.51,0.55)
   hMC['Lfinal'].AddEntry( hMC["Y_P8prim_scaled"],'Pythia8 primary scaled','PL' )
   hMC['Lfinal'].AddEntry( hMC["Y_Cascade_scaled"],'Pythia6 cascade scaled','PL' )
   hMC['Lfinal'].AddEntry( av,'muflux measurement','PL' )
   hMC['Lfinal'].AddEntry( hMC["etaNA50"],'NA50 parametrization','PL' )
   hMC['Lfinal'].Draw()
   hMC['Final'].Update()
   myPrint(hMC['Final'],'FinalResultJpsi_'+tmplate)
   myCopy('FinalResultJpsi_'+tmplate+'.png')
   myCopy('FinalResultJpsi_'+tmplate+'.pdf')
# max y for J/psi:
   pz = 400.
   E = ROOT.TMath.Sqrt(PDG.GetParticle(443).Mass()**2+pz**2)
   print "max ycm for Jpsi =", rapidity(E,pz)-yBeam()
   return results
def EffCorrConsistencyCheck(fM='B',ptCut=1.0,pmin=20.,BDTCut=None, muID=2,withWeight=False):
   tag = 'muID'+str(muID)+'_'+fM+'-'+str(ptCut)+'_'+str(pmin)
   if BDTCut: tag += '_BDT'
   if withWeight: tag += '_wp6'
   hnameDict = {'HighMass-P8YieldsEffCorrected':{'gen':'Y_P8prim_scaledHighMass-P8','cor':'mc-'+fM+'_ycor1CHighMass-JpsiP8-Jpsi_effAndResolCorrected_P8prim'},
                'HighMass-CascadeYieldsEffCorrected':{'gen':'Y_Cascade_scaledHighMass-Cascade','cor':'mc-'+fM+'_ycor1CHighMass-Jpsi-Jpsi_effAndResolCorrected_Cascade'}}
   for hname in hnameDict:
       hMC['f'+hname] = ROOT.TFile(tag+'/'+hname+'.root')
       ROOT.gROOT.cd()
       ut.bookCanvas(hMC,hname,hname,900,600,1,1)
       tx = hMC[hname].cd()
       print "open ",tag+'/'+hname
       tc = hMC['f'+hname].Get(hname+'Canvas')
       c = 'Cascade'
       if hname.find('P8')>0: c = 'P8prim'
       print hname,c
       hMC['gen'+c] = tc.FindObject(hnameDict[hname]['gen']).Clone(hnameDict[hname]['gen'])
       hMC['gen'+c].SetTitle(';y_{CM};N_{J/#psi}')
       hMC['gen'+c].SetStats(0)
       hMC['gen'+c].GetXaxis().SetRangeUser(0.2,2.0)
       hMC['gen'+c].Draw()
       hMC['cor'+c] = tc.FindObject(hnameDict[hname]['cor']).Clone(hnameDict[hname]['cor'])
       hMC['cor'+c].SetStats(0)
       hMC['cor'+c].Draw('same')
       tx.Update()
   for hname in hnameDict:
       tx = hMC[hname].cd()
       c = 'Cascade'
       if hname.find('P8')>0: c = 'P8prim'
       hMC['gen'+c].SetMaximum(hMC['cor'+c].GetBinContent(hMC['cor'+c].FindBin(0.2))*1.1)
       hMC['gen'+c].GetYaxis().SetMaxDigits(2)
       hMC['gen'+c].Draw()
       hMC['cor'+c].Draw('same')
       tx.Update()
       myPrint(hMC[hname],hname+tag)


def lowMassAcceptance(ptCut=0.,pmin=20.0,muID=1):
 normalization = {}
 trackEffFudgeFactor = 1+2*simpleEffCorMu
 for x in MCStats: normalization[x] = dataStats/MCStats[x]/trackEffFudgeFactor 
#
 ut.bookHist(hMC,  'mc-YandPt1GeV_rec', 'rapidity of reconstructed ',  60, 0.,6., 80,0.,4. )
 ut.bookHist(hMC,  'mc-YandPt10GeV_rec','rapidity of reconstructed ',  60, 0.,6., 80,0.,4. )
 ut.bookHist(hData,'YandPt10GeV_rec','rapidity of reconstructed ',     60, 0.,6., 80,0.,4. )
 y_beam = yBeam()
 theCut = theJpsiCut('mcor',False,ptCut,pmin,300.,muID,BDTCut)
 theCut = "chi21*chi22<0&&abs(chi21)<0.9&&abs(chi22)<0.9&&p1>10.0&&p2>10.0"
 # ycor1C = '0.5*log( ( sqrt(0.8*0.8+pcor*pcor) + sqrt(pcor*pcor-ptcor*ptcor) )/( sqrt(0.8*0.8+pcor*pcor) - sqrt(pcor*pcor-ptcor*ptcor) ))-'+str(y_beam)
 ycor1C = 'ycor-'+str(y_beam)
 for x in MCStats: 
    hMC[x].Draw(ycor1C+":ptcor>>mc-YandPt"+x+"_rec",'mcor>0.3&&mcor<2.&&'+theCut)
    hMC["mc-YandPt"+x+"_rec_norm"]=hMC["mc-YandPt"+x+"_rec"].Clone("mc-YandPt"+x+"_rec_norm")
    hMC["mc-YandPt"+x+"_rec_norm"].Scale(normalization[x])
    hMC["mc-YandPt"+x+"_rec_pt"]=hMC["mc-YandPt"+x+"_rec_norm"].ProjectionX("mc-YandPt"+x+"_rec_pt")
    hMC["mc-YandPt"+x+"_rec_y"]=hMC["mc-YandPt"+x+"_rec_norm"].ProjectionY("mc-YandPt"+x+"_rec_y")
 hData['f'].nt.Draw(ycor1C+":ptcor>>YandPt10GeV_rec",'mcor>0.3&&mcor<2.&&'+theCut)
 hData['YandPt10GeV_rec_pt']=hData['YandPt10GeV_rec'].ProjectionX('YandPt10GeV_rec_pt')
 hData['YandPt10GeV_rec_y']=hData['YandPt10GeV_rec'].ProjectionY('YandPt10GeV_rec_y')

def diMuonAnalysis(fm='B'):
 y_beam = yBeam()
 loadNtuples()
 sTreeData  = hData['f'].nt
# make normalization
    # covered cases: cuts = '',      simpleEffCor=0.024, simpleEffCorMu=0.024
    # covered cases: cuts = 'Chi2<', simpleEffCor=0.058, simpleEffCorMu=0.058
    # covered cases: cuts = 'All', simpleEffCor=0.058,   simpleEffCorMu=0.129
    # 1GeV mbias,      1.806 Billion PoT 
    # 10GeV MC,       66.02 Billion PoT 
    # using 626 POT/mu-event and preliminary counting of good tracks -> 12.63 -> pot factor 7.02
    # using 710 POT/mu-event, full field
# 
 hMC['weights'] = {'1GeV': MCStats['1GeV']/dataStats/(1+simpleEffCor*2),'10GeV':MCStats['10GeV']/dataStats/(1+simpleEffCor*2)}
#
 ptCutList = [0.0,0.5,0.8,0.9,1.0,1.1,1.2,1.3,1.4,1.5,1.6]
 theCutTemplate = theJpsiCut('m',True ,'XYZ',20.,300.,2,False)
 ut.bookHist(hMC, 'mc_theta','cos theta mother - daughter1',100,-1,1.)
 ut.bookHist(hMC, 'mc_thetaJ','cos theta mother - daughter1 Jpsi',100,-1,1.)
 ut.bookHist(hData, 'theta','cos theta mother - daughter1',100,-1,1.)
 ut.bookCanvas(hMC,'tTheta','costheta',900,600,1,1)
 ut.bookCanvas(hMC,'tMass','mass',900,600,1,1)
 hMC['mc_theta'].SetLineColor(ROOT.kRed)
 hMC['mc_thetaJ'].SetLineColor(ROOT.kMagenta)
 theCut = theCutTemplate.replace('XYZ','0')
 ROOT.gROOT.cd()
 myDraw('cosTheta>>mc_thetaJ',theCut+'&&Jpsi==443')
 myDraw('cosTheta>>mc_theta',theCut)
 sTreeData.Draw('cosTheta>>theta',theCut)
 hMC['tTheta'].cd(1)
 hMC['mc_theta'].Scale(1./hMC['mc_theta'].GetEntries())
 hMC['mc_thetaJ'].Scale(1./hMC['mc_thetaJ'].GetEntries())
 hData['theta'].Scale(1./hData['theta'].GetEntries())
 hMC['mc_theta'].Draw()
 hMC['mc_thetaJ'].Draw('same')
 hData['theta'].Draw('same')
 myPrint(hMC['tTheta'],'dimuon-theta')
 ut.bookHist(hMC, 'mc_IP','IP',100,0.,100.)
 ut.bookHist(hMC, 'mc_IPJ','IP',100,0.,100.)
 ut.bookHist(hData, 'IP','IP',100,0.,100.)
 ut.bookCanvas(hMC,'tIP','distance to target',900,600,1,1)
 hMC['mc_IP'].SetLineColor(ROOT.kRed)
 hMC['mc_IPJ'].SetLineColor(ROOT.kMagenta)
 myDraw('Ip1>>mc_IPJ',theCut+'&&Jpsi==443')
 myDraw('Ip1>>mc_IP',theCut)
 sTreeData.Draw('Ip1>>IP',theCut)
 myDraw('Ip2>>+mc_IPJ',theCut+'&&Jpsi==443')
 myDraw('Ip2>>+mc_IP',theCut)
 sTreeData.Draw('Ip2>>+IP',theCut)
 hMC['tIP'].cd()
 hMC['mc_IP'].Scale(1./hMC['mc_IP'].GetEntries())
 hMC['mc_IPJ'].Scale(1./hMC['mc_IPJ'].GetEntries())
 hData['IP'].Scale(1./hData['IP'].GetEntries())
 hMC['mc_IP'].Draw()
 hMC['mc_IPJ'].Draw('same')
 hData['IP'].Draw('same')
 myPrint(hMC['tIP'],'dimuon-IP')
 ut.bookHist(hMC, 'm_MC','inv mass;M [GeV/c^{2}]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
 ut.bookHist(hMC, 'm_MClow','inv mass;M [GeV/c^{2}]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
 hMC['dummy'].cd()
 colors = {221:ROOT.kBlue,223:ROOT.kCyan,113:ROOT.kGreen,331:ROOT.kOrange,333:ROOT.kRed,443:ROOT.kMagenta}
 nmax = 0
 for j in colors:
   pname = PDG.GetParticle(j).GetName()
   hname = 'Mass_'+pname.replace('/','')
   hMC[hname]=hMC['m_MClow'].Clone(hname)
   hMC[hname].SetTitle('inv mass '+PDG.GetParticle(j).GetName()+' ;M [GeV/c^{2}]')
   hMC[hname].SetLineColor(colors[j])
   hMC[hname].SetStats(0)
   myDraw('m>>'+hname,'Jpsi=='+str(j))
   if hMC[hname].GetMaximum()>nmax: nmax = hMC[hname].GetMaximum()
   hname = 'Masscor_'+pname.replace('/','')
   hMC[hname]=hMC['m_MClow'].Clone(hname)
   hMC[hname].SetTitle('inv mass '+PDG.GetParticle(j).GetName()+' ;M [GeV/c^{2}]')
   hMC[hname].SetLineColor(colors[j])
   hMC[hname].SetStats(0)
   myDraw('mcor>>'+hname,'Jpsi=='+str(j))
   if hMC[hname].GetMaximum()>nmax: nmax = hMC[hname].GetMaximum()
 for z in ['','cor']:
  first = True
  hMC['lMassMC'+z]=ROOT.TLegend(0.7,0.7,0.95,0.95)
  for j in colors:
    pname = PDG.GetParticle(j).GetName()
    hname = 'Mass'+z+'_'+pname.replace('/','')
    hMC[hname].SetStats(0)
    if first:
       first = False
       hMC[hname].SetMaximum(nmax*1.1)
       hMC[hname].SetTitle(';M [GeV/c^{2}]')
       hMC[hname].Draw()
    else:
       hMC[hname].Draw('same')
    hMC['lMassMC'+z].AddEntry(hMC[hname],pname,'PL')
  hMC['lMassMC'+z].Draw()
  myPrint(hMC['dummy'],'MCdiMuonMass'+z)

 # doesn't help really theCutTemplate +=  '&&abs(cosTheta)<0.8' 
 vText={'m':'inv mass and fits','mcor':'inv mass, dE and direction corrected, and fits','mcor2':'inv mass, direction corrected, and fits'}
 for v in vText:
  hMC['fitResult'+v]={}
  hData['fitResult'+v]={}
  for ptCut in ptCutList:
   sptCut = str(ptCut)
   hMC['fitResult'+v][ptCut] = {}
   hData['fitResult'+v][ptCut] = {}
#
   theCut =  theCutTemplate.replace('XYZ',sptCut)
   if v.find('mcor')==0: 
      theCut = theCut.replace('pt1','pt1cor')
      theCut = theCut.replace('pt2','pt2cor')
   ROOT.gROOT.cd()
   twoCBYieldFit(fm,'ycor',0.2,1.8,'y_{CMS}',theCut,nBins=1,printout=1,v=v)
   hData[v+'_'+sptCut]   = hData[fm+'_ycor0'].Clone(v+'_'+sptCut)
   for x in ['','lowMass','highMass','back']:
     hData['Fun_'+fm+sptCut+x] = hData['Fun'+fm+'_ycor0'+x].Clone('Fun'+fm+'_'+sptCut+x)
   fr = hData['FitResults-'+fm+'_ycor0']
   fun = hData[fm+'_ycor0'].GetFunction('Fun'+fm+'_ycor0')
   for n in range(fun.GetNpar()):   hData['fitResult'+v][ptCut][fun.GetParName(n)] = [fr.Parameter(n),fr.ParError(n)]
   hData['fitResult'+v][ptCut]['signal'] = [hData[fm+'_ycor-Jpsi'].GetBinContent(1),hData[fm+'_ycor-Jpsi'].GetBinError(1)]
# MC
   hMC['mc-'+v+'_'+sptCut] = hMC['mc-'+fm+'_ycor10GeV0'].Clone('mc-'+v+'_'+sptCut)
   fr = hMC['FitResults-mc-'+fm+'_ycor10GeV0']
   fun = hMC['mc-'+fm+'_ycor10GeV0'].GetFunction('mc-Fun'+fm+'_ycor10GeV0')
   for n in range(fun.GetNpar()):   hMC['fitResult'+v][ptCut][fun.GetParName(n)] = [fr.Parameter(n),fr.ParError(n)]
   hMC['fitResult'+v][ptCut]['signal'] = [hMC['mc-'+fm+'_ycor10GeV-Jpsi'].GetBinContent(1),hMC['mc-'+fm+'_ycor10GeV-Jpsi'].GetBinError(1)]
   hMC['mc-'+v+'_Jpsi_'+sptCut] = hMC['mc-'+fm+'_ycorHighMass-10GeV0'].Clone('mc-'+v+'_Jpsi_'+sptCut)
   hMC['mcP8-'+v+'_'+sptCut] = hMC['mc-'+fm+'_ycorHighMass-JpsiP80'].Clone('mcP8-'+v+'_'+sptCut)
   fr = hMC['FitResults-mc-'+fm+'_ycorHighMass-JpsiP80']
   fun = hMC['mc-'+fm+'_ycorHighMass-JpsiP80'].GetFunction('mc-Fun'+fm+'_ycorHighMass-JpsiP80')
   for n in range(fun.GetNpar()):   hMC['fitResult'+v][ptCut][fun.GetParName(n)] = [fr.Parameter(n),fr.ParError(n)]
   hMC['fitResult'+v][ptCut]['signalP8'] = [hMC['mc-'+fm+'_ycorHighMass-JpsiP8-Jpsi'].GetBinContent(1),hMC['mc-'+fm+'_ycorHighMass-JpsiP8-Jpsi'].GetBinError(1)]
   hMC['mcP8-'+v+'_Jpsi_'+sptCut] = hMC['mc-'+fm+'_ycorHighMass-JpsiP80'].Clone('mcP8-'+v+'_Jpsi_'+sptCut)
# same sign
   twoCBYieldFit(fm,'ycor',0.2,1.8,'y_{CMS}',theCut.replace('chi21*chi22<0','chi21*chi22>0'),nBins=1,printout=1,v=v)
   hData['SS-'+v+'_'+sptCut] = hData[fm+'_ycor0'].Clone('SS-'+v+'_'+sptCut)
   l = hData['SS-'+v+'_'+sptCut].GetListOfFunctions()
   l.Remove(hData['SS-'+v+'_'+sptCut].GetFunction('Fun'+fm+'_ycor0'))
   hMC['SS-mc-'+v+'_'+sptCut] = hMC['mc-'+fm+'_ycor10GeV0'].Clone('SS-mc-'+v+'_'+sptCut)
   l = hMC['SS-mc-'+v+'_'+sptCut].GetListOfFunctions()
   l.Remove(hMC['SS-mc-'+v+'_'+sptCut].GetFunction('mc-Fun'+fm+'_ycor10GeV0'))
   hData['SS-'+v+'_'+sptCut].SetLineColor(ROOT.kRed)
   hMC['SS-mc-'+v+'_'+sptCut].SetLineColor(ROOT.kRed)

  ut.bookCanvas(hMC,'fits'+v,vText[v],1800,800,5,4)
  j = 1
  for ptCut in  ptCutList:
   sptCut = str(ptCut)
   tc = hMC['fits'+v].cd(j)
   hMC['mc-'+v+'_Jpsi_'+sptCut].SetLineColor(ROOT.kMagenta)
   hMC['mc-'+v+'_Jpsi_'+sptCut].Draw('same')
   hMC['SS-mc-'+v+'_'+sptCut].Draw('same')
   tc.Update()
   stats = tc.GetPrimitive('stats')
   stats.SetOptFit(10111)
   stats.SetFitFormat('5.4g')
   stats.SetX1NDC(0.41)
   stats.SetY1NDC(0.41)
   stats.SetX2NDC(0.99)
   stats.SetY2NDC(0.84)
   tc.Update()
# data
   tc = hMC['fits'+v].cd(j+5)
   hData[v+'_'+sptCut].Draw()
   #if v=='mcor':
# psi(2S) 
    #myGauss.FixParameter(1,fitResult.Parameter(1))
    #myGauss.FixParameter(2,fitResult.Parameter(2))
    #myGauss.ReleaseParameter(9)
   hData['SS-'+v+'_'+sptCut].Draw('same')
   tc.Update()
   stats = tc.GetPrimitive('stats')
   stats.SetOptFit(10111)
   stats.SetFitFormat('5.4g')
   stats.SetX1NDC(0.41)
   stats.SetY1NDC(0.41)
   stats.SetX2NDC(0.99)
   stats.SetY2NDC(0.84)
   tc.Update()
   j+=1
   if j==6: j+=5
   hMC['tMass'].cd()
   hMC['mc-'+v+'_'+sptCut].Draw()
   hMC['SS-mc-'+v+'_'+sptCut].Draw('same')
   myPrint(hMC['tMass'],'mc_dimuon_'+v+sptCut)
   hData[v+'_'+sptCut].Draw()
   hData['SS-'+v+'_'+sptCut].Draw('same')
   myPrint(hMC['tMass'],'m_dimuon_'+v+sptCut)
  hMC['fits'+v].Update()
  myPrint(hMC['fits'+v],v+'_dimuon_all')
#
  param = {1:'signal',2:'Background',3:'Mass',4:'Sigma',5:'signalP8'}
  txt   = {1:'; #it{p}_{T}>X GeV/c; Nsignal',5:'; #it{p}_{T}>X GeV/c; NsignalP8',
           3:'; #it{p}_{T}>X GeV/c; M [GeV/c^{2}]',
           4:'; #it{p}_{T}>X GeV/c; #sigma [GeV/c^{2}]',
           2:'; #it{p}_{T}>X GeV/c; background'}
  choices = {'MC':hMC,'Data':hData}
  for c in choices:
   h=choices[c]
   for p in param:
    if c=='Data' and p==5:continue
    hname = 'evolution'+v+param[p]+c
    ut.bookHist(h,hname,v+' evolution of '+param[p]+txt[p],20,0., 2.)
    for ptCut in ptCutList:
        k = h[hname].FindBin(ptCut)
        if p==2:
           if c=='MC':
               nlow  = h['mc-'+v+'_'+str(ptCut)].FindBin(2.8)
               nhigh = h['mc-'+v+'_'+str(ptCut)].FindBin(3.5)
               back  = h['mc-'+v+'_'+str(ptCut)].GetEntries() - h['fitResult'+v][ptCut][param[1]][0]
           else:
               nlow  = h[v+'_'+str(ptCut)].FindBin(2.8)
               nhigh = h[v+'_'+str(ptCut)].FindBin(3.5)
               back  = h[v+'_'+str(ptCut)].GetEntries()  - h['fitResult'+v][ptCut][param[1]][0]
           h[hname].SetBinContent(k,back)
           h[hname].SetBinError(k,ROOT.TMath.Sqrt(back))
        else:
           h[hname].SetBinContent(k,h['fitResult'+v][ptCut][param[p]][0])
           h[hname].SetBinError(k,h['fitResult'+v][ptCut][param[p]][1])
  ut.bookCanvas(hMC,'evolutionC'+v,'evolution',1600,500,4,1)
  for p in param:
   j = p
   if p==5: continue
   tc = hMC['evolutionC'+v].cd(j)
   hname = 'evolution'+v+param[p]
   resetMinMax(hMC[hname+'MC'])
   resetMinMax(hData[hname+'Data'])
   hMC[hname+'MC'].SetLineColor(ROOT.kRed)
   hMC[hname+'MC'].GetXaxis().SetRangeUser(0.0,2.0)
   hData[hname+'Data'].GetXaxis().SetRangeUser(0.0,2.0)
   hMC[hname+'MC'].SetMaximum(1.1*max(hMC[hname+'MC'].GetMaximum(),hData[hname+'Data'].GetMaximum()))
   if j==1:
        hMC[hname+'MC'].GetYaxis().SetMaxDigits(3)
   if j==2:
        tc.SetLogy(1)
        hMC[hname+'MC'].GetYaxis().SetMaxDigits(5)
   if j==3: 
        hMC[hname+'MC'].SetMaximum(3.5)
        hMC[hname+'MC'].SetMinimum(2.8)
   if j==4: 
        hMC[hname+'MC'].SetMaximum(0.6)
        hMC[hname+'MC'].SetMinimum(0.2)
   hMC[hname+'MC'].SetTitle('')
   hMC[hname+'MC'].SetStats(0)
   hData[hname+'Data'].SetStats(0)
   hMC[hname+'MC'].Draw()
   hData[hname+'Data'].Draw('same')
   tc = hMC['dummy'].cd()
   if j==2: tc.SetLogy(1)
   hMC[hname+'MC'].Draw()
   hData[hname+'Data'].Draw('same')
   myPrint(hMC['dummy'],'EvolutionOfCuts_dimuon'+v+'_'+param[p])
  myPrint(hMC['evolutionC'+v],'EvolutionOfCuts_dimuon'+v)
# truth momentum
 ut.bookCanvas(hMC,'kin','Jpsi kinematics',1800,1000,3,2)
 ut.bookHist(hMC, 'pt','pt',100,0.,5.)
 ut.bookHist(hMC, 'ptTrue','pt vs ptTrue',100,0.,5.,100,0.,5.)
 ut.bookHist(hMC, 'pTrue' ,'p vs pTrue',100,0.,400.,100,0.,400.)
 ut.bookHist(hMC, 'delpTrue' ,'pTrue - p',100,-20.,70.)
 ut.bookHist(hMC, 'delptTrue' ,'ptTrue - pt',100,-2.,2.)
 tc = hMC['kin'].cd(1)
 myDraw('p:PTRUE>>pTrue','Jpsi==443')
 myDraw('pt:PtTRUE>>ptTrue','Jpsi==443')
 myDraw('PTRUE-p>>delpTrue','Jpsi==443')
 myDraw('PtTRUE-pt>>delptTrue','Jpsi==443')
 ROOT.gROOT.cd()
 tc = hMC['kin'].cd(1)
 hMC['pTrue'].Draw('colz')
 tc = hMC['kin'].cd(4)
 hMC['delpTrue'].Fit('gaus')
 tc.Update()
 stats = tc.GetPrimitive('stats')
 stats.SetOptFit(10111)
 stats.SetFitFormat('5.4g')
 stats.SetX1NDC(0.50)
 stats.SetY1NDC(0.41)
 stats.SetX2NDC(0.99)
 stats.SetY2NDC(0.84)
 tc.Update()
 tc = hMC['kin'].cd(2)
 hMC['ptTrue'].Draw('colz')
 tc = hMC['kin'].cd(5)
 hMC['delptTrue'].Fit('gaus')
 tc.Update()
 stats = tc.GetPrimitive('stats')
 stats.SetOptFit(10111)
 stats.SetFitFormat('5.4g')
 tc.Update()
 tc = hMC['kin'].cd(3)
 hMC['ptTrue_x']=hMC['ptTrue'].ProjectionX('ptTrue_x')
 hMC['ptTrue_y']=hMC['ptTrue'].ProjectionY('ptTrue_y')
 hMC['pTrue_x']=hMC['pTrue'].ProjectionX('pTrue_x')
 hMC['pTrue_y']=hMC['pTrue'].ProjectionY('pTrue_y')
 hMC['ptTrue_x'].SetLineColor(ROOT.kRed)
 hMC['pTrue_x'].SetLineColor(ROOT.kRed)
 hMC['pTrue_x'].Draw()
 hMC['pTrue_y'].Draw('same')
 tc = hMC['kin'].cd(6)
 hMC['ptTrue_x'].Draw()
 hMC['ptTrue_y'].Draw('same')
 myPrint(hMC['kin'],'JpsiKinematics')
# low mass
 ut.bookCanvas(hMC,'lkin','low mass kinematics',1800,1000,3,2)
 ut.bookHist(hMC, 'lpt','pt',100,0.,5.)
 ut.bookHist(hMC, 'lptTrue','pt vs ptTrue',100,0.,5.,100,0.,5.)
 ut.bookHist(hMC, 'lpTrue' ,'p vs pTrue',100,0.,400.,100,0.,400.)
 ut.bookHist(hMC, 'ldelpTrue' ,'pTrue - p',100,-20.,70.)
 ut.bookHist(hMC, 'ldelptTrue' ,'ptTrue - pt',100,-2.,2.)
 tc = hMC['lkin'].cd(1)
 select=""
 for c in colors:
  if c==443: continue
  select+="||Jpsi=="+str(c)
 select = select[2:]
 myDraw('p:PTRUE>>lpTrue',select)
 myDraw('pt:PtTRUE>>lptTrue',select)
 myDraw('PTRUE-p>>ldelpTrue',select)
 myDraw('PtTRUE-pt>>ldelptTrue',select)
 tc = hMC['lkin'].cd(1)
 hMC['lpTrue'].Draw('colz')
 tc = hMC['lkin'].cd(4)
 hMC['ldelpTrue'].Fit('gaus')
 tc.Update()
 stats = tc.GetPrimitive('stats')
 stats.SetOptFit(10111)
 stats.SetFitFormat('5.4g')
 stats.SetX1NDC(0.50)
 stats.SetY1NDC(0.41)
 stats.SetX2NDC(0.99)
 stats.SetY2NDC(0.84)
 tc.Update()
 tc = hMC['lkin'].cd(2)
 hMC['lptTrue'].Draw('colz')
 tc = hMC['lkin'].cd(5)
 hMC['ldelptTrue'].Fit('gaus')
 tc.Update()
 stats = tc.GetPrimitive('stats')
 stats.SetOptFit(10111)
 stats.SetFitFormat('5.4g')
 tc.Update()
 tc = hMC['lkin'].cd(3)
 hMC['lptTrue_x']=hMC['lptTrue'].ProjectionX('lptTrue_x')
 hMC['lptTrue_y']=hMC['lptTrue'].ProjectionY('lptTrue_y')
 hMC['lpTrue_x']=hMC['lpTrue'].ProjectionX('lpTrue_x')
 hMC['lpTrue_y']=hMC['lpTrue'].ProjectionY('lpTrue_y')
 hMC['lptTrue_x'].SetLineColor(ROOT.kRed)
 hMC['lpTrue_x'].SetLineColor(ROOT.kRed)
 hMC['lpTrue_x'].Draw()
 hMC['lpTrue_y'].Draw('same')
 tc = hMC['lkin'].cd(6)
 hMC['lptTrue_x'].Draw()
 hMC['lptTrue_y'].Draw('same')
 myPrint(hMC['lkin'],'LowMassKinematics')

# muon dEdx
 ut.bookCanvas(hMC,'TdEdx','dEdx',1800,1200,1,3)
 tc = hMC['TdEdx'].cd(1)
 ut.bookHist(hMC, 'delpTrue2' ,'p-pTrue vs p',40,0.,400.,50,-50.,50.)
 ut.bookHist(hMC, 'delpTrue2True' ,'p-pTrue vs pTrue',40,0.,400.,50,-50.,50.)
 myDraw('(p1-p1True):p1>>delpTrue2','')
 myDraw('(p2-p2True):p2>>+delpTrue2','') # applying cuts does not make a difference
 myDraw('(p1-p1True):p1True>>delpTrue2True','')
 myDraw('(p2-p2True):p2True>>+delpTrue2True','')
 ROOT.gROOT.cd()
 hMC['meanLoss']=hMC['delpTrue2'].ProjectionX('meanLoss')
 hMC['meanLossTrue']=hMC['delpTrue2True'].ProjectionX('meanLossTrue')
 for n in range(1,hMC['delpTrue2'].GetXaxis().GetNbins()+1):
   tmp = hMC['delpTrue2'].ProjectionY('tmp',n,n)
   # hMC['meanLoss'].SetBinContent(n, tmp.GetBinCenter(ut.findMaximumAndMinimum(tmp)[3]))
   hMC['meanLoss'].SetBinContent(n, tmp.GetMean())
   hMC['meanLoss'].SetBinError(n,tmp.GetRMS())
   tmp = hMC['delpTrue2True'].ProjectionY('tmp',n,n)
   hMC['meanLossTrue'].SetBinContent(n, tmp.GetMean())
   hMC['meanLossTrue'].SetBinError(n,tmp.GetRMS())
 hMC['meanLoss'].Draw()
 hMC['meanLoss'].Fit('pol2','S','',20.,300.)
 tc =hMC['TdEdx'].cd(2)
 hMC['meanLossTrue'].Draw()
 hMC['meanLossTrue'].Fit('pol2','S','',20.,300.)
 tc =hMC['TdEdx'].cd(3)
 ut.bookHist(hMC, 'delp' ,'p-pTrue',50,-50.,50.)
 hMC['delpFunOfPtCut']=ROOT.TGraph()
 dp = 0.1
 ptCut = 0.0
 for k in range(20):
  myDraw('(p1-p1True)>>delp','Jpsi==443&&pt1>'+str(ptCut+dp/2.)+'&&pt1<'+str(ptCut-dp/2.))
  myDraw('(p2-p2True)>>+delp','Jpsi==443&&pt2>'+str(ptCut+dp/2.)+'&&pt1<'+str(ptCut-dp/2.))
  dE = hMC['delp'].GetMean()
  hMC['delpFunOfPtCut'].SetPoint(k,ptCut,dE)
  ptCut+=dp
 ut.bookHist(hMC, 'delpt' ,'delpt',20,0.,2.)
 hMC['delpt'].SetMaximum(0.0)
 hMC['delpt'].SetMinimum(-10.0)
 hMC['delpt'].Draw()
 hMC['delpFunOfPtCut'].Draw()
# -7.97  -1.52 * ptCut + 0.93 * ptCut**2

 v='mcor'
 ptCut = 1.0
 sptCut = str(ptCut)
 theCut =  theCutTemplate.replace('XYZ',sptCut)
 if v=='mcor': 
      theCut = theCut.replace('pt1','pt1cor')
      theCut = theCut.replace('pt2','pt2cor')
# yield as function of pt
 makeProjection('ptcor',0.,2.,'#it{p}_{T} [GeV/c^{2}]',theCut)
# yield as function of y
 makeProjection('ycor',0.,2.,'y_{CMS}',theCut)
# yield as function of p
 makeProjection('pcor',20.,220.,'#it{p} [GeV/c^{2}]',theCut)
# polarization
 makeProjection('cosCScor',-1.,1.,'cos{theta}CS',theCut)
 # fit for polarization
 hData['polFun'] = ROOT.TF1('polFun','[0]*(1+x**2*[1])',2)
 rc = hData['JpsicosCScor'].Fit(hData['polFun'],'S','',-1.,1.)
 fitResult = rc.Get()
 print "polarization CS #Lambda=%5.2F +/- %5.2F"%(fitResult.Parameter(1),fitResult.ParError(1))
 makeProjection('cosTheta',-1.,1.,'cos{theta}',theCut)
 rc = hData['JpsicosTheta'].Fit(hData['polFun'],'S','',-1.,1.)
 fitResult = rc.Get()
 print "polarization CS #Lambda=%5.2F +/- %5.2F"%(fitResult.Parameter(1),fitResult.ParError(1))

# low mass in bins of p and pt
 ut.bookHist(hMC, 'mc-lowMassppt','low mass pt vs p;#it{p} [GeV/c];#it{p}_{T} [GeV/c]',50,0.,400.,50,0.,5.)
 ut.bookHist(hData, 'lowMassppt','low mass pt vs p;#it{p} [GeV/c];#it{p}_{T} [GeV/c]',50,0.,400.,50,0.,5.)
 sptCut = '0'
 theCut =  '('+sptCut+'<pt1||'+sptCut+'<pt2)&&chi21*chi22<0&&abs(chi21)<0.9&&abs(chi22)<0.9&&p1>20&&p2>20'
 if v=='mcor': 
      theCut = theCut.replace('pt1','pt1cor')
      theCut = theCut.replace('pt2','pt2cor')
 ut.bookHist(hMC, 'mc-lowMassAll','low mass ;M [GeV/c^[2]]',100,0.,5.)
 ut.bookHist(hData, 'lowMassAll', 'low mass ;M [GeV/c^[2]]',100,0.,5.)
 myDraw('mcor>>mc-lowMassAll',theCut)
 sTreeData.Draw('mcor>>lowMassAll',theCut)
 hMC['mc-lowMassAll'].Scale(1./hMC['weights']['10GeV'])
 tc=hMC['dummy'].cd()
 hMC['mc-lowMassAll'].SetLineColor(ROOT.kMagenta)
 hData['lowMassAll'].Draw()
 hMC['mc-lowMassAll'].Draw('same')
 myPrint(hMC['dummy'],'lowMassAll')
 theCut =  '('+sptCut+'<pt1||'+sptCut+'<pt2)&&chi21*chi22<0&&abs(chi21)<0.9&&abs(chi22)<0.9&&p1>20&&p2>20&&mcor>0.4&&mcor<2.0'
 if v=='mcor': 
      theCut = theCut.replace('pt1','pt1cor')
      theCut = theCut.replace('pt2','pt2cor')
 myDraw('ptcor:pcor>>mc-lowMassppt',theCut)
 sTreeData.Draw('pt:p>>lowMassppt',theCut)
 hMC['mc-lowMassppt'].Scale(1./hMC['weights']['10GeV'])
 ut.bookCanvas(hData,'lowMass','lowMass summary',1600,1200,1,2)
 hData['lowMass1'] = hData['lowMass'].cd(1)
 hData['lowMass1'].Divide(2,1)
 tc = hData['lowMass1'].cd(1)
 tc.SetLogy(1)
 hData['lowMassppt_projx'] = hData['lowMassppt'].ProjectionX('lowMassppt_projx')
 hData['lowMassppt_projx'].GetXaxis().SetRangeUser(40.,400.)
 hData['lowMassppt_projx'].SetStats(0)
 hData['lowMassppt_projx'].SetTitle('')
 hData['lowMassppt_projx'].Draw()
 hMC['mc-lowMassppt_projx'] = hMC['mc-lowMassppt'].ProjectionX('mc-lowMassppt_projx')
 hMC['mc-lowMassppt_projx'].SetLineColor(ROOT.kMagenta)
 hMC['mc-lowMassppt_projx'].Draw('same')
 tc = hData['lowMass1'].cd(2)
 tc.SetLogy(1)
 hData['lowMassppt_projy'] = hData['lowMassppt'].ProjectionY('lowMassppt_projy')
 hData['lowMassppt_projy'].SetStats(0)
 hData['lowMassppt_projy'].SetTitle('')
 hData['lowMassppt_projy'].Draw()
 hMC['mc-lowMassppt_projy'] = hMC['mc-lowMassppt'].ProjectionY('mc-lowMassppt_projy')
 hMC['mc-lowMassppt_projy'].SetLineColor(ROOT.kMagenta)
 hMC['mc-lowMassppt_projy'].Draw('same')
 hMC['mc-ratioLowMass'] = hMC['mc-lowMassppt'].Clone('mc-ratioLowMass')
 hData['ratioLowMass']  = hData['lowMassppt'].Clone('ratioLowMass')
 hMC['mc-ratioLowMass'].Rebin2D(5,5)
 hData['ratioLowMass'].Rebin2D(5,5)
 asymVersion = False
 for mx in range(1,hMC['mc-ratioLowMass'].GetNbinsX()+1):
  for my in range(1,hMC['mc-ratioLowMass'].GetNbinsY()+1):
    Nmc = hMC['mc-ratioLowMass'].GetBinContent(mx,my)
    Nda = hData['ratioLowMass'].GetBinContent(mx,my)
    eNmc = hMC['mc-ratioLowMass'].GetBinError(mx,my)
    eNda = hData['ratioLowMass'].GetBinError(mx,my)
    if Nmc>10 and Nda>10:
         if asymVersion:
          R = (Nda-Nmc)/(Nda+Nmc)
          sig_data = ROOT.TMath.Sqrt(eNda**2+(Nda*daSysError)**2)
          sig_MC   = ROOT.TMath.Sqrt(eNmc**2+(Nmc*mcSysError)**2)
          e1 = 2*Nda/(Nda+Nmc)**2
          e2 = 2*Nmc/(Nda+Nmc)**2
          eR = ROOT.TMath.Sqrt( (e1*sig_MC)**2+(e2*sig_data)**2 )
         else: # ratio  version
          R = (Nda/Nmc)
          eR = ROOT.TMath.Sqrt( (R/Nmc*eNmc)**2+(R/Nda*eNda)**2 )
    else:      
         R  = 0. # -1      # R = 0
         eR = 0.
    hData['ratioLowMass'].SetBinContent(mx,my,R)
    hData['ratioLowMass'].SetBinError(mx,my,eR)
 tc = hData['lowMass'].cd(2)
 ROOT.gStyle.SetPaintTextFormat("5.2f")
 hData['ratioLowMass'].GetXaxis().SetRangeUser(40.,400.)
 hData['ratioLowMass'].SetStats(0)
 if asymVersion: hData['ratioLowMass'].SetTitle('data - MC / data + MC')
 else: hData['ratioLowMass'].SetTitle('data/MC')
 hData['ratioLowMass'].GetYaxis().SetRangeUser(0,3.)
 hData['ratioLowMass'].SetMarkerSize(1.8)
 hData['ratioLowMass'].Draw('texte')
 myPrint(hData['lowMass'],'lowMassSummary')
 ut.writeHists(hMC,fm+'-diMuonAnalysis-MC.root')
 ut.writeHists(hData,fm+'-diMuonAnalysis-Data.root')
def energyLoss(step='determine'):
# muon dEdx
 tc = hMC['dummy'].cd(1)
 if step == 'determine':
   hMC['incl'] = ROOT.TChain('muons')
   hMC['incl'].AddFile("recMuons_1GeV.root")
   hMC['incl'].AddFile("recMuons_10GeV.root")
   hMC['fP8']=ROOT.TFile('recMuons_P8.root')
   hMC['fP6']=ROOT.TFile('recMuons_Cascade.root')
   hMC['P8']=hMC['fP8'].muons
   hMC['P6']=hMC['fP6'].muons
   V = ['incl','P8','P6']
   ROOT.gROOT.cd()
   theCut = "DTz<3332&&abs(muID)==13&&oz<-100&&goodTrack==111&&chi2<0.9"
   for v in V: 
       ut.bookHist(hMC, 'eloss_'+v ,'pDT-pTrue vs pDT',40,0.,400.,50,-50.,50.)
       hMC[v].Draw('sqrt(DTpx*DTpx+DTpy*DTpy+DTpz*DTpz)-sqrt(px*px+py*py+pz*pz):sqrt(DTpx*DTpx+DTpy*DTpy+DTpz*DTpz)>>eloss_'+v,theCut)
   V = ['incl','P8','P6','all']
   hMC['eloss_all']=hMC['eloss_incl'].Clone('eloss_all')
   hMC['eloss_all'].Add(hMC['eloss_P6'])
   hMC['eloss_all'].Add(hMC['eloss_P8'])
   for v in V: 
       hMC['eloss_p_'+v]=hMC['eloss_'+v].ProjectionX('eloss_p_'+v)
       hMC['eloss_p_'+v].Reset()
       for n in range(1,hMC['eloss_'+v].GetNbinsX()+1):
             tmp = hMC['eloss_'+v].ProjectionY('tmp',n,n)
             mean = tmp.GetMean()
             errmean = tmp.GetMeanError()
             hMC['eloss_p_'+v].SetBinContent(n,mean)
             hMC['eloss_p_'+v].SetBinError(n,errmean)
   hMC['eloss_p_g']=ROOT.TGraph()
   for n in range(1,hMC['eloss_p_all'].GetNbinsX()+1):
     hMC['eloss_p_g'].SetPoint(n-1,hMC['eloss_p_all'].GetBinCenter(n),hMC['eloss_p_all'].GetBinContent(n))
   hMC['eloss_p_all'].Draw()
   myPrint()
 elif step=='apply':
   theCut = theJpsiCut('mcor',True,1.0,20.,300.,2,False)
   if MC:
     xTarget=0
     yTarget=0
     zTarget = -377.
   else:
     xTarget=0.53
     yTarget=-0.2
     zTarget = -377.
   nt = hMC['Jpsi']
   nt = hData['f'].nt
   if nt.GetLeaf("    prec1x"): nt.GetLeaf("    prec1x").SetName("prec1x")
   ut.bookHist(hMC, 'mcor', 'inv mass;M [GeV/c^{2}];N',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
   ut.bookHist(hMC, 'mcorNew', 'inv mass;M [GeV/c^{2}];N',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
   nt.Draw('mcor>>mcor',theCut)
   nt.Draw('>>eventList',theCut)
   eventList = ROOT.gROOT.FindObject('eventList')
   Pcor={}
   P={}
   X={}
   for n in range(eventList.GetN()):
      rc = nt.GetEvent(eventList.GetEntry(n))
      P[1] = ROOT.Math.PxPyPzMVector(nt.prec1x,nt.prec1y,nt.prec1z,muonMass)
      P[2] = ROOT.Math.PxPyPzMVector(nt.prec2x,nt.prec2y,nt.prec2z,muonMass)
      X[1] = ROOT.TVector3(nt.rec1x,nt.rec1y,nt.rec1z)
      X[2] = ROOT.TVector3(nt.rec2x,nt.rec2y,nt.rec2z)
# make dE correction plus direction from measured point
      O = ROOT.TVector3(xTarget,yTarget,zTarget)
      for k in range(1,3):
        dline = X[k]-O
        norm  = dline.Mag()
        Ecor  = P[k].E()-hMC['eloss_p_g'].Eval(P[k].E())
        Pcor[k]  = ROOT.Math.PxPyPzMVector(Ecor*dline.X()/norm,Ecor*dline.Y()/norm,Ecor*dline.Z()/norm,muonMass)
      J = Pcor[1]+Pcor[2]
      rc = hMC['mcorNew'].Fill(J.M())

def makeProjection(proj,projMin,projMax,projName,theCut,nBins=9,ntName='10GeV',printout=2,fixSignal=False,secondGaussian=True):
   y_beam = yBeam()
   v='mcor'
   fitOption = 'SEQL'
   if printout==2: fitOption='SEL'
   sTreeData  = hData['f'].nt
   if hMC.has_key('MCbins'+proj):
      hMC.pop('MCbins'+proj)
      hData.pop('bins'+proj)
   if hMC.has_key('mc-'+proj): hMC.pop('mc-'+proj).Delete()
# book 2d histograms in mass vs variable space
   ut.bookHist(hMC, 'mc-'+proj, ' N J/#psi ;'+projName, nBins,projMin,projMax,InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
   if hData.has_key(proj): hData.pop(proj).Delete()
   ut.bookHist(hData,  proj,    ' N J/#psi ;'+projName, nBins,projMin,projMax,InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
   hData['Jpsi'+proj]  = hData[proj].ProjectionX('Jpsi'+proj)
   hMC['mc-Jpsi'+proj] = hMC['mc-'+proj].ProjectionX('mc-Jpsi'+proj)
   N1 = int(ROOT.TMath.Sqrt(nBins))
   N2 = N1
   while(N2*N1<nBins): N2+=1
   ut.bookCanvas(hMC,'MCbins'+proj,'mass in bins '+projName,1800,1200,N1,N2)
   ut.bookCanvas(hData,'bins'+proj,'mass in bins '+projName,1800,1200,N1,N2)

   par={"MC":[],"Data":[]}
   hMC['dummy'].cd()
   if proj=='ycor': cutExp = "ycor-"+str(y_beam)
   elif proj=='ycor1C': cutExp = ycor1C+"-"+str(y_beam)
   else:            cutExp = proj
   for m in par: 
       pmin = projMin
       delp = (projMax-projMin)/float(nBins)
       if m=='MC': 
           myDraw(v+':'+cutExp+'>>mc-'+proj,theCut,ntName)
           histo = hMC['mc-'+proj].ProjectionY('mass')
       else:       
           sTreeData.Draw(v+':'+cutExp+'>>'+proj,theCut)
           histo = hData[proj].ProjectionY('mass')
# find initial fit parameters
       myGauss = fGlobal['myGauss'].Clone(m+proj)
       init_Gauss(myGauss)
       myGauss.FixParameter(1,3.1)
       myGauss.FixParameter(2,0.35)
       myGauss.FixParameter(4,1.1)
       myGauss.FixParameter(5,0.35)
       if not secondGaussian and m=='MC': myGauss.FixParameter(3,0.)
       rc = histo.Fit(myGauss,fitOption,'',0.5,5.)
       myGauss.ReleaseParameter(1)
       myGauss.ReleaseParameter(2)
       if secondGaussian or m=='Data': 
         myGauss.ReleaseParameter(4)
         myGauss.ReleaseParameter(5)
       histo.Draw()
       rc = histo.Fit(myGauss,fitOption,'',0.5,5.)
       fitResult = rc.Get()
       for n in range(11): par[m].append(fitResult.Parameter(n))
       for k in range(nBins):
         pmax = pmin+delp
         hMC['mc-'+proj+str(k)]=hMC['mc-'+proj].ProjectionY('mc-'+proj+str(k),k+1,k+1)
         hMC['mc-'+proj+str(k)].SetTitle('inv mass MC '   +str(pmin)+'<'+proj+'<'+str(pmax)+';M [GeV/c^{2}]')
         hData[proj+str(k)]=hData[proj].ProjectionY(proj+str(k),k+1,k+1)
         hData[proj+str(k)].SetTitle('inv mass DATA ' +str(pmin)+'<'+proj+'<'+str(pmax)+';M [GeV/c^{2}]')
         pmin=pmax
#
   pmin = projMin
   for k in range(nBins):
     cases = {'MC':hMC['mc-'+proj+str(k)],'Data':hData[proj+str(k)]}
     for c in cases:
       histo = cases[c]
       if c=='MC': tc=hMC['MCbins'+proj].cd(k+1)
       else: tc=hData['bins'+proj].cd(k+1)
       myGauss = fGlobal['myGauss'].Clone(c+proj+str(k))
       init_Gauss(myGauss)
       for n in [1,2,4,5]:  myGauss.FixParameter(n,par[c][n])
       if not secondGaussian and c=='MC': myGauss.FixParameter(3,0.)
       histo.Draw()
       myGauss.FixParameter(7,0.)
       if histo.GetEntries()>10:
        myGauss.FixParameter(0,0.)
        rc = histo.Fit(myGauss,fitOption,'',0.5,2.)
        myGauss.ReleaseParameter(0)
        rc = histo.Fit(myGauss,fitOption,'',0.5,6.)
        if not fixSignal:
          myGauss.ReleaseParameter(1)
          myGauss.ReleaseParameter(2)
        if secondGaussian or m=='Data': 
          myGauss.ReleaseParameter(4)
          myGauss.ReleaseParameter(5)
        rc = histo.Fit(myGauss,fitOption,'',0.5,5.)
        fitResult = rc.Get()
        N = fitResult.Parameter(0)
        if N<0: 
          myGauss.SetParameter(0,abs(N))
          rc = histo.Fit(myGauss,fitOption,'',0.5,5.)
          fitResult = rc.Get()
        N = fitResult.Parameter(0)
        E = fitResult.ParError(0)
        if fitResult.Parameter(1)>4 or fitResult.Parameter(1)<2: 
          N=0
          E=0
       else:
        N=0
        E=0
       tc.Update()
       stats = tc.GetPrimitive('stats')
       stats.SetOptFit(10111)
       stats.SetFitFormat('5.4g')
       stats.SetX1NDC(0.41)
       stats.SetY1NDC(0.41)
       stats.SetX2NDC(0.99)
       stats.SetY2NDC(0.84)
       tc.Update()
       if c=='MC': 
          hMC['mc-Jpsi'+proj].SetBinContent(k+1,N)
          hMC['mc-Jpsi'+proj].SetBinError(k+1,E)
       else: 
          hData['Jpsi'+proj].SetBinContent(k+1,N)
          hData['Jpsi'+proj].SetBinError(k+1,E)
   if printout>0:
     myPrint(hData['bins'+proj],'diMuonBins'+proj)
     myPrint(hMC['MCbins'+proj],'MC-diMuonBins'+proj+ntName)
     hMC['dummy'].cd()
     hMC['mc-Jpsi'+proj].SetLineColor(ROOT.kMagenta)
     hmax = 1.1*max(hMC['mc-Jpsi'+proj].GetMaximum(),hData['Jpsi'+proj].GetMaximum())
     hMC['mc-Jpsi'+proj].SetMaximum(hmax)
     hMC['mc-Jpsi'+proj].Draw()
     hData['Jpsi'+proj].Draw('same')
     myPrint(hMC['dummy'],'diMuonBins'+proj+ntName+'Summary')

def unconvolute(z,hjpsi,effMin):
   yranges=[0.25,1.85]
   ymin = yranges[0]
   xaxis = hMC['YM'+z].GetXaxis()
   bw = xaxis.GetBinWidth(1)
   NyieldEffCorrected = {}
   for k in range(1,xaxis.GetNbins()+1):
      NyieldEffCorrected[k]=[0,0]
# for a given ycor, find distribution of ytrue
   while ymin < yranges[1]:
      i = xaxis.FindBin(ymin)
      hMC['YM'+z+'_ycor'+str(i)]=hMC['YM'+z].ProjectionY('YM'+z+'_ycor'+str(i),i,i )
      xslice = hMC['YM'+z+'_ycor'+str(i)]
      norm = xslice.GetSumOfWeights()
      n = hjpsi.FindBin(ymin)
      Nrec = hjpsi.GetBinContent(n)
      Erec = hjpsi.GetBinError(n)
      xslice.Scale(Nrec/norm)
      for k in range(1,xslice.GetNbinsX()+1):
          x = xslice.GetBinCenter(k)
          e = hMC['YEff'+z+'_graph'].Eval(x)
          if e>effMin:
              NyieldEffCorrected[k][0]+=xslice.GetBinContent(k)/e
              # 25.3. 2020: NyieldEffCorrected[k][1]+=(xslice.GetBinContent(k)/e * Erec/(Nrec+1E-9))**2
              NyieldEffCorrected[k][1]+=(xslice.GetBinContent(k)/e * Erec/(Nrec+1E-9))
# errors
      ymin+=bw
   xslice.Reset()
   hname = hjpsi.GetName()+"_effAndResolCorrected"+z
   hMC[hname]=xslice.Clone(hname)
   hMC[hname].SetMarkerStyle(21)
   for k in range(1,xaxis.GetNbins()+1):
      if NyieldEffCorrected[k][0]<1E10:
         hMC[hname].SetBinContent(k,NyieldEffCorrected[k][0])
         #  hMC[hname].SetBinError(k,ROOT.TMath.Sqrt(NyieldEffCorrected[k][1]))
         hMC[hname].SetBinError(k,NyieldEffCorrected[k][1])
      else:   
         hMC[hname].SetBinContent(k,0.)
         hMC[hname].SetBinError(k,0.)

import math
def init_twoCB0(myCB,bw):
   myCB.FixParameter(0,bw)
   myCB.SetParName(0,'binwidth')
   myCB.SetParName(1,'psi(1S)')
   myCB.SetParName(2,'Mass')
   myCB.SetParName(3,'Sigma')
   myCB.SetParName(4,'alpha')
   myCB.SetParName(5,'n')
   myCB.SetParName(6,'SignalLow')
   myCB.SetParName(7,'MeanLow')
   myCB.SetParName(8,'SigmaLow')
   myCB.SetParName(9,'alphaLow')
   myCB.SetParName(10,'nLow')
   myCB.SetParName(11,'p0')
   myCB.SetParName(12,'p1')
   myCB.SetParName(13,'psi(2S)')
   myCB.SetParName(14,'alphaLeft')
   myCB.SetParName(15,'nLeft')
   myCB.SetParName(17,'Drell Yan')
   myCB.SetParameter(1,100.)
   myCB.SetParLimits(1,0.0,1E6)
   myCB.SetParameter(2,3.1)
   myCB.SetParameter(3,0.4)
   myCB.SetParameter(4,1.0)  # alpha
   myCB.SetParLimits(4,0.0,10.)   # powerlaw for x < xmean-sigma*alpha
   myCB.SetParameter(5,10.)  # n
   myCB.SetParLimits(5,0.0,100.)
   myCB.SetParameter(6,100.)
   myCB.SetParLimits(6,0.0,1E6)
   myCB.SetParameter(7,1.)
   myCB.SetParameter(8,0.4)
   myCB.SetParameter(9,-1.0)   # alphaRight
   myCB.SetParLimits(9,-0.5,-1.5)
   myCB.SetParameter(10,10.)  # nRight
   myCB.SetParLimits(10,0.0,50.)
   myCB.SetParameter(11,1.)
   myCB.SetParameter(12,0)
   myCB.FixParameter(13,0.)
   myCB.FixParameter(14,0.0)    # alphaLeft
   myCB.FixParameter(15,10.)    # nLeft
   myCB.FixParameter(16,0.)     # switch for sum, high/low mass, background, Jpsi
   myCB.FixParameter(17,0.)     # Drell Yan

def init_twoCB(myCB,bw,ptCut,h,fromPrevFit=False):
   init_twoCB0(myCB,bw)
   if not fromPrevFit:
    myCB.SetParameter(1,h['fitResult'][ptCut]['psi(1S)'][0])
    myCB.SetParameter(2,h['fitResult'][ptCut]['Mean'][0])
    myCB.SetParameter(3,h['fitResult'][ptCut]['Sigma'][0])
    myCB.SetParameter(4,0.3)
    myCB.SetParameter(5,3.5)
    myCB.SetParameter(6,h['fitResult'][ptCut]['SignalLow'][0])
    myCB.SetParameter(7,h['fitResult'][ptCut]['MeanLow'][0])
    myCB.SetParameter(8,h['fitResult'][ptCut]['SigmaLow'][0])
    myCB.SetParameter(9,0.3)
    myCB.SetParameter(10,3.5)
    myCB.SetParameter(11,h['fitResult'][ptCut]['p1'][0])
    myCB.SetParameter(12,h['fitResult'][ptCut]['p2'][0])
    myCB.FixParameter(13,0.)
    myCB.SetParameter(17,h['fitResult'][ptCut]['DY'][0])
   else:
    myCB.SetParameter(1,h['fitResultCB'][ptCut]['psi(1S)'][0])
    myCB.SetParameter(2,h['fitResultCB'][ptCut]['Mass'][0])
    myCB.FixParameter(3,h['fitResultCB'][ptCut]['Sigma'][0])
    myCB.FixParameter(4,h['fitResultCB'][ptCut]['alpha'][0])
    myCB.FixParameter(5,h['fitResultCB'][ptCut]['n'][0])
    myCB.SetParameter(6,h['fitResultCB'][ptCut]['SignalLow'][0])
    myCB.SetParameter(7,h['fitResultCB'][ptCut]['MeanLow'][0])
    myCB.FixParameter(8,h['fitResultCB'][ptCut]['SigmaLow'][0])
    myCB.FixParameter(9,h['fitResultCB'][ptCut]['alphaLow'][0])
    myCB.FixParameter(10,h['fitResultCB'][ptCut]['nLow'][0])
    myCB.SetParameter(11,h['fitResultCB'][ptCut]['p0'][0])
    myCB.SetParameter(12,h['fitResultCB'][ptCut]['p1'][0])
    myCB.FixParameter(12,0.)
    myCB.FixParameter(13,0.)
    myCB.SetParameter(17,h['fitResultCB'][ptCut]['DY'][0])
    myCB.ReleaseParameter(2)
    myCB.ReleaseParameter(7)
def norm_twoCB(B,im='',sLow=2.0,sHigh=5.0,bLow=0.3,bHigh=3.0):
  if B.ClassName()=='TF1':
    N2 = B.GetParameter(1)
    N1 = B.GetParameter(6)
    bw = B.GetParameter(0)
    fGlobal['cb'].SetParameters(B.GetParameter(1),B.GetParameter(2),B.GetParameter(3),B.GetParameter(4),B.GetParameter(5))
    if im=='s': signalNormalized = simpleIntegral(fGlobal['cb'],sLow,sHigh)
    else:       signalNormalized = fGlobal['cb'].Integral(sLow,sHigh)
    fGlobal['cb'].SetParameters(B.GetParameter(6),B.GetParameter(7),B.GetParameter(8),B.GetParameter(9),B.GetParameter(10))
    if im=='s': lowMassNormalized = simpleIntegral(fGlobal['cb'],bLow,bHigh)
    else:       lowMassNormalized = fGlobal['cb'].Integral(bLow,bHigh)
    err_lowMassNormalized = 0
    if N1>0: err_lowMassNormalized = lowMassNormalized/N1*B.GetParError(6)
    err_signalNormalized  = 0
    if N2>0:  err_signalNormalized = signalNormalized/N2*B.GetParError(1)
  else:
    N2 = B.Parameter(1)
    N1 = B.Parameter(6)
    bw = B.Parameter(0)
    fGlobal['cb'].SetParameters(B.Parameter(1),B.Parameter(2),B.Parameter(3),B.Parameter(4),B.Parameter(5))
    if im=='s': signalNormalized = simpleIntegral(fGlobal['cb'],sLow,sHigh)
    else:       signalNormalized = fGlobal['cb'].Integral(sLow,sHigh)
    fGlobal['cb'].SetParameters(B.Parameter(6),B.Parameter(7),B.Parameter(8),B.Parameter(9),B.Parameter(10))
    if im=='s': lowMassNormalized = simpleIntegral(fGlobal['cb'],bLow,bHigh)
    else:       lowMassNormalized = fGlobal['cb'].Integral(bLow,bHigh)
    err_lowMassNormalized = 0
    if N1>0: err_lowMassNormalized = lowMassNormalized/N1*B.ParError(6)
    err_signalNormalized  = 0
    if N2>0:  err_signalNormalized = signalNormalized/N2*B.ParError(1)
  return [lowMassNormalized,err_lowMassNormalized],[signalNormalized,err_signalNormalized]

def fitWithTwoCB():
 hMC['dummy'].cd()
 ptCutList = [0.0,0.8,0.9,1.0,1.1,1.2,1.3,1.4,1.5,1.6]
 bw = hMC['m_MC'].GetBinWidth(1)
 cases = {'':hData,'mc-':hMC}
 v = 'mcor'
 for c in cases:
  h=cases[c]
  h['fitResultCB']={}
  for ptCut in ptCutList:
   h['myCB2'+str(ptCut)+c] = ROOT.TF1('2CB'+str(ptCut)+c,TwoCrystalBall,0,10,14)
   myCB = h['myCB2'+str(ptCut)+c]
   init_twoCB(myCB,bw,ptCut,h)
   hname = c+v+'_'+str(ptCut)
   print "+++++ Fit",hname
   myCB.FixParameter(9,10.) # alpha positive and large -> gauss part only
   myCB.FixParameter(5,10.) # alpha positive and large -> gauss part only
   rc = h[hname].Fit(myCB,'S','',0.5,5.)
   myCB.ReleaseParameter(5)
   rc = h[hname].Fit(myCB,'SE','',0.5,5.)
   myCB.ReleaseParameter(9)
   rc = h[hname].Fit(myCB,'SE','',0.5,5.)
   fitResult=rc.Get()
   if math.isnan(fitResult.ParError(1)) or math.isnan(fitResult.ParError(6)):
      myCB.FixParameter(4,10.)
      rc = h[hname].Fit(myCB,'S','',0.5,5.)
      myCB.ReleaseParameter(4)
      rc = h[hname].Fit(myCB,'SE','',0.5,5.)
      fitResult=rc.Get()
      if math.isnan(fitResult.ParError(1)) or math.isnan(fitResult.ParError(6)):
        myCB.FixParameter(4,10.)
        rc = h[hname].Fit(myCB,'SE','',0.5,5.)
        fitResult=rc.Get()
   h['fitResultCB'][ptCut]={}
   for n in range(1,13):
       h['fitResultCB'][ptCut][myCB.GetParName(n)] = [fitResult.Parameter(n),fitResult.ParError(n)]
   myCB.ReleaseParameter(13)
   rc = h[hname].Fit(myCB,'SE','',0.5,5.)
   fitResult=rc.Get()
   n=13
   h['fitResultCB'][ptCut][myCB.GetParName(n)] = [fitResult.Parameter(n),fitResult.ParError(n)]
   myCB.FixParameter(13,0.)
   rc = h[hname].Fit(myCB,'SE','',0.5,5.)
 for j in range(1,21): hMC['fits'+v].cd(j).Update()
 hMC['fits'+v].Update()
 myPrint(hMC['fits'+v],v+'_CBdimuon_all')
# p/pt
# try Jpsi p,pt based on ptmu > 1.4
 fillProjectionCB('ptcor',1.4,nBins=9)
 fillProjectionCB('pcor', 1.4,nBins=9)
 fillProjectionCB('ycor', 1.4,nBins=9)
# make ratio data / mc with lumi weighted:
 hData['ratios']={}
 for ptCut in ptCutList:
   hData['ratios'][ptCut]={}
   for fit in ['','CB']:
    hData['ratios'][ptCut][fit]={}
    for M in ['psi(1S)','SignalLow']:
     N = hData['fitResult'+fit][ptCut][M][0]
     E = hData['fitResult'+fit][ptCut][M][1]
     fudgeFactor = 1.
     if M=='psi(1S)': fudgeFactor = (1.+jpsiCascadeContr)
     MCN = hMC['fitResult'+fit][ptCut][M][0]*fudgeFactor
     MCE = hMC['fitResult'+fit][ptCut][M][1]*fudgeFactor
# '10GeV':MCStats['10GeV']/dataStats/(1+simpleEffCor*2)
     R = N/MCN * hMC['weights']['10GeV']
     ER = ROOT.TMath.Sqrt( (R/N*E)**2 + (R/MCN*MCE)**2)
     hData['ratios'][ptCut][fit][M]=[R,ER]
 for M in ['psi(1S)','SignalLow']:
    print "results for ",M
    for ptCut in ptCutList:
      r = "%5.2F +/- %5.2F"%(hData['ratios'][ptCut][''][M][0],hData['ratios'][ptCut][''][M][1])
      rCB = "%5.2F +/- %5.2F"%(hData['ratios'][ptCut]['CB'][M][0],hData['ratios'][ptCut]['CB'][M][1])
      print "Ratio Data/MC with pt cut %3.2F: gauss  %s  crystalball %s"%(ptCut,r,rCB)
 print "results for mass difference Jpsi low"
 cases = {'':hData,'mc-':hMC}
 for c in cases:
   h=cases[c]
   h['delm']={}
   for ptCut in ptCutList:
     h['delm'][ptCut]={}
     for fit in ['','CB']:
       m = 'Mass'
       if fit=='': m = "Mean"
       Delm  = h['fitResult'+fit][ptCut][m][0] - h['fitResult'+fit][ptCut]['MeanLow'][0]
       eDelm = ROOT.TMath.Sqrt(h['fitResult'+fit][ptCut][m][1]**2+h['fitResult'+fit][ptCut]['MeanLow'][1]**2)
       h['delm'][ptCut][fit]=[Delm,eDelm]
 for ptCut in ptCutList:
    r1 = "%5.2F +/- %5.2F"%(hData['delm'][ptCut][''][0],hData['delm'][ptCut][''][1])
    r2 = "%5.2F +/- %5.2F"%(hData['delm'][ptCut]['CB'][0],hData['delm'][ptCut]['CB'][1])
    r3 = "%5.2F +/- %5.2F"%(hMC['delm'][ptCut][''][0],hMC['delm'][ptCut][''][1])
    r4 = "%5.2F +/- %5.2F"%(hMC['delm'][ptCut]['CB'][0],hMC['delm'][ptCut]['CB'][1])
    print "Dm high-low pt cut: %3.2F: gauss  %s  crystalball %s ||MC gauss  %s  crystalball %s  "%(ptCut,r1,r2,r3,r4)
 ptCut = 1.4
 fit = 'CB'
 m = 'Mass'
 for c in cases:
   h=cases[c]
   print "Jpsi mass measured - PDG %5s %5.3F +/-%5.3F "%(c,h['fitResult'+fit][ptCut][m][0]-3.0969,h['fitResult'+fit][ptCut][m][1])
 v = "mcor"
 param = {1:'Signal',2:'Mass',3:'Sigma'}
 txt   = {1:'; #it{p}_{T}>X GeV/c; Nsignal',2:'; #it{p}_{T}>X GeV/c; M [GeV/c^{2}]',3:'; #it{p}_{T}>X GeV/c; #sigma [GeV/c^{2}]'}
 choices = {'MC':hMC,'Data':hData}
 for c in choices:
   h=choices[c]
   for p in range(1,4):
    hname = 'evolutionCB'+v+param[p]+c
    ut.bookHist(h,hname,v+' evolution of '+param[p]+txt[p],20,0., 2.)
    for ptCut in ptCutList:
        k = h[hname].FindBin(ptCut)
        h[hname].SetBinContent(k,h['fitResultCB'][ptCut][myCB.GetParName(p)][0])
        h[hname].SetBinError(k,h['fitResultCB'][ptCut][myCB.GetParName(p)][1])
        k+=1
 for p in range(1,4):
   tc = hMC['evolutionC'+v].cd(p)
   hname = 'evolutionCB'+v+param[p]
   resetMinMax(hMC[hname+'MC'])
   resetMinMax(hData[hname+'Data'])
   hMC[hname+'MC'].SetLineColor(ROOT.kRed)
   hMC[hname+'MC'].GetXaxis().SetRangeUser(0.9,2.0)
   hData[hname+'Data'].GetXaxis().SetRangeUser(0.9,2.0)
   hMC[hname+'MC'].SetMaximum(1.1*max(hMC[hname+'MC'].GetMaximum(),hData[hname+'Data'].GetMaximum()))
   if p==2: 
        hMC[hname+'MC'].SetMaximum(3.5)
        hMC[hname+'MC'].SetMinimum(3.)
   if p==3: 
        hMC[hname+'MC'].SetMaximum(0.4)
        hMC[hname+'MC'].SetMinimum(0.3)
   hMC[hname+'MC'].Draw()
   hData[hname+'Data'].Draw('same')
 myPrint(hMC['evolutionC'+v],'EvolutionOfCuts_dimuonCB'+v)

def fillProjectionCB(proj,ptCut,nBins=9):
 hMC['dummy'].cd()
 bw = hMC['m_MC'].GetBinWidth(1)
 cases = {'':hData,'mc-':hMC}
 for k in range(nBins):
   for c in cases:
    h=cases[c]
    histo = h[c+proj+str(k)]
    tc = h[c.replace('mc-','MC')+'bins'+proj].cd(k+1)
    myCB = h['myCB2'+str(ptCut)+c]
    init_twoCB(myCB,bw,ptCut,h,True)
    rc = histo.Fit(myCB,'SQ','',0.5,5.)
    myCB.ReleaseParameter(3)
    myCB.ReleaseParameter(4)
    rc = histo.Fit(myCB,'SQ','',0.5,5.)
    fitResult = rc.Get()
    if not fitResult:
        N=0
        E=0
    elif fitResult.Parameter(2)>4. or fitResult.Parameter(2)<2.: 
       myCB.FixParameter(2,3.1)
       myCB.FixParameter(3,0.35)
       rc = histo.Fit(myCB,'SQ','',0.5,5.)
       fitResult = rc.Get()
    if fitResult and histo.GetEntries()>10 and fitResult.Parameter(2)<4.:
     N = fitResult.Parameter(1)
     E = fitResult.ParError(1)
     tc.Update()
     stats = tc.GetPrimitive('stats')
     stats.SetOptFit(10111)
     stats.SetFitFormat('5.4g')
     stats.SetX1NDC(0.41)
     stats.SetY1NDC(0.41)
     stats.SetX2NDC(0.99)
     stats.SetY2NDC(0.84)
     tc.Update()
     h[c+'Jpsi'+proj].SetBinContent(k+1,N)
     h[c+'Jpsi'+proj].SetBinError(k+1,E)
 myPrint(hData['bins'+proj],'diMuonBins'+proj+'CB')
 myPrint(hMC['MCbins'+proj],'MC-diMuonBins'+proj+'CB')
 hMC['mc-Jpsi'+proj].SetLineColor(ROOT.kMagenta)
 hMC['mc-Jpsi'+proj+'_scaled']=hMC['mc-Jpsi'+proj].Clone('mc-Jpsi'+proj+'_scaled')
 hMC['mc-Jpsi'+proj+'_scaled'].Scale(1./hMC['mc-Jpsi'+proj].GetSumOfWeights())
 hData['Jpsi'+proj+'_scaled']=hData['Jpsi'+proj].Clone('Jpsi'+proj+'_scaled')
 hData['Jpsi'+proj+'_scaled'].Scale(1./hData['Jpsi'+proj].GetSumOfWeights())
 hmax = 1.1*max(ut.findMaximumAndMinimum(hData['Jpsi'+proj+'_scaled'])[1],ut.findMaximumAndMinimum(hMC['mc-Jpsi'+proj+'_scaled'])[1])
 hData['Jpsi'+proj+'_scaled'].SetMaximum(hmax)
 hMC['dummy'].cd()
 hData['Jpsi'+proj+'_scaled'].Draw()
 hMC['mc-Jpsi'+proj+'_scaled'].Draw('same')
 myPrint(hMC['dummy'],'diMuonBins'+proj+'CBSummary')

def MCmigration():
 sptCut = '1.4'
 theCutTemplate =  '('+sptCut+'<pt1||'+sptCut+'<pt2)&&chi21*chi22<0&&abs(chi21)<0.9&&abs(chi22)<0.9&&p1<200&&p2<200&&p1>20&&p2>20&&mcor>0.5'
 Nbins = 25
 ut.bookHist(hMC, 'pMigration' ,'p vs pTrue',Nbins,0.,400.,Nbins,0.,400.)
 tc = hMC['kin'].cd(1)
 myDraw('p:PTRUE>>pTrue',theCutTemplate+'&&Jpsi==443') # x axis = Ptrue, y axis Preco
 hMC['pRec'] = hMC['pMigration'].ProjectionY('pRec')
 hMC['pTRUE'] = hMC['pMigration'].ProjectionX('pTRUE')
 Prec2True = {}
 for j in range(1,Nbins+1):
  tmp = hMC['pMigration'].ProjectionX(str(j),j,j)
  if tmp.GetEntries()>0: tmp.Scale(1./tmp.GetEntries())
  Prec2True[j]={}
  for l in range(1,Nbins+1): Prec2True[j][l]=tmp.GetBinContent(l)
# cross check
 ut.bookHist(hMC, 'ptrueTest' ,'pTrue from pRec',Nbins,0.,400.)
 for j in range(1,Nbins):
    nRec = hMC['pRec'].GetBinContent(j)
    eRec = hMC['pRec'].GetBinError(j)
    for l in range(1,Nbins+1):
      nTrue = nRec*Prec2True[j][l]
      eTrue = (nRec*eRec)**2
      N,E = hMC['ptrueTest'].GetBinContent(l),hMC['ptrueTest'].GetBinError(l)
      rc = hMC['ptrueTest'].SetBinContent(l,N+nTrue)
      rc = hMC['ptrueTest'].SetBinError(l,E+eTrue)
 for l in range(1,Nbins+1):
   eTrue = (nRec*eRec)**2
   E = hMC['ptrueTest'].GetBinContent(l)
   rc = hMC['ptrueTest'].SetBinError(l,ROOT.TMath.Sqrt(E))

def resetMinMax(x):
  x.SetMinimum(-1111)
  x.SetMaximum(-1111)
def plotOccupancy(sTree):
    ut.bookHist(h,'upStreamOcc',"station 1&2 function of track mom",50,-0.5,199.5,100,0.,500.)
    for n in range(sTree.GetEntries()):
        rc = sTree.GetEvent(n)
        for k in range(len(sTree.GoodTrack)):
            if sTree.GoodTrack[k]<0: continue
            p=ROOT.TVector3(sTree.Px[k],sTree.Py[k],sTree.Pz[k])
            occ = sTree.stationOcc[1]+sTree.stationOcc[2]+sTree.stationOcc[5]+sTree.stationOcc[6]
            rc=h['upStreamOcc'].Fill(occ,p.Mag())

myExpo = ROOT.TF1('expo','abs([0])*exp(-abs([1]*x))+abs([2])*exp(-abs([3]*x))+[4]',5)
myExpo.SetParName(0,'Signal1')
myExpo.SetParName(1,'tau1')
myExpo.SetParName(2,'Signal2')
myExpo.SetParName(3,'tau2')
myExpo.SetParName(4,'const')

def synchFrom48():
    path = "/media/truf/disk2/home/truf/ShipSoft/ship-ubuntu-1710-48/refit-mu/"
    for d in os.listdir(path):
        if os.path.isdir(path+'/'+d): os.system('cp -r '+path+'/'+d+'  .')
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
def updateFigures(debug=False):
   temp = subprocess.check_output('grep ".pdf" /mnt/hgfs/Images/Jpsi/AnalysisNote/introduction.tex',shell=True)
   for x in temp.split('\n'):
       for z in x.split('includegraphics'):
          tmp=z.split('figs/')
          if len(tmp)<2: continue
          ump = tmp[1].split('.pdf')
          if len(ump)<2: continue
          plot = ump[0]+'.pdf'
          if os.path.isfile(plot):
             if debug: print "update ",plot,time.ctime(os.path.getmtime(plot))
             myCopy(plot)
          else: print "plot not found",plot
def updateFiguresForPowerPoint(debug=False):
   temp = subprocess.check_output('grep ".pdf" /mnt/hgfs//VMgate/Jpsi/AnalysisNote/introduction.tex',shell=True)
   for x in temp.split('\n'):
       for z in x.split('includegraphics'):
          tmp=z.split('figs/')
          if len(tmp)<2: continue
          ump = tmp[1].split('.pdf')
          if len(ump)<2: continue
          plot = ump[0]+'.png'
          if os.path.isfile(plot):
             if debug: print "update ",plot,time.ctime(os.path.getmtime(plot))
             os.system('cp '+plot+' /mnt/hgfs/VMgate/Jpsi/AnalysisNote/png/')
          else: print "plot not found",plot
def myPrint(obj,aname):
    name = aname.replace('/','')
    obj.Print(name+'.root')
    obj.Print(name+'.pdf')
    obj.Print(name+'.png')
def eosPrint(obj,aname):
   eosServer = 'root://eosuser.cern.ch/'
   eosPath   = '/eos/user/t/truf/SHiP/muflux/FairShipWork/'
   name = aname.replace('/','')
   myPrint(obj,name)
   for ex in ['.root','.pdf','.png']:
     os.system('xrdcp -f '+name+ex+'  '+eosServer+eosPath+name+ex)
def eosCopyBack(name):
   eosServer = 'root://eosuser.cern.ch/'
   eosPath   = '/eos/user/t/truf/SHiP/muflux/FairShipWork/'
   for ex in ['.root','.pdf','.png']:
     os.system('xrdcp -f '+eosServer+eosPath+name+ex+' '+name+ex)
     myCopy(name+ex)
def eosCopy(name):
   eosServer = 'root://eosuser.cern.ch/'
   eosPath   = '/eos/user/t/truf/SHiP/muflux/FairShipWork/'
   for ex in ['.root','.pdf','.png']:
     os.system('xrdcp -f '+name+ex+' '+eosServer+eosPath+name+ex)
def fitExpo(h,hname):
    myExpo.SetParameter(0,12.)
    myExpo.SetParameter(1,-0.027)
    myExpo.FixParameter(2,0.)
    myExpo.FixParameter(3,-0.030)
    myExpo.SetParameter(4,1.)
    rc = h[hname].Fit(myExpo,'S','',250.,500.)
    fitresult = rc.Get()
    back = fitresult.Parameter(4)
    hnameb=hname+'_backsubtr'
    h[hnameb]= h[hname].Clone(hnameb)
    for n in range(1,h[hname].GetNbinsX()+1):
        h[hnameb].SetBinContent(n,h[hname].GetBinContent(n)-back)

def studyGhosts():
    sTree = sTreeMC
    h = hMC
    ut.bookHist(h,'gfCurv',             'ghost fraction vs curvature',100,0.,100.,100,0.,0.1)
    ut.bookHist(h,'gf',             'ghost fraction',100,0.,100.,100,0.,500.)
    ut.bookHist(h,'gftrue',         'ghost fraction',100,0.,100.,100,0.,500.)
    ut.bookHist(h,'gfDiff',         'ghost fraction vs reco - true mom',100,0.,100.,500,0.,500.)
    ut.bookHist(h,'RPCMatch',       'RPC matching no ghost',100,0.,10.,100,0.,10.)
    ut.bookHist(h,'RPCMatch_ghosts','RPC matching ghost>33',100,0.,10.,100,0.,10.)
    ut.bookHist(h,'R','rpc match',100,0.,100.,100,0.,10.)
    ut.bookHist(h,'Chi2/DoF','Chi2/DoF',100,0.,100.,100,0.,5.)
    ut.bookHist(h,'DoF','DoF',100,0.,100.,30,0.5,30.5)
    for n in range(sTree.GetEntries()):
        if n%500000==0:
            curFile = sTree.GetCurrentFile().GetName()
            tmp = curFile.split('/')
            print "now at event ",n,tmp[len(tmp)-2],'/',tmp[len(tmp)-1],time.ctime()
        rc = sTree.GetEvent(n)
        if not sTreeMC.FindBranch("MCghostfraction") : continue
        for k in range(sTree.nTr):
            muTagged  = False
            muTaggedX = False
            clone     = False
            if sTree.GoodTrack[k]<0: continue
            if sTree.GoodTrack[k]%2==1:
                muTaggedX = True
                if int(sTree.GoodTrack[k]/10)%2==1: muTagged = True
            if sTree.GoodTrack[k]>999:  clone = True
            if clone: continue
            if not muTagged: continue
            gf    = sTree.MCghostfraction[k]*100
            R = (sTree.Dely[k]/3.)**2+(sTree.Delx[k]/1.5)**2
            rc =   h['Chi2/DoF'].Fill(gf,sTree.Chi2[k])
            rc = h['DoF'].Fill(gf,sTree.nDoF[k])
            rc = h['R'].Fill(gf,R)
            # if R>5: continue
            if gf<1:  
                rc =   h['RPCMatch'].Fill(sTree.Delx[k],sTree.Dely[k])
            if gf>33: 
                rc =   h['RPCMatch_ghosts'].Fill(sTree.Delx[k],sTree.Dely[k])
            p     =ROOT.TVector3(sTree.Px[k],sTree.Py[k],sTree.Pz[k])
            pTrue =ROOT.TVector3(sTree.MCTruepx[k],sTree.MCTruepy[k],sTree.MCTruepz[k])
            rc    = h['gfDiff'].Fill(gf,p.Mag() - pTrue.Mag())
            rc    = h['gftrue'].Fill(gf, pTrue.Mag())
            rc    = h['gf'].Fill(gf,p.Mag() )
            rc = h['gfCurv'].Fill(gf,1./p.Mag() )
    h['P']       =h['gf'].ProjectionY('P')
    h['Ptrue']   =h['gftrue'].ProjectionY('Ptrue')
    h['Ptrue'].SetLineColor(ROOT.kMagenta)
    for x in ['gf','gftrue','Chi2/DoF','R','DoF']:
        if x.find('true')>0: h[x].SetLineColor(ROOT.kGreen)
        else:   h[x].SetLineColor(ROOT.kBlue)
        h[x+'_perfect']      =h[x].ProjectionY(x+'_perfect',1,1)
        h[x+'_ghosts']       =h[x].ProjectionY(x+'_ghosts',33,100)
        h[x+'_ghosts'].SetLineColor(ROOT.kRed)
    h['gf_perfect'].SetTitle(' ;#it{p} [GeV/c];N/5GeV')
    h['gf_perfect'].SetLineColor(ROOT.kGreen)
    h['gf_ghosts'].SetTitle('ghost > 33;#it{p} [GeV/c];N/5GeV')
    ut.writeHists(h,'ghostStudy.root')
def init_Gauss(myGauss,bw=''):
 myGauss.SetParName(0,'psi(1S)')
 myGauss.SetParName(1,'Mean')
 myGauss.SetParName(2,'Sigma')
 myGauss.SetParName(3,'SignalLow')
 myGauss.SetParName(4,'MeanLow')
 myGauss.SetParName(5,'SigmaLow')
 myGauss.SetParName(6,'p0')
 myGauss.SetParName(7,'p1')
 myGauss.SetParName(8,'p2')
 myGauss.SetParName(9,'psi(2S)')
 myGauss.SetParameter(0,1000.)
 myGauss.SetParameter(1,3.1)
 myGauss.SetParameter(2,0.35)
 myGauss.SetParameter(3,1000.)
 myGauss.SetParameter(4,1.0)
 myGauss.SetParameter(5,0.1)
 myGauss.SetParameter(6,10.)
 myGauss.SetParameter(7,1.)
 myGauss.FixParameter(8,0.)
 myGauss.FixParameter(9,0.)
 myGauss.FixParameter(10,0.)
def stupidCopy():
 for x in os.listdir('.'):
  if x.find('dimuon_all.p')<0: continue
  os.system('cp '+x+' '+ x.replace('all','AND_all'))

def analzyeMuonScattering():
  if not hMC.has_key('10GeV'): loadNtuples()
  nt   = hMC['10GeV']
  ntD  = hData['f'].nt
  ut.bookHist(hMC, 'dEdx','dE;dE [GeV/c^{2}]',100,-50.,25.,20,0.,200.)
  ut.bookHist(hMC, 'scatteringX',   '; #theta^{true}_{X} - #theta^{reco}_{X}         [rad]',100,-0.05,0.05,20,0.,200.)
  ut.bookHist(hMC, 'scatteringXcor','; #theta^{true}_{X} - #theta^{cor}_{X}          [rad]',100,-0.05,0.05,20,0.,200.)
  ut.bookHist(hMC, 'scatteringY'   ,'; #theta^{true}_{Y} - #theta^{reco}_{Y}         [rad]',100,-0.05,0.05,20,0.,200.)
  ut.bookHist(hMC, 'scatteringYcor','; #theta^{true}_{Y} - #theta^{cor}_{Y}          [rad]',100,-0.05,0.05,20,0.,200.)
  ut.bookHist(hMC, 'scatteringT',    '; #theta^{true} - #theta^{reco}                [rad]',100,-0.05,0.05,20,0.,200.)
  ut.bookHist(hMC, 'scatteringTcor', '; #theta^{true} - #theta^{reco}                [rad]',100,-0.05,0.05,20,0.,200.)
  ut.bookHist(hData, 'XcorData','; #theta^{reco}_{X} - #theta^{cor}_{X}              [rad]',100,-0.05,0.05,20,0.,200.)
  ut.bookHist(hMC,     'XcorMC','; #theta^{reco}_{X} - #theta^{cor}_{X}              [rad]'    ,100,-0.05,0.05,20,0.,200.)
  ut.bookHist(hData, 'YcorData','; #theta^{reco}_{Y} - #theta^{cor}_{Y}              [rad]',100,-0.05,0.05,20,0.,200.)
  ut.bookHist(hMC,     'YcorMC','; #theta^{reco}_{Y} - #theta^{cor}_{Y}              [rad]'    ,100,-0.05,0.05,20,0.,200.)
  ut.bookHist(hData, 'TcorData','; #theta^{reco}  - #theta^{cor}               [rad]',100,-0.05,0.05,20,0.,200.)
  ut.bookHist(hMC,     'TcorMC','; #theta^{reco}  - #theta^{cor}               [rad]'    ,100,-0.05,0.05,20,0.,200.)

  ROOT.gROOT.cd()
  nt.Draw('p1:(p1-p1True)>>dEdx','')
  nt.Draw('p2:(p2-p2True)>>+dEdx','')
  ptCut1 = 'pt1>0'
  ptCut2 = 'pt2>0'
  nt.Draw('p1:p1x/p1z-prec1x/prec1z>>scatteringX',ptCut1 )
  nt.Draw('p2:p2x/p2z-prec2x/prec2z>>+scatteringX',ptCut2 )
  nt.Draw('p1:p1x/p1z-rec1x/(rec1z- '+str(zTarget)+')>>scatteringXcor',ptCut1 )
  nt.Draw('p2:p2x/p2z-rec2x/(rec2z- '+str(zTarget)+')>>+scatteringXcor',ptCut2 )

  nt.Draw('p1:p1y/p1z-prec1y/prec1z>>scatteringY','')
  nt.Draw('p2:p2y/p2z-prec2y/prec2z>>+scatteringY','')
  nt.Draw('p1:p1y/p1z-rec1y/(rec1z- '+str(zTarget)+')>>scatteringYcor')
  nt.Draw('p2:p2y/p2z-rec2y/(rec2z- '+str(zTarget)+')>>+scatteringYcor')

  nt.Draw('p1:sqrt(p1x*p1x+p1y*p1y)/p1z-sqrt(prec1y*prec1y+prec1x*prec1x)/prec1z>>scatteringT','')
  nt.Draw('p2:sqrt(p2x*p2x+p2y*p2y)/p2z-sqrt(prec2y*prec2y+prec2x*prec2x)/prec2z>>+scatteringT','')
  nt.Draw('p1:sqrt(p1x*p1x+p1y*p1y)/p1z-sqrt(rec1y*rec1y+rec1x*rec1x)/(rec1z- '+str(zTarget)+')>>scatteringTcor')
  nt.Draw('p2:sqrt(p2x*p2x+p2y*p2y)/p2z-sqrt(rec2y*rec2y+rec2x*rec2x)/(rec2z- '+str(zTarget)+')>>+scatteringTcor')
# look at applied angle correction
  nt.Draw('p1:prec1x/prec1z-rec1x/(rec1z- '+str(zTarget)+')>>XcorMC',ptCut1 )
  nt.Draw('p2:prec2x/prec2z-rec2x/(rec2z- '+str(zTarget)+')>>XcorMC',ptCut2)
  ntD.Draw('p1:prec1x/prec1z-rec1x/(rec1z- '+str(zTarget)+')>>XcorData',ptCut1 )
  ntD.Draw('p2:prec2x/prec2z-rec2x/(rec2z- '+str(zTarget)+')>>XcorData',ptCut2)

  nt.Draw('p1:prec1y/prec1z-rec1y/(rec1z- '+str(zTarget)+')>>YcorMC',ptCut1 )
  nt.Draw('p2:prec2y/prec2z-rec2y/(rec2z- '+str(zTarget)+')>>YcorMC',ptCut2)
  ntD.Draw('p1:prec1y/prec1z-rec1y/(rec1z- '+str(zTarget)+')>>YcorData',ptCut1 )
  ntD.Draw('p2:prec2y/prec2z-rec2y/(rec2z- '+str(zTarget)+')>>YcorData',ptCut2)

  nt.Draw('p1:sqrt(prec1y*prec1y+prec1x*prec1x)/prec1z-sqrt(rec1y*rec1y+rec1x*rec1x)/(rec1z- '+str(zTarget)+')>>TcorMC',ptCut1 )
  nt.Draw('p2:sqrt(prec2y*prec2y+prec2x*prec2x)/prec2z-sqrt(rec2y*rec2y+rec2x*rec2x)/(rec2z- '+str(zTarget)+')>>TcorMC',ptCut2)
  ntD.Draw('p1:sqrt(prec1y*prec1y+prec1x*prec1x)/prec1z-sqrt(rec1y*rec1y+rec1x*rec1x)/(rec1z- '+str(zTarget)+')>>TcorData',ptCut1 )
  ntD.Draw('p2:sqrt(prec2y*prec2y+prec2x*prec2x)/prec2z-sqrt(rec2y*rec2y+rec2x*rec2x)/(rec2z- '+str(zTarget)+')>>TcorData',ptCut2)

  hMC['dEdxMean']=hMC['dEdx'].ProjectionY('dEdxMean')
  hMC['dEdxMean'].Reset()
  for n in range(1,hMC['dEdxMean'].GetNbinsX()+1):
    tmp = hMC['dEdx'].ProjectionX('tmp',n,n)
    hMC['dEdxMean'].SetBinContent(n,tmp.GetMean())
    hMC['dEdxMean'].SetBinError(n,tmp.GetRMS())
  hMC['dEdxMean'].Fit('pol2','S','',10.,190.)
#
  ut.bookCanvas(hMC,'scattering','scattering X and Y',1600,900,3,3)
  ut.bookCanvas(hMC,'singlePlot',' ',900,1200,1,1)
  j=1
  for x in ['scatteringX','scatteringY','scatteringT','scatteringXcor','scatteringYcor','scatteringTcor']:
    hMC[x+'Mean']=hMC[x].ProjectionX(x+'Mean')
    tc=hMC['scattering'].cd(j)
    hMC[x].Draw('colz')
    j+=1
  for tc in [hMC['scattering'].cd(5),hMC['singlePlot'].cd()]:
   hMC['scatteringXcorMean'].SetLineColor(ROOT.kGreen)
   hMC['scatteringXcorMean'].Draw()
   hMC['scatteringXMean'].Draw('same')
  myPrint(tc,'scatteringX')
  for tc in [hMC['scattering'].cd(6),hMC['singlePlot'].cd()]:
   hMC['scatteringYcorMean'].SetLineColor(ROOT.kGreen)
   hMC['scatteringYcorMean'].Draw()
   hMC['scatteringYMean'].Draw('same')
  myPrint(tc,'scatteringY')
  for tc in [hMC['scattering'].cd(7),hMC['singlePlot'].cd()]:
   hMC['scatteringTcorMean'].SetLineColor(ROOT.kGreen)
   hMC['scatteringTcorMean'].Draw()
   hMC['scatteringTMean'].Draw('same')
  myPrint(tc,'scatteringT')

  ut.bookCanvas(hMC,'scatteringDataMC','scattering Data vs MC',1600,900,2,3)
  hMC['scatteringDataMC'].cd(1)
  for proj in ['X','Y','T']:
   for x in ['RMS','Mean']:
    hMC['scatt'+proj+'cor'+x+'_MC']=hMC[proj+'corMC'].ProjectionY('scatt'+proj+'cor'+x+'_MC')
    hMC['scatt'+proj+'cor'+x+'_MC'].Reset()
    hMC['scatt'+proj+'cor'+x+'_MC'].GetYaxis().SetTitle('[rad]')
    hData['scatt'+proj+'cor'+x+'_Data']=hData[proj+'corData'].ProjectionY('scatt'+proj+'cor'+x+'_Data')
    hData['scatt'+proj+'cor'+x+'_Data'].GetYaxis().SetTitle('[rad]')
    hData['scatt'+proj+'cor'+x+'_Data'].Reset()
   for n in range(1,hMC['scatt'+proj+'corRMS_MC'].GetNbinsX()+1):
    tmp = hMC[proj+'corMC'].ProjectionX('tmp',n,n)
    rc = tmp.Fit('gaus','SQ')
    fitresult = rc.Get()
    hMC['scatt'+proj+'corRMS_MC'].SetBinContent(n,fitresult.Parameter(2))
    hMC['scatt'+proj+'corMean_MC'].SetBinContent(n,fitresult.Parameter(1))
    tmp = hData[proj+'corData'].ProjectionX('tmp',n,n)
    rc = tmp.Fit('gaus','SQ')
    fitresult = rc.Get()
    hData['scatt'+proj+'corRMS_Data'].SetBinContent(n,fitresult.Parameter(2))
    hData['scatt'+proj+'corMean_Data'].SetBinContent(n,fitresult.Parameter(1))
    hData['scatt'+proj+'corMean_Data'].SetTitle('Mean; #it{p} [GeV/c]; mean correction [rad]')
    hData['scatt'+proj+'corRMS_Data'].SetTitle('RMS; #it{p} [GeV/c]; sigma of correction [rad]')
  j = 1
  for proj in ['X','Y','T']:
    for x in ['RMS','Mean']:
      for tc in [hMC['scatteringDataMC'].cd(j),hMC['singlePlot'].cd()]:
       hData['scatt'+proj+'cor'+x+'_Data'].SetMinimum( min(hData['scatt'+proj+'cor'+x+'_Data'].GetMinimum(),hMC['scatt'+proj+'cor'+x+'_MC'].GetMinimum()))
       hData['scatt'+proj+'cor'+x+'_Data'].SetMaximum( max(hData['scatt'+proj+'cor'+x+'_Data'].GetMaximum(),hMC['scatt'+proj+'cor'+x+'_MC'].GetMaximum()))
       hData['scatt'+proj+'cor'+x+'_Data'].SetMinimum(0)
       hData['scatt'+proj+'cor'+x+'_Data'].SetStats(0)
       hData['scatt'+proj+'cor'+x+'_Data'].Draw()
       hMC['scatt'+proj+'cor'+x+'_MC'].SetLineColor(ROOT.kMagenta)
       hMC['scatt'+proj+'cor'+x+'_MC'].Draw('same')
       if proj=='T': myPrint(tc,'scatteringDataMC_'+x)
      j+=1

def JpsiAcceptance0():
    hMC['f0']=ROOT.TFile.Open(os.environ['EOSSHIP']+"/eos/experiment/ship/data/jpsicascade/cascade_MSEL61_20M.root")
    nt=hMC['f0'].nt
    two = f.Get('2').Clone('2')
    primJpsi  = two.GetBinContent(1)
    totalJpsi = two.GetSumOfWeights() # = nt.GetEntries()
    print "primary: %5.2F%%,  cascade: %5.2F%% "%(primJpsi/totalJpsi*100.,100.-primJpsi/totalJpsi*100.)
#
    ut.bookHist(hMC,'Jpsi_p/pt','momentum vs Pt (GeV);#it{p} [GeV/c]; #it{p}_{T} [GeV/c]',500,0.,500.,100,0.,10.)
    ut.bookHist(hMC,'Jpsi_y',   'rapidity cm; y_{CM}',100,-1.,5.,25,0.,500.,10,0.,10.)
    for event in nt:
       mom = ROOT.TLorentzVector(event.px,event.py,event.pz,event.E)
       rc = hMC['Jpsi_p/pt'].Fill(mom.P(),mom.Pt())
       rc = hMC['Jpsi_y'].Fill(mom.Rapidity(),mom.P(),mom.Pt())

def analyzeInvMassBias():
  if not hMC.has_key('f10'):
    hMC['f10'] = ROOT.TFile('ntuple-invMass-MC-10GeV.root')
    hMC['10GeV']=hMC['f10'].nt
    hData['f'] = ROOT.TFile('ntuple-InvMass-refitted.root')
  InvMassPlots = [160,0.,8.]
  ptCutList = [0.0,0.8,0.9,1.0,1.1,1.2,1.3,1.4,1.5,1.6]
  nt = hMC['10GeV']
  ut.bookHist(hMC,'deltaXY','diff xy muon1 and muon2;x [cm]; y [cm]',100,0.,20.,100,0.,20.)
  nt.Draw('abs(prec1x-prec2x):abs(prec1y-prec2y)>>deltaXY','mcor<0.25')
# muon dEdx
  ut.bookHist(hMC, 'delpTrue2' ,'p-pTrue vs pTrue',20,0.,400.,50,-50.,50.)
  nt.Draw('(p1-p1True):p1>>delpTrue2','Jpsi==443&&pt1>1.4')
  nt.Draw('(p2-p2True):p2>>+delpTrue2','Jpsi==443&&pt2>1.4') # applying cuts does not make a difference
# inv mass from true mom
  for x in ['','_truePt']:
   ut.bookHist(hMC, 'm_MCtrue'+x, 'inv mass;M [GeV/c^{2}];#it{p}_{Tmin} [GeV/c]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2],10,0.,2.)
   ut.bookHist(hMC, 'm_MCdEdx'+x, 'inv mass;M [GeV/c^{2}];#it{p}_{Tmin} [GeV/c]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2],10,0.,2.)
   ut.bookHist(hMC, 'm_MCmult'+x, 'inv mass;M [GeV/c^{2}];#it{p}_{Tmin} [GeV/c]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2],10,0.,2.)
   ut.bookHist(hMC, 'm_MCcor'+x,  'inv mass;M [GeV/c^{2}];#it{p}_{Tmin} [GeV/c]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2],10,0.,2.)
   ut.bookHist(hMC, 'm_MCcor2'+x, 'inv mass;M [GeV/c^{2}];#it{p}_{Tmin} [GeV/c]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2],10,0.,2.)
   ut.bookHist(hMC, 'm_MCtrueSigma'+x, '#sigma_{M} ;M [GeV/c^{2}]',10,0.,2.)
   ut.bookHist(hMC, 'm_MCdEdxSigma'+x, '#sigma_{M} ;M [GeV/c^{2}]',10,0.,2.)
   ut.bookHist(hMC, 'm_MCmultSigma'+x, '#sigma_{M} ;M [GeV/c^{2}]',10,0.,2.)
   ut.bookHist(hMC, 'm_MCcorSigma'+x,  '#sigma_{M} ;M [GeV/c^{2}]',10,0.,2.)
   ut.bookHist(hMC, 'm_MCcor2Sigma'+x, '#sigma_{M} ;M [GeV/c^{2}]',10,0.,2.)
  Ptrue = {}
  Prec  = {}
  Pcor  = {}
  Pcor2  = {}
  x = '_truePt'
  for event in nt:
   if event.Jpsi!=443: continue
   Ptrue[1] = ROOT.Math.PxPyPzMVector(event.p1x,event.p1y,event.p1z,muonMass)
   Ptrue[2] = ROOT.Math.PxPyPzMVector(event.p2x,event.p2y,event.p2z,muonMass)
   Prec[1]  = ROOT.Math.PxPyPzMVector(event.prec1x,event.prec1y,event.prec1z,muonMass)
   Prec[2]  = ROOT.Math.PxPyPzMVector(event.prec2x,event.prec2y,event.prec2z,muonMass)
   tdir = ROOT.TVector3(event.rec1x,event.rec1y,event.rec1z-zTarget)
   cor = Prec[1].P()/tdir.Mag()
   Pcor[1]  = ROOT.Math.PxPyPzMVector(tdir.X()*cor,tdir.Y()*cor,tdir.Z()*cor,muonMass)
   cor = Ptrue[1].P()/tdir.Mag()
   Pcor2[1]  = ROOT.Math.PxPyPzMVector(tdir.X()*cor,tdir.Y()*cor,tdir.Z()*cor,muonMass)
   tdir = ROOT.TVector3(event.rec2x,event.rec2y,event.rec2z-zTarget)
   cor = Prec[2].P()/tdir.Mag()
   Pcor[2]  = ROOT.Math.PxPyPzMVector(tdir.X()*cor,tdir.Y()*cor,tdir.Z()*cor,muonMass)
   cor = Ptrue[2].P()/tdir.Mag()
   Pcor2[2]  = ROOT.Math.PxPyPzMVector(tdir.X()*cor,tdir.Y()*cor,tdir.Z()*cor,muonMass)
   P=Ptrue[1]+Ptrue[2]
   PtMinTrue = min(Ptrue[1].Pt(),Ptrue[2].Pt())
   PtMin = min(Prec[1].Pt(),Prec[2].Pt())
   rc = hMC['m_MCtrue'].Fill(P.M(),PtMin)
   rc = hMC['m_MCtrue'+x].Fill(P.M(),PtMinTrue)
   P=Pcor[1]+Pcor[2]
   PtMin = min(Pcor[1].Pt(),Pcor[2].Pt())
   rc = hMC['m_MCcor'].Fill(P.M(),PtMin)
   rc = hMC['m_MCcor'+x].Fill(P.M(),PtMinTrue)
   P=Pcor2[1]+Pcor2[2]
   PtMin = min(Pcor2[1].Pt(),Pcor2[2].Pt())
   rc = hMC['m_MCcor2'].Fill(P.M(),PtMin)
   rc = hMC['m_MCcor2'+x].Fill(P.M(),PtMinTrue)
   PdEloss = {}
   Pmult   = {}
   for j in range(1,3): 
       dEloss=Prec[j].P()/Ptrue[j].P()
       PdEloss[j]= ROOT.Math.PxPyPzMVector(Ptrue[j].X()*dEloss,Ptrue[j].Y()*dEloss,Ptrue[j].Z()*dEloss,muonMass)
       Pmult[j]= ROOT.Math.PxPyPzMVector(Prec[j].X()/dEloss,Prec[j].Y()/dEloss,Prec[j].Z()/dEloss,muonMass)
   P=PdEloss[1]+PdEloss[2]
   PtMin = min(PdEloss[1].Pt(),PdEloss[2].Pt())
   rc = hMC['m_MCdEdx'].Fill(P.M(),PtMin)
   rc = hMC['m_MCdEdx'+x].Fill(P.M(),PtMinTrue)
   P=Pmult[1]+Pmult[2]
   PtMin = min(Pmult[1].Pt(),Pmult[2].Pt())
   rc = hMC['m_MCmult'].Fill(P.M(),PtMin)
   rc = hMC['m_MCmult'+x].Fill(P.M(),PtMinTrue)
  for z in ['','_truePt']:
   for x in ['m_MCdEdx','m_MCmult','m_MCtrue','m_MCcor','m_MCcor2']:
    hname = x+'Mean'+z
    hMC[hname] = hMC[x+z].ProjectionY(hname)
    hMC[hname].Reset()
    hMC[hname].SetStats(0)
    hMC[hname.replace('Mean','Sigma')].SetStats(0)
    Nmax = hMC[hname].GetNbinsX()
    for k in range(Nmax):
     tmp = hMC[x+z].ProjectionX('tmp',k,Nmax)
     if x.find('true')>0:
      hMC[hname].SetBinContent(k,tmp.GetMean())
      hMC[hname].SetBinError(k,0.01)
     else:
      rc = tmp.Fit('gaus','S')
      fitresult = rc.Get()
      hMC[hname].SetBinContent(k,fitresult.Parameter(1))
      hMC[hname].SetBinError(k,fitresult.ParError(1))
      hMC[hname.replace('Mean','Sigma')].SetBinContent(k,fitresult.Parameter(2))
      hMC[hname.replace('Mean','Sigma')].SetBinError(k,fitresult.ParError(2))
   ut.bookCanvas(hMC,'TinvMassBiasMean'+z,'inv mass bias, mean',1900,650,1,1)
   ut.bookCanvas(hMC,'TinvMassBiasSigma'+z,'inv mass bias, sigma',1900,650,1,1)
   for tt in ['Mean','Sigma']:
    t=tt+z
    hMC['TinvMassBias'+t].cd()
    if tt=='Mean':
     hMC['m_MCdEdx'+t].SetMinimum(2.)
     hMC['m_MCdEdx'+t].SetMaximum(4.5)
    else:
     hMC['m_MCdEdx'+t].SetMinimum(0.)
     hMC['m_MCdEdx'+t].SetMaximum(1.0)
    hMC['m_MCdEdx'+t].SetMarkerStyle(21)
    hMC['m_MCdEdx'+t].SetLineColor(ROOT.kRed)
    hMC['m_MCmult'+t].SetLineColor(ROOT.kMagenta)
    hMC['m_MCmult'+t].SetMarkerStyle(20)
    hMC['m_MCcor'+t].SetLineColor(ROOT.kBlue)
    hMC['m_MCcor'+t].SetMarkerStyle(29)
    hMC['m_MCcor'+t].SetMarkerSize(1.8)
    hMC['m_MCcor2'+t].SetLineColor(ROOT.kGreen)
    hMC['m_MCcor2'+t].SetMarkerStyle(28)
    hMC['m_MCcor2'+t].SetMarkerSize(1.8)
    hMC['m_MCdEdx'+t].Draw()
    hMC['m_MCmult'+t].Draw('same')
    hMC['m_MCtrue'+t].Draw('same')
    hMC['m_MCcor'+t].Draw('same')
    hMC['m_MCcor2'+t].Draw('same')
    hMC['legInvMassBias'+t]=ROOT.TLegend(0.11,0.66,0.48,0.92)
    rc = hMC['legInvMassBias'+t].AddEntry(hMC['m_MCdEdx'+t],'effect of dEdx','PL')
    rc = hMC['legInvMassBias'+t].AddEntry(hMC['m_MCmult'+t],'effect of multiple scattering','PL')
    rc = hMC['legInvMassBias'+t].AddEntry(hMC['m_MCcor2'+t],'true momentum, correction of direction','PL')
    rc = hMC['legInvMassBias'+t].AddEntry(hMC['m_MCcor'+t], 'reco momentum, correction of direction','PL')
    rc = hMC['legInvMassBias'+t].AddEntry(hMC['m_MCtrue'+t],'true mass','PL')
    hMC['legInvMassBias'+t].Draw()
    myPrint(hMC['TinvMassBias'+t],'invMassBias'+t)

def debug():
    Nstat = {}
    for n in range(sTreeMC.GetEntries()):
        rc = sTreeMC.GetEvent(n)  
        fname = sTreeMC.GetCurrentFile().GetName()
        if not Nstat.has_key(fname): Nstat[fname]=[sTreeMC.GetEntries(),0,0,0]
        rc = sTreeMC.GetEvent(n)
        Nstat[fname][1]+=sTreeMC.nTr
        Nstat[fname][2]+=sTreeMC.MCRecoRPC.size()
        Nstat[fname][3]+=sTreeMC.MCRecoDT.size()
    return Nstat

def debugInvMass(sTree,nMax=1000):
    stats = {}
    currentFile=""
    N=0
    for n in range(0,sTree.GetEntries()):
        rc = sTree.GetEvent(n)
        if sTree.GetCurrentFile().GetName()!=currentFile:
          currentFile = sTree.GetCurrentFile().GetName()
          nInFile = n
        P    = {}
        IP   = {}
        Pcor = {}
        Pcor2 = {}
        for k in range(len(sTree.GoodTrack)):
            if sTree.GoodTrack[k]<0: continue
            if sTree.GoodTrack[k]%2!=1 or  int(sTree.GoodTrack[k]/10)%2!=1: continue
            if sTree.GoodTrack[k]>999:  continue
            P[k] = ROOT.Math.PxPyPzMVector(sTree.Px[k],sTree.Py[k],sTree.Pz[k],muonMass)
            l = (sTree.z[k] - zTarget)/(sTree.Pz[k]+ 1E-19)
            x = sTree.x[k]+l*sTree.Px[k]
            y = sTree.y[k]+l*sTree.Py[k]
            IP[k] = ROOT.TMath.Sqrt(x*x+y*y)
# make dE correction plus direction from measured point
            dline   = ROOT.TVector3(sTree.x[k],sTree.y[k],sTree.z[k]-zTarget)
            Ecor = P[k].E()+dEdxCorrection(P[k].P())
            norm = dline.Mag()
            Pcor[k]  = ROOT.Math.PxPyPzMVector(Ecor*dline.X()/norm,Ecor*dline.Y()/norm,Ecor*dline.Z()/norm,muonMass)
            Pcor2[k] = ROOT.Math.PxPyPzMVector(P[k].P()*dline.X()/norm,P[k].P()*dline.Y()/norm,P[k].P()*dline.Z()/norm,muonMass)
# now we have list of selected tracks, P.keys()
        if len(P)<2: continue
        shortName = currentFile.split('/')[11]
        if not stats.has_key(shortName): stats[shortName]=[]
        stats[shortName].append(n-nInFile)
        N+=1
        if N>nMax: break
    return stats
def JpsiPrimary():
    y_beam = yBeam()
    ut.bookHist(hMC,'Y','Y of Jpsi     ;y_{CMS}',100,-2.,2.)
    ut.bookHist(hMC,'Yprim','Y of primary Jpsi     ;y_{CMS}',100,-2.,2.)
    ut.bookHist(hMC,'Ysec','Y of Jpsi from cascasde;y_{CMS}', 100,-2.,2.)
    ut.bookHist(hMC,'Y_rec','Y of Jpsi ;y_{CMS}',100,-2.,2.)
    ut.bookHist(hMC,'Yprim_rec','Y of primary Jpsi ;y_{CMS}',100,-2.,2.)
    ut.bookHist(hMC,'Ysec_rec','Y of Jpsi from cascasde;y_{CMS}', 100,-2.,2.)
    ut.bookHist(hMC,'deltaYcor','ycor-YTRUE;#Delta y', 100,-1.,1.)
#
    ROOT.gROOT.cd()
    T = ROOT.TLatex()
    T.SetTextColor(ROOT.kBlue)
#
    tc = hMC['dummy'].cd()
    tc.SetLogy(0)
    hMC['Jpsi'].Draw('YTRUE-'+str(y_beam)+'>>Y')
    hMC['Jpsi'].Draw('YTRUE-'+str(y_beam)+'>>Yprim','Pmother==400')
    hMC['Jpsi'].Draw('YTRUE-'+str(y_beam)+'>>Ysec','Pmother>10&&Pmother<400')
    hMC['Yprim'].SetLineColor(ROOT.kRed)
    hMC['Yprim'].SetTitle('')
    hMC['Yprim'].SetStats(0)
    hMC['Ysec'].SetStats(0)
    hMC['Yprim'].Draw()
    hMC['Ysec'].Draw('same')
    hMC['lyprim']=ROOT.TLegend(0.6,0.75,0.95,0.85)
    l1 = hMC['lyprim'].AddEntry(hMC['Yprim'],'from primary production','PL')
    l1.SetTextColor(hMC['Yprim'].GetLineColor())
    l2 = hMC['lyprim'].AddEntry(hMC['Ysec'],'from cascade production','PL')
    l2.SetTextColor(hMC['Ysec'].GetLineColor())
    hMC['lyprim'].Draw()
    NA50 = hMC['Yprim'].Integral(hMC['Yprim'].FindBin(-0.425 ),hMC['Yprim'].FindBin(0.575))
    Acc_NA50 = NA50/hMC['Yprim'].GetSumOfWeights()
    rc = T.DrawLatexNDC(0.29,0.15,"NA50: -0.425<y<0.575:%5.1F%%"%(Acc_NA50*100))
    tc.Update()
    myPrint(tc,'YJpsiPrimAndSec')
#
    sptCut = '1.4'
    theCut =  '('+sptCut+'<pt1||'+sptCut+'<pt2)&&chi21*chi22<0&&abs(chi21)<0.9&&abs(chi22)<0.9&&p1<300&&p2<300&&p1>20&&p2>20&&mcor>0.20'
    theCut = theCut.replace('pt1','pt1cor')
    theCut = theCut.replace('pt2','pt2cor')
    makeProjection('cosCScor',-1.0,1.0,'cosCScor',theCut,nBins=10,ntName='Jpsi',printout=0)
    dataAcc = hData['JpsicosCScor'].Integral(hData['JpsicosCScor'].FindBin(-0.5),hData['JpsicosCScor'].FindBin(0.5))
    dataAcc = dataAcc/hData['JpsicosCScor'].GetSumOfWeights()
    MCAcc = hMC['mc-JpsicosCScor'].Integral(hMC['mc-JpsicosCScor'].FindBin(-0.5),hMC['mc-JpsicosCScor'].FindBin(0.5))
    MCAcc = MCAcc/hMC['mc-JpsicosCScor'].GetSumOfWeights()
    print "JUST FOR INFORMATION:  -0.5<cosCScor<0.5,  acceptance:  data=%5.2F%%,  MC=%5.2F%%  "%(dataAcc*100,MCAcc*100)

    tc = hMC['dummy'].cd()
    theCut+= '&&cosCScor>-0.5&&cosCScor<0.5'
    hMC['Jpsi'].Draw('YTRUE-'+str(y_beam)+'>>Y_rec',               'mcor>2.0&&mcor<4.&&'+theCut)
    hMC['Jpsi'].Draw('YTRUE-'+str(y_beam)+'>>Yprim_rec',           'Pmother==400&&mcor>2.0&&mcor<4.&&'+theCut)
    hMC['Jpsi'].Draw('YTRUE-'+str(y_beam)+'>>Ysec_rec', 'Pmother>10&&Pmother<400&&mcor>2.0&&mcor<4.&&'+theCut)

    hMC['YP8_rec'] = hMC['Yprim_rec'].Clone('YP8_rec')
    hMC['JpsiP8'].Draw('YTRUE-'+str(y_beam)+'>>YP8_rec',               'mcor>2.0&&mcor<4.&&'+theCut)

    for x in ['','prim','sec']:
        hMC[x+'Eff']=ROOT.TEfficiency(hMC['Y'+x+'_rec'],hMC['Y'+x])
        hMC[x+'Eff'].Draw()
        tc.Update()
        hMC[x+'Effgraph'] = hMC[x+'Eff'].GetPaintedGraph()
        hMC[x+'Effgraph'].SetMinimum(0.0)
        hMC[x+'Effgraph'].SetMaximum(0.4)
        hMC[x+'Effgraph'].GetXaxis().SetRangeUser(-2.,2.)
    hMC['primEff'].SetLineColor(ROOT.kRed)
    hMC['primEff'].Draw()
    hMC['secEff'].Draw('same')
    ypos = 0.8
    Eff_Muflux={}
    for xx in ['Y','Yprim','Ysec ']:
     x=xx.replace(' ','')
     Muflux     = hMC[x].Integral(hMC['Yprim'].FindBin(0.4),hMC['Yprim'].FindBin(1.5))
     Muflux_rec = hMC[x+'_rec'].Integral(hMC['Yprim'].FindBin(0.4),hMC['Yprim'].FindBin(1.5))
     Eff_Muflux[x] = Muflux_rec/Muflux
     # rc = T.DrawLatexNDC(0.18,ypos,xx.replace('Y','')+": 0.4<y<1.5:%5.1F%%"%(Eff_Muflux[x]*100))
     ypos-=0.1
    tc.Update()
    myPrint(tc,'YEffJpsiPrimAndSec')
    hMC['Yprim'].Draw()
    hMC['Ysec'].Draw('same')
    hMC['lyprim'].Draw()
    ypos = 0.4
    Acc_Muflux={}
    for xx in ['Y','Yprim','Ysec ']:
     x=xx.replace(' ','')
     Muflux     = hMC[x].Integral(hMC['Yprim'].FindBin(0.4),hMC['Yprim'].FindBin(1.5))
     total      = hMC[x].GetSumOfWeights()
     Acc_Muflux[x] = Muflux/total
     rc = T.DrawLatexNDC(0.18,ypos,xx.replace('Y','')+": 0.4<y<1.5/total:%5.1F%%"%(Acc_Muflux[x]*100))
     ypos-=0.1
    tc.Update()
    myPrint(tc,'YAccJpsiPrimAndSec')
#  ycor resolution
    hMC['Jpsi'].Draw('ycor-YTRUE>>deltaYcor',theCut)
    hMC['deltaYcor'].Fit('gaus')
    tc.Update()
    stats = tc.GetPrimitive('stats')
    stats.SetOptFit(10111)
    stats.SetX1NDC(0.60)
    stats.SetY1NDC(0.60)
    stats.SetX2NDC(0.98)
    stats.SetY2NDC(0.93)
    tc.Update()
    myPrint(tc,'YcorResolution')
#
    makeProjection('ycor',0.4,1.5,'y_{CMS}',theCut,nBins=1,ntName='Jpsi',printout=0)
    fitFun = hData['ycor0'].GetFunction('Dataycor0')
    Ndata = fitFun.GetParameter(0)
    Edata = fitFun.GetParError(0)
    Nsignal = Ndata/Eff_Muflux['Y']
    Esignal = Edata/Eff_Muflux['Y']
    print "Ndata fitted: %5.2F +/- %5.2F"%(Ndata,Edata)
    print "Ndata eff corrected: %5.2F +/- %5.2F"%(Nsignal,Esignal)
#
    makeProjection('ycor',0.,2.,'y_{CMS}',theCut,nBins=20,ntName='Jpsi',printout=0)
    hData['Jpsiycor_effCorrected']  = hData['Jpsiycor'].Clone('Jpsiycor_effCorrected')
    hMC['mc-Jpsiycor_effCorrected'] = hMC['mc-Jpsiycor'].Clone('mc-Jpsiycor_effCorrected')
    nSteps = 11
    binWidth = hData['Jpsiycor'].GetBinWidth(1)/float(nSteps)
    for X in [ [hData['Jpsiycor'],hData["Jpsiycor_effCorrected"]],[hMC['mc-Jpsiycor'],hMC["mc-Jpsiycor_effCorrected"]] ]:
      for n in range(1,hData['Jpsiycor'].GetNbinsX()+1): 
         x    = X[0].GetBinLowEdge(n)
         y    = X[0].GetBinContent(n)
         yerr = X[0].GetBinError(n)
         meanEff = 0
         for k in range(nSteps):
           meanEff += hMC['Effgraph'].Eval(x)
           x+=binWidth
         e = meanEff/float(nSteps)
         if e>0.01:
          X[1].SetBinContent(n,y/e)
          X[1].SetBinError(n,yerr/e)
         else:
          X[1].SetBinContent(n,0.)
          X[1].SetBinError(n,0.)

# y distrib from cascade
    ut.readHists(hMC,'Ydistributions.root')
    hMC['YP8'] = hMC['Ypt_P8'].ProjectionX('YP8')
    hMC['dummy'].cd()
    a,b = hData["Jpsiycor_effCorrected"].FindBin(0.3),hData["Jpsiycor_effCorrected"].FindBin(1.4)
    c,d = hMC["Y"].FindBin(0.3),hMC["Y"].FindBin(1.4)
    sbin = hData["Jpsiycor_effCorrected"].GetBinWidth(1)/hMC['Y'].GetBinWidth(1)
    hMC['Y'].Scale(hData["Jpsiycor_effCorrected"].Integral(a,b)/hMC["Y"].Integral(c,d))
    hMC['Y'].Scale(sbin)
    hMC['YP8'].Scale(hData["Jpsiycor_effCorrected"].Integral(a,b)/hMC["YP8"].Integral(c,d))
    hMC['YP8'].Scale(sbin)
    hData["Jpsiycor_effCorrected"].SetStats(0)
    hData["Jpsiycor_effCorrected"].SetLineColor(ROOT.kBlue)
    hMC['mc-Jpsiycor_effCorrected'].SetLineColor(ROOT.kMagenta)
    hMC['Y'].SetLineColor(ROOT.kMagenta)
    hMC['YP8'].SetLineColor(ROOT.kCyan)
    hMC['Y'].SetStats(0)
    hMC['YP8'].SetStats(0)
    hMC['mc-Jpsiycor_effCorrected'].SetStats(0)
    hData["Jpsiycor_effCorrected"].SetMinimum(0.)
    hData["Jpsiycor_effCorrected"].SetMaximum(20000.)
    hData["Jpsiycor_effCorrected"].Draw()
    hMC['Y'].Draw('same')
    hMC['YP8'].Draw('same')
# cross check, take efficiency, apply to Yrec and compare with Ytrue
    hMC['mc-Jpsiycor_effCorrected'].Scale(hData["Jpsiycor_effCorrected"].Integral(a,b)/hMC["mc-Jpsiycor_effCorrected"].Integral(a,b))
    hMC['mc-Jpsiycor_effCorrected'].Draw('same')
    hMC['lyeffcor']=ROOT.TLegend(0.48,0.63,0.95,0.85)
    l1 = hMC['lyeffcor'].AddEntry(hData["Jpsiycor_effCorrected"],'data eff corrected','PL')
    l1.SetTextColor(hData["Jpsiycor_effCorrected"].GetLineColor())
    l2 = hMC['lyeffcor'].AddEntry(hMC['mc-Jpsiycor_effCorrected'],'MC cascade eff corrected','PL')
    l2.SetTextColor(hMC['mc-Jpsiycor_effCorrected'].GetLineColor())
    l3 = hMC['lyeffcor'].AddEntry(hMC['Y'],'MC cascade truth','PL')
    l3.SetTextColor(hMC['Y'].GetLineColor())
    l4 = hMC['lyeffcor'].AddEntry(hMC['YP8'],'MC Pythia8 truth','PL')
    l4.SetTextColor(hMC['YP8'].GetLineColor())
    hMC['lyeffcor'].Draw()
    myPrint(hMC['dummy'],'YeffCorrectedXcheck')
#
    cases = {'Y':ROOT.kMagenta,'Yprim':ROOT.kRed,'Ysec':ROOT.kGreen}
    for x in cases:
     hMC[x+'_rec_arbNorm'] = hMC[x+'_rec'].Clone(x+'_rec_arbNorm')
     hMC[x+'_rec_arbNorm'].Scale(hData['Jpsiycor'].GetSumOfWeights()/hMC['Y_rec'].GetSumOfWeights())
     sbin = hMC[x+'_rec_arbNorm'].GetBinWidth(1)/hData['Jpsiycor'].GetBinWidth(1)
     hMC[x+'_rec_arbNorm'].Scale(1./sbin)
     hMC[x+'_rec_arbNorm'].SetLineColor(cases[x])
     hMC[x+'_rec_arbNorm'].SetTitle('')
     hMC[x+'_rec_arbNorm'].SetStats(0)
    hMC['mc-Jpsiycor_arbNorm'] = hMC['mc-Jpsiycor'].Clone('mc-Jpsiycor_arbNorm')
    hMC['mc-Jpsiycor_arbNorm'].SetLineColor(cases['Y'])
    hMC['mc-Jpsiycor_arbNorm'].SetStats(0)
    hMC['mc-Jpsiycor_arbNorm'].Scale(hData['Jpsiycor'].GetSumOfWeights()/hMC['mc-Jpsiycor_arbNorm'].GetSumOfWeights())
    hData['Jpsiycor'].SetStats(0)
    hMC['Y_rec_arbNorm'].GetYaxis().SetTitle('arbitrary units')
    tc = hMC['dummy'].cd()
    hMC['Y_rec_arbNorm'].Draw()
    hMC['Ysec_rec_arbNorm'].Draw('same')
    hMC['Yprim_rec_arbNorm'].Draw('same')
    hMC['mc-Jpsiycor_arbNorm'].Draw('same')
    hData['Jpsiycor'].Draw('same')
    T.SetTextSize(0.04)
    rc = T.DrawLatexNDC(0.12,0.835,"efficiency corrected events: %5.1F #pm %5.1F"%(Nsignal,Esignal))
    rc = T.DrawLatexNDC(0.12,0.935,"efficiency and acceptance corrected events: %5.1F #pm %5.1F"%(\
                        Nsignal/Acc_Muflux['Y'],Esignal/Acc_Muflux['Y']))
    tc.Update()
    myPrint(tc,'YJpsiData')
    Ilumi = 30.7 # pb-1.  N = sigma * lumi
    Ilumi_error = 0.7 #  
    sigma = Nsignal/Acc_Muflux['Y'] / Ilumi
    E1 = Esignal/Acc_Muflux['Y'] / Ilumi
    E2 = sigma / Ilumi * Ilumi_error
    sigma_error = ROOT.TMath.Sqrt(E1*E1+E2*E2)
    print "sigma = %5.2F +/-%5.2F nb "%(sigma/1000.,sigma_error/1000.)
    print "sigma_prim = %5.2F +/-%5.2F nb "%(sigma/1000.*0.55,sigma_error/1000.*0.55)
def JpsiPrimaryUpdate():
    for x in ['PmotherJpsi','PmotherJpsi_zoom','YJpsiPrimAndSec','YEffJpsiPrimAndSec','YAccJpsiPrimAndSec','YJpsiData','YcorResolution']:
         os.system('cp '+x+'.p* /mnt/hgfs/Images/VMgate/Jpsi/')

def fiducialJpsi(onlyPlot=True):
  hMC['ptHard']  = ROOT.TF1('ptHard','[0]*(1+x/[1])**(-6)')
  y_beam = yBeam()
  variables = {'Ypt':'sqrt(px*px+py*py):0.5*log((E+pz)/(E-pz))-'+str(y_beam),
                 'ppt':'sqrt(px*px+py*py+pz*pz):sqrt(px*px+py*py)'}
  prods = {'10GeV':hMC['Jpsi10GeV'],'1GeV':hMC['Jpsi1GeV'],'P8':hMC['JpsiP8_Primary'],'Cascade':hMC['JpsiCascade']}
  prodsColour = {'10GeV':ROOT.kBlue,'1GeV':ROOT.kCyan,'P8':ROOT.kGreen,'Cascade':ROOT.kMagenta}
  projections = ['P','Pt','Y']
  ut.bookHist(hMC,'pMother',  'p of mother;[GeV/c];[GeV/c]', 1000,0.,401.)
  ut.bookHist(hMC,'pMotherZoom',  'p of mother;[GeV/c];[GeV/c]', 100,399.,401.)
  if not onlyPlot:
    ut.bookHist(hMC,'ppt',  'p vs pt;[GeV/c];[GeV/c]', 100,0.,10., 100,0.,401.)
    ut.bookHist(hMC,'Ypt',  'Y of Jpsi;y_{CMS}', 100,-2.,2., 100,0.,10.)
#
    for p in prods:
      y='pMother'
      hMC[y+'_'+p]=hMC[y].Clone(y+'_'+p)
      y='pMotherZoom'
      hMC[y+'_'+p]=hMC[y].Clone(y+'_'+p)
      for y in ['ppt','Ypt']:
         for x in ['','prim','sec']:
            hMC[y+'_'+x+p]=hMC[y].Clone(y+'_'+x+p)
    for p in prods:
        prods[p].Draw('sqrt(mpx*mpx+mpy*mpy+mpz*mpz)>>pMother_'+p)
        prods[p].Draw('sqrt(mpx*mpx+mpy*mpy+mpz*mpz)>>pMotherZoom_'+p)
        for v in variables: 
           hMC[v+'_'+p].SetStats(0)
           prods[p].Draw(variables[v]+'>>'+v+'_'+p)
           prods[p].Draw(variables[v]+'>>'+v+'_sec'+p,'sqrt(mpx*mpx+mpy*mpy+mpz*mpz)<399.999')
           prods[p].Draw(variables[v]+'>>'+v+'_prim'+p,'sqrt(mpx*mpx+mpy*mpy+mpz*mpz)>399.999')
    hadronAbsorberEffect(Pmin=20.)
    hMC['Yacc_10GeV'] = hMC['Yacc'].Clone('Yacc_10GeV')
    hadronAbsorberEffect(Pmin=10.)
    hMC['Yacc_1GeV'] = hMC['Yacc'].Clone('Yacc_1GeV')
    ut.writeHists(hMC,'Ydistributions.root')
  if onlyPlot: ut.readHists(hMC,'Ydistributions.root')
  tc = hMC['dummy'].cd()
  tc.SetLogy(1)
  hMC['pMother_Cascade'].Draw()
  myPrint(hMC['dummy'],'PmotherJpsi')
  hMC['pMotherZoom_Cascade'].Draw()
  myPrint(hMC['dummy'],'PmotherJpsi_zoom')
  ut.bookCanvas(hMC,'MCprodComp','Jpsi MC productions',1600,900,3,2)
  for p in prods:
       hMC['Pt_'+p]=hMC['ppt_'+p].ProjectionX('Pt_'+p)
       hMC['Pt_'+p].SetTitle(';Pt [GeV/c]')
       hMC['Y_'+p]=hMC['Ypt_'+p].ProjectionX('Y_'+p)
       hMC['Y_'+p].SetTitle(';Y  ')
       hMC['P_'+p]=hMC['ppt_'+p].ProjectionY('P_'+p)
       hMC['P_'+p].SetTitle(';P  [GeV/c]')
  for v in projections:
    for p in prods:
      if p=='10GeV': continue
      scale(hMC[v+'_'+p],hMC[v+'_10GeV'])
  j=1
  for v in projections:
     hMC['l'+v]=ROOT.TLegend(0.59,0.75,0.95,0.87)
     for p in prods:
        hMC[v+'_'+p].SetLineColor(prodsColour[p])
     tc = hMC['MCprodComp'].cd(j)
     j+=1
     p='10GeV'
     hMC[v+'_'+p].SetStats(0)
     if v=='P': hMC[v+'_'+p].SetMaximum(1.1*hMC[v+'_Cascade'].GetMaximum())
     hMC[v+'_'+p].Draw()
     x = hMC['l'+v].AddEntry(hMC[v+'_'+p],p,'PL')
     x.SetTextColor(prodsColour[p])
     for p in prods:
        if p=='10GeV': continue
        hMC[v+'_'+p].SetStats(0)
        hMC[v+'_'+p].Draw('same')
        x = hMC['l'+v].AddEntry(hMC[v+'_'+p],p,'PL')
        x.SetTextColor(prodsColour[p])
     hMC['l'+v].Draw()
  tc = hMC['MCprodComp'].cd(j)
  p='10GeV'
  scale(hMC['Yacc_'+p],hMC['Y_'+p])
  hMC['Y_10GeV'].Draw()
  hMC['Y_P8'].Draw('same')
  hMC['Yacc_10GeV'].Draw('same')
  hMC['l10Y']=ROOT.TLegend(0.59,0.75,0.95,0.87)
  hMC['l10Y'].AddEntry(hMC['Y_P8'],'Pythia8 primary','PL')
  hMC['l10Y'].AddEntry(hMC['Yacc_10GeV'],'Pythia8 E_{#mu}>20GeV','PL')
  hMC['l10Y'].AddEntry(hMC['Y_10GeV'],'Pythia8 from SHiP background simulation','PL')
  hMC['l10Y'].Draw()
  tc = hMC['MCprodComp'].cd(j+1)
  p='1GeV'
  scale(hMC['Yacc_'+p],hMC['Y_'+p])
  hMC['Y_1GeV'].Draw()
  hMC['Y_P8'].Draw('same')
  hMC['Yacc_1GeV'].Draw('same')
  hMC['l1Y']=ROOT.TLegend(0.59,0.75,0.95,0.87)
  hMC['l1Y'].AddEntry(hMC['Y_P8'],'Pythia8 primary','PL')
  hMC['l1Y'].AddEntry(hMC['Yacc_1GeV'],'Pythia8 E_{#mu}>10GeV','PL')
  hMC['l1Y'].AddEntry(hMC['Y_1GeV'],'Pythia8 from SHiP background simulation','PL')
  hMC['l1Y'].Draw()
  myPrint(hMC['MCprodComp'],'JpsiProductionComparison')

def scale(A,B,R=[]):
    if len(R)==0:     A.Scale(B.GetSumOfWeights()/A.GetSumOfWeights())
    else:
     wA = A.Integral(A.FindBin(R[0]),A.FindBin(R[1]))
     wB = B.Integral(B.FindBin(R[0]),B.FindBin(R[1]))
     A.Scale(wB/wA)
    sbin = B.GetBinWidth(1)/A.GetBinWidth(1)
    A.Scale(sbin)

def hadronAbsorberEffect(Pmin=20.):
    Mmu = ROOT.TDatabasePDG.Instance().GetParticle(13).Mass()
    y_beam = yBeam()
    nt = hMC['JpsiP8_Primary']
    ut.bookHist(hMC,'Emu','E of mu',100,0.,100.)
    ut.bookHist(hMC,'Yacc','Y',100,-2.,2.)
    ut.bookHist(hMC,'Y0','Y',100,-2.,2.)
    for event in nt:
       if event.id!=443: continue
       PJpsi = ROOT.TMath.Sqrt(event.px*event.px+event.py*event.py+event.pz*event.pz)
       EJpsi = event.E
       MJpsi = event.M
       gamma = PJpsi/MJpsi
       beta  = PJpsi/EJpsi
       pmu = ROOT.TMath.Sqrt( (MJpsi/2.)**2 - Mmu**2)
       phi = ROOT.gRandom.Rndm()*2.*ROOT.TMath.Pi()
       pmuParallel = abs(pmu * ROOT.TMath.Cos(phi))
       Emu = gamma*MJpsi/2.+beta*gamma*pmuParallel
       rc = hMC['Emu'].Fill(Emu)
       y  = 0.5*ROOT.TMath.Log((EJpsi+event.pz)/(EJpsi-event.pz))-y_beam
       rc = hMC['Y0'].Fill(y)
       if Emu>Pmin:
          rc = hMC['Yacc'].Fill(y)
def rapidityVSpt():
    ut.bookHist(hMC,'ypt','y/pt'    ,100,-2.0,2.0,100,0.0,5.0)
    ybeam = yBeam()
    hMC['JpsiP8_Primary'].Draw('sqrt(px*px+py*py):0.5*log((E+pz)/(E-pz))-'+str(ybeam)+'>>ypt')

def simulateMuonMomentum(plotOnly=False,JpsiOnly=True,save=True,fakeJpsi=True):
    lowMass = {'eta':221,'omega':223,'phi':333,'rho0':113,'eta_prime':331}
    y_beam = yBeam()
    Mmu = ROOT.TDatabasePDG.Instance().GetParticle(13).Mass()
    colors = {}
    if JpsiOnly:
       colors['JpsiCascade']    = [ROOT.kMagenta,23,'']
       colors['JpsiP8_Primary'] = [ROOT.kRed,22,'same']
    else:
       colors['Cascade']    = [ROOT.kMagenta,23,'']
       hMC['fCascade'] = ROOT.TFile("FourDP-101-115.root")
       hMC['Cascade'] = hMC['fCascade'].Get('4DP')
    c = ''
    if not JpsiOnly: c='lowMass-'
    if not JpsiOnly and fakeJpsi: c='lowMassJ-'
    if plotOnly:
     ut.readHists(hMC,c+'muonKinematics-p-pt-minpt.root')
    else:
     for g in colors:
       nt = hMC[g]
       ut.bookHist(hMC,'y/cosCS_'+g   ,'y/cosCS'    ,40,-2.0,2.0,100,-1.0,1.0)
       ut.bookHist(hMC,'ptmin/cosCS_'+g   ,'ptmin/cosCS'    , 100,0.0,5.0,100,-1.0,1.0)
       ut.bookHist(hMC,'cosThetaMax/cosCS_'+g   ,'cosThetaMax/cosCS'    , 100,0.0,0.5,100,-1.0,1.0)
       ut.bookHist(hMC,'cosThetaMax/cosCS_ycut_'+g   ,'cosThetaMax/cosCS'    , 100,0.0,0.5,100,-1.0,1.0)
       ut.bookHist(hMC,'y/cosHE_'+g   ,'y/cosHE'    ,40,-2.0,2.0,100,-1.0,1.0)
       for cosCut in ['','cosCS<0.5_']:
         ut.bookHist(hMC,'y/pt_'+cosCut+g   ,'y/pt'    ,40,-2.0,2.0,100,0.0,5.0)
         ut.bookHist(hMC,'y/ptJ_'+cosCut+g   ,'y/ptJ'    ,40,-2.0,2.0,100,0.0,5.0)
         ut.bookHist(hMC,'y/p_'+cosCut+g    ,'y/p'     ,40,-2.0,2.0,400,0.0,400.0)
         ut.bookHist(hMC,'y/maxp_'+cosCut+g    ,'y/maxp'     ,40,-2.0,2.0,400,0.0,400.0)
         ut.bookHist(hMC,'y/minpt_'+cosCut+g,'y/min pt'      ,40,-2.0,2.0,100,0.0,5.0)
         ut.bookHist(hMC,'y/maxpt_'+cosCut+g,'y/max pt'      ,40,-2.0,2.0,100,0.0,5.0)
         ut.bookHist(hMC,'y/minptJ_'+cosCut+g,'y/min pt'      ,40,-2.0,2.0,100,0.0,5.0)
         ut.bookHist(hMC,'y/maxptJ_'+cosCut+g,'y/max pt'      ,40,-2.0,2.0,100,0.0,5.0)
       PJpsiLab = ROOT.TLorentzVector()
       PMuCMS   =  ROOT.TLorentzVector()
       k=1
       for event in nt:
          k+=1
          #if k>100000: break
          if event.id!=443 and JpsiOnly: continue
          elif not event.id in lowMass.values() and not JpsiOnly: continue
          if JpsiOnly:          PJpsiLab.SetXYZM(event.px,event.py,event.pz,event.M)
          else:                 PJpsiLab.SetXYZT(event.px,event.py,event.pz,event.E)
          PJpsi3V = ROOT.TVector3(event.px,event.py,event.pz)
          boost = PJpsiLab.BoostVector()
          pmu   = ROOT.TMath.Sqrt( (PJpsiLab.M()/2.)**2 - Mmu**2)
          phi   = ROOT.gRandom.Rndm() * 2*ROOT.TMath.Pi()
          theta = ROOT.TMath.ACos(1 - 2*ROOT.gRandom.Rndm())
          plepton = []
          for p in [1.,-1.]:
             px = p*pmu*ROOT.TMath.Cos(phi)*ROOT.TMath.Sin(theta)
             py = p*pmu*ROOT.TMath.Sin(phi)*ROOT.TMath.Sin(theta)
             pz = p*pmu*ROOT.TMath.Cos(theta)
             PMuCMS.SetXYZM(px,py,pz,Mmu)
             PMuCMS.Boost(-boost)
             plepton.append(PMuCMS.Clone())
          if 0.5>ROOT.gRandom.Rndm(): 
             PLepton     = plepton[0]
             PAntilepton = plepton[1]
          else:
             PLepton     = plepton[1]
             PAntilepton = plepton[0]
          P1pl = PLepton.E()+PLepton.Pz()
          P2pl = PAntilepton.E()+PAntilepton.Pz()
          P1mi = PLepton.E()-PLepton.Pz()
          P2mi = PAntilepton.E()-PAntilepton.Pz()
          PJpsi = PLepton+PAntilepton
          cosCS = PJpsi.Pz()/(abs(PJpsi.Pz())+1E-9) * 1./PJpsi.M()/ROOT.TMath.Sqrt(PJpsi.M2()+PJpsi.Pt()**2)*(P1pl*P2mi-P2pl*P1mi)
          PLeptonCMS = PLepton.Clone()
          PLeptonCMS.Boost(boost)
          cosHE = (PLeptonCMS.Px()*PJpsiLab.Px()+PLeptonCMS.Py()*PJpsiLab.Py()+PLeptonCMS.Pz()*PJpsiLab.Pz())/(PLeptonCMS.P()*PJpsiLab.P())
          y = PJpsiLab.Rapidity() - y_beam
          if fakeJpsi:
            E  = ROOT.TMath.Sqrt(PJpsiLab.P()**2+3.0969*3.0969)
            pz = PJpsiLab.Pz()
            y  = 0.5*ROOT.TMath.Log( (E+pz)/(E-pz) ) - y_beam
          hMC['y/cosCS_'+g].Fill(y,cosCS)
          hMC['y/cosHE_'+g].Fill(y,cosHE)
          hMC['cosThetaMax/cosCS_'+g].Fill(max(plepton[0].Pt()/plepton[0].P(),plepton[1].Pt()/plepton[1].P()),cosCS)
          if y > 0.8: hMC['cosThetaMax/cosCS_ycut_'+g].Fill(max(plepton[0].Pt()/plepton[0].P(),plepton[1].Pt()/plepton[1].P()),cosCS)
          cosCut = ''
          minPtJ = 9999.
          maxPtJ = 0.
          for PMuLab in plepton:
             ptLab = PMuLab.Pt()
             tmp = ROOT.TVector3(PMuLab.Px(),PMuLab.Py(),PMuLab.Pz())
             ptJ = PJpsi3V.Cross(tmp).Mag()/tmp.Mag()
             cosCut = ''
             rc = hMC['y/pt_'+cosCut+g].Fill(y,ptLab)
             rc = hMC['y/ptJ_'+cosCut+g].Fill(y,ptJ)
             rc = hMC['y/p_'+cosCut+g].Fill(y,PMuLab.P())
             if abs(cosCS)<0.5: 
                 cosCut = 'cosCS<0.5_'
                 rc = hMC['y/pt_'+cosCut+g].Fill(y,ptLab)
                 rc = hMC['y/ptJ_'+cosCut+g].Fill(y,ptJ)
                 rc = hMC['y/p_'+cosCut+g].Fill(y,PMuLab.P())
             if ptJ<minPtJ : minPtJ = ptJ
             if ptJ>maxPtJ : maxPtJ = ptJ

          cosCut = ''
          rc = hMC['y/minpt_'+cosCut+g].Fill(y,max(plepton[0].Pt(),plepton[1].Pt()))
          rc = hMC['y/minptJ_'+cosCut+g].Fill(y,minPtJ)
          rc = hMC['y/maxpt_'+cosCut+g].Fill(y,min(plepton[0].Pt(),plepton[1].Pt()))
          rc = hMC['y/maxptJ_'+cosCut+g].Fill(y,maxPtJ)
          rc = hMC['y/maxp_'+cosCut+g].Fill(y,min(plepton[0].P(),plepton[1].P()))
          rc = hMC['ptmin/cosCS_'+g].Fill(max(plepton[0].Pt(),plepton[1].Pt()),cosCS)
          if abs(cosCS)<0.5: 
             cosCut = 'cosCS<0.5_'
             rc = hMC['y/minpt_'+cosCut+g].Fill(y,max(plepton[0].Pt(),plepton[1].Pt()))
             rc = hMC['y/minptJ_'+cosCut+g].Fill(y,minPtJ)
             rc = hMC['y/maxpt_'+cosCut+g].Fill(y,min(plepton[0].Pt(),plepton[1].Pt()))
             rc = hMC['y/maxptJ_'+cosCut+g].Fill(y,maxPtJ)
             rc = hMC['y/maxp_'+cosCut+g].Fill(y,min(plepton[0].P(),plepton[1].P()))
     if save: ut.writeHists(hMC,c+'muonKinematics-p-pt-minpt.root')
#
    for x in hMC:
       if type(hMC[x])==type({}): continue
       if type(hMC[x])==type([]): continue
       if hMC[x].ClassName().find('TH')==0: 
          hMC[x].SetStats(0)
    for cosCut in ['','cosCS<0.5_']:
      if not JpsiOnly:     ut.bookCanvas(hMC,c+cosCut+'muonKinematics-p-pt-minpt','muon kinematics',1600,1200,4,3)
      else:     ut.bookCanvas(hMC,c+cosCut+'muonKinematics-p-pt-minpt','muon kinematics',1600,1400,4,4)
      hMC['muonKinematics'] = hMC[c+cosCut+'muonKinematics-p-pt-minpt']
      j=1
      for g in colors:
        gc = cosCut+g
        hMC['muonKinematics'].cd(j)
        hMC['y/p_'+gc].SetTitle(';y_{cm};P [GeV/c]')
        hMC['y/p_'+gc].Draw('colz')
        hMC['muonKinematics'].cd(j+1)
        hMC['y/pt_'+gc].SetTitle(';y_{cm};P_{T} [GeV/c]')
        hMC['y/pt_'+gc].Draw('colz')
        hMC['muonKinematics'].cd(j+2)
        hMC['y/minpt_'+gc].Draw('colz')
        hMC['y/minpt_'+gc].SetTitle(';y_{cm};max P_{T} [GeV/c]')
        hMC['muonKinematics'].cd(j+3)
        hMC['y/maxp_'+gc].SetTitle(';y_{cm};min P [GeV/c]')
        hMC['y/maxp_'+gc].Draw('colz')
        j+=4
        hMC['y/p_'+gc].SetLineColor(colors[g][0])
        hMC['y/p_'+gc].SetMarkerColor(colors[g][0])
        hMC['y/p_'+gc].SetMarkerStyle(colors[g][1])
        hMC['y/pt_'+gc].SetLineColor(colors[g][0])
        hMC['y/pt_'+gc].SetMarkerColor(colors[g][0])
        hMC['y/pt_'+gc].SetMarkerStyle(colors[g][1])
      maximas = {'p_':[],'pt_':[],'minpt_':[],'maxp_':[],'I-vis_maxp_':[],'I-vis_minpt_':[],'I-vis_maxpt_':[]}
      first = True
      for g in colors:
        gc = cosCut+g
        if first: drawOption = ''
        else: drawOption = 'same'
        tc = hMC['muonKinematics'].cd(j)
        tc.SetLogy(1)
        hMC['p_'+gc] = hMC['y/p_'+gc].ProjectionY('p_'+gc)
        hMC['p_'+gc].Rebin(10)
        hMC['p_'+gc].SetStats(0)
        hMC['p_'+gc].Scale(1./hMC['p_'+gc].GetSumOfWeights())
        maximas['p_'].append(hMC['p_'+gc].GetMaximum()*1.5)
        hMC['p_'+gc].Draw(drawOption+colors[g][2])
        hMC['muonKinematics'].cd(j+1)
        hMC['pt_'+gc] = hMC['y/pt_'+gc].ProjectionY('pt_'+gc)
        hMC['pt_'+gc].SetStats(0)
        hMC['pt_'+gc].Scale(1./hMC['pt_'+gc].GetSumOfWeights())
        maximas['pt_'].append(hMC['pt_'+gc].GetMaximum())
        hMC['pt_'+gc].Draw(drawOption+colors[g][2])
        hMC['muonKinematics'].cd(j+2)
        hMC['minpt_'+gc]=hMC['y/minpt_'+gc].ProjectionY('minpt_'+gc)
        hMC['minpt_'+gc].SetStats(0)
        hMC['minpt_'+gc].SetLineColor(colors[g][0])
        hMC['minpt_'+gc].SetMarkerColor(colors[g][0])
        hMC['minpt_'+gc].SetMarkerStyle(colors[g][1])
        hMC['minpt_'+gc].Scale(1./hMC['minpt_'+gc].GetSumOfWeights())
        maximas['minpt_'].append(hMC['minpt_'+gc].GetMaximum())
        hMC['minpt_'+gc].Draw(drawOption+colors[g][2])
        tc = hMC['muonKinematics'].cd(j+3)
        tc.SetLogy(1)
        hMC['maxp_'+gc]=hMC['y/maxp_'+gc].ProjectionY('maxp_'+gc)
        hMC['maxp_'+gc].Rebin(10)
        hMC['maxp_'+gc].SetStats(0)
        hMC['maxp_'+gc].SetLineColor(colors[g][0])
        hMC['maxp_'+gc].SetMarkerColor(colors[g][0])
        hMC['maxp_'+gc].SetMarkerStyle(colors[g][1])
        hMC['maxp_'+gc].Scale(1./hMC['maxp_'+gc].GetSumOfWeights())
        maximas['maxp_'].append(hMC['maxp_'+gc].GetMaximum()*1.5)
        hMC['maxp_'+gc].Draw(drawOption+colors[g][2])
        Y = hMC['y/maxp_'+gc].ProjectionX()
        ymin,ymax = Y.FindBin(0.4),Y.FindBin(1.8)
        hMC['vis_maxp_'+gc] = hMC['y/maxp_'+gc].ProjectionY('vis_maxp_'+g,ymin,ymax)
        hMC['vis_maxp_'+gc].SetStats(0)
        ut.makeIntegralDistrib(hMC,'vis_maxp_'+gc,overFlow=True)
        hMC['I-vis_maxp_'+gc].Scale(1./hMC['vis_maxp_'+gc].GetEntries())
        hMC['I-vis_maxp_'+gc].GetXaxis().SetRangeUser(0.,100.)
        hMC['vis_minpt_'+gc] = hMC['y/minpt_'+gc].ProjectionY('vis_minpt_'+g,ymin,ymax)
        hMC['vis_minpt_'+gc].SetStats(0)
        ut.makeIntegralDistrib(hMC,'vis_minpt_'+gc,overFlow=True)
        hMC['I-vis_minpt_'+gc].Scale(1./hMC['vis_minpt_'+gc].GetEntries())
        hMC['vis_maxpt_'+gc] = hMC['y/maxpt_'+gc].ProjectionY('vis_maxpt_'+g,ymin,ymax)
        hMC['vis_maxpt_'+gc].SetStats(0)
        ut.makeIntegralDistrib(hMC,'vis_maxpt_'+gc,overFlow=True)
        hMC['I-vis_maxpt_'+gc].Scale(1./hMC['vis_maxpt_'+gc].GetEntries())
        hMC['I-vis_minpt_'+gc].GetXaxis().SetRangeUser(0.,2.)
        hMC['I-vis_maxpt_'+gc].GetXaxis().SetRangeUser(0.,2.)
        hMC['I-vis_maxp_'+gc].SetLineColor(colors[g][0])
        hMC['I-vis_maxp_'+gc].SetMarkerColor(colors[g][0])
        hMC['I-vis_maxp_'+gc].SetMarkerStyle(colors[g][1])
        hMC['I-vis_minpt_'+gc].SetLineColor(colors[g][0])
        hMC['I-vis_minpt_'+gc].SetMarkerColor(colors[g][0])
        hMC['I-vis_minpt_'+gc].SetMarkerStyle(colors[g][1])
        hMC['I-vis_maxpt_'+gc].SetLineColor(colors[g][0])
        hMC['I-vis_maxpt_'+gc].SetMarkerColor(colors[g][0])
        hMC['I-vis_maxpt_'+gc].SetMarkerStyle(colors[g][1])
        tc = hMC['muonKinematics'].cd(j+4)
        maximas['I-vis_minpt_'].append(hMC['I-vis_minpt_'+gc].GetMaximum())
        hMC['I-vis_minpt_'+gc].Draw(drawOption+colors[g][2])
        tc = hMC['muonKinematics'].cd(j+5)
        maximas['I-vis_maxp_'].append(hMC['I-vis_maxp_'+gc].GetMaximum())
        hMC['I-vis_maxp_'+gc].Draw(drawOption+colors[g][2])
        tc = hMC['muonKinematics'].cd(j+6)
        maximas['I-vis_maxpt_'].append(hMC['I-vis_maxpt_'+gc].GetMaximum())
        hMC['I-vis_maxpt_'+gc].Draw(drawOption+colors[g][2])
      for x in maximas: 
          maximas[x].sort(reverse=True)
          for g in colors:
             gc = cosCut+g
             hMC[x+gc].SetMaximum(maximas[x][0]*1.1)
      for x in hMC['muonKinematics'].GetListOfPrimitives(): x.Update()
      myPrint(hMC['muonKinematics'],c+cosCut+'muonKinematics')
    ut.bookCanvas(hMC,'dummy',' ',900,600,1,1)
    tc = hMC['dummy'].cd()
    for g in colors:
        hMC['ptmin/cosCS_'+g].SetTitle(';min P_{T} [GeV/c];cos #Theta_{CS}')
        hMC['ptmin/cosCS_'+g].Draw('colz')
        myPrint(hMC['dummy'],g+'muonKinematicsCosCSandPtmin')
# is the following needed? 20/3/2020
    for g in colors:
      hist = 'cosThetaMax/cosCS_ycut_'
      if hMC.has_key(hist+g):
        hMC[hist+g].SetTitle(';max(sin #Theta_{#mu});cos #Theta_{CS}')
        hMC[hist+g].Draw('colz')
        myPrint(hMC['dummy'],g+'muonKinematicsCosCSandTheta')
        test = hMC[hist+g].ProjectionX()
        hMC['cosCSProj'+g] = hMC[hist+g].ProjectionY('cosCSProj'+g)
        hMC['cosCSInAcceptance'+g] = hMC[hist+g].ProjectionY('cosCSInAcceptance'+g,1,test.FindBin(0.054))
        hMC['cosCSInAcceptance'+g].SetLineColor(colors[g][0])
        hMC['cosCSInAcceptance'+g].SetMarkerColor(colors[g][0])
        hMC['cosCSInAcceptance'+g].SetMarkerStyle(colors[g][1])
        hMC['cosCSProj'+g].SetLineColor(colors[g][0])
        hMC['cosCSProj'+g].SetMarkerColor(colors[g][0])
        hMC['cosCSProj'+g].SetMarkerStyle(colors[g][1])
    gs = colors.keys()
    if hMC.has_key(hist+gs[0]):
      for g in colors:
         weight = hMC['cosCSProj'+g].GetSumOfWeights()
         hMC['cosCSProj'+g].Scale(1./weight)
         hMC['cosCSInAcceptance'+g].Scale(1./weight)
         hMC['cosCSProj'+g].SetStats(0)
         hMC['cosCSInAcceptance'+g].SetStats(0)
      hist = 'cosCSProj'+gs[0]
      hMC[hist].GetYaxis().SetTitle('arbitrary units')
      hMC[hist].SetMinimum(0)
      hMC[hist].Draw('p')
      hMC[hist].Draw('histsame')
      for n in range(0,len(colors)):
         for hist in ['cosCSInAcceptance'+gs[n],'cosCSProj'+gs[n]]:
           hMC[hist].Draw('histsame')
           hMC[hist].Draw('psame')
      myPrint(hMC['dummy'],'muonKinematicsCosCSInAcceptance')

def JpsiPtinBinsOfY(ntName='Jpsi'):
    y_beam = yBeam()
    ut.bookHist(hMC, 'm_MC','inv mass;M [GeV/c^{2}]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
    sptCut = '1.4'
    theCut =  '('+sptCut+'<pt1||'+sptCut+'<pt2)&&chi21*chi22<0&&abs(chi21)<0.9&&abs(chi22)<0.9&&p1<300&&p2<300&&p1>20&&p2>20&&mcor>0.20'
    theCut = theCut.replace('pt1','pt1cor')
    theCut = theCut.replace('pt2','pt2cor')
    ut.bookCanvas(hMC,'ptVSy','Jpsi pt distribution for different y ranges',1600,1200,2,2)
    ROOT.gROOT.cd()
#
    yranges = ['0.4-0.7','0.7-1.0','1.0-1.3','1.3-1.6']
    for y in yranges:
      ycuts = y.split('-')
      theCuty = theCut+"&&ycor<"+ycuts[1]+'+'+str(y_beam)+"&&ycor>"+ycuts[0]+"+"+str(y_beam)
      makeProjection('ptcor',0.,5.,'ptcor',    theCuty,nBins=16,ntName=ntName,printout=0,fixSignal=False,secondGaussian=False)
      hData['Jpsiptcor-y'+y]=hData['Jpsiptcor'].Clone('Jpsiptcor-y'+y)
      hMC['mc-Jpsiptcor-y'+y]=hMC['mc-Jpsiptcor'].Clone('mc-Jpsiptcor-y'+y)
      hMC['MCbinsptcor-y'+y]=hMC['MCbinsptcor'].Clone('MCbinsptcor-y'+y)
      hData['binsptcor-y'+y]=hData['binsptcor'].Clone('binsptcor-y'+y)
    j=1
    for y in yranges:
        hMC['ptVSy'].cd(j)
        j+=1
        hData['Jpsiptcor-y'+y].SetLineColor(ROOT.kBlue)
        hData['Jpsiptcor-y'+y].SetMinimum(0.)
        hData['Jpsiptcor-y'+y].SetLineWidth(2)
        hData['Jpsiptcor-y'+y].SetMaximum(1600)
        hData['Jpsiptcor-y'+y].Draw()
        hMC['mc-Jpsiptcor-y'+y].SetLineColor(ROOT.kMagenta)
        scale(hMC['mc-Jpsiptcor-y'+y],hData['Jpsiptcor-y'+y])
        hMC['mc-Jpsiptcor-y'+y].Draw('same')
    myPrint(hMC['ptVSy'],ntName+'-pt-distribution4different-y-ranges')

def compareJpsiProds():
    y_beam = yBeam()
    sptCut = '1.4'
    theCut =  '('+sptCut+'<pt1||'+sptCut+'<pt2)&&chi21*chi22<0&&abs(chi21)<0.9&&abs(chi22)<0.9&&p1<300&&p2<300&&p1>20&&p2>20&&mcor>0.20'
    theCut = theCut.replace('pt1','pt1cor')
    theCut = theCut.replace('pt2','pt2cor')
    cases = {'JpsiP8':'Jpsi==443&&mcor>2.0&&mcor<4.&&'+theCut,'Jpsi':'Jpsi==443&&mcor>2.0&&mcor<4.&&'+theCut}
    ut.bookCanvas(hMC,'MCprodComp','Jpsi MC productions',1600,1200,2,2)
#
    ROOT.gROOT.cd()
    makeProjection('ptcor',0.,5.,'ptcor',    theCut,nBins=20,ntName='Jpsi',printout=0)
    makeProjection('pcor',0.,400.,'pcor',    theCut,nBins=20,ntName='Jpsi',printout=0)
    makeProjection('ycor',0.,2.,'ycor',      theCut,nBins=20,ntName='Jpsi',printout=0)
#
    variables = {'ycor':'ycor-'+str(y_beam),'pcor':'pcor', 'ptcor':'ptcor'}
    for nt in cases:
        ut.bookHist(hMC,'ycor_'+nt,'ycor_'+nt+';y',100,0.,2.)
        ut.bookHist(hMC,'pcor_'+nt,'pcor_'+nt+';[GeV/c]',100,0.,400.)
        ut.bookHist(hMC,'ptcor_'+nt,'ptcor_'+nt+';[GeV/c]',100,0.,10.)
        for var in variables:
            hMC[var+'_'+nt].SetStats(0)
            hMC[nt].Draw(variables[var]+'>>'+var+'_'+nt,cases[nt])
    hMC['ptcor_Jpsi'].GetXaxis().SetRangeUser(0.,6.)
    k=1
    for nt in cases:
        for var in variables:
            hMC[var+'_'+nt+'_scaled']=hMC[var+'_'+nt].Clone(var+'_'+nt+'_scaled')
    for var in variables:
        tc = hMC['MCprodComp'].cd(k)
        k+=1
        hMC['l'+var]=ROOT.TLegend(0.59,0.75,0.95,0.87)
        hData['Jpsi'+var].SetLineColor(ROOT.kRed)
        norm = hData['Jpsi'+var].GetSumOfWeights()
        sbin = hData['Jpsi'+var].GetBinWidth(1)/hMC[var+'_JpsiP8'+'_scaled'].GetBinWidth(1)
        hMC[var+'_JpsiP8'+'_scaled'].Scale(norm/hMC[var+'_JpsiP8'].GetEntries())
        hMC[var+'_JpsiP8'+'_scaled'].Scale(sbin)
        hMC[var+'_JpsiP8'+'_scaled'].SetLineColor(ROOT.kMagenta)
        hMC[var+'_JpsiP8'+'_scaled'].SetTitle(var)
        hMC[var+'_Jpsi'+'_scaled'].Scale(norm/hMC[var+'_Jpsi'].GetEntries())
        hMC[var+'_Jpsi'+'_scaled'].Scale(sbin)
        hMC[var+'_Jpsi'+'_scaled'].SetMinimum(0)
        hMC[var+'_Jpsi'+'_scaled'].SetMaximum(1.1*max( hMC[var+'_Jpsi'+'_scaled'].GetMaximum(),
                          hMC[var+'_JpsiP8'+'_scaled'].GetMaximum(),hData['Jpsi'+var].GetMaximum()))
        hMC[var+'_Jpsi'+'_scaled'].Draw()
        hData['Jpsi'+var].SetLineWidth(2)
        hData['Jpsi'+var].SetStats(0)
        hData['Jpsi'+var].Draw('same')
        hMC[var+'_JpsiP8'+'_scaled'].Draw('same')
        hMC['l'+var].AddEntry(hData['Jpsi'+var],'Data','PL')
        hMC['l'+var].AddEntry(hMC[var+'_JpsiP8'+'_scaled'],'Pythia8  only primary','PL')
        hMC['l'+var].AddEntry(hMC[var+'_Jpsi'+'_scaled'],'Pythia6 cascade','PL')
        hMC['l'+var].Draw()
    myPrint(hMC['MCprodComp'],'JpsiProdComparison')
def trueCosCS1():
# problem, only has info for reconstructed muons
    ut.bookHist(hMC,'trueCosCSvsReco','true Cos CStheta',100,-1.,1.,100,-1.,1.)
    ut.bookHist(hMC,'diffCosCScor','true Cos CStheta - reco',100,-1.,1.)
    ut.bookHist(hMC,'diffCosCS','true Cos CStheta - reco',100,-1.,1.)
    nt = hMC['JpsiP8']
    ptCut = 1.0
    pmin = 20.0
    pmax = 300.
    for n in range(nt.GetEntries()):
          rc=nt.GetEvent(n)
          if nt.Jpsi!=443: continue
          if max(nt.pt1cor,nt.pt2cor)<ptCut: continue
          if min(nt.p1,nt.p2)<pmin: continue
          if max(nt.p1,nt.p2)>pmax: continue
          if nt.mcor<0.2: continue
          if nt.p1x==nt.p2x: continue
          if nt.chi21 < 0: 
            PLepton     = ROOT.Math.PxPyPzMVector(nt.p1x,nt.p1y,nt.p1z,muonMass)
            PAntilepton = ROOT.Math.PxPyPzMVector(nt.p2x,nt.p2y,nt.p2z,muonMass)
          else: 
            PLepton     = ROOT.Math.PxPyPzMVector(nt.p2x,nt.p2y,nt.p2z,muonMass)
            PAntilepton = ROOT.Math.PxPyPzMVector(nt.p1x,nt.p1y,nt.p1z,muonMass)
          P1pl = PLepton.E()+PLepton.Pz()
          P2pl = PAntilepton.E()+PAntilepton.Pz()
          P1mi = PLepton.E()-PLepton.Pz()
          P2mi = PAntilepton.E()-PAntilepton.Pz()
          PJpsi = PLepton+PAntilepton
          cosCSraw = PJpsi.z()/abs(PJpsi.z()) * 1./PJpsi.M()/ROOT.TMath.Sqrt(PJpsi.M2()+PJpsi.Pt()**2)*(P1pl*P2mi-P2pl*P1mi)
          if cosCSraw==0:
              print  PJpsi.z(),PJpsi.M(),PJpsi.Pt(),P1pl,P2mi,P2pl,P1mi
          rc = hMC['trueCosCSvsReco'].Fill(nt.cosCScor,cosCSraw)
          rc = hMC['diffCosCScor'].Fill(cosCSraw - nt.cosCScor)
          rc = hMC['diffCosCS'].Fill(cosCSraw - nt.cosCSraw)
    tc = hMC['dummy'].cd()
    hMC['diffCosCS'].SetTitle('; cos #Theta; arbitrary unit')
    hMC['diffCosCScor'].SetTitle('; cos #Theta; arbitrary unit')
    hMC['diffCosCS'].Fit('gaus')
    tc.Update()
    stats = tc.GetPrimitive('stats')
    stats.SetOptFit(10111)
    stats.SetFitFormat('5.4g')
    stats.SetX1NDC(0.64)
    stats.SetY1NDC(0.61)
    stats.SetX2NDC(0.98)
    stats.SetY2NDC(0.91)    
    hMC['diffCosCScor'].Fit('gaus')
    tc.Update()
    stats = tc.GetPrimitive('stats')
    stats.SetOptFit(10111)
    stats.SetFitFormat('5.4g')
    stats.SetX1NDC(0.64)
    stats.SetY1NDC(0.23)
    stats.SetX2NDC(0.98)
    stats.SetY2NDC(0.53)
    hMC['diffCosCS'].Draw('same')
    tc.Update()
    myPrint(hMC['dummy'],'cosCScorResolution')

    hMC['mean'] = hMC['trueCosCSvsReco'].ProjectionY('mean')
    hMC['mean'].Reset()
    hMC['RMS']  = hMC['trueCosCSvsReco'].ProjectionY('RMS')
    hMC['RMS'].Reset()
    for n in range(1,hMC['trueCosCSvsReco'].GetNbinsX()+1):
       hMC['CosCS_mig'+str(n)] = hMC['trueCosCSvsReco'].ProjectionY('CosCS_mig'+str(n),n,n) # true distribution for given reco
       rc = hMC['CosCS_mig'+str(n)].Fit('gaus','SQ')
       fitResult = rc.Get()
       hMC['mean'].SetBinContent(n,fitResult.Parameter(1))
       hMC['RMS'].SetBinContent(n,fitResult.Parameter(2))
# efficiency as function of true cosCS, arbitrary units, assuming original distribution was flat.
    hMC['CosCS_eff']=hMC['trueCosCSvsReco'].ProjectionY('CosCS_eff')
    hMC['CosCS_rec']=hMC['trueCosCSvsReco'].ProjectionX('CosCS_rec')
# first, determine migration, from reco to true, then correct as function of true
    f = ROOT.TFile("JpsiKinematicsRec_cosCScorB-1.0_20.0.root")
    hData['B_cosCScor-Jpsi'] = f.xxx.FindObject('B_cosCScor-Jpsi').Clone('B_cosCScor-Jpsi')
    c = 'Data'
    c = 'JpsiP8'
    if c=='JpsiP8': hjpsi = hMC['CosCS_rec'] # should be later the data distribution
    else:         hjpsi = hData['B_cosCScor-Jpsi']
    yranges=[-0.8,0.8]
    ymin   = yranges[0]
    NyieldEffCorrected = {}
    for k in range(1,hjpsi.GetNbinsX()+1):
      NyieldEffCorrected[k]=[0,0]
# for a given cosCScor, find distribution of cosCStrue
    bw    = hjpsi.GetBinWidth(1)
    while ymin < yranges[1]:
      i = hMC['CosCS_rec'].FindBin(ymin)
      j = hMC['CosCS_rec'].FindBin(ymin+bw)
      xslice = hMC['trueCosCSvsReco'].ProjectionY('CosCS_mig'+str(i),i,j)
      norm   = xslice.GetSumOfWeights()
      n      = hjpsi.FindBin(ymin)
      Nrec = hjpsi.GetBinContent(n)
      Erec = hjpsi.GetBinError(n)
      xslice.Scale(Nrec/norm)
      for k in range(1,xslice.GetNbinsX()+1):
          x = xslice.GetBinCenter(k)
          e = hMC['CosCS_eff'].GetBinContent(k)+1E-10
          NyieldEffCorrected[n][0]+=xslice.GetBinContent(k)/e
          NyieldEffCorrected[n][1]+=(xslice.GetBinContent(k)/e * Erec/(Nrec+1E-9))
      ymin+=bw
    hMC['CosCS_effCor'] = hjpsi.Clone('CosCS_effCor')
    hMC['CosCS_effCor'].Reset()
    hname = 'CosCS_effCor'
    for k in range(1,hjpsi.GetNbinsX()+1):
      if NyieldEffCorrected[k][0]<1E10:
         hMC[hname].SetBinContent(k,NyieldEffCorrected[k][0])
         hMC[hname].SetBinError(k,NyieldEffCorrected[k][1])
      else:   
         hMC[hname].SetBinContent(k,0.)
         hMC[hname].SetBinError(k,0.)

def trueCosCS2():
# try to mimick distribution using jpsi directly
    ut.bookHist(hMC,'trueCosCS','true Cos CStheta',100,-1.,1.)
    ut.bookHist(hMC,'JpsiPtvsY','pt vs y Jpsi',100,-2.,2.,100,0.,5.)
    ut.bookHist(hMC,'JpsiIPtvsY','pt vs y Jpsi intermediate',100,-2.,2.,100,0.,5.)
    y_beam = yBeam()
    for nt in hMC['JpsiP8_PrimaryMu']:
       PJpsi = ROOT.Math.PxPyPzMVector(nt.px,nt.py,nt.pz,nt.M)
       if nt.p1x==nt.p2x and nt.p1y==nt.p2y and nt.p1z==nt.p2z:
          rc = hMC['JpsiIPtvsY'].Fill(PJpsi.Rapidity()-y_beam,PJpsi.Pt())
          continue
       rc = hMC['JpsiPtvsY'].Fill(PJpsi.Rapidity()-y_beam,PJpsi.Pt())
       PLepton     = ROOT.Math.PxPyPzMVector(nt.p1x,nt.p1y,nt.p1z,muonMass)
       PAntilepton = ROOT.Math.PxPyPzMVector(nt.p2x,nt.p2y,nt.p2z,muonMass)
       P1pl = PLepton.E()+PLepton.Pz()
       P2pl = PAntilepton.E()+PAntilepton.Pz()
       P1mi = PLepton.E()-PLepton.Pz()
       P2mi = PAntilepton.E()-PAntilepton.Pz()
       cosCSraw = PJpsi.z()/abs(PJpsi.z()) * 1./PJpsi.M()/ROOT.TMath.Sqrt(PJpsi.M2()+PJpsi.Pt()**2)*(P1pl*P2mi-P2pl*P1mi)
       rc = hMC['trueCosCS'].Fill(cosCSraw)

def plots4AnalysisNote(fm='B'):
 if not hMC.has_key('meanLossTrue'):
    ut.readHists(hMC,fm+'-diMuonAnalysis-MC.root')
    ut.readHists(hData,fm+'-diMuonAnalysis-Data.root')
 tc = hMC['dummy'].cd()
 hMC['meanLossTrue'].SetStats(0)
 hMC['meanLossTrue'].SetTitle(' ; true momentum [GeV/c]; mean energy loss [GeV/c]')
 hMC['meanLossTrue'].GetXaxis().SetRangeUser(10.,300.)
 hMC['meanLossTrue'].Fit('pol2','S','',20.,300.)
 hMC['meanLossTrue'].Draw()
 myPrint(tc,'meanLossTrue')
 #
 tc.SetLogy(1)
 for ptcut in ["0.0","1.0"]:
  hMC['mc-mcor_Jpsi_'+ptcut].SetStats(0)
  hMC['SS-mc-mcor_'+ptcut].SetStats(0)
  hMC['mc-mcor_'+ptcut].Draw()
  hMC['mc-mcor_Jpsi_'+ptcut].Draw('same')
  hMC['SS-mc-mcor_'+ptcut].Draw('same')
  myCB = hMC['mc-mcor_'+ptcut].GetFunction("mc-Fun"+fm+"_ycor10GeV0")
  stats = hMC['mc-mcor_'+ptcut].FindObject('stats')
  stats.SetX1NDC(0.63)
  stats.SetY1NDC(0.59)
  stats.SetX2NDC(0.99)
  stats.SetY2NDC(0.96)
  params,funTemplate = getFitDictionary(fm)
  sfun = ROOT.TF1('tmp',funTemplate['F'],0,10,funTemplate['N'])
  for n in range(myCB.GetNpar()):
     sfun.SetParameter(n,myCB.GetParameter(n))
     sfun.SetParError(n,myCB.GetParError(n))
  if fm=='CB': tmp = norm_twoCB(sfun)
  if fm=='B':  tmp = norm_twoBukin(sfun)
  T = ROOT.TLatex()
  txtLow = "N_{Low mass}: %6.1F #pm %6.1F "%(tmp[0][0],tmp[0][1])
  txtSig  = "N_{J/#Psi}     : %6.1F #pm %6.1F "%(tmp[1][0],tmp[1][1])
  T.DrawLatex(5.5,10.,txtLow)
  T.DrawLatex(5.5,20.,txtSig)

  hMC['legmc-mcor_'+ptcut]=ROOT.TLegend(0.63,0.20,0.99,0.32)
  l1 = hMC['legmc-mcor_'+ptcut].AddEntry(hMC['mc-mcor_'+ptcut],'opposite sign muons','PL')
  l1.SetTextColor(hMC['mc-mcor_'+ptcut].GetLineColor())
  l2 = hMC['legmc-mcor_'+ptcut].AddEntry(hMC['SS-mc-mcor_'+ptcut],'same sign muons','PL')
  l2.SetTextColor(hMC['SS-mc-mcor_'+ptcut].GetLineColor())
  l3 = hMC['legmc-mcor_'+ptcut].AddEntry(hMC['mc-mcor_Jpsi_'+ptcut],'from J/#psi','PL')
  l3.SetTextColor(hMC['mc-mcor_Jpsi_'+ptcut].GetLineColor())
  hMC['legmc-mcor_'+ptcut].Draw()
  tc.Update()
  myPrint(tc,fm+'-dimuon-MC-'+ptcut+'GeVptlog')
#
def plotDrellYanAndLowMass():
  ut.bookCanvas(hMC,'DYcanvas','mass in bins ycor1C',1800,1200,4,5)
  for i in range(20):
     hMC['DYcanvas'].cd(i+1)
     hMC['mc-B_ycor1CLowMass-10GeV'+str(i)].Draw()
     hMC['sDYmc-B_ycor1C10GeV'+str(i)] = hMC['DYmc-B_ycor1C10GeV'+str(i)].Clone('sDYmc-B_ycor1C10GeV'+str(i))
     hMC['sDYmc-B_ycor1C10GeV'+str(i)].Scale(DYfactor)
     hMC['sDYmc-B_ycor1C10GeV'+str(i)].SetLineColor(ROOT.kOrange)
     fun=hMC['sDYmc-B_ycor1C10GeV'+str(i)].GetFunction('DY')
     if fun: fun.SetBit(ROOT.TF1.kNotDraw)
     hMC['sDYmc-B_ycor1C10GeV'+str(i)].Draw('same')
def mergeMassandPullPlots(fitMethod='B',ptCut=1.0,pmin=20.,BDTCut=None,muID=2,withWeight=True):
    tag = 'muID'+str(muID)+'_'+fitMethod+'-'+str(ptCut)+'_'+str(pmin)
    if BDTCut: tag += '_BDT'
    if withWeight: tag += '_wp6'
    print tag
    os.chdir(topDir)
    os.chdir(tag)
    f = ROOT.TFile('pullPlot_binsB_ycor1C.root')
    ROOT.gROOT.cd()
    pulls = f.Get('res_bins'+fitMethod+'_ycor1C').Clone()
    f = ROOT.TFile('Data-diMuonBins_'+fitMethod+'_ycor1C.root')
    ROOT.gROOT.cd()
    mass = f.Get('binsB_ycor1C').Clone()
    cpad = {}
    c0 = ROOT.TCanvas("c0","c0",900,600)
    aspect = 0.3
    pad1 = ROOT.TPad("pad1", "The pad 80% of the height",0.0,aspect,1.0,1.0,0)
    pad1.SetBottomMargin(0.001)
    pad1.SetLogy(1)
    pad2 = ROOT.TPad("pad2", "The pad 20% of the height",0.0,0.0,1.0,aspect,0)
    pad2.SetTopMargin(0.001)
    pad2.SetBottomMargin(0.19)
    pad2.SetLogy(0)
    pad1.Draw()
    pad2.Draw()
    for n in range(len(mass.GetListOfPrimitives())):
        pad1.cd()
        pad = mass.GetListOfPrimitives()[n]
        cpad[n]={}
        for p in pad.GetListOfPrimitives():
            cpad[n][p.GetName()]=p.Clone()
        if not cpad[n].has_key(fitMethod+'_ycor1C'+str(n)):continue
        cpad[n][fitMethod+'_ycor1C'+str(n)].GetYaxis().SetTitle("N events")
        cpad[n][fitMethod+'_ycor1C'+str(n)].GetXaxis().SetRangeUser(0.3,8.0)
        txt = cpad[n][fitMethod+'_ycor1C'+str(n)].GetTitle().split('DATA')[1]
        txt = txt.replace('ycor1C','y_{cm}')
        cpad[n][fitMethod+'_ycor1C'+str(n)].SetTitle(txt)
        cpad[n][fitMethod+'_ycor1C'+str(n)].Draw()
        cpad[n]['Fun'+fitMethod+'_ycor1C'+str(n)+'highMass'].Draw('same')
        cpad[n]['Fun'+fitMethod+'_ycor1C'+str(n)+'lowMass'].Draw('same')
        cpad[n]['Fun'+fitMethod+'_ycor1C'+str(n)+'back'].Draw('same')
        cpad[n][fitMethod+'_ycor1C'+str(n)].Draw('same')
        pad2.cd()
        pad = pulls.GetListOfPrimitives()[n]
        for p in pad.GetListOfPrimitives():
            cpad[n][p.GetName()]=p.Clone()
        cpad[n]['res_'+fitMethod+'_ycor1C'+str(n)].SetTitle('')
        cpad[n]['res_'+fitMethod+'_ycor1C'+str(n)].SetMaximum(4.9)
        cpad[n]['res_'+fitMethod+'_ycor1C'+str(n)].SetMinimum(-4.9)
        cpad[n]['res_'+fitMethod+'_ycor1C'+str(n)].GetXaxis().SetRangeUser(0.3,8.0)
        yax = cpad[n]['res_'+fitMethod+'_ycor1C'+str(n)].GetYaxis()
        M = yax.GetLabelSize()*(1-aspect)/aspect
        yax.SetLabelSize(M)
        yax.SetTitle('(N-N_{fit}) / #sqrt{N}') # SetTitle('#frac{N-N_{fit}}{#sqrt{N}}')
        yax.SetTitleSize(M)
        yax.SetTitleOffset(0.3)
        xax = cpad[n]['res_'+fitMethod+'_ycor1C'+str(n)].GetXaxis()
        M = xax.GetLabelSize()*(1-aspect)/aspect
        xax.SetLabelSize(M)
        M = xax.GetTitleSize()*(1-aspect)/aspect
        xax.SetTitleSize(M)
        cpad[n]['res_'+fitMethod+'_ycor1C'+str(n)].Draw('P')
        myPrint(c0,tag+'_MassAndPullPlot_bins'+fitMethod+'_ycor1C_'+str(n))
    myCopy(tag+"_MassAndPullPlot_bins"+fitMethod+"_ycor1C_*.pdf")

def plots4AnalysisNotePsi2S(ptCut=1.0):
    # ut.readHists(hData,'muID2_B-1.0_20.0_wp6/Data-histos.root')
    fitOption = 'SL'
    minX = 0.5
    maxX = 8.0
    hData['mcor_1.0'].Draw()
    funB2S = ROOT.TF1('B2S',my2BukinPdf,0,10,17)
    init_twoBukin(funB2S,hData['mcor_1.0'].GetBinWidth(1))
    for n in range(funB1S.GetNpar()):
      funB2S.SetParameter(n,hData['FunB_1.0'].GetParameter(n))
    funB2S.ReleaseParameter(16)
    funB2S.SetParameter(16,0.)
    rc = myFit(hData['mcor_1.0'],funB2S,fitOption,minX,maxX)

def plots4Paper(ptmax=1.0,pmin=20.0,fM='B',mu='muID2'):
   D = mu+'_'+fM+'-'+str(ptmax)+'_'+str(pmin)
   sample = "Data"
   tmp = ROOT.TFile(D+'/'+sample+'-diMuonBins_'+fM+'_ycor1C.root')
   X = tmp.Get('bins'+fM+'_ycor1C').Clone('bins'+fM+'_ycor1C')
   k=1
   for p in X.GetListOfPrimitives():
       if k==1: histo = p.FindObject('B_ycor1C'+str(k)).Clone('B_ycor1C')
       else:
           htmp = p.FindObject('B_ycor1C'+str(k)).Clone()
           histo.Add(htmp)
       k+=1
   
def plots4AnalysisNoteEvol(ptCut=1.0):
 # yield as function of pt cut
 if not hMC.has_key('meanLossTrue'):
    ut.readHists(hMC,'diMuonAnalysis-MC.root')
    ut.readHists(hData,'diMuonAnalysis-Data.root')
 tc = hMC['dummy'].cd()
 tc.SetLogy(0)
 v = 'mcor'
 ratio = 'ratio'+v
 hMC[ratio] = hMC['evolution'+v+'signalP8MC'].Clone('ratio')
 hMC[ratio].Divide(hData['evolution'+v+'signalData'])
 hMC[ratio].SetTitle('')
 hMC[ratio].GetYaxis().SetTitle('MC/signal     yield arbitrary units')
 hMC[ratio].SetMarkerStyle(21)
 hMC[ratio].SetLineColor(ROOT.kBlue)
 hMC[ratio].SetMarkerColor(ROOT.kBlue)
 hMC[ratio].SetMinimum(5.)
 hMC[ratio].SetMaximum(10.)
 hMC[ratio].SetStats(0)
 hMC[ratio].Draw()
 R = hMC[ratio].GetBinContent(hMC[ratio].FindBin(1.0))
 hMC['Rline']=ROOT.TGraph()
 hMC['Rline'].SetPoint(0,0.,R*1.05)
 hMC['Rline'].SetPoint(1,2.,R*1.05)
 hMC['Rline'].SetPoint(2,2.,R*0.95)
 hMC['Rline'].SetPoint(3,0.,R*0.95)
 hMC['Rline'].SetLineColor(ROOT.kRed)
 hMC['Rline'].SetFillColor(ROOT.kRed)
 hMC['Rline'].SetFillStyle(3016)
 #hMC['Rline'].Draw('f')
 hMC['Rline2'] = ROOT.TLine(0.0,R,2.0,R)
 hMC['Rline2'].SetLineColor(ROOT.kRed)
 hMC['Rline2'].Draw('same')
 myPrint(hMC['dummy'],'EvolutionOfCuts_dimuon'+v+'_BackgroundOversignal')
#
 for c in ['Mass','Sigma']:
  if c=='Mass':   hMC['evolutionmcor'+c+'MC'].SetMinimum(2.4)
  if c=='Sigma':   hMC['evolutionmcor'+c+'MC'].SetMinimum(0.2)
  if c=='Sigma':   hMC['evolutionmcor'+c+'MC'].SetMaximum(0.7)
  hMC['evolutionmcor'+c+'MC'].SetMarkerStyle(22)
  hMC['evolutionmcor'+c+'MC'].SetMarkerColor(ROOT.kRed)
  hMC['evolutionmcor'+c+'MC'].SetLineColor(ROOT.kRed)
  hMC['evolutionmcor'+c+'MC'].Draw()
  hMC['evolutionm'+c+'MC'].SetMarkerStyle(23)
  hMC['evolutionm'+c+'MC'].SetMarkerColor(ROOT.kRed)
  hMC['evolutionm'+c+'MC'].Draw('same')
  hData['evolutionm'+c+'Data'].SetMarkerStyle(23)
  hData['evolutionm'+c+'Data'].SetMarkerColor(ROOT.kBlue)
  hData['evolutionm'+c+'Data'].Draw('same')
  hData['evolutionmcor'+c+'Data'].SetMarkerStyle(22)
  hData['evolutionmcor'+c+'Data'].SetMarkerColor(ROOT.kBlue)
  hData['evolutionmcor'+c+'Data'].SetLineColor(ROOT.kBlue)
  hData['evolutionmcor'+c+'Data'].Draw('same')
  hData['L'+c]=ROOT.TLegend(0.12,0.75,0.66,0.93)
  for hist in [hData['evolutionm'+c+'Data'],hMC['evolutionm'+c+'MC'],hData['evolutionmcor'+c+'Data'],hMC['evolutionmcor'+c+'MC']]:
     hMC['T'+hist.GetName()]=ROOT.TGraph()
     aG = hMC['T'+hist.GetName()]
     nG = 0
     for n in range(1,hist.GetNbinsX()+1):
          v = hist.GetBinContent(n)
          if v > 0: 
              aG.SetPoint(nG,hist.GetBinCenter(n),v)
              nG+=1
     aG.SetLineColor(hist.GetLineColor())
     #aG.Draw('same')
  rc = hData['L'+c].AddEntry(hMC['evolutionmcor'+c+'MC'],'Monte Carlo: with corrected momentum','PL')
  rc.SetTextColor(hMC['evolutionmcor'+c+'MC'].GetLineColor())
  rc = hData['L'+c].AddEntry(hData['evolutionmcor'+c+'Data'],'Data: with corrected momentum','PL')
  rc.SetTextColor(hData['evolutionmcor'+c+'Data'].GetLineColor())
  rc = hData['L'+c].AddEntry(hMC['evolutionm'+c+'MC'],'Monte Carlo: reconstructed momentum','PL')
  rc.SetTextColor(hMC['evolutionm'+c+'MC'].GetLineColor())
  rc = hData['L'+c].AddEntry(hData['evolutionm'+c+'Data'],'Data: reconstructed momentum','PL')
  rc.SetTextColor(hData['evolutionm'+c+'Data'].GetLineColor())
  hData['L'+c].Draw('same')
  myPrint(hMC['dummy'],'EvolutionOfCuts_dimuon_inv'+c)

 sptcut = str(ptCut)
 norm  = hData['mcor_'+ptcut].GetMaximum()
 fun = hData['Nmcor_'+ptcut].GetFunction('2CB1.4')
 hMC['Nmc-mcor_'+ptcut] = hMC['mc-mcor_'+ptcut].Clone('Nmc-mcor_'+ptcut)
 norm = 1./hMC['weights']['10GeV']
 hMC['Nmc-mcor_'+ptcut].Scale(norm)
 hMC['Nmc-mcor_'+ptcut].SetLineColor(ROOT.kMagenta)
 hData['mcor_'+ptcut].Draw()
 funMC = hMC['Nmc-mcor_'+ptcut].GetFunction('2CB1.4mc-')
 funMC.SetParameter(1,funMC.GetParameter(1)*norm)
 funMC.SetParameter(6,funMC.GetParameter(6)*norm)
 funMC.SetParameter(11,funMC.GetParameter(11)*norm)
 funMC.SetParameter(12,funMC.GetParameter(12)*norm)
 hMC['Nmc-mcor_'+ptcut].Draw('same')

 for x in ['B','CB']:
  hn2 = 'YieldMCoverData'+x
  hMC[hn2]= hMC['evolution'+x+'mcorSignalMC'].Clone(hn2)
  hMC[hn2].Divide(hData['evolution'+x+'mcorSignalData'])
  hMC[hn2].GetYaxis().SetRangeUser(0.5,2.0)
  hMC[hn2].GetXaxis().SetRangeUser(0.9,1.7)
  hMC[hn2].GetYaxis().SetTitle("Yield MC/data not normalized")
  hMC[hn2].SetLineColor(ROOT.kBlue)
  hMC[hn2].SetStats(0)
  hMC[hn2].Fit('pol0','Q','',0.0,1.7)
  myPrint(tc,'dimuon-evolptcut-yieldratio'+x)
#
  hn2 = 'evolution'+x+'mcorMassMC'
  hMC[hn2].SetStats(0)
  hMC[hn2].GetYaxis().SetRangeUser(2.9,3.4)
  hMC[hn2].GetXaxis().SetRangeUser(0.9,1.7)
  hMC[hn2].Draw()
  hData['evolution'+x+'mcorMassData'].Draw('same')
  myPrint(tc,'dimuon-evolptcut-Mass'+x)
#
  hn2 = 'evolution'+x+'mcorSigmaMC'
  hMC[hn2].SetStats(0)
  hMC[hn2].GetYaxis().SetRangeUser(0.2,0.5)
  hMC[hn2].GetXaxis().SetRangeUser(0.9,1.7)
  hMC[hn2].Draw()
  hData['evolution'+x+'mcorSigmaData'].Draw('same')
  myPrint(tc,'dimuon-evolptcut-Sigma'+x)
# 
def trainBDT():
 loadNtuples(BDT='')
 y_beam = yBeam()
 f = ROOT.TFile("signal.root","RECREATE")
 signal = ROOT.TNtuple("ntuple","ntuple","mcor:Jpsi:p1:p2:ptmin:ptmax:sumPt")
 t = hMC['10GeV']
 for n in range(t.GetEntries()):
   rc = t.GetEvent(n)
   # theCut =  'chi21*chi22<0&&abs(chi21)<0.9&&abs(chi22)<0.9&&mcor>0.20'
   if not (t.chi21*t.chi22<0):continue
   if not (abs(t.chi21)<0.9 and abs(t.chi22)<0.9): continue
   if not t.mcor>0.2: continue
   if not (t.cosCScor>-0.5 and t.cosCScor<0.5): continue
   E  = ROOT.TMath.Sqrt(t.pcor*t.pcor+3.0969*3.0969)
   Pz = ROOT.TMath.Sqrt(t.pcor*t.pcor-t.ptcor*t.ptcor)
   ycor1C = 0.5*ROOT.TMath.Log( (E + Pz) / (E-Pz) ) - y_beam
   if ycor1C < 1.0: continue
#
   if t.pt1cor<t.pt2cor: 
     minPt = t.pt1cor
     maxPt = t.pt2cor
     p1    = t.p1
     p2    = t.p2
   else: 
     minPt = t.pt2cor
     maxPt = t.pt1cor
     p2    = t.p1
     p1    = t.p2
   rc = signal.Fill(t.mcor,t.Jpsi,p1,p2,minPt,maxPt,t.pt1cor+t.pt2cor)
 print "events for training",signal.GetEntries()
 ROOT.TMVA.Tools.Instance()
 fout = ROOT.TFile("testTMVA.root","RECREATE")
 factory = ROOT.TMVA.Factory("TMVAClassification", fout,":".join([
                            "!V","!Silent","Color","DrawProgressBar","Transformations=I;D;P;G,D","AnalysisType=Classification"]
                                ))
 dataloader = ROOT.TMVA.DataLoader("dataset")
 dataloader.AddVariable("p1","F")
 dataloader.AddVariable("p2","F")
 dataloader.AddVariable("ptmin","F")
 dataloader.AddVariable("ptmax","F")
 dataloader.AddVariable("sumPt","F")
 dataloader.AddSignalTree(signal)
 dataloader.AddBackgroundTree(signal)
 sideBand       = 'Jpsi!=443'
 signalRegion   = 'Jpsi==443'
 sigCut = ROOT.TCut(signalRegion)
 bgCut  = ROOT.TCut(sideBand)
 dataloader.PrepareTrainingAndTestTree(sigCut,   # signal events
                                    bgCut,    # background events
                                   ":".join([
                                        "nTrain_Signal=5000",
                                        "nTrain_Background=5000",
                                        "SplitMode=Random",
                                        "NormMode=NumEvents",
                                        "!V"
                                       ]))
 method = factory.BookMethod(dataloader,ROOT.TMVA.Types.kBDT, "BDT",
                   ":".join([
                       "!H",
                       "!V",
                       "NTrees=850",
                       "MinNodeSize=15",
                       "MaxDepth=3",
                       "BoostType=AdaBoost",
                       "AdaBoostBeta=0.5",
                       "SeparationType=GiniIndex",
                       "nCuts=20",
                       "PruneMethod=NoPruning",
                       ]))

 factory.TrainAllMethods()
 factory.TestAllMethods()
 factory.EvaluateAllMethods()
 h['BDTtraining']=signal
def useBDT():
 dataloader = ROOT.TMVA.Reader()
 BDTp1 = array('f',[0])
 BDTp2 = array('f',[0])
 BDTptmin = array('f',[0])
 BDTptmax = array('f',[0])
 BDTsumPt = array('f',[0])
 dataloader.AddVariable("p1",BDTp1)
 dataloader.AddVariable("p2",BDTp2)
 dataloader.AddVariable("ptmin",BDTptmin)
 dataloader.AddVariable("ptmax",BDTptmin)
 dataloader.AddVariable("sumPt",BDTsumPt)
 dataloader.BookMVA("BDT","dataset/weights/TMVAClassification_BDT.weights.xml")
 nts    = [hMC['10GeV'],hMC['Jpsi'],hMC['JpsiP8'],hData['f'].nt]
 for t in nts:
    variables = "BDT"
    for v in t.GetListOfLeaves():
       variables+=":"+v.GetName()
    fBDT  = ROOT.TFile.Open("BDT-"+t.GetCurrentFile().GetName(), 'RECREATE')
    ntBDT = ROOT.TNtuple("nt","dimuon",variables)
    for n in range(t.GetEntries()):
      rc = t.GetEvent(n)
      if t.pt1<t.pt2: 
        BDTptmin[0] = t.pt1cor
        BDTptmax[0] = t.pt2cor
        BDTp1[0]    = t.p1
        BDTp2[0]    = t.p2
      else: 
        BDTptmin[0] = t.pt2cor
        BDTptmax[0] = t.pt1cor
        BDTp2[0]    = t.p1
        BDTp1[0]    = t.p2
      BDTsumPt[0]  = t.pt1cor+t.pt2cor
      bdtOutput = dataloader.EvaluateMVA("BDT")
      theArray = [bdtOutput]
      X = t.GetArgs()
      for k in range(t.GetListOfLeaves().GetEntries()): 
          theArray.append(X[k])
      theTuple = array('f',theArray)
      ntBDT.Fill(theTuple)
    fBDT.cd()
    ntBDT.Write()

def NA50Glauber():
   h['Glauber']=ROOT.TF1('Glauber','[0]*exp(-[1]*x)')
   h['Glauber'].SetParameter(0,5.)
   dataSet={}
   dataSet[9.01]  ={'HI':[5.11,0.18],'LI':[5.27,0.23],'400':[4.717,0.026]}
   dataSet[26.98] ={'HI':[4.88,0.23],'LI':[5.14,0.21],'400':[4.417,0.022]}
   dataSet[63.55] ={'HI':[4.74,0.18],'LI':[4.97,0.22],'400':[4.280,0.022]}
   dataSet[107.87]={'HI':[4.45,0.18],'LI':[4.52,0.20],'400':[3.994,0.022]}
   dataSet[183.84]={'HI':[4.05,0.15],'LI':[4.17,0.37],'400':[3.791,0.019]}
   dataSet[207.2] ={'HI':[-1.0,0.0],'LI':[-1.0,0.0],  '400':[3.715,0.016]}
   ut.bookHist(h,'NA50HI','NA50HI',3000,0.,300.)
   ut.bookHist(h,'NA50LI','NA50LI',3000,0.,300.)
   ut.bookHist(h,'NA50400','NA50400',3000,0.,300.)
   h['NA50400'].SetMarkerStyle(2)
   for A in dataSet:
     for x in ['HI','LI','400']:
       n = h['NA50'+x].FindBin(A)
       h['NA50'+x].SetBinContent(n,dataSet[A][x][0])
       h['NA50'+x].SetBinError(n,dataSet[A][x][1])
   h['NA50400'].Fit(h['Glauber'])
   # NA50 publication, sigma0 = 5.1+/-0.1, sigma_abs = 4.6+/-0.6
   print "value at Mo 95.96:",h['Glauber'].Eval(95.96)

def stripMult0():
 for fname in ['ntuple-InvMass-refitted.root','ntuple-invMass-MC-1GeV-repro.root','ntuple-invMass-MC-10GeV-repro.root','ntuple-invMass-MC-Jpsi.root','ntuple-invMass-MC-JpsiP8.root']:
   print "start with ",fname
   tmpFile = fname.replace('.','_0.')
   fin     = ROOT.TFile.Open(fname)
   t       = fin.nt
   fout    = ROOT.TFile(tmpFile,'recreate')
   sTree = t.CloneTree(0)
   nEvents = 0
   for n in range(t.GetEntries()):
     rc = t.GetEvent(n)
     if t.mult>0:
        rc = sTree.Fill(t.GetArgs())
        nEvents+=1
   print "finished ",nEvents
   sTree.AutoSave()
   fout.Close()
def studyMassConstraint():
   ut.bookHist(hMC,'yresol0','yres no corrections',100,-1.,1.)
   ut.bookHist(hMC,'yresol1','yres with ycor',100,-1.,1.)
   ut.bookHist(hMC,'yresol2','yres with ycor',100,-1.,1.)
   ut.bookHist(hMC,'yresol3','yres with ycor',100,-1.,1.)
   for nt in hMC['Jpsi']:
      P = {}
      Pcor = {}
      for i in range(1,3):
        P[i] = ROOT.Math.PxPyPzMVector(eval('nt.prec'+str(i)+'x'),eval('nt.prec'+str(i)+'y'),eval('nt.prec'+str(i)+'z'),muonMass)
# make dE correction plus direction from measured point
        dline = ROOT.TVector3(eval('nt.rec'+str(i)+'x'),eval('nt.rec'+str(i)+'y'),eval('nt.rec'+str(i)+'z')-zTarget)
        Ecor  = P[i].E()+dEdxCorrection(P[i].P())
        norm = dline.Mag()
        Pcor[i]  = ROOT.Math.PxPyPzMVector(Ecor*dline.X()/norm,Ecor*dline.Y()/norm,Ecor*dline.Z()/norm,muonMass)
      M = Pcor[1] + Pcor[2]
      M0 = P[1] + P[2]
      rc = hMC['yresol0'].Fill(M0.Rapidity() - nt.YTRUE)
      rc = hMC['yresol1'].Fill(M.Rapidity() - nt.YTRUE)
      #E = ROOT.TMath.Sqrt(M.P()**2+3.0969**2)
      #rc = hMC['yresol2'].Fill(0.5*ROOT.TMath.Log((E+M.z())/(E-M.z())) - nt.YTRUE)
      E = ROOT.TMath.Sqrt(nt.pcor**2+3.0969**2)
      Pz = ROOT.TMath.Sqrt(nt.pcor**2-nt.ptcor**2)
      rc = hMC['yresol2'].Fill(0.5*ROOT.TMath.Log((E+Pz)/(E-Pz)) - nt.YTRUE)
   hMC['Jpsi'].Draw(ycor1C+'-YTRUE>>yresol3')
   tc = hMC['dummy'].cd()
   hMC['yresol2'].SetLineColor(ROOT.kMagenta)
   hMC['yresol2'].Fit('gaus')
   hMC['yresol2'].Draw()
   tc.Update()
   stats = tc.GetPrimitive('stats')
   stats.SetOptStat(1000000001)
   stats.SetOptFit(10011)
   stats.SetFitFormat('5.4g')
   stats.SetX1NDC(0.64)
   stats.SetX2NDC(0.90)
   stats.SetY1NDC(0.23)
   stats.SetY2NDC(0.46)
   hMC['yresol1'].SetLineColor(ROOT.kGreen)
   hMC['yresol1'].Fit('gaus')
   hMC['yresol1'].Draw()
   tc.Update()
   stats = tc.GetPrimitive('stats')
   stats.SetOptStat(1000000001)
   stats.SetOptFit(10011)
   stats.SetFitFormat('5.4g')
   stats.SetX1NDC(0.64)
   stats.SetX2NDC(0.90)
   stats.SetY1NDC(0.46)
   stats.SetY2NDC(0.69)
   hMC['yresol0'].SetLineColor(ROOT.kBlue)
   hMC['yresol0'].Fit('gaus')
   hMC['yresol0'].Draw()
   tc.Update()
   stats = tc.GetPrimitive('stats')
   stats.SetOptStat(1000000001)
   stats.SetOptFit(10011)
   stats.SetFitFormat('5.4g')
   stats.SetX1NDC(0.64)
   stats.SetX2NDC(0.90)
   stats.SetY1NDC(0.69)
   stats.SetY2NDC(0.93)
   hMC['yresol2'].Draw()
   hMC['yresol1'].Draw('same')
   hMC['yresol0'].Draw('same')
   myPrint(hMC['dummy'],'YwithConstraints')
   for x in hMC['dummy'].GetListOfPrimitives():
        if x.GetName().find("yreso")==0:
            g = x.GetFunction('gaus')
            print x.GetName(),g.GetParameter(2)

def fullSim(n,nInFile):
    eospathSim = os.environ['EOSSHIP']+'/eos/experiment/ship/user/truf/muflux-sim/'
    fname = sTree.GetCurrentFile().GetName().replace('ntuple-','')
    if hMC['fnt']:
       if hMC['fnt'].GetCurrentFile().GetName().find(fname)<0:
          hMC['fMC'] = ROOT.TFile.Open(fname)
          hMC['fnt'] = hMC['fMC'].cbmsim
    else: 
          hMC['fMC'] = ROOT.TFile.Open(fname)
          hMC['fnt'] = hMC['fMC'].cbmsim
    rc = hMC['fnt'].GetEvent(n-nInFile)

def particleGun(fname='ship.conical.PG_13-TGeant4-run-1-20.root'):
# simulate coverage of drift stations before magnetic
# run_simScript.py -PG --pID 13 --Estart 100. --Eend 110. --charm=1 --CharmdetSetup=0
# myPgun.SetBoxXYZ(-100.,100.,-100.,100.,10.)
  viewDict = {0:'_x',1:'_u',2:'_v'}
  f=ROOT.TFile(fname)
  ut.bookHist(hMC,'o','overlap',100,-100,100,100,-100,100)
  ut.bookHist(hMC,'s4','overlap',100,-100,100,100,-100,100)
  ut.bookHist(hMC,'0','generated',100,-100,100,100,-100,100)
  ut.bookHist(hMC,'z','z',1000,0.,1000.)
  sTree = f.cbmsim
  for event in sTree:
    mpoints = {}
    for hit in event.MufluxSpectrometerPoint:
      if hit.PdgCode()!=13: continue
      test = ROOT.MufluxSpectrometerHit(hit.GetDetectorID(),0.)
      info = test.StationInfo()
      m = hit.GetTrackID()
      if not mpoints.has_key(m): mpoints[m]={'_u1':0,'_v2':0,'_x1':0,'_x2':0,'_x3':0,'_x4':0}
      mpoints[m][viewDict[info[4]]+str(info[0])]+=1
      rc = hMC['z'].Fill(hit.GetZ())
      if info[0]==4:
         s4x = hit.GetX()
         s4y = hit.GetY()
    for m in mpoints:
      passed = True
      for l in mpoints[m]:
         if mpoints[m][l]<2: passed = False
      if not passed: continue
      rc = hMC['o'].Fill(event.MCTrack[m].GetStartX(),event.MCTrack[m].GetStartY())
      rc = hMC['s4'].Fill(s4x,s4y)
    rc = hMC['0'].Fill(event.MCTrack[0].GetStartX(),event.MCTrack[0].GetStartY())
#
  ut.writeHists(hMC,'ParticleGun.root')
  hMC['dummy'].cd()
  hMC['s4'].Scale(1./hMC['s4'].GetMaximum())
  hMC['s4'].SetMinimum(0.0)
  hMC['s4'].SetStats(0)
  hMC['s4'].SetTitle(';x [cm]; y [cm]')
  hMC['s4'].Draw('contourz')
  myPrint(hMC['dummy'],'Fig-ParticleGun')

  yMin = ROOT.TF1('yMin','0.5*log((sqrt(x*x+3.0969*3.0969)+x*cos(0.08))/(sqrt(x*x+3.0969*3.0969)-x*cos(0.08)))-3.3741')
  yMax = ROOT.TF1('yMax','0.5*log((sqrt(x*x+3.0969*3.0969)+x*cos(0.0))/(sqrt(x*x+3.0969*3.0969)-x*cos(0.0)))-3.3741')
def studyOriginOfTracks(pidCheck=22):
   hMC['fnt'] = None
   sTree=sTreeMC
   currentFile = ''
   for n in range(sTree.GetEntries()):
      rc = sTree.GetEvent(n)
      if sTree.GetCurrentFile().GetName()!=currentFile:
          currentFile = sTree.GetCurrentFile().GetName()
          nInFile = n
      foundTracks = []
      for k in range(len(sTree.GoodTrack)):
         if sTree.GoodTrack[k]<0: continue
         if sTree.GoodTrack[k]%2!=1 or  int(sTree.GoodTrack[k]/10)%2!=1: continue
         if sTree.GoodTrack[k]>999:  continue
         foundTracks.append(k)
      if len(foundTracks)<2: continue
      fullSim(n,nInFile)
      mo={}
      for t in foundTracks:
        mo[t] = hMC['fnt'].MCTrack[sTree.MCID[t]].GetMotherId()
      for i1 in range( len(foundTracks)-1 ):
         for i2 in range(i1, len(foundTracks) ):
           if mo[foundTracks[i1]]== mo[foundTracks[i2]]:
             t1 = foundTracks[i1]
             pid   = hMC['fnt'].MCTrack[sTree.MCID[t1]].GetPdgCode()
             pidmo = hMC['fnt'].MCTrack[mo[t1]].GetPdgCode()
             if abs(pidmo) == pidCheck: 
                print n,pid,pidmo, hMC['fnt'].GetCurrentFile()
                hMC['fnt'].MCTrack.Dump()

def makeDalphaPlot(case='Data',xTarget=0.7,yTarget=-0.1):
  if case=='Data': 
     print "Program should have been started with: -f \
/eos/experiment/ship/user/truf/muflux-reco/RUN_8000_2365,\
/eos/experiment/ship/user/truf/muflux-reco/RUN_8000_2361,\
/eos/experiment/ship/user/truf/muflux-reco/RUN_8000_2415 -D True -r -t repro"
     h = hData
     sTree = sTreeData
     tag = ''
  else: 
     print "Program should have been started with: -B True -r -t repro"
     h = hMC
     sTree = sTreeMC
     tag = 'mc-'
  hname = tag+'Dalpha'
  ut.bookHist(h, hname, 'cor angle;P [GeV/c];theta [rad]',400,0,400.,200000,0.0,0.2)
  ut.bookHist(h,tag+'targetXY',"extrap to target",100,-10.,10.,100,-10.,10.)
  for event in sTree:
    for n in range(event.nTr):
      if event.GoodTrack[n]<0 or event.GoodTrack[n]>900: continue
      if abs(event.Chi2[n]>0.9): continue
      P = ROOT.TVector3(event.Px[n],event.Py[n],event.Pz[n])
      if P.Mag()>10. and event.GoodTrack[n]!=111: continue
      Pcor = ROOT.TVector3((event.x[n]-xTarget)/(event.z[n] - zTarget),(event.y[n]-yTarget)/(event.z[n] - zTarget), 1.)
      cosalpha = P.Dot(Pcor)/(P.Mag()*Pcor.Mag())
      alpha = ROOT.TMath.ACos(cosalpha)
      Ecor = P.Mag()+dEdxCorrection(P.Mag())
      rc = h[hname].Fill(Ecor,alpha)
      if Ecor>150. and Ecor<300:
        lam = (event.z[n] - zTarget)/event.Pz[n]
        X = event.x[n]+lam*event.Px[n]
        Y = event.y[n]+lam*event.Py[n]
        rc = h[tag+'targetXY'].Fill(X,Y)
  cut = 'sqrt(Px*Px+Py*Py+Pz*Pz)>150.&&sqrt(Px*Px+Py*Py+Pz*Pz)<300&&GoodTrack==111&&abs(Chi2)<0.9'
  sTree.Draw('y+(z+'+str(abs(zTarget))+')*Py/Pz:x+(z+'+str(abs(zTarget))+')*Px/Pz>>'+tag+'targetXY',cut)

  for x in [hname]:
     h[x+'_p']=h[x].ProjectionX(x+'_p')
     for n in range(1,h[x+'_p'].GetNbinsX()+1):
        tmp=h[x].ProjectionY('tmp',n,n)
        h[x+'_p'].SetBinContent(n,tmp.GetMean())
        h[x+'_p'].SetBinError(n,tmp.GetMeanError())
  ut.writeHists(h,hname+'.root')
def makeMomSlice(x,exampleBin=-1):
     hMC[x+'_p']=hMC[x].ProjectionX(x+'_p')
     for n in range(1,hMC[x+'_p'].GetNbinsX()+1):
        tmp=hMC[x].ProjectionY('tmp',n,n)
        hMC[x+'_p'].SetBinContent(n,tmp.GetMean())
        hMC[x+'_p'].SetBinError(n,tmp.GetMeanError())
        if n==exampleBin:
           tmp.Rebin(10)
           tmp.GetXaxis().SetRangeUser(0.0,02)
           tmp.SetTitle(x+'_distrib_'+str(exampleBin))
           tmp.Draw()
           myPrint(hMC['dummy'],x+'_distrib_'+str(exampleBin))
def studyInvMassResolution(command='',xTarget=0.53,yTarget=-0.2,plotOnly=False,threeD=False,debug=False):
  if plotOnly:
       ut.readHists(hMC,'MSangleStudy.root')
       hData['DalphaJpsi']   = hMC['DalphaJpsi']
       hData['targetXYJpsi'] = hMC['targetXYJpsi']
  elif command.find("MS")==0:
    if command.find("data")>0:
     ROOT.gROOT.cd()
     for p in ['_x','_y']:
          ut.bookHist(hData, 'Dalpha'+p, 'cor angle;P [GeV/c];theta [rad]',50,0,200.,100000,-0.1,0.1)
     ut.bookHist(hData, 'targetXY',"extrap to target",100,0.,400.,100,-10.,10.,100,-10.,10.)
     ut.bookHist(hData, 'targetZ',"extrap to target",100,0.,400.,200,-700.,300.)
     ut.bookHist(hData, 'targetIP',"extrap to target",100,0.,400.,100,0.,10.)
     theCut = "GoodTrack%100==11&&abs(Chi2)<0.9"
     if xTarget<0:
        splus_xTarget="-"+str(abs(xTarget))
        sminus_xTarget="+"+str(abs(xTarget))
     else: 
        splus_xTarget="+"+str(xTarget)
        sminus_xTarget="-"+str(xTarget)
     if yTarget<0:
        splus_yTarget="-"+str(abs(yTarget))
        sminus_yTarget="+"+str(abs(yTarget))
     else: 
        splus_yTarget="+"+str(yTarget)
        sminus_yTarget="-"+str(yTarget)
     P = "sqrt(Px*Px+Py*Py+Pz*Pz)"
     sTreeData.Draw("Px/Pz-(x"+sminus_xTarget+")/(z+"+str(abs(zTarget))+"):"+P+">>Dalpha_x",theCut)
     sTreeData.Draw("Py/Pz-(y"+sminus_yTarget+")/(z+"+str(abs(zTarget))+"):"+P+">>+Dalpha_y",theCut)
     Y = "y-((z + "+str(abs(zTarget))+")/Pz)*Py"
     X = "x-((z + "+str(abs(zTarget))+")/Pz)*Px"
     sTreeData.Draw(Y+":"+X+":"+P+">>targetXY",theCut)
     rho = "-((x"+sminus_xTarget+")+(y"+sminus_yTarget+"))*Pz/(Px+Py)"
     Z   = "z"+rho
     sTreeData.Draw(Z+":"+P+">>targetZ",theCut)
     IP = "sqrt(("+rho+"*Px/Pz+x"+sminus_xTarget+")**2+("+rho+"*Py/Pz+y"+sminus_yTarget+")**2)"
     sTreeData.Draw(IP+":"+P+">>targetIP",theCut)
     ut.writeHists(hData,'MSangleStudy_'+options.listOfFiles.replace(',','_')+'.root')
     return
    else:
     loadNtuples()
     rnr       = ROOT.TRandom()
     hMC['ntmuons'] = ROOT.TChain('muons')
     if command=="MS10":
        hMC['ntmuons'].AddFile("recMuons_1GeV.root")
        hMC['ntmuons'].AddFile("recMuons_10GeV.root")
     elif command=="MSP8":
        hMC['ntmuons'].AddFile('recMuons_P8.root')
     elif command=="MSP6":
        hMC['ntmuons'].AddFile('recMuons_Cascade.root')
     ROOT.gROOT.cd()
     ut.bookHist(hMC, 'invMass_true', 'inv mass;M [GeV/c^{2}]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
     ut.bookHist(hMC, 'invMass_rec', 'inv mass;M [GeV/c^{2}]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
     ut.bookHist(hMC, 'invMass_cor', 'inv mass;M [GeV/c^{2}]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
     ut.bookHist(hMC, 'invMass_cor_trueP',     'inv mass;M [GeV/c^{2}]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
     ut.bookHist(hMC, 'invMass_cor_trueTheta', 'inv mass;M [GeV/c^{2}]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
     ut.bookHist(hMC, 'invMass_cor_scaled', 'inv mass;M [GeV/c^{2}]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
     if threeD:
       ut.bookHist(hMC, 'theta(pcor-ptrue)', 'angle;P [GeV/c];theta [rad]',50,0,200.,200000,0,0.2)
       ut.bookHist(hMC, 'alpha_p0pDT', 'angle;P [GeV/c];theta [rad]',50,0,200.,200000,0,0.2)
       ut.bookHist(hMC, 'alpha_p0pcor', 'angle;P [GeV/c];theta [rad]',50,0,200.,200000,0,0.2)
       ut.bookHist(hMC, 'alpha_p0pRec', 'angle;P [GeV/c];theta [rad]',50,0,200.,200000,0,0.2)
       ut.bookHist(hMC, 'Jpsi_alpha_p0pRec', 'angle;P [GeV/c];theta [rad]',50,0,200.,200000,0,0.2)
       ut.bookHist(hMC, 'alpha_pDTpRec', 'angle;P [GeV/c];theta [rad]',50,0,200.,200000,0,0.2)
       ut.bookHist(hMC, 'alpha_p0pcorRec', 'angle;P [GeV/c];theta [rad]',50,0,200.,200000,0,0.2)
       ut.bookHist(hMC, 'Jpsi_alpha_p0pcorRec', 'angle;P [GeV/c];theta [rad]',50,0,200.,200000,0,0.2)
       ut.bookHist(hMC, 'alpha_zTarget_pcorRec', 'angle;P [GeV/c];theta [rad]',50,0,200.,200000,0,0.2)
       ut.bookHist(hMC, 'mcDalpha',   'cor angle;P [GeV/c];theta [rad]',50,0,200.,200000,0.0,0.2)
       ut.bookHist(hMC, 'mcDalphaDT', 'cor angle;P [GeV/c];theta [rad]',50,0,200.,200000,0.0,0.2)
       ut.bookHist(hMC, 'Jpsi_mcDalpha', 'cor angle;P [GeV/c];theta [rad]',50,0,200.,200000,0.0,0.2)
       ut.bookHist(hMC, 'hitResol','hit resolution',100,0.,400.,100,0.,2.)
       ut.bookHist(hMC, 'Jpsi_hitResol','hit resolution',100,0.,400.,100,0.,2.)
       ut.bookHist(hMC, 'Jpsi_Dalpha', 'cor angle;P [GeV/c];theta [rad]',50,0,200.,200000,0.0,0.2)
     else:
       for p in ['_x','_y']:
         ut.bookHist(hMC, 'theta(pcor-ptrue)'+p, 'angle;P [GeV/c];theta [rad]',50,0,200.,100000,-0.1,0.1)
         ut.bookHist(hMC, 'alpha_p0pDT'+p, 'angle;P [GeV/c];theta [rad]',50,0,200.,100000,-0.1,0.1)
         ut.bookHist(hMC, 'alpha_p0pDT2'+p, 'angle;PDT [GeV/c];theta [rad]',50,0,200.,100000,-0.1,0.1)
         ut.bookHist(hMC, 'alpha_p0pcor'+p, 'angle;P [GeV/c];theta [rad]',50,0,200.,100000,-0.1,0.1)
         ut.bookHist(hMC, 'alpha_p0pRec'+p, 'angle;P [GeV/c];theta [rad]',50,0,200.,100000,-0.1,0.1)
         ut.bookHist(hMC, 'Jpsi_alpha_p0pRec'+p, 'angle;P [GeV/c];theta [rad]',50,0,200.,100000,-0.1,0.1)
         ut.bookHist(hMC, 'alpha_pDTpRec'+p, 'angle;P [GeV/c];theta [rad]',50,0,200.,100000,-0.1,0.1)
         ut.bookHist(hMC, 'alpha_p0pcorRec'+p, 'angle;P [GeV/c];theta [rad]',50,0,200.,100000,-0.1,0.1)
         ut.bookHist(hMC, 'Jpsi_alpha_p0pcorRec'+p, 'angle;P [GeV/c];theta [rad]',50,0,200.,100000,-0.1,0.1)
         ut.bookHist(hMC, 'alpha_zTarget_pcorRec'+p, 'angle;P [GeV/c];theta [rad]',50,0,200.,100000,-0.1,0.1)
         ut.bookHist(hMC, 'mcDalpha'+p,   'cor angle;P [GeV/c];theta [rad]',50,0,200.,100000,-0.1,0.1)
         ut.bookHist(hMC, 'mcDalphaDT'+p, 'cor angle;P [GeV/c];theta [rad]',50,0,200.,100000,-0.1,0.1)
         ut.bookHist(hMC, 'Jpsi_mcDalpha'+p, 'cor angle;P [GeV/c];theta [rad]',50,0,200.,100000,-0.1,0.1)
         ut.bookHist(hMC, 'hitResol'+p,'hit resolution'+p,100,0.,400.,100,-1.,1.)
         ut.bookHist(hMC, 'Jpsi_hitResol'+p,'hit resolution'+p,100,0.,400.,100,-1.,1.)
         ut.bookHist(hMC, 'Jpsi_Dalpha'+p, 'cor angle;P [GeV/c];theta [rad]',50,0,200.,100000,-0.1,0.1)
     ut.bookHist(hMC, 'delP', 'delta P/P versus P;P [GeV/c];#Delta P [GeV/c]',50,0,400.,100,-1.,1.)
     ut.bookHist(hMC, 'mctargetXY',"extrap to target",100,0.,400.,100,-10.,10.,100,-10.,10.)
     ut.bookHist(hMC, 'Jpsi_mctargetXY',"extrap to target",100,0.,400.,100,-10.,10.,100,-10.,10.)
     ut.bookHist(hMC, 'mctargetZ',"extrap to target",100,0.,400.,200,-700.,300.)
     ut.bookHist(hMC, 'mctargetIP',"extrap to target",100,0.,400.,100,0.,10.)
     ut.bookHist(hMC, 'Jpsi_mctargetZ',"extrap to target",100,0.,400.,200,-700.,300.)
     ut.bookHist(hMC, 'Jpsi_mctargetIP',"extrap to target",100,0.,400.,100,0.,10.)
     ut.bookHist(hMC, 'originXYZ',"origin of track",400,-400.,0.,100,-10.,10.,100,-10.,10.)
     ut.bookHist(hMC, 'originXY_Zfix',"origin of track",100,-10.,10.,100,-10.,10.)
     ut.bookHist(hMC, 'Jpsi_originXYZ',"origin of track",400,-400.,0.,100,-10.,10.,100,-10.,10.)
     ut.bookHist(hMC, 'Jpsi_originXY_Zfix',"origin of track",100,-10.,10.,100,-10.,10.)
     ut.bookHist(hMC, 'dEdx','dEdx',100,0.,400.,1000,0.,100.)
     ut.bookHist(hMC, 'dEdx_DT','dEdx',100,0.,400.,1000,0.,100.)
     ut.bookHist(hMC, 'dEdx_rec','dEdx',100,0.,400.,200,-100.,100.)
     ut.bookHist(hMC, 'Jpsi_targetXY',"extrap to target",100,0.,400.,100,-10.,10.,100,-10.,10.)
     ut.bookHist(hMC, 'Jpsi_targetZ',"extrap to target",100,0.,400.,200,-700.,300.)
     ut.bookHist(hMC, 'Jpsi_targetIP',"extrap to target",100,0.,400.,100,0.,10.)
     ROOT.gROOT.cd()

     theCut  = "DTz<3332&&abs(muID)==13&&oz<-100&&goodTrack==111&&chi2<0.9" # because of some strange events with oz=0 in P8
     hMC['ntmuons'].Draw('ox:oy:oz>>originXYZ',theCut)
     hMC['ntmuons'].Draw('ox+('+str(zTarget)+'-oz)*px/pz:oy+('+str(zTarget)+'-oz)*py/pz>>originXY_Zfix',theCut)
     theCutJpsi = theCut+"&&moID==443"
     hMC['ntmuons'].Draw('ox:oy:oz>>Jpsi_originXYZ',theCutJpsi)
     hMC['ntmuons'].Draw('ox+('+str(zTarget)+'-oz)*px/pz:oy+('+str(zTarget)+'-oz)*py/pz>>Jpsi_originXY_Zfix',theCutJpsi)

     P =  "sqrt(px*px+py*py+pz*pz)"
     E =  "sqrt(recpx*recpx+recpy*recpy+recpz*recpz)"
     DT = "sqrt(DTpx*DTpx+DTpy*DTpy+DTpz*DTpz)"
# targetXY
     Y = "recy-((recz + "+str(abs(zTarget))+")/recpz)*recpy"
     X = "recx-((recz + "+str(abs(zTarget))+")/recpz)*recpx"
     hMC['ntmuons'].Draw(Y+":"+X+":"+E+">>mctargetXY",theCut)
# IP
     rho = "-(recx+recy)*recpz/(recpx+recpy)"
     Z = "recz"+rho
     hMC['ntmuons'].Draw(Z+":"+E+">>mctargetZ",theCut)
     IP = "sqrt(("+rho+"*recpx/recpz+recx)**2+("+rho+"*recpy/recpz+recy)**2)"
     hMC['ntmuons'].Draw(IP+":"+E+">>mctargetIP",theCut)
#MS
     Y = "((px*DTpx+py*DTpy+pz*DTpz)/("+P+"*"+DT+"))"
     if threeD: hMC['ntmuons'].Draw("acos("+Y+"):"+P+">>alpha_p0pDT",theCutJpsi)
     else:
        for p in ['px','py']:   hMC['ntmuons'].Draw(p+"/pz-DT"+p+"/DTpz:"+P+">>alpha_p0pDT_"+p[1],theCutJpsi)
        for p in ['px','py']:   hMC['ntmuons'].Draw(p+"/pz-DT"+p+"/DTpz:"+DT+">>alpha_p0pDT2_"+p[1],theCutJpsi)
     Pcor = "sqrt((DTx-ox)**2+(DTy-oy)**2++(DTz-oz)**2)"
     Y = "((DTx-ox)*px+(DTy-oy)*py+(DTz-oz)*pz)/("+Pcor+"*"+P+")"
     if threeD: hMC['ntmuons'].Draw("acos("+Y+"):"+P+">>alpha_p0pcor",theCutJpsi)
     else:
        for p in ['px','py']:   hMC['ntmuons'].Draw(p+"/pz-(DT"+p[1]+"-o"+p[1]+")/(DTz-oz):"+P+">>alpha_p0pcor_"+p[1],theCutJpsi)
# with reco
     r = "sqrt(recpx*recpx+recpy*recpy+recpz*recpz)"
     Y = "((px*recpx+py*recpy+pz*recpz)/("+P+"*"+r+"))"
     if threeD: hMC['ntmuons'].Draw("acos("+Y+"):"+P+">>alpha_p0pRec",theCutJpsi)
     else:
        for p in ['px','py']:   hMC['ntmuons'].Draw(p+"/pz-rec"+p+"/recpz:"+P+">>alpha_p0pRec_"+p[1],theCutJpsi)
     PcorRec1 = "sqrt((recx-ox)**2+(recy-oy)**2++(recz-oz)**2)"
     Y = "((recx-ox)*px+(recy-oy)*py+(recz-oz)*pz)/("+PcorRec1+"*"+P+")"
     if threeD: hMC['ntmuons'].Draw("acos("+Y+"):"+P+">>alpha_p0pcorRec",theCutJpsi)
     else:
        for p in ['px','py']:   hMC['ntmuons'].Draw(p+"/pz-(rec"+p[1]+"-o"+p[1]+")/(recz-oz):"+P+">>alpha_p0pcorRec_"+p[1],theCutJpsi)
     PcorRec2 = "sqrt(("+str(0)+"-recx)**2+("+str(0)+"-recy)**2+("+str(zTarget)+"-recz)**2)"
     Y = "(-("+str(0)+"-recx)*px-("+str(0)+"-recy)*py-("+str(zTarget)+"-recz)*pz)/("+PcorRec2+"*"+P+")"
     if threeD: hMC['ntmuons'].Draw("acos("+Y+"):"+P+">>alpha_zTarget_pcorRec",theCutJpsi)
     else:
        for p in ['px','py']:   hMC['ntmuons'].Draw(p+"/pz-(rec"+p[1]+")/(recz-"+str(zTarget)+"):"+P+">>alpha_zTarget_pcorRec_"+p[1],theCutJpsi)
     Y = "(-("+str(0)+"-recx)*recpx-("+str(0)+"-recy)*recpy-("+str(zTarget)+"-recz)*recpz)/("+PcorRec2+"*"+r+")"
     if threeD: hMC['ntmuons'].Draw("acos("+Y+"):"+r+">>mcDalpha",theCutJpsi)
     else:
        for p in ['px','py']:   
             hMC['ntmuons'].Draw("rec"+p+"/recpz-(rec"+p[1]+")/(recz-"+str(zTarget)+"):"+E+">>mcDalpha_"+p[1],theCutJpsi)
     Y = "(-("+str(0)+"-recx)*DTpx-("+str(0)+"-recy)*DTpy-("+str(zTarget)+"-recz)*DTpz)/("+PcorRec2+"*"+DT+")"
     if threeD: hMC['ntmuons'].Draw("acos("+Y+"):"+r+">>mcDalphaDT",theCutJpsi)
     else:
        for p in ['px','py']:   hMC['ntmuons'].Draw("DT"+p+"/DTpz-(rec"+p[1]+")/(recz-"+str(zTarget)+"):"+DT+">>mcDalphaDT_"+p[1],theCutJpsi)
     Y = "((recpx*DTpx+recpy*DTpy+recpz*DTpz)/("+r+"*"+DT+"))"
     if threeD: hMC['ntmuons'].Draw("acos("+Y+"):"+DT+">>alpha_pDTpRec",theCutJpsi)
     else:
       for p in ['px','py']:   hMC['ntmuons'].Draw("DT"+p+"/DTpz-rec"+p+"/recpz:"+P+">>alpha_pDTpRec_"+p[1],theCutJpsi)
     hMC['ntmuons'].Draw(P+'-'+DT+':'+P+'>>dEdx',theCut)
     hMC['ntmuons'].Draw(P+'-'+DT+':'+DT+'>>dEdx_DT',theCut)
     hMC['ntmuons'].Draw(P+'-'+E+':'+E+'>>dEdx_rec',theCut)
#
     Xdel="(recx-(DTx-(recz-DTz)*DTpx/DTpz))"
     Ydel="(recy-(DTy-(recz-DTz)*DTpy/DTpz))"
     Y = "sqrt("+Xdel+"*"+Xdel+"+"+Ydel+"*"+Ydel+")"
     if threeD:
        hMC['ntmuons'].Draw(Y+":"+DT+">>hitResol",theCut)
        hMC['ntmuons'].Draw(Y+":"+DT+">>Jpsi_hitResol",theCutJpsi)
     else:
        tmp = {'x':Xdel,'y':Ydel}
        for p in tmp:
           hMC['ntmuons'].Draw(tmp[p]+":"+DT+">>hitResol_"+p,theCut)
           hMC['ntmuons'].Draw(tmp[p]+":"+DT+">>Jpsi_hitResol_"+p,theCutJpsi)
# data
     theCut = theJpsiCut('mcor',True,1.0, 0.,300.,2,False)+"&&abs(3.1-mcor)<0.5"
# targetXY
     V = {'1':'p1','2':'p2'}
     pf = {'MC':'mc','Data':''}
     if command=="MSP6":
        ntuples = {'MC':hMC['fJpsi'].nt,'Data':hData['f'].nt}
     if command=="MSP8":
        ntuples = {'MC':hMC['fJpsiP8'].nt,     'Data':hData['f'].nt}
     if command=="MS10":
        ntuples = {'MC':hMC['10GeV'],  'Data':hData['f'].nt}
     for x in ntuples:
       s_xTarget=str(0)
       s_yTarget=str(0)
       splus_xTarget="+"+str(0)
       sminus_xTarget="-"+str(0)
       if x=='Data':
          if xTarget<0:
            splus_xTarget="-"+str(abs(xTarget))
            sminus_xTarget="+"+str(abs(xTarget))
          else: 
            splus_xTarget="+"+str(xTarget)
            sminus_xTarget="-"+str(xTarget)
          if yTarget<0:
            splus_yTarget="-"+str(abs(yTarget))
            sminus_yTarget="+"+str(abs(yTarget))
          else: 
            splus_yTarget="+"+str(yTarget)
            sminus_yTarget="-"+str(yTarget)

          sp_yTarget=str(yTarget)
       nt = ntuples[x]
       if nt.GetLeaf("    prec1x"): nt.GetLeaf("    prec1x").SetName("prec1x")
       for n in V:
        m = 'rec'+n
        r = "sqrt(p"+m+"x*p"+m+"x+p"+m+"y*p"+m+"y+p"+m+"z*p"+m+"z)"
        PcorRec2 = "sqrt(("+splus_xTarget+"-"+m+"x)**2+("+splus_yTarget+"-"+m+"y)**2+("+str(zTarget)+"-"+m+"z)**2)"
        Y = "(-("+splus_xTarget+"-"+m+"x)*p"+m+"x-("+splus_yTarget+"-"+m+"y)*p"+m+"y-("+str(zTarget)+"-"+m+"z)*p"+m+"z)/("+PcorRec2+"*"+r+")"
        if threeD: nt.Draw("acos("+Y+"):"+r+">>+Jpsi_"+pf[x]+"Dalpha",theCut)
        else:
          nt.Draw("p"+m+"x/p"+m+"z-("+m+"x"+sminus_xTarget+")/("+m+"z+"+str(abs(zTarget))+"):"+r+">>+Jpsi_"+pf[x]+"Dalpha_x",theCut)
          nt.Draw("p"+m+"y/p"+m+"z-("+m+"y"+sminus_yTarget+")/("+m+"z+"+str(abs(zTarget))+"):"+r+">>+Jpsi_"+pf[x]+"Dalpha_y",theCut)
        if x!='Data':
           P = "sqrt(p"+n+"x*p"+n+"x+p"+n+"y*p"+n+"y+p"+n+"z*p"+n+"z)"
           Y = "((p"+n+"x*p"+m+"x+p"+n+"y*p"+m+"y+p"+n+"z*p"+m+"z)/("+P+"*"+r+"))"
           if threeD: nt.Draw("acos("+Y+"):"+P+">>+Jpsi_alpha_p0pRec",theCut)
           else:
              for p in ['px','py']: nt.Draw("p"+n+p[1]+"/p"+n+"z-p"+m+p[1]+"/p"+m+"z:"+P+">>+Jpsi_alpha_p0pRec_"+p[1],theCut)
           PcorRec1 = "sqrt(("+m+"x-ox)**2+("+m+"y-oy)**2+("+m+"z-oz)**2)"
           Y = "(("+m+"x-ox)*p"+n+"x+("+m+"y-oy)*p"+n+"y+("+m+"z-oz)*p"+n+"z)/("+PcorRec1+"*"+P+")"
           if threeD: nt.Draw("acos("+Y+"):"+P+">>+Jpsi_alpha_p0pcorRec",theCut)
           else:
              for p in ['px','py']:  nt.Draw("p"+n+p[1]+"/p"+n+"z-("+m+p[1]+"-o"+p[1]+")/("+m+"z-oz):"+P+">>+Jpsi_alpha_p0pcorRec_"+p[1],theCut)
        Y = m+"y-(("+m+"z + "+str(abs(zTarget))+")/p"+m+"z)*p"+m+"y"
        X = m+"x-(("+m+"z + "+str(abs(zTarget))+")/p"+m+"z)*p"+m+"x"
        P = "sqrt(p"+m+"x*p"+m+"x+p"+m+"y*p"+m+"y+p"+m+"z*p"+m+"z)"
        nt.Draw(Y+":"+X+":"+P+">>+Jpsi_"+pf[x]+"targetXY",theCut)
        rho = "-(("+m+"x"+sminus_xTarget+")+("+m+"y"+sminus_yTarget+"))*p"+m+"z/(p"+m+"x+p"+m+"y)"
        Z = m+"z"+rho
        nt.Draw(Z+":"+P+">>+Jpsi_"+pf[x]+"targetZ",theCut)
        IP = "sqrt(("+rho+"*p"+m+"x/p"+m+"z+"+m+"x"+sminus_xTarget+")**2+("+rho+"*p"+m+"y/p"+m+"z+"+m+"y"+sminus_yTarget+")**2)"
        nt.Draw(IP+":"+P+">>+Jpsi_"+pf[x]+"targetIP",theCut)
# 
        if x!='Data' and debug:
           Ptrue={}
           Prec={}
           Pcor={}
           PcorScaled={}
           Pcor_trueP={}
           Pcor_trueTheta={}
           ptCut = 1.0
           pmin = 20.0
           pmax = 300.
           for event in nt:
              if event.p1x==nt.p2x: continue
              if event.Jpsi!=443: continue
              if max(event.pt1cor,event.pt2cor)<ptCut: continue
              if event.mcor<0.2: continue
              if event.chi21*event.chi22>0: continue
              if max(abs(event.chi21),abs(event.chi22))>0.9: continue
              if min(event.p1,event.p2)<pmin or max(event.p1,event.p2)>pmax: continue
              Ptrue[1] = ROOT.Math.PxPyPzMVector(event.p1x,event.p1y,event.p1z,muonMass)
              Ptrue[2] = ROOT.Math.PxPyPzMVector(event.p2x,event.p2y,event.p2z,muonMass)
              Prec[1]  = ROOT.Math.PxPyPzMVector(event.prec1x,event.prec1y,event.prec1z,muonMass)
              Prec[2]  = ROOT.Math.PxPyPzMVector(event.prec2x,event.prec2y,event.prec2z,muonMass)
# make dE correction plus direction from measured point
              scale = 0. # 25.
              sigX = 0.02*scale
              sigY = 0.06*scale
              sigPVz = 20.
              xOff = 0. # 1.
              yOff = 0. # -0.5
              dline         = ROOT.TVector3(event.rec1x,event.rec1y,event.rec1z-zTarget)
              norm = dline.Mag()
              dlineScaled   = ROOT.TVector3(event.rec1x+sigX*rnr.Gaus()+xOff,event.rec1y+sigY*rnr.Gaus()+yOff,event.rec1z-zTarget+sigPVz*rnr.Gaus())
              normScaled = dlineScaled.Mag()
              Ecor = Prec[1].E()+dEdxCorrection(Prec[1].P())
              Pcor[1]  = ROOT.Math.PxPyPzMVector(Ecor*dline.X()/norm,Ecor*dline.Y()/norm,Ecor*dline.Z()/norm,muonMass)
              PcorScaled[1]  = ROOT.Math.PxPyPzMVector(Ecor*dlineScaled.X()/normScaled,Ecor*dlineScaled.Y()/normScaled,Ecor*dlineScaled.Z()/normScaled,muonMass)
              Pcor_trueP[1] = ROOT.Math.PxPyPzMVector(Ptrue[1].P()*dline.X()/norm,Ptrue[1].P()*dline.Y()/norm,Ptrue[1].P()*dline.Z()/norm,muonMass)
              Pcor_trueTheta[1] = ROOT.Math.PxPyPzMVector(Ecor*Ptrue[1].x()/Ptrue[1].P(),Ecor*Ptrue[1].y()/Ptrue[1].P(),Ecor*Ptrue[1].z()/Ptrue[1].P(),muonMass)
              dline         = ROOT.TVector3(event.rec2x,event.rec2y,event.rec2z-zTarget)
              dlineScaled   = ROOT.TVector3(event.rec2x+sigX*rnr.Gaus()+xOff,event.rec2y+sigY*rnr.Gaus()+yOff,event.rec2z-zTarget+sigPVz*rnr.Gaus())
              Ecor = Prec[2].E()+dEdxCorrection(Prec[2].P())
              norm = dline.Mag()
              normScaled = dlineScaled.Mag()
              Pcor[2]  = ROOT.Math.PxPyPzMVector(Ecor*dline.X()/norm,Ecor*dline.Y()/norm,Ecor*dline.Z()/norm,muonMass)
              PcorScaled[2]  = ROOT.Math.PxPyPzMVector(Ecor*dlineScaled.X()/normScaled,Ecor*dlineScaled.Y()/normScaled,Ecor*dlineScaled.Z()/normScaled,muonMass)
              Pcor_trueP[2] = ROOT.Math.PxPyPzMVector(Ptrue[2].P()*dline.X()/norm,Ptrue[2].P()*dline.Y()/norm,Ptrue[2].P()*dline.Z()/norm,muonMass)
              Pcor_trueTheta[2] = ROOT.Math.PxPyPzMVector(Ecor*Ptrue[2].x()/Ptrue[2].P(),Ecor*Ptrue[2].y()/Ptrue[2].P(),Ecor*Ptrue[2].z()/Ptrue[2].P(),muonMass)
              Ltrue = Ptrue[1]+Ptrue[2]
              Lrec  = Prec[1]+Prec[2]
              Lcor  = Pcor[1]+Pcor[2]
              LcorScaled  = PcorScaled[1]+PcorScaled[2]
              Lcor_trueP  = Pcor_trueP[1]+Pcor_trueP[2]
              Lcor_trueTheta  = Pcor_trueTheta[1]+Pcor_trueTheta[2]
              rc = hMC['invMass_true'].Fill(Ltrue.M())
              rc = hMC['invMass_rec'].Fill(Lrec.M())
              rc = hMC['invMass_cor'].Fill(Lcor.M())
              rc = hMC['invMass_cor_trueP'].Fill(Lcor_trueP.M())
              rc = hMC['invMass_cor_trueTheta'].Fill(Lcor_trueTheta.M())
              rc = hMC['invMass_cor_scaled'].Fill(LcorScaled.M())
# from Bukin fit, data sigma about 30% worse than MC, M**2 = 2*p1*p2*(1-cos theta)
# try 15% more error on angle.
    #ROOT.gRandom.Gaus()*0.15
              if 0>1:
                for j in [1,2]:
                  a = ROOT.TVector3(Ptrue[j].X(),Ptrue[j].Y(),Ptrue[j].Z())
                  b = ROOT.TVector3(Pcor[j].X(),Pcor[j].Y(),Pcor[j].Z())
                  theta = a.Dot(b)/(a.Mag()*b.Mag())
                  delP  = Pcor[j].P() - Ptrue[j].P()
                  rc = hMC['theta(pcor-ptrue)'].Fill(Ptrue[j].P(),ROOT.TMath.ACos(theta))
                  rc = hMC['delP'].Fill(Ptrue[j].P(),delP/Ptrue[j].P())
     ut.writeHists(hMC,'MSangleStudy_'+command+'.root')
     return
##############################################################################################################################################
  for x in ['alpha_p0pDT','alpha_p0-pcor','alpha_zTargetpcorRec','alpha_pDTpRec',#'mc-Dalpha','Dalpha',
            'alpha_p0pRec','alpha_p0pcorRec','mc-DalphaJpsi','DalphaJpsi','hitResol']:
      makeMomSlice(x,exampleBin=-1)

# check beam position
  tc = hMC['dummy'].cd()
  tc.SetLogy(0)
  hMC['DG'] = ROOT.TF1("DG", "gaus(0) + gaus(3)", -10, 10)
  hMC['DG'].SetParameter(0,3500)
  hMC['DG'].SetParameter(1,0)
  hMC['DG'].SetParameter(2,1.) 
  hMC['DG'].SetParameter(3,100.)
  hMC['DG'].SetParameter(4,0.)
  hMC['DG'].SetParameter(5,5.)
  hMC['DG'].SetParName(0,'N1')
  hMC['DG'].SetParName(1,'mean')
  hMC['DG'].SetParName(2,'sigma1')
  hMC['DG'].SetParName(3,'N2')
  hMC['DG'].SetParName(4,'mean2')
  hMC['DG'].SetParName(5,'sigma2')
  hData["targetXYJpsi_X"]= hData["targetXYJpsi"].ProjectionX("targetXYJpsi_X")
  hData["targetXYJpsi_Y"]= hData["targetXYJpsi"].ProjectionY("targetXYJpsi_Y")
  hData["targetXYJpsi_X"].Fit(hMC['DG'],'S','',-10.,10.)
  hData["targetXYJpsi_Y"].Fit(hMC['DG'],'S','',-10.,10.)
  hData["targetXYJpsi_X"].Draw()
  tc.Update()
  stats = tc.GetPrimitive('stats')
  stats.SetOptStat(1000000001)
  stats.SetOptFit(1111)
  stats.SetFitFormat('5.4g')
  stats.SetX1NDC(0.60)
  stats.SetY1NDC(0.33)
  stats.SetX2NDC(0.98)
  stats.SetY2NDC(0.94)
  myPrint(hMC['dummy'],'target_X')
  hData["targetXYJpsi_Y"].Draw()
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
  myPrint(hMC['dummy'],'target_Y')
  hMC["mc-targetXY_X"]= hMC["mc-targetXY"].ProjectionX("mc-targetXY_X")
  hMC["mc-targetXY_Y"]= hMC["mc-targetXY"].ProjectionY("mc-targetXY_Y")
  hMC["mc-targetXY_X"].Fit(hMC['DG'],'S','',-10.,10.)
  hMC["mc-targetXY_Y"].Fit(hMC['DG'],'S','',-10.,10.)
  hMC["mc-targetXY_X"].Draw()
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
  myPrint(hMC['dummy'],'MC-target_X')
  hMC["mc-targetXY_Y"].Draw()
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
  myPrint(hMC['dummy'],'MC-target_Y')
#
  hData['DalphaJpsi_p'] = hMC['DalphaJpsi_p']
# 13.6/P sqrt(L/x0)(1+0.038 log(L/x0)), L/X0 = 412
  function = "sqrt((13.6/1000.*sqrt([0])/x*(1.+0.038*log([0])))**2+[1]**2)"
  hMC['fitfun'] = ROOT.TF1('fitfun',function,0,400)
#
  tc = hMC['dummy'].cd()
  tc.SetLogy(1)
  hMC['mc-DalphaJpsi_p'].SetLineColor(ROOT.kCyan)
  hMC['mc-DalphaJpsi_p'].SetStats(0)
  hMC['mc-Dalpha_p'].SetLineColor(ROOT.kMagenta)
  hMC['mc-Dalpha_p'].SetStats(0)
  hMC['mc-Dalpha_p'].GetXaxis().SetRangeUser(0.,200.)
  rc = hMC['mc-Dalpha_p'].Fit('fitfun','S','',10,200.)
  fitResult = rc.Get()
  hMC['txtmc-Dalpha'] = ROOT.TLatex(50.,0.045,"equivalent rad. length %5.1F +/-%5.1F X0"%(fitResult.Parameter(0),fitResult.ParError(0)))
  hMC['txtmc-Dalpha'].SetTextColor(hMC['mc-Dalpha_p'].GetLineColor())
  hMC['txtmc-Dalpha2'] = ROOT.TLatex(50.,0.035,"#Theta_{DT}: %5.1F +/-%5.1F mrad"%(fitResult.Parameter(1)*1000,fitResult.ParError(1)*1000))
  hMC['txtmc-Dalpha2'].SetTextColor(hMC['mc-Dalpha_p'].GetLineColor())
  hMC['mc-Dalpha_p'].GetXaxis().SetRangeUser(0.,200.)
  rc = hMC['mc-DalphaJpsi_p'].Fit('fitfun','S','',10,200.)
  fitResult = rc.Get()
  hMC['txtmc-DalphaJpsi'] = ROOT.TLatex(50.,0.025,"equivalent rad. length %5.1F +/-%5.1F X0"%(fitResult.Parameter(0),fitResult.ParError(0)))
  hMC['txtmc-DalphaJpsi'].SetTextColor(hMC['mc-DalphaJpsi_p'].GetLineColor())
  hMC['txtmc-DalphaJpsi2'] = ROOT.TLatex(50.,0.020,"#Theta_{DT}: %5.1F +/-%5.1F mrad"%(fitResult.Parameter(1)*1000,fitResult.ParError(1)*1000))
  hMC['txtmc-DalphaJpsi2'].SetTextColor(hMC['mc-DalphaJpsi_p'].GetLineColor())
  hData['DalphaJpsi_p'].SetStats(0)
  rc = hData['DalphaJpsi_p'].Fit('fitfun','S','',10,200.)
  fitResult = rc.Get()
  hData['txt-Dalpha'] = ROOT.TLatex(50.,0.086,"equivalent rad. length %5.1F +/-%5.1F X0"%(fitResult.Parameter(0),fitResult.ParError(0)))
  hData['txt-Dalpha'].SetTextColor(hData['DalphaJpsi_p'].GetLineColor())
  hData['txt-Dalpha2'] = ROOT.TLatex(50.,0.066,"#Theta_{DT}: %5.1F +/-%5.1F mrad"%(fitResult.Parameter(1)*1000,fitResult.ParError(1)*1000))
  hData['txt-Dalpha2'].SetTextColor(hData['DalphaJpsi_p'].GetLineColor())
  hData['DalphaJpsi_p'].SetMinimum(01E-5)
  hMC['mc-Dalpha_p'].Draw()
  hMC['mc-DalphaJpsi_p'].Draw('same')
  hData['DalphaJpsi_p'].Draw('same')
  for t in [hMC['txtmc-Dalpha'],hMC['txtmc-Dalpha2'],hMC['txtmc-DalphaJpsi'],hMC['txtmc-DalphaJpsi2'],hData['txt-Dalpha'],hData['txt-Dalpha2']]:
      t.SetTextSize(0.03)
      t.Draw('same')
  myPrint(hMC['dummy'],'MS_angle-correction')
#
  hMC['fitfun'].FixParameter(1,0.)
  rc = hMC['alpha_p0-pDT)_p'].Fit('fitfun','S','',10,400.)
  fitResult = rc.Get()
  hMC['txtalpha_p0-pDT)'] = ROOT.TText(100.,0.01,"equivalent rad. length %5.1F +/-%5.1F X0"%(fitResult.Parameter(0),fitResult.ParError(0)))
  hMC['txtalpha_p0-pDT)'].SetTextColor(hMC['alpha_p0-pDT)_p'].GetLineColor())
  rc = hMC['alpha_p0-pcor)_p'].Fit('fitfun','S','',10,400.)
  fitResult = rc.Get()
  hMC['txtalpha_p0-pcor)'] = ROOT.TText(20.,0.0005,"equivalent rad. length %5.1F +/-%5.1F X0"%(fitResult.Parameter(0),fitResult.ParError(0)))
  hMC['txtalpha_p0-pcor)'].SetTextColor(hMC['alpha_p0-pcor)_p'].GetLineColor())
  hMC['alpha_p0-pcor)_p'].GetFunction('fitfun').SetLineColor(hMC['alpha_p0-pcor)_p'].GetLineColor())
  hMC['funAlpha'] = hMC['fitfun'].Clone('funAlpha')
  hMC['funAlpha'].SetParameter(0,412.)
  hMC['funAlpha'].SetLineColor(ROOT.kMagenta)
  hMC['txtalpha'] = ROOT.TText(100.,0.02,"nominal rad. length %5.1F X0"%(412.))
  hMC['txtalpha'].SetTextColor(hMC['funAlpha'].GetLineColor())
  hMC['alpha_p0-pcor)_p'].SetStats(0)
  hMC['alpha_p0-pcor)_p'].SetTitle('')
  hMC['alpha_p0-pcor)_p'].SetLineColor(ROOT.kGreen)
  hMC['alpha_p0-pDT)_p'].SetStats(0)
  hMC['alpha_p0-pDT)_p'].SetTitle('')
  hMC['alpha_p0-pDT)_p'].GetYaxis().SetTitle('#Delta #theta [rad]')
  hMC['alpha_p0-pDT)_p'].SetLineColor(ROOT.kRed)
  hMC['alpha_p0-pDT)_p'].Draw()
  hMC['txtalpha_p0-pDT)'].Draw()
  hMC['alpha_p0-pcor)_p'].Draw('same')
  hMC['txtalpha_p0-pcor)'].Draw()
  hMC['funAlpha'].Draw('same')
  hMC['txtalpha'].Draw()
  hMC['Lalpha'] = ROOT.TLegend(0.21,0.79,0.83,0.97)
  rc = hMC['Lalpha'].AddEntry(hMC['alpha_p0-pDT)_p'],'MS angle, momentum direction at 1st station','PL')
  rc.SetTextColor(hMC['alpha_p0-pDT)_p'].GetLineColor())
  rc = hMC['Lalpha'].AddEntry(hMC['alpha_p0-pcor)_p'],'MS angle using 1st hit','PL')
  rc.SetTextColor(hMC['alpha_p0-pcor)_p'].GetLineColor())
  rc = hMC['Lalpha'].AddEntry(hMC['funAlpha'],'theory','PL')
  rc.SetTextColor(hMC['funAlpha'].GetLineColor())
  hMC['Lalpha'].Draw('same')
  myPrint(hMC['dummy'],'MS_angle')
#
  hMC['alpha_zTarget-pcorRec)_p'].SetStats(0)
  hMC['alpha_zTarget-pcorRec)_p'].SetTitle('')
  hMC['alpha_zTarget-pcorRec)_p'].SetLineColor(ROOT.kCyan)
  hMC['alpha_p0-pRec)_p'].SetStats(0)
  hMC['alpha_p0-pRec)_p'].SetLineColor(ROOT.kBlue)
  hMC['alpha_p0-pcorRec)_p'].SetLineColor(ROOT.kRed)
  hMC['alpha_p0-pcorRec)_p'].SetStats(0)
  hMC['alpha_p0-pRec)_p'].GetYaxis().SetTitle('#Delta #theta [rad]')
  hMC['fitfun'].ReleaseParameter(1)
  hname = 'alpha_p0-pRec)_p'
  rc = hMC[hname].Fit('fitfun','S','',10,300.)
  hMC['txt'+hname] = ROOT.TLatex(50.,0.045,"#Theta_{DT}: %5.1F +/-%5.1F mrad"%(fitResult.Parameter(0)*1000,fitResult.ParError(0)*1000))
  hMC['txt'+hname].SetTextColor(hMC[hname].GetLineColor())
  hMC['txt'+hname+'2'] = ROOT.TLatex(50.,0.035,"#Theta_{DT}: %5.1F +/-%5.1F mrad"%(fitResult.Parameter(1)*1000,fitResult.ParError(1)*1000))
  hMC['txt'+hname+'2'].SetTextColor(hMC[hname].GetLineColor())
  hname = 'alpha_p0-pcorRec)_p'
  rc = hMC[hname].Fit('fitfun','S','',10,300.)
  hMC['txt'+hname] = ROOT.TLatex(50.,0.025,"#Theta_{DT}: %5.1F +/-%5.1F mrad"%(fitResult.Parameter(0)*1000,fitResult.ParError(0)*1000))
  hMC['txt'+hname].SetTextColor(hMC[hname].GetLineColor())
  hMC['txt'+hname+'2'] = ROOT.TLatex(50.,0.02,"#Theta_{DT}: %5.1F +/-%5.1F mrad"%(fitResult.Parameter(1)*1000,fitResult.ParError(1)*1000))
  hMC['txt'+hname+'2'].SetTextColor(hMC[hname].GetLineColor())
  hname = 'alpha_zTarget-pcorRec)_p'
  rc = hMC[hname].Fit('fitfun','S','',10,300.)
  hMC['alpha_p0-pRec)_p'].Draw()
  hMC['alpha_p0-pcorRec)_p'].Draw('same')
  hMC['alpha_zTarget-pcorRec)_p'].Draw('same')
  hMC['alpha_p0-pcor)_p'].Draw('same')
  hMC['LRecalpha'] = ROOT.TLegend(0.25,0.73,0.65,0.85)
  rc = hMC['LRecalpha'].AddEntry(hMC['alpha_p0-pRec)_p'],'MS angle, reconstructed momentum direction','PL')
  rc.SetTextColor(hMC['alpha_p0-pRec)_p'].GetLineColor())
  rc = hMC['LRecalpha'].AddEntry(hMC['alpha_p0-pcorRec)_p'],'MS angle using 1st state of track','PL')
  rc.SetTextColor(hMC['alpha_zTarget-pcorRec)_p'].GetLineColor())
  rc = hMC['LRecalpha'].AddEntry(hMC['alpha_zTarget-pcorRec)_p'],'MS angle using zTarget and 1st state of track','PL')
  rc.SetTextColor(hMC['alpha_p0-pcorRec)_p'].GetLineColor())
  rc = hMC['LRecalpha'].AddEntry(hMC['alpha_p0-pcor)_p'],'MS angle using 1st hit','PL')
  rc.SetTextColor(hMC['alpha_p0-pcor)_p'].GetLineColor())
  hMC['LRecalpha'].Draw('same')
  myPrint(hMC['dummy'],'MS_angle_rec')
  if command.find('MS')==0: return
  for x in ['theta(pcor-ptrue)','delP']:
    hMC[x+'_P']=hMC[x].ProjectionX(x+'_P')
    hMC[x+'_P'].SetStats(0)
    hMC[x+'_Pmean']=hMC[x+'_P'].Clone(x+'_P')
    hMC[x+'_Pmean'].SetStats(0)
    for n in range(1,hMC[x].GetNbinsX()+1):
       tmp = hMC[x].ProjectionY('tmp',n,n)
       if tmp.GetEntries()<50: 
          rms = 0
          mean = 0
       else: 
          rms = tmp.GetRMS()
          mean = tmp.GetMean()
       hMC[x+'_P'].SetBinContent(n,rms)
       hMC[x+'_Pmean'].SetBinContent(n,mean)
  tc = hMC['dummy'].cd()
  tc.SetLogy(0)
  hMC['delP_Pmean'].Draw()
  myPrint(hMC['dummy'],'delP_Pmean')
  hMC['delP_P'].Draw()
  hMC['presol'] = ROOT.TF1('presol','0.01*sqrt(0.683**2+(0.031*x)**2)',0,400)
  hMC['presol'].SetLineColor(ROOT.kRed)
  hMC['presol'].Draw('same')
  myPrint(hMC['dummy'],'delP_P_MS')
#
  hMC['theta(pcor-ptrue)_P'].Draw()
  myPrint(hMC['dummy'],'theta(pcor-ptrue)_P_MS')
#
  hMC['invMass_rec'].SetLineColor(ROOT.kBlue)
  hMC['invMass_cor'].SetLineColor(ROOT.kGreen)
  hMC['invMass_cor_trueTheta'].SetTitle('')
  hMC['invMass_cor_trueTheta'].SetLineColor(ROOT.kMagenta)
  hMC['invMass_cor_trueP'].SetLineColor(ROOT.kRed)
  hMC['invMass_cor'].SetStats(0)
  hMC['invMass_rec'].SetStats(0)
  hMC['invMass_cor_trueTheta'].SetStats(0)
  hMC['invMass_cor_trueP'].SetStats(0)
  hMC['invMass_cor_trueTheta'].Draw()
  hMC['invMass_cor_trueP'].Draw('same')
  hMC['invMass_cor'].Draw('same')
  hMC['invMass_rec'].Draw('same')
  hMC['LinvMass'] = ROOT.TLegend(0.49,0.56,0.88,0.78)
  rc = hMC['LinvMass'].AddEntry(hMC['invMass_rec'],'inv mass with reconstructed momentum','PL')
  rc.SetTextColor(hMC['invMass_rec'].GetLineColor())
  rc = hMC['LinvMass'].AddEntry(hMC['invMass_cor'],'inv mass with corrected momentum','PL')
  rc.SetTextColor(hMC['invMass_cor'].GetLineColor())
  rc = hMC['LinvMass'].AddEntry(hMC['invMass_cor_trueP'],'inv mass with true muon energy','PL')
  rc.SetTextColor(hMC['invMass_cor_trueP'].GetLineColor())
  rc = hMC['LinvMass'].AddEntry(hMC['invMass_cor_trueTheta'],'inv mass with true momentum direction','PL')
  rc.SetTextColor(hMC['invMass_cor_trueTheta'].GetLineColor())
  hMC['LinvMass'].Draw('same')
  myPrint(hMC['dummy'],'invMass_MS_dE')

def muonEfficiency0():
   ut.bookHist(hMC,'P','P track',300,0.,300.)
   ut.bookHist(hMC,'Pmux','P track mux confirmed',300,0.,300.)
   ut.bookHist(hMC,'Pmu','P track mu confirmed',300,0.,300.)
   ROOT.gROOT.cd()
   hMC['Jpsi'].Draw('p1cor>>P',' Jpsi==443')
   hMC['Jpsi'].Draw('p2cor>>P+','Jpsi==443')
   hMC['Jpsi'].Draw('p1cor>>Pmux', 'Jpsi==443&&muID1%2==1')
   hMC['Jpsi'].Draw('p2cor>>Pmux+','Jpsi==443&&muID1%2==1')
   hMC['Jpsi'].Draw('p1cor>>Pmu',  'Jpsi==443&&muID1%100==11')
   hMC['Jpsi'].Draw('p2cor>>Pmu+', 'Jpsi==443&&muID1%100==11')
   hMC['muEffx']=ROOT.TEfficiency(hMC['Pmux'],hMC['P'])
   hMC['muEff'] =ROOT.TEfficiency(hMC['Pmu'], hMC['P'])

def studyVertex(nt):
   ut.bookHist(hMC,'vxXY','vertex xy',)
   ut.bookHist(hMC, 'targetXYZ',"extrap to target",200,-700.,300.,100,-10.,10.,100,-10.,10.)
   if nt.GetLeaf("    prec1x"): nt.GetLeaf("    prec1x").SetName("prec1x")
   for k in range(nt.GetEntries()):
      rc = nt.GetEvent(k)
      if nt.mult>2:continue
      if max(nt.pt1cor,nt.pt2cor)<1.: continue
      if nt.chi21*nt.chi22>0: continue
      if abs(nt.chi21)>0.9 or abs(nt.chi22)>0.9: continue
      if max(nt.p1,nt.p2)>300.0: continue
      if abs(3.1-nt.mcor)>0.4: continue
      if not (nt.muID1%100==11 and nt.muID2%100==11): continue
      PosDir={}
      PosDir[1] = [ROOT.TVector3(nt.rec1x,nt.rec1y,nt.rec1z),ROOT.TVector3(nt.prec1x,nt.prec1y,nt.prec1z)]
      PosDir[2] = [ROOT.TVector3(nt.rec2x,nt.rec2y,nt.rec2z),ROOT.TVector3(nt.prec2x,nt.prec2y,nt.prec2z)]
      X,Y,Z,dist  =  myVertex(1,2,PosDir)
      rc = hMC['targetXYZ'].Fill(Z,Y,X)
   ut.writeHists(hMC,'myVertex.root')
def myVertex(t1,t2,PosDir,xproj=False):
    # closest distance between two tracks
            # d = |pq . u x v|/|u x v|
    if not xproj:
        a = ROOT.TVector3(PosDir[t1][0](0) ,PosDir[t1][0](1) ,PosDir[t1][0](2))
        u = ROOT.TVector3(PosDir[t1][1](0) ,PosDir[t1][1](1) ,PosDir[t1][1](2))
        c = ROOT.TVector3(PosDir[t2][0](0) ,PosDir[t2][0](1) ,PosDir[t2][0](2))
        v = ROOT.TVector3(PosDir[t2][1](0) ,PosDir[t2][1](1) ,PosDir[t2][1](2))
    else:
        a = ROOT.TVector3(PosDir[t1][0](0) ,0, PosDir[t1][0](2))
        u = ROOT.TVector3(PosDir[t1][1](0), 0, PosDir[t1][1](2))
        c = ROOT.TVector3(PosDir[t2][0](0) ,0, PosDir[t2][0](2))
        v = ROOT.TVector3(PosDir[t2][1](0), 0, PosDir[t2][1](2))
    pq = a-c
    uCrossv = u.Cross(v)
    dist  = pq.Dot(uCrossv)/(uCrossv.Mag()+1E-8)
    # u.a - u.c + s*|u|**2 - u.v*t    = 0
    # v.a - v.c + s*v.u    - t*|v|**2 = 0
    E = u.Dot(a) - u.Dot(c) 
    F = v.Dot(a) - v.Dot(c) 
    A,B = u.Mag2(), -u.Dot(v) 
    C,D = u.Dot(v), -v.Mag2()
    t = -(C*E-A*F)/(B*C-A*D)
    X = c.x()+v.x()*t
    Y = c.y()+v.y()*t
    Z = c.z()+v.z()*t
    return X,Y,Z,abs(dist)
def studyDrellYanAndCharm(DYxsec=1.5):
     ut.bookCanvas(hMC,'DYandCharm','Drell Yan and charm',2400,1200,3,1)
     MCs = {'Charm2':[Charmfactor,ROOT.kBlue],'DY':[DYfactor*DYxsec,ROOT.kRed]}
     for mc in MCs:
        ut.bookHist(hMC,'muMom'+mc,'muon momentum;GeV/c',100,0.,400.,50,0.,5.)
        ut.bookHist(hMC,'trueMass'+mc,'dimuon mass;GeV/c^{2}',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
        ut.bookHist(hMC,'trueMassWithSel'+mc,'dimuon mass;GeV/c^{2}',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
        for nt in hMC[mc]:
           if abs(nt.p1x-nt.p2x)<1E-5: continue # clones
           mu1 = ROOT.Math.PxPyPzMVector(nt.p1x,nt.p1y,nt.p1z,muonMass)
           mu2 = ROOT.Math.PxPyPzMVector(nt.p2x,nt.p2y,nt.p2z,muonMass)
           R = mu1+mu2
           rc = hMC['trueMass'+mc].Fill(R.M())
           if min(mu1.P(),mu2.P())>20. and max(mu1.Pt(),mu2.Pt())>1.0: rc = hMC['trueMassWithSel'+mc].Fill(R.M())
        hMC['trueMass'+mc].Scale(MCs[mc][0])
        hMC['trueMassWithSel'+mc].Scale(MCs[mc][0])
        hMC['trueMass'+mc].SetLineColor(MCs[mc][1])
        hMC['trueMass'+mc].GetXaxis().SetRangeUser(0.,5.)
        hMC['trueMassWithSel'+mc].SetLineColor(MCs[mc][1])
        hMC['trueMassWithSel'+mc].GetXaxis().SetRangeUser(0.,5.)
     hMC['DYandCharm'].cd(1)
     hMC['trueMassDY'].Draw()
     hMC['trueMassCharm2'].Draw('same')
     hMC['DYandCharm'].cd(2)
     hMC['trueMassWithSelDY'].Draw()
     hMC['trueMassWithSelCharm2'].Draw('same')
     hMC['DYandCharm'].cd(3)
     rc = hMC['Charm2'].Draw('sqrt(p1x*p1x+p1y*p1y):sqrt(p1x*p1x+p1y*p1y+p1z*p1z)>>muMomCharm2')
     rc = hMC['DY'].Draw('sqrt(p1x*p1x+p1y*p1y):sqrt(p1x*p1x+p1y*p1y+p1z*p1z)>>muMomDY')
     hMC['muMomCharm2_p'] = hMC['muMomCharm2'].ProjectionX('muMomCharm2_p')
     hMC['muMomDY_p']     = hMC['muMomDY'].ProjectionX('muMomDY_p')
     hMC['muMomCharm2_p'].Scale(MCs['Charm2'][0])
     hMC['muMomDY_p'].Scale(MCs['DY'][0])
     hMC['muMomCharm2_p'].SetLineColor(MCs['Charm2'][1])
     hMC['muMomDY_p'].SetLineColor(MCs['DY'][1])
     hMC['muMomCharm2_p'].Draw()
     hMC['muMomDY_p'].Draw('same')
def studyDrellYan(fitMethod='B',weighted=False,withDY=False,fillMom=False):
   X =   {'0.0':ROOT.kBlack,'1.0':ROOT.kGreen, '2.0':ROOT.kBlue,'4.0':ROOT.kRed}
   txt = {'0.0':'no DY',    '1.0':'nominal DY','2.0':'2x DY','4.0':'4x DY'}
   S   = {'lowMass':ROOT.kBlue,'highMass':ROOT.kMagenta,'Charm':ROOT.kGreen,'DY':ROOT.kCyan}
# muon momentum true
   hMC['dummy'].cd()
   if fillMom: studyDrellYanAndCharm()
   hData['FitYield']={}
   for z in X:
     x = z+fitMethod
     hMC['DY'+x]={}
     hData['DY'+x]={}
     ut.readHists(hMC['DY'+x],'muID2_'+fitMethod+'-1.0_20.0_DY'+z+'_wp6/MC-histos.root')
     ut.readHists(hData['DY'+x],'muID2_'+fitMethod+'-1.0_20.0_DY'+z+'_wp6/Data-histos.root')
# fit result from twoCBYieldfit
     NJpsi  = hData['DY'+x][fitMethod+'_ycor1C-Jpsi'].GetBinContent(19)
     eNJpsi = hData['DY'+x][fitMethod+'_ycor1C-Jpsi'].GetBinError(19)
     hData['FitYield'][x]=[NJpsi,eNJpsi]
     hMC['lowMass'+x]  = hMC['DY'+x]['mc-'+fitMethod+'_ycor1CLowMass-10GeV'].ProjectionY('lowMass'+x)
     hMC['highMass'+x] = hMC['DY'+x]['mc-'+fitMethod+'_ycor1CHighMass-Jpsi'].ProjectionY('highMass'+x)
     hMC['Charm'+x]    = hMC['DY'+x]['Charmmc-'+fitMethod+'_ycor1CLowMass-10GeV'].ProjectionY('Charm'+x)
     hMC["hDY"+x]      = hMC['DY'+x]['DYmc-'+fitMethod+'_ycor1CLowMass-10GeV'].ProjectionY("hDY"+x)
     hMC['lowMass'+x].SetLineColor(X[z])
# rapidity
     hMC['Y_lowMass'+x]  = hMC['DY'+x]['mc-'+fitMethod+'_ycor1CLowMass-10GeV'].ProjectionX('Y_lowMass'+x)
     hMC['Y_highMass'+x] = hMC['DY'+x]['mc-'+fitMethod+'_ycor1CHighMass-Jpsi'].ProjectionX('Y_highMass'+x)
     hMC['Y_Charm'+x]    = hMC['DY'+x]['Charmmc-'+fitMethod+'_ycor1CLowMass-10GeV'].ProjectionX('Y_Charm'+x)
     hMC["Y_DY"+x]      = hMC['DY'+x]['DYmc-'+fitMethod+'_ycor1CLowMass-10GeV'].ProjectionX("Y_DY"+x)
     for s in S:
       hMC['sY_'+s+x]  = hMC['Y_'+s+x].Clone('sY_'+s+x)
       hMC['sY_'+s+x].Scale(1./hMC['Y_'+s+x].GetSumOfWeights())
       hMC['sY_'+s+x].SetLineColor(S[s])
       hMC['Y_'+s+x].SetLineColor(S[s])
     mctag =  'lowMass'+x
# make fit
     fitOption='SL'
     minX = 0.5
     maxX = 8.0
     bw = hMC[mctag].GetBinWidth(1)
     params,funTemplate = getFitDictionary(fitMethod)
     if withDY:
        hMC["GDYmctagk"]=None
        histo = hMC["hDY"+x]
        bw = histo.GetBinWidth(1)
        params,funTemplate = getFitDictionary('B')   # always use bukin with two tails
        F = ROOT.TF1('DY',funTemplate['F'],0,10,funTemplate['N'])
        funTemplate['Init'](F,bw)
        for l in params['fixParams']: F.FixParameter(l,params['fixParams'][l])
        F.SetParameter(params['signalLow'],histo.GetEntries())
        F.FixParameter(params['signal'],0.)
        F.FixParameter(params['highMass'],3.1)
        F.FixParameter(params['highSigma'],0.3)
        F.FixParameter(params['psi(2s)'],0.0)
        F.FixParameter(params['DY'],0.0)
        for l in params['highTails']: F.FixParameter(l,params['highTails'][l])
        for l in params['pol']:       F.FixParameter(l,0.)
        F.FixParameter(params['DY'],0.)
        rc = myFit(histo,F,'SQL',0.5,6.)
     fname = 'fun-lowMass'+x
     hMC[fname] = ROOT.TF1(fname,funTemplate['F'],0,10,funTemplate['N'])
     CB = hMC[fname]
     funTemplate['Init'](CB,bw)
     for l in params['fixParams']: CB.FixParameter(l,params['fixParams'][l])
     CB.SetParameter(params['signalLow'],hMC[mctag].GetEntries())
   # fix high mass to 0
     CB.FixParameter(params['signal'],0.)
     CB.FixParameter(params['highMass'],3.1)
     CB.FixParameter(params['highSigma'],0.3)
     CB.FixParameter(params['psi(2s)'],0.0)
     CB.FixParameter(params['DY'],0.0)
     for l in params['highTails']: CB.FixParameter(l,params['highTails'][l])
     for l in params['pol']:       CB.FixParameter(l,0.)
     if withDY:
        CB.ReleaseParameter(params['DY'])
        CB.SetParameter(params['DY'],0.5)
        hMC["GDYmctagk"] = hMC["hDY"+x].GetFunction('DY')
     else:
   # no Drell Yan
        CB.FixParameter(params['DY'],0.)
        hMC["GDYmctagk"]=None
     for l in params['lowTailsOff']: CB.FixParameter(l,params['lowTailsOff'][l])
     rc = myFit(hMC[mctag],CB,fitOption,minX,maxX)
     if rc[0]!=0:
        print "FIT  ERROR: ",mctag
        break
     for l in params['lowTails']: 
        CB.ReleaseParameter(l)
        CB.SetParameter(l,params['lowTails'][l])
     for l in params['lowTailsLimits']: 
        CB.SetParLimits(l,params['lowTailsLimits'][l][0],params['lowTailsLimits'][l][1])
     # for l in params['pol']:       CB.ReleaseParameter(l)
     rc = myFit(hMC[mctag],CB,fitOption,minX,maxX)
     rc = myFit(hMC[mctag],CB,fitOption,minX,maxX)
     hMC[mctag].GetFunction(fname).SetLineColor(X[z])
     if rc[0]!=0:
        print "FIT  ERROR: ",mctag
        break
   ROOT.gStyle.SetOptStat(0)
   hMC['lowMass4.0'+fitMethod].SetTitle('; GeV/c{2};N')
   hMC['lowMass4.0'+fitMethod].SetMinimum(0.)
   hMC['lowMass4.0'+fitMethod].Draw()
   hMC['lowMass1.0'+fitMethod].Draw('same')
   hMC['lowMass2.0'+fitMethod].Draw('same')
   hMC['lowMass0.0'+fitMethod].Draw('same')
   myPrint(hMC['dummy'],'DrellYan-lowmass-'+fitMethod)
# rapidity
   hMC['dummy'].cd()
   x='0.0'+fitMethod
   hMC['sY_Charm'+x].Draw()
   hMC['LY']=ROOT.TLegend(0.5,0.6,0.9,0.8)
   for s in S:
       hMC['sY_'+s+x].Draw('same')
       rc = hMC['LY'].AddEntry(hMC['sY_'+s+x],s,'PL')
   hMC['LY'].Draw('same')
   myPrint(hMC['dummy'],'Y-distrDiffSources-'+fitMethod)

# fix signal shape from MC
   params,funTemplate = getFitDictionary(fitMethod)
   histo = hMC['highMass0.0'+fitMethod]
   bw = histo.GetBinWidth(1)
   fname = 'fun-MC'
   hMC[fname] = ROOT.TF1(fname,funTemplate['F'],0,10,funTemplate['N'])
   CB = hMC[fname]
   funTemplate['Init'](CB,bw)
   for l in params['fixParams']: CB.FixParameter(l,params['fixParams'][l])
   Nguess = histo.Integral(histo.FindBin(2.6),histo.FindBin(3.5))
   CB.SetParameter(params['signal'],Nguess)
   for l in params['lowTailsOff']: 
      CB.FixParameter(l,params['lowTailsOff'][l])
   for l in params['highTailsLimits']: 
      CB.SetParLimits(l,params['highTailsLimits'][l][0],params['highTailsLimits'][l][1])
   CB.FixParameter(params['signalLow'],0)
   CB.FixParameter(params['lowMass'],0)
   CB.FixParameter(params['lowSigma'],0)
   CB.FixParameter(params['psi(2s)'],0.0)
   CB.FixParameter(params['DY'],0.0)
   rc = myFit(histo,CB,fitOption,minX,maxX)
   hMC["fitResult"] = rc[2]
# now data:
   hData['M'] = hData['DY0.0'+fitMethod][fitMethod+'_ycor1C'].ProjectionY('DY0_M')
   histo = hData['M']
   bw = histo.GetBinWidth(1)
   fname = 'fun-Data'
   hData[fname] = ROOT.TF1(fname,funTemplate['F'],0,10,funTemplate['N'])
   CB = hData[fname]
   funTemplate['Init'](CB,bw)
   for l in params['fixParams']: CB.FixParameter(l,params['fixParams'][l])
   Nguess = histo.Integral(histo.FindBin(2.6),histo.FindBin(3.5))
   CB.SetParameter(params['signal'],Nguess)
   Nguess = histo.Integral(histo.FindBin(0.5),histo.FindBin(2.0))
   for l in params['lowTails']: 
      CB.ReleaseParameter(l)
      CB.SetParameter(l,params['lowTails'][l])
   for l in params['lowTailsLimits']: 
      CB.SetParLimits(l,params['lowTailsLimits'][l][0],params['lowTailsLimits'][l][1])
   for l in params['highTailsLimits']: 
      CB.SetParLimits(l,params['highTailsLimits'][l][0],params['highTailsLimits'][l][1])
   for l in params['highTails']:CB.FixParameter(l,hMC["fitResult"].Parameter(l))
   CB.SetParameter(params['signalLow'],Nguess)
   CB.FixParameter(params['psi(2s)'],0.0)
   CB.FixParameter(params['DY'],0.0)
   for l in params['pol']:       CB.FixParameter(l,0)
   rc = myFit(histo,CB,fitOption,minX,maxX)
   # for l in params['pol']:       CB.ReleaseParameter(l)
   rc = myFit(histo,CB,fitOption,minX,maxX)
   CB.ReleaseParameter(params['psi(2s)'])
   rc = myFit(histo,CB,fitOption,minX,maxX)
   for l in params['highTails']:CB.ReleaseParameter(l)
   rc = myFit(histo,CB,fitOption,minX,maxX)

   hData["fitResult"] = rc[2]

   histo.SetTitle('; GeV/c{2};N')
   histo.Draw()
   myPrint(hMC['dummy'],'DrellYan-data-'+fitMethod)
# add MC normalized to same npot, take MC low mass and add signal from fit.
   fun = histo.GetFunction(fname)
   Fsignal = 'signal'+fitMethod
   hMC[Fsignal]   = ROOT.TF1(Fsignal,funTemplate['F'],0,10,funTemplate['N'])
   hMC['signal']  = hMC[Fsignal]
   hMC['lowMass'] = ROOT.TF1('lowMass',funTemplate['F'],0,10,funTemplate['N'])
   hMC['back']    = ROOT.TF1('back',funTemplate['F'],0,10,funTemplate['N'])
   for fx in [Fsignal,'lowMass','back']:
     for i in range(funTemplate['N']): 
        hMC[fx].FixParameter(i,fun.GetParameter(i))
   hMC[Fsignal].SetParameter(params['switch'],1)
   hMC['lowMass'].FixParameter(params['switch'],2)
   hMC['back'].FixParameter(params['switch'],3)
   hMC['lowMass'].SetLineColor(ROOT.kGreen)
   hMC['back'].SetLineColor(ROOT.kGreen)

   ut.bookCanvas(hMC,'dataAndMC1',' ',1200,900,1,1)
   hMC['dataAndMC1'].cd(1)
   nMax = ut.findMaximumAndMinimum(histo)[1]
   fac = dataStats/MCStats['10GeV']
   for z in X:
     x=z+fitMethod
     hMC['normlowMass'+x]=hMC['lowMass'+x].Clone('normlowMass'+x)
     hMC['normlowMass'+x].Scale(fac)
     bw = hMC['normlowMass'+x].GetBinWidth(1)
     for n in range(1,hMC['normlowMass'+x].GetNbinsX()+1):
        x1 = hMC['normlowMass'+x].GetBinLowEdge(n)
        x2 = x1+bw
        S = hMC[Fsignal].Integral(x1,x2)/bw
        hMC['normlowMass'+x].SetBinContent(n,hMC['normlowMass'+x].GetBinContent(n)+S)
     minMax = ut.findMaximumAndMinimum(hMC['normlowMass'+x])
     if minMax[1]>nMax:  nMax = minMax[1]
   histo.SetMarkerStyle(33)
   histo.SetMarkerColor(ROOT.kMagenta)
   histo.SetLineColor(ROOT.kMagenta)
   histo.SetMaximum(nMax*1.1)
   histo.DrawCopy()
   hData['LDY']=ROOT.TLegend(0.5,0.6,0.9,0.8)
   rc = hData['LDY'].AddEntry(histo,'Data','PL')
   for z in X: 
      x=z+fitMethod
      hMC['normlowMass'+x].Draw('samehist')
      rc = hData['LDY'].AddEntry(hMC['normlowMass'+x],'MC '+txt[z],'PL')
   hData['LDY'].Draw('same')
   myPrint(hMC['dataAndMC1'],'DrellYan-data-And-MC-'+fitMethod)

#  a*hMC['lowMass0'] + b*DYfactor*hMC["hDY0.0"] + c*Charmfactor*hMC["hCharm0.0"] + signal
   hMC['dummy'].cd()
   hMC["Ndy"] = hMC["hDY0.0"+fitMethod].Clone('Ndy')
   hMC["Ndy"].Scale(1./hMC["hDY0.0"+fitMethod].GetSumOfWeights())
   hMC["Ncharm"] = hMC["Charm0.0"+fitMethod].Clone('Ncharm')
   hMC["Ncharm"].Scale(1./hMC["Charm0.0"+fitMethod].GetSumOfWeights())
   colors = {}
   colors['MDrell Yan']      =     [24,ROOT.kCyan]
   colors['Mcharm'] =              [27,ROOT.kRed+3]
   hMC["Ndy"].SetLineColor(colors['MDrell Yan'][1])
   hMC["Ndy"].SetMarkerColor(colors['MDrell Yan'][1])
   hMC["Ndy"].SetMarkerStyle(colors['MDrell Yan'][0])
   hMC["Ncharm"].SetLineColor(colors['Mcharm'][1])
   hMC["Ncharm"].SetMarkerColor(colors['Mcharm'][1])
   hMC["Ncharm"].SetMarkerStyle(colors['Mcharm'][0])
   hMC["Ndy"].Draw()
   hMC["Ncharm"].Draw('same')
   myPrint(hMC['dummy'],'DrellYanAndCharm_shape')

   hMC['lowMass0.0']= hMC['lowMass0.0'+fitMethod]
   hMC["hDY0.0"]    = hMC['hDY0.0'+fitMethod]
   hMC["Charm0.0"]  = hMC['Charm0.0'+fitMethod]
   ut.bookCanvas(hMC,'dataAndMC2',' ',1200,900,1,1)
   hMC['dataAndMC2'].cd(1)
   npar = 3
   gMinuit = ROOT.TMinuit(npar)
   gMinuit.SetMaxIterations(100000)
   gMinuit.SetFCN(fcn)
   vstart  = array('d',[1.0,2.0,0.0])
   step    = array('d',[0.1,0.1,0.1])
   ierflg  = ctypes.c_int()
   name = [ROOT.TString("mbias"),ROOT.TString("DY"),ROOT.TString("Charm")]
   for i in range(npar): gMinuit.DefineParameter(i, name[i].Data(), vstart[i], step[i], 0.,10000.)
   #gMinuit.FixParameter(0)
   #gMinuit.FixParameter(1)
   gMinuit.FixParameter(2)
   gMinuit.mnexcm("SIMPLEX",vstart,npar,ierflg)
   gMinuit.Migrad()
   pars = {}
   for i in range(3):
     pars[i]=[ctypes.c_double(),ctypes.c_double()]
     gMinuit.GetParameter(i,pars[i][0],pars[i][1])
   print "RESULT:",pars[0][0].value, pars[1][0].value, pars[2][0].value
   norm = dataStats/MCStats['10GeV']
   hMC['test'] = hMC['lowMass0.0'+fitMethod].Clone('test')
   hMC['test'].Reset()
   hMC['test'].Add(hMC['lowMass0.0'+fitMethod],norm*pars[0][0].value)
   hMC['test'].SetLineColor(ROOT.kGray+1)
   hMC['test'].SetMarkerStyle(23)
   hMC['test'].SetMarkerColor(ROOT.kGray+1)
   hMC['test'].SetMinimum(0)
   hMC['testDY'] = hMC["hDY0.0"+fitMethod].Clone('testDY')
   hMC['testDY'].Scale(norm*DYfactor*pars[1][0].value)
   hMC['testDY'].SetLineColor(ROOT.kOrange-7)
   hMC['testDY'].SetMarkerColor(ROOT.kOrange-7)
   hMC['testDY'].SetMarkerStyle(4)
   hMC['testCharm'] = hMC["Charm0.0"+fitMethod].Clone('testCharm')
   hMC['testCharm'].Scale(norm*Charmfactor*pars[2][0].value)
   hMC['testCharm'].SetLineColor(ROOT.kGreen-7)
   hMC['testCharm'].SetMarkerColor(ROOT.kGreen-7)
   hMC['testCharm'].SetMarkerStyle(27)
   hMC['test'].Add(hMC["testDY"])
   hMC['test'].Add(hMC["testCharm"])

   hMC['test'].Draw()
   hMC['testDY'].Draw('same')
   hMC['testCharm'].Draw('same')
   hData['M'].Draw('same')
   hMC['lowMass'].DrawF1(0.5,8.,'same')  # low mass part of signal fit
   hMC[Fsignal].DrawF1(0.5,8.,'same')   # signal part of signal fit
   T = ROOT.TLatex()
   mLow  = 0.5
   mHigh = 5.0 
   if fitMethod=='G':  tmp = norm_myGauss(CB,im='',sLow=2.0,sHigh=mHigh,bLow=mLow,bHigh=mHigh)
   if fitMethod=='B':  tmp = norm_twoBukin(CB,im='',sLow=2.0,sHigh=mHigh,bLow=mLow,bHigh=mHigh)
   if fitMethod=='CB': tmp = norm_twoCB(hData["fitResult"],im='',sLow=2.0,sHigh=mHigh,bLow=mLow,bHigh=mHigh)
   T.SetTextSize(0.04)
   T.DrawLatex(2.5,1700.,"mbias scaled by     %5.2F #pm %5.2F "%(pars[0][0].value,pars[0][1].value))
   if pars[2][0].value != 0: 
        T.DrawLatex(2.5,1200.,"Charm scaled by %5.2F #pm %5.2F "%(pars[2][0].value,pars[2][0].value))
        T.DrawLatex(2.5,1450.,"Drell-Yan scaled by %5.2F #pm %5.2F "%(pars[1][0].value,pars[1][1].value))
   else:
        rCharm = 0.35
        T.DrawLatex(2.5,1450.,"Charm + Drell-Yan scaled by %5.2F #pm %5.2F "%(pars[1][0].value,pars[1][1].value))
   T.SetTextSize(0.05)
   T.DrawLatex(1.73,2242.,"N_{low\, mass}:%5.1F\pm%5.1F"%(tmp[0][0],tmp[0][1])) 
   T.DrawLatex(2.5,2500.,"N_{J/\Psi}:  %5.1F\pm%5.1F"%(tmp[1][0],tmp[1][1]))
   oname = 'DrellYan-data-And-MC-adjusted'+fitMethod
   myPrint(hMC['dataAndMC2'],oname)
   for x in hData['FitYield']: print hData['FitYield'][x]
   sumData = hData['M'].Integral(hData['M'].FindBin(mLow),hData['M'].FindBin(mHigh))
   sumFit = tmp[0][0]+tmp[1][0]
   print "cross check lowmass=%5.1F  signal=%5.1F  sum=%5.1F  delta=%4.2F%%"%(tmp[0][0],tmp[1][0],sumFit,(sumData-sumFit)/sumData*100)

def fcn(npar, gin, f, par, iflag):
#calculate chisquare
    bw = hMC['lowMass0.0'].GetBinWidth(1)
    chisq  = 0
    # print "fcn called",par[0],par[1],par[2]
    norm = dataStats/MCStats['10GeV']
    for n in range(12,100):
       if hData['M'].GetBinContent(n)<250. : continue
       x1 = hMC['lowMass0.0'].GetBinLowEdge(n)
       x2 = x1+bw
       S     = hMC['signal'].Integral(x1,x2)/bw
       LM    = par[0]*hMC['lowMass0.0'].GetBinContent(n)
       DY    = par[1]*DYfactor*hMC["hDY0.0"].GetBinContent(n)
       Charm = par[2]*Charmfactor*hMC["Charm0.0"].GetBinContent(n)
       # print "?",n,S,norm*abs(LM), norm*abs(DY),norm*abs(Charm)
       N = S + norm*(abs(LM) + abs(DY) + abs(Charm))
       dN = hData['M'].GetBinContent(n)-N
       errSq = hData['M'].GetBinError(n)**2+norm**2*(\
           (par[0]*hMC['lowMass0.0'].GetBinError(n))**2+\
           (par[1]*DYfactor*hMC["hDY0.0"].GetBinError(n))**2+\
           (par[2]*Charmfactor*hMC["Charm0.0"].GetBinError(n))**2)
       chisq += (dN)**2/errSq
    f[0] = chisq
    # print "return",f[0],par[0],par[1],par[2]
    return
def gausAnd3Bukins(x,par):
# 3 bukin for low mass, charm, DY and gaus for signal
  par1 = hMC['originalfun-LM'].GetParameter(1)*par[1]
  hMC['fun-LM'].SetParameter(1,par1)
  Nlow = hMC['fun-LM'].Eval(x[0])
  par2 = hMC['originalfun-DY'].GetParameter(1)*par[2]
  hMC['fun-DY'].SetParameter(1,par2)
  NDY  = hMC['fun-DY'].Eval(x[0])
  par3 = hMC['originalfun-Charm'].GetParameter(1)*par[3]
  hMC['fun-Charm'].SetParameter(1,par3)
  NCharm = hMC['fun-Charm'].Eval(x[0])
  fGlobal['gausN'].SetParameter(0,par[4]*par[0])
  fGlobal['gausN'].SetParameter(1,par[5])
  fGlobal['gausN'].SetParameter(2,par[6])
  Nhigh = fGlobal['gausN'].Eval(x[0])
  Nback = abs(par[7]+par[8]*x[0])
  N2S = 0
  fGlobal['gausN'].SetParameter(1,par[5]+3.6871 - 3.0969)
  if par[9] > 0:
     fGlobal['gausN'].SetParameter(0,par[9]*par[0])
     N2S = abs(fGlobal['gausN'].Eval(x[0]))
  elif par[9] < -999:
     # fix psi2s to NA50 Ag, 1.6% of 1S
     fGlobal['gausN'].SetParameter(0,0.016*par[4]*par[0])
     N2S = abs(fGlobal['gausN'].Eval(x[0]))
  if par[10]==1: return Nhigh
  if par[10]==2: return Nlow
  if par[10]==3: return Nback
  if par[10]==4: return N2S
  if par[10]==5: return NDY
  if par[10]==6: return NCharm
  return Nlow+Nback+N2S+Nhigh+NDY+NCharm
def test3Bukins(fitMethod='G'):
# to run after study Drell Yan
   params,funTemplate = getFitDictionary(fitMethod)
   norm = dataStats/MCStats['10GeV']
   hMC['dummy'].cd()
   hMC['fit-test'] = hMC['test'].Clone('fit-test')
   fun = hMC['lowMass2.0'].GetListOfFunctions()[0]
   fun.FixParameter(10,0)
   fun.FixParameter(11,0)
   hMC['testCharm'] = hMC["Charm0.0"].Clone('testCharm')
   hMC['testCharm'].Scale(norm*Charmfactor)
   rc = hMC['testCharm'].Fit(fun,'SL','',0.5,8.)
   fitResult = rc.Get()
   fname = 'fun-Charm'
   hMC[fname] = ROOT.TF1(fname,funTemplate['F'],0,10,funTemplate['N'])
   for j in range(funTemplate['N']):
       hMC[fname].FixParameter(j,fitResult.Parameter(j))
       hMC[fname].SetParName(j,fitResult.ParName(j))
   hMC['original'+fname]=hMC[fname].Clone('original'+fname)
   hMC[fname].ReleaseParameter(params['signalLow'])
   hMC['testDY'] = hMC["hDY0.0"].Clone('testDY')
   hMC['testDY'].Scale(norm*DYfactor)
   rc = hMC['testDY'].Fit(fun,'SL','',0.5,8.)
   fitResult = rc.Get()
   fname = 'fun-DY'
   hMC[fname] = ROOT.TF1(fname,funTemplate['F'],0,10,funTemplate['N'])
   for j in range(funTemplate['N']):
       hMC[fname].FixParameter(j,fitResult.Parameter(j))
       hMC[fname].SetParName(j,fitResult.ParName(j))
   hMC['original'+fname]=hMC[fname].Clone('original'+fname)
   hMC[fname].ReleaseParameter(params['signalLow'])
   hMC['testLM'] = hMC['lowMass0.0'].Clone('testLM')
   hMC['testLM'].Scale(norm)
   fun.ReleaseParameter(10)
   fun.SetParLimits(10,0,1000)
   rc = hMC['testLM'].Fit(fun,'SL','',0.5,8.)
   fitResult = rc.Get()
   fname = 'fun-LM'
   hMC[fname] = ROOT.TF1(fname,funTemplate['F'],0,10,funTemplate['N'])
   for j in range(funTemplate['N']):
       hMC[fname].FixParameter(j,fitResult.Parameter(j))
       hMC[fname].SetParName(j,fitResult.ParName(j))
   hMC['original'+fname]=hMC[fname].Clone('original'+fname)
   hMC[fname].ReleaseParameter(params['signalLow'])

   F = ROOT.TF1('3B1G',gausAnd3Bukins,0,10,11)
   F.FixParameter(0,bw)
   F.SetParName(0,'binwidth')
   F.SetParName(1,'low mass')
   F.SetParLimits(1,0.,1E9)
   F.SetParName(2,'Drell Yan')
   F.SetParLimits(2,0.,1E9)
   F.SetParName(3,'charm')
   F.SetParLimits(3,0.,1E9)
   F.SetParName(4,'J/psi')
   F.SetParName(5,'mass')
   F.SetParName(6,'sigma')
   F.SetParName(7,'p0')
   F.SetParName(8,'p1')
   F.SetParName(9,'psi(2S)')
   F.FixParameter(9,-1.)
   F.SetParName(10,'switch')
   F.FixParameter(10,0)
   F.SetParameter(1,1.)
   F.SetParameter(2,1.)
   F.SetParameter(3,1.)
   F.SetParameter(4,hMC['signal'].GetParameter(7))
   F.SetParameter(5,hMC['signal'].GetParameter(8))
   F.SetParameter(6,hMC['signal'].GetParameter(9))
   F.FixParameter(6,hMC['signal'].GetParameter(9))
   rc = hData['M'].Fit(F,'SL','',0.5,8.)

def PDFs(pMin=20.,pMax=300.,ptCut=1.0,muID=2,BDTCut=False,inYrange=True):
   X = {'1':ROOT.kBlack,'2':ROOT.kBlue+2,'3':ROOT.kAzure+2,'4':ROOT.kMagenta+2,'8':ROOT.kPink+8,'13':ROOT.kRed+1,'17':ROOT.kGreen-2}
   S = {'1':33,         '2':43,          '3':23,           '4':22,             '8':39,          '13':29,         '17':34}
   mMax=0
   for n in ['p','n']:
      ut.bookHist(hMC,'xsecNA50_'+n,'xsec',100,0.0,100.)
      ut.bookHist(hMC,'xsecM_'+n,'xsec',100,0.0,1000.)
   for x in X:
       p='pdf'+x
       hMC[p]={}
       ut.readHists(hMC[p],'/eos/experiment/ship/user/truf/muflux-sim/pythia8/pythia8_PDFpset'+x+'_Emin0.5.root')
       for n in ['p','n']:
# xsec
          Nuu = hMC[p]['M_'+n].GetEntries()
          if hMC[p]['xsec_'+n].GetBinContent(2)<1:
                Npot = 10**(int(ROOT.TMath.Log10(Nuu)))*10 # npot not stored
          else: Npot = hMC[p]['xsec_'+n].GetBinContent(2) 
          fudgefac = Nuu/Npot
          totalX = hMC[p]['xsec_'+n].GetBinContent(1) # mbar
          binWidth = hMC[p]['M_'+n].GetXaxis().GetBinWidth(1)
#
          h['y'+x+'_'+n] = hMC[p]['M_'+n].ProjectionY('y'+x+'_'+n)
          h['y'+x+'_'+n].Scale(1./h['y'+x+'_'+n].GetSumOfWeights())
          h['y'+x+'_'+n].GetYaxis().SetTitle("arbitrary units")
          h['y'+x+'_'+n].SetLineColor(X[x])
          h['y'+x+'_'+n].SetMinimum(0)
          h['y'+x+'_'+n].SetMarkerStyle(S[x])
          h['y'+x+'_'+n].SetMarkerColor(X[x])
          h['y'+x+'_'+n].SetStats(0)
          yaxis = h['y'+x+'_'+n].GetXaxis()
          if inYrange:
            ymin = yaxis.FindBin(0.3)
            ymax = yaxis.FindBin(2.0)
          else:
            ymin = 1
            ymax = yaxis.GetNbins()
          mProj = 'M'+x+'_'+n
          h[mProj] = hMC[p]['M_'+n].ProjectionX(mProj,ymin,ymax)
          binWidth = h[mProj].GetBinWidth(1)
          h[mProj].Scale(totalX/Npot*1E9)
          h[mProj].GetYaxis().SetTitle("pbarn/"+str(int(binWidth*1000.))+"MeV/c^{2}")
          h[mProj].SetLineColor(X[x])
          h[mProj].SetMarkerStyle(S[x])
          h[mProj].SetMarkerColor(X[x])
          h[mProj].GetXaxis().SetRangeUser(0.,5.)
          h[mProj].SetStats(0)
          if h[mProj].GetMaximum()>mMax: mMax=h[mProj].GetMaximum()
          xx = h[mProj].Integral(h[mProj].FindBin(2.9),h[mProj].FindBin(4.5))
          rc = hMC['xsecM_'+n].Fill(xx)

# NA50 range
          xax = hMC[p]['cosCSJpsi_'+n].GetXaxis()
          yax = hMC[p]['cosCSJpsi_'+n].GetYaxis()
          Mmin = xax.FindBin(-0.5)
          Mmax = xax.FindBin(0.5)
          Ymin = yax.FindBin(-0.425)
          Ymax = yax.FindBin(0.575)
          tmp  = hMC[p]['cosCSJpsi_'+n].ProjectionX('M',Ymin,Ymax)
          xNA50 = tmp.Integral(Mmin,Mmax)/Npot
          xx = totalX*xNA50*1E9
          rc = hMC['xsecNA50_'+n].Fill(xx)
          print "%s %s %5.2F nb   %5.2F pb "%(x,n,totalX*1E6*fudgefac,totalX*xNA50*1E9)
   for n in ['p','n']:
       print "average xsec in NA50 range for p on %s: (%5.2F +/- %5.2F)pb"%(n,hMC['xsecNA50_'+n].GetMean(),hMC['xsecNA50_'+n].GetRMS())
       print "average xsec in NA50 mass range for p on %s: (%5.2F +/- %5.2F)pb"%(n,hMC['xsecM_'+n].GetMean(),hMC['xsecM_'+n].GetRMS())
   ut.bookCanvas(h,'yPDF','yPDF',1800,1200,2,2)
   j=1
   for c in ['M','y']:
    for n in ['p','n']:
      tc = h['yPDF'].cd(j)
      if c=='M': 
          tc.SetLogy(1)
          h[c+'1_'+n].SetMaximum(mMax*1.2)
      h[c+'1_'+n].Draw()
      h['L'+c+n]=ROOT.TLegend(0.14,0.17,0.46,0.41)
      xKeys = []
      for x in X: xKeys.append(int(x)) 
      xKeys.sort()
      for y in xKeys:
        x=str(y)
        h[c+x+'_'+n].Draw('same')
        rc = h['L'+c+n].AddEntry(h[c+x+'_'+n],n+' PDF set '+x,'PL')
      h['L'+c+n].Draw('same')
      j+=1
   myPrint(h['yPDF'],'PDFcomparison')
   yaxis = hMC['pdf4']['M_p'].GetYaxis()
   ymin = yaxis.FindBin(0.2)
   ymax = yaxis.FindBin(2.0)
   A = hMC['pdf4']['M_p'].ProjectionX('4M',ymin,ymax)
   A.Add(hMC['pdf4']['M_n'].ProjectionX('4Mn',ymin,ymax))
   A.Scale(1./A.GetSumOfWeights())
   B = hMC['pdf13']['M_p'].ProjectionX('13M',ymin,ymax)
   B.Add(hMC['pdf13']['M_n'].ProjectionX('13Mn',ymin,ymax))
   B.Scale(1./B.GetSumOfWeights())
   hMC['scalePDFM']=A.Clone('scalePDFM')
   hMC['scalePDFM'].Divide(B)
   A = hMC['pdf4']['M_p'].Project3D('xy')
   A.Add(hMC['pdf4']['M_n'].Project3D('xy'))
   A.Scale(1./A.GetSumOfWeights())
   A.SetName('4xy')
   B = hMC['pdf13']['M_p'].Project3D('xy')
   B.Add(hMC['pdf13']['M_n'].Project3D('xy'))
   B.Scale(1./B.GetSumOfWeights())
   B.SetName('13xy')
   hMC['scalePDFMY']=A.Clone('scalePDFMY')
   hMC['scalePDFMY'].Divide(B)
#
   ut.bookHist(hMC, 'MDY',       ' N J/#psi ;',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
   ut.bookHist(hMC, 'trueMDY',   ' N J/#psi ;',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
   ut.bookHist(hMC, 'MDYscaled', ' N J/#psi ;',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2],100,0.,5.)
   ut.bookHist(hMC, 'MDYresol', ' N J/#psi ;',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2],100,-2.,2.)
   y_beam = yBeam()
   for nt in hMC['DY']:
       if abs(nt.p1x-nt.p2x)<0.001: continue    # clone
       if not nt.mult<3: continue
       if not max(nt.pt1cor,nt.pt2cor)>ptCut: continue
       if not nt.chi21*nt.chi22<0: continue
       if not max(abs(nt.chi21),abs(nt.chi22))<0.9: continue
       if not min(nt.p1,nt.p2)>pMin: continue
       if not max(nt.p1,nt.p2)<pMax: continue
       if not abs(nt.cosCScor)<0.5: continue
       nenner = ROOT.TMath.Sqrt(nt.pcor*nt.pcor+3.0969*3.0969)+ROOT.TMath.Sqrt(nt.pcor*nt.pcor-nt.ptcor*nt.ptcor)
       zahler = ROOT.TMath.Sqrt(nt.pcor*nt.pcor+3.0969*3.0969)-ROOT.TMath.Sqrt(nt.pcor*nt.pcor-nt.ptcor*nt.ptcor)
       y = 0.5*ROOT.TMath.Log(nenner/zahler)-y_beam
       if y<0.2 or y>2.0: continue
       if muID==2:
          if nt.muID1!=111 or nt.muID2!=111 : continue
       elif muID==1:
          if nt.muID1!=111 and nt.muID2!=111 : continue
       else:
          print "this muonID is not supported",muID
          1/0
       rc = hMC['MDY'].Fill(nt.mcor)
       P1 = ROOT.Math.PxPyPzMVector(nt.p1x,nt.p1y,nt.p1z,muonMass)
       P2 = ROOT.Math.PxPyPzMVector(nt.p2x,nt.p2y,nt.p2z,muonMass)
       L = P1+P2
       m = L.M()
       if m<0.49: continue
       rc = hMC['MDYresol'].Fill(nt.mcor,nt.mcor-m)
       ycm = L.Rapidity()-y_beam
       rc = hMC['trueMDY'].Fill(m)
       mbin = hMC['scalePDFMY'].GetXaxis().FindBin(m)
       ybin = hMC['scalePDFMY'].GetYaxis().FindBin(ycm)
       w    = hMC['scalePDFMY'].GetBinContent(ybin,mbin)
       if w<1E-6: w=1
       rc   = hMC['MDYscaled'].Fill(nt.mcor,w,w)

def AnalysisNote_OppositeSign(pMin=20.,pMax=300.,ptCut=1.0,muID=2,BDTCut=False,DYxsec=1.,weighted=False):
   if not hMC.has_key('DY'):loadNtuples()
   ut.bookHist(hMC, 'M',   ' N J/#psi ;',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
   ut.bookHist(hMC, 'MSS', ' N J/#psi ;',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
   ut.bookHist(hMC, 'MOS', ' N J/#psi ;',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
   ROOT.gROOT.cd()
   Ndata = hData['f'].nt.Draw('mcor>>M','chi21*chi22<0')
   mu = Ndata/(324.75E9/710.)
   print "max pile up <", mu/2.
   theCutOS = theJpsiCut('mcor',False,ptCut,pMin,pMax,muID,BDTCut,sameSign=False)
   theCutSS = theJpsiCut('mcor',False,ptCut,pMin,pMax,muID,BDTCut,sameSign=True)
   NsameSign = hData['f'].nt.Draw('mcor>>M',theCutSS)
   hData['MsameSign']=hMC['M'].Clone('MsameSign')
   NoppSign  = hData['f'].nt.Draw('mcor>>M',theCutOS)
   hData['MoppoSign']=hMC['M'].Clone('MoppoSign')
   NsameSignMC = hMC['10GeV'].Draw('mcor>>M',theCutSS)
   NoppSignMC =  hMC['10GeV'].Draw('mcor>>M',theCutOS)
   hMC['MDrell Yan']=hMC['M'].Clone('MDrell Yan')
   NDY = hMC['DY'].Draw('mcor>>MDrell Yan',theCutOS)
   hMC['Mcharm']=hMC['M'].Clone('Mcharm')
   NCharm2 = hMC['Charm2'].Draw('mcor>>Mcharm',theCutOS)
   print "same sign rate, Data:",NsameSign/float(NsameSign+NoppSign)," MC:",NsameSignMC/float(NsameSignMC+NoppSignMC)
   MCorigin = {'ss':{},'os':{}}
   tchannel =            {1:"Decay",
                          2:"Hadronic inelastic",
                          3:"Gamma conversion",
                          4:"Positron annihilation",
                          5:"charm",
                          6:"beauty",
                          7:"Di-muon P8",
                          8:"Photo nuclear interaction",
                          9:"Decay mixed",
                         10:"clone",
                         11:"Drell Yan",
                         12:"Photon collision",  # "prompt photon"
                         13:"Prompt quark",
                         98:"no muon",
                         99:"invalid"}
   for nt in hMC['10GeV']:
       if min(nt.p1cor,nt.p2cor)<pMin: continue
       if max(nt.p1cor,nt.p2cor)>pMax: continue
       if max(nt.pt1cor,nt.pt2cor)<ptCut: continue
       if abs(nt.chi21)>0.9 or abs(nt.chi22)>0.9: continue
       if nt.muID1!=111 or nt.muID2!=111 : continue
       if nt.procID2 in [5,6] or nt.procID in [5,6]: continue #handled separately
       c='os'
       if nt.chi21*nt.chi22>0: c = 'ss'
       if c=='ss': rc = hMC['MSS'].Fill(nt.mcor)
       else:  rc = hMC['MOS'].Fill(nt.mcor)
       if nt.procID2 in [3,4,5,6,8,10,12,13]: key = tchannel[nt.procID2]
       if nt.procID2 == 7:
           key = 'mixed sources'
           pid = abs(int(nt.Jpsi))
           if pid>1:
             pname = PDG.GetParticle(pid).GetName()
             if pname in ['omega','rho0','J/psi','phi',"eta'","eta","psi'"]:
                  key = pname+' primary'
             else:
                print pname
       if nt.procID2 == 1 or nt.procID2 == 2:
             key = 'low mass secondary'
       if nt.procID2 == 9 or nt.procID2 == 98 or nt.procID2 == 99 :
             key = 'mixed sources'
       hname = 'M'+key
       if not MCorigin[c].has_key(key):
            MCorigin[c][key]=0
            if c=='os':
              hMC[hname]=hMC['M'].Clone(hname)
              hMC[hname].Reset()
       MCorigin[c][key]+=1
       if c=='os': rc = hMC[hname].Fill(nt.mcor)
   # drell yan, 49*10000 events simulated. Cross section total = 69nb into mumum
   # Mo inelastic cross section 10.5mb
   # 10GeV MC = 66.02E9 pot
   # scale factor for 10GeV stats = 66.02E9/(49*20E3+2*49*10E3-20E3) * 69E-6/10.5
   if weighted:
     if not hMC.has_key('DY'): loadNtuples()
     PDFs(pMin,pMax,ptCut,muID,BDTCut)
     hMC["MDrell Yan"] = hMC['MDYscaled'].ProjectionX('MDrell Yan')
     NDY = hMC['MDrell Yan'].GetSumOfWeights()
   MCorigin['os']['Drell Yan'] = NDY * DYfactor * DYxsec
   hMC['MDrell Yan'].Scale(DYfactor)
   hMC['MOS'].Add(hMC['MDrell Yan'])
   MCorigin['os']['charm'] = NCharm2 * Charmfactor
   hMC['Mcharm'].Scale(Charmfactor)
   hMC['MOS'].Add(hMC['Mcharm'])
   hMC['sorted_list'] = sorted(MCorigin['os'].items(), key=operator.itemgetter(1),reverse=True)
   sorted_list = hMC['sorted_list']
   for s in sorted_list:
      print "%25s  %5.3G"%(s[0],1.E6*s[1]/MCStats['10GeV'])
# same sign
   print "stats for same sign"
   xsorted_list = sorted(MCorigin['ss'].items(), key=operator.itemgetter(1),reverse=True)
   for s in xsorted_list:
      print "%25s  %5.3G"%(s[0],1.E6*s[1]/MCStats['10GeV'])
   ut.bookCanvas(hMC,'TM','',1600,900,1,1)
   colors = {}
   colors['MDrell Yan']      =         [24,ROOT.kCyan,'Drell Yan']
   colors['MJ/psi primary'] =          [33,ROOT.kRed,'J/#{Psi} primary']
   colors['Momega primary'] =          [22,ROOT.kGreen,'#{omega} primary']
   colors['Mrho0 primary'] =           [23,ROOT.kGreen+2,'#{rho^0} primary']
   colors['Mlow mass secondary'] =     [25,ROOT.kBlue,'low mass secondary']
   colors['Mlow mass resonances'] =    [25,ROOT.kBlue,'low mass resonances']
   colors["Mphi primary"] =            [21,ROOT.kGreen-2,'#{phi} primary']
   colors['MGamma conversion'] =       [26,ROOT.kTeal-5,'#{gamma} conversion']
   colors["Meta' primary"]      =      [29,ROOT.kGreen-10,"#{eta'} primary"]
   colors["Meta primary"] =            [33,ROOT.kGreen-3,'#{eta} primary']
   colors['MPhoton collision'] =       [30,ROOT.kOrange,'Photon collision']
   colors['MPrompt quark']     =       [30,ROOT.kOrange+2,'Prompt quark']
   colors["Mpsi' primary"] =           [20,ROOT.kMagenta,"#{psi'} primary"]
   colors['Mcharm'] =                  [27,ROOT.kRed+3,'charm']
   colors['Mbeauty'] =                 [28,ROOT.kRed-7,'beauty']
   colors['MPositron annihilation'] =  [31,ROOT.kCyan-2,'Positron annihilation']
   colors['MPhoto nuclear interaction'] = [31,ROOT.kCyan-2,'Photo nuclear interaction']
   colors['Mnuclear'] =                [31,ROOT.kCyan-2,'nuclear interaction']
   colors['Mothers'] =                 [49,ROOT.kGray+1,'others']
   colors['Munknown'] =                [49,ROOT.kGray+2,'unknown']
   colors['Mclone'] =                  [49,ROOT.kBlue-8,'clone']
   colors['Mmixed sources'] =          [49,ROOT.kCyan-5,'mixed sources']
   colors['MSS'] =                     [20,ROOT.kRed,'MSS']
   colors['MOS'] =                     [24,ROOT.kBlue,'MOS']
   for x in colors:
       if not hMC.has_key(x): continue
       hMC[x].SetStats(0)
       hMC[x].SetTitle(';GeV/c^{2};N/'+str(int(hMC['MOS'].GetBinWidth(1)*1000))+'MeV/c^{2} ' )
       hMC[x].SetMarkerStyle(colors[x][0])
       hMC[x].SetMarkerColor(colors[x][1])
       hMC[x].SetLineColor(colors[x][1])
       hMC[x].GetXaxis().SetRangeUser(0.2,6.)
#  
   tc = hMC['TM'].cd()
   tc.SetLogy(1)
   d = {'MsameSign':[20,ROOT.kRed],'MoppoSign':[24,ROOT.kBlue]}
   for x in d:
       hData[x].SetStats(0)
       hData[x].SetTitle(';GeV/c^{2};N/'+str(int(hMC['MOS'].GetBinWidth(1)*1000))+'MeV/c^{2} ' )
       hData[x].SetMarkerStyle(d[x][0])
       hData[x].SetMarkerColor(d[x][1])
       hData[x].SetLineColor(d[x][1])
       hData[x].GetXaxis().SetRangeUser(0.2,6.)
   hData['MoppoSign'].Draw('p')
   hData['MoppoSign'].Draw('hsame')
   hData['MsameSign'].Draw('histsame')
   hData['MsameSign'].Draw('psame')
   hData['LOSSS']=ROOT.TLegend(0.64,0.67,0.88,0.78)
   rc = hData['LOSSS'].AddEntry(hData['MoppoSign'],'opposite sign','PL')
   rc = hData['LOSSS'].AddEntry(hData['MsameSign'],'same sign','PL')
   hData['LOSSS'].Draw('same')
   hData['TOSSS'] = ROOT.TLatex()
   hData['TOSSS'].DrawLatexNDC(0.4,0.8,"Data")
   myPrint(hMC['TM'],'Fig-OppAndSameSign')
   hMC['MOS'].Draw('p')
   hMC['MOS'].Draw('hsame')
   hMC['MSS'].Draw('histsame')
   hMC['MSS'].Draw('psame')
   hMC['LOSSS']=ROOT.TLegend(0.64,0.67,0.88,0.78)
   rc = hMC['LOSSS'].AddEntry(hMC['MOS'],'opposite sign','PL')
   rc = hMC['LOSSS'].AddEntry(hMC['MSS'],'same sign','PL')
   hMC['LOSSS'].Draw('same')
   hMC['TOSSS'] = ROOT.TLatex()
   hMC['TOSSS'].DrawLatexNDC(0.4,0.8,"Simulation")
   myPrint(hMC['TM'],'Fig-OppAndSameSignMC')
   hMC['MOS'].SetMinimum(3)
   hMC['MOS'].Draw('p')
   hMC['MOS'].Draw('hsame')
   hMC['LSOU']=ROOT.TLegend(0.67,0.43,0.85,0.85)
   rc = hMC['LSOU'].AddEntry(hMC['MOS'],'All opposite sign','PL')
   for y in sorted_list:
       x='M'+y[0]
       if not hMC.has_key(x): continue
       if x in ['MSS','MOS']: continue
       hMC[x].Draw('hsame')
       hMC[x].Draw('psame')
       rc = hMC['LSOU'].AddEntry(hMC[x],colors[x][2],'PL')
   hMC['LSOU'].Draw('same')
   tag = 'muID'+str(muID)+str(ptCut)+'_'+str(pMin)
   myPrint(hMC['TM'],'Fig-OppSignSources_'+tag)
# simplified version, group categories
   ut.bookCanvas(hMC,'TM2','',1600,900,1,1)
   tc = hMC['TM2'].cd()
   tc.SetLogy(1)
   simpleList = ['Mlow mass resonances','MDrell Yan','MJ/psi primary','Mcharm',"Mpsi' primary","Mnuclear","Mmixed sources"]
   hMC['Mlow mass resonances'] = hMC['Momega primary'].Clone('Mlow mass resonances')
   hMC['Mlow mass resonances'].Add(hMC['Mrho0 primary'])
   hMC['Mlow mass resonances'].Add(hMC['Mlow mass secondary'])
   hMC['Mlow mass resonances'].Add(hMC['Mphi primary'])
   hMC['Mlow mass resonances'].Add(hMC["Meta' primary"])
   hMC['Mlow mass resonances'].Add(hMC['Meta primary'])
   hMC['Mnuclear'] = hMC['MGamma conversion'].Clone('Mnuclear')
   hMC['Mnuclear'].Add(hMC['MPhoton collision'])
   hMC['Mnuclear'].Add(hMC['MPositron annihilation'])
   hMC['Mnuclear'].Add(hMC['MPhoto nuclear interaction'])
   hMC['LSOU2']=ROOT.TLegend(0.67,0.43,0.85,0.85)
   rc = hMC['LSOU2'].AddEntry(hMC['MOS'],'All opposite sign','PL')
   hMC['MOS'].Draw('p')
   hMC['MOS'].Draw('hsame')
   for x in simpleList:
       hMC[x].Draw('hsame')
       hMC[x].Draw('psame')
       rc = hMC['LSOU2'].AddEntry(hMC[x],colors[x][2],'PL')
   hMC['LSOU2'].Draw('same')
   tag = 'muID'+str(muID)+str(ptCut)+'_'+str(pMin)
   myPrint(hMC['TM2'],'Fig-OppSignSources_simple_'+tag)
   return MCorigin
def AnalysisNote_JpsiMassResolution(ptCut=1.0,pmin=20.0,muID=1,BDTCut=False):
   prods       = {'P8':hMC['JpsiP8'],'P6':hMC['Jpsi']}
   theCutcosCS = theJpsiCut('mcor',True,ptCut,pmin,300.,muID,BDTCut)
   ut.bookCanvas(hMC,'xxx','xxx',900,600,1,1)
   tc = hMC['xxx'].cd()
   ROOT.gROOT.cd()
   ut.bookHist(hMC,'M',   ' ;M_{\mu^{+}\mu^{-}} [GeV/c^{2}]'       ,100,0.,5.)
   ut.bookHist(hMC,'Mcor',' ;M_{\mu^{+}\mu^{-}} [GeV/c^{2}]'       ,100,0.,5.)
   prods['P8'].Draw('m>>M',theCutcosCS      +'&&Jpsi==443&&originZ1<-100&&p1x!=p2x')
   prods['P8'].Draw('mcor>>Mcor',theCutcosCS+'&&Jpsi==443&&originZ1<-100&&p1x!=p2x')
   rcM = hMC['M'].Fit('gaus','S')
   rcMcor = hMC['Mcor'].Fit('gaus','S')
   hMC['M'].Draw()
   tc.Update()
   stats = tc.GetPrimitive('stats')
   stats.SetOptStat(1000000001)
   stats.SetOptFit(11)
   stats.SetFitFormat('5.4g')
   stats.SetX1NDC(0.70)
   stats.SetY1NDC(0.68)
   stats.SetX2NDC(0.99)
   stats.SetY2NDC(0.85)
   hMC['Mcor'].Draw()
   tc.Update()
   stats = tc.GetPrimitive('stats')
   stats.SetOptStat(1000000001)
   stats.SetOptFit(11)
   stats.SetFitFormat('5.4g')
   stats.SetX1NDC(0.70)
   stats.SetY1NDC(0.49)
   stats.SetX2NDC(0.99)
   stats.SetY2NDC(0.66)
   hMC['M'].Draw('same')
   myPrint(hMC['xxx'],'Fig-JpsiInvMassResolution')
def AnalysisNote_JpsiKinematics():
  y_beam = yBeam()
  ROOT.gROOT.cd()
  variables = {'Ypt':'sqrt(px*px+py*py):0.5*log((E+pz)/(E-pz))-'+str(y_beam),
                 'ppt':'sqrt(px*px+py*py+pz*pz):sqrt(px*px+py*py)'}
  prods       = {'P8':hMC['JpsiP8_Primary'],'P6':hMC['JpsiCascade'],'Cascade':hMC['JpsiCascade']}
  prodsColour = {'P8':[ROOT.kRed,22],'P6':[ROOT.kMagenta,26],'Cascade':[ROOT.kMagenta,21]}
  projections = ['P','Pt','Y']
  for p in prods:
     ut.bookHist(hMC,'ppt_'+p,  'p vs pt;[GeV/c];[GeV/c]',      150,0.,10., 100,0.,401.)
     ut.bookHist(hMC,'Ypt_'+p,  'Y of Jpsi;y_{CMS}',100,-2.,2., 150,0.,10.)
  for p in prods:
     for v in variables:
       hMC[v+'_'+p].SetStats(0)
       if p=='P6': prods[p].Draw(variables[v]+'>>'+v+'_'+p,'sqrt(mpx*mpx+mpy*mpy+mpz*mpz)>399.999')
       else: prods[p].Draw(variables[v]+'>>'+v+'_'+p)
  tc = hMC['dummy'].cd()
  tc.SetLogy(0)
  for p in prods:
      hMC['Ypt_'+p].GetYaxis().SetRangeUser(0.,6.)
      hMC['Ypt_'+p].GetYaxis().SetTitle('p_{T}  [GeV/c]')
  # 2d plots
      hMC['Ypt_'+p].Draw('colz')
      myPrint(hMC['dummy'],'Fig-ypt'+p)
      hMC['Y_'+p]  = hMC['Ypt_'+p].ProjectionX('Y_'+p)
      hMC['Pt_'+p] = hMC['Ypt_'+p].ProjectionY('Pt_'+p)
      hMC['P_'+p] = hMC['ppt_'+p].ProjectionY('P_'+p)
      hMC['Y_'+p].Scale(1./hMC['Y_'+p].GetSumOfWeights())
      hMC['Pt_'+p].Scale(1./hMC['Pt_'+p].GetSumOfWeights())
      hMC['P_'+p].Scale(1./hMC['P_'+p].GetSumOfWeights())
  for p in prods:
    for v in ['P_','Pt_','Y_']:
      hMC[v+p].SetLineColor(prodsColour[p][0])
      hMC[v+p].SetMarkerColor(prodsColour[p][0])
      hMC[v+p].SetMarkerStyle(prodsColour[p][1])
      hMC[v+p].SetTitle('')
      hMC[v+p].SetStats(0)
  # 1d plots
  tc.SetLogy(1)
  for v in ['P_','Pt_','Y_']:
      hMC['l'+v]=ROOT.TLegend(0.35,0.28,0.62,0.45)
      hMC[v+'P8'].Draw()
      hMC[v+'P6'].Draw('same')
      hMC[v+'Cascade'].Draw('same')
      x = hMC['l'+v].AddEntry(hMC[v+'P8'],'Pythia8 prompt','PL')
      x.SetTextColor(prodsColour['P8'][0])
      x = hMC['l'+v].AddEntry(hMC[v+'Cascade'],'Pythia6','PL')
      x.SetTextColor(prodsColour['Cascade'][0])
      x = hMC['l'+v].AddEntry(hMC[v+'P6'],'Pythia6 prompt','PL')
      x.SetTextColor(prodsColour['P6'][0])
      hMC['l'+v].Draw('same')
      myPrint(hMC['dummy'],'Fig-JpsiKinematics-'+v.replace('_',''))
def AnalysisNote_JpsiKinematics_reloaded(case='1D'):
  if case=="2D":
    for fname in ['Fig-yptP8','Fig-yptCascade']:
         f=ROOT.TFile(fname+'.root')
         dummy=f.Get('dummy').Clone('dummy')
         dummy.Draw()
         for x in dummy.GetListOfPrimitives():
              if x.ClassName().find('TH')==0:
                  x.SetTitle(';y_{cm};p_{T}   [GeV/c]')
         dummy.Draw()
         f.Close()
         myPrint(dummy,fname)
  if case=="1D":
    u ={'P':'P  [GeV/c]','Pt':'P_{T}  [GeV/c]','Y':'y_{cm}'}
    for v in u:
         fname = "Fig-JpsiKinematics-"+v
         f=ROOT.TFile(fname+'.root')
         dummy=f.Get('dummy').Clone('dummy')
         dummy.Draw()
         for x in dummy.GetListOfPrimitives():
              if x.ClassName().find('TH')==0:
                  x.SetTitle(';'+u[v]+';#events')
         dummy.Draw()
         f.Close()
         myPrint(dummy,fname)
  if case=='CS':
    for fname in ['JpsiP8_PrimarymuonKinematicsCosCSandPtmin','JpsiCascademuonKinematicsCosCSandPtmin']:
         f=ROOT.TFile(fname+'.root')
         dummy=f.Get('dummy').Clone('dummy')
         dummy.Draw()
         for x in dummy.GetListOfPrimitives():
              if x.ClassName().find('TH')==0:
                  if fname.find('Ptmin')>0:
                     x.GetYaxis().SetTitle('#Theta_{CS}')
                  if fname.find('Theta')>0:
                     x.GetYaxis().SetTitle('#Theta_{CS}')
                     x.GetXaxis().SetTitle('#Theta_{#mu}')
                  if fname.find('InAcc')>0:
                     x.GetXaxis().SetTitle('#Theta_{CS}')
         dummy.Draw()
         f.Close()
         myPrint(dummy,fname)

def AnalysisNote_muonKinematics(JpsiOnly=True,fakeJpsi=True):
    c = ''
    if not JpsiOnly: c='lowMass-'
    if not JpsiOnly and fakeJpsi: c='lowMassJ-'
    for cosCut in ['','cosCS<0.5_']:
       f = ROOT.TFile(c+cosCut+'muonKinematics.root')
       X = f.Get(c+cosCut+'muonKinematics-p-pt-minpt')
       X.Draw()
       if cosCut!='': X.SetName(c+'cosCS0.5_muonKinematics-p-pt-minpt')
       printPads(X,ytitle='arbitrary unit')
       myCopy(c+'*.pdf')

def AnalysisNote_invMassBinsY(ptmax,pmin,fM):
   D = fM+'-'+str(ptmax)+'_'+str(pmin)
   sample = "Data"
   tmp = ROOT.TFile(D+'/'+sample+'-diMuonBins_'+fM+'_ycor1C.root')
   X = tmp.Get('bins'+fM+'_ycor1C').Clone()
   name = D+'bins'+fM+'_ycor1C'
   X.SetName(name)
   printPads(X)
   myCopy(name+'*.pdf')

def AnalysisNote_YcorResol():
   fy = ROOT.TFile('YwithConstraints.root')   
   dummy = fy.Get('dummy').Clone('dummy')
   yresol={}
   for k in range(1,4):
    yresol[k] = dummy.GetListOfPrimitives()[k]
    g = yresol[k].GetListOfFunctions()[0]
    print k,g.GetParameter(2)

def AnalysisNote_InvMassFitParameters(muID=1,ptmax=1.0,pmin=20.,fM='B',BDTCut=False,withWeight=True):
   tag = 'muID'+str(muID)+'_'+fM+'-'+str(ptmax)+'_'+str(pmin)
   if BDTCut: tag += '_BDT'
   if withWeight: tag += '_wp6'
   name = 'Fitsystematics-'+tag+'_ycor1C'
   tmp = ROOT.TFile(name+'.root')
   X = tmp.Get(name)
   X.Draw()
   printPads(X)
   myCopy(name+'*.png')
   myCopy(name+'*.pdf')
   name = 'DataWithLowMassMC-'+tag+'_ycor1C'
   tmp = ROOT.TFile(tag+'/'+name+'.root')
   X = tmp.Get("norm-MCbinsLowMass-"+fM+"_ycor1C10GeV")
   X.SetName(name)
   X.Draw()
   printPads(X)
   myCopy(name+'*.pdf')
   myCopy(name+'*.png')

def AnalysisNote_JpsiEfficiencies(muID=1,ptmax=1.0,pmin=20.,fM='B',BDTCut=False,withWeight=True):
   ut.bookCanvas(hMC,'xxx','xxx',900,600,1,1)
   tag = 'muID'+str(muID)+'_'+fM+'-'+str(ptmax)+'_'+str(pmin)
   if BDTCut: tag += '_BDT'
   if withWeight: tag += '_wp6'
   name = "JpsiEfficiencies"
   print tag+'/'+name+'.root'
   tmp = ROOT.TFile(tag+'/'+name+'.root')
   ROOT.gROOT.cd()
   X = tmp.Get('dummy')
   eff = {}
   for x in ["Y_P8prim","Y_Cascade"]:
    hMC[x+"_eff"] = X.FindObject(x+"_clone").Clone(x+"_eff")
    tc = hMC['xxx'].cd()
    hMC[x+"_eff"].Draw()
    hMC['xxx'].Update()
    g = hMC[x+"_eff"].GetPaintedGraph()
    g.GetXaxis().SetRangeUser(0.0,2.0)
   hMC["Y_P8prim_eff"].Draw()
   hMC["Y_Cascade_eff"].Draw('same')
   L = ROOT.TLegend(0.35,0.75,0.70,0.9)
   rc = L.AddEntry(hMC["Y_P8prim_eff"],"Efficiency using Pythia8",'PL')
   rc.SetTextColor(hMC["Y_P8prim_eff"].GetLineColor())
   rc = L.AddEntry(hMC["Y_Cascade_eff"],"Efficiency using Pythia6",'PL')
   rc.SetTextColor(hMC["Y_Cascade_eff"].GetLineColor())
   L.Draw('same')
   myPrint(hMC['xxx'],'Effycor'+tag)
# migration, example
   n = 30
   ut.readHists(hMC,tag+'/MC-histos.root')
   test = hMC["YM_Cascade"].ProjectionY()
   ylow = "%3.1F"%(test.GetBinLowEdge(n))
   ymax = "%3.1F"%(test.GetBinLowEdge(n)+test.GetBinWidth(n))
   p30 = hMC["YM_Cascade"].ProjectionY(ylow+" < y_{cm} reco < "+ymax,n,n)
   p30.Scale(1./p30.GetSumOfWeights())
   p30.SetTitle(";y_{cm} true; arbitrary units")
   p30.GetXaxis().SetRangeUser(0.0,2.0)
   tc = hMC['xxx'].cd()
   p30.Draw('hist')
   hMC['xxx'].Update()
   stats = tc.GetPrimitive('stats')
   stats.SetOptStat(1101)
   stats.SetX1(1.33)
   stats.SetX2(1.93)
   stats.SetY1(0.43)
   stats.SetY2(0.60)
   tc.Update()
   myPrint(hMC['xxx'],'ExampleYcorMigration')
   myCopy('Effycor'+tag+'.pdf')
   myCopy('ExampleYcorMigration'+'.pdf')
def AnalysisNote_MCcheck(ptmax,pmin,fM):
   ut.bookCanvas(hMC,'xxx','xxx',900,600,1,1)
   tc = hMC['xxx'].cd()
   D = fM+'-'+str(ptmax)+'_'+str(pmin)
   for name in ["HighMass-P8YieldsEffCorrected","HighMass-CascadeYieldsEffCorrected"]:
      tmp = ROOT.TFile(D+'/'+name+'.root')
      X = tmp.Get(name+'Canvas')
      ROOT.gROOT.cd()
      for x in X.GetListOfPrimitives():
        if x.ClassName().find('TH')==0:
           hMC[x.GetName()]=x.Clone(x.GetName())
   # Cascade
   L = ROOT.TLegend(0.3,0.16,0.66,0.31)
   z = "mc-CB_ycor1CHighMass-Jpsi-Jpsi_effAndResolCorrected_P8prim"
   hMC[z].SetTitle(';y_{cm} true;arbitrary units')
   hMC[z].Draw()
   rc = L.AddEntry(hMC[z],"Efficiency correction using Pythia8",'PL')
   rc.SetTextColor(hMC[z].GetLineColor())
   z = "mc-CB_ycor1CHighMass-Jpsi-Jpsi_effAndResolCorrected_Cascade"
   hMC[z].SetTitle(';y_{cm} true;arbitrary units')
   hMC[z].Draw('same')
   rc = L.AddEntry(hMC[z],"Efficiency correction using Pythia6",'PL')
   rc.SetTextColor(hMC[z].GetLineColor())
   z = "Y_Cascade_scaledHighMass-Cascade"
   hMC[z].Draw('same')
   rc = L.AddEntry(hMC[z],"Original distribution from Pythia6",'PL')
   rc.SetTextColor(hMC[z].GetLineColor())
   L.Draw()
   tc.Update()
   myPrint(hMC['xxx'],'MCcheckCascade')
   # P8
   L = ROOT.TLegend(0.3,0.16,0.66,0.31)
   z = "mc-CB_ycor1CHighMass-JpsiP8-Jpsi_effAndResolCorrected_P8prim"
   hMC[z].SetTitle(';y_{cm} true;arbitrary units')
   hMC[z].Draw()
   rc = L.AddEntry(hMC[z],"Efficiency correction using Pythia8",'PL')
   rc.SetTextColor(hMC[z].GetLineColor())
   z = "mc-CB_ycor1CHighMass-JpsiP8-Jpsi_effAndResolCorrected_Cascade"
   hMC[z].SetTitle(';y_{cm} true;arbitrary units')
   hMC[z].Draw('same')
   rc = L.AddEntry(hMC[z],"Efficiency correction using Pythia6",'PL')
   rc.SetTextColor(hMC[z].GetLineColor())
   z="Y_P8prim_scaledHighMass-P8"
   hMC[z].Draw('same')
   rc = L.AddEntry(hMC[z],"Original distribution from Pythia8",'PL')
   rc.SetTextColor(hMC[z].GetLineColor())
   L.Draw()
   tc.Update()
   myPrint(hMC['xxx'],'MCcheckP8prim')
   myCopy('MCcheck*.pdf')
# what about ultimate check with 10GeV? Does not work for efficiency correction, don't know original distribution.
# but know POT. Would this work?

def AnalysisNote_JpsiKinematicsReco(ptCut=1.0,pmin=20.,pmax = 300.,BDTCut=None, muID=1,fitMethod='B',copy=False):
   tag = 'muID'+str(muID)+'_'+fitMethod+'-'+str(ptCut)+'_'+str(pmin)
   if BDTCut: tag += '_BDT'
   os.chdir(topDir)
   if not os.path.isdir(tag): os.system('mkdir '+tag)
   os.chdir(tag)
   if copy: 
        myCopy('JpsiKinematicsRec_*.pdf')
        os.chdir(topDir)
        return
   category = {}
   category['_Cascade']     = {'nt':hMC['Jpsi'],  'ntOriginal':hMC['JpsiCascade'],   'cut':'id==443',  'cutrec':'&&Jpsi==443&&originZ1<-100&&p1x!=p2x'}
   category['_P8prim']      = {'nt':hMC['JpsiP8'],'ntOriginal':hMC['JpsiP8_Primary'],'cut':'id==443',  'cutrec':'&&Jpsi==443&&originZ1<-100&&p1x!=p2x'}
   colors = {}
   colors['_Cascade']    = [ROOT.kMagenta,23,'Pythia6']
   colors['_P8prim']     = [ROOT.kRed,22,'Pythia8']
   colors['Data']        = [ROOT.kBlue,21,'Data']
#
   theCutcosCS = theJpsiCut('mcor',True,ptCut,pmin,300.,muID,BDTCut)
   theCut      = theJpsiCut('mcor',False,ptCut,pmin,300.,muID,BDTCut)
#
   ut.bookCanvas(hMC,'xxx','xxx',900,600,1,1)
   tc = hMC['xxx'].cd()
#
   y_beam = yBeam()
   ROOT.gROOT.cd()
   for z in category:
     ut.bookHist(hMC,'recP'+z,'P Jpsi '       ,100,0.,400.)
     ut.bookHist(hMC,'recPt'+z,'Pt Jpsi '     ,100,0.,10.)
     ut.bookHist(hMC,'recY'+z,'Ycm Jpsi '     ,200,-2.,2.)
     ut.bookHist(hMC,'reccosCS'+z,'cosCS Jpsi '  ,100,-1.,1.)
     ut.bookHist(hMC,'rec_ppt'+z,  'p vs pt;p_{T} [GeV/c];p [GeV/c]',      150,0.,10., 100,0.,401.)
     ut.bookHist(hMC,'rec_Ypt'+z,  'Y of Jpsi;y_{CMS};p_{T} [GeV/c]',100,-2.,2., 150,0.,10.)
     category[z]['nt'].Draw('ptcor:'+ycor1C+'-'+str(y_beam)+'>>rec_Ypt'+z,theCutcosCS+category[z]['cutrec'])
     category[z]['nt'].Draw('pcor:ptcor>>rec_ppt'+z,theCutcosCS+category[z]['cutrec'])
     category[z]['nt'].Draw('ptcor>>recPt'+z,theCutcosCS+category[z]['cutrec'])
     category[z]['nt'].Draw('pcor>>recP'+z,theCutcosCS+category[z]['cutrec'])
     category[z]['nt'].Draw(ycor1C+'-'+str(y_beam)+'>>recY'+z,theCutcosCS+category[z]['cutrec'])
     category[z]['nt'].Draw('cosCScor>>reccosCS'+z,theCut+category[z]['cutrec'])
#
   ut.readHists(hMC,'MC-histos.root')
   ut.readHists(hData,'Data-histos.root')
   cases = {}
# pt
   cases['pt'] = {'par':'ptcor','text':'p_{T}','pjmin':0.,'pjmax':5.,         'MC':'recPtXXXX','norm':[0,3.]}
# p
   cases['p'] = {'par':'pcor','text':'p','pjmin':0.,'pjmax':300.,             'MC':'recPXXXX','norm':[0,200.]}
# ycm
   cases['ycm'] = {'par':'ycor1C','text':'y_{cm}','pjmin':0.2,'pjmax':1.8,    'MC':'recYXXXX','norm':[0.5,1.5]}
# cosCS
   cases['cosCS'] = {'par':'cosCScor','text':'cosCS','pjmin':-0.8,'pjmax':0.8,'MC':'reccosCSXXXX','norm':[-0.5,0.5]}
   for x in cases:
     proj = cases[x]
     if x=='ycm':
       fY = ROOT.TFile('diMuonBins'+fitMethod+'_ycor1CSummary.root')
       hData[fitMethod+'_'+proj['par']+'-Jpsi'] = fY.dummy.FindObject(fitMethod+'_ycor1C-Jpsi').Clone(fitMethod+'_ycor1C-Jpsi')
     else:
       if x=='cosCS': twoCBYieldFit(fitMethod,proj['par'],proj['pjmin'],proj['pjmax'],proj['text'],theCut,     nBins=15,printout=1)
       else:          twoCBYieldFit(fitMethod,proj['par'],proj['pjmin'],proj['pjmax'],proj['text'],theCutcosCS,nBins=15,printout=1)
   for x in cases:
     proj = cases[x]
     X = hData[fitMethod+'_'+proj['par']+'-Jpsi']
     X.SetLineColor(colors['Data'][0])
     X.SetMarkerColor(colors['Data'][0])
     X.SetMarkerStyle(colors['Data'][1])
     X.SetStats(0)
     X.SetTitle(';'+proj['text']+';N arbitrary units')
     normD = X.Integral(X.FindBin(proj['norm'][0]),X.FindBin(proj['norm'][1]))*X.GetBinWidth(1)
     hMax = X.GetMaximum()
     for z in category:
       Y = hMC[proj['MC'].replace('XXXX',z)]
       normMC = Y.Integral(X.FindBin(proj['norm'][0]),Y.FindBin(proj['norm'][1]))*Y.GetBinWidth(1)
       if normMC == 0: 
           print "Error",Y,Y.FindBin(proj['norm'][0]),Y.FindBin(proj['norm'][1])
       Y.Scale(normD/normMC)
       Y.SetLineColor(colors[z][0])
       Y.SetMarkerColor(colors[z][0])
       Y.SetMarkerStyle(colors[z][1])
       Y.SetStats(0)
       if Y.GetMaximum()>hMax: hMax = Y.GetMaximum()
     hMC['xxx'].cd()
     hData[fitMethod+'_'+proj['par']+'-Jpsi'].SetMaximum(hMax*1.1)
     hData[fitMethod+'_'+proj['par']+'-Jpsi'].Draw()
     hMC['mc-'+fitMethod+'_'+proj['par']+'10GeV-Jpsi'].Draw('same')
     hMC['mc-'+fitMethod+'_'+proj['par']+'HighMass-JpsiP8-Jpsi'].Draw('same')
     hMC['mc-'+fitMethod+'_'+proj['par']+'HighMass-Jpsi-Jpsi'].Draw('same')
     L = ROOT.TLegend(0.6,0.6,0.85,0.70)
     rc = L.AddEntry(X,"Data",'PL')
     rc.SetTextColor(X.GetLineColor())
     for z in category:
       X = hMC[proj['MC'].replace('XXXX',z)]
       X.Draw('same')
       rc = L.AddEntry(X,colors[z][2],'PL')
       rc.SetTextColor(X.GetLineColor())
     L.Draw()
     hMC['xxx'].Update()
     myPrint(hMC['xxx'],'JpsiKinematicsRec_'+proj['par'])

def AnalysisNote_PrimVertex(case='pos'):
 ut.bookCanvas(hMC,'PV','PV',500,800,1,1)
 hMC['PV'].SetLeftMargin(0.13)
 hMC['PV'].cd()
 if case==pos:
   F = ROOT.TFile('primaryVertex.root')
   tc = F.Get('primV').Clone()
   proj = {1:'X',2:'Y',3:'Z'}
   i=0
   for pad in tc.GetListOfPrimitives():
      i+=1
      obj={}
      for o in pad.GetListOfPrimitives():
         cl = o.ClassName()
         if not obj.has_key(cl):obj[cl]=[]
         obj[cl].append(o.Clone())
      nmax = 0
      hmax = 0
      for n in range(len(obj['TH1D'])):
        tmp = ut.findMaximumAndMinimum(obj['TH1D'][n])
        obj['TH1D'][n].SetMaximum(tmp[1]*1.1)
        txt = obj['TH1D'][n].GetTitle()
        obj['TH1D'][n].SetTitle(';'+proj[i]+' [cm]; arbitrary units')
        if tmp[1]>nmax:
            nmax = tmp[1]
            hmax = n
      opt=''
      if obj['TH1D'][hmax].GetLineColor()==ROOT.kMagenta: opt='hist'
      obj['TH1D'][hmax].Draw(opt)
      for x in obj['TLatex']: 
          if i==3: x.SetX(0.32+x.GetX())
          else: x.SetX(0.03+x.GetX())
      for c in obj:
         for x in obj[c]:
           opt=''
           if c=='TH1D' and x.GetLineColor()==ROOT.kMagenta: opt='hist'
           x.Draw(opt+'same')
      myPrint(hMC['PV'],'primvx_'+proj[i])
 else:
   F = ROOT.TFile('ResStudy_origin.root')
   target = F.Get('target').Clone()
   pad = target.GetListOfPrimitives()[0]
   P6Jpsi = pad.FindObject("P6Jpsi_originXYZ_projx").Clone()
   P8Jpsi = pad.FindObject("P8Jpsi_originXYZ_projx").Clone()
   MC10Jpsi = pad.FindObject("MC10Jpsi_originXYZ_projx").Clone()
   tc = hMC['PV'].cd()
   P6Jpsi.SetTitle('; Z [cm];arbitrary units')
   P6Jpsi.GetXaxis().SetRangeUser(-400,-200)
   P6Jpsi.Draw('hist')
   P8Jpsi.Draw('histsame')
   MC10Jpsi.Draw('histsame')
   L = ROOT.TLegend(0.22,0.28,0.52,0.48)
   rc = L.AddEntry(P6Jpsi,"Pythia6 J/#psi",'PL')
   rc = L.AddEntry(P8Jpsi,"Pythia8 J/#psi",'PL')
   rc = L.AddEntry(MC10Jpsi,"Pythia8 incl",'PL')
   L.Draw()
   myPrint(hMC['PV'],'truez')
def debugCosCSfit(ptCut=1.0,pmin=20.,pmax = 300.,BDTCut=None, muID=1,im='s',sLow=2.0,sHigh=5.0,bLow=2.0,bHigh=5.0):
   os.chdir(topDir)
   fitMethods = ['B','CB']
   fitParam   = {}
   fM = {'CB':{'signal':1,'mass':2,'sigma':3},'B':{'signal':7,'mass':8,'sigma':9},'G':{'signal':0,'mass':1,'sigma':2}}
   for fitMethod in fitMethods:
     hMC['f'+fitMethod]         = ROOT.TFile('muID'+str(muID)+'_'+fitMethod+'-'+str(ptCut)+'_'+str(pmin)+'/Data-diMuonBins_'+fitMethod+'_cosCScor.root')
     hMC['fLowMass'+fitMethod]  = ROOT.TFile('muID'+str(muID)+'_'+fitMethod+'-'+str(ptCut)+'_'+str(pmin)+'/MCbinsLowMass-'+fitMethod+'_cosCScor10GeV.root')
     hMC['LowMass'+fitMethod]   = hMC['fLowMass'+fitMethod].Get('MCbinsLowMass-'+fitMethod+'_cosCScor10GeV')
     hMC['fHighMass'+fitMethod]  = ROOT.TFile('muID'+str(muID)+'_'+fitMethod+'-'+str(ptCut)+'_'+str(pmin)+'/MCbinsHighMass-'+fitMethod+'_cosCScor10GeV.root')
     hMC['HighMass'+fitMethod]   = hMC['fHighMass'+fitMethod].Get('MCbinsHighMass-'+fitMethod+'_cosCScor10GeV')
     hMC['fsum'+fitMethod]       = ROOT.TFile('muID'+str(muID)+'_'+fitMethod+'-'+str(ptCut)+'_'+str(pmin)+'/diMuonBins'+fitMethod+'_cosCScorSummary.root')
     hMC['LowMass'+fitMethod].Draw()
     hMC['HighMass'+fitMethod].Draw()
     hMC['bins'+fitMethod+'_cosCScor'] = hMC['f'+fitMethod].Get('bins'+fitMethod+'_cosCScor')
     hMC['bins'+fitMethod+'_cosCScor'].Draw()
     for x in [fitMethod+'_cosCScor-Jpsi']: 
        hMC[x] = hMC['fsum'+fitMethod].dummy.FindObject(x).Clone(x)
     hData['bins'+fitMethod+'_cosCScor']  =  hMC['f'+fitMethod].Get('bins'+fitMethod+'_cosCScor').Clone('bins'+fitMethod+'_cosCScor')
     fitParam[fitMethod] = {}
     j = 0
     keys = []
     for p in hData['bins'+fitMethod+'_cosCScor'].GetListOfPrimitives():
        hx = p.FindObject(fitMethod+'_cosCScor'+str(j))
        if not hx: break
        tmp = hx.GetTitle().split(' ')[3].split('<')
        v = "%5.2F"%(float(tmp[0]))
        if abs(float(tmp[0]))<0.0001: v='0.0'
        v+="<"+tmp[1]+"<"
        if abs(float(tmp[2]))<0.0001: v+='0.0'
        else: v+="%5.2F"%(float(tmp[2]))
        keys.append(v)
        fitParam[fitMethod][v] = {}
        fun = hx.GetFunction("Fun"+fitMethod+"_cosCScor"+str(j))
        for par in fM[fitMethod]:
         if par == "signal":
           params,funTemplate = getFitDictionary(fitMethod)
           sfun = ROOT.TF1('tmp',funTemplate['F'],0,10,funTemplate['N'])
           for i in range(funTemplate['N']): sfun.SetParameter(i,fun.GetParameter(i))
           if fitMethod=='CB': tmp = norm_twoCB(sfun,im,sLow,sHigh,bLow,bHigh)
           if fitMethod=='B':  tmp = norm_twoBukin(sfun,im,sLow,sHigh,bLow,bHigh)
           fitParam[fitMethod][v][par]= tmp[1][0]
           fitParam[fitMethod][v]['Back']= tmp[0][0]
         else: 
           fitParam[fitMethod][v][par] = fun.GetParameter(fM[fitMethod][par])
        j+=1
#
     j = 0
     for p in hMC['HighMass'+fitMethod].GetListOfPrimitives():
        hx = p.FindObject('mc-'+fitMethod+'_cosCScorHighMass-10GeV'+str(j))
        if not hx: break
        tmp = hx.GetTitle().split(' ')[3].split('<')
        v = "%5.2F"%(float(tmp[0]))
        if abs(float(tmp[0]))<0.0001: v='0.0'
        v+="<"+tmp[1]+"<"
        if abs(float(tmp[2]))<0.0001: v+='0.0'
        else: v+="%5.2F"%(float(tmp[2]))
        fun = hx.GetFunction("mc-Fun"+fitMethod+"_cosCScorHighMass-10GeV"+str(j))
        par = "MCsignal"
        params,funTemplate = getFitDictionary(fitMethod)
        sfun = ROOT.TF1('tmp',funTemplate['F'],0,10,funTemplate['N'])
        for i in range(funTemplate['N']): sfun.SetParameter(i,fun.GetParameter(i))
        if fitMethod=='CB': tmp = norm_twoCB(sfun,im,sLow,sHigh,bLow,bHigh)
        if fitMethod=='B':  tmp = norm_twoBukin(sfun,im,sLow,sHigh,bLow,bHigh)
        fitParam[fitMethod][v][par]= tmp[1][0]
        j+=1
   print "          interval    signal  B       CB    back  B       CB       mass   B     CB       sigma   B     CB"
   for k in keys:
      print "%25s: %7.2F   %7.2F   %7.2F   %7.2F   %7.2F   %7.2F   %7.2F   %7.2F  "%(k,
              fitParam['B'][k]['signal'], fitParam['CB'][k]['signal'],fitParam['B'][k]['Back'], fitParam['CB'][k]['Back'],
              fitParam['B'][k]['mass'], fitParam['CB'][k]['mass'],fitParam['B'][k]['sigma'], fitParam['CB'][k]['sigma'])
   return fitParam

def AnalysisNote_LowMassKinematicsReco(ptmax=0.0,pmin=20.,mMax=2.0,muID=1,BDTCut=False):
   trackEffFudgeFactor = 1+2*simpleEffCorMu
   MCnorm = dataStats/MCStats['10GeV'] / trackEffFudgeFactor
   category = {}
   category['_10GeV']    = {'nt':hMC['10GeV'],   'ntOriginal':None,   'cut':'id!=443&&id!=100443',  'cutrec':'&&0.25<mcor&&mcor<'+str(mMax)}
   category['Data']      = {'nt':hData['f'].nt,  'ntOriginal':None,   'cut':'id!=443&&id!=100443',  'cutrec':'&&0.25<mcor&&mcor<'+str(mMax)}
   colors = {}
   colors['_10GeV']    = [ROOT.kRed,23,'Pythia8/Geant4']
   colors['Data']      = [ROOT.kBlue,21,'Data']
   lmIds = [223,221,113,333,331]
         #omega,eta,rho0,phi,eta'  Problem: decays from resonances in Geant4 may also have proton/neutron... has mother.
   lmSel = "(Jpsi==223||Jpsi==221||Jpsi==113||Jpsi==333||Jpsi==331)"
   theCutcosCS = theJpsiCut('mcor',True, ptmax,pmin,300.,muID,BDTCut)
   theCut      = theJpsiCut('mcor',False,ptmax,pmin,300.,muID,BDTCut)
   y_beam = yBeam()
   ROOT.gROOT.cd()
   for z in category:
     ut.bookHist(hMC,'recM'+z,'M;   M [GeV/c^{2}] '       ,100,0.,5.)
     ut.bookHist(hMC,'recP'+z,'P low Mass;   p [GeV/c] '       ,100,0.,400.)
     ut.bookHist(hMC,'recPt'+z,'Pt low Mass; p_{T} [GeV/c]  '     ,100,0.,10.)
     ut.bookHist(hMC,'recY'+z,'Ycm low Mass; y_{cm} '     ,100,0.,4.)
     ut.bookHist(hMC,'reccosCS'+z,'cosCS low Mass '  ,100,-1.,1.)
     category[z]['nt'].Draw('mcor>>recM'+z,theCutcosCS)
     category[z]['nt'].Draw('ptcor>>recPt'+z,theCutcosCS+category[z]['cutrec'])
     category[z]['nt'].Draw('pcor>>recP'+z,theCutcosCS+category[z]['cutrec'])
     category[z]['nt'].Draw('ycor-'+str(y_beam)+'>>recY'+z,theCutcosCS+category[z]['cutrec'])
     category[z]['nt'].Draw('cosCScor>>reccosCS'+z,theCut+category[z]['cutrec'])
     if z!='Data':
        ut.bookHist(hMC,'trueP/Pt'+z, 'true P/Pt low Mass;   p [GeV/c];pT [GeV/c] '       ,100,0.,400.,100,0.,10.)
        ut.bookHist(hMC,'trueY/Pt'+z, 'true Ycm/Pt low Mass; y_{cm} ; p [GeV/c]'     ,100,0.,4.,100,0.,10.)
        category[z]['nt'].Draw('PtTRUE:PTRUE>>trueP/Pt'+z,theCutcosCS+category[z]['cutrec'])
        category[z]['nt'].Draw('PTRUE:(YTRUE-'+str(y_beam)+')>>trueY/Pt'+z,theCutcosCS+category[z]['cutrec'])
#
   cases = {}
# mcor
   unit = "%4.2F"%(hMC['recM'+z].GetBinWidth(1)*1000.)
   cases['m']     = {'par':'mcor' ,  'text':'M [GeV/c^{2}];N/'+unit+' MeV/c^{2} ','pjmin':0.,'pjmax':5.,               'MC':'recMXXXX','norm':[0,1.5],'log':0}
# pt 
   unit = "%4.2F"%(hMC['recPt'+z].GetBinWidth(1)*1000.)
   cases['pt']    = {'par':'ptcor',  'text':'p_{T} [GeV/c];N/'+unit+' MeV/c^{2} ','pjmin':0.,'pjmax':5.,          'MC':'recPtXXXX','norm':[0,5.],'log':1}
# p
   unit = "%4.2F"%(hMC['recPt'+z].GetBinWidth(1))
   cases['p']     = {'par':'pcor',   'text':'p [GeV/c];N/'+unit+' GeV/c^{2} ','pjmin':0.,'pjmax':300.,             'MC':'recPXXXX','norm':[0,200.],'log':1}
# ycm
   unit = "%4.2F"%(hMC['recY'+z].GetBinWidth(1))
   cases['ycm']   = {'par':'ycor','text':'y_{cm};N/'+unit,'pjmin':0.2,'pjmax':1.8,      'MC':'recYXXXX','norm':[0.5,1.5],'log':0}
# cosCS
   unit = "%4.2F"%(hMC['reccosCS'+z].GetBinWidth(1))
   cases['cosCS'] = {'par':'cosCScor','text':'cosCS;N/'+unit,'pjmin':-0.8,'pjmax':0.8,    'MC':'reccosCSXXXX','norm':[-0.5,0.5],'log':0}
   for x in cases:
     proj = cases[x]
     ut.bookCanvas(hMC,'t'+x,' ',900,600,1,1)
     tc = hMC['t'+x].cd()
     tc.SetLogy(proj['log'])
     z='Data'
     histname = proj['MC'].replace('XXXX',z)
     X = hMC[histname]
     X.SetLineColor(colors[z][0])
     X.SetMarkerColor(colors[z][0])
     X.SetMarkerStyle(colors[z][1])
     X.SetStats(0)
     X.SetTitle(';'+proj['text'])
     z='_10GeV'
     histname = proj['MC'].replace('XXXX','_10GeV')
     Y = hMC[histname]
     Y.Scale(MCnorm)
     Y.SetLineColor(colors[z][0])
     Y.SetMarkerColor(colors[z][0])
     Y.SetMarkerStyle(colors[z][1])
     Y.SetStats(0)
     max1 = ut.findMaximumAndMinimum(X)[1]
     max2 = ut.findMaximumAndMinimum(Y)[1]
     hMax = max( max1, max2 )
     if proj['log']>0: X.SetMaximum(hMax*1.5)
     else: X.SetMaximum(hMax*1.2)
     X.Draw()
     hMC['L'+x] = ROOT.TLegend(0.63,0.77,0.88,0.87)
     rc = hMC['L'+x].AddEntry(X,"Data",'PL')
     rc.SetTextColor(X.GetLineColor())
     Y.Draw('same')
     rc = hMC['L'+x].AddEntry(Y,colors[z][2],'PL')
     rc.SetTextColor(Y.GetLineColor())
     hMC['L'+x].Draw()
     hMC['t'+x].Update()
     myPrint(hMC['t'+x],'LowMassKinematicsRec_'+proj['par'])
   myCopy('LowMassKinematicsRec_*.pdf')

def AnalysisNote_InvMassAndFitFunction(ptCut=1.0,pmin=20.,BDTCut = False,muID=1,copyToFigs=True,yrange=[0.3,1.8]):
   ROOT.gROOT.cd()
   trackEffFudgeFactor = 1+2*simpleEffCorMu
   MCnorm = dataStats/MCStats['10GeV'] / trackEffFudgeFactor
   pmax      = 300.
   if BDTCut:    ptCut,pmin,pmax = 0.,0.,1000.
   theCutcosCS = theJpsiCut('mcor','True',ptCut,pmin,pmax,muID,BDTCut)
   for fitMethod in ['CB','B','G']:
     tag = fitMethod+'-'+str(ptCut)+'_'+str(pmin)
     if BDTCut: tag += '_BDT'
     tag+='_invMass'
     os.chdir(topDir)
     if not os.path.isdir(tag): os.system('mkdir '+tag)
     os.chdir(tag)
     twoCBYieldFit(fitMethod,'ycor1C',yrange[0],yrange[1],'ycm',theCutcosCS,nBins=1,printout=2)
     tc = hMC['dummy'].cd()
     samples = {'Data':hData[fitMethod+'_ycor1C0'],'10GeV':hMC['mc-'+fitMethod+'_ycor1C10GeV0'],'HighMass':hMC['mc-'+fitMethod+'_ycor1CHighMass-Jpsi0'],
                'LowMass':hMC['mc-'+fitMethod+'_ycor1CLowMass-10GeV0']}
     for sample in samples:
       samples[sample].SetTitle('')
       samples[sample].Draw()
       tc.Update()
       stats = tc.GetPrimitive('stats')
       stats.SetOptFit(10111)
       stats.SetFitFormat('5.4g')
       stats.SetX1NDC(0.68)
       stats.SetY1NDC(0.15)
       stats.SetX2NDC(0.99)
       stats.SetY2NDC(0.98)
       myPrint(hMC['dummy'],"Fig-"+sample+fitMethod)
       if copyToFigs: myCopy("Fig-"+sample+fitMethod+'.pdf')
     print "Data signal:  %s   %7.2F +/ %7.2F"%(fitMethod,hData[str(fitMethod)+'_ycor1C-Jpsi'].GetBinContent(1),hData[str(fitMethod)+'_ycor1C-Jpsi'].GetBinError(1))
     print "MC signal:  %s   %7.2F +/ %7.2F  "%(fitMethod,hMC['mc-'+str(fitMethod)+'_ycor1C10GeV-Jpsi'].GetBinContent(1),hMC['mc-'+str(fitMethod)+'_ycor1C10GeV-Jpsi'].GetBinError(1))
     ratio = hData[str(fitMethod)+'_ycor1C-Jpsi'].GetBinContent(1) / hMC['mc-'+str(fitMethod)+'_ycor1C10GeV-Jpsi'].GetBinContent(1) / MCnorm
     err1 =  ratio*hData[str(fitMethod)+'_ycor1C-Jpsi'].GetBinError(1)/hData[str(fitMethod)+'_ycor1C-Jpsi'].GetBinContent(1)
     err2 =  ratio*hMC['mc-'+str(fitMethod)+'_ycor1C10GeV-Jpsi'].GetBinError(1)/hMC['mc-'+str(fitMethod)+'_ycor1C10GeV-Jpsi'].GetBinContent(1)
     err = ROOT.TMath.Sqrt( err1**2+err2**2)
     print "Ratio normalized Data / MC  %s  %5.3F +/- %5.3F"%(fitMethod,ratio,err)
def AnalysisNote_JpsiPolarization(ptCut=1.0,pmin=20.,pmax = 300.,BDTCut=None, muID=1):
   hData['polFun'] = ROOT.TF1('polFun','[0]*(1+x**2*[1])',2)
   for fitMethod in ['B','CB']:
     tag = 'muID'+str(muID)+'_'+fitMethod+'-'+str(ptCut)+'_'+str(pmin)
     if BDTCut: tag += '_BDT'
     os.chdir(topDir)
     if not os.path.isdir(tag): os.system('mkdir '+tag)
     os.chdir(tag)
     hMC[fitMethod+'fCosCS'] = ROOT.TFile('JpsiKinematicsRec_cosCScor.root')
     ROOT.gROOT.cd()
     hMC[fitMethod+'xxx'] = hMC[fitMethod+'fCosCS'].Get('xxx').Clone(fitMethod+'xxx')
     hMC[fitMethod+'xxx'].SetName(fitMethod+'xxx')
     for x in hMC[fitMethod+'xxx'].GetListOfPrimitives():
       if x.GetName()=='TPave':
         x.SetX1NDC(0.374165)
         x.SetY1NDC(0.299475)
         x.SetX2NDC(0.572383)
         x.SetY2NDC(0.469352)
     for hname in [fitMethod+'_cosCScor-Jpsi','reccosCS_P8prim','reccosCS_Cascade','mc-'+fitMethod+'_cosCScor10GeV-Jpsi',
                   'mc-'+fitMethod+'_cosCScorHighMass-Jpsi-Jpsi','mc-'+fitMethod+'_cosCScorHighMass-JpsiP8-Jpsi']:
        hx = hMC[fitMethod+'xxx'].FindObject(hname)
        hx.SetMinimum(0.)
        hx.SetStats(0)
        hMC[hname] = hx.Clone(hname)
        norm = (hx.GetBinContent(hx.FindBin(-0.1))+hx.GetBinContent(hx.FindBin(0.1)))/2.
        hx.Scale(1./norm)
     hMC[fitMethod+'xxx'].DrawClone()
     # make simple eff correction
     ut.bookCanvas(hMC,'pol'+fitMethod,'  ',1200,900,1,1)
     hMC['pol'+fitMethod].cd()
     hMC['cosCSEff']=hMC['reccosCS_P8prim'].Clone('cosCSEff')
     hMC['cosCSEff'].Add(hMC['reccosCS_Cascade'])
     hMC['cosCSEff'].Fit('chebyshev9')
     effFun = hMC['cosCSEff'].GetFunction('chebyshev9')
     hMC[fitMethod+'_cosCScor_effCorrected'] =  hMC[fitMethod+'_cosCScor-Jpsi'].Clone(fitMethod+'_cosCScor_effCorrected')
     hx = hMC[fitMethod+'_cosCScor_effCorrected']
     hx.Reset()
     hMC[fitMethod+'_cosCScor_effCorrected_JpsiP8']  = hMC[fitMethod+'_cosCScor-Jpsi'].Clone(fitMethod+'_cosCScor_effCorrected_JpsiP8')
     hMC[fitMethod+'_cosCScor_effCorrected_JpsiP8'].Divide(hMC['mc-'+fitMethod+'_cosCScorHighMass-JpsiP8-Jpsi'])
     hMC[fitMethod+'_cosCScor_effCorrected_Jpsi']    = hMC[fitMethod+'_cosCScor-Jpsi'].Clone(fitMethod+'_cosCScor_effCorrected_Jpsi')
     hMC[fitMethod+'_cosCScor_effCorrected_Jpsi'].Divide(hMC['mc-'+fitMethod+'_cosCScorHighMass-Jpsi-Jpsi'])
     for hx in [hMC[fitMethod+'_cosCScor_effCorrected_JpsiP8'],hMC[fitMethod+'_cosCScor_effCorrected_Jpsi']]:
       norm = (hx.GetBinContent(hx.FindBin(-0.1))+hx.GetBinContent(hx.FindBin(0.1)))/2.
       hx.Scale(1./norm)
       hx.SetMaximum(1.1)
       hx.SetMinimum(0.0)
       fun = hData['polFun'].Clone('fun'+hx.GetName())
       rc = hx.Fit(fun,'S','',-0.5,0.5)
     hMC[fitMethod+'_cosCScor10GeV_effCorrected']  = hx.Clone(fitMethod+'_cosCScor10GeV_effCorrected')
     hMC[fitMethod+'_cosCScorHighMass-JpsiP8_effCorrected'] = hx.Clone(fitMethod+'_cosCScorHighMass-JpsiP8_effCorrected')
     hMC[fitMethod+'_cosCScorHighMass-Jpsi_effCorrected']   = hx.Clone(fitMethod+'_cosCScorHighMass-Jpsi_effCorrected')
     colors = {}
     colors[fitMethod+'_cosCScor'] = [ROOT.kBlue,21,'data']
     colors['mc-'+fitMethod+'_cosCScor10GeV']           = [ROOT.kMagenta,24,'10GeV']
     colors['mc-'+fitMethod+'_cosCScorHighMass-JpsiP8'] = [ROOT.kRed,22,'Pythia8']
     colors['mc-'+fitMethod+'_cosCScorHighMass-Jpsi']   = [ROOT.kOrange,23,'Pythia6']
# mmh this is the true distribution, can there be a resolution effect? No, see trueCosCS1()
     txt = {}
     for j in range(1,hMC[fitMethod+'_cosCScor-Jpsi'].GetNbinsX()+1):
        binL = hMC[fitMethod+'_cosCScor-Jpsi'].GetBinLowEdge(j)
        binL = int(binL*1000)/1000.
        binH = binL +hMC[fitMethod+'_cosCScor-Jpsi'].GetBinWidth(j)
        eff = effFun.Integral(binL,binH)
        for x in  [fitMethod+'_cosCScor','mc-'+fitMethod+'_cosCScor10GeV','mc-'+fitMethod+'_cosCScorHighMass-JpsiP8','mc-'+fitMethod+'_cosCScorHighMass-Jpsi']:
           signal = hMC[x+'-Jpsi'].GetBinContent(j)/eff
           hx = hMC[x.replace('mc-','')+'_effCorrected']
           hx.SetBinContent(j,signal)
           err = hMC[x+'-Jpsi'].GetBinError(j)/eff
           hx.SetBinError(j,err)
     for x in  colors:
           hx = hMC[x.replace('mc-','')+'_effCorrected']
           norm = (hx.GetBinContent(hx.FindBin(-0.1))+hx.GetBinContent(hx.FindBin(0.1)))/2.
           hx.Scale(1./norm)
           hx.SetMaximum(1.1)
           hx.SetMinimum(0.0)
           hx.SetMarkerStyle(colors[x][1])
           hx.SetMarkerColor(colors[x][0])
           hx.SetLineColor(colors[x][0])
           fun = hData['polFun'].Clone('fun'+hx.GetName())
           fun.SetLineColor(colors[x][0])
           rc = hx.Fit(fun,'S','',-0.5,0.5) # N*(1+L*x**2)
           fitResult = rc.Get()
           txt[x]  = "%s #Lambda=%5.2F +/- %5.2F"%(colors[x][2],fitResult.Parameter(1),fitResult.ParError(1))
     T=ROOT.TLatex()
     T.SetTextSize(0.04)
     y = 0.2
     hMC[fitMethod+'_cosCScor_effCorrected'].Draw()
     for x in  colors:
        hx = hMC[x.replace('mc-','')+'_effCorrected']
        hx.Draw('same')
        T.SetTextColor(colors[x][0])
        T.DrawLatexNDC(0.15,y,txt[x])
        y+=0.08
  # make average between B and CB and add sys error
   os.chdir(topDir)
   hx = 'AV_cosCScor_effCorrected'
   hMC[hx] = hMC['B_cosCScor_effCorrected'].Clone(hx)
   for n in range(1,hMC[hx].GetNbinsX()+1):
     nB,eB = hMC['B_cosCScor_effCorrected'].GetBinContent(n),hMC['B_cosCScor_effCorrected'].GetBinError(n)
     nCB,eCB = hMC['CB_cosCScor_effCorrected'].GetBinContent(n),hMC['CB_cosCScor_effCorrected'].GetBinError(n)
     nmean = (nB+nCB)/2.
     emeansq = ( (nmean-nB)**2 + (nmean-nCB)**2) / 2.
     etot = ROOT.TMath.Sqrt(max(eB,eCB)**2+emeansq)
     hMC[hx].SetBinContent(n,nmean)
     hMC[hx].SetBinError(n,etot)
   ut.bookCanvas(hMC,'polAv','  ',1200,900,1,1)
   hMC['polAv'].cd()
   fun = hData['polFun'].Clone('fun'+hMC[hx].GetName())
   rc = hMC[hx].Fit(fun,'S','',-0.8,0.8) # N*(1+L*x**2)
   c1 = hMC['Bxxx'].DrawClone()
   c1.Print('BrecCosCS_muID'+str(muID)+'.pdf')
   c1.Print('BrecCosCS_muID'+str(muID)+'.png')
   myPrint(hMC['polAv'],'AvEffCorCosCS_muID'+str(muID))
   myPrint(hMC['polB'],'BEffCorCosCS_muID'+str(muID))
#
   ut.bookCanvas(hMC,'polSum','  ',1200,900,1,1)
   T = ROOT.TLatex()
   T.SetTextSize(0.03)
   colors = {}
   colors['B_Jpsi']       = ROOT.kCyan
   colors['B_JpsiP8']     = ROOT.kRed
   colors['CB_Jpsi']       = ROOT.kBlue
   colors['CB_JpsiP8']     = ROOT.kMagenta
   dy = 0.15
   txt ={}
   for fitMethod in ['B','CB']:
     for MC in ['_Jpsi','_JpsiP8']:
       fun = hMC[fitMethod+'_cosCScor_effCorrected'+MC].GetFunction('fun'+fitMethod+'_cosCScor_effCorrected'+MC)
       fun.SetLineColor(colors[fitMethod+MC])
       hMC[fitMethod+'_cosCScor_effCorrected'+MC].SetLineColor(colors[fitMethod+MC])
       hMC[fitMethod+'_cosCScor_effCorrected'+MC].SetMarkerColor(colors[fitMethod+MC])
       rc  = hMC[fitMethod+'_cosCScor_effCorrected'+MC].Fit(fun,'SQ','',-0.6,0.6)
       fitResult = rc.Get()
       txt[fitMethod+'_cosCScor_effCorrected'+MC]  = "%3s %8s: polarization CS #Lambda=%5.2F+/-%5.2F"%(fitMethod,MC,fitResult.Parameter(1),fitResult.ParError(1))
   for fitMethod in ['B','CB']:
     for MC in ['_Jpsi','_JpsiP8']:
       if dy < 0.2: hMC[fitMethod+'_cosCScor_effCorrected'+MC].Draw()
       else:        hMC[fitMethod+'_cosCScor_effCorrected'+MC].Draw('same')
       T.SetTextColor(colors[fitMethod+MC])
       T.DrawLatexNDC(0.2,dy,txt[fitMethod+'_cosCScor_effCorrected'+MC])
       dy+=0.051

def debugCosCSreco(fitMethod='B'):
  for x in [fitMethod+'_cosCScor-Jpsi','mc-'+fitMethod+'_cosCScor10GeV-Jpsi','mc-'+fitMethod+'_cosCScorHighMass-Jpsi-Jpsi','mc-'+fitMethod+'_cosCScorHighMass-JpsiP8-Jpsi']:
   norm = (hMC[x].GetBinContent(hMC[x].FindBin(-0.1))+hMC[x].GetBinContent(hMC[x].FindBin(0.1)))/2.
   hMC[x].Scale(1./norm)
   hMC[x].Fit('gaus')
   hMC[x].GetFunction('gaus').SetLineColor(hMC[x].GetMarkerColor())
  hMC[fitMethod+'_cosCScor-Jpsi'].SetMinimum(0.)
  hMC['mc-'+fitMethod+'_cosCScor-Jpsi'].Draw()
  hMC['mc-'+fitMethod+'_cosCScor10GeV-Jpsi'].Draw('same')
  hMC['mc-'+fitMethod+'_cosCScorHighMass-Jpsi-Jpsi'].Draw('same')
  hMC['mc-'+fitMethod+'_cosCScorHighMass-JpsiP8-Jpsi'].Draw('same')
  myPrint(hMC['pol'],fitMethod+'-cosCSraw')
def summaryRPCacceptanceIssue():
  hData['Results_2']  = JpsiAcceptanceSys(ptCut=1.0,pmin=20.,BDTCut=None, muID=2)
  hData["B_ycor1C-Jpsi_effCorrected_average-muID2"] = hMC["B_ycor1C-Jpsi_effCorrected_average"].Clone("B_ycor1C-Jpsi_effCorrected_average-muID2")
  hData['Results_1']  = JpsiAcceptanceSys(ptCut=1.0,pmin=20.,BDTCut=None, muID=1)
  hData["B_ycor1C-Jpsi_effCorrected_average-muID1"] = hMC["B_ycor1C-Jpsi_effCorrected_average"].Clone("B_ycor1C-Jpsi_effCorrected_average-muID1")
  hData['Results_12'] = JpsiAcceptanceSys(ptCut=1.0,pmin=20.,BDTCut=None, muID=12)
  hData["B_ycor1C-Jpsi_effCorrected_average-muID12"] = hMC["B_ycor1C-Jpsi_effCorrected_average"].Clone("B_ycor1C-Jpsi_effCorrected_average-muID12")

  hData["B_ycor1C-Jpsi_effCorrected_average-muID2"].SetLineColor(ROOT.kMagenta)
  hData["B_ycor1C-Jpsi_effCorrected_average-muID2"].SetMarkerColor(ROOT.kMagenta)
  hData["B_ycor1C-Jpsi_effCorrected_average-muID12"].SetLineColor(ROOT.kCyan)
  hData["B_ycor1C-Jpsi_effCorrected_average-muID12"].SetMarkerColor(ROOT.kCyan)
  hData["B_ycor1C-Jpsi_effCorrected_average-muID12"].SetMarkerStyle(22)
  hData["B_ycor1C-Jpsi_effCorrected_average-muID1"].SetLineColor(ROOT.kBlue)
  hData["B_ycor1C-Jpsi_effCorrected_average-muID1"].SetMarkerColor(ROOT.kBlue)
  hData["B_ycor1C-Jpsi_effCorrected_average-muID1"].SetMarkerStyle(23)
  hData["B_ycor1C-Jpsi_effCorrected_average-muID2"].Draw()
  hData["B_ycor1C-Jpsi_effCorrected_average-muID1"].Draw('same')
  hData["B_ycor1C-Jpsi_effCorrected_average-muID12"].Draw('same')
  hData['legaverage-muID']=ROOT.TLegend(0.16,0.28,0.62,0.46)
  rc = hData['legaverage-muID'].AddEntry(hData["B_ycor1C-Jpsi_effCorrected_average-muID2"],'with both muons X/Y RPC matched','PL')
  rc.SetTextColor(hData["B_ycor1C-Jpsi_effCorrected_average-muID2"].GetLineColor())
  rc = hData['legaverage-muID'].AddEntry(hData["B_ycor1C-Jpsi_effCorrected_average-muID1"],'at least one muon X/Y RPC matched','PL')
  rc.SetTextColor(hData["B_ycor1C-Jpsi_effCorrected_average-muID1"].GetLineColor())
  rc = hData['legaverage-muID'].AddEntry(hData["B_ycor1C-Jpsi_effCorrected_average-muID12"],'with both muons only X RPC matched','PL')
  rc.SetTextColor(hData["B_ycor1C-Jpsi_effCorrected_average-muID12"].GetLineColor())
  hData['legaverage-muID'].Draw()
  myPrint(hMC['Final'],"JpsiCrossRPCFix")
def summaryRPCacceptanceIssue2():
 withCosCSCut=True
 ptCut = 1.0 
 pmin = 10.
 pmax = 300.
 BDTCut=None
 muID=2
 ycor = 'ycor1C'
 category = {}
 category['_Cascade']     = {'cut':'id==443',            'cutrec':'&&Jpsi==443&&originZ1<-100&&p1x!=p2x'}
 category['_P8prim']      = {'cut':'id==443',            'cutrec':'&&Jpsi==443&&originZ1<-100&&p1x!=p2x'}
 colors = {}
 colors['_Cascade']    = ROOT.kMagenta
 colors['_Cascadeprim']= ROOT.kCyan
 colors['_P8prim']     = ROOT.kRed
 colors['Data']        = ROOT.kBlue
#  
 theCut = theJpsiCut('mcor',withCosCSCut,ptCut,pmin,pmax,muID,BDTCut)
 fold = ROOT.TFile('refit/ntuple-invMass-MC-Jpsi.root')
 fnew = ROOT.TFile('refit-mu/ntuple-invMass-MC-Jpsi_mu.root')
 y_beam = yBeam()
 z='_Cascade'
 ut.bookHist(hMC,'YandPt'+z+'_rec','rapidity of reconstructed ',  200,-2.,2., 60, 0.,6.)
 hMC['YandPt'+z+'_recOLD']=hMC['YandPt'+z+'_rec'].Clone('YandPt'+z+'_recOLD')
 hMC['YandPt'+z+'_recNEW']=hMC['YandPt'+z+'_rec'].Clone('YandPt'+z+'_recNEW')
 fold.nt.Draw('PtTRUE:(YTRUE-'+str(y_beam)+')>>YandPt'+z+'_recOLD',theCut+category[z]['cutrec'])
 fnew.nt.Draw('PtTRUE:(YTRUE-'+str(y_beam)+')>>YandPt'+z+'_recNEW',theCut+category[z]['cutrec'])
 hMC['Y_recOLD']=hMC['YandPt'+z+'_recOLD'].ProjectionX()
 hMC['Y_recNEW']=hMC['YandPt'+z+'_recNEW'].ProjectionX()
 hMC['ratio']=hMC['Y_recOLD'].Clone('ratio')
 hMC['ratio'].Divide(hMC['Y_recNEW'])
 hMC['ratio'].GetXaxis().SetRangeUser(0.,2.)
 hMC['ratio'].SetTitle('rate increase;y_{CM}')
 hMC['ratio'].SetStats(0)
 hMC['ratio'].SetMinimum(0.)
def summaryRPCacceptanceIssue3():
# check change in MC muon flux with RPC fix:
  tc = hMC['dummy'].cd()
  ut.readHists(hData,"sumHistos--simulation10GeV-repro.root")
  c="Chi2<"
  hMC['new'] = hData[c+'p/ptmu'].Clone('new')
  hData.clear()
  ut.readHists(hData,"../refit/sumHistos--simulation10GeV-repro.root")
  hMC['old'] = hData[c+'p/ptmu'].Clone('old')
  hMC['new'].SetLineColor(ROOT.kRed)
  hMC['new'].SetMarkerColor(ROOT.kRed)
  for c in ['old','new']:
    hMC['P'+c]=hMC[c].ProjectionX('P'+c)
    #hMC['P'+c].Rebin(10)
    hMC['P'+c].GetXaxis().SetRangeUser(5.,300.)
  hMC['Pold'].Draw()
  hMC['Pnew'].Draw('same')
  hMC['Pratio'] =  hMC['Pnew'].Clone('Pratio')
  hMC['Pratio'].Divide(hMC['Pold'])
  hMC['Pratio'].SetMinimum(0.7)
  hMC['Pratio'].SetMaximum(1.02)
  hMC['Pratio'].SetStats(0)
  hMC['Pratio'].SetTitle('MC: after correction / before')
  tc.SetGridy(1)
  hMC['Pratio'].Draw('hist')
  myPrint(hMC['dummy'],'RPCissueMuflux')
def summaryRPCacceptanceIssue4():
  f=ROOT.TFile('MC-ComparisonChi2mu_linP.root')
  ROOT.gROOT.cd()
  hMC['linMCp/ptmu_x'] = f.output.FindObject('linMCp/ptmu_x').Clone('linMCp/ptmu_x')
  hMC['linMC10p/ptmu_x'] = f.output.FindObject('linMC10p/ptmu_x').Clone('linMC10p/ptmu_x')
  hData['linp/ptmu_x'] = f.output.FindObject('linp/ptmu_x').Clone('linp/ptmu_x')
  f=ROOT.TFile('../refit/MC-ComparisonChi2mu_linP.root')
  ROOT.gROOT.cd()
  hMC['linMCp/ptmu_xOLD'] = f.output.FindObject('linMCp/ptmu_x').Clone('linMCp/ptmu_xOLD')
  hMC['linMC10p/ptmu_xOLD'] = f.output.FindObject('linMC10p/ptmu_x').Clone('linMC10p/ptmu_xOLD')
  hData['linp/ptmu_x'].Draw()
  m = hData['linp/ptmu_x'].GetMinimum()
  hMC['linMCp/ptmu_x'].SetLineColor(ROOT.kGreen)
  hMC['linMCp/ptmu_x'].GetXaxis().SetRangeUser(5.,20.)
  hMC['linMCp/ptmu_x'].SetMinimum(m)
  hMC['linMCp/ptmu_x'].Draw('same')
  hMC['linMC10p/ptmu_x'].SetLineColor(ROOT.kGreen)
  hMC['linMC10p/ptmu_x'].GetXaxis().SetRangeUser(20,300.)
  hMC['linMC10p/ptmu_x'].SetMinimum(m)
  hMC['linMC10p/ptmu_x'].Draw('same')
  hMC['linMC10p/ptmu_xOLD'].GetXaxis().SetRangeUser(20,300.)
  hMC['linMC10p/ptmu_xOLD'].SetMinimum(m)
  hMC['linMC10p/ptmu_xOLD'].Draw('same')
  hMC['linMCp/ptmu_xOLD'].GetXaxis().SetRangeUser(5.,20.)
  hMC['linMCp/ptmu_xOLD'].SetMinimum(m)
  hMC['linMCp/ptmu_xOLD'].Draw('same')
  hMC['ratioMCp/ptmu_x']=hMC['linMCp/ptmu_xOLD'].Clone('ratioMCp/ptmu_x')
  hMC['ratioMCp/ptmu_x'].Divide(hMC['linMCp/ptmu_x'])
  hMC['ratioMC10p/ptmu_x']=hMC['linMC10p/ptmu_xOLD'].Clone('ratioMC10p/ptmu_x')
  hMC['ratioMC10p/ptmu_x'].Divide(hMC['linMC10p/ptmu_x'])
  ut.bookCanvas(hMC,'dummy2','ratio',1200,900)
  tc = hMC['dummy2'].cd()
  tc.SetGridy(1)
  hMC['XXX'] = hData['linp/ptmu_x'].Clone('XXX')
  hMC['XXX'].Reset()
  hMC['XXX'].SetMaximum(1.4)
  hMC['XXX'].SetMinimum(0.9)
  hMC['XXX'].Draw()
  hMC['ratioMC10p/ptmu_x'].Draw('same')
  hMC['ratioMCp/ptmu_x'].Draw('same')


def cosCSLowMass():
  for ptmax in [1.0,0.0]:
     AnalysisNote_LowMassKinematicsReco(ptmax=ptmax,pmin=20.,mMax=2.0,muID=2,BDTCut=False)
     hMC['dummy'].cd()
     hMC['reccosCSData'].GetYaxis().SetTitle('arbitrary unit')
     hMC['reccosCSData'].Draw()
     scale(hMC['reccosCS_10GeV'],hMC['reccosCSData'],R=[])
     hMC['reccosCS_10GeV'].Draw('same')
     test = hMC['reccosCSData'].Clone('test')
     test.Divide(hMC['reccosCS_10GeV'])
     test.Scale(hMC['reccosCSData'].GetMaximum()/2.)
     test.Draw('same')
     myPrint(hMC['dummy'],'cosCSLowMass_'+str(ptmax))
  myCopy('cosCSLowMass_*.png')
  myCopy('cosCSLowMass_*.pdf')
def retrieveJpsiKinematics(ptCut=1.0,pmin=20.,pmax = 300.,BDTCut=None, muID=1,fitMethod='B'):
   colors = {}
   colors['HighMass-Jpsi-Jpsi']       = [ROOT.kCyan,26,'MC Pythia6','same']
   colors['HighMass-JpsiP8-Jpsi']     = [ROOT.kRed, 32,'MC Pythia8','same']
   colors['Data']                     = [ROOT.kBlue,21,'Data','']
   tag = 'muID'+str(muID)+'_'+fitMethod+'-'+str(ptCut)+'_'+str(pmin)
   if BDTCut: tag += '_BDT'
   os.chdir(topDir)
   for c in ['ptcor','pcor','ycor1C','cosCScor']:
     f = ROOT.TFile(tag+'/JpsiKinematicsRec_'+c+'.root')
     ROOT.gROOT.cd()
     for x in f.xxx.GetListOfPrimitives():
        if x.ClassName().find('TH')==0:
           print x.GetName()
           hMC[x.GetName()] = x.Clone()
           hMC[x.GetName()+'_norm'] = x.Clone()
           hMC[x.GetName()+'_norm'].SetStats(0)
           hMC[x.GetName()+'_norm'].GetYaxis().SetTitle('arbitrary units')
           if c.find('pt')==0: 
              hMC[x.GetName()+'_norm'].GetXaxis().SetTitle('p_{T}  [GeV/c]')
           if c.find('pc')==0: 
              hMC[x.GetName()+'_norm'].GetXaxis().SetTitle('p  [GeV/c]')
           hMC[x.GetName()+'_norm'].Scale(1./hMC[x.GetName()].GetSumOfWeights())
     ut.bookCanvas(hMC,'TC'+c,' ',900,600,1,1)
     hMC['TC'+c].cd()
     hMC['L'+c] = ROOT.TLegend(0.7,0.70,0.95,0.85)
     plotHistos = {}
     hMax = 0
     for x in colors:
        if x=='Data':
           hx = fitMethod+'_'+c+'-Jpsi_norm'
        else:
           hx = 'mc-'+fitMethod+'_'+c+x+'_norm'
        hMC[hx].SetLineColor(colors[x][0])
        hMC[hx].SetMarkerStyle(colors[x][1])
        hMC[hx].SetMarkerColor(colors[x][0])
        plotHistos[hx]=x
        if hMC[hx].GetMaximum()>hMax: hMax = hMC[hx].GetMaximum()
     keys = plotHistos.keys()
     aHisto = hMC[keys[0]]
     x = plotHistos[keys[0]]
     aHisto.SetMaximum(hMax*1.05)
     aHisto.Draw()
     rc = hMC['L'+c].AddEntry(aHisto,colors[x][2],'PL')
     for n in range(1,len(keys)): 
       aHisto = hMC[keys[n]]
       aHisto.Draw('same')
       x = plotHistos[keys[n]]
       rc = hMC['L'+c].AddEntry(aHisto,colors[x][2],'PL')
       rc.SetTextColor(aHisto.GetLineColor())
     hMC['L'+c].Draw()
     myPrint(hMC['TC'+c],'JpsiKinematicsRec_'+c+'-'+tag)

def weight4Pythia6():
   y_beam = yBeam()
   colors = {}
   colors['_Cascade']    = [ROOT.kMagenta,23,'Pythia6','JpsiCascade',   'pythia64','same']
   colors['_P8prim']     = [ROOT.kRed,    22,'Pythia8','JpsiP8_Primary','pythia82','']
   ROOT.gROOT.cd()
   for z in colors:
     ut.bookHist(hMC,'YandPt'+z,'pt vs rapidity of original ', 200,-2.,2., 100, 0.,10.)
     hMC[colors[z][3]].Draw('sqrt(px*px+py*py):0.5*log((E+pz)/(E-pz))-'+str(y_beam)+'>>YandPt'+z,     'id==443')
     hMC['Pt'+z] = hMC['YandPt'+z].ProjectionY('Pt'+z)
     hMC['Y'+z]  = hMC['YandPt'+z].ProjectionX('Y'+z)
   hMC['p6w'] = hMC['Pt_P8prim'].Clone('p6w')
   hMC['p6w'].Divide(hMC['Pt_Cascade'])
   hMC['p6w'].Scale(1./hMC['p6w'].GetMaximum())
   rc = hMC['p6w'].Fit('pol9','SQ','',0.,6.)
   hMC['fp6w'] = hMC['p6w'].GetFunction('pol9')
   hMC['p8w'] = hMC['Y_Cascade'].Clone('p8w')
   hMC['p8w'].Divide(hMC['Y_P8prim'])
   hMC['p8w'].Scale(1./hMC['p8w'].GetMaximum())
   rc = hMC['p8w'].Fit('pol9','SQ','',-1.,2.)
   hMC['fp8w'] = hMC['p8w'].GetFunction('pol9')

def compWithEric():
   hMC['pythia82']={}
   hMC['pythia64']={}
   hMC['pythia82']['f']=ROOT.TFile('/mnt/hgfs/Images/VMgate/Jpsi/pythia82.root')
   hMC['pythia64']['f']=ROOT.TFile('/mnt/hgfs/Images/VMgate/Jpsi/pythia64.root')
   pcol = {'pythia64':[ROOT.kBlue,32,'Pythia64'],'pythia82':[ROOT.kCyan,26,'Pythia82']}
   for x in ['pythia64','pythia82']:
     for z in ['pJpsi','pTZ','ytrue']:
       hMC[x][z]=hMC[x]['f'].Get(z).Clone(z+x)
       hMC[x][z].Scale(1./hMC[x][z].GetSumOfWeights()/hMC[x][z].GetBinWidth(1))
       hMC[x][z].SetStats(0)
       hMC[x][z].SetLineColor(pcol[x][0])
       hMC[x][z].SetMarkerStyle(pcol[x][1])
       hMC[x][z].SetMarkerColor(pcol[x][0])
   colors={}
   colors['_Cascade']    = [ROOT.kMagenta,23,'Pythia6','JpsiCascade',   'pythia64','same']
   colors['_P8prim']     = [ROOT.kRed,    22,'Pythia8','JpsiP8_Primary','pythia82','']
   ROOT.gROOT.cd()
   for z in colors:
     ut.bookHist(hMC,'P'+z,'P Jpsi '       ,100,0.,400.)
     ut.bookHist(hMC,'Pt'+z,'Pt Jpsi '     ,120,0.,6.)
     ut.bookHist(hMC,'Y'+z,'Y Jpsi '       ,140,0.,7.)
     hMC[colors[z][3]].Draw('sqrt(px*px+py*py+pz*pz)>>P'+z,'id==443')
     hMC[colors[z][3]].Draw('sqrt(px*px+py*py)>>Pt'+z,     'id==443')
     hMC[colors[z][3]].Draw('0.5*log((E+pz)/(E-pz))>>Y'+z, 'id==443')
   ut.bookCanvas(hMC,'comparison','  ',1800,900,3,1)
   pdict = {'P':'pJpsi','Pt':'pTZ','Y':'ytrue'}
   j=1
   for x in pdict:
      hMC['comparison'].cd(j)
      hMC['L'+str(j)] = ROOT.TLegend(0.6,0.6,0.85,0.70)
      for z in colors:
        hMC[x+z].Scale(1./hMC[x+z].GetSumOfWeights()/hMC[x+z].GetBinWidth(1))
        hMC[x+z].SetLineColor(colors[z][0])
        hMC[x+z].SetMarkerStyle(colors[z][1])
        hMC[x+z].SetMarkerColor(colors[z][0])
        hMC[x+z].SetStats(0)
        hMC[x+z].Draw(colors[z][5])
        rc = hMC['L'+str(j)].AddEntry(hMC[x+z],colors[z][2],'PL')
        rc.SetTextColor(hMC[x+z].GetLineColor())
      for z in ['pythia64','pythia82']:
        hMC[z][pdict[x]].Draw('same')
        rc = hMC['L'+str(j)].AddEntry(hMC[z][pdict[x]],pcol[z][2],'PL')
        rc.SetTextColor(hMC[z][pdict[x]].GetLineColor())
      hMC['L'+str(j)].Draw()
      j+=1
def MakeKeysToDThits(event,minToT=-999):
    keysToDThits={}
    key = -1
    for hit in event.Digi_MufluxSpectrometerHits:
        key+=1
        #if not hit.hasTimeOverThreshold(): continue
        if not hit.isValid(): continue
        detID=hit.GetDetectorID()
        if detID<0: continue # feature for converted data in February'19
        if keysToDThits.has_key(detID):
            prevTDC = event.Digi_MufluxSpectrometerHits[keysToDThits[detID][0]].GetDigi()
            prevToT = event.Digi_MufluxSpectrometerHits[keysToDThits[detID][0]].GetTimeOverThreshold()
            # print "MakeKeysToDThits, non unique Digi_MufluxSpectrometerHits",detID,hit.GetDigi(),hit.GetTimeOverThreshold(),hit.hasTimeOverThreshold(),prevTDC,prevToT
            if hit.hasTimeOverThreshold(): keysToDThits[detID]=[key]
        else:
            keysToDThits[detID]=[key]
    key = -1
    for hit in event.Digi_LateMufluxSpectrometerHits:
        key+=1
        if not hit.isValid(): continue
        if not hit.hasTimeOverThreshold(): continue
        if hit.GetTimeOverThreshold()<minToT : continue
        detID=hit.GetDetectorID()
        if not keysToDThits.has_key(detID): 
            print "MakeKeysToDThits, late hit but no first one",detID
            keysToDThits[detID]=[-1]
        keysToDThits[detID].append(key)
    return keysToDThits
def mcTrackID2(event,m):
    detIDToKey = MakeKeysToDThits(event,9999.)
    info = event.TrackInfos[m]
    trackIDs = {}
    for d in range(info.N()):
        detID = info.detId(d)
        if detID//10000000<3: continue
        MCTrackID = event.MufluxSpectrometerPoint[detIDToKey[detID][0]].GetTrackID()
        if not trackIDs.has_key(MCTrackID): trackIDs[MCTrackID]=0
        trackIDs[MCTrackID]+=1
    sorted_trackIDs = sorted(trackIDs.items(), key=operator.itemgetter(1),reverse=True)
    return sorted_trackIDs[0][0]
def muonEventCategory(event,mu):
   check = False
   procList = {"Decay":1,"Hadronic inelastic":2,"Lepton pair production":3,"Photo nuclear interaction":8,"Positron annihilation":4,"Primary particle emission":7}
   G4procList = procList.keys()
   if mu[0]==mu[1]:
      return 10
# easy cases
   if abs(mu[0].GetPdgCode())!=13 or abs(mu[1].GetPdgCode())!=13: 
       return 98
# heavy flavour event ?
   for m in event.MCTrack:
        if abs(m.GetPdgCode()) in [5332,5232,5132,5232,5122,531,511,521]:
           return 5
        if abs(m.GetPdgCode()) in [4332,4232,4132,4232,4122,431,411,421]:
           return 6
# same mother
   if mu[0].GetMotherId() == mu[1].GetMotherId():
     if mu[0].GetProcName().Data() == mu[1].GetProcName().Data():
        if mu[0].GetProcName().Data() in G4procList:
           return procList[mu[0].GetProcName().Data()]
   if mu[0].GetMotherId() != mu[1].GetMotherId():
# different mother
     if abs(mu[0].GetPdgCode())==13 and abs(mu[1].GetPdgCode())==13:
       gM = {}
       for m in range(2):
          mo = mu[m].GetMotherId()
          while abs(event.MCTrack[mo].GetPdgCode()) == 13:
             mo=event.MCTrack[mo].GetMotherId()
          gM[m]=mo
       if gM[0]==gM[1]:
          if event.MCTrack[gM[0]].GetPdgCode()==23:
             return 11
          if event.MCTrack[gM[0]].GetPdgCode()==22:
             return 12
          if event.MCTrack[gM[0]].GetPdgCode() in [1,2,3,-1,-2,-3]:
             return 13
     if mu[0].GetProcName().Data()=="Decay" or mu[1].GetProcName().Data()=="Decay":
         return 9
   return 99
def checkDiMuon(event,mu):
   check = False
   pName = mu.GetProcName()
   if  pName.Data() == "Hadronic inelastic" or  pName.Data() == "Positron annihilation" or pName.Data() == "Lepton pair production":  check = True
   Pcode = abs( event.MCTrack[mu.GetMotherId()].GetPdgCode())
   if Pcode==221 or Pcode==223 or Pcode==333 or Pcode==113 or Pcode == 331: check = True
   return check

def extractMuons(E='1GeV'):
    rnr       = ROOT.TRandom()
    sTreeMC = ROOT.TChain('cbmsim')
    path = os.environ["EOSSHIP"]+"/eos/experiment/ship/data/Mbias/background-prod-2018/"
    if E=='1GeV':
        tmp = "pythia8_Geant4_1.0_cXXXX_mu.root"
        for k in range(0,20000,1000):
            fname = path+tmp.replace('XXXX',str(k))
            try:
                    test = ROOT.TFile.Open(fname)
                    if test.cbmsim.GetEntries()>0:   sTreeMC.Add(fname)
            except:
                    print "file not found",fname
                    continue
#
    if E=="Charm":
        fname = path+"pythia8_Geant4_charm_0-19_1.0_mu.root"
        try:
                test = ROOT.TFile.Open(fname)
                if test.cbmsim.GetEntries()>0:   sTreeMC.Add(fname)
        except:
                print "file not found",fname
#
    if E=='10GeV':
        tmp = "pythia8_Geant4_10.0_withCharmandBeautyXXXX_mu.root"
        for k in range(0,67000,1000):
            fname = path+tmp.replace('XXXX',str(k))
            try:
                    test = ROOT.TFile.Open(fname)
                    if test.cbmsim.GetEntries()>0:   sTreeMC.Add(fname)
            except:
                    print "file not found",fname
                    continue
    f     = ROOT.TFile("originMCmuons_"+E+".root","RECREATE")
    muons = ROOT.TNtuple("muons","muons","px:py:pz:ox:oy:oz:moID:procID:w")
    for event in sTreeMC:
      moList = {}
      muList = []
      for p in event.vetoPoint:
          if abs(p.PdgCode())!=13: continue
          m = event.MCTrack[p.GetTrackID()]
          if checkDiMuon(event,m) :
              mo = m.GetMotherId()
              if not moList.has_key(mo): moList[mo]=[]
              moList[mo].append(m)
          else:
              muList.append(m)
      for mo in moList:
        if rnr.Uniform(0.,1.)>0.99:
           for m in moList[mo]:
               muList.append(m)
      for mu in muList:
          mo = event.MCTrack[mu.GetMotherId()]
          rc = muons.Fill(mu.GetPx(),mu.GetPy(),mu.GetPz(),mu.GetStartX(),mu.GetStartY(),mu.GetStartZ(),mo.GetPdgCode(),
                          mu.GetProcID(),mu.GetWeight())
    f.cd()
    muons.Write()

def extractDecays(E):
    ut.bookHist(h,'MP','mass/P',500,0.,5.,100,0.,400.)
    ut.bookHist(h,'Pmu','muon momentum',400,0.,400.)
#
    sTreeMC = ROOT.TChain('cbmsim')
    path = os.environ["EOSSHIP"]+"/eos/experiment/ship/data/Mbias/background-prod-2018/"
    if E=='1GeV':
        tmp = "pythia8_Geant4_1.0_cXXXX_mu.root"
        for k in range(0,20000,1000):
            fname = path+tmp.replace('XXXX',str(k))
            try:
                    test = ROOT.TFile.Open(fname)
                    if test.cbmsim.GetEntries()>0:   sTreeMC.Add(fname)
            except:
                    print "file not found",fname
                    continue

    if E=="Charm":
        fname = path+"pythia8_Geant4_charm_0-19_1.0_mu.root"
        try:
                test = ROOT.TFile.Open(fname)
                if test.cbmsim.GetEntries()>0:   sTreeMC.Add(fname)
        except:
                print "file not found",fname

    if E=='10GeV':
        tmp = "pythia8_Geant4_10.0_withCharmandBeautyXXXX_mu.root"
        for k in range(0,67000,1000):
            fname = path+tmp.replace('XXXX',str(k))
            try:
                    test = ROOT.TFile.Open(fname)
                    if test.cbmsim.GetEntries()>0:   sTreeMC.Add(fname)
            except:
                    print "file not found",fname
                    continue
    f     = ROOT.TFile("originalDecays_"+E+".root","RECREATE")
    muons = ROOT.TNtuple("muons","muons","px:py:pz:M:moID:procID:w:px1:py1:pz1:px2:py2:pz2")
    for event in sTreeMC:
      mus = []
      decay = {}
      for m in event.MCTrack:
         if abs(m.GetPdgCode())!=13: continue
         if m.GetProcID()==23: mus.append(m)
         if m.GetProcID()==4 or m.GetProcID()==0 :
             mo = m.GetMotherId()
             if not decay.has_key(mo): decay[mo]=[]
             decay[mo].append(m)
      for j in range(len(mus)-1):
        for k in range(j+1,len(mus)):
          if not mus[k].GetPdgCode()*mus[j].GetPdgCode()<0: continue
          mu1 = ROOT.Math.PxPyPzMVector(mus[j].GetPx(),mus[j].GetPy(),mus[j].GetPz(),muonMass)
          mu2 = ROOT.Math.PxPyPzMVector(mus[k].GetPx(),mus[k].GetPy(),mus[k].GetPz(),muonMass)
          R = mu1+mu2
          rc = h['MP'].Fill( R.M(),R.P() )
          rc = h['Pmu'].Fill(mu1.P())
          rc = h['Pmu'].Fill(mu2.P())
          rc = muons.Fill(R.Px(),R.Py(),R.Pz(),R.M(),-1,23,mus[j].GetWeight(),
               mus[j].GetPx(),mus[j].GetPy(),mus[j].GetPz(),
               mus[k].GetPx(),mus[k].GetPy(),mus[k].GetPz())
      for mo in decay:
        if not len(decay[mo])==2: continue
        if not decay[mo][0].GetPdgCode()*decay[mo][1].GetPdgCode()<0: continue
        Mmo = event.MCTrack[mo]
        rc = muons.Fill(Mmo.GetPx(),Mmo.GetPy(),Mmo.GetPz(),Mmo.GetMass(),Mmo.GetPdgCode(),decay[mo][0].GetProcID(),Mmo.GetWeight(),
               decay[mo][0].GetPx(),decay[mo][0].GetPy(),decay[mo][0].GetPz(),
               decay[mo][1].GetPx(),decay[mo][1].GetPy(),decay[mo][1].GetPz())
    f.cd()
    muons.Write()
    ut.writeHists(h,'extractDecays.root')

def extractRecMuons(E='1GeV',debug=False):
    f     = ROOT.TFile("recMuons_"+E+".root","RECREATE")
    variables = "px:py:pz:ox:oy:oz:moID:muID:procID:w:chi2:goodTrack:recpx:recpy:recpz:recx:recy:recz:DTpx:DTpy:DTpz:DTx:DTy:DTz:mcor"
    muons = ROOT.TNtuple("muons","muons",variables)
    currentFile = ''
    sTreeFullMC = None
    for n in range(0,sTreeMC.GetEntries()):
      rc = sTreeMC.GetEvent(n)
      if sTreeMC.GetCurrentFile().GetName()!=currentFile:
            currentFile = sTreeMC.GetCurrentFile().GetName()
            nInFile = n
# search for 2 track event amd calculate mcor:
      if len(sTreeMC.GoodTrack)>2:continue
      mcor = -999.
      if len(sTreeMC.GoodTrack)==2:
        sTree = sTreeMC
        Pcor={}
        P={}
        if sTree.GoodTrack[0]<0   or sTree.GoodTrack[1]<0:    continue
        if sTree.GoodTrack[0]>999 or sTree.GoodTrack[1]>999:  continue
        for k in range(2):
          P[k] = ROOT.Math.PxPyPzMVector(sTree.Px[k],sTree.Py[k],sTree.Pz[k],muonMass)
# make dE correction plus direction from measured point
          dline   = ROOT.TVector3(sTree.x[k],sTree.y[k],sTree.z[k]-zTarget)
          Ecor = P[k].E()+dEdxCorrection(P[k].P())
          norm = dline.Mag()
          Pcor[k]  = ROOT.Math.PxPyPzMVector(Ecor*dline.X()/norm,Ecor*dline.Y()/norm,Ecor*dline.Z()/norm,0.105658)
#    theCut =  'mult<3&&max(pt1,pt2)>'+sptCut+'&&chi21*chi22<0&&max(abs(chi21),abs(chi22))<0.9&&\max(p1,p2)<'+str(pmax)+'&&min(p1,p2)>'+str(pmin)+'&&mcor>0.20'
        if max(Pcor[0].Pt(),Pcor[1].Pt())>1.0 and min(P[0].P(),P[1].P())>20.0:
           X = Pcor[0]+Pcor[1]
           mcor = X.M()
      for j in range(sTreeMC.nTr):
        if sTreeMC.GoodTrack[j]<0 or sTreeMC.GoodTrack[j]>999: continue
        fname = sTreeMC.GetCurrentFile().GetName().replace('ntuple-','')
        if sTreeFullMC:
           if sTreeFullMC.GetCurrentFile().GetName().find(fname)<0:
                fMC = ROOT.TFile.Open(fname)
                sTreeFullMC = fMC.cbmsim
        else: 
            fMC = ROOT.TFile.Open(fname)
            sTreeFullMC = fMC.cbmsim
        rc = sTreeFullMC.GetEvent(n-nInFile)
        if not sTreeMC.MCID[j] < sTreeFullMC.MCTrack.GetEntries():
            print "A",n,nInFile,currentFile
            continue
        if sTreeMC.MCID[j]<0: continue
        trueMu = sTreeFullMC.MCTrack[sTreeMC.MCID[j]]
        mu = trueMu
        mo = sTreeFullMC.MCTrack[mu.GetMotherId()]
        MCRecoDTpx=-999.
        MCRecoDTpy=-999.
        MCRecoDTpz=-999.
        MCRecoDTx =-999.
        MCRecoDTy =-999.
        MCRecoDTz = 3333.
        closestHit = None
        for hit in sTreeFullMC.MufluxSpectrometerPoint:
          if hit.GetTrackID() != sTreeMC.MCID[j]: continue
          if hit.GetZ()<MCRecoDTz:
              MCRecoDTz=hit.GetZ()
              MCRecoDTy=hit.GetY()
              MCRecoDTx=hit.GetX()
              MCRecoDTpx=hit.GetPx()
              MCRecoDTpy=hit.GetPy()
              MCRecoDTpz=hit.GetPz()
        if mu.GetStartZ()>-0.5 and abs(trueMu.GetPdgCode())==13 and MCRecoDTz < 3000. and debug:
            print "strange event",n,nInFile,currentFile,j,sTreeMC.MCID[j]
        theArray = [mu.GetPx(),mu.GetPy(),mu.GetPz(),mu.GetStartX(),mu.GetStartY(),mu.GetStartZ(),mo.GetPdgCode(),trueMu.GetPdgCode(),
                          mu.GetProcID(),mu.GetWeight(),sTreeMC.Chi2[j],sTreeMC.GoodTrack[j],sTreeMC.Px[j],sTreeMC.Py[j],sTreeMC.Pz[j],
                          sTreeMC.x[j],sTreeMC.y[j],sTreeMC.z[j],MCRecoDTpx,MCRecoDTpy,MCRecoDTpz,MCRecoDTx,MCRecoDTy,MCRecoDTz,mcor]
        theTuple = array('f',theArray)
        rc = muons.Fill(theTuple)
    f.cd()
    muons.Write()
def muonEfficiency(E='1GeV',pMin = 5.,pMax=300.,ptMax = 4.,cuts='Chi2<0.7'):
    # python -i $SHIPBUILD/FairShip/charmdet/MufluxNtuple.py -A True -r -t repro
    # possible cuts: '', 'All', 'Chi2<', 'Delx<', 'Dely<'
    hMC['fGen']  = ROOT.TFile("originMCmuons_"+E+".root")
    hMC['ntGen'] = hMC['fGen'].muons
    hMC['fRec']  = ROOT.TFile("recMuons_"+E+".root")
    hMC['ntRec'] = hMC['fRec'].muons
    ROOT.gROOT.cd()
    ut.bookHist(hMC,'energyLoss','energy loss ',100,0.,400.,100,-10.,50.)
    for x in ['','Chi2','Mu']:
       ut.bookHist(hMC,'Pgen'+x,'Pgen '+x,400,0.,400.,100,0.,5.)
       ut.bookHist(hMC,'Prec'+x,'Prec '+x,400,0.,400.,100,0.,5.)
#
    for x in ['','Chi2','Mu']:
       ut.bookHist(hMC,'Ygen'+x,'Ygen '+x,200,0.,10.,100,0.,5.)
       ut.bookHist(hMC,'Yrec'+x,'Yrec '+x,200,0.,10.,100,0.,5.)
#
    for x in ['','Chi2','Mu']:
       ut.bookHist(hMC,'txtygen'+x,'txtygen '+x,100,-0.1,0.1,100,-0.1,0.1)
       ut.bookHist(hMC,'txtyrec'+x,'txtyrec '+x,100,-0.1,0.1,100,-0.1,0.1)

    pMinMu = 17.
    hMC['ntGen'].Draw('sqrt(px*px+py*py):sqrt(px*px+py*py+pz*pz)>>Pgen')
    hMC['ntGen'].Draw('sqrt(px*px+py*py):0.5*log((sqrt(px*px+py*py+pz*pz)+pz)/(sqrt(px*px+py*py+pz*pz)-pz))>>Ygen')
    hMC['ntGen'].Draw('py/pz:px/pz>>txtygen')
    hMC['PgenChi2']=hMC['Pgen'].Clone('PgenChi2')
    hMC['YgenChi2']=hMC['Ygen'].Clone('YgenChi2')
    hMC['txtygenChi2']=hMC['txtygen'].Clone('txtygenChi2')
    hMC['ntGen'].Draw('sqrt(px*px+py*py):sqrt(px*px+py*py+pz*pz)>>PgenMu')
    hMC['ntGen'].Draw('sqrt(px*px+py*py):0.5*log((sqrt(px*px+py*py+pz*pz)+pz)/(sqrt(px*px+py*py+pz*pz)-pz))>>YgenMu','sqrt(px*px+py*py+pz*pz)>'+str(pMinMu))
    hMC['ntGen'].Draw('py/pz:px/pz>>txtygenMu','sqrt(px*px+py*py+pz*pz)>'+str(pMinMu))
    hMC['ntRec'].Draw('sqrt(px*px+py*py+pz*pz)-sqrt(recpx*recpx+recpy*recpy+recpz*recpz):sqrt(px*px+py*py+pz*pz)>>energyLoss')
    # mean loss 7GeV
#
    theCut = "sqrt(recpx*recpx+recpy*recpy+recpz*recpz)>"+str(pMin)+\
           "&&sqrt(recpx*recpx+recpy*recpy+recpz*recpz)<"+str(pMax)+\
           "&&sqrt(recpx*recpx+recpy*recpy)<"+str(ptMax)
    theCut+= "&&abs(muID)==13&&goodTrack>0&&goodTrack<999"
    #muTagged = "&&goodTrack==111&&sqrt(recpx*recpx+recpy*recpy+recpz*recpz)>10.&&sqrt(px*px+py*py+pz*pz)>"+str(pMinMu)
    muTagged = "&&goodTrack==111&&sqrt(px*px+py*py+pz*pz)>"+str(pMinMu)
#
    hMC['ntRec'].Draw('sqrt(px*px+py*py):sqrt(px*px+py*py+pz*pz)>>Prec',theCut)
    hMC['ntRec'].Draw('sqrt(px*px+py*py):0.5*log((sqrt(px*px+py*py+pz*pz)+pz)/(sqrt(px*px+py*py+pz*pz)-pz))>>Yrec',theCut)
    hMC['ntRec'].Draw('py/pz:px/pz>>txtyrec',theCut)

    hMC['ntRec'].Draw('sqrt(px*px+py*py):sqrt(px*px+py*py+pz*pz)>>PrecChi2',theCut+"&&"+cuts.lower())
    hMC['ntRec'].Draw('sqrt(px*px+py*py):0.5*log((sqrt(px*px+py*py+pz*pz)+pz)/(sqrt(px*px+py*py+pz*pz)-pz))>>YrecChi2',theCut+"&&"+cuts.lower())
    hMC['ntRec'].Draw('py/pz:px/pz>>txtyrecChi2',theCut+"&&"+cuts.lower())

    hMC['ntRec'].Draw('sqrt(px*px+py*py):sqrt(px*px+py*py+pz*pz)>>PrecMu',theCut+"&&"+cuts.lower()+"&&goodTrack==111")
    hMC['ntRec'].Draw('sqrt(px*px+py*py):0.5*log((sqrt(px*px+py*py+pz*pz)+pz)/(sqrt(px*px+py*py+pz*pz)-pz))>>YrecMu',theCut+"&&"+cuts.lower()+muTagged)
    hMC['ntRec'].Draw('py/pz:px/pz>>txtyrecMu',theCut+"&&"+cuts.lower()+muTagged)

    tc = hMC['dummy'].cd()
    for u in ['','Chi2','Mu']:
       hMC['Prec'+u].Rebin2D(5,5)
       hMC['Yrec'+u].Rebin2D(5,5)
       hMC['Pgen'+u].Rebin2D(5,5)
       hMC['Ygen'+u].Rebin2D(5,5)
       for c in ['P','Y','txty']:
          for nx in range(0,hMC[c+'gen'+u].GetNbinsX()+2):
             for ny in range(0,hMC[c+'gen'+u].GetNbinsY()+2):
                  if hMC[c+'rec'+u].GetBinContent(nx,ny)>hMC[c+'gen'+u].GetBinContent(nx,ny):
                        hMC[c+'rec'+u].SetBinContent(nx,ny,hMC[c+'gen'+u].GetBinContent(nx,ny))
       hMC['PEff'+u]=ROOT.TEfficiency(hMC['Prec'+u].ProjectionX(),hMC['Pgen'+u].ProjectionX())
       hMC['YEff'+u]=ROOT.TEfficiency(hMC['Yrec'+u].ProjectionX(),hMC['Ygen'+u].ProjectionX())
       hMC['txtyEff'+u]=ROOT.TEfficiency(hMC['txtyrec'+u],hMC['txtygen'+u])
       hMC['txtyEffX'+u]=ROOT.TEfficiency(hMC['txtyrec'+u].ProjectionX(),hMC['txtygen'+u].ProjectionX())
       hMC['txtyEffY'+u]=ROOT.TEfficiency(hMC['txtyrec'+u].ProjectionY(),hMC['txtygen'+u].ProjectionY())
#
       hMC['Peff'+u]=hMC['Prec'+u].ProjectionX('Peff'+u)
       hMC['Peff'+u].Divide(hMC['Pgen'+u].ProjectionX())
       hMC['Yeff'+u]=hMC['Yrec'+u].ProjectionX('Yeff'+u)
       hMC['Yeff'+u].Divide(hMC['Ygen'+u].ProjectionX())
       hMC['P/Pteff'+u]=hMC['Prec'+u].Clone('P/Pteff'+u)
       hMC['P/Pteff'+u].Divide(hMC['Pgen'+u])
       hMC['Y/Pteff'+u]=hMC['Yrec'+u].Clone('Y/Pteff'+u)
       hMC['Y/Pteff'+u].Divide(hMC['Ygen'+u])

       hMC['txtyEff'+u].Draw('colz')
       tc.Update()
       g = hMC['txtyEff'+u].GetPaintedHistogram()
       g.SetMinimum(0.2)
# mirror y
       hMC['tygen'+u] = hMC['txtygen'+u].ProjectionY('tygen'+u)
       hMC['t-ygen'+u] = hMC['tygen'+u].Clone('t-ygen'+u)
       hMC['t-ygen'+u].SetLineColor(ROOT.kMagenta)
       hMC['tyrec'+u] = hMC['txtyrec'+u].ProjectionY('tyrec'+u)
       hMC['t-yrec'+u] = hMC['tyrec'+u].Clone('t-yrec'+u)
       hMC['t-yrec'+u].SetLineColor(ROOT.kMagenta)
# 1 - 50 down
# 51 -100 up
       for n in range(1,101):
          hMC['t-yrec'+u].SetBinContent(n,hMC['tyrec'+u].GetBinContent(101-n))
       hMC['tyEffY'+u]=ROOT.TEfficiency(hMC['tyrec'+u],hMC['tygen'])
       hMC['t-yEffY'+u]=ROOT.TEfficiency(hMC['t-yrec'+u],hMC['t-ygen'])

def repeatFit(X):
#    X = hData['B_ycor1C11']
   hname = X.GetName()
   if not hname.find('CB_')<0:  fitMethod='CB'
   elif not hname.find('B_')<0: fitMethod='B'
   else: fitMethod='G'
   fitOption='SL+'
   minX = 0.5
   maxX = 8.0
   params,funTemplate = getFitDictionary(fitMethod)
   CB = ROOT.TF1(fitMethod,funTemplate['F'],0,10,funTemplate['N'])
   hFun = X.GetFunction(hname.replace(fitMethod,"Fun"+fitMethod))
   funTemplate['Init'](CB,hFun.GetParameter(0))
   for j in range(funTemplate['N']): 
     CB.SetParameter(j,hFun.GetParameter(j))
     CB.SetParError(j,hFun.GetParError(j))
     if hFun.GetParError(j)==0:
         CB.FixParameter(j,hFun.GetParameter(j))
   rc = X.Fit(CB,fitOption,'',minX,maxX)
   fitResult = rc.Get()
   fitResult.MinFcnValue()
   return fitResult,CB

###########################################################
if options.command=='MufluxReco':
    curFile = ''
    if sTreeMC: 
          if sTreeMC.GetEvent(0)>0:
             curFile = sTreeMC.GetCurrentFile().GetName()
    if fdir.find('simulation')==0 or curFile.find('sim')>0: mufluxReco(sTreeMC,hMC,nseq=options.nseq,ncpus=options.ncpus)
    else: mufluxReco(sTreeData,hData)
elif options.command=='RecoEffFunOfOcc':
    RecoEffFunOfOcc()
elif options.command=='invMass':
    curFile = ''
    if sTreeMC: 
          if sTreeMC.GetEvent(0)>0:
             curFile = sTreeMC.GetCurrentFile().GetName()
    if fdir.find('simulation')==0 or curFile.find('sim')>0:
      invMass(sTreeMC,hMC,nseq=options.nseq,ncpus=options.ncpus)
    else:
      invMass(sTreeData,hData)
elif options.command=='JpsiYield' or options.command=='JpsiKinematicsReco' or options.command=='JpsiPolarization':
   ROOT.gROOT.SetBatch(True)
   loadNtuples(ext='')
   tmp = options.JpsiCuts.split(',')
   ptCut = float(tmp[0])
   pmin  = float(tmp[1])
   muID  = int(tmp[2])
   fM    = tmp[3]
   if len(tmp)>4: wW = True
   print "execute command ",options.command,ptCut,pmin,muID,fitMethod
   if options.command=='JpsiYield': 
          JpsiAcceptance(        withCosCSCut=True, ptCut = ptCut, pmin = pmin, pmax = 300., BDTCut=None, muID=muID, fitMethod=fM,withWeight=wW)
   if options.command=='JpsiKinematicsReco': 
          AnalysisNote_JpsiKinematicsReco( ptCut = ptCut, pmin = pmin, pmax = 300., BDTCut=None, muID=muID, fitMethod=fM)
   if options.command=='JpsiPolarization': 
          JpsiPolarization(ptCut = ptCut, pmin = pmin, pmax = 300., BDTCut=None, muID=muID, fitMethod=fM,nBins=20, pTJpsiMin=tmp[4], pTJpsiMax=tmp[5])
elif options.command=='MS':
          studyInvMassResolution(command='MSdata')
elif options.command=='runAll':
   ROOT.gROOT.SetBatch(True)
   runAll(fM=options.fitMethod,DY=options.DYxsec)
elif options.batch:
    ROOT.gROOT.SetBatch(True)
else:
   ut.bookCanvas(hMC,'dummy',' ',900,600,1,1)
