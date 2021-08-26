import ROOT
# to be run after detector modules are created, simplest way:
# python -i $SNDBUILD/sndsw/shipLHC/run_simSND.py -n 10 --Ntuple -f /eos/experiment/sndlhc/MonteCarlo/FLUKA/muons_up/version1/unit30_Nm.root --eMin 1.0
# import SciFiMapping

geoFile = "geofile_full.Ntuple-TGeant4.root"
fgeo = ROOT.TFile.Open(geoFile)
from ShipGeoConfig import ConfigRegistry
from rootpyPickler import Unpickler
#load geo dictionary
upkl    = Unpickler(fgeo)
snd_geo = upkl.load('ShipGeo')
 
# -----Create geometry----------------------------------------------
import shipLHC_conf as sndDet_conf

run = ROOT.FairRunSim()
run.SetName("TGeant4")  # Transport engine
run.SetOutputFile(ROOT.TMemFile('output', 'recreate'))  # Output file
run.SetUserConfig("g4Config_basic.C") # geant4 transport not used
rtdb = run.GetRuntimeDb()
modules = sndDet_conf.configure(run,snd_geo)
sGeo = fgeo.FAIRGeom
top = sGeo.GetTopVolume()
# hierarchy:  top<-volTarget<-ScifiVolume<- ScifiHorPlaneVol<-HorMatVolume<-FibreVolume
#                                                                                     <- ScifiVertPlaneVol<-VertMatVolume<-FibreVolume

def ycross(a,R,x):
    A = R*R - (x-a)**2
    if A<0: return False
    y = ROOT.TMath.Sqrt(A)
    return y
def integralSqrt(ynorm):
     return 1./2.*(ynorm*ROOT.TMath.Sqrt(1-ynorm*ynorm)+ROOT.TMath.ASin(ynorm))
def fraction(R,x,y):
       F= 2*R*R*(integralSqrt(y/R) )
       F-=(2*x*y)
       return  F/(R*R*ROOT.TMath.Pi())
def area(a,R,xL,xR):
    if xL>xR: 
          print("wrong overlap, xL>xR")
          return -1
    fracL = -1
    fracR = -1
    if xL<=a-R and xR>=a+R: return 1
    leftC    = ycross(a,R,xL)
    rightC = ycross(a,R,xR)
    if not leftC and not rightC: 
          # print('no solution')
          return -1
    if rightC: fracR = fraction(R,xR-a,rightC)
    if leftC:    fracL = fraction(R,a-xL,leftC)
    theAnswer = 0
    if leftC: 
          if xL<a: theAnswer += 1-fracL
          else:      theAnswer += fracL
          if rightC:   theAnswer -=1
    if rightC: 
          if xR>a: theAnswer += 1-fracR
          else:      theAnswer +=  fracR
    return theAnswer

def getFibre2SiPM():
   scifi   = modules['Scifi']
   sipm = scifi.SiPMOverlap()           # 12 SiPMs per mat, made for horizontal mats
   sGeo = ROOT.gGeoManager
   HorMat  = sGeo.FindVolumeFast('HorMatVolume')
   VertMat = sGeo.FindVolumeFast('VertMatVolume')
   fibresSiPM = {}
   for mat in [VertMat,HorMat]:
       fibresRadius = False
       orient = 0
       if mat.GetName().find('Hor')==0: orient = 1
       M = mat.GetName()
       fibresSiPM[M]={}
       for fibre in mat.GetNodes():
          if not fibresRadius:
              fibresRadius=fibre.GetVolume().GetShape().GetDX()
          fID = fibre.GetNumber()     # this should be reduced to local libre number
          a = fibre.GetMatrix().GetTranslation()[orient]
      # check for overlap with any of the SiPM channels
          for vol in sipm.GetNodes():    # 12 SiPMs
                 trans0 = vol.GetMatrix().GetTranslation()[1]
                 # print("0   ",vol.GetName(),trans0[0],trans0[1],trans0[2])
                 for iSiPM in vol.GetVolume().GetNodes():  # 2 volumes with gap
                     trans1 = iSiPM.GetMatrix().GetTranslation()[1]
                     # print("1        ",iSiPM.GetName(),trans1[0],trans1[1],trans1[2])
                     for x in iSiPM.GetVolume().GetNodes():    # 64 channels
                        transx = x.GetMatrix().GetTranslation()[1]
                        # print("2                    ",x.GetName(),transx+trans1+trans0)
                        dSiPM = x.GetVolume().GetShape().GetDY()
                        xcentre = transx+trans1+trans0
                        if abs(xcentre-a)>4*fibresRadius: continue # no need to check further
                        W = area(a,fibresRadius,xcentre-dSiPM/2.,xcentre+dSiPM/2.)
                        if W<0: continue
                        N = x.GetNumber()
                        # print('debug',N,fID,a,xcentre-dSiPM/2.,xcentre+dSiPM/2.,W)
                        if not N in fibresSiPM[M]:     fibresSiPM[M][N] = {}
                        fibresSiPM[M][N][fID] = W
   return fibresSiPM

from array import array
def position():
   nav = sGeo.GetCurrentNavigator()
   path = "/volTarget_1/ScifiVolume_1000000/ScifiHorPlaneVol_0/HorMatVolume_1010000"
   nav.cd(path)
   mat = nav.GetCurrentNode()
   loc = array('d',[0,0,0])
   glo = array('d',[0,0,0])
   for fibre in mat.GetNodes():
     trans = fibre.GetMatrix().GetTranslation()
     nav.cd(path+"/"+fibre.GetName())
     nav.LocalToMaster(loc,glo)
     print(fibre.GetName(),trans[0],trans[1],trans[2],' : ',glo)




