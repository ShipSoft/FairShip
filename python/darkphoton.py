import math
import os
#from scipy import interpolate 
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

def readPDGtable():
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
                if 'EXCLSUM' in strType:
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

dataEcm,dataR = readPDGtable()

def interpolatePDGtable():
    """ Find the best value for R for the given center-of-mass energy """
    #using scipy
    #fun = interpolate.interp1d(dataEcm,dataR)
    #using ROOT
    fun = r.Math.Interpolator(dataEcm.size(),r.Math.Interpolation.kLINEAR) #,Interpolation.kPOLYNOMIAL)
    print 'function type:%s'%fun.Type()
    fun.SetData(dataEcm,dataR);
    return fun

def Ree_interp(s): # s in GeV
    """ Using PDG values for sigma(e+e- -> hadrons) / sigma(e+e- -> mu+mu-) """
    # Da http://pdg.lbl.gov/2012/hadronic-xsections/hadron.html#miscplots
    #ecm = math.sqrt(s)
    ecm = s
    if ecm>=4.8:
        print 'Asking for interpolation beyond 4.8 GeV: not implemented, needs extending!'
        result=0
    elif ecm>=dataEcm[0]:
        result = float(PdgR.Eval(ecm))
    else:
        result=0
    #print 'Ree_interp for mass %3.3f is %.3e'%(s,result)
    return result

def leptonicDecayWidth(mDarkPhoton, epsilon, lepton): # mDarkPhoton in GeV
    """ Dark photon decay width into leptons, in GeV (input short name of lepton family) """
    ml = mass(lepton)
    #print 'lepton %s mass %.3e'%(lepton,ml)
    
    #ml = ml/1000. # all in GeV
    constant = (1./3.) * alphaQED * mDarkPhoton * pow(epsilon, 2.)
    if 2.*ml < mDarkPhoton:
        rad = math.sqrt( 1. - (4.*ml*ml)/(mDarkPhoton*mDarkPhoton) )
    else:
        rad = 0.

    par = 1. + (2.*ml*ml)/(mDarkPhoton*mDarkPhoton)
    tdw=math.fabs(constant*rad*par)
    #print 'Leptonic decay width to %s is %.3e'%(lepton,tdw)
    return tdw
    
def leptonicBranchingRatio(mDarkPhoton, epsilon, lepton):
    return leptonicDecayWidth(mDarkPhoton, epsilon, lepton) / totalDecayWidth(mDarkPhoton, epsilon)
    #if lepton == e:
    #   otherlepton = mu
    #   br = 1. - ((leptonicDecayWidth(mDarkPhoton, epsilon, otherlepton) + hadronicDecayWidth(mDarkPhoton, epsilon))/totalDecayWidth(mDarkPhoton, epsilon))
    #else: 
    #   br = leptonicDecayWidth(mDarkPhoton, epsilon, lepton) / totalDecayWidth(mDarkPhoton, epsilon)
    #return br
        
def hadronicDecayWidth(mDarkPhoton, epsilon):
    """ Dark photon decay into hadrons """
    """(mumu)*R"""
    gmumu=leptonicDecayWidth(mDarkPhoton, epsilon, 'mu')
    tdw=gmumu*Ree_interp(mDarkPhoton)
    #print 'Hadronic decay width is %.3e'%(tdw)
    return tdw;
        
def hadronicBranchingRatio(mDarkPhoton, epsilon):
    return hadronicDecayWidth(mDarkPhoton, epsilon) / totalDecayWidth(mDarkPhoton, epsilon)
        
def totalDecayWidth(mDarkPhoton, epsilon): # mDarkPhoton in GeV
    """ Total decay width in GeV """
    #return hGeV*c / cTau(mDarkPhoton, epsilon)
    tdw = (leptonicDecayWidth(mDarkPhoton, epsilon, 'e')
           + leptonicDecayWidth(mDarkPhoton, epsilon, 'mu')
           + leptonicDecayWidth(mDarkPhoton, epsilon, 'tau')
           + hadronicDecayWidth(mDarkPhoton, epsilon))

    #print 'Total decay width %e'%(tdw)

    return tdw
    #if Ree_const in vars():
    #   return 3./((1.+Ree_const)*alphaQED*mDarkPhoton*pow(epsilon,2.))
    #else:
    #   return 3./((1.+Ree_interp(mDarkPhoton))*alphaQED*mDarkPhoton*pow(epsilon,2.))
        
        
def scaleNEventsIncludingHadrons(mDarkPhoton, epsilon, n):
    """ Very simple patch to take into account A' -> hadrons """
    brh = hadronicBranchingRatio(mDarkPhoton, epsilon)
    #print brh
    # if M > m(c cbar):
    if mDarkPhoton > 2.*mass('c'):
        visible_frac = 1.
    else:
        visible_frac = 2./3.
    
    increase = brh*visible_frac
    #print increase
    return n*(1. + increase)
            
            
def cTau(mDarkPhoton, epsilon): # decay length in meters, dark photon mass in GeV
    """ Dark Photon lifetime in cm"""
    ctau=hGeV*ccm/totalDecayWidth(mDarkPhoton, epsilon)
    #print "ctau dp.py %.3e"%(ctau) 
    #p1 = 0.8 / (1. + Ree_interp(mDarkPhoton))
    #p2 = pow((pow(10., -6.) / epsilon),2.)
    #p3 = 100. / (mDarkPhoton*1000.)
    #ctau=p1*p2*p3
    return ctau #GeV/MeV conversion
            
def lifetime(mDarkPhoton, epsilon):
    return cTau(mDarkPhoton, epsilon)/ccm
            
#def Ree(s): # s in MeV
#   """ sigma(e+e- -> hadrons) / sigma(e+e- -> mu+mu-) """
#   if s > 2.*mt:
#       ratio = ncol*(qu*qu + qd*qd + qc*qc + qs*qs + qb*qb + qt*qt)
#   elif s > 2.*mb:
#       ratio = ncol*(qu*qu + qd*qd + qc*qc + qs*qs + qb*qb)
#   elif s > 2.*mc:
#       ratio = ncol*(qu*qu + qd*qd + qc*qc + qs*qs)
#   elif s > 2.*ms:
#       ratio = ncol*(qu*qu + qd*qd + qs*qs)
#   elif s > 2.*md:
#       ratio = ncol*(qu*qu + qd*qd)
#   elif s > 2.*mu:
#       ratio = ncol*(qu*qu)
#   else:
#       ratio = 0


def allowedChannels(mDarkPhoton):
    print "Allowed channels for dark photon mass = %3.3f"%mDarkPhoton
    allowedDecays = {'A -> hadrons':'yes'}
    if mDarkPhoton > 2.*mass('e'):
        allowedDecays.update({'A -> e- e+':'yes'})
        print "allowing decay to e"
    if mDarkPhoton > 2.*mass('mu'):
        allowedDecays.update({'A -> mu- mu+':'yes'})
        print "allowing decay to mu"
    if mDarkPhoton > 2.*mass('tau'):
        allowedDecays.update({'A -> tau- tau+':'yes'})
        print "allowing decay to tau"
                        
    return allowedDecays
                    
                            
                            
def findBranchingRatio(mDarkPhoton,epsilon,decayString):
    br = 0.
    if   decayString == 'A -> e- e+': br = leptonicBranchingRatio(mDarkPhoton, epsilon, 'e')
    elif   decayString == 'A -> mu- mu+': br = leptonicBranchingRatio(mDarkPhoton, epsilon, 'mu')
    elif   decayString == 'A -> tau- tau+': br = leptonicBranchingRatio(mDarkPhoton, epsilon, 'tau')
    elif   decayString == 'A -> hadrons': br = hadronicBranchingRatio(mDarkPhoton, epsilon)
    else:
        print 'findBranchingRatio ERROR: unknown decay %s'%decayString
        quit()
        
    return br

