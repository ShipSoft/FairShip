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

# get mapping from C++
def getFibre2SiPMCPP(modules):
	scifi   = modules['Scifi']
	scifi.SiPMOverlap()
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
   ut.bookHist(h,'S','fibres/sipm',15,-0.5,14.5)
   ut.bookHist(h,'Eff','efficiency',110,0.,1.1)
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
	sGeo = ROOT.gGeoManager
	SiPMmapVol = sGeo.FindVolumeFast("SiPMmapVol")
	for l1 in  SiPMmapVol.GetNodes():   # 3 mats with 4 SiPMs each and 128 channels
		t1 = l1.GetMatrix().GetTranslation()[1]
		if l1.GetNumber()%1000==0: print( "%s  %5.2F"%(l1.GetName(),(t1)*10.))

def inspectMats():
	sGeo = ROOT.gGeoManager
	ScifiHorPlaneVol = sGeo.FindVolumeFast("ScifiHorPlaneVol")
	for l1 in  ScifiHorPlaneVol.GetNodes():    # 3 mats
		t1 = l1.GetMatrix().GetTranslation()[1]
		print(l1.GetName(),t1)
		for l2 in  l1.GetVolume().GetNodes():
			t2 = l2.GetMatrix().GetTranslation()[1]
			print("       ",l2.GetName(),t2,t1+t2)
def checkFibreCoverage(Finv):
	for mat in range(1,4):
		for row in range(1,7):
			for channel in range(1,473):
				fID = mat*10000+row*1000+channel
				if not fID in Finv: print('missing fibre:',fID)
def checkLocalPosition(fibresSiPM):
	ut.bookHist(h,'delta','central - weighted',100,-20.,20.)
	L = localPosition(fibresSiPM)
	sGeo = ROOT.gGeoManager
	SiPMmapVol = sGeo.FindVolumeFast("SiPMmapVol")
	for l in  SiPMmapVol.GetNodes():
		n  = l.GetNumber()
		ty = l.GetMatrix().GetTranslation()[1]
		delta = ty-L[n]
		rc = h['delta'].Fill(delta*10*1000.)
