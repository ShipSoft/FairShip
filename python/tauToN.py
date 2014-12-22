"""
   Module to compute HNL production branching ratios
   for tau -> N X decays
   Author: Elena Graverini (elena.graverini@cern.ch)
   Last updated: 16/09/2014

"""


from __future__ import division
from scipy.integrate import quad
from array import array
from options import *

def phsp2bodyTauToN(pp):
    # Assuming the hadron is a pion
    MN = pp.MN
    MTau = pp.masses['tau']
    MPi = pp.masses['pi']
    if MN*(MN+2.*MPi) > (MTau**2. - MPi**2.):
        return 0.
    p1 = ( (1. - MN**2./MTau**2.)**2. - (MPi**2./MTau**2.)*(1. + MN**2./MTau**2.) )
    p2 = ( 1. - ( (MPi-MN)**2./MTau**2. ) )
    p3 = ( 1. - ( (MPi+MN)**2./MTau**2. ) )
    p4 = math.sqrt(p2*p3)
    return p1*p3

def phsp3bodyTauToN(EN, pp, lepton):
    MN = pp.MN
    if EN<MN:
        return 0.
    MTau = pp.masses['tau']
    ML = pp.masses[lepton]
    if EN>MTau-ML:
        return 0.
    #if EN > MTau/2.:
    #    return 0.
    p1 = ( 1. - ML**2./(MTau**2.+MN**2.-2.*EN*MTau) )**2.
    p2 = math.sqrt(EN**2. - MN**2.)
    p3 = (MTau-EN) * (1.- (MN**2.+ML**2.)/MTau**2.)
    p4 = ( 1.- ML**2./(MTau**2.+MN**2.-2.*EN*MTau) ) * ( (MTau-EN)**2./MTau + (EN**2.-MN**2.)/(3.*MTau) )
    #print EN, p1, p2, (p3-p4), p3, p4
    return math.fabs(p1*p2*(p3-p4))

def EMax3body(pp, lepton):
    MTau = pp.masses['tau']
    ML = pp.masses[lepton]
    MN = pp.MN
    PNMax = (0.5/MTau) * math.sqrt( (MTau**2. - (ML+MN)**2.) * (MTau**2. - (ML-MN)**2.) )
    ENMax = math.sqrt( MN**2. + PNMax**2. )
    return ENMax



def integrate3bodyTauToN(pp, lepton):
    EMin = pp.MN
    EMax = EMax3body(pp,lepton)
    if EMin >= EMax:
        return 0.
    integral = quad(phsp3bodyTauToN,
        EMin, EMax,
        args=(pp, lepton),
        full_output=True)
    return integral[0]

def brTauToPiN(pp):
    # Assuming the hadron is a pion
    if pp.MN >= (pp.masses['tau'] - pp.masses['pi']):
        return 0.
    const = (pp.tauTau/pp.hGeV) * pp.U2[2] * pp.GF**2. * pp.CKM.Vud**2. * pp.fpi**2. * pp.masses['tau']**3. * (1./(16.*math.pi))
    ps = phsp2bodyTauToN(pp)
    return const*ps*2.  # Generally speaking, I'm taking just half of the tau decays

def brTauToNuEllN(pp, lepton):
    if pp.MN >= (pp.masses['tau'] - pp.masses[lepton]):
        return 0.
    const = (pp.tauTau/pp.hGeV) * pp.U2[2] * pp.GF**2. * pp.masses['tau']**2. * (1./(4.*math.pi**3.))
    ps = integrate3bodyTauToN(pp, lepton)
    return const*ps*2. # Generally speaking, I'm taking just half of the tau decays



cSaver = []


if __name__ == '__main__':
    pp = physicsParameters()
    pp.setNCoupling([0.02e-8,0.25e-8,1.e-8])
    #m = np.linspace(0,pp.masses[pp.name2particle['tau']]-pp.masses[pp.name2particle['e']],100).tolist()
    m = np.logspace(-3., math.log10(pp.masses[pp.name2particle['tau']]-pp.masses[pp.name2particle['e']]), 100).tolist()
    bre3, brmu3, brpi2, sumFromTau, brFromMu, brFromE = [], [], [], [], [], []
    #m.remove(m[0])
    m.remove(m[-1])
    for mass in m:
        pp.setNMass(mass)
        pp.setNCoupling([0.02e-8,0.25e-8,1.e-8])
        adj = (pp.nDs/pp.nTotCharm)*0.0543 #br(Ds->taunu)
        bre3.append(brTauToNuEllN(pp,'e')*adj)
        brmu3.append(brTauToNuEllN(pp,'mu')*adj)
        brpi2.append(brTauToPiN(pp)*adj)
        sumFromTau.append(adj*(brTauToPiN(pp)+brTauToNuEllN(pp,'e')+brTauToNuEllN(pp,'mu')))
        pp.setNCoupling([(0.25*0.25)*1.e-8,1.e-8,0.25e-8])
        pp.computeProductionWeights('mu')
        adj = (pp.nDs + (pp.nD+pp.nD0)*pp.w3body['mu']) / pp.nTotCharm
        brFromMu.append(pp.computeNProdBR(1)*adj)
        pp.setNCoupling([1.e-8,0.02e-8,0.02e-8])
        pp.computeProductionWeights('e')
        adj = (pp.nDs + (pp.nD+pp.nD0)*pp.w3body['e']) / pp.nTotCharm
        brFromE.append(pp.computeNProdBR(0)*adj)
    gre3 = r.TGraph(len(m), array('f',m), array('f',bre3))
    grmu3 = r.TGraph(len(m), array('f',m), array('f',brmu3))
    grpi2 = r.TGraph(len(m), array('f',m), array('f',brpi2))
    gre = r.TGraph(len(m), array('f',m), array('f',brFromE))
    grmu = r.TGraph(len(m), array('f',m), array('f',brFromMu))
    grtau = r.TGraph(len(m), array('f',m), array('f',sumFromTau))
    grtau.SetLineColor(r.kPink-9)
    grtau.SetMarkerColor(r.kPink-9)
    gre3.SetLineColor(r.kRed)
    grmu3.SetLineColor(r.kBlue)
    gre.SetLineColor(r.kMagenta+3)
    grmu.SetLineColor(r.kMagenta+3)
    gre.SetLineWidth(2)
    grmu.SetLineWidth(2)
    grtau.SetLineWidth(2)
    gre.SetMarkerColor(r.kMagenta+3)
    grmu.SetMarkerColor(r.kMagenta+3)
    gre.SetLineStyle(2)
    grmu.SetLineStyle(9)
    grpi2.SetLineColor(r.kBlack)
    gre3.SetMarkerColor(r.kRed)
    grmu3.SetMarkerColor(r.kBlue)
    grpi2.SetMarkerColor(r.kBlack)
    gre3.SetLineWidth(2)
    grmu3.SetLineWidth(2)
    grpi2.SetLineWidth(2)
    mgr = r.TMultiGraph()
    mgr.SetTitle('HNL production from #tau flavour')
    mgr.Add(gre3)
    mgr.Add(grmu3)
    mgr.Add(grpi2)
    mgr.Add(grtau)
    mgr.Add(gre)
    mgr.Add(grmu)
    c1 = r.TCanvas()
    cSaver.append(c1)
    c1.SetLogy()
    c1.SetLogx()
    c1.SetGrid()
    mgr.Draw('alp')
    mgr.GetXaxis().SetTitle('HNL mass (GeV)')
    mgr.GetXaxis().SetRangeUser(0.01,1.77)
    mgr.GetYaxis().SetTitle('Production BR')
    mgr.GetYaxis().SetRangeUser(1.e-14,1.e-9)
    mgr.GetXaxis().CenterTitle()
    mgr.GetXaxis().SetTitleSize(0.06)
    mgr.GetXaxis().SetTitleOffset(0.79)
    mgr.GetYaxis().CenterTitle()
    mgr.GetYaxis().SetTitleSize(0.06)
    mgr.GetYaxis().SetTitleOffset(0.78)
    leg = r.TLegend(0.33,0.1,0.63,0.38)
    leg.SetFillColor(r.kWhite)
    leg.AddEntry(grpi2,'#tau #rightarrow #pi N','lp')
    leg.AddEntry(gre3,'#tau #rightarrow e #nu_{e} N','lp')
    leg.AddEntry(grmu3,'#tau #rightarrow #mu #nu_{#mu} N','lp')
    leg.AddEntry(grtau,'U_{#tau} production','lp')
    leg.AddEntry(gre,'U_{e} production','lp')
    leg.AddEntry(grmu,'U_{#mu} production','lp')
    leg.SetTextSize(0.048)
    leg.Draw()
    c1.Modified()
    c1.Update()







































#def integrate3bodyTauToN(pp, lepton, nToys=1000):
#    #### Setting up the parameters for generation
#    MN = pp.MN
#    ML = pp.masses[pp.name2particle[lepton]]
#    MTau = pp.masses[pp.name2particle['tau']]
#    pTau = r.TLorentzVector(0., 0., 0., MTau)
#    masses = array('d', [0., ML, MN])
#    event = r.TGenPhaseSpace()
#    event.SetDecay(pTau, 3, masses)
#    
#    Nq2 = 20 
#    NEN = 20
#    ENMax = (mH-mh)
#    ENMax =  r.TMath.Sqrt(((ENMax**2-ml**2-mN**2)/2.)**2+mN**2)
#    hist = r.TH2F("hist", "", Nq2, (ml+mN)**2, (mH-mh)**2, NEN, mN, ENMax)
#
#    ###### Integral
#    Integral = 0.
#
#    #### For loop in order to integrate
#    for i in xrange(nToys):
#        event.Generate()
#        #### Getting momentum of the daughters
#        ph = event.GetDecay(0)
#        pN    = event.GetDecay(1)
#        pl    = event.GetDecay(2)
#        #### Computing the parameters to compute the phase space
#        q = pl+pN
#        q2 = q.M2()
#        EN = pN.E()
#
#        iBin = hist.Fill(q2, EN)
#        
#        if hist.GetBinContent(iBin)==1.:
#            val = PhaseSpace3Body(q2, EN, mH, mh, mN, ml)
#            Integral+=val*hist.GetXaxis().GetBinWidth(1)*hist.GetYaxis().GetBinWidth(1)
#
#    hist.Delete()
#    return {'Int':Integral, "PHSP":hist}
#    pass
