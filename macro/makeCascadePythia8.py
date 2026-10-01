# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Pythia8 version of makeCascade.py: generate ccbar or bbbar in the hadronic cascade of the target.

Same algorithm and output ntuple as makeCascade.py, so the output can be used as input file of
run_fixedTarget.py. Every particle on the cascade stack produces a signal event with probability
chi/chi_max, chi = K * sigma(signal) / sigma(total), and a minimum-bias event whose hadrons above
threshold are added to the stack. Pythia8 changes the beam energy event by event only for soft QCD,
so signal events are generated in batches in 10% momentum bins, in the centre-of-mass frame, and
boosted to the lab along the projectile.

Unlike makeCascade.py, elastic scattering does not increase the cascade depth, so depth 1 (the
normalisation of run_fixedTarget.py) covers the beam proton up to its first inelastic interaction.

With --charm-production inclusive, charm signal events are inclusive inelastic events (SoftQCD:inelastic)
generated at the exact momentum and direction of the projectile and kept if they contain charm, instead
of forced HardQCD:hardccbar events. The FTFT tune describes charm production data with inclusive events;
forced production has somewhat different x_F and pT^2 distributions. The normalisation (chi) is the same.
"""

import argparse
import math
import random
import time
from array import array
from typing import NamedTuple

import numpy as np
import pythia8
import ROOT

# cascade beam particles, anti-particles are generated automatically if they exist.
CASCADE_IDS = [2212, 211, 2112, 321, 130, 310]
TARGET_NUCLEONS = [2212, 2112]
# fraction of protons in the nucleus, 74/184 for W, 42/98 for Mo
PROTON_FRACTION = {"W": 0.40, "Mo": 0.43}


class SignalConfig(NamedTuple):
    """Settings of the heavy-flavour signal."""

    p_threshold: float
    ids: set[int]
    process: str
    kfactors: tuple[float, float] | None


# per heavy quark (4: charm, 5: beauty): lower momentum limit [GeV] for cascade and signal particles
# (and their antis), signal hadrons, forced production process and K-factors for nucleon and meson
# beams. The FTFT charm K-factors normalise inclusive charm production (SoftQCD:inelastic), the
# cascade forces it (HardQCD:hardccbar), see KFORCED_CHARM below.
SIGNAL = {
    4: SignalConfig(
        p_threshold=34.0,
        ids={411, 421, 431, 4122, 4132, 4232, 4332, 4412, 4414, 4422, 4424, 4432, 4434, 4444},
        process="HardQCD:hardccbar = on",
        kfactors=None,
    ),
    5: SignalConfig(
        p_threshold=130.0,
        ids={511, 521, 531, 541, 5122, 5132, 5142, 5232, 5242, 5332, 5342, 5412, 5414, 5422, 5424, 5432, 5434}
        | {5442, 5444, 5512, 5514, 5522, 5524, 5532, 5534, 5542, 5544, 5554},
        process="HardQCD:hardbbbar = on",
        kfactors=(1.04, 1.19),
    ),
}

# FTFT tune (arXiv:2608.29076): parameters differing from Monash 2013, as in FixedTargetGenerator.cxx
FTFT_SETTINGS = [
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

# Forced-production charm K-factors equivalent to the FTFT inclusive normalisation (K = 2.48 for
# nucleon and 2.02 for meson beams), K_incl * sigma_incl / sigma_forced, from Pythia 8.312 runs with
# the FTFT tune. The ratio of inclusive to forced charm grows towards threshold, so the K-factor
# depends on the beam momentum (GeV); values are interpolated in log(p) and kept flat outside the grid.
# Measured for p p, p n, pi+ p and pi- p from 34 GeV, the charm threshold of the cascade, to 400 GeV
# (statistical precision 1-2% above 60 GeV, 2-5% below); other beams use isospin
# (n p = p n, n n = p p, pi+ n = pi- p, pi- n = pi+ p), antinucleons the nucleon and kaons the mean
# pion values.
KFORCED_CHARM_P = [34.0, 40.0, 47.0, 60.0, 100.0, 160.0, 250.0, 400.0]
KFORCED_CHARM = {
    (2212, 2212): [35.52, 25.24, 17.48, 13.99, 10.06, 9.11, 8.10, 7.30],
    (2212, 2112): [38.08, 24.22, 18.93, 13.90, 10.56, 8.94, 8.25, 7.06],
    (211, 2212): [12.93, 10.76, 9.92, 8.30, 6.49, 5.87, 5.33, 5.16],
    (-211, 2212): [10.89, 9.22, 7.66, 7.03, 5.79, 5.30, 5.12, 5.12],
}

# momentum bins of the signal events: p_beam / SIGNAL_BIN_RATIO^i
SIGNAL_BIN_RATIO = 1.1

PDG = ROOT.TDatabasePDG.Instance()


def kforced_charm(beam_id, nucleon_id, p):
    """Forced-production charm K-factor for beam_id on target nucleon nucleon_id at momentum p."""
    abs_id = abs(beam_id)
    if abs_id in (2212, 2112):
        # n on p behaves as p on n, and n on n as p on p
        key = (2212, nucleon_id) if abs_id == 2212 else (2212, 2112 if nucleon_id == 2212 else 2212)
        kfactors = KFORCED_CHARM[key]
    elif abs_id == 211:
        # pi+ n behaves as pi- p, and pi- n as pi+ p
        sign = 1 if beam_id > 0 else -1
        key = (sign * 211 if nucleon_id == 2212 else -sign * 211, 2212)
        kfactors = KFORCED_CHARM[key]
    else:
        kfactors = [0.5 * (a + b) for a, b in zip(KFORCED_CHARM[211, 2212], KFORCED_CHARM[-211, 2212])]
    return float(np.interp(math.log(p), np.log(KFORCED_CHARM_P), kfactors))


def signal_kfactor(kfactors, beam_id, nucleon_id, p):
    """K-factor applied to the forced signal cross section of beam_id on nucleon_id at momentum p.

    kfactors: (nucleon beams, meson beams), or None for the momentum-dependent charm K-factors.
    """
    if kfactors is None:
        return kforced_charm(beam_id, nucleon_id, p)
    return kfactors[0] if abs(beam_id) in (2212, 2112) else kfactors[1]


def mass(pdg_id):
    particle = PDG.GetParticle(pdg_id)
    assert particle is not None, f"Unknown PDG: {pdg_id}"
    return particle.Mass()


def ecm(beam_id, nucleon_id, p):
    """Centre-of-mass energy of beam_id with momentum p on nucleon_id at rest."""
    m_beam, m_target = mass(beam_id), mass(nucleon_id)
    return math.sqrt(m_beam**2 + m_target**2 + 2.0 * m_target * math.sqrt(p**2 + m_beam**2))


def cm_beam_settings(beam_id, nucleon_id, p):
    return [
        f"Beams:idA = {beam_id}",
        f"Beams:idB = {nucleon_id}",
        # centre-of-mass frame: events generated at the nearest grid momentum are boosted with the
        # momentum and direction of the actual projectile
        "Beams:frameType = 1",
        f"Beams:eCM = {ecm(beam_id, nucleon_id, p)}",
    ]


class PythiaFactory:
    """Create initialised Pythia8 instances with the tune, their own seed and stable cascade and signal
    particles. The seeds are drawn from a generator of their own, so that they do not follow the draws
    of the cascade; Pythia8 accepts seeds up to 900000000."""

    def __init__(self, seed, tune_settings, stable_ids):
        self.seeds = random.Random(f"pythia8-{seed}")
        self.tune_settings = tune_settings
        self.stable_ids = stable_ids
        self.n_instances = 0

    def __call__(self, settings):
        self.n_instances += 1
        pythia = pythia8.Pythia("", False)
        for setting in [*self.tune_settings, *settings, "Print:quiet = on", "Random:setSeed = on"]:
            pythia.readString(setting)
        pythia.readString(f"Random:seed = {self.seeds.randint(1, 900000000)}")
        for pdg_id in self.stable_ids:
            pythia.readString(f"{pdg_id}:mayDecay = off")
        if not pythia.init():
            raise RuntimeError(f"Pythia8 initialisation failed for {settings}")
        return pythia


def next_event(pythia):
    """Generate the next event, giving up after 100 failed attempts."""
    for _ in range(100):
        if pythia.next():
            return
    raise RuntimeError(
        f"Pythia8 failed to generate an event for beams {pythia.infoPython().idA()} on {pythia.infoPython().idB()}"
    )


class SignalEvents:
    """Signal events in momentum bins p_beam / SIGNAL_BIN_RATIO^i, generated in batches of increasing
    size, one Pythia8 instance per batch."""

    def __init__(self, new_pythia, process, signal_ids, p_beam):
        self.new_pythia = new_pythia
        self.process = process
        self.signal_ids = signal_ids
        self.p_beam = p_beam
        self.buffers = {}

    def next(self, beam_id, nucleon_id, p):
        """Return process code and signal hadrons (id, px, py, pz, E, m) in the CM frame of an event at
        momentum p."""
        p_bin = round(math.log(self.p_beam / p) / math.log(SIGNAL_BIN_RATIO))
        buffer, n_fill = self.buffers.setdefault((beam_id, nucleon_id, p_bin), ([], 5))
        if not buffer:
            n_fill = min(2 * n_fill, 1000)
            self.buffers[beam_id, nucleon_id, p_bin] = (buffer, n_fill)
            pythia = self.new_pythia(
                [self.process, *cm_beam_settings(beam_id, nucleon_id, self.p_beam / SIGNAL_BIN_RATIO**p_bin)]
            )
            for _ in range(n_fill):
                next_event(pythia)
                event = pythia.event
                hadrons = [
                    event[i] for i in range(event.size()) if event[i].idAbs() in self.signal_ids and event[i].isFinal()
                ]
                buffer.append(
                    (pythia.infoPython().code(), [(h.id(), h.px(), h.py(), h.pz(), h.e(), h.m()) for h in hadrons])
                )
        return buffer.pop()


# safety limit on the inclusive events tried for one charm signal event; near the 34 GeV threshold
# about 1 in 3e5 inelastic events contains charm
MAX_INCLUSIVE_TRIES = 100_000_000


class InclusiveSignalEvents:
    """Inclusive inelastic events with signal hadrons, at the exact projectile momentum, one Pythia8 instance
    per target nucleon. Events are hadronised only if they contain a heavy quark, which saves most of the
    time spent on events without one."""

    def __init__(self, new_pythia, signal_ids, heavy_quark, p_beam):
        self.signal_ids = signal_ids
        self.heavy_quark = heavy_quark
        self.pythia = [
            new_pythia(
                ["SoftQCD:inelastic = on", "HadronLevel:all = off"]
                + ["Beams:frameType = 3", "Beams:allowVariableEnergy = on", "Beams:allowIDAswitch = on"]
                + [f"Beams:idB = {nucleon_id}", f"Beams:pzA = {p_beam}", "Beams:pzB = 0."]
            )
            for nucleon_id in TARGET_NUCLEONS
        ]
        self.n_tried = 0

    def next(self, beam_id, i_nucleon, px, py, pz):
        """Return process code and signal hadrons (id, px, py, pz, E, m) in the lab frame."""
        pythia = self.pythia[i_nucleon]
        pythia.setBeamIDs(beam_id, TARGET_NUCLEONS[i_nucleon])
        pythia.setKinematics(px, py, pz, 0.0, 0.0, 0.0)
        for _ in range(MAX_INCLUSIVE_TRIES):
            next_event(pythia)
            self.n_tried += 1
            event = pythia.event
            if not any(event[i].idAbs() == self.heavy_quark for i in range(event.size())):
                continue
            if not pythia.forceHadronLevel():
                continue
            event = pythia.event
            hadrons = [
                event[i] for i in range(event.size()) if event[i].idAbs() in self.signal_ids and event[i].isFinal()
            ]
            if hadrons:
                return pythia.infoPython().code(), [(h.id(), h.px(), h.py(), h.pz(), h.e(), h.m()) for h in hadrons]
        raise RuntimeError(
            f"no charm in {MAX_INCLUSIVE_TRIES} inclusive events of {beam_id} on {TARGET_NUCLEONS[i_nucleon]}"
            f" at p = ({px:.1f}, {py:.1f}, {pz:.1f}) GeV"
        )


def parse_args():
    ap = argparse.ArgumentParser(description="Run SHiP makeCascade with Pythia8: generate ccbar or bbbar")
    ap.add_argument(
        "-s",
        "--seed",
        type=int,
        default=int(time.time() * 100000000 % 900000000),
        help="Random number seed, integer. If not given, current time will be used",
    )
    ap.add_argument(
        "-t",
        "--Fntuple",
        dest="output",
        default="",
        help="Name of ntuple output file, default: Cascade{nevgen/1000}k-pythia8-{pythia8_tune}-MSEL{mselcb}-ntuple.root",
    )
    ap.add_argument(
        "-n", "--nevgen", dest="n_pot", type=int, default=100000, help="Number of events to produce, default 100000"
    )
    ap.add_argument(
        "-E", "--pbeamh", dest="p_beam", type=float, default=400.0, help="Energy of beam in GeV, default 400 GeV"
    )
    ap.add_argument(
        "-m",
        "--mselcb",
        dest="heavy_quark",
        type=int,
        default=4,
        help="4 (5): charm (beauty) production, default charm",
        choices=[4, 5],
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
    ap.add_argument(
        "--charm-production",
        default="forced",
        choices=["forced", "inclusive"],
        help="Charm signal events from forced (HardQCD:hardccbar) or inclusive (SoftQCD:inelastic) production; "
        "inclusive is only for charm (-m 4), beauty is always forced",
    )
    ap.add_argument(
        "--nev", dest="n_sigma_events", type=int, default=2000, help="Events per momentum point for sig/sigtot"
    )
    ap.add_argument(
        "--nrpoints",
        dest="n_momentum_points",
        type=int,
        default=40,
        help="Number of momentum points taken to calculate sig/sigtot",
    )
    args = ap.parse_args()
    p_threshold = SIGNAL[args.heavy_quark].p_threshold
    if args.n_pot < 1 or args.n_sigma_events < 1 or args.n_momentum_points < 2 or args.p_beam <= p_threshold:
        ap.error(f"need --nevgen >= 1, --nev >= 1, --nrpoints >= 2 and a beam energy above {p_threshold} GeV")
    if args.output == "":
        args.output = f"Cascade{int(args.n_pot / 1000)}k-pythia8-{args.pythia8_tune}-MSEL{args.heavy_quark}-ntuple.root"
    return args


def main():
    args = parse_args()
    signal = SIGNAL[args.heavy_quark]
    p_threshold, signal_ids, signal_process = signal.p_threshold, signal.ids, signal.process
    proton_fraction = PROTON_FRACTION[args.target_composition]
    if args.pythia8_tune == "FTFT":
        tune_settings, kfactors = FTFT_SETTINGS, signal.kfactors
    else:
        tune_settings, kfactors = [], (1.0, 1.0)

    random.seed(args.seed)
    new_pythia = PythiaFactory(args.seed, tune_settings, [*CASCADE_IDS, *signal_ids])

    # minimum-bias events with variable beam particle and energy, one instance per target nucleon
    mbias_pythia = [
        new_pythia(
            ["SoftQCD:all = on", "Beams:frameType = 3", "Beams:allowVariableEnergy = on", "Beams:allowIDAswitch = on"]
            + [f"Beams:idB = {nucleon_id}", f"Beams:pzA = {args.p_beam}", "Beams:pzB = 0."]
        )
        for nucleon_id in TARGET_NUCLEONS
    ]

    # chi = K * sigma(signal) / sigma(total) vs momentum for all beam and target particles.
    # The grid is logarithmic and chi is interpolated in log(chi) vs log(p): chi varies by orders of
    # magnitude over the range and most of that variation sits close to the threshold.
    p_grid = np.geomspace(p_threshold, args.p_beam, args.n_momentum_points)
    log_p_grid = np.log(p_grid)
    log_chi, sigma = {}, {}
    for pdg_id in CASCADE_IDS:
        for beam_id in sorted({pdg_id, -pdg_id}):
            if not PDG.GetParticle(beam_id):
                continue
            for i_nucleon, nucleon_id in enumerate(TARGET_NUCLEONS):
                sigma[beam_id, i_nucleon] = []
                for p in p_grid:
                    pythia = new_pythia(
                        [signal_process, "PartonLevel:all = off", "HadronLevel:all = off"]
                        + cm_beam_settings(beam_id, nucleon_id, p)
                    )
                    for _ in range(args.n_sigma_events):
                        next_event(pythia)
                    sigma[beam_id, i_nucleon].append(
                        signal_kfactor(kfactors, beam_id, nucleon_id, p) * pythia.infoPython().sigmaGen()
                    )
                sigma_total = [
                    mbias_pythia[i_nucleon].getSigmaTotal(beam_id, nucleon_id, ecm(beam_id, nucleon_id, p))
                    for p in p_grid
                ]
                log_chi[beam_id, i_nucleon] = np.log([s / t for s, t in zip(sigma[beam_id, i_nucleon], sigma_total)])
                print(
                    f"K*sigma and chi at {args.p_beam} GeV for {beam_id} on {nucleon_id}: "
                    f"{sigma[beam_id, i_nucleon][-1]:.3e} mb, {math.exp(log_chi[beam_id, i_nucleon][-1]):.3e}"
                )
    chi_max = max(np.exp(c).max() for c in log_chi.values())
    # cross section per nucleon of the target composition, at the beam energy, for the normalisation
    sigma_QQ = proton_fraction * sigma[2212, 0][-1] + (1.0 - proton_fraction) * sigma[2212, 1][-1]
    print(f"K*sigma per nucleon at {args.p_beam} GeV: {1e3 * sigma_QQ:.2f} ub")

    signal_events = SignalEvents(new_pythia, signal_process, signal_ids, args.p_beam)
    inclusive_events = (
        InclusiveSignalEvents(new_pythia, signal_ids, args.heavy_quark, args.p_beam)
        if args.charm_production == "inclusive" and args.heavy_quark == 4
        else None
    )

    output_file = ROOT.TFile.Open(args.output, "RECREATE")
    ntuple = ROOT.TNtuple(
        "pythia6",
        "pythia8 heavy flavour",
        "id:px:py:pz:E:M:mid:mpx:mpy:mpz:mE:mM:k:a0:a1:a2:a3:a4:a5:a6:a7:a8:a9:a10:a11:a12:a13:a14:a15:\
s0:s1:s2:s3:s4:s5:s6:s7:s8:s9:s10:s11:s12:s13:s14:s15",
    )
    # number of signal particles per cascade depth, used by FixedTargetGenerator for the normalisation
    depth_hist = ROOT.TH1F("2", "nr signal per cascade depth", 50, 0.5, 50.5)
    # cross section per nucleon [mb] this file was generated with, read back by run_fixedTarget.py to
    # scale chicc/chibb, so that the normalisation follows the beam energy, tune and target of the file
    # hadd adds TParameters by default; keep the value of the first file when cascade files are merged
    sigma_parameter = ROOT.TParameter("double")("sigma_QQ", sigma_QQ)  # type: ignore[missing-attribute]
    sigma_parameter.SetMergeMode("f")
    sigma_parameter.Write()

    t0 = time.time()
    for i_pot in range(args.n_pot):
        if i_pot % 1000 == 0:
            print("Generate event ", i_pot)
        # stack: PID, px, py, pz, cascade depth, ancestors, interaction processes
        stack: list[tuple[int, float, float, float, int, list[int], list[int]]] = []
        stack.append((2212, 0.0, 0.0, args.p_beam, 1, [2212] + 99 * [0], 100 * [0]))
        while stack:
            beam_id, px, py, pz, depth, ancestors, processes = stack.pop()
            p = math.sqrt(px**2 + py**2 + pz**2)
            i_nucleon = 0 if random.random() < proton_fraction else 1
            nucleon_id = TARGET_NUCLEONS[i_nucleon]
            if math.exp(np.interp(math.log(p), log_p_grid, log_chi[beam_id, i_nucleon])) / chi_max > random.random():
                beam_mass = mass(beam_id)
                beam = ROOT.TLorentzVector(px, py, pz, math.sqrt(p**2 + beam_mass**2))
                if inclusive_events is not None:
                    code, hadrons = inclusive_events.next(beam_id, i_nucleon, px, py, pz)
                else:
                    code, hadrons = signal_events.next(beam_id, nucleon_id, p)
                boost = (beam + ROOT.TLorentzVector(0, 0, 0, mass(nucleon_id))).BoostVector()  # type: ignore[missing-attribute]
                n_processes = min(depth - 1, 15)
                for hadron_id, *p4, hadron_mass in hadrons:
                    hadron = ROOT.TLorentzVector(*p4)
                    if inclusive_events is None:  # forced events are generated in the CM frame
                        hadron.RotateUz(beam.Vect().Unit())  # type: ignore[missing-attribute]
                        hadron.Boost(boost)  # type: ignore[missing-attribute]
                    row = [hadron_id, hadron.Px(), hadron.Py(), hadron.Pz(), hadron.E(), hadron_mass]
                    row += [beam_id, px, py, pz, beam.E(), beam_mass, depth]
                    row += ancestors[:16] + processes[:n_processes] + [code] + (15 - n_processes) * [0]
                    ntuple.Fill(array("f", row))
                    depth_hist.Fill(depth)
            # minimum-bias event to add new cascade particles to the stack
            i_nucleon = 0 if random.random() < proton_fraction else 1
            pythia = mbias_pythia[i_nucleon]
            pythia.setBeamIDs(beam_id, TARGET_NUCLEONS[i_nucleon])
            pythia.setKinematics(px, py, pz, 0.0, 0.0, 0.0)
            next_event(pythia)
            code = pythia.infoPython().code()
            if code == 102:
                # Elastic scattering does not start a new cascade generation: the scattered hadron keeps
                # its depth. Depth 1 is then everything the beam proton produces up to and including its
                # first inelastic interaction, which is what chicc/chibb in run_fixedTarget.py normalise.
                final = [pythia.event[i] for i in range(pythia.event.size()) if pythia.event[i].isFinal()]
                leading = max(final, key=lambda part: part.pAbs())
                if leading.pAbs() > p_threshold and len(stack) < 999:
                    stack.append((beam_id, leading.px(), leading.py(), leading.pz(), depth, ancestors, processes))
                continue
            new_depth = min(depth + 1, 98)
            if depth == 1:  # first inelastic interaction process of the beam proton
                processes = [code] + processes[1:]
            for i in range(pythia.event.size()):
                part = pythia.event[i]
                if part.idAbs() in CASCADE_IDS and part.isFinal() and part.pAbs() > p_threshold and len(stack) < 999:
                    new_ancestors = ancestors[: new_depth - 1] + [part.id()] + ancestors[new_depth:]
                    new_processes = processes[: new_depth - 1] + [code] + processes[new_depth:]
                    stack.append((part.id(), part.px(), part.py(), part.pz(), new_depth, new_ancestors, new_processes))

    print(f"Generated {args.n_pot} p.o.t. in {time.time() - t0} s with {new_pythia.n_instances} Pythia8 instances")
    if inclusive_events is not None:
        print(f"{inclusive_events.n_tried} inclusive events generated for the charm signal")
    output_file.Write()
    output_file.Close()
    print(f"Output file is {args.output}")


if __name__ == "__main__":
    main()
