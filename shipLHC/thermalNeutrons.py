#!/usr/bin/env python 
import ROOT
from decorators import *

# setenv NeutronHPCrossSections  ${G4NEUTRONHPDATA}  see https://geant4.web.cern.ch/sites/geant4.web.cern.ch/files//geant4/support/training/users_workshop_2002/lectures/models.pdf 

import os
import shipunit as u
from argparse import ArgumentParser
ROOT.gROOT.ProcessLine('#include "Geant4/G4UIterminal.hh"')
ROOT.gROOT.ProcessLine('#include "Geant4/G4Neutron.hh"')
ROOT.gROOT.ProcessLine('#include "Geant4/G4ProcessManager.hh"')
ROOT.gROOT.ProcessLine('#include "Geant4/G4ParticleHPThermalScattering.hh"')
ROOT.gROOT.ProcessLine('#include "Geant4/G4ParticleHPElastic.hh"')
ROOT.gROOT.ProcessLine('#include "Geant4/G4HadronElasticProcess.hh"')
ROOT.gROOT.ProcessLine('#include "Geant4/G4HadronicProcessStore.hh"')
ROOT.gROOT.ProcessLine('#include "Geant4/G4ParticleHPThermalScatteringData.hh"')
ROOT.gROOT.ProcessLine('#include "Geant4/G4ParticleHPElasticData.hh"')
ROOT.gROOT.ProcessLine('#include "Geant4/G4GenericPhysicsList.hh"')
ROOT.gROOT.ProcessLine('#include "Geant4/G4RunManager.hh"')
ROOT.gROOT.ProcessLine('#include "Geant4/G4TransportationManager.hh"')

parser = ArgumentParser()
parser.add_argument("-b", "--heartbeat",  dest="heartbeat", type=int,  help="progress report",            default=10000)
parser.add_argument("-n", "--nEvents",      dest="nEvents",     type=int,  help="number of events",        default=100)
parser.add_argument("-r", "--run",                 dest="run",       type=int,  help="production sequence number", default=0)
parser.add_argument('--material',               dest='targetMaterial',      type=str,help="target material BoronCarbide or  Boratedpolyethylene",                     default="BoronCarbide")
parser.add_argument('--thick',                      dest='targetLength',      type=float,help="target thickness",                     default=0.1)
parser.add_argument('-c', '--command',    dest='command',              help="command")
parser.add_argument("--Estart",  dest="Estart",   help="start of energy range of particle gun (default= 0 MeV)", required=False, default=1E-20, type=float)
parser.add_argument("--Eend",    dest="Eend",    help="end of energy range of particle gun  (default=10 MeV)", required=False, default=0.01, type=float)
parser.add_argument("--pID",     dest="pID",     help="id of particle used by the gun (default=2112)", required=False, default=2112, type=int)
parser.add_argument("--setup",     dest="neutron",     help="setup for absorptionLength or neutron in cold box)", required=False, action='store_true')
options = parser.parse_args()

# -------------------------------------------------------------------
logEstart = int(ROOT.TMath.Log10(options.Estart))
logEend  = int(ROOT.TMath.Log10(options.Eend))
outFile = 'thermNeutron_'+options.targetMaterial+'_'+str(options.targetLength)+'_'+str(logEstart)+'_'+str(logEend)+'_'+str(options.run)+'.root'
if options.neutron:  outFile = 'thermNeutron_%s_coldbox_%s-%iM.root'%(options.targetMaterial,str(options.run),options.nEvents/1000000.)
parFile = outFile.replace('thermNeutron','params-thermNeutron')

# -----Timer--------------------------------------------------------
timer = ROOT.TStopwatch()
timer.Start()

# -----Create simulation run----------------------------------------
run = ROOT.FairRunSim()
run.SetName('TGeant4')  # Transport engine
run.SetOutputFile(outFile)  # Output file
run.SetUserConfig("g4ConfigNeutron.C") # user configuration file default g4Config.C

# -----Create PrimaryGenerator--------------------------------------
primGen = ROOT.FairPrimaryGenerator()

if options.neutron:
   Neutrongen = ROOT.NeutronGenerator_FLUKA()
   primGen.AddGenerator(Neutrongen)
else:
   myPgun = ROOT.FairBoxGenerator(options.pID,1)
   myPgun.SetEkinRange(options.Estart,options.Eend)
   myPgun.SetPhiRange(0, 0) # // Azimuth angle range [degree]
   myPgun.SetThetaRange(0,0)
   myPgun.SetXYZ(0.,0.,-1.)
   primGen.AddGenerator(myPgun)

ROOT.FairLogger.GetLogger().SetLogScreenLevel("WARNING") # otherwise stupid printout for each event

# -----Materials----------------------------------------------
run.SetMaterials("media.geo")
# -----Create geometry----------------------------------------------
cave = ROOT.ShipCave("CAVE")
cave.SetGeometryFileName("caveXS.geo")
run.AddModule(cave)

target = ROOT.boxTarget()
target.SetTarget(options.targetMaterial,options.targetLength*u.cm,not options.neutron)
run.AddModule(target)

#
run.SetGenerator(primGen)

# -----Initialize simulation run------------------------------------
run.Init()
from decorators import *

neutron = ROOT.G4Neutron.Neutron()
pManager = neutron.GetProcessManager()

thermal = False
if thermal:
   process = pManager.GetProcess("hadElastic")
   if process: pManager.RemoveProcess(process)
   process1 = ROOT.G4HadronElasticProcess()
   pManager.AddDiscreteProcess(process1)
   model1a = ROOT.G4ParticleHPElastic()
   eV = 1E-6
   model1a.SetMinEnergy(4*eV)  # valid after ThermalScattering, EMax 4 eV, 1 = MeV
   process1.RegisterMe(model1a)
   process1.AddDataSet(ROOT.G4ParticleHPElasticData())
   model1b = ROOT.G4ParticleHPThermalScattering()
   process1.RegisterMe(model1b)
   process1.AddDataSet(ROOT.G4ParticleHPThermalScatteringData())
pManager.DumpInfo()

gMC = ROOT.TVirtualMC.GetMC()
fStack = gMC.GetStack()
fStack.SetMinPoints(-1)
fStack.SetEnergyCut(-1.)

# -----Start run----------------------------------------------------
run.Run(options.nEvents)

# -----Finish-------------------------------------------------------
timer.Stop()
rtime = timer.RealTime()
ctime = timer.CpuTime()
print(' ')
print("Macro finished succesfully.") 
print("Output file is ",  outFile)
print("Real time ",rtime, " s, CPU time ",ctime,"s")

run.CreateGeometryFile("geofile-"+outFile)
sGeo = ROOT.gGeoManager
sGeo.SetNmeshPoints(10000)
sGeo.CheckOverlaps(0.1)  # 1 micron takes 5minutes
sGeo.PrintOverlaps()


h={}
import rootUtils as ut
def count(hFile = outFile):
   f=ROOT.TFile(hFile)
   ut.bookHist(h,'E',';log10(Ekin [MeV])',1000,-10.,4.)
   ut.bookHist(h,'Epassed',';log10(Ekin [MeV])',1000,-10.,4.)
   ut.bookHist(h,'Lab',';absorption Length vs logE',1000,-10.,4.,500,-0.1,10.)
   ut.bookHist(h,'Labz',';absorption Length vs logE',1000,-10.,4.,500,-0.1,10.)
   ut.bookHist(h,'xyz','',   100,-0.1,0.1,100,-0.1,0.1,200,-1.,1.)
   ut.bookHist(h,'dxyz','',100,-0.1,0.1,100,-0.1,0.1,200,-1.,1.)
   ut.bookHist(h,'Epassed',';log10(Ekin [MeV])',1000,-10.,4.)
   Npassed = 0
   for sTree in f.cbmsim:
       N = sTree.MCTrack[0]
       Ekin = N.GetP()**2/(2*N.GetMass())*1000.
       logEkin = ROOT.TMath.Log10(Ekin)
       rc = h['E'].Fill(logEkin)
       for p in sTree.vetoPoint:
          if not p.PdgCode()==2112:  continue
          if p.GetDetectorID()==1 :
             mean = ROOT.TVector3(p.GetX(),p.GetY(),p.GetZ())
             end = p.LastPoint()
             D = 2*(end-mean)
             start = 2*mean-end
             rc = h['Lab'].Fill(logEkin,D.Mag())
             rc = h['Labz'].Fill(logEkin,D.Z())
             rc = h['xyz'].Fill(start.X(),start.Y(),start.Z())
             rc = h['dxyz'].Fill(end.X(),end.Y(),end.Z())
          else:
               Npassed+=1
               rc = h['Epassed'].Fill(ROOT.TMath.Log10(Ekin))
   h['Eff'] = ROOT.TEfficiency(h['Epassed'],h['E'])
   h['Eff'].Draw()
   print(Npassed)

pathToPlots = "/mnt/hgfs/microDisk/CERNBOX/SND@LHC/Thermal Neutrons/"
def myPrint(tc,tname):
   for z in ['.png','.pdf','.root']:
      tc.Print(tname+z)
      os.system('mv '+tname+z+' '+pathToPlots)


def absorptionLength():
    for material in ['Boratedpolyethylene','BoronCarbide']:
           for Erange in ['-10_-8','-8_-7','-6_-4']:
               fname = "thermNeutron_"+material+"_100.0_"+Erange+"_0.root"
               count(fname)
               for x in ['Lab','Labz']:
                   hname = x+'_'+material+E 
                   h[hname] = h[x].ProfileX(hname,1,-1,'g')





def absorptionLengthOLD():
 Lfun = ROOT.TF1('Lfun','[0]*(10**x)**[1]',-9,-6)
 Lfun.SetParameter(0,6.4)
 Lfun.SetParameter(1,0.98)
 hFiles = {"thermNeutron_BoronCarbide_X.XX_-E_-E_0.root":[0.08,0.3],"thermNeutron_Boratedpolyethylene_X.XX_0.root":[1.0,100.]}
 # thermNeutron_BoronCarbide_4.0_-8_-7_0.root

 Ls = {0.01:ROOT.kRed,0.1:ROOT.kOrange,0.04:ROOT.kCyan,0.4:ROOT.kBlue,4.0:ROOT.kMagenta}

 for hFile in hFiles:
    material = hFile.split('_')[1]
    ut.bookCanvas(h,'absorb'+material,'',1200,800,1,1)
    h['absorb'+material].cd()
    for L in Ls:
          l = str(L)
          if L<3:  tmp = hFile.replace("X.XX",l).replace(" _-E_-E","")
          else:     tmp = hFile.replace("X.XX",l).replace(" _-E_-E","_-8_-7")
          count(tmp)
          h['Eff_'+l]=h['Eff'].Clone('Eff_'+l)
          h['L_'+l]=ROOT.TGraph()
          h['L_'+l].SetLineColor(Ls[L])
          h['Eff'].Draw()
          g = h['Eff'].GetPaintedGraph()
          for n in range(g.GetN()):
                 logE, p = g.GetPointX(n),g.GetPointY(n)
                 if p>0:
                     absL = -L/ROOT.TMath.Log(p) 
                 else:
                     absL = 0
                 h['L_'+l].SetPoint(n,logE,absL)
    ut.bookHist(h,'L',';logE; L [cm]',100,-9.,-6.)
    h['L'].SetMaximum(hFiles[hFile][0])
    h['L'].SetStats(0)
    h['L'].Draw()
    for L in Ls:
            if L>hFiles[hFile][1]: continue
            h['L_'+str(L)].Draw('same')
            h['L_'+str(0.1)].Fit(Lfun)
    myPrint(h['absorb'+material],'absorbLength'+material)


rate = ROOT.TF1('rate','1./10**x*exp(-[0]/([1]*sqrt(10**x)))',-9,2)
# BoronCarbide:    130cm sqrt(E/MeV)               Boratedpolyethylene  1490cm sqrt(E/MeV)
rate.SetParameter(0,1.)
rate.SetParameter(1,130.)
# BoronCarbide for 0.1cm:                 max rate at 0.13 eV       1cm:  max rate at 16eV           
# Boratedpolyethylene for 0.1cm:  max rate at <0.01 eV     1cm:  max rate at 0.13 eV       4cm:   max rate at 1.6 eV
# attenuation of 1E-7 required.

rate.Draw()

import hepunit as G4Unit
ROOT.gROOT.ProcessLine('#include "Geant4/G4HadronicProcessStore.hh"')

def debugging():
   neutron = ROOT.G4Neutron.Neutron()
   neutron.DumpTable()
   pManager = neutron.GetProcessManager()
   pManager.DumpInfo()
   for p in pManager.GetProcessList(): 
      p.DumpInfo()
   store = ROOT.G4HadronicProcessStore.Instance()
   store.Dump(1)
   runManager = ROOT.G4RunManager.GetRunManager()
   gt = ROOT.G4TransportationManager.GetTransportationManager()
   gn = gt.GetNavigatorForTracking()
   world = gn.GetWorldVolume().GetLogicalVolume()
   vmap = {}
   for da in range(world.GetNoDaughters()):
     vl = world.GetDaughter(da)
     vmap[vl.GetName().c_str()] = vl
     lvl = vl.GetLogicalVolume() 
     mat = lvl.GetMaterial()
     print("%2i  %s  %5.3F g/cm3  %5.2F kg  %s"%(da, vl.GetName(),mat.GetDensity()/G4Unit.g*G4Unit.cm3,lvl.GetMass()/G4Unit.kg,mat.GetName()))
     for n in range(mat.GetNumberOfElements()):
         element = mat.GetElement(n)
         print("      %2i  %s   %4.1F    %5.4F "%(n,element.GetName(),element.GetAtomicMassAmu(),mat.GetFractionVector()[n]))
