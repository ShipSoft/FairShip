import ROOT, os, sys
import shipunit as u
import hnl,rpvsusy
from pythia8_conf_utils import *
import readDecayTable

def configurerpvsusy(P8gen, mass, couplings, sfermionmass, benchmark, inclusive, deepCopy=False):
    # configure pythia8 for Ship usage
    debug=True
    if debug: cf=open('pythia8_conf.txt','w')
    h=readFromAscii("branchingratiosrpvsusybench%d"%benchmark)
    P8gen.UseRandom3() 
    P8gen.SetMom(400)  # beam momentum in GeV 
    if deepCopy: P8gen.UseDeepCopy()
    pdg = ROOT.TDatabasePDG.Instance()
    # let strange particle decay in Geant4
    p8 = P8gen.getPythiaInstance()
    n=1
    while n!=0:
     n = p8.particleData.nextId(n)
     p = p8.particleData.particleDataEntryPtr(n)
     if p.tau0()>1: 
      command = str(n)+":mayDecay = false"
      p8.readString(command)
      print "Pythia8 configuration: Made %s stable for Pythia, should decay in Geant4"%(p.name())
    if inclusive=="True":
        P8gen.SetParameters("SoftQCD:inelastic = on")
        P8gen.SetParameters("PhotonCollision:gmgm2mumu = on")
        P8gen.SetParameters("PromptPhoton:all = on")
        P8gen.SetParameters("WeakBosonExchange:all = on")
        
    # generate RPV neutralino from inclusive charm hadrons
    if inclusive=="c":
        P8gen.SetParameters("HardQCD::hardccbar  = on")
	if debug: cf.write('P8gen.SetParameters("HardQCD::hardccbar  = on")\n')
        # add RPVSUSY
        rpvsusy_instance = rpvsusy.RPVSUSY(mass, couplings, sfermionmass, benchmark, debug=True)
        ctau = rpvsusy_instance.computeNLifetime(system="FairShip") * u.c_light * u.cm
        print "RPVSUSY ctau ",ctau
        P8gen.SetParameters("9900015:new = N2 N2 2 0 0 "+str(mass)+" 0.0 0.0 0.0 "+str(ctau/u.mm)+"  0   1   0   1   0") 
        if debug: cf.write('P8gen.SetParameters("9900015:new = N2 N2 2 0 0 '+str(mass)+' 0.0 0.0 0.0 '+str(ctau/u.mm)+'  0   1   0   1   0") \n')
        P8gen.SetParameters("9900015:isResonance = false")
        if debug: cf.write('P8gen.SetParameters("9900015:isResonance = false")\n')
	P8gen.SetParameters("Next:numberCount    =  0")
        if debug: cf.write('P8gen.SetParameters("Next:numberCount    =  0")\n')
        # Configuring decay modes...
        rpvsusy_instance.AddChannelsToPythia(P8gen)

        # Finish HNL setup...
        P8gen.SetParameters("9900015:mayDecay = on")
	if debug: cf.write('P8gen.SetParameters("9900015:mayDecay = on")\n')
        P8gen.SetHNLId(9900015)
	if debug: cf.write('P8gen.SetHNLId(9900015)\n')
        # also add to PDG
        gamma = u.hbarc / float(ctau) #197.3269631e-16 / float(ctau) # hbar*c = 197 MeV*fm = 197e-16 GeV*cm
        addHNLtoROOT(pid=9900015,m=mass,g=gamma)
        # 12 14 16 neutrinos replace with N2
        charmhistograms = ['d_mu','ds_mu']
        # no tau decay here to consider
        totaltauBR      = 0.0 
        maxsumBR        = getmaxsumbrrpvsusy(h,charmhistograms,mass,couplings)
        if maxsumBR==0.:
           print "No phase space for RPV neutralino from c at this mass:",mass,". Quitting."
           sys.exit()
        totalBR         = gettotalbrrpvsusy(h,charmhistograms,mass,couplings)
        

        #overwrite D_s+ decays
        P8gen.SetParameters("431:new  D_s+  D_s-    1   3   0    1.96849"\
                            "    0.00000    0.00000    0.00000  1.49900e-01   0   1   0   1   0")
	if debug: cf.write('P8gen.SetParameters("431:new  D_s+      D_s-        1 3 0 1.96849'\
                           '    0.00000 0.00000 0.00000 1.49900e-01 0 1 0 1 0")\n')
        sumBR=0.
        if getbr(h,'ds_mu',mass,couplings[1])>0.:
           P8gen.SetParameters("431:addChannel      1  "+str(getbr(h,'ds_mu',mass,couplings[1])/maxsumBR)+\
                               "    0      -13       9900015")
	   if debug: cf.write('P8gen.SetParameters("431:addChannel       1  '+\
                              str(getbr(h,'ds_mu',mass,couplings[1])/maxsumBR)+'    0      -13       9900015")\n')
           sumBR+=float(getbr(h,'ds_mu',mass,couplings[1])/maxsumBR) 
        if sumBR<1. and sumBR>0.:
            P8gen.SetParameters("431:addChannel      1   "+str(1.-sumBR)+"    0       22      -11")
            if debug: cf.write('P8gen.SetParameters("411:addChannel       1  '+\
                               str(1.-sumBR)+'    0       22      22")\n')
        
        #overwrite D+ decays
        P8gen.SetParameters("411:new  D+ D-    1   3   0    1.86962"\
                            "    0.00000    0.00000    0.00000  3.11800e-01   0   1   0   1   0")
	if debug: cf.write('P8gen.SetParameters("411:new D+          D-        1 3 0 1.86962'\
                           ' 0.00000 0.00000 0.00000 3.11800e-01 0 1 0 1 0")\n')
        sumBR=0.
        if getbr(h,'d_mu',mass,couplings[1])>0.:
           P8gen.SetParameters("411:addChannel      1  "+str(getbr(h,'d_mu',mass,couplings[1])/maxsumBR)+\
                               "    0      -13       9900015")
	   if debug: cf.write('P8gen.SetParameters("411:addChannel       1  '+\
                              str(getbr(h,'d_mu',mass,couplings[1])/maxsumBR)+\
                              '    0      -13       9900015")\n')
           sumBR+=float(getbr(h,'d_mu',mass,couplings[1])/maxsumBR) 
        if sumBR<1. and sumBR>0.:
           P8gen.SetParameters("411:addChannel      1   "+str(1.-sumBR)+"    0       22      -11")
	   if debug: cf.write('P8gen.SetParameters("411:addChannel       1  '+\
                              str(1.-sumBR)+'    0       22      22")\n')
        
        P8gen.List(9900015)
	if debug: cf.write('P8gen.List(9900015)\n')

    if inclusive=="b":
        P8gen.SetParameters("HardQCD::hardbbbar  = on")
	if debug: cf.write('P8gen.SetParameters("HardQCD::hardbbbar  = on")\n')
        # add RPVSUSY
        rpvsusy_instance = rpvsusy.RPVSUSY(mass, couplings, sfermionmass, benchmark, debug=True)
        ctau = rpvsusy_instance.computeNLifetime(system="FairShip") * u.c_light * u.cm
        P8gen.SetParameters("9900015:new = N2 N2 2 0 0 "+str(mass)+" 0.0 0.0 0.0 "+str(ctau/u.mm)+"  0   1   0   1   0") 
	if debug: cf.write('P8gen.SetParameters("9900015:new = N2 N2 2 0 0 '+str(mass)+' 0.0 0.0 0.0 '+str(ctau/u.mm)+'  0   1   0   1   0")\n')
        P8gen.SetParameters("9900015:isResonance = false")
	if debug: cf.write('P8gen.SetParameters("9900015:isResonance = false"\n')
        # Configuring decay modes...
        rpvsusy_instance.AddChannelsToPythia(P8gen)
        # Finish HNL setup...
        P8gen.SetParameters("9900015:mayDecay = on")
	if debug: cf.write('P8gen.SetParameters("9900015:mayDecay = on")\n')
        P8gen.SetHNLId(9900015)
	if debug: cf.write('P8gen.SetHNLId(9900015)\n')
        # also add to PDG
        gamma = u.hbarc / float(ctau) #197.3269631e-16 / float(ctau) # hbar*c = 197 MeV*fm = 197e-16 GeV*cm
        addHNLtoROOT(pid=9900015,m=mass,g=gamma)
        # 12 14 16 neutrinos replace with N2
        beautyhistograms = ['b_mu','b_tau','b0_nu_mu','b0_nu_tau']
        maxsumBR=getmaxsumbrrpvsusy(h,beautyhistograms,mass,couplings)
        if maxsumBR==0.:
           print "No phase space for HNL from b at this mass:",mass,". Quitting."
           sys.exit()
        totalBR=gettotalbrrpvsusy(h,beautyhistograms,mass,couplings)

        #overwrite B+ decays
        P8gen.SetParameters("521:new  B+               B-    1   3   0    5.27925"\
                            "0.00000    0.00000    0.00000  4.91100e-01   0   1   0   1   0")
	if debug: cf.write('P8gen.SetParameters("521:new  B+               B-    1   3   0'\
                           '5.27925    0.00000    0.00000    0.00000  4.91100e-01   0   1   0   1   0")\n')
        sumBR=0.
        if getbr(h,'b_tau',mass,couplings[1])>0.:
           P8gen.SetParameters("521:addChannel      1  "+\
                               str(getbr(h,'b_tau',mass,couplings[1])/maxsumBR)+"    0       9900015      -15")
	   if debug: cf.write('P8gen.SetParameters("521:addChannel      1  '+\
                              str(getbr(h,'b_tau',mass,couplings[1])/maxsumBR)+'    0       9900015      -15")\n')
           sumBR+=float(getbr(h,'b_tau',mass,couplings[1])/maxsumBR) 
        if sumBR<1. and sumBR>0.:
           P8gen.SetParameters("521:addChannel      1   "+\
                               str(1.-sumBR)+"    0       22      22")
	   if debug: cf.write('P8gen.SetParameters("521:addChannel      1   '+\
                              str(1.-sumBR)+'    0       22      22")\n')

        #overwrite B0 decays
        P8gen.SetParameters("511:new  B0  Bbar0    1   0   0    5.27958"\
                            "    0.00000    0.00000    0.00000  4.58700e-01   0   1   0   1   0")
	if debug: cf.write('P8gen.SetParameters("511:new  B0  Bbar0    1   0   0'\
                           '    5.27958    0.00000    0.00000    0.00000  4.58700e-01   0   1   0   1   0")\n')
        sumBR=0.
        if getbr(h,'b0_nu_tau',mass,couplings[1])>0.:
           P8gen.SetParameters("511:addChannel      1  "+\
                               str(getbr(h,'b0_nu_tau',mass,couplings[1])/maxsumBR)+\
                               "   22       9900015      16")
        if sumBR<1. and sumBR>0.:
           P8gen.SetParameters("511:addChannel      1   "+\
                               str(1.-sumBR)+"    0       22      22")
	   if debug: cf.write('P8gen.SetParameters("511:addChannel      1   '+\
                              str(1.-sumBR)+'    0       22      22")\n')
        
        P8gen.List(9900015)
        if debug: cf.write('P8gen.List(9900015)\n')
    
    if debug: cf.close()
    





def configure(P8gen, mass, couplings, inclusive, deepCopy=False):
    # configure pythia8 for Ship usage
    debug=True
    if debug: cf=open('pythia8_conf.txt','w')
    h=readFromAscii()
    P8gen.UseRandom3() # TRandom1 or TRandom3 ?
    P8gen.SetMom(400)  # beam momentum in GeV 
    if deepCopy: P8gen.UseDeepCopy()
    pdg = ROOT.TDatabasePDG.Instance()
    # let strange particle decay in Geant4
    p8 = P8gen.getPythiaInstance()
    n=1
    while n!=0:
     n = p8.particleData.nextId(n)
     p = p8.particleData.particleDataEntryPtr(n)
     if p.tau0()>1: 
      command = str(n)+":mayDecay = false"
      p8.readString(command)
      print "Pythia8 configuration: Made %s stable for Pythia, should decay in Geant4"%(p.name())
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
        print "HNL ctau",ctau
        P8gen.SetParameters("9900015:new = N2 N2 2 0 0 "+str(mass)+" 0.0 0.0 0.0 "+str(ctau/u.mm)+"  0   1   0   1   0") 
        if debug: cf.write('P8gen.SetParameters("9900015:new = N2 N2 2 0 0 '+str(mass)+' 0.0 0.0 0.0 '+str(ctau/u.mm)+'  0   1   0   1   0") \n')
        P8gen.SetParameters("9900015:isResonance = false")
        if debug: cf.write('P8gen.SetParameters("9900015:isResonance = false")\n')
	P8gen.SetParameters("Next:numberCount    =  0")
        if debug: cf.write('P8gen.SetParameters("Next:numberCount    =  0")\n')
        # Configuring decay modes...
        readDecayTable.addHNLdecayChannels(P8gen, hnl_instance, conffile=os.path.expandvars('$FAIRSHIP/python/DecaySelection.conf'), verbose=False)
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
        channels = [ {'id':'4132','decay':'xic0_Xi-_e',   'coupling':0,'idlepton':-11,'idhadron':-3312},\
                     {'id':'4132','decay':'xic0_Xi-_mu',  'coupling':1,'idlepton':-11,'idhadron':-3312}]
        setChannels(P8gen,h,channels,mass,couplings,maxsumBR)

        #overwrite D0 decays
        P8gen.SetParameters("421:new  D0  Dbar0    1   0   0    1.86486    0.00000    0.00000    0.00000  1.22900e-01   0   1   0   1   0")
        channels = [ {'id':'421','decay':'d0_K-_e',   'coupling':0,'idlepton':-11,'idhadron':-321},\
                     {'id':'421','decay':'d0_K*-_e',  'coupling':0,'idlepton':-11,'idhadron':-323},\
                     {'id':'421','decay':'d0_K-_mu',  'coupling':1,'idlepton':-13,'idhadron':-321},\
                     {'id':'421','decay':'d0_K*-_mu', 'coupling':1,'idlepton':-13,'idhadron':-323}]
        setChannels(P8gen,h,channels,mass,couplings,maxsumBR)

        #overwrite tau- decays
        P8gen.SetParameters("15:new  tau-  tau+    2   -3   0    1.77682    0.00000    0.00000    0.00000  8.71100e-02   0   1   0   1   0")
        channels = [ {'id':'15','decay':'tau_pi-', 'coupling':2,'idhadron':-211},\
                     {'id':'15','decay':'tau_K-',  'coupling':2,'idhadron':-321},\
                     {'id':'15','decay':'tau_rho-',  'coupling':2,'idhadron':-213},\
                     {'id':'15','decay':'tau__nu_e_bar_e',  'coupling':2,'idlepton':11,'idhadron':-12},\
                     {'id':'15','decay':'tau_nu_tau_e',     'coupling':2,'idlepton':11,'idhadron':-16},\
                     {'id':'15','decay':'tau_nu_mu_bar_mu',     'coupling':2,'idlepton':13,'idhadron':-14},\
                     {'id':'15','decay':'tau_nu_tau_mu',     'coupling':2,'idlepton':13,'idhadron':-16}]
        setChannels(P8gen,h,channels,mass,couplings,maxsumBR)

        #overwrite D_s+ decays
        P8gen.SetParameters("431:new  D_s+  D_s-    1   3   0    1.96849    0.00000    0.00000    0.00000  1.49900e-01   0   1   0   1   0")
        channels = [ {'id':'431','decay':'ds_mu', 'coupling':1,'idlepton':-13},\
                     {'id':'411','decay':'ds_e',  'coupling':0,'idlepton':-11},\
                     {'id':'411','decay':'ds_tau','coupling':2,'idlepton':-15}]
        setChannels(P8gen,h,channels,mass,couplings,maxsumBR)

        #overwrite Lambda_c+ decays
        P8gen.SetParameters("4122:new  Lambda_c+   Lambda_cbar-    2   3   0    2.28646    0.00000    0.00000    0.00000  5.99000e-02   0   1   0   1   0")
        channels = [ {'id':'4122','decay':'lambdac_Lambda0_e', 'coupling':0,'idlepton':-11,'idhadron':3122},\
                     {'id':'4122','decay':'lambdac_Lambda0_mu', 'coupling':1,'idlepton':-13,'idhadron':3122}]
        setChannels(P8gen,h,channels,mass,couplings,maxsumBR)

        #overwrite D+ decays
        P8gen.SetParameters("411:new  D+ D-    1   3   0    1.86962    0.00000    0.00000    0.00000  3.11800e-01   0   1   0   1   0")
        channels = [ {'id':'411','decay':'d_mu', 'coupling':1,'idlepton':-13},\
                     {'id':'411','decay':'d_e',  'coupling':0,'idlepton':-11},\
                     {'id':'411','decay':'d_tau','coupling':2,'idlepton':-15},\
                     {'id':'411','decay':'d_K0_e','coupling':0,'idlepton':-11,'idhadron':311},\
                     {'id':'411','decay':'d_K0_mu','coupling':1,'idlepton':-13,'idhadron':311}]
        setChannels(P8gen,h,channels,mass,couplings,maxsumBR)
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
        beautyhistograms = ['bc_tau','b_D*0_bar_tau','bs_D_s-_tau','b_tau','lambdab_Lambda_c+_tau','Xib_Xi_c+_tau',\
                            'Omega_b-_tau','b0_D*-_tau','bs_D*_s-_tau','b_D0_bar_tau','b0_D-_tau','b_e','bc_e','b_D*0_bar_e',\
                            'b_D0_bar_e','b0_D*-_e','b0_D-_e','bs_D_s-_e','bs_D*_s-_e','bc_B_s0_e','bc_B0_e','bc_B*0_e','bc_B*_s0_e',\
                            'lambdab_Lambda_c+_e','Xib_Xi_c+_e','Omega_b-_e','b_mu','bc_mu','b_D*0_bar_mu','b_D0_bar_mu','b0_D-_mu',\
                            'b0_D*-_mu','bs_D_s-_mu','bs_D*_s-_mu','bc_B_s0_mu','bc_B0_mu','bc_B*0_mu','bc_B*_s0_mu','lambdab_Lambda_c+_mu','Xib_Xi_c+_mu','Omega_b-_mu','b_mu']
# disable Bc until production is sorted out
        tmp = []
        for x in beautyhistograms:
           if  x[:2]=='bc': continue
           tmp.append(x)
        beautyhistograms = tmp
        maxsumBR=getmaxsumbr(h,beautyhistograms,mass,couplings,0.)
        if maxsumBR==0.:
           print "No phase space for HNL from b at this mass:",mass,". Quitting."
           sys.exit()
        totalBR=gettotalbr(h,beautyhistograms,mass,couplings,0.)
        #overwrite Lambda_b0 decays
        P8gen.SetParameters("5122:new  Lambda_b0        Lambda_bbar0    2   0   0    5.61940    0.00000    0.00000    0.00000  3.69000e-01   0   1   0   1   0")
        channels = [ {'id':'5122','decay':'lambdab_Lambda_c+_e','coupling':0,'idlepton':11,'idhadron':4122},\
                     {'id':'5122','decay':'lambdab_Lambda_c+_mu','coupling':1,'idlepton':13,'idhadron':4122},\
                     {'id':'5122','decay':'lambdab_Lambda_c+_tau','coupling':2,'idlepton':15,'idhadron':4122}]
        setChannels(P8gen,h,channels,mass,couplings,maxsumBR)

        #overwrite B+ decays
        P8gen.SetParameters("521:new  B+               B-    1   3   0    5.27925    0.00000    0.00000    0.00000  4.91100e-01   0   1   0   1   0")
        channels = [ {'id':'521','decay':'b_tau','coupling':2,'idlepton':-15},\
                     {'id':'521','decay':'b_mu', 'coupling':1,'idlepton':-13},\
                     {'id':'521','decay':'b_e',  'coupling':0,'idlepton':-11},\
                     {'id':'521','decay':'b_D0_bar_e',   'coupling':0,'idlepton':-11,'idhadron':-421},\
                     {'id':'521','decay':'b_D*0_bar_e',  'coupling':0,'idlepton':-11,'idhadron':-423},\
                     {'id':'521','decay':'b_D0_bar_mu',   'coupling':1,'idlepton':-13,'idhadron':-421},\
                     {'id':'521','decay':'b_D*0_bar_mu',  'coupling':1,'idlepton':-13,'idhadron':-423},\
                     {'id':'521','decay':'b_D0_bar_tau',   'coupling':2,'idlepton':-15,'idhadron':-421},\
                     {'id':'521','decay':'b_D*0_bar_tau',  'coupling':2,'idlepton':-15,'idhadron':-423}]
        setChannels(P8gen,h,channels,mass,couplings,maxsumBR)

        #overwrite Xi_b0 decays
        P8gen.SetParameters("5232:new  Xi_b0            Xi_bbar0    2   0   0    5.78800    0.00000    0.00000    0.00000  3.64000e-01   0   1   0   1   0")
        channels = [ {'id':'5232','decay':'Xib_Xi_c+_tau','coupling':2,'idlepton':-15},\
                     {'id':'5232','decay':'Xib_Xi_c+_mu','coupling':1,'idlepton':-13},\
                     {'id':'5232','decay':'Xib_Xi_c+_e','coupling':0,'idlepton':-11}]
        setChannels(P8gen,h,channels,mass,couplings,maxsumBR)

        #overwrite B_s0 decays
        P8gen.SetParameters("531:new  B_s0             B_sbar0    1   0   0    5.36677    0.00000    0.00000    0.00000  4.39000e-01   0   1   0   1   0")
        channels = [ {'id':'531','decay':'bs_D_s-_e',   'coupling':0,'idlepton':-11,'idhadron':-431},\
                     {'id':'531','decay':'bs_D*_s-_e',  'coupling':0,'idlepton':-11,'idhadron':-433},\
                     {'id':'531','decay':'bs_D_s-_mu',  'coupling':1,'idlepton':-13,'idhadron':-431},\
                     {'id':'531','decay':'bs_D*_s-_mu', 'coupling':1,'idlepton':-13,'idhadron':-433},\
                     {'id':'531','decay':'bs_D_s-_tau', 'coupling':2,'idlepton':-15,'idhadron':-431},\
                     {'id':'531','decay':'bs_D*_s-_tau','coupling':2,'idlepton':-15,'idhadron':-433}]
        setChannels(P8gen,h,channels,mass,couplings,maxsumBR)

        #overwrite Omega_b- decays
        P8gen.SetParameters("5332:new  Omega_b-         Omega_bbar+    2   -3   0    6.07000    0.00000    0.00000    0.00000  3.64000e-01   0   1   0   1   0")
        channels = [ {'id':'5332','decay':'Omega_b-_tau','coupling':2,'idlepton':-15},\
                     {'id':'5332','decay':'Omega_b-_mu','coupling':1,'idlepton':-13},\
                     {'id':'5332','decay':'Omega_b-_e','coupling':0,'idlepton':-11}]
        setChannels(P8gen,h,channels,mass,couplings,maxsumBR)

        #overwrite B_c+ decays
        P8gen.SetParameters("541:new  B_c+             B_c-    1   3   0    6.27700    0.00000    0.00000    0.00000  1.38000e-01   0   1   0   1   0")
        channels = [ {'id':'541','decay':'bc_tau','coupling':2,'idlepton':-15},\
                     {'id':'541','decay':'bc_e',  'coupling':0,'idlepton':-11},\
                     {'id':'541','decay':'bc_mu', 'coupling':1,'idlepton':-13},\
                     {'id':'541','decay':'bc_B0_e',    'coupling':0,'idlepton':-11,'idhadron':511},\
                     {'id':'541','decay':'bc_B*0_e',   'coupling':0,'idlepton':-11,'idhadron':513},\
                     {'id':'541','decay':'bc_B_s0_e',  'coupling':0,'idlepton':-11,'idhadron':531},\
                     {'id':'541','decay':'bc_B*_s0_e', 'coupling':0,'idlepton':-11,'idhadron':533},\
                     {'id':'541','decay':'bc_B0_mu',   'coupling':1,'idlepton':-13,'idhadron':511},\
                     {'id':'541','decay':'bc_B*0_mu',  'coupling':1,'idlepton':-13,'idhadron':513},\
                     {'id':'541','decay':'bc_B_s0_mu', 'coupling':1,'idlepton':-13,'idhadron':531},\
                     {'id':'541','decay':'bc_B*_s0_mu','coupling':1,'idlepton':-13,'idhadron':533} ]
        setChannels(P8gen,h,channels,mass,couplings,maxsumBR)

        #overwrite B0 decays
        P8gen.SetParameters("511:new  B0  Bbar0    1   0   0    5.27958    0.00000    0.00000    0.00000  4.58700e-01   0   1   0   1   0")
        channels = [ {'id':'511','decay':'b0_D-_e',   'coupling':0,'idlepton':-11,'idhadron':-411},\
                     {'id':'511','decay':'b0_D*-_e',  'coupling':0,'idlepton':-11,'idhadron':-413},\
                     {'id':'511','decay':'b0_D-_mu',  'coupling':1,'idlepton':-13,'idhadron':-411},\
                     {'id':'511','decay':'b0_D*-_mu', 'coupling':1,'idlepton':-13,'idhadron':-413},\
                     {'id':'511','decay':'b0_D-_tau', 'coupling':2,'idlepton':-15,'idhadron':-411},\
                     {'id':'511','decay':'b0_D*-_tau','coupling':2,'idlepton':-15,'idhadron':-413} ]
        setChannels(P8gen,h,channels,mass,couplings,maxsumBR)

        P8gen.List(9900015)
        if debug: cf.write('P8gen.List(9900015)\n')
    if debug: cf.close()
