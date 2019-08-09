import ROOT as r
import os,sys,getopt
import rootUtils as ut
import shipunit as u
import darkphoton
from ShipGeoConfig import ConfigRegistry 
from decorators import *
from rootpyPickler import Unpickler
from array import array
import shipRoot_conf
import dpProductionRates as dputil
import math as m
import numpy as np
from decimal import Decimal

shipRoot_conf.configure() 
try:
    opts, args = getopt.getopt(sys.argv[1:], "f:g:", ["nEvents=","geoFile="])
except getopt.GetoptError:
    print 'no file'
    sys.exit()
for o,a in opts:
    if o in ('-f',): inputFile = a
    if o in ('-g', '--geoFile',): geoFile = a
 
tmp=inputFile.replace("/eos/experiment/ship/data/DarkPhoton/PBC-June-3/190514/reco/","")
tmp1=tmp.replace('_rec.root','')
tmp2=tmp1.replace('mass','')
tmp3=tmp2.replace('eps','')     
out=tmp3.split('_') 
pro=out[0]
mass_mc=float(out[1])
eps=float(out[2])
#mass_mc=Decimal(out[1])
#eps=Decimal(out[2])

eosship =  r.gSystem.Getenv("EOSSHIP")
eospath = eosship+inputFile
f = r.TFile.Open(eospath)
sTree=f.cbmsim
eospath = eosship+geoFile
fgeo = r.TFile.Open(eospath)
sGeo = r.gGeoManager

upkl    = Unpickler(fgeo)
ShipGeo = upkl.load('ShipGeo')
ecalGeoFile = ShipGeo.ecal.File
hcalGeoFile = ShipGeo.hcal.File 
dy = ShipGeo.Yheight/u.m
MeasCut=25


# -----Create geometry----------------------------------------------
import shipDet_conf
run = r.FairRunSim()
run.SetName("TGeant4")  # Transport engine
run.SetOutputFile(ROOT.TMemFile('output', 'recreate'))  # Output file
run.SetUserConfig("g4Config_basic.C") # geant4 transport not used, only needed for the mag field
rtdb = run.GetRuntimeDb()
# -----Create geometry----------------------------------------------
modules = shipDet_conf.configure(run,ShipGeo)

import geomGeant4
if hasattr(ShipGeo.Bfield,"fieldMap"):
  fieldMaker = geomGeant4.addVMCFields(ShipGeo, '', True, withVirtualMC = False)
else:
  print "no fieldmap given, geofile too old, not anymore support"
  exit(-1)
sGeo   = fgeo.FAIRGeom
geoMat =  r.genfit.TGeoMaterialInterface()
ROOT.genfit.MaterialEffects.getInstance().init(geoMat)
bfield = r.genfit.FairShipFields()
bfield.setField(fieldMaker.getGlobalField())
fM = r.genfit.FieldManager.getInstance()
fM.init(bfield)

volDict = {}
i=0
for x in ROOT.gGeoManager.GetListOfVolumes():
 volDict[i]=x.GetName()
 i+=1

# prepare veto decisions
import shipVeto
veto = shipVeto.Task(sTree)
vetoDets={}

PDG = r.TDatabasePDG.Instance()

import TrackExtrapolateTool 
targ=r.TVector3(0,0,ShipGeo.target.z0)

def dist2InnerWall(X,Y,Z):
    dist = 0
    node = sGeo.FindNode(X,Y,Z)
    if ShipGeo.tankDesign < 5:
        if not 'cave' in node.GetName(): return dist  # TP 
    else:
        if not 'decayVol' in node.GetName(): return dist
    start = array('d',[X,Y,Z])
    nsteps = 8
    dalpha = 2*r.TMath.Pi()/nsteps
    rsq = X**2+Y**2
    minDistance = 100 *u.m
    for n in range(nsteps):
        alpha = n * dalpha
        sdir  = array('d',[r.TMath.Sin(alpha),r.TMath.Cos(alpha),0.])
        node = sGeo.InitTrack(start, sdir)
        nxt = sGeo.FindNextBoundary()
        if ShipGeo.tankDesign < 5 and nxt.GetName().find('I')<0: return 0    
        distance = sGeo.GetStep()
        if distance < minDistance  : minDistance = distance
    return minDistance

def checkFiducialVolume(sTree,tkey,dy):
# extrapolate track to middle of magnet and check if in decay volume
   inside = True
   #if not fiducialCut: return True
   fT = sTree.FitTracks[tkey]
   rc,pos,mom = TrackExtrapolateTool.extrapolateToPlane(fT,ShipGeo.Bfield.z)
   if not rc: return False
   if not dist2InnerWall(pos.X(),pos.Y(),pos.Z())>0: return False
   return inside

def isInFiducial(X,Y,Z):
    if Z > ShipGeo.TrackStation1.z : return False
    if Z < ShipGeo.vetoStation.z+100.*u.cm : return False
    if dist2InnerWall(X,Y,Z)<5*u.cm: return False
    return True 
 
def findmum():
    for dp_ind,dp_tr in enumerate(sTree.MCTrack):
        if dp_tr.GetPdgCode()==9900015 or dp_tr.GetPdgCode()==4900023:
            mum_id=dp_tr.GetMotherId()
            dp_id=dp_ind
            #print dp_id
            if pro=='qcd' and dp_id==0: continue
            #print mum_id 
            mum_pdg=sTree.MCTrack[mum_id].GetPdgCode()
            if pro=='meson': xsw = dputil.getDPprodRate(mass_mc,eps,'meson',mum_pdg)
            else: xsw = dputil.getDPprodRate(mass_mc,eps,pro,0) 
            wg = sTree.MCTrack[dp_id].GetWeight()
            #print dp_id 
            dp_mom=r.TVector3(sTree.MCTrack[dp_id].GetPx(),sTree.MCTrack[dp_id].GetPy(),sTree.MCTrack[dp_id].GetPz())
            dp_mag=sTree.MCTrack[dp_id].GetP()
            break
        else: xsw,wg,dp_id,dp_mom,dp_mag=-99,-99,-99,-99,-99
    return xsw,wg,dp_id,dp_mom,dp_mag

def ImpactParameter(point,tPos,tMom):
    t = 0
    if hasattr(tMom,'P'): P = tMom.P()
    else:                 P = tMom.Mag()
    for i in range(3):   t += tMom(i)/P*(point(i)-tPos(i))
    dist = 0
    for i in range(3):   dist += (point(i)-tPos(i)-t*tMom(i)/P)**2
    dist = r.TMath.Sqrt(dist)
    return dist

def IP(X,Y,Z,dp_M,dp_Mag):
    target = r.TVector3(0., 0., ShipGeo.target.z0)
    delta = 0.
    delta += (target(0) - X) * dp_M(0)/dp_Mag
    delta += (target(1) - Y) * dp_M(1)/dp_Mag
    delta += (target(2) - Z) * dp_M(2)/dp_Mag
    ip = 0.
    ip += (target(0) - X - delta*dp_M(0)/dp_Mag)**2.
    ip += (target(1) - Y - delta*dp_M(1)/dp_Mag)**2.
    ip += (target(2) - Z - delta*dp_M(2)/dp_Mag)**2.
    return r.TMath.Sqrt(ip)

def find_signal(pdg):
    if abs(pdg)== 11 or abs(pdg)== 13 or abs(pdg)== 111 or abs(pdg)== 321 or abs(pdg)== 211 or abs(pdg)== 22 or abs(pdg)== 2212: return True

def find_lepton(pdg):
    if abs(pdg) == 11 or abs(pdg) == 13 or abs(pdg) == 15: return True

def find_stablehadron(pdg):
    if abs(pdg) == 111 or abs(pdg) == 211 or abs(pdg) == 321 or abs(pdg) == 2212: return True

def checkTrue(sTree, dp_id):
    #lepto=0
    PID=[]
    for mc,tr in enumerate(sTree.MCTrack):
        pid = tr.GetPdgCode()
        mom = tr.GetMotherId() 
        if mc>1:
            mom_pid=sTree.MCTrack[mom].GetPdgCode()
            if abs(pid)>9 and abs(pid)!=21:
                if mom==dp_id:#leptons in all process and/or hadrons in meson process
                    PID.append(mc)
                elif (abs(pid)>6 or abs(pid)!=21) and (abs(mom_pid)<7 or abs(mom_pid)==21):#hadrons in qcd and pbrem
                    PID.append(mc)

    return PID

h={}
ut.bookHist(h,'DOCA','DOCA')

ut.bookHist(h,'DP','invariant Mass (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPW','invariant Mass with Weights (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPves','invariant Mass (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPvesW','invariant Mass with Weights (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPang','invariant Mass (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPangW','invariant Mass with Weights (GeV)',50,0.,mass_mc+5.)

ut.bookHist(h,'DP_e','invariant Mass (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPW_e','invariant Mass with Weights (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPves_e','invariant Mass (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPvesW_e','invariant Mass with Weights (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPang_e','invariant Mass (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPangW_e','invariant Mass with Weights (GeV)',50,0.,mass_mc+5.)

ut.bookHist(h,'DP_mu','invariant Mass (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPW_mu','invariant Mass with Weights (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPves_mu','invariant Mass (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPvesW_mu','invariant Mass with Weights (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPang_mu','invariant Mass (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPangW_mu','invariant Mass with Weights (GeV)',50,0.,mass_mc+5.)

ut.bookHist(h,'DP_tau','invariant Mass (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPW_tau','invariant Mass with Weights (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPves_tau','invariant Mass (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPvesW_tau','invariant Mass with Weights (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPang_tau','invariant Mass (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPangW_tau','invariant Mass with Weights (GeV)',50,0.,mass_mc+5.)

ut.bookHist(h,'DP_had','invariant Mass (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPW_had','invariant Mass with Weights (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPves_had','invariant Mass (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPvesW_had','invariant Mass with Weights (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPang_had','invariant Mass (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPangW_had','invariant Mass with Weights (GeV)',50,0.,mass_mc+5.)

ut.bookHist(h,'DP_oth','invariant Mass (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPW_oth','invariant Mass with Weights (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPves_oth','invariant Mass (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPvesW_oth','invariant Mass with Weights (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPang_oth','invariant Mass (GeV)',50,0.,mass_mc+5.)
ut.bookHist(h,'DPangW_oth','invariant Mass with Weights (GeV)',50,0.,mass_mc+5.)

ut.bookHist(h,'DPangW_test','invariant Mass with Weights (GeV)',50,0.,mass_mc+5.)
def myEventLoop(n):
    #print n
    rc=sTree.GetEntry(n)
    fm=findmum()
    xsw=fm[0]
    wg=fm[1]
    dp_id=fm[2]
    dp_M=fm[3]
    dp_Mag=fm[4]
    MA,MAS=[],[] 
    DPmom=r.TLorentzVector(0.,0.,0.,0.)
    DPma=r.TLorentzVector(0.,0.,0.,0.) 
    dau=-99
    DOC=[]
    TR=0
    T1,T2=[],[]
    VES=0 
    r_track=0
    f_track=0
    RECO=0
    debug=0
    e, mu, tau, had, oth_a, oth_v  = 0, 0, 0, 0, 0, 0
    #print "mom find"
    if xsw==-99 and wg==-99 and dp_id==-99: return
    #print "mom found"
    h['DPW'].Fill(mass_mc) 
    dau=checkTrue(sTree,dp_id)
    for xxx in dau:
        if abs(sTree.MCTrack[xxx].GetPdgCode())==11:
            doca=sTree.MCTrack[xxx].GetStartT() 
            TR+=1
            e+=1
        elif abs(sTree.MCTrack[xxx].GetPdgCode())==13:
            doca=sTree.MCTrack[xxx].GetStartT() 
            TR+=1
            mu+=1
        elif abs(sTree.MCTrack[xxx].GetPdgCode())==15:
            doca=sTree.MCTrack[xxx].GetStartT()
            TR+=1
            tau+=1
        else:
            doca=sTree.MCTrack[xxx].GetStartT() 
            had+=1

    for F,FIT in enumerate(sTree.FitTracks):
        fitStatus = FIT.getFitStatus()
        if not fitStatus.isFitConverged(): continue
        xx = FIT.getFittedState()
        mc = sTree.MCTrack[sTree.fitTrack2MC[F]]
        vtx=r.TVector3(mc.GetStartX(), mc.GetStartY(), mc.GetStartZ())
        mom=r.TVector3(mc.GetPx(), mc.GetPy(), mc.GetPz())
        #print "ftrack"
        if not isInFiducial(vtx.X(),vtx.Y(),vtx.Z()): continue
        #print "ftrack vessel"
        if find_signal(xx.getPDG()):
            #print "ftrack signal"
            f_track+=1
        else:
            oth_v+=1
            #print 'fit track is rejected?', xx.getPDG()
        if not checkFiducialVolume(sTree,F,dy): continue
        nmeas = fitStatus.getNdf()
        chi2 = fitStatus.getChi2()
        if not nmeas>25: continue
        if not chi2/nmeas<5: continue
        if not xx.getMomMag()>1.: continue
        #if not mc.GetStartT()<=1.:continue
        h['DPangW_test'].Fill(mc.GetStartT()-doca)
        if not (mc.GetStartT()-doca)<=1.: continue
        if find_signal(xx.getPDG()):
            RECO+=1
        else:
            oth_a+=1
            #print 'reco is rejected?', xx.getPDG()

    if e>1: 
        h['DP_e'].Fill(mass_mc)
    if mu>1:
        h['DP_mu'].Fill(mass_mc)
    if tau>1:
        h['DP_tau'].Fill(mass_mc)
    if had>0:
        h['DP_had'].Fill(mass_mc)

    if f_track>1:
        if e>1:
            h['DPvesW_e'].Fill(mass_mc,wg)
            h['DPves_e'].Fill(mass_mc)  
        if mu>1:
            h['DPvesW_mu'].Fill(mass_mc,wg)
            h['DPves_mu'].Fill(mass_mc) 
        if had>0:
            h['DPvesW_had'].Fill(mass_mc,wg)
            h['DPves_had'].Fill(mass_mc)         
        if tau>1:
            h['DPvesW_tau'].Fill(mass_mc,wg)
            h['DPves_tau'].Fill(mass_mc)

    if f_track>1 and RECO>1:
        if e>1:
            h['DPang_e'].Fill(mass_mc,wg*xsw)
            h['DPangW_e'].Fill(mass_mc,wg)  
        if mu>1:
            h['DPang_mu'].Fill(mass_mc,wg*xsw)
            h['DPangW_mu'].Fill(mass_mc,wg) 
        if had>0:
            h['DPang_had'].Fill(mass_mc,wg*xsw)
            h['DPangW_had'].Fill(mass_mc,wg)         
        if tau>1:
            h['DPang_tau'].Fill(mass_mc,wg*xsw)
            h['DPangW_tau'].Fill(mass_mc,wg)

    if e>1 or mu>1 or tau>1 or had>0:
        h['DP'].Fill(mass_mc)
        if f_track>1:
            h['DPvesW'].Fill(mass_mc,wg)
            h['DPves'].Fill(mass_mc)
            if RECO>1: 
                #print "reco"
                h['DPangW'].Fill(mass_mc)       
                h['DPang'].Fill(mass_mc,wg*xsw)
            else:
                h['DPangW_oth'].Fill(mass_mc,wg)
                h['DPang_oth'].Fill(mass_mc,wg*xsw)
        else: 
            h['DPves_oth'].Fill(mass_mc)
            h['DPvesW_oth'].Fill(mass_mc,wg) 
    elif TR<2 and had==0: 
        #Dump(sTree.MCTrack)
        h['DP_oth'].Fill(mass_mc)
        #print "one track", e, mu, tau, had

nEvents =sTree.GetEntries()
#print nEvents
#nEvents = 200
#Dump(sTree.MCTrack)
for n in range(nEvents):
    myEventLoop(n)
#print "tau_v", h['DPves_tau'].Integral()
#print "e_v",   h['DPves_e'].Integral()
#print "mu_v",  h['DPves_mu'].Integral()
#print "had_v", h['DPves_had'].Integral()
#print "oth_v", h['DPves_oth'].Integral()

#print "tau_a", h['DPangW_tau'].Integral()
#print "e_a",   h['DPangW_e'].Integral()
#print "mu_a",  h['DPangW_mu'].Integral()
#print "had_a", h['DPangW_had'].Integral()
#print "oth_a", h['DPangW_oth'].Integral()

#print "e ", h['DP_e'].Integral()
#print "mu ", h['DP_mu'].Integral()
#print "tau ", h['DP_tau'].Integral()
#print "had ", h['DP_had'].Integral()
#print "oth ", h['DP_oth'].Integral()

#print "Reco Eff", h['DPangW'].Integral()
#print "Vessel ",  h['DPves'].Integral() 

#print "dd/gen", h['DP'].Integral()/h['DPW'].Integral()

o1 = tmp1+"_Ana_e.dat"
o2 = tmp1+"_Ana_mu.dat"
o3 = tmp1+"_Ana_tau.dat" 
o4 = tmp1+"_Ana_hadron.dat"

o6 = tmp1+"_Ana_other.dat"
o7 = tmp1+"_Ana_all.dat"

o8 = tmp1+"_Ana_sum.dat"

o9 = tmp1+"_Ana_rate1.dat"
o10 = tmp1+"_Ana_rate2.dat"

a=open(o1,'w+')
b=open(o2,'w+')
c=open(o3,'w+')
d=open(o4,'w+')

f=open(o6,'w+')
g=open(o7,'w+')

H=open(o8,'w+')

k=open(o9,'w+')
l=open(o10,'w+')

Sum,ves_s,ang_s= 0., 0., 0.

if Decimal(h['DP_e'].Integral()):
    #print float(h['DPangW_e'].Integral()), float(h['DPvesW_e'].Integral())
    if Decimal(h['DPvesW_e'].Integral()):
        ang_s+=float(h['DPangW_e'].Integral())
        ves_s+=float(h['DPvesW_e'].Integral())
        rf = Decimal(h['DPangW_e'].Integral())/Decimal(h['DPvesW_e'].Integral())
    if not Decimal(h['DPvesW_e'].Integral()): rf = 0.
    Sum+=float(h['DP_e'].Integral())
    a.write('%.5g %s %.9E %.9E %.9E' %(mass_mc, eps, Decimal(h['DP_e'].Integral())/Decimal(h['DP'].Integral()), Decimal(h['DPvesW_e'].Integral())/Decimal(h['DP_e'].Integral()), rf))
    a.write('\n')

if Decimal(h['DP_mu'].Integral()):
    #print float(h['DPangW_mu'].Integral()), float(h['DPvesW_mu'].Integral())
    if Decimal(h['DPvesW_mu'].Integral()): 
        cf = Decimal(h['DPangW_mu'].Integral())/Decimal(h['DPvesW_mu'].Integral())
        ang_s+=float(h['DPangW_mu'].Integral())
        ves_s+=float(h['DPvesW_mu'].Integral())
    if not Decimal(h['DPvesW_mu'].Integral()): cf = 0.
    Sum+=float(h['DP_mu'].Integral())
    b.write('%.5g %s %.9E %.9E %.9E' %(mass_mc, eps, Decimal(h['DP_mu'].Integral())/Decimal(h['DP'].Integral()), Decimal(h['DPvesW_mu'].Integral())/Decimal(h['DP_mu'].Integral()), cf))
    b.write('\n')

if Decimal(h['DP_tau'].Integral()):
    if Decimal(h['DPvesW_tau'].Integral()): 
        lf = Decimal(h['DPangW_tau'].Integral())/Decimal(h['DPvesW_tau'].Integral())
        ang_s+=float(h['DPangW_tau'].Integral())
        ves_s+=float(h['DPvesW_tau'].Integral())
    if not Decimal(h['DPvesW_tau'].Integral()): lf = 0.
    Sum+=float(h['DP_tau'].Integral())
    c.write('%.5g %s %.9E %.9E %.9E' %(mass_mc, eps, Decimal(h['DP_tau'].Integral())/Decimal(h['DP'].Integral()), Decimal(h['DPvesW_tau'].Integral())/Decimal(h['DP_tau'].Integral()), lf))
    c.write('\n')

if Decimal(h['DP_had'].Integral()):
    if Decimal(h['DPvesW_had'].Integral()):
        bf = Decimal(h['DPangW_had'].Integral())/Decimal(h['DPvesW_had'].Integral())
        ang_s+=float(h['DPangW_had'].Integral())
        ves_s+=float(h['DPvesW_had'].Integral())
    if not Decimal(h['DPvesW_had'].Integral()): bf = 0.
    Sum+=float(h['DP_had'].Integral())
    d.write('%.5g %s %.9E %.9E %.9E' %(mass_mc, eps, Decimal(h['DP_had'].Integral())/Decimal(h['DP'].Integral()), Decimal(h['DPvesW_had'].Integral())/Decimal(h['DP_had'].Integral()), bf))
    d.write('\n')

if Decimal(h['DP'].Integral()):
    if Decimal(h['DPvesW'].Integral()): df= Decimal(h['DPangW_oth'].Integral())/Decimal(h['DPvesW'].Integral())
    if not Decimal(h['DPvesW'].Integral()): df = 0.
    f.write('%.5g %s %.9E %.9E %.9E' %(mass_mc, eps, Decimal(h['DP_oth'].Integral())/Decimal(h['DPW'].Integral()), Decimal(h['DPvesW_oth'].Integral())/Decimal(h['DP'].Integral()), df))
    f.write('\n')#mass, epsilon, how much we lose from 2 track selection, how much we lose in vessel, how much we lose in final selection
    if Decimal(ves_s): af = Decimal(ang_s/ves_s)
    if not Decimal(ves_s): af = 0.
    g.write('%.5g %s %.9E %.9E %.9E %.9E' %(mass_mc, eps, Decimal(h['DP'].Integral())/Decimal(h['DPW'].Integral()), Decimal(Sum)/Decimal(h['DP'].Integral()), Decimal(ves_s)/Decimal(Sum), af))
    g.write('\n')
    H.write('%.5g %s %.9E %.9E %.9E %.9E %.9E' %(mass_mc, eps, nEvents, Decimal(h['DPW'].Integral()), Decimal(h['DP'].Integral()), Decimal(h['DPves'].Integral()), Decimal(h['DPangW'].Integral())))
    H.write('\n')

NomL  = 0.
DenL  = 0.
DP_instance=darkphoton.DarkPhoton(mass_mc,eps)

if Decimal(h['DP_e'].Integral()):
    BR1=DP_instance.findBranchingRatio('A -> e- e+')
    NomL+=float(h['DPang_e'].Integral())
    DenL+=float(h['DP_e'].Integral())*BR1
if Decimal(h['DP_mu'].Integral()):
    BR2=DP_instance.findBranchingRatio('A -> mu- mu+')
    NomL+=float(h['DPang_mu'].Integral())
    DenL+=float(h['DP_mu'].Integral())*BR2
if Decimal(h['DP_tau'].Integral()):
    BR3=DP_instance.findBranchingRatio('A -> tau- tau+')
    NomL+=float(h['DPang_tau'].Integral())
    DenL+=float(h['DP_tau'].Integral())*BR3
if Decimal(h['DP'].Integral()):
    RecLW=NomL/DenL*2.0e+20
    RecW=Decimal(h['DPang'].Integral()/h['DP'].Integral()*2.0e+20)#weighted Selected/weighted Vessel
    k.write('%.5g %s %.9E' %(mass_mc, eps, RecW)) 
    k.write('\n')       
    l.write('%.5g %s %.9g' %(mass_mc, eps, RecLW)) 
    l.write('\n')

#print mass_mc, eps, RecW
a.close()
b.close()
c.close()
d.close()
f.close()
g.close()
H.close()
k.close()
l.close()

#print Sum, h['DP'].Integral()
#print ves_s, h['DPvesW'].Integral()
#print ang_s, h['DPangW'].Integral()

hfile =tmp1+"_Ana.root" 
r.gROOT.cd()
ut.writeHists(h,hfile)

#print hfile
#print h['DP'].Integral() 
#print RecW
#print RecLW
