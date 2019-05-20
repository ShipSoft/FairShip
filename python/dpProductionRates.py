import ROOT,os,sys,getopt,math
import shipunit as u
import proton_bremsstrahlung


PDG = ROOT.TDatabasePDG.Instance()
protonFlux = 2e20


def isDP(pdg):
    if (pdg==9900015 or pdg==4900023): 
        return True
    return False

def pbremProdRate(mass,epsilon,doprint=False):
    xswg = proton_bremsstrahlung.prodRate(mass, epsilon)
    if doprint: print "A' production rate per p.o.t: \t %.8g"%(xswg)
    penalty = proton_bremsstrahlung.penaltyFactor(mass)
    if doprint: print "A' penalty factor: \t %.8g"%penalty
    if doprint: print "A' rescaled production rate per p.o.t:\t %.8g"%(xswg*penalty)
    return xswg*penalty

#obtained with Pythia8: average number of meson expected per p.o.t from inclusive pp to X production, 100k events produced
def getAverageMesonRate(mumPdg):
    if (mumPdg==111): return 6.166
    if (mumPdg==221): return 0.7012
    if (mumPdg==223): return 0.8295
    if (mumPdg==331): return 0.07825
    print " -- ERROR, unknown mother pdgId %d"%mumPdg
    return 0

#from the PDG, decay to photon channels available for mixing with DP
def mesonBRtoPhoton(mumPdg,doprint=False):
    br = 1
    if (mumPdg==111): br = 0.9879900
    if (mumPdg==221): br = 0.3931181
    if (mumPdg==223): br = 0.0834941
    if (mumPdg==331): br = 0.0219297
    if (doprint==True): print "BR of %d meson to photons: %.8g"%(mumPdg,br)
    return br 

def brMesonToGammaDP(mass,epsilon,mumPdg,doprint=False):
    mMeson = PDG.GetParticle(mumPdg).Mass()
    if (doprint==True): print "Mass of mother %d meson is %3.3f"%(mumPdg,mMeson)
    if (mass<mMeson): br = 2*epsilon**2*pow((1-mass**2/mMeson**2),3)*mesonBRtoPhoton(mumPdg,doprint)
    else: br = 0
    if (doprint==True): print "Branching ratio of %d meson to DP is %.8g"%(mumPdg,br)
    return br

def brMesonToMesonDP(mass,epsilon,mumPdg,dauPdg,doprint=False):
    mMeson = PDG.GetParticle(mumPdg).Mass()
    mDaughterMeson = PDG.GetParticle(dauPdg).Mass()
    if (doprint==True): print "Mass of mother %d meson is %3.3f"%(mumPdg,mMeson)
    if (doprint==True): print "Mass of daughter %d meson is %3.3f"%(dauPdg,mDaughterMeson)
    fac1 = (mMeson**2-mass**2-mDaughterMeson**2)**2
    fac2 = ROOT.TMath.Sqrt((mMeson**2-mass**2+mDaughterMeson**2)**2 - 4*mMeson**2*mDaughterMeson**2)
    fac3 = pow(mMeson**2-mass**2,3)
    massfactor = fac1*fac2/fac3
    if (mass<(mMeson-mDaughterMeson)): br = epsilon**2*mesonBRtoPhoton(mumPdg,doprint)*massfactor
    else: br = 0
    if (doprint==True): print "Branching ratio of %d meson to DP is %.8g"%(mumPdg,br)
    return br

def brMesonToDP(mass,epsilon,mumPdg,doprint=False):
    if mumPdg==223: return brMesonToMesonDP(mass,epsilon,mumPdg,111,doprint)
    elif (mumPdg==111 or mumPdg==221 or mumPdg==331): return brMesonToGammaDP(mass,epsilon,mumPdg,doprint)
    else: 
        print "Warning! Unknown mother pdgId %d, not implemented. Setting br to 0."%mumPdg
        return 1

def mesonProdRate(mass,epsilon,mumPdg,doprint=False):
    #print "avgrate %.8g, brmeson %.8g"%(getAverageMesonRate(mumPdg),brMesonToDP(mass,epsilon,mumPdg,doprint))
    avgMeson = getAverageMesonRate(mumPdg)*brMesonToDP(mass,epsilon,mumPdg,doprint)
    if doprint==True: print "Average %d meson production rate per p.o.t: %.8g"%(mumPdg,avgMeson)
    return avgMeson

#from interpolation of Pythia XS, normalised to epsilon^2
def qcdprodRate(mass,epsilon,doprint=False):
    xs = 0
    if (mass > 3):
        xs = math.exp(-5.673-0.8869*mass)
    elif (mass > 1.4):
        xs = math.exp(-3.802-1.532*mass)
    else:
        xs = 0.0586-0.09037*mass + 0.0360743*mass*mass
    return xs*epsilon*epsilon

def getDPprodRate(mass,epsilon,prodMode,mumPdg,doprint=False):
    if ('pbrem' in prodMode):
        return pbremProdRate(mass,epsilon,doprint)
    elif ('meson' in prodMode):
        return mesonProdRate(mass,epsilon,mumPdg,doprint)
    elif ('qcd' in prodMode):
        return qcdprodRate(mass,epsilon,doprint)
    else:
        print "Unknown production mode! Choose among pbrem, meson or qcd."
        return 1

