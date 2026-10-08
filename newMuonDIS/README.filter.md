<!--
SPDX-License-Identifier: LGPL-3.0-or-later
SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration
-->

Filtering prepared DIS events
============================

After building ShipMuDIS, run in the FairShip environment:

```sh
python newMuonDIS/filterEvents.py -f prepared.root -o selected.root \
    -g geometry.root --min-charged 2
```

Multiple input files are accepted after `-f`. The output must not already exist.
Use `--ignore-input-containing STRING` (repeatable) to skip matching filenames while
searching input directories recursively. Without this option, filenames containing
`filtered` are skipped; supplied patterns replace that default. Explicit input
files are not subject to these patterns.
`-s` sets the first muon entry; `-n` limits the number of input entries (zero
processes none; -1 processes all remaining entries).

The filter cut applies independently to each DIS interaction in each material.
`--filter-option 0` (the default) requires at least two charged daughters with momentum above 1 GeV whose extrapolated positions
are within a centred 4 m by 6 m plane: `|x| <= 200 cm`, `|y| <= 300 cm`.
All daughters start at their DIS vertex. Only crossings in the particle's
direction of motion count. Outgoing muons are included by default. Use
`--exclude-muons` to count only charged non-muons. ROOT's PDG database supplies
charges, with a nuclear-PDG-code fallback; unknown non-nuclear codes do not
count as charged.

Choose another acceptance condition with `--filter-option`:

* **0:** the existing single-plane charged-multiplicity filter. `--min-charged`,
  `--detector-z`, and `--no-detector-acceptance` retain their original meaning.
* **1:** at least two charged daughters with momentum above 1 GeV must each hit `(Tr1 or Tr2)` **and**
  `(Tr3 or Tr4)` **and** the timing detector. Each plane uses its own global
  x/y exit-face bounds from `GetVolumeExitFaceXY()`, including placement offsets.
  The plane centres are read from the placed
  `Tr1`, `Tr2`, `Tr3`, `Tr4`, and `Timing Detector` geometry volumes. Hits from
  different daughters cannot be combined to satisfy one track's condition.
* **2:** at least one non-neutrino daughter, including visible neutral
  daughters, must enter the
  rectangular detector volume `|x| <= 200 cm`, `|y| <= 300 cm`, from the front
  face of `Tr1` to the back face of `SplitCalDetector`. Bounds include parent
  placements and the volumes' bounding-box extents. Neutral particles travel
  in straight lines; charged particles use both field maps. Side entries count,
  including tracks that miss both z-end planes. Daughters starting inside count.

Options 1 and 2 require geometry and detector acceptance. Their multiplicities
are fixed (two and one respectively); `--min-charged` applies only to option 0.
`--exclude-muons` applies to all three options. Only intersections along the
particle's forward trajectory count, including motion towards decreasing z.
These are geometric acceptance tests, not detector-efficiency or interaction
models. The existing custom `SetFilter` predicate still overrides every mode.

`--pythia-decays` additionally decays each DIS daughter with Pythia8 before
applying the selected filter option. A daughter is replaced recursively only when it moves
towards Tr1 and its sampled vacuum-decay vertex is upstream of Tr1; otherwise
it remains a filter candidate. Decay products start at their Pythia production
vertices. This requires detector acceptance and uses `--pythia-decay-seed`
(default `0`, a time-based seed chosen by Pythia8 and wrapped into
`[1, 900000000]` before initialization). The effective seed is logged at info
level and can be passed back with `--pythia-decay-seed` to reproduce the run.
Each original daughter's proper lifetime is sampled once; Pythia propagates
it to its vacuum decay vertex and samples the lifetimes of its decay products.
It models decays in vacuum only, not
interactions with detector material.
The decayer explicitly enables PDG IDs `211`, `321`, `130`, `310`, `3112`,
`3122`, `3222`, `3312`, `3322`, and `3334` (including antiparticles). A decay
still contributes daughters only if its sampled vertex is before Tr1.

```sh
python newMuonDIS/filterEvents.py -f prepared.root -o selected.root \
    -g geometry.root --filter-option 1
```

In C++, call `selection.SetFilterOption(1)` before or after
`SetDetectorAcceptance(...)`. Missing geometry volumes produce an error.

The plane defaults to the global z coordinate of the `Tr1` station centre in
the imported ROOT geometry, including parent placements. `--detector-z` overrides
it in cm. Like `macro/ShipReco.py`, the filter loads `ShipGeo` from the geometry
file and calls `geomGeant4.addVMCFields(..., withVirtualMC=False)` for the SST
`MainSpecMap`; the field maker remains alive throughout filtering.
The filename and translation default to `ShipGeo.Bfield.fieldMap` (relative to
`VMCWORKDIR`) and `ShipGeo.Bfield.z`. `--field-map` overrides the filename;
explicit paths are resolved relative to the current directory.
`--field-z` supplies an explicit map offset (cm), for example `0` for a map
already expressed in global coordinates. Map coordinates are in cm and map
file field values in Tesla, as required by `ShipBFieldMap`.

When the imported geometry contains `MuonShieldArea`, the filter also loads
`files/<ShipGeo.shieldName>.root` as `muonShieldField`, with z offset
`ShipGeo.muShield.Entrance[0]` and quadrant symmetry, matching the simulation
field setup. `--muon-shield-field-map` and `--muon-shield-field-z` override the
shield map path and offset (cm). Missing maps or geometry metadata are reported
as errors rather than silently omitting shield deflection. Both map files are
excluded from recursive input discovery. Geometries without `MuonShieldArea`
continue to support SST-only propagation.

The shield's global z range comes from the `MuonShieldArea` bounding box,
including all parent placements, and is logged at initialization. A nonzero
shield map must overlap this range. Nonzero fringe fields outside the iron are
retained. Before filtering, a vertex-only scan over the requested `-s/-n`
entries finds the minimum MS vertex z. Earlier vertices in other materials or
detector planes lower this limit conservatively. The shield bounds scan skips
map layers wholly upstream of this limit; no fixed shield-depth cut is used.
Unreadable vertex data falls back to the full map. The original field map and
its interpolation remain unchanged.
Propagation uses straight lines outside both maps' conservative 3D bounds,
jumping to the next ray/bounds intersection, and sums fields where they overlap.

`--min-charged` sets the minimum number of accepted charged daughters.
`--no-detector-acceptance` explicitly restores multiplicity-only filtering;
geometry and field inputs are then optional. Geometry/map files are excluded
from recursive event-file discovery.

Only passing interactions are copied, together with their complete daughter
lists, cross sections, targets, vertices and times. Muons with no passing DIS
interaction are omitted. MC tracks and detector hits are preserved, as are
per-material `wDIS` weights (already normalized during generation). The
`MuonDIS` tree remains compatible with the prepared input schema.

Each material directory contains unweighted validation histograms before the
cut and with suffix `filtered` after the cut. Muon histograms before the cut
include zero-DIS entries; filtered muon histograms include only muons with a
passing interaction in that material. In detailed mode, `muon_vtx_weight_` and
`muon_vtx_weight_filtered`
record the per-material `wDIS` once per input muon in their respective samples,
with unit entry weight. Their nominal range is [0, 1000], with fixed bin width and visible flow bins. Momentum fractions use sums of momentum
magnitudes; the muon fraction includes all muon daughters. Charged multiplicity
histograms always count all charged species, independent of `--exclude-muons`.
Malformed entries are logged and skipped before histogram filling.

Every distribution axis has two additional visible bins of the original width:
the first collects values below the nominal lower limit, and the last collects
values at or above the nominal upper limit. This applies independently to both
axes in 2D histograms, including corner overflow. Values are filled at the flow
bin centres, so histogram means include these folded coordinates. Entry counts
are unchanged. The labelled `filter_counts` summary retains its eight bins.


`daughter_pdg_grouped_` and `daughter_pdg_grouped_filtered` group daughters
into 11 labelled bins: e+, e-, mu+, mu-, gamma, all neutrinos/antineutrinos,
pi+/-, other charged hadrons, pi0, other neutral hadrons, and other particles.
Hadron categories use ROOT's meson/baryon classification and charge; nuclei
and unrecognized PDG codes are included in the last bin.

The default **compact** output keeps these distributions before and after
selection in each material directory:

* `muon_pt_vs_p_*`: input muon momentum and transverse momentum;
* `vertex_z_*` and `vertex_*_vs_*_*`: DIS vertex position;
* `daughter_pdg_grouped_*`: daughter composition;
* `n_charged_candidates_*`: charged candidate multiplicity;
* `neutral_candidate_energy_TD_*`: neutral energy reaching the actual TD face,
  excluding neutrinos and antineutrinos (PDG ±12, ±14, ±16).

Each material also retains `filter_counts`. The weighted XY efficiency
numerators and denominators are retained for every p/pT/material bin.
This is 360 histograms with the default material and kinematic bins.
`--detailed-histograms` (or `SetDetailedHistograms(true)` in C++) additionally
books the older redundant projections, raw PDG and momentum-fraction plots,
and the per-XY-cell z efficiency numerators/denominators. All files in a merge
must use the same histogram mode and binning. Ratios are calculated only from
the merged numerator and denominator.

Filter efficiencies are stored as weighted numerator (`filter_efficiency_passed_*`,
`filter_efficiency_z_passed_*`) and denominator (`filter_efficiency_all_*`,
`filter_efficiency_z_all_*`) histograms. Sum these inputs across files (and
materials, if needed) before dividing passed by all to compute efficiencies.
No efficiency ratios or canvases are stored. The output file owns all histograms;
closing it releases their memory, including on repeated filtering runs.

New filter outputs contain `filter_counts` in each material directory, storing
processed/selected raw and weighted counts for both muons and DIS interactions.
Processed counts cover valid entries, excluding unreadable/malformed entries.
Selected muons are counted separately per material: a muon contributes when at
least one interaction passes there. Muon weighted counts sum `wDIS` once per
muon; DIS weighted counts sum `nDIS * wDIS`.

Custom selections
-----------------

For other selections, supply a C++ predicate (it replaces the default cut):

```cpp
MuDISFilter selection;
selection.SetFilter([](const std::vector<DISparticle>& daughters) {
  unsigned energetic = 0;
  for (const auto& p : daughters)
    if (std::abs(p.pid) == 211 && p.E > 1.) ++energetic;
  return energetic >= 2;
});
selection.process_file("prepared.root", "selected.root");
```

`SetFilter({})` restores the default multiplicity and detector-acceptance cut. The predicate
receives all daughters of a single interaction. It can also be declared via
`ROOT.gInterpreter.Declare` when steering from Python.

Reusable magnetic propagation
-----------------------------

`MagneticTrackPropagator` is independent of DIS event data. It takes a
`ShipBFieldMap*`, an optional `TGeoManager*`, and an optional third
`ShipBFieldMap*` for the muon shield. Positions are in cm, momentum vectors in
GeV/c (magnitude and direction together), and charge in units of e.
All objects are borrowed: keep them alive and unchanged during propagation.
A null field explicitly means zero field for generic transport; the filter
requires a supplied map when detector acceptance is enabled.

```cpp
ShipBFieldMap field("SST", "spectrometer.root", 0., 0., fieldZ);
MagneticTrackPropagator transport(&field, gGeoManager);
TVector3 start(0., 0., 4000.), momentum(0.1, 0., 10.);
TVector3 hit, momentumAtPlane;
double planeZ = transport.GetPlaneZ();  // Tr1, or pass another volume name
bool ok = transport.Extrapolate(-1., start, momentum, planeZ, hit, momentumAtPlane);

// Cache once, then query many z positions without evaluating the field again.
if (transport.BuildTrajectory(-1., start, momentum, planeZ)) {
  transport.PositionAt((start.Z() + planeZ) / 2., hit);
}

MuDISFilter selection;
selection.SetDetectorAcceptance(&field, gGeoManager);  // optional third argument: plane z
selection.process_file("prepared.root", "selected.root");
```

To include a shield map already loaded and positioned by the caller:

```cpp
MagneticTrackPropagator transport(&field, gGeoManager, shieldField);
auto shieldZ = transport.GetMuonShieldZRange();
MuDISFilter selection;
selection.SetDetectorAcceptance(&field, gGeoManager,
                               std::numeric_limits<double>::quiet_NaN(), shieldField);
```

The shield map requires a placed `MuonShieldArea` volume in the geometry.
The NaN detector z keeps the default `Tr1` plane; a finite z overrides it.
Existing SST-only calls remain supported.

`GetVolumeZRange(name)` returns the global front/back bounds of a placed volume.
`IntersectsBox(charge, position, momentum, minimum, maximum)` tests whether a
forward trajectory enters an axis-aligned box. It stops at the first hit, so
a later turning point does not undo a hit. Charged segments use cubic Hermite
interpolation and side-face crossings, with the same numerical accuracy limits
as the propagator; neutral or entirely field-free tracks use exact ray/box
intersection. Charged trajectories that turn in z before any hit remain outside
the supported monotonic-z transport model.

Nonzero map layers, neighbouring interpolation cells, map placement, rotations
and quadrant symmetry determine conservative global 3D bounding boxes. These
boxes can include empty pockets; they never remove weak fields. Transverse
misses and field-free gaps use exact linear transport, including possible entry
through a side face. Inside the
field regions, adaptive RK4 with step doubling follows the Lorentz force; steps
are bounded by half the smallest active map grid spacing and a 5 cm maximum path step.
No threshold removes weak fringe fields. Grids with nonzero noise throughout
their volume consequently require integration throughout that volume.

`SetAccuracy(positionTolerance, relativeMomentumTolerance, maxStep)` controls
the local step comparison tolerances (defaults: 0.001 cm and 1e-6) and maximum
step in cm. These are local controls, not a bound on accumulated global error.
Cached positions use cubic Hermite interpolation between accepted steps and
linear segments; `GetTrajectorySize()` reports the number of cached points.
Queries outside the cached interval return false. Changing accuracy clears the
cache; failed trajectory construction also clears it.

Transport includes magnetic bending only, with constant momentum magnitude:
no energy loss, scattering, decays or geometry/material navigation. Generic
extrapolation can run in either z direction. Tracks with zero momentum, nearly
zero pz, a reversal in pz, or failed numerical convergence return false and do
not count towards filter acceptance. The cached path represents one monotonic
z crossing, not multiple crossings of a curling track. This implementation
does not change `MuDISProcessor` or `MuonPath`.

`SetMuonShieldMinZ(z)` restricts the shield bounds scan to the required global
z range (cm); `GetMuonShieldMinZ()` reports the limit. Shield bounds are built
lazily on the first charged propagation. A later request extending below the
limit automatically expands and rebuilds them, preserving backward propagation
and reuse with earlier vertices. The default is the complete map.

Input branches in a chain
-------------------------

Readers call `PrepareEntry(tree, entry)` before `GetEntry(entry)`. On each file
change they bind and type-check branches on that file's tree. All hit vectors,
DIS vectors, counts, weights and path-length buffers are cleared before each
read. UBT, SBT and SST hit branches are optional and become empty when
absent. TD hits, the total and all per-material path lengths, MC tracks and the
DIS payload are required (TD hit vectors may be empty). An absent or incompatible
required branch fails the read instead of reusing data from an earlier file. Replay rejects such input;
filtering/preparation do not process failed reads. Optional branches with an
incompatible type also fail the read.
