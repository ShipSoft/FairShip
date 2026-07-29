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


def derive_cross_sections(target_composition, A=None, chicc=None, chibb=None):
    """Return default-scaled chicc/chibb, honouring explicit overrides.

    ``A`` overrides the ``target_composition`` preset; ``chicc``/``chibb``
    override the target-derived value when not ``None``.
    """
    A = A if A is not None else TARGET_A[target_composition]
    if A <= 0:
        raise ValueError(f"Invalid target mass number A={A}. Must be > 0.")
    scale = (A / A_REF) ** (heavyflavour_Ascale - mbias_Ascale)
    chicc = chicc if chicc is not None else CHICC_REF * scale
    chibb = chibb if chibb is not None else CHIBB_REF * scale
    return CrossSections(chicc, chibb, A, scale)


def format_summary(cs, target_composition):
    """One human-readable summary of the derived cross-section ratios."""
    return (
        f"Target composition: {target_composition}, A={cs.A}, "
        f"scale=(A/{A_REF})^({heavyflavour_Ascale}-{mbias_Ascale})={cs.scale:.4f}\n"
        f"Derived cross-section ratios: chicc={cs.chicc:.3e}, chibb={cs.chibb:.3e}"
    )
