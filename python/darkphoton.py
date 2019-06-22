import math
import os
import ROOT as r

#from settings import *
#from functions import *
from hnl import mass
from hnl import PDGname

# constants
alphaQED = 1./137.
ccm = 2.99792458e+10
hGeV = 6.58211928*pow(10.,-16)* pow(10.,-9) # no units or it messes up!!

#utilities
# sigma(e+e- -> hadrons) / sigma(e+e- -> mu+mu-)

class DarkPhoton:
    "dark photon setup"
    
    def __init__(self, mass, eps):
        self.mDarkPhoton = mass
        self.epsilon = eps
        self.dataEcm,self.dataR = self.readPDGtable()
        self.PdgR = self.interpolatePDGtable()

    def readPDGtable(self):
        """ Returns R data from PDG in a easy to use format """
        ecm=r.vector('double')()
        ratio=r.vector('double')()
        """ecm,ratio = [],[]"""
        with open(os.path.expandvars('$FAIRSHIP/input/rpp2012-hadronicrpp_page1001.dat'),'r') as f:
            for line in f:
                line = line.split()
                try:
                    numEcm = float(line[0])
                    numR = float(line[3])
                    strType = line[7]
                    strBis = line[8]
                    #if numEcm<2:
                    #   print numEcm,numR,strType
                    if (('EXCLSUM' in strType) or ('EDWARDS' in strType) or ('BLINOV' in strType)):
                        ecm.push_back(numEcm)
                        ratio.push_back(numR)
                        #print numEcm,numR,strType
                    if 'BAI' in strType and '01' in strBis:
                        ecm.push_back(numEcm)
                        ratio.push_back(numR)
                        #print numEcm,numR,strType
                except:
                    continue
        return ecm,ratio


    def interpolatePDGtable(self):
        """ Find the best value for R for the given center-of-mass energy """
        fun = r.Math.Interpolator(self.dataEcm.size(),r.Math.Interpolation.kLINEAR)
        fun.SetData(self.dataEcm,self.dataR);
        return fun

    def Ree_interp(self,s): # s in GeV
        """ Using PDG values for sigma(e+e- -> hadrons) / sigma(e+e- -> mu+mu-) """
        # Da http://pdg.lbl.gov/2012/hadronic-xsections/hadron.html#miscplots
        #ecm = math.sqrt(s)
        ecm = s
        if ecm>=10.29:
            print 'Warning! Asking for interpolation beyond 10.29 GeV: not implemented, needs extending! Taking value at 10.29 GeV'
            result=float(self.PdgR.Eval(10.29))
        elif ecm>=self.dataEcm[0]:
            result = float(self.PdgR.Eval(ecm))
        else:
            result=0
        #print 'Ree_interp for mass %3.3f is %.3e'%(s,result)
        return result

    def leptonicDecayWidth(self,lepton): # mDarkPhoton in GeV
        """ Dark photon decay width into leptons, in GeV (input short name of lepton family) """
        ml = mass(lepton)
        #print 'lepton %s mass %.3e'%(lepton,ml)
        
        constant = (1./3.) * alphaQED * self.mDarkPhoton * pow(self.epsilon, 2.)
        if 2.*ml < self.mDarkPhoton:
            rad = math.sqrt( 1. - (4.*ml*ml)/(self.mDarkPhoton*self.mDarkPhoton) )
        else:
            rad = 0.
            
        par = 1. + (2.*ml*ml)/(self.mDarkPhoton*self.mDarkPhoton)
        tdw=math.fabs(constant*rad*par)
        #print 'Leptonic decay width to %s is %.3e'%(lepton,tdw)
        return tdw
    
    def leptonicBranchingRatio(self,lepton):
        return self.leptonicDecayWidth(lepton) / self.totalDecayWidth()
        
    def hadronicDecayWidth(self):
        """ Dark photon decay into hadrons """
        """(mumu)*R"""
        gmumu=self.leptonicDecayWidth('mu-')
        tdw=gmumu*self.Ree_interp(self.mDarkPhoton)
        #print 'Hadronic decay width is %.3e'%(tdw)
        return tdw;
    
    def hadronicBranchingRatio(self):
        return self.hadronicDecayWidth() / self.totalDecayWidth()
    
    def totalDecayWidth(self): # mDarkPhoton in GeV
        """ Total decay width in GeV """
        #return hGeV*c / cTau(mDarkPhoton, epsilon)
        tdw = (self.leptonicDecayWidth('e-')
               + self.leptonicDecayWidth('mu-')
               + self.leptonicDecayWidth('tau-')
               + self.hadronicDecayWidth())
        
        #print 'Total decay width %e'%(tdw)
        
        return tdw

    def cTau(self): # decay length in meters, dark photon mass in GeV
        """ Dark Photon lifetime in cm"""
        ctau=hGeV*ccm/self.totalDecayWidth()
        #print "ctau dp.py %.3e"%(ctau) 
        return ctau #GeV/MeV conversion
    
    def lifetime(self):
        return cTau()/ccm

    def findBranchingRatio(self,decayString):
        br = 0.
        if   decayString == 'A -> e- e+': br = self.leptonicBranchingRatio('e-')
        elif   decayString == 'A -> mu- mu+': br = self.leptonicBranchingRatio('mu-')
        elif   decayString == 'A -> tau- tau+': br = self.leptonicBranchingRatio('tau-')
        elif   decayString == 'A -> hadrons': br = self.hadronicBranchingRatio()
        else:
            print 'findBranchingRatio ERROR: unknown decay %s'%decayString
            quit()
            
        return br

    def allowedChannels(self):
        print "Allowed channels for dark photon mass = %3.3f"%self.mDarkPhoton
        allowedDecays = {'A -> hadrons':'yes'}
        if self.mDarkPhoton > 2.*mass('e-'):
            allowedDecays.update({'A -> e- e+':'yes'})
            print "allowing decay to e"
        if self.mDarkPhoton > 2.*mass('mu-'):
            allowedDecays.update({'A -> mu- mu+':'yes'})
            print "allowing decay to mu"
        if self.mDarkPhoton > 2.*mass('tau-'):
            allowedDecays.update({'A -> tau- tau+':'yes'})
            print "allowing decay to tau"
                        
        return allowedDecays
                    
                            
    def scaleNEventsIncludingHadrons(self,n):
        """ Very simple patch to take into account A' -> hadrons """
        brh = self.hadronicBranchingRatio()
        #print brh
        # if M > m(c cbar):
        if self.mDarkPhoton > 2.*mass('c'):
            visible_frac = 1.
        else:
            visible_frac = 2./3.
    
        increase = brh*visible_frac
        #print increase
        return n*(1. + increase)
            
            
