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
    if not (('-' in particle) or ('+' in particle)):
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
                            'rho':0.102*u.GeV,
                            'eta':1.2*0.130*u.GeV,
                            'eta\'':-0.45*0.130*u.GeV} #GeV^2 ? check units!!

# Load some useful constants
c = constants()

class HNLbranchings():
    """
    Lifetime and total and partial decay widths of an HNL
    """
    def __init__(self, mass, couplings):
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
### Next code needs to be reviewed and properly integrated into FairShip classes

    def Width_H0_nu(self, H, alpha):
        """
        Returns the HNL decay width into neutral meson and neutrino

        Inputs:
        - H is a string (name of the meson)
        - alpha is the lepton flavour of the nu (1, 2 or 3)
        """
        if self.MN < (mass(H)):
            return 0.
        width = (math.fabs(self.U2[alpha-1])/(32.*u.pi))*(self.GF**2.)*(c.decayConstant[H]**2.)
        par = (self.MN**3.)*((1 - ((self.masses[H]**2.)/(self.MN**2.)))**2.)
        if H == 'rho':
            par = par*2./(self.masses[H]**2.)
            par = par*(1 + 2.*((self.masses[H]**2.)/(self.MN**2.)))
        width = width*par
        width = 2.*width # Majorana case (charge conjugate channels)
        return width
    def Width_H_l(self, H, alpha):
        l = [None,'e','mu','tau']
        if self.MN < (self.masses[H] + self.masses[l[alpha]]):
            return 0.
        width = (math.fabs(self.U2[alpha-1])/(16.*math.pi))*(self.GF**2.)*(self.decayConstant[H]**2.)
        width = width*(self.MN**3.)*self.CKMelemSq[H]
        par = ( ((1 - ((self.masses[l[alpha]]**2.)/(self.MN**2.)))**2.) 
                - ( (self.masses[H]**2.)/(self.MN**2.)
                * (1 + ((self.masses[l[alpha]]**2.)/(self.MN**2.))) ) )
        if H == 'rho':
            par = ( ((1 - ((self.masses[l[alpha]]**2.)/(self.MN**2.)))**2.) 
                    + ( (self.masses[H]**2.)/(self.MN**2.)
                    * (1 + (((self.masses[l[alpha]]**2. - 2.*self.masses[H]**2.))/(self.MN**2.))) ) )
            par = par*2./(self.masses[H]**2.)
            
        width = width*par
        rad = math.sqrt( ( 1-((self.masses[H]-self.masses[l[alpha]])**2.)/(self.MN**2.) )
                * ( ( 1-((self.masses[H]+self.masses[l[alpha]])**2.)/(self.MN**2.) ) ) )
        width = width*rad
        width = 2.*width # Majorana case (charge conjugate channels)
        return width
    def Width_3nu(self):
        width = (self.GF**2.)*(self.MN**5.)*sum(self.U2)/(192.*(math.pi**3.))
        width = 2.*width # Majorana case (charge conjugate channels)
        return width
    def Width_l1_l2_nu(self, alpha, beta, gamma): # alpha, beta for the two leptons, gamma for the neutrino
        l = [None,'e','mu','tau','up','down','strange','charm','bottom','top']
        if self.MN < (self.masses[l[alpha]] + self.masses[l[beta]]):
            return 0.

        if (alpha > 3) and (beta == alpha): # N -> nu qq or N -> nu ll (mainly Z0)
            width = (self.GF**2.)*(self.MN**5.)*self.U2[gamma-1]/(192.*(math.pi**3.))

        elif ((alpha in [4, 7, 9]) and (beta in [5, 6, 8])) or ((alpha in [5, 6, 8]) and (beta in [4, 7, 9])): # N -> l W, W -> u dbar, index gamma stands for massive lepton
            if gamma == 3: # tau too massive for this parametrisation
                return 0.
            if self.MN < (self.masses[l[alpha]] + self.masses[l[beta]] + self.masses[l[gamma]]):
                return 0.
            width = (self.GF**2.)*(self.MN**5.)*self.U2[gamma-1]/(192.*(math.pi**3.))*self.CKMelemSq[(alpha-4, beta-4)]

        elif (alpha <= 3) and (beta <= 3):
            width = (self.GF**2.)*(self.MN**5.)*self.U2[alpha-1]/(192.*(math.pi**3.))

        else:
            return 0.

        if alpha != beta:
            xl = max([self.masses[l[alpha]] , self.masses[l[beta]]])/self.MN
            width = width*(1. - 8.*xl**2. + 8.*xl**6. - (12.*xl**4.)*math.log(xl**2.))
        else:
            xl = self.masses[l[alpha]] / self.MN
            lo = 0.
            logContent = (1. - 3.*xl**2. - (1.-xl**2.)*math.sqrt(1. - 4.*xl**2.) ) / ( (xl**2.)*(1 + math.sqrt(1. - 4.*xl**2.)) )
            if logContent > 0:
                lo = math.log( logContent )
            c1 = 0.25*(1. - 4.*self.s2thetaw + 8.*self.s2thetaw**2.)
            c2 = 0.5*self.s2thetaw*(2.*self.s2thetaw -1.)
            c3 = 0.25*(1. + 4.*self.s2thetaw + 8.*self.s2thetaw**2.)
            c4 = 0.5*self.s2thetaw*(2.*self.s2thetaw +1.)
            d = (alpha == gamma)
            width = width*( (c1*(1-d)+c3*d)*( (1.-14.*xl**2. -2.*xl**4. -12.*xl**6.)*math.sqrt(1-4.*xl**2) +12.*xl**4. *(-1.+xl**4.)*lo )
                            + 4.*(c2*(1-d)+c4*d)*( xl**2. *(2.+10.*xl**2. -12.*xl**4.) * math.sqrt(1.-4.*xl**2) + 6.*xl**4. *(1.-2.*xl**2+2.*xl**4)*lo ) )
        #if alpha>3 and beta>3: # N -> q q nu
        #    width = width*self.CKMelemSq[(alpha-4, beta-4)]
        width = 2.*width # Majorana case (charge conjugate channels)
        return width

    def NDecayWidth(self):
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

################################################################################
