"""
# ==================================================================
#   Python module
#
#   This module provides methods to compute the lifetime and
#   branching ratio of SUSY RPV neutralino given its mass and couplings as
#   input parameters.
#
#   Created: 30/04/2016 Konstantinos A. Petridis (konstantinos.petridis@cern.ch)
#
#   Sample usage:
#     ipython -i rpvsusy.py
#     In [1]: b = RPVSYSY(1.,[1, 1],1e3,1,True)
#     HNLbranchings instance initialized with couplings:
#          \lambda_{production}       = 1GeV
#	   \lambda_{decay}            = 1GeV
#          universal sfermion mass    = 1e3GeV
#
#     benchmark scenario:
#          1 (values between 1 and 5)
#     and mass:
#	   m = 1.0 GeV
#     In [2]: b.computeNLifetime()
#     Out[2]: 0.0219634078804
#     In [3]: b.findBranchingRatio('N -> K+ mu-')
#     Out[3]: 0.11826749348890987
#
# ==================================================================
"""

import re
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
             or ('nu_' in particle) or ('eta' in particle) or ('phi' in particle) )
        and (particle not in ['d','u','s','c','b','t'])):
        particle += '+'
    return particle

def PDGcode(particle):
    """
    Read particle ID from PDG database
    """
    particle = PDGname(particle)
    tPart = pdg.GetParticle(particle)
    return int(tPart.PdgCode())

def mass(particle):
    """
    Read particle mass from PDG database
    """
    particle = PDGname(particle)
    tPart = pdg.GetParticle(particle)
    return tPart.Mass()

def width(particle):
    """
    Read particle width from PDG database
    """
    particle = PDGname(particle)
    tPart = pdg.GetParticle(particle)
    return tPart.Width()

def lifetime(particle):
    """
    Read particle lifetime from PDG database
    """
    particle = PDGname(particle)
    tPart = pdg.GetParticle(particle)
    if particle=="D0" or particle=="D0bar" :
        return 4.1e-13
    elif particle=="D+" or particle=="D-":
        return 1.0e-12
    elif particle=="D_s+" or particle=="D_s-":
        return 5.0e-13
    elif particle=="B0" or particle=="B0bar":
        return 1.5e-12
    elif particle=="B+" or particle=="B-":
        return 1.6e-12
    
    return tPart.Lifetime()


class constants():
    """
    Store some constants useful for HNL physics
    """
    def __init__(self):
        self.decayConstant = {'K+':0.156*u.GeV,
                              'K-':0.156*u.GeV,
                              'K_L0':0.156/math.sqrt(2)*u.GeV,
                              'K_S0':0.156/math.sqrt(2)*u.GeV,
                              'K*0':0.230*u.GeV,
                              'K*0_bar':0.230*u.GeV,
                              'K*+':0.230*u.GeV,
                              'K*-':0.230*u.GeV,
                              'phi':0.230*u.GeV,
                              'eta':-0.142*u.GeV,
                              "eta\'":0.038*u.GeV,
                              'D+':0.205*u.GeV,'D*+':0.205*u.GeV,
                              'D-':0.205*u.GeV,'D*-':0.205*u.GeV,
                              'D_s+':0.259*u.GeV,'D*_s+':0.259*u.GeV,
                              'D_s-':0.259*u.GeV,'D*_s-':0.259*u.GeV,
                              'B+':0.191*u.GeV,'B-':0.191*u.GeV,
                              'B0':0.191*u.GeV,'B_s0':0.228*u.GeV,
                              'B0_bar':0.191*u.GeV,'B_s0_bar':0.228*u.GeV} 

        self.GF   = 1.166379e-05/(u.GeV*u.GeV)             # Fermi's constant (GeV^-2)
        self.MW   = 80.385*u.GeV
        self.gW2  = self.GF/math.sqrt(2)*8*self.MW*self.MW # SU(2)L gauge coupling squared
        self.s2thetaw = 0.23126                            # square sine of the Weinberg angle
        self.t2thetaw = self.s2thetaw/(1-self.s2thetaw)    # square tan of the Weinberg angle
        self.heV = 6.58211928*pow(10.,-16)                 # no units or it messes up!!
        self.hGeV = self.heV * pow(10.,-9)                 # no units or it messes up!!
        # defined in Eq (30)--(32) of [1511.07436], but without 
        # the coupling over sfermion mass, that will come later
        self.GST2 = {'slepton'   : self.gW2*self.t2thetaw*9./8.,
                     'sneutrino' : self.gW2*self.t2thetaw*9./8.,
                     'tlepton'   : self.gW2*self.t2thetaw*1./32.,
                     'tneutrino' : self.gW2*self.t2thetaw*1./32.} 



# Load some useful constants
c = constants()

class RPVSUSYbranchings():
    """
    Lifetime and total and partial decay widths of an RPV neutralino
    """
    def __init__(self, mass, couplings, sfmass, benchmark,debug=False):
        """
        Initialize with mass and couplings of the RPV neutralino

        Inputs:
        mass (GeV)
        which benchmark scenario (1,2,3,4,5)
        couplings (list of [\lambda production, \lambda decay])
        sfermion mass to normalise the couplings by (GeV)
        """
        self.MN = mass*u.GeV
        self.U  = couplings
        self.U2 = [ui*ui for ui in self.U]
        self.sfmass = sfmass
        self.bench  = benchmark
        self.decays =  {1:['N -> K+ mu-','N -> K*+ mu-','N -> K*0 nu_mu','N -> K_L0 nu_mu','N -> K_S0 nu_mu'],
                        2:['N -> K+ mu-','N -> K*+ mu-','N -> K*0 nu_mu','N -> K_L0 nu_mu','N -> K_S0 nu_mu',
                           'N -> eta nu_mu','N -> eta\' nu_mu','N -> phi nu_mu'],
                        3:['N -> K+ mu-','N -> K*+ mu-','N -> K*0 nu_mu','N -> K_L0 nu_mu','N -> K_S0 nu_mu'],
                        4:['N -> D+ mu-','N -> D*+ mu-','N -> K*0 nu_mu','N -> K_L0 nu_mu','N -> K_S0 nu_mu'],
                        5:['N -> K+ tau-','N -> K*+ tau-','N -> K*0 nu_tau','N -> K_L0 nu_tau','N -> K_S0 nu_tau']}

        self.prods   =  {1:['D+ -> N mu+'],
                         2:['D_s+ -> N mu+'],
                         3:['B0 -> N nu_mu'],
                         4:['B0 -> N nu_mu'],
                         5:['B0 -> N nu_tau','B+ -> N tau+']}


        if debug:
            print "RPVSUSYbranchings instance initialized with couplings:"
            print "\t benchmark scenario   = %d"%self.bench
            print "\t decay coupling       = %s"%self.U[0]
            print "\t production coupling  = %s"%self.U[1]
            print "\t sfermion mass        = %s"%self.sfmass
            print "\t total prod coupling  = %s"%(self.U[0]/self.sfmass**2)
            print "\t total decay coupling = %s"%(self.U[1]/self.sfmass**2)
            print "and mass:"
            print "\tm = %s GeV"%(self.MN)

    def Get_Prod_Modes(self):
        return self.prods[self.bench]

    def Get_Dec_Modes(self):
        return self.decays[self.bench]

    def AddChannelsToPythia(self,P8Gen,verbose=True):
        decays_tmp = self.decays[self.bench]
        for decay in decays_tmp:
            decay_cpy = decay
            decay_cpy = decay_cpy.replace("N -> ","")
            particles = decay_cpy.split()
            codes     = [PDGcode(p) for p in particles]
            print decay
            bf        = self.findDecayBranchingRatio(decay)
            if any("K+" in s for s in particles) or\
               any("K-" in s for s in particles) or\
               any("K*+" in s for s in particles) or\
               any("K*-" in s for s in particles) or\
               any("K*0" in s for s in particles) or\
               any("K*0_bar" in s for s in particles):
                bf             = bf/2.
                codes_str      = ' '.join([str(code) for code in codes])
                P8Gen.SetParameters("9900015:addChannel = 1 "+str(bf)+" 0 "+codes_str)
                codes_str_conj = ' '.join([str(-1*code) for code in codes])
                P8Gen.SetParameters("9900015:addChannel = 1 "+str(bf)+" 0 "+codes_str_conj)
            else:
                codes_str      = ' '.join([str(code) for code in codes])
                P8Gen.SetParameters("9900015:addChannel = 1 "+str(bf)+" 0 "+codes_str)
            if verbose:
                print "debug readdecay table",particles,codes,bf
            

            
    def Width_H_L(self, H, L):
        """
        Returns the RPV neutralino decay width into neutral meson and lepton

        Inputs:
        - H is a string (name of the meson)
        - L is a string (name of the lepton)
        """
        if self.MN < (mass(H)+mass(L)):
            return 0.
        
        phsp=math.sqrt(self.MN**4+mass(H)**4+mass(L)**4-\
                       2*self.MN**2*mass(H)**2-2*self.MN**2*mass(L)**2-\
                       2*mass(H)**2*mass(L)**2)
        tmp_width=0
        if 'nu_mu' in L or 'nu_e' in L or 'nu_tau' in L:
            tmp_width = phsp/(self.sfmass**4*128*u.pi*self.MN**3)*\
                        c.GST2['sneutrino']*c.decayConstant[H]**2*\
                        (self.MN**2+mass(L)**2-mass(H)**2)
        else:
            tmp_width = phsp/(self.sfmass**4*128*u.pi*self.MN**3)*\
                        c.GST2['slepton']*c.decayConstant[H]**2*\
                        (self.MN**2+mass(L)**2-mass(H)**2)
            
        if 'K*' in H or 'D*' in H or "phi" in H:
            if 'nu_mu' in L or 'nu_e' in L or 'nu_tau' in L:
                tmp_width = phsp/(self.sfmass**4*2*u.pi*self.MN**3)*\
                            c.GST2['tneutrino']*c.decayConstant[H]**2*\
                            (2*(self.MN**2-mass(L)**2)**2-mass(H)**2*(mass(H)**2+self.MN**2+mass(L)**2))
            else:
                tmp_width = phsp/(self.sfmass**4*2*u.pi*self.MN**3)*\
                            c.GST2['tlepton']*c.decayConstant[H]**2*\
                            (2*(self.MN**2-mass(L)**2)**2-mass(H)**2*(mass(H)**2+self.MN**2+mass(L)**2))
        width=self.U2[1]*tmp_width
        # contributions both from decay and production couplings
        if self.bench==1 and ('K_' in H or 'K*' in H):
            width=(self.U2[0]+self.U2[1])*tmp_width
        # contributions only from production coupling
        if self.bench==2 and ('eta' in H or 'phi' in H):
            width=self.U2[0]*tmp_width
        
        # Majorana case (charge conjugate channels)
        width = 2.*width 
        return width


    def Width_N_L(self, H, L):
        """
        Returns the Meson decay width to RPV neutralino and lepton
        Inputs:
        - H is a string (name of the meson)
        - L is a string (name of the lepton)
        """
        
        if mass(H) < (self.MN+mass(L)):
            return 0.
        phsp=math.sqrt(self.MN**4+mass(H)**4+mass(L)**4-\
                       2*self.MN**2*mass(H)**2-2*self.MN**2*mass(L)**2-\
                       2*mass(H)**2*mass(L)**2)
        
        tmp_width=0
        if 'nu_mu' in L or 'nu_e' in L or 'nu_tau' in L:
            tmp_width = phsp/(self.sfmass**4*64*u.pi*mass(H)**3)*\
                        c.GST2['sneutrino']*c.decayConstant[H]**2*\
                        (mass(H)**2-self.MN**2-mass(L)**2)
        else:
            tmp_width = phsp/(self.sfmass**4*64*u.pi*mass(H)**3)*\
                        c.GST2['slepton']*c.decayConstant[H]**2*\
                        (mass(H)**2-self.MN**2-mass(L)**2)
            
        if 'K*' in H or 'D*' in H or "phi" in H:
            if 'nu_mu' in L or 'nu_e' in L or 'nu_tau' in L:
                tmp_width = phsp/(self.sfmass**4*3*u.pi*mass(H)**3)*\
                            c.GST2['tneutrino']*c.decayConstant[H]**2*\
                            (mass(H)**2*(mass(H)**2+self.MN**2+mass(L)**2-2*(self.MN**2-mass(L)**2)**2))
            else:
                tmp_width = phsp/(self.sfmass**4*3*u.pi*mass(H)**3)*\
                            c.GST2['tlepton']*c.decayConstant[H]**2*\
                            (mass(H)**2*(mass(H)**2+self.MN**2+mass(L)**2-2*(self.MN**2-mass(L)**2)**2))
                            
        width=self.U2[0]*tmp_width
        
        return width



    def NdecayWidth(self):
        """
        Returns the total SUSYRPV neutralino decay width
        """
        declist    = self.decays[self.bench]
        hadlist    = [re.search('->\ (.+?)\ ',dec).group(1) for dec in declist]
        leplist    = [dlist[1].strip() for dlist in [re.findall(r"\ \w+",dec) for dec in declist]]
        print leplist,hadlist
        totalwidth = sum([self.Width_H_L(hadlist[i],leplist[i]) for i in range(0,len(hadlist))])
        return totalwidth

    def NprodWidth(self):
        """
        Returns the total SUSYRPV neutralino production width
        """
        declist    = self.prods[self.bench]
        hadlist    = [re.search('(.+?)\ ->',dec).group(1) for dec in declist]
        leplist    = [dlist[1].strip() for dlist in [re.findall(r"\ \w+",dec) for dec in declist]]
        totalwidth = sum([self.Width_N_L(hadlist[i],leplist[i]) for i in range(0,len(hadlist))])
        return totalwidth


    def findDecayBranchingRatio(self, decayString):
        """
        Returns the branching ratio of the selected SUSY RPV neutralino decay channel

        Inputs:
        - decayString is a string describing the decay, in the form 'N -> stuff1 ... stuffN'
        """
        had        = re.search('->\ (.+?)\ ',decayString).group(1)
        decaysplit = decayString.split(' ')
        for split in decaysplit:
            if split.find('mu')>-1 or split.find('e')>-1 or split.find('tau')>-1:
                lep = split
        if had == 'pi+' or had == 'pi-' or had == 'pi0':
            print "findBranchingRatio() ERROR: Pions in final "\
                  "state have not been implemented, please choose "\
                  "a different decay mode of out...\n"
            print self.decays
            return -999
        
        corrdecstring = 'N -> %s %s'%(had,lep)
        listdecs      = self.decays[self.bench]
        gooddec       = False
        print "findBranchingRation() INFO: "\
              "You have chosen the decay: '",\
              corrdecstring
        for dec in listdecs:
            if corrdecstring in dec:
                gooddec = True
        if gooddec is False:
            print "findBranchingRation() ERROR: Badly "\
                  "formulated decay string, please choose "\
                  "one of the following\n"
            print self.decays
            return -999
                
        br = 0.
        totalwidth = self.NdecayWidth()
        if totalwidth > 0.0:
            br = self.Width_H_L(had,lep)/totalwidth
        return br


    def findProdBranchingRatio(self, decayString):
        """
        Returns the branching ratio of the selected SUSY RPV neutralino product channel

        Inputs:
        - decayString is a string describing the decay, in the form 'H -> N ... stuffN'
        """
        had    = re.search('(.+?)\ ->',decayString).group(1)
        decaysplit = decayString.split(' ')
        for split in decaysplit:
            if split.find('mu')>-1 or split.find('e')>-1 or split.find('tau')>-1:
                lep = split
        if had == 'pi+' or had == 'pi-' or had == 'pi0':
            print "findProdBranchingRatio() ERROR: Pions in final "\
                  "state have not been implemented, please choose "\
                  "a different decay mode of out...\n"
            print self.decays
            return -999
        
        corrdecstring = '%s -> N %s'%(had,lep)
        listdecs      = self.prods[self.bench]
        gooddec       = False
        print "findProdBranchingRation() INFO: "\
              "You have chosen the decay: '",\
              corrdecstring
        for dec in listdecs:
            if corrdecstring in dec:
                gooddec = True
        if gooddec is False:
            print "findProdBranchingRation() ERROR: Badly "\
                  "formulated decay string, please choose "\
                  "one of the following\n"
            print self.decays
            return -999
        
        br = self.Width_N_L(had,lep)/(self.Width_N_L(had,lep)+c.hGeV/lifetime(had))
        return br

class RPVSUSY(RPVSUSYbranchings):
    """
    SUSY RPV neutralino  physics according to the nuMSM
    """
    def __init__(self, mass, couplings, sfmass, benchmark, debug=False):
        """
        Initialize with mass and couplings of the HNL

        Inputs:
        mass (GeV)
        couplings (list of [\lambda_{production}^{2}, \lambda_{decay}^{2}])
        mass of universal sfermion
        which benchmark (integer between 1 and 5 inclusive)
        """
        RPVSUSYbranchings.__init__(self, mass, couplings, sfmass, benchmark, debug)
    def computeNLifetime(self,system="SI"):
        """
        Compute the RPV neutralino lifetime

        Inputs:
        - system: choose between default (i.e. SI, result in s) or FairShip (result in ns)
        """
        decwidth = self.NdecayWidth()  
        if decwidth == 0.0:
            return 0.0
        self.NLifetime = c.hGeV / decwidth
	if system == "FairShip": self.NLifetime *= 1.e9
        return self.NLifetime

