# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Pythia8 version of makeCascade.py: generate ccbar or bbbar in the hadronic cascade of the target.

Same algorithm and output ntuple as makeCascade.py, so the output can be used as input file of
run_fixedTarget.py. Every particle on the cascade stack produces a signal event with probability
chi/chi_max, chi = K * sigma(signal) / sigma(total), and a minimum-bias event whose hadrons above
threshold are added to the stack. Pythia8 changes the beam energy event by event only for soft QCD,
so signal events are generated in batches in 10% momentum bins, in the centre-of-mass frame, and
boosted to the lab along the projectile.
"""

import argparse
import math
import random
import time
from array import array

import numpy as np
import pythia8
import ROOT

ap = argparse.ArgumentParser(description="Run SHiP makeCascade with Pythia8: generate ccbar or bbbar")
ap.add_argument(
    "-s",
    "--seed",
    type=int,
    default=int(time.time() * 100000000 % 900000000),
    help="Random number seed, integer. If not given, current time will be used",
)
ap.add_argument("-t", "--Fntuple", default="", help="Name of ntuple output file")
ap.add_argument("-n", "--nevgen", type=int, default=100000, help="Number of events to produce, default 100000")
ap.add_argument("-E", "--pbeamh", type=float, default=400.0, help="Energy of beam in GeV, default 400 GeV")
ap.add_argument(
    "-m", "--mselcb", type=int, default=4, help="4 (5): charm (beauty) production, default charm", choices=[4, 5]
)
ap.add_argument(
    "--target-composition",
    default="W",
    help="Target composition (to determine the ratio of protons in the material). Default is Tungsten (W). Only other choice is Molybdenum (Mo)",
    choices=["W", "Mo"],
)
ap.add_argument(
    "--pythia8-tune",
    default="default",
    choices=["default", "FTFT"],
    help="Pythia8 tune: default (Monash 2013) or FTFT (arXiv:2608.29076, with its K-factors)",
)
ap.add_argument("--nev", type=int, default=2000, help="Events / momentum")
ap.add_argument("--nrpoints", type=int, default=20, help="Number of momentum points taken to calculate sig/sigtot")
args = ap.parse_args()
if args.Fntuple == "":
    args.Fntuple = f"Cascade{int(args.nevgen / 1000)}k-pythia8-{args.pythia8_tune}-MSEL{args.mselcb}-ntuple.root"

# cascade beam particles, anti-particles are generated automatically if they exist.
idbeam = [2212, 211, 2112, 321, 130, 310]
target = [2212, 2112]
# fraction of protons in the nucleus, 74/184 for W, 42/98 for Mo
fracp = 0.40 if args.target_composition == "W" else 0.43

# lower momentum limit for beam and signal particles (and their antis), K-factors for nucleon and meson beams
if args.mselcb == 4:
    pbeaml = 34.0
    idsig = {411, 421, 431, 4122, 4132, 4232, 4332, 4412, 4414, 4422, 4424, 4432, 4434, 4444}
    process = "HardQCD:hardccbar = on"
    kfactor = (2.48, 2.02)
else:
    pbeaml = 130.0
    idsig = {511, 521, 531, 541, 5122, 5132, 5142, 5232, 5242, 5332, 5342, 5412, 5414, 5422, 5424, 5432, 5434}
    idsig |= {5442, 5444, 5512, 5514, 5522, 5524, 5532, 5534, 5542, 5544, 5554}
    process = "HardQCD:hardbbbar = on"
    kfactor = (1.04, 1.19)

# FTFT tune: parameters differing from Monash 2013, as in FixedTargetGenerator.cxx
tune = []
if args.pythia8_tune == "FTFT":
    tune = [
        "Tune:pp = 14",
        "StringZ:aLund = 2.0",
        "StringZ:bLund = 0.2",
        "StringZ:rFactC = 2.0",
        "MultipartonInteractions:ecmRef = 30.",
        "MultipartonInteractions:pT0Ref = 0.69",
        "MultipartonInteractions:ecmPow = 0.266",
        "BeamRemnants:halfMassForKT = 1.21",
        "PDF:piSet = 1",
    ]
else:
    kfactor = (1.0, 1.0)

PDG = ROOT.TDatabasePDG.Instance()
random.seed(args.seed)
nseed = 0


def new_pythia(settings):
    """Return an initialised Pythia8 with the tune, its own seed and stable cascade and signal particles."""
    global nseed
    nseed += 1
    py = pythia8.Pythia("", False)
    for s in [*tune, *settings, "Print:quiet = on", "Random:setSeed = on"]:
        py.readString(s)
    py.readString(f"Random:seed = {(args.seed + 7919 * nseed) % 900000000}")
    for kf in [*idbeam, *idsig]:
        py.readString(f"{kf}:mayDecay = off")
    if not py.init():
        raise RuntimeError(f"Pythia8 initialisation failed for {settings}")
    return py


def ecm(pid, idpn, p):
    ma, mt = PDG.GetParticle(pid).Mass(), PDG.GetParticle(target[idpn]).Mass()
    return math.sqrt(ma**2 + mt**2 + 2.0 * mt * math.sqrt(p**2 + ma**2))


def beams(pid, idpn, p):
    return [
        f"Beams:idA = {pid}",
        f"Beams:idB = {target[idpn]}",
        "Beams:frameType = 1",
        f"Beams:eCM = {ecm(pid, idpn, p)}",
    ]


# minimum-bias events with variable beam particle and energy, one instance per target nucleon
mbias = [
    new_pythia(
        ["SoftQCD:all = on", "Beams:frameType = 3", "Beams:allowVariableEnergy = on", "Beams:allowIDAswitch = on"]
        + [f"Beams:idB = {tid}", f"Beams:pzA = {args.pbeamh}", "Beams:pzB = 0."]
    )
    for tid in target
]

# chi = K * sigma(signal) / sigma(total) vs momentum for all beam and target particles
pgrid = np.linspace(pbeaml, args.pbeamh, args.nrpoints)
chi = {}
for kf in idbeam:
    for pid in sorted({kf, -kf}):
        if not PDG.GetParticle(pid):
            continue
        k = kfactor[0] if abs(pid) in (2212, 2112) else kfactor[1]
        for idpn in range(2):
            chi[pid, idpn] = []
            for p in pgrid:
                py = new_pythia([process, "PartonLevel:all = off", "HadronLevel:all = off", *beams(pid, idpn, p)])
                for _ in range(args.nev):
                    py.next()
                sigtot = mbias[idpn].getSigmaTotal(pid, target[idpn], ecm(pid, idpn, p))
                chi[pid, idpn].append(k * py.infoPython().sigmaGen() / sigtot)
            print(f"chi at {args.pbeamh} GeV for {pid} on {target[idpn]}: {chi[pid, idpn][-1]}")
chimx = max(c[-1] for c in chi.values())

# signal events at bin momenta pbeamh/1.1^i, generated in batches of increasing size
buffers = {}


def signal_event(pid, idpn, p):
    """Return process code and signal hadrons (id, px, py, pz, E, m) in the CM frame of an event at momentum p."""
    ibin = round(math.log(args.pbeamh / p) / math.log(1.1))
    buf, nfill = buffers.setdefault((pid, idpn, ibin), ([], 5))
    if not buf:
        nfill = min(2 * nfill, 1000)
        buffers[pid, idpn, ibin] = (buf, nfill)
        py = new_pythia([process, *beams(pid, idpn, args.pbeamh / 1.1**ibin)])
        for _ in range(nfill):
            while not py.next():
                pass
            ev = py.event
            hadrons = [ev[i] for i in range(ev.size()) if ev[i].idAbs() in idsig and ev[i].isFinal()]
            buf.append((py.infoPython().code(), [(h.id(), h.px(), h.py(), h.pz(), h.e(), h.m()) for h in hadrons]))
    return buf.pop()


ftup = ROOT.TFile.Open(args.Fntuple, "RECREATE")
Ntup = ROOT.TNtuple(
    "pythia6",
    "pythia8 heavy flavour",
    "id:px:py:pz:E:M:mid:mpx:mpy:mpz:mE:mM:k:a0:a1:a2:a3:a4:a5:a6:a7:a8:a9:a10:a11:a12:a13:a14:a15:\
s0:s1:s2:s3:s4:s5:s6:s7:s8:s9:s10:s11:s12:s13:s14:s15",
)
# number of signal particles per cascade depth, used by FixedTargetGenerator for the normalisation
hdepth = ROOT.TH1F("2", "nr signal per cascade depth", 50, 0.5, 50.5)

t0 = time.time()
for iev in range(args.nevgen):
    if iev % 1000 == 0:
        print("Generate event ", iev)
    # stack: PID, px, py, pz, cascade depth, ancestors, interaction processes
    stack = [[2212, 0.0, 0.0, args.pbeamh, 1, [2212] + 99 * [0], 100 * [0]]]
    while stack:
        pid, px, py, pz, depth, anc, sub = stack.pop()
        p = math.sqrt(px**2 + py**2 + pz**2)
        idpn = 0 if random.random() < fracp else 1
        if np.interp(p, pgrid, chi[pid, idpn]) / chimx > random.random():
            code, hadrons = signal_event(pid, idpn, p)
            m = PDG.GetParticle(pid).Mass()
            beam = ROOT.TLorentzVector(px, py, pz, math.sqrt(p**2 + m**2))
            boost = (beam + ROOT.TLorentzVector(0, 0, 0, PDG.GetParticle(target[idpn]).Mass())).BoostVector()
            nsub = min(depth - 1, 15)
            for hid, *p4, hm in hadrons:
                v = ROOT.TLorentzVector(*p4)
                v.RotateUz(beam.Vect().Unit())
                v.Boost(boost)
                vl = [hid, v.Px(), v.Py(), v.Pz(), v.E(), hm, pid, px, py, pz, beam.E(), m, depth]
                Ntup.Fill(array("f", vl + anc[:16] + sub[:nsub] + [code] + (15 - nsub) * [0]))
                hdepth.Fill(depth)
        # minimum-bias event to add new cascade particles to the stack
        idpn = 0 if random.random() < fracp else 1
        mb = mbias[idpn]
        mb.setBeamIDs(pid, target[idpn])
        mb.setKinematics(px, py, pz, 0.0, 0.0, 0.0)
        while not mb.next():
            pass
        code = mb.infoPython().code()
        icas = min(depth + 1, 98)
        if depth == 1:  # interaction process of the first proton
            sub = [code] + sub[1:]
        for i in range(mb.event.size()):
            part = mb.event[i]
            if part.idAbs() in idbeam and part.isFinal() and part.pAbs() > pbeaml and len(stack) < 999:
                tmp = anc[: icas - 1] + [part.id()] + anc[icas:]
                stmp = sub[: icas - 1] + [code] + sub[icas:]
                stack.append([part.id(), part.px(), part.py(), part.pz(), icas, tmp, stmp])

print(f"Generated {args.nevgen} p.o.t. in {time.time() - t0} s with {nseed} Pythia8 instances")
ftup.Write()
ftup.Close()
print(f"Output file is {args.Fntuple}")
