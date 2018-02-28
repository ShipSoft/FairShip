import ROOT, os, sys
import shipunit as u
import readDecayTable
import darkphoton
import proton_bremsstrahlung

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

def manipulatePhysics(mass, P8Gen, cf):
    if (pi0Start < mass < pi0Stop):
        # use pi0 -> gamma A'
        selectedMum = 111
        P8Gen.SetParameters("111:oneChannel = 1 1 0 22 9900015")
        cf.write('P8Gen.SetParameters("111:oneChannel = 1 1 0 22 9900015")\n')
    elif etaStart < mass < etaStop:
        # use eta -> gamma A'
        selectedMum = 221
        P8Gen.SetParameters("221:oneChannel = 1 1 0 22 9900015")
        cf.write('P8Gen.SetParameters("221:oneChannel = 1 1 0 22 9900015")\n')
    elif omegaStart < mass < omegaStop:
        # use omega -> pi0 A'
        selectedMum = 223
        P8Gen.SetParameters("223:oneChannel = 1 1 0 111 9900015")
        cf.write('P8Gen.SetParameters("223:oneChannel = 1 1 0 111 9900015")\n')
    elif eta1Start < mass < eta1Stop:
        # use eta' -> gamma A'
        selectedMum = 331
        P8Gen.SetParameters("331:oneChannel = 1 1 0 22 9900015")
        #should be considered also for mass < 0.188 GeV....
        #P8Gen.SetParameters("331:oneChannel = 1 1 0 223 9900015")29%BR
        #P8Gen.SetParameters("331:oneChannel = 1 1 0 113 9900015")2.75%BR
        cf.write('P8Gen.SetParameters("331:oneChannel = 1 1 0 22 9900015")\n')
    else:
        print "ERROR: please enter a nicer mass."
        return -1
    return selectedMum



def configure(P8Gen, mass, epsilon, inclusive, deepCopy=False):
    # configure pythia8 for Ship usage
    debug=True
    if debug: cf=open('pythia8_darkphotonconf.txt','w')
    #h=readFromAscii()
    P8Gen.UseRandom3() # TRandom1 or TRandom3 ?
    P8Gen.SetMom(400)  # beam momentum in GeV 
    if deepCopy: P8Gen.UseDeepCopy()
    pdg = ROOT.TDatabasePDG.Instance()
    if inclusive=="meson":
    # let strange particle decay in Geant4
        p8 = P8Gen.getPythiaInstance()
        n=1
        while n!=0:
          n = p8.particleData.nextId(n)
          p = p8.particleData.particleDataEntryPtr(n)
          if p.tau0()>1: 
           command = str(n)+":mayDecay = false"
           p8.readString(command)
           print "Pythia8 configuration: Made %s stable for Pythia, should decay in Geant4"%(p.name())
    
        # Configuring production
        P8Gen.SetParameters("SoftQCD:nonDiffractive = on")
        if debug: cf.write('P8Gen.SetParameters("SoftQCD:nonDiffractive = on")\n')

    elif inclusive=="qcd":
        P8Gen.SetDY()
    # produce a Z' from hidden valleys model
        p8 = P8Gen.getPythiaInstance()
        n=1
        while n!=0:
          n = p8.particleData.nextId(n)
          p = p8.particleData.particleDataEntryPtr(n)
          if p.tau0()>1: 
           command = str(n)+":mayDecay = false"
           p8.readString(command)
           print "Pythia8 configuration: Made %s stable for Pythia, should decay in Geant4"%(p.name())
    
        # Configuring production
        P8Gen.SetParameters("HiddenValley:ffbar2Zv = on")
        if debug: cf.write('P8Gen.SetParameters("HiddenValley:ffbar2Zv = on")\n')

    elif inclusive=="pbrem":
        P8Gen.SetParameters("ProcessLevel:all = off")
        if debug: cf.write('P8Gen.SetParameters("ProcessLevel:all = off")\n')
        #Also allow resonance decays, with showers in them
        #P8Gen.SetParameters("Standalone:allowResDec = on")

        #Optionally switch off decays.
        #P8Gen.SetParameters("HadronLevel:Decay = off")

        #Switch off automatic event listing in favour of manual.
        P8Gen.SetParameters("Next:numberShowInfo = 0")
        P8Gen.SetParameters("Next:numberShowProcess = 0")
        P8Gen.SetParameters("Next:numberShowEvent = 0")
        proton_bremsstrahlung.protonEnergy=P8Gen.GetMom()
        norm=proton_bremsstrahlung.prodRate(mass, epsilon)
        print "A' production rate per p.o.t: \t %.8g"%norm
        P8Gen.SetPbrem(proton_bremsstrahlung.hProdPDF(mass, epsilon, norm, 350, 1500))

    #Define dark photon
    DP_instance = darkphoton.DarkPhoton(mass,epsilon)
    ctau = DP_instance.cTau()
    print 'ctau p8dpconf file =%3.15f cm'%ctau
    P8Gen.List(P8Gen.GetDPId())
    if inclusive=="qcd":
        P8Gen.SetParameters(str(P8Gen.GetDPId())+":new = A A 3 0 0 "+str(mass)+" 0.002 0.0 0.0 "+str(ctau/u.mm)+"  1   1   0   1   0") 
        if debug: cf.write('P8Gen.SetParameters('+str(P8Gen.GetDPId())+'":new = A A 3 0 0 '+str(mass)+' 0.002 0.0 0.0 '+str(ctau/u.mm)+'  1   1   0   1   0") \n')
    else:
        P8Gen.SetParameters(str(P8Gen.GetDPId())+":new = A A 3 0 0 "+str(mass)+" 0.0 0.0 0.0 "+str(ctau/u.mm)+"  0   1   0   1   0") 
        if debug: cf.write('P8Gen.SetParameters('+str(P8Gen.GetDPId())+'":new = A A 3 0 0 '+str(mass)+' 0.0 0.0 0.0 '+str(ctau/u.mm)+'  0   1   0   1   0") \n')

    if inclusive=="qcd":
        P8Gen.SetParameters(str(P8Gen.GetDPId())+":onMode = off")
    
    P8Gen.SetParameters("Next:numberCount    =  0")
    if debug: cf.write('P8Gen.SetParameters("Next:numberCount    =  0")\n')

    # Configuring decay modes...
    readDecayTable.addDarkPhotondecayChannels(P8Gen,DP_instance, conffile=os.path.expandvars('$FAIRSHIP/python/darkphotonDecaySelection.conf'), verbose=True)
    # Finish HNL setup...
    P8Gen.SetParameters(str(P8Gen.GetDPId())+":mayDecay = on")
    if debug: cf.write('P8Gen.SetParameters('+str(P8Gen.GetDPId())+'":mayDecay = on")\n')
    #P8Gen.SetDPId(P8Gen.GetDPId())
    #if debug: cf.write('P8Gen.SetDPId(%d)\n',%P8Gen.GetDPId())
       # also add to PDG
    gamma = u.hbarc / float(ctau) #197.3269631e-16 / float(ctau) # hbar*c = 197 MeV*fm = 197e-16 GeV*cm
    print 'gamma=%e'%gamma
    addDPtoROOT(pid=P8Gen.GetDPId(),m=mass,g=gamma)
    
    if inclusive=="meson":
        #change meson decay to dark photon depending on mass
	selectedMum = manipulatePhysics(mass, P8Gen, cf)
        print 'selected mum is : %d'%selectedMum


    if debug: cf.close()
