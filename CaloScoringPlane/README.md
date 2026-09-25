# CaloScoringPlane

An ideal detector plane that replaces the former SplitCal calorimeter. It is
meant for studies that need the particles arriving at the calorimeter position
(MC truth), optionally with a parametrised particle identification.

## Geometry and simulation

A 1 mm thick vacuum box, 4 m × 6 m, whose upstream face is the calorimeter entrance window, just downstream of the timing detector (z = 96.570 m, the former SplitCal front face)
(`ship_geo.CaloScoringPlane` in `python/geometry_config.py`; node `CaloScoringPlane_1`).
There is no energy-deposit requirement: every track that **enters** the box
produces one `CaloScoringPlanePoint` with the MC-truth position, momentum,
time and PDG code at the exit face, neutral particles included. A track crossing the plane
twice gives two points (the sign of `pz` tells the direction). Tracks with a
point are kept in `MCTrack`. Branch: `CaloScoringPlanePoint` in the `cbmsim` tree.

## Digitisation and particle identification

`python/detectors/CaloScoringPlaneDetector.py` (run by `ShipReco.py`) makes one
`CaloScoringPlaneHit` per point, skipping neutrinos (`IgnoredPdg`) and, by default,
backward-going crossings (`ForwardOnly`). The hit holds the x/y position and
time, optionally smeared (`PositionResolution`, `TimeResolution`), the
MC-truth momentum, and the identified species (`GetPid()`, `IsElectron()`,
`IsHadron()`, `IsMuon()`, `IsIdentified()`).

Branches in the reconstruction output:

| Branch                  | Content                                   |
| ----------------------- | ----------------------------------------- |
| `Digi_CaloScoringPlaneHits` | `std::vector<CaloScoringPlaneHit>`            |
| `digiCaloScoringPlane2MC`   | per hit, the MC track index (-2 if that track was not stored) |

The species is drawn by `CaloScoringPlanePID` from energy-dependent confusion
matrices given with

```bash
python $FAIRSHIP/macro/ShipReco.py -f sim.root -g geo.root \
    --caloScoringPlanePID $FAIRSHIP/geometry/caloScoringPlane_pid_provided.yaml
```

Without `--caloScoringPlanePID` the identification is perfect.

### True species

| PDG code                                   | Species    |
| ------------------------------------------ | ---------- |
| ±11                                        | electron   |
| ±13                                        | muon       |
| mesons and baryons (incl. n, K⁰L)          | hadron     |
| anything else (γ, ν, nuclei, BSM codes)    | unknown, never identified |

`pdg_overrides` in the configuration changes this per |PDG code|.

### Configuration file

```yaml
species: [electron, hadron, muon] # order of rows (true) and columns (identified)
interpolation: log # linear (default) or log: interpolate linearly in E or in log E
points: # strictly increasing total energy in GeV
  - energy: 1.0
    matrix: # matrix[i][j] = P(identified as species[j] | true species[i]); rows sum to 1
      - [0.90, 0.09, 0.01]
      - [0.08, 0.82, 0.10]
      - [0.01, 0.14, 0.85]
  - energy: 100.0
    matrix: [[0.98, 0.019, 0.001], [0.015, 0.975, 0.01], [0.001, 0.009, 0.99]]
pdg_overrides: # optional: |PDG code| -> electron, hadron, muon or none
  22: electron
```

The energy is the total energy at the plane, from the point momentum and the
PDG mass. Between two points each matrix element is interpolated; below the
first or above the last point that point's matrix is used. Mistakes in the
file (unknown key or species, a row not summing to 1, energies not
increasing, ...) raise an error that names the entry and line.
`geometry/caloScoringPlane_pid_provided.yaml` is the configuration used for the
`maximal_opt_CHEAP5_fixed` setup.

### Using CaloScoringPlanePID directly

From C++ (link against the `CaloScoringPlane` library):

```cpp
#include "CaloScoringPlanePID.h"

CaloScoringPlanePID pid("$FAIRSHIP/geometry/caloScoringPlane_pid_provided.yaml");
CaloScoringPlanePID::Species s = pid.Identify(point);  // point: CaloScoringPlanePoint, uses gRandom
double pMisId = pid.Probability(CaloScoringPlanePID::kHadron, CaloScoringPlanePID::kMuon, 7.5);
```

From Python:

```python
pid = ROOT.CaloScoringPlanePID("caloScoringPlane_pid.yaml")
if pid.Identify(point) == ROOT.CaloScoringPlanePID.kMuon:
    ...
```

`examples/calo_scoring_plane_pid_example.py` applies it to all points of a
simulation file and prints the resulting true → identified table.
