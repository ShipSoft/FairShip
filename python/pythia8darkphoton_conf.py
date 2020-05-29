from __future__ import division
from __future__ import print_function
import ROOT, os, sys
import shipunit as u
import readDecayTable
import darkphoton
import proton_bremsstrahlung
from method_logger import MethodLogger

# Boundaries for production in meson decays
# mass of the mesons
pi0mass    = 0.1349770
etamass    = 0.547862
omegamass  = 0.78265
eta1mass   = 0.95778


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

def manipulatePhysics(motherMode, mass, P8gen):
    #changes of the table, now it is deleted and we have each meson mother for each meson production
    #print motherMode
    if motherMode=='pi0' and pi0mass-mass>=0.0000001:
        # use pi0 -> gamma A'
        selectedMum = 111
        P8gen.SetParameters("111:oneChannel = 1 1 0 22 9900015")
        
    elif motherMode == 'eta' and etamass-mass>=0.000001:
        # use eta -> gamma A'
        #print "eta"
        selectedMum = 221
        P8gen.SetParameters("221:oneChannel = 1 1 0 22 9900015")
        
    elif motherMode=="omega" and omegamass-mass>=0.00001:
        # use omega -> pi0 A'
        #print "omega"
        selectedMum = 223
        P8gen.SetParameters("223:oneChannel = 1 1 0 111 9900015")
        
    elif motherMode=='eta1' and eta1mass-mass>=0.00001:
        # use eta' -> gamma A'
        selectedMum = 331
        P8gen.SetParameters("331:oneChannel = 1 1 0 22 9900015")
        #should be considered also for mass < 0.188 GeV....
        #P8gen.SetParameters("331:oneChannel = 1 1 0 223 9900015")29%BR
        #P8gen.SetParameters("331:oneChannel = 1 1 0 113 9900015")2.75%BR
        
    elif motherMode=='eta11' and eta1mass-mass>=0.00001:
        # use eta' -> gamma A'
        selectedMum = 331
        P8gen.SetParameters("331:oneChannel = 1 1 0 113 9900015")
        #should be considered also for mass < 0.188 GeV....
        #P8gen.SetParameters("331:oneChannel = 1 1 0 223 9900015")29%BR
        #P8gen.SetParameters("331:oneChannel = 1 1 0 113 9900015")2.75%BR
        
    else:
        #print "ERROR: please enter a nicer mass, for meson production it needs to be between %3.3f and %3.3f."%(pi0Start,eta1Stop)
        return -1
    return selectedMum

def configure(P8gen, mass, epsilon, inclusive, motherMode, deepCopy=False, debug=True):
    # configure pythia8 for Ship usage
    if debug:
        pythia_log=open('pythia8_conf.txt','w')
        P8gen = MethodLogger(P8gen, sink=pythia_log)
    P8gen.UseRandom3() # TRandom1 or TRandom3 ?
    P8gen.SetMom(400)  # beam momentum in GeV 
    if deepCopy: P8gen.UseDeepCopy()
    pdg = ROOT.TDatabasePDG.Instance()
    if inclusive=="meson":
    # let strange particle decay in Geant4
        p8 = P8gen.getPythiaInstance()
        n=1
        while n!=0:
          n = p8.particleData.nextId(n)
          p = p8.particleData.particleDataEntryPtr(n)
          if p.tau0()>1: 
           command = str(n)+":mayDecay = false"
           p8.readString(command)
           print("Pythia8 configuration: Made %s stable for Pythia, should decay in Geant4"%(p.name()))
    
        # Configuring production
        P8gen.SetParameters("SoftQCD:nonDiffractive = on")

    elif inclusive=="qcd":
        P8gen.SetDY()
        P8gen.SetMinDPMass(0.7)

        if (mass<P8gen.MinDPMass()): 
            print("WARNING! Mass is too small, minimum is set to %3.3f GeV."%P8gen.MinDPMass())
            return 0

    # produce a Z' from hidden valleys model
        p8 = P8gen.getPythiaInstance()
        n=1
        while n!=0:
          n = p8.particleData.nextId(n)
          p = p8.particleData.particleDataEntryPtr(n)
          if p.tau0()>1: 
           command = str(n)+":mayDecay = false"
           p8.readString(command)
           print("Pythia8 configuration: Made %s stable for Pythia, should decay in Geant4"%(p.name()))
    
        # Configuring production
        P8gen.SetParameters("HiddenValley:ffbar2Zv = on")
        P8gen.SetParameters("HiddenValley:Ngauge = 1")

    elif inclusive=="pbrem":
        P8gen.SetParameters("ProcessLevel:all = off")
        #Also allow resonance decays, with showers in them
        #P8gen.SetParameters("Standalone:allowResDec = on")

        #Optionally switch off decays.
        #P8gen.SetParameters("HadronLevel:Decay = off")

        #Switch off automatic event listing in favour of manual.
        P8gen.SetParameters("Next:numberShowInfo = 0")
        P8gen.SetParameters("Next:numberShowProcess = 0")
        P8gen.SetParameters("Next:numberShowEvent = 0")
        proton_bremsstrahlung.protonEnergy=P8gen.GetMom()
        norm=proton_bremsstrahlung.prodRate(mass, epsilon)
        print("A' production rate per p.o.t: \t %.8g"%norm)
        P8gen.SetPbrem(proton_bremsstrahlung.hProdPDF(mass, epsilon, norm, 350, 1500))

    #Define dark photon
    DP_instance = darkphoton.DarkPhoton(mass,epsilon)
    ctau = DP_instance.cTau()
    print('ctau p8dpconf file =%3.6f cm'%ctau)
    print('Initial particle parameters for PDGID %d :'%P8gen.GetDPId())
    P8gen.List(P8gen.GetDPId())
    if inclusive=="qcd":
        dpid = P8gen.GetDPId()
        P8gen.SetParameters("{}:m0 = {:.12}".format(dpid, mass))
        #P8gen.SetParameters(str(P8gen.GetDPId())+":mWidth = "+str(u.mm/ctau))
        P8gen.SetParameters("{}:mWidth = {:.12}".format(dpid, u.hbarc/ctau))
        P8gen.SetParameters("{}:mMin = 0.001".format(dpid))
        P8gen.SetParameters("{}:tau0 = {:.12}".format(dpid, ctau/u.mm))
        #P8gen.SetParameters("ParticleData:modeBreitWigner = 0")   
        #P8gen.SetParameters(str(P8gen.GetDPId())+":isResonance = false")
        #P8gen.SetParameters(str(P8gen.GetDPId())+":all = A A 3 0 0 "+str(mass)+" 0.0 0.0 0.0 "+str(ctau/u.mm)+"  0   1   0   1   0") 
        P8gen.SetParameters("{}:onMode = off".format(dpid))
    else:
        P8gen.SetParameters("{}:new = A A 3 0 0 {:.12} 0.0 0.0 0.0 {:.12}  0   1   0   1   0"\
                            .format(P8gen.GetDPId(), mass, ctau/u.mm))
        #if (inclusive=="pbrem"): 
        ### Do not set as resonance: decays to hadron doesn't work properly below 0.7 GeV.
        #   P8gen.SetParameters(str(P8gen.GetDPId())+":isResonance = true")
        #   P8gen.SetParameters(str(P8gen.GetDPId())+":mWidth = "+str(u.hbarc/ctau))
        #   P8gen.SetParameters(str(P8gen.GetDPId())+":mMin = 0.001")
    
    P8gen.SetParameters("Next:numberCount    =  0")

    # Configuring decay modes...
    readDecayTable.addDarkPhotondecayChannels(P8gen, mass, DP_instance, conffile=os.path.expandvars('$FAIRSHIP/python/darkphotonDecaySelection.conf'), verbose=True)
    # Finish DP setup...
    P8gen.SetParameters("{}:mayDecay = on".format(P8gen.GetDPId()))
    #P8gen.SetDPId(P8gen.GetDPId())
    # also add to PDG
    gamma = u.hbarc / float(ctau) #197.3269631e-16 / float(ctau) # hbar*c = 197 MeV*fm = 197e-16 GeV*cm
    print('gamma=%e'%gamma)
    addDPtoROOT(pid=P8gen.GetDPId(),m=mass,g=gamma)
    
    if inclusive=="meson":
        #change meson decay to dark photon depending on mass
        selectedMum = manipulatePhysics(motherMode, mass, P8gen)
        print('selected mum is : %d'%selectedMum)
        if (selectedMum == -1): return 0

    #P8gen.SetParameters("Check:particleData = on")

    if debug: pythia_log.close()

    return 1
