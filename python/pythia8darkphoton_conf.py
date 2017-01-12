import ROOT, os, sys
import shipunit as u
import readDecayTable
import darkphoton

# Boundaries for production in meson decays
# mass of the meson - mass of other decay product!!
pi0Start = 0.
pi0Stop = 0.13498
etaStart = 0.13498
etaStop = 0.54786
omegaStart = 0.54786
omegaStop = 0.64767 # 0.78265-0.13498
eta1Start = 0.64767
eta1Stop = 0.95778


def addDPtoROOT(pid=9900015 ,m = 0.2, g=4.866182e-04):
    pdg = ROOT.TDatabasePDG.Instance()
    pdg.AddParticle('A','DarkPhoton', m, False, g, 0., 'A', pid)


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

def manipulatePhysics(mass, P8gen, cf):
    if (pi0Start < mass < pi0Stop):
        # use pi0 -> gamma A'
        selectedMum = 111
        P8gen.SetParameters("111:oneChannel = 1 1 0 22 9900015")
        cf.write('P8gen.SetParameters("111:oneChannel = 1 1 0 22 9900015")\n')
    elif etaStart < mass < etaStop:
        # use eta -> gamma A'
        selectedMum = 221
        P8gen.SetParameters("221:oneChannel = 1 1 0 22 9900015")
        cf.write('P8gen.SetParameters("221:oneChannel = 1 1 0 22 9900015")\n')
    elif omegaStart < mass < omegaStop:
        # use omega -> pi0 A'
        selectedMum = 223
        P8gen.SetParameters("223:oneChannel = 1 1 0 111 9900015")
        cf.write('P8gen.SetParameters("223:oneChannel = 1 1 0 111 9900015")\n')
    elif eta1Start < mass < eta1Stop:
        # use eta' -> gamma A'
        selectedMum = 331
        P8gen.SetParameters("331:oneChannel = 1 1 0 22 9900015")
        #should be considered also for mass < 0.188 GeV....
        #P8gen.SetParameters("331:oneChannel = 1 1 0 223 9900015")29%BR
        #P8gen.SetParameters("331:oneChannel = 1 1 0 113 9900015")2.75%BR
        cf.write('P8gen.SetParameters("331:oneChannel = 1 1 0 22 9900015")\n')
    else:
        print "ERROR: please enter a nicer mass."
        return -1
    return selectedMum



def configure(P8gen, mass, epsilon, inclusive, deepCopy=False):
    # configure pythia8 for Ship usage
    debug=True
    if debug: cf=open('pythia8_darkphotonconf.txt','w')
    #h=readFromAscii()
    P8gen.UseRandom3() # TRandom1 or TRandom3 ?
    P8gen.SetMom(400)  # beam momentum in GeV 
    if deepCopy: P8gen.UseDeepCopy()
    pdg = ROOT.TDatabasePDG.Instance()
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
    if debug: cf.write('P8gen.SetParameters("3222:mayDecay = off")\n')
    if inclusive=="meson":
        # Configuring production
        P8gen.SetParameters("SoftQCD:nonDiffractive = on")
	if debug: cf.write('P8gen.SetParameters("SoftQCD:nonDiffractive = on")\n')

        #Define dark photon
        ctau = darkphoton.cTau(mass,epsilon)
        print 'ctau p8dpconf file =%3.15f cm'%ctau
        P8gen.SetParameters("9900015:new = A A 2 0 0 "+str(mass)+" 0.0 0.0 0.0 "+str(ctau/u.mm)+"  0   1   0   1   0") 
        if debug: cf.write('P8gen.SetParameters("9900015:new = A A 2 0 0 '+str(mass)+' 0.0 0.0 0.0 '+str(ctau/u.mm)+'  0   1   0   1   0") \n')
        P8gen.SetParameters("9900015:isResonance = false")
        if debug: cf.write('P8gen.SetParameters("9900015:isResonance = false")\n')

	P8gen.SetParameters("Next:numberCount    =  0")
        if debug: cf.write('P8gen.SetParameters("Next:numberCount    =  0")\n')

        # Configuring decay modes...
        readDecayTable.addDarkPhotondecayChannels(P8gen,mass, epsilon, conffile=os.path.expandvars('$FAIRSHIP/python/darkphotonDecaySelection.conf'), verbose=True)
         # Finish HNL setup...
        P8gen.SetParameters("9900015:mayDecay = on")
	if debug: cf.write('P8gen.SetParameters("9900015:mayDecay = on")\n')
        P8gen.SetDPId(9900015)
	if debug: cf.write('P8gen.SetDPId(9900015)\n')
       # also add to PDG
        gamma = u.hbarc / float(ctau) #197.3269631e-16 / float(ctau) # hbar*c = 197 MeV*fm = 197e-16 GeV*cm
        print 'gamma=%e'%gamma
        addDPtoROOT(pid=9900015,m=mass,g=gamma)

        #change meson decay to dark photon depending on mass
	selectedMum = manipulatePhysics(mass, P8gen, cf)
        print 'selected mum is : %d'%selectedMum


    if debug: cf.close()
