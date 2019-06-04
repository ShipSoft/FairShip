#import yep
import ROOT,os,time,sys,operator,atexit
ROOT.gROOT.ProcessLine('typedef std::unordered_map<int, std::unordered_map<int, std::unordered_map<int, std::vector<MufluxSpectrometerHit*>>>> nestedList;')

from decorators import *
import __builtin__ as builtin
ROOT.gStyle.SetPalette(ROOT.kGreenPink)
PDG = ROOT.TDatabasePDG.Instance()
# -----Timer--------------------------------------------------------
timer = ROOT.TStopwatch()
# stop printing errors
ROOT.gErrorIgnoreLevel = ROOT.kBreak
from argparse import ArgumentParser
import shipunit as u
import rootUtils as ut
from array import array

########
zeroField    = False
DAFfitter    = True
withMaterial = True
MCdata = False
########
MCsmearing=0.04  #  + 0.027**2 -> 0.05
####### 
cuts={}
cuts['Ndf'] = 9
cuts['deltaNdf'] = 2
cuts['yMax']     = 5.
cuts['tot']      = 9.
cuts['hitDist'] = 5.
cuts['minLayersUV'] = 2
cuts['maxClusterSize'] = 2
cuts['delxAtGoliath'] = 8.
cuts['lateArrivalsToT'] = 9999.
# smallest group of channels for RT calibration
cuts['RTsegmentation'] = 12
# for muontagger clustering
cuts['muTaggerCluster_max'] = 6
cuts['muTaggerCluster_sep'] = 15
cuts['muTrackMatchX']= 5.
cuts['muTrackMatchY']= 10.
cuts['muTaggerCluster_grouping'] = 3
cuts["RPCmaxDistance"] = 10.

vbot = ROOT.TVector3()
vtop = ROOT.TVector3()
alignConstants = {}
h={}
log = {}
debug = False

views =  {1:['_x','_u'],2:['_x','_v'],3:['_x'],4:['_x']}
viewsI = {1:[0,1],2:[0,2],3:[0],4:[0]}
viewC = {0:"_x",1:"_u",2:"_v"}

muSources = {'eta':221,'omega':223,'phi':333,'rho0':113,'eta_prime':331}
muSourcesIDs = muSources.values()
rnr       = ROOT.TRandom()
#-----prepare python exit-----------------------------------------------
def pyExit():
 ut.errorSummary()
# atexit.register(pyExit)

parser = ArgumentParser()
parser.add_argument("-f", "--files", dest="listOfFiles", help="list of files comma separated", required=True)
parser.add_argument("-l", "--fileCatalog", dest="catalog", help="list of files in file", default=False)
parser.add_argument("-c", "--cmd", dest="command", help="command to execute", default="")
parser.add_argument("-d", "--Display", dest="withDisplay", help="detector display", default=True)
parser.add_argument("-e", "--eos", dest="onEOS", help="files on EOS", default=False)
parser.add_argument("-u", "--update", dest="updateFile", help="update file", default=False)
parser.add_argument("-i", "--input", dest="inputFile", help="input histo file", default='residuals.root')
parser.add_argument("-g", "--geofile", dest="geoFile", help="input geofile", default='')

options = parser.parse_args()
fnames = []
if options.catalog:
 tmp = open(options.listOfFiles)
 for x in tmp.readlines():
  fname = x.replace('\n','')
  if fname.find("root")<0:continue
  f=ROOT.TFile.Open(fname)
  sTree = f.cbmsim
  if not sTree.GetBranch("FitTracks"): 
   print "does not contain FitTracks",fname
   f.Close()
   continue
  fnames.append(fname)
  fnames.append(x.replace('\n',''))
 tmp.close()
else:
 fnames = options.listOfFiles.split(',')
fname = fnames[0]
if options.updateFile:
 f=ROOT.TFile(fname,'update')
 sTree=f.Get('cbmsim')
 if not sTree: 
   print "Problem with updateFile",f
   exit(-1)
else:
 sTree = ROOT.TChain('cbmsim')
 for f in fnames: 
  print "add ",f
  if options.onEOS: sTree.Add(os.environ['EOSSHIP']+f)
  else:             sTree.Add(f)

rnames = []
for fname in fnames:
 rnames.append(fname[fname.rfind('/')+1:])
rname = rnames[0]
#sTree.SetMaxVirtualSize(300000)

from ShipGeoConfig import ConfigRegistry
if options.geoFile=="":
 ShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/charm-geometry_config.py")
else:
 from ShipGeoConfig import ConfigRegistry
 from rootpyPickler import Unpickler
#load Shipgeo dictionary
 fgeo = ROOT.TFile.Open(options.geoFile)
 upkl    = Unpickler(options.geoFile)
 ShipGeo = upkl.load('ShipGeo')
builtin.ShipGeo = ShipGeo
import charmDet_conf
run = ROOT.FairRunSim()
run.SetName("TGeant4")  # Transport engine
run.SetOutputFile(ROOT.TMemFile('output', 'recreate'))  # Output file
run.SetUserConfig("g4Config_basic.C") # geant4 transport not used, only needed for creating VMC field
rtdb = run.GetRuntimeDb()
modules = charmDet_conf.configure(run,ShipGeo)
# -----Create geometry----------------------------------------------
run.Init()
sGeo = ROOT.gGeoManager
nav = sGeo.GetCurrentNavigator()
top = sGeo.GetTopVolume()
top.SetVisibility(0)
if options.withDisplay:
 try: top.Draw('ogl')
 except: pass

saveGeofile = False
import saveBasicParameters
if saveGeofile:
 run.CreateGeometryFile("muflux_geofile.root")
# save ShipGeo dictionary in geofile
 saveBasicParameters.execute("muflux_geofile.root",ShipGeo)

# alignment
xpos = {}
xposb = {}
ypos = {}
yposb = {}
zpos = {}
residuals = [0.]*24
# positions are relative to the top / bottom end plates of a station, corrected from survey positions with known offset in y, 
# 2cm + length of the bolt 150mm on the top and 50mm on the bottom
Nchannels = {1:12,2:12,3:48,4:48}

#survey
survey = {} # X survey[xxx][1] Y survey[xxx][2] Z survey[xxx][0]
daniel = {}
# For T1 and 2, the survey target is placed above/below the endplates, offset in y. 
# For T3 it is placed 7cm in front and for T4 7cm behind the endplate, so there is an offset in z
survey['T1_MA_01']=[ 9.0527, 0.2443, 0.7102 ]
daniel['T1_MA_01']=[244.30,531.85,9052.70]
survey['T1_MA_02']=[ 9.0502, -0.2078, 0.7092  ]
daniel['T1_MA_02']=[-207.80,530.85,9050.20]
survey['T1_MA_03']=[ 9.0564, -0.2075, -0.6495  ]
daniel['T1_MA_03']=[-207.50,-570.85,9056.40]
survey['T1_MA_04']=[ 9.0578, 0.2436, -0.6503  ]
daniel['T1_MA_04']=[ 243.60,-571.65,9057.80]
survey['T1_MB_01']=[ 9.5376, -0.5044, 0.5647  ]
daniel['T1_MB_01']=[ -504.54,564.60,9537.42  ]
survey['T1_MB_02']=[ 9.5388, -0.7293, 0.1728  ]
daniel['T1_MB_02']=[ -729.38,172.83,9539.00  ]
survey['T1_MB_03']=[ 9.5420, 0.4446, -0.4995  ]
daniel['T1_MB_03']=[ 444.63,-499.49,9541.94  ]
survey['T1_MB_04']=[ 9.5435, 0.6693, -0.1073  ]
daniel['T1_MB_04']=[ 669.28,-107.28,9543.47  ]
survey['T2_MC_01']=[ 9.7424, 0.7588, 0.1730  ]
daniel['T2_MC_01']=[ 758.84, 173.03, 9742.35  ]
survey['T2_MC_02']=[ 9.7433, 0.5327, 0.5657  ]
daniel['T2_MC_02']=[532.67, 565.72, 9743.27 ]
survey['T2_MC_03']=[ 9.7381, -0.6374, -0.1104  ]
daniel['T2_MC_03']=[-637.45, -110.36, 9738.21 ]
survey['T2_MC_04']=[ 9.7409, -0.4121, -0.5021  ]
daniel['T2_MC_04']=[-412.30,-501.89, 9740.98  ]
survey['T2_MD_01']=[ 10.2314, 0.2385, 0.7078  ]
daniel['T2_MD_01']=[ 238.50, 530.50, 10231.40  ]
survey['T2_MD_02']=[ 10.2276, -0.2121, 0.7087  ]
daniel['T2_MD_02']=[ -212.10,531.40,10227  ]
survey['T2_MD_03']=[ 10.2285, -0.2157, -0.6488  ]
daniel['T2_MD_03']=[ -215.70, -570.35, 10228.50 ]
survey['T2_MD_04']=[ 10.2302, 0.2361, -0.6495  ]
daniel['T2_MD_04']=[ 236.10, -575.05, 10230.20  ]
survey['T3_B01']=[  14.5712,  0.9285, -0.6818 ]
daniel['T3_B01']=[  928.59, -681.74, 14641.10 ]
survey['T3_B02']=[  14.5704,  0.5926, -0.6823 ]
daniel['T3_B02']=[  592.62, -682.23, 14640.30 ]
survey['T3_B03']=[  14.5699,  0.4245, -0.6844 ]
daniel['T3_B03']=[  424.52, -684.35, 14639.90 ]
survey['T3_B04']=[  14.5686,  0.0884, -0.6854 ]
daniel['T3_B04']=[  88.46, -685.39, 14638.60 ]
survey['T3_B05']=[  14.5685, -0.0813, -0.6836 ]
daniel['T3_B05']=[  -81.23, -683.57, 14638.50 ]
survey['T3_B06']=[  14.5694, -0.4172, -0.6840 ]
daniel['T3_B06']=[  -417.09, -683.99, 14639.30 ]
survey['T3_B07']=[  14.5696, -0.5859, -0.6864 ]
daniel['T3_B07']=[  -585.80, -686.33, 14639.60 ]
survey['T3_B08']=[  14.5693, -0.9216, -0.6845 ]
daniel['T3_B08']=[  -921.58, -684.47, 14639.20 ]
survey['T3_T01']=[  14.5733,  0.9253, 0.8931 ]
daniel['T3_T01']=[  925.40, 893.09,14643.20 ]
survey['T3_T02']=[  14.5741,  0.5893, 0.8914 ]
daniel['T3_T02']=[  589.42, 891.36,14644.10 ]
survey['T3_T03']=[  14.5746,  0.4212, 0.8907 ]
daniel['T3_T03']=[  421.23, 890.75, 14644.60 ]
survey['T3_T04']=[  14.5750,  0.0852, 0.8905 ]
daniel['T3_T04']=[  85.28, 890.55, 14645.00 ]
survey['T3_T05']=[  14.5756, -0.0839, 0.8899 ]
daniel['T3_T05']=[  -83.89, 889.94, 14645.50 ]
survey['T3_T06']=[  14.5769, -0.4198, 0.8888 ]
daniel['T3_T06']=[  -419.69, 888.85, 14646.90 ]
survey['T3_T07']=[  14.5781, -0.5896, 0.8908 ]
daniel['T3_T07']=[  -589.56, 890.77, 14648.10 ]
survey['T3_T08']=[  14.5812, -0.9256, 0.8896 ]
daniel['T3_T08']=[  -925.57, 889.62, 14651.20 ]
survey['T4_B01']=[  16.5436,  0.9184, -0.6848 ]
daniel['T4_B01']=[  918.35,-684.86,16473.60 ]
survey['T4_B02']=[  16.5418,  0.5824, -0.6867 ]
daniel['T4_B02']=[  582.36, -686.73, 16471.90 ]
survey['T4_B03']=[  16.5408,  0.4144, -0.6875 ]
daniel['T4_B03']=[  414.37, -687.52, 16470.90 ]
survey['T4_B04']=[  16.5389,  0.0785, -0.6883 ]
daniel['T4_B04']=[  78.51, -688.32, 16468.90 ]
survey['T4_B05']=[  16.5389, -0.0888, -0.6890 ]
daniel['T4_B05']=[  -88.80, -689.05, 16468.90 ]
survey['T4_B06']=[  16.5396, -0.4247, -0.6884 ]
daniel['T4_B06']=[  -424.75, -688.49, 16469.60 ]
survey['T4_B07']=[  16.5400, -0.5936, -0.6888 ]
daniel['T4_B07']=[  -593.65, -688.85, 16470.00 ]
survey['T4_B08']=[  16.5402, -0.9295, -0.6877 ]
daniel['T4_B08']=[  -929.54, -687.77, 16470.20 ]
survey['T4_T01']=[  16.5449,  0.9207, 0.8899 ]
daniel['T4_T01']=[  920.70,889.81,16475.00  ]
survey['T4_T02']=[  16.5456,  0.5845, 0.8884 ]
daniel['T4_T02']=[  584.44, 888.30, 16475.70  ]
survey['T4_T03']=[  16.5460,  0.4168, 0.8873 ]
daniel['T4_T03']=[  416.74, 887.26, 16476.10  ]
survey['T4_T04']=[  16.5474,  0.0804, 0.8862 ]
daniel['T4_T04']=[  80.34, 886.14, 16477.50 ]
survey['T4_T05']=[  16.5480, -0.0876, 0.8862 ]
daniel['T4_T05']=[  -87.55, 886.10, 16478.00 ]
survey['T4_T06']=[  16.5497, -0.4234, 0.8862 ]
daniel['T4_T06']=[  -423.40, 886.18, 16479.80 ]
survey['T4_T07']=[  16.5507, -0.5919, 0.8866 ]
daniel['T4_T07']=[  -591.89, 886.58, 16480.80 ]
survey['T4_T08']=[  16.5518, -0.9280, 0.8869 ]
daniel['T4_T08']=[  -928.06, 886.85, 16481.80 ]

survey['RPC1_L']= [ 17.6823, 1.1611, 1.1909]
survey['RPC1_R']= [ 17.6864, -1.2679, 1.2145 ]
survey['RPC2_L']= [ 18.6319, 1.1640, 1.1926 ]
survey['RPC2_R']= [ 18.6360, -1.2650, 1.2065 ]
survey['RPC3_L']= [ 19.1856, 1.1644, 1.1933 ]
survey['RPC3_R']= [ 19.1902, -1.2646, 1.2021 ]
survey['RPC4_L']= [ 19.7371, 1.1610, 1.1938 ]
survey['RPC4_R']= [ 19.7410, -1.2670, 1.1979 ]
survey['RPC5_L']= [ 20.2852, 1.1677, 1.1945 ]
survey['RPC5_R']= [ 20.2891, -1.2614, 1.1943 ]

Lcorrection={}
# length of the bolt 150mm on the top and 50mm on the bottom
Lcorrection['T1_MA_01'] = -(20.+150.+8.65)/10.
Lcorrection['T1_MA_02'] = -(20.+150.+8.65)/10.
Lcorrection['T1_MA_03'] = (20.+50.+8.35)/10.
Lcorrection['T1_MA_04'] = (20.+50.+8.35)/10.
Lcorrection['T1_MB_01'] = -(20.+150.)/10.
Lcorrection['T1_MB_02'] = -(20.+150.)/10.
Lcorrection['T1_MB_03'] = (20.+50.)/10.
Lcorrection['T1_MB_04'] = (20.+50.)/10.
Lcorrection['T2_MC_01'] = -(20.+150.)/10.
Lcorrection['T2_MC_02'] = -(20.+150.)/10.
Lcorrection['T2_MC_03'] = (20.+50.)/10.
Lcorrection['T2_MC_04'] = (20.+50.)/10.
Lcorrection['T2_MD_01'] = -(20.+150.+7.3)/10.
Lcorrection['T2_MD_02'] = -(20.+150.+7.3)/10.
Lcorrection['T2_MD_03'] = (20.+50.+8.45)/10.   # 8.45 or 4.45
Lcorrection['T2_MD_04'] = (20.+50.+8.45)/10.   # 8.45 or 4.45

surveyXYZ = {}
for s in survey: 
  surveyXYZ[s]=[survey[s][1]*100.,survey[s][2]*100.,survey[s][0]*100.]
for s in daniel: daniel[s]=[daniel[s][0]/10.,daniel[s][1]/10.,daniel[s][2]/10.]

Langle={}
for s in ['T1_MA_','T1_MB_','T2_MC_','T2_MD_']:
   delx = surveyXYZ[s+'01'][0]-surveyXYZ[s+'04'][0]
   dely = surveyXYZ[s+'01'][1]-surveyXYZ[s+'04'][1]
   Langle[s+'01-04'] = ROOT.TMath.ATan2(dely,delx)
   delx = surveyXYZ[s+'02'][0]-surveyXYZ[s+'03'][0]
   dely = surveyXYZ[s+'02'][1]-surveyXYZ[s+'03'][1]
   Langle[s+'02-03'] = ROOT.TMath.ATan2(dely,delx)
for s in survey: 
  if s.find('T1')<0 and s.find('T2')<0: continue
  if s.find('01')>0:   a = s.replace('01','01-04')
  elif s.find('04')>0: a = s.replace('04','01-04')
  elif s.find('02')>0: a = s.replace('02','02-03')
  elif s.find('03')>0: a = s.replace('03','02-03')
  #surveyXYZ[s][0] = surveyXYZ[s][0] + Lcorrection[s]*ROOT.TMath.Cos(Langle[a])
  #surveyXYZ[s][1] = surveyXYZ[s][1] + Lcorrection[s]*ROOT.TMath.Sin(Langle[a])

# cross checks
ut.bookHist(h,'lengthCalibration','length Calibration',100,-0.2,0.2)
if debug:
 for s in ['T1_MA_0','T2_MD_0']:
  delta = daniel[s+'1'][0]-daniel[s+'2'][0]
  print s,'top',delta-45.2
  rc=h['lengthCalibration'].Fill(delta-45.2)
  delta = daniel[s+'4'][0]-daniel[s+'3'][0]
  rc=h['lengthCalibration'].Fill(delta-45.2)
  print s,'bottom',delta-45.2
for k in range(4):
 for s in ['T3_T0','T4_T0']:
  delta = daniel[s+str(2*k+1)][0]-daniel[s+str(2*k+2)][0]
  rc=h['lengthCalibration'].Fill(delta-8.*4.2)


rn ={}
rn['T1_MB_01'] = [21.55,72.60]    # top left = 1
rn['T1_MB_02'] = [-23.65,72.60]   # top right = 2
rn['T1_MB_04'] = [21.55,-62.60]   # bottom left = 4
rn['T1_MB_03'] = [-23.65,-62.60]  # bottom right = 3
rn['T2_MC_01'] = rn['T1_MB_01'] 
rn['T2_MC_02'] = rn['T1_MB_02']
rn['T2_MC_04'] = rn['T1_MB_04']
rn['T2_MC_03'] = rn['T1_MB_03']

#overall z positioning
#T1X:
zpos['T1X'] = (daniel['T1_MA_01'][2]+daniel['T1_MA_02'][2]+daniel['T1_MA_03'][2]+daniel['T1_MA_04'][2])/4. + 3.03
ypos['T1X'] = [(daniel['T1_MA_01'][1]+daniel['T1_MA_02'][1])/2.,(daniel['T1_MA_04'][1]+daniel['T1_MA_03'][1])/2.]
test = ROOT.MufluxSpectrometerHit(10002012,0.)
test.MufluxSpectrometerEndPoints(vbot,vtop)
deltaZ = zpos['T1X']-(vbot[2]+vtop[2])/2. 
n = 10002012
start = daniel['T1_MA_01'][0] # (daniel['T1_MA_01'][0]+daniel['T1_MA_04'][0])/2. bottom survey measurements do not match nominal distance
delta = (start - (daniel['T1_MA_02'][0]+daniel['T1_MA_03'][0])/2.-1.1-2.1) / 10.
delta = 4.2
for i in range(12): 
 xpos[n-i] = start - delta * i
 ypos[n-i] = ypos['T1X']
 zpos[n-i] = zpos['T1X']-deltaZ
n = 10012001
start =  daniel['T1_MA_02'][0] +1.1 #   (daniel['T1_MA_02'][0]+daniel['T1_MA_03'][0])/2. +1.1
for i in range(12): 
 xpos[n+i] = start + delta * i
 ypos[n+i] = ypos['T1X']
 zpos[n+i] = zpos['T1X']+3.64-deltaZ
n = 10102001
start = start -1.1 #  (daniel['T1_MA_02'][0]+daniel['T1_MA_03'][0])/2.
for i in range(12): 
 xpos[n+i] = start + delta * i
 ypos[n+i] = ypos['T1X']
 zpos[n+i] = zpos['T1X']+3.64+4.06-deltaZ
n = 10112001
start = start - 2.1 #  (daniel['T1_MA_02'][0]+daniel['T1_MA_03'][0])/2. - 2.1
for i in range(12): 
 xpos[n+i] = start + delta * i
 ypos[n+i] = ypos['T1X']
 zpos[n+i] = zpos['T1X']+3.64+4.06+3.64-deltaZ

#T1u: take survey corrected points
zpos['T1U'] = (daniel['T1_MB_01'][2]+daniel['T1_MB_02'][2]+daniel['T1_MB_03'][2]+daniel['T1_MB_04'][2])/4. - 3.03 -3.64 -4.06 -3.64
angleu1 = ROOT.TMath.ATan2((daniel['T1_MB_01'][0]-daniel['T1_MB_04'][0]),(daniel['T1_MB_01'][1]-daniel['T1_MB_04'][1]))
angleu2 = ROOT.TMath.ATan2((daniel['T1_MB_02'][0]-daniel['T1_MB_03'][0]),(daniel['T1_MB_02'][1]-daniel['T1_MB_03'][1]))
angleu = (angleu1+angleu2)/2.

angle = -angleu # 60.208/180.*ROOT.TMath.Pi()  ???
tx,ty=0,0
for i in range(1,5):
 p = 'T1_MB_0'+str(i)
 tx += daniel[p][0] - (rn[p][0]*ROOT.TMath.Cos(angle) - rn[p][1]*ROOT.TMath.Sin(angle))
 ty += daniel[p][1] - (rn[p][0]*ROOT.TMath.Sin(angle) + rn[p][1]*ROOT.TMath.Cos(angle))
 if debug: print "%s: %5.4F, %5.4F"%(p, (daniel[p][0] - (rn[p][0]*ROOT.TMath.Cos(angle) - rn[p][1]*ROOT.TMath.Sin(angle)))*10,\
                        (daniel[p][1] - (rn[p][0]*ROOT.TMath.Sin(angle) + rn[p][1]*ROOT.TMath.Cos(angle)))*10)
tx=tx/4.
ty=ty/4.

L =  110.
start = (rn['T1_MB_01'][0]+rn['T1_MB_04'][0])/2.
delta = (start - ( (rn['T1_MB_02'][0]+rn['T1_MB_03'][0])/2.+1.1+2.1) )/ 10.
delta = 4.2

n = 11002012
for i in range(12): 
 xnom = start - delta * i
 ynom = L/2.
 xpos[n-i] = xnom *ROOT.TMath.Cos(angle) - ynom*ROOT.TMath.Sin(angle) + tx
 ypos[n-i] = xnom *ROOT.TMath.Sin(angle) + ynom*ROOT.TMath.Cos(angle) + ty
 ynom = -L/2.
 xposb[n-i] = xnom *ROOT.TMath.Cos(angle) - ynom*ROOT.TMath.Sin(angle) + tx
 yposb[n-i] = xnom *ROOT.TMath.Sin(angle) + ynom*ROOT.TMath.Cos(angle) + ty
 zpos[n-i] = zpos['T1U']-deltaZ
n = 11012001
start = (rn['T1_MB_02'][0]+rn['T1_MB_03'][0])/2.+1.1
for i in range(12): 
 xnom = start + delta * i
 ynom = L/2.
 xpos[n+i] = xnom *ROOT.TMath.Cos(angle) - ynom*ROOT.TMath.Sin(angle) + tx
 ypos[n+i] = xnom *ROOT.TMath.Sin(angle) + ynom*ROOT.TMath.Cos(angle) + ty
 ynom = -L/2.
 xposb[n+i] = xnom *ROOT.TMath.Cos(angle) - ynom*ROOT.TMath.Sin(angle) + tx
 yposb[n+i] = xnom *ROOT.TMath.Sin(angle) + ynom*ROOT.TMath.Cos(angle) + ty
 zpos[n+i] = zpos['T1U']+3.64-deltaZ
n = 11102001
start = (rn['T1_MB_02'][0]+rn['T1_MB_03'][0])/2.
for i in range(12): 
 xnom = start + delta * i
 ynom = L/2.
 xpos[n+i] = xnom *ROOT.TMath.Cos(angle) - ynom*ROOT.TMath.Sin(angle) + tx
 ypos[n+i] = xnom *ROOT.TMath.Sin(angle) + ynom*ROOT.TMath.Cos(angle) + ty
 ynom = -L/2.
 xposb[n+i] = xnom *ROOT.TMath.Cos(angle) - ynom*ROOT.TMath.Sin(angle) + tx
 yposb[n+i] = xnom *ROOT.TMath.Sin(angle) + ynom*ROOT.TMath.Cos(angle) + ty
 zpos[n+i] = zpos['T1U']+3.64+4.06 -deltaZ
n = 11112001
start = start - 2.1
for i in range(12): 
 xnom = start + delta * i
 ynom = L/2.
 xpos[n+i] = xnom *ROOT.TMath.Cos(angle) - ynom*ROOT.TMath.Sin(angle) + tx
 ypos[n+i] = xnom *ROOT.TMath.Sin(angle) + ynom*ROOT.TMath.Cos(angle) + ty
 ynom = -L/2.
 xposb[n+i] = xnom *ROOT.TMath.Cos(angle) - ynom*ROOT.TMath.Sin(angle) + tx
 yposb[n+i] = xnom *ROOT.TMath.Sin(angle) + ynom*ROOT.TMath.Cos(angle) + ty
 zpos[n+i] = zpos['T1U']+3.64+4.06+3.64-deltaZ

# T2X:
zpos['T2X'] = (daniel['T2_MD_01'][2]+daniel['T2_MD_02'][2]+daniel['T2_MD_03'][2]+daniel['T2_MD_04'][2])/4. - 3.03 - 3.64 - 4.06 - 3.6480
ypos['T2X'] = [(daniel['T2_MD_01'][1]+daniel['T2_MD_02'][1])/2.,(daniel['T2_MD_04'][1]+daniel['T2_MD_03'][1])/2.]
n = 21112001
start = daniel['T2_MD_03'][0] # (daniel['T2_MD_02'][0]+daniel['T2_MD_03'][0])/2.  top x survey do not match nominal distance, makes 1.8mm difference to FairShip
delta = ( (daniel['T2_MD_01'][0]+daniel['T2_MD_04'][0])/2. - (start+1.1-2.1)) / 11.
delta = 4.2  # nominal distance, more reliable

for i in range(12): 
 xpos[n+i] = start + delta * i
 ypos[n+i] = ypos['T2X']
 zpos[n+i] = zpos['T2X']+3.64+4.06+3.64-deltaZ
n = 21102001
start = start - 2.1
for i in range(12): 
 xpos[n+i] = start + delta * i
 ypos[n+i] = ypos['T2X']
 zpos[n+i] = zpos['T2X']+3.64+4.06-deltaZ
n = 21012001
start = start + 1.1
for i in range(12): 
 xpos[n+i] = start + delta * i
 ypos[n+i] = ypos['T2X']
 zpos[n+i] = zpos['T2X']+3.64-deltaZ
n = 21002001
start = start + 2.1
for i in range(12): 
 xpos[n+i] = start + delta * i
 ypos[n+i] = ypos['T2X']
 zpos[n+i] = zpos['T2X']-deltaZ

#T2v:take survey corrected points
anglev1 = ROOT.TMath.ATan2((daniel['T2_MC_02'][0]-daniel['T2_MC_03'][0]),(daniel['T2_MC_02'][1]-daniel['T2_MC_03'][1]))
anglev2 = ROOT.TMath.ATan2((daniel['T2_MC_01'][0]-daniel['T2_MC_04'][0]),(daniel['T2_MC_01'][1]-daniel['T2_MC_04'][1]))
anglev = (anglev1+anglev2)/2.

zpos['T2V'] = (daniel['T2_MC_01'][2]+daniel['T2_MC_02'][2]+daniel['T2_MC_03'][2]+daniel['T2_MC_04'][2])/4. + 3.03
L =  110.
angle = -anglev # ???
tx,ty=0,0
for i in range(1,5):
 p = 'T2_MC_0'+str(i)
 tx += daniel[p][0] - (rn[p][0]*ROOT.TMath.Cos(angle) - rn[p][1]*ROOT.TMath.Sin(angle))
 ty += daniel[p][1] - (rn[p][0]*ROOT.TMath.Sin(angle) + rn[p][1]*ROOT.TMath.Cos(angle))
 if debug: print "%s: %5.4F, %5.4F"%(p, (daniel[p][0] - (rn[p][0]*ROOT.TMath.Cos(angle) - rn[p][1]*ROOT.TMath.Sin(angle)))*10,\
                        (daniel[p][1] - (rn[p][0]*ROOT.TMath.Sin(angle) + rn[p][1]*ROOT.TMath.Cos(angle)))*10)
tx=tx/4.
ty=ty/4.

n = 20112001
start = (rn['T2_MC_02'][0]+rn['T2_MC_03'][0])/2.
delta = ((rn['T2_MC_01'][0]+rn['T2_MC_04'][0])/2. - ( (rn['T2_MC_02'][0]+rn['T2_MC_03'][0])/2.-2.1+1.1)) / 11.
delta = 4.2

for i in range(12): 
 xnom = start + delta * i
 ynom = L/2.
 xpos[n+i] = xnom *ROOT.TMath.Cos(angle) - ynom*ROOT.TMath.Sin(angle) + tx
 ypos[n+i] = xnom *ROOT.TMath.Sin(angle) + ynom*ROOT.TMath.Cos(angle) + ty
 ynom = -L/2.
 xposb[n+i] = xnom *ROOT.TMath.Cos(angle) - ynom*ROOT.TMath.Sin(angle) + tx
 yposb[n+i] = xnom *ROOT.TMath.Sin(angle) + ynom*ROOT.TMath.Cos(angle) + ty
 zpos[n+i] = zpos['T2V']+3.64+4.06+3.64-deltaZ
n = 20102001
start = start - 2.1
for i in range(12): 
 xnom = start + delta * i
 ynom = L/2.
 xpos[n+i] = xnom *ROOT.TMath.Cos(angle) - ynom*ROOT.TMath.Sin(angle) + tx
 ypos[n+i] = xnom *ROOT.TMath.Sin(angle) + ynom*ROOT.TMath.Cos(angle) + ty
 ynom = -L/2.
 xposb[n+i] = xnom *ROOT.TMath.Cos(angle) - ynom*ROOT.TMath.Sin(angle) + tx
 yposb[n+i] = xnom *ROOT.TMath.Sin(angle) + ynom*ROOT.TMath.Cos(angle) + ty
 zpos[n+i] = zpos['T2V']+3.64+4.06-deltaZ
n = 20012012
start = (rn['T2_MC_01'][0]+rn['T2_MC_04'][0])/2.
for i in range(12): 
 xnom = start - delta * i
 ynom = L/2.
 xpos[n-i] = xnom *ROOT.TMath.Cos(angle) - ynom*ROOT.TMath.Sin(angle) + tx
 ypos[n-i] = xnom *ROOT.TMath.Sin(angle) + ynom*ROOT.TMath.Cos(angle) + ty
 ynom = -L/2.
 xposb[n-i] = xnom *ROOT.TMath.Cos(angle) - ynom*ROOT.TMath.Sin(angle) + tx
 yposb[n-i] = xnom *ROOT.TMath.Sin(angle) + ynom*ROOT.TMath.Cos(angle) + ty
 zpos[n-i] = zpos['T2V']+3.64-deltaZ
n = 20002012
start = start + 2.1
for i in range(12): 
 xnom = start - delta * i
 ynom = L/2.
 xpos[n-i] = xnom *ROOT.TMath.Cos(angle) - ynom*ROOT.TMath.Sin(angle) + tx
 ypos[n-i] = xnom *ROOT.TMath.Sin(angle) + ynom*ROOT.TMath.Cos(angle) + ty
 ynom = -L/2.
 xposb[n-i] = xnom *ROOT.TMath.Cos(angle) - ynom*ROOT.TMath.Sin(angle) + tx
 yposb[n-i] = xnom *ROOT.TMath.Sin(angle) + ynom*ROOT.TMath.Cos(angle) + ty
 zpos[n-i] = zpos['T2V']-deltaZ

#T3aX:
zpos['T3aX'] = (( daniel['T3_T01'][2] + daniel['T3_B01'][2] + daniel['T3_T02'][2] + daniel['T3_B02'][2])/4. + 4.33)
ypos['T3aX'] = [(daniel['T3_T01'][1]+daniel['T3_T02'][1])/2.,(daniel['T3_B01'][1]+daniel['T3_B02'][1])/2.]

delta = ( (daniel['T3_T01'][0] + daniel['T3_B01'][0])/2. - (daniel['T3_T02'][0] + daniel['T3_B02'][0])/2. )/8.
delta = 4.2

n = 30002037
start = (daniel['T3_T02'][0] + daniel['T3_B02'][0])/2. -delta +2.1 -delta
for i in range(12): 
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T3aX']-deltaZ
n = 30012037
start = (daniel['T3_T02'][0] + daniel['T3_B02'][0])/2. -delta
for i in range(12): 
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T3aX']+3.64-deltaZ
n = 30102037
start = (daniel['T3_T02'][0] + daniel['T3_B02'][0])/2. -delta -1.1
for i in range(12): 
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T3aX']+3.64+4.06-deltaZ
n = 30112037
start = (daniel['T3_T02'][0] + daniel['T3_B02'][0])/2. -delta -1.1 -2.1
for i in range(12): 
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T3aX']+3.64+4.06+3.64-deltaZ

#T3bX:
zpos['T3bX'] = (( daniel['T3_T03'][2] + daniel['T3_B03'][2] + daniel['T3_T04'][2] + daniel['T3_B04'][2])/4. + 4.33)
ypos['T3bX'] = [(daniel['T3_T03'][1]+daniel['T3_T04'][1])/2.,(daniel['T3_B03'][1]+daniel['T3_B04'][1])/2.]

delta = ( (daniel['T3_T03'][0] + daniel['T3_B03'][0])/2. - (daniel['T3_T04'][0] + daniel['T3_B04'][0])/2. )/8.
delta = 4.2

n = 30002025
start =  (daniel['T3_T04'][0] + daniel['T3_B04'][0])/2.  -delta +2.1 -delta
for i in range(12): 
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T3bX']-deltaZ
n = 30012025
start =  (daniel['T3_T04'][0] + daniel['T3_B04'][0])/2.  -delta 
for i in range(12): 
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T3bX']+3.64-deltaZ
n = 30102025
start =  (daniel['T3_T04'][0] + daniel['T3_B04'][0])/2.  -delta -1.1
for i in range(12):
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T3bX']+3.64+4.06-deltaZ
n = 30112025
start =  (daniel['T3_T04'][0] + daniel['T3_B04'][0])/2.  -delta -1.1 -2.1
for i in range(12):
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T3bX']+3.64+4.06+3.64-deltaZ

#T3cX:
zpos['T3cX'] = (( daniel['T3_T05'][2] + daniel['T3_B05'][2] + daniel['T3_T06'][2] + daniel['T3_B06'][2])/4. + 4.33)
ypos['T3cX'] = [(daniel['T3_T05'][1]+daniel['T3_T06'][1])/2.,(daniel['T3_B05'][1]+daniel['T3_B06'][1])/2.]

delta = ( (daniel['T3_T05'][0] + daniel['T3_B05'][0])/2. - (daniel['T3_T06'][0] + daniel['T3_B06'][0])/2. )/8.
delta = 4.2

n = 30002013
start = (daniel['T3_T06'][0] + daniel['T3_B06'][0])/2. -delta +2.1 -delta
for i in range(12):
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T3cX']-deltaZ
n = 30012013
start = (daniel['T3_T06'][0] + daniel['T3_B06'][0])/2. -delta 
for i in range(12):
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T3cX']+3.64-deltaZ
n = 30102013
start = start -1.1
for i in range(12):
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T3cX']+3.64+4.06-deltaZ
n = 30112013
start = start -2.1
for i in range(12):
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T3cX']+3.64+4.06+3.64-deltaZ

#T3dX:
zpos['T3dX'] = (( daniel['T3_T07'][2] + daniel['T3_B07'][2] + daniel['T3_T08'][2] + daniel['T3_B08'][2])/4. + 4.33)
ypos['T3dX'] = [(daniel['T3_T07'][1]+daniel['T3_T08'][1])/2.,(daniel['T3_B07'][1]+daniel['T3_B08'][1])/2.]

delta = ( (daniel['T3_T07'][0] + daniel['T3_B07'][0])/2. - (daniel['T3_T08'][0] + daniel['T3_B08'][0])/2. )/8.
delta = 4.2


n = 30002001
start = (daniel['T3_T08'][0] + daniel['T3_B08'][0])/2. -delta +2.1 -delta
for i in range(12): 
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T3dX'] -deltaZ
n = 30012001
start = (daniel['T3_T08'][0] + daniel['T3_B08'][0])/2. -delta 
for i in range(12):
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T3dX']+3.64-deltaZ
n = 30102001
start =(daniel['T3_T08'][0] + daniel['T3_B08'][0])/2. -delta -1.1
for i in range(12):
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T3dX']+3.64+4.06-deltaZ
n = 30112001
start = (daniel['T3_T08'][0] + daniel['T3_B08'][0])/2. -delta -1.1 -2.1
for i in range(12):
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T3dX']+3.64+4.06+3.64-deltaZ

#T4aX:
zpos['T4aX'] = (( daniel['T4_T01'][2] + daniel['T4_B01'][2] + daniel['T4_T02'][2] + daniel['T4_B02'][2])/4. - 4.33 -3.64-4.06-3.64)
ypos['T4aX'] = [(daniel['T4_T01'][1]+daniel['T4_T02'][1])/2.,(daniel['T4_B01'][1]+daniel['T4_B02'][1])/2.]

delta = ( (daniel['T4_T01'][0] + daniel['T4_B01'][0])/2. - (daniel['T4_T02'][0] + daniel['T4_B02'][0])/2. )/8.
delta = 4.2

n = 40002048
start = (daniel['T4_T02'][0] + daniel['T4_B02'][0])/2.  -delta +45.2
for i in range(12):
 xpos[n-i] = start - delta * i
 zpos[n-i] = zpos['T4aX']-deltaZ
n = 40012037
start = (daniel['T4_T02'][0] + daniel['T4_B02'][0])/2.  -delta +1.1
for i in range(12):
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T4aX']+3.64-deltaZ
n = 40102037
start = (daniel['T4_T02'][0] + daniel['T4_B02'][0])/2.  -delta  
for i in range(12):
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T4aX']+3.64+4.06-deltaZ
n = 40112037
start = (daniel['T4_T02'][0] + daniel['T4_B02'][0])/2.  -delta  -2.1
for i in range(12):
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T4aX']+3.64+4.06+3.64-deltaZ

#T4bX:
zpos['T4bX'] = (( daniel['T4_T03'][2] + daniel['T4_B03'][2] + daniel['T4_T04'][2] + daniel['T4_B04'][2])/4. - 4.33 -3.64-4.06-3.64)
ypos['T4bX'] = [(daniel['T4_T03'][1]+daniel['T4_T04'][1])/2.,(daniel['T4_B03'][1]+daniel['T4_B04'][1])/2.]

delta = ( (daniel['T4_T03'][0] + daniel['T4_B03'][0])/2. - (daniel['T4_T04'][0] + daniel['T4_B04'][0])/2. )/8.
delta = 4.2

n = 40002036
start = (daniel['T4_T04'][0] + daniel['T4_B04'][0])/2. -delta +45.2
for i in range(12):
 xpos[n-i] = start - delta * i
 zpos[n-i] = zpos['T4bX']-deltaZ
n = 40012025
start = (daniel['T4_T04'][0] + daniel['T4_B04'][0])/2. -delta +45.2 -10*delta-2.1
for i in range(12):
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T4bX']+3.64-deltaZ
n = 40102025
start = (daniel['T4_T04'][0] + daniel['T4_B04'][0])/2. -delta 
for i in range(12):
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T4bX']+3.64+4.06-deltaZ
n = 40112025
start = (daniel['T4_T04'][0] + daniel['T4_B04'][0])/2. -delta  -2.1
for i in range(12):
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T4bX']+3.64+4.06+3.64-deltaZ

#T4cX:
zpos['T4cX'] = (( daniel['T4_T05'][2] + daniel['T4_B05'][2] + daniel['T4_T06'][2] + daniel['T4_B06'][2])/4. - 4.33 -3.64-4.06-3.64)
ypos['T4cX'] = [(daniel['T4_T05'][1]+daniel['T4_T06'][1])/2.,(daniel['T4_B05'][1]+daniel['T4_B06'][1])/2.]

delta = ( (daniel['T4_T05'][0] + daniel['T4_B05'][0])/2. - (daniel['T4_T06'][0] + daniel['T4_B06'][0])/2. )/8.
delta = 4.2

n = 40002024
start = (daniel['T4_T06'][0] + daniel['T4_B06'][0])/2.  -delta +45.2
for i in range(12):
 xpos[n-i] = start - delta * i
 zpos[n-i] = zpos['T4cX']-deltaZ
n = 40012013
start = (daniel['T4_T06'][0] + daniel['T4_B06'][0])/2.  -delta +45.2 -10*delta-2.1
for i in range(12):
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T4cX']+3.64-deltaZ
n = 40102013
start = (daniel['T4_T06'][0] + daniel['T4_B06'][0])/2.  -delta  
for i in range(12):
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T4cX']+3.64+4.06-deltaZ
n = 40112013
start = (daniel['T4_T06'][0] + daniel['T4_B06'][0])/2.  -delta -2.1
for i in range(12):
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T4cX']+3.64+4.06+3.64-deltaZ

#T4dX:
zpos['T4dX'] = (( daniel['T4_T07'][2] + daniel['T4_B07'][2] + daniel['T4_T08'][2] + daniel['T4_B08'][2])/4. - 4.33 -3.64-4.06-3.64)
ypos['T4dX'] = [(daniel['T4_T07'][1]+daniel['T4_T08'][1])/2.,(daniel['T4_B07'][1]+daniel['T4_B08'][1])/2.]

delta = ( (daniel['T4_T07'][0] + daniel['T4_B07'][0])/2. - (daniel['T4_T08'][0] + daniel['T4_B08'][0])/2. )/8.
delta = 4.2

n = 40002012
start = (daniel['T4_T08'][0] + daniel['T4_B08'][0])/2. -delta +45.2
for i in range(12):
 xpos[n-i] = start - delta * i
 zpos[n-i] = zpos['T4dX']-deltaZ
n = 40012001
start = (daniel['T4_T08'][0] + daniel['T4_B08'][0])/2.  -delta +45.2 -10*delta-2.1
for i in range(12):
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T4dX']+3.64-deltaZ
n = 40102001
start = (daniel['T4_T08'][0] + daniel['T4_B08'][0])/2.  -delta
for i in range(12):
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T4dX']+3.64+4.06-deltaZ
n = 40112001
start = (daniel['T4_T08'][0] + daniel['T4_B08'][0])/2.  -delta -2.1
for i in range(12):
 xpos[n+i] = start + delta * i
 zpos[n+i] = zpos['T4dX']+3.64+4.06+3.64-deltaZ

if debug:
 for a in Langle:
   print a,Langle[a]*180./ROOT.TMath.Pi()
 for s in ['T1_MA_','T1_MB_','T2_MC_','T2_MD_']:
  for x in ['01','02','03','04']:
   print 'delta survey corrected - Daniel: %s %6.4F,%6.4F,%6.4F'%(s+x,surveyXYZ[s+x][0]-daniel[s+x][0],surveyXYZ[s+x][1]-daniel[s+x][1],surveyXYZ[s+x][2]-daniel[s+x][2])
 for s in ['T1_MA_','T1_MB_','T2_MC_','T2_MD_']:
  for top in ['01','02']:
   delx = surveyXYZ[s+top][0]-surveyXYZ[s+top.replace('01','04').replace('02','03')][0]
   dely = surveyXYZ[s+top][1]-surveyXYZ[s+top.replace('01','04').replace('02','03')][1]
   r = ROOT.TMath.Sqrt(delx**2+dely**2) 
   angle = ROOT.TMath.ATan2(delx,dely)*180./ROOT.TMath.Pi()
   print s+top,angle,r
 
#rpc
rpc={}
DT={}

def compareAlignment():
 ut.bookHist(h,'alignCompare','compare Alignments',100,-120.,120.,100,-120.,120.)
 ut.bookHist(h,'alignCompareDiffs','compare Alignments',100,-1.,1.)
 keys = xpos.keys()
 keys.sort()
 for d in keys:
   test = ROOT.MufluxSpectrometerHit(d,0.)
   test.MufluxSpectrometerEndPoints(vbot,vtop)
   statnb,vnb,pnb,lnb,view,channelID,tdcId,nRT = stationInfo(test)
   angle = ROOT.TMath.ATan2(-vtop[0]+vbot[0],-vtop[1]+vbot[1])/ROOT.TMath.Pi()*180
   L = ROOT.TMath.Sqrt( (vbot[0]-vtop[0])**2+(vbot[1]-vtop[1])**2)
   if view=='_x': vbotD,vtopD = ROOT.TVector3(xpos[d],L/2.,zpos[d]),ROOT.TVector3(xpos[d],-L/2.,zpos[d])
   else: vbotD,vtopD = ROOT.TVector3(xposb[d],yposb[d],zpos[d]),ROOT.TVector3(xpos[d],ypos[d],zpos[d])
   angleD = ROOT.TMath.ATan2(vtopD[0]-vbotD[0],vtopD[1]-vbotD[1])/ROOT.TMath.Pi()*180
   if abs(vtop[0]-vbot[0])<1:
    x0 = (vtop[0]+vbot[0])/2.
   else:
    m = (vtop[1]-vbot[1])/(vtop[0]-vbot[0])
    b = vtop[1]-m*vtop[0]
    x0 = -b/m 
   if abs(vtopD[0]-vbotD[0])<1:
    x0D = (vtopD[0]+vbotD[0])/2.
   else:   
    mD = (vtopD[1]-vbotD[1])/(vtopD[0]-vbotD[0])
    bD = vtopD[1]-mD*vtopD[0]
    x0D = -bD/mD
   diff = x0-x0D
   z = (vbot[2]+vtop[2])/2.
   txt = ""
   if abs(diff)>0.1 : txt = "!!! "
   if abs(z-vbotD[2])>0.1: txt+= "!!z"
   print "%s %i x/y pos from Daniel %7.4F %7.4F %7.4F %7.4F %7.4F  from FairShip  %7.4F %7.4F %7.4F %7.4F %7.4F diff %5.4F zdiff %5.4F"\
                %(txt,d,x0D,angleD,vbotD[1],vtopD[1],vbotD[2],x0,angle,vtop[1],vbot[1],vbot[2],(x0D-x0)*10.,(z-vbotD[2])*10)
   if abs(vbot[2]-vtop[2])>0.1: print "!!! z tilt",vbot[2],vtop[2]
   rc = h['alignCompare'].Fill(x0D,x0)
   rc = h['alignCompareDiffs'].Fill(x0D-x0)
 z0_D = zpos['T1X']/10.
 test = ROOT.MufluxSpectrometerHit(10002001,0.)
 test.MufluxSpectrometerEndPoints(vbot,vtop)
 z0_F = (vbot[2]+vtop[2])/2.
# distance to T1 u
 test = ROOT.MufluxSpectrometerHit(11002001,0.)
 test.MufluxSpectrometerEndPoints(vbot,vtop)
 z1_U = (vbot[2]+vtop[2])/2. - z0_F
 print "distance T1 X to T1 U:",zpos['T1U']/10.-z0_D,z1_U
# distance to T2 V
 test = ROOT.MufluxSpectrometerHit(20002001,0.)
 test.MufluxSpectrometerEndPoints(vbot,vtop)
 z2_V = (vbot[2]+vtop[2])/2. - z0_F
 print "distance T1 X to T2 V:",zpos['T2V']/10.-z0_D,z2_V
# distance to T2 X
 test = ROOT.MufluxSpectrometerHit(21002001,0.)
 test.MufluxSpectrometerEndPoints(vbot,vtop)
 z2_X = (vbot[2]+vtop[2])/2. - z0_F
 print "distance T1 X to T2 X:",zpos['T2X']/10.-z0_D,z2_X
# distance to T3 X
 test = ROOT.MufluxSpectrometerHit(30002001,0.)
 test.MufluxSpectrometerEndPoints(vbot,vtop)
 z3_X = (vbot[2]+vtop[2])/2. - z0_F
 print "distance T1 X to T3 X:",(zpos['T3aX']+zpos['T3bX']+zpos['T3cX']+zpos['T3dX'])/(4*10.)-z0_D,z3_X
# distance to T4 X
 test = ROOT.MufluxSpectrometerHit(40002001,0.)
 test.MufluxSpectrometerEndPoints(vbot,vtop)
 z4_X = (vbot[2]+vtop[2])/2. - z0_F
 print "distance T1 X to T4 X:",(zpos['T4aX']+zpos['T4bX']+zpos['T4cX']+zpos['T4dX'])/(4*10.)-z0_D,z4_X
#
def surveyVSfairship():
 print "z-positions relative to station 1"
 test = ROOT.MufluxSpectrometerHit(10002012,0.)
 test.MufluxSpectrometerEndPoints(vbot,vtop)
 z1 = (surveyXYZ['T1_MA_01'][2]+surveyXYZ['T1_MA_04'][2])/2.+3.03
 z1F = vtop[2]
 print "                               X       topY    botY     Z"
 print "%s, %7.3F,%7.3F,%7.3F,%7.3F"%("T1_MA_01/04 survey corrected",(surveyXYZ['T1_MA_01'][0]+surveyXYZ['T1_MA_04'][0])/2.,surveyXYZ['T1_MA_01'][1],surveyXYZ['T1_MA_04'][1],z1-z1)
 print "%s, %7.3F,%7.3F,%7.3F,%7.3F"%("T1_MA_01/04 Daniel          ",(daniel['T1_MA_01'][0]+daniel['T1_MA_04'][0])/2.,daniel['T1_MA_01'][1],daniel['T1_MA_04'][1],(daniel['T1_MA_01'][2]+daniel['T1_MA_04'][2])/2.+3.03-z1)
 print "%s, %7.3F,%7.3F,%7.3F,%7.3F"%("tube 10002012               ",vtop[0],vbot[1],vtop[1],vtop[2]-z1F)
# same station
 vtop2,vbot2 = ROOT.TVector3(),ROOT.TVector3()
 test2 = ROOT.MufluxSpectrometerHit(10102001,0.)
 test2.MufluxSpectrometerEndPoints(vbot2,vtop2)
 delx = (daniel['T1_MA_01'][0]+daniel['T1_MA_04'][0])/2.-(daniel['T1_MA_02'][0]+daniel['T1_MA_03'][0])/2.
 dely = [daniel['T1_MA_01'][1]-daniel['T1_MA_02'][1],daniel['T1_MA_04'][1]-daniel['T1_MA_03'][1]]
 delz = ((daniel['T1_MA_01'][2]+daniel['T1_MA_04'][2])/2.+3.03) - ((daniel['T1_MA_02'][2]+daniel['T1_MA_03'][2])/2.+3.03+3.64+4.06)
 print "%s, %7.3F,%7.3F,%7.3F,%7.3F"%("T1_MA_01/04 - T1_MA_02/03   ",delx,dely[0],dely[1],delz)
 print "%s, %7.3F,%7.3F,%7.3F,%7.3F"%("tube 10002012 - 10102001    ",vtop[0]-vtop2[0],vtop[1]-vtop2[1],vbot[1]-vbot2[1],vtop[2]-vtop2[2])
 test = ROOT.MufluxSpectrometerHit(21112001,0.)
 test.MufluxSpectrometerEndPoints(vbot,vtop)
 z2 = (surveyXYZ['T2_MD_02'][2]+surveyXYZ['T2_MD_03'][2])/2.-3.03
 print "%s, %7.3F,%7.3F,%7.3F,%7.3F"%("T2_MD_02/03 survey corrected",(surveyXYZ['T2_MD_02'][0]+surveyXYZ['T2_MD_03'][0])/2.,surveyXYZ['T2_MD_02'][1],surveyXYZ['T2_MD_03'][1],z2-z1)
 print "%s, %7.3F,%7.3F,%7.3F,%7.3F"%("T2_MD_02/03 Daniel          ",(daniel['T2_MD_02'][0]+daniel['T2_MD_03'][0])/2.,daniel['T2_MD_02'][1],daniel['T2_MD_03'][1],(daniel['T2_MD_02'][2]+daniel['T2_MD_03'][2])/2.-3.03-z1)
 print "%s, %7.3F,%7.3F,%7.3F,%7.3F"%("tube 21112001               ",vtop[0],vbot[1],vtop[1],vtop[2]-z1F)
 test = ROOT.MufluxSpectrometerHit(11002012,0.)
 test.MufluxSpectrometerEndPoints(vbot,vtop)
 z1b = (surveyXYZ['T1_MB_01'][2]+surveyXYZ['T1_MB_04'][2])/2.-3.03-3.64-4.06-3.64
 z1bF = vtop[2]
 m = (surveyXYZ['T1_MB_01'][1]-surveyXYZ['T1_MB_04'][1])/(surveyXYZ['T1_MB_01'][0]-surveyXYZ['T1_MB_04'][0])
 b = surveyXYZ['T1_MB_01'][1] - m*surveyXYZ['T1_MB_01'][0]
 xposAty0 = -b/m
 m = (daniel['T1_MB_01'][1]-daniel['T1_MB_04'][1])/(daniel['T1_MB_01'][0]-daniel['T1_MB_04'][0])
 b = daniel['T1_MB_01'][1] - m*daniel['T1_MB_01'][0]
 xposAty0D = -b/m 
 m = (vbot[1]-vtop[1])/(vbot[0]-vtop[0])
 b = vbot[1] - m*vbot[0]
 xposAty0F = -b/m 
 print "                               X@Y=0       topY    botY     Z"
 print "%s, %7.3F,%7.3F,%7.3F,%7.3F"%("T1_MB_01/04 survey corrected",xposAty0,surveyXYZ['T1_MB_01'][1],surveyXYZ['T1_MB_04'][1],z1b-z1)
 print "%s, %7.3F,%7.3F,%7.3F,%7.3F"%("T1_MB_01/04 Daniel          ",xposAty0D,daniel['T1_MB_01'][1],daniel['T1_MB_04'][1],(daniel['T1_MB_01'][2]+daniel['T1_MB_04'][2])/2.-3.03-3.64-4.06-3.64-z1)
 print "%s, %7.3F,%7.3F,%7.3F,%7.3F"%("tube 11002012               ",xposAty0F,vbot[1],vtop[1],vtop[2]-z1F)
 test = ROOT.MufluxSpectrometerHit(20012012,0.)
 test.MufluxSpectrometerEndPoints(vbot,vtop)
 z2b = (surveyXYZ['T2_MC_01'][2]+surveyXYZ['T2_MC_04'][2])/2.+3.03+3.64
 m = (surveyXYZ['T2_MC_01'][1]-surveyXYZ['T2_MC_04'][1])/(surveyXYZ['T2_MC_01'][0]-surveyXYZ['T2_MC_04'][0])
 b = surveyXYZ['T2_MC_01'][1] - m*surveyXYZ['T2_MC_01'][0]
 xposAty0 = -b/m
 m = (daniel['T2_MC_01'][1]-daniel['T2_MC_04'][1])/(daniel['T2_MC_01'][0]-daniel['T2_MC_04'][0])
 b = daniel['T2_MC_01'][1] - m*daniel['T2_MC_01'][0]
 xposAty0D = -b/m 
 m = (vbot[1]-vtop[1])/(vbot[0]-vtop[0])
 b = vbot[1] - m*vbot[0]
 xposAty0F = -b/m 
 print "%s, %7.3F,%7.3F,%7.3F,%7.3F"%("T2_MC_01/04 survey corrected",xposAty0,surveyXYZ['T2_MC_01'][1],surveyXYZ['T2_MC_04'][1],z2b-z1)
 print "%s, %7.3F,%7.3F,%7.3F,%7.3F"%("T2_MC_01/04 Daniel          ",xposAty0D,daniel['T2_MC_01'][1],daniel['T2_MC_04'][1],(daniel['T2_MC_01'][2]+daniel['T2_MC_04'][2])/2.+3.03+3.64-z1)
 print "%s, %7.3F,%7.3F,%7.3F,%7.3F"%("tube 20012012               ",xposAty0F,vbot[1],vtop[1],vtop[2]-z1F)
 test = ROOT.MufluxSpectrometerHit(30012046,0.)
 test.MufluxSpectrometerEndPoints(vbot,vtop)
 # For T3 it is placed 7cm in front and for T4 7cm behind the endplate
 z3 = (surveyXYZ['T3_T01'][2]+surveyXYZ['T3_B01'][2])/2.+4.33+3.64 + 7.0
 print "%s, %7.3F,%7.3F,%7.3F,%7.3F"%("T3_T01/B01  survey corrected",(surveyXYZ['T3_T01'][0]+surveyXYZ['T3_B01'][0])/2.,surveyXYZ['T3_T01'][1],surveyXYZ['T3_B01'][1],z3-z1)
 print "%s, %7.3F,%7.3F,%7.3F,%7.3F"%("T3_T01/B01  Daniel          ",(daniel['T3_T01'][0]+daniel['T3_B01'][0])/2.,daniel['T3_T01'][1],daniel['T3_B01'][1],(daniel['T3_T01'][2]+daniel['T3_B01'][2])/2.+4.33+3.64-z1)
 print "%s, %7.3F,%7.3F,%7.3F,%7.3F"%("tube 30012046               ",vtop[0],vbot[1],vtop[1],vtop[2]-z1F)
 test = ROOT.MufluxSpectrometerHit(40102046,0.)
 test.MufluxSpectrometerEndPoints(vbot,vtop)
 z4 = (surveyXYZ['T4_T01'][2]+surveyXYZ['T4_B01'][2])/2.-4.33-3.64 - 7.0
 print "%s, %7.3F,%7.3F,%7.3F,%7.3F"%("T4_T01/B01  survey corrected",(surveyXYZ['T4_T01'][0]+surveyXYZ['T4_B01'][0])/2.,surveyXYZ['T4_T01'][1],surveyXYZ['T4_B01'][1],z4-z1)
 print "%s, %7.3F,%7.3F,%7.3F,%7.3F"%("T4_T01/B01  Daniel          ",(daniel['T4_T01'][0]+daniel['T4_B01'][0])/2.,daniel['T4_T01'][1],daniel['T4_B01'][1],(daniel['T4_T01'][2]+daniel['T4_B01'][2])/2.-4.33-3.64-z1)
 print "%s, %7.3F,%7.3F,%7.3F,%7.3F"%("tube 40102046               ",vtop[0],vbot[1],vtop[1],vtop[2]-z1F)

def checkZtilts():
 # station 1 and 2  01: +x,+y 02: -x,+y, 03: -x,-y 04: +x,-y 
 for s in ['T1_MA_','T1_MB_','T2_MC_','T2_MD_']:
  meanZ = 0
  for x in ['01','02','03','04']:
   meanZ += daniel[s+x][2]
  meanZ = meanZ/4.
  rms = 0
  for x in ['01','02','03','04']:
    rms += (daniel[s+x][2]-meanZ)**2
  rms = ROOT.TMath.Sqrt(rms)
  diffTopBot =  daniel[s+'01'][2]-daniel[s+'04'][2],daniel[s+'02'][2]-daniel[s+'03'][2]
  diffLefRig =  daniel[s+'01'][2]-daniel[s+'02'][2],daniel[s+'04'][2]-daniel[s+'03'][2]
  print s,meanZ,rms,' top/bot ',diffTopBot,' left/right ',diffLefRig
 # station 1 and 2  01: +x,+y 02: -x,+y, 03: -x,-y 04: +x,-y 
 for s in ['T3','T4']:
  meanZ = 0
  for y in ['_T','_B']:
   for x in ['01','02','03','04','05','06','07','08']:
    meanZ += daniel[s+y+x][2]
    print s+y+x,daniel[s+y+x][2]
  meanZ = meanZ/16.
  rms = 0
  for y in ['_T','_B']:
   for x in ['01','02','03','04','05','06','07','08']:
    rms += (daniel[s+y+x][2]-meanZ)**2
  rms = ROOT.TMath.Sqrt(rms)
  print s,meanZ,rms
 

h['dispTrack3D']=[]
h['dispTrack']=[]
h['dispTrackY']=[]

withTDC = True
withDefaultAlignment = True

def dispTrack3D(theTrack):
     zstart = 0
     nPoints = 100
     delz = 1000./nPoints
     nt = len(h['dispTrack3D'])
     h['dispTrack3D'].append( ROOT.TPolyLine3D(nPoints) )
     h['dispTrack3D'][nt].SetLineWidth(3)
     h['dispTrack3D'][nt].SetLineColor(ROOT.kBlack)
     for nP in range(nPoints):
      zstart+=delz
      rc,pos,mom = extrapolateToPlane(theTrack,zstart)
      if not rc: print "extrap failed"
      else: 
        h['dispTrack3D'][nt].SetPoint(nP,pos[0],pos[1],pos[2])
     rc = ROOT.gROOT.FindObject('c1').cd()
     h['dispTrack3D'][nt].Draw('oglsame')
     rc = ROOT.gROOT.FindObject('c1').Update()
def displayDTLayers():
 ut.bookHist(h,'upstream','upstream layers',12,-0.5,11.5,30,-0.5,29.5)
 if not h.has_key('layerDisplay'): ut.bookCanvas(h,key='layerDisplay',title='Upstream Layers',nx=1600,ny=1200,cx=1,cy=0)
 h['upstreamG'] = ROOT.TGraph()
 h['upstreamG'].Set(0)
 h['upstreamG'].SetMarkerStyle(8)
 h['upstreamG'].SetMarkerSize(2)
 n=0
 for hit in sTree.Digi_MufluxSpectrometerHits:
    detID = hit.GetDetectorID()
    if detID<0: continue # feature for converted data in February'19
    statnb,vnb,pnb,lnb,view,channelID,tdcId,nRT = stationInfo(hit)
    nr = detID%100
    y = 2*pnb+lnb+(statnb-1)*16
    if view=='_u': y+=8
    if view=='_x' and statnb>1: y+=8
    h['upstreamG'].SetPoint(n,nr,y)
    n+=1
 tc = h['layerDisplay'].cd(1)
 h['upstream'].Draw()
 h['upstreamG'].Draw('sameP')

def plotEvent(n=-1):
   h['dispTrack']=[]
   h['dispTrack3D']=[]
   h['dispTrackY']=[]
   if not n<0: rc = sTree.GetEvent(n)
   h['hitCollection']= {'upstream':[0,ROOT.TGraph()],'downstream':[0,ROOT.TGraph()],'muonTaggerX':[0,ROOT.TGraph()],'muonTaggerY':[0,ROOT.TGraph()]}
   h['stereoHits'] = []
   for c in h['hitCollection']: rc=h['hitCollection'][c][1].SetName(c)
   for c in h['hitCollection']: rc=h['hitCollection'][c][1].Set(0)
   ut.bookHist(h,'xz','x (y) vs z',500,0.,1200.,100,-150.,150.)
   if not h.has_key('simpleDisplay'): ut.bookCanvas(h,key='simpleDisplay',title='simple event display',nx=1200,ny=800,cx=1,cy=0)
   rc = h[ 'simpleDisplay'].cd(1)
   h['xz'].SetMarkerStyle(30)
   h['xz'].SetStats(0)
   h['xz'].Draw('b')
   for hit in sTree.Digi_MufluxSpectrometerHits:
    if not hit.hasTimeOverThreshold(): continue   # 16% of the hits, isn't it a bit too much?
    statnb,vnb,pnb,lnb,view,channelID,tdcId,nRT = stationInfo(hit)
    # print statnb,vnb,pnb,lnb,view,hit.GetDetectorID()
    vbot,vtop = strawPositionsBotTop[hit.GetDetectorID()]
    if view != '_x':
      stereoHit = ROOT.TGraph()
      stereoHit.SetPoint(0,vbot[2],vbot[0])
      stereoHit.SetPoint(1,vtop[2],vtop[0])
      h['stereoHits'].append(stereoHit)
      continue
    if statnb<3:  
     c = h['hitCollection']['upstream'] 
     rc = c[1].SetPoint(c[0],vbot[2],vbot[0])
     c[0]+=1 
    else:
     c = h['hitCollection']['downstream'] 
     rc = c[1].SetPoint(c[0],vbot[2],vbot[0])
     c[0]+=1
   c  = h['hitCollection']['muonTaggerX'] 
   cy = h['hitCollection']['muonTaggerY']
   if sTree.GetBranch("Digi_MuonTaggerHits"):
    for hit in sTree.Digi_MuonTaggerHits:
     channelID = hit.GetDetectorID()
     statnb = channelID/10000
     view   = (channelID-10000*statnb)/1000
     channel = channelID%1000
     vbot,vtop = RPCPositionsBotTop[channelID]
     if view == 1:
      x,z =  (vtop[0]+vbot[0])/2.,(vtop[2]+vbot[2])/2.
      rc = c[1].SetPoint(c[0],z,x)
      c[0]+=1
     if view == 0:
      y,z =  (vtop[1]+vbot[1])/2.,(vtop[2]+vbot[2])/2.
      rc = cy[1].SetPoint(cy[0],z,y)  
      cy[0]+=1
   h['hitCollection']['downstream'][1].SetMarkerColor(ROOT.kRed)
   h['hitCollection']['upstream'][1].SetMarkerColor(ROOT.kBlue)
   h['hitCollection']['muonTaggerX'][1].SetMarkerColor(ROOT.kGreen)
   h['hitCollection']['muonTaggerY'][1].SetMarkerColor(ROOT.kCyan)
   for c in h['hitCollection']: rc=h['hitCollection'][c][1].SetMarkerStyle(30)
   for c in h['hitCollection']:
     if h['hitCollection'][c][1].GetN()<1: continue
     rc=h['hitCollection'][c][1].Draw('sameP')
     h['display:'+c]=h['hitCollection'][c][1]
   for g in h['stereoHits']:
     g.SetLineWidth(2)
     g.Draw('same')
   h[ 'simpleDisplay'].Update()

viewDict = {0:'_x',1:'_u',2:'_v'}
def stationInfo(hit):
 info = hit.StationInfo()
 return info[0],info[1],info[2],info[3],viewDict[info[4]],info[5],info[6],info[7]/cuts['RTsegmentation']
 #      statnb,   vnb,    pnb,    lnb,     view,         channelID,tdcId,  nRT

tdcIds ={'1000_x':[0],'1001_x':[0],'1010_x':[0],'1011_x':[0],
         '1100_u':[0],'1101_u':[0],'1110_u':[0],'1111_u':[0],
         '2000_v':[0],'2001_v':[0],'2010_v':[1],'2011_v':[1],
         '2100_x':[1],'2101_x':[1],'2110_x':[1],'2111_x':[1],
         '3000_x':[3,4],  '3001_x':[3,4],  '3010_x':[3,4],'3011_x':[3,4],
         '4000_x':[3,2,1],'4001_x':[3,2,1],'4010_x':[2,1],'4011_x':[2,1]}

xLayers = {}
channels = {}
for s in range(1,5):
 xLayers[s]={}
 channels[s]={}
 for p in range(2):
  xLayers[s][p]={}
  channels[s][p]={}
  for l in range(2):
   xLayers[s][p][l]={}
   channels[s][p][l]={}
   for view in ['_x','_u','_v']:
    if (s==1 and view=='_v') or (s==2 and view=='_u') or (s>2 and view != '_x'): continue
    ut.bookHist(h,str(1000*s+100*p+10*l)+view,'hit map station'+str(s)+' plane'+str(p)+' layer '+str(l)+view,50,-0.5,49.5)
    v = 0 
    if s==2 and view == "_x": v = 1
    if s==1 and view == "_u": v = 1
    myDetID = s * 1000 + v * 100 + p * 10 + l
    for nRT in range(576 / cuts['RTsegmentation'] ):
      ut.bookHist(h,"TDC"   +str(nRT),         'TDC station'+str(s)+' plane'+str(p)+' layer '+str(l)+view,1500,-500.,2500.)
      ut.bookHist(h,"TDC"   +str(nRT)+'_noToT','TDC station'+str(s)+' plane'+str(p)+' layer '+str(l)+view,1500,-500.,2500.)
    xLayers[s][p][l][view]=h[str(1000*s+100*p+10*l)+view]
    channels[s][p][l][view]=12
    if s>2: channels[s][p][l][view]=48
for x in xpos.keys():
      ut.bookHist(h,"TDC"   +str(x),'TDC '+str(x)  ,1500,-500.,2500.)
      ut.bookHist(h,"TDC"   +str(x),'noToT '+str(x),1500,-500.,2500.)

ut.bookHist(h,'T0tmp','T0 temp',1250,-500.,2000.)
ut.bookHist(h,'T0','T0',1250,-500.,2000.)

noiseThreshold=10
noisyChannels=[] # [30112016, 40012005, 40012007, 40012008, 40112031, 40112032] only present in some runs
deadChannels4MC = ROOT.std.vector('int')()
for c in [10112001,11112012,20112003,30002042,30012026,30102021,30102025,30112013,30112018,40102014]: deadChannels4MC.push_back(c)
gol =  sGeo.GetTopVolume().GetNode("volGoliath_1")
zgoliath = gol.GetMatrix().GetTranslation()[2]

for n in range(1,5):
 for x in ROOT.gGeoManager.GetTopVolume().GetNodes(): 
   if x.GetName().find('volDriftTube')<0: continue
   for y in x.GetVolume().GetNodes():
    if y.GetName().find('plane')<0: continue
    for z in y.GetVolume().GetNodes():
      rc = nav.cd('/'+x.GetName()+'/'+y.GetName()+'/'+z.GetName())
      vol = nav.GetCurrentNode()
      shape = vol.GetVolume().GetShape()
      local = array('d',[0,0,0])
      globOrigin = array('d',[0,0,0])
      nav.LocalToMaster(local,globOrigin)
      DT[z.GetName()] = [shape.GetDX(),shape.GetDY(),globOrigin[2]]

nav.cd('/VMuonBox_1/VSensitive1_1')
loc = array('d',[0,0,0])
glob = array('d',[0,0,0])
nav.LocalToMaster(loc,glob)
zRPC1 = glob[2]
cuts['zRPC1'] = zRPC1
node = nav.GetCurrentNode()
dx = node.GetVolume().GetShape().GetDX()
dy = node.GetVolume().GetShape().GetDY()
loc = array('d',[-dx,0,0])
nav.LocalToMaster(loc,glob)
cuts['xLRPC1'] = glob[0]
loc = array('d',[dx,0,0])
nav.LocalToMaster(loc,glob)
cuts['xRRPC1'] = glob[0]
loc = array('d',[0,-dy,0])
nav.LocalToMaster(loc,glob)
cuts['yBRPC1'] = glob[1]
loc = array('d',[0,dy,0])
nav.LocalToMaster(loc,glob)
cuts['yTRPC1'] = glob[1]
cuts["firstDTStation_z"] = DT['Station_1_x_plane_0_layer_0_10000000'][2]
cuts["lastDTStation_z"]  = DT['Station_4_x_plane_1_layer_1_40110000'][2]

def DTEfficiencyFudgefactor(method=-1):
 if method <1: effFudgeFactors = {"u":1.1, "v":1.1, "x2":1.1, "x3":1.1, "x1":1.1,"x4":1.1}
 if method ==0: effFudgeFactors = {"x1":0.97, "u":0.95, "x2":0.96, "v":0.96, "x3":0.92, "x4":0.97} # method 0
 if method ==2: effFudgeFactors = {"x1":0.94, "u":0.93, "x2":0.95, "v":0.93, "x3":0.90, "x4":0.94} # method 2
 for x in effFudgeFactors: muflux_Reco.setEffFudgeFactor(x,effFudgeFactors[x])

# C++ reconstruction/monitoring
xSHiP = ROOT.TTreeReader(sTree)
muflux_Reco = ROOT.MufluxReco(xSHiP)
for x in cuts: muflux_Reco.setCuts(x,cuts[x])
DTEfficiencyFudgefactor(method=-1)
if sTree.GetBranch('MCTrack'):  muflux_Reco.setNoisyChannels(deadChannels4MC)

def MakeKeysToDThits(minToT=-999):
  keysToDThits={}
  key = -1
  for hit in sTree.Digi_MufluxSpectrometerHits:
   key+=1
   #if not hit.hasTimeOverThreshold(): continue
   if not hit.isValid() and MCdata: continue
   detID=hit.GetDetectorID()
   if detID<0: continue # feature for converted data in February'19
   if keysToDThits.has_key(detID):
     prevTDC = sTree.Digi_MufluxSpectrometerHits[keysToDThits[detID][0]].GetDigi()
     prevToT = sTree.Digi_MufluxSpectrometerHits[keysToDThits[detID][0]].GetTimeOverThreshold()
     # print "MakeKeysToDThits, non unique Digi_MufluxSpectrometerHits",detID,hit.GetDigi(),hit.GetTimeOverThreshold(),hit.hasTimeOverThreshold(),prevTDC,prevToT
     if hit.hasTimeOverThreshold(): keysToDThits[detID]=[key]
   else:
    keysToDThits[detID]=[key]
  key = -1
  for hit in sTree.Digi_LateMufluxSpectrometerHits:
   key+=1
   if not hit.hasTimeOverThreshold(): continue
   if hit.GetTimeOverThreshold()<minToT : continue
   detID=hit.GetDetectorID()
   if not keysToDThits.has_key(detID): 
     print "MakeKeysToDThits, late hit but no first one",detID
     keysToDThits[detID]=[-1]
   keysToDThits[detID].append(key)
  return keysToDThits


def studyLateDTHits(nevents=1000,nStart=0):
 ut.bookHist(h,'multLateDTHits','multiplicity of late DT hits',11,-1.5,9.5)
 ut.bookHist(h,'ToverTvsTDC','Time over threshold vs tdc',300,-1000.,2000.,300,-1000.,2000.)
 nHits=0
 for n in range(nStart,nevents):
   rc=sTree.GetEvent(n)
   keysToDThits=MakeKeysToDThits()
   for channel in keysToDThits:
     if keysToDThits[channel][0]<0: rc=h['multLateDTHits'].Fill(-1)
     else: 
      nHits+=1
      rc=h['multLateDTHits'].Fill(len(keysToDThits[channel])-1)
      for n in range(1,len(keysToDThits[channel])):
        key = keysToDThits[channel][n]
        aHit = sTree.Digi_LateMufluxSpectrometerHits[key]
        rc=h['ToverTvsTDC'].Fill( aHit.GetTimeOverThreshold() ,aHit.GetDigi())
 ROOT.gROOT.FindObject('c1').cd()
 h['multLateDTHits'].Draw()
 print "nHits",nHits
def nicePrintout(hits):
  t0 = 0
  if MCdata: t0 = sTree.ShipEventHeader.GetEventTime()
  print "station layer channels tdc time-over-threshold ..."
  lateText = []
  keysToDThits=MakeKeysToDThits(100)
  for s in range(1,5):
   for v in [0,1,2]:
    if v==2 and s!=2:continue
    if v==1 and s!=1:continue
    for l in range(4):
     txt = str(s) + ' '+viewC[v]+' '+str(l)+' : '
     tdc = ''
     for hit in hits[v][s][l]:
      statnb,vnb,pnb,lnb,view,channelID,tdcId,nRT = stationInfo(hit)
      txt+=str(channelID)+' '
      tdc+="%5.0F %5.0F "%(hit.GetDigi()-t0,hit.GetTimeOverThreshold())
      lateArrivals = len(keysToDThits[hit.GetDetectorID()])
      if lateArrivals>1: 
       tmp = str(s) + ' '+viewC[v]+' '+str(l)+' : '+str(channelID)+' '
       for n in range(1,len(keysToDThits[hit.GetDetectorID()])):
        key = keysToDThits[hit.GetDetectorID()][n]
        lHit = sTree.Digi_LateMufluxSpectrometerHits[key]
        tmp+="%5.0F %5.0F "%(lHit.GetDigi()-t0,lHit.GetTimeOverThreshold())
       lateText.append(tmp)
     print "%-20s %s"%(txt,tdc)
  print "---- channels with late hits",len(lateText)
  for txt in lateText: print txt
def plotHitMaps(onlyPlotting=False):
 if not onlyPlotting: muflux_Reco.fillHitMaps()
 plotHitMapsOld(onlyPlotting=True)

def hitMapsFromFittedTracks():
 for s in range(1,5):
  for p in range(2):
   for l in range(2): 
       xLayers[s][p][l]['_x'].Reset()
       if s==1: xLayers[s][p][l]['_u'].Reset()
       if s==2: xLayers[s][p][l]['_v'].Reset()
 for event in sTree:
  for trInfo in event.TrackInfos:
   for n in range(trInfo.N()):
    if trInfo.wL(n) <0.1 and trInfo.wR(n) <0.1: continue
    detID = trInfo.detId(n)
    hit = ROOT.MufluxSpectrometerHit(detID,0)
    s,v,p,l,view,channelID,tdcId,mdoduleId = stationInfo(hit)
    rc = xLayers[s][p][l][view].Fill(channelID)
 ut.writeHists(h,'histos-HitmapsFromFittedTracks-'+rname)
def plotHitMapsOld(onlyPlotting=False):
 noisyChannels = []
 deadThreshold = 1.E-4 # ~1% typical occupancy
 deadChannels = []
 if sTree.GetBranch("FitTracks"):
   FitTracksBrStatus =  sTree.GetBranchStatus("FitTracks")
   sTree.SetBranchStatus("FitTracks",0)
 if not onlyPlotting:
  for event in sTree:
   for hit in event.Digi_MufluxSpectrometerHits:
    s,v,p,l,view,channelNr,tdcId,nRT = stationInfo(hit)
    tot = ''
    if not hit.hasTimeOverThreshold(): tot='_noToT'
    try:
     rc = xLayers[s][p][l][view].Fill(channelNr)
    except:
     print "plotHitMaps error",hit.GetDetectorID(),s,v,p,l,view,channelNr,tdcId
     continue
    if hit.GetDetectorID() not in noisyChannels:
     t0 = 0
     if MCdata: t0 = sTree.ShipEventHeader.GetEventTime()
     rc = h['TDC'+str(nRT)+tot].Fill(hit.GetDigi()-t0)
    channel = 'TDC'+str(hit.GetDetectorID())
    if not h.has_key(channel+tot): h[channel+tot]=h['TDC'+str(nRT)+tot].Clone(channel)
    rc = h[channel+tot].Fill(hit.GetDigi()-t0)
 if not h.has_key('hitMapsX'): ut.bookCanvas(h,key='hitMapsX',title='Hit Maps All Layers',nx=1600,ny=1200,cx=4,cy=6)
 if not h.has_key('TDCMapsX'): ut.bookCanvas(h,key='TDCMapsX',title='TDC Maps All Layers',nx=1600,ny=1200,cx=5,cy=10)
 if not h.has_key('TDCMapsX_noToT'): ut.bookCanvas(h,key='TDCMapsX_noToT',title='TDC Maps All Layers noToT',nx=1600,ny=1200,cx=5,cy=10)
 j  = 0
 jt = 0
 for s in range(1,5):
  for view in ['_x','_u','_v']:
   for p in range(2):
    for l in range(2):
     if not xLayers[s][p][l].has_key(view):continue
     if s>2 and view != '_x': continue
     if s==1 and view == '_v'or s==2 and view == '_u': continue
     j+=1
     rc = h['hitMapsX'].cd(j)
     xLayers[s][p][l][view].Draw()
     mean = xLayers[s][p][l][view].GetEntries()/channels[s][p][l][view]
     v = 0
     if s==2 and view == "_x": v = 1
     if s==1 and view == "_u": v = 1
     myDetID = s * 10000000 + v * 1000000 + p * 100000 + l*10000
     for i in range(2,int(xLayers[s][p][l][view].GetEntries())+1):
      if i+1>Nchannels[s]: continue
      channel = myDetID+i-1 + 2000
      if xLayers[s][p][l][view].GetBinContent(i) > noiseThreshold * mean:
        print "noisy channel:",s,p,l,view,xLayers[s][p][l][view].GetBinContent(i) , noiseThreshold , mean
        if not channel in noisyChannels: noisyChannels.append(myDetID+i-1)
      if xLayers[s][p][l][view].GetBinContent(i) < max(1,deadThreshold * mean):
        print "dead channel:",s,p,l,view,i,xLayers[s][p][l][view].GetBinContent(i) , deadThreshold , mean
        deadChannels.append(channel)
#
 for nRT in range(1,576/cuts['RTsegmentation']+1):
      jt+=1
      tp = h['TDCMapsX'].cd(jt)
      tp.SetLogy(1)
      h['TDC'+str(nRT-1)].Draw()
      tp = h['TDCMapsX_noToT'].cd(jt)
      tp.SetLogy(1)
      h['TDC'+str(nRT-1)+'_noToT'].Draw()

 print "list of noisy channels"
 for n in noisyChannels: print n
 print "list of dead channels"
 for n in deadChannels: print n
 if sTree.GetBranch("FitTracks"): sTree.SetBranchStatus("FitTracks",FitTracksBrStatus)

def printScalers():
   ut.bookHist(h,'integratedrate','rate integrated',100,-0.5,99.5)
   ut.bookHist(h,'rate','rate',100,-0.5,99.5)
   ut.bookHist(h,'scalers','rate',100,-0.5,99.5)
   if not h.has_key('rates'): ut.bookCanvas(h,key='rates',title='Rates',nx=800,ny=400,cx=2,cy=1)
   rc = h['rates'].cd(1)
   scalers = sTree.GetCurrentFile().Get('scalers')
   if not scalers:
     print "no scalers in this file"
     return
   scalers.GetEntry(0)
   ns = 0
   for x in scalers.GetListOfBranches():
    name = x.GetName()
    s = eval('scalers.'+name)
    if name!='slices': 
      print "%20s :%8i"%(name,s)
      rc=h['scalers'].Fill(ns,s)
      ns+=1
    else:
      r0 = 0
      for n in range(s.size()):
        r0 = s[n] - r0
        if r0<0: r0 = s[n]
        rc=h['rate'].Fill(n,r0)
        rc=h['integratedrate'].Fill(n,s[n])
        r0 = s[n]
   h['rate'].Draw('hist')
   rc = h['rates'].cd(2)
   h['integratedrate'].Draw('hist')

ut.bookHist(h,'delx','delta x',200,-50.,50.)
ut.bookHist(h,'delta_mean_uv','delta to mean u and v',200,-10.,10.)
ut.bookHist(h,'magPos','XY at goliath, PR',100,-50.,50.,100,-50.,50.)
for dets in ['34','stereo12','y12']: ut.bookHist(h,'tracklets'+dets,'hits per view',10,-0.5,9.5)

def plotRPCHitmap():
 ut.bookHist(h,'rpcHitmap','rpc Hitmaps',60,-0.5,59.5)
 for n in range(1,6):
  for l in range(2):
    ut.bookHist(h,'rpcHitmap'+str(n)+str(l),'rpc Hitmaps station '+str(n)+'layer '+str(l),200,-0.5,199.5)
 for event in sTree:
    for m in event.Digi_MuonTaggerHits:
      layer = m.GetDetectorID()/1000
      rc = h['rpcHitmap'].Fill(layer)
      channel = m.GetDetectorID()%1000
      rc = h['rpcHitmap'+str(layer)].Fill(channel)
 if not h.has_key('rpcPlot'): ut.bookCanvas(h,key='rpcPlot',title='RPC Hitmaps',nx=1200,ny=600,cx=4,cy=3)
 j=0
 for n in range(1,6):
  for l in range(2):
    j+=1
    rc = h['rpcPlot'].cd(j)
    h['rpcHitmap'+str(n)+str(l)].Draw()
 j+=1
 rc = h['rpcPlot'].cd(j)
 h['rpcHitmap'].Draw()

def plotTimeOverThreshold(N,Debug=False):
 ut.bookHist(h,'ToverT','Time over threshold',3000,-1000.,2000.)
 ut.bookHist(h,'endTime','End Time',100,0.,2000.)
 ut.bookHist(h,'tdc','tdc',100,-200.,2000.)
 for n in range(N):
  rc = sTree.GetEvent(n)
  flag = False
  for aHit in sTree.Digi_MufluxSpectrometerHits:
   detID=hit.GetDetectorID()
   if detID<0: continue # feature for converted data in February'19
   if not aHit.hasTimeOverThreshold():
    rc=h['ToverT'].Fill( -999. )
    continue
   rc=h['ToverT'].Fill( aHit.GetTimeOverThreshold() )
   rc=h['tdc'].Fill( aHit.GetDigi())
   rc=h['endTime'].Fill( aHit.GetDigi()+aHit.GetTimeOverThreshold() )
   if aHit.GetTimeOverThreshold() < 10: flag = True
  if flag and Debug:
     print n
     spectrHitsSorted = ROOT.nestedList()
     muflux_Reco.sortHits(sTree.Digi_MufluxSpectrometerHits,spectrHitsSorted,True)
     for s in range(1,5):
      for view in viewsI[s]:
        for l in range(4):
         for hit in spectrHitsSorted[view][s][l]:
           print s,viewC[view],l,hit.GetDetectorID()%1000,hit.GetTimeOverThreshold()  

from array import array

gMan  = ROOT.gGeoManager
geoMat =  ROOT.genfit.TGeoMaterialInterface()
#
if zeroField: bfield = ROOT.genfit.BellField()
else:         bfield = ROOT.genfit.FairShipFields()
fM = ROOT.genfit.FieldManager.getInstance()
fM.init(bfield)
ROOT.genfit.MaterialEffects.getInstance().init(geoMat)
if zeroField: ROOT.genfit.MaterialEffects.getInstance().setNoEffects()

fitter = ROOT.genfit.DAF()
fitter.setMaxIterations(50)
# fitter.setDebugLvl(1) # produces lot of printout

def materialEffects(switch):
 mat = ROOT.genfit.MaterialEffects.getInstance()
 if not switch: 
  mat.setNoEffects()
 else:
  mat.setMscModel('GEANE')
  mat.setEnergyLossBetheBloch(True)
  mat.setNoiseBetheBloch(True)
  mat.setNoiseCoulomb(True)
  mat.setEnergyLossBrems(True)
  mat.setNoiseBrems(True)

def extractMinAndMax():
 h['tMinAndTmax']={}
 for p in h['TDCMapsX'].GetListOfPrimitives():
  for x in p.GetListOfPrimitives():
   if x.InheritsFrom('TH1'):
     p.cd()
     p.Update()
     tmin = 1000.
     tmax = -1.
     for n in range(1,x.GetNbinsX()-2):
      if x.GetBinContent(n)>2 and x.GetBinContent(n+1)>x.GetBinContent(n)+2 and x.GetBinContent(n+10)>x.GetBinContent(n):
       tmin = x.GetBinCenter(n)
       break
     tmp = x.Clone('tmp')
     tmp.Rebin(10)
     runningMean = 0
     mean = tmp.GetBinContent(tmp.FindBin(tmp.GetMean()))
     for m in range(tmp.GetNbinsX()-1,0,-1):
      runningMean=max(tmp.Integral(m,tmp.GetNbinsX()) / float(tmp.GetNbinsX()-m),2)
      if tmp.GetBinContent(m)>mean/5.:
       tmax = tmp.GetBinCenter(m)
       break
     h['tMinAndTmax'][x.GetName()]=[tmin,tmax]
     h[x.GetName()+'tMin'] =  ROOT.TArrow(tmin,-5.,tmin,0.8,0.05,">")
     h[x.GetName()+'tMax'] =  ROOT.TArrow(tmax,-5.,tmax,0.8,0.05,">")
     h[x.GetName()+'tMin'].SetLineColor(ROOT.kRed)
     h[x.GetName()+'tMax'].SetLineColor(ROOT.kRed)
     h[x.GetName()+'tMin'].Draw()
     h[x.GetName()+'tMax'].Draw()
     p.Update()

def extractRTPanda(hname= 'TDC1000_x'):
 R = ShipGeo.MufluxSpectrometer.InnerTubeDiameter/2. #  = 3.63*u.cm 
 h['rt'+hname] = ROOT.TGraph()
 h['rt'+hname].SetName('rt'+hname)
 n0 = h[hname].FindBin(h['tMinAndTmax'][hname][0])
 n1 = h[hname].FindBin(h['tMinAndTmax'][hname][1])
 Ntot = 0
 for n in range(n0,n1):
   Ntot += h[hname].GetBinContent(n)
 for n in range(n0,n1):
   N = 0
   for k in range(n0,n):
     N+=h[hname].GetBinContent(k)
   h['rt'+hname].SetPoint(n-n0,h[hname].GetBinCenter(n), N/float(Ntot+1E-20)*R)
 h['rt'+hname].SetTitle('rt'+hname)
 h['rt'+hname].SetLineWidth(2)
 if not hname.find('TDC1')<0: h['rt'+hname].SetLineColor(ROOT.kBlue)
 elif not hname.find('TDC2')<0: h['rt'+hname].SetLineColor(ROOT.kCyan)
 elif not hname.find('TDC3')<0: h['rt'+hname].SetLineColor(ROOT.kGreen)
 elif not hname.find('TDC4')<0: h['rt'+hname].SetLineColor(ROOT.kGreen+2)
 h['RTrelations'].cd(1)
 h['legRT'].AddEntry(h['rt'+hname],h['rt'+hname].GetTitle(),'PL')
 h['rt'+hname].Draw('same')
 
def makeRTrelations():
 if not h.has_key('RTrelations'): 
  ut.bookCanvas(h,key='RTrelations',title='RT relations',nx=800,ny=500,cx=1,cy=1)
  h['RTrelations'].cd(1)
  x = h['TDC0']
  h['emptyHist'] = ROOT.TH2F('empty',' ;[ns];[cm] ',100,x.GetBinCenter(1),x.GetBinCenter(x.GetNbinsX()),100,0.,2.)
  h['emptyHist'].SetStats(0)
  h['emptyHist'].Draw()
  extractMinAndMax()    # this has to run after filling TDC histos from trackfit!!
  h['legRT'] = ROOT.TLegend(0.76,0.11,0.997,0.869)
 for p in h['TDCMapsX'].GetListOfPrimitives():
  for o in p.GetListOfPrimitives():
   if o.InheritsFrom('TH1'):  extractRTPanda(hname=o.GetName())
 h['legRT'].Draw('same')

ut.bookHist(h,'TDC2R','RT relation; t [ns] ; r [cm]',100,0.,3000.,100,0.,2.)

def RT(hit,t):
# rt relation, drift time to distance
  R  = ShipGeo.MufluxSpectrometer.InnerTubeDiameter/2. #  = 3.63*u.cm
  t0 = 0
  if MCdata:
   t0 = t-sTree.ShipEventHeader.GetEventTime()
   r =  t0*ShipGeo.MufluxSpectrometer.v_drift
   if MCsmearing: 
     r+=rnr.Gaus(0,MCsmearing)
     r=abs(r)
  else:
   s,v,p,l,view,channelID,tdcId,nRT = stationInfo(hit)
   if nRT in [16,17]: nRT = 18
   if nRT in [30,31]: nRT = 32   # not enough statistics for left and right of T3
   name = 'TDC'+str(nRT)
   if t==0: t=0.1
   if t > h['tMinAndTmax'][name][1]:  r = R
   elif t< h['tMinAndTmax'][name][0]: r = 0
   else: 
      r = h['rt'+name].Eval(t)
   if h.has_key('RTcorr'): r+=h['RTcorr'].Eval(r)
  h['TDC2R'].Fill(t-t0,r)
  return r

def checkMCSmearing():
 ut.bookHist(h,'spr','spatial resolution MC',100,-1.,1.)
 ut.bookHist(h,'MCposX','diff position X',100,-1.,1.)
 ut.bookHist(h,'nMeasMC','number of hits per track',50,-0.5,49.5)
 for i in range(sTree.GetEntries()):
  trackID = {}
  rc = sTree.GetEvent(i)
  if sTree.Digi_MufluxSpectrometerHits.GetEntries() != sTree.MufluxSpectrometerPoint.GetEntries():
    print "digi does not agree with MC, break"
    break
  for n in range(sTree.Digi_MufluxSpectrometerHits.GetEntries()):
   p =  sTree.Digi_MufluxSpectrometerHits[n]
   pmc = sTree.MufluxSpectrometerPoint[n]
   mcp = pmc.GetTrackID()
   if mcp<0: continue
   if abs(sTree.MCTrack[mcp].GetPdgCode())!=13: continue
   t = p.GetDigi()
   # r = (t-sTree.ShipEventHeader.GetEventTime())*ShipGeo.MufluxSpectrometer.v_drift
   r = RT(p,t)
   rc = h['spr'].Fill(r-pmc.dist2Wire())
   vbot,vtop = strawPositionsBotTop[p.GetDetectorID()]
   rc = h['MCposX'].Fill(pmc.GetX()-vbot[0]+r)
   rc = h['MCposX'].Fill(pmc.GetX()-vbot[0]-r)
   if not trackID.has_key(mcp): trackID[mcp]=[]
   trackID[mcp].append(n)
  for mcp in trackID:
   rc=h['nMeasMC'].Fill(len(trackID[mcp]))

def originMCmuons():
 ut.bookHist(h,'origin z/r','origin of muons, z vs r',1000,-600.,600.,100,0.,10.)
 for i in range(sTree.GetEntries()):
  rc = sTree.GetEvent(i)
  r = ROOT.TMath.Sqrt(sTree.MCTrack[0].GetStartX()**2+sTree.MCTrack[0].GetStartY()**2)
  rc = h['origin z/r'].Fill(sTree.MCTrack[0].GetStartZ(),r)
# from TrackExtrapolateTool
parallelToZ = ROOT.TVector3(0., 0., 1.) 
def extrapolateToPlane(fT,z,cplusplus=True):
  rc,pos,mom = False,None,None
  fst = fT.getFitStatus()
  if not fst.isFitConverged(): return rc,pos,mom
# try C++
  if cplusplus:
   pos = ROOT.TVector3()
   mom = ROOT.TVector3()
   try:
    trackLength = muflux_Reco.extrapolateToPlane(fT,z,pos,mom)
    rc = True
   except:
    rc = False
# etrapolate to a plane perpendicular to beam direction (z)
  else:
   if z > DT['Station_1_x_plane_0_layer_0_10000000'][2]-10 and z < DT['Station_4_x_plane_1_layer_1_40110000'][2] + 10:
# find closest measurement
    mClose = 0
    mZmin = 999999.
    M = min(fT.getNumPointsWithMeasurement(),30) # for unknown reason, get stuck for track with large measurements
    for m in range(0,M):
     # print "extr to state m",m,fT.getNumPointsWithMeasurement()
     # if not fT.getPointWithMeasurementAndFitterInfo(m,rep): continue
     try:     st = fT.getFittedState(m)
     except:  
       print "cannot get fitted state"
       continue
     Pos = st.getPos()
     if abs(z-Pos.z())<mZmin:
      mZmin = abs(z-Pos.z())
      mClose = m
    fstate =  fT.getFittedState(mClose)
    NewPosition = ROOT.TVector3(0., 0., z)
    pdgcode = -int(13*fstate.getCharge())
    rep    = ROOT.genfit.RKTrackRep( pdgcode ) 
    state  = ROOT.genfit.StateOnPlane(rep) 
    pos,mom = fstate.getPos(),fstate.getMom()
    rep.setPosMom(state,pos,mom)
    try:    
      rep.extrapolateToPlane(state, NewPosition, parallelToZ )
      pos,mom = state.getPos(),state.getMom()
      rc = True 
    except: 
      print 'error with extrapolation: z=',z/u.m,'m',pos.X(),pos.Y(),pos.Z(),mom.X(),mom.Y(),mom.Z()
      error =  "extrapolateToPlane: error with extrapolation: z=%7.3F m %7.3F %7.3F %7.3F %7.3F %7.3F %7.3F "%(z/u.m,pos.X(),pos.Y(),pos.Z(),mom.X(),mom.Y(),mom.Z())
      ut.reportError(error)
      if Debug: print error
      rc = False
      return rc,pos,mom
   else:
    if z < DT['Station_1_x_plane_0_layer_0_10000000'][2]:
# use linear extrapolation from first state
     fstate = fT.getFittedState(0)
    elif z > DT['Station_4_x_plane_1_layer_1_40110000'][2]:
     M = min(fT.getNumPointsWithMeasurement()-1,30)
     try: 
      fstate = fT.getFittedState(fT.getNumPointsWithMeasurement()-1)
     except: 
       fstate = fT.getFittedState(0)
    pos,mom = fstate.getPos(),fstate.getMom()
# use linear extrap
    lam = (z-pos[2])/mom[2]
    pos[2]=z
    pos[0]=pos[0]+lam*mom[0]
    pos[1]=pos[1]+lam*mom[1]
    rc = True
  return rc,pos,mom

for x in ['','mu']:
 for s in ["","Decay","Hadronic inelastic","Lepton pair","Positron annihilation","charm","beauty","Di-muon P8"]:
  ut.bookHist(h,'p/pt'+x+s,'momentum vs Pt (GeV);p [GeV/c]; p_{T} [GeV/c]',500,0.,500.,100,0.,10.)
  ut.bookHist(h,'p/px'+x+s,'momentum vs Px (GeV);p [GeV/c]; p_{X} [GeV/c]',500,0.,500.,200,-10.,10.)
  ut.bookHist(h,'p/Abspx'+x+s,'momentum vs Px (GeV);p [GeV/c]; p_{X} [GeV/c]',500,0.,500.,100,0.,10.)
  ut.bookHist(h,'TrackMult'+x+s,'track multiplicity',10,-0.5,9.5)
  ut.bookHist(h,'chi2'+x+s,'chi2/nDoF',100,0.,10.)
  ut.bookHist(h,'Nmeasurements'+x+s,'number of measurements used',25,-0.5,24.5)
  ut.bookHist(h,'xy'+x+s,'xy of first state;x [cm];y [cm]',100,-30.,30.,100,-30.,30.)
  ut.bookHist(h,'pxpy'+x+s,'px/pz py/pz of first state',100,-0.2,0.2,100,-0.2,0.2)
  ut.bookHist(h,'p1/p2'+x+s,'momentum p1 vs p2;p [GeV/c]; p [GeV/c]',500,0.,500.,500,0.,500.)
  ut.bookHist(h,'pt1/pt2'+x+s,'P_{T} 1 vs P_{T} 2;p [GeV/c]; p [GeV/c]',100,0.,10.,100,0.,10.)
  ut.bookHist(h,'p1/p2s'+x+s,'momentum p1 vs p2 same sign;p [GeV/c]; p [GeV/c]',500,0.,500.,500,0.,500.)
  ut.bookHist(h,'pt1/pt2s'+x+s,'P_{T} 1 vs P_{T} 2 same sign;p [GeV/c]; p [GeV/c]',100,0.,10.,100,0.,10.)
  if x != '':continue
  ut.bookHist(h,'trueMom'+x+s,'true MC momentum;P [GeV/c];#sigma P/P',500,0.,500.)
  ut.bookHist(h,'recoMom'+x+s,'reco MC momentum;P [GeV/c];#sigma P/P',500,0.,500.)
  ut.bookHist(h,'momResol'+x+s,'momentum resolution function of momentum;P [GeV/c];#sigma P/P', 200,-0.5,0.5,40,0.,400.)
ut.bookHist(h,'Trscalers','scalers for track counting',20,0.5,20.5)
ut.bookHist(h,'weightVsSource','weight vs source MC check',10,-0.5,9.5,1000,0.0,1000.)
for view in ['_u1','_v2','_x1','_x2','_x3','_x4']:
   ut.bookHist(h,'Fitpoints'+view,'points'+view,100,0,400,10,-0.5,9.5)


bfield = ROOT.genfit.FairShipFields()
Bx,By,Bz = ROOT.Double(),ROOT.Double(),ROOT.Double()
def displayTrack(theTrack,debug=False):
     zstart = 0
     nPoints = 100
     delz = 1000./nPoints
     nt = len(h['dispTrack'])
     h['dispTrack'].append( ROOT.TGraph(nPoints) )
     h['dispTrackY'].append( ROOT.TGraph(nPoints) )
     for nP in range(nPoints):
      zstart+=delz
      rc,pos,mom = extrapolateToPlane(theTrack,zstart)
      if not rc: print "dispTrack extrap failed"
      else: 
        h['dispTrack'][nt].SetPoint(nP,zstart,pos[0])
        h['dispTrackY'][nt].SetPoint(nP,zstart,pos[1])
        if debug:
         bfield.get(pos[0],pos[1],pos[2],Bx,By,Bz)
         print "%5.2F %5.2F %5.2F %5.2F %5.2F %5.2F %5.2F %5.2F %5.2F "%(pos[0],pos[1],pos[2],Bx,By,Bz,mom[0],mom[1],mom[2])
        # ptkick 1.03 / dalpha
      if nP ==0:
        fitStatus = theTrack.getFitStatus()
        print "trackinfo P/Pt/chi2/DoF/Ndf:%6.2F %6.2F %6.2F %6.2F"%(mom.Mag(),mom.Pt(),fitStatus.getChi2()/fitStatus.getNdf(),fitStatus.getNdf())
        st = theTrack.getFittedState(0)
        # if st.getPDG()*st.getCharge()>0: print "something wrong here",st.getPDG(),st.getCharge()
        if debug:
         N = theTrack.getNumPointsWithMeasurement()
         momU = theTrack.getFittedState(0).getMom()
         momD = theTrack.getFittedState(N-1).getMom()
         dalpha = momU[0]/momU[2] - ( momD[0]/momD[2] )
         slopeA = momU[0]/momU[2]
         slopeB = momD[0]/momD[2]
         posU = theTrack.getFittedState(0).getPos()
         posD = theTrack.getFittedState(N-1).getPos()
         bA = posU[0]-slopeA*posU[2]
         bB = posD[0]-slopeB*posD[2]
         x1 = zgoliath*slopeA+bA
         x2 = zgoliath*slopeB+bB
         delx = x2-x1
         rc = h['delx'].Fill(delx)
         print "mom from pt kick=",1.03/dalpha
         for j in range(theTrack.getNumPointsWithMeasurement()):
          st = theTrack.getFittedState(j)
          pos,mom = st.getPos(), st.getMom()
          print "%i %5.2F %5.2F %5.2F %5.2F %5.2F  %5.2F %i %i "%(j,pos[0],pos[1],pos[2],mom[0],mom[1],mom[2],st.getPDG(),st.getCharge())
     h['dispTrack'][nt].SetLineColor(ROOT.kMagenta)
     h['dispTrack'][nt].SetLineWidth(2)
     h['dispTrackY'][nt].SetLineColor(ROOT.kCyan)
     h['dispTrackY'][nt].SetLineWidth(2)
     h['simpleDisplay'].cd(1)
     h['dispTrack'][nt].Draw('same')
     h['dispTrackY'][nt].Draw('same')
     h[ 'simpleDisplay'].Update()
     dispTrack3D(theTrack)
def plotMuonTaggerTrack(muTracks):
     for view in ['X','Y']:
      for muTrack in muTracks[view]:
       h['simpleDisplay'].cd(1)
       nt = len(h['dispTrack'])
       h['dispTrack'].append( ROOT.TGraph(2) )
       h['dispTrackY'].append( ROOT.TGraph(2) ) # tricky, framework expects equal number of x and y projections
       zStart = 850.
       x = muTrack[0]*zStart+muTrack[1]
       h['dispTrack'][nt].SetPoint(0,zStart,x)
       zEnd = 1180.
       x = muTrack[0]*zEnd+muTrack[1]
       h['dispTrack'][nt].SetPoint(1,zEnd,x)
       if view == 'X': h['dispTrack'][nt].SetLineColor(ROOT.kRed)
       else:  h['dispTrack'][nt].SetLineColor(ROOT.kBlue)
       h['dispTrack'][nt].SetLineWidth(2)
       h['dispTrack'][nt].Draw('same')
     h[ 'simpleDisplay'].Update()

def findSimpleEvent(event,nmin=2,nmax=6):
   spectrHitsSorted = ROOT.nestedList()
   muflux_Reco.sortHits(sTree.Digi_MufluxSpectrometerHits,spectrHitsSorted,True)
   nH  = {1:0,2:0,3:0,4:0}
   passed = True
   for s in range(1,5):
    for l in range(4):
     for hit in spectrHitsSorted[0][s][l]:  nH[s]+=1
    if nH[s]<nmin or nH[s]>nmax: passed = False
   nu = 0
   for l in range(4):
    for hit in spectrHitsSorted[1][1][l]:  nu+=1
   if nu<nmin or nu>nmax: passed = False
   nv = 0
   for l in range(4):
    for hit in spectrHitsSorted[2][2][l]:  nv+=1
   if nv<nmin or nv>nmax: passed = False
   return passed

def fitTracks(nMax=-1,simpleEvents=True,withDisplay=False,nStart=0,debug=False,PR=1,withRT=False,chi2UL=3):
# simpleEvents=True: select special clean events for testing track fit
 for x in ['p/pt','p/px','p/Abspx','Nmeasurements','chi2','xy','pxpy','TDC2R','p1/p2','pt1/pt2',
           'p/ptmu','p/pxmu','p/Abspxmu','Nmeasurementsmu','chi2mu','xymu','pxpymu']: h[x].Reset()
 if not withDisplay and not Debug and not simpleEvents:
   muflux_Reco.trackKinematics(3.)
   momDisplay()
   return
 for n in range(nStart,sTree.GetEntries()):
   rc = sTree.GetEvent(n)
   if MCdata:
    if sTree.Digi_MufluxSpectrometerHits.GetEntries() != sTree.MufluxSpectrometerPoint.GetEntries():
     print "digi does not agree with MC, break",n
     break
     if PR<10 and sTree.ShipEventHeader.GetUniqueID()==1: continue # non reconstructed events 
   if not withDisplay and n%10000==0: print "event #",n
   if nMax==0: break
   if simpleEvents and simpleEvents<2:
    if not findSimpleEvent(sTree): continue
   if withDisplay:
     print "event #",n
     plotEvent(n)
   if PR==3: theTracks = bestTracks() 
   else:     theTracks = findTracks(PR)
   if simpleEvents==2 and len(theTracks)<simpleEvents: continue
   if PR==1 and len(theTracks)>1: RPCclusters, RPCtracks = muonTaggerClustering(11) # in case file was made with simple reco
   else: RPCclusters, RPCtracks = muonTaggerClustering(PR)
   if withDisplay: plotMuonTaggerTrack(RPCtracks)
   N = -1
   if len(theTracks)>0:
    for aTrack in theTracks:
     N+=1
     fitStatus   = aTrack.getFitStatus()
     if not fitStatus.isFitConverged(): continue
# track quality
     if PR<10: hitsPerStation = countMeasurements(N,PR)
     else:     hitsPerStation = countMeasurements(aTrack,PR)
     if len(hitsPerStation['x1'])<2: continue
     if len(hitsPerStation['x2'])<2: continue
     if len(hitsPerStation['x3'])<2: continue
     if len(hitsPerStation['x4'])<2: continue
     chi2 = fitStatus.getChi2()/fitStatus.getNdf()
     fittedState = aTrack.getFittedState()
     P = fittedState.getMomMag()
     Px,Py,Pz = fittedState.getMom().x(),fittedState.getMom().y(),fittedState.getMom().z()
     if Debug:
       if abs(Py/Pz)>0.15: print 'event with large angle track:',n
     rc = h['chi2'].Fill(chi2)
     rc = h['Nmeasurements'].Fill(fitStatus.getNdf())
     if chi2 > chi2UL: continue
     rc = h['p/pt'].Fill(P,ROOT.TMath.Sqrt(Px*Px+Py*Py))
     rc = h['p/px'].Fill(P,Px)
     rc = h['p/Abspx'].Fill(P,abs(Px))
     pos = fittedState.getPos()
     rc = h['xy'].Fill(pos[0],pos[1])
     rc = h['pxpy'].Fill(Px/Pz,Py/Pz)
# check for muon tag
     rc,posRPC,momRPC = extrapolateToPlane(aTrack,zRPC1)
     if rc:
      tagged = {'X':False,'Y':False}
      for proj in ['X','Y']:
       for m in RPCtracks[proj]:
         if abs(posRPC[0]-m[0]*zRPC1+m[1]) < cuts['muTrackMatch'+proj]: tagged[proj]=True
      if tagged['X'] and tagged['Y'] : # within ~3sigma of any mutrack
       rc = h['chi2mu'].Fill(chi2)
       rc = h['Nmeasurementsmu'].Fill(fitStatus.getNdf())
       rc = h['p/ptmu'].Fill(P,ROOT.TMath.Sqrt(Px*Px+Py*Py))
       rc = h['p/pxmu'].Fill(P,Px)
       rc = h['p/ABSpxmu'].Fill(P,Abs(Px))
       rc = h['xymu'].Fill(pos[0],pos[1])
       rc = h['pxpymu'].Fill(Px/Pz,Py/Pz)
#
     if len(theTracks)==2 and N==0:
      bTrack = theTracks[1]
      fitStatus   = bTrack.getFitStatus()
      if not fitStatus.isFitConverged(): continue
      chi2 = fitStatus.getChi2()/fitStatus.getNdf()
      fittedState = bTrack.getFittedState()
      Pb = fittedState.getMomMag()
      Pbx,Pby,Pbz = fittedState.getMom().x(),fittedState.getMom().y(),fittedState.getMom().z()
      if chi2 > chi2UL: continue
      rc = h['p1/p2'].Fill(P,Pb)
      rc = h['pt1/pt2'].Fill(ROOT.TMath.Sqrt(Px*Px+Py*Py),ROOT.TMath.Sqrt(Pbx*Pbx+Pby*Pby))
    if withRT:
     for hit in sTree.Digi_MufluxSpectrometerHits:
      if not hit.hasTimeOverThreshold(): continue
      rc = RT(hit,hit.GetDigi())
   if withDisplay:
     for theTrack in theTracks:
          fitStatus   = theTrack.getFitStatus()
          if not fitStatus.isFitConverged(): continue
          displayTrack(theTrack,debug)
     next = raw_input("Next (Ret/Quit): ")         
     if next<>'':  break
   if len(theTracks)>0: nMax-=1
   if not hasattr(theTracks,'Class'):
    for theTrack in theTracks:   theTrack.Delete()
 momDisplay()
def momDisplay():
 ROOT.gStyle.SetPalette(ROOT.kGreenPink)
 for x in ['','mu']:
  t = 'mom'+x
  if not h.has_key(t): ut.bookCanvas(h,key=t,title='trackfit'+x,nx=1200,ny=600,cx=4,cy=2)
  rc = h[t].cd(1)
  h['p/pt'+x].SetStats(0)
  rc = h['p/pt'+x].Draw('colz')
  rc = h[t].cd(2)
  rc.SetLogy(1)
  h['p/pt'+x+'_x']=h['p/pt'+x].ProjectionX()
  h['p/pt'+x+'_x'].SetName('p/pt'+x+'_x')
  h['p/pt'+x+'_x'].SetTitle('P [GeV/c]')
  h['p/pt'+x+'_x'].Draw()
  rc = h[t].cd(3)
  h['p/pt'+x+'_y']=h['p/pt'+x].ProjectionY()
  h['p/pt'+x+'_y'].SetName('p/pt'+x+'_y')
  h['p/pt'+x+'_y'].SetTitle('Pt [GeV/c]')
  h['p/pt'+x+'_y'].Draw()
  h[t].Update()
  stats = h['p/pt'+x+'_x'].FindObject('stats')
  stats.SetOptStat(11111111)
  rc = h[t].cd(4)
  h['chi2'+x].Draw()
  rc = h[t].cd(5)
  h['Nmeasurements'+x].Draw()
  rc = h[t].cd(6)
  h['xy'+x].Draw('colz')
  rc = h[t].cd(7)
  h['pxpy'+x].Draw('colz')
  rc = h[t].cd(8)
  if x=='' and h['TDC2R'].GetEntries()>0:
   h['TDC2R_projx'] = h['TDC2R'].ProjectionY()
   h['TDC2R_projx'].SetTitle('RT Relation r projection')
   h['TDC2R_projx'].SetXTitle('drift distance [cm]')
   h['TDC2R_projx'].Draw()
  else:
   h['px'+x]=h['p/pt'+x].ProjectionX()
   h['px'+x].SetName('px'+x)
   h['px'+x].SetTitle('P [GeV/c]')
   h['px'+x].Draw()  
  h[t].Update()
 
sigma_spatial = 0.25 # almost binary resolution! (ShipGeo.MufluxSpectrometer.InnerTubeDiameter/2.)/ROOT.TMath.Sqrt(12) 

def bestTracks():
 theTracks1 = findTracks(PR=11)
 theTracks2 = findTracks(PR=12)
 bestTracks = cloneKiller(theTracks1 + theTracks2)
 return bestTracks
def fitTrack(hitlist,Pstart=3.):
# need measurements
   global fitter
   hitPosLists={}
   trID = 0
   posM = ROOT.TVector3(0, 0, 20.)
   momM = ROOT.TVector3(0,0,Pstart*u.GeV)
# approximate covariance
   covM = ROOT.TMatrixDSym(6)
   resolution   = sigma_spatial
   if not withTDC: resolution = 10*sigma_spatial
   for  i in range(3):   covM[i][i] = resolution*resolution
   # covM[0][0]=resolution*resolution*100.
   for  i in range(3,6): covM[i][i] = ROOT.TMath.Power(resolution / (4.*2.) / ROOT.TMath.Sqrt(3), 2)
   rep = ROOT.genfit.RKTrackRep(13)
# start state
   state = ROOT.genfit.MeasuredStateOnPlane(rep)
   rep.setPosMomCov(state, posM, momM, covM)
# create track
   seedState = ROOT.TVectorD(6)
   seedCov   = ROOT.TMatrixDSym(6)
   rep.get6DStateCov(state, seedState, seedCov)
   theTrack = ROOT.genfit.Track(rep, seedState, seedCov)
   unSortedList = {}
   tmpList = {}
   k=0
   for nhit in hitlist:
      numHit = 0
      if type(nhit)==type(1):   
          hit = sTree.Digi_MufluxSpectrometerHits[nhit]
          numHit = nhit
      else: hit = nhit
      vbot,vtop = strawPositionsBotTop[hit.GetDetectorID()]
      tdc = hit.GetDigi()
      s,v,p,l,view,channelID,tdcId,nRT = stationInfo(hit)
      distance = 0
      if withTDC: distance = RT(hit,tdc)
      tmp = array('d',[vtop[0],vtop[1],vtop[2],vbot[0],vbot[1],vbot[2],distance])
      unSortedList[k] = [ROOT.TVectorD(7,tmp),hit.GetDetectorID(),numHit,view]
      tmpList[k] = vtop[2]
      k+=1
   sorted_z = sorted(tmpList.items(), key=operator.itemgetter(1))
   for k in sorted_z:
      tp = ROOT.genfit.TrackPoint() # note how the point is told which track it belongs to
      hitCov = ROOT.TMatrixDSym(7)
      hitCov[6][6] = resolution*resolution
      # if unSortedList[k[0]][3] != '_x': hitCov[6][6] = 4*resolution*resolution
      measurement = ROOT.genfit.WireMeasurement(unSortedList[k[0]][0],hitCov,1,6,tp) # the measurement is told which trackpoint it belongs to
      measurement.setMaxDistance(ShipGeo.MufluxSpectrometer.InnerTubeDiameter/2.)
      measurement.setDetId(unSortedList[k[0]][1])
      # if Debug: print "trackfit add detid",unSortedList[k[0]][1],unSortedList[k[0]][0][6]
      measurement.setHitId(unSortedList[k[0]][2])
      tp.addRawMeasurement(measurement) # package measurement in the TrackPoint                                          
      theTrack.insertPoint(tp)  # add point to Track
   if not theTrack.checkConsistency():
    print "track not consistent"
    theTrack.Delete()
    return -2
# do the fit
   timer.Start()
   try:  fitter.processTrack(theTrack) # processTrackWithRep(theTrack,rep,True)
   except:   
      print "fit failed"
      timer.Stop()
      theTrack.Delete()
      return -1
    # print "time to fit the track",timer.RealTime()
   if timer.RealTime()>1: # make a new fitter, didn't helped
      error =  "fitTrack::very long fit time %8.6F  %6i"%(timer.RealTime(),len(hitlist))
      ut.reportError(error)
      if Debug: print error
   fitStatus   = theTrack.getFitStatus()
   if Debug: print "Fit result: converged chi2 Ndf",fitStatus.isFitConverged(),fitStatus.getChi2(),fitStatus.getNdf()
   if not fitStatus.isFitConverged():
      theTrack.Delete()
      return -1
   if Debug: 
     chi2 = fitStatus.getChi2()/fitStatus.getNdf()
     fittedState = theTrack.getFittedState()
     P = fittedState.getMomMag()
     print "track fitted Ndf #Meas P",fitStatus.getNdf(), theTrack.getNumPointsWithMeasurement(),P
   if fitStatus.getNdf() < cuts['Ndf']:
      theTrack.Delete()
      return -2 
   return theTrack

def getSlopes(cl1,cl2,view='_x'):
    x,z=[],[]
    for cl in [cl1,cl2]:
     for hit in cl:
      if view=='_x':
        x.append(hit[1])
        z.append(hit[2])
      else:
        x.append(cl[hit][3])
        z.append(cl[hit][4])
    line = numpy.polyfit(z,x,1)
    return line[0],line[1]

Debug = False

minHitsPerCluster, maxHitsPerCluster = 2,10
topA,botA = ROOT.TVector3(),ROOT.TVector3()
topB,botB = ROOT.TVector3(),ROOT.TVector3()
clusters = {}
pl = {0:'00',1:'01',2:'10',3:'11'}
ut.bookHist(h,'biasResTrackMom','momentum of tracks used for biased residuals',400,0.0,400.0)
for s in range(1,5):
   clusters[s]={}
   for view in ['_x','_u','_v']:
    if s>2 and view != '_x': continue
    if s==1 and view == '_v' or s==2 and view == '_u': continue
    ut.bookHist(h,'del'+view+str(s),'del x for '+str(s)+view,100,-20.,20.)
    clusters[s][view]={}
    dx = 0
    for layer in range(0,4):  # p*2+l
      for x in DT:
        if not x.find( 'Station_'+str(s)+view+'_plane_'+pl[layer][0]+'_layer_'+pl[layer][1] )<0:
         dx = DT[x][0]
         dy = DT[x][1]
         break
      if dx == 0:
        print "this should never happen",'Station_'+str(s)+view+'_plane_'+pl[layer][0]+'_layer_'+pl[layer][1]
      ut.bookHist(h,'biasResX_'+str(s)+view+str(layer),'biased residual for '+str(s)+view+' '+str(layer),100,-0.5,0.5,20,-dx,dx)
      ut.bookHist(h,'biasResXL_'+str(s)+view+str(layer),'biased residual for '+str(s)+view+' '+str(layer),100,-2.,2.,20,-dx,dx)
      ut.bookHist(h,'linearRes'+str(s)+view+str(layer),'linear track model residual for '+str(s)+view+' '+str(layer),100,-20.,20.,10,-dx,dx)
      ut.bookHist(h,'biasResY_'+str(s)+view+str(layer),'biased residual for '+str(s)+view+' '+str(layer),100,-0.5,0.5,20,-dy,dy)
      ut.bookHist(h,'biasResYL_'+str(s)+view+str(layer),'biased residual for '+str(s)+view+' '+str(layer),100,-2.,2.,20,-dy,dy)
      ut.bookHist(h,'biasResDist_'+str(s)+view+str(layer),'residual versus drift radius',100,0.,2.,1000,-2.0,2.0)

# book residual histograms for each tube
for detID in xpos:
      ut.bookHist(h,'biasResX_' +str(detID),'biased residual for channel '+str(detID),100,-0.5,0.5,20,-dx,dx)
      ut.bookHist(h,'biasResXL_'+str(detID),'biased residual for channel '+str(detID),100,-2.,2.,20,-dx,dx)
      ut.bookHist(h,'biasResY_' +str(detID),'biased residual for channel '+str(detID),100,-0.5,0.5,20,-dy,dy)      
      ut.bookHist(h,'biasResYL_'+str(detID),'biased residual for channel '+str(detID),100,-2.,2.,20,-dy,dy)      
ut.bookHist(h,'biasResDist','residual versus drift radius',100,0.,2.,1000,-2.0,2.0)
ut.bookHist(h,'biasResDist2','residual versus track distance',100,0.,2.,1000,-2.0,2.0)

ut.bookHist(h,'clsN','cluster sizes',10,-0.5,9.5)
ut.bookHist(h,'Ncls','number of clusters / event',10,-0.5,9.5)
ut.bookHist(h,'delY','del Y from stereo; [cm]',100,-40.,40.)
ut.bookHist(h,'yest','estimated Y from stereo; [cm]',100,-100.,100.)

myGauss = ROOT.TF1('gauss','abs([0])/(abs([2])*sqrt(2*pi))*exp(-0.5*((x-[1])/[2])**2)+abs([3])',4)
myGauss.SetParName(0,'Signal')
myGauss.SetParName(1,'Mean')
myGauss.SetParName(2,'Sigma')
myGauss.SetParName(3,'bckgr')

exclude_layer = None
import MufluxPatRec
def testPR(onlyHits=False):
 global exclude_layer
 trackCandidates = []
 TaggerHits = []
 withNTaggerHits = 0
 withTDCPR = False
 DTHits = []
 key = -1
 for hit in sTree.Digi_MufluxSpectrometerHits:
   key+=1
   # if not hit.isValid(): continue
   if not hit.hasTimeOverThreshold(): continue
   if hit.GetDetectorID() in noisyChannels: continue
   detID = hit.GetDetectorID()
   s,v,p,l,view,channelID,tdcId,nRT = stationInfo(hit)
   if exclude_layer != None and view != '_x':
     if (2*p+l)==exclude_layer:  continue
   vbot,vtop = strawPositionsBotTop[detID]
   tdc = hit.GetDigi()
   distance = 0
   if withTDCPR: distance = RT(hit,tdc)
   DTHits.append( {'digiHit':key,'xtop':vtop.x(),'ytop':vtop.y(),'z':vtop.z(),'xbot':vbot.x(),'ybot':vbot.y(),'dist':distance, 'detID':detID} )
 track_hits = MufluxPatRec.execute(DTHits, TaggerHits, withNTaggerHits, withTDCPR)
 hitlist = {}
 k = 0
 if Debug: 
   print "PR returned %i track candidates"%(len(track_hits))
   plotTracklets(track_hits)
 for nTrack in track_hits:
  h['magPos'].Fill(track_hits[nTrack]['x_in_magnet'],track_hits[nTrack]['y_in_magnet'])
  # node = sGeo.FindNode(track_hits[nTrack]['x_in_magnet'],track_hits[nTrack]['y_in_magnet'],zgoliath)
  # if node.GetName() != "volGoliath_1": continue
  hitlist[k]=[]
  # if len(track_hits[nTrack]['34'])<5 or len(track_hits[nTrack]['y12'])<5: continue
  for dets in ['34','stereo12','y12']:
   rc = h['tracklets'+dets].Fill(len(track_hits[nTrack][dets]))
   for aHit in  track_hits[nTrack][dets]:
    hitlist[k].append( aHit['digiHit'])
  aTrack = fitTrack(hitlist[k],abs(track_hits[nTrack]['p']))
  if type(aTrack) != type(1):
   trackCandidates.append(aTrack)
   k+=1
 if onlyHits: return hitlist
 return trackCandidates

def plotTracklets(track_hits):
 for nTrack in track_hits:
  upStream = True
  for x in [track_hits[nTrack]['y12'],track_hits[nTrack]['34']]:
   clus = {1:[],2:[]}
   for hits in x:
    detID = hits['detID']/10000000
    if detID>2: detID-=2
    clus[detID].append([0,(hits['xtop']+hits['xbot'])/2.,hits['z']])
   slopeA,bA = getSlopes(clus[1],clus[2])
   x1 = zgoliath*slopeA+bA
   nt = len(h['dispTrackSeg'])
   h['dispTrackSeg'].append( ROOT.TGraph(2) )
   if upStream:
    h['dispTrackSeg'][nt].SetPoint(0,0.,bA)
    h['dispTrackSeg'][nt].SetPoint(1,400.,slopeA*400+bA)
    h['dispTrackSeg'][nt].SetLineColor(ROOT.kRed)
    upStream=False
   else:
    h['dispTrackSeg'][nt].SetPoint(0,300.,slopeA*300+bA)
    h['dispTrackSeg'][nt].SetPoint(1,900.,slopeA*900+bA)
    h['dispTrackSeg'][nt].SetLineColor(ROOT.kBlue)
   h['dispTrackSeg'][nt].SetLineWidth(2)
   h['simpleDisplay'].cd(1)
   h['dispTrackSeg'][nt].Draw('same')
 h['simpleDisplay'].Update()

def printClustersPerStation(clusters,s,view):
 k=0
 for n in clusters[s][view]:
   print '--------'
   for x in n:
     s,v,p,l,view,channelID,tdcId,nRT = stationInfo(x[0])
     print k,':',s,view,2*p+l,x[2],x[3]
   k+=1

def findDTClusters(removeBigClusters=True):
   spectrHitsSorted = ROOT.nestedList()
   muflux_Reco.sortHits(sTree.Digi_MufluxSpectrometerHits,spectrHitsSorted,True)
   if Debug: nicePrintout(spectrHitsSorted)
   clusters =  {}
   for s in range(1,5):
    clusters[s]={}
    for view in viewsI[s]:
     allHits = {}
     ncl=0
     for l in range(4): 
      allHits[l]={}
      for hit in spectrHitsSorted[view][s][l]:
       channelID = hit.GetDetectorID()%1000
       allHits[l][channelID]=hit
     if removeBigClusters:
      clustersPerLayer = {}
      for l in range(4):
       clustersPerLayer[l] = dict(enumerate(grouper(allHits[l].keys(),1), 1))
       for Acl in clustersPerLayer[l]:
        if len(clustersPerLayer[l][Acl])>cuts['maxClusterSize']: # kill cross talk brute force
           for x in clustersPerLayer[l][Acl]:
            dead = allHits[l].pop(x)
            if Debug: print "pop",s,viewC[view],l,x
     ncl=0
     tmp={}
     tmp[ncl]=[]
     perLayerUsedHits = {0:[],1:[],2:[],3:[]}
     for level in [1]:
      for i in range(1,Nchannels[s]+1):
       perLayer = {0:0,1:0,2:0,3:0}
       for i0 in range( max(1,i-1),min(Nchannels[s]+1,i+2)):
        if allHits[0].has_key(i0):
          tmp[ncl].append(allHits[0][i0])
          perLayer[0]=i0
       for i1 in range( max(1,i-1), min(Nchannels[s]+1,i+2)):
        if allHits[1].has_key(i1):
          tmp[ncl].append(allHits[1][i1])
          perLayer[1]=i1
       for i2 in range( max(1,i-1), min(Nchannels[s]+1,i+2)):
        if allHits[2].has_key(i2):  
          tmp[ncl].append(allHits[2][i2])
          perLayer[2]=i2
       for i3 in range( max(1,i-1), min(Nchannels[s]+1,i+2)):
        if allHits[3].has_key(i3): 
          tmp[ncl].append(allHits[3][i3])
          perLayer[3]=i3
       if ( (perLayer[0]>0) + (perLayer[1]>0) + (perLayer[2]>0) + (perLayer[3]>0) ) > level:
         # at least 2 hits per station
         ncl+=1
       tmp[ncl]=[]
     if len(tmp[ncl])==0: tmp.pop(ncl)
# cleanup, outliers
     tmpClean = {}
     for ncl in tmp:
       test = []
       mean = 0
       for hit in tmp[ncl]:
          bot,top =  strawPositionsBotTop[hit.GetDetectorID()]
          x = (bot[0]+top[0])/2.
          mean+=x
          test.append([hit,x])
       mean=mean/float(len(test))
# more cleanup, outliers
       tmpClean[ncl]=[]
       for cl in test:
          if abs(mean-cl[1])<2.5 : 
            tmpClean[ncl].append(cl[0])
# cleanup, remove lists contained in another list
     clusters[s][view]=[]
     if len(tmpClean)>0:
      ncl = 0
      marked = []
      for n1 in range(len(tmpClean)):
        if len(tmpClean[n1])==0: continue
        contained = False
        for n2 in range(len(tmpClean)):
          if n1==n2: continue
          if n2 in marked: continue
          if set(tmpClean[n1]) <= set(tmpClean[n2]):
           contained = True
           break
        if contained:  marked.append(n1)
      for n1 in range(len(tmpClean)):
         if len(tmpClean[n1])<2: continue
         if n1 in marked: continue
         test = []
         mean = 0
         for hit in tmpClean[n1]:
          bot,top =  strawPositionsBotTop[hit.GetDetectorID()]
          x = (bot[0]+top[0])/2.
          z = (bot[2]+top[2])/2.
          mean+=x
          test.append([hit,x,z,hit.GetDetectorID()%1000])
         mean=mean/float(len(test))
# more cleanup, outliers
         clusters[s][view].append([])
         for cl in test:
          if abs(mean-cl[1])<2.5: clusters[s][view][ncl].append(cl)
         if len(clusters[s][view][ncl])==0:
           clusters[s][view].pop(ncl)
         else: ncl+=1
     rc = h['clsN'].Fill(ncl)
# eventually split too big clusters for stero layers:
   for s in [1,2]:
    for view in viewsI[s]:
     if view==0:continue
     tmp = {}
     check = {}
     for cl in clusters[s][view]:
      if len(cl)>5:
       for hit in cl: 
         if not tmp.has_key(hit[3]):
           tmp[hit[3]]  =[]
           check[hit[3]]=[]
         if hit[0].GetDetectorID() in check[hit[3]]: continue
         tmp[hit[3]].append(hit)
         check[hit[3]].append(hit[0].GetDetectorID())
     for n in tmp:
       if len(tmp[n])>1:
         clusters[s][view].append(tmp[n])
   if Debug:
    for s in range(1,5):
     for view in viewsI[s]:
      printClustersPerStation(clusters,s,view)
   return clusters

def findDTClustersDebug1(n,tmp):
  for hit in tmp[n]:
   s,v,p,l,view,channelID,tdcId,nRT = stationInfo(hit)
   bot,top = strawPositionsBotTop[hit.GetDetectorID()]
   print s,v,p*2+l,channelID,(bot[0]+top[0])/2.

def findDTClustersDebug2(L):
 for l in L:
  for hit in L[l]:
    print stationInfo(hit),hit.GetTimeOverThreshold() 

def findTracks(PR = 1,linearTrackModel = False,withCloneKiller=True):
   if PR < 3 and sTree.GetBranch('FitTracks'): return sTree.FitTracks
   if PR%2==0 : 
    trackCandidates = testPR()
    if len(trackCandidates)>1: trackCandidates=cloneKiller(trackCandidates)
    return trackCandidates
# switch of trackfit material effect in first pass
   materialEffects(False)
   keysToDThits=MakeKeysToDThits(cuts['lateArrivalsToT'])
   vbot,vtop = strawPositionsBotTop[30002001]
   T3z = vbot[2]
   T3ytop = vtop[1]
   T3ybot = vbot[1]
   trackCandidates = []
   clusters = findDTClusters(removeBigClusters=True)
   # now we have to make a loop over all combinations 
   allStations = True
   for s in range(1,5):
      if len(clusters[s][0])==0: allStations = False
   if len(clusters[1][1])==0 or len(clusters[2][2])==0:   allStations = False
   if allStations:
    t1t2cand = []
    # list of lists of cluster1, cluster2, x
    t3t4cand = []
    h['dispTrackSeg'] = []
    nTrx = -1
    for cl1 in clusters[1][0]:
     for cl2 in clusters[2][0]:
      slopeA,bA = getSlopes(cl1,cl2)
      x1 = zgoliath*slopeA+bA
      t1t2cand.append([cl1,cl2,x1,slopeA,bA])
      nTrx+=1
      if Debug:
       nt = len(h['dispTrackSeg'])
       h['dispTrackSeg'].append( ROOT.TGraph(2) )
       h['dispTrackSeg'][nt].SetPoint(0,0.,bA)
       h['dispTrackSeg'][nt].SetPoint(1,400.,slopeA*400+bA)
       h['dispTrackSeg'][nt].SetLineColor(ROOT.kRed+nTrx)
       h['dispTrackSeg'][nt].SetLineWidth(2)
       h['simpleDisplay'].cd(1)
       h['dispTrackSeg'][nt].Draw('same')
       nt+=1
    for cl1 in clusters[3][0]:
     for cl2 in clusters[4][0]:
      slopeA,bA = getSlopes(cl1,cl2)
      x1 = zgoliath*slopeA+bA
      t3t4cand.append([cl1,cl2,x1,slopeA,bA])
      if Debug:
       nt = len(h['dispTrackSeg'])
       h['dispTrackSeg'].append( ROOT.TGraph(2) )
       h['dispTrackSeg'][nt].SetPoint(0,300.,slopeA*300+bA)
       h['dispTrackSeg'][nt].SetPoint(1,900.,slopeA*900+bA)
       h['dispTrackSeg'][nt].SetLineColor(ROOT.kBlue)
       h['dispTrackSeg'][nt].SetLineWidth(2)
       h['simpleDisplay'].cd(1)
       h['dispTrackSeg'][nt].Draw('same')
       nt+=1
    if Debug: 
      print "trackCandidates",len(t1t2cand),len(t3t4cand)
      h['simpleDisplay'].Update()
    nTrx = -1
    for nt1t2 in range(len(t1t2cand)):
     t1t2 = t1t2cand[nt1t2]
     nTrx+=1
     for nt3t4 in range(len(t3t4cand)):
      t3t4 = t3t4cand[nt3t4]
      delx = t3t4[2]-t1t2[2]
      h['delx'].Fill(delx)
# check also extrapolations at t1 t2, or t3 t4
# makes only sense for zero field
      if linearTrackModel: makeLinearExtrapolations(t1t2,t3t4)
      if abs(delx) < cuts['delxAtGoliath']:
# check for matching u and v hits, make uv combination and check extrap to 
       stereoHits = {}
       if Debug:  print "stereo clusters",len(clusters[1][1]),len(clusters[2][2])
       for nu in range(len(clusters[1][1])):
        stereoHits[1]={}
        clu = clusters[1][1][nu]
        mean_u = 0
        n_u = 0 
        for cl in clu:
           botA,topA = strawPositionsBotTop[cl[0].GetDetectorID()]
           z = (botA[2]+topA[2])/2.
           sl  = (botA[1]-topA[1])/(botA[0]-topA[0])
           b = topA[1]-sl*topA[0]
           yest = sl*(t1t2[3]*topA[2]+t1t2[4])+b
           rc = h['yest'].Fill(yest)
           if yest > botA[1]+cuts['yMax'] : continue
           if yest < topA[1]-cuts['yMax'] : continue
           stereoHits[1][cl[0].GetDetectorID()]=[cl[0],sl,b,yest,z]
           mean_u+=yest
           n_u+=1
        mean_u = mean_u/float(n_u)
        if Debug:  print "0 stereo u",len(stereoHits[1])
        for x in stereoHits[1].keys():
           delta = stereoHits[1][x][3]-mean_u
           rc = h['delta_mean_uv'].Fill(delta)
           if abs(delta)>cuts['hitDist']:  stereoHits[1].pop(x)
# new idea, calulate average of y coordinates, reject hits with distance > 2.5cm!!!!!
        for nv in range(len(clusters[2][2])):
         mean_v = 0
         n_v = 0 
         stereoHits[2]={}
         clv =  clusters[2][2][nv]
         for cl in clv: 
           botA,topA = strawPositionsBotTop[cl[0].GetDetectorID()]
           z = (botA[2]+topA[2])/2.
           sl  = (botA[1]-topA[1])/(botA[0]-topA[0])
           b = topA[1]-sl*topA[0]
           yest = sl*(t1t2[3]*topA[2]+t1t2[4])+b
           rc = h['yest'].Fill(yest)
           if yest > botA[1]+cuts['yMax'] : continue
           if yest < topA[1]-cuts['yMax'] : continue
           stereoHits[2][cl[0].GetDetectorID()]=[cl[0],sl,b,yest,z]
           mean_v+=yest
           n_v+=1
         mean_v = mean_v/float(n_v)
         if Debug:  print "1 stereo v",len(stereoHits[2])
         for x in stereoHits[2].keys():
           delta = stereoHits[2][x][3]-mean_v
           rc = h['delta_mean_uv'].Fill(delta)
           if abs(delta)>cuts['hitDist']:  stereoHits[2].pop(x)
#
         if Debug:  print "stereo  u v",len(stereoHits[1]),len(stereoHits[2])
         if len(stereoHits[1])<cuts['minLayersUV'] or len(stereoHits[2])<cuts['minLayersUV']: continue
         slopeA,bA = getSlopes(stereoHits[1],stereoHits[2],'_uv')
         if Debug: 
            print "y slope",slopeA,bA
            print '----> u'
            for x in stereoHits[1]:  print stereoHits[1][x][3],stereoHits[1][x][4]
            print '----> v'
            for x in stereoHits[2]:  print stereoHits[2][x][3],stereoHits[2][x][4]
         # remove unphysical combinations, pointing outside t3
         yAtT3 = T3z*slopeA + bA
         if Debug: print "uv",nu,nv,yAtT3,T3ybot ,T3ytop , (yAtT3 - T3ybot)  > 2*cuts['yMax'] ,(T3ytop - yAtT3) > 2*cuts['yMax'] 
         if  (yAtT3 - T3ybot)  > 2*cuts['yMax']  or (T3ytop - yAtT3) > 2*cuts['yMax'] : continue
         if Debug:
          nt = len(h['dispTrackSeg'])
          h['dispTrackSeg'].append( ROOT.TGraph(2) )
          h['dispTrackSeg'][nt].SetPoint(0,0.,bA)
          h['dispTrackSeg'][nt].SetPoint(1,900.,slopeA*900+bA)
          h['dispTrackSeg'][nt].SetLineColor(ROOT.kRed+nTrx)
          h['dispTrackSeg'][nt].SetLineWidth(2)
          h['simpleDisplay'].cd(1)
          h['dispTrackSeg'][nt].Draw('same')
          h['simpleDisplay'].Update()
          nt+=1
#
         hitList = []
         for p in range(2):
          for cl in t1t2[p]: hitList.append(cl[0])
         for p in stereoHits:
          for cl in stereoHits[p]: hitList.append(stereoHits[p][cl][0])
         for p in range(2):
          for cl in t3t4[p]: hitList.append(cl[0])
# add late arrivals
         if cuts['lateArrivalsToT']<3000:
          tmp=[]
          for x in hitList:
           l =  len(keysToDThits[x.GetDetectorID()])
           for k in range(1,l):
            key = keysToDThits[x.GetDetectorID()][k]
            tmp.append(sTree.Digi_LateMufluxSpectrometerHits[key])
          hitList=hitList+tmp
         if linearTrackModel: 
          trackCandidates = hitList
         else:
          if zeroField: momFromptkick = 1000.
          else: momFromptkick=ROOT.TMath.Abs(1.03/(t3t4[3]-t1t2[3]+1E-20))
          if Debug:  print "fit track t1t2 %i t3t4 %i stereo %i,%i, with hits %i,  delx %6.3F, pstart %6.3F"%(nt1t2,nt3t4,nu,nv,len(hitList),delx,momFromptkick)
          aTrack = fitTrack(hitList,momFromptkick)
          if Debug:  print "result of trackFit",aTrack
          if type(aTrack) != type(1):
# check if track is still in acceptance:
            rc,pos,mom = extrapolateToPlane(aTrack,T3z)
            reject = False
            if ( (pos[1] - T3ybot)  > 1.2*cuts['yMax'] or (T3ytop - pos[1]) > 1.2*cuts['yMax'] ): reject = True
            mStatistics = countMeasurements(aTrack,PR)
            if len(mStatistics['u'])<cuts['minLayersUV'] or len(mStatistics['v'])<cuts['minLayersUV']: reject = True # require 2 measurements in each view
            if not reject: trackCandidates.append(aTrack)
            else:
             aTrack.Delete()
             if Debug: 
              print "track rejected, outside T3 acceptance or not enough u/v measurements"
              print  (pos[1] - T3ybot)  > 1.2*cuts['yMax'] , (T3ytop - pos[1]) > 1.2*cuts['yMax'] , \
                      len(mStatistics['u'])<2, len(mStatistics['v'])<2
   if withMaterial: materialEffects(True)
   if withCloneKiller:
    if len(trackCandidates)>1: trackCandidates = cloneKiller(trackCandidates)
    if Debug: print "# tracks after clonekiller = ",len(trackCandidates)
    if withMaterial:
     for aTrack in trackCandidates:
      fitter.processTrack(aTrack)
      if Debug: printTrackMeasurements(aTrack,PR)
# switch on trackfit material effect for final fit
   return trackCandidates

def overlap(a,b):
 return [x for x in a if x in b]

def tuneMCefficiency(tkey):
 effFudgeFac = {'u': 0.84, 'v': 0.82, 'x2': 0.91, 'x3': 0.89, 'x1': 0.94, 'x4': 0.96}
 measurements = countMeasurements(tkey)
 detectors = {'x1':0,'x2':0,'x3':0,'x4':0,'u':0,'v':0}
 for d in detectors:
   for m in measurements[d]:
    if rnr.Uniform() < effFudgeFac[d]: detectors[d]+=1
 passed = True
 for d in detectors:
      if detectors[d]<2:
        passed = False
        break
 return passed

def countMeasurements(aTrack,PR=1):
 mStatistics = {'x1':[],'x2':[],'x3':[],'x4':[],'xAll':[],'xDown':[],'xUp':[],'uv':[],'u':[],'v':[]}
 if PR==1 and sTree.GetBranch("TrackInfos"):
  trInfo = sTree.TrackInfos[aTrack]
  for n in range(trInfo.N()):
    detID = trInfo.detId(n)
    hit = ROOT.MufluxSpectrometerHit(detID,0)
    s,v,p,l,view,channelID,tdcId,mdoduleId = stationInfo(hit)
    if trInfo.wL(n) <0.1 and trInfo.wR(n) <0.1: continue
    if view != '_x': 
       mStatistics['uv'].append(detID)
       if view == '_u':  mStatistics['u'].append(detID)
       if view == '_v':  mStatistics['v'].append(detID)
    else:            
     mStatistics['xAll'].append(detID)
     mStatistics['x'+str(s)].append(detID)
    if s > 2:        mStatistics['xDown'].append(detID)
    else:            mStatistics['xUp'].append(detID)
 else:
  for p in aTrack.getPointsWithMeasurement():
    rawM = p.getRawMeasurement()
    info = p.getFitterInfo()
    if not info: continue
    detID = rawM.getDetId()
    test = ROOT.MufluxSpectrometerHit(detID,0.)
    s,v,p,l,view,channelID,tdcId,nRT = stationInfo(test)
    if info.getWeights()[0] <0.1 and info.getWeights()[1] <0.1: continue
    if view != '_x': 
       mStatistics['uv'].append(detID)
       if view != '_u':  mStatistics['u'].append(detID)
       if view != '_v':  mStatistics['v'].append(detID)
    else:            mStatistics['xAll'].append(detID)
    if s > 2:        mStatistics['xDown'].append(detID)
 return mStatistics
def cloneKiller(trackCandidates):
# if all x measurements identical take the one with most u,v
# if tracks share >50% of downstream hits, take the one with max measurements
 detIDs = {}
 for j in range( len(trackCandidates) ):
   detIDs[j]=countMeasurements(trackCandidates[j],PR=11)
 for j in range(len(detIDs)-1):
   if len(detIDs[j]['xDown'])==0: continue
   tj = float(len(detIDs[j]['xDown']))
   sj = trackCandidates[j].getFitStatus()
   for k in range(j+1,len(detIDs)):
     if len(detIDs[k]['xDown'])==0: continue
  # not yet ready
     #if len(detIDs[j]['xAll'])==len(detIDs[k]['xAll']):
     # if len(overlap(detIDs[j]['xAll'],detIDs[k]['xAll']))==len(detIDs[j]['xAll']):
# only differ in stereo 
     #  if len(detIDs['uv']
     o = overlap(detIDs[j]['xDown'],detIDs[k]['xDown'])
     tk = float(len(detIDs[k]['xDown']))
     if max(len(o)/tj,len(o)/tk)>0.49:
       sk = trackCandidates[k].getFitStatus()
       if   sj.getNdf() < sk.getNdf()-cuts['deltaNdf']: detIDs[j]['xDown']=[]
       elif sk.getNdf() < sj.getNdf()-cuts['deltaNdf']: detIDs[k]['xDown']=[]
       elif sj.getChi2()/sj.getNdf() < sk.getChi2()/sk.getNdf():   detIDs[k]['xDown']=[]
       elif sk.getChi2()/sk.getNdf() < sj.getChi2()/sj.getNdf(): detIDs[j]['xDown']=[]
       else: detIDs[j]['xDown']=[]
       if Debug: print "j,k",j,sj.getNdf(),sj.getChi2(),sj.getChi2()/sj.getNdf(),len(detIDs[j]['xDown']),len(detIDs[j]['uv']),' | ', k,sk.getNdf(),sk.getChi2(),sk.getChi2()/sk.getNdf(),len(detIDs[k]['xDown']),len(detIDs[k]['uv'])
     if len(detIDs[j]['xDown'])==0: break
 cloneKilledTracks = []
 j=-1
 for aTrack in trackCandidates:
   j+=1
   if Debug: print "clone killer at work",j,len(detIDs[j]['xDown'])
   if  len(detIDs[j]['xDown'])>0: 
     cloneKilledTracks.append(aTrack)
 j=-1
 for aTrack in trackCandidates:
   j+=1
   if  len(detIDs[j]['xDown'])==0: aTrack.Delete()
 return cloneKilledTracks

def makeLinearExtrapolations(t1t2,t3t4):
 for hit in sTree.Digi_MufluxSpectrometerHits:
    if not hit.hasTimeOverThreshold(): continue
    if hit.GetDetectorID() in noisyChannels:  continue
    s,v,p,l,view,channelID,tdcId,nRT = stationInfo(hit)
    if view != '_x': continue
    vbot,vtop = strawPositionsBotTop[hit.GetDetectorID()]
    z = (vbot[2]+vtop[2])/2.
    x = (vbot[0]+vtop[0])/2.
    if s < 3: track = t3t4
    else:     track = t1t2
    delX = x - (track[3]*z+track[4])
    h['linearRes'+str(s)+view+str(2*p+l)].Fill(delX,x)
 track = t3t4
 for hit in sTree.Digi_MuonTaggerHits:
    channelID = hit.GetDetectorID()
    s  = channelID/10000
    v  = (channelID-10000*s)/1000
    if v!=1: continue # only x info
    vtop,vbot = RPCPositionsBotTop[channelID]
    z = (vtop[2]+vbot[2])/2.
    x = (vtop[0]+vbot[0])/2.
    delX = x - (track[3]*z+track[4])
    h['RPCResX_'+str(s)+str(v)].Fill(delX,x)

def testClusters(nEvent=-1,nTot=1000):
  eventRange = [0,sTree.GetEntries()]
  if not nEvent<0: eventRange = [nEvent,nEvent+nTot]
  for Nr in range(eventRange[0],eventRange[1]):
   sTree.GetEvent(Nr)
   print "===== New Event =====",Nr
   plotEvent(Nr)
   trackCandidates = findTracks()
   print "tracks found",len(trackCandidates)
   for aTrack in trackCandidates:
      displayTrack(aTrack)
   next = raw_input("Next (Ret/Quit): ")
   if next<>'':  break

def printResiduals(aTrack):
   if not aTrack.getNumPointsWithMeasurement()>0: return
   sta = aTrack.getFittedState(0)
   txt = {}
   tmpList={}
   k=0
   for hit in sTree.Digi_MufluxSpectrometerHits:
          if not hit.hasTimeOverThreshold(): continue
          if hit.GetDetectorID() in noisyChannels:  continue
          s,v,p,l,view,channelID,tdcId,nRT = stationInfo(hit)
          vbot,vtop = strawPositionsBotTop[hit.GetDetectorID()]
          z = (vbot[2]+vtop[2])/2.
          rc,pos,mom = extrapolateToPlane(aTrack,z)
          if not rc:
           error =  "printResiduals: plotBiasedResiduals extrap failed"
           ut.reportError(error)
           continue
          distance = 0
          if RTrelations.has_key(rname) or MCdata:
           distance = RT(hit,hit.GetDigi())
          tmp = (vbot[0] - vtop[0])*pos[1] - (vbot[1] - vtop[1])*pos[0] + vtop[0]*vbot[1] - vbot[0]*vtop[1]
          tmp = -tmp/ROOT.TMath.Sqrt( (vtop[0]-vbot[0])**2+(vtop[1]-vbot[1])**2)  # to have same sign as difference in X
          xL = tmp -distance
          xR = tmp +distance
          if abs(xL)<abs(xR):res = xL
          else: res = xR
          tmpList[k]=pos[2]
          txt[k]="%i %s %i %5.3F %5.3F %5.3F %5.3F "%( s,view,2*p+l,pos[0],pos[1],pos[2],res)
          k+=1
   sorted_z = sorted(tmpList.items(), key=operator.itemgetter(1))
   for k in sorted_z:
      print txt[k[0]]

# make TDC plots for hits matched to tracks)
def plotBiasedResiduals(nEvent=-1,nTot=1000,PR=1,onlyPlotting=False,minP=3.):
 timerStats = {'fit':0,'analysis':0,'prepareTrack':0,'extrapTrack':0,'fillRes':0}
 if not onlyPlotting:
  h['biasResDist'].Reset()
  h['biasResDist2'].Reset()
  if not h.has_key('hitMapsX'): plotHitMaps()
  for s in xLayers:
     for p in xLayers[s]:
      for l in xLayers[s][p]:
       for view in xLayers[s][p][l]:
         h[xLayers[s][p][l][view].GetName()].Reset()
         hkey = str(s)+view+str(2*p+l)
         h['biasResDist_'+hkey].Reset()
         h['biasResDist2Wire_'+hkey] = h['biasResDist2'].Clone('biasResDist2Wire_'+hkey)
         ut.bookHist(h,'distIfNoHit_'+hkey,'shortest distance to wire if no hit',100,0.,5.)
  for n in range(576/cuts['RTsegmentation'] ):   h['TDC'+str(n)].Reset()
#
  pos = ROOT.TVector3()
  mom = ROOT.TVector3()
  eventRange = [0,sTree.GetEntries()]
  if not nEvent<0: eventRange = [nEvent,nEvent+nTot]
  timerStats = {'fit':0,'analysis':0,'prepareTrack':0,'extrapTrack':0,'fillRes':0}
  for Nr in range(eventRange[0],eventRange[1]):
   getEvent(Nr)
   h['T0tmp'].Reset()
   if Nr%10000==0:   print "now at event",Nr,' of ',sTree.GetEntries(),sTree.GetCurrentFile().GetName(),time.ctime()
   if not findSimpleEvent(sTree): continue
   timer.Start()
   trackCandidates = findTracks(PR)
   timerStats['fit']+=timer.RealTime()
   if len(trackCandidates)==1: 
    timer.Start()
    spectrHitsSorted = ROOT.nestedList()
    muflux_Reco.sortHits(sTree.Digi_MufluxSpectrometerHits,spectrHitsSorted,True)
    for aTrack in trackCandidates:
       fst = aTrack.getFitStatus()
       if not fst.isFitConverged(): continue
       try:
        sta = aTrack.getFittedState(0)
       except:
        print "problem with getting state, event",sTree.GetCurrentFile().GetName(),Nr
        continue
       if sta.getMomMag() < minP and not zeroField: continue
# check for hits in each station
       stations={1:0,2:0,3:0,4:0}
       for p in aTrack.getPoints():
           rawM = p.getRawMeasurement()
           s = rawM.getDetId()/10000000
           if s < 1 or s > 4: 
             print "error with rawM", rawM.getDetId()
           stations[s]+=1
       if not (stations[1]>1 and stations[2]>1 and stations[3]>1 and stations[4]>1) : continue
       rc = h['biasResTrackMom'].Fill(sta.getMomMag())
       timerStats['prepareTrack']+=timer.RealTime()
       timer.Start()
       for s in range(1,5):
        for view in viewsI[s]:
         for l in range(4):
          hitFound = False
          for hit in spectrHitsSorted[view][s][l]:
           ss,vv,pp,ll,vw,channelID,tdcId,nRT = stationInfo(hit)
           vbot,vtop = strawPositionsBotTop[hit.GetDetectorID()]
           z = (vbot[2]+vtop[2])/2.
           timer.Start()
          # rc,pos,mom = extrapolateToPlane(aTrack,z)
           trackLength = muflux_Reco.extrapolateToPlane(aTrack,z,pos,mom)
           timerStats['extrapTrack']+=timer.RealTime()
           timer.Start()
           if not rc:
            error =  "plotBiasedResiduals: extrapolation failed"
            ut.reportError(error)
            continue
           distance = 0
           if withTDC or MCdata:
            distance = RT(hit,hit.GetDigi())
          #d = (vbot[0] - vtop[0])*pos[1] - (vbot[1] - vtop[1])*pos[0] + vtop[0]*vbot[1] - vbot[0]*vtop[1]
          #d = -d/ROOT.TMath.Sqrt( (vtop[0]-vbot[0])**2+(vtop[1]-vbot[1])**2)  # to have same sign as difference in X
           normal = mom.Cross(vtop-vbot)
           d = normal.Dot(pos-vbot)/normal.Mag()
           res = abs(d) - distance
           h['biasResDist'].Fill(distance,res)
           h['biasResDist2'].Fill(abs(d),res)
           if abs(res) < 0.2: hitFound = True
           hkey = str(ss)+vw+str(2*pp+ll)
           h['biasResDist2Wire_'+hkey].Fill(abs(d),res)
           h['biasResDist_'+hkey].Fill(distance,res)
           m = (vtop[0]-vbot[0])/(vtop[1]-vbot[1])
           b = vtop[0]-m*vtop[1]
           if pos[0]<m*pos[1]+b:
          # left of wire
            d = -abs(d)
           resR = d - distance
           resL = d + distance
           h['biasResX_'+hkey].Fill(resR,pos[0])
           h['biasResY_'+hkey].Fill(resR,pos[1])
           h['biasResXL_'+hkey].Fill(resR,pos[0])
           h['biasResYL_'+hkey].Fill(resR,pos[1])
           h['biasResX_'+hkey].Fill(resL,pos[0])
           h['biasResY_'+hkey].Fill(resL,pos[1])
           h['biasResXL_'+hkey].Fill(resL,pos[0])
           h['biasResYL_'+hkey].Fill(resL,pos[1])
# now for each tube
           detID = str(hit.GetDetectorID())
           h['biasResX_'+detID].Fill(res,pos[0])
           h['biasResY_'+detID].Fill(res,pos[1])
           h['biasResXL_'+detID].Fill(res,pos[0])
           h['biasResYL_'+detID].Fill(res,pos[1])
# make hit and TDC plots for hits matched to tracks, within window suitable for not using TDC
           if abs(res) < 4. :
            t0 = 0
            if MCdata: t0 = sTree.ShipEventHeader.GetEventTime()
            rc = h['TDC'+str(nRT)].Fill(hit.GetDigi()-t0)
            rc = xLayers[ss][pp][ll][vw].Fill( channelID )
            rc = h['T0tmp'].Fill(hit.GetDigi()-t0)
          if not hitFound:
# fill histogram with closest distance to a wire, find z position of present station s layer l
           v = 0
           if (s==1 and view==1) or (s==2 and view==0): v=1000000
           firstWire = s*10000000+v+2000+(l%2)*10000+(l/2)*100000+1
           vbot,vtop = strawPositionsBotTop[firstWire]
           z = (vbot[2]+vtop[2])/2.
           trackLength = muflux_Reco.extrapolateToPlane(aTrack,z,pos,mom)
           minDist = 10000.
           for n in range(Nchannels[s]):
            vbot,vtop = strawPositionsBotTop[firstWire+n]
            normal = mom.Cross(vtop-vbot)
            d = normal.Dot(pos-vbot)/normal.Mag()
            if abs(d)<minDist: minDist=abs(d)
           h['distIfNoHit_'+hkey].Fill(minDist)
       t0 = h['T0tmp'].GetMean()
       rc = h['T0'].Fill(t0)
       timerStats['fillRes']+=timer.RealTime()
       timer.Start()
   timerStats['analysis']+=timer.RealTime()
   for aTrack in trackCandidates:   aTrack.Delete()
 if not h.has_key('biasedResiduals'): 
      ut.bookCanvas(h,key='biasedResiduals',title='biasedResiduals',nx=1600,ny=1200,cx=4,cy=6)
      ut.bookCanvas(h,key='biasedResidualsX',title='biasedResiduals function of X',nx=1600,ny=1200,cx=4,cy=6)
      ut.bookCanvas(h,key='biasedResidualsY',title='biasedResiduals function of Y',nx=1600,ny=1200,cx=4,cy=6)
 j=1
 for s in range(1,5):
   for view in ['_x','_u','_v']:
    if s>2 and view != '_x': continue
    if s==1 and view == '_v' or s==2 and view == '_u': continue
    for l in range(0,4):
     if withTDC:     hname = 'biasResX_'+str(s)+view+str(l)
     else:     hname = 'biasResXL_'+str(s)+view+str(l)
     hnameProjX = 'biasRes_'+str(s)+view+str(l)
     h[hnameProjX] = h[hname].ProjectionX()
     tc = h['biasedResiduals'].cd(j)
     if h[hname].GetEntries()<10:
       h[hnameProjX].Draw() 
       j+=1
       continue
     fitResult = h[hnameProjX].Fit('gaus','SQ','',-0.5,0.5)
     rc = fitResult.Get()
     fitFunction = h[hnameProjX].GetFunction('gauss')
     if not fitFunction : fitFunction = myGauss
     if not rc:
      print "simple gaus fit failed"
      fitFunction.SetParameter(0,h[hnameProjX].GetEntries()*h[hnameProjX].GetBinWidth(1))
      fitFunction.SetParameter(1,0.)
      fitFunction.SetParameter(2,0.1)
      fitFunction.SetParameter(3,1.)
     else:
      fitFunction.SetParameter(0,rc.GetParams()[0]*ROOT.TMath.Sqrt(2*ROOT.TMath.Pi())*rc.GetParams()[2])
      fitFunction.SetParameter(1,rc.GetParams()[1])
      fitFunction.SetParameter(2,rc.GetParams()[2])
      fitFunction.SetParameter(3,0.)
     fitResult = h[hnameProjX].Fit(fitFunction,'SQ','',-0.2,0.2)
     fitResult = h[hnameProjX].Fit(fitFunction,'SQ','',-0.5,0.5)
     rc = fitResult.Get()
     if not rc:
       print hnameProjX
       h[hnameProjX].Draw()
       j+=1
       continue
     tc.Update()
     stats = h[hnameProjX].FindObject("stats")
     stats.SetX1NDC(0.563258)
     stats.SetY1NDC(0.526687)
     stats.SetX2NDC(0.938728)
     stats.SetY2NDC(0.940086)
     stats.SetOptFit(111)
     stats.SetOptStat(0)
     mean = rc.GetParams()[1]
     rms  = rc.GetParams()[2]
     Emean = rc.GetErrors()[1]
     Erms  = rc.GetErrors()[2]
     print "%i, %s, %i mean=%5.2F+/-%5.2F RMS=%5.2F+/-%5.2F [mm]"%(s,view,l,mean*10,Emean*10,rms*10,Erms*10)
     residuals[j-1]= h[hnameProjX].GetMean()   # fitresult too unstable, mean
     # make plot of mean as function of X,Y
     for p in ['X','Y']:
      if withTDC:      hname = 'biasRes'+p+'_'+str(s)+view+str(l)
      else:      hname = 'biasRes'+p+'L_'+str(s)+view+str(l)
      hmean = hname+'_mean'+p
      h[hmean] = h[hname].ProjectionY(hname+'_mean')
      h[hmean].Reset()
      rc = h['biasedResiduals'+p].cd(j)  
      for k in range(1,h[hname].GetNbinsY()+1):
       sli = hname+'_'+str(k) 
       h[sli] = h[hname].ProjectionX(sli,k,k)
       if h[sli].GetEntries()<10: continue
       fitResult = h[sli].Fit('gaus','SQ','',-0.5,0.5)
       rc = fitResult.Get()
       fitFunction = h[sli].GetFunction('gauss')
       if not fitFunction : fitFunction = myGauss
       if not rc:
        print "simple gaus fit failed"
        fitFunction.SetParameter(0,h[sli].GetEntries()*h[sli].GetBinWidth(1))
        fitFunction.SetParameter(1,0.)
        fitFunction.SetParameter(2,0.1)
        fitFunction.SetParameter(3,1.)
       else:
        fitFunction.SetParameter(0,rc.GetParams()[0]*ROOT.TMath.Sqrt(2*ROOT.TMath.Pi())*rc.GetParams()[2])
        fitFunction.SetParameter(1,rc.GetParams()[1])
        fitFunction.SetParameter(2,rc.GetParams()[2])
        fitFunction.SetParameter(3,0.)
       fitResult = h[sli].Fit(fitFunction,'SQ','',-0.3,0.3)
       rc = fitResult.Get()
       mean,rms = 0,0
       if rc:
        mean = rc.GetParams()[1]
        rms  = rc.GetParams()[2]
       rc = h[hmean].SetBinContent( k, mean)
       rc = h[hmean].SetBinError(k, rms)
      amin,amax,nmin,nmax = ut.findMaximumAndMinimum(h[hmean])
      if amax<3. and amin>-3.:
       h[hmean].SetMaximum(0.2)
       h[hmean].SetMinimum(-0.2)
      else: 
       h[hmean].SetLineColor(ROOT.kRed)
       h[hmean].SetMaximum(0.2)
       h[hmean].SetMinimum(-0.2)
      h[hmean].Draw()
     j+=1
 momDisplay()
 print "timing:",timerStats
def investigateActiveArea():
 r = 1.815
 h['biasResDist2_projx'].Draw()
 h['tubeLine']=ROOT.TLine(r,0,r,2000)
 h['tubeLine'].SetLineColor(ROOT.kRed)
 h['tubeLine'].Draw('same')
 h['tubeLineX']=ROOT.TLine(r-0.19,0,r-0.19,2000)
 h['tubeLineX'].SetLineColor(ROOT.kMagenta)
 h['tubeLineX'].Draw('same')

def plotSigmaRes():
 ut.bookHist(h,'resDistr','residuals',50,0.,0.1)
 for tc in h['biasedResiduals'].GetListOfPrimitives():
  for p in tc.GetListOfPrimitives():
   if p.InheritsFrom('TH1'):
    fitFun = p.GetFunction('gauss')
    h['resDistr'].Fill(fitFun.GetParameter(2))
 ROOT.gROOT.FindObject('c1').cd()
 h['resDistr'].Draw()
def calculateRTcorrection():
  hkeys = h.keys()
  for hist in hkeys:
   if hist.find('biasResDist')!=0: continue
   if not hist.find('proj')<0: continue
   if hist == 'biasResDist2' : continue
   v=hist.replace('biasResDist','')
   h['RTcorr'+v]=ROOT.TGraph()
   N = 0
   tmpx = h[hist].ProjectionX()
   hresol = 'resVsDr'+v
   h[hresol]=tmpx.Clone(hresol)
   h[hresol].SetTitle('resolution as function of driftRadius')
   h[hresol].Reset()
   for n in range(1,h[hist].GetNbinsX()):
    tmp = h[hist].ProjectionY('tmp',n,n+1)
    fitResult = tmp.Fit('gaus','SQ','',-0.2,0.2)
    rc = fitResult.Get()
    if rc:
     h['RTcorr'+v].SetPoint(N,tmpx.GetBinCenter(n),rc.GetParams()[1])
     h[hresol].SetBinContent(n,rc.GetParams()[2])
     N+=1
  if not h.has_key('RTCorrection'): 
      ut.bookCanvas(h,key='RTCorrection',title='RTCorrection',nx=1200,ny=1400,cx=1,cy=2)
  tc = h['RTCorrection'].cd(1)
  h['RTcorr'].SetLineColor(ROOT.kMagenta)
  h['RTcorr'].SetLineWidth(2)
  h['hRTCorrection']=h['resVsDr'].Clone('hRTCorrection')
  h['hRTCorrection'].SetTitle('')
  h['hRTCorrection'].SetStats(0)
  h['hRTCorrection'].SetMaximum(0.02)
  h['hRTCorrection'].SetMinimum(-0.02)
  h['hRTCorrection'].Reset()
  h['hRTCorrection'].SetLineColor(0)
  h['hRTCorrection'].Draw()
  for x in h:
   if x.find('RTcorr')!=0: continue
   h[x].Draw()
  tc = h['RTCorrection'].cd(2)
  h['resVsDr'].SetLineColor(ROOT.kMagenta)
  h['resVsDr'].SetLineWidth(2)
  h['resVsDr'].SetMaximum(0.2)
  h['resVsDr'].Draw()
  for x in h:
   if x.find('resVsDr')!=0: continue
   if x.find('u')>0 or x.find('v')>0: 
       h[x].SetLineColor(ROOT.kGreen)
   elif x.find('_3')>0 or x.find('_4')>0: 
       h[x].SetLineColor(ROOT.kRed)
   h[x].Draw('same')

def analyzeSingleDT():
 keys = xpos.keys()
 keys.sort()
 for detID in keys:
    histo = h['biasResX_'+str(detID)+'_projx']
    mean,rms = -999.,0.
    if histo.GetSumOfWeights()>25:
     fitResult = histo.Fit('gaus','SQ','',-0.5,0.5)
     rc = fitResult.Get()
     fitFunction = histo.GetFunction('gauss')
     if not fitFunction : fitFunction = myGauss
     if not rc:
        # print "simple gaus fit failed"
        fitFunction.SetParameter(0,histo.GetEntries()*histo.GetBinWidth(1))
        fitFunction.SetParameter(1,0.)
        fitFunction.SetParameter(2,0.1)
        fitFunction.SetParameter(3,1.)
     else:
        fitFunction.SetParameter(0,rc.GetParams()[0]*ROOT.TMath.Sqrt(2*ROOT.TMath.Pi())*rc.GetParams()[2])
        fitFunction.SetParameter(1,rc.GetParams()[1])
        fitFunction.SetParameter(2,rc.GetParams()[2])
        fitFunction.SetParameter(3,0.)
     fitResult = histo.Fit(fitFunction,'SQ','',-0.3,0.3)
     rc = fitResult.Get()
     if rc:
        mean = rc.GetParams()[1]
        rms  = rc.GetParams()[2]
    uf =  histo.GetBinContent(0)
    of = histo.GetBinContent(histo.GetNbinsX()+1)
    if mean < -900: print "channel:%i : not enough statistics, integral=%i, under- over-flow: %i,%i"%(detID,histo.GetSumOfWeights(),uf,of)
    else: print "channel:%i : mean=%6.3Fmm,  sigma=%6.3Fmm"%(detID,mean*10,rms*10)

def plot2dResiduals(minEntries=-1):
 if not h.has_key('biasedResiduals2dX'): 
      ut.bookCanvas(h,key='biasedResiduals2dX',title='biasedResiduals function of X',nx=1600,ny=1200,cx=4,cy=6)
      ut.bookCanvas(h,key='biasedResiduals2dY',title='biasedResiduals function of Y',nx=1600,ny=1200,cx=4,cy=6)
 j=1
 for s in range(1,5):
   for view in ['_x','_u','_v']:
    if s>2 and view != '_x': continue
    if s==1 and view == '_v' or s==2 and view == '_u': continue
    for l in range(0,4):
     hname = 'biasResX_'+str(s)+view+str(l)
     if h[hname].GetEntries()<1: continue
     print s,view,l,h[hname].GetEntries()
     for p in ['X','Y']:
      hname = 'biasRes'+p+'_'+str(s)+view+str(l)
      rc = h['biasedResiduals2d'+p].cd(j)
      if minEntries >0: h[hname].SetMinimum(minEntries)
      h[hname].Draw('box')
     j+=1

myGauss2 = ROOT.TF1('test','abs([0])/(abs([2])*sqrt(2*pi))*exp(-0.5*((x-[1])/[2])**2)+abs( [3]+[6]*x+[7]*x**2 )+abs([4])/(abs([5])*sqrt(2*pi))*exp(-0.5*((x-[1])/[5])**2)',8)
myGauss2.SetParName(0,'Signal')
myGauss2.SetParName(1,'Mean')
myGauss2.SetParName(2,'Sigma')
myGauss2.SetParName(3,'bckgr')
myGauss2.SetParName(4,'Tail')
myGauss2.SetParName(5,'Sigma2')
myGauss2.SetParName(6,'bckgr2')
myGauss2.SetParName(7,'bckgr3')
myGauss2.FixParameter(6,0.)
myGauss2.FixParameter(7,0.)
# try to get an estimate per layer by analyzing residual plots with large statistics
# is the second gaussian due to close left/right ambiguities? or real signal?
def binoEff(n=4,k=2):
 totEff = 0
 for i in range(k,n+1):  totEff += ROOT.TMath.Binomial(n,i)*eff**i*(1-eff)**(n-i)
 print "global efficiency = %5.4F  %i %i"%(totEff,n,k)

def DTeffWithRPCTracks(Nevents=0,onlyPlotting=False):
 align2RPC = {4:[-1.,3.2],3:[-2.,5.],2:[-6.,8.],1:[-6.,8.]}
 if not onlyPlotting:
  if Nevents==0: Nevents = sTree.GetEntries()
  for tag_s in range(1,5):
   for s in range(1,5):
    ut.bookHist(h,'hitsIn'+str(s)+'_'+str(tag_s),'number of hits '+str(s),10,-0.5,9.5)
    ut.bookHist(h,'hits'  +str(s)+'_'+str(tag_s),'number of hits in layer '+str(s),5,-0.5,4.5)
    for l in range(4):
     if tag_s==1: ut.bookHist(h,'distX' +str(s)+str(l),'distance of RPC track to hit '+str(s)+str(l),100,-10.,10.)
     ut.bookHist(h,'distXref'+str(s)+str(l)+'_'+str(tag_s),'distance of refitted RPC track to hit '+str(s)+str(l),100,-10.,10.)
  Ntot  = [0,0,0,0,0]
  Ineff = 0
  view = 0
  for n in range(Nevents):
   rc = sTree.GetEvent(n)
   if not findSimpleEvent(sTree): continue
   if len(sTree.RPCTrackX)>1 or len(sTree.RPCTrackY)>1 : continue
   spectrHitsSorted = ROOT.nestedList()
   candidates= {1:{0:[],1:[],2:[],3:[]}, 2:{0:[],1:[],2:[],3:[]}, 3:{0:[],1:[],2:[],3:[]},4:{0:[],1:[],2:[],3:[]}}
   muflux_Reco.sortHits(sTree.Digi_MufluxSpectrometerHits,spectrHitsSorted,True)
   for mu in sTree.RPCTrackX:
  # mu.m()*z + mu.b()
    for s in range(1,5):
      for l in range(4):
       for hit in spectrHitsSorted[view][s][l]:
         vbot,vtop = strawPositionsBotTop[hit.GetDetectorID()]
         z = (vbot[2]+vtop[2])/2.
         x = (vbot[0]+vtop[0])/2.
         xExtr = mu.m()*z + mu.b()
         diff = x-xExtr + align2RPC[s][0]
         if abs(x-xExtr)<align2RPC[s][1]: candidates[s][l].append(hit)
         rc = h['distX'+str(s)+str(l)].Fill(x-xExtr)
     # tagging with station tag_s, require only one candidate.
    for tag_s in range(1,5):
     unique = True
     for l in candidates[tag_s]:
      if len(candidates[tag_s][l])>1: unique = False
     if not unique: continue
     pos={}
     zRPC1 = 880.
     pos[zRPC1] = mu.m()*zRPC1 + mu.b()
     for l in candidates[tag_s]:
      for hit in candidates[tag_s][l]:
       vbot,vtop = strawPositionsBotTop[hit.GetDetectorID()]
       pos[(vbot[2]+vtop[2])/2.]=(vbot[0]+vtop[0])/2.
     if len(pos)<3: continue # 1 RPC point + >1 DT point
     coefficients = numpy.polyfit(pos.keys(),pos.values(),1)
     Ntot[tag_s] += 1
     nhits={1:0,2:0,3:0,4:0}
     for s in range(1,5):
       for l in range(4):
          first = True
          for hit in spectrHitsSorted[view][s][l]:
           vbot,vtop = strawPositionsBotTop[hit.GetDetectorID()]
           z = (vbot[2]+vtop[2])/2.
           x = (vbot[0]+vtop[0])/2.
           xExtr = coefficients[0]*z + coefficients[1]
           rc = h['distXref'+str(s)+str(l)+'_'+str(tag_s)].Fill(x-xExtr)
           if abs(x-xExtr)<5.:
             if first:
               nhits[s]+=1
               first = False
               h['hits'+str(s)+'_'+str(tag_s)].Fill(l)
       h['hitsIn'+str(s)+'_'+str(tag_s)].Fill(nhits[s])
     if nhits[4] < 2: Ineff+=1
     for s in range(1,5): h['hits'+str(s)+'_'+str(tag_s)].SetBinContent(6,Ntot[tag_s])
  print "rough estimate of station inefficiency:",float(Ineff)/(Ntot[tag_s]+1E-5)
  ut.writeHists(h,'histos-DTEff'+rname)
 else:
# analysis part
  if not h.has_key('hits1_1'): ut.readHists(h,'DTEff.root')
  effPerLayer = {}
  for tag_s in range(1,5):
   t = 'tagstation'+str(tag_s)
   if not h.has_key(t):
    ut.bookCanvas(h,key=t,title='with tagging station '+str(tag_s),nx=1600,ny=1200,cx=4,cy=4)
   print "analysis with tagging station ",tag_s
   effPerLayer[tag_s] = {}
   for s in range(1,5):
    for l in range(4):
     j = (s-1)*4+l+1
     h[t].cd(j)
     hname = 'distXref'+str(s)+str(l)+'_'+str(tag_s)
     fitFunction = myGauss
     fitFunction.SetParameter(0,h[hname].GetEntries()*h[hname].GetBinWidth(1))
     fitFunction.SetParameter(1,0.)
     fitFunction.SetParameter(2,1.2)
     fitFunction.SetParameter(3,0.)
     fitResult = h[hname].Fit(fitFunction,'SQ','',-10.,10.)
     rc = fitResult.Get()
     background = rc.Parameter(3) * h[hname].GetNbinsX()
     signal = h[hname].GetSumOfWeights()-background
     effPerLayer[tag_s][10*s+l] = signal / float(h['hits'+str(s)+'_'+str(tag_s)].GetBinContent(6))
   h[t].Print('DTeffPerLayer-station'+str(tag_s)+'_res.pdf')
   h[t].Print('DTeffPerLayer-station'+str(tag_s)+'_res.png')
  print "tagging station                   :   1       2       3       4"
  for s in range(1,5):
   for l in range(4): 
    text = "efficiencies for station %i layer %i:"%(s,l)
    for tag_s in range(1,5):
      text+=" %5.2F%% "%(effPerLayer[tag_s][10*s+l]*100)
    print text
  ut.bookHist(h,'DTeffPerLayer','DT hit efficiency per layer',50,0.5,50.5)
  choice = {1:2,2:1,3:1,4:1}
  for s in choice:
   tag_s = choice[s]
   for l in range(4):
     h['DTeffPerLayer'].SetBinContent(s*10+l+1,effPerLayer[tag_s][10*s+l])
  h['DTeffPerLayer'].SetMinimum(0.6)
  h['DTeffPerLayer'].SetMaximum(1.0)
  h['DTeffPerLayer'].SetStats(0)
  t =  ROOT.gROOT.FindObject('c1')
  t.cd()
  h['DTeffPerLayer'].Draw()
  t.Print('DTeffPerLayer.pdf')
  t.Print('DTeffPerLayer.png')
# inefficiency per station
  first = True
  h['leghits']=ROOT.TLegend(0.51,0.41,0.84,0.59)
  for s in choice:
    tag_s = choice[s]
    ntracks = h['hits'+str(s)+'_'+str(tag_s)].GetBinContent(6)
    xHits = h['hitsIn'+str(s)+'_'+str(tag_s)]
    inEff = xHits.GetBinContent(1)+xHits.GetBinContent(2)
    xx = 'tmphitsIn'+str(s)+'_'+str(tag_s)
    h[xx]=xHits.Clone(xx)
    h[xx].Scale(1./ntracks)
    h[xx].SetStats(0)
    h[xx].SetLineColor(s+1)
    h[xx].SetLineWidth(2)
    h[xx].SetMarkerStyle(20)
    if first: 
       h[xx].GetXaxis().SetRangeUser(-0.5,6.5)
       h[xx].Draw()
       first = False
    else:  h[xx].Draw('same')
    rc = h['leghits'].AddEntry(h[xx],xHits.GetName().split('_')[0],'PL')
    print "station %i ineff=%5.2F%%"%(s,inEff/ntracks*100.)
  h['leghits'].Draw()
  t.Print('DTeffHitsPerStation.pdf')
  t.Print('DTeffHitsPerStation.png')
  

def efficiencyEstimates(method=0):
 hinweis={}
 hinweis[0] = "method 0: use biasResDistX, count entries between -0.5 and 0.5"
 hinweis[1] = "method 1: use biasResDistX, but take signal from single gauss fit"
 hinweis[2] = "method 2: use biasRes, subtract background from fit on number of entries"
 hinweis[3] = "method 3: use biasRes, take signal from double gauss fit"
 if not h.has_key('biasedResiduals'): plotBiasedResiduals(onlyPlotting=True)
 Ntracks = h['biasResTrackMom'].GetEntries()
 ut.bookHist(h,'effLayer','efficiency per Layer',24,-0.5,23.5)
 if not h.has_key('biasResDistX_1_x1'):
  for s in range(1,5):
   for view in ['_x','_u','_v']:
    if s>2 and view != '_x': continue
    if s==1 and view == '_v' or s==2 and view == '_u': continue
    for l in range(0,4):
     hname = 'biasResDistX_'+str(s)+view+str(l)
     h[hname] = h['biasResDist_'+str(s)+view+str(l)].ProjectionY().Clone(hname)
 j = 0
 h['effDict'] = {}
 print "efficiencies using ",hinweis[method]
 for s in range(1,5):
   for view in ['_x','_u','_v']:
    if s>2 and view != '_x': continue
    if s==1 and view == '_v' or s==2 and view == '_u': continue
    effStation = 0
    for l in range(0,4):
     tc = h['biasedResiduals'].cd(j+1)
     if method == 0 or method == 1: hname = 'biasResDistX_'+str(s)+view+str(l)
     else:                          hname = 'biasResXL_'+str(s)+view+str(l)+'_projx'
     xmin = h[hname].GetBinCenter(1)
     xmax = h[hname].GetBinCenter(h[hname].GetNbinsX()-1)
     if method==0 or method==1: 
      xmin = h[hname].GetBinCenter(h[hname].FindBin(-0.7))
      xmax = h[hname].GetBinCenter(h[hname].FindBin(0.7))
     fitResult = h[hname].Fit('gaus','SQ','',xmin,xmax)
     rc = fitResult.Get()
     fitFunction = h[hname].GetFunction('DoubleGauss')
     if not fitFunction : fitFunction = myGauss2
     if not rc:
      print "simple gaus fit failed"
      fitFunction.SetParameter(0,h[hname].GetEntries()*h[hname].GetBinWidth(1))
      fitFunction.SetParameter(1,0.)
      fitFunction.SetParameter(2,0.1)
      fitFunction.SetParameter(3,1.)
      fitFunction.SetParameter(4,0.)
      fitFunction.SetParameter(5,1.)
     else:
      fitFunction.SetParameter(0,rc.GetParams()[0]*ROOT.TMath.Sqrt(2*ROOT.TMath.Pi())*rc.GetParams()[2])
      fitFunction.SetParameter(1,rc.GetParams()[1])
      fitFunction.SetParameter(2,rc.GetParams()[2])
      fitFunction.SetParameter(3,0.)
      fitFunction.SetParameter(4,fitFunction.GetParameter(0)*0.1)
      fitFunction.SetParameter(5,fitFunction.GetParameter(2)*10.)
     fitResult = h[hname].Fit(fitFunction,'SQ','',xmin,xmax)
     h[hname].Draw()
     rc = fitResult.Get()
     if method == 0: estSignal = h[hname].Integral(375,625)
     elif method == 1 or method == 3: estSignal = ( abs(rc.GetParams()[0])+abs(rc.GetParams()[4]))/h[hname].GetBinWidth(1)
     elif method == 2: estSignal = h[hname].GetSumOfWeights() - rc.GetParams()[3]*h[hname].GetNbinsX()
     eff = estSignal/float(Ntracks)
     print "eff for %s = %5.2F"%(hname,eff)
     h['effDict'][hname]=eff
     effStation += eff
     rc = h['effLayer'].Fill(j,eff)
     j+=1
    print "station, %i %s, average efficiency: %5.3F"%(s,view,effStation/4.)
 for p in h['biasedResiduals'].GetListOfPrimitives():   p.SetLogy(1)
 tc1 = ROOT.gROOT.FindObject('c1')
 tc1.cd()
 for n in range(1,h['effLayer'].GetNbinsX()+1): h['effLayer'].SetBinError(n,0.02)
 h['effLayer'].SetMaximum(1.)
 h['effLayer'].SetMinimum(0.)
 h['effLayer'].SetStats(0)
 fitResult = h['effLayer'].Fit('pol0','SQ')
 rc=fitResult.Get()
 h['Efftxt'] = ROOT.TLatex(8,0.4,'mean efficiency = %5.2F'%(rc.GetParams()[0]))
 h['Efftxt'].Draw()
 h['biasedResiduals'].Print('effEstimate-method'+str(method)+'.png')
 h['biasedResiduals'].Print('effEstimate-method'+str(method)+'.pdf')
 tc1.Print('effEstimate-method'+str(method)+'-summary.png')
 tc1.Print('effEstimate-method'+str(method)+'-summary.pdf')
def checkEffectOfEffCor():
 interestingHistos = []
 for a in ['p/pt','p/Abspx','p1/p2','p1/p2s','Trscalers']:
  for x in ['','mu']:
    interestingHistos.append(a+x)
 h['MC']      = {}
 h['MCtuned2'] = {}
 h['MCtuned0'] = {}
 h['MCNotune'] = {}
 h['MCtuned0rec'] = {}
 ut.readHists(h['MC'],         'momDistributions-mbias.root',interestingHistos)
 ut.readHists(h['MCtuned2'],   'momDistributions-mbias-effTuned-M2.root',interestingHistos)
 ut.readHists(h['MCtuned0'],   'momDistributions-mbias-effTuned-M0.root',interestingHistos)
 ut.readHists(h['MCtuned0rec'],   'momDistributions-mbias-effTuned-M0-reco.root',interestingHistos)
 ut.readHists(h['MCNotune'],   'momDistributions-mbias-NoeffTuned.root',interestingHistos)
 ut.readHists(h['MC'],         'momDistributions-charm.root',interestingHistos)
 ut.readHists(h['MCtuned2'],   'momDistributions-charm-effTuned-M2.root',interestingHistos)
 ut.readHists(h['MCtuned0'],   'momDistributions-charm-effTuned-M0.root',interestingHistos)
 ut.readHists(h['MCtuned0rec'],   'momDistributions-charm-effTuned-M0-reco.root',interestingHistos)
 ut.readHists(h['MCNotune'],   'momDistributions-charm-NoeffTuned.root',interestingHistos)
 h['MC']['p/pt_projx'].Draw()
 h['MCtuned0']['p/pt_projx'].SetLineColor(ROOT.kRed)
 h['MCtuned2']['p/pt_projx'].SetLineColor(ROOT.kGreen)
 h['MCtuned0rec']['p/pt_projx'].SetLineColor(ROOT.kCyan)
 h['MCNotune']['p/pt_projx'].SetLineColor(ROOT.kMagenta)
 h['MC']['p/pt_projxB']=h['MC']['p/pt_projx'].Clone('p/pt_projxB')
 h['MC']['p/pt_projxB'].Rebin(10)
 for x in ['MCtuned0','MCtuned2','MCNotune','MCtuned0rec']:
  print x, h[x]['p/pt_projx'].GetEntries()/h['MC']['p/pt_projx'].GetEntries()
  # h[x]['p/pt_projx'].Draw('same')
  h[x+'ratio']= h[x]['p/pt_projx'].Clone(x+'ratio')
  h[x+'ratio'].Divide(h['MC']['p/pt_projx'])
  h[x+'ratio'].Fit('pol0','','',5.,300.)
  h[x+'ratioB']= h[x]['p/pt_projx'].Clone(x+'ratioB')
  h[x+'ratioB'].Rebin(10)
  h[x+'ratioB'].Divide(h['MC']['p/pt_projxB'])
 h['MCtuned0'+'ratioB'].SetMaximum(1.02)
 h['MCtuned0'+'ratioB'].SetMinimum(0.50)
 h['MCtuned0'+'ratioB'].Draw()
 for x in ['MCtuned2','MCtuned0rec']:h[x+'ratioB'].Draw('same')
 for x in ['MCtuned0','MCtuned2','MCtuned0rec']:
   h[x+'ratio'].GetXaxis().SetRangeUser(5,100)
   h[x+'ratio'].Draw('same')
   
def printTrackMeasurements(atrack,PR=1):
  mult = {'_x':0,'_u':0,'_v':0}
  rej  = {'_x':0,'_u':0,'_v':0}
  if PR==1 and sTree.GetBranch("TrackInfos"):
    trInfo = sTree.TrackInfos[atrack]
    for n in range(trInfo.N()):
       detID = trInfo.detId(n)
       hit = ROOT.MufluxSpectrometerHit(detID,0)
       s,v,p,l,view,channelID,tdcId,nRT = stationInfo(hit)
       print "%3i %3i %3i %3i %3s %3i %3i %4.2F %4.2F "%(\
    s,v,p,l,view,channelID,tdcId,trInfo.wL(n),trInfo.wR(n))
       if trInfo.wL(n)<0.1 and trInfo.wR(n) < 0.1: rej[view]+=1
       else:  mult[view]+=1
  else:
   for p in atrack.getPointsWithMeasurement():
    rawM = p.getRawMeasurement()
    info = p.getFitterInfo()
    if not info: continue
    detID = rawM.getDetId()
    hit = ROOT.MufluxSpectrometerHit(detID,0)
    s,v,p,l,view,channelID,tdcId,nRT = stationInfo(hit)
    coords = rawM.getRawHitCoords()
    print "%3i %3i %3i %3i %3s %3i %3i %4.2F %4.2F %5.2F %5.2F %5.2F "%(
    s,v,p,l,view,channelID,tdcId,info.getWeights()[0],info.getWeights()[1],coords[0],coords[1],coords[2])
    if info.getWeights()[0]<0.1 and info.getWeights()[1] < 0.1: rej[view]+=1
    else:  mult[view]+=1
  print "views     used",mult
  print "views rejected",rej
import operator
def debugTrackFit(nEvents,nStart=0,simpleEvents=True,singleTrack=True,PR=1):
 matches={'good':[],'bad':[]}
 ut.bookHist(h,'residuals','all residuals',100,-1.,1.)
 ut.bookHist(h,'extrapX','extrap in X',100,-20.,20.)
 ut.bookHist(h,'extrapY','extrap in Y',100,-20.,20.)
 ut.bookHist(h,'fitfail_good','fitfailure by channel for good events',700,0.5,700.5)
 ut.bookHist(h,'fitfail_bad','fitfailure by channel for bad events',700,0.5,700.5)
#
 fitFailures=[{},{}]
 fitSuccess =[{},{}]
 for n in range(nStart,nStart+nEvents):
  rc = sTree.GetEvent(n)
  if simpleEvents:
   if not findSimpleEvent(sTree): continue
  tracks = findTracks(PR)
  if singleTrack and len(tracks)!=1: continue
# select RPC tracks with good Y info
  clusters, RPCtracks = muonTaggerClustering()
  if len(RPCtracks['X'])>1 or len(RPCtracks['Y'])>1: print n,len(RPCtracks['X']),len(RPCtracks['Y'])
  if len(RPCtracks['X'])!=1 or len(RPCtracks['Y'])!=1: continue
  X = RPCtracks['X'][0][0]*zRPC1+RPCtracks['X'][0][1]
  Y = RPCtracks['Y'][0][0]*zRPC1+RPCtracks['Y'][0][1]
  track_index = -1
  for atrack in tracks:
   track_index +=1
   st = atrack.getFitStatus()
   if not st.isFitConverged(): continue
   rc,pos,mom = extrapolateToPlane(atrack,zRPC1)
   if not rc: continue 
   if abs(pos[0]-X)>5. : continue # not worth checking Y
   delta = pos[1]-Y
   if Debug: print "event# %i difference in X,Y %5.3F %5.3F "%(n,pos[0]-X,delta)
   rc = h['extrapX'].Fill(pos[0]-X)
   rc = h['extrapY'].Fill(delta)
   if abs(delta)<10. :     matches['good'].append(n)  # within ~3sigma
   else :                  
      matches['bad'].append(n)
      print "event# %i difference in X,Y %5.3F %5.3F "%(n,pos[0]-X,delta)
   Nmeas = atrack.getNumPointsWithMeasurement()
   if Nmeas>2: Npoints = Nmeas
   else:
     tr = sTree.TrackInfos[track_index]
     Npoints = tr.N()
   for kp in range(Npoints):
     wL,wR = -999,-999
     if Nmeas>2:
      p = atrack.getPointsWithMeasurement()[kp]
      rawM  = p.getRawMeasurement()
      detID = rawM.getDetId()
      info  = p.getFitterInfo()
      if info: 
         wL = info.getWeights()[0]
         wR = info.getWeights()[1]
     else:
      detID = tr.detId(kp)
      wL = tr.wL(kp)
      wR = tr.wR(kp)
     if abs(delta)<10.:      k=0
     elif abs(pos[1]-Y)>50.: k=1
     else: continue
     if wL<0.1 and wR < 0.1:
# record failure rate
      if not detID in fitFailures[k]: fitFailures[k][detID]=0
      fitFailures[k][detID]+=1
     else:
      if not detID in fitSuccess[k]: fitSuccess[k][detID]=0
      fitSuccess[k][detID]+=1
# upstream 12 channel, downstream 48
# 4 4 4 4    4 4 = 576
 for k in range(2):
  for detID in fitFailures[k]:
   test = ROOT.MufluxSpectrometerHit(detID,0)
   s,v,p,l,view,channelID,tdcId,nRT = stationInfo(test)
   vbot,vtop = strawPositionsBotTop[detID]
   x = channelID
   if s > 2: x+= (s-2)*200 + 48*(2*l+p)
   else: 
     if view == '_u':   x+=50
     elif view == '_v': x+=100
     elif s==2: x+=150
     x+=12*(2*l+p)
   r = 1
   if fitSuccess[k].has_key(detID): r=fitFailures[k][detID]/float(fitSuccess[k][detID]+fitFailures[k][detID])
   if k==0:     rc=h['fitfail_good'].SetBinContent(x,r)
   else:        rc=h['fitfail_bad'].SetBinContent(x,r)
# only look at the pathological cases
 print "Summary: good matches: %i   bad matches: %i    failure rate %5.2F"%(
  len(matches['good']),len(matches['bad']),len(matches['bad'])/float(len(matches['bad'])+len(matches['good']) ) )
 ROOT.gROOT.FindObject('c1').cd()
 h['extrapY'].Draw()
 return matches

def plotLinearResiduals():
 if not h.has_key('linearResiduals2dX'): 
   plotRPCExtrap(0,-1)
   ut.bookCanvas(h,key='linearResiduals2dX',title='linear track model, residuals function of X',nx=1600,ny=1200,cx=4,cy=4)
   ut.bookCanvas(h,key='linearResidualsX',title='linear track model, residuals',nx=1600,ny=1200,cx=4,cy=4)
 for s in range(1,5):
   for view in ['_x']:
    for l in range(0,4):
       hname = 'linearRes'+str(s)+view+str(l)
       h[hname].Reset()
 for Nr in range(sTree.GetEntries()):
   sTree.GetEvent(Nr)
   if Nr%10000==0:   print "now at event",Nr,' of ',sTree.GetEntries(),sTree.GetCurrentFile().GetName()
   if not findSimpleEvent(sTree): continue
   trackCandidates = findTracks(PR = 1,linearTrackModel = True)
 j=1
 for s in range(1,5):
   for view in ['_x']:
    for l in range(0,4):
     hname = 'linearRes'+str(s)+view+str(l)
     rc = h['linearResiduals2dX'].cd(j)  
     h[hname].Draw('box')
     rc = h['linearResidualsX'].cd(j)  
     proj = h[hname].ProjectionX(hname+'_projx')
     proj.Draw()
     print "%s: %7.3F"%(hname, proj.GetMean())
     j+=1
 j=1
 for s in range(1,5):
  h['RPCResiduals'].cd(j*2-1)
  h['RPCResX_'+str(s)+'1'].Draw('colz')
  h['RPCResiduals'].cd(j*2)
  h['RPCResX_'+str(s)+'1'].ProjectionX().Draw()
  j+=1

h['270'] = {'1GeV':{},'10GeV':{},'1GeVCharm':{}}
h['500'] = {'1GeV':{},'10GeV':{},'1GeVCharm':{}}
def mergeHistosForMomResol():
 # 1GeV mbias,      1.8 Billion PoT 
 # 1GeV charm,     10.2 Billion PoT,  10 files
 # 10GeV MC,         65 Billion PoT 
 MCStats   = 1.8E9
 sim10fact = 1.8/(65.*(1.-0.016)) # normalize 10GeV to 1GeV stats, 1.6% of 10GeV stats not processed.
 charmNorm  = {1:0.176,10:0.424}
 beautyNorm = {1:0.,   10:0.01218}
 sources = {"":1.,"Hadronic inelastic":100.,"Lepton pair":100.,"Positron annihilation":100.,"charm":1./charmNorm[10],"beauty":1./beautyNorm[10]}
 if len(hMC)==0:
  interestingHistos = []
  for a in ['trueMom','recoMom','momResol','curvResol','Fitpoints_u1','Fitpoints_v2','Fitpoints_x1','Fitpoints_x2','Fitpoints_x3','Fitpoints_x4']:
    for source in sources:  interestingHistos.append(a+source)
  ut.readHists(h['270']['1GeV'],       'momDistributions-1GeV-mbias-0.root',interestingHistos)
  ut.readHists(h['270']['1GeVCharm'],  'momDistributions-1GeV-charm-0.root',interestingHistos)
  ut.readHists(h['270']['10GeV'],      'momDistributions-10GeV-mbias-0.root',interestingHistos)
  ut.readHists(h['500']['1GeV'],       'momDistributions-1GeV-mbias.root',interestingHistos)
  ut.readHists(h['500']['1GeVCharm'],  'momDistributions-1GeV-charm.root',interestingHistos)
  ut.readHists(h['500']['10GeV'],      'momDistributions-10GeV.root',interestingHistos)
  for res in ['270','500']:
   for a in ['trueMom','recoMom','Fitpoints_u1','Fitpoints_v2','Fitpoints_x1','Fitpoints_x2','Fitpoints_x3','Fitpoints_x4']:
    h['MC'+res+a] = h[res]['1GeV'][a].Clone('MC'+res+a)
    h['MC'+res+a].Add(h[res]['1GeVCharm'][a],charmNorm[1])
    h['MC10'+res+a] = h[res]['10GeV'][a].Clone('MC10'+res+a)
# special treatment for 10GeV to get weights right
    h['MC10'+res+a].Add(h[res]['10GeV'][a+"charm"],-1.+charmNorm[10])
    h['MC10'+res+a].Add(h[res]['10GeV'][a+"beauty"],-1.+beautyNorm[10])
    h['MC10'+res+a].Scale(sim10fact)
  # 2d histos, only for resolution plot, don't care about mom distribution'
   h["momResol"+res] = h[res]['1GeV']["momResol"].Clone()
   h["momResol"+res].Add(h[res]['1GeVCharm']["momResol"])
   h["momResol"+res].Add(h[res]['10GeV']["momResol"])
  # use 1 GeV below 20GeV and 10 GeV above
   for a in ['trueMom','recoMom']:
    h[res+a]=h["MC10"+res+a].Clone()
    for n in range(h[a].GetNbinsX()):
      if h[res+a].GetBinCenter(n)<20. : 
       h[res+a].SetBinContent(n,h["MC"+res+a].GetBinContent(n))
   h[res+'trueMom'].SetLineColor(ROOT.kGreen)
   ut.makeIntegralDistrib(h,res+'trueMom')
   ut.makeIntegralDistrib(h,res+'recoMom')
   h['I-'+res+'trueMom'].SetTitle(' ;P [GeV/c]; #SigmaN with P>x')
   h['I-'+res+'trueMom'].SetMinimum(0.5)
   h['I-'+res+'trueMom'].SetStats(0)
   h['I-'+res+'trueMom'].GetXaxis().SetRangeUser(5.,500.)
# true mom, reco mom
 t = "true Mom"
 if not h.has_key(t): ut.bookCanvas(h,t,'true and reco momentum',900,600,1,1)
 tc=h[t].cd(1)
 tc.SetLogy()
 h['I-270trueMom'].Draw()
 h['I-270recoMom'].Draw('same')
 h['I-500recoMom'].SetLineColor(ROOT.kMagenta)
 h['I-500recoMom'].Draw('same')
 h['leg'+t]=ROOT.TLegend(0.31,0.67,0.85,0.85)
 h['leg'+t].AddEntry(h['I-270trueMom'],'true momentum ','PL')
 h['leg'+t].AddEntry(h['I-270recoMom'],'reconstructed momentum 270#mum','PL')
 h['leg'+t].AddEntry(h['I-500recoMom'],'reconstructed momentum 500#mum','PL')
 h['leg'+t].Draw()
 h[t].Print('True-Reco.png')
 h[t].Print('True-Reco.pdf')
#
 fSqrt = ROOT.TF1('momResol','sqrt([0]**2+x**2*[1]**2)',2)
 fSqrt.SetParName(0,'constant')
 fSqrt.SetParName(1,'linear')
 t = 'momResolution'
 if not h.has_key(t): ut.bookCanvas(h,t,'momentum Resolution',900,600,1,1)
 tc=h[t].cd(1)
 for res in ['270','500']:
  hname = 'momResol'+res
  h[hname+'P'] = h[hname].ProjectionY(hname+'P')
  h[hname+'P'].Reset()
  h[hname+'Perr']=h[hname+'P'].Clone(hname+'Perr')
  for n in range(1,h[hname+'P'].GetNbinsX()+1):
    h[hname+str(n)] = h[hname].ProjectionX(hname+str(n),n,n)
    if h[hname+str(n)].GetEntries()<50: continue
    if n>10: h[hname+str(n)].Rebin(5)
    fitFunction = h[hname+str(n)].GetFunction('gauss')
    if not fitFunction: fitFunction = myGauss 
    fitFunction.SetParameter(0,h[hname+str(n)].GetMaximum()*0.02)
    fitFunction.SetParameter(1,0.)
    fitFunction.SetParameter(2,0.01)
    fitFunction.FixParameter(3,0.)
    fitResult = h[hname+str(n)].Fit(fitFunction,'S','',-1.,1.)
    rc = fitResult.Get()
    if not rc: continue
    mean = rc.GetParams()[1]
    rms  = rc.GetParams()[2]
    print n,mean,rms
    h[hname+'Perr'].SetBinContent(n,mean)
    h[hname+'Perr'].SetBinError(n,abs(rms))
    h[hname+'P'].SetBinContent(n,abs(rms))
  h[hname+'P'].Fit('pol1','QW','',0.,300.)
  fitFun = h[hname+'P'].GetFunction('pol1')
  fSqrt.SetParameter(0,fitFun.GetParameter(0))
  fSqrt.SetParameter(1,fitFun.GetParameter(1))
  h[hname+'P'].Fit(fSqrt,'W','',0.,300.)
 for res in ['270','500']:
  hname = 'momResol'+res
  h[hname+'P'].SetTitle('momentum resolution function of momentum;P [GeV/c];#sigma P/P')
  h[hname+'P'].SetStats(0)
  h[hname+'P'].SetMaximum(0.15)
  fSqrt = h[hname+'P'].GetFunction('momResol')
  p0 = "%4.3F"%(100*fSqrt.GetParameter(0))
  p1 = "%4.3F"%(100*fSqrt.GetParameter(1))
  if res == '500': 
      h['text'+res] = ROOT.TLatex(50.,0.09,'#sigmaP/P = ('+p0+'+'+p1+')%')
      h[hname+'P'].Draw('same')
      h[hname+'P'].SetLineColor(ROOT.kMagenta)
      h['text'+res].SetTextColor(ROOT.kMagenta)
  else:
      h['text'+res] = ROOT.TLatex(160.,0.02,'#sigmaP/P = ('+p0+'+'+p1+')%')
      h['text'+res].SetTextColor(ROOT.kBlue)
      h[hname+'P'].Draw()
  h['text'+res].Draw('same')
 h['leg'+t]=ROOT.TLegend(0.14,0.75,0.64,0.87)
 h['leg'+t].AddEntry(h['momResol270'],'default  270#mum ','PL')
 h['leg'+t].AddEntry(h['momResol500'],'adjusted 500#mum','PL')
 h['leg'+t].Draw()
 h[t].Print('momentumResolution.png')
 h[t].Print('momentumResolution.pdf')
 
def hitResolution():
 ut.bookHist(h,'hitResol','hit resolution',100,-0.5,0.5)
 for n in range(sTree.GetEntries()):
  rc = sTree.GetEvent(n)
  for k in range(sTree.Digi_MufluxSpectrometerHits.GetEntries()):
    hit = sTree.Digi_MufluxSpectrometerHits[k]
    trueHit = sTree.MufluxSpectrometerPoint[k]
    hit.MufluxSpectrometerEndPoints(vbot,vtop)
    TDC = hit.GetDigi() - (vtop[0]-trueHit.GetX())/(ROOT.TMath.C() *100./1000000000.0)
    distance = RT('x',TDC)
    h['hitResol'].Fill(distance - trueHit.dist2Wire())

def matchedRPCHits(aTrack,maxDistance=10.):
  matchedHits={1:{0:[],1:[]},2:{0:[],1:[]},3:{0:[],1:[]},4:{0:[],1:[]},5:{0:[],1:[]}}
  rc,pos,mom = extrapolateToPlane(aTrack,zRPC1)
  Nmatched = 0
  inAcc    = False
  if rc: 
    if pos[0]>cuts['xLRPC1'] and pos[0]<cuts['xRRPC1'] and pos[1]>cuts['yBRPC1'] and pos[1]<cuts['yTRPC1']:
       inAcc = True
    for hit in sTree.Digi_MuonTaggerHits:
       channelID = hit.GetDetectorID()
       s  = channelID/10000
       v  = (channelID-10000*s)/1000
       vtop,vbot = RPCPositionsBotTop[channelID]
       z = (vtop[2]+vbot[2])/2.
       rc,pos,mom = extrapolateToPlane(aTrack,z)
       if not rc:
         error =  "RPCextrap: plotRPCExtrap failed"
         ut.reportError(error)
         if Debug: print error
         continue
       if v==0:
         Y = (vtop[1]+vbot[1])/2.
         res = pos[1] - Y
       else:
         X = (vtop[0]+vbot[0])/2.
         res = pos[0] - X
       if abs(res)<maxDistance:
         matchedHits[s][v].append(hit)
    for s in matchedHits:
      for v in matchedHits[s]:
        Nmatched+= len(matchedHits[s][v])
    return inAcc,Nmatched

def plotRPCExtrap(nEvent=-1,nTot=1000,PR=1,onlyPlotting=False):
 if not onlyPlotting:
  eventRange = [0,sTree.GetEntries()]
  if not nEvent<0: eventRange = [nEvent,nEvent+nTot]
  for s in range(1,6):
   for v in range(2):
    if v==1: dx=20
    if v==0: dx=20
    ut.bookHist(h,'RPCResX_'+str(s)+str(v),'RPC residual for '+str(s)+' '+ str(v),100,-dx,dx,20,-140.,140.)
    ut.bookHist(h,'RPCResY_'+str(s)+str(v),'RPC residual for '+str(s)+' '+ str(v),100,-dx,dx,20,-140.,140.)
    ut.bookHist(h,'RPCextTrack_'+str(s)+str(v),'mom of tracks extr to RPC k with RPC k+1 matched',100,0.,100.)
    ut.bookHist(h,'RPCfired_'+str(s)+str(v),'mom of tracks extr to RPC k and matched with RPC k+1 matched',100,0.,100.)
   ut.bookHist(h,'RPCfired_or_'+str(s),'mom of tracks extr to RPC k and matched with RPC k+1 or of 0 and 1',100,0.,100.)
  ut.bookHist(h,'RPCResX1_p','RPC residual for station 1 function of track momentum',100,-dx,dx,100,0.,100.)
  ut.bookHist(h,'RPCMatchedHits','matched RPC hits as function of track momentum',10,0.5,10.5,20,-0.5,19.5,100,0.,100.)
  ut.bookHist(h,'RPCMeanMatchedHits','mean matched RPC hits as function of track momentum',100,0.,100.)
  ut.bookHist(h,'RPC>1','fraction of tracks with > 1 RPC hits',100,0.,100.)
  ut.bookHist(h,'RPC<2XY','position of tracks with < 2 RPC hits and p>30GeV',50,-100.,100.,50,-100.,100.)
  ut.bookHist(h,'RPC_p', 'momentum of tracks pointing to RPC',100,0.,100.)
  for k in range(2,20):
   ut.bookHist(h, 'RPC<'+str(k)+'_p', '  < '+str(k)+' RPC hits p',100,0.,100.)
  if PR==1:  
       muflux_Reco.RPCextrap()
       return
  for Nr in range(eventRange[0],eventRange[1]):
   getEvent(Nr)
   if Nr%10000==0:   print "now at event",Nr,' of ',sTree.GetEntries(),sTree.GetCurrentFile().GetName(),time.ctime()
   if not sTree.Digi_MuonTaggerHits.GetEntries()>0: continue
   if not findSimpleEvent(sTree): continue
   trackCandidates = findTracks(PR)
   for aTrack in trackCandidates:
       matchedHits={1:{0:[],1:[]},2:{0:[],1:[]},3:{0:[],1:[]},4:{0:[],1:[]},5:{0:[],1:[]}}
       st = aTrack.getFitStatus()
       if not st.isFitConverged(): continue
       if not aTrack.getNumPointsWithMeasurement()>0: continue
       sta = aTrack.getFittedState(0)
       if sta.getMomMag() < 1.: continue
       nHit = -1
       rc,pos1,mom = extrapolateToPlane(aTrack,cuts['zRPC1'])
       if not rc: continue
       inAcc=False
       if pos1[0]>cuts['xLRPC1'] and pos1[0]<cuts['xRRPC1'] and pos1[1]>cuts['yBRPC1'] and pos1[1]<cuts['yTRPC1']: 
         inAcc=True
       for hit in sTree.Digi_MuonTaggerHits:
        nHit+=1
        channelID = hit.GetDetectorID()
        s  = channelID/10000
        v  = (channelID-10000*s)/1000
        vtop,vbot = RPCPositionsBotTop[channelID]
        z = (vtop[2]+vbot[2])/2.
        rc,pos,mom = extrapolateToPlane(aTrack,z)
        if not rc:
         error =  "RPCextrap: plotRPCExtrap failed"
         ut.reportError(error)
         if Debug: print error
         continue
        # closest distance from point to line
        # res = vbot[0]*pos[1] - vtop[0]*pos[1] - vbot[1]*pos[0]+ vtop[0]*vbot[1] + pos[0]*vtop[1]-vbot[0]*vtop[1]
        # res = -res/ROOT.TMath.Sqrt( (vtop[0]-vbot[0])**2+(vtop[1]-vbot[1])**2)
        if v==0:
         Y = (vtop[1]+vbot[1])/2.
         res = pos[1] - Y
         h['RPCResY_'+str(s)+str(v)].Fill(res,Y)
        else:
         X = (vtop[0]+vbot[0])/2.
         res = pos[0] - X
         h['RPCResX_'+str(s)+str(v)].Fill(res,X)
         if s==1: h['RPCResX1_p'].Fill(res,sta.getMomMag())
        if abs(res)<cuts["RPCmaxDistance"]:
           matchedHits[s][v].append(nHit)
       # record number of hits per station and view and track momentum
       # but only for tracks in acceptance
       if inAcc:
        Nmatched = 0
        p = min(99.9,sta.getMomMag())
# try the following:
#  require matched hit in station k+1
#  record how often hit matched in station k
        for k in range(1,5):
         for v in range(0,2):
           if len(matchedHits[k+1][v])==0: continue
           rc = h['RPCextTrack_'+str(k)+str(v)].Fill(p)
           if len(matchedHits[k][v])>0: rc = h['RPCfired_'+str(k)+str(v)].Fill(p)
           if v==0:
              if len(matchedHits[k][v])>0 or len(matchedHits[k][v+1])>0: rc = h['RPCfired_or_'+str(k)].Fill(p)
        for s in matchedHits:
         for v in matchedHits[s]:
          rc = h['RPCMatchedHits'].Fill(2*s-1+v,len(matchedHits[s][v]),p)
          Nmatched+=len(matchedHits[s][v])
        if Nmatched <2 and p>30: rc = h['RPC<2XY'].Fill(pos1[0],pos1[1])
        rc = h['RPC_p'].Fill(p)
        for k in range(2,20):
         if Nmatched<k: rc = h['RPC<'+str(k)+'_p'].Fill(p)
 if not h.has_key('RPCResiduals'): 
      ut.bookCanvas(h,key='RPCResiduals',title='RPCResiduals',nx=1600,ny=1200,cx=2,cy=5)
      ut.bookCanvas(h,key='RPCResidualsXY',title='RPCResiduals function of Y/X',nx=1600,ny=1200,cx=2,cy=5)
      ut.bookCanvas(h,key='RPCResidualsP',title='RPCResiduals function of muon momentum',nx=900,ny=900,cx=1,cy=1)
 j=1
 for s in range(1,6):
   for v in range(0,2):  # 1 = x layer vertical strip, 0 = y layer horizontal strips
     if v==1:     
       hname = 'RPCResX_'+str(s)+str(v)
       p='X'
       jk = 2*j
     elif v==0:   
       hname = 'RPCResY_'+str(s)+str(v)
       p='Y'
       jk = 2*j-1
     hnameProjX = 'RPCRes_'+str(s)+str(v)
     if h[hname].GetEntries()==0: continue
     h[hnameProjX] = h[hname].ProjectionX()
     myGauss.SetParameter(0,h[hnameProjX].GetMaximum())
     myGauss.SetParameter(1,0.)
     myGauss.SetParameter(2,10.)
     myGauss.SetParameter(3,1.)
     rc = h['RPCResiduals'].cd(jk)
     if v==0: fitResult = h[hnameProjX].Fit(myGauss,'SQ','',-40.,40.)
     else:    fitResult = h[hnameProjX].Fit(myGauss,'SQ','',-10.,10.)
     rc = fitResult.Get()
     if not rc: continue
     mean = rc.GetParams()[1]
     rms  = rc.GetParams()[2]
     print "%i, %i, mean=%5.2F RMS=%5.2F"%(s,v,mean,rms)
     # make plot of mean as function of X,Y
     rc = h['RPCResidualsXY'].cd(jk)   
     hname = 'RPCRes'+p+'_'+str(s)+str(v)
     hmean = hname+'_mean'+p
     h[hmean] = h[hname].ProjectionY(hname+'_mean')
     h[hmean].Reset()
     for k in range(1,h[hname].GetNbinsY()+1):
       sli = hname+'_'+str(k) 
       h[sli] = h[hname].ProjectionX(sli,k,k)
       if h[sli].GetEntries()<10: continue
       myGauss.SetParameter(0,h[sli].GetMaximum())
       myGauss.SetParameter(1,0.)
       myGauss.SetParameter(2,4.)
       myGauss.SetParameter(3,1.)
       if v==0: fitResult = h[sli].Fit(myGauss,'SQ','',-40.,40.)
       else:   fitResult = h[sli].Fit(myGauss,'SQ','',-10.,10.)
       rc = fitResult.Get()
       if not rc: continue
       params = rc.GetParams()
       if not params: continue
       mean = rc.GetParams()[1]
       rms  = rc.GetParams()[2]
       rc = h[hmean].Fill( h[hmean].GetBinCenter(k), mean)
     h[hmean].Draw()
   j+=1
 if not h.has_key('RPCResiduals2dXY'): 
      ut.bookCanvas(h,key='RPCResiduals2dXY',title='muon tagger Residuals function of X/Y',nx=1600,ny=1200,cx=2,cy=5)
 j=1
 for s in range(1,6):
   for v in range(0,2):  # 1 = x layer vertical strip, 0 = y layer horizontal strips
     if v==0: 
       p = 'Y'
       jk = j*2-1
     if v==1: 
       p = 'X'
       jk = j*2 
     rc = h['RPCResiduals2dXY'].cd(jk)  
     hname = 'RPCRes'+p+'_'+str(s)+str(v)
     h[hname].Draw('box')
   j+=1
 h['RPCResidualsP'].cd(1)
 h['RPCResX1_p'].Draw('colz')
#         rc = h['RPCMatchedHits'].Fill(2*s-1+v,len(matchedHits[s][v]),mom.Mag())
 zax = h['RPCMatchedHits'].GetZaxis() # 100  momentum
 xax = h['RPCMatchedHits'].GetXaxis() # 10  bins  station and view
 yax = h['RPCMatchedHits'].GetYaxis() # 20  multiplicity
 for ip in range(1,zax.GetNbins()+1):
    Nmean = 0
    Nentries = 0
    Ntracks1 = 0
    for ks in range(1,xax.GetNbins()+1):
      Ntracks1=h['RPCMatchedHits'].GetBinContent(ks,1,ip)+h['RPCMatchedHits'].GetBinContent(ks,2,ip)
      for n in range(1,yax.GetNbins()+1):
         Nmean += h['RPCMatchedHits'].GetBinContent(ks,n,ip)*xax.GetBinCenter(n)
         Nentries+=h['RPCMatchedHits'].GetBinContent(ks,n,ip)
    Nmean = Nmean / float(Nentries+1E-10)
    rc = h['RPCMeanMatchedHits'].SetBinContent(ip,Nmean)
    fraction = (Nentries-Ntracks1)/(Nentries+1E-10)
    rc = h['RPC>1'].SetBinContent(ip,fraction)
    for k in range(2,20):
      h['RPCeff_'+str(k)]=h['RPC<'+str(k)+'_p'].Clone('RPCeff_'+str(k))
      h['RPCeff_'+str(k)].Divide(h['RPC_p'])
 ut.bookCanvas(h,key='RPCEff',title='RPC efficiencies',nx=1600,ny=1200,cx=3,cy=4)
 const = ROOT.TF1('const','pol0',10,100)
 l=1
 for s in range(1,5):
  for v in range(3):
   if v==2: 
     hname = 'RPCfired_or_'+str(s)
     h['Eff'+hname]=ROOT.TEfficiency(h[hname],h['RPCextTrack_'+str(s)+str(0)])
   else: 
     hname = 'RPCfired_'+str(s)+str(v)
     h['Eff'+hname]=ROOT.TEfficiency(h[hname],h['RPCextTrack_'+str(s)+str(v)])
   pad = h['RPCEff'].cd(l)
   l+=1
   rc = h['Eff'+hname].Fit(const)
   h['Eff'+hname].Draw('AP')
   pad.Update()
   graph = h['Eff'+hname].GetPaintedGraph()
   graph.SetMinimum(0.9)
   graph.SetMaximum(1.01)
   pad.Update()
   fun = h['Eff'+hname].GetListOfFunctions()[0]
   eff = fun.GetParameter(0)
   err = fun.GetParError(0)
   h['txtEff'+hname] = ROOT.TMathText(25,0.92,'eff = (%5.2F\pm%5.2F)%s'%(eff*100,err*100,'\\hbox{%}'))
   h['txtEff'+hname].SetTextSize(0.1)
   h['txtEff'+hname].Draw()
 print "do not forget there were runs without one RPC station"
 
def debugRPCstrips():
  ut.bookHist(h,'RPCstrips','RPC strips',1000,-100.,100.,1000,-100.,100.)
  h['RPCstrips'].Draw()
  s=1
  for v in range(2):
   for c in range(1,185):
    if v==0 and c>105: continue
    if v==1 and c<12: continue
    if c%5==0:
     h['RPCstrip'+str(v)+str(c)]=ROOT.TGraph()
     detID = s*10000+v*1000+c
     hit = ROOT.MuonTaggerHit(detID,0)
     hit.EndPoints(vtop,vbot)
     h['RPCstrip'+str(v)+str(c)].SetPoint(0,vtop[0],vtop[1])
     h['RPCstrip'+str(v)+str(c)].SetPoint(1,vbot[0],vbot[1])
     if v == 0: h['RPCstrip'+str(v)+str(c)].SetLineColor(ROOT.kRed)
     if v == 1: h['RPCstrip'+str(v)+str(c)].SetLineColor(ROOT.kBlue)
     h['RPCstrip'+str(v)+str(c)].Draw('same')
def debugRPCYCoordinate():
 ut.bookHist(h,'y1y2','y1 vs y2 of RPC',100,-100.,100.,100,-100.,100.)
 for n in range(10000):
  rc = sTree.GetEvent(n)
  if not findSimpleEvent(sTree): continue
  for hit in sTree.Digi_MuonTaggerHits:
    channelID = hit.GetDetectorID()
    s  = channelID/10000
    v  = (channelID-10000*s)/1000
    if v==0 and s==1:
      hit.EndPoints(vtop,vbot)
      y1 = (vtop[1]+vbot[1])/2.
      for hit in sTree.Digi_MuonTaggerHits:
       channelID = hit.GetDetectorID()
       s  = channelID/10000
       v  = (channelID-10000*s)/1000
       if v==0 and s==2:
        hit.EndPoints(vtop,vbot)
        y2 = (vtop[1]+vbot[1])/2.
        rc = h['y1y2'].Fill(y1,y2)

alignCorrection={}
for p in range(32): alignCorrection[p]=[0,0,0]
slopeX = {3:[0,0,0,0],
          2:[0,0,0,0]}
slopeY = {2:[0,0,0,0]}

# x layer
withCorrections=True
if MCdata: withCorrections=False
if withCorrections:
 alignCorrection[0]=[ 0, 0, 0]   # by hand
 alignCorrection[1]=[ 0, 0, 0]
 alignCorrection[2]=[ 0, 0, 0]
 alignCorrection[3]=[ 0, 0, 0]
# u layers
 alignCorrection[4]=[ 0.0, 0, 0]
 alignCorrection[5]=[ 0.0, 0, 0]
 alignCorrection[6]=[ 0.0, 0, 0]
 alignCorrection[7]=[ 0.0, 0, 0]
# v layers
 alignCorrection[8]= [ 0.035, 0, 0]
 alignCorrection[9]= [ 0.007, 0, 0]
 alignCorrection[10]=[ -0.009, 0, 0]
 alignCorrection[11]=[ -0.03, 0, 0]
# x layers
 alignCorrection[12]=[ 0.18, 0, 0]
 alignCorrection[13]=[ 0.16, 0, 0]
 alignCorrection[14]=[ 0.136, 0, 0]
 alignCorrection[15]=[ 0.12, 0, 0]
# T 3
 alignCorrection[16]=[ 0.008, 0, 0] #-
 alignCorrection[17]=[ 0.04, 0, 0] #-
 alignCorrection[18]=[ 0.018, 0, 0] #-
 alignCorrection[19]=[ 0.07, 0, 0] #-
 alignCorrection[20]=[ -0.078, 0, 0] #+
 alignCorrection[21]=[ -0.09, 0, 0] #+
 alignCorrection[22]=[ -0.08, 0, 0] #+
 alignCorrection[23]=[ -0.09, 0, 0] #+
# T 4
 alignCorrection[24]=[ 0, 0, 0]
 alignCorrection[25]=[ 0, 0, 0]
 alignCorrection[26]=[ 0.0, 0, 0]
 alignCorrection[27]=[ 0.0, 0, 0]
 alignCorrection[28]=[ 0.0, 0, 0]
 alignCorrection[29]=[ 0.0, 0, 0]
 alignCorrection[30]=[ 0.0, 0, 0]
 alignCorrection[31]=[ 0.0, 0, 0]

 slopeX = {2:[-0.001,-0.001,-0.001,-0.001],
           3:[-0.0048,-0.0048,-0.0048,-0.0048]} # 7Feb
 slopeY = {2:[0.0065,0.0065,0.0065,0.0065]}

strawPositionsBotTop={}
def strawPosition():
 for detID in alignConstants['strawPositions']:
  b = alignConstants['strawPositions'][detID]['bot']
  t = alignConstants['strawPositions'][detID]['top']
  strawPositionsBotTop[detID]=[ROOT.TVector3(b[0],b[1],b[2]),ROOT.TVector3(t[0],t[1],t[2])]
  muflux_Reco.setDTPositions(detID,t[0],t[1],t[2],b[0],b[1],b[2])

RPCPositionsBotTop = {}
def RPCPosition():
 for s in range(1,6):
  for v in range(2):
   for c in range(1,185):
    if v==0 and c>116: continue
    detID = s*10000+v*1000+c
    hit = ROOT.MuonTaggerHit(detID,0)
    a,b = correctAlignmentRPC(hit,v)
    RPCPositionsBotTop[detID] = [a.Clone(),b.Clone()]
    x = (a[0]+b[0])/2.
    y = (a[1]+b[1])/2.
    z = (a[2]+b[2])/2.
    muflux_Reco.setRPCPositions(detID,x,y,z)

def correctAlignment(hit):
 detID = hit.GetDetectorID()
 vbot,vtop = ROOT.TVector3(), ROOT.TVector3()
 rc = hit.MufluxSpectrometerEndPoints(vbot,vtop)
 if withDefaultAlignment and not withCorrections: return vbot,vtop
 s,v,p,l,view,channelID,tdcId,nRT = stationInfo(hit)
 if withDefaultAlignment and withCorrections:
  x= (2*p+l)
  if s==1 and view=='_u': x+=4
  if s==2 and view=='_v': x+=8
  if s==2 and view=='_x': x+=12
  if s==3 : 
     x+=16
     if vbot[0]>0:x+=4
  if s==4:
     x+=24
     if vbot[0]>0:x+=4
  for i in range(3):
     vbot[i] = vbot[i]+alignCorrection[x][i]
     vtop[i] = vtop[i]+alignCorrection[x][i]
  return vbot,vtop
 if view=='_x':
  vbot[0]=xpos[detID]
  vtop[0]=xpos[detID]
 else:
  # make same mistake as in geometry, top is with y<0 and bot with y>0:
  vtop[0]=xposb[detID]
  vtop[1]=yposb[detID]
  vbot[0]=xpos[detID]
  vbot[1]=ypos[detID]
 vbot[2]=zpos[detID]
 vtop[2]=zpos[detID]
 pl= (2*p+l)
 x = pl
 if s==1 and view=='_u': x = pl+4
 if s==2 and view=='_v': x = pl+8
 if s==2 and view=='_x': x = pl+12
 if s==3 : 
     x=pl+16
     if vbot[0]>0:x+=4
 if s==4:
     x=pl+24
     if vbot[0]>0:x+=4
 if s==3: 
    vbot[0] += slopeX[s][pl]*vbot[0]
    vtop[0] += slopeX[s][pl]*vtop[0]
 if s==2: 
    vbot[0] += (slopeY[s][pl]*vbot[1] + slopeX[s][pl]*vbot[0])
    vtop[0] += (slopeY[s][pl]*vtop[1] + slopeX[s][pl]*vtop[0])
 for i in range(3):
    vbot[i] = vbot[i]+alignCorrection[x][i]
    vtop[i] = vtop[i]+alignCorrection[x][i]
 return vbot,vtop

def loopTracks(r,w):
    os.close(r) 
    w = os.fdopen(w, 'w') 
    chisq=0
    for Nr in listOfTracks:
     rc=sTree.GetEvent(Nr)
     hitlist = listOfTracks[Nr]
     aTrack = fitTrack(hitlist,1.)
     if type(aTrack) != type(1):
      fitStatus = aTrack.getFitStatus()
      chisq+=fitStatus.getChi2()/fitStatus.getNdf()
     else: chisq+=10
    chisq = chisq/len(listOfTracks)
    print "chisq=",chisq
    w.write(str(chisq))
    w.close()
    os._exit(0)

def FCN(npar, gin, f, par, iflag):
#calculate chisquare
   chisq  = 0
   for p in range(16):
     alignCorrection[p]=[par[p],0,0]
   r, w = os.pipe()
   pid  = os.fork() # bypassing memory issues with running genfit
   if pid == 0:
      chisq = loopTracks(r,w)
   else:
    print("In the parent process after forking the child {}".format(pid))
    finished = os.waitpid(0, 0)
    print(finished)
    os.close(w)
    r=os.fdopen(r)
    f[0] = float(r.read())
    print "FCN returns",f[0],len(listOfTracks)
    print "T1x",par[0],par[1],par[2],par[3]
    print "T1u",par[4],par[5],par[6],par[7]
    print "T2v",par[8],par[9],par[10],par[11]
    print "T2x",par[12],par[13],par[14],par[15]
   return
listOfTracks = {}
def makeFit():
# new idea, first loop over N events, store hits of all track candidates
# then make loop over tracks and fit, sum track chi2
 for Nr in range(50000):
   rc = sTree.GetEvent(Nr)
   if not findSimpleEvent(sTree): continue
   track_hits = testPR(onlyHits=True)
   if len(track_hits)!=1: continue
   listOfTracks[Nr]= []
   for nhit in track_hits[0]: listOfTracks[Nr].append(nhit)
 npar = 24
 ierflg  = ROOT.Long(0)
 gMinuit = ROOT.TMinuit(npar) # https://root.cern.ch/download/minuit.pdf
 gMinuit.SetFCN(FCN)
 gMinuit.SetErrorDef(0.5)
 vstart  = array('d',[0]*npar)
 for p in range(16):
    vstart[p] = alignCorrection[p][0]
 p = 0
 for s in ['T1_x','T1_u','T2_v','T2_x','T3_x','T4_x']:
  for l in range(4):
      gMinuit.mnparm(p, s+str(l), vstart[p], 0.5, 0.,0.,ierflg)
      p+=1
 for p in range(4,24):gMinuit.FixParameter(p)
 strat = array('d',[0])
 gMinuit.mnexcm("SET STR",strat,1,ierflg) # 0 faster, 2 more reliable
 gMinuit.mnexcm("SIMPLEX",vstart,npar,ierflg)
 gMinuit.mnexcm("MIGRAD",vstart,npar,ierflg)
 
def debugGeometrie():
 test = ROOT.MufluxSpectrometerHit(10002012,0)
 test.MufluxSpectrometerEndPoints(vbot,vtop)
 print vtop[1],vbot[1]
 test = ROOT.MufluxSpectrometerHit(11002012,0)
 test.MufluxSpectrometerEndPoints(vbot,vtop)
 m = (vtop[1]-vbot[1])/((vtop[0]-vbot[0]))
 b = vtop[1] - m*vtop[0]
 start = -b/m
 print vtop[1],vbot[1]
 statnb,vnb,pnb,lnb,view,channelID,tdcId,nRT = stationInfo(test)
 nav = ROOT.gGeoManager.GetCurrentNavigator()
 prefix = "Station_"+str(statnb)+str(view)+"_plane_"+str(pnb)+"_" 
 plane = prefix+str(statnb)+str(vnb)+str(pnb)+"00000"
 layer = prefix+"layer_"+str(lnb)+"_"+str(statnb)+str(vnb)+str(pnb)+str(lnb)+"0000" 
 wire = "gas_"+str(test.GetDetectorID())
 if statnb<3: wire = "gas_12_"+str(test.GetDetectorID())
 stat = "volDriftTube"+str(statnb)+"_"+str(statnb) 
 path = "/"+stat+"/"+plane+"/"+layer+"/"+wire
 rc = nav.cd(path)
 W = nav.GetCurrentNode()
 S = W.GetVolume().GetShape()
 top = array('d',[0,0,S.GetDZ()])
 bot = array('d',[0,0,-S.GetDZ()]) 
 Gtop = array('d',[0,0,0])
 Gbot = array('d',[0,0,0])
 nav.LocalToMaster(top, Gtop)
 nav.LocalToMaster(bot, Gbot)

 o = [S.GetOrigin()[0],S.GetOrigin()[1],S.GetOrigin()[2]]
 local = array('d',o)
 globOrigin  = array('d',[0,0,0])
 nav.LocalToMaster(local,globOrigin)

#new idea for residuals:
#4 rounds, in each round one layer from all stations is switched off
def residualLoop(nstart=0,nend=50000):
  for l in range(4):
   global exclude_layer
   exclude_layer = l
   plotBiasedResiduals(nstart,nend,2)
   for s in ['1_x','1_u','2_x','2_u','3_x','4_x']:
    name = 'biasResX_'+s+str(2*p+l)
    h['un'+name] = h[name].Clone('un'+name)
    name = 'biasResY_'+s+str(2*p+l)
    h['un'+name] = h[name].Clone('un'+name)
  exclude_layer = None
  if not h.has_key('unbiasedResiduals'): 
      ut.bookCanvas(h,key='unbiasedResiduals',title='unbiasedResiduals',nx=1600,ny=1200,cx=4,cy=6)
      ut.bookCanvas(h,key='unbiasedResidualsX',title='unbiasedResiduals function of X',nx=1600,ny=1200,cx=4,cy=6)
      ut.bookCanvas(h,key='unbiasedResidualsY',title='unbiasedResiduals function of Y',nx=1600,ny=1200,cx=4,cy=6)
  j=1
  for s in range(1,5):
   for view in ['_x','_u','_v']:
    if s>2 and view != '_x': continue
    if s==1 and view == '_v' or s==2 and view == '_u': continue
    for l in range(0,4):
     hname = 'biasResX_'+str(s)+view+str(l)
     hnameProjX = 'biasRes_'+str(s)+view+str(l)
     if h[hname].GetEntries()<10:
       h[hnameProjX].Draw() 
       j+=1
       continue
     h[hnameProjX] = h[hname].ProjectionX()
     tc = h['unbiasedResiduals'].cd(j)
     fitResult = h[hnameProjX].Fit('gaus','SQ','',-0.5,0.5)
     rc = fitResult.Get()
     if not rc:
      # print "simple gaus fit failed"
      myGauss.SetParameter(0,h[hnameProjX].GetEntries())
      myGauss.SetParameter(1,0.)
      myGauss.SetParameter(2,0.1)
      myGauss.SetParameter(3,1.)
     else:
      myGauss.SetParameter(0,rc.GetParams()[0])
      myGauss.SetParameter(1,rc.GetParams()[1])
      myGauss.SetParameter(2,rc.GetParams()[2])
      myGauss.SetParameter(3,0.)
     fitResult = h[hnameProjX].Fit(myGauss,'SQ','',-0.2,0.2)
     fitResult = h[hnameProjX].Fit(myGauss,'SQ','',-0.5,0.5)
     rc = fitResult.Get()
     if not rc:
       print hnameProjX
       h[hnameProjX].Draw()
       j+=1
       continue
     tc.Update()
     stats = h[hnameProjX].FindObject("stats")
     stats.SetX1NDC(0.563258)
     stats.SetY1NDC(0.526687)
     stats.SetX2NDC(0.938728)
     stats.SetY2NDC(0.940086)
     stats.SetOptFit(111)
     stats.SetOptStat(0)
     mean = rc.GetParams()[1]
     rms  = rc.GetParams()[2]
     Emean = rc.GetErrors()[1]
     Erms  = rc.GetErrors()[2]
     print "%i, %s, %i mean=%5.2F+/-%5.2F RMS=%5.2F+/-%5.2F [mm]"%(s,view,l,mean*10,Emean*10,rms*10,Erms*10)
     residuals[j-1]= h[hnameProjX].GetMean()   # fitresult too unstable, mean
     # make plot of mean as function of X,Y
     for p in ['X','Y']:
      hname = 'biasRes'+p+'_'+str(s)+view+str(l)
      hmean = hname+'_mean'+p
      h[hmean] = h[hname].ProjectionY(hname+'_mean')
      h[hmean].Reset()
      rc = h['unbiasedResiduals'+p].cd(j)  
      for k in range(1,h[hname].GetNbinsY()+1):
       sli = hname+'_'+str(k) 
       h[sli] = h[hname].ProjectionX(sli,k,k)
       if h[sli].GetEntries()<10: continue
       myGauss.SetParameter(0,h[sli].GetMaximum())
       myGauss.SetParameter(1,0.)
       myGauss.SetParameter(2,0.1)
       myGauss.SetParameter(3,1.)
       fitResult = h[sli].Fit(myGauss,'SQ','',-5.,5.)
       rc = fitResult.Get()
       mean,rms = 0,0
       if rc:
        mean = rc.GetParams()[1]
        rms  = rc.GetParams()[2]
       rc = h[hmean].Fill( h[hmean].GetBinCenter(k), mean)
      amin,amax,nmin,nmax = ut.findMaximumAndMinimum(h[hmean])
      if amax<3. and amin>-3.:
       h[hmean].SetMaximum(2.)
       h[hmean].SetMinimum(-2.)
      else: 
       h[hmean].SetLineColor(ROOT.kRed)
       h[hmean].SetMaximum(10.)
       h[hmean].SetMinimum(-10.)
      h[hmean].Draw()
     j+=1

def correctAlignmentRPC(hit,v):
 hit.EndPoints(vtop,vbot)
 if not sTree.GetBranch('MuonTaggerPoint'):
  if v==1:
   vbot[0] = -vbot[0] -1.21
   vtop[0] = -vtop[0] -1.21
  else:
   vbot[1] = vbot[1] -1.21
   vtop[1] = vtop[1] -1.21
 return vbot,vtop

def grouper(iterable,grouping):
    prev = None
    group = []
    iterable.sort()
    for item in iterable:
        if not prev or item - prev <= grouping:
            group.append(item)
        else:
            yield group
            group = [item]
        prev = item
    if group:
        yield group
import numpy, warnings
warnings.filterwarnings('error')

def muonTaggerClustering(PR=11):
 hitsPerStation={}
 clustersPerStation={}
 tracks = {}
 if sTree.GetBranch('RPCTrackY') and PR==1:
  for view in ['X','Y']:
   tracks[view] = []
   for aTrack in eval('sTree.RPCTrack'+view):
     tracks[view].append([aTrack.m(),aTrack.b()])
  return clustersPerStation,tracks
 for s in range(1,6):
  for l in range(2):
   hitsPerStation[10*s+l]=[]
   clustersPerStation[10*s+l]=[]
 for m in sTree.Digi_MuonTaggerHits:
   layer = m.GetDetectorID()/1000
   channel = m.GetDetectorID()%1000
   hitsPerStation[layer].append(channel)
 for l in range(2):
  for s in range(1,6):
   L = len(hitsPerStation[10*s+l])
   if L<1: continue
   temp = dict(enumerate(grouper(hitsPerStation[10*s+l],cuts['muTaggerCluster_grouping']), 1))
   clustersPerStation[10*s+l]={}
   for cl in temp:
    if len(temp[cl])>cuts['muTaggerCluster_max']: continue
    clusCentre = 0
    zCentre = 0
    for hit in temp[cl]:
     vbot,vtop = RPCPositionsBotTop[(10*s+l)*1000+hit]
     clusCentre+=vbot[1-l]
     zCentre+=(vbot[2]+vtop[2])/2.
    clusCentre = clusCentre/float(len(temp[cl]))
    zCentre    = zCentre/float(len(temp[cl]))
    clusCentre =  (int(clusCentre*1000) + float(s)/10.)/1000. # encode station number
    clustersPerStation[10*s+l][cl]=[temp[cl],clusCentre,zCentre]
  if l==0: view = 'Y'
  else: view = 'X'
  tracks[view] = []
  test = []
  for s in range(1,6):
   for cl in clustersPerStation[10*s+l]:
    test.append(clustersPerStation[10*s+l][cl][1])
  tmp = dict(enumerate(grouper(test,cuts['muTaggerCluster_sep']), 1))
  trackCand = []
  for x in tmp:
    if len(tmp[x])>2: trackCand.append(tmp[x])
  for n in trackCand:
    zpositions  = []
    for coord in n:
# find z position
     found = False
     for s in range(1,6):
       if found: break
       for cl in clustersPerStation[10*s+l]:
        if clustersPerStation[10*s+l][cl][1]==coord: 
           zpositions.append(clustersPerStation[10*s+l][cl][2])
           found = True
           break
    tmp = list(zpositions)
    test = dict(enumerate(grouper(tmp,10.), 1))
    if len(test)>2:
      coefficients = numpy.polyfit(zpositions,n,1)
      tracks[view].append(coefficients)
 return clustersPerStation,tracks

def testForSameDetID(nEvent=-1,nTot=1000):
  ut.bookHist(h,'multHits','DT hits multiplicity',10,-0.5,9.5)
  ut.bookHist(h,'multHits_deltaT','DT multiple hits delta T',100,0.,2000.)
  ut.bookHist(h,'multHits_deltaTz','DT multiple hits delta T',400,-200.,200.)
  eventRange = [0,sTree.GetEntries()]
  if not nEvent<0: eventRange = [nEvent,nEvent+nTot]
  listOfTDCs = {}
  for Nr in range(eventRange[0],eventRange[1]):
   rc = sTree.GetEvent(Nr)
   listOfDigits={}
   for hit in sTree.Digi_MufluxSpectrometerHits:
     detID = hit.GetDetectorID()
     if detID<0: continue # feature for converted data in February'19
     if not listOfDigits.has_key(detID): 
       listOfDigits[detID]=[0,[]]
       listOfTDCs[detID]={}
     tdcModule = hit.GetTDC()
     if not listOfTDCs[detID].has_key(tdcModule):
       listOfTDCs[detID][tdcModule] = 0
     listOfTDCs[detID][tdcModule] +=1 
     listOfDigits[detID][0]+=1
     listOfDigits[detID][1].append(hit.GetDigi())
   for x in listOfDigits:
    rc=h['multHits'].Fill(listOfDigits[x][0])
    if listOfDigits[x][0]>1:
      print x
      listOfDigits[x][1].sort()
      for t in range(1,len(listOfDigits[x][1])):
       rc=h['multHits_deltaT'].Fill(abs(t-listOfDigits[x][1][0]))
       rc=h['multHits_deltaTz'].Fill(abs(t-listOfDigits[x][1][0]))
  for detID in listOfTDCs:
    test = ROOT.MufluxSpectrometerHit(detID,0.)
    s,v,p,l,view,channelID,tdcId,nRT = stationInfo(test)
    if tdcId not in listOfTDCs[detID].keys(): 
       print "not matching TDC id",detID,tdcId,listOfTDCs[detID]
    if len(listOfTDCs[detID])>1:
        print detID,listOfTDCs[detID]

def clusterSizesPerLayer(nevents):
  ut.bookHist(h,'ToverT','Time over threshold',3000,-1000.,2000.)
  for s in range(1,5):
    for view in views[s]:
     for l in range(4):
       ut.bookHist(h,'multHits_'+str(s)+view+str(l),'DT cluster size',16,-0.5,15.5)
  for Nr in range(nevents):
   rc = sTree.GetEvent(Nr)
   spectrHitsSorted = ROOT.nestedList()
   muflux_Reco.sortHits(sTree.Digi_MufluxSpectrometerHits,spectrHitsSorted,True)
   for s in range(1,5):
    for view in viewsI[s]:
     for l in range(4):
       allHits=[]
       for x in spectrHitsSorted[view][s][l]:
         allHits.append(x.GetDetectorID()%1000)
       clustersPerLayer = dict(enumerate(grouper(allHits,1), 1))
       for Acl in clustersPerLayer:
         rc = h['multHits_'+str(s)+viewC[view]+str(l)].Fill(len(clustersPerLayer[Acl]))
         if len(clustersPerLayer[Acl])>3:
          for aHit in spectrHitsSorted[view][s][l]: 
             #print Nr,s,view,l,aHit.GetDetectorID()%1000,aHit.GetWidth()
             h['ToverT'].Fill(aHit.GetTimeOverThreshold())
  ut.bookCanvas(h,key='clusSizes',title='Cluster sizes per Layer',nx=1600,ny=1200,cx=4,cy=6)
  j=1
  for s in range(1,5):
    for view in views[s]:
     for l in range(4):
      tc=h['clusSizes'].cd(j)
      tc.SetLogy(1)
      hname = 'multHits_'+str(s)+viewC[view]+str(l)
      h[hname+'x']=h[hname].Clone(hname+'x')
      h[hname+'x'].Scale(1./float(h[hname].GetEntries()))
      h[hname+'x'].Draw()
      j+=1

def studyDeltaRays():
 #MC 
 ut.bookHist(h,'station1Occ','station1 Occupancy',50,0.0,50.)
 ut.bookHist(h,'station1OccX','station1 Occupancy deltaRay present',50,0.0,50.)
 ut.bookHist(h,'deltaRay','E vs z',100,-1.0,1.0,100,0.0,10.)
 ut.bookHist(h,'deltaRayN','hits vs z',100,-1.0,1.0,50,0.0,50.)
 ut.bookHist(h,'deltaRayNvsE','hits vs E',100,0.0,10.0,50,0.0,50.)
 for n in range(sTree.GetEntries()):
  rc=sTree.GetEvent(n)
  if not (sTree.RPCTrackX.GetEntries()==1) or not (sTree.RPCTrackY.GetEntries()==1) : continue
  N=0
  spectrHitsSorted = ROOT.nestedList()
  muflux_Reco.sortHits(sTree.Digi_MufluxSpectrometerHits,spectrHitsSorted,True)
  for l in range(4):  N+= len(spectrHitsSorted[0][1][l])
  rc = h['station1Occ'].Fill(N)
  if MCdata:
   found = False
   for m in sTree.MCTrack:
    pName = m.GetProcName().Data()
    if not pName.find('Delta ray')<0:
     if m.GetStartZ()/100. < 0.05 and m.GetStartZ()/100. > -0.3: 
        rc = h['deltaRayNvsE'].Fill(m.GetP(),N)
        if m.GetP()>0.01:  
           rc = h['station1OccX'].Fill(N)
           found = True
     rc = h['deltaRay'].Fill(m.GetStartZ()/100.,m.GetP())
     rc = h['deltaRayN'].Fill(m.GetStartZ()/100.,N)
   # if not found and N>8: sTree.MCTrack.Dump()

def studyScintillator():
 ut.bookHist(h,'sc','sc',1000,-500.,2000.)
 ut.bookHist(h,'sc6','sc',1000,-500.,2000.)
 ut.bookHist(h,'sc7','sc',1000,-500.,2000.)
 ut.bookHist(h,'scmult','sc multiplicity',10,-0.5,9.5)
 for n in range(sTree.GetEntries()):
  rc=sTree.GetEvent(n)
  rc=h['scmult'].Fill(sTree.Digi_ScintillatorHits.GetEntries())
  for sc in sTree.Digi_ScintillatorHits:
    rc=h['sc'].Fill(sc.GetDigi())
    rc=h['sc'+str(sc.GetDetectorID())].Fill(sc.GetDigi())

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

def findV0(nstart=0,nmax=-1,PR=1):
 if nmax<0: nmax = sTree.GetEntries()
 ut.bookHist(h,'doca','distance between two tracks',100,0.,50.)
 ut.bookHist(h,'nRPC','matchedRPCHits',50,0.,50.)
 ut.bookHist(h,'v0mass_wc','V0 mass wrong charge combinations',100,0.2,1.8,100,-120.,120.)
 ut.bookHist(h,'v0mass','V0 mass ',100,0.2,1.8,100,-120.,120.)
 mass = PDG.GetParticle(211).Mass()
 for n in range(nstart,nmax):
  rc = sTree.GetEvent(n)
  tracks = findTracks(PR)
  if len(tracks)<2: continue
  PosDir = {}
  tr = 0
  for aTrack in tracks:
      st = aTrack.getFitStatus()
      if not st.isFitConverged(): continue
      if st.getNdf()<12: continue
      inAcc, nRPC = matchedRPCHits(aTrack)
      rc = h['nRPC'].Fill(nRPC)
      if not inAcc: continue
      if nRPC > 5: continue
      xx  = aTrack.getFittedState()
      PosDir[tr] = [xx.getPos(),xx.getDir(),ROOT.TLorentzVector(),xx.getCharge(),aTrack.getFitStatus().getNdf()]
      mom = xx.getMom()
      E = ROOT.TMath.Sqrt( mass*mass + mom.Mag2() )
      PosDir[tr][2].SetPxPyPzE(mom.x(),mom.y(),mom.z(),E)
      tr+=1
  for tr1 in range(tr-1):
   for tr2 in range(tr1+1,tr):
    xv,yv,zv,doca = myVertex(0,1,PosDir)
    V0Mom = PosDir[0][2]+PosDir[1][2]
    rc = h['doca'].Fill(doca)
    print n,doca,zv,V0Mom.M(),PosDir[0][3],PosDir[1][3],PosDir[0][4],PosDir[1][4]
    if doca > 5: continue
    if PosDir[tr1][3]*PosDir[tr2][3]< 0: rc = h['v0mass'].Fill(V0Mom.M(),zv)
    else: rc = h['v0mass_wc'].Fill(V0Mom.M(),zv)
def getEvent(n):
 global rname
 rc = sTree.GetEvent(n)
 if sTree.GetListOfFiles().GetEntries()>1:
   temp = sTree.GetCurrentFile().GetName()
   curFile = temp[temp.rfind('/')+1:]
   if curFile != rname:
    rname = curFile
    if withTDC:
     h['tMinAndTmax'] = RTrelations[rname]['tMinAndTmax']
     for s in h['tMinAndTmax']: h['rt'+s] = RTrelations[rname]['rt'+s]
    if withDefaultAlignment: importAlignmentConstants()

from rootpyPickler import Pickler
from rootpyPickler import Unpickler
import pickle
from shutil import copyfile

def makeRTrelPersistent(RTrelations):
 for fname in fnames:
   rname = fname[fname.rfind('/')+1:]
   newName = rname.replace('.root','_RT.root')
   if fname.find('eos')<0:
    copyfile(fname,newName)
   else:
    for l in range(10):
     rc = os.system("xrdcp -f $EOSSHIP"+fname+" "+newName)
     if rc == 0: break
     time.sleep(30)
    if rc != 0: 
        print "Problem with copying file",fname,rc
        continue
   ftemp = ROOT.TFile.Open(newName,'update')
   sTree = ftemp.Get("cbmsim")
   if not sTree:
     print "Problem with making RTrel persistent, file",ftemp,ftemp.ls()
     continue
   ftemp.cd('')
   ftemp.mkdir('RT')
   ftemp.cd('RT')
   for s in RTrelations:
     if s.find('rt')<0: continue
     RTrelations[s].Write()
   pkl = Pickler(ftemp)
   pkl.dump(h['tMinAndTmax'],'tMinAndTmax')
   ftemp.cd('')
   ftemp.mkdir('histos')
   ftemp.histos.cd('')
   h['TDCMapsX'].Write()
   h['hitMapsX'].Write()
   h["RTrelations"].Write()
   ftemp.Write("",ROOT.TFile.kOverwrite)
   ftemp.Close()
def makeAlignmentConstantsPersistent():
  ftemp=sTree.GetCurrentFile()
  ftemp.cd('histos')
  momDisplay()
  h['mom'].Write()
  strawPositionsP = {}
  for straw in xpos:
    vbot,vtop = strawPositionsBotTop[straw]
    strawPositionsP[straw]={'top':[vtop[0],vtop[1],vtop[2]],'bot':[vbot[0],vbot[1],vbot[2]]}
  alignConstants={'strawPositions':strawPositionsP,'alignCorrection':alignCorrection}
  pkl = Pickler(ftemp)
  pkl.dump(alignConstants,'alignConstants')

def importAlignmentConstants():
   global alignConstants
   alignConstants = {}
   RPCPosition()
   if not sTree.GetCurrentFile().Get('alignConstants') or withCorrections:
    for straw in xpos:
      hit = ROOT.MufluxSpectrometerHit(straw,0.)
      strawPositionsBotTop[hit.GetDetectorID()]=correctAlignment(hit)
    print "importing alignment constants from code"
    return
   upkl    = Unpickler(sTree.GetCurrentFile())
   try:
    alignConstants = upkl.load('alignConstants')
    print "importing alignment constants from file",sTree.GetCurrentFile().GetName()
    strawPosition()
   except:
    print "loading of alignment constants failed for file",sTree.GetCurrentFile().GetName()
def importRTrel():
  for fname in fnames:
   if len(fnames)==1: f=sTree.GetCurrentFile()
   else:   f = ROOT.TFile.Open(fname)
   rname = fname[fname.rfind('/')+1:]
   RTrelations[rname] = {}
   upkl    = Unpickler(f)
   RTrelations[rname]={}
   try:
    RTrelations[rname]['tMinAndTmax'] = upkl.load('tMinAndTmax')
    for x in RTrelations[rname]['tMinAndTmax']: RTrelations[rname]['rt'+x]=f.RT.Get('rt'+x)
    h['tMinAndTmax'] = RTrelations[rname]['tMinAndTmax']
    for s in h['tMinAndTmax']: h['rt'+s] = RTrelations[rname]['rt'+s]
   except:
    print "loading of RT failed for file",rname
   f.Close()
def analyzeRTrel():
  global fnames
  fnames = []
  for x in os.listdir('.'):
   if x.find('_RT')>0 and x.find('histos')<0: fnames.append(x)
  importRTrel()
  for x in RTrelations[fnames[0]]['tMinAndTmax']:
    ut.bookHist(h,x+'Tmin',x+'Tmin',100,-130.,-30.)
    ut.bookHist(h,x+'Tmax',x+'Tmax',600,1100.,1700.)
  for fname in RTrelations:
   for x in RTrelations[fname]['tMinAndTmax']:
    rc = h[x+'Tmin'].Fill(RTrelations[fname]['tMinAndTmax'][x][0])
    rc = h[x+'Tmax'].Fill(RTrelations[fname]['tMinAndTmax'][x][1])
  ut.bookCanvas(h,'RTMins','RT Min',1200,900,7,5)
  ut.bookCanvas(h,'RTMaxs','RT Max',1200,900,7,5)
  keys = RTrelations[fnames[0]]['tMinAndTmax'].keys()
  keys.sort()
  for n in range(1,35):
   tc = h['RTMins'].cd(n)
   h[keys[n-1]+'Tmin'].Draw()
   tc = h['RTMaxs'].cd(n)
   h[keys[n-1]+'Tmax'].Draw()

# to START
RTrelations = {}
zeroFieldData=['SPILLDATA_8000_0515970150_20180715_220030.root']
def init(database='muflux_RTrelations.pkl',remake=False,withReco=False):
 global withTDC,RTrelations
 if os.path.exists(database): RTrelations = pickle.load(open(database))
 N = sTree.GetEntries()
 if not RTrelations.has_key(rname) or remake:
  withTDC = False
  sTree.SetBranchStatus("FitTracks",0)
  plotBiasedResiduals(PR=11)
  print "start making RT relations"
  makeRTrelations() # should be done after first pass with track reco, requires large number of events > 10000
  RTrelations[rname] =  {'tMinAndTmax':h['tMinAndTmax']}
  for s in h['tMinAndTmax']: RTrelations[rname]['rt'+s] = h['rt'+s]
  fpkl=open(database,'w')
  pickle.dump(RTrelations,fpkl)
  fpkl.close()
 else:
  h['tMinAndTmax'] = RTrelations[rname]['tMinAndTmax']
  for s in h['tMinAndTmax']: h['rt'+s] = RTrelations[rname]['rt'+s]
 withTDC = True
 if withReco:
  plotBiasedResiduals(PR=11)
  plotRPCExtrap(PR=11)
  ut.writeHists(h,'histos-'+rname,plusCanvas=True)
#
def monitorMasterTrigger():
 ut.bookHist(h,'masterTrigger','t of master trigger',1000,200.,400.)
 ut.bookHist(h,'delay','delay time',1000,-2000.,2000.)
 ut.bookHist(h,'tdcCor','corrected TDC time',1000,-2000.,3000.)
 ut.bookHist(h,'tdc', 'TDC time from hit',    1000,-2000.,3000.)
 ut.bookHist(h,'tdc#4','TDC 4', 1000,-2000.,10000.)
 for n in range(sTree.GetEntries()):
  rc=sTree.GetEvent(n)
  for mt in sTree.Digi_MasterTrigger:
   rc = h['masterTrigger'].Fill(mt.GetDigi())
  if sTree.Digi_MasterTrigger.GetEntries()==0: 
    rc = h['masterTrigger'].Fill(201.)
  else:
   tdcDict = {}
   for k in range(sTree.Digi_Triggers.GetEntries()):
    hit = sTree.Digi_Triggers[k]
    if tdcDict.has_key(k): 
      print "Error, double trigger TDC ID",k
      if not hit.GetDigi()<tdcDict[k]: continue
    tdcDict[hit.GetTDC()]=hit.GetDigi()
   if not tdcDict.has_key(4):
     h['masterTrigger'].Fill(210+4)
     continue
   else: rc = h['tdc#4'].Fill(tdcDict[4])
   delay = sTree.Digi_MasterTrigger[0].GetDigi() - tdcDict[4]
   rc = h['delay'].Fill(delay)
   for hit in sTree.Digi_MufluxSpectrometerHits:
    detID=hit.GetDetectorID()
    if detID<0: continue # feature for converted data in February'19
    rc = h['tdc'].Fill(hit.GetDigi())
    if not hit.hasDelay():
     tdcID = hit.GetTDC()
     if not tdcDict.has_key(tdcID):
       h['masterTrigger'].Fill(210+tdcID*10)
       if hit.hasTrigger() : print "this should not happen, no trigger but hasTrigger",n
       continue
     if not hit.hasTrigger() : print "this should not happen, trigger but hasTrigger false",n
     lt = tdcDict[tdcID]
     tdcCor = hit.GetDigi() - delay - lt - 1323.0 # default value used to make the correction during conversion
     rc = h['tdcCor'].Fill(tdcCor)

def disableBranches():
 # if sTree.GetBranchStatus("FitTracks"): sTree.SetBranchStatus("FitTracks",0)
 if sTree.GetBranchStatus("Digi_BeamCounters"): sTree.SetBranchStatus("Digi_BeamCounters",0)
 if sTree.GetBranchStatus("Digi_LateMufluxSpectrometerHits"): sTree.SetBranchStatus("Digi_LateMufluxSpectrometerHits",0)
 if sTree.GetBranchStatus("Digi_MufluxSpectrometerHits"): sTree.SetBranchStatus("Digi_MufluxSpectrometerHits",0)
 if sTree.GetBranchStatus("Digi_Scintillators"): sTree.SetBranchStatus("Digi_Scintillators",0)
 if sTree.GetBranchStatus("Digi_Triggers"): sTree.SetBranchStatus("Digi_Triggers",0)
 if sTree.GetBranchStatus("Digi_MasterTrigger"): sTree.SetBranchStatus("Digi_MasterTrigger",0)
 if sTree.GetBranchStatus("Digi_MuonTaggerHits"): sTree.SetBranchStatus("Digi_MuonTaggerHits",0)
def checkForDiMuon():
  boost = False
  for t in sTree.MCTrack:
   if abs(t.GetPdgCode())!=13: continue
   moID  = abs(sTree.MCTrack[t.GetMotherId()].GetPdgCode())
   if moID in muSourcesIDs: 
     boost = True
     break
   pName = t.GetProcName().Data()
   if not( pName.find('Lepton pair')<0 and pName.find('Positron annihilation')<0  and  pName.find('Hadronic inelastic')<0 ):
     boost = True
     break
  return boost
def muonOrigin():
 muonO= {}
 muonO2 = {}
 doubleProc = [0,0,0]
 N = sTree.GetEntries()
 for n in range(N):
  rc=sTree.GetEvent(n)
  # if sTree.FitTracks.GetEntries()==0: continue
  muP = 0
  processed = []
  for hit in sTree.MufluxSpectrometerPoint: 
   i=hit.GetTrackID()
   if i<0: continue
   if i in processed: continue
   processed.append(i)
   t=sTree.MCTrack[i]
   if abs(t.GetPdgCode())!=13: continue
   moID  = abs(sTree.MCTrack[t.GetMotherId()].GetPdgCode())
   pName = t.GetProcName().Data()
   if muP!=0: 
     if pName!=muP: 
       # print "two muons, two processes",n,muP,pName
       doubleProc[1] +=1
   else:
      muP = pName
   if not muonO.has_key(pName):
     muonO[pName]=0
     muonO2[pName]={}
   if not muonO2[pName].has_key(moID): muonO2[pName][moID]=0
   muonO[pName]+=1
   muonO2[pName][moID]+=1
  if len(processed)>0: doubleProc[0] +=1
 sorted_o = sorted(muonO.items(), key=operator.itemgetter(1))
 for p in sorted_o:
    print "%30s %5.2F %%"%(p[0],p[1]/float(doubleProc[0])*100.)
 for p in ['Primary particle emission', 'Decay']:
   print "for process ",p
   sorted_p = sorted(muonO2[p].items(), key=operator.itemgetter(1))
   for x in sorted_p:
    part = PDG.GetParticle(x[0])
    if not part: particleName = str(x[0])
    else: particleName = PDG.GetParticle(x[0]).GetName()
    print "   %20s %5.2F %%"%(particleName,x[1]/float(doubleProc[0])*100.)
 print "double process ",doubleProc
 return

def splitOffBoostedEvents():
    curFile = sTree.GetCurrentFile().GetName()
    newFile1 = curFile.replace(".root","_dimuon99.root")
    newFile2 = curFile.replace(".root","_dimuon1.root")
    os.system('cp '+curFile+' '+newFile1)
    os.system('cp '+curFile+' '+newFile2)
    # make new files without reco branches
    sTree.SetBranchStatus("FitTracks",0)
    sTree.SetBranchStatus("RPCTrackX",0)
    sTree.SetBranchStatus("RPCTrackY",0)
    sTree.SetBranchStatus("TrackInfos",0)
    newf1 = ROOT.TFile(newFile1,"recreate")
    newTree1 = sTree.CloneTree(0)
    newf2 = ROOT.TFile(newFile2,"recreate")
    newTree2 = sTree.CloneTree(0)
    for n in range(sTree.GetEntries()):
      rc = sTree.GetEntry(n)
      if checkForDiMuon() and rnr.Uniform(0.,1.)<0.99: rc = newTree1.Fill() # dimuon99
      else:                                            rc = newTree2.Fill() # dimuon1
    sTree.Clear()
    newTree1.AutoSave()
    newf1.Close()
    newTree2.AutoSave()
    newf2.Close()
    newf1 = ROOT.TFile(newFile1)
    newf2 = ROOT.TFile(newFile2)
    n12 = newf1.cbmsim.GetEntries() + newf2.cbmsim.GetEntries()
    N = sTree.GetEntries()
    newf1.Close()
    newf2.Close()
    sTree.GetCurrentFile().Close()
    if n12 == N: 
       print "check OK"
       os.system('mv '+newFile2+' '+curFile)
    else: print "unitarity violated",f,n1,n2,sTree.GetEntries()
def plotDTPoints(onlyPlotting=False):
 views = ['_u1','_v2','_x1','_x2','_x3','_x4']
 if not onlyPlotting:
  for view in views:
   ut.bookHist(h,'points'+view,'points'+view,100,0,400,10,-0.5,9.5)
   ut.bookHist(h,'Fitpoints'+view,'points'+view,100,0,400,10,-0.5,9.5)
  for n in range(sTree.GetEntries()):
   rc = sTree.GetEvent(n)
   hitsPerTrack = {}
   mom = {}
   for p in sTree.MufluxSpectrometerPoint:
    t = p.GetTrackID()
    if not hitsPerTrack.has_key(t):
     if abs(p.PdgCode())!=13:continue
     P = ROOT.TVector3(p.GetPx(),p.GetPy(),p.GetPz())
     if P.Mag() < 10: continue
     if abs(p.GetX())>10 or abs(p.GetY())>10 : continue
     hitsPerTrack[t] = {'_u1':0,'_v2':0,'_x1':0,'_x2':0,'_x3':0,'_x4':0}
     mom[t] = P.Mag()
    test = ROOT.MufluxSpectrometerHit(p.GetDetectorID(),0.)
    statnb,vnb,pnb,lnb,view,channelID,tdcId,nRT = stationInfo(test)
    key = view+str(statnb)
    hitsPerTrack[t][key]+=1
   for view in views:
    for t in hitsPerTrack:
     rc = h['points'+view].Fill(mom[t],hitsPerTrack[t][view])
   n = 0
   for aTrack in sTree.FitTracks:
    fst = aTrack.getFitStatus()
    if not fst.isFitConverged(): continue
    fstate =  aTrack.getFittedState(0)
    mom = fstate.getMom()
    mStatistics = countMeasurements(n,PR=1)
    for view in views:
      v = view.replace('_','')
      if v=='u1': v='u'
      if v=='v2': v='v'
      rc = h['Fitpoints'+view].Fill(mom.Mag(),len(mStatistics[v]))
  ut.writeHists(h,'histos-DTPoints-'+rname)
 cases = {'FitPoints':'Fitpoints'}
 if MCdata: cases['MC-DTPoints']='points'
 for t in cases:
  if not h.has_key(t): 
    ut.bookCanvas(h,key=t,title=t,nx=1200,ny=600,cx=3,cy=2)
    ut.bookCanvas(h,key=t+'proj',title=t,nx=1200,ny=600,cx=3,cy=2)
  n = 1
  for view in views:
   mean     = 'mean'+cases[t]+view
   oneHit234 = 'oneHit234'+cases[t]+view
   twoHit34 = 'twoHit34'+cases[t]+view
   h[mean]    = h[cases[t]+view].ProjectionX().Clone(mean)
   h[oneHit234]= h[cases[t]+view].ProjectionX().Clone(oneHit234)
   h[twoHit34]= h[cases[t]+view].ProjectionX().Clone(twoHit34)
   h[cases[t]+view+'proj']= h[cases[t]+view].ProjectionY().Clone(cases[t]+view+'proj')
   h[oneHit234].SetMaximum(-1111)
   h[oneHit234].SetMinimum(-1111)
   h[twoHit34].SetMaximum(-1111)
   h[twoHit34].SetMinimum(-1111)
   for k in range(1,h[mean].GetNbinsX()):
       test = h[cases[t]+view].ProjectionY('test',k,k) 
       h[mean].SetBinContent(k,test.GetMean())
       h[mean].SetBinError(k,0)
       ratio = float(test.GetBinContent(2))/(test.GetBinContent(3)+test.GetBinContent(4)+test.GetBinContent(5)+1E-6)
       h[oneHit234].SetBinContent(k,ratio)
       h[oneHit234].SetBinError(k,0)
       ratio = float(test.GetBinContent(3))/(test.GetBinContent(4)+test.GetBinContent(5)+1E-6)
       h[twoHit34].SetBinContent(k,ratio)
       h[twoHit34].SetBinError(k,0)
   tc = h[t].cd(n)
   h[mean].SetMinimum(2.)
   h[mean].SetMaximum(4.)
   h[mean].Fit('pol1','PL','',50,300)
   h[mean].SetStats(0)
   h[mean].Draw('hist')
   h[mean].GetFunction('pol1').Draw('same')
   tc = h[t+'proj'].cd(n)
   tc.SetLogy()
   h[cases[t]+view+'proj'].GetXaxis().SetRangeUser(-0.5,6.5)
   h[cases[t]+view+'proj'].Draw('hist')
   n+=1
   h[t].Print(t+'meanFunP.pdf')
   h[t].Print(t+'meanFunP.png')
   h[t+'proj'].Print(t+'distribution.png')
   h[t+'proj'].Print(t+'distribution.pdf')
def plotFitPoints():
 t = 'Fitpoints'
 views = ['_u1','_v2','_x1','_x2','_x3','_x4']
 interestingHistos=[]
 for view in views: interestingHistos.append(t+view)
 ut.readHists(hMC,'../DTPoints-mbias.root',interestingHistos)
 ut.readHists(h,'momDistributions.root',interestingHistos)
 if not h.has_key(t): 
   ut.bookCanvas(h,key=t,title=t,nx=1200,ny=600,cx=3,cy=2)
   ut.bookCanvas(h,key=t+'proj',title=t,nx=1200,ny=600,cx=3,cy=2)
 histos = {'data':h,'MC':hMC}
 for data in ['data','MC']:
  hx = histos[data]
  for view in views:
   mean      = data+'mean'+t+view
   oneHit234 = data+'oneHit234'+t+view
   twoHit34  = data+'twoHit34'+t+view
   h[mean]     = hx[t+view].ProjectionX().Clone(mean)
   h[oneHit234]= hx[t+view].ProjectionX().Clone(oneHit234)
   h[twoHit34] = hx[t+view].ProjectionX().Clone(twoHit34)
   h[data+t+view+'proj']= hx[t+view].ProjectionY().Clone(data+t+view+'proj')
   h[oneHit234].SetMaximum(-1111)
   h[oneHit234].SetMinimum(-1111)
   h[twoHit34].SetMaximum(-1111)
   h[twoHit34].SetMinimum(-1111)
   for k in range(1,h[mean].GetNbinsX()):
       test = hx[t+view].ProjectionY('test',k,k) 
       h[mean].SetBinContent(k,test.GetMean())
       h[mean].SetBinError(k,0)
       ratio = float(test.GetBinContent(2))/(test.GetBinContent(3)+test.GetBinContent(4)+test.GetBinContent(5)+1E-6)
       h[oneHit234].SetBinContent(k,ratio)
       h[oneHit234].SetBinError(k,0)
       ratio = float(test.GetBinContent(3))/(test.GetBinContent(4)+test.GetBinContent(5)+1E-6)
       h[twoHit34].SetBinContent(k,ratio)
       h[twoHit34].SetBinError(k,0)
   h[mean].SetMinimum(2.)
   h[mean].SetMaximum(4.)
   h[mean].Fit('pol1','PL','',50,300)
   h[mean].SetStats(0)
 for data in ['data','MC']:
  hx = histos[data]
  n = 1
  for view in views:
   tc = h[t].cd(n)
   mean      = data+'mean'+t+view
   if data == 'MC':
       h[mean].SetLineColor(ROOT.kGreen)
       h[mean].Draw('histsame')
   else:
       h[mean].SetLineColor(ROOT.kBlue)
       h[mean].Draw('hist')
   h[mean].GetFunction('pol1').Draw('same')
   tc = h[t+'proj'].cd(n)
   tc.SetLogy()
   hname = data+t+view+'proj'
   h[hname].GetXaxis().SetRangeUser(-0.5,6.5)
   if data == 'MC':    
      h[hname].SetLineColor(ROOT.kGreen)
      h[hname].Draw('histsame')
   else:    
      h[hname].SetLineColor(ROOT.kBlue)
      h[hname].Draw('hist')
   n+=1
 h[t].Print(t+'meanFunP.pdf')
 h[t].Print(t+'meanFunP.png')
 h[t+'proj'].Print(t+'distribution.png')
 h[t+'proj'].Print(t+'distribution.pdf')
def plotEnergyLoss():
 f=ROOT.TFile('PinPout.root')
 PinPout = f.PinPout
 PinPout.SetStats(0)
 PinPout.SetTitle('incoming vs. outgoing momentum;p [GeV/c];p [GeV/c];  ')
 PinPout.Draw('box')
 lx = ROOT.TLine(0.,1.,10.,1.)
 lx.DrawClone()
 ly = ROOT.TLine(5.,0.,5.,10.)
 ly.DrawClone()

hMC      = {}
hCharm   = {}
hMC10GeV = {}

hMC0={}
hMC2={}
hMCrec0={}
hCharm0={}
hCharm2={}
hCharmrec0={}
hMC10GeV0={}
hMC10GeV2={}
hMC10GeVrec0={}
def checkMCEffTuning():
 charmNorm  = {1:0.176,10:0.424}
 beautyNorm = {1:0.,   10:0.01218}
 sim10fact = 1.8/(65.*(1.-0.016)) # normalize 10GeV to 1GeV stats, 1.6% of 10GeV stats not processed.
 sources = {"":1.,"Hadronic inelastic":100.,"Lepton pair":100.,"Positron annihilation":100.,"charm":1./charmNorm[10],"beauty":1./beautyNorm[10]}
 interestingHistos = []
 for a in ['p/pt']:
   for x in ['','mu']:
    for source in sources:  interestingHistos.append(a+x+source)
 ut.readHists(hMC,   'momDistributions-mbias.root',interestingHistos)
 ut.readHists(hCharm,'momDistributions-charm.root',interestingHistos)
 ut.readHists(hMC10GeV,'momDistributions-10GeVTR.root',interestingHistos)
 ut.readHists(hMC0,   'momDistributions-1GeV-mbias-effTuned-M0.root',interestingHistos)
 ut.readHists(hMC2,   'momDistributions-1GeV-mbias-effTuned-M2.root',     interestingHistos)
 ut.readHists(hMCrec0,   'momDistributions-1GeV-mbias-effTuned-M0-reco.root',interestingHistos)
 ut.readHists(hCharm0,'momDistributions-1GeV-charm-effTuned-M0.root',interestingHistos)
 ut.readHists(hCharm2,'momDistributions-1GeV-charm-effTuned-M2.root',     interestingHistos)
 ut.readHists(hCharmrec0,'momDistributions-1GeV-charm-effTuned-M0-reco.root',interestingHistos)
 ut.readHists(hMC10GeV0,'momDistributions-10GeV-mbias-effTuned-M0.root',interestingHistos)
 ut.readHists(hMC10GeV2,'momDistributions-10GeV-mbias-effTuned-M2.root',interestingHistos)
 ut.readHists(hMC10GeVrec0,'momDistributions-10GeV-mbias-effTuned-M0-reco.root',interestingHistos)
 a= 'p/pt_projx'
 print "method 0 / default"
 print "1GeV mbias:",hMC0[a].GetEntries()/hMC[a].GetEntries(),hMCrec0[a].GetEntries()/hMC[a].GetEntries()
 print "1GeV charm:",hCharm0[a].GetEntries()/hCharm[a].GetEntries(),hCharmrec0[a].GetEntries()/hCharm[a].GetEntries()
 print "10GeV     :",hMC10GeV0[a].GetEntries()/hMC10GeV[a].GetEntries(),hMC10GeVrec0[a].GetEntries()/hMC10GeV[a].GetEntries()
 print "method 2 / default"
 print "1GeV mbias:",hMC2[a].GetEntries()/hMC[a].GetEntries()
 print "1GeV charm:",hCharm2[a].GetEntries()/hCharm[a].GetEntries()
 print "10GeV     :",hMC10GeV2[a].GetEntries()/hMC10GeV[a].GetEntries()
# effect on mom distribution of eff tuning
 methods = {'default':[hMC,hCharm,hMC10GeV],'M0':[hMC0,hCharm0,hMC10GeV0],'M2':[hMC2,hCharm2,hMC10GeV2],'M0rec':[hMCrec0,hCharmrec0,hMC10GeVrec0]}
 for m in methods:
  h['MC'+m+a] = methods[m][0][a].Clone('MC'+m+a)
  h['MC'+m+a].Add(methods[m][1][a],charmNorm[1])
  h['MC10'+m+a] = methods[m][2][a].Clone('MC'+m+a)
  h['MC10'+m+a].Add(methods[m][2][a.replace("_","charm_")],-1.+charmNorm[10])
  h['MC10'+m+a].Add(methods[m][2][a.replace("_","beauty_")],-1.+beautyNorm[10])
  h['MC10'+m+a].Scale(sim10fact)
  for n in range(1,h['MC'+m+a].GetNbinsX()+1):
    if h['MC'+m+a].GetBinCenter(n)>10:
      h['MC'+m+a].SetBinContent(n,h['MC10'+m+a].GetBinContent(n))
      h['MC'+m+a].SetBinError(n,h['MC10'+m+a].GetBinError(n))
  h['MC'+m+a].Rebin(5)
  ut.makeIntegralDistrib(h,'MC'+m+a)
 colors = {'M0':ROOT.kRed,'M2':ROOT.kBlue,'M0rec':ROOT.kMagenta}
 t = 'MC-Comparison eff tuning'
 if not h.has_key(t): ut.bookCanvas(h,key=t,title='MC-Comparison eff tuning',nx=900,ny=600,cx=1,cy=1)
 tc = h[t].cd(1)
 h['leg'+t]=ROOT.TLegend(0.55,0.65,0.85,0.85)
 n = 0
 for m in methods: 
  if m == 'default':continue
  ihist = 'I-'+m+'OverDefault'
  h[ihist] = h['I-MC'+m+a].Clone(ihist)
  h[ihist].Divide(h['I-MCdefault'+a])
  h[ihist].SetLineColor(colors[m])
  h[ihist].GetXaxis().SetRangeUser(5,400)
  h[ihist].SetStats(0)
  h[ihist].SetMaximum(1.1)
  h[ihist].SetTitle('efficiency correction as function of momentum '+m+';p [GeV/c];efficiency correction')
  if n == 0: h[ihist].Draw()
  else: h[ihist].Draw('same')
  n+=1
  h['leg'+t].AddEntry(h[ihist],'method '+m+' / default','PL')
 h['leg'+t].Draw()
def MCcomparison(pot = -1, pMin = 5.,effCor=True,eric=False):
 # 1GeV mbias,      1.8 Billion PoT 
 # 1GeV charm,     10.2 Billion PoT,  10 files
 # 10GeV MC,         65 Billion PoT 
 # data RUN_2395, ~10.6 Billion PoT, 742 files
 # using 626 POT/mu-event and preliminary counting of good tracks -> 12.63 -> pot factor 7.02
 # using 710 POT/mu-event, full field
 # mbias POT/ charm POT = 0.176 (1GeV), 0.424 (10GeV)
 MCStats = 1.8E9
 sim10fact = 1.8/(65.*(1.-0.016)) # normalize 10GeV to 1GeV stats, 1.6% of 10GeV stats not processed.
 muPerPot = 710 # 626
 charmNorm  = {1:0.176,10:0.424}
 beautyNorm = {1:0.,   10:0.01218}
 sources = {"":1.,"Hadronic inelastic":100.,"Lepton pair":100.,"Positron annihilation":100.,"charm":1./charmNorm[10],"beauty":1./beautyNorm[10],"Di-muon P8":100.}
 if len(hMC)==0:
  interestingHistos = []
  for a in ['p/pt','p/Abspx','p1/p2','p1/p2s','Trscalers']:
   for x in ['','mu']:
    for source in sources:  interestingHistos.append(a+x+source)
  ut.readHists(h,     'momDistributions.root',interestingHistos)
  # uncorrected MC histos
  if not effCor:
   ut.readHists(hMC,   'momDistributions-mbias.root',interestingHistos)
   ut.readHists(hCharm,'momDistributions-charm.root',interestingHistos)
   if eric: ut.readHists(hMC10GeV,'momDistributions-10GeV.root',interestingHistos)
   else:    ut.readHists(hMC10GeV,'momDistributions-10GeVTR.root',interestingHistos)
  else:
   ut.readHists(hMC,   'momDistributions-1GeV-mbias-effTuned-M0-reco.root',interestingHistos)
   ut.readHists(hMC,   'momDistributions-1GeV-mbias-effTuned-M2.root',     interestingHistos)
   ut.readHists(hCharm,'momDistributions-1GeV-charm-effTuned-M0-reco.root',interestingHistos)
   ut.readHists(hCharm,'momDistributions-1GeV-charm-effTuned-M2.root',     interestingHistos)
   ut.readHists(hMC10GeV,'momDistributions-10GeV-mbias-effTuned-M0-reco.root',interestingHistos)
   ut.readHists(hMC10GeV,'momDistributions-10GeV-mbias-effTuned-M2.root',interestingHistos)
   MCStats = MCStats*2.
  for a in ['p/pt','p/Abspx','p1/p2','p1/p2s']:
    for x in ['','mu']:
     if a.find('p1/p2')==0 and x=='mu': continue
     for hstore in [hMC,hCharm,hMC10GeV]: 
# for new category "G4default", subtract dimuons made by SHiP modification to G4
      hstore[a+x+"G4default"]=hstore[a+x].Clone(a+x+"G4default")
      hstore[a+x+"G4default"].Add(hstore[a+x+"Hadronic inelastic"],-1.)
     
 if pot <0: # (default, use Hans normalization)
   pot = h['Trscalers'].GetBinContent(3) * muPerPot / MCStats
   print "PoT data",h['Trscalers'].GetBinContent(3) * muPerPot / 1E9," billion"
 if pot == 0:
   z = h['MCp/pt'].ProjectionX()
   MCPG5 = z.Integral(z.FindBin(pMin),z.GetNbinsX())
   z = h['p/pt'].ProjectionX()
   PG5 = z.Integral(z.FindBin(pMin),z.GetNbinsX())
   norm = PG5/MCPG5
   print "use as normalization:",norm
 else: norm = pot
 for a in ['p/pt','p/Abspx','p1/p2','p1/p2s']:
   for x in ['','mu']:
    if a.find('p1/p2')==0 and x=='mu': continue
    h['MC'+a+x]   = hMC[a+x].Clone('MC'+a+x)
    h['MC'+a+x].Add(hCharm[a+x],charmNorm[1])
    h['MC'+a+x].Scale(norm)
    for source in sources:
     if source == "" or source == "beauty": continue
     xxx = a+x+source
     if source == "charm":
      h['MC'+xxx] = hCharm[a+x].Clone('MC'+xxx)
      h['MC'+xxx].Scale(charmNorm[1])
     else:
      if not xxx in hMC:  
        print xxx, " need to remake histos for 1GeV "
        h['MC'+xxx] = hMC[a+x].Clone('MC'+xxx)
        h['MC'+xxx].Reset()
      else:
        h['MC'+xxx] = hMC[xxx].Clone('MC'+xxx)
     h['MC'+xxx].Scale(norm)
#
    h['MC10'+a+x] = hMC10GeV[a+x].Clone('MC10'+a+x)
# special treatment for 10GeV to get weights right
    if eric: # data with boosted channels
     for source in sources:
      if source == "": continue
      xxx = a+x+source
      h['MC10'+a+x].Add(hMC10GeV[xxx],-1.+1./sources[source])
      h['MC10'+xxx] = hMC10GeV[xxx].Clone('MC10'+xxx)
      h['MC10'+xxx].Scale(1./sources[source])
      h['MC10'+xxx].Scale(1.8/65.) # scale it to 1GeV MC statistics
     h['MC10'+a+x].Scale(1.8/65.)
    else:
     h['MC10'+a+x].Add(hMC10GeV[a+x+"charm"],-1.+charmNorm[10])
     h['MC10'+a+x].Add(hMC10GeV[a+x+"beauty"],-1.+beautyNorm[10])
     for source in sources:
      if source == "": continue
      xxx = a+x+source
      h['MC10'+xxx] = hMC10GeV[xxx].Clone('MC10'+xxx)
      if source == "charm" or source == "beauty": h['MC10'+xxx].Scale(sim10fact/sources[source]*norm)
      else: h['MC10'+xxx].Scale(sim10fact*norm)
     h['MC10'+a+x].Scale(sim10fact*norm)

#
 optSorted = ['','MC','MC10','MCcharm','MCDi-muon P8','MCHadronic inelastic','MCLepton pair','MCPositron annihilation',
                         'MC10charm','MC10Hadronic inelastic','MC10Di-muon P8','MC10Lepton pair','MC10Positron annihilation'] # decay removed, only covers part
 opt = {'':['',ROOT.kBlue,'data'],'MC':['same',ROOT.kRed,'MC inclusive'],'MC10':['same',ROOT.kRed,'MC 10GeV total'],
           'MCcharm':['same',ROOT.kGreen,'Charm'],'MC10charm':['same',ROOT.kGreen,'Charm'],
           'MCHadronic inelastic':['same',ROOT.kCyan+1,'Dimuon from decays G4'],
           'MC10Hadronic inelastic':['same',ROOT.kCyan+1,'Dimuon from decays G4'],
           'MCLepton pair':['same',ROOT.kGreen+1,'Lepton pair'],'MCPositron annihilation':['same',ROOT.kRed+2,'Positron annihilation'],
           'MC10Lepton pair':['same',ROOT.kGreen+1,'Lepton pair'],'MC10Positron annihilation':['same',ROOT.kRed+2,'Positron annihilation'],
           'MCDi-muon P8':['same',ROOT.kCyan,'Dimuon from decays P8'],
           'MC10Di-muon P8':['same',ROOT.kCyan,'Dimuon from decays P8'] }
 for d in ['','I-']:
  for x in ['','mu']:
   t = d+'MC-Comparison'+x
   if not h.has_key(t): ut.bookCanvas(h,key=t,title=d+' MC / Data '+x,nx=1200,ny=600,cx=3,cy=2)
   if d=='':
    for a in ['p/pt','p/Abspx','p1/p2']:
     if a=='p1/p2' and x=='mu': continue
     for source in sources:
      xxx = a+x+source
      h['MC10'+xxx+'_x']    = h['MC10'+xxx].ProjectionX()
      if source == "":  h[xxx+'_x'] = h[xxx].ProjectionX()
      if source == "beauty": continue
      h['MC'+xxx+'_x']    = h['MC'+xxx].ProjectionX()
    for i1 in opt:
     i = i1
     source = ""
     if not i.find('MC10')<0: 
        i = 'MC10'
        source = i1.split('MC10')[1]
     elif not i.find('MC')<0: 
        i = 'MC'
        source = i1.split('MC')[1]
     z = x+source
# MC 1 GeV should agree with data above P>5GeV
# MC 10 GeV should agree with data above P>20GeV ? 10 GeV should also fit
     if i == "MC":
      h[i+'p/pt'+z+'_y']   =h[i+'p/pt'+z].ProjectionY(i+'p/pt'+z+'_y'      ,h[i+'p/pt'+x+'_x'].FindBin(pMin),h[i+'p/pt'+x+'_x'].FindBin(20.))
      tmp = h[i+'10p/pt'+z].ProjectionY('tmp',h[i+'p/pt'+x+'_x'].FindBin(20)+1,h[i+'p/pt'+x+'_x'].GetNbinsX())
# attempt to make pt/px distribution with 1 GeV and 10 GeV MC
      h[i+'p/pt'+z+'_y'].Add(tmp)
      h[i+'p/Abspx'+z+'_y']=h[i+'p/Abspx'+z].ProjectionY(i+'p/Abspx'+z+'_y',h[i+'p/pt'+x+'_x'].FindBin(pMin),h[i+'p/pt'+x+'_x'].FindBin(20.))
      tmp = h[i+'10p/Abspx'+z].ProjectionY('tmp',h[i+'p/pt'+x+'_x'].FindBin(20)+1,h[i+'p/pt'+x+'_x'].GetNbinsX())
      h[i+'p/Abspx'+z+'_y'].Add(tmp)
      for pInterval in [ [pMin,50.],[51.,100.],[101.,200.],[201.,300.] ]:
       interval = '_y'+str(pInterval[0])+'-'+str(pInterval[1])
       if pInterval[0]<20:
         h[i+'p/pt'+z+interval]   =h[i+'p/pt'+z].ProjectionY(i+'p/pt'+z+interval      ,h[i+'p/pt'+x+'_x'].FindBin(pInterval[0]),h[i+'p/pt'+x+'_x'].FindBin(20.))
         tmp = h[i+'10p/pt'+z].ProjectionY('tmp',h[i+'p/pt'+x+'_x'].FindBin(20.)+1,h[i+'p/pt'+x+'_x'].FindBin(pInterval[1]))
# attempt to make pt/px distribution with 1 GeV and 10 GeV MC
         h[i+'p/pt'+z+interval].Add(tmp)
         h[i+'p/Abspx'+z+interval]=h[i+'p/Abspx'+z].ProjectionY(i+'p/Abspx'+z+interval,h[i+'p/pt'+x+'_x'].FindBin(pInterval[0]),h[i+'p/pt'+x+'_x'].FindBin(20.))
         tmp = h[i+'10p/Abspx'+z].ProjectionY('tmp',h[i+'p/pt'+x+'_x'].FindBin(20.)+1,h[i+'p/pt'+x+'_x'].FindBin(pInterval[1]))
         h[i+'p/Abspx'+z+interval].Add(tmp)
       else:
         h[i+'p/pt'+z+interval]   =h[i+'p/pt'+z].ProjectionY(i+'p/pt'+z+interval      ,h[i+'p/pt'+x+'_x'].FindBin(pInterval[0]),h[i+'p/pt'+x+'_x'].FindBin(pInterval[1]))
         h[i+'p/Abspx'+z+interval]=h[i+'p/Abspx'+z].ProjectionY(i+'p/Abspx'+z+interval,h[i+'p/pt'+x+'_x'].FindBin(pInterval[0]),h[i+'p/pt'+x+'_x'].FindBin(pInterval[1]))
       h[i+'p/pt'+z+interval].SetTitle('pt for '+str(pInterval[0])+' < P < '+str(pInterval[1]))
       h[i+'p/Abspx'+z+interval].SetTitle('|px| for '+str(pInterval[0])+' < P < '+str(pInterval[1]))
     else:
      h[i+'p/pt'+z+'_y']   =h[i+'p/pt'+z].ProjectionY(i+'p/pt'+z+'_y'      ,h[i+'p/pt'+x+'_x'].FindBin(pMin),h[i+'p/pt'+x+'_x'].GetNbinsX())
      h[i+'p/Abspx'+z+'_y']=h[i+'p/Abspx'+z].ProjectionY(i+'p/Abspx'+z+'_y',h[i+'p/pt'+x+'_x'].FindBin(pMin),h[i+'p/pt'+x+'_x'].GetNbinsX())
      for pInterval in [ [pMin,50.],[51.,100.],[101.,200.],[201.,300.] ]:
       interval = '_y'+str(pInterval[0])+'-'+str(pInterval[1])
       h[i+'p/pt'+z+interval]   =h[i+'p/pt'+z].ProjectionY(i+'p/pt'+z+interval      ,h[i+'p/pt'+x+'_x'].FindBin(pInterval[0]),h[i+'p/pt'+x+'_x'].FindBin(pInterval[1]))
       h[i+'p/Abspx'+z+interval]=h[i+'p/Abspx'+z].ProjectionY(i+'p/Abspx'+z+interval,h[i+'p/pt'+x+'_x'].FindBin(pInterval[0]),h[i+'p/pt'+x+'_x'].FindBin(pInterval[1]))
       h[i+'p/pt'+z+interval].SetTitle('pt for '+str(pInterval[0])+' < P < '+str(pInterval[1]))
       h[i+'p/Abspx'+z+interval].SetTitle('|px| for '+str(pInterval[0])+' < P < '+str(pInterval[1]))
     ut.makeIntegralDistrib(h,i+'p/pt'+x+source+'_x')
     ut.makeIntegralDistrib(h,i+'p/pt'+x+source+'_y')
     ut.makeIntegralDistrib(h,i+'p/Abspx'+x+source+'_y')
#
   tc = 1
   rc = h[t].cd(tc)
   rc.SetLogy(1)
   h['leg'+t+str(tc)]=ROOT.TLegend(0.50,0.61,0.96,0.93)
   mx1 = ut.findMaximumAndMinimum(h[d+'p/pt'+x+'_x'])[1]
   mx2 = ut.findMaximumAndMinimum(h[d+'MCp/pt'+x+'_x'])[1]
   hMax = max(mx1,mx2)
   for i1 in optSorted:
    i = i1
    source = ""
    if not i.find('MC10')<0: 
        i = 'MC10'
        source = i1.split('MC10')[1]
    elif not i.find('MC')<0: 
        i = 'MC'
        source = i1.split('MC')[1]
        h[d+i+'p/pt'+xx+'_x']
    xx = x+source
    h[d+i+'p/pt'+xx+'_x'].SetTitle('momentum P')
    h[d+i+'p/pt'+xx+'_x'].SetMaximum(hMax*10.)
    h[d+i+'p/pt'+xx+'_x'].SetMinimum(1.)
    h[d+i+'p/pt'+xx+'_x'].SetLineWidth(1)
    h[d+i+'p/pt'+xx+'_x'].SetMarkerSize(1)
    h[d+i+'p/pt'+xx+'_x'].SetLineColor(opt[i1][1])
    h[d+i+'p/pt'+xx+'_x'].SetStats(0)
    h[d+i+'p/pt'+xx+'_x'].Draw(opt[i1][0])
    if i =='MC':  h[d+i+'p/pt'+xx+'_x'].GetXaxis().SetRangeUser(0,50)
    if i =='MC10':  h[d+i+'p/pt'+xx+'_x'].GetXaxis().SetRangeUser(20,500)
    if i.find('MC10')<0: h['leg'+t+str(tc)].AddEntry(h[d+i+'p/pt'+xx+'_x'],opt[i1][2],'PL')
   h['leg'+t+str(tc)].Draw('same')
   tc = 2
   rc = h[t].cd(tc)
   rc.SetLogy(1)
   h['leg'+t+str(tc)]=ROOT.TLegend(0.50,0.61,0.96,0.93)
   mx1 = ut.findMaximumAndMinimum(h[d+'p/pt'+x+'_y'])[1]
   mx2 = ut.findMaximumAndMinimum(h[d+'MCp/pt'+x+'_y'])[1]
   hMay = max(mx1,mx2)
   for i1 in optSorted:
    i = i1
    source = ""
    if not i.find('MC10')<0:
        i = 'MC10'
        source = i1.split('MC10')[1]
    elif not i.find('MC')<0: 
        i = 'MC'
        source = i1.split('MC')[1]
    if i=='MC10': continue # Pt/Px distributions from 1GeV and 10GeV are merged into one
    xx = x+source
    h[d+i+'p/pt'+xx+'_y'].SetTitle('transverse momentum Pt, P>'+str(pMin))
    h[d+i+'p/pt'+xx+'_y'].SetMaximum(hMay*10.)
    h[d+i+'p/pt'+xx+'_y'].SetMinimum(1.)
    h[d+i+'p/pt'+xx+'_y'].SetLineWidth(1)
    h[d+i+'p/pt'+xx+'_y'].SetMarkerSize(1)
    h[d+i+'p/pt'+xx+'_y'].SetLineColor(opt[i1][1])
    h[d+i+'p/pt'+xx+'_y'].SetStats(0)
    h[d+i+'p/pt'+xx+'_y'].Draw(opt[i1][0])
    if i.find('MC10')<0: h['leg'+t+str(tc)].AddEntry(h[d+i+'p/pt'+xx+'_y'],opt[i1][2],'PL')
   h['leg'+t+str(tc)].Draw('same')
   tc = 3
   rc = h[t].cd(tc)
   rc.SetLogy(1)
   h['leg'+t+str(tc)]=ROOT.TLegend(0.50,0.61,0.96,0.93)
   mx1 = ut.findMaximumAndMinimum(h[d+'p/Abspx'+x+'_y'])[1]
   mx2 = ut.findMaximumAndMinimum(h[d+'MCp/Abspx'+x+'_y'])[1]
   hMaPx = max(mx1,mx2)
   for i1 in optSorted:
    i = i1
    source = ""
    if not i.find('MC10')<0: 
        i = 'MC10'
        source = i1.split('MC10')[1]
    elif not i.find('MC')<0: 
        i = 'MC'
        source = i1.split('MC')[1]
    if i=='MC10': continue
    xx = x+source
    h[d+i+'p/Abspx'+xx+'_y'].SetTitle('Px, P>'+str(pMin))
    h[d+i+'p/Abspx'+xx+'_y'].SetMaximum(hMaPx*10.)
    h[d+i+'p/Abspx'+xx+'_y'].SetMinimum(1.)
    h[d+i+'p/Abspx'+xx+'_y'].SetLineWidth(1)
    h[d+i+'p/Abspx'+xx+'_y'].SetMarkerSize(1)
    h[d+i+'p/Abspx'+xx+'_y'].SetLineColor(opt[i1][1])
    h[d+i+'p/Abspx'+xx+'_y'].SetStats(0)
    h[d+i+'p/Abspx'+xx+'_y'].Draw(opt[i1][0])
    if i.find('MC10')<0: h['leg'+t+str(tc)].AddEntry(h[d+i+'p/Abspx'+xx+'_y'],opt[i1][2],'PL')
   h['leg'+t+str(tc)].Draw('same')
   tc = 4
   rc = h[t].cd(tc)
   h['leg'+t+str(tc)]=ROOT.TLegend(0.42,0.54,0.88,0.86)
   for i1 in optSorted:
    i = i1
    source = ""
    if not i.find('MC10')<0: 
        i = 'MC10'
        source = i1.split('MC10')[1]
    elif not i.find('MC')<0: 
        i = 'MC'
        source = i1.split('MC')[1]
    xx = x+source
    h['lin'+d+i+'p/pt'+xx+'_x']=h[d+i+'p/pt'+xx+'_x'].Clone('lin'+d+i+'p/pt'+xx+'_x')
    h['lin'+d+i+'p/pt'+xx+'_x'].GetXaxis().SetRange(1,120)
    h['lin'+d+i+'p/pt'+xx+'_x'].SetMaximum(hMax*1.1)
    h['lin'+d+i+'p/pt'+xx+'_x'].SetMinimum(0.)
    h['lin'+d+i+'p/pt'+xx+'_x'].Draw(opt[i1][0])
    if i.find('MC10')<0: h['leg'+t+str(tc)].AddEntry(h[d+i+'p/pt'+xx+'_x'],opt[i1][2],'PL')
    if i =='MC10':  h['lin'+d+i+'p/pt'+xx+'_x'].GetXaxis().SetRangeUser(20,500)
   h['leg'+t+str(tc)].Draw('same')
   tc = 5
   rc = h[t].cd(tc)
   h['leg'+t+str(tc)]=ROOT.TLegend(0.42,0.54,0.88,0.86)
   for i1 in optSorted:
    i = i1
    source = ""
    if not i.find('MC10')<0: 
        i = 'MC10'
        source = i1.split('MC10')[1]
    elif not i.find('MC')<0: 
        i = 'MC'
        source = i1.split('MC')[1]
    if i=='MC10': continue
    xx = x+source
    h['lin'+d+i+'p/pt'+xx+'_y']=h[d+i+'p/pt'+xx+'_y'].Clone('lin'+d+i+'p/pt'+xx+'_y')
    h['lin'+d+i+'p/pt'+xx+'_y'].GetXaxis().SetRange(1,25)
    h['lin'+d+i+'p/pt'+xx+'_y'].SetMaximum(hMay*1.1)
    h['lin'+d+i+'p/pt'+xx+'_y'].SetMinimum(0.)
    h['lin'+d+i+'p/pt'+xx+'_y'].SetStats(0)
    h['lin'+d+i+'p/pt'+xx+'_y'].Draw(opt[i1][0])
    if i.find('MC10')<0: h['leg'+t+str(tc)].AddEntry(h[d+i+'p/pt'+xx+'_y'],opt[i1][2],'PL')
   h['leg'+t+str(tc)].Draw('same')
   tc = 6
   rc = h[t].cd(tc)
   h['leg'+t+str(tc)]=ROOT.TLegend(0.42,0.54,0.88,0.86)
   for i1 in optSorted:
    i = i1
    source = ""
    if not i.find('MC10')<0: 
        i = 'MC10'
        source = i1.split('MC10')[1]
    elif not i.find('MC')<0: 
        i = 'MC'
        source = i1.split('MC')[1]
    if i=='MC10': continue
    xx = x+source
    h['lin'+d+i+'p/Abspx'+xx+'_y']=h[d+i+'p/Abspx'+xx+'_y'].Clone('lin'+d+i+'p/Abspx'+xx+'_y')
    h['lin'+d+i+'p/Abspx'+xx+'_y'].GetXaxis().SetRange(1,25)
    h['lin'+d+i+'p/Abspx'+xx+'_y'].SetMaximum(hMaPx*1.1)
    h['lin'+d+i+'p/Abspx'+xx+'_y'].SetMinimum(0.)
    h['lin'+d+i+'p/Abspx'+xx+'_y'].SetStats(0)
    h['lin'+d+i+'p/Abspx'+xx+'_y'].Draw(opt[i][0])
    if i.find('MC10')<0: h['leg'+t+str(tc)].AddEntry(h[d+i+'p/Abspx'+xx+'_y'],opt[i1][2],'PL')
   h['leg'+t+str(tc)].Draw('same')
   h[t].Update()
   h[t].Print('MC-Comparison'+d+x+'.pdf')
   h[t].Print('MC-Comparison'+d+x+'.png')
 for x in ['','mu']:
  if x != '': print "=== muon tagged ===="
  else: print       "=== all tracks  ===="
  for P in [5.,10.,50.,100.]:
   nbin = h['p/pt'+x+'_x'].FindBin(P)
   print "data/MC P>%5i GeV: %5.2F"%(int(P),h['I-p/pt'+x+'_x'].GetBinContent(nbin)/h['I-MCp/pt'+x+'_x'].GetBinContent(nbin))
# pt in slices of P
 x = 'mu'
 for t in ['MC-Comparison Pt','MC-Comparison Px']:
  if not h.has_key(t): ut.bookCanvas(h,key=t,title=' MC / Data '+t.split(' ')[1],nx=1200,ny=600,cx=2,cy=2)
  y = 1
  for pInterval in [ [pMin,50.],[51.,100.],[101.,200.],[201.,300.] ]:
   interval = '_y'+str(pInterval[0])+'-'+str(pInterval[1])
   tc = h[t].cd(y)
   y+=1
   h['leg'+t+str(tc)]=ROOT.TLegend(0.42,0.54,0.88,0.86)
   for i1 in optSorted:
    i = i1
    source = ""
    if not i.find('MC10')<0: 
        i = 'MC10'
        source = i1.split('MC10')[1]
    elif not i.find('MC')<0: 
        i = 'MC'
        source = i1.split('MC')[1]
    if i=='MC10': continue
    xx = x+source
    proj = 'p/pt'
    if t.find('Px')>0: proj = 'p/Abspx'
    hname = i+proj+xx+interval
    mx1 = ut.findMaximumAndMinimum(h[ proj+x+interval])[1]
    mx2 = ut.findMaximumAndMinimum(h['MC'+proj+x+interval])[1]
    hMaPx = max(mx1,mx2)
    h[hname].GetXaxis().SetRangeUser(0.,5.)
    h[hname].SetMaximum(hMaPx*1.1)
    h[hname].SetMinimum(0.)
    h[hname].SetStats(0)
    h[hname].SetLineWidth(1)
    h[hname].SetMarkerSize(1)
    h[hname].SetLineColor(opt[i1][1])
    h[hname].Draw(opt[i][0])
    if i.find('MC10')<0: h['leg'+t+str(tc)].AddEntry(h[hname],opt[i1][2],'PL')
   h['leg'+t+str(tc)].Draw('same')
  h[t].Update()
  h[t].Print('MC-Comparison'+t.replace(' ','')+'.pdf')
  h[t].Print('MC-Comparison'+t.replace(' ','')+'.png')

# some code for 2 track events
 osign = {'':'opposite sign','s':'same sign'}
 for s in osign:
  t = '2trackOverAll'+osign[s]
  if not h.has_key(t): ut.bookCanvas(h,key=t,title=' momentum of muons in 2-track events '+osign[s],nx=800,ny=1200,cx=1,cy=2)
  txt = {6:'P>5GeV/c',21:'P>20GeV/c'}
  pad = 1
  rebin = False #5
  for case in txt:
   tc = h[t].cd(pad)
   h['leg'+t+str(pad)+s]=ROOT.TLegend(0.42,0.54,0.88,0.86)
   hn = 'p1p2'+txt[case]+s
   h[hn] = h['p1/p2'+s].ProjectionX(hn,case,500)
   h[hn].Add(h['p1/p2'+s].ProjectionY('p1p2y'+txt[case]+s,case,500))
   if rebin>1: h[hn].Rebin(rebin)
   norm = h['p/ptmu_x'].Integral(case,500)
   h[hn].Scale(1./norm)
   h[hn].SetTitle('P in 2-track events '+txt[case]+'; GeV/c;N2/Nall with P > / ')
   h[hn].SetStats(0)
   h[hn].SetMaximum(0.1)
   h[hn].SetMinimum(2E-6)
   ut.makeIntegralDistrib(h,hn)
   Ihn = 'I-'+hn
   h[Ihn].GetXaxis().SetRangeUser(case,500)
   h[Ihn].Draw()
   h['leg'+t+str(pad)+s].AddEntry(h[hn],opt[''][2],'PL')
   tc.SetLogy()
# now MC
   if case < 20: mchist = 'MCp1/p2'+s
   else:         mchist = 'MC10p1/p2'+s
   hn='MCp1p2'+txt[case]+s
   h[hn] = h[mchist].ProjectionX(hn,case,500)
   h[hn].Add(h[mchist].ProjectionY('MCp1p2y'+txt[case]+s,case,500))
   if rebin>1: h[hn].Rebin(rebin)
   if case < 20: norm = h['MCp/ptmu_x'].Integral(case,500)
   else:         norm = h['MC10p/ptmu_x'].Integral(case,500)
   h[hn].Scale(1./norm)
   h[hn].SetStats(0)
   h[hn].SetTitle('P in 2-track events, one track with '+txt[case]+'; GeV/c')
   h[hn].SetLineColor(opt['MC'][1])
   ut.makeIntegralDistrib(h,hn)
   Ihn = 'I-'+hn
   h[Ihn].Draw('same')
   h[Ihn].GetXaxis().SetRangeUser(case,500)
   h['leg'+t+str(pad)+s].AddEntry(h[hn],opt['MC'][2],'PL')
   tc.SetLogy()
   for i1 in optSorted:
    if i1.find('MC')<0: continue
    if i1.find('MC10')<0 and case==21: continue
    if not i1.find('MC10')<0 and case==6: continue
    if not i1.find('MC10')<0: 
        i = 'MC10'
        source = i1.split('MC10')[1]
    elif not i.find('MC')<0: 
        i = 'MC'
        source = i1.split('MC')[1]
    if source == '': continue
    hn='MCp1p2'+source+txt[case]+s
    h[hn] = h[i+'p1/p2'+s+source].ProjectionX(hn,case,500)
    h[hn].Add(h[i+'p1/p2'+s+source].ProjectionY(i+'p1/p2y'+source+txt[case]+s,case,500))
    if rebin>1: h[hn].Rebin(5)
    h[hn].SetLineColor(opt[i1][1])
    h[hn].SetStats(0)
    h[hn].Scale(1./norm)
    ut.makeIntegralDistrib(h,hn)
    Ihn = 'I-'+hn
    h[Ihn].Draw('same')
    h[Ihn].GetXaxis().SetRange(case,500)
    h['leg'+t+str(pad)+s].AddEntry(h[hn],opt[i1][2],'PL')
   h['leg'+t+str(pad)+s].Draw('same')
   pad +=1
  h[t].Print('MC-Comparison 2Tracks'+osign[s]+'.pdf')
  h[t].Print('MC-Comparison 2Track'+osign[s]+'.png')
def printSources():
 charmNorm  = {1:0.176,10:0.424}
 beautyNorm = {1:0.,   10:0.01218}
 sources = {"":1.,"Hadronic inelastic":100.,"Lepton pair":100.,"Positron annihilation":100.,"charm":1./charmNorm[10],"beauty":1./beautyNorm[10],"Di-muon P8":100.}
 print "     source           P>5GeV/c          P>20GeV/c"
 for xx in sources:
   i='MC'
   d='I-'
   hname = d+i+'p/pt'+xx+'_x'
   hname10 = d+i+'10p/pt'+xx+'_x'
   if not h.has_key(hname):continue
   ratio = h[hname].GetBinContent(1)/h[d+i+'p/pt_x'].GetBinContent(1)*100
   ratio10 = h[hname10].GetBinContent(21)/h[d+i+'10p/pt_x'].GetBinContent(21)*100
   print " %25s %4.2F%%    %4.2F%% "%(xx,ratio,ratio10)

def MCchecks():
 mult={}
 mult['0']=0
 for n in range(sTree.GetEntries()):
  rc=sTree.GetEvent(n)
  if n%10000==0: print n
  muon={}
  for m in sTree.MCTrack:
   if abs(m.GetPdgCode())==13:
     mult['0']+=1
     p = m.GetProcName().Data()
     if not muon.has_key(p): muon[p]=0
     muon[p]+=1
  if len(muon)==0:
    print "MCchecks",sTree.GetCurrentFile().GetName()
    sTree.MCTrack.Dump()
  for p in muon:
   if not mult.has_key(p): mult[p]={}
   N = muon[p]
   if not mult[p].has_key(N): mult[p][N]=0
   mult[p][N]+=1
 return mult
hruns={}
def compareRuns(runs=[]):
 # runs = [2307,2357,2359,2360,2361,2365,2366,2395,2396]
 # runs = [2200,2201,2202,2203,2205,2206,2207,2208,2276]
 eventStats = {}
 noField = [2199,2200,2201]
 intermediateField = [2383,2388,2389,2390,2392,2395,2396]
 noTracks = [2334, 2335, 2336, 2337, 2345, 2389,2390]
 ROOT.gStyle.SetPalette(ROOT.kGreenPink)
 if len(runs)==0:
  keyword = 'RUN_8000_2'
  temp = os.listdir('.')
  for x in temp:
   if x.find(keyword)<0: continue
   if not os.path.isdir(x): continue
   r = int(x[x.rfind('/')+1:].split('_')[2])
   if r in noField: continue
   if not hruns.has_key(r): 
    runs.append(r)
    hruns[r]={}
    f = ROOT.TFile(x+'/momDistributions.root')
    print "opening run",x
    hruns[r]['Trscalers'] = f.GetKey('Trscalers').ReadObj().Clone()
    hruns[r]['Trscalers'].SetDirectory(ROOT.gROOT)
    hname = 'p/pt'
    hruns[r][hname] = f.GetKey(hname).ReadObj().Clone()
    hruns[r][hname].SetDirectory(ROOT.gROOT)
    hname = 'p/ptmu'
    hruns[r][hname] = f.GetKey(hname).ReadObj().Clone()
    hruns[r][hname].SetDirectory(ROOT.gROOT)
    hnamex = 'p/pt_x'+str(r)
    hruns[r][hnamex] = hruns[r][hname].ProjectionX(hnamex)
    hruns[r][hnamex].SetDirectory(ROOT.gROOT)
 else:
  for r in runs:
   if not hruns.has_key(r): 
    hruns[r]={}
    ut.readHists(hruns[r],'momDistributions_RUN_8000_'+str(r)+'.root')
 runs.sort()
 first = True
 j=0
 if not h.has_key('RunComparison'): 
   ut.bookCanvas(h,key='RunComparison',title='Momentum',nx=1600,ny=1200,cx=1,cy=0)
   ut.bookCanvas(h,key='EventStatistics',title='Event Statistics',nx=800,ny=600,cx=1,cy=0)
   ut.bookHist(h,'HEventStatistics','Event Statistics;run number',100,2000,3000)
 h['legRunComparison']=ROOT.TLegend(0.42,0.54,0.88,0.86)
 tc = h['RunComparison'].cd(1)
 tc.SetLogy(1)
 for r in runs:
  first = False
  hname = 'p/pt_x'+str(r)
  N = hruns[r]['Trscalers'].GetBinContent(1)
  print ">>>>>>   statistics for RUN",r
  print "number of events",hruns[r]['Trscalers'].GetBinContent(1)
  print "events with tracks %5.2F%%"%(hruns[r]['Trscalers'].GetBinContent(2)/hruns[r]['Trscalers'].GetBinContent(1)*100)
  print "tracks/event                     %5.2F%%"%(hruns[r]['Trscalers'].GetBinContent(3)/hruns[r]['Trscalers'].GetBinContent(1)*100)
  print "ratio of muon tagged tracks / all tracks %5.2F%%"%(hruns[r]['p/ptmu'].GetEntries()/(hruns[r]['p/pt'].GetEntries()+1E-6))
  print "mean p %5.2F GeV/c, rms %5.2F GeV/c"%(hruns[r][hname].GetMean(),hruns[r][hname].GetRMS())
  eventStats[r]=[hruns[r]['Trscalers'].GetBinContent(2)/hruns[r]['Trscalers'].GetBinContent(1),
                 hruns[r]['Trscalers'].GetBinContent(3)/hruns[r]['Trscalers'].GetBinContent(1),
                 hruns[r][hname].GetMean(),
                 hruns[r]['Trscalers'].GetBinContent(2),
                 hruns[r]['p/ptmu'].GetEntries()/(hruns[r]['p/pt'].GetEntries()+1E-6)]
  hruns[r][hname].Scale(1/N)
  hruns[r][hname].SetLineWidth(3)
  hruns[r][hname].SetStats(0)
  hruns[r][hname].SetTitle(str(r))
  if first:  
      hruns[r][hname].Draw('PLC PMC')
      first = False
  else:  hruns[r][hname].Draw('same PLC PMC')
  h['legRunComparison'].AddEntry(hruns[r][hname],str(r),'PL')
  j+=1
 tc.BuildLegend()
 tc = h['EventStatistics'].cd(1)
 h['eventStats1']=ROOT.TGraph(len(eventStats))
 h['eventStats2']=ROOT.TGraph(len(eventStats))
 h['eventStats3']=ROOT.TGraph(len(eventStats))
 h['eventStats4']=ROOT.TGraph(len(eventStats))
 n=0
 for r in eventStats:
   h['eventStats1'].SetPoint(n,r,eventStats[r][0])
   h['eventStats2'].SetPoint(n,r,eventStats[r][1])
   h['eventStats3'].SetPoint(n,r,eventStats[r][2]/100.)
   h['eventStats4'].SetPoint(n,r,eventStats[r][4]/5.)
   n+=1

 h['legruns']=ROOT.TLegend(0.29,0.18,0.76,0.36)
 h['eventStats1'].SetMarkerColor(ROOT.kBlue)
 h['eventStats1'].SetMarkerSize(1)
 h['eventStats1'].SetMarkerStyle(21)
 h['eventStats2'].SetMarkerColor(ROOT.kBlue-4)
 h['eventStats2'].SetMarkerSize(1)
 h['eventStats2'].SetMarkerStyle(22)
 h['eventStats3'].SetMarkerColor(ROOT.kRed)
 h['eventStats3'].SetMarkerSize(1)
 h['eventStats3'].SetMarkerStyle(28)
 h['eventStats4'].SetMarkerColor(ROOT.kMagenta)
 h['eventStats4'].SetMarkerSize(1)
 h['eventStats4'].SetMarkerStyle(29)
 h['eventStats1'].SetTitle('Run statistics  Data Quality')
 h['eventStats1'].SetMinimum(-0.01)
 h['eventStats1'].SetMaximum(0.3)
 h['eventStats1'].Draw('AP')
 h['legruns'].AddEntry(h['eventStats1'],'N events with tracks / N events','PL')
 h['legruns'].AddEntry(h['eventStats2'],'N of tracks / N events','PL')
 h['legruns'].AddEntry(h['eventStats3'],'mean momentum GeV *100','PL')
 h['legruns'].AddEntry(h['eventStats4'],'N of mu tracks / N of tracks *5','PL')
 h['eventStats2'].SetMarkerColor(3)
 h['eventStats2'].Draw('P')
 h['eventStats3'].Draw('P')
 h['eventStats4'].Draw('P')
 h['legruns'].Draw('same')
 return eventStats

def mergeGoodRuns(excludeRPC=False,path='.'):
 #path = '/media/truf/disk2/home/truf/ShipSoft/ship-ubuntu-1710-64'
 noField           = [2199,2200,2201]
 intermediateField = [2383,2388,2389,2390,2392,2395,2396]
 noTracks          = [2334, 2335, 2336, 2337, 2345, 2389, 2390]
 RPCbad = [2144,2154,2183,2192,2210,2211,2217,2218,2235,2236,2237,2240,2241,2243,2291,2345,2359]
 badRuns = [2142, 2143, 2144, 2149]
 keyword = 'RUN_8000_2'
 temp = os.listdir(path)
 cmd = 'hadd -f momDistributions.root '
 for x in temp:
  if x.find(keyword)<0: continue
  if not os.path.isdir(path+'/'+x): continue
  r = int(x[x.rfind('/')+1:].split('_')[2])
  if r in badRuns or r in noTracks or r in intermediateField or r in noField : continue
  if excludeRPC and (r in RPCbad or (r>2198 and r < 2275)) : continue
  cmd += path+'/'+x+'/momDistributions.root '
 os.system(cmd)

def fcn(npar, gin, f, par, iflag):
#calculate chisquare
   x='mu'
   chisq  = 0
   dataMC     = abs(par[0])
   charmMbias = abs(par[1])
   for proj in ['p/Abspx_y'+x,'p/pt'+x+'_x']:
    for n in range(1, h[proj].GetNbinsX()+1 ):
     if proj == 'p/pt'+x+'_x' and h[proj].GetBinCenter(n)<5: continue
     delta = h[proj].GetBinContent(n) - dataMC*(hMC[proj].GetBinContent(n)+charmMbias*hCharm[proj].GetBinContent(n))
     errSq = h[proj].GetBinContent(n) + dataMC**2*hMC[proj].GetBinContent(n)+\
             (dataMC*charmMbias)**2*hCharm[proj].GetBinContent(n)
     if errSq>0: chisq += delta**2/errSq
   f[0] = chisq
   if iflag !=2: print par[0],par[1],chisq
   return
def doFit(p0=5.7,p1=0.17):
# prepare histos
 x='mu'
 pMin = 5.
 for a in ['p/pt','p/px']:
  for H in [h,hMC,hCharm]:
    H[a+'_x'+x] = H[a+x].ProjectionX(a+'_x'+x)
 a = 'p/Abspx'
 for H in [h,hMC,hCharm]:
    H[a+'_y'+x] = H[a+x].ProjectionY(a+'_y'+x,h[a+'_x'+x].FindBin(pMin),h[a+'_x'+x].GetNbinsX())
 npar = 2
 gMinuit = ROOT.TMinuit(npar)
 gMinuit.SetMaxIterations(100000)
 gMinuit.SetFCN(fcn)
 vstart  = array('d',[p0,p1])
 step    = array('d',[2.,2.])
 ierflg  = ROOT.Long(0)
 name = [ROOT.TString("dataMC"),ROOT.TString("charmMbias")]
 for i in range(npar): gMinuit.mnparm(i, name[i], vstart[i], step[i], 0.,0.,ierflg)
 #gMinuit.FixParameter(0)
 gMinuit.mnexcm("SIMPLEX",vstart,npar,ierflg)
 gMinuit.mnexcm("MIGRAD",vstart,npar,ierflg)
 pot = ROOT.Double()
 charmNorm = ROOT.Double()
 e = ROOT.Double()
 gMinuit.GetParameter(0,pot,e)
 gMinuit.GetParameter(1,charmNorm,e)
 print "RESULT:",abs(pot), abs(charmNorm)
 MCcomparison(abs(pot), pMin,1.0,abs(charmNorm))
def doFitByHand():
 p0min = 1.
 p0max = 10.
 p1min = 0.1
 p1max = 5.
 N = 100
 chi2Max = 1E10
 pChi2Min = [1.,1.]
 for p0 in numpy.linspace(p0min,p0max,N):
  for p1  in numpy.linspace(p1min,p1max,N):
   p=[p0,p1]
   chi2=[0]
   fcn(2,0,chi2,p,2)
   if chi2[0]<chi2Max:
    pChi2Min = [p0,p1]
    chi2Max=chi2[0]
 print chi2Max,pChi2Min
def additionalMomSmearing():
  hname = 'MCp/pt_x'
  folname = 'S'+hname
# true resolution: sigma = [0.36/100.,0.036/100.]
  fudge = 2.
  sigma = [0.36/100.*fudge,0.036/100.*fudge]
  h[folname]=h[hname].Clone(folname)
  h[folname].Reset()
  for n in range(1,h[hname].GetNbinsX()+1):
    P = h[hname].GetBinCenter(n)
    N = h[hname].GetBinContent(n)
    sig = (sigma[0]+P*sigma[1])*P
    for n in range(int(N+0.5)):
      p = rnr.Gaus(P,sig)
      rc = h[folname].Fill(p)
  ut.makeIntegralDistrib(h,hname)
  h[hname].Draw()
  h[folname].SetLineColor(ROOT.kBlue)
  h[folname].Draw('same')

def copyRTRelation():
 f       = sTree.GetCurrentFile()
 fname   = f.GetName()
 rawName = fname.replace('_RT.root','.root')
 ftemp   = fname.replace('_RT.root','_RTx.root')
 os.system('cp '+rawName +' '+ftemp)
 h['TDCMapsX'] = f.histos.Get('TDCMapsX').Clone('TDCMapsX')
 h['hitMapsX'] = f.histos.Get('hitMapsX').Clone('hitMapsX')
 h['RTrelations'] = f.histos.Get('RTrelations').Clone('RTrelations')
 h['TDC2R_py'] = f.histos.Get('TDC2R_py').Clone('TDC2R_py')
 f.Close()
 f = ROOT.TFile.Open(ftemp,'update')
 event = f.Get("cbmsim")
 if not event:
     print "Problem with making RTrel persistent, file",f,f.ls()
     return -1
 f.cd('')
 f.mkdir('RT')
 f.cd('RT')
 for s in RTrelations[fname]:
     if s.find('rt')<0: continue
     RTrelations[fname][s].Write()
 pkl = Pickler(f)
 pkl.dump(h['tMinAndTmax'],'tMinAndTmax')
 f.cd('')
 f.mkdir('histos')
 f.histos.cd('')
 h['TDCMapsX'].Write()
 h['hitMapsX'].Write()
 h["RTrelations"].Write()
 f.Write("",ROOT.TFile.kOverwrite)
 f.Close()
def recoStep0():
  global withTDC
  withTDC = False
  disableBranches()
  withMaterial = False
  materialEffects(False)
  plotBiasedResiduals(PR=1)
  makeRTrelations()
  RTrelations =  {'tMinAndTmax':h['tMinAndTmax']}
  for s in h['tMinAndTmax']: RTrelations['rt'+s] = h['rt'+s]
  makeRTrelPersistent(RTrelations)
def recoStep1(PR=11):
# make fitted tracks  
  #disableBranches()
  global MCdata
  fGenFitArray = ROOT.TClonesArray("genfit::Track") 
  fGenFitArray.BypassStreamer(ROOT.kTRUE)
  fitTracks   = sTree.Branch("FitTracks", fGenFitArray,32000,-1)
  fTrackInfoArray = ROOT.TClonesArray("TrackInfo")
  fTrackInfoArray.BypassStreamer(ROOT.kTRUE)
  TrackInfos      = sTree.Branch("TrackInfos", fTrackInfoArray,32000,-1)
  fRPCTrackArray = {'X':ROOT.TClonesArray("RPCTrack"),'Y':ROOT.TClonesArray("RPCTrack")}
  RPCTrackbranch = {}
  for x in fRPCTrackArray: 
   fRPCTrackArray[x].BypassStreamer(ROOT.kTRUE)
   RPCTrackbranch[x] = sTree.Branch("RPCTrack"+x, fRPCTrackArray[x],32000,-1)
  if sTree.GetBranch('MCTrack'): MCdata = True

  for n in range(sTree.GetEntries()):
    if n%10000==0: print "Now at event",n,"of",sTree.GetEntries(),sTree.GetCurrentFile().GetName(),time.ctime()
    rc = sTree.GetEvent(n)
    fGenFitArray.Clear()
    fTrackInfoArray.Clear()
    for x in ['X','Y']: fRPCTrackArray[x].Clear()
    if PR==3: theTracks = bestTracks()
    else: theTracks = findTracks(PR)
    for aTrack in theTracks:
     nTrack   = fGenFitArray.GetEntries()
     fTrackInfoArray[nTrack] = ROOT.TrackInfo(aTrack)
     aTrack.prune("CFL") # aTrack.prune("CURM")  # FL keep first and last point only, C deleteTrackRep, W deleteRawMeasurements, I U R M
     fGenFitArray[nTrack] = aTrack
    RPCclusters, RPCtracks = muonTaggerClustering(PR=11)
    for x in ['X','Y']:
     for aTrack in RPCtracks[x]:
      nTrack   = fRPCTrackArray[x].GetEntries()
      try:
       fRPCTrackArray[x][nTrack] = ROOT.RPCTrack(aTrack[0],aTrack[1])
      except:
       print nTrack,x,aTrack
     RPCTrackbranch[x].Fill()
    fitTracks.Fill()
    TrackInfos.Fill()
    for aTrack in theTracks: aTrack.Delete()
  sTree.Write()
  makeAlignmentConstantsPersistent()
  ftemp=sTree.GetCurrentFile()
  ftemp.Write("",ROOT.TFile.kOverwrite)
  ftemp.Close()
  print "finished adding fitted tracks",options.listOfFiles
  print "make suicid"
  os.system('kill '+str(os.getpid()))
def recoMuonTaggerTracks():
  global MCdata
  global sTree
  if sTree.GetBranch('MCTrack'): MCdata = True
  fname = sTree.GetCurrentFile().GetName()
  if sTree.GetBranch("RPCTrackX"):
    print "remove RECO branch and rerun muonTagger reconstruction"
    os.system('cp '+fname+' '+fname.replace('.root','orig.root')) # make backup
    for br in ['RPCTrackX','RPCTrackY']:
     b = sTree.GetBranch(br)
     sTree.GetListOfBranches().Remove(b)
     l = sTree.GetLeaf(br)
     sTree.GetListOfLeaves().Remove(l)
     sTree.Write()
    fn = sTree.GetCurrentFile().GetName()
    f  = ROOT.TFile(fn,'update')
    sTree = f.cbmsim
  fRPCTrackArray = {'X':ROOT.TClonesArray("RPCTrack"),'Y':ROOT.TClonesArray("RPCTrack")}
  RPCTrackbranch = {}
  for x in fRPCTrackArray: 
   fRPCTrackArray[x].BypassStreamer(ROOT.kTRUE)
   RPCTrackbranch[x] = sTree.Branch("RPCTrack"+x, fRPCTrackArray[x],32000,-1)
  for n in range(sTree.GetEntries()):
    if n%10000==0: print "Now at event",n,"of",sTree.GetEntries(),sTree.GetCurrentFile().GetName(),time.ctime()
    rc = sTree.GetEvent(n)
    for x in ['X','Y']: fRPCTrackArray[x].Clear()
    if MCdata: 
      if sTree.FitTracks.GetEntries()==0:
       for x in ['X','Y']: RPCTrackbranch[x].Fill()
       continue
    RPCclusters, RPCtracks = muonTaggerClustering(PR=11)
    for x in ['X','Y']:
     for aTrack in RPCtracks[x]:
      nTrack   = fRPCTrackArray[x].GetEntries()
      try:
       fRPCTrackArray[x][nTrack] = ROOT.RPCTrack(aTrack[0],aTrack[1])
      except:
       print nTrack,x,aTrack
     RPCTrackbranch[x].Fill()
  sTree.Write()
  ftemp = sTree.GetCurrentFile()
  ftemp.Write("",ROOT.TFile.kOverwrite)
  ftemp.Close()
  ftest = ROOT.TFile(fname)
  OK = False
  if ftest.GetKey('cbmsim'):
   sTree = ftest.cbmsim
   check = sTree.GetBranch('RPCTrackY').GetZipBytes()
   check += sTree.GetBranch('RPCTrackY').GetZipBytes()
   if check/float(sTree.GetBranch('FitTracks').GetZipBytes())>0.003: OK = True
  if not OK:
   print "muon track reco failed, reinstall original file"
   os.system('mv '+fname.replace('.root','orig.root')+' '+fname)
  else:
   os.system('rm '+fname.replace('.root','orig.root'))
   print "finished adding muonTagger tracks",options.listOfFiles
  print "make suicid"
  os.system('kill '+str(os.getpid()))
def anaResiduals():
  if not sTree.GetBranch('FitTracks'):
    print "this file has no tracks",sTree.GetCurrentFile().GetName()
  else:
   muflux_Reco.trackKinematics(3.)
   if MCdata:
      MCchecks()
   else:
      printScalers()
   plotRPCExtrap(PR=1)
   norm = h['TrackMult'].GetEntries()
   print '*** Track Stats ***',norm
   ut.writeHists(h,'histos-analysis-'+rname)
if options.command == "":
 print "existing methods"
 print " --- plotHitMaps(): hitmaps / layer, TDC / layer, together with list of noisy channels"
 print " --- plotEvent(n) : very basic event display, just x hits in x/z projection " 
 print " --- plotRPCHitmap() : basic plots for RPC "
 print " --- momentum plot and track fitting tests:"
 print " ---     fitTracks(100) and fitTracks(100,True,True) with simple Display and 3d display of tracks with detector, low occupancy events"
 print " --- testClusters(nstart,nevents), clustering of hits and pattern recognition followed by track fit"
 print " --- plotBiasedResiduals(nstart,nevents), fit tracks in low occupancy events and plot residuals, plot2dResiduals() for display del vs x, del vs y"
 print " --- plotLinearResiduals(), to be used for zero field"
 print " --- plotRPCExtrap(nstart,nevents), extrapolate track to RPC hits"
 print " --- printScalers()"
 print " --- init(): outdated! do boostrapping, determine RT relation using fitted tracks, do plotBiasedResiduals and plotRPCExtrap with TDC"
 print " --- momResolution(), with MC data"

 vetoLayer = []
 database='muflux_RTrelations.pkl'
 if sTree.GetBranch('MCTrack'):
    print "MC data identified"
    MCdata=True
 elif sTree.GetCurrentFile().GetKey('RT'):
  importRTrel()
 elif os.path.exists(database):
   RTrelations = pickle.load(open(database))
   if not RTrelations.has_key(rname):
    print "You should run init() to determine the RT relations or use _RT file"
   else:
    h['tMinAndTmax'] = RTrelations[rname]['tMinAndTmax']
    for s in h['tMinAndTmax']: h['rt'+s] = RTrelations[rname]['rt'+s]
 withCorrections = False
 importAlignmentConstants()
#
if options.command == "recoStep0":
  withTDC=False
  print "make clean TDC distributions"
  importAlignmentConstants()
  recoStep0()
  print "finished making RT relations"
elif options.command == "recoStep1":
  if sTree.GetBranch('MCTrack'):
   MCdata = True
   withDefaultAlignment = True
   sigma_spatial = 0.25
   withCorrections = False
   # DTEfficiencyFudgefactor(method=0)
  else:
   importRTrel()
   withDefaultAlignment = False
   sigma_spatial = 0.25
   withCorrections = True  
  print "add fitted tracks"
  importAlignmentConstants()
  recoStep1(PR=11)
elif options.command == "anaResiduals":
  ROOT.gROOT.SetBatch(True)
  if sTree.GetEntries()>0:
   if sTree.GetBranch('MCTrack'):
    MCdata = True
    # DTEfficiencyFudgefactor(method=0)
   if not MCdata: importRTrel()
   withCorrections = False
   importAlignmentConstants()
   anaResiduals()
   print "finished with analysis step",options.listOfFiles
  else: print "no events, exit"
elif options.command == "alignment":
  ROOT.gROOT.SetBatch(True)
  if sTree.GetBranch('MCTrack'):
   MCdata = True
   withDefaultAlignment = True
   sigma_spatial = 0.25
   withCorrections = False
  else:
   importRTrel()
   withDefaultAlignment = False
   sigma_spatial = 0.25
   withCorrections = True   
  h['hitMapsX'] = 1
  importAlignmentConstants()
  plotBiasedResiduals(PR=11,minP=10)
  ut.writeHists(h,'histos-residuals-'+rname)
  hitMapsFromFittedTracks()
elif options.command == "plotResiduals":
  print "reading histograms with residuals"
  ut.readHists(h,options.listOfFiles)
  plotBiasedResiduals(onlyPlotting=True)
  if h.has_key('RPCResY_10'):
   plotRPCExtrap(onlyPlotting=True)
elif options.command == "recoMuonTaggerTracks":
  importAlignmentConstants()
  recoMuonTaggerTracks()
elif options.command == "momResolution":
  MCdata = True
  withDefaultAlignment = True
  sigma_spatial = 0.25
  withCorrections = False
  importAlignmentConstants()
  momResolution(PR=1,onlyPlotting=False)
elif options.command == "splitOffBoostedEvents": splitOffBoostedEvents()
elif options.command == "plotDTPoints":   plotDTPoints()
elif options.command == "DTeffWithRPCTracks":
  withCorrections = False
  importAlignmentConstants()
  DTeffWithRPCTracks()
elif options.command == "hitMapsFromFittedTracks":
 hitMapsFromFittedTracks()
elif options.command == "test":
 yep.start('output.prof')
 for x in sTree.GetListOfBranches(): sTree.SetBranchStatus(x.GetName(),0)
 # sTree.SetBranchStatus('RPCTrackY',1)
 sTree.SetBranchStatus('FitTracks',1)
 for n in range(50000):
   rc=sTree.GetEvent(n)
 yep.stop()
 print "finished"
#alignConstants.pop('strawPositions') # if recorded alignment constants should not be used.
