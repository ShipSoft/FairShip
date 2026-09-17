# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import pytest
from heavyFlavourScaling import (
    CHIBB_REF,
    CHICC_REF,
    SIGMA_BB_REF,
    SIGMA_CC_REF,
    check_run_type_override,
    derive_cross_sections,
)


def test_mo_preset_is_reference():
    cs = derive_cross_sections("Mo")
    assert cs.A == 98.0
    assert cs.scale == pytest.approx(1.0)
    assert cs.chicc == pytest.approx(CHICC_REF)
    assert cs.chibb == pytest.approx(CHIBB_REF)


def test_w_preset_scales_up():
    cs = derive_cross_sections("W")
    assert cs.A == 184.0
    assert cs.scale == pytest.approx((184.0 / 98.0) ** 0.29)
    assert cs.chicc == pytest.approx(CHICC_REF * cs.scale)
    assert cs.chibb == pytest.approx(CHIBB_REF * cs.scale)


def test_A_without_target_composition():
    cs = derive_cross_sections(A=181.0)
    assert cs.A == 181.0
    assert cs.scale == pytest.approx((181.0 / 98.0) ** 0.29)
    assert cs.chicc == pytest.approx(CHICC_REF * cs.scale)
    assert cs.chibb == pytest.approx(CHIBB_REF * cs.scale)


def test_explicit_A_overrides_preset():
    """Passing both is deliberate: an explicit A wins over the "W" preset."""
    cs = derive_cross_sections("W", A=98.0)
    assert cs.A == 98.0
    assert cs.scale == pytest.approx(1.0)


def test_explicit_ratios_override_derived():
    cs = derive_cross_sections(A=98.0, chicc=5e-3, chibb=2e-7)
    assert cs.chicc == 5e-3
    assert cs.chibb == 2e-7


def test_missing_target_and_A_raises():
    with pytest.raises(ValueError):
        derive_cross_sections()


def test_non_positive_A_raises():
    with pytest.raises(ValueError):
        derive_cross_sections(A=0)
    with pytest.raises(ValueError):
        derive_cross_sections(A=-1.0)


def test_override_matching_run_type_is_accepted():
    # charm run with chicc, beauty run with chibb, and no override at all.
    check_run_type_override(is_beauty=False, chicc=1e-3, chibb=None)
    check_run_type_override(is_beauty=True, chicc=None, chibb=1e-7)
    check_run_type_override(is_beauty=False, chicc=None, chibb=None)


def test_override_wrong_run_type_raises():
    with pytest.raises(ValueError, match="beauty run"):
        check_run_type_override(is_beauty=True, chicc=1e-3, chibb=None)
    with pytest.raises(ValueError, match="charm run"):
        check_run_type_override(is_beauty=False, chicc=None, chibb=1e-7)


def test_both_overrides_raise():
    with pytest.raises(ValueError, match="only one"):
        check_run_type_override(is_beauty=False, chicc=1e-3, chibb=1e-7)


def test_sigma_QQ_scales_the_charm_reference_only():
    cs = derive_cross_sections("Mo", sigma_QQ=2 * SIGMA_CC_REF)
    assert cs.chicc == pytest.approx(2 * CHICC_REF)
    assert cs.chibb == pytest.approx(CHIBB_REF)


def test_sigma_QQ_scales_the_beauty_reference_for_a_beauty_file():
    cs = derive_cross_sections("Mo", sigma_QQ=2 * SIGMA_BB_REF, is_beauty=True)
    assert cs.chibb == pytest.approx(2 * CHIBB_REF)
    assert cs.chicc == pytest.approx(CHICC_REF)


def test_sigma_QQ_reference_value_reproduces_default():
    assert derive_cross_sections("W", sigma_QQ=SIGMA_CC_REF).chicc == pytest.approx(derive_cross_sections("W").chicc)


def test_sigma_QQ_does_not_override_explicit_chicc():
    assert derive_cross_sections("Mo", chicc=1e-3, sigma_QQ=2 * SIGMA_CC_REF).chicc == pytest.approx(1e-3)


def test_invalid_sigma_QQ():
    with pytest.raises(ValueError, match="sigma_QQ"):
        derive_cross_sections("W", sigma_QQ=0.0)
