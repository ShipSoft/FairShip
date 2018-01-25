#!/usr/bin/env python2
import argparse
import numpy as np
import ROOT as r
# Fix https://root-forum.cern.ch/t/pyroot-hijacks-help/15207 :
r.PyConfig.IgnoreCommandLineOptions = True
import shipunit as u
import rootUtils as ut


def main():
    parser = argparse.ArgumentParser(description='Script to create flux maps.')
    parser.add_argument(
        'inputfile',
        help='''Simulation results to use as input. '''
        '''Supports retrieving files from EOS via the XRootD protocol.''')
    parser.add_argument(
        'geofile',
        help='''Geometry file to use. '''
        '''Supports retrieving files from EOS via the XRootD protocol.''')
    parser.add_argument(
        '-o',
        '--outputfile',
        default='flux_map.root',
        help='''File to write the flux maps to. '''
        '''Will be recreated if it already exists.''')
    args = parser.parse_args()
    g = r.TFile.Open(args.geofile, 'read')
    sGeo = g.FAIRGeom
    f = r.TFile.Open(args.outputfile, 'recreate')
    f.cd()
    maxpt = 10. * u.GeV
    maxp = 360. * u.GeV
    h = {}

    # Define histograms
    for suffix, title in [('mu', '#mu#pm hits'), ('all', 'All hits')]:
        ut.bookHist(h, 'muon_tiles_{}'.format(suffix),
                    '{};x[cm];y[cm]'.format(title), 200, -1000, +1000, 90,
                    -900, 900)
        ut.bookHist(h, 'muon_bars_x_{}'.format(suffix),
                    '{};x[cm];y[cm]'.format(title), 2, -300, +300, 240, -600,
                    600)
        ut.bookHist(h, 'muon_bars_y_{}'.format(suffix),
                    '{};x[cm];y[cm]'.format(title), 120, -300, +300, 4, -600,
                    600)
        ut.bookHist(h, 'timing_{}'.format(suffix),
                    '{};x[cm];y[cm]'.format(title), 3, -252, +252, 167, -501,
                    501)
        ut.bookHist(h, 'UVT_{}'.format(suffix), '{};x[cm];y[cm]'.format(title),
                    100, -300, +300, 100, -300, 300)
        ut.bookHist(h, 'NuTauMu_{}'.format(suffix), '{};x[cm];y[cm]'.format(title),
                    100, -300, +300, 100, -300, 300)
        ut.bookHist(h, 'ECAL_TP_{}'.format(suffix),
                    '{};x[cm];y[cm]'.format(title), 167, -501, +501, 334,
                    -1002, 1002)
        ut.bookHist(h, 'ECAL_Alt_{}'.format(suffix),
                    '{};x[cm];y[cm]'.format(title), 50, -500, +500, 100, -1000,
                    1000)
        ut.bookHist(h, 'SBT_Liquid_{}'.format(suffix), '{};z[cm];#phi'.format(title),
                    100, -3000, +3000, 100, -r.TMath.Pi(), r.TMath.Pi())
        ut.bookHist(h, 'SBT_Plastic_{}'.format(suffix), '{};z[cm];#phi'.format(title),
                    100, -3000, +3000, 100, -r.TMath.Pi(), r.TMath.Pi())
        for station in range(1, 6):
            ut.bookHist(h, 'T{}_{}'.format(station, suffix),
                        '{};x[cm];y[cm]'.format(title), 10, -250, +250, 20,
                        -500, 500)
    for suffix in ['', '_original']:
        ut.bookHist(h, 'mu_p{}'.format(suffix), '#mu#pm;p[GeV];', 100, 0, maxp)
        ut.bookHist(h, 'mu_pt{}'.format(suffix), '#mu#pm;p_t[GeV];', 100, 0,
                    maxpt)
        ut.bookHist(h, 'mu_ppt{}'.format(suffix), '#mu#pm;p[GeV];p_t[GeV];',
                    100, 0, maxp, 100, 0, maxpt)
    ut.bookHist(h, 'smear', '#mu#pm initial vertex;x[cm];y[cm]', 100, -10, +10,
                100, -10, 10)
    ut.bookHist(h, 'ECAL_TP_e', 'e#pm with E#geq 250 MeV;x[cm];y[cm]', 167,
                -501, +501, 334, -1002, 1002)
    ut.bookHist(h, 'ECAL_Alt_e', 'e#pm with E#geq 250 MeV;x[cm];y[cm]', 50,
                -500, +500, 100, -1000, 1000)
    ut.bookHist(h, 'ECAL_TP_gamma', '#gamma;x[cm];y[cm]', 167, -501, +501, 334,
                -1002, 1002)
    ut.bookHist(h, 'ECAL_Alt_gamma', '#gamma;x[cm];y[cm]', 50, -500, +500, 100,
                -1000, 1000)
    ut.bookHist(h, 'ECAL_e_E', 'e#pm;E[GeV/c^{2}];', 100, 0, 1)
    ut.bookHist(h, 'ECAL_gamma_E', '#gamma;E[GeV/c^{2}];', 100, 0, 1)
    ch = r.TChain('cbmsim')
    ch.Add(args.inputfile)
    n = ch.GetEntries()
    print n
    i = 0
    for event in ch:
        if i % 10000 == 0:
            print '{}/{}'.format(i, n)
        i += 1
        muon = False
        original_muon = event.MCTrack[1]
        try:
            h['smear'].Fill(original_muon.GetStartX(),
                            original_muon.GetStartY())
        except AttributeError:
            continue
        weight = original_muon.GetWeight()
        if weight == 0:
            weight = 1.
        for hit in event.strawtubesPoint:
            if hit:
                if not hit.GetEnergyLoss() > 0:
                    continue
                x = hit.GetX()
                y = hit.GetY()
                z = hit.GetZ()
                px = hit.GetPx()
                py = hit.GetPy()
                pz = hit.GetPz()
                pt = np.hypot(px, py)
                P = np.hypot(pz, pt)
                pid = hit.PdgCode()
                assert pid not in [12, -12, 14, -14, 16, -16]
                detector_ID = hit.GetDetectorID()
                station = detector_ID / 10000000
                h['T{}_all'.format(station)].Fill(x, y, weight)
                if abs(pid) == 13:
                    muon = True
                    h['T{}_mu'.format(station)].Fill(x, y, weight)
                    h['mu_p'].Fill(P, weight)
                    h['mu_pt'].Fill(pt, weight)
                    h['mu_ppt'].Fill(P, pt, weight)
        for hit in event.EcalPoint:
            if hit:
                if not hit.GetEnergyLoss() > 0:
                    continue
                x = hit.GetX()
                y = hit.GetY()
                px = hit.GetPx()
                py = hit.GetPy()
                pz = hit.GetPz()
                pt = np.hypot(px, py)
                P = np.hypot(pz, pt)
                pid = hit.PdgCode()
                if pid in [12, -12, 14, -14, 16, -16]:
                    continue
                h['ECAL_TP_all'].Fill(x, y, weight)
                h['ECAL_Alt_all'].Fill(x, y, weight)
                if abs(pid) == 13:
                    muon = True
                    h['mu_p'].Fill(P, weight)
                    h['mu_pt'].Fill(pt, weight)
                    h['mu_ppt'].Fill(P, pt, weight)
                    h['ECAL_TP_mu'].Fill(x, y, weight)
                    h['ECAL_Alt_mu'].Fill(x, y, weight)
                elif abs(pid) == 11:
                    Esq = px**2 + py**2 + pz**2 + 0.000511**2
                    h['ECAL_e_E'].Fill(np.sqrt(Esq), weight)
                    h['ECAL_TP_e'].Fill(x, y, weight)
                    h['ECAL_Alt_e'].Fill(x, y, weight)
                elif abs(pid) == 22:
                    Esq = px**2 + py**2 + pz**2
                    h['ECAL_gamma_E'].Fill(np.sqrt(Esq), weight)
                    h['ECAL_TP_gamma'].Fill(x, y, weight)
                    h['ECAL_Alt_gamma'].Fill(x, y, weight)
        for hit in event.ShipRpcPoint:
            if hit:
                if not hit.GetEnergyLoss() > 0:
                    continue
                x = hit.GetX()
                y = hit.GetY()
                z = hit.GetZ()
                px = hit.GetPx()
                py = hit.GetPy()
                pz = hit.GetPz()
                pt = np.hypot(px, py)
                P = np.hypot(pz, pt)
                pid = hit.PdgCode()
                assert pid not in [12, -12, 14, -14, 16, -16]
                h['NuTauMu_all'].Fill(x, y, weight)
                if abs(pid) == 13:
                    muon = True
                    h['mu_p'].Fill(P, weight)
                    h['mu_pt'].Fill(pt, weight)
                    h['mu_ppt'].Fill(P, pt, weight)
                    h['NuTauMu_mu'].Fill(x, y, weight)
        for hit in event.muonPoint:
            if hit:
                if not hit.GetEnergyLoss() > 0:
                    continue
                x = hit.GetX()
                y = hit.GetY()
                px = hit.GetPx()
                py = hit.GetPy()
                pz = hit.GetPz()
                pt = np.hypot(px, py)
                P = np.hypot(pz, pt)
                pid = hit.PdgCode()
                assert pid not in [12, -12, 14, -14, 16, -16]
                h['muon_tiles_all'].Fill(x, y, weight)
                h['muon_bars_x_all'].Fill(x, y, weight)
                h['muon_bars_y_all'].Fill(x, y, weight)
                if abs(pid) == 13:
                    muon = True
                    h['mu_p'].Fill(P, weight)
                    h['mu_pt'].Fill(pt, weight)
                    h['mu_ppt'].Fill(P, pt, weight)
                    h['muon_tiles_mu'].Fill(x, y, weight)
                    h['muon_bars_y_mu'].Fill(x, y, weight)
                    h['muon_bars_x_mu'].Fill(x, y, weight)
        for hit in event.vetoPoint:
            if hit:
                if not hit.GetEnergyLoss() > 0:
                    continue
                x = hit.GetX()
                y = hit.GetY()
                z = hit.GetZ()
                px = hit.GetPx()
                py = hit.GetPy()
                pz = hit.GetPz()
                pt = np.hypot(px, py)
                P = np.hypot(pz, pt)
                pid = hit.PdgCode()
                detector_ID = hit.GetDetectorID()
                assert pid not in [12, -12, 14, -14, 16, -16]
                detector = sGeo.FindNode(x, y, z).GetName()
                # Timing detector:
                if detector == 'TimeDet_1':
                    h['timing_all'].Fill(x, y, weight)
                    if abs(pid) == 13:
                        muon = True
                        h['mu_p'].Fill(P, weight)
                        h['mu_pt'].Fill(pt, weight)
                        h['mu_ppt'].Fill(P, pt, weight)
                        h['timing_mu'].Fill(x, y, weight)
                    continue
                # UVT
                if detector == 'VetoTimeDet_1':
                    h['UVT_all'].Fill(x, y, weight)
                    if abs(pid) == 13:
                        muon = True
                        h['mu_p'].Fill(P, weight)
                        h['mu_pt'].Fill(pt, weight)
                        h['mu_ppt'].Fill(P, pt, weight)
                        h['UVT_mu'].Fill(x, y, weight)
                    continue
                phi = r.TMath.ATan2(y, x)
                if 99999 < detector_ID < 999999:
                    h['SBT_Liquid_all'].Fill(z, phi, weight)
                    if abs(pid) == 13:
                        muon = True
                        h['mu_p'].Fill(P, weight)
                        h['mu_pt'].Fill(pt, weight)
                        h['mu_ppt'].Fill(P, pt, weight)
                        h['SBT_Liquid_mu'].Fill(z, phi, weight)
                    continue
                elif detector_ID > 999999:
                    h['SBT_Plastic_all'].Fill(z, phi, weight)
                    if abs(pid) == 13:
                        muon = True
                        h['mu_p'].Fill(P, weight)
                        h['mu_pt'].Fill(pt, weight)
                        h['mu_ppt'].Fill(P, pt, weight)
                        h['SBT_Plastic_mu'].Fill(z, phi, weight)
                    continue
                print 'Unidentified vetoPoint.'
        if muon:
            h['mu_p_original'].Fill(original_muon.GetP(), weight)
            h['mu_pt_original'].Fill(original_muon.GetPt(), weight)
            h['mu_ppt_original'].Fill(original_muon.GetP(),
                                      original_muon.GetPt(), weight)
            # NOTE: muons are counted several times if they create several hits
            #       But the original muon is only counted once.
    print 'Event loop done'
    for key in h:
        classname = h[key].Class().GetName()
        if 'TH' in classname or 'TP' in classname:
            h[key].Write()
    f.Close()


if __name__ == '__main__':
    r.gErrorIgnoreLevel = r.kWarning
    r.gROOT.SetBatch(True)
    main()
