"""
# ==================================================================
#   Python module
#
#   This module provides methods to compute the lifetime and
#   branching ratio of HNLs given its mass and couplings as
#   input parameters.
#
#   Created: 30/11/2014 Elena Graverini (elena.graverini@cern.ch)
#
#   Sample usage:
#     ipython -i hnl.py
#     In [1]: b = HNL(1.,[1.e-8, 2.e-8, 1.e-9],True)
#     HNLbranchings instance initialized with couplings:
#          U2e   = 1e-08
#	   U2mu  = 2e-08
#	   U2tau = 1e-09
#     and mass:
#	   m = 1.0 GeV
#     In [2]: b.computeNLifetime()
#     Out[2]: 4.777721453160521e-05
#     In [3]: b.findBranchingRatio('N -> pi mu')
#     Out[3]: 0.11826749348890987
#
# ==================================================================
"""

import math
import ROOT
import shipunit as u

# Load PDG database
pdg = ROOT.TDatabasePDG.Instance()

def PDGname(particle):
    """
    Trim particle name for use with the PDG database
    """
    if 'down' in particle: return 'd'
    if 'up' in particle: return 'u'
    if 'strange' in particle: return 's'
    if 'charm' in particle: return 'c'
    if 'bottom' in particle: return 'b'
    if 'beauty' in particle: return 'b'
    if 'top' in particle: return 't'
    if '1' in particle:
        particle = particle.replace('1',"'")
    if (not (('-' in particle) or ('+' in particle) or ('0' in particle)
             or ('nu_' in particle) or ('eta' in particle))
        and (particle not in ['d','u','s','c','b','t'])):
        particle += '+'
    return particle

def mass(particle):
    """
    Read particle mass from PDG database
    """
    particle = PDGname(particle)
    tPart = pdg.GetParticle(particle)
    return tPart.Mass()

def lifetime(particle):
    """
    Read particle lifetime from PDG database
    """
    particle = PDGname(particle)
    tPart = pdg.GetParticle(particle)
    return tPart.Lifetime()

class CKMmatrix():
    """
    CKM matrix, from http://pdg.lbl.gov/2013/reviews/rpp2013-rev-ckm-matrix.pdf
    """
    def __init__(self):
        self.Vud = 0.9742
        self.Vus = 0.2252
        self.Vub = 4.2e-03
        self.Vcd = 0.23
        self.Vcs = 1.
        self.Vcb = 4.1e-02
        self.Vtd = 8.4e-03
        self.Vts = 4.3e-02
        self.Vtb = 0.89

class constants():
    """
    Store some constants useful for HNL physics
    """
    def __init__(self):
        self.decayConstant = {'pi':0.1307*u.GeV,
                            'pi0':0.130*u.GeV,
                            'rho':0.102*u.GeV, 'rho0':0.102*u.GeV,
                            'eta':1.2*0.130*u.GeV,
                            'eta1':-0.45*0.130*u.GeV} #GeV^2 ? check units!!
        self.GF = 1.166379e-05/(u.GeV*u.GeV) # Fermi's constant (GeV^-2)
        self.s2thetaw = 0.23126 # square sine of the Weinberg angle
        self.heV = 6.58211928*pow(10.,-16) # no units or it messes up!!
        self.hGeV = self.heV * pow(10.,-9) # no units or it messes up!!

# Load some useful constants
c = constants()

class HNLbranchings():
    """
    Lifetime and total and partial decay widths of an HNL
    """
    def __init__(self, mass, couplings, debug=False):
        """
        Initialize with mass and couplings of the HNL

        Inputs:
        mass (GeV)
        couplings (list of [U2e, U2mu, U2tau])
        """
        self.U2 = couplings
        self.U = [math.sqrt(ui) for ui in self.U2]
        self.MN = mass*u.GeV
        self.CKM = CKMmatrix()
        self.CKMelemSq = {'pi':self.CKM.Vud**2.,
                        'rho':self.CKM.Vud**2.,
                        'K':self.CKM.Vus**2.,
                        # Quarks:
                        # 0=u, 1=d, 2=s, 3=c, 4=b, 5=t
                        (0,0):1., (1,1):1., (2,2):1., (3,3):1., (4,4):1., (5,5):1., #flavour with same flavour
                        (0,3):0., (3,0):0., (0,5):0., (5,0):0., (3,5):0., (5,3):0., #up-type with up-type
                        (1,2):0., (2,1):0., (1,4):0., (4,1):0., (2,4):0., (4,2):0., #down-type with down-type
                        (0,1):self.CKM.Vud**2., (1,0):self.CKM.Vud**2.,
                        (0,2):self.CKM.Vus**2., (2,0):self.CKM.Vus**2.,
                        (0,4):self.CKM.Vub**2., (4,0):self.CKM.Vub**2.,
                        (3,1):self.CKM.Vcd**2., (1,3):self.CKM.Vcd**2.,
                        (3,2):self.CKM.Vcs**2., (2,3):self.CKM.Vcs**2.,
                        (3,4):self.CKM.Vcb**2., (4,3):self.CKM.Vcb**2.,
                        (5,1):self.CKM.Vtd**2., (1,5):self.CKM.Vtd**2.,
                        (5,2):self.CKM.Vts**2., (2,5):self.CKM.Vts**2.,
                        (5,4):self.CKM.Vtb**2., (4,5):self.CKM.Vtb**2.}
        self.decays = [ 'N -> nu nu nu',
                        'N -> e- e+ nu_e', 'N -> e- e+ nu_mu', 'N -> e- e+ nu_tau',
                        'N -> e+ mu- nu_e', 'N -> e- mu+ nu_mu',
                        'N -> mu- mu+ nu_e', 'N -> mu- mu+ nu_mu', 'N -> mu- mu+ nu_tau',
                        'N -> tau- tau+ nu_e', 'N -> tau- tau+ nu_mu', 'N -> tau- tau+ nu_tau', 
                        'N -> e+ tau- nu_e', 'N -> e- tau+ nu_tau', 
                        'N -> mu+ tau- nu_mu', 'N -> mu- tau+ nu_tau', 
                        'N -> pi0 nu_e', 'N -> pi0 nu_mu', 'N -> pi0 nu_tau', 
                        'N -> pi+ e-',
                        'N -> pi+ mu-',
                        'N -> rho0 nu_e', 'N -> rho0 nu_mu', 'N -> rho0 nu_tau', 
                        'N -> rho+ e-',
                        'N -> rho+ mu-' ]
        if debug:
            print "HNLbranchings instance initialized with couplings:"
            print "\tU2e   = %s"%self.U2[0]
            print "\tU2mu  = %s"%self.U2[1]
            print "\tU2tau = %s"%self.U2[2]
            print "and mass:"
            print "\tm = %s GeV"%(self.MN)

    def Width_H0_nu(self, H, alpha):
        """
        Returns the HNL decay width into neutral meson and neutrino

        Inputs:
        - H is a string (name of the meson)
        - alpha is the lepton flavour of the nu (1, 2 or 3)
        """
        if self.MN < (mass(H)):
            return 0.
        width = (math.fabs(self.U2[alpha-1])/(32.*u.pi))*(c.GF**2.)*(c.decayConstant[H]**2.)
        par = (self.MN**3.)*((1 - ((mass(H)**2.)/(self.MN**2.)))**2.)
        if 'rho' in H:
            par = par*2./(mass(H)**2.)
            par = par*(1 + 2.*((mass(H)**2.)/(self.MN**2.)))
        width = width*par
        width = 2.*width # Majorana case (charge conjugate channels)
        return width

    def Width_H_l(self, H, alpha):
        """
        Returns the HNL decay width into charged meson and lepton

        Inputs:
        - H is a string (name of the meson)
        - alpha is the lepton flavour (1, 2 or 3)
        """
        l = [None,'e','mu','tau']
        if self.MN < (mass(H) + mass(l[alpha])):
            return 0.
        width = (math.fabs(self.U2[alpha-1])/(16.*u.pi))*(c.GF**2.)*(c.decayConstant[H]**2.)
        width = width*(self.MN**3.)*self.CKMelemSq[H]
        par = ( ((1 - ((mass(l[alpha])**2.)/(self.MN**2.)))**2.) 
                - ( (mass(H)**2.)/(self.MN**2.)
                * (1 + ((mass(l[alpha])**2.)/(self.MN**2.))) ) )
        if 'rho' in H:
            par = ( ((1 - ((mass(l[alpha])**2.)/(self.MN**2.)))**2.) 
                    + ( (mass(H)**2.)/(self.MN**2.)
                    * (1 + (((mass(l[alpha])**2. - 2.*mass(H)**2.))/(self.MN**2.))) ) )
            par = par*2./(mass(H)**2.)
            
        width = width*par
        rad = math.sqrt( ( 1-((mass(H)-mass(l[alpha]))**2.)/(self.MN**2.) )
                * ( ( 1-((mass(H)+mass(l[alpha]))**2.)/(self.MN**2.) ) ) )
        width = width*rad
        width = 2.*width # Majorana case (charge conjugate channels)
        return width

    def Width_3nu(self):
        """
        Returns the HNL decay width into three neutrinos
        """
        width = (c.GF**2.)*(self.MN**5.)*sum(self.U2)/(192.*(u.pi**3.))
        width = 2.*width # Majorana case (charge conjugate channels)
        return width

    def Width_l1_l2_nu(self, alpha, beta, gamma): # alpha, beta for the two leptons, gamma for the neutrino
        """
        Returns the HNL decay width into two charged fermions and a neutrino or one lepton and a qqbar pair (through W)

        Inputs:
        - alpha is the flavour of the first lepton (1, 2 or 3) or quark (4, 5, 6, 7, 8, 9)
        - beta is the flavour of the second lepton (1, 2 or 3) or quark (4, 5, 6, 7, 8, 9)
        -   (choose from: e, mu, tau, up, down, strange, charm, beauty, top)
        - gamma is the flavour of the neutrino (or of the lepton in the N->lW case) (1, 2 or 3)
        """
        l = [None,'e','mu','tau','up','down','strange','charm','bottom','top']
        if self.MN < (mass(l[alpha]) + mass(l[beta])):
            return 0.
        if (alpha > 3) and (beta == alpha): # N -> nu qq or N -> nu ll (mainly Z0)
            width = (c.GF**2.)*(self.MN**5.)*self.U2[gamma-1]/(192.*(u.pi**3.))

        elif ((alpha in [4, 7, 9]) and (beta in [5, 6, 8])) or ((alpha in [5, 6, 8]) and (beta in [4, 7, 9])): # N -> l W, W -> u dbar, index gamma stands for massive lepton
            if gamma == 3: # tau too massive for this parametrisation
                return 0.
            if self.MN < (mass(l[alpha]) + mass(l[beta]) + mass(l[gamma])):
                return 0.
            width = (c.GF**2.)*(self.MN**5.)*self.U2[gamma-1]/(192.*(u.pi**3.))*self.CKMelemSq[(alpha-4, beta-4)]
        elif (alpha <= 3) and (beta <= 3):
            #width = (c.GF**2.)*(self.MN**5.)*self.U2[alpha-1]/(192.*(u.pi**3.))
            if (alpha != beta) and (gamma not in [alpha, beta]):
                return 0.
            width = (self.GF**2.)*(self.MN**5.)*self.U2[gamma-1]/(192.*(math.pi**3.))
        else:
            return 0.
        if alpha != beta:
            xl = max([mass(l[alpha]) , mass(l[beta])])/self.MN
            width = width*(1. - 8.*xl**2. + 8.*xl**6. - (12.*xl**4.)*math.log(xl**2.))
        else:
            xl = mass(l[alpha]) / self.MN
            lo = 0.
            logContent = (1. - 3.*xl**2. - (1.-xl**2.)*math.sqrt(1. - 4.*xl**2.) ) / ( (xl**2.)*(1 + math.sqrt(1. - 4.*xl**2.)) )
            if logContent > 0:
                lo = math.log( logContent )
            c1 = 0.25*(1. - 4.*c.s2thetaw + 8.*c.s2thetaw**2.)
            c2 = 0.5*c.s2thetaw*(2.*c.s2thetaw -1.)
            c3 = 0.25*(1. + 4.*c.s2thetaw + 8.*c.s2thetaw**2.)
            c4 = 0.5*c.s2thetaw*(2.*c.s2thetaw +1.)
            d = (alpha == gamma)
            width = width*( (c1*(1-d)+c3*d)*( (1.-14.*xl**2. -2.*xl**4. -12.*xl**6.)*math.sqrt(1-4.*xl**2) +12.*xl**4. *(-1.+xl**4.)*lo )
                            + 4.*(c2*(1-d)+c4*d)*( xl**2. *(2.+10.*xl**2. -12.*xl**4.) * math.sqrt(1.-4.*xl**2) + 6.*xl**4. *(1.-2.*xl**2+2.*xl**4)*lo ) )
        width = 2.*width # Majorana case (charge conjugate channels)
        return width

    def NDecayWidth(self):
        """
        Returns the total HNL decay width
        """
        if self.MN < 1.:
            totalWidth = ( self.Width_3nu()
                    + sum([self.Width_H_l('pi',l) + self.Width_H_l('rho',l) + self.Width_H0_nu('pi0',l) + self.Width_H0_nu('rho',l) + self.Width_H0_nu('eta',l) + self.Width_H0_nu('eta1',l) for l in [1,2,3]])
                    + sum([self.Width_l1_l2_nu(a,b,g) for a in [1,2,3] for b in [1,2,3] for g in [1,2,3]]) )
        elif self.MN > 2.:
            totalWidth = ( self.Width_3nu() + sum([self.Width_l1_l2_nu(a,b,g) for a in range(1,10) for b in range(1,10) for g in [1,2,3]]) )
        else:
            m1, m2 = 1., 2.
            tempMass = self.MN
            self.MN = m1
            w1 = ( self.Width_3nu()
                    + sum([self.Width_H_l('pi',l) + self.Width_H_l('rho',l) + self.Width_H0_nu('pi0',l) + self.Width_H0_nu('rho',l) + self.Width_H0_nu('eta',l) + self.Width_H0_nu('eta1',l) for l in [1,2,3]])
                    + sum([self.Width_l1_l2_nu(a,b,g) for a in [1,2,3] for b in [1,2,3] for g in [1,2,3]]) )
            self.MN = m2
            w2 = ( self.Width_3nu() + sum([self.Width_l1_l2_nu(a,b,g) for a in range(1,10) for b in range(1,10) for g in [1,2,3]]) )
            self.MN = tempMass
            totalWidth = w1 + (self.MN - m1)*(w2 - w1)/(m2 - m1)
        return totalWidth

    def findBranchingRatio(self, decayString):
        """
        Returns the branching ratio of the selected HNL decay channel

        Inputs:
        - decayString is a string describing the decay, in the form 'N -> stuff1 ... stuffN'
        """
        br = 0.
        totalWidth = self.NDecayWidth()
        if   decayString == 'N -> pi+ e-': br = self.Width_H_l('pi',1) / totalWidth
        elif decayString == 'N -> pi0 nu_e': br = self.Width_H0_nu('pi0',1) / totalWidth
        elif decayString == 'N -> pi0 nu_mu': br = self.Width_H0_nu('pi0',2) / totalWidth
        elif decayString == 'N -> pi0 nu_tau': br = self.Width_H0_nu('pi0',3) / totalWidth
        elif decayString == 'N -> pi+ mu-': br = self.Width_H_l('pi',2) / totalWidth
        elif decayString == 'N -> rho0 nu_e': br = self.Width_H0_nu('rho0',1) / totalWidth
        elif decayString == 'N -> rho0 nu_mu': br = self.Width_H0_nu('rho0',2) / totalWidth
        elif decayString == 'N -> rho0 nu_tau': br = self.Width_H0_nu('rho0',3) / totalWidth
        elif decayString == 'N -> rho+ e-': br = self.Width_H_l('rho',1) / totalWidth
        elif decayString == 'N -> rho+ mu-': br = self.Width_H_l('rho',2) / totalWidth
        elif decayString == 'N -> e- e+ nu_e': br = self.Width_l1_l2_nu(1,1,1) / totalWidth
        elif decayString == 'N -> e- e+ nu_mu': br = self.Width_l1_l2_nu(1,1,2) / totalWidth
        elif decayString == 'N -> e- e+ nu_tau': br = self.Width_l1_l2_nu(1,1,3) / totalWidth
        elif decayString == 'N -> mu- mu+ nu_e': br = self.Width_l1_l2_nu(2,2,1) / totalWidth
        elif decayString == 'N -> mu- mu+ nu_mu': br = self.Width_l1_l2_nu(2,2,2) / totalWidth
        elif decayString == 'N -> mu- mu+ nu_tau': br = self.Width_l1_l2_nu(2,2,3) / totalWidth
        elif decayString == 'N -> tau- tau+ nu_e': br = self.Width_l1_l2_nu(3,3,1) / totalWidth
        elif decayString == 'N -> tau- tau+ nu_mu': br = self.Width_l1_l2_nu(3,3,2) / totalWidth
        elif decayString == 'N -> tau- tau+ nu_tau': br = self.Width_l1_l2_nu(3,3,3) / totalWidth
        elif decayString == 'N -> e+ mu- nu_e': br = self.Width_l1_l2_nu(2,1,1) / totalWidth
        elif decayString == 'N -> e- mu+ nu_mu': br = self.Width_l1_l2_nu(1,2,2) / totalWidth
        elif decayString == 'N -> e+ tau- nu_e': br = self.Width_l1_l2_nu(3,1,1) / totalWidth
        elif decayString == 'N -> e- tau+ nu_tau': br = self.Width_l1_l2_nu(1,3,3) / totalWidth
        elif decayString == 'N -> mu+ tau- nu_mu': br = self.Width_l1_l2_nu(3,2,2) / totalWidth
        elif decayString == 'N -> mu- tau+ nu_tau': br = self.Width_l1_l2_nu(2,3,3) / totalWidth
        elif decayString == 'N -> pi+ tau-': br = self.Width_H_l('pi',3) / totalWidth
        elif decayString == 'N -> rho+ tau-': br = self.Width_H_l('rho',3) / totalWidth
        elif decayString == 'N -> nu nu nu' or decayString == 'N -> 3nu':
            br = self.Width_3nu() / totalWidth # inclusive
        elif decayString == 'N -> hadrons':
            if self.MN < 1.:
                br = sum([self.Width_H_l('pi',l) + self.Width_H_l('rho',l) + self.Width_H0_nu('pi0',l) + self.Width_H0_nu('rho',l) + self.Width_H0_nu('eta',l) + self.Width_H0_nu('eta1',l) for l in [1,2,3]])/totalWidth
            elif self.MN > 2.:
                br = sum([self.Width_l1_l2_nu(a,b,g) for a in range(4,10) for b in range(4,10) for g in [1,2,3]])/totalWidth
            else:
                m1, m2 = 1., 2.
                tempMass = self.MN
                self.MN = m1
                br1 = sum([self.Width_H_l('pi',l) + self.Width_H_l('rho',l) + self.Width_H0_nu('pi0',l) + self.Width_H0_nu('rho',l) + self.Width_H0_nu('eta',l) + self.Width_H0_nu('eta1',l) for l in [1,2,3]])/totalWidth
                self.MN = m2
                br2 = sum([self.Width_l1_l2_nu(a,b,g) for a in range(4,10) for b in range(4,10) for g in [1,2,3]])/totalWidth
                self.MN = tempMass
                br = br1 + (self.MN - m1)*(br2 - br1)/(m2 - m1)
        elif decayString == 'N -> charged hadrons':
            if self.MN < 1.:
                br = sum([self.Width_H_l('pi',l) + self.Width_H_l('rho',l) for l in [1,2,3]])/totalWidth
            elif self.MN > 2.:
                br = sum([self.Width_l1_l2_nu(a,b,g) for a in range(4,10) for b in range(4,10) for g in [1,2,3]])/totalWidth
            else:
                m1, m2 = 1., 2.
                tempMass = self.MN
                self.MN = m1
                br1 = sum([self.Width_H_l('pi',l) + self.Width_H_l('rho',l) for l in [1,2,3]])/totalWidth
                self.MN = m2
                br2 = sum([self.Width_l1_l2_nu(a,b,g) for a in range(4,10) for b in range(4,10) for g in [1,2,3]])/totalWidth
                self.MN = tempMass
                br = br1 + (self.MN - m1)*(br2 - br1)/(m2 - m1)
        else:
            print 'findBranchingRatio ERROR: unknown decay %s'%decayString
            quit()
        return br

    def allowedChannels(self):
        """
        Returns a dictionary of kinematically allowed decay channels

        Inputs:
        - decayString is a string describing the decay, in the form 'N -> stuff1 ... stuffN'
        """
        m = self.MN
        allowedDecays = {'N -> nu nu nu':'yes'}
        if m > 2.*mass('e'):
            allowedDecays.update({'N -> e- e+ nu_e':'yes'})
            allowedDecays.update({'N -> e- e+ nu_mu':'yes'})
            allowedDecays.update({'N -> e- e+ nu_tau':'yes'})
            if m > mass('e') + mass('mu'):
                allowedDecays.update({'N -> e+ mu- nu_e':'yes'})
                allowedDecays.update({'N -> e- mu+ nu_mu':'yes'})
            if m > mass('pi0'):
                allowedDecays.update({'N -> pi0 nu_e':'yes'})
                allowedDecays.update({'N -> pi0 nu_mu':'yes'})
                allowedDecays.update({'N -> pi0 nu_tau':'yes'})
            if m > mass('pi') + mass('e'):
                allowedDecays.update({'N -> pi+ e-':'yes'})
                if m > 2.*mass('mu'):
                    allowedDecays.update({'N -> mu- mu+ nu_e':'yes'})
                    allowedDecays.update({'N -> mu- mu+ nu_mu':'yes'})
                    allowedDecays.update({'N -> mu- mu+ nu_tau':'yes'})
                    if m > mass('pi') + mass('mu'):
                        allowedDecays.update({'N -> pi+ mu-':'yes'})
                        if m > mass('rho0'):
                            allowedDecays.update({'N -> rho0 nu_e':'yes'})
                            allowedDecays.update({'N -> rho0 nu_mu':'yes'})
                            allowedDecays.update({'N -> rho0 nu_tau':'yes'})
                        if m > mass('rho') + mass('e'):
                            allowedDecays.update({'N -> rho+ e-':'yes'})
                            if m > mass('rho') + mass('mu'):
                                allowedDecays.update({'N -> rho+ mu-':'yes'})
                                if m > mass('e') + mass('tau'):
                                    allowedDecays.update({'N -> e+ tau- nu_e':'yes'})
                                    allowedDecays.update({'N -> e- tau+ nu_tau':'yes'})
                                    if m > mass('mu') + mass('tau'):
                                        allowedDecays.update({'N -> mu+ tau- nu_mu':'yes'})
                                        allowedDecays.update({'N -> mu- tau+ nu_tau':'yes'})
                                        if m > 2.*mass('tau'):
                                            allowedDecays.update({'N -> tau- tau+ nu_e':'yes'})
                                            allowedDecays.update({'N -> tau- tau+ nu_mu':'yes'})
                                            allowedDecays.update({'N -> tau- tau+ nu_tau':'yes'})
        for decay in self.decays:
            if decay not in allowedDecays:
                allowedDecays.update({decay:'no'})
        return allowedDecays




class HNL(HNLbranchings):
    """
    HNL physics according to the nuMSM
    """
    def __init__(self, mass, couplings, debug=False):
        """
        Initialize with mass and couplings of the HNL

        Inputs:
        mass (GeV)
        couplings (list of [U2e, U2mu, U2tau])
        """
        HNLbranchings.__init__(self, mass, couplings, debug)
    def computeNLifetime(self,system="SI"):
        """
        Compute the HNL lifetime

        Inputs:
        - system: choose between default (i.e. SI, result in s) or FairShip (result in ns)
        """
        self.NLifetime = c.hGeV / self.NDecayWidth()
	if system == "FairShip": self.NLifetime *= 1.e9
        return self.NLifetime

