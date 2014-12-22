"""

    Module to compute HNLs production branching ratios
    for charm and beauty meson decays
    Author: Elena Graverini (elena.graverini@cern.ch)
    Last updated: 16/09/2014

"""

from __future__ import division
from options import *

indx = {'e':0, 'mu':1, 'tau':2}

def BR2Body(pp, meson, lepton):
    if meson == 'B':
        MH = pp.masses['B']
        V = pp.CKM.Vub
        tau = pp.tauB
        f = pp.fB
    elif meson == 'Ds':
        MH = pp.masses['Ds']
        V = pp.CKM.Vcs
        tau = pp.tauDs
        f = pp.fDs
    else:
        print 'BR2Body: select B or Ds!'
        sys.exit(-1)
    alpha = indx[lepton]
    phsp = pp.phsp2body(MH, pp.MN, pp.masses[lepton])
    const = (tau/pp.hGeV) * pp.GF**2. * f**2. * MH * pp.MN**2. * pp.U2[alpha] * V**2. / (8. * math.pi)
    br = phsp*const*2. #majorana -> x2
    return br

def BR3Body(pp, meson, lepton): #only pseudoscalar into pseudoscalars (no B -> D* l N)
    alpha = indx[lepton]
    if meson == 'B' or meson == 'B0' or meson == 'Bs':
        V = pp.CKM.Vcb
    elif meson == 'D' or meson == 'D0':
        V = pp.CKM.Vcs
    if meson == 'B':
        MH = pp.masses['B']
        Mh = pp.masses['D0']
        tau = pp.tauB
        family = 'B'
    elif meson == 'B0':
        MH = pp.masses['B0']
        Mh = pp.masses['D']
        tau = pp.tauB0
        family = 'B'
    elif meson == 'Bs':
        MH = pp.masses['Bs']
        Mh = pp.masses['Ds']
        tau = pp.tauBs
        family = 'Bs'
    elif meson == 'D':
        MH = pp.masses['D']
        Mh = pp.masses['K0']
        tau = pp.tauD
        family = 'D'
    elif meson == 'D0':
        MH = pp.masses['D0']
        Mh = pp.masses['K']
        tau = pp.tauD0
        family = 'D'
    else:
        print 'BR3Body: unknown meson!'
        sys.exit(-1)
    phsp = pp.Integrate3Body(family, MH, Mh, pp.MN, pp.masses[lepton], nToys=300)
    #print 'Phase space is: %s'%phsp
    const = (tau/pp.hGeV) * pp.U2[alpha] * V**2. * pp.GF**2. / (64. * math.pi**3. * MH**2.)
    br = phsp*const*2.*2. #majorana -> x2, vector channels -> x2
    return br


if __name__ == '__main__':
    pp = physicsParameters()
    couplings = [(0.25*0.25)*1.e-8,1.e-8,0.25e-8]
    pp.setNCoupling(couplings)
    pp.setNMass(0.5)
    
    masses = np.linspace(0.5,4.,50).tolist()
    from array import array
    brD2, brD3, brB2, brB3, brBs3, brSum = [], [], [], [], [], []
    for mass in masses:
        pp.setNMass(mass)
        brB2.append(BR2Body(pp,'B','mu')*pp.Xbb)
        brB3.append(BR3Body(pp,'B','mu')*((pp.nB+pp.nB0)/(pp.nB+pp.nB0+pp.nBs))*pp.Xbb)
        brBs3.append(BR3Body(pp,'Bs','mu')*(pp.nBs/(pp.nB+pp.nB0+pp.nBs))*pp.Xbb)
        brD3.append(BR3Body(pp,'D','mu')*((pp.nD0 + pp.nD)/(pp.nDs+pp.nD0+pp.nD))*pp.Xcc)
        #brD2.append(pp.computeNProdBR(1)*(pp.nDs/(pp.nDs+pp.nD0+pp.nD))*pp.Xcc)
        brD2.append(BR2Body(pp,'Ds','mu')*(pp.nDs/(pp.nDs+pp.nD0+pp.nD))*pp.Xcc)
        brSum.append(BR3Body(pp,'B','mu')*pp.Xbb
            +BR2Body(pp,'B','mu')*((pp.nB+pp.nB0)/(pp.nB+pp.nB0+pp.nBs))*pp.Xbb
            +BR3Body(pp,'Bs','mu')*(pp.nBs/(pp.nB+pp.nB0+pp.nBs))*pp.Xbb
            +BR3Body(pp,'D','mu')*((pp.nD0 + pp.nD)/(pp.nDs+pp.nD0+pp.nD))*pp.Xcc
            #+pp.computeNProdBR(1)*(pp.nDs/(pp.nDs+pp.nD0+pp.nD))*pp.Xcc
            +BR2Body(pp,'Ds','mu')*(pp.nDs/(pp.nDs+pp.nD0+pp.nD))*pp.Xcc)
    massesr = array('f',masses)
    brB2r = array('f',brB2)
    brB3r = array('f',brB3)
    brBs3r = array('f',brBs3)
    brD2r = array('f',brD2)
    brD3r = array('f',brD3)
    brSr = array('f',brSum)
    grB2 = r.TGraph(len(masses),massesr,brB2r)
    grB3 = r.TGraph(len(masses),massesr,brB3r)
    grBs3 = r.TGraph(len(masses),massesr,brBs3r)
    grD2 = r.TGraph(len(masses),massesr,brD2r)
    grD3 = r.TGraph(len(masses),massesr,brD3r)
    grS = r.TGraph(len(masses),massesr,brSr)
    grB2.SetLineColor(r.kRed)
    grB3.SetLineColor(r.kBlue)
    grBs3.SetLineColor(r.kViolet)
    grD2.SetLineColor(r.kOrange)
    grD3.SetLineColor(r.kGreen)
    grS.SetLineColor(r.kBlack)
    grB2.SetMarkerColor(r.kRed)
    grB3.SetMarkerColor(r.kBlue)
    grBs3.SetMarkerColor(r.kViolet)
    grD2.SetMarkerColor(r.kOrange)
    grD3.SetMarkerColor(r.kGreen)
    grS.SetMarkerColor(r.kBlack)
    grB2.SetLineWidth(2)
    grB3.SetLineWidth(2)
    grBs3.SetLineWidth(2)
    grD2.SetLineWidth(2)
    grD3.SetLineWidth(2)
    grS.SetLineWidth(2)
    grS.SetLineStyle(7)
    mgr = r.TMultiGraph()
    mgr.SetTitle('HNL production in SHiP (U^{2}=%s)'%couplings)
    mgr.Add(grB2)
    mgr.Add(grB3)
    mgr.Add(grBs3)
    mgr.Add(grD2)
    mgr.Add(grD3)
    mgr.Add(grS)
    c1 = r.TCanvas()
    c1.SetLogy()
    mgr.Draw('alp')
    mgr.GetXaxis().SetTitle('HNL mass (GeV)')
    mgr.GetYaxis().SetRangeUser(1.e-20,1.e-12)
    leg = r.TLegend(0.5,0.5211,0.8793,0.8814)
    leg.AddEntry(grD2,'BR(D_{s}#rightarrow#muN) #times #chi_{D_{s}}','lp')
    leg.AddEntry(grD3,'BR(D#rightarrowK#muN) #times #chi_{D}','lp')
    leg.AddEntry(grB2, 'BR(B#rightarrow#muN) #times #chi_{bb}','lp')
    leg.AddEntry(grB3,'BR(B#rightarrowD#muN) #times #chi_{B}','lp')
    leg.AddEntry(grBs3,'BR(B_{s}#rightarrowD_{s}#muN) #times #chi_{B_{s}}','lp')
    leg.AddEntry(grS,'Total N production','lp')
    leg.SetFillColor(r.kWhite)
    leg.Draw()
    c1.Update()
    
