# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Tests for reading the CaloScoringPlane PID file (python/caloScoringPlanePID.py).

The numerical checks (rows summing to 1, energies increasing, ...) are done in
C++ by CaloScoringPlanePID::Set() and tested in tests/test_calo_scoring_plane_pid.cxx;
the tests at the end check that their errors reach Python with the file name.
"""

import os

import pytest
import yaml
from caloScoringPlanePID import SPECIES, PIDConfigError, load, parse

SHIPPED = os.path.join(os.path.dirname(__file__), "..", "geometry", "caloScoringPlane_pid_provided.yaml")
IDENTITY = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


def config(**extra):
    return {"points": [{"energy": 1, "matrix": IDENTITY}], **extra}


def test_species_order_is_that_of_the_cpp_enum():
    assert SPECIES == ("electron", "hadron", "muon")


def test_defaults():
    model = parse(config())
    assert model.energies == [1.0]
    assert model.matrices == [1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert model.overrides == {}
    assert not model.log_interpolation


def test_rows_and_columns_are_reordered():
    # file order muon, electron, hadron; P(mu -> mu) = 0.7, P(mu -> hadron) = 0.3
    model = parse(
        {
            "species": ["muon", "electron", "hadron"],
            "points": [{"energy": 1, "matrix": [[0.7, 0.0, 0.3], [0, 1, 0], [0, 0, 1]]}],
        }
    )
    e, h, mu = 0, 1, 2
    m = model.matrices
    assert m[3 * mu + mu] == 0.7
    assert m[3 * mu + h] == 0.3
    assert m[3 * e + e] == 1.0
    assert m[3 * h + h] == 1.0


def test_log_interpolation_and_several_points():
    model = parse(
        {
            "interpolation": "log",
            "points": [{"energy": 3, "matrix": IDENTITY}, {"energy": 100.0, "matrix": IDENTITY}],
        }
    )
    assert model.log_interpolation
    assert model.energies == [3.0, 100.0]
    assert len(model.matrices) == 18


def test_overrides_by_absolute_pdg_code():
    model = parse(config(pdg_overrides={22: "electron", -211: "none", 130: "muon"}))
    assert model.overrides == {22: 0, 211: -1, 130: 2}


def test_empty_pdg_overrides_key_is_allowed():
    # "pdg_overrides:" with every entry commented out parses as None
    assert parse(yaml.safe_load("pdg_overrides:\n" + yaml.safe_dump(config()))).overrides == {}


@pytest.mark.parametrize(
    ("cfg", "message"),
    [
        ([1, 2], "top level must be a mapping"),
        (config(energies=[1]), "unknown key(s) energies"),
        (config(species=["electron", "electron", "muon"]), "'species' must be a permutation"),
        (config(species=["electron", "pion", "muon"]), "'species' must be a permutation"),
        (config(interpolation="spline"), "'interpolation' must be linear or log"),
        ({"points": []}, "'points' must be a non-empty list"),
        ({"species": list(SPECIES)}, "'points' must be a non-empty list"),
        ({"points": [{"energy": 1}]}, "points[0] must have exactly the keys"),
        ({"points": [{"energy": 1, "matrix": IDENTITY, "x": 2}]}, "points[0] must have exactly the keys"),
        ({"points": [{"energy": 1, "matrix": [[1, 0], [0, 1], [0, 0]]}]}, "points[0].matrix must be 3 rows"),
        ({"points": [{"energy": 1, "matrix": [[1, 0, 0], [0, 1, 0]]}]}, "points[0].matrix must be 3 rows"),
        ({"points": [{"energy": "high", "matrix": IDENTITY}]}, "points[0].energy must be a number"),
        ({"points": [{"energy": 1, "matrix": [[1, 0, 0], [0, "a", 0], [0, 0, 1]]}]}, "points[0].matrix[1][1]"),
        ({"points": [{"energy": 1, "matrix": [[True, 0, 0], [0, 1, 0], [0, 0, 1]]}]}, "must be a number"),
        (config(pdg_overrides=[22]), "'pdg_overrides' must map PDG codes"),
        (config(pdg_overrides={"gamma": "electron"}), "keys must be PDG codes"),
        (config(pdg_overrides={22: "photon"}), "pdg_overrides[22] must be one of"),
    ],
)
def test_malformed_files_are_rejected(cfg, message):
    with pytest.raises(PIDConfigError) as error:
        parse(cfg, "pid.yaml")
    assert str(error.value).startswith("pid.yaml: ")
    assert message in str(error.value)


def test_missing_file(tmp_path):
    with pytest.raises(PIDConfigError, match="cannot read the PID file"):
        load(str(tmp_path / "missing.yaml"))


def test_invalid_yaml(tmp_path):
    path = tmp_path / "broken.yaml"
    path.write_text("points: [\n")
    with pytest.raises(PIDConfigError, match="not valid YAML"):
        load(str(path))


def test_environment_variables_are_expanded(tmp_path, monkeypatch):
    (tmp_path / "pid.yaml").write_text(yaml.safe_dump(config()))
    monkeypatch.setenv("PID_TEST_DIR", str(tmp_path))
    assert load("$PID_TEST_DIR/pid.yaml").energies == [1.0]


def test_shipped_file_parses():
    model = load(SHIPPED)
    assert model.log_interpolation
    assert model.energies == sorted(model.energies)
    assert len(model.matrices) == 9 * len(model.energies)


# --- through the C++ class (needs the compiled CaloScoringPlane library) ---


@pytest.fixture(scope="module")
def ROOT():
    ROOT = pytest.importorskip("ROOT")
    if ROOT.gSystem.Load("libCaloScoringPlane") < 0:
        pytest.skip("libCaloScoringPlane not available")
    return ROOT


def test_shipped_file_loads_into_the_cpp_class(ROOT):
    from caloScoringPlanePID import load_pid

    pid = load_pid(SHIPPED)
    assert list(pid.GetEnergies()) == load(SHIPPED).energies
    assert pid.IsLogInterpolation()


def test_no_file_gives_perfect_identification(ROOT):
    from caloScoringPlanePID import load_pid

    pid = load_pid(None)
    assert pid.Identify(13, 5.0, 0.99) == ROOT.CaloScoringPlanePID.kMuon


def test_numerical_errors_name_the_file(ROOT, tmp_path):
    from caloScoringPlanePID import load_pid

    path = tmp_path / "pid.yaml"
    path.write_text(yaml.safe_dump({"points": [{"energy": 1, "matrix": [[0.5, 0.4, 0], [0, 1, 0], [0, 0, 1]]}]}))
    with pytest.raises(PIDConfigError) as error:
        load_pid(str(path))
    assert str(path) in str(error.value)
    assert "true electron row sums to 0.9" in str(error.value)


def test_nan_in_the_file_is_rejected(ROOT, tmp_path):
    from caloScoringPlanePID import load_pid

    path = tmp_path / "pid.yaml"
    path.write_text("points:\n  - energy: .nan\n    matrix: [[1, 0, 0], [0, 1, 0], [0, 0, 1]]\n")
    with pytest.raises(PIDConfigError, match="not finite"):
        load_pid(str(path))
