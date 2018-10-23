# pid deffiner
import ROOT, sys
import shipunit as u
import rootUtils as ut
import math as m
import TrackExtrapolateTool
import ctypes
import shipDet_conf

class Task:
 "initialize"

 def __init__(self,main):
  print "****************************************"
  print "*** You are using PID version 18.1.0 ***"
  print "****************************************"
  self.sTree = main.sTree
  self.fpidArray  = ROOT.TClonesArray("pid")
  if not self.sTree.GetBranch("pid"):
    self.pID   = self.sTree.Branch("Pid",  self.fpidArray,32000,-1)
  else: 
    self.pID = self.sTree.pid
  self.reps,self.states,self.newPosDir = {},{},{}
  self.PDG = ROOT.TDatabasePDG.Instance()
  fGeo = ROOT.gGeoManager
  top  = fGeo.GetTopVolume()
  dv = top.GetNode('DecayVolume_1')
  ns = dv.GetNodes()
  T1Lid = ns.FindObject("T1Lid_1").GetMatrix()
  self.z_start = T1Lid.GetTranslation()[2]
  self.zpositions = {}
  self.parallelToZ = ROOT.TVector3(0., 0., 1.)
  hadron = top.GetNode("Hcal_1")
  hvol = hadron.GetVolume()
  self.zpositions['hcal'] = hadron.GetMatrix().GetTranslation()[2]
  ecal = top.GetNode("Ecal_1")
  evol = ecal.GetVolume()   
  self.zpositions['ecal'] = ecal.GetMatrix().GetTranslation()[2]
  x = sys.modules['__main__']
  ShipGeo = x.ShipGeo
  for i in range(4):
   muonDet = top.GetNode('MuonDetector_'+str(i+1))
   if muonDet: self.zpositions['muon'+str(i)] = muonDet.GetMatrix().GetTranslation()[2]
   else: self.zpositions['muon'+str(i)] = ShipGeo['MuonStation'+str(i)].z
  self.hcal = sys.modules['__main__']. modules['Hcal']
  self.pad_size_x = 5 #cm
  self.pad_size_y = 5 #cm
  self.dimensions_x = 300 #cm half witdth
  self.dimensions_y = 600 #cm half witdth
  self.rx=250
  self.ry=500
  self.muly_acceptance = 50.0
  self.ncells_x=m.floor((2*self.dimensions_x)/self.pad_size_x)
  self.ncells_y=m.floor((2*self.dimensions_y)/self.pad_size_y) 
  self.threshold_pad_energy = 0.2
  self.Ecal_dx = 15 #cm
  self.Ecal_dy = 15 #cm
  self.Ecal_EP_threshold_min = 0.92 #acceptence region for E over P in Ecal >  self.Ecal_EP_threshold_min
  self.Ecal_EP_threshold_max = 10
  self.Hit_number_threshold=3    #number of pad-hits around the extrapolated tracks in MuonDet
  self.hitlimit_x,self.hitlimit_y=5,5    #x-y area to check the number of pad-hits
  self.cutNdf = 25

  self.P_min00,self.P_max00,self.dx00_min,self.dx00_max,self.dy00_min,self.dy00_max=-99,-99,-99,-99,-99,-99
  self.P_min01,self.P_max01,self.dx01_min,self.dx01_max,self.dy01_min,self.dy01_max=-99,-99,-99,-99,-99,-99
  self.P_min02,self.P_max02,self.dx02_min,self.dx02_max,self.dy02_min,self.dy02_max=-99,-99,-99,-99,-99,-99
  self.P_min03,self.P_max03,self.dx03_min,self.dx03_max,self.dy03_min,self.dy03_max=-99,-99,-99,-99,-99,-99

  self.P_min10,self.P_max10,self.dx10_min,self.dx10_max,self.dy10_min,self.dy10_max=  0,  8, -5,  5, -5, 5
  self.P_min11,self.P_max11,self.dx11_min,self.dx11_max,self.dy11_min,self.dy11_max=-99,-99,-99,-99,-99,-99
  self.P_min12,self.P_max12,self.dx12_min,self.dx12_max,self.dy12_min,self.dy12_max=-99,-99,-99,-99,-99,-99
  self.P_min13,self.P_max13,self.dx13_min,self.dx13_max,self.dy13_min,self.dy13_max=-99,-99,-99,-99,-99,-99

  self.P_min20,self.P_max20,self.dx20_min,self.dx20_max,self.dy20_min,self.dy20_max=  8, 13, -5,  5, -5, 5
  self.P_min21,self.P_max21,self.dx21_min,self.dx21_max,self.dy21_min,self.dy21_max= 13, 20, -3,  3, -3, 3
  self.P_min22,self.P_max22,self.dx22_min,self.dx22_max,self.dy22_min,self.dy22_max=-99,-99,-99,-99,-99,-99

  self.P_min30,self.P_max30,self.dx30_min,self.dx30_max,self.dy30_min,self.dy30_max= 20,999, -4,  4, -4, 4
  self.P_min31,self.P_max31,self.dx31_min,self.dx31_max,self.dy31_min,self.dy31_max=-99,-99,-99,-99,-99,-99

 def execute(self):
 ## make particles persistent ##
  self.PID()
  self.pID.Fill()

 def HcalHits(self):
 ## hcalPoint hits ##  
  self.hcal1 = []
  self.hcal2 = []
  self.new_hcal2 = []
  if not  hasattr(self.sTree,'HcalPointLite'): return
  for chit in self.sTree.HcalPointLite:
   if not chit.GetEnergyLoss()>0: continue
   detID = chit.GetDetectorID()
   x = ctypes.c_float()
   y = ctypes.c_float()
   section = ctypes.c_int()
   self.hcal.GetCellCoordInf(detID,x,y,section)
   ELoss = chit.GetEnergyLoss()/u.MeV
   if ELoss>0: self.hcal1.append([x.value,y.value,section.value,ELoss])

 def muonDigitHit(self):
 ## merging muonPoint hits inside each pad ##
  self.list1 = []
  self.list2 = []
  self.new_list2 = []
#  print 'numer of hites = ', self.sTree.muonPoint.GetEntries()
  for ahit in self.sTree.muonPoint:
   if not ahit.GetEnergyLoss()>0: continue
   detID = ahit.GetDetectorID()
   if m.fabs(ahit.GetZ()-self.zpositions['muon0'])<self.muly_acceptance:
      mul=0
      ##print 'mu0 = ',ahit.GetX(),ahit.GetY(),ahit.GetEnergyLoss()/u.MeV,ahit.GetZ()
      X_hit_pos0=ahit.GetX()+self.dimensions_x
      Y_hit_pos0=ahit.GetY()+self.dimensions_y
      pos_hit_x0=m.floor(X_hit_pos0/self.pad_size_x)+1
      pos_hit_y0=m.floor(Y_hit_pos0/self.pad_size_y)+1
      if (pos_hit_x0<0 or pos_hit_x0>self.ncells_x) or (pos_hit_y0<0 or pos_hit_y0>self.ncells_y): continue
      E = ahit.GetEnergyLoss()/u.MeV
#      print "--*--->>  ", E,pos_hit_x0,pos_hit_y0, mul
      if not E<self.threshold_pad_energy: self.list1.append([pos_hit_x0,pos_hit_y0,E,mul])
   if m.fabs(ahit.GetZ()-self.zpositions['muon1'])<self.muly_acceptance:
      mul1=1
      ##print 'mu1 = ',ahit.GetX(),ahit.GetY(),ahit.GetEnergyLoss()/u.MeV,ahit.GetZ()
      X_hit_pos1=ahit.GetX()+self.dimensions_x
      Y_hit_pos1=ahit.GetY()+self.dimensions_y
      pos_hit_x1=m.floor(X_hit_pos1/self.pad_size_x)+1
      pos_hit_y1=m.floor(Y_hit_pos1/self.pad_size_y)+1
      if (pos_hit_x1<0 or pos_hit_x1>self.ncells_x) or (pos_hit_y1<0 or pos_hit_y1>self.ncells_y): continue
      E1 = ahit.GetEnergyLoss()/u.MeV
#      print "--**--->>  ", E1,pos_hit_x1,pos_hit_y1, mul1
      if not E1<self.threshold_pad_energy: self.list1.append([pos_hit_x1,pos_hit_y1,E1,mul1])
   if m.fabs(ahit.GetZ()-self.zpositions['muon2'])<self.muly_acceptance:
      mul2=2
      ##print 'mu2 = ',ahit.GetX(),ahit.GetY(),ahit.GetEnergyLoss()/u.MeV,ahit.GetZ()
      X_hit_pos2=ahit.GetX()+self.dimensions_x
      Y_hit_pos2=ahit.GetY()+self.dimensions_y
      pos_hit_x2=m.floor(X_hit_pos2/self.pad_size_x)+1
      pos_hit_y2=m.floor(Y_hit_pos2/self.pad_size_y)+1
      if (pos_hit_x2<0 or pos_hit_x2>self.ncells_x) or (pos_hit_y2<0 or pos_hit_y2>self.ncells_y): continue
      E2 = ahit.GetEnergyLoss()/u.MeV
#      print "--***--->>  ", E2,pos_hit_x2,pos_hit_y2, mul2
      if not E2<self.threshold_pad_energy: self.list1.append([pos_hit_x2,pos_hit_y2,E2,mul2])
   if m.fabs(ahit.GetZ()-self.zpositions['muon3'])<self.muly_acceptance:
      mul3=3
      ##print 'mu3 = ',ahit.GetX(),ahit.GetY(),ahit.GetEnergyLoss()/u.MeV,ahit.GetZ()
      X_hit_pos3=ahit.GetX()+self.dimensions_x
      Y_hit_pos3=ahit.GetY()+self.dimensions_y
      pos_hit_x3=m.floor(X_hit_pos3/self.pad_size_x)+1
      pos_hit_y3=m.floor(Y_hit_pos3/self.pad_size_y)+1
      if (pos_hit_x3<0 or pos_hit_x3>self.ncells_x) or (pos_hit_y3<0 or pos_hit_y3>self.ncells_y): continue
      E3 = ahit.GetEnergyLoss()/u.MeV
#      print "--****--->>  ", E3,pos_hit_x3,pos_hit_y3, mul3
      if not E3<self.threshold_pad_energy: self.list1.append([pos_hit_x3,pos_hit_y3,E3,mul3])
  for i in range(len(self.list1)):
   E, E1, E2, E3, EE, E_tot=0,0,0,0,0,0
   x,y, E, mull = self.list1[i][0], self.list1[i][1], self.list1[i][2], self.list1[i][3]
   for j in range(len(self.list1)):   
     xx, yy, EE, mulll = self.list1[j][0], self.list1[j][1], self.list1[j][2], self.list1[j][3]
     if x == xx and y == yy and mull == mulll: E_tot+=EE
     j+=1
   #print 'E_tot', E_tot
   if not mull==0: self.list2.append([x,y,E_tot,mull])
   i+=1
  for elem in self.list2:
    if elem not in self.new_list2:  self.new_list2.append(elem)
  self.list2 = self.new_list2
  #if not self.list2==[]: print 'hits in each pad = ', self.list2

 def PID(self):
 ## extrapolation and pid check ##
  self.muonDigitHit()
  self.HcalHits()
  self.fpidArray.Delete()
  ppid    = self.fpidArray

  i=-1
  for fT in self.sTree.FitTracks:
    self.El,self.Hl,self.OverHit=False,False,False
    self.pid00,self.pid01,self.pid02,self.pid03,self.pid10,self.pid11,self.pid12,self.pid13=False,False,False,False,False,False,False,False
    self.pid20,self.pid21,self.pid22,self.pid30,self.pid31=False,False,False,False,False
    self.pid_mu=False
    self.vol_mu1,self.vol_ecal,self.vol_hcal=False,False,False
    self.pos_pad_x0,self.pos_pad_y0,self.pos_pad_x1,self.pos_pad_y1,self.pos_pad_x2,self.pos_pad_y2,self.pos_pad_x3,self.pos_pad_y3=0,0,0,0,0,0,0,0
    self.extrap_X_ecal,self.extrap_Y_ecal,self.extrap_X_hcal,self.extrap_Y_hcal=0.,0.,0.,0.
    self.P=0.
    i+=1
    fst = fT.getFitStatus()
    if not fst.isFitConverged() or fst.getNdf() < self.cutNdf: 
      pidObject=ROOT.pid()
      pidObject.SetTrackID(i)
      pidObject.SetTrackPID(-3)
      nPID=ppid.GetEntries()
      ppid[nPID]=pidObject
      continue
    fittedState = fT.getFittedState()
    self.P = fittedState.getMomMag()
    self.extrapStates = {}
    for self.det in self.zpositions:
     rc,pos,mom = TrackExtrapolateTool.extrapolateToPlane(fT,self.zpositions[self.det])
#     print rc
     if rc>0:
      self.extrapStates[self.det] = [pos.X(),pos.Y(),self.zpositions[self.det]]
      self.hcal_ID()
      self.muon_ID()
      self.elec_ID()
    pidObject=ROOT.pid()
    pidObject.SetTrackID(i)
    if not rc> 0:
      pidObject.SetTrackPID(-1)
      nPID=ppid.GetEntries()
      ppid[nPID]=pidObject
      continue
    self.run_hcal_ID()
    self.run_elec_ID()
    self.run_muon_ID()
    if self.El==True and self.vol_ecal==False:
      pidObject.SetTrackPID(1)
#      print '==== Is Electron'
    if (self.pid10==True or self.pid20==True or self.pid21==True or self.pid30==True or self.pid_mu==True) and self.El==False and self.vol_mu1==False: 
      pidObject.SetTrackPID(3)
      self.Hl=False
 #     print '**** Is Muon'
    if self.pid10==False and self.pid20==False and self.pid21==False and self.pid30==False and self.pid_mu==False and self.El==False and self.Hl==True and self.vol_hcal==False:
      pidObject.SetTrackPID(2)
  #      print '$$$$ Is Hadron'
    if self.vol_ecal==True or self.vol_mu1==True:
      pidObject.SetTrackPID(-2)
#      print '==== It is out of the acceptance'
    nPID=ppid.GetEntries()
    ppid[nPID]=pidObject
   # print "---------------- "

 def muon_ID(self):
    if self.det == 'muon0':
      extrap_X_mu0 = self.extrapStates[self.det][0]
      extrap_Y_mu0 = self.extrapStates[self.det][1]
      extrap_Z_mu0 = self.extrapStates[self.det][2]
      X_pos0=extrap_X_mu0+self.dimensions_x
      Y_pos0=extrap_Y_mu0+self.dimensions_y
      self.pos_pad_x0=m.floor(X_pos0/self.pad_size_x)+1
      self.pos_pad_y0=m.floor(Y_pos0/self.pad_size_y)+1
    if self.det == 'muon1':
      self.extrap_X_mu1 = self.extrapStates[self.det][0]
      self.extrap_Y_mu1 = self.extrapStates[self.det][1]
      extrap_Z_mu1 = self.extrapStates[self.det][2]
      X_pos1=self.extrap_X_mu1+self.dimensions_x
      Y_pos1=self.extrap_Y_mu1+self.dimensions_y
      self.pos_pad_x1=m.floor(X_pos1/self.pad_size_x)+1
      self.pos_pad_y1=m.floor(Y_pos1/self.pad_size_y)+1
    if self.det == 'muon2':
      extrap_X_mu2 = self.extrapStates[self.det][0]
      extrap_Y_mu2 = self.extrapStates[self.det][1]
      extrap_Z_mu2 = self.extrapStates[self.det][2]
      X_pos2=extrap_X_mu2+self.dimensions_x
      Y_pos2=extrap_Y_mu2+self.dimensions_y
      self.pos_pad_x2=m.floor(X_pos2/self.pad_size_x)+1
      self.pos_pad_y2=m.floor(Y_pos2/self.pad_size_y)+1
    if self.det == 'muon3':
      extrap_X_mu3 = self.extrapStates[self.det][0]
      extrap_Y_mu3 = self.extrapStates[self.det][1]
      extrap_Z_mu3 = self.extrapStates[self.det][2]
      X_pos3=extrap_X_mu3+self.dimensions_x
      Y_pos3=extrap_Y_mu3+self.dimensions_y
      self.pos_pad_x3=m.floor(X_pos3/self.pad_size_x)+1
      self.pos_pad_y3=m.floor(Y_pos3/self.pad_size_y)+1

 def run_muon_ID(self):
     for i in range(len(self.list2)):
        X,Y, e, Mull = self.list2[i][0], self.list2[i][1], self.list2[i][2], self.list2[i][3]
        if Mull==0:
            delta_x0 = X-self.pos_pad_x0
            delta_y0 = Y-self.pos_pad_y0
            if (self.P>self.P_min00 and self.P<self.P_max00) and (delta_x0>self.dx00_min and delta_x0<self.dx00_max) and (delta_y0>self.dy00_min and delta_y0<self.dy00_max):
              self.pid00=True
            if (self.P>self.P_min01 and self.P<self.P_max01) and (delta_x0>self.dx01_min and delta_x0<self.dx01_max) and (delta_y0>self.dy01_min and delta_y0<self.dy01_max):
              self.pid01=True
            if (self.P>self.P_min02 and self.P<self.P_max02) and (delta_x0>self.dx02_min and delta_x0<self.dx02_max) and (delta_y0>self.dy02_min and delta_y0<self.dy02_max):
              self.pid02=True
            if (self.P>self.P_min03 and self.P<self.P_max03) and (delta_x0>self.dx03_min and delta_x0<self.dx03_max) and (delta_y0>self.dy03_min and delta_y0<self.dy03_max):
              self.pid03=True

 #           if (self.P>self.P_min00 and self.P<self.P_max00) and m.fabs(delta_x0)<self.hitlimit_x and m.fabs(delta_y0)<self.hitlimit_y: nhit0+=1
#        if nhit0>=self.Hit_number_threshold: overhit=True
        if Mull==1:
            delta_x1 = X-self.pos_pad_x1
            delta_y1 = Y-self.pos_pad_y1
            if (self.P>self.P_min10 and self.P<self.P_max10) and (delta_x1>self.dx10_min and delta_x1<self.dx10_max) and (delta_y1>self.dy10_min and delta_y1<self.dy10_max):
              self.pid10=True
            if (self.P>self.P_min11 and self.P<self.P_max11) and (delta_x1>self.dx11_min and delta_x1<self.dx11_max) and (delta_y1>self.dy11_min and delta_y1<self.dy11_max):
              self.pid11=True
            if (self.P>self.P_min12 and self.P<self.P_max12) and (delta_x1>self.dx12_min and delta_x1<self.dx12_max) and (delta_y1>self.dy12_min and delta_y1<self.dy12_max):
              self.pid12=True
            if (self.P>self.P_min13 and self.P<self.P_max13) and (delta_x1>self.dx13_min and delta_x1<self.dx13_max) and (delta_y1>self.dy13_min and delta_y1<self.dy13_max):
              self.pid13=True
        if Mull==2:
            delta_x2 = X-self.pos_pad_x2
            delta_y2 = Y-self.pos_pad_y2
            if (self.P>self.P_min20 and self.P<self.P_max20) and (delta_x2>self.dx20_min and delta_x2<self.dx20_max) and (delta_y2>self.dy20_min and delta_y2<self.dy20_max):
              self.pid20=True
            if (self.P>self.P_min21 and self.P<self.P_max21) and (delta_x2>self.dx21_min and delta_x2<self.dx21_max) and (delta_y2>self.dy21_min and delta_y2<self.dy21_max):
              self.pid21=True
            if (self.P>self.P_min22 and self.P<self.P_max22) and (delta_x2>self.dx22_min and delta_x2<self.dx22_max) and (delta_y2>self.dy22_min and delta_y2<self.dy22_max):
              self.pid22=True
        if Mull==3:
            delta_x3 = X-self.pos_pad_x3
            delta_y3 = Y-self.pos_pad_y3
            if (self.P>self.P_min30 and self.P<self.P_max30) and (delta_x3>self.dx30_min and delta_x3<self.dx30_max) and (delta_y3>self.dy30_min and delta_y3<self.dy30_max):
              self.pid30=True
            if (self.P>self.P_min31 and self.P<self.P_max31) and (delta_x3>self.dx31_min and delta_x3<self.dx31_max) and (delta_y3>self.dy31_min and delta_y3<self.dy31_max):
              self.pid31=True

     if not self.P>5 and (self.pid10==False and self.pid20==False and self.pid21==False and self.pid30==False):
       chmu1=m.fabs((22.67-self.E_tot_h1)/22.67)
       chmu2=m.fabs((55.75-self.E_tot_h2)/55.75)
       if (chmu1<0.5 and chmu2<0.5): 
         self.pid_mu=True
     check_vol_mu1=(m.pow(self.extrap_X_mu1,2)/m.pow(self.rx,2))+(m.pow(self.extrap_Y_mu1,2)/m.pow(self.ry,2))
     if check_vol_mu1>1: 
       self.vol_mu1=True

 def elec_ID(self):
    if self.det == 'ecal':
     self.extrap_X_ecal = self.extrapStates[self.det][0]
     self.extrap_Y_ecal = self.extrapStates[self.det][1]
     extrap_Z_ecal = self.extrapStates[self.det][2]

 def run_elec_ID(self):
     for aClus in self.sTree.EcalReconstructed:
       x1_Clus, y1_Clus, Ene1_Clus =  aClus.X(), aClus.Y(), aClus.RecoE()
       Ecal_delta_x=x1_Clus - self.extrap_X_ecal
       Ecal_delta_y=y1_Clus - self.extrap_Y_ecal
       EP=Ene1_Clus/self.P
       if (EP>self.Ecal_EP_threshold_min and EP<self.Ecal_EP_threshold_max)  and m.fabs(Ecal_delta_x)<self.Ecal_dx and m.fabs(Ecal_delta_y)<self.Ecal_dy:
         self.El=True
     if self.pid10==False and self.pid20==False and self.pid21==False and self.pid30==False and self.El==False and self.pid_mu==False: self.Hl=True
     check_vol_ecal=(m.pow(self.extrap_X_ecal,2)/m.pow(self.rx,2))+(m.pow(self.extrap_Y_ecal,2)/m.pow(self.ry,2))
     if check_vol_ecal>1: 
       self.vol_ecal=True

 def hcal_ID(self):
    if self.det == 'hcal':
      self.extrap_X_hcal = self.extrapStates[self.det][0]
      self.extrap_Y_hcal = self.extrapStates[self.det][1]
      extrap_Z_hcal = self.extrapStates[self.det][2]

 def run_hcal_ID(self):
      N1,N2,M,E_est,E_totale=0,0,0,0.,0.
      self.E_tot_h1,self.E_tot_h2,self.E_tot=0.,0.,0.
      for i in range(len(self.hcal1)):
        x,y,s,E= self.hcal1[i][0], self.hcal1[i][1], self.hcal1[i][2], self.hcal1[i][3]
        delta_x = x-self.extrap_X_hcal
        delta_y = y-self.extrap_Y_hcal
        if (m.pow(delta_x,2)+m.pow(delta_y,2))<2500 and s==0:
          self.E_tot_h1+=E
        if (m.pow(delta_x,2)+m.pow(delta_y,2))<2500 and s==1:
          self.E_tot_h2+=E
        E_totale+=E
      self.E_tot = self.E_tot_h1+self.E_tot_h2
      check_vol_hcal=(m.pow(self.extrap_X_hcal,2)/m.pow(self.rx,2))+(m.pow(self.extrap_Y_hcal,2)/m.pow(self.ry,2))
      if check_vol_hcal>1: 
        self.vol_hcal=True
