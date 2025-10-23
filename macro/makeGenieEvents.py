"""Generate GENIE neutrino interaction events from flux histograms.

This “launcher” wraps `genie_utils` (gmkspl/gevgen/gntpc helpers) and adds:
- Argument parsing with sensible defaults and validation
- Optional *nudet* mode (disables charm/tau decays via GXMLPATH)
- Automatic neutrino/antineutrino scaling based on flux hist sums
- Structured logging and robust error reporting

Typical use
-----------
$ python $FAIRSHIP/macro/makeGenieEvents sim \
    --seed 65539 \
    --output ./work \
    --filedir /eos/experiment/ship/data/Mbias/background-prod-2018 \
    --target iron \
    --nevents 1000 \
    --particles 16 -16 \
    --emin 0.5 --emax 350 \
    --xsec-file gxspl-FNALsmall.xml \
    --flux-file pythia8_Geant4_1.0_withCharm_nu.root \
    --event-generator-list CC \
    --nudet

Notes
-----
- This tool *does not* modify your parent shell environment.
- `--nudet` sets `GXMLPATH` for the child process only (you can override path
  with `--gxmlpath`).

"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Mapping, Sequence
from pathlib import Path

import fairship.shipRoot_conf as shipRoot_conf
import ROOT  # type: ignore
from fairship.utils.genie_interface import (
    add_hists,
    generate_genie_events,
    get_1D_flux_name,
    make_ntuples,
    make_splines,
)

# ------------------------- Defaults & Mappings --------------------------------

DEFAULT_XSEC_FILE = "gxspl-FNALsmall.xml"
DEFAULT_FLUX_FILE = "pythia8_Geant4_1.0_withCharm_nu.root"

DEFAULT_SPLINE_DIR = Path(
    "/eos/experiment/ship/user/edursov/genie/genie_xsec/v3_02_00/NULL/G1802a00000-k250-e1000/data"
)
DEFAULT_FILE_DIR = Path("/eos/experiment/ship/data/Mbias/background-prod-2018")

TARGET_CODE = {
    "iron": "1000260560",
    "lead": "1000822040[0.014],1000822060[0.241],1000822070[0.221],1000822080[0.524]",
    "tungsten": "1000741840",
}

NUPDGLIST = [16, -16, 14, -14, 12, -12]

# ------------------------------ Helpers ---------------------------------------
shipRoot_conf.configure()


def extract_nu_over_nubar(
    neutrino_flux: Path, particles: Sequence[int]
) -> dict[int, float]:
    """Compute ν/ν̄ = sum(nu)/sum(nubar) from 1D flux histograms."""
    f = ROOT.TFile(str(neutrino_flux), "READ")
    if not f or f.IsZombie():
        raise FileNotFoundError(f"Cannot open flux file: {neutrino_flux}")
    try:
        ratios: dict[int, float] = {}
        for pdg in particles:
            fam = abs(int(pdg))
            h_nu = f.Get(get_1D_flux_name(fam))
            h_nubar = f.Get(get_1D_flux_name(-fam))
            if not h_nu or not h_nubar:
                raise FileNotFoundError(
                    f"Missing hists {get_1D_flux_name(fam)} / "
                    f"{get_1D_flux_name(-fam)} in {neutrino_flux}"
                )
            s_nu = float(h_nu.GetSumOfWeights())
            s_nubar = float(h_nubar.GetSumOfWeights())
            if s_nubar <= 0.0:
                raise FileNotFoundError(
                    f"ν̄ sum of weights is zero for family {fam} in {neutrino_flux}"
                )
            ratios[fam] = s_nu / s_nubar
            log_output = (
                f"ν/ν̄ ratio for |PDG|={fam}: "
                f"{ratios[fam]:.4f} (nu={s_nu}, nubar={s_nubar})"
            )
            logging.info(log_output)
        return ratios
    finally:
        f.Close()


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _build_env(nudet: bool, gxmlpath: Path | None) -> Mapping[str, str | None] | None:
    """Build per-call env overrides (sets GXMLPATH only in nudet mode)."""
    if not nudet:
        return None
    val = (
        str(gxmlpath)
        if gxmlpath
        else "/eos/experiment/ship/user/aiuliano/GENIE_FNAL_nu_splines"
    )
    return {"GXMLPATH": val}


def _target_code(name: str) -> str:
    code = TARGET_CODE.get(name.lower())
    if not code:
        raise ValueError(f"Unknown target '{name}'. Choices: {', '.join(TARGET_CODE)}")
    return code


def _pdg_list(particles: Sequence[int]) -> Sequence[int]:
    return [int(p) for p in particles]


def make_splines_cli(target: str, work_dir: Path, nknots: int, emax: float) -> None:
    """Build xsec splines with gmkspl and write `xsec_splines.xml` to work_dir."""
    _ensure_dir(work_dir)
    output = work_dir / "xsec_splines.xml"
    make_splines(
        nupdglist=NUPDGLIST,
        targetcode=_target_code(target),
        emax=emax,
        nknots=nknots,
        outputfile=output,
    )
    logging.info(f"Spline file written: {output}")


def make_events(
    *,
    run: int,
    nevents: int,
    particles: Sequence[int],
    targetcode: str,
    process: str | None,
    emin: float,
    emax: float,
    neutrino_flux: Path,
    splines: Path,
    seed: int,
    env_vars: Mapping[str, str | None] | None,
    work_dir: Path,
    nu_over_nubar: Mapping[int, float],
) -> None:
    """Generate events for PDGs, convert to GST, and attach 2D flux."""
    _ensure_dir(work_dir)
    pdg_db = ROOT.TDatabasePDG()

    for pdg in particles:
        fam = abs(pdg)
        part = pdg_db.GetParticle(int(pdg))
        pdg_name = part.GetName() if part else str(pdg)

        # anti-neutrinos scaled by flux ratio
        N = int(nevents) if pdg > 0 else int(nevents / nu_over_nubar[fam])

        out_dir = work_dir / f"genie-{pdg_name}_{N}_events"
        _ensure_dir(out_dir)

        nudet_suffix = "_nudet" if env_vars and env_vars.get("GXMLPATH") else ""
        filename = (
            f"run_{run}_{pdg_name}_{N}_events_{targetcode}_{emin}_{emax}_GeV_"
            f"{process or 'ALL'}{nudet_suffix}.ghep.root"
        )
        ghep_path = out_dir / filename
        gst_path = out_dir / f"genie-{filename}"

        logging.info(
            f"Generating {N} events for PDG {pdg_name} (run={run}) -> {ghep_path}"
        )

        generate_genie_events(
            nevents=N,
            nupdg=int(pdg),
            emin=emin,
            emax=emax,
            targetcode=targetcode,
            inputflux=str(neutrino_flux),
            spline=str(splines),
            outputfile=str(ghep_path),
            process=process,
            seed=int(seed),
            irun=int(run),
            env_vars=env_vars,
        )
        make_ntuples(str(ghep_path), str(gst_path), env_vars=env_vars)
        add_hists(str(neutrino_flux), str(gst_path), int(pdg))

        logging.info(f"Done PDG {pdg_name}: {ghep_path} -> {gst_path}")


# ----------------------------- CLI & main -------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run GENIE neutrino simulation")
    sub = p.add_subparsers(dest="cmd", required=True)

    # sim command
    ap = sub.add_parser("sim", help="Make GENIE simulation file(s)")
    ap.add_argument(
        "-s", "--seed", type=int, default=65539, help="RNG seed (default: GENIE 65539)"
    )
    ap.add_argument(
        "-o",
        "--output",
        dest="work_dir",
        type=Path,
        default=Path("./work"),
        help="Output directory",
    )
    ap.add_argument(
        "-f",
        "--filedir",
        dest="filedir",
        type=Path,
        default=DEFAULT_FILE_DIR,
        help="Flux dir",
    )
    ap.add_argument(
        "-c",
        "--crosssectiondir",
        dest="splinedir",
        type=Path,
        default=DEFAULT_SPLINE_DIR,
        help="Spline dir",
    )
    ap.add_argument(
        "--xsec-file",
        type=str,
        default=DEFAULT_XSEC_FILE,
        help=f"Spline XML (default: {DEFAULT_XSEC_FILE})",
    )
    ap.add_argument(
        "--flux-file",
        type=str,
        default=DEFAULT_FLUX_FILE,
        help=f"Flux ROOT (default: {DEFAULT_FLUX_FILE})",
    )
    ap.add_argument(
        "-t",
        "--target",
        type=str,
        default="iron",
        choices=sorted(TARGET_CODE),
        help="Target material",
    )
    ap.add_argument(
        "-n", "--nevents", type=int, default=100, help="Events per neutrino species"
    )
    ap.add_argument("--emin", type=float, default=0.5, help="Min Eν [GeV]")
    ap.add_argument("--emax", type=float, default=350.0, help="Max Eν [GeV]")
    ap.add_argument(
        "-e",
        "--event-generator-list",
        dest="evtype",
        type=str,
        default=None,
        help="GENIE generator list (e.g. CC, CCDIS, CCQE, CharmCCDIS, RES, CCRES, ...)",
    )
    ap.add_argument(
        "--nudet", action="store_true", help="Disable charm & tau decays via GXMLPATH"
    )
    ap.add_argument(
        "--gxmlpath", type=Path, default=None, help="Override GXMLPATH in --nudet mode"
    )
    ap.add_argument(
        "-p",
        "--particles",
        nargs="+",
        type=int,
        default=NUPDGLIST,
        help="PDGs (e.g. 16 -16 14 -14 12 -12). Default: all flavors",
    )
    ap.add_argument("-r", "--run", type=int, default=1, help="GENIE run number")
    ap.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v or -vv)",
    )

    # spline command
    ap1 = sub.add_parser(
        "spline", help="Make a new cross-section spline (xsec_splines.xml)"
    )
    ap1.add_argument(
        "-t", "--target", type=str, default="iron", choices=sorted(TARGET_CODE)
    )
    ap1.add_argument(
        "-o", "--output", dest="work_dir", type=Path, default=Path("./work")
    )
    ap1.add_argument("-n", "--nknots", type=int, default=500)
    ap1.add_argument("--emax", type=float, default=400.0)

    return p


def main(argv: Sequence[str] | None = None) -> int:
    """Launch GENIE event generation or spline creation from CLI args."""
    # CLI
    parser = _build_parser()
    args = parser.parse_args(argv)

    # logging
    level = logging.WARNING
    if args.verbose == 1:
        level = logging.INFO
    elif args.verbose >= 2:
        level = logging.DEBUG
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")

    # ROOT env
    shipRoot_conf.configure()

    if args.cmd == "spline":
        make_splines_cli(
            target=args.target,
            work_dir=args.work_dir,
            nknots=args.nknots,
            emax=args.emax,
        )
        return 0

    # sim
    env_vars = _build_env(nudet=bool(args.nudet), gxmlpath=args.gxmlpath)
    targetcode = _target_code(args.target)

    splines = (args.splinedir / args.xsec_file).resolve()
    flux = (args.filedir / args.flux_file).resolve()
    if not splines.is_file():
        parser.error(f"Spline file not found: {splines}")
    if not flux.is_file():
        parser.error(f"Flux ROOT file not found: {flux}")

    particles = _pdg_list(args.particles)
    nu_over_nubar = extract_nu_over_nubar(flux, particles)

    logging.info(
        f"Seed: {args.seed} | "
        f"Target: {args.target} ({targetcode}) | "
        f"Process: {args.evtype or 'ALL'} | "
        f"nudet={bool(args.nudet)}"
    )
    make_events(
        run=int(args.run),
        nevents=int(args.nevents),
        particles=particles,
        targetcode=targetcode,
        process=args.evtype,
        emin=float(args.emin),
        emax=float(args.emax),
        neutrino_flux=flux,
        splines=splines,
        seed=int(args.seed),
        env_vars=env_vars,
        work_dir=args.work_dir.resolve(),
        nu_over_nubar=nu_over_nubar,
    )
    logging.info("Event generation completed successfully.")
    return 0


if __name__ == "__main__":
    main()
