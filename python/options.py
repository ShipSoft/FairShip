"""

    Program to study SHiP's sensitivity to HNLs
    This module includes classes to:
    * store the physics parameters and functions
    * store the experimental parameters and functions to compute the acceptance
    * simulate a N-body decay
    Author: Elena Graverini (elena.graverini@cern.ch)
    Last updated: 16/09/2014
    
"""

from __future__ import division
import sys, os, random
import math
import ROOT as r
import numpy as np
from array import array
import tauToN
import NFromBMesons
import cfg


def roundToN(x, n=2):
    if x:
        result = round(x, -int(math.floor(math.log10(math.fabs(x)))) + (n - 1))
    else:
        result = 0.
    return result


class physicsParameters():
    """ Set the physics parameters here. Everything is in GeV. """
    def __init__(self, energy, root_dir_path = os.getcwd()):
        self.root_dir_path = root_dir_path
        self.beamE = energy
        if energy==400:
            self.charmSourceFile = 'CharmFixTarget.root'
            self.beautySourceFile = 'BeautyFixTarget.root'
            # Contents of the source file
            self.nD = 5635
            self.nD0 = 11465
            self.nDs = 1553
            self.nTotCharm = self.nD + self.nD0 + self.nDs
            self.nB0 = 1027
            self.nB = 1088
            self.nBs = 173
            self.nTotBeauty = self.nB + self.nB0 + self.nBs
            self.Xcc = 0.45e-03
            self.Xbb = 4.52e-8

        elif energy==350:
            self.charmSourceFile = 'CharmFixTarget350.root'
            # Contents of the source file
            self.nD = 819#5635
            self.nD0 = 1715#11465
            self.nDs = 240#1553
            self.nTotCharm = self.nD + self.nD0 + self.nDs
            self.Xcc = 0.37e-03
        else:
            print "ERROR: the energy required (%s) is not expected! Possibilities are 350 GeV and 400 GeV"%energy
            quit()  
        self.sourceTreeName = 'newTree'

        self.modelFactors = [(52.,1.,1.), (1.,16.,3.8), (0.061,1.,4.3), (48.,1.,1.), (1.,11.,11.)]
        self.models = [tuple([c/max(fact) for c in fact]) for fact in self.modelFactors]
        self.factors = [sum(model) for model in self.models]
        self.leptons = ['e', 'mu', 'tau']
        self.decays = ['N -> nu nu nu',
                        'N -> e e nu',
                        'N -> e mu nu',
                        'N -> mu mu nu',
                        'N -> tau tau nu',
                        'N -> e tau nu',
                        'N -> mu tau nu',
                        'N -> pi0 nu',
                        'N -> pi e',
                        'N -> pi mu',
                        'N -> rho nu',
                        'N -> rho e',
                        'N -> rho mu',
                        'rho -> pi pi',
                        'rho -> pi pi0',
                        'pi0 -> gamma gamma',
                        'Ds -> mu N',
                        'Ds -> e N',
                        'Ds -> nu tau',
                        'B -> e N', 'B -> mu N', 'B -> tau N',
                        'tau -> mu N nu', 'tau -> e N nu',
                        'D -> K0 mu N', 'D -> K0 e N',
                        'D0 -> K mu N', 'D0 -> K e N',
                        'B -> D0 e N', 'B -> D0 mu N', 'B -> D0 tau N',
                        'B0 -> D e N', 'B0 -> D mu N', 'B0 -> D tau N',
                        'Bs -> Ds e N', 'Bs -> Ds mu N', 'Bs -> Ds tau N']
        self.masses = {'mu':0.10565,
                    'e':0.000511,
                    'tau':1.7768,
                    'pi':0.13957,
                    'pi0':0.13498,
                    'eta':0.54785,
                    'omega':0.78265,
                    'eta1':0.95778,
                    'K':0.493677,
                    'K0':0.498614,
                    'Ds':1.9685,
                    'D':1.86962,
                    'D0':1.865,
                    'Dst':2.007,
                    'p':0.938,
                    'rho':0.775,
                    'nu':0.,
                    'gamma':0.,
                    'up':2.3e-3,
                    'down':4.8e-3,
                    'strange':95.e-3,
                    'charm':1.28,
                    'bottom':4.18,
                    'top':173.,
                    'W':80.39,
                    'Z':91.19,
                    'B':5.279,
                    'Bs':5.367,
                    'B0':5.280,
                    'Bst':5.325,
                    'Bsst':5.415}
        self.m_max = {}
        self.m_max['charm'] = [self.masses['Ds']-self.masses[self.leptons[0]],
                            self.masses['Ds']-self.masses[self.leptons[1]],
                            self.masses['tau']-self.masses['e']]
        self.m_max['beauty'] = [self.masses['B']-self.masses[self.leptons[0]],
                            self.masses['B']-self.masses[self.leptons[1]],
                            self.masses['B']-self.masses['tau']]
        self.particle2id = {'D':411, 'D0':421, 'Ds':431,
                            'B0':511, 'B':521, 'Bs':531}
        self.alphaQED = 1./137.
        self.heV = 6.58211928*pow(10.,-16)
        self.hGeV = self.heV * pow(10.,-9)
        self.c = 3. * pow(10.,8)
        self.GF = 1.166379e-05 # Fermi's constant (GeV^-2)
        self.s2thetaw = 0.23126 # square sine of the Weinberg angle
        self.fpi = 0.1307 # from http://pdg.lbl.gov/2006/reviews/decaycons_s808.pdf
        self.fD = 0.2226
        self.fDs = 0.2801
        self.fB = 0.190 # from gorbunov, shaposhnikov
        self.fBs = 0.230 # from gorbunov, shaposhnikov
        self.tauB = 1.64e-12
        self.tauB0 = 1.52e-12
        self.tauBs = 1.52e-12
        self.tauD = 1.e-12 #sec
        self.tauDs = 0.5e-12
        self.tauD0 = 4.1e-13
        self.tauTau = 2.91e-13 #sec
        self.decayConstant = {'pi':0.1307, #GeV
                            'pi0':0.130, #GeV
                            'rho':0.102, #GeV
                            'eta':1.2*0.130, #GeV
                            'eta1':-0.45*0.130} #GeV^2
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
        self.BRDsToTau = 0.0543
        #self.w2body = {}
        self.w3body = {}
        #self.lifetimeFun = interpNLifetime('NLifetime.dat')

    def fplus(self, family, q2):
        if family == 'D':
            Mv = self.masses['Dst']
            f0 = 0.727
        elif family == 'B':
            Mv = self.masses['Bst']
            f0 = 0.4
        elif family == 'Bs':
            Mv = self.masses['Bsst']
            f0 = 0.4
        else:
            print 'fplus: unknown meson family!'
            sys.exit(-1)
        val = (Mv**2/(Mv**2-q2))*f0
        return val
    def fzero(self, family, q2):
        if family == 'D':
            Ms = self.masses['D']
            f0 = 0.727
        elif family == 'B':
            Ms = self.masses['B']
            f0 = 0.4
        elif family == 'Bs':
            Ms = self.masses['Bs']
            f0 = 0.4
        else:
            print 'fzero: unknown meson family!'
            sys.exit(-1)
        val = (Ms**2/(Ms**2-q2))*f0
        return val
    def fminus(self, family, q2, mH, mh):
        val = (self.fzero(family, q2)-self.fplus(family, q2))*(mH**2-mh**2)/q2
        return val
    def PhaseSpace3Body(self, family, q2, EN, mH, mh, mN, ml):
        fp = self.fplus(family, q2)
        fm = self.fminus(family, q2, mH, mh)
        PhaseSpace = (fm**2)*(q2*(mN**2+ml**2)-(mN**2-ml**2)**2)+2.*fp*fm*((mN**2)*(2*mH**2-2*mh**2-4*EN*mH-ml**2+mN**2+q2)+(ml**2)*(4.*EN*mH+ml**2-mN**2-q2))
        PhaseSpace += (fp**2)*((4.*EN*mH+ml**2-mN**2-q2)*(2.*mH**2-2.*mh**2-4.*EN*mH-ml**2+mN**2+q2)-(2.*mH**2+2.*mh**2-q2)*(q2-mN**2-ml**2))
        return PhaseSpace
    def phsp2body(self, mH, mN, ml):
        if mN >= (mH-ml):
            return 0.
        p1 = 1. - mN**2./mH**2. + 2.*(ml**2./mH**2.) + (ml**2./mN**2.)*(1. - (ml**2./mH**2.))
        p2 = ( 1. + (mN**2./mH**2.) - (ml**2./mH**2.) )**2. - 4.*(mN**2./mH**2.)
        p3 = math.sqrt( p2 )
        return p1*p3
    def Integrate3Body(self, family, mH, mh, mN, ml, nToys=1000):
        #### Setting up the parameters for generation
        W = r.TLorentzVector(0., 0., 0., mH)
        masses = array('d', [mh, mN, ml])
        event = r.TGenPhaseSpace()
        event.SetDecay(W, 3, masses)
        Nq2 = 20 
        NEN = 20
        ENMax = (mH-mh)
        ENMax = r.TMath.Sqrt(((ENMax**2-ml**2-mN**2)/2.)**2+mN**2) # converte massa max ad energia max
        hist = r.TH2F("hist", "", Nq2, (ml+mN)**2, (mH-mh)**2, NEN, mN, ENMax)
        ###### Integral
        Integral = 0.
        #### For loop in order to integrate
        for i in xrange(nToys):
            event.Generate()
            #### Getting momentum of the daughters
            ph = event.GetDecay(0)
            pN = event.GetDecay(1)
            pl = event.GetDecay(2)
            #### Computing the parameters to compute the phase space
            q = pl+pN
            q2 = q.M2()
            EN = pN.E()
            iBin = hist.Fill(q2, EN)
            if hist.GetBinContent(iBin)==1.:
                val = self.PhaseSpace3Body(family, q2, EN, mH, mh, mN, ml)
                Integral+=val*hist.GetXaxis().GetBinWidth(1)*hist.GetYaxis().GetBinWidth(1)
        hist.Delete()    
        return Integral
    def setNCoupling(self, couplings):
        self.U2 = couplings
        self.U = [math.sqrt(ui) for ui in self.U2]
    def computeU2tot(self):
        self.U2tot = sum(self.U2)
        return self.U2tot
    def setNMass(self, mass):
        self.MN = mass
        self.NM = mass
        if 'N' in self.masses:
            self.masses['N'] = self.MN
        else:
            self.masses.update({'N':self.MN})

    def computeNLifetime(self):
        self.NLifetime = self.hGeV / self.NDecayWidth()
        return self.NLifetime
    def drawNDecayVtx(self, momentum, originVtx):
        speed = momentum.Beta()*self.c
        DeltaT = momentum.Gamma()*r.gRandom.Exp(self.NLifetime)
        DeltaL = speed*DeltaT
        direction = momentum.Vect().Unit()
        endVtx = r.TVector3(direction.X()*DeltaL, direction.Y()*DeltaL, direction.Z()*DeltaL)
        decayVtx = originVtx + endVtx
        return decayVtx
    def energy(self, p, m):
        return math.sqrt(p*p + m*m)
    def momentum(self, E, m):
        return math.sqrt(E*E - m*m)
    def Width_H0_nu(self, H, alpha):
        if self.MN < (self.masses[H]):
            return 0.
        width = (math.fabs(self.U2[alpha-1])/(32.*math.pi))*(self.GF**2.)*(self.decayConstant[H]**2.)
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
    def findBranchingRatio(self, decayString):
        br = 0.
        totalWidth = self.NDecayWidth()
        if decayString == 'N -> pi e':
            br = self.Width_H_l('pi',1) / totalWidth
        elif decayString == 'N -> pi0 nu' or decayString == 'N -> pi nu':
            br = sum([self.Width_H0_nu('pi0',l) for l in [1,2,3]]) / totalWidth
        elif decayString == 'N -> pi mu':
            br = self.Width_H_l('pi',2) / totalWidth
        elif decayString == 'N -> rho nu' or decayString == 'N -> rho0 nu':
            br = sum([self.Width_H0_nu('rho',l) for l in [1,2,3]]) / totalWidth
        elif decayString == 'N -> rho e':
            br = self.Width_H_l('rho',1) / totalWidth
        elif decayString == 'N -> rho mu':
            br = self.Width_H_l('rho',2) / totalWidth
        elif decayString == 'N -> e e nu':
            br = sum([self.Width_l1_l2_nu(1,1,l) for l in [1,2,3]]) / totalWidth
        elif decayString == 'N -> mu mu nu':
            br = sum([self.Width_l1_l2_nu(2,2,l) for l in [1,2,3]]) / totalWidth
        elif decayString == 'N -> tau tau nu':
            br = sum([self.Width_l1_l2_nu(3,3,l) for l in [1,2,3]]) / totalWidth
        elif decayString == 'N -> e mu nu':
            br = (sum([self.Width_l1_l2_nu(1,2,l) for l in [1,2,3]]) + sum([self.Width_l1_l2_nu(2,1,l) for l in [1,2,3]])) / totalWidth
        elif decayString == 'N -> e tau nu':
            br = (sum([self.Width_l1_l2_nu(1,3,l) for l in [1,2,3]]) + sum([self.Width_l1_l2_nu(3,1,l) for l in [1,2,3]])) / totalWidth
        elif decayString == 'N -> mu tau nu':
            br = (sum([self.Width_l1_l2_nu(2,3,l) for l in [1,2,3]]) + sum([self.Width_l1_l2_nu(3,2,l) for l in [1,2,3]])) / totalWidth
        elif decayString == 'N -> nu nu nu' or decayString == 'N -> 3nu':
            br = self.Width_3nu() / totalWidth
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
        elif decayString == 'N -> TLEP visible':
            # eenu, mumunu, emunu, etaunu, tautaunu, mutaunu
            br0 = ( (sum([self.Width_l1_l2_nu(1,1,l) for l in [1,2,3]]) 
                   + sum([self.Width_l1_l2_nu(2,2,l) for l in [1,2,3]])
                   + (sum([self.Width_l1_l2_nu(1,2,l) for l in [1,2,3]]) + sum([self.Width_l1_l2_nu(2,1,l) for l in [1,2,3]]))
                   )/ totalWidth )
            br = br0
            if self.MN > 2.:
                br1 = ( (sum([self.Width_l1_l2_nu(a,b,g) for a in [4,7,9] for b in [5,6,8] for g in [1,2,3]]) +
                        sum([self.Width_l1_l2_nu(a,b,g) for a in [5,6,8] for b in [4,7,9] for g in [1,2,3]]) +
                        sum([self.Width_l1_l2_nu(3,3,l) for l in [1,2,3]]) + #tau tau nu
                        (sum([self.Width_l1_l2_nu(1,3,l) for l in [1,2,3]]) + sum([self.Width_l1_l2_nu(3,1,l) for l in [1,2,3]])) + #e tau nu
                        (sum([self.Width_l1_l2_nu(2,3,l) for l in [1,2,3]]) + sum([self.Width_l1_l2_nu(3,2,l) for l in [1,2,3]])) #mu tau nu
                        )/ totalWidth )
                br = br0 + br1
            if 1. <= self.MN <= 2.:
                m1, m2 = 1., 2.
                tempMass = self.MN
                self.MN = m2
                br2 = ( (sum([self.Width_l1_l2_nu(a,b,g) for a in [4,7,9] for b in [5,6,8] for g in [1,2,3]]) +
                        sum([self.Width_l1_l2_nu(a,b,g) for a in [5,6,8] for b in [4,7,9] for g in [1,2,3]]) +
                        sum([self.Width_l1_l2_nu(3,3,l) for l in [1,2,3]]) + #tau tau nu
                        (sum([self.Width_l1_l2_nu(1,3,l) for l in [1,2,3]]) + sum([self.Width_l1_l2_nu(3,1,l) for l in [1,2,3]])) + #e tau nu
                        (sum([self.Width_l1_l2_nu(2,3,l) for l in [1,2,3]]) + sum([self.Width_l1_l2_nu(3,2,l) for l in [1,2,3]])) #mu tau nu
                        )/ totalWidth ) + br0
                self.MN = tempMass
                br = br0 + (self.MN - m1)*(br2 - br0)/(m2 - m1)
        else:
            print 'findBranchingRatio ERROR: unknown decay %s'%decayString
            sys.exit(-1)
        return br
    def HNLAllowedDecays(self):
        m = self.MN
        allowedDecays = {'N -> nu nu nu':'yes'}
        if m > 2.*self.masses['e']:
            allowedDecays.update({'N -> e e nu':'yes'})
            if m > self.masses['e'] + self.masses['mu']:
                allowedDecays.update({'N -> e mu nu':'yes'})
            if m > self.masses['pi0']:
                allowedDecays.update({'N -> pi0 nu':'yes'})
            if m > self.masses['pi'] + self.masses['e']:
                allowedDecays.update({'N -> pi e':'yes'})
                if m > 2.*self.masses['mu']:
                    allowedDecays.update({'N -> mu mu nu':'yes'})
                    if m > self.masses['pi'] + self.masses['mu']:
                        allowedDecays.update({'N -> pi mu':'yes'})
                        if m > self.masses['rho']:
                            allowedDecays.update({'N -> rho nu':'yes'})
                            if m > self.masses['rho'] + self.masses['e']:
                                allowedDecays.update({'N -> rho e':'yes'})
                                if m > self.masses['rho'] + self.masses['mu']:
                                    allowedDecays.update({'N -> rho mu':'yes'})
                                    if m > self.masses['e'] + self.masses['tau']:
                                        allowedDecays.update({'N -> e tau nu':'yes'})
                                        if m > self.masses['mu'] + self.masses['tau']:
                                            allowedDecays.update({'N -> mu tau nu':'yes'})
                                            if m > 2.*self.masses['tau']:
                                                allowedDecays.update({'N -> tau tau nu':'yes'})
        for decay in self.decays:
            if decay not in allowedDecays and decay.startswith('N'):
                allowedDecays.update({decay:'no'})
        return allowedDecays



def expon(x, par):
    return math.exp( (-1.)*float(par[0])*float(x[0]) )


class experimentParams():
    """ The experimental settings (beam, geometry...)
        Requires an instance pp of physicsParameters() """
        # cfg=cfg: dirty idea of Elena, to be sure that we are doing the correct thing in case of the blue volume! Hopefully we are also doing correctly for the others!
    def __init__(self, pp, name, config=cfg.cfg()):
        self.cfg = config
        self.LTfun = r.TF1("lifetime",expon,0., 1000.,2)
        if name == "SHiP" or name == "ship" or name == "SHIP":
            self.decayVolumes = []
            self.zMagnet = []

            for v in self.cfg.vols:
                self.decayVolumes.append(cfg.ellipticalVolume(*v))
                self.zMagnet.append(self.decayVolumes[-1].z2-self.cfg.deltaMagnet)
            
                
            self.protonEnergy = pp.beamE #400. # GeV/c
            self.protonMomentum = pp.momentum(self.protonEnergy, pp.masses['p'])
            self.protonFlux = 2.*pow(10.,20.)

            
            #self.firstVolume = cfg.firstVolume #[60., 100., 2.5] # start, end, radius (m)
            #self.secondVolume = cfg.secondVolume #[110., 150., 2.5] # start, end, radius (m)
            #if self.firstVolume[0]:
            #    self.v1ThetaMax = None #cfg.a1*cfg.b1/sqrt((cfg.b1*)self.firstVolume[2]/self.firstVolume[0]
            #else:
            #    self.v1ThetaMax = math.radians(90.)
            #self.v2ThetaMax = self.secondVolume[2]/self.secondVolume[0]
            
        elif name == "TLEP" or name == "tlep" or name == "Tlep":
            self.nZ = 1.e12
            self.nW = 1.e11
            self.efficiency = 1.
            self.minSVdistance = 1.e-3 # 1 mm (maybe increase to 5 mm)
            self.Rmin = 1.e-3
            self.Rmax = 1. # 1 m (maybe increase?)
            self.BRZnunu = 0.08
            self.BRWlnu = 0.108
        else:
            print "experimentParams ERROR: please provide the name of the experiment!"

    def inEllipse(self, vtx, volumeIndex, shape):
        volume = self.decayVolumes[volumeIndex]

        if not (shape=='squared' or shape=='round'):
            print 'ERROR: %s is not a defined shape'%shape
            sys.exit()
            
        a = volume.a(vtx.Z())
        b = volume.b(vtx.Z())
        #print 'a,b',a,b
        
        if shape == 'squared' and ((abs(vtx.X()) < a) and (abs(vtx.Y()) < b)):
            return True
        elif shape == 'round' and ((vtx.X()**2.)/(a**2.) + (vtx.Y()**2.)/(b**2.)) < 1.:
            return True
        return False

    def inEllipticalAcceptance(self, vtx, kids, volumeIndex, P_kick, shape, exclude5m):
        # Because we don't have the energy to do it properly --> TODO: P_kick, shape, exclude5m should be removed as inputs, and be taken from self.cfg ;-)
        assert(self.cfg.P_kick == P_kick)
        assert(self.cfg.shape == shape)
        assert(self.cfg.excludeFirst5m == exclude5m)
        
        volume = self.decayVolumes[volumeIndex]
        if not kids:
            return False
        if exclude5m:
            if (volume.z1 < vtx.Z() < volume.z1+5.):
                return False
        detectable = []
        if (vtx.Z() > volume.z1) and (vtx.Z() < volume.z2): # longitudinal vtx acc
            if self.inEllipse(vtx, volumeIndex, shape): # transverse vtx acc
                charge = [1, -1]
                if bool(random.getrandbits(1)):
                    charge = [-1, 1]
                if len(kids) == 4:
                    charge.extend([0,0])
                for (index, particle) in enumerate(kids): # daughters acc
                    # check if it goes out of the magnet
                    #print P_kick, volume, vtx, particle, charge[index], self.zMagnet[volumeIndex]
                    trash, posAtMag = self.propagate(P_kick, volumeIndex, vtx, particle, charge[index], self.zMagnet[volumeIndex])
                    if not self.inEllipse(posAtMag, volumeIndex, shape):
                        return False
                    # check if it crosses the detector
                    newFourMom, endPos = self.propagate(P_kick, volumeIndex, vtx, particle, charge[index], volume.z2)
                    
                    if self.inEllipse(endPos, volumeIndex, shape):
                        detectable.append(True)
                    #else:
                    #    ellVol.a2 = cfg.a2forCalo(ellVol, 3.)
                    #    ellVol.b2 = cfg.b2forCalo(ellVol, 6.)
                    #    if inEllipse(endPos, ellVol, shape):
                    #        detectable.append(True)
                    else:
                        detectable.append(False)
                return bool(np.product(detectable))
        # Otherwise
        return False

    
    def propagate(self, P_kick, volumeIndex, vtx, fourMom, charge, z):
        """ Returns the 4-momentum and position of a particle at a given z """
        positionAtMagnet = r.TVector3()
        positionAtMagnet.SetZ(self.zMagnet[volumeIndex])
        if vtx.Z() >= positionAtMagnet.Z():
            #print 'Z: ', vtx.Z(), positionAtMagnet.Z()
            newFourMom = fourMom
            positionAtMagnet = vtx
        else:
            tx = fourMom.Px() / fourMom.Pz()
            ty = fourMom.Py() / fourMom.Pz()
            dz = positionAtMagnet.Z() - vtx.Z()
            positionAtMagnet.SetX( vtx.X() + tx*dz )
            positionAtMagnet.SetY( vtx.Y() + ty*dz )
            alpha = P_kick.Mag() / fourMom.Vect().Mag()
            newFourMom = r.TLorentzVector(fourMom)
            newFourMom.RotateX(charge*alpha)
    
        dz = z - positionAtMagnet.Z()
        tx = newFourMom.Px() / newFourMom.Pz()
        ty = newFourMom.Py() / newFourMom.Pz()
        position = r.TVector3()
        position.SetZ(z)
        position.SetX( positionAtMagnet.X() + tx*dz )
        position.SetY( positionAtMagnet.Y() + ty*dz )
    
        return newFourMom, position
            
    # This function is used to write r as a function of phi, to find the max theta for being inside ship. 
    def r(self,phi,volume):
        ## ellipse in polar coordinate
        return volume.a1*volume.b1/math.sqrt((volume.b1*math.cos(phi))**2. + (volume.a1*math.sin(phi))**2.)
    #return volume.a1*volume.b1/math.sqrt((volume.a1*math.cos(phi))**2. + (volume.b1*math.sin(phi))**2.)
                                  
    def maxTheta(self,phi,volume,z=None):
        if z is None:
            z = volume.z1
        if z == 0.:
            return math.pi/2.
        return self.r(phi,volume)/z
        
    def makeVtxInVolume(self, momentum, ct, volumeIndex):
        '''if volume == 1:
            vol = self.firstVolume
        elif volume == 2:
            vol = self.secondVolume
        else:
            print "ERROR: select decay volume 1 or 2"
            return 0
        '''
        volume = self.decayVolumes[volumeIndex]
        gamma = momentum.Gamma()
        Direction = momentum.Vect().Unit()
        costheta = math.fabs(momentum.CosTheta())
        if momentum.Pz():
            dxdz = momentum.Px()/momentum.Pz()
            dydz = momentum.Py()/momentum.Pz()
        else:
            dxdz, dydz = 0., 0.

        #Origin = r.TVector3( vol[0]*dxdz, vol[0]*dydz, vol[0] )
        Origin = r.TVector3( volume.z1*dxdz, volume.z1*dydz, volume.z1 )

        if not self.inEllipse(Origin, volumeIndex, 'round'):
            #print "makeVtxInVolume WARNING: generating decay vertex outside volume!"
            return Origin #we just need something counted out of acceptance
        
        self.LTfun.SetParameter(0, 1./(gamma*ct))

        # If phi is such that the particle will leave the decay volume
        # before volume.z2, recompute its maximum path accordingly:
        if momentum.Theta() > self.maxTheta(momentum.Phi(), volume, volume.z2):
            '''P = Origin
            #P.Print()
            #R = Direction * (volume.z2 )#- volume.z1)
            #R.Print()
            R = r.TVector3( volume.z2*dxdz, volume.z2*dydz, volume.z2 )
            #R.Print()
            
            Q = r.TVector3(self.r(momentum.Phi(), volume) * math.cos(momentum.Phi()),
                self.r(momentum.Phi(), volume) * math.sin(momentum.Phi()),
                volume.z1)
            S = r.TVector3(self.r(momentum.Phi(), volume) * math.cos(momentum.Phi()),
                self.r(momentum.Phi(), volume) * math.sin(momentum.Phi()),
                volume.z2)
            t = ((Q-P).Cross(S)).Mag() / (R.Cross(S)).Mag()
            ExitPoint = P + t*R
            print "--->",ExitPoint.X(), ExitPoint.Y(), ExitPoint.Z()
            maxlength = (ExitPoint - Origin).Mag()
            '''
            x1 = Origin
            x2 = r.TVector3( volume.z2*dxdz, volume.z2*dydz, volume.z2 )
            
            x3 = r.TVector3(self.r(momentum.Phi(), volume) * math.cos(momentum.Phi()),
                self.r(momentum.Phi(), volume) * math.sin(momentum.Phi()),
                volume.z1)
            x4 = r.TVector3(self.r(momentum.Phi(), volume) * math.cos(momentum.Phi()),
                self.r(momentum.Phi(), volume) * math.sin(momentum.Phi()),
                volume.z2)

            a = x2-x1
            b = x4-x3
            c = x3-x1

            c_cross_b = c.Cross(b)
            a_cross_b = a.Cross(b)

            num = c_cross_b.Dot(a_cross_b)
            den = a_cross_b.Mag2()
            
            ExitPoint = x1 + a * (num/den)
            #print "--->",ExitPoint.X(), ExitPoint.Y(), ExitPoint.Z()
            maxlength = (ExitPoint - Origin).Mag()
        else:
            #maxlength = (vol[1]-vol[0])/costheta
            maxlength = (volume.z2-volume.z1)/costheta
        DL = self.LTfun.GetRandom(0., maxlength)
        EndVertex = r.TVector3(Direction[0]*DL, Direction[1]*DL, Direction[2]*DL)
        EndVertex = Origin + EndVertex
        return EndVertex
    
    def TLEPacceptance(self,pp,boson):
        if (boson is not 'Z') and (boson is not 'W'):
            print 'TLEPacceptance: please define the source of neutrinos (Z or W)!'
            sys.exit(-1)
        lt = pp.computeNLifetime()
        mb = pp.masses[boson]
        gamma = (mb/(2.*pp.MN)) + (pp.MN/(2.*mb)) #this neglects ml in W->lN
        cgammatau = lt*gamma*pp.c
        esp1 = (-1.)*self.Rmin/cgammatau
        esp2 = (-1.)*self.Rmax/cgammatau
        try:
            result = np.nan_to_num(np.exp(esp1) - np.exp(esp2))
        except (ValueError, FloatingPointError):
            result = 0.
        return result
    '''def inAcceptance(self, vtx, particleList, volume):
        if not particleList:
            return False
        if volume == 1:
            vol = self.firstVolume
            tMax = self.v1ThetaMax
        elif volume == 2:
            vol = self.secondVolume
            tMax = self.v2ThetaMax
        else:
            print "experimentParams.inAcceptance ERROR: please select volume 1 or 2!"
        detectable = []
        if (vtx.Z() > vol[0]) and (vtx.Z() < vol[1]): # longitudinal vtx acc
            if (vtx.X()**2. + vtx.Y()**2.) < vol[2]: # transverse vtx acc
                for particle in particleList:
                    tx = particle.Px() / particle.Pz()
                    ty = particle.Py() / particle.Pz()
                    endPos1 = r.TVector3()
                    endPos1.SetZ(vol[1])
                    endPos1.SetX( vtx.X() + tx*(endPos1.Z() - vtx.Z()) )
                    endPos1.SetY( vtx.Y() + ty*(endPos1.Z() - vtx.Z()) )
                    if (endPos1.X()**2. + endPos1.Y()**2.) < vol[2]**2.:
                        detectable.append(True)
                    else:
                        detectable.append(False)
                return bool(np.product(detectable))
        # Otherwise
        return False
    '''

    '''def inAcceptance(self, vtx, particleList, volume):
        if not particleList:
            return False
        
        detectable = []
        if (vtx.Z() > self.decayVol.z1) and (vtx.Z() < self.decayVol.z2): # longitudinal vtx acc
            if (vtx.X()**2./self.decayVol.a1**2 + vtx.Y()**2./self.decayVol.b1**2) < 1.: # transverse vtx acc
                for particle in particleList:
                    tx = particle.Px() / particle.Pz()
                    ty = particle.Py() / particle.Pz()
                    endPos1 = r.TVector3()
                    endPos1.SetZ(self.decayVol.z2)
                    endPos1.SetX( vtx.X() + tx*(endPos1.Z() - vtx.Z()) )
                    endPos1.SetY( vtx.Y() + ty*(endPos1.Z() - vtx.Z()) )
                    if (endPos1.X()**2./self.decayVol.a1**2 + endPos1.Y()**2./self.decayVol.b1**2) < 1.:
                        detectable.append(True)
                    else:
                        detectable.append(False)
                return bool(np.product(detectable))
        # Otherwise
        return False
    '''
    
	
    def probVtxInVolume(self, momentum, ct, volumeIndex):
        '''if volume == 1:
            vol = self.firstVolume
        elif volume == 2:
            vol = self.secondVolume
        else:
            print "ERROR: select decay volume 1 or 2"
            return 0
        '''
        gamma = momentum.Gamma()
        costheta = np.fabs(momentum.CosTheta())
        tantheta = np.tan(momentum.Theta())
        '''start = vol[0]
        end = vol[1]
        rad = vol[2]
        '''

        volume = self.decayVolumes[volumeIndex]
        start = volume.z1
        end = volume.z2
        rad = self.r(momentum.Phi(),volume)
        #print rad
        stop = min(rad/tantheta, end)
        if stop < start:
            return 0.
        esp1 = (-1.) * (start/costheta) / (gamma*ct)
        esp2 = (-1.) * (stop/costheta) / (gamma*ct)
        try:
            result = np.nan_to_num(np.fabs( np.exp(esp1) - np.exp(esp2) ))
        except (ValueError, FloatingPointError):
            result = 0.
        return result
    
    def GeometricAcceptance(self, momentum, volumeIndex):
        tMax = self.maxTheta(momentum.Phi(),self.decayVolumes[volumeIndex])
        '''if volume == 1:
            if self.v1ThetaMax is None:
                tMax = self.maxTheta(self.r(momentum.Phi()))#self.v1ThetaMax
            else:
                tMax = self.v1ThetaMax
        elif volume == 2:
            tMax = self.v2ThetaMax
        else:
            print "ERROR: select decay volume 1 or 2"
            return 0
        '''
        if momentum.Theta() < tMax and momentum.Pz() > 0.:
            return True
        return False

        

class decayNBody():
    """ General 2-bodies decay representation.
        Requires an instance pp of physicsParameters(). """
    def __init__(self, pp):
        self.pp = pp
        self.mother = None
        self.kid1 = None
        self.kid2 = None
        self.particles = [None]
        self.lifetime = None
        self.gen = r.TGenPhaseSpace()
    def readString(self, decayName):
        if decayName not in self.pp.decays:
            print 'decayNBody::readString ERROR: decay %s not found in database!'%decayName
            sys.exit(-1)
        self.name = decayName
        self.particles = [p for p in self.name.replace('->',' ').split()]
        self.mother = self.particles[0]
        self.motherMass = self.pp.masses[self.mother]
        self.pMother = r.TLorentzVector(0., 0., 0., self.motherMass)
        self.kid1 = self.particles[1]
        self.kid2 = self.particles[2]
        self.childrenMasses = array('d', [self.pp.masses[self.kid1], self.pp.masses[self.kid2]])
        self.nbody = 2
        if self.name in (self.pp.decays[:7]+self.pp.decays[22:]):
            self.nbody = 3
            self.kid3 = self.particles[3]
            self.childrenMasses = array('d', [self.pp.masses[self.kid1], self.pp.masses[self.kid2], self.pp.masses[self.kid3]])
        if sum(self.childrenMasses) > self.motherMass:
            print 'decayNBody::readString ERROR: children too heavy! %s'%decayName
            sys.exit(-1)
    def setPMother(self, pMother):
        self.pMother = pMother
    def setLifetime(self, lifetime):
        self.lifetime = lifetime
    def makeDecay(self):
        """ if no setPMother method is called, this method makes a RF decay """
        if not self.childrenMasses:
            print "decayNBody ERROR: I have no particles!"
            sys.exit(-1)
        self.gen.SetDecay(self.pMother, self.nbody, self.childrenMasses)
        self.gen.Generate()
        self.pKid1, self.pKid2 = self.gen.GetDecay(0), self.gen.GetDecay(1)
        if self.nbody == 3:
            self.pKid3 = self.gen.GetDecay(2)
            return self.pKid1, self.pKid2, self.pKid3
        return self.pKid1, self.pKid2
    def boostChildren(self, pBoost):
        """ requires a TLorentzVector::BoostVector pBoost """
        self.pKid1.Boost(pBoost)
        self.pKid2.Boost(pBoost)

class myNEvent():
    """ Sterile neutrino production and decay.
        Requires an instance pp of physicsParameters(). """
    def __init__(self, pp):
        if not 'N' in pp.masses:
            print "physicsParameters ERROR: sterile neutrino mass undefined!"
            sys.exit(-1)
        if not pp.U:
            print "physicsParameters ERROR: sterile neutrino coupling undefined!"
            sys.exit(-1)
        self.pp = pp #physics
        self.production = decayNBody(self.pp)
        self.decay = decayNBody(self.pp)






class CKMmatrix():
    # From http://pdg.lbl.gov/2013/reviews/rpp2013-rev-ckm-matrix.pdf
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



def productionBR(pp, source, flavour):
    leptons = [None, 'e', 'mu', 'tau']
    BR = 0.
    if source == 'charm':
        BR0 = pp.Xcc
        if flavour == 3:
            BR0 *= (pp.nDs/pp.nTotCharm)*pp.BRDsToTau
            if pp.MN < (pp.masses['tau'] - pp.masses['e']):
                BR += BR0*tauToN.brTauToNuEllN(pp,'e')
            if pp.MN < (pp.masses['tau'] - pp.masses['mu']):
                BR += BR0*tauToN.brTauToNuEllN(pp,'mu')
            if pp.MN < (pp.masses['tau'] - pp.masses['pi']):
                BR += BR0*tauToN.brTauToPiN(pp)
        else:
            if pp.MN < (pp.masses['Ds']-pp.masses[leptons[flavour]]):
                BR += BR0*(pp.nDs/pp.nTotCharm) * NFromBMesons.BR2Body(pp,'Ds',leptons[flavour])
            if pp.MN < (pp.masses['D0']-pp.masses['K']-pp.masses[leptons[flavour]]):
                BR += BR0*(pp.nD0/pp.nTotCharm) * NFromBMesons.BR3Body(pp,'D0',leptons[flavour])
            if pp.MN < (pp.masses['D']-pp.masses['K0']-pp.masses[leptons[flavour]]):
                BR += BR0*(pp.nD/pp.nTotCharm) * NFromBMesons.BR3Body(pp,'D',leptons[flavour])
    elif source == 'beauty':
        BR0 = pp.Xbb
        if pp.MN < (pp.masses['B'] - pp.masses[leptons[flavour]]):
            BR += BR0*(pp.nB/pp.nTotBeauty) * NFromBMesons.BR2Body(pp, 'B', leptons[flavour])
        if pp.MN < (pp.masses['B'] - pp.masses[leptons[flavour]] - pp.masses['D0']):
            BR += BR0*(pp.nB/pp.nTotBeauty) * NFromBMesons.BR3Body(pp, 'B', leptons[flavour])
        if pp.MN < (pp.masses['B0'] - pp.masses[leptons[flavour]] - pp.masses['D']):
            BR += BR0*(pp.nB0/pp.nTotBeauty) * NFromBMesons.BR3Body(pp, 'B0', leptons[flavour])
        if pp.MN < (pp.masses['Bs'] - pp.masses[leptons[flavour]] - pp.masses['Ds']):
            BR += BR0*(pp.nBs/pp.nTotBeauty) * NFromBMesons.BR3Body(pp, 'Bs', leptons[flavour])
    return BR
