import ROOT
# to be run after detector modules are created, simplest way:
# python -i $SNDBUILD/sndsw/shipLHC/run_simSND.py -n 10 --Ntuple -f /eos/experiment/sndlhc/MonteCarlo/FLUKA/muons_up/version1/unit30_Nm.root --eMin 1.0
# import SciFiMapping

if __name__ == "__main__":
	print("open geofile")
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
    if rightC: fracR = fraction(R,abs(xR-a),rightC)
    if leftC:    fracL = fraction(R,abs(xL-a),leftC)
    theAnswer = 0
    if leftC: 
          if xL<a: theAnswer += 1-fracL
          else:      theAnswer += fracL
          if rightC:   theAnswer -=1
    if rightC: 
          if xR>a: theAnswer += 1-fracR
          else:      theAnswer +=  fracR
    return theAnswer

def getFibre2SiPM(modules):
   sGeo = ROOT.gGeoManager
   nav = sGeo.GetCurrentNavigator()
   scifi   = modules['Scifi']
   scifi.SiPMOverlap()           # 12 SiPMs per mat, made for horizontal mats, fibres staggered along y-axis.
   sipm = sGeo.FindVolumeFast("SiPMmapVol")
   nav.cd("/cave_1/volTarget_1/ScifiVolume_1000000/ScifiHorPlaneVol_0/HorMatVolume_1010000")
   matNode = nav.GetCurrentNode()   # example mat
   mat = matNode.GetVolume()   # example mat
   fibresSiPM = {}
   fibresRadius = False
   offSet = matNode.GetMatrix().GetTranslation()[1]
   for fibre in mat.GetNodes():
          if not fibresRadius:  fibresRadius=fibre.GetVolume().GetShape().GetDX()
          fID = fibre.GetNumber()%10000     # local fibre number, global fibre number = SOM+fID
                                                                                    # S=station, O=orientation, M=mat
          a = offSet + fibre.GetMatrix().GetTranslation()[1]
      # check for overlap with any of the SiPM channels
          for nSiPM in range(0,4):         # 12 SiPMs total and 4 SiPMs per mat
                 vol = sipm.GetNodes()[nSiPM]
                 trans0 = vol.GetMatrix().GetTranslation()[1]
                 # print("0   ",vol.GetName(),trans0[0],trans0[1],trans0[2])
                 for iSiPM in vol.GetVolume().GetNodes():  # 2 volumes with gap
                     trans1 = iSiPM.GetMatrix().GetTranslation()[1]
                     # print("1        ",iSiPM.GetName(),trans1[0],trans1[1],trans1[2])
                     for x in iSiPM.GetVolume().GetNodes():    # 64 channels
                        transx    = x.GetMatrix().GetTranslation()[1]
                        xcentre = transx+trans1+trans0
                        # print('debug',iSiPM.GetName(),xcentre,x.GetNumber(),x.GetName(),x.GetMatrix().GetTranslation()[0],x.GetMatrix().GetTranslation()[1],x.GetMatrix().GetTranslation()[2])
                        # print("2                    ",trans0,trans1,transx)
                        dSiPM = x.GetVolume().GetShape().GetDY()
                        if abs(xcentre-a)>4*fibresRadius: continue # no need to check further
                        W = area(a,fibresRadius,xcentre-dSiPM,xcentre+dSiPM)
                        if W<0: continue
                        N = x.GetNumber()
                        # print('debug',N,fID,a,x.GetName(),xcentre-dSiPM,xcentre+dSiPM,W)
                        if not N in fibresSiPM:     fibresSiPM[N] = {}
                        fibresSiPM[N][fID] = {'weight':W,'xpos':a}
   return fibresSiPM

def SiPMfibres(F):
	Finv = {}
	for sipm in F:
		for fibre in F[sipm]:
			if not fibre in Finv: Finv[fibre]={}
			Finv[fibre][sipm]=F[sipm][fibre]
	return Finv

# get mapping from C++
def getFibre2SiPMCPP(modules):
	scifi   = modules['Scifi']
	scifi.SiPMmapping()
	F=scifi.GetSiPMmap()
	fibresSiPM = {}
	for x in F:
		fibresSiPM[x.first]={}
		for z in x.second:
			fibresSiPM[x.first][z.first]={'weight':z.second[0],'xpos':z.second[1]}
	return fibresSiPM

def getSiPM2FibreCPP(modules):
	scifi   = modules['Scifi']
	X=scifi.GetFibresMap()
	siPMFibres = {}
	for x in X:
		siPMFibres[x.first]={}
		for z in x.second:
			siPMFibres[x.first][z.first]={'weight':z.second[0],'xpos':z.second[1]}
	return siPMFibres

from array import array
def localPosition(fibresSiPM):
   meanPos = {}
   for N in fibresSiPM:
        m = 0
        w = 0
        for fID in fibresSiPM[N]:
            m+=fibresSiPM[N][fID]['weight']*fibresSiPM[N][fID]['xpos']
            w+=fibresSiPM[N][fID]['weight']
        meanPos[N] = m/w
   return meanPos

h={}
import rootUtils as ut
def overlap(F,Finv):
   ut.bookHist(h,'W','overlap/fibre',110,0.,1.1)
   ut.bookHist(h,'C','coverage',50,0.,10.)
   ut.bookHist(h,'S','fibres/sipm',5,-0.5,4.5)
   ut.bookHist(h,'Eff','efficiency',100,0.,1.)
   for n in F:
     C=0
     for fid in F[n]:
          rc = h['W'].Fill(F[n][fid]['weight'])
          C+=F[n][fid]['weight']
     rc = h['C'].Fill(C)
   for n in Finv:
     E=0
     for sipm in Finv[n]:
          E+=Finv[n][sipm]['weight']
     rc = h['Eff'].Fill(E)
     rc = h['S'].Fill(len(Finv[n]))

def test(chan):
    for x in F['VertMatVolume'][chan]:
            print('%6i:%5.2F'%(x,F['VertMatVolume'][chan][x])) 

def inspectSiPM():
	SiPMmapVol = sGeo.FindVolumeFast("SiPMmapVol")
	for l1 in  SiPMmapVol.GetNodes():
		t1 = l1.GetMatrix().GetTranslation()[1]
		print(l1.GetName(),t1)
		for l2 in  l1.GetVolume().GetNodes():
			t2 = l2.GetMatrix().GetTranslation()[1]
			print("       ",l2.GetName(),t2)
			for l3 in  l2.GetVolume().GetNodes():
				t3 = l3.GetMatrix().GetTranslation()[1]
				dy = l3.GetVolume().GetShape().GetDY()
				print("                     ", l3.GetName(),t3,t1+t2+t3,dy)



