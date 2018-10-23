import ROOT,os,sys,operator
from decorators import *
import __builtin__ as builtin
ROOT.gStyle.SetPalette(ROOT.kDarkBodyRadiator)
PDG = ROOT.TDatabasePDG.Instance()
# -----Timer--------------------------------------------------------
timer = ROOT.TStopwatch()
# stop printing errors
ROOT.gErrorIgnoreLevel = ROOT.kBreak
from argparse import ArgumentParser
import shipunit as u
import rootUtils as ut
from array import array

vbot = ROOT.TVector3()
vtop = ROOT.TVector3()
h={}
debug = False

parser = ArgumentParser()
parser.add_argument("-f", "--files", dest="listOfFiles", help="list of files comma separated", required=True)
parser.add_argument("-c", "--cmd", dest="command", help="command to execute", default="")
parser.add_argument("-d", "--Display", dest="withDisplay", help="detector display", default=True)
parser.add_argument("-e", "--eos", dest="onEOS", help="files on EOS", default=False)
parser.add_argument("-u", "--update", dest="updateFile", help="update file", default=False)

options = parser.parse_args()

fnames = options.listOfFiles.split(',')
fname = fnames[0]
if options.updateFile:
 f=ROOT.TFile(fname,'update')
 sTree=f.cbmsim
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
sTree.SetMaxVirtualSize(300000000)

from ShipGeoConfig import ConfigRegistry
ShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/charm-geometry_config.py")
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
   statnb,vnb,pnb,lnb,view = stationInfo(test)
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

h['dispTrack3D']=[]
h['dispTrack']=[]
h['dispTrackY']=[]

withTDC = True

import time
def printEventsWithDTandRPC(nstart=0):
 for n in range(nstart,sTree.GetEntries()):
  rc = sTree.GetEvent(n)
  if sTree.Digi_MufluxSpectrometerHits.GetEntries()*sTree.Digi_MuonTaggerHits.GetEntries()>0:
   print "Event number:",n
   plotEvent(n)
   next = raw_input("Next (Ret/Quit): ")         
   if next<>'':  break
h['hitCollection']={}

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
    statnb,vnb,pnb,lnb,view = stationInfo(hit)
    nr = hit.GetDetectorID()%100
    y = 2*pnb+lnb+(statnb-1)*16
    if view=='_u': y+=8
    if view=='_x' and statnb>1: y+=8
    h['upstreamG'].SetPoint(n,nr,y)
    n+=1
 tc = h['layerDisplay'].cd(1)
 h['upstream'].Draw()
 h['upstreamG'].Draw('sameP')

def plotEvent(n):
   h['dispTrack']=[]
   h['dispTrack3D']=[]
   h['dispTrackY']=[]
   rc = sTree.GetEvent(n)
   h['hitCollection']= {'upstream':[0,ROOT.TGraph()],'downstream':[0,ROOT.TGraph()],'muonTaggerX':[0,ROOT.TGraph()],'muonTaggerY':[0,ROOT.TGraph()]}
   h['stereoHits'] = []
   for c in h['hitCollection']: rc=h['hitCollection'][c][1].SetName(c)
   for c in h['hitCollection']: rc=h['hitCollection'][c][1].Set(0)
   ut.bookHist(h,'xz','x (y) vs z',500,0.,1200.,100,-150.,150.)
   if not h.has_key('simpleDisplay'): ut.bookCanvas(h,key='simpleDisplay',title='simple event display',nx=1600,ny=1200,cx=1,cy=0)
   rc = h[ 'simpleDisplay'].cd(1)
   h['xz'].SetMarkerStyle(30)
   h['xz'].SetStats(0)
   h['xz'].Draw('b')
   for hit in sTree.Digi_MufluxSpectrometerHits:
    statnb,vnb,pnb,lnb,view = stationInfo(hit)
    # print statnb,vnb,pnb,lnb,view,hit.GetDetectorID()
    vbot,vtop = correctAlignment(hit)
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
     vtop,vbot = correctAlignmentRPC(hit,view)
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

def stationInfo(hit):
 # 10112012
 # first digit = station number, second digit v, third and fourth layer
 detid = hit.GetDetectorID()
 statnb = detid/10000000; 
 vnb =  (detid - statnb*10000000)/1000000
 pnb =  (detid - statnb*10000000 - vnb*1000000)/100000
 lnb =  (detid - statnb*10000000 - vnb*1000000 - pnb*100000)/10000
 view = "_x"
 if vnb==0 and statnb==2: view = "_v"
 if vnb==1 and statnb==1: view = "_u"
 if pnb>1:
   print "something wrong with detector id",detid
   pnb = 0
 return statnb,vnb,pnb,lnb,view

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
    ut.bookHist(h,str(1000*s+100*p+10*l)+view,'hit map station'+str(s)+' plane'+str(p)+' layer '+str(l)+view,50,-0.5,49.5)
    ut.bookHist(h,"TDC"+str(1000*s+100*p+10*l)+view,'TDC station'+str(s)+' plane'+str(p)+' layer '+str(l)+view,1250,-500.,2000.)
    xLayers[s][p][l][view]=h[str(1000*s+100*p+10*l)+view]
    channels[s][p][l][view]=12
    if s>2: channels[s][p][l][view]=48
ut.bookHist(h,'T0tmp','T0 temp',1250,-500.,2000.)
ut.bookHist(h,'T0','T0',1250,-500.,2000.)

noiseThreshold=10
noisyChannels=[30112016, 40012005, 40012007, 40012008, 40112031, 40112032]

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

def sortHits(event):
 spectrHitsSorted = {'_x':{1:[],2:[],3:[],4:[]},'_u':{1:[],2:[],3:[],4:[]},'_v':{1:[],2:[],3:[],4:[]}}
 for hit in event.Digi_MufluxSpectrometerHits:
   statnb,vnb,pnb,lnb,view = stationInfo(hit)
   spectrHitsSorted[view][statnb].append(hit)
 return spectrHitsSorted

def plotHitMaps():
 noisyChannels=[]
 for event in sTree:
  for hit in event.Digi_MufluxSpectrometerHits:
   s,v,p,l,view = stationInfo(hit)
   rc = xLayers[s][p][l][view].Fill(hit.GetDetectorID()%1000)
   if hit.GetDetectorID() not in noisyChannels:
    t0 = 0
    if hasattr(sTree,'MCTrack'): t0 = sTree.ShipEventHeader.GetEventTime()
    rc = h['TDC'+xLayers[s][p][l][view].GetName()].Fill(hit.GetDigi()-t0)
   channel = 'TDC'+str(hit.GetDetectorID())
   if not h.has_key(channel): h[channel]=h['TDC'+xLayers[s][p][l][view].GetName()].Clone(channel)
   rc = h[channel].Fill(hit.GetDigi()-t0)
  if not h.has_key('hitMapsX'): ut.bookCanvas(h,key='hitMapsX',title='Hit Maps All Layers',nx=1600,ny=1200,cx=4,cy=6)
  if not h.has_key('TDCMapsX'): ut.bookCanvas(h,key='TDCMapsX',title='TDC Maps All Layers',nx=1600,ny=1200,cx=4,cy=6)
 j=0
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
     tp = h['TDCMapsX'].cd(j)
     tp.SetLogy(1)
     h['TDC'+xLayers[s][p][l][view].GetName()].Draw()
     mean = xLayers[s][p][l][view].GetEntries()/channels[s][p][l][view]
     for i in range(1,int(xLayers[s][p][l][view].GetEntries())+1):
      if xLayers[s][p][l][view].GetBinContent(i) > noiseThreshold * mean:
        print "noisy channel:",s,p,l,view,xLayers[s][p][l][view].GetBinContent(i) , noiseThreshold , mean
        v = 0
        if s==2 and view == "_x": v = 1
        if s==1 and view == "_u": v = 1
        myDetID = s * 10000000 + v * 1000000 + p * 100000 + l*10000
        channel = myDetID+i-1 + 2000
        if not channel in noisyChannels: noisyChannels.append(myDetID+i-1)
 print "list of noisy channels"
 for n in noisyChannels: print n

def sumStations():
 h['TDC_12']= h['TDC1000_x'].Clone('TDC_12')
 h['TDC_12'].SetTitle('TDC station 1 and 2 all layers')
 h['TDC_12'].Reset()
 for s in range(1,3):
  for p in range(2):
   for l in range(2):
    for view in ['_x','_u','_v']:
     h['TDC_12'].Add(h["TDC"+str(1000*s+100*p+10*l)+view])
 h['TDC_34']= h['TDC3000_x'].Clone('TDC_34')
 h['TDC_34'].SetTitle('TDC station 3 and 4 all layers')
 h['TDC_34'].Reset()
 for s in range(3,5):
  for p in range(2):
   for l in range(2):
    if s==4 and p==0 and l==1 or s==4 and p==1 and l==1: continue 
    for view in ['_x']:
     h['TDC_34'].Add(h["TDC"+str(1000*s+100*p+10*l)+view])



def printScalers():
   ut.bookHist(h,'integratedrate','rate integrated',100,-0.5,99.5)
   ut.bookHist(h,'rate','rate',100,-0.5,99.5)
   if not h.has_key('rates'): ut.bookCanvas(h,key='rates',title='Rates',nx=800,ny=400,cx=2,cy=1)
   rc = h['rates'].cd(1)
   scalers = f.scalers
   if not scalers:
     print "no scalers in this file"
     return
   scalers.GetEntry(0)
   for x in scalers.GetListOfBranches():
    name = x.GetName()
    s = eval('scalers.'+name)
    if name!='slices': print "%20s :%8i"%(name,s)
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
ut.bookHist(h,'magPos','XY at goliath, PR',100,-50.,50.,100,-50.,50.)
for dets in ['34','stereo12','y12']: ut.bookHist(h,'tracklets'+dets,'hits per view',10,-0.5,9.5)
def zCentre():
 ut.bookHist(h,'xs','x vs z',500,0.,800.,100,-150.,150.)
 ut.bookHist(h,'xss','x vs station',4,0.5,4.5,100,-150.,150.)
 ut.bookHist(h,'wss','wire vs station',4,0.5,4.5,100, -0.5,99.5)
 ut.bookHist(h,'center','z crossing',500,0.,500.)
 ut.bookHist(h,'delzCentrT3','extr to T3',100,-100.,100.)
 ut.bookHist(h,'delT2','extr to T2',100,-100.,100.)
 ut.bookHist(h,'delT1','extr to T1',100,-100.,100.)
 for event in sTree:
  spectrHitsSorted = sortHits(event)
  X = {1:0,2:0,3:0,4:0}
  Z = {1:0,2:0,3:0,4:0}
  nH  = {1:0,2:0,3:0,4:0}
  passed = True
  for s in range(1,5):
   for hit in spectrHitsSorted['_x'][s]:
     rc = hit.MufluxSpectrometerEndPoints(vbot,vtop)
     rc = h['xs'].Fill( (vbot[2]+vtop[2])/2.,(vbot[0]+vtop[0])/2.)
     rc = h['xss'].Fill( s,(vbot[0]+vtop[0])/2.)
     wire = hit.GetDetectorID()%1000
     rc = h['wss'].Fill(s,wire)
     if hit.GetDetectorID() in noisyChannels:
       continue  
     X[s]+=(vbot[0]+vtop[0])/2.
     Z[s]+=(vbot[2]+vtop[2])/2.
     nH[s]+=1
   if nH[s]<3 or nH[s]>6: passed = False
   if not passed: break
   Z[s]=Z[s]/float(nH[s])
   X[s]=X[s]/float(nH[s])
  if not passed: continue
  slopeA = (X[2]-X[1])/(Z[2]-Z[1])
  slopeB = (X[4]-X[3])/(Z[4]-Z[3])
  bA = X[1]-slopeA*Z[1]
  bB = X[3]-slopeB*Z[3]
  zC = (bB-bA)/(slopeA-slopeB+1E-10)
  rc = h['center'].Fill(zC)
  x1 = zgoliath*slopeA+bA
  x2 = zgoliath*slopeB+bB
  rc = h['delx'].Fill(x2-x1)
  rc = h['delT3'].Fill( slopeA*Z[3]+bA-X[3])
  delT1 = slopeB*Z[1]+bB-X[1]
  rc = h['delT1'].Fill( delT1 )
  if delT1 > -20 and delT1 < 10:
   delT2 = slopeB*Z[2]+bB-X[2]
   rc = h['delT2'].Fill( delT2 )
   #if delT2<-18 and delT2>-22 or delT2<38 and delT2> 30:
   #  txt = ''
   #  for hit in spectrHitsSorted['_x'][2]: txt+=str(hit.GetDetectorID())+" "
   #  print delT2,  txt
  
 if not h.has_key('magnetX'): ut.bookCanvas(h,key='magnetX',title='Tracks crossing at magnet',nx=1600,ny=600,cx=3,cy=2)
 h['magnetX'].cd(1)
 h['delx'].Draw()
 h['magnetX'].cd(2)
 h['center'].Draw()
 h['magnetX'].cd(4)
 h['delT3'].Draw()
 h['magnetX'].cd(5)
 h['delT1'].Draw()
 h['magnetX'].cd(6)
 h['delT2'].Draw()

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

from array import array

gMan  = ROOT.gGeoManager
geoMat =  ROOT.genfit.TGeoMaterialInterface()
#
bfield = ROOT.genfit.FairShipFields()
fM = ROOT.genfit.FieldManager.getInstance()
fM.init(bfield)
ROOT.genfit.MaterialEffects.getInstance().init(geoMat)
#ROOT.genfit.MaterialEffects.getInstance().setNoEffects()
fitter = ROOT.genfit.DAF()
fitter.setMaxIterations(50)
# fitter.setDebugLvl(1) # produces lot of printout

def extractMinAndMax():
 h['tMinAndTmax']={}
 for j in range(1,4*6+1):
  p = h['TDCMapsX'].cd(j)
  p.Update()
  for x in p.GetListOfPrimitives():
   if x.InheritsFrom("TH1"): break
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
  h[x.GetName()+'tMin'] = line = ROOT.TArrow(tmin,-5.,tmin,0.8,0.05,">")
  h[x.GetName()+'tMax'] = line = ROOT.TArrow(tmax,-5.,tmax,0.8,0.05,">")
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
   h['rt'+hname].SetPoint(n,h[hname].GetBinCenter(n), N/float(Ntot)*R)
 h['rt'+hname].SetTitle('rt'+hname)
 h['rt'+hname].SetLineWidth(2)
 if not hname.find('TDC1')<0: h['rt'+hname].SetLineColor(ROOT.kBlue)
 elif not hname.find('TDC2')<0: h['rt'+hname].SetLineColor(ROOT.kCyan)
 elif not hname.find('TDC3')<0: h['rt'+hname].SetLineColor(ROOT.kGreen)
 elif not hname.find('TDC4')<0: h['rt'+hname].SetLineColor(ROOT.kGreen+2)
 h['RTrelations'].cd(1)
 h['rt'+hname].Draw('same')

def makeRTrelations():
 if not h.has_key('RTrelations'): 
  ut.bookCanvas(h,key='RTrelations',title='RT relations',nx=800,ny=500,cx=1,cy=1)
  h['RTrelations'].cd(1)
  x = h['TDC1000_x']
  h['emptyHist'] = ROOT.TH2F('empty',' ',100,x.GetBinCenter(1),x.GetBinCenter(x.GetNbinsX()),100,0.,2.)
  h['emptyHist'].SetStats(0)
  h['emptyHist'].Draw()
  extractMinAndMax()    # this has to run after filling TDC histos from trackfit!!
 for s in range(1,5):
  for view in ['_x','_u','_v']:
   for p in range(2):
    for l in range(2):
     if not xLayers[s][p][l].has_key(view):continue
     if s>2 and view != '_x': continue
     if s==1 and view == '_v'or s==2 and view == '_u': continue
     extractRTPanda(hname= 'TDC'+xLayers[s][p][l][view].GetName())

def extractRT(xmin,xmax,hname= 'TDC1000_x',function='parabola'):
# good result with extractRT(610,1850,hname= 'TDC1000_x')
#                  extractRT(625,2000,hname= 'TDC4000_x')
#                  extractRT(610,2000,hname= 'TDC3000_x')
# 
 s = int(hname[3:4])
 binW = h[hname].GetBinWidth(2)
 tMinAndTmax = {1:[587,1860],2:[587,1860],3:[610,2300],4:[610,2100]}
 R = ShipGeo.MufluxSpectrometer.InnerTubeDiameter/2. #  = 3.63*u.cm 
 maxDriftTime = tMinAndTmax[s][1]-tMinAndTmax[s][0]
 # parabola
 if function == 'parabola':
  P2 = '( ('+str(maxDriftTime)+'-'+str(R)+'*[1] )/'+str(R)+'**2 )'
  myDnDr = ROOT.TF1('DnDr','[0]/([1]+2*(x-[2])*'+P2+')+[3]',4)
  myDnDr.SetParameter(0,h[hname].GetMaximum())
  myDnDr.SetParameter(1,1.)
  myDnDr.SetParameter(2,tMinAndTmax[s][0])
  myDnDr.ReleaseParameter(2)
 #myDnDr.FixParameter(2,tMinAndTmax[s][0])
  myDnDr.SetParameter(3,10.)
  myDnDr.FixParameter(3,0)
# Panda function
 else:
  # myDnDr = ROOT.TF1('DnDr','[0]+[1]*(1+[2]*exp(([4]-x)/[3]))',5)
  myDnDr = ROOT.TF1('DnDr','[0]+[1]*(1+[2]*exp(([4]-x)/[3]))/( (1+exp(([4]-x)/[6]))*(1+exp((x-[5])/[7])) )',8)
  myDnDr.SetParameter(0,3.9) # noise level
  myDnDr.SetParameter(1,h[hname].GetMaximum()) # normalisation
  myDnDr.SetParameter(2,1.) # shape parameters
  myDnDr.SetParameter(3,1.)
  myDnDr.SetParameter(4,tMinAndTmax[s][0]) # t0 and tmax
  myDnDr.FixParameter(5,tMinAndTmax[s][1])
  myDnDr.FixParameter(6,1E20) # slope of the leading and trailing edge
  myDnDr.FixParameter(7,1E20)
 fitResult = h[hname].Fit(myDnDr,'S','',xmin,xmax)
 rc = fitResult.Get()
 p1 = rc.GetParams()[1]
 p2 = (maxDriftTime-R*p1)/R**2
 print 'constants for ',hname,p1,p2
# cross check
 tx = R*p1+R**2*p2
 rx = (-p1 + ROOT.TMath.Sqrt( p1**2 + 4*p2*maxDriftTime) )/ ( 2*p2 )
 print maxDriftTime,R,'|',tx,rx
 # ROOT.gROOT.FindObject('c1').cd(1)

ut.bookHist(h,'TDC2R','RT relation; t [ns] ; r [cm]',100,0.,3000.,100,0.,2.)

def RT(s,t):
# rt relation, drift time to distance
  R = ShipGeo.MufluxSpectrometer.InnerTubeDiameter/2. #  = 3.63*u.cm 
  if hasattr(sTree,'MCTrack'):
   r = (t-sTree.ShipEventHeader.GetEventTime())*ShipGeo.MufluxSpectrometer.v_drift
  else:
   if t > h['tMinAndTmax']['TDC'+s][1]: r = R
   elif t< h['tMinAndTmax']['TDC'+s][0]: r = 0
   else: r = h['rtTDC'+s].Eval(t)
  h['TDC2R'].Fill(t,r)
  return r

# from TrackExtrapolateTool
parallelToZ = ROOT.TVector3(0., 0., 1.) 
def extrapolateToPlane(fT,z):
# etrapolate to a plane perpendicular to beam direction (z)
  rc,pos,mom = False,None,None
  fst = fT.getFitStatus()
  if fst.isFitConverged():
   if z > DT['Station_1_x_plane_0_layer_0_10000000'][2]-10 and z < DT['Station_4_x_plane_1_layer_1_40110000'][2] + 10:
# find closest measurement
    mClose = 0
    mZmin = 999999.
    M = min(fT.getNumPointsWithMeasurement(),30) # for unknown reason, get stuck for track with large measurements
    for m in [0,M/2,M-1]:
     # print "extr to state m",m,fT.getNumPointsWithMeasurement()
     st = fT.getFittedState(m)
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
      pass
   else:
    if z < DT['Station_1_x_plane_0_layer_0_10000000'][2]:
# use linear extrapolation from first state
     fstate = fT.getFittedState(0)
    elif z > DT['Station_4_x_plane_1_layer_1_40110000'][2]:
     fstate = fT.getFittedState(fT.getNumPointsWithMeasurement()-1)
# use linear extrap
    pos,mom = fstate.getPos(),fstate.getMom()
    lam = (z-pos[2])/mom[2]
    pos[2]=z
    pos[0]=pos[0]+lam*mom[0]
    pos[1]=pos[1]+lam*mom[1]
    rc = True 
  return rc,pos,mom

ut.bookHist(h,'p/pt','momentum vs Pt (GeV);p [GeV/c]; p_[T] [GeV/c]',400,0.,400.,100,0.,10.)
ut.bookHist(h,'chi2','chi2/nDoF',100,0.,25.)
ut.bookHist(h,'Nmeasurements','number of measurements used',25,-0.5,24.5)

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
        h['dispTrack'][nt].SetPoint(nP,pos[2],pos[0])
        h['dispTrackY'][nt].SetPoint(nP,pos[2],pos[1])
        if debug:
         bfield.get(pos[0],pos[1],pos[2],Bx,By,Bz)
         print "%5.2F %5.2F %5.2F %5.2F %5.2F %5.2F %5.2F %5.2F %5.2F "%(pos[0],pos[1],pos[2],Bx,By,Bz,mom[0],mom[1],mom[2])
        # ptkick 1.03 / dalpha
      if nP ==0:
        fitStatus = theTrack.getFitStatus()
        print "trackinfoP/Pt/chi2/DoF/Ndf:%6.2F %6.2F %6.2F %6.2F"%(mom.Mag(),mom.Pt(),fitStatus.getChi2()/fitStatus.getNdf(),fitStatus.getNdf())
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

def findSimpleEvent(event,nmin=3,nmax=6):
   spectrHitsSorted = sortHits(event)
   nH  = {1:0,2:0,3:0,4:0}
   passed = True
   for s in range(1,5):
    for hit in spectrHitsSorted['_x'][s]:  nH[s]+=1
    if nH[s]<nmin or nH[s]>nmax: passed = False
   nu = 0
   for hit in spectrHitsSorted['_u'][1]:  nu+=1
   if nu<nmin or nu>nmax: passed = False
   nv = 0
   for hit in spectrHitsSorted['_v'][2]:  nv+=1
   if nv<nmin or nv>nmax: passed = False
   return passed 

def fitTracks(nMax=-1,simpleEvents=True,withDisplay=False,nStart=0,debug=False,PR=1):
# select special clean events for testing track fit
 for n in range(nStart,sTree.GetEntries()):
   rc = sTree.GetEvent(n)
   if nMax==0: break
   if simpleEvents:
    if not findSimpleEvent(sTree): continue
   if withDisplay:
     print "event #",n
     plotEvent(n)
   theTracks = findTracks(PR)
   if withDisplay:
     for theTrack in theTracks:     displayTrack(theTrack,debug)
     next = raw_input("Next (Ret/Quit): ")         
     if next<>'':  break
   if len(theTracks)>0: nMax-=1
 momDisplay()
def momDisplay():
 if not h.has_key('mom'): ut.bookCanvas(h,key='mom',title='trackfit',nx=1200,ny=600,cx=4,cy=2)
 rc = h['mom'].cd(1)
 h['p/pt'].SetStats(0)
 rc = h['p/pt'].Draw('colz')
 rc = h['mom'].cd(2)
 rc.SetLogy(1)
 h['p/pt_x']=h['p/pt'].ProjectionX()
 h['p/pt_x'].SetName('p/pt_x')
 h['p/pt_x'].SetTitle('P [GeV/c]')
 h['p/pt_x'].Draw()
 rc = h['mom'].cd(3)
 h['p/pt_y']=h['p/pt'].ProjectionY()
 h['p/pt_y'].SetName('p/pt_x')
 h['p/pt_y'].SetTitle('Pt [GeV/c]')
 h['p/pt_y'].Draw()
 h['mom'].Update()
 stats = h['p/pt_x'].FindObject('stats')
 stats.SetOptStat(11111111)
 rc = h['mom'].cd(4)
 h['chi2'].Draw()
 rc = h['mom'].cd(5)
 h['Nmeasurements'].Draw()
 rc = h['mom'].cd(6)
 h['TDC2R_projx'] = h['TDC2R'].ProjectionY()
 h['TDC2R_projx'].SetTitle('RT Relation r projection')
 h['TDC2R_projx'].SetXTitle('drift distance [cm]')
 h['TDC2R_projx'].Draw()
 rc = h['mom'].cd(7)
 h['xy'].Draw('colz')
 rc = h['mom'].cd(8)
 h['pxpy'].Draw('colz')
 h['mom'].Update()
 
sigma_spatial = 0.2 # 0.2*(ShipGeo.MufluxSpectrometer.InnerTubeDiameter/2.)/ROOT.TMath.Sqrt(12) 
def makeTracks():
     hitlist = []
     nhit = -1
     for hit in sTree.Digi_MufluxSpectrometerHits:
      nhit+=1
      if hit.GetDetectorID() in noisyChannels: continue
      hitlist.append(nhit)
     return fitTrack(hitlist)

def fitTrack(hitlist,Pstart=3.):
# need measurements
   global fitter
   hitPosLists={}
   trID = 0
   posM = ROOT.TVector3(0, 0, 20.)
   momM = ROOT.TVector3(0,0,Pstart*u.GeV)
# approximate covariance
   covM = ROOT.TMatrixDSym(6)
   resolution = sigma_spatial
   if not withTDC: resolution = 5*sigma_spatial
   for  i in range(3):   covM[i][i] = resolution*resolution
   covM[0][0]=resolution*resolution*100.
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
   hitCov = ROOT.TMatrixDSym(7)
   hitCov[6][6] = resolution*resolution
   unSortedList = {}
   tmpList = {}
   k=0
   for nhit in hitlist:
      if type(nhit)==type(1):   hit = sTree.Digi_MufluxSpectrometerHits[nhit]
      else: hit = nhit
      vbot,vtop = correctAlignment(hit)
      tdc = hit.GetDigi()
      s,v,p,l,view = stationInfo(hit)
      distance = 0
      if withTDC: distance = RT(xLayers[s][p][l][view].GetName(),tdc)
      tmp = array('d',[vtop[0],vtop[1],vtop[2],vbot[0],vbot[1],vbot[2],distance])
      unSortedList[k] = ROOT.TVectorD(7,tmp)
      tmpList[k] = vtop[2]
      k+=1
   sorted_z = sorted(tmpList.items(), key=operator.itemgetter(1))
   for k in sorted_z:
      tp = ROOT.genfit.TrackPoint(theTrack) # note how the point is told which track it belongs to 
      measurement = ROOT.genfit.WireMeasurement(unSortedList[k[0]],hitCov,1,6,tp) # the measurement is told which trackpoint it belongs to
      measurement.setMaxDistance(ShipGeo.MufluxSpectrometer.InnerTubeDiameter/2.)
      tp.addRawMeasurement(measurement) # package measurement in the TrackPoint                                          
      theTrack.insertPoint(tp)  # add point to Track
   if not theTrack.checkConsistency():
    print "track not consistent"
    rep.Delete()
    return -2
# do the fit
   timer.Start()
   try:  fitter.processTrack(theTrack) # processTrackWithRep(theTrack,rep,True)
   except:   
      print "fit failed"
      rep.Delete()
      timer.Stop()
      return -1
    # print "time to fit the track",timer.RealTime()
   if timer.RealTime()>1: # make a new fitter, didn't helped
     print "very long fit time",timer.RealTime(),len(hitlist)
   fitStatus   = theTrack.getFitStatus()
   if Debug: print "Fit result:",fitStatus.isFitConverged(),fitStatus.getChi2(),fitStatus.getNdf()
   if not fitStatus.isFitConverged():
      rep.Delete()
      return -1
   chi2 = fitStatus.getChi2()/fitStatus.getNdf()
   rc = h['Nmeasurements'].Fill(fitStatus.getNdf())
   fittedState = theTrack.getFittedState()
   P = fittedState.getMomMag()
   if Debug: print "track fitted",fitStatus.getNdf(), theTrack.getNumPointsWithMeasurement(),P
   if fitStatus.getNdf() < 9:
      rep.Delete()
      return -2 
   Px,Py,Pz = fittedState.getMom().x(),fittedState.getMom().y(),fittedState.getMom().z()
   rc = h['p/pt'].Fill(P,ROOT.TMath.Sqrt(Px*Px+Py*Py))
   rc = h['chi2'].Fill(fitStatus.getChi2()/fitStatus.getNdf())
   pos = fittedState.getPos()
   rc = h['xy'].Fill(pos[0],pos[1])
   rc = h['pxpy'].Fill(Px/Pz,Py/Pz)
   return theTrack

def testT0():
 ut.bookHist(h,'means0','mean vs s0',100,0.,3000.,100,0.,3000.)
 ut.bookHist(h,'means1','mean vs s1',100,0.,3000.,100,0.,3000.)
 ut.bookHist(h,'means2','mean vs s2',100,0.,3000.,100,0.,3000.)
 for event in sTree:
    sumOfTDCs = 0
    if event.Digi_MufluxSpectrometerHits.GetEntries() < 15 or event.Digi_MufluxSpectrometerHits.GetEntries() > 30: continue
    for m in event.Digi_MufluxSpectrometerHits:
      sumOfTDCs+=m.GetDigi()
    mean = sumOfTDCs/float(event.Digi_MufluxSpectrometerHits.GetEntries())
    if event.Digi_ScintillatorHits.GetEntries()==0:
      print "no scint"
    else:
     rc = h['means0'].Fill(mean,event.Digi_ScintillatorHits[0].GetDigi())
     rc = h['means1'].Fill(mean,event.Digi_ScintillatorHits[1].GetDigi())
     if event.Digi_ScintillatorHits.GetEntries()>2:
      rc = h['means2'].Fill(mean,event.Digi_ScintillatorHits[2].GetDigi())

def getSlope(cl1,cl2):
# linear fit, minimize distances in X
    zx,zmx,zsq,zmz,n=0,0,0,0,0
    xmean,zmean=0,0
    for cl in [cl1,cl2]:
     for hit in cl:
       xmean+=hit[1]
       zmean+=hit[2]
       zx+=hit[1]*hit[2]
       zsq+=hit[2]*hit[2]
       n+=1
    A = (zx-zmean*xmean/float(n))/(zsq-zmean*zmean/float(n)) # checked 19 September 2018
    b = (xmean-A*zmean)/float(n) # checked 19 September 2018
    return A,b

Debug = False
delxAtGoliath=8.
clusterWidth = 5.
yMatching = 10.
minHitsPerCluster, maxHitsPerCluster = 2,6
topA,botA = ROOT.TVector3(),ROOT.TVector3()
topB,botB = ROOT.TVector3(),ROOT.TVector3()
clusters = {}
pl = {0:'00',1:'01',2:'10',3:'11'}
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

ut.bookHist(h,'clsN','cluster sizes',10,-0.5,9.5)
ut.bookHist(h,'Ncls','number of clusters / event',10,-0.5,9.5)
ut.bookHist(h,'delY','del Y from stereo; [cm]',100,-40.,40.)
ut.bookHist(h,'yest','estimated Y from stereo; [cm]',100,-100.,100.)
ut.bookHist(h,'xy','xy of first state;x [cm];y [cm]',100,-30.,30.,100,-30.,30.)
ut.bookHist(h,'pxpy','px/pz py/pz of first state',100,-0.2,0.2,100,-0.2,0.2)
views = {1:['_x','_u'],2:['_x','_v'],3:['_x'],4:['_x']}
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
 withTDC = False
 DTHits = []
 key = -1
 for hit in sTree.Digi_MufluxSpectrometerHits:
   key+=1
   if not hit.isValid: continue
   if hit.GetDetectorID() in noisyChannels: continue
   detID = hit.GetDetectorID()
   s,v,p,l,view = stationInfo(hit)
   if exclude_layer != None and view != '_x':
     if (2*p+l)==exclude_layer:  continue
   vbot,vtop = correctAlignment(hit)
   tdc = hit.GetDigi()
   s,v,p,l,view = stationInfo(hit)
   distance = 0
   if withTDC: distance = RT(xLayers[s][p][l][view].GetName(),tdc)
   DTHits.append( {'digiHit':key,'xtop':vtop.x(),'ytop':vtop.y(),'z':vtop.z(),'xbot':vbot.x(),'ybot':vbot.y(),'dist':distance, 'detID':detID} )
 track_hits = MufluxPatRec.execute(DTHits, TaggerHits, withNTaggerHits, withTDC)
 hitlist = {}
 k = 0
 for nTrack in track_hits:
  h['magPos'].Fill(track_hits[nTrack]['x_in_magnet'],track_hits[nTrack]['y_in_magnet'])
  node = sGeo.FindNode(track_hits[nTrack]['x_in_magnet'],track_hits[nTrack]['y_in_magnet'],zgoliath)
  if node.GetName() != "volGoliath_1": continue
  hitlist[k]=[]
  #if len(track_hits[nTrack]['34'])<5 or len(track_hits[nTrack]['y12'])<5: continue
  for dets in ['34','stereo12','y12']:
   rc = h['tracklets'+dets].Fill(len(track_hits[nTrack][dets]))
   for aHit in  track_hits[nTrack][dets]:
    hitlist[k].append( aHit['digiHit'])
  aTrack = fitTrack(hitlist[k],abs(track_hits[nTrack]['p']))
  if type(aTrack) != type(1):
   trackCandidates.append(aTrack)
   k+=1
  else: hitlist.pop(k)
 if onlyHits: return hitlist
 return trackCandidates

def findTracks(PR = 2,linearTrackModel = False, onlyX = False):
   if PR < 3 and sTree.GetBranch('FitTracks'): return sTree.FitTracks
   if PR%2==0 : return testPR()
   yMax = 20.
   trackCandidates = []
   spectrHitsSorted = sortHits(sTree)
   for s in range(1,5):
    for view in views[s]:
     allHits = {}
     clusters[s][view]={}
     for l in range(4): allHits[l]=[]
     for hit in spectrHitsSorted[view][s]:
      statnb,vnb,pnb,layer,view = stationInfo(hit)
      allHits[pnb*2+layer].append(hit)
     hitsChecked=[]
     ncl = 0
     for hitA in allHits[0]:
       botA,topA = correctAlignment(hitA)
       xA = (botA[0]+topA[0])/2.
       zA = (botA[2]+topA[2])/2.
       clusters[s][view][ncl]=[[hitA,xA,zA]]
       for k in range(1,4):
         for hitB in allHits[k]:
          botB,topB = correctAlignment(hitB)
          xB = (botB[0]+topB[0])/2.
          delx = xA-xB
          rc = h['del'+view+str(s)].Fill(delx)
          if abs(delx)<clusterWidth:
           zB = (botB[2]+topB[2])/2.
           clusters[s][view][ncl].append([hitB,xB,zB])
           hitsChecked.append(hitB.GetDetectorID())
       ncl+=1
     for hitA in allHits[1]:
       if hitA.GetDetectorID() in hitsChecked: continue
       botA,topA = correctAlignment(hitA)
       xA = (botA[0]+topA[0])/2.
       zA = (botA[2]+topA[2])/2.
       clusters[s][view][ncl]=[[hitA,xA,zA]]
       for k in range(2,4):
         for hitB in allHits[k]:
          if hitB.GetDetectorID() in hitsChecked: continue
          botB,topB = correctAlignment(hitB)
          xB = (botB[0]+topB[0])/2.
          delx = xA-xB
          rc = h['del'+view+str(s)].Fill(delx)
          if abs(delx)<clusterWidth:
           zB = (botB[2]+topB[2])/2.
           clusters[s][view][ncl].append([hitB,xB,zB])
           hitsChecked.append(hitB.GetDetectorID())
       ncl+=1
     if minHitsPerCluster==2:
      for hitA in allHits[2]:
       if hitA.GetDetectorID() in hitsChecked: continue
       botA,topA = correctAlignment(hitA)
       xA = (botA[0]+topA[0])/2.
       zA = (botA[2]+topA[2])/2.
       clusters[s][view][ncl]=[[hitA,xA,zA]]
       for k in range(3,4):
         for hitB in allHits[k]:
          if hitB.GetDetectorID() in hitsChecked: continue
          botB,topB = correctAlignment(hitB)
          xB = (botB[0]+topB[0])/2.
          delx = xA-xB
          rc = h['del'+view+str(s)].Fill(delx)
          if abs(delx)<clusterWidth:
           zB = (botB[2]+topB[2])/2.
           clusters[s][view][ncl].append([hitB,xB,zB])
           hitsChecked.append(hitB.GetDetectorID())
       ncl+=1
     rc = h['clsN'].Fill(ncl)
     Ncl = 0
     keys = clusters[s][view].keys()
     for x in keys:
      aCl = clusters[s][view][x]
      if len(aCl)<minHitsPerCluster or len(aCl)>maxHitsPerCluster:   dummy = clusters[s][view].pop(x)
      else: Ncl+=1
     rc = h['Ncls'].Fill(Ncl)
   # make list of hits, see per event 1 and 2 tracks most
   # now we have to make a loop over all combinations 
   allStations = True
   for s in range(1,5):
      if len(clusters[s]['_x'])==0:   allStations = False
   if len(clusters[1]['_u'])==0:      allStations = False
   if len(clusters[2]['_v'])==0:      allStations = False
   if allStations:
    t1t2cand = []
    # list of lists of cluster1, cluster2, x
    t3t4cand = []
    h['dispTrackSeg'] = []
    for cl1 in clusters[1]['_x']:
     for cl2 in clusters[2]['_x']:
      slopeA,bA = getSlope(clusters[1]['_x'][cl1],clusters[2]['_x'][cl2])
      x1 = zgoliath*slopeA+bA
      t1t2cand.append([clusters[1]['_x'][cl1],clusters[2]['_x'][cl2],x1,slopeA,bA])
      if Debug:
       nt = len(h['dispTrackSeg'])
       h['dispTrackSeg'].append( ROOT.TGraph(2) )
       h['dispTrackSeg'][nt].SetPoint(0,0.,bA)
       h['dispTrackSeg'][nt].SetPoint(1,400.,slopeA*400+bA)
       h['dispTrackSeg'][nt].SetLineColor(ROOT.kRed)
       h['dispTrackSeg'][nt].SetLineWidth(2)
       h['simpleDisplay'].cd(1)
       h['dispTrackSeg'][nt].Draw('same')
       nt+=1
    for cl1 in clusters[3]['_x']:
     for cl2 in clusters[4]['_x']:
      slopeA,bA = getSlope(clusters[3]['_x'][cl1],clusters[4]['_x'][cl2])
      x1 = zgoliath*slopeA+bA
      t3t4cand.append([clusters[3]['_x'][cl1],clusters[4]['_x'][cl2],x1,slopeA,bA])
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
    for nt1t2 in range(len(t1t2cand)):
     t1t2 = t1t2cand[nt1t2]
     for nt3t4 in range(len(t3t4cand)):
      t3t4 = t3t4cand[nt3t4]
      delx = t3t4[2]-t1t2[2]
      h['delx'].Fill(delx)
# check also extrapolations at t1 t2, or t3 t4
# makes only sense for zero field
      if linearTrackModel: makeLinearExtrapolations(t1t2,t3t4)
      if abs(delx) < delxAtGoliath:
       hitList = []
       for p in range(2):
         for cl in t1t2[p]: hitList.append(cl[0])
       for p in range(2):
         for cl in t3t4[p]: hitList.append(cl[0])
# check for matching u and v hits, X
       stereoHits = {'u':[],'v':[]}
       for n in clusters[1]['_u']:
        if len(clusters[1]['_u'][n])<2: continue
        for cl in clusters[1]['_u'][n]:
           botA,topA = correctAlignment(cl[0])
           sl  = (botA[1]-topA[1])/(botA[0]-topA[0])
           b = topA[1]-sl*topA[0]
           yest = sl*(t1t2[3]*topA[2]+t1t2[4])+b
           rc = h['yest'].Fill(yest)
           if yest < botA[1]-yMax: continue
           if yest >topA[1]+yMax: continue
           stereoHits['u'].append([cl[0],sl,b,yest])
       for n in clusters[2]['_v']:
        if len(clusters[2]['_v'][n])<2: continue
        for cl in clusters[2]['_v'][n]: 
           botA,topA = correctAlignment(cl[0])
           sl  = (botA[1]-topA[1])/(botA[0]-topA[0])
           b = topA[1]-sl*topA[0]
           yest = sl*(t1t2[3]*topA[2]+t1t2[4])+b
           rc = h['yest'].Fill(yest)
           if yest < botA[1]-yMax: continue
           if yest > topA[1]+yMax: continue
           stereoHits['v'].append([cl[0],sl,b,yest])
       nu = 0
       matched = {}
       for clu in stereoHits['u']:
        nv=0
        for clv in stereoHits['v']:
           dely = clu[3]-clv[3]
           rc = h['delY'].Fill(dely)
           if abs(dely)<yMatching:
            node = sGeo.FindNode(0,(clu[3]+clv[3])/2.,zgoliath)
            if node.GetName() == "volGoliath_1":
             matched[clv[0]]=True
             matched[clu[0]]=True
           nv+=1
        nu+=1
       if not onlyX:
        for cl in matched: 
          if matched[cl]: hitList.append(cl)
       if linearTrackModel: return hitList
       if rname in zeroFieldData: 
         momFromptkick = 1000.
       else: momFromptkick=ROOT.TMath.Abs(1.03/(t3t4[3]-t1t2[3]+1E-20))
       if Debug:  print "fit track t1t2 t3t4 with hits, stereo, delx, pstart",nt1t2,nt3t4,len(hitList),len(matched),delx,momFromptkick
       aTrack = fitTrack(hitList,momFromptkick)
       if type(aTrack) != type(1):
         trackCandidates.append(aTrack)
   return trackCandidates

def makeLinearExtrapolations(t1t2,t3t4):
 for hit in sTree.Digi_MufluxSpectrometerHits:
    if hit.GetDetectorID() in noisyChannels:  continue
    s,v,p,l,view = stationInfo(hit)
    if view != '_x': continue
    vbot,vtop = correctAlignment(hit)
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
    vtop,vbot = correctAlignmentRPC(hit,v)
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
          if hit.GetDetectorID() in noisyChannels:  continue
          s,v,p,l,view = stationInfo(hit)
          vbot,vtop = correctAlignment(hit)
          z = (vbot[2]+vtop[2])/2.
          try:
           rc,pos,mom = extrapolateToPlane(aTrack,z)
          except:
           print "plotBiasedResiduals extrap failed"
           continue
          distance = 0
          if RTrelations.has_key(rname) or hasattr(sTree,'MCTrack'):
           distance = RT(xLayers[s][p][l][view].GetName(),hit.GetDigi())
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
def plotBiasedResiduals(nEvent=-1,nTot=1000,PR=1):
  if not h.has_key('hitMapsX'): plotHitMaps()
  for s in xLayers:
     for p in xLayers[s]:
      for l in xLayers[s][p]:
       for view in xLayers[s][p][l]:
         h['TDC'+xLayers[s][p][l][view].GetName()].Reset()
#
  eventRange = [0,sTree.GetEntries()]
  if not nEvent<0: eventRange = [nEvent,nEvent+nTot]
  for Nr in range(eventRange[0],eventRange[1]):
   getEvent(Nr)
   h['T0tmp'].Reset()
   if Nr%500==0:   print "now at event",Nr
   if not findSimpleEvent(sTree): continue
   trackCandidates = findTracks(PR)
   for aTrack in trackCandidates:
       if not aTrack.getNumPointsWithMeasurement()>0: continue
       sta = aTrack.getFittedState(0)
       if sta.getMomMag() < 3.: continue
       for hit in sTree.Digi_MufluxSpectrometerHits:
          if hit.GetDetectorID() in noisyChannels:  continue
          s,v,p,l,view = stationInfo(hit)
          vbot,vtop = correctAlignment(hit)
          z = (vbot[2]+vtop[2])/2.
          try:
           rc,pos,mom = extrapolateToPlane(aTrack,z)
          except:
           print "plotBiasedResiduals extrap failed"
           continue
          distance = 0
          if withTDC and (RTrelations.has_key(rname) or hasattr(sTree,'MCTrack')):
           distance = RT(xLayers[s][p][l][view].GetName(),hit.GetDigi())
          tmp = (vbot[0] - vtop[0])*pos[1] - (vbot[1] - vtop[1])*pos[0] + vtop[0]*vbot[1] - vbot[0]*vtop[1]
          tmp = -tmp/ROOT.TMath.Sqrt( (vtop[0]-vbot[0])**2+(vtop[1]-vbot[1])**2)  # to have same sign as difference in X
          xL = tmp -distance
          xR = tmp +distance
          if abs(xL)<abs(xR):res = xL
          else: res = xR
          h['biasResX_'+str(s)+view+str(2*p+l)].Fill(res,pos[0])
          h['biasResY_'+str(s)+view+str(2*p+l)].Fill(res,pos[1])
          h['biasResXL_'+str(s)+view+str(2*p+l)].Fill(res,pos[0])
          h['biasResYL_'+str(s)+view+str(2*p+l)].Fill(res,pos[1])
# make TDC plots for hits matched to tracks, within window suitable for not using TDC
          if abs(res) < 2. :
            t0 = 0
            if hasattr(sTree,'MCTrack'): t0 = sTree.ShipEventHeader.GetEventTime()
            rc = h['TDC'+xLayers[s][p][l][view].GetName()].Fill(hit.GetDigi()-t0)
            rc = h['T0tmp'].Fill(hit.GetDigi()-t0)
   #for aTrack in trackCandidates: aTrack.Delete()
   t0 = h['T0tmp'].GetMean()
   rc = h['T0'].Fill(t0)
   for aTrack in trackCandidates: 
     rep = aTrack.getCardinalRep()
     aTrack.Delete()
     rep.Delete()
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
     if h[hname].GetEntries()<10:
       h[hnameProjX].Draw() 
       j+=1
       continue
     h[hnameProjX] = h[hname].ProjectionX()
     tc = h['biasedResiduals'].cd(j)
     fitResult = h[hnameProjX].Fit('gaus','SQ','',-0.5,0.5)
     rc = fitResult.Get()
     fitFunction = h[hnameProjX].GetFunction('gauss')
     if not fitFunction : fitFunction = myGauss
     if not rc:
      print "simple gaus fit failed"
      fitFunction.SetParameter(0,h[hnameProjX].GetEntries())
      fitFunction.SetParameter(1,0.)
      fitFunction.SetParameter(2,0.1)
      fitFunction.SetParameter(3,1.)
     else:
      fitFunction.SetParameter(0,rc.GetParams()[0])
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
       rc = h[hmean].SetBinContent( k, mean)
       rc = h[hmean].SetBinError(k, rms)
      amin,amax,nmin,nmax = ut.findMaximumAndMinimum(h[hmean])
      if amax<3. and amin>-3.:
       h[hmean].SetMaximum(0.1)
       h[hmean].SetMinimum(-0.1)
      else: 
       h[hmean].SetLineColor(ROOT.kRed)
       h[hmean].SetMaximum(0.5)
       h[hmean].SetMinimum(-0.5)
      h[hmean].Draw()
     j+=1
  momDisplay()
def plot2dResiduals():
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
      h[hname].Draw('box')
     j+=1
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
   if Nr%1000==0:   print "now at event",Nr
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

def momResolution():
  ut.bookHist(h,'momResol','momentum resolution function of momentum',100,-0.1,0.1,10,0.,100.)
  for n in range(sTree.GetEntries()):
   rc = sTree.GetEvent(n)
   if not findSimpleEvent(sTree): continue
   tracks = findTracks()
   if len(tracks)<1: continue
   zmin = 1000.
   kMin = 0
   for k in range(sTree.MufluxSpectrometerPoint.GetEntries()):
     mp = sTree.MufluxSpectrometerPoint[k]
     if mp.GetZ()<zmin:
        zmin = mp.GetZ()
        kMin = k
   mp = sTree.MufluxSpectrometerPoint[kMin]
   trueP=ROOT.TVector3(mp.GetPx(),mp.GetPy(),mp.GetPz())
   st = tracks[0].getFittedState()
   recoP = st.getMom()
   rc = h['momResol'].Fill((recoP.Mag()-trueP.Mag())/trueP.Mag(),trueP.Mag())
def hitResolution():
 ut.bookHist(h,'hitResol','hit resolution',100,-0.5,0.5)
 for n in range(100):
  rc = sTree.GetEvent(n)
  for k in range(sTree.Digi_MufluxSpectrometerHits.GetEntries()):
    hit = sTree.Digi_MufluxSpectrometerHits[k]
    trueHit = sTree.MufluxSpectrometerPoint[k]
    hit.MufluxSpectrometerEndPoints(vbot,vtop)
    TDC = hit.GetDigi() - (vtop[0]-trueHit.GetX())/(ROOT.TMath.C() *100./1000000000.0)
    distance = RT('x',TDC)
    h['hitResol'].Fill(distance - trueHit.dist2Wire())

def plotRPCExtrap(nEvent=-1,nTot=1000,PR=1):
  nav.cd('/VMuonBox_1/VSensitive1_1')
  loc = array('d',[0,0,0])
  glob = array('d',[0,0,0])
  nav.LocalToMaster(loc,glob)
  zRPC1 = glob[2]
  maxDistance=10.
  eventRange = [0,sTree.GetEntries()]
  if not nEvent<0: eventRange = [nEvent,nEvent+nTot]
  for s in range(1,6):
   for v in range(2):
    if v==1: dx=20
    if v==0: dx=20
    ut.bookHist(h,'RPCResX_'+str(s)+str(v),'RPC residual for '+str(s)+' '+ str(v),100,-dx,dx,20,-140.,140.)
    ut.bookHist(h,'RPCResY_'+str(s)+str(v),'RPC residual for '+str(s)+' '+ str(v),100,-dx,dx,20,-140.,140.)
  ut.bookHist(h,'RPCResX1_p','RPC residual for station 1 function of track momentum',100,-dx,dx,100,0.,100.)
  ut.bookHist(h,'RPCMatchedHits','matched RPC hits as function of track momentum',10,0.5,10.5,20,-0.5,19.5,100,0.,100.)
  ut.bookHist(h,'RPCMeanMatchedHits','mean matched RPC hits as function of track momentum',100,0.,100.)
  ut.bookHist(h,'RPC>1','fraction of tracks with > 1 RPC hits',100,0.,100.)
  for Nr in range(eventRange[0],eventRange[1]):
   getEvent(Nr)
   if Nr%10000==0:   print "now at event",Nr
   if not sTree.Digi_MuonTaggerHits.GetEntries()>0: continue
   if not findSimpleEvent(sTree): continue
   trackCandidates = findTracks(PR)
   for aTrack in trackCandidates:
       matchedHits={1:{0:[],1:[]},2:{0:[],1:[]},3:{0:[],1:[]},4:{0:[],1:[]},5:{0:[],1:[]}}
       if not aTrack.getNumPointsWithMeasurement()>0: continue
       sta = aTrack.getFittedState(0)
       if sta.getMomMag() < 1.: continue
       nHit = -1
       rc,pos,mom = extrapolateToPlane(aTrack,zRPC1)
       inAcc=False
       node = sGeo.FindNode(pos[0],pos[1],zRPC1)
       if not node: 
         print "RPCextrap: node not found, ",pos[0],pos[1],zRPC1
       elif node.GetName() != "cave_1": 
         inAcc=True
       for hit in sTree.Digi_MuonTaggerHits:
        nHit+=1
        channelID = hit.GetDetectorID()
        s  = channelID/10000
        v  = (channelID-10000*s)/1000
        vtop,vbot = correctAlignmentRPC(hit,v)
        z = (vtop[2]+vbot[2])/2.
        try:
           rc,pos,mom = extrapolateToPlane(aTrack,z)
        except:
           print "plotRPCExtrap failed"
           continue
        if rc<0: continue
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
        if abs(res)<maxDistance:
           matchedHits[s][v].append(nHit)
       # record number of hits per station and view and track momentum
       # but only for tracks in acceptance
       if inAcc:
        for s in matchedHits:
         for v in matchedHits[s]:
          p = min(99.9,sta.getMomMag())
          rc = h['RPCMatchedHits'].Fill(2*s-1+v,len(matchedHits[s][v]),p)
  if not h.has_key('RPCResiduals'): 
      ut.bookCanvas(h,key='RPCResiduals',title='RPCResiduals',nx=1600,ny=1200,cx=2,cy=4)
      ut.bookCanvas(h,key='RPCResidualsXY',title='RPCResiduals function of Y/X',nx=1600,ny=1200,cx=2,cy=4)
      ut.bookCanvas(h,key='RPCResidualsP',title='RPCResiduals function of muon momentum',nx=900,ny=900,cx=1,cy=1)
  j=1
  for s in range(1,5):
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
      ut.bookCanvas(h,key='RPCResiduals2dXY',title='muon tagger Residuals function of X/Y',nx=1600,ny=1200,cx=2,cy=4)
  j=1
  for s in range(1,5):
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
  zax = h['RPCMatchedHits'].GetZaxis()
  xax = h['RPCMatchedHits'].GetXaxis()
  yax = h['RPCMatchedHits'].GetYaxis()
  for ip in range(1,zax.GetNbins()+1):
    Nmean = 0
    Nentries = 0
    Ntracks1 = 0
    for ks in range(1,xax.GetNbins()+1):
      for n in range(1,yax.GetNbins()+1):
         Nmean += h['RPCMatchedHits'].GetBinContent(ks,n,ip)*xax.GetBinCenter(n)
         Nentries+=h['RPCMatchedHits'].GetBinContent(ks,n,ip)
         if xax.GetBinCenter(n)>1: Ntracks1+=h['RPCMatchedHits'].GetBinContent(ks,n,ip)
    Nmean = Nmean / float(Nentries+1E-10)
    rc = h['RPCMeanMatchedHits'].SetBinContent(ip,Nmean)
    fraction = Ntracks1/(Nentries+1E-10)
    rc = h['RPC>1'].SetBinContent(ip,fraction)
def debugRPCstrips():
  ut.bookHist(h,'RPCstrips','RPC strips',1000,-100.,100.,1000,-100.,100.)
  h['RPCstrips'].Draw()
  s=1
  for v in range(2):
   for c in range(184):
    if v==0 and c>105: continue
    if v==1 and c<12: continue
    if c%5==0:
     h['RPCstrip'+str(v)+str(c)]=ROOT.TGraph()
     detID = s*10000+v*1000+c
     hit = ROOT.MuonTaggerHit(detID,0)
     hit.EndPoints(vtop,vbot)
     vtop[0]=-vtop[0]
     vbot[0]=-vbot[0]
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
for p in range(24): alignCorrection[p]=[0,0,0]
# x layer
withCorrections=True
if not hasattr(sTree,'MCTrack') and withCorrections:
 alignCorrection[0]=[ 0.0, 0, 0]   # by hand
 alignCorrection[1]=[ 0.0, 0, 0]
 alignCorrection[2]=[ 0.0, 0, 0]
 alignCorrection[3]=[ 0.0 ,0, 0]
# u layers
 alignCorrection[4]=[ 0.0, 0, 0]
 alignCorrection[5]=[ 0.0, 0, 0]
 alignCorrection[6]=[ 0.0, 0, 0]
 alignCorrection[7]=[ 0.0, 0, 0]
# v layers
 alignCorrection[8]= [ 0.0, 0, 0]
 alignCorrection[9]= [ 0.0, 0, 0]
 alignCorrection[10]=[ 0.0, 0, 0]
 alignCorrection[11]=[ 0.0, 0, 0]
# x layers
 alignCorrection[12]=[ 0.0, 0, 0]
 alignCorrection[13]=[ 0.0, 0, 0]
 alignCorrection[14]=[ 0.0, 0, 0]
 alignCorrection[15]=[ 0.0, 0, 0]
# T 3
 alignCorrection[16]=[ 0.0, 0, 0]
 alignCorrection[17]=[ 0.0, 0, 0]
 alignCorrection[18]=[ 0.0, 0, 0]
 alignCorrection[19]=[ 0.0, 0, 0]
# T 4
 alignCorrection[20]=[ 0.0, 0, 0]
 alignCorrection[21]=[ 0.0, 0, 0]
 alignCorrection[22]=[ 0.0, 0, 0]
 alignCorrection[23]=[ 0.0, 0, 0]

def correctAlignment(hit,force=False):
 vbot,vtop = ROOT.TVector3(), ROOT.TVector3()
 rc = hit.MufluxSpectrometerEndPoints(vbot,vtop)
 s,v,p,l,view = stationInfo(hit)
 if view=='_x':
  vbot[0]=xpos[hit.GetDetectorID()]
  vtop[0]=xpos[hit.GetDetectorID()]
 else:
  vtop[0]=xpos[hit.GetDetectorID()]
  vtop[1]=ypos[hit.GetDetectorID()]
  vbot[0]=xposb[hit.GetDetectorID()]
  vbot[1]=yposb[hit.GetDetectorID()]
 vbot[2]=zpos[hit.GetDetectorID()]
 vtop[2]=zpos[hit.GetDetectorID()]
 x= (2*p+l)
 if s==1 and view=='_u': x+=4
 if s==2 and view=='_v': x+=8
 if s==2 and view=='_x': x+=12
 if s==3 : x+=16
 if s==4:  x+=20
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
 statnb,vnb,pnb,lnb,view = stationInfo(test)
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
      print "simple gaus fit failed"
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
 if v==1:
  vbot[0] = -vbot[0] -1.21
  vtop[0] = -vtop[0] -1.21
 else:
  vbot[1] = vbot[1] -1.21
  vtop[1] = vtop[1] -1.21
  
 return vbot,vtop

def testMultipleHits(nEvent=-1,nTot=1000):
  ut.bookHist(h,'multHits','DT hits multiplicity',10,-0.5,9.5)
  ut.bookHist(h,'multHits_deltaT','DT multiple hits delta T',100,0.,2000.)
  eventRange = [0,sTree.GetEntries()]
  if not nEvent<0: eventRange = [nEvent,nEvent+nTot]
  for Nr in range(eventRange[0],eventRange[1]):
   rc = sTree.GetEvent(Nr)
   listOfDigits={}
   for hit in sTree.Digi_MufluxSpectrometerHits:
     detID = hit.GetDetectorID()
     if not listOfDigits.has_key(detID): listOfDigits[detID]=[0,[]]
     listOfDigits[detID][0]+=1
     listOfDigits[detID][1].append(hit.GetDigi())
   for x in listOfDigits:
    rc=h['multHits'].Fill(listOfDigits[x][0])
    if listOfDigits[x][0]>1:
      listOfDigits[x][1].sort()
      for t in range(1,len(listOfDigits[x][1])):
       rc=h['multHits_deltaT'].Fill(t-listOfDigits[x][1][0])

def studyScintiallator():
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

def findV0(nstart=0,nmax=-1):
 if nmax<0: nmax = sTree.GetEntries()
 ut.bookHist(h,'v0mass_wc','V0 mass wrong charge combinations',100,0.2,1.8,50,-120.,20.)
 ut.bookHist(h,'v0mass','V0 mass ',100,0.2,1.8,50,-120.,20.)
 for n in range(nstart,nmax):
  rc = sTree.GetEvent(n)
  tracks = findTracks()
  if len(tracks) <2: continue
  PosDir = {}
  tr = 0
  mass = PDG.GetParticle(211).Mass()
  for aTrack in tracks:
      xx  = aTrack.getFittedState()
      PosDir[tr] = [xx.getPos(),xx.getDir(),ROOT.TLorentzVector(),xx.getCharge()]
      mom = xx.getMom()
      E = ROOT.TMath.Sqrt( mass*mass + mom.Mag2() )
      PosDir[tr][2].SetPxPyPzE(mom.x(),mom.y(),mom.z(),E)
      tr+=1
  xv,yv,zv,doca = myVertex(0,1,PosDir)
  V0Mom = PosDir[0][2]+PosDir[1][2]
  print n,doca,zv,V0Mom.M(),PosDir[0][3],PosDir[1][3]
  if doca > 5: continue
  if PosDir[0][3]*PosDir[1][3]< 0: rc = h['v0mass'].Fill(V0Mom.M(),zv)
  else: rc = h['v0mass_wc'].Fill(V0Mom.M(),zv)
def getEvent(n):
 global rname
 rc = sTree.GetEvent(n)
 if withTDC:
  temp = sTree.GetCurrentFile().GetName()
  curFile = temp[temp.rfind('/')+1:]
  if curFile != rname:
   rname = curFile
   h['tMinAndTmax'] = RTrelations[rname]['tMinAndTmax']
   for s in h['tMinAndTmax']: h['rt'+s] = RTrelations[rname]['rt'+s]

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
    os.system("xrdcp $EOSSHIP"+fname+" "+newName)
   ftemp = ROOT.TFile.Open(newName,'update')
   sTree = ftemp.cbmsim
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
  ftemp.cd('')
  ftemp.mkdir('alignment')
  ftemp.alignment.cd('')
  alignConstants={'xpos':xpos,'ypos':ypos,'zpos':zpos,'alignCorrection':alignCorrection}
  pkl = Pickler(ftemp)
  pkl.dump(alignConstants,'alignConstants')
  momDisplay()
  h['mom'].Write()

def importRTrel():
  for fname in fnames:
   f = ROOT.TFile.Open(fname)
   rname = fname[fname.rfind('/')+1:]
   RTrelations[rname] = {}
   upkl    = Unpickler(f)
   RTrelations[rname]={}
   RTrelations[rname]['tMinAndTmax'] = upkl.load('tMinAndTmax')
   for x in RTrelations[rname]['tMinAndTmax']: RTrelations[rname]['rt'+x]=f.RT.Get('rt'+x)
   h['tMinAndTmax'] = RTrelations[rname]['tMinAndTmax']
   for s in h['tMinAndTmax']: h['rt'+s] = RTrelations[rname]['rt'+s]
   f.Close()
# to START
RTrelations = {}
zeroFieldData=['SPILLDATA_8000_0515970150_20180715_220030.root']
def init(database='muflux_RTrelations.pkl',remake=False,withReco=False):
 global withTDC
 if os.path.exists(database): RTrelations = pickle.load(open(database))
 N = sTree.GetEntries()
 if not RTrelations.has_key(rname) or remake:
  withTDC = False
  plotBiasedResiduals(0,N)
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
  plotBiasedResiduals(0,N)
  plotRPCExtrap(0,N)
  ut.writeHists(h,'histos-'+rname,plusCanvas=True)
#

def recoStep0():
  global witTDC
  withTDC = False
  plotBiasedResiduals(nEvent=0,nTot=sTree.GetEntries(),PR=2)
  makeRTrelations()
  RTrelations =  {'tMinAndTmax':h['tMinAndTmax']}
  for s in h['tMinAndTmax']: RTrelations['rt'+s] = h['rt'+s]
  makeRTrelPersistent(RTrelations)
def recoStep1():
# fitted tracks
  importRTrel()
  fGenFitArray = ROOT.TClonesArray("genfit::Track") 
  fGenFitArray.BypassStreamer(ROOT.kFALSE)
  fitTracks   = sTree.Branch("FitTracks", fGenFitArray,32000,-1)
  n = 0
  for event in sTree:
    if n%1000==0: print "Now at event",n
    n+=1
    fGenFitArray.Delete()
    theTracks = testPR()
    for aTrack in theTracks:
     nTrack   = fGenFitArray.GetEntries()
     aTrack.prune("CFL")
     fGenFitArray[nTrack] = aTrack
    fitTracks.Fill()
  sTree.Write()
  makeAlignmentConstantsPersistent()
  ftemp=sTree.GetCurrentFile()
  ftemp.Write("",ROOT.TFile.kOverwrite)
  ftemp.Close()

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
 print " --- init(): do boostrapping, determine RT relation using fitted tracks, do plotBiasedResiduals and plotRPCExtrap with TDC"

 vetoLayer = []
 database='muflux_RTrelations.pkl'
 if sTree.GetCurrentFile().GetKey('RT'):
  importRTrel()
 else:
  if os.path.exists(database):
   RTrelations = pickle.load(open(database))
   if not RTrelations.has_key(rname):
    print "You should run init() to determine the RT relations"
   else:
    h['tMinAndTmax'] = RTrelations[rname]['tMinAndTmax']
    for s in h['tMinAndTmax']: h['rt'+s] = RTrelations[rname]['rt'+s]

# spills with TDC 
# SPILLDATA_8000_0519186540_20180723_084148.root *
# SPILLDATA_8000_0519181180_20180723_082356.root
# SPILLDATA_8000_0519180060_20180723_082012.root
# SPILLDATA_8000_0519180250_20180723_082050.root
# SPILLDATA_8000_0519567560_20180724_055152.root
#      SPILLDATA_8000_0515970150_20180715_220030.root file with multiple hits   TDC calibration bad, few events
# SPILLDATA_8000_0519181735_20180723_082547.root 
# SPILLDATA_8000_0519181365_20180723_082433.root
# SPILLDATA_8000_0519181920_20180723_082624.root
# SPILLDATA_8000_0519181550_20180723_082510.root +
# SPILLDATA_8000_0519180435_20180723_082127.root
# SPILLDATA_8000_0519182110_20180723_082702.root ok
# SPILLDATA_8000_0519180620_20180723_082204.root ok
# SPILLDATA_8000_0519182295_20180723_082739.root ok
# SPILLDATA_8000_0519180805_20180723_082241.root ok
# SPILLDATA_8000_0519182365_20180723_082753.root ok
# SPILLDATA_8000_0519180990_20180723_082318.root ok
# SPILLDATA_8000_0519182440_20180723_082808.root ok

if options.command == "recoStep0":
  withTDC=False
  print "determine RT relations, make new files"
  recoStep0()
if options.command == "recoStep1":
  print "add fitted tracks"
  recoStep1()
