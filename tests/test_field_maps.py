# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Check that every shipped field map is stored the way ShipBFieldMap reads it.

The reader streams the ``Data`` tree sequentially and indexes it as
``(iX*Ny + iY)*Nz + iZ``. Nothing in the file states that ordering, and when
``Nx == Ny`` with matching x and y ranges a transposed map still has the right
number of entries, so it is read mirrored about the x = y plane without a
single complaint. That is what happened to the default spectrometer map.

Two things pin the ordering down. The stored node coordinates say what the
writer intended, and the divergence of the field says what is actually in the
file: a physical field has div B = 0, and no transposition survives that.
"""

from pathlib import Path

import fieldMapTools as fmt
import numpy as np
import pytest

MAP_DIRECTORY = Path(__file__).resolve().parent.parent / "files"

# Per map: the component that dominates on the beam axis, how much better the
# divergence has to be than the transposed reading, and how large the
# divergence may be next to the local gradient scale.
#
# The shield maps sit inside iron on a coarse grid, so their numerical
# divergence is large and only weakly discriminating; their node coordinates
# carry the check instead. The measured values are roughly 50x / 0.015 for the
# spectrometer maps, 3.7x / 0.29 for the older one, and 2.2x / 0.9 for the
# shield maps.
EXPECTED = {
    "2026_09_28_SHiP_SpectrometerField_ECN3_MgB2": ("Bx", 10.0, 0.1),
    "2026_09_28_MainSpectrometerField_V13_3500": ("Bx", 10.0, 0.1),
    "2026_09_28_MainSpectrometerField_V21_2000": ("Bx", 10.0, 0.1),
    "2026_09_28_MainSpectrometerField_V21_3000": ("Bx", 10.0, 0.1),
    "2026_07_02_MainSpectrometerField_V21_2455": ("Bx", 10.0, 0.1),
    "MainSpectrometerField": ("Bx", 2.0, 0.5),
    "TRY_2025": ("By", 1.4, 1.2),
    "TRY_2026": ("By", 1.4, 1.2),
}


def _is_lfs_pointer(path):
    with path.open("rb") as handle:
        return handle.read(40).startswith(b"version https://git-lfs")


def _discover():
    """Every readable field map in files/.

    Unfetched git-lfs pointers are dropped one by one rather than taken as a
    reason to skip the lot, so a partly fetched checkout still checks the maps
    it does have.
    """
    if not MAP_DIRECTORY.is_dir():
        return []
    candidates = sorted(MAP_DIRECTORY.glob("*.root"))
    return [path for path in candidates if not _is_lfs_pointer(path) and fmt.is_field_map(path)]


MAPS = _discover()

pytestmark = pytest.mark.skipif(not MAPS, reason="no field maps in files/ (git-lfs objects not fetched?)")


@pytest.fixture(scope="module")
def loaded():
    """Every map read once, as ``{stem: (range, field)}``."""
    return {path.stem: (fmt.read_range(path), fmt.read_field(path)) for path in MAPS}


def expectation(stem):
    """What this map should look like, or a skip if nobody has said."""
    if stem not in EXPECTED:
        pytest.skip(f"{stem} is not listed in EXPECTED (see test_map_is_expected)")
    return EXPECTED[stem]


@pytest.mark.parametrize("path", MAPS, ids=lambda path: path.stem)
def test_map_is_expected(path):
    """A new map has to be added to EXPECTED deliberately, not by accident."""
    assert path.stem in EXPECTED, (
        f"{path.name} is not listed in EXPECTED. Work out which component it is "
        "meant to produce and how clean its divergence is, then add it."
    )


@pytest.mark.parametrize("path", MAPS, ids=lambda path: path.stem)
def test_binning_is_consistent(path):
    rng = fmt.read_range(path)
    assert min(rng.dx, rng.dy, rng.dz) > 0.0
    assert min(rng.Nx, rng.Ny, rng.Nz) >= 2
    # Limits that are not a whole number of bins apart would put every node
    # away from where the interpolation looks for it.
    assert max(rng.extent_mismatch()) < 1e-2
    assert fmt.entry_count(path) == rng.N


@pytest.mark.parametrize("path", MAPS, ids=lambda path: path.stem)
def test_coordinates_follow_the_assumed_order(path):
    """The regression test: a transposed map is off by tens of bins here."""
    rng = fmt.read_range(path)
    residuals = fmt.coord_residuals(path, rng)
    assert residuals is not None, (
        f"{path.name} stores no x,y,z branches, so its ordering cannot be "
        "verified. Repack it with field/canonicaliseFieldMap.py."
    )
    # The builtin max() skips a NaN that is not first, so check explicitly.
    assert np.all(np.isfinite(residuals)), f"{path.name} stores non-finite node coordinates: residuals {residuals}"
    assert max(residuals) < 0.5, (
        f"{path.name} is stored in {fmt.infer_data_order(path, rng)} order, not "
        "the ascending z,y,x order ShipBFieldMap assumes."
    )


@pytest.mark.parametrize("path", MAPS, ids=lambda path: path.stem)
def test_divergence_prefers_the_stored_order(path, loaded):
    """div B = 0 only holds for the reading that matches the file."""
    _, minimum_ratio, maximum_relative = expectation(path.stem)
    rng, field = loaded[path.stem]
    as_stored, scale = fmt.div_b_rms(field, rng)
    transposed, _ = fmt.div_b_rms(fmt.transpose_xy(field), rng)
    assert as_stored * minimum_ratio < transposed
    assert as_stored < maximum_relative * scale


@pytest.mark.parametrize("path", MAPS, ids=lambda path: path.stem)
def test_expected_component_dominates_on_axis(path, loaded):
    """Catches a Bx/By column swap, which leaves div B untouched."""
    dominant = expectation(path.stem)[0]
    rng, field = loaded[path.stem]
    peaks = np.abs(fmt.on_axis(field, rng)).max(axis=0)
    index = fmt.FIELD_BRANCHES.index(dominant)
    others = np.delete(peaks, index).max()
    assert peaks[index] > 5.0 * others
