# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Target-composition scaling of charm/beauty over min-bias cross-section ratios.

Shared by ``macro/makeDecay.py`` and ``macro/run_fixedTarget.py`` so the physics
constants and the ``chicc``/``chibb`` derivation live in a single place.
"""

from collections import namedtuple

# Reference values for Molybdenum (historical defaults). Cross-section ratios
# scale heavy-flavour ~ A and mbias ~ A^(0.71).
heavyflavour_Ascale = 1
mbias_Ascale = 0.71

A_REF = 98.0
CHICC_REF = 1.7e-3  # prob to produce primary ccbar pair/pot on Mo
CHIBB_REF = 1.6e-7  # prob to produce primary bbbar pair/pot on Mo
TARGET_A = {"W": 184.0, "Mo": 98.0}

CrossSections = namedtuple("CrossSections", ["chicc", "chibb", "A", "scale"])


def derive_cross_sections(target_composition=None, A=None, chicc=None, chibb=None):
    """Return default-scaled chicc/chibb, honouring explicit overrides.

    ``A`` overrides the ``target_composition`` preset; ``chicc``/``chibb``
    override the target-derived value when not ``None``. Supply either
    ``target_composition`` (a known preset) or an explicit ``A``.
    """
    if A is None:
        if target_composition is None:
            raise ValueError(f"Provide either target_composition (one of {sorted(TARGET_A)}) or an explicit A.")
        A = TARGET_A[target_composition]
    if A <= 0:
        raise ValueError(f"Invalid target mass number A={A}. Must be > 0.")
    scale = (A / A_REF) ** (heavyflavour_Ascale - mbias_Ascale)
    chicc = chicc if chicc is not None else CHICC_REF * scale
    chibb = chibb if chibb is not None else CHIBB_REF * scale
    return CrossSections(chicc, chibb, A, scale)


def check_run_type_override(is_beauty, chicc, chibb):
    """Reject a cross-section override that does not match the run type.

    A run is either charm or beauty, so at most one of ``chicc``/``chibb`` is
    meaningful. Passing the wrong one (or both) is a mistake and raises
    ``ValueError`` with a clear message rather than being silently ignored.
    """
    if chicc is not None and chibb is not None:
        raise ValueError("Set only one of --chicc / --chibb; a run is either charm or beauty.")
    if is_beauty and chicc is not None:
        raise ValueError("This is a beauty run: pass --chibb, not --chicc.")
    if not is_beauty and chibb is not None:
        raise ValueError("This is a charm run: pass --chicc, not --chibb.")


def format_summary(cs, target_composition=None):
    """One human-readable summary of the derived cross-section ratios."""
    label = target_composition or "custom (A given)"
    return (
        f"Target composition: {label}, A={cs.A}, "
        f"scale=(A/{A_REF})^({heavyflavour_Ascale}-{mbias_Ascale})={cs.scale:.4f}\n"
        f"Derived cross-section ratios: chicc={cs.chicc:.3e}, chibb={cs.chibb:.3e}"
    )
