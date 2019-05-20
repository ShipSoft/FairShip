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
        '-o',
        '--outputfile',
        default='flux_map.root',
        help='''File to write the flux maps to. '''
        '''Will be recreated if it already exists.''')
    args = parser.parse_args()
    f = r.TFile.Open(args.outputfile, 'recreate')
    f.cd()
    maxpt = 10. * u.GeV
    maxp = 360. * u.GeV
    h = {}

    # Define histograms
    for nplane in range(0, 23):
        ut.bookHist(h, 'NuTauMu_all_{}'.format(nplane),
                    'Rpc_{};x[cm];y[cm]'.format(
                        nplane), 100, -300, +300, 100, -300,
                    300)
        ut.bookHist(h, 'NuTauMu_mu_{}'.format(nplane),
                    'Rpc_{};x[cm];y[cm]'.format(
                        nplane), 100, -300, +300, 100, -300,
                    300)
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
        ut.bookHist(h, 'TargetTracker_{}'.format(suffix),
                    '{};x[cm];y[cm]'.format(title), 120, -60, 60, 120, -60,
                    60)
        ut.bookHist(h, 'TargetTracker_yvsz_{}'.format(suffix),
                    '{};z[cm];y[cm]'.format(
                        title), 400, -3300, -2900, 120, -60,
                    60)
        ut.bookHist(h, 'TargetTracker_xvsz_{}'.format(suffix),
                    '{};z[cm];x[cm]'.format(
                        title), 400, -3300, -2900, 120, -60,
                    60)
        ut.bookHist(h, 'NuTauMu_{}'.format(suffix),
                    '{};x[cm];y[cm]'.format(title), 100, -300, +300, 100, -300,
                    300)
        ut.bookHist(h, 'NuTauMu_yvsz_{}'.format(suffix),
                    '{};z[cm];y[cm]'.format(
                        title), 200, -2680, -2480, 600, -300,
                    300)
        ut.bookHist(h, 'NuTauMu_xvsz_{}'.format(suffix),
                    '{};z[cm];x[cm]'.format(
                        title), 200, -2680, -2480, 600, -300,
                    300)
        ut.bookHist(h, 'ECAL_TP_{}'.format(suffix),
                    '{};x[cm];y[cm]'.format(title), 167, -501, +501, 334,
                    -1002, 1002)
        ut.bookHist(h, 'ECAL_Alt_{}'.format(suffix),
                    '{};x[cm];y[cm]'.format(title), 50, -500, +500, 100, -1000,
                    1000)
        ut.bookHist(h, 'SBT_Liquid_{}'.format(suffix),
                    '{};z[cm];#phi'.format(title), 100, -3000, +3000, 100,
                    -r.TMath.Pi(), r.TMath.Pi())
        ut.bookHist(h, 'SBT_Plastic_{}'.format(suffix),
                    '{};z[cm];#phi'.format(title), 100, -3000, +3000, 100,
                    -r.TMath.Pi(), r.TMath.Pi())
        for station in range(1, 5):
            ut.bookHist(h, 'T{}_{}'.format(station, suffix),
                        '{};x[cm];y[cm]'.format(title), 10, -250, +250, 20,
                        -500, 500)

    ut.bookHist(h, 'NuTauMu_mu_p', '#mu#pm;p[GeV];', 100, 0, maxp)
    ut.bookHist(h, 'NuTauMu_mu_pt', '#mu#pm;p_t[GeV];', 100, 0,
                maxpt)
    ut.bookHist(h, 'NuTauMu_mu_ppt', '#mu#pm;p[GeV];p_t[GeV];',
                100, 0, maxp, 100, 0, maxpt)
    ut.bookHist(h, 'NuTauMu_all_p', '#mu#pm;p[GeV];', 100, 0, maxp)
    ut.bookHist(h, 'NuTauMu_all_pt', '#mu#pm;p_t[GeV];', 100, 0,
                maxpt)
    ut.bookHist(h, 'NuTauMu_all_ppt', '#mu#pm;p[GeV];p_t[GeV];',
                100, 0, maxp, 100, 0, maxpt)

    for suffix in ['', '_original']:
        ut.bookHist(h, 'mu_p{}'.format(suffix), '#mu#pm;p[GeV];', 100, 0, maxp)
        ut.bookHist(h, 'mu_pt{}'.format(suffix), '#mu#pm;p_t[GeV];', 100, 0,
                    maxpt)
        ut.bookHist(h, 'mu_ppt{}'.format(suffix), '#mu#pm;p[GeV];p_t[GeV];',
                    100, 0, maxp, 100, 0, maxpt)
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
        for hit in event.strawtubesPoint:
            if hit:
                if not hit.GetEnergyLoss() > 0:
                    continue
                trid = hit.GetTrackID()
                assert trid > 0
                weight = event.MCTrack[trid].GetWeight()
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
                    muonid = trid
                    h['T{}_mu'.format(station)].Fill(x, y, weight)
                    h['mu_p'].Fill(P, weight)
                    h['mu_pt'].Fill(pt, weight)
                    h['mu_ppt'].Fill(P, pt, weight)
        for hit in event.EcalPoint:
            if hit:
                if not hit.GetEnergyLoss() > 0:
                    continue
                trid = hit.GetTrackID()
                assert trid > 0
                weight = event.MCTrack[trid].GetWeight()
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
                    muonid = trid
                    h['mu_p'].Fill(P, weight)
                    h['mu_pt'].Fill(pt, weight)
                    h['mu_ppt'].Fill(P, pt, weight)
                    h['ECAL_TP_mu'].Fill(x, y, weight)
                    h['ECAL_Alt_mu'].Fill(x, y, weight)
                elif abs(pid) == 11:
                    Esq = px ** 2 + py ** 2 + pz ** 2 + 0.000511 ** 2
                    h['ECAL_e_E'].Fill(np.sqrt(Esq), weight)
                    h['ECAL_TP_e'].Fill(x, y, weight)
                    h['ECAL_Alt_e'].Fill(x, y, weight)
                elif abs(pid) == 22:
                    Esq = px ** 2 + py ** 2 + pz ** 2
                    h['ECAL_gamma_E'].Fill(np.sqrt(Esq), weight)
                    h['ECAL_TP_gamma'].Fill(x, y, weight)
                    h['ECAL_Alt_gamma'].Fill(x, y, weight)
        for hit in event.TTPoint:
            if hit:
                if not hit.GetEnergyLoss() > 0:
                    continue
                trid = hit.GetTrackID()
                assert trid > 0
                detID = hit.GetDetectorID()
                weight = event.MCTrack[trid].GetWeight()
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
                if detID == 0:
                    h['TargetTracker_all'].Fill(x, y, weight)
                h['TargetTracker_xvsz_all'].Fill(z, x, weight)
                h['TargetTracker_yvsz_all'].Fill(z, y, weight)
                if abs(pid) == 13:
                    muon = True
                    muonid = trid
                    h['mu_p'].Fill(P, weight)
                    h['mu_pt'].Fill(pt, weight)
                    h['mu_ppt'].Fill(P, pt, weight)
                    if detID == 0:
                        h['TargetTracker_mu'].Fill(x, y, weight)
                    h['TargetTracker_xvsz_mu'].Fill(z, x, weight)
                    h['TargetTracker_yvsz_mu'].Fill(z, y, weight)
        for hit in event.ShipRpcPoint:
            if hit:
                if not hit.GetEnergyLoss() > 0:
                    continue
                trid = hit.GetTrackID()
                assert trid > 0
                detID = hit.GetDetectorID()
                nplane = detID - 10000
                weight = event.MCTrack[trid].GetWeight()
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
                if nplane >= 0:
                    h['NuTauMu_all_{}'.format(nplane)].Fill(x, y, weight)
                h['NuTauMu_xvsz_all'].Fill(z, x, weight)
                h['NuTauMu_yvsz_all'].Fill(z, y, weight)
                if detID == 10000:
                    h['NuTauMu_all_p'].Fill(P, weight)
                    h['NuTauMu_all_pt'].Fill(pt, weight)
                    h['NuTauMu_all_ppt'].Fill(P, pt, weight)
                if abs(pid) == 13:
                    muon = True
                    muonid = trid
                    h['mu_p'].Fill(P, weight)
                    h['mu_pt'].Fill(pt, weight)
                    h['mu_ppt'].Fill(P, pt, weight)
                    h['NuTauMu_mu'].Fill(x, y, weight)
                    if nplane >= 0:
                        # fill the histogram corresponding to nplane
                        h['NuTauMu_mu_{}'.format(nplane)].Fill(x, y, weight)
                    if detID == 10000:
                        h['NuTauMu_mu_p'].Fill(P, weight)
                        h['NuTauMu_mu_pt'].Fill(pt, weight)
                        h['NuTauMu_mu_ppt'].Fill(P, pt, weight)
                    h['NuTauMu_xvsz_mu'].Fill(z, x, weight)
                    h['NuTauMu_yvsz_mu'].Fill(z, y, weight)
        for hit in event.TimeDetPoint:
            if hit:
                if not hit.GetEnergyLoss() > 0:
                    continue
                trid = hit.GetTrackID()
                assert trid > 0
                weight = event.MCTrack[trid].GetWeight()
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
                h['timing_all'].Fill(x, y, weight)
                if abs(pid) == 13:
                    muon = True
                    muonid = trid
                    h['mu_p'].Fill(P, weight)
                    h['mu_pt'].Fill(pt, weight)
                    h['mu_ppt'].Fill(P, pt, weight)
                    h['timing_mu'].Fill(x, y, weight)
        for hit in event.muonPoint:
            if hit:
                if not hit.GetEnergyLoss() > 0:
                    continue
                trid = hit.GetTrackID()
                assert trid > 0
                weight = event.MCTrack[trid].GetWeight()
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
                    muonid = trid
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
                trid = hit.GetTrackID()
                assert trid > 0
                weight = event.MCTrack[trid].GetWeight()
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
                phi = r.TMath.ATan2(y, x)
                if 99999 < detector_ID < 999999:
                    h['SBT_Liquid_all'].Fill(z, phi, weight)
                    if abs(pid) == 13:
                        muon = True
                        muonid = trid
                        h['mu_p'].Fill(P, weight)
                        h['mu_pt'].Fill(pt, weight)
                        h['mu_ppt'].Fill(P, pt, weight)
                        h['SBT_Liquid_mu'].Fill(z, phi, weight)
                    continue
                elif detector_ID > 999999:
                    h['SBT_Plastic_all'].Fill(z, phi, weight)
                    if abs(pid) == 13:
                        muon = True
                        muonid = trid
                        h['mu_p'].Fill(P, weight)
                        h['mu_pt'].Fill(pt, weight)
                        h['mu_ppt'].Fill(P, pt, weight)
                        h['SBT_Plastic_mu'].Fill(z, phi, weight)
                    continue
                print 'Unidentified vetoPoint.'
        if muon:
            original_muon = event.MCTrack[muonid]
            weight = original_muon.GetWeight()
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
