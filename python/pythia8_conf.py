import ROOT, os, sys
import shipunit as u
import hnl
import readDecayTable

def addHNLtoROOT(pid=9900015 ,m = 1.0, g=3.654203020370371E-21):
    pdg = ROOT.TDatabasePDG.Instance()
    pdg.AddParticle('N2','HNL', m, False, g, 0., 'N2', pid)

def readFromAscii():
    FairShip = os.environ['FAIRSHIP'] 
    ascii = open(FairShip+'/shipgen/branchingratios.dat')
    h={}
    content = ascii.readlines()
    n = 0
    while n<len(content):
       line = content[n] 
       if not line.find('TH1F')<0:
          keys = line.split('|')
          n+=1
          limits = content[n].split(',')
          hname = keys[1]
          if len(keys)<5: keys.append(',') 
          h[ hname ] = ROOT.TH1F(hname,keys[2]+';'+keys[3]+';'+keys[4],int(limits[0]),float(limits[1]),float(limits[2]) )
       else:
          keys = line.split(',')
          h[ hname ].SetBinContent(int(keys[0]),float(keys[1]) )
       n+=1
    return h
def getbr(h,histoname,mass,coupling):
    #0 MeV< mass < 3.200 GeV 
    mass = int(mass*1000) 
    br=h[histoname].GetBinContent(mass)
    br=br*coupling
    return br

def getmaxsumbr(h,histograms,mass,couplings,totaltaubr):
    #0 MeV< mass < 3.200 GeV 
    maxsumbr=0.0
    sumbrs={}
    brdstauadded=0
    leptons=['e','mu','tau'] 
    for histoname in histograms: 
       item = histoname.split('_') 
       lepton = item[len(item)-1]
       meson = item[0]
       try:
          coupling=couplings[leptons.index(lepton)]
       except:
          coupling=couplings[2] 
       if histoname[:3]=='tau': coupling=couplings[2] 
       try:
          sumbrs[meson]+=getbr(h,histoname,mass,coupling)
       except:
          sumbrs[meson]=getbr(h,histoname,mass,coupling)
       if meson=="ds" and brdstauadded==0 and totaltaubr>0.:
          sumbrs[meson]+=totaltaubr
	  brdstauadded=1       	  
    maxsumbr=max(sumbrs.values())
    return maxsumbr

def gettotalbr(h,histograms,mass,couplings,totaltaubr):
    totalbr=0.0 
    leptons=['e','mu','tau'] 
    for histoname in histograms: 
       item = histoname.split('_') 
       lepton = item[len(item)-1]
       try:
          coupling=couplings[leptons.index(lepton)] 
       except:
          coupling=couplings[2] 
       if histoname[:3]=='tau': coupling=couplings[2] 
       totalbr+=getbr(h,histoname,mass,coupling)
    return totalbr

def configure(P8gen, mass, couplings, inclusive, deepCopy=False):
    # configure pythia8 for Ship usage
    debug=True
    if debug: cf=open('pythia8_conf.txt','w')
    h=readFromAscii()
    P8gen.UseRandom3() # TRandom1 or TRandom3 ?
    P8gen.SetMom(400)  # beam momentum in GeV 
    if deepCopy: P8gen.UseDeepCopy()
    pdg = ROOT.TDatabasePDG.Instance()
    # pythia stuff not known to ROOT
    pdg.AddParticle('system','system', 0., False, 0., 0., 'XXX', 90)
    pdg.AddParticle('p_diffr+','p_diffr+', 0., False, 0., 0., 'XXX', 9902210)
    # let strange particle decay in Geant4
    ## the following does not work because need to have N2 decaying
    #P8gen.SetParameters("ParticleDecays:limitTau0 = on")
    #P8gen.SetParameters("ParticleDecays:tau0Max = 1")
    # explicitly make KS and KL stable
    P8gen.SetParameters("130:mayDecay  = off")
    if debug: cf.write('P8gen.SetParameters("130:mayDecay  = off")\n')
    P8gen.SetParameters("310:mayDecay  = off")
    if debug: cf.write('P8gen.SetParameters("310:mayDecay  = off")\n')
    P8gen.SetParameters("3122:mayDecay = off")
    if debug: cf.write('P8gen.SetParameters("3122:mayDecay = off")\n')
    P8gen.SetParameters("3222:mayDecay = off")
    if inclusive=="True":
        P8gen.SetParameters("SoftQCD:inelastic = on")
        P8gen.SetParameters("PhotonCollision:gmgm2mumu = on")
        P8gen.SetParameters("PromptPhoton:all = on")
        P8gen.SetParameters("WeakBosonExchange:all = on")
    if inclusive=="c":
        P8gen.SetParameters("HardQCD::hardccbar  = on")
	if debug: cf.write('P8gen.SetParameters("HardQCD::hardccbar  = on")\n')
        # add HNL
        #ctau = 5.4E+06 # for tests use 5.4E+03  # nominal ctau = 54 km = 5.4E+06 cm = 5.4E+07 mm
        #mass = 1.0 # GeV
        hnl_instance = hnl.HNL(mass, couplings, debug=True)
        ctau = hnl_instance.computeNLifetime(system="FairShip") * u.c_light * u.cm
        P8gen.SetParameters("9900015:new = N2 N2 2 0 0 "+str(mass)+" 0.0 0.0 0.0 "+str(ctau/u.mm)+"  0   1   0   1   0") 
        if debug: cf.write('P8gen.SetParameters("9900015:new = N2 N2 2 0 0 '+str(mass)+' 0.0 0.0 0.0 '+str(ctau/u.mm)+'  0   1   0   1   0") \n')
        P8gen.SetParameters("9900015:isResonance = false")
        if debug: cf.write('P8gen.SetParameters("9900015:isResonance = false")\n')
	P8gen.SetParameters("Next:numberCount    =  0")
        if debug: cf.write('P8gen.SetParameters("Next:numberCount    =  0")\n')
        # Configuring decay modes...
        readDecayTable.addHNLdecayChannels(P8gen, hnl_instance, conffile=os.path.expandvars('$FAIRSHIP/python/DecaySelection.conf'), verbose=True)
        # Finish HNL setup...
        P8gen.SetParameters("9900015:mayDecay = on")
	if debug: cf.write('P8gen.SetParameters("9900015:mayDecay = on")\n')
        P8gen.SetHNLId(9900015)
	if debug: cf.write('P8gen.SetHNLId(9900015)\n')
        # also add to PDG
        gamma = u.hbarc / float(ctau) #197.3269631e-16 / float(ctau) # hbar*c = 197 MeV*fm = 197e-16 GeV*cm
        addHNLtoROOT(pid=9900015,m=mass,g=gamma)
        # 12 14 16 neutrinos replace with N2
        charmhistograms = ['ds_e','d_e','d0_K-_e','d0_K*-_e','d_K0_e','lambdac_Lambda0_e','xic0_Xi-_e','ds_mu','d_mu','d0_K-_mu','d_K0_mu','d0_K*-_mu','lambdac_Lambda0_mu','xic0_Xi-_mu','d_tau','ds_tau']
        tauhistograms= ['tau_nu_e_bar_e','tau_nu_mu_bar_mu','tau_nu_tau_e','tau_nu_tau_mu','tau_pi-','tau_K-','tau_rho-']
        totaltauBR=gettotalbr(h,tauhistograms,mass,couplings,0.)
        maxsumBR=getmaxsumbr(h,charmhistograms,mass,couplings,totaltauBR)
        if maxsumBR==0.:
           print "No phase space for HNL from c at this mass:",mass,". Quitting."
           sys.exit()
        totalBR=gettotalbr(h,charmhistograms,mass,couplings,totaltauBR)
        #overwrite Xi_c0 decays
        P8gen.SetParameters("4132:new  Xi_c0            Xi_cbar0    2   0   0    2.47088    0.00000    0.00000    0.00000  3.36000e-02   0   1   0   1   0")
	if debug: cf.write('P8gen.SetParameters("4132:new Xi_c0  Xi_cbar0     2 0 0 2.47088 0.00000 0.00000 0.00000 3.36000e-02 0 1 0 1 0")\n')
        sumBR=0.
        if getbr(h,'xic0_Xi-_e',mass,couplings[0])>0.:
           P8gen.SetParameters("4132:addChannel      1  "+str(getbr(h,'xic0_Xi-_e',mass,couplings[0])/maxsumBR)+"   22      -11       9900015 3312")
	   if debug: cf.write('P8gen.SetParameters("4132:addChannel      1  '+str(getbr(h,'xic0_Xi-_e',mass,couplings[0])/maxsumBR)+'   22      -11       9900015 3312")\n')
           sumBR+=float(getbr(h,'xic0_Xi-_e',mass,couplings[0])/maxsumBR) 
        if getbr(h,'xic0_Xi-_mu',mass,couplings[1])>0.:
           P8gen.SetParameters("4132:addChannel      1  "+str(getbr(h,'xic0_Xi-_mu',mass,couplings[1])/maxsumBR)+"   22      -13       9900015 3312")
	   if debug: cf.write('P8gen.SetParameters("4132:addChannel      1  '+str(getbr(h,'xic0_Xi-_mu',mass,couplings[1])/maxsumBR)+'   22      -13       9900015 3312")\n')
           sumBR+=float(getbr(h,'xic0_Xi-_mu',mass,couplings[1])/maxsumBR) 
        if sumBR<1. and sumBR>0.:
           P8gen.SetParameters("4132:addChannel      1   "+str(1.-sumBR)+"    0       22      22")
	   if debug: cf.write('P8gen.SetParameters("4132:addChannel      1  '+str(1.-sumBR)+'    0       22      22")\n')
        #overwrite D0 decays
        P8gen.SetParameters("421:new  D0  Dbar0    1   0   0    1.86486    0.00000    0.00000    0.00000  1.22900e-01   0   1   0   1   0")
	if debug: cf.write('P8gen.SetParameters("421:new D0      Dbar0         1 0 0 1.86486 0.00000 0.00000 0.00000 1.22900e-01  1 0 1 0")\n')
        sumBR=0.
        if getbr(h,'d0_K-_e',mass,couplings[0])>0.:
           P8gen.SetParameters("421:addChannel      1  "+str(getbr(h,'d0_K-_e',mass,couplings[0])/maxsumBR)+"   22      -11       9900015     -321")
	   if debug: cf.write('P8gen.SetParameters("421:addChannel       1  '+str(getbr(h,'d0_K-_e',mass,couplings[0])/maxsumBR)+'   22      -11       9900015     -321")\n')
           sumBR+=float(getbr(h,'d0_K-_e',mass,couplings[0])/maxsumBR)  
        if getbr(h,'d0_K*-_e',mass,couplings[0])>0.:
           P8gen.SetParameters("421:addChannel      1  "+str(getbr(h,'d0_K*-_e',mass,couplings[0])/maxsumBR)+"   22      -11       9900015     -323")
	   if debug: cf.write('P8gen.SetParameters("421:addChannel       1  '+str(getbr(h,'d0_K*-_e',mass,couplings[0])/maxsumBR)+'   22      -11       9900015     -323")\n')
           sumBR+=float(getbr(h,'d0_K*-_e',mass,couplings[0])/maxsumBR) 
        if getbr(h,'d0_K-_mu',mass,couplings[1])>0.:
           P8gen.SetParameters("421:addChannel      1  "+str(getbr(h,'d0_K-_mu',mass,couplings[1])/maxsumBR)+"   22      -13       9900015     -321")
	   if debug: cf.write('P8gen.SetParameters("421:addChannel       1  '+str(getbr(h,'d0_K-_mu',mass,couplings[1])/maxsumBR)+'   22      -13       9900015     -321")\n')
           sumBR+=float(getbr(h,'d0_K-_mu',mass,couplings[1])/maxsumBR) 
        if getbr(h,'d0_K*-_mu',mass,couplings[1])>0.:
           P8gen.SetParameters("421:addChannel      1  "+str(getbr(h,'d0_K*-_mu',mass,couplings[1])/maxsumBR)+"   22      -13       9900015     -323")
	   if debug: cf.write('P8gen.SetParameters("421:addChannel       1  '+str(getbr(h,'d0_K*-_mu',mass,couplings[1])/maxsumBR)+'   22      -13       9900015     -323")\n')
           sumBR+=float(getbr(h,'d0_K*-_mu',mass,couplings[1])/maxsumBR) 
        if sumBR<1. and sumBR>0.:
           P8gen.SetParameters("421:addChannel      1   "+str(1.-sumBR)+"    0       22      22")
           if debug: cf.write('P8gen.SetParameters("421:addChannel       1  '+str(1.-sumBR)+'    0       22      22")\n')

        #overwrite tau- decays
        P8gen.SetParameters("15:new  tau-  tau+    2   -3   0    1.77682    0.00000    0.00000    0.00000  8.71100e-02   0   1   0   1   0")
	if debug: cf.write('P8gen.SetParameters("15:new  tau-     tau+         2 -3 0 1.77682 0.00000 0.00000 0.00000 8.71100e-02 0 1 0 1 0")\n')
        sumBR=0.
        if getbr(h,'tau_pi-',mass,couplings[2])>0.:
           P8gen.SetParameters("15:addChannel      1  "+str(getbr(h,'tau_pi-',mass,couplings[2])/maxsumBR)+" 1521       9900015     -211")
	   if debug: cf.write('P8gen.SetParameters("15:addChannel        1  '+str(getbr(h,'tau_pi-',mass,couplings[2])/maxsumBR)+' 1521       9900015     -211")\n')
           sumBR+=float(getbr(h,'tau_pi-',mass,couplings[2])/maxsumBR) 
        if getbr(h,'tau_K-',mass,couplings[2])>0.:
           P8gen.SetParameters("15:addChannel      1  "+str(getbr(h,'tau_K-',mass,couplings[2])/maxsumBR)+" 1521       9900015     -321")
	   if debug: cf.write('P8gen.SetParameters("15:addChannel        1  '+str(getbr(h,'tau_K-',mass,couplings[2])/maxsumBR)+' 1521       9900015     -321")\n')
           sumBR+=float(getbr(h,'tau_K-',mass,couplings[2])/maxsumBR) 
        if getbr(h,'tau_rho-',mass,couplings[2])>0.:
           P8gen.SetParameters("15:addChannel      1  "+str(getbr(h,'tau_rho-',mass,couplings[2])/maxsumBR)+" 1521       9900015     -213")
	   if debug: cf.write('P8gen.SetParameters("15:addChannel        1  '+str(getbr(h,'tau_rho-',mass,couplings[2])/maxsumBR)+' 1521       9900015     -213")\n')
           sumBR+=float(getbr(h,'tau_rho-',mass,couplings[2])/maxsumBR) 
        if getbr(h,'tau_nu_e_bar_e',mass,couplings[2])>0.:
           P8gen.SetParameters("15:addChannel      1  "+str(getbr(h,'tau_nu_e_bar_e',mass,couplings[2])/maxsumBR)+" 1531       9900015       11      -12")
	   if debug: cf.write('P8gen.SetParameters("15:addChannel        1  '+str(getbr(h,'tau_nu_e_bar_e',mass,couplings[2])/maxsumBR)+' 1531       9900015       11      -12")\n')
           sumBR+=float(getbr(h,'tau_nu_e_bar_e',mass,couplings[2])/maxsumBR) 
        if getbr(h,'tau_nu_tau_e',mass,couplings[2])>0.:
           P8gen.SetParameters("15:addChannel      1  "+str(getbr(h,'tau_nu_tau_e',mass,couplings[2])/maxsumBR)+" 1531       9900015       11      -16")
	   if debug: cf.write('P8gen.SetParameters("15:addChannel        1  '+str(getbr(h,'tau_nu_tau_e',mass,couplings[2])/maxsumBR)+' 1531       9900015       11      -16")\n')
           sumBR+=float(getbr(h,'tau_nu_tau_e',mass,couplings[2])/maxsumBR) 
        if getbr(h,'tau_nu_mu_bar_mu',mass,couplings[2])>0.:
           P8gen.SetParameters("15:addChannel      1  "+str(getbr(h,'tau_nu_mu_bar_mu',mass,couplings[2])/maxsumBR)+" 1531       9900015       13      -14")
	   if debug: cf.write('P8gen.SetParameters("15:addChannel        1  '+str(getbr(h,'tau_nu_mu_bar_mu',mass,couplings[2])/maxsumBR)+' 1531       9900015       13      -14")\n')
           sumBR+=float(getbr(h,'tau_nu_mu_bar_mu',mass,couplings[2])/maxsumBR) 
        if getbr(h,'tau_nu_tau_mu',mass,couplings[2])>0.:
           P8gen.SetParameters("15:addChannel      1  "+str(getbr(h,'tau_nu_tau_mu',mass,couplings[2])/maxsumBR)+" 1531       9900015       13      -16")
	   if debug: cf.write('P8gen.SetParameters("15:addChannel        1  '+str(getbr(h,'tau_nu_tau_mu',mass,couplings[2])/maxsumBR)+' 1531       9900015       13      -16")\n')
           sumBR+=float(getbr(h,'tau_nu_tau_mu',mass,couplings[2])/maxsumBR) 

        #overwrite D_s+ decays
        P8gen.SetParameters("431:new  D_s+  D_s-    1   3   0    1.96849    0.00000    0.00000    0.00000  1.49900e-01   0   1   0   1   0")
	if debug: cf.write('P8gen.SetParameters("431:new  D_s+      D_s-        1 3 0 1.96849 0.00000 0.00000 0.00000 1.49900e-01 0 1 0 1 0")\n')
        sumBR=0.
        if getbr(h,'ds_mu',mass,couplings[1])>0.:
           P8gen.SetParameters("431:addChannel      1  "+str(getbr(h,'ds_mu',mass,couplings[1])/maxsumBR)+"    0      -13       9900015")
	   if debug: cf.write('P8gen.SetParameters("431:addChannel       1  '+str(getbr(h,'ds_mu',mass,couplings[1])/maxsumBR)+'    0      -13       9900015")\n')
           sumBR+=float(getbr(h,'ds_mu',mass,couplings[1])/maxsumBR) 
        if getbr(h,'ds_e',mass,couplings[1])>0.:
           P8gen.SetParameters("431:addChannel      1  "+str(getbr(h,'ds_e',mass,couplings[0])/maxsumBR)+"    0      -11       9900015")
	   if debug: cf.write('P8gen.SetParameters("431:addChannel       1  '+str(getbr(h,'ds_e',mass,couplings[0])/maxsumBR)+'    0      -11       9900015")\n')
           sumBR+=float(getbr(h,'ds_e',mass,couplings[0])/maxsumBR) 
        if getbr(h,'ds_tau',mass,couplings[2])>0.:
           P8gen.SetParameters("431:addChannel      1  "+str(getbr(h,'ds_tau',mass,couplings[2])/maxsumBR)+"    0      -15       9900015")
	   if debug: cf.write('P8gen.SetParameters("431:addChannel       1  '+str(getbr(h,'ds_tau',mass,couplings[2])/maxsumBR)+'    0      -15       9900015")\n')
           sumBR+=float(getbr(h,'ds_tau',mass,couplings[2])/maxsumBR) 
        P8gen.SetParameters("431:addChannel      1  "+str(totaltauBR/maxsumBR)+"    0      -15       16")
	if debug: cf.write('P8gen.SetParameters("431:addChannel       1  '+str(totaltauBR/maxsumBR)+'    0      -15       16")\n')
        sumBR+=float(totaltauBR/maxsumBR) 
        if sumBR<1. and sumBR>0.:
           P8gen.SetParameters("431:addChannel      1   "+str(1.-sumBR)+"    0       22      -11")
	   if debug: cf.write('P8gen.SetParameters("431:addChannel       1  '+str(1.-sumBR)+'    0       22      22")\n')
        #overwrite Lambda_c+ decays
        P8gen.SetParameters("4122:new  Lambda_c+   Lambda_cbar-    2   3   0    2.28646    0.00000    0.00000    0.00000  5.99000e-02   0   1   0   1   0")
	if debug: cf.write('P8gen.SetParameters("4122:new Lambda_c+ Lambda_cbar- 2 3 0 2.28646 0.00000 0.00000 0.00000 5.99000e-02 0 1 0 1 0")\n')
        sumBR=0
        if getbr(h,'lambdac_Lambda0_e',mass,couplings[0])>0.:
           P8gen.SetParameters("4122:addChannel      1  "+str(getbr(h,'lambdac_Lambda0_e',mass,couplings[0])/maxsumBR)+"   22      -11       9900015     3122")
	   if debug: cf.write('P8gen.SetParameters("4122:addChannel      1  '+str(getbr(h,'lambdac_Lambda0_e',mass,couplings[0])/maxsumBR)+'   22      -11       9900015     3122")\n')
           sumBR+=float(getbr(h,'lambdac_Lambda0_e',mass,couplings[0])/maxsumBR) 
        if getbr(h,'lambdac_Lambda0_mu',mass,couplings[1])>0.:
           P8gen.SetParameters("4122:addChannel      1  "+str(getbr(h,'lambdac_Lambda0_mu',mass,couplings[1])/maxsumBR)+"   22      -13       9900015     3122")
	   if debug: cf.write('P8gen.SetParameters("4122:addChannel      1  '+str(getbr(h,'lambdac_Lambda0_mu',mass,couplings[1])/maxsumBR)+'   22      -13       9900015     3122")\n')
           sumBR+=float(getbr(h,'lambdac_Lambda0_mu',mass,couplings[1])/maxsumBR) 
        if sumBR<1. and sumBR>0.:
           P8gen.SetParameters("4122:addChannel      1   "+str(1.-sumBR)+"    0       22      -11")
	   if debug: cf.write('P8gen.SetParameters("4122:addChannel      1  '+str(1.-sumBR)+'    0       22      22")\n')

        #overwrite D+ decays
        P8gen.SetParameters("411:new  D+ D-    1   3   0    1.86962    0.00000    0.00000    0.00000  3.11800e-01   0   1   0   1   0")
	if debug: cf.write('P8gen.SetParameters("411:new D+          D-        1 3 0 1.86962 0.00000 0.00000 0.00000 3.11800e-01 0 1 0 1 0")\n')
        sumBR=0.
        if getbr(h,'d_mu',mass,couplings[1])>0.:
           P8gen.SetParameters("411:addChannel      1  "+str(getbr(h,'d_mu',mass,couplings[1])/maxsumBR)+"    0      -13       9900015")
	   if debug: cf.write('P8gen.SetParameters("411:addChannel       1  '+str(getbr(h,'d_mu',mass,couplings[1])/maxsumBR)+'    0      -13       9900015")\n')
           sumBR+=float(getbr(h,'d_mu',mass,couplings[1])/maxsumBR) 
        if getbr(h,'d_e',mass,couplings[1])>0.:
           P8gen.SetParameters("411:addChannel      1  "+str(getbr(h,'d_e',mass,couplings[0])/maxsumBR)+"    0      -11       9900015")
	   if debug: cf.write('P8gen.SetParameters("411:addChannel       1  '+str(getbr(h,'d_e',mass,couplings[0])/maxsumBR)+'    0      -11       9900015")\n')
           sumBR+=float(getbr(h,'d_e',mass,couplings[0])/maxsumBR) 
        if getbr(h,'d_tau',mass,couplings[2])>0.:
           P8gen.SetParameters("411:addChannel      1  "+str(getbr(h,'d_tau',mass,couplings[2])/maxsumBR)+"    0      -15       9900015")
	   if debug: cf.write('P8gen.SetParameters("411:addChannel       1  '+str(getbr(h,'d_tau',mass,couplings[2])/maxsumBR)+'    0      -15       9900015")\n')
           sumBR+=float(getbr(h,'d_tau',mass,couplings[2])/maxsumBR) 
        if getbr(h,'d_K0_e',mass,couplings[0])>0.:
           P8gen.SetParameters("411:addChannel      1  "+str(getbr(h,'d_K0_e',mass,couplings[0])/maxsumBR)+"   22      -11       9900015      311")
	   if debug: cf.write('P8gen.SetParameters("411:addChannel       1  '+str(getbr(h,'d_K0_e',mass,couplings[0])/maxsumBR)+'   22      -11       9900015      311")\n')
           sumBR+=float(getbr(h,'d_K0_e',mass,couplings[0])/maxsumBR) 
        if getbr(h,'d_K0_mu',mass,couplings[1])>0.:
           P8gen.SetParameters("411:addChannel      1  "+str(getbr(h,'d_K0_mu',mass,couplings[1])/maxsumBR)+"   22      -13       9900015      311")
	   if debug: cf.write('P8gen.SetParameters("411:addChannel       1  '+str(getbr(h,'d_K0_mu',mass,couplings[1])/maxsumBR)+'   22      -13       9900015      311")\n')
           sumBR+=float(getbr(h,'d_K0_mu',mass,couplings[1])/maxsumBR) 
        if sumBR<1. and sumBR>0.:
           P8gen.SetParameters("411:addChannel      1   "+str(1.-sumBR)+"    0       22      -11")
	   if debug: cf.write('P8gen.SetParameters("411:addChannel       1  '+str(1.-sumBR)+'    0       22      22")\n')
        P8gen.List(9900015)
	if debug: cf.write('P8gen.List(9900015)\n')
    if inclusive=="b":
        P8gen.SetParameters("HardQCD::hardbbbar  = on")
	if debug: cf.write('P8gen.SetParameters("HardQCD::hardbbbar  = on")\n')
        # add HNL
        #ctau = 5.4E+06 # for tests use 5.4E+03  # nominal ctau = 54 km = 5.4E+06 cm = 5.4E+07 mm
        #mass = 1.0 # GeV
        hnl_instance = hnl.HNL(mass, couplings, debug=True)
        ctau = hnl_instance.computeNLifetime(system="FairShip") * u.c_light * u.cm
        P8gen.SetParameters("9900015:new = N2 N2 2 0 0 "+str(mass)+" 0.0 0.0 0.0 "+str(ctau/u.mm)+"  0   1   0   1   0") 
	if debug: cf.write('P8gen.SetParameters("9900015:new = N2 N2 2 0 0 '+str(mass)+' 0.0 0.0 0.0 '+str(ctau/u.mm)+'  0   1   0   1   0")\n')
        P8gen.SetParameters("9900015:isResonance = false")
	if debug: cf.write('P8gen.SetParameters("9900015:isResonance = false"\n')
        # Configuring decay modes...
        readDecayTable.addHNLdecayChannels(P8gen, hnl_instance, conffile=os.path.expandvars('$FAIRSHIP/python/DecaySelection.conf'), verbose=True)
        # Finish HNL setup...
        P8gen.SetParameters("9900015:mayDecay = on")
	if debug: cf.write('P8gen.SetParameters("9900015:mayDecay = on")\n')
        P8gen.SetHNLId(9900015)
	if debug: cf.write('P8gen.SetHNLId(9900015)\n')
        # also add to PDG
        gamma = u.hbarc / float(ctau) #197.3269631e-16 / float(ctau) # hbar*c = 197 MeV*fm = 197e-16 GeV*cm
        addHNLtoROOT(pid=9900015,m=mass,g=gamma)
        # 12 14 16 neutrinos replace with N2
        beautyhistograms = ['bc_tau','b_D*0_bar_tau','bs_D_s-_tau','b_tau','lambdab_Lambda_c+_tau','Xib_Xi_c+_tau','Omega_b-_tau','b0_D*-_tau','bs_D*_s-_tau','b_D0_bar_tau','b0_D-_tau','b_e','bc_e','b_D*0_bar_e','b_D0_bar_e','b0_D*-_e','b0_D-_e','bs_D_s-_e','bs_D*_s-_e','bc_B_s0_e','bc_B0_e','bc_B*0_e','bc_B*_s0_e','lambdab_Lambda_c+_e','Xib_Xi_c+_e','Omega_b-_e','b_mu','bc_mu','b_D*0_bar_mu','b_D0_bar_mu','b0_D-_mu','b0_D*-_mu','bs_D_s-_mu','bs_D*_s-_mu','bc_B_s0_mu','bc_B0_mu','bc_B*0_mu','bc_B*_s0_mu','lambdab_Lambda_c+_mu','Xib_Xi_c+_mu','Omega_b-_mu','b_mu',] 
        maxsumBR=getmaxsumbr(h,beautyhistograms,mass,couplings,0.)
        if maxsumBR==0.:
           print "No phase space for HNL from b at this mass:",mass,". Quitting."
           sys.exit()
        totalBR=gettotalbr(h,beautyhistograms,mass,couplings,0.)
        #overwrite Lambda_b0 decays
        P8gen.SetParameters("5122:new  Lambda_b0        Lambda_bbar0    2   0   0    5.61940    0.00000    0.00000    0.00000  3.69000e-01   0   1   0   1   0")
	if debug: cf.write('P8gen.SetParameters("5122:new  Lambda_b0        Lambda_bbar0    2   0   0    5.61940    0.00000    0.00000    0.00000  3.69000e-01   0   1   0   1   0")\n')
        sumBR=0.
        if getbr(h,'lambdab_Lambda_c+_e',mass,couplings[0])>0.:
           P8gen.SetParameters("5122:addChannel      1  "+str(getbr(h,'lambdab_Lambda_c+_e',mass,couplings[0])/maxsumBR)+"   22      9900015       11     4122")
	   if debug: cf.write('P8gen.SetParameters("5122:addChannel      1  '+str(getbr(h,'lambdab_Lambda_c+_e',mass,couplings[0])/maxsumBR)+'   22      9900015       11     4122")\n')
           sumBR+=float(getbr(h,'lambdab_Lambda_c+_e',mass,couplings[0])/maxsumBR) 
        if getbr(h,'lambdab_Lambda_c+_mu',mass,couplings[1])>0.:
           P8gen.SetParameters("5122:addChannel      1  "+str(getbr(h,'lambdab_Lambda_c+_mu',mass,couplings[1])/maxsumBR)+"   22      9900015       13     4122")
	   if debug: cf.write('P8gen.SetParameters("5122:addChannel      1  '+str(getbr(h,'lambdab_Lambda_c+_mu',mass,couplings[1])/maxsumBR)+'   22      9900015       13     4122")\n')
           sumBR+=float(getbr(h,'lambdab_Lambda_c+_mu',mass,couplings[1])/maxsumBR) 
        if getbr(h,'lambdab_Lambda_c+_tau',mass,couplings[2])>0.:
           P8gen.SetParameters("5122:addChannel      1  "+str(getbr(h,'lambdab_Lambda_c+_tau',mass,couplings[2])/maxsumBR)+"   22      9900015       15     4122")
	   if debug: cf.write('P8gen.SetParameters("5122:addChannel      1  '+str(getbr(h,'lambdab_Lambda_c+_tau',mass,couplings[2])/maxsumBR)+'   22      9900015       15     4122")\n')
           sumBR+=float(getbr(h,'lambdab_Lambda_c+_tau',mass,couplings[2])/maxsumBR) 
        if sumBR<1. and sumBR>0.:
           P8gen.SetParameters("5122:addChannel      1   "+str(1.-sumBR)+"    0       22      -11")
	   if debug: cf.write('P8gen.SetParameters("5122:addChannel      1   '+str(1.-sumBR)+'    0       22      22")\n')
        #overwrite B+ decays
        P8gen.SetParameters("521:new  B+               B-    1   3   0    5.27925    0.00000    0.00000    0.00000  4.91100e-01   0   1   0   1   0")
	if debug: cf.write('P8gen.SetParameters("521:new  B+               B-    1   3   0    5.27925    0.00000    0.00000    0.00000  4.91100e-01   0   1   0   1   0")\n')
        sumBR=0.
        if getbr(h,'b_tau',mass,couplings[2])>0.:
           P8gen.SetParameters("521:addChannel      1  "+str(getbr(h,'b_tau',mass,couplings[2])/maxsumBR)+"    0       9900015      -15")
	   if debug: cf.write('P8gen.SetParameters("521:addChannel      1  '+str(getbr(h,'b_tau',mass,couplings[2])/maxsumBR)+'    0       9900015      -15")\n')
           sumBR+=float(getbr(h,'b_tau',mass,couplings[2])/maxsumBR) 
        if getbr(h,'b_mu',mass,couplings[2])>0.:
           P8gen.SetParameters("521:addChannel      1  "+str(getbr(h,'b_mu',mass,couplings[1])/maxsumBR)+"    0       9900015      -13")
	   if debug: cf.write('P8gen.SetParameters("521:addChannel      1  '+str(getbr(h,'b_mu',mass,couplings[1])/maxsumBR)+'    0       9900015      -13")\n')
           sumBR+=float(getbr(h,'b_mu',mass,couplings[1])/maxsumBR) 
        if getbr(h,'b_e',mass,couplings[2])>0.:
           P8gen.SetParameters("521:addChannel      1  "+str(getbr(h,'b_e',mass,couplings[0])/maxsumBR)+"    0       9900015      -11")
	   if debug: cf.write('P8gen.SetParameters("521:addChannel      1  '+str(getbr(h,'b_e',mass,couplings[0])/maxsumBR)+'    0       9900015      -11")\n')
           sumBR+=float(getbr(h,'b_e',mass,couplings[0])/maxsumBR) 
        if getbr(h,'b_D0_bar_e',mass,couplings[0])>0.:
           P8gen.SetParameters("521:addChannel      1  "+str(getbr(h,'b_D0_bar_e',mass,couplings[0])/maxsumBR)+"   22       9900015      -11     -421")
	   if debug: cf.write('P8gen.SetParameters("521:addChannel      1  '+str(getbr(h,'b_D0_bar_e',mass,couplings[0])/maxsumBR)+'   22       9900015      -11     -421")\n')
           sumBR+=float(getbr(h,'b_D0_bar_e',mass,couplings[0])/maxsumBR) 
        if getbr(h,'b_D*0_bar_e',mass,couplings[0])>0.:
           P8gen.SetParameters("521:addChannel      1  "+str(getbr(h,'b_D*0_bar_e',mass,couplings[0])/maxsumBR)+"   22       9900015      -11     -423")
	   if debug: cf.write('P8gen.SetParameters("521:addChannel      1  '+str(getbr(h,'b_D*0_bar_e',mass,couplings[0])/maxsumBR)+'   22       9900015      -11     -423")\n')
           sumBR+=float(getbr(h,'b_D*0_bar_e',mass,couplings[0])/maxsumBR) 
        if getbr(h,'b_D0_bar_mu',mass,couplings[1])>0.:
           P8gen.SetParameters("521:addChannel      1  "+str(getbr(h,'b_D0_bar_mu',mass,couplings[1])/maxsumBR)+"   22       9900015      -13     -421")
	   if debug: cf.write('P8gen.SetParameters("521:addChannel      1  '+str(getbr(h,'b_D0_bar_mu',mass,couplings[1])/maxsumBR)+'   22       9900015      -13     -421")\n')
           sumBR+=float(getbr(h,'b_D0_bar_mu',mass,couplings[1])/maxsumBR) 
        if getbr(h,'b_D*0_bar_mu',mass,couplings[1])>0.:
           P8gen.SetParameters("521:addChannel      1  "+str(getbr(h,'b_D*0_bar_mu',mass,couplings[1])/maxsumBR)+"   22       9900015      -13     -423")
	   if debug: cf.write('P8gen.SetParameters("521:addChannel      1  '+str(getbr(h,'b_D*0_bar_mu',mass,couplings[1])/maxsumBR)+'   22       9900015      -13     -423")\n')
           sumBR+=float(getbr(h,'b_D*0_bar_mu',mass,couplings[1])/maxsumBR) 
        if getbr(h,'b_D0_bar_tau',mass,couplings[2])>0.:
           P8gen.SetParameters("521:addChannel      1  "+str(getbr(h,'b_D0_bar_tau',mass,couplings[2])/maxsumBR)+"   22       9900015      -15     -421")
	   if debug: cf.write('P8gen.SetParameters("521:addChannel      1  '+str(getbr(h,'b_D0_bar_tau',mass,couplings[2])/maxsumBR)+'   22       9900015      -15     -421")\n')
           sumBR+=float(getbr(h,'b_D0_bar_tau',mass,couplings[2])/maxsumBR) 
        if getbr(h,'b_D*0_bar_tau',mass,couplings[2])>0.:
           P8gen.SetParameters("521:addChannel      1  "+str(getbr(h,'b_D*0_bar_tau',mass,couplings[2])/maxsumBR)+"   22       9900015      -15     -423")
	   if debug: cf.write('P8gen.SetParameters("521:addChannel      1  '+str(getbr(h,'b_D*0_bar_tau',mass,couplings[2])/maxsumBR)+'   22       9900015      -15     -423")\n')
           sumBR+=float(getbr(h,'b_D*0_bar_tau',mass,couplings[2])/maxsumBR) 
        if sumBR<1. and sumBR>0.:
           P8gen.SetParameters("521:addChannel      1   "+str(1.-sumBR)+"    0       22      22")
	   if debug: cf.write('P8gen.SetParameters("521:addChannel      1   '+str(1.-sumBR)+'    0       22      22")\n')
        #overwrite Xi_b0 decays
        P8gen.SetParameters("5232:new  Xi_b0            Xi_bbar0    2   0   0    5.78800    0.00000    0.00000    0.00000  3.64000e-01   0   1   0   1   0")
	if debug: cf.write('P8gen.SetParameters("5232:new  Xi_b0            Xi_bbar0    2   0   0    5.78800    0.00000    0.00000    0.00000  3.64000e-01   0   1   0   1   0")\n')
        sumBR=0.
        if sumBR<1. and sumBR>0.:
           P8gen.SetParameters("5232:addChannel      1   "+str(1.-sumBR)+"    0       22      22")
	   if debug: cf.write('P8gen.SetParameters("5232:addChannel      1   '+str(1.-sumBR)+'    0       22      22")\n')

        #overwrite B_s0 decays
        P8gen.SetParameters("531:new  B_s0             B_sbar0    1   0   0    5.36677    0.00000    0.00000    0.00000  4.39000e-01   0   1   0   1   0")
	if debug: cf.write('P8gen.SetParameters("531:new  B_s0             B_sbar0    1   0   0    5.36677    0.00000    0.00000    0.00000  4.39000e-01   0   1   0   1   0")\n')
        sumBR=0.
        if getbr(h,'bs_D_s-_e',mass,couplings[0])>0.:
           P8gen.SetParameters("531:addChannel      1  "+str(getbr(h,'bs_D_s-_e',mass,couplings[0])/maxsumBR)+"   22       9900015      -11     -431")
	   if debug: cf.write('P8gen.SetParameters("531:addChannel      1  '+str(getbr(h,'bs_D_s-_e',mass,couplings[0])/maxsumBR)+'   22       9900015      -11     -431")\n')
           sumBR+=float(getbr(h,'bs_D_s-_e',mass,couplings[0])/maxsumBR) 
        if getbr(h,'bs_D*_s-_e',mass,couplings[0])>0.:
           P8gen.SetParameters("531:addChannel      1  "+str(getbr(h,'bs_D*_s-_e',mass,couplings[0])/maxsumBR)+"   22       9900015      -11     -433")
	   if debug: cf.write('P8gen.SetParameters("531:addChannel      1  '+str(getbr(h,'bs_D*_s-_e',mass,couplings[0])/maxsumBR)+'   22       9900015      -11     -433")\n')
           sumBR+=float(getbr(h,'bs_D*_s-_e',mass,couplings[0])/maxsumBR) 
        if getbr(h,'bs_D_s-_mu',mass,couplings[1])>0.:
           P8gen.SetParameters("531:addChannel      1  "+str(getbr(h,'bs_D_s-_mu',mass,couplings[1])/maxsumBR)+"   22       9900015      -13     -431")
	   if debug: cf.write('P8gen.SetParameters("531:addChannel      1  '+str(getbr(h,'bs_D_s-_mu',mass,couplings[1])/maxsumBR)+'   22       9900015      -13     -431")\n')
           sumBR+=float(getbr(h,'bs_D_s-_mu',mass,couplings[1])/maxsumBR) 
        if getbr(h,'bs_D*_s-_mu',mass,couplings[1])>0.:
           P8gen.SetParameters("531:addChannel      1  "+str(getbr(h,'bs_D*_s-_mu',mass,couplings[1])/maxsumBR)+"   22       9900015      -13     -433")
	   if debug: cf.write('P8gen.SetParameters("531:addChannel      1  '+str(getbr(h,'bs_D*_s-_mu',mass,couplings[1])/maxsumBR)+'   22       9900015      -13     -433")\n')
           sumBR+=float(getbr(h,'bs_D*_s-_mu',mass,couplings[1])/maxsumBR) 
        if getbr(h,'bs_D_s-_tau',mass,couplings[2])>0.:
           P8gen.SetParameters("531:addChannel      1  "+str(getbr(h,'bs_D_s-_tau',mass,couplings[2])/maxsumBR)+"   22       9900015      -15     -431")
	   if debug: cf.write('P8gen.SetParameters("531:addChannel      1  '+str(getbr(h,'bs_D_s-_tau',mass,couplings[2])/maxsumBR)+'   22       9900015      -15     -431")\n')
           sumBR+=float(getbr(h,'bs_D_s-_tau',mass,couplings[2])/maxsumBR) 
        if getbr(h,'bs_D*_s-_tau',mass,couplings[2])>0.:
           P8gen.SetParameters("531:addChannel      1  "+str(getbr(h,'bs_D*_s-_tau',mass,couplings[2])/maxsumBR)+"   22       9900015      -15     -433")
	   if debug: cf.write('P8gen.SetParameters("531:addChannel      1  '+str(getbr(h,'bs_D*_s-_tau',mass,couplings[2])/maxsumBR)+'   22       9900015      -15     -433")\n')
           sumBR+=float(getbr(h,'bs_D*_s-_tau',mass,couplings[2])/maxsumBR) 
        if sumBR<1. and sumBR>0.:
           P8gen.SetParameters("531:addChannel      1   "+str(1.-sumBR)+"    0       22      22")
	   if debug: cf.write('P8gen.SetParameters("531:addChannel      1   '+str(1.-sumBR)+'    0       22      22")\n')

        #overwrite Omega_b- decays
        P8gen.SetParameters("5332:new  Omega_b-         Omega_bbar+    2   -3   0    6.07000    0.00000    0.00000    0.00000  3.64000e-01   0   1   0   1   0")
	if debug: cf.write('P8gen.SetParameters("5332:new  Omega_b-         Omega_bbar+    2   -3   0    6.07000    0.00000    0.00000    0.00000  3.64000e-01   0   1   0   1   0")\n')
        sumBR=0.
        if sumBR<1. and sumBR>0.:
           P8gen.SetParameters("5332:addChannel      1   "+str(1.-sumBR)+"    0       22      11")
	   if debug: cf.write('P8gen.SetParameters("5332:addChannel      1   '+str(1.-sumBR)+'    0       22      22")\n')

        #overwrite B_c+ decays
        P8gen.SetParameters("541:new  B_c+             B_c-    1   3   0    6.27700    0.00000    0.00000    0.00000  1.38000e-01   0   1   0   1   0")
	if debug: cf.write('P8gen.SetParameters("541:new  B_c+             B_c-    1   3   0    6.27700    0.00000    0.00000    0.00000  1.38000e-01   0   1   0   1   0")\n')
        sumBR=0.
        if getbr(h,'bc_tau',mass,couplings[2])>0.:
           P8gen.SetParameters("541:addChannel      1  "+str(getbr(h,'bc_tau',mass,couplings[2])/maxsumBR)+"    0       9900015      -15")
	   if debug: cf.write(' P8gen.SetParameters("541:addChannel      1  '+str(getbr(h,'bc_tau',mass,couplings[2])/maxsumBR)+'    0       9900015      -15")\n')
           sumBR+=float(getbr(h,'bc_tau',mass,couplings[2])/maxsumBR) 
        if getbr(h,'bc_e',mass,couplings[2])>0.:
           P8gen.SetParameters("541:addChannel      1  "+str(getbr(h,'bc_e',mass,couplings[0])/maxsumBR)+"    0       9900015      -11")
	   if debug: cf.write('P8gen.SetParameters("541:addChannel      1  '+str(getbr(h,'bc_e',mass,couplings[0])/maxsumBR)+'    0       9900015      -11")\n')
           sumBR+=float(getbr(h,'bc_e',mass,couplings[0])/maxsumBR) 
        if getbr(h,'bc_mu',mass,couplings[2])>0.:
           P8gen.SetParameters("541:addChannel      1  "+str(getbr(h,'bc_mu',mass,couplings[1])/maxsumBR)+"    0       9900015      -13")
	   if debug: cf.write('P8gen.SetParameters("541:addChannel      1  '+str(getbr(h,'bc_mu',mass,couplings[1])/maxsumBR)+'    0       9900015      -13")\n')
           sumBR+=float(getbr(h,'bc_mu',mass,couplings[1])/maxsumBR) 
        if getbr(h,'bc_B0_e',mass,couplings[0])>0.:
           P8gen.SetParameters("541:addChannel      1  "+str(getbr(h,'bc_B0_e',mass,couplings[0])/maxsumBR)+"   22      -11       9900015      511")
	   if debug: cf.write('P8gen.SetParameters("541:addChannel      1  '+str(getbr(h,'bc_B0_e',mass,couplings[0])/maxsumBR)+'   22      -11       9900015      511")\n')
           sumBR+=float(getbr(h,'bc_B0_e',mass,couplings[0])/maxsumBR) 
        if getbr(h,'bc_B*0_e',mass,couplings[0])>0.:
           P8gen.SetParameters("541:addChannel      1  "+str(getbr(h,'bc_B*0_e',mass,couplings[0])/maxsumBR)+"   22      -11       9900015      513")
	   if debug: cf.write('P8gen.SetParameters("541:addChannel      1  '+str(getbr(h,'bc_B*0_e',mass,couplings[0])/maxsumBR)+'   22      -11       9900015      513")\n')
           sumBR+=float(getbr(h,'bc_B*0_e',mass,couplings[0])/maxsumBR) 
        if getbr(h,'bc_B_s0_e',mass,couplings[0])>0.:
           P8gen.SetParameters("541:addChannel      1  "+str(getbr(h,'bc_B_s0_e',mass,couplings[0])/maxsumBR)+"   22      -11       9900015      531")
	   if debug: cf.write('P8gen.SetParameters("541:addChannel      1  '+str(getbr(h,'bc_B_s0_e',mass,couplings[0])/maxsumBR)+'   22      -11       9900015      531")\n')
           sumBR+=float(getbr(h,'bc_B_s0_e',mass,couplings[0])/maxsumBR) 
        if getbr(h,'bc_B*_s0_e',mass,couplings[0])>0.:
           P8gen.SetParameters("541:addChannel      1  "+str(getbr(h,'bc_B*_s0_e',mass,couplings[0])/maxsumBR)+"   22      -11       9900015      533")
	   if debug: cf.write('P8gen.SetParameters("541:addChannel      1  '+str(getbr(h,'bc_B*_s0_e',mass,couplings[0])/maxsumBR)+'   22      -11       9900015      533")\n')
           sumBR+=float(getbr(h,'bc_B*_s0_e',mass,couplings[0])/maxsumBR) 
        if getbr(h,'bc_B0_mu',mass,couplings[1])>0.:
           P8gen.SetParameters("541:addChannel      1  "+str(getbr(h,'bc_B0_mu',mass,couplings[1])/maxsumBR)+"   22      -13       9900015      511")
	   if debug: cf.write('P8gen.SetParameters("541:addChannel      1  '+str(getbr(h,'bc_B0_mu',mass,couplings[1])/maxsumBR)+'   22      -13       9900015      511")\n')
           sumBR+=float(getbr(h,'bc_B0_mu',mass,couplings[1])/maxsumBR) 
        if getbr(h,'bc_B*0_mu',mass,couplings[1])>0.:
           P8gen.SetParameters("541:addChannel      1  "+str(getbr(h,'bc_B*0_mu',mass,couplings[1])/maxsumBR)+"   22      -13       9900015      513")
	   if debug: cf.write('P8gen.SetParameters("541:addChannel      1  '+str(getbr(h,'bc_B*0_mu',mass,couplings[1])/maxsumBR)+'   22      -13       9900015      513")\n')
           sumBR+=float(getbr(h,'bc_B*0_mu',mass,couplings[1])/maxsumBR) 
        if getbr(h,'bc_B_s0_mu',mass,couplings[1])>0.:
           P8gen.SetParameters("541:addChannel      1  "+str(getbr(h,'bc_B_s0_mu',mass,couplings[1])/maxsumBR)+"   22      -13       9900015      531")
	   if debug: cf.write('P8gen.SetParameters("541:addChannel      1  '+str(getbr(h,'bc_B_s0_mu',mass,couplings[1])/maxsumBR)+'   22      -13       9900015      531")\n')
           sumBR+=float(getbr(h,'bc_B_s0_mu',mass,couplings[1])/maxsumBR) 
        if getbr(h,'bc_B*_s0_mu',mass,couplings[1])>0.:
           P8gen.SetParameters("541:addChannel      1  "+str(getbr(h,'bc_B*_s0_mu',mass,couplings[1])/maxsumBR)+"   22      -13       9900015      533")
	   if debug: cf.write('P8gen.SetParameters("541:addChannel      1  '+str(getbr(h,'bc_B*_s0_mu',mass,couplings[1])/maxsumBR)+'   22      -13       9900015      533")\n')
           sumBR+=float(getbr(h,'bc_B*_s0_mu',mass,couplings[1])/maxsumBR) 
        if sumBR<1. and sumBR>0.:
           P8gen.SetParameters("541:addChannel      1   "+str(1.-sumBR)+"    0       22      -11")
	   if debug: cf.write('P8gen.SetParameters("541:addChannel      1   '+str(1.-sumBR)+'    0       22      22")\n')

        #overwrite B0 decays
        P8gen.SetParameters("511:new  B0  Bbar0    1   0   0    5.27958    0.00000    0.00000    0.00000  4.58700e-01   0   1   0   1   0")
	if debug: cf.write('P8gen.SetParameters("511:new  B0  Bbar0    1   0   0    5.27958    0.00000    0.00000    0.00000  4.58700e-01   0   1   0   1   0")\n')
        sumBR=0.
        if getbr(h,'b0_D-_e',mass,couplings[0])>0.:
           P8gen.SetParameters("511:addChannel      1  "+str(getbr(h,'b0_D-_e',mass,couplings[0])/maxsumBR)+"   22       9900015      -11     -411")
	   if debug: cf.write('P8gen.SetParameters("511:addChannel      1  '+str(getbr(h,'b0_D-_e',mass,couplings[0])/maxsumBR)+'   22       9900015      -11     -411")\n')
           sumBR+=float(getbr(h,'b0_D-_e',mass,couplings[0])/maxsumBR) 
        if getbr(h,'b0_D*-_e',mass,couplings[0])>0.:
           P8gen.SetParameters("511:addChannel      1  "+str(getbr(h,'b0_D*-_e',mass,couplings[0])/maxsumBR)+"   22       9900015      -11     -413")
	   if debug: cf.write('P8gen.SetParameters("511:addChannel      1  '+str(getbr(h,'b0_D*-_e',mass,couplings[0])/maxsumBR)+'   22       9900015      -11     -413")\n')
           sumBR+=float(getbr(h,'b0_D*-_e',mass,couplings[0])/maxsumBR) 
        if getbr(h,'b0_D-_mu',mass,couplings[1])>0.:
           P8gen.SetParameters("511:addChannel      1  "+str(getbr(h,'b0_D-_mu',mass,couplings[1])/maxsumBR)+"   22       9900015      -13     -411")
	   if debug: cf.write('P8gen.SetParameters("511:addChannel      1  '+str(getbr(h,'b0_D-_mu',mass,couplings[1])/maxsumBR)+'   22       9900015      -13     -411")\n')
           sumBR+=float(getbr(h,'b0_D-_mu',mass,couplings[1])/maxsumBR) 
        if getbr(h,'b0_D*-_mu',mass,couplings[1])>0.:
           P8gen.SetParameters("511:addChannel      1  "+str(getbr(h,'b0_D*-_mu',mass,couplings[1])/maxsumBR)+"   22       9900015      -13     -413")
	   if debug: cf.write('P8gen.SetParameters("511:addChannel      1  '+str(getbr(h,'b0_D*-_mu',mass,couplings[1])/maxsumBR)+'   22       9900015      -13     -413")\n')
           sumBR+=float(getbr(h,'b0_D*-_mu',mass,couplings[1])/maxsumBR) 
        if getbr(h,'b0_D-_tau',mass,couplings[2])>0.:
           P8gen.SetParameters("511:addChannel      1  "+str(getbr(h,'b0_D-_tau',mass,couplings[2])/maxsumBR)+"   22       9900015      -15     -411")
	   if debug: cf.write('P8gen.SetParameters("511:addChannel      1  '+str(getbr(h,'b0_D-_tau',mass,couplings[2])/maxsumBR)+'   22       9900015      -15     -411")\n')
           sumBR+=float(getbr(h,'b0_D-_tau',mass,couplings[2])/maxsumBR) 
        if getbr(h,'b0_D*-_tau',mass,couplings[2])>0.:
           P8gen.SetParameters("511:addChannel      1  "+str(getbr(h,'b0_D*-_tau',mass,couplings[2])/maxsumBR)+"   22       9900015      -15     -413")
	   if debug: cf.write('P8gen.SetParameters("511:addChannel      1  '+str(getbr(h,'b0_D*-_tau',mass,couplings[2])/maxsumBR)+'   22       9900015      -15     -413")\n')
           sumBR+=float(getbr(h,'b0_D*-_tau',mass,couplings[2])/maxsumBR) 
        if sumBR<1. and sumBR>0.:
           P8gen.SetParameters("511:addChannel      1   "+str(1.-sumBR)+"    0       22      22")
	   if debug: cf.write('P8gen.SetParameters("511:addChannel      1   '+str(1.-sumBR)+'    0       22      22")\n')
        P8gen.List(9900015)
        if debug: cf.write('P8gen.List(9900015)\n')
    if debug: cf.close()
