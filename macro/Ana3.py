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
shipRoot_conf.configure()
dpMom = False
try:
    opts, args = getopt.getopt(sys.argv[1:], "d:p:m:e:A:g:f:", ["date=","production=","mass=","epsilon=","motherID=","geoFile=","final_dest="])

except getopt.GetoptError:
    print 'no file'
    sys.exit()

for o,a in opts:
    if o in ('-d',): date = a
    if o in ('-p',): pro = a
    if o in ('-m',): mass_mc = a
    if o in ('-e',): eps = a
    if o in ('-A',): dpMom = a
    if o in ('-g', '--geoFile',): geoFile = a
    if o in ('-f',): dest = a
if dpMom: tmp1 = "/eos/experiment/ship/data/DarkPhoton/PBC-June-3/"+date+"/reco/"+pro+"_"+dpMom+"_mass"+mass_mc+"_eps"+eps
if not dpMom: tmp1 = "/eos/experiment/ship/data/DarkPhoton/PBC-June-3/"+date+"/reco/"+pro+"_mass"+mass_mc+"_eps"+eps
inputFile = tmp1+"_rec.root"
#print inputFile
mass_mc=float(mass_mc)
eps=float(eps)
 

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
 
def ImpactParameter(point,tPos,tMom):
    t = 0
    if hasattr(tMom,'P'): P = tMom.P()
    else:                 P = tMom.Mag()
    for i in range(3):   t += tMom(i)/P*(point(i)-tPos(i))
    dist = 0
    for i in range(3):   dist += (point(i)-tPos(i)-t*tMom(i)/P)**2
    dist = r.TMath.Sqrt(dist)
    return dist

def findmum():#this function finds the mother of DP with weight,xs,momentum etc. USED for finding DP event
    for dp_ind,dp_tr in enumerate(sTree.MCTrack):
        if dp_tr.GetPdgCode()==9900015 or dp_tr.GetPdgCode()==4900023:
            mum_id=dp_tr.GetMotherId()
            dp_id=dp_ind
            #print dp_id
            if pro=='qcd' and dp_id==0: continue
            #print mum_id 
            mum_pdg=sTree.MCTrack[mum_id].GetPdgCode()
            #print mum_pdg
            if pro=='meson':
                xsw = dputil.getDPprodRate(mass_mc,eps,'meson',mum_pdg)
                if dpMom=='eta1' and xsw!=0:
                    xsw1=xsw[1]
                    xsw=xsw[0]
            else: xsw = dputil.getDPprodRate(mass_mc,eps,pro,0) 
            wg = sTree.MCTrack[dp_id].GetWeight()
            #print dp_id 
            dp_mom=r.TVector3(sTree.MCTrack[dp_id].GetPx(),sTree.MCTrack[dp_id].GetPy(),sTree.MCTrack[dp_id].GetPz())
            dp_mag=sTree.MCTrack[dp_id].GetP()
            break
        else:
            if dpMom=='eta1': xsw,xsw1,wg,dp_id,dp_mom,dp_mag=0,0,0,0,0,0
            if not dpMom=='eta1':xsw,wg,dp_id,dp_mom,dp_mag=0,0,0,0,0
    if dpMom=='eta1': return xsw,xsw1,wg,dp_id,dp_mom,dp_mag
    if not dpMom=='eta1': return xsw,wg,dp_id,dp_mom,dp_mag

def find_signal(pdg):# this function finds the signal tracks. USED for finding signals in fittracks.. It is also looks for pi0 and gamma BUT no gamma or pi0 in FitTracks. So, signals are proton+-, pion+-, kaon+-, electron +- muon +-
    #if abs(pdg)== 11 or abs(pdg)== 13 or abs(pdg)== 111 or abs(pdg)== 321 or abs(pdg)== 211 or abs(pdg)== 22 or abs(pdg)== 2212: return True
    if abs(pdg)== 11 or abs(pdg)== 13 or abs(pdg)== 111 or abs(pdg)== 321 or abs(pdg)== 211 or abs(pdg)== 2212: return True
def checkTrue(sTree, dp_id):# this function gives the DP with its direct decay channel USED for finding the DP events with at least two e,mu,tau channel or any hadronic channel from MCTracks.
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
                    PID.append(mc)#I NEED TO THINK OF SMT TO SPLIT NEUTRAL CHANNELS
    return PID

h={}
ut.bookHist(h,'DOCA','DOCA')

ut.bookHist(h,'DPang1','invariant Mass (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPang1_e','invariant Mass (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPang1_mu','invariant Mass (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPang1_tau','invariant Mass (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPang1_had','invariant Mass (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPang1_oth','invariant Mass (GeV)',100,0.,mass_mc+5.)

ut.bookHist(h,'DP','invariant Mass (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPW','invariant Mass with Weights (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPves','invariant Mass (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPvesW','invariant Mass with Weights (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPang','invariant Mass (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPangW','invariant Mass with Weights (GeV)',100,0.,mass_mc+5.)

ut.bookHist(h,'DP_e','invariant Mass (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPW_e','invariant Mass with Weights (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPves_e','invariant Mass (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPvesW_e','invariant Mass with Weights (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPang_e','invariant Mass (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPangW_e','invariant Mass with Weights (GeV)',100,0.,mass_mc+5.)

ut.bookHist(h,'DP_mu','invariant Mass (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPW_mu','invariant Mass with Weights (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPves_mu','invariant Mass (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPvesW_mu','invariant Mass with Weights (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPang_mu','invariant Mass (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPangW_mu','invariant Mass with Weights (GeV)',100,0.,mass_mc+5.)

ut.bookHist(h,'DP_tau','invariant Mass (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPW_tau','invariant Mass with Weights (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPves_tau','invariant Mass (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPvesW_tau','invariant Mass with Weights (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPang_tau','invariant Mass (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPangW_tau','invariant Mass with Weights (GeV)',100,0.,mass_mc+5.)

ut.bookHist(h,'DP_had','invariant Mass (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPW_had','invariant Mass with Weights (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPves_had','invariant Mass (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPvesW_had','invariant Mass with Weights (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPang_had','invariant Mass (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPangW_had','invariant Mass with Weights (GeV)',100,0.,mass_mc+5.)

ut.bookHist(h,'DP_oth','invariant Mass (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPW_oth','invariant Mass with Weights (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPves_oth','invariant Mass (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPvesW_oth','invariant Mass with Weights (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPang_oth','invariant Mass (GeV)',100,0.,mass_mc+5.)
ut.bookHist(h,'DPangW_oth','invariant Mass with Weights (GeV)',100,0.,mass_mc+5.)

ut.bookHist(h,'DOCA','Doca between two tracks',100,0.,100)

ut.bookHist(h,'IP','Impact Parameter',100,0.,10.)

def myEventLoop(n):# Analysis is starting here
    #print n
    rc=sTree.GetEntry(n)
    fm=findmum()
    if dpMom == 'eta1':
        xsw=fm[0]
        xsw1=fm[1]
        wg=fm[2]
        dp_id=fm[3]
        dp_M=fm[4]
        dp_Mag=fm[5]
    if not dpMom == 'eta1':
        xsw=fm[0]
        wg=fm[1]
        dp_id=fm[2]
        dp_M=fm[3]
        dp_Mag=fm[4]
    MA,MAS=[],[] 
    DPmom=r.TLorentzVector(0.,0.,0.,0.)
    DPma=r.TLorentzVector(0.,0.,0.,0.) 
    dau=0
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
    if xsw==0 and wg==0 and dp_id==0: return
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
            """if abs(sTree.MCTrack[xxx].GetPdgCode())==111:
                print n, sTree.MCTrack[xxx].GetPdgCode()
            if abs(sTree.MCTrack[xxx].GetPdgCode())==211:
                print n, sTree.MCTrack[xxx].GetPdgCode()"""

    for F,FIT in enumerate(sTree.FitTracks):
        fitStatus = FIT.getFitStatus()
        if not fitStatus.isFitConverged(): continue
        xx = FIT.getFittedState()
        mc = sTree.MCTrack[sTree.fitTrack2MC[F]]
        vtx=r.TVector3(mc.GetStartX(), mc.GetStartY(), mc.GetStartZ())
        mom=r.TVector3(mc.GetPx(), mc.GetPy(), mc.GetPz())
        trackDir = xx.getDir()
        trackPos = xx.getPos()
        vx = ROOT.TVector3()
        mc.GetStartVertex(vx)
        t = 0
        for i in range(3):   t += trackDir(i)*(vx(i)-trackPos(i))
        dist = 0
        for i in range(3):   dist += (vx(i)-trackPos(i)-t*trackDir(i))**2
        dist = ROOT.TMath.Sqrt(dist)
        h['IP'].Fill(dist)
        #print "ftrack"
        if not isInFiducial(vtx.X(),vtx.Y(),vtx.Z()): continue
        #print "ftrack vessel"
        if not find_signal(xx.getPDG()): continue#This is VESSEL Cut
        #print "ftrack signal"
        f_track+=1
        if not checkFiducialVolume(sTree,F,dy): continue
        nmeas = fitStatus.getNdf()
        chi2 = fitStatus.getChi2()
        if not nmeas>25.: continue
        if not chi2/nmeas<5.: continue
        if not xx.getMomMag()>1.: continue
        #if not mc.GetStartT()<=1.:continue
        h['DOCA'].Fill(mc.GetStartT()-doca)
        if not (mc.GetStartT()-doca)<=1.: continue
        print "DOCA", xx.getPDG(), dist, n
        if not dist<10.: continue
        print "RECO", xx.getPDG(), dist, n
        if find_signal(xx.getPDG()):#This is RECO Cut
            print "SIG", xx.getPDG(), dist, n
            RECO+=1
        else:
            oth_a+=1
            #print 'reco is rejected?', xx.getPDG()

    if e>1:#at least two electrons decay channel FOR BR
        h['DP_e'].Fill(mass_mc)
    if mu>1:#at least two muons decay channel FOR BR
        h['DP_mu'].Fill(mass_mc)
    if tau>1:#at least two taus decay channel FOR BR
        h['DP_tau'].Fill(mass_mc)
    if had>0:#any hadronic decay channel for BR
        h['DP_had'].Fill(mass_mc)

    if f_track>1:#at least two charged particle in the VESSEL
        if e>1:#at least two electrons decay channel FOR VES_PROB
            h['DPvesW_e'].Fill(mass_mc,wg)
            h['DPves_e'].Fill(mass_mc)  
        if mu>1:#at least two muons decay channel FOR VES_PROB 
            h['DPvesW_mu'].Fill(mass_mc,wg)
            h['DPves_mu'].Fill(mass_mc) 
        if had>0:#any hadronic decay channel for VES_PROB
            h['DPvesW_had'].Fill(mass_mc,wg)
            h['DPves_had'].Fill(mass_mc)         
        if tau>1:#at least two taus decay channel FOR VES_PROB
            h['DPvesW_tau'].Fill(mass_mc,wg)
            h['DPves_tau'].Fill(mass_mc)

    if f_track>1 and RECO>1:#at least two charged tracks in the FINAL CUT
        if e>1:#at least two electrons decay channel FOR RECO_EFF
            h['DPang_e'].Fill(mass_mc,wg*xsw)
            if dpMom == 'eta1': h['DPang1_e'].Fill(mass_mc,wg*xsw1)
            h['DPangW_e'].Fill(mass_mc,wg)  
        if mu>1:#at least two muons decay channel FOR RECO_EFF
            h['DPang_mu'].Fill(mass_mc,wg*xsw)
            if dpMom == 'eta1': h['DPang1_mu'].Fill(mass_mc,wg*xsw1)
            h['DPangW_mu'].Fill(mass_mc,wg) 
        if had>0:#any hadronic decay channel for RECO_EFF
            h['DPang_had'].Fill(mass_mc,wg*xsw)
            if dpMom == 'eta1': h['DPang1_had'].Fill(mass_mc,wg*xsw1)
            h['DPangW_had'].Fill(mass_mc,wg)         
        if tau>1:#at least two taus decay channel FOR RECO_EFF
            h['DPang_tau'].Fill(mass_mc,wg*xsw)
            if dpMom == 'eta1': h['DPang1_tau'].Fill(mass_mc,wg*xsw1)
            h['DPangW_tau'].Fill(mass_mc,wg)

    if e>1 or mu>1 or tau>1 or had>0:#at least two charged leptons decay channel and any hadronic decay channel FOR BR_TOT
        h['DP'].Fill(mass_mc)
        if f_track>1:##at least two charged tracks in the VESL
            h['DPvesW'].Fill(mass_mc,wg)
            h['DPves'].Fill(mass_mc)
            if RECO>1:#at least two charged tracks in the FINAL CUT 
                #print "reco"
                h['DPangW'].Fill(mass_mc)       
                h['DPang'].Fill(mass_mc,wg*xsw)#FOR THE RATE
                if dpMom == 'eta1': h['DPang1'].Fill(mass_mc,wg*xsw1)
            else:
                h['DPangW_oth'].Fill(mass_mc,wg)
                h['DPang_oth'].Fill(mass_mc,wg*xsw)
                if dpMom == 'eta1': h['DPang1_oth'].Fill(mass_mc,wg*xsw1)
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
tmp1=tmp1.replace("reco","ana/dat")
tmp1= tmp1.replace(date,dest)
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

if float(h['DPvesW_e'].Integral())>0.:
    ang_s+=float(h['DPangW_e'].Integral())
    ves_s+=float(h['DPvesW_e'].Integral())
    Sum+=float(h['DP_e'].Integral())
    a.write('%.4g %s %.8g %.8g %.8g' %(mass_mc, eps, float(h['DP_e'].Integral())/float(h['DP'].Integral()), float(h['DPvesW_e'].Integral())/float(h['DP_e'].Integral()), float(h['DPangW_e'].Integral())/float(h['DPvesW_e'].Integral())))
    a.write('\n')
if float(h['DPvesW_mu'].Integral())!=0:
    ang_s+=float(h['DPangW_mu'].Integral())
    ves_s+=float(h['DPvesW_mu'].Integral())
    Sum+=float(h['DP_mu'].Integral())
    b.write('%.4g %s %.8g %.8g %.8g' %(mass_mc, eps, float(h['DP_mu'].Integral())/float(h['DP'].Integral()), float(h['DPvesW_mu'].Integral())/float(h['DP_mu'].Integral()), float(h['DPangW_mu'].Integral())/float(h['DPvesW_mu'].Integral())))
    b.write('\n')
if float(h['DPvesW_tau'].Integral())!=0:
    ang_s+=float(h['DPangW_tau'].Integral())
    ves_s+=float(h['DPvesW_tau'].Integral())
    Sum+=float(h['DP_tau'].Integral())
    c.write('%.4g %s %.8g %.8g %.8g' %(mass_mc, eps, float(h['DP_tau'].Integral())/float(h['DP'].Integral()), float(h['DPvesW_tau'].Integral())/float(h['DP_tau'].Integral()), float(h['DPangW_tau'].Integral())/float(h['DPvesW_tau'].Integral())))
    c.write('\n')
if float(h['DPvesW_had'].Integral())!=0:
    ang_s+=float(h['DPangW_had'].Integral())
    ves_s+=float(h['DPvesW_had'].Integral())
    Sum+=float(h['DP_had'].Integral())
    d.write('%.4g %s %.8g %.8g %.8g' %(mass_mc, eps, float(h['DP_had'].Integral())/float(h['DP'].Integral()), float(h['DPvesW_had'].Integral())/float(h['DP_had'].Integral()), float(h['DPangW_had'].Integral())/float(h['DPvesW_had'].Integral())))
    d.write('\n')

if float(h['DPvesW'].Integral())!=0.: 
    f.write('%.4g %s %.8g %.8g %.8g' %(mass_mc, eps, float(h['DP_oth'].Integral())/float(h['DPW'].Integral()), float(h['DPvesW_oth'].Integral())/float(h['DP'].Integral()), float(h['DPangW_oth'].Integral())/float(h['DPvesW'].Integral())))
    f.write('\n')#mass, epsilon, how much we lose from 2 track selection, how much we lose in vessel, how much we lose in final selection
if float(ves_s)!=0:
    g.write('%.4g %s %.8g %.8g %.8g %.8g' %(mass_mc, eps, float(h['DP'].Integral()/h['DPW'].Integral()), float(Sum/h['DP'].Integral()), float(ves_s/Sum), float(ang_s/ves_s)))
    g.write('\n')

if float(h['DP'].Integral())!=0:
    H.write('%.4g %s %.8g %.8g %.8g %.8g %.8g' %(mass_mc, eps, nEvents, float(h['DPW'].Integral()), float(h['DP'].Integral()), float(h['DPves'].Integral()), float(h['DPangW'].Integral())))
    H.write('\n')

NomL  = 0.
NomL1 = 0.
DenL  = 0.
DP_instance=darkphoton.DarkPhoton(float(mass_mc),float(eps))

if float(h['DP_e'].Integral())!=0:
    BR1=DP_instance.findBranchingRatio('A -> e- e+')
    NomL+=float(h['DPang_e'].Integral())
    if dpMom == "eta1": NomL1+=float(h['DPang1_e'].Integral())
    DenL+=float(h['DP_e'].Integral())*BR1
if float(h['DP_mu'].Integral())!=0:
    BR2=DP_instance.findBranchingRatio('A -> mu- mu+')
    NomL+=float(h['DPang_mu'].Integral())
    if dpMom == "eta1": NomL1+=float(h['DPang1_mu'].Integral())
    DenL+=float(h['DP_mu'].Integral())*BR2
if float(h['DP_tau'].Integral())!=0:
    BR3=DP_instance.findBranchingRatio('A -> tau- tau+')
    NomL+=float(h['DPang_tau'].Integral())
    if dpMom == "eta1": NomL1+=float(h['DPang1_tau'].Integral())
    DenL+=float(h['DP_tau'].Integral())*BR3
if float(h['DP'].Integral())!=0:
    RecLW=NomL/DenL*2.0e+20
    RecW=h['DPang'].Integral()/h['DP'].Integral()*2.0e+20#weighted Selected/weighted Vessel
    if dpMom=="eta1":
        RecLW1=NomL1/DenL*2.0e+20
        RecW1=h['DPang1'].Integral()/h['DP'].Integral()*2.0e+20
        k.write('%.4g %s %.8g %.8g' %(mass_mc, eps, RecW1, RecW)) 
        k.write('\n')       
        l.write('%.4g %s %.8g %.8g' %(mass_mc, eps, RecLW1, RecLW)) 
        l.write('\n')
    if not dpMom=="eta1":
        k.write('%.4g %s %.8g' %(mass_mc, eps, RecW)) 
        k.write('\n')       
        l.write('%.4g %s %.8g' %(mass_mc, eps, RecLW)) 
        l.write('\n')
print mass_mc, eps, RecW
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

tmp1=tmp1.replace("reco","ana/dat")
tmp1=tmp1.replace(date,dest)
hfile =tmp1+"_Ana.root" 
r.gROOT.cd()
ut.writeHists(h,hfile)

#print hfile
#print h['DP'].Integral() 
#print RecW
#print RecLW
