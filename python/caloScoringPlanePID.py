# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Read the CaloScoringPlane particle-identification file.

The file holds energy-dependent electron / hadron / muon confusion matrices
(format: CaloScoringPlane/README.md, example:
geometry/caloScoringPlane_pid_provided.yaml). parse() checks its structure and
returns a PIDModel in the species order of the C++ class; make_pid() hands it
to CaloScoringPlanePID::Set(), which checks the numbers (finite, non-negative,
rows summing to 1, energies increasing). load_pid() does both for a file.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import yaml

# Order of CaloScoringPlanePID::Species (kElectron = 0, kHadron = 1, kMuon = 2).
SPECIES = ("electron", "hadron", "muon")
_OVERRIDE_SPECIES = {"electron": 0, "hadron": 1, "muon": 2, "none": -1}
_KEYS = {"species", "interpolation", "points", "pdg_overrides"}


class PIDConfigError(ValueError):
    """The PID file is malformed; the message names the file and the entry."""


@dataclass
class PIDModel:
    """Confusion matrices in the species order of CaloScoringPlanePID."""

    energies: list[float]
    matrices: list[float]  # 9 per energy, row-major: rows true, columns identified
    overrides: dict[int, int] = field(default_factory=dict)  # |pdg| -> species
    log_interpolation: bool = False


def _number(value: Any, where: str, source: str) -> float:
    # bool is an int subclass, but "true" is not a probability.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PIDConfigError(f"{source}: {where} must be a number, not {value!r}")
    return float(value)


def parse(config: Any, source: str = "<string>") -> PIDModel:
    """Check the structure of a parsed PID file and reorder it to SPECIES."""
    if not isinstance(config, dict):
        raise PIDConfigError(f"{source}: the top level must be a mapping")
    unknown = sorted(str(k) for k in config if k not in _KEYS)
    if unknown:
        raise PIDConfigError(f"{source}: unknown key(s) {', '.join(unknown)}")

    species = config.get("species", list(SPECIES))
    if not isinstance(species, list) or sorted(map(str, species)) != sorted(SPECIES):
        raise PIDConfigError(f"{source}: 'species' must be a permutation of {', '.join(SPECIES)}, not {species!r}")
    order = [SPECIES.index(s) for s in species]  # file row/column -> internal index

    interpolation = config.get("interpolation", "linear")
    if interpolation not in ("linear", "log"):
        raise PIDConfigError(f"{source}: 'interpolation' must be linear or log, not {interpolation!r}")

    points = config.get("points")
    if not isinstance(points, list) or not points:
        raise PIDConfigError(f"{source}: 'points' must be a non-empty list of {{energy, matrix}}")
    energies: list[float] = []
    matrices: list[float] = []
    for k, point in enumerate(points):
        where = f"points[{k}]"
        if not isinstance(point, dict) or set(point) != {"energy", "matrix"}:
            raise PIDConfigError(f"{source}: {where} must have exactly the keys 'energy' and 'matrix'")
        energies.append(_number(point["energy"], f"{where}.energy", source))
        rows = point["matrix"]
        if not isinstance(rows, list) or len(rows) != 3 or any(not isinstance(r, list) or len(r) != 3 for r in rows):
            raise PIDConfigError(f"{source}: {where}.matrix must be 3 rows of 3 numbers")
        matrix = [0.0] * 9
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                matrix[3 * order[i] + order[j]] = _number(value, f"{where}.matrix[{i}][{j}]", source)
        matrices.extend(matrix)

    overrides: dict[int, int] = {}
    raw = config.get("pdg_overrides") or {}  # an empty key (all entries commented out) is allowed
    if not isinstance(raw, dict):
        raise PIDConfigError(f"{source}: 'pdg_overrides' must map PDG codes to species")
    for pdg, name in raw.items():
        if isinstance(pdg, bool) or not isinstance(pdg, int):
            raise PIDConfigError(f"{source}: 'pdg_overrides' keys must be PDG codes, not {pdg!r}")
        if name not in _OVERRIDE_SPECIES:
            raise PIDConfigError(
                f"{source}: pdg_overrides[{pdg}] must be one of {', '.join(_OVERRIDE_SPECIES)}, not {name!r}"
            )
        overrides[abs(pdg)] = _OVERRIDE_SPECIES[name]

    return PIDModel(energies, matrices, overrides, interpolation == "log")


def load(path: str) -> PIDModel:
    """Read and parse a PID file; environment variables and ~ are expanded."""
    expanded = os.path.expanduser(os.path.expandvars(path))
    try:
        with open(expanded) as f:
            config = yaml.safe_load(f)
    except OSError as error:
        raise PIDConfigError(f"cannot read the PID file {expanded}: {error.strerror}") from error
    except yaml.YAMLError as error:
        raise PIDConfigError(f"{expanded}: not valid YAML: {error}") from error
    return parse(config, expanded)


def make_pid(model: PIDModel, source: str = "<model>") -> Any:
    """Build a CaloScoringPlanePID from a model; numbers are checked in C++."""
    import ROOT

    pid = ROOT.CaloScoringPlanePID()
    overrides = ROOT.std.map("int", "int")()
    for pdg, species in model.overrides.items():
        overrides[pdg] = species
    try:
        pid.Set(
            ROOT.std.vector("double")(model.energies),
            ROOT.std.vector("double")(model.matrices),
            overrides,
            model.log_interpolation,
        )
    except Exception as error:  # std::invalid_argument, raised through cppyy
        message = str(error).splitlines()[-1].strip()
        raise PIDConfigError(f"{source}: {message}") from error
    return pid


def load_pid(path: str | None) -> Any:
    """CaloScoringPlanePID from a PID file, or perfect identification without one."""
    if not path:
        import ROOT

        return ROOT.CaloScoringPlanePID()
    return make_pid(load(path), os.path.expanduser(os.path.expandvars(path)))
