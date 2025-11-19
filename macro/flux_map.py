#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import argparse
import numpy as np
import ROOT as r
import shipunit as u
import rootUtils as ut
import logger as log


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
        ut.bookHist(h, f'NuTauMu_all_{nplane}',
                    'Rpc_{};x[cm];y[cm]'.format(
                        nplane), 100, -300, +300, 100, -300,
                    300)
        ut.bookHist(h, f'NuTauMu_mu_{nplane}',
                    'Rpc_{};x[cm];y[cm]'.format(
                        nplane), 100, -300, +300, 100, -300,
                    300)
    for suffix, title in [('mu', '#mu#pm hits'), ('all', 'All hits')]:
        ut.bookHist(h, f'timing_{suffix}',
                    f'{title};x[cm];y[cm]', 3, -252, +252, 167, -501,
                    501)
        ut.bookHist(h, f'TargetTracker_{suffix}',
                    f'{title};x[cm];y[cm]', 120, -60, 60, 120, -60,
                    60)
        ut.bookHist(h, f'TargetTracker_yvsz_{suffix}',
                    '{};z[cm];y[cm]'.format(
                        title), 400, -3300, -2900, 120, -60,
                    60)
        ut.bookHist(h, f'TargetTracker_xvsz_{suffix}',
                    '{};z[cm];x[cm]'.format(
                        title), 400, -3300, -2900, 120, -60,
                    60)
        ut.bookHist(h, f'NuTauMu_{suffix}',
                    f'{title};x[cm];y[cm]', 100, -300, +300, 100, -300,
                    300)
        ut.bookHist(h, f'NuTauMu_yvsz_{suffix}',
                    '{};z[cm];y[cm]'.format(
                        title), 200, -2680, -2480, 600, -300,
                    300)
        ut.bookHist(h, f'NuTauMu_xvsz_{suffix}',
                    '{};z[cm];x[cm]'.format(
                        title), 200, -2680, -2480, 600, -300,
                    300)
        ut.bookHist(h, f'SBT_Liquid_{suffix}',
                    f'{title};z[cm];#phi', 100, -3000, +3000, 100,
                    -r.TMath.Pi(), r.TMath.Pi())
        ut.bookHist(h, f'SBT_Plastic_{suffix}',
                    f'{title};z[cm];#phi', 100, -3000, +3000, 100,
                    -r.TMath.Pi(), r.TMath.Pi())
        for station in range(1, 5):
            ut.bookHist(h, f'T{station}_{suffix}',
                        f'{title};x[cm];y[cm]', 10, -250, +250, 20,
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
        ut.bookHist(h, f'mu_p{suffix}', '#mu#pm;p[GeV];', 100, 0, maxp)
        ut.bookHist(h, f'mu_pt{suffix}', '#mu#pm;p_t[GeV];', 100, 0,
                    maxpt)
        ut.bookHist(h, f'mu_ppt{suffix}', '#mu#pm;p[GeV];p_t[GeV];',
                    100, 0, maxp, 100, 0, maxpt)
    ch = r.TChain('cbmsim')
    ch.Add(args.inputfile)
    n = ch.GetEntries()
    log.info(n)
    i = 0
    for event in ch:
        if i % 10000 == 0:
            log.info(f'{i}/{n}')
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
                station = hit.GetStationNumber()
                h[f'T{station}_all'].Fill(x, y, weight)
                if abs(pid) == 13:
                    muon = True
                    muonid = trid
                    h[f'T{station}_mu'].Fill(x, y, weight)
                    h['mu_p'].Fill(P, weight)
                    h['mu_pt'].Fill(pt, weight)
                    h['mu_ppt'].Fill(P, pt, weight)
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
                    h[f'NuTauMu_all_{nplane}'].Fill(x, y, weight)
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
                        h[f'NuTauMu_mu_{nplane}'].Fill(x, y, weight)
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
                log.warning('Unidentified vetoPoint.')
        if muon:
            original_muon = event.MCTrack[muonid]
            weight = original_muon.GetWeight()
            h['mu_p_original'].Fill(original_muon.GetP(), weight)
            h['mu_pt_original'].Fill(original_muon.GetPt(), weight)
            h['mu_ppt_original'].Fill(original_muon.GetP(),
                                      original_muon.GetPt(), weight)
            # NOTE: muons are counted several times if they create several hits
            #       But the original muon is only counted once.
    log.info('Event loop done')
    for key in h:
        classname = h[key].Class().GetName()
        if 'TH' in classname or 'TP' in classname:
            h[key].Write()
    f.Close()


if __name__ == '__main__':
    r.gErrorIgnoreLevel = r.kWarning
    r.gROOT.SetBatch(True)
    main()
