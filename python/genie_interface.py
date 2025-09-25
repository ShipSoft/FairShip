"""Utilities to run GENIE tools with per-call environment overrides.

This module wraps common GENIE command-line tools (``gmkspl``, ``gevgen``,
``gntpc``) and a ROOT helper to copy flux histograms into simulation files.
It provides:

- Safe subprocess execution (no ``shell=True``)
- Per-call environment overrides (set/unset variables like ``GXMLPATH``)
- Helpful printing/logging of the exact command line

Notes
-----
* A Python process cannot modify its parent shell environment. Use the
  ``env_vars=...`` argument to set/unset variables **for the child process**
  only. If you need to persist environment variables, put them in your shell
  rc (e.g. ``~/.bashrc``) or wrap execution in ``source/env`` scripts.

* The path to ``Messenger_laconic.xml`` is auto-detected from ``$GENIE`` if
  defined and readable; otherwise the ``--message-thresholds`` option is
  omitted.

Example
-------
>>> from genie_interface import generate_genie_events
>>> generate_genie_events(
...     nevents=1000, nupdg=14, emin=1, emax=100, targetcode="1000080160",
...     inputflux="/path/flux.root", spline="/path/xsec.xml", outputfile="out",
...     env_vars={"GXMLPATH": "/opt/genie/config", "GENIE": "/cvmfs/.../genie"}
... )
"""

from __future__ import annotations

import logging
import os
import shlex
import subprocess
from typing import Dict, Optional, Union
from collections.abc import Mapping, Sequence

import ROOT  # type: ignore

__all__ = [
    "_run",
    "get_1D_flux_name",
    "get_2D_flux_name",
    "make_splines",
    "generate_genie_events",
    "make_ntuples",
    "add_hists",
    "main",
]

__version__ = "0.1.0"

PathLike = Union[str, os.PathLike]

logger = logging.getLogger(__name__)


def _merge_env(env_vars: Mapping[str, str | None] | None) -> dict[str, str]:
    """Merge ``env_vars`` with the current environment.

    Parameters
    ----------
    env_vars:
        Mapping of KEY -> VALUE to set for the child process. Use ``None`` to
        **unset** a variable (remove it) for the child environment.

    Returns
    -------
    dict
        The environment dict to pass into ``subprocess.run``.
    """
    env: dict[str, str] = dict(os.environ)
    if env_vars:
        for k, v in env_vars.items():
            if v is None:
                env.pop(k, None)
            else:
                env[k] = str(v)
    return env


def _run(
    args: Sequence[str],
    env_vars: Mapping[str, str | None] | None = None,
    *,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Run a command with optional environment overrides.

    Parameters
    ----------
    args:
        Command and arguments, each as a separate list element. (No shell.)
    env_vars:
        Optional mapping of KEY -> VALUE to inject into the child environment.
        Use ``None`` value to **unset** a variable.
    check:
        If True (default), raise ``CalledProcessError`` on non-zero exit.

    Returns
    -------
    subprocess.CompletedProcess
        The completed process object.

    Raises
    ------
    subprocess.CalledProcessError
        If the command exits with non-zero status and ``check=True``.
    """
    env = _merge_env(env_vars)
    cmd_str = shlex.join(args)
    logger.info("Executing: %s", cmd_str)
    print(">>", cmd_str)
    return subprocess.run(args, env=env, check=check)


def get_1D_flux_name(nupdg: int) -> str:
    """Return the TH1D flux histogram name for a given neutrino PDG.

    Naming convention (as used by input flux ROOT files):
    - Neutrino (PDG > 0):  ``'10' + |pdg|``
    - Anti-neutrino (PDG < 0): ``'20' + |pdg|``

    Examples
    --------
    >>> get_1D_flux_name(12)    # nu_e
    '1012'
    >>> get_1D_flux_name(-12)   # anti-nu_e
    '2012'
    """
    x = ROOT.TMath.Abs(nupdg)
    return ("10" if nupdg > 0 else "20") + str(x)


def get_2D_flux_name(nupdg: int) -> str:
    """Return the TH2D p–pT flux histogram name for a given neutrino PDG.

    Naming convention (as used by input flux ROOT files):
    - Neutrino (PDG > 0):  ``'12' + |pdg|``
    - Anti-neutrino (PDG < 0): ``'22' + |pdg|``

    Examples
    --------
    >>> get_2D_flux_name(12)    # nu_e
    '1212'
    >>> get_2D_flux_name(-12)   # anti-nu_e
    '2212'
    """
    x = ROOT.TMath.Abs(nupdg)
    return ("12" if nupdg > 0 else "22") + str(x)


def make_splines(
    nupdglist: Sequence[int],
    targetcode: str,
    emax: int | float,
    nknots: int,
    outputfile: PathLike,
    env_vars: Mapping[str, str | None] | None = None,
) -> subprocess.CompletedProcess:
    """Generate GENIE cross-section splines via ``gmkspl``.

    Parameters
    ----------
    nupdglist:
        Iterable of neutrino PDG codes (e.g. ``[12, 14, 16, -12, -14, -16]``).
    targetcode:
        GENIE nuclear target code (e.g. ``'1000080160'`` for O-16).
    emax:
        Maximum neutrino energy (GeV).
    nknots:
        Number of knots for the spline generation.
    outputfile:
        Path to output XML spline file.
    env_vars:
        Per-call environment overrides (e.g. set ``GXMLPATH`` or ``GENIE``).

    Returns
    -------
    subprocess.CompletedProcess
    """
    inputnupdg = ",".join(str(p) for p in nupdglist)
    args = [
        "gmkspl",
        "-p",
        inputnupdg,
        "-t",
        targetcode,
        "-n",
        str(nknots),
        "-e",
        str(emax),
        "-o",
        str(outputfile),
    ]
    return _run(args, env_vars=env_vars)


def generate_genie_events(
    nevents: int,
    nupdg: int,
    emin: int | float,
    emax: int | float,
    targetcode: str,
    inputflux: PathLike,
    spline: PathLike,
    outputfile: PathLike,
    *,
    process: str | None = None,
    seed: int | None = None,
    irun: int | None = None,
    env_vars: Mapping[str, str | None] | None = None,
) -> subprocess.CompletedProcess:
    """Run GENIE ``gevgen`` to generate events.

    Parameters
    ----------
    nevents:
        Number of events to generate.
    nupdg:
        Neutrino PDG code (e.g. 12, 14, 16 or negatives for anti-neutrinos).
    emin, emax:
        Energy range in GeV (inclusive, inclusive as accepted by GENIE).
    targetcode:
        GENIE nuclear target code.
    inputflux:
        Path to ROOT file with flux histograms.
    spline:
        Path to GENIE cross-section spline XML file.
    outputfile:
        Output prefix/file for GENIE (as accepted by ``-o``).
    process:
        Optional GENIE generator list (e.g. ``'CCDIS'``, ``'NC'``).
    seed:
        Optional RNG seed for reproducibility.
    irun:
        Optional integer run number (``--run``).
    env_vars:
        Per-call environment overrides (e.g. set/unset ``GXMLPATH``, ``GENIE``).

    Returns
    -------
    subprocess.CompletedProcess

    Notes
    -----
    If ``GENIE`` is defined in the child environment, this function will try
    to pass ``--message-thresholds $GENIE/config/Messenger_laconic.xml`` if
    the file exists; otherwise that option is omitted.
    """
    env = _merge_env(env_vars)

    msg_xml = None
    genie_root = env.get("GENIE")
    if genie_root:
        candidate = os.path.join(genie_root, "config", "Messenger_laconic.xml")
        if os.path.isfile(candidate):
            msg_xml = candidate

    args = [
        "gevgen",
        "-n",
        str(nevents),
        "-p",
        str(nupdg),
        "-t",
        targetcode,
        "-e",
        f"{emin},{emax}",
    ]
    if msg_xml:
        args += ["--message-thresholds", msg_xml]

    args += [
        "-f",
        f"{inputflux},{get_1D_flux_name(nupdg)}",
        "--cross-sections",
        str(spline),
        "-o",
        str(outputfile),
    ]

    if process is not None:
        args += ["--event-generator-list", process]
    if seed is not None:
        args += ["--seed", str(seed)]
    if irun is not None:
        args += ["--run", str(irun)]

    return _run(args, env_vars=env_vars)


def make_ntuples(
    inputfile: PathLike,
    outputfile: PathLike,
    env_vars: Mapping[str, str | None] | None = None,
) -> subprocess.CompletedProcess:
    """Convert a GENIE ``.ghep.root`` file to GST via ``gntpc``.

    Parameters
    ----------
    inputfile:
        Input GHEP file (e.g. ``gntp.0.ghep.root``).
    outputfile:
        Output GST file path.
    env_vars:
        Per-call environment overrides.

    Returns
    -------
    subprocess.CompletedProcess
    """
    args = ["gntpc", "-i", str(inputfile), "-f", "gst", "-o", str(outputfile)]
    return _run(args, env_vars=env_vars)


def add_hists(inputflux: PathLike, simfile: PathLike, nupdg: int) -> None:
    """Copy the 2D p–pT flux histogram from ``inputflux`` into ``simfile``.

    Parameters
    ----------
    inputflux:
        Path to ROOT file containing TH2D flux histograms.
    simfile:
        Path to the simulation ROOT file to **update** (opened in 'UPDATE' mode).
    nupdg:
        Neutrino PDG code used to select the histogram (see ``get_2D_flux_name``).

    Raises
    ------
    FileNotFoundError
        If the requested histogram is not found in ``inputflux``.
    RuntimeError
        If ROOT fails to open either file.
    """
    infile = ROOT.TFile(str(inputflux), "READ")
    if not infile or infile.IsZombie():
        raise RuntimeError(f"Failed to open input flux file: {inputflux}")
    sfile = ROOT.TFile(str(simfile), "UPDATE")
    if not sfile or sfile.IsZombie():
        infile.Close()
        raise RuntimeError(f"Failed to open simulation file for update: {simfile}")

    try:
        hname = get_2D_flux_name(nupdg)
        obj = infile.Get(hname)
        if not obj:
            raise FileNotFoundError(f"Histogram '{hname}' not found in {inputflux}")
        # Write into the current directory of sfile
        sfile.cd()
        obj.Write()
    finally:
        infile.Close()
        sfile.Close()


# --------------------------- CLI ---------------------------------------------

def _parse_env_kv(pairs: Sequence[str]) -> dict[str, str | None]:
    """Parse ``KEY=VAL`` pairs for ``--env`` CLI flag."""
    out: dict[str, str | None] = {}
    for p in pairs:
        if "=" not in p:
            raise ValueError(f"Expected KEY=VALUE, got '{p}'")
        k, v = p.split("=", 1)
        out[k] = v
    return out


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="genie-utils", description="GENIE helpers with per-call env overrides"
    )
    parser.add_argument(
        "--env",
        metavar="KEY=VALUE",
        action="append",
        default=[],
        help="Set environment variable(s) for the child process (repeatable).",
    )
    parser.add_argument(
        "--unset",
        metavar="KEY",
        action="append",
        default=[],
        help="Unset environment variable(s) for the child process (repeatable).",
    )
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Increase verbosity."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_spl = sub.add_parser("splines", help="Run gmkspl")
    p_spl.add_argument("-p", "--pdg", nargs="+", type=int, required=True)
    p_spl.add_argument("-t", "--target", required=True)
    p_spl.add_argument("-e", "--emax", type=float, required=True)
    p_spl.add_argument("-n", "--nknots", type=int, required=True)
    p_spl.add_argument("-o", "--output", required=True)

    p_gen = sub.add_parser("generate", help="Run gevgen")
    p_gen.add_argument("-n", "--nevents", type=int, required=True)
    p_gen.add_argument("-p", "--pdg", type=int, required=True)
    p_gen.add_argument("--emin", type=float, required=True)
    p_gen.add_argument("--emax", type=float, required=True)
    p_gen.add_argument("-t", "--target", required=True)
    p_gen.add_argument("-f", "--flux", required=True)
    p_gen.add_argument("-s", "--spline", required=True)
    p_gen.add_argument("-o", "--output", required=True)
    p_gen.add_argument("--process", default=None)
    p_gen.add_argument("--seed", type=int, default=None)
    p_gen.add_argument("--run", type=int, dest="irun", default=None)

    p_nt = sub.add_parser("ntuples", help="Run gntpc (ghep -> gst)")
    p_nt.add_argument("-i", "--input", required=True)
    p_nt.add_argument("-o", "--output", required=True)

    p_add = sub.add_parser("add-hists", help="Copy 2D flux hist to sim file")
    p_add.add_argument("-f", "--flux", required=True)
    p_add.add_argument("-s", "--sim", required=True)
    p_add.add_argument("-p", "--pdg", type=int, required=True)

    args = parser.parse_args(argv)

    # logging
    level = logging.WARNING
    if args.verbose == 1:
        level = logging.INFO
    elif args.verbose >= 2:
        level = logging.DEBUG
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")

    # env merging for CLI
    env_vars: dict[str, str | None] = {}
    if args.env:
        env_vars.update(_parse_env_kv(args.env))
    for key in args.unset:
        env_vars[key] = None

    if args.cmd == "splines":
        make_splines(
            nupdglist=args.pdg,
            targetcode=args.target,
            emax=args.emax,
            nknots=args.nknots,
            outputfile=args.output,
            env_vars=env_vars or None,
        )
    elif args.cmd == "generate":
        generate_genie_events(
            nevents=args.nevents,
            nupdg=args.pdg,
            emin=args.emin,
            emax=args.emax,
            targetcode=args.target,
            inputflux=args.flux,
            spline=args.spline,
            outputfile=args.output,
            process=args.process,
            seed=args.seed,
            irun=args.irun,
            env_vars=env_vars or None,
        )
    elif args.cmd == "ntuples":
        make_ntuples(
            inputfile=args.input,
            outputfile=args.output,
            env_vars=env_vars or None,
        )
    elif args.cmd == "add-hists":
        add_hists(inputflux=args.flux, simfile=args.sim, nupdg=args.pdg)
    else:
        parser.error("Unknown command")

    return 0


if __name__ == "__main__":
    main()
