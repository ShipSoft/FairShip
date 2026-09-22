# Data-driven J/psi generator for FairShip

Replaces Pythia8 for this one channel. Production kinematics come from NA50
(400 GeV p-W) and the SHiP 2018 testbeam; the absolute rate comes from the NA50
tungsten anchor, scaled with A^0.925 and, when a target model is given,
integrated over the real material stack. The decay is done directly in the
Collins–Soper frame. The **nominal generation weight is identical event by
event**, so the effective sample size equals the number of events. (Optional
systematic reweighting, for example in polarisation, breaks that by
construction — see below.)

## Files

| File | Role |
| --- | --- |
| `JpsiSampler.h/.cxx` | physics core, no ROOT or FairRoot dependency |
| `JpsiGenerator.h/.cxx` | FairShip front end (`SHiP::Generator`) |
| `makeJpsiNtuple.cxx` | optional standalone ntuple writer |
| `test_JpsiSampler.cxx` | self-test, runs in a few seconds |

```
g++ -O2 -std=c++17 test_JpsiSampler.cxx JpsiSampler.cxx -o test_jpsi && ./test_jpsi
```

## Normalisation

```
rate  = P(J/psi -> mu mu) per POT            if a target model is given
      = chi_mumu per interacting proton      otherwise
rate /= BR                                   for the inclusive Jpsi output
weight = nPot * rate / nEvents               enhancement E = 1 / weight
```

The rate depends on the output mode, so an inclusive J/psi sample is *not*
normalised like a dimuon one: its weight is larger by 1/BR = 16.78. The test
suite checks this explicitly.

Everything entering the weight is computed deterministically on fixed grids.
The rapidity acceptance `f_y` folds in the kinematic limit analytically —
at each y only p_T < p_T,max(y) is allowed, and the same factor is used for
generation and for the normalisation — so the weight does not depend on the
seed. The tests verify bit-identical `f_y`, `chi_mumu` and `weight` across
seeds.

The NA50 anchor is always used inside its own windows in rapidity and
|cos Θ_CS|. There is no switch to change that: a global factor of two on the
SHiP table cancels in the shape, which is all the SHiP data are used for. The
alternative convention is stored as `chi_mumu_fullcos_diagnostic` in the
metadata for comparison work only.

## Composition knob

`SetEnhancement(E)` or `SetNEvents(N)`. `E = 1` reproduces the physical rate for
the requested POT (weight 1 per event, about 9.5×10⁷ events for a 5×10¹³ spill);
`E = 10³` gives a thousand times more J/psi, each with weight 10⁻³. Weights stay
identical, so nothing is distorted; combining with a minimum-bias sample only
requires vetoing J/psi-descendant tracks there. `NEventsToGenerate()` returns
the count when the enhancement form is used.

## Physics knobs

| Setter | Default | Meaning |
| --- | --- | --- |
| `SetMom(p)` | 400 | beam momentum, GeV/c |
| `SetTargetMaterial("W"\|"Mo")` or `(A, rho)` | W | per-nucleon anchor when no geometry scan is used |
| `SetRapidityShape("data"\|"hybrid"\|"gauss")` | data | SHiP bins / power-law join / pure NA50 |
| `SetForwardTail(n)` | 6.0 | exponent of (1−\|x_F\|)^n above the data range |
| `SetDataRange(lo, hi)` | 0.4, 1.8 | SHiP bins used |
| `SetYMatch(y)` | 0.5 | Gaussian/tail join for the hybrid shape |
| `SetGaussian(mean, sigma)` | −0.2, 0.85 | NA50 Gaussian, e.g. 0.81 for the NA60 value |
| `SetPtSq(v)` | 1.9 | solves the NA50 mixture for this ⟨p_T²⟩ |
| `SetFHard(f)` | — | sets the mixture directly instead |
| `SetThermalSlope(T)` | 0.2867 | thermal slope, GeV |
| `SetThermalJacobian(bool)` | true | dN/dp_T ∝ p_T m_T K₁ or m_T K₁ |
| `SetPolarisation(lambda)` | 0 | CS polar coefficient, in decay *and* normalisation |
| `SetOutputMode("mumu"\|"jpsi"\|"both")` | mumu | also selects the normalisation |
| `SetSeed(s)` | 12345 | seeds the sampler; the beam offset uses `gRandom`, seeded by the macro |
| `SetSmearBeam(sigma)`, `SetPaintRadius(r)` | 0.8 cm, 5 cm | same beam profile and defaults as `FixedTargetGenerator` |

Configuration is validated in the constructor (T, p0, σ_y, f_hard ∈ [0,1],
λ ≥ −1, n_events > 0, layer geometry), so a bad setup fails at `Init()` rather
than producing NaNs later.

### Polarisation

The NA50 anchor is quoted inside |cos Θ_CS| < 0.5, and

```
f_cos(lambda) = (1 + lambda/12) / (2 (1 + lambda/3))
```

which is 0.5 only at λ = 0. `SetPolarisation` changes the decay angles and the
acceptance together, and χ_μμ scales as 1/f_cos. λ = 0.11 raises χ by 2.7%.

To study λ by reweighting an existing unpolarised sample instead, multiply by

```
w_pol = (1 + lambda cos^2 Theta_CS) / (1 + lambda/3)
```

for the angular shape **and** by `0.5 / f_cos(lambda)` for the normalisation.
The tests compare the generated cos Θ_CS distribution with the analytic density
for λ = −0.5, −0.14, +0.3 and +1.0.

## Vertex and mixed targets

Two options, and both give the vertex distribution *and* the absolute rate from
the same integral:

- `SetTargetCoordinates(z0, z1, x, y)` — scans the FairShip geometry along the
  beam axis with `gGeoManager->FindNode`, using
  `dP/dz = exp(−τ(z)) n_A(z) B_μμ σ_Jpsi(A(z))` with σ_Jpsi ∝ A^α. Take z0 and
  z1 from `ship_geo.target.z0` and `+ ship_geo.target.length`. The scan result
  is pushed into the sampler with `SetProbMuMuPerPot`, so a Mo/W target gets
  both the right vertex shape and the right rate.
- `AddLayer("Mo", 58.)`, `AddLayer("W", 92.)` — the same integral over an
  explicit slab stack, no geometry needed. Used by the standalone writer and
  the tests, which check that a thick pure-W stack reproduces χ_μμ to better
  than 1% and that the Mo/W stack gives 87% of it.

## FairShip integration

`fairship_jpsi.patch` does everything against current `main`: it adds the four
source files to `shipgen/`, registers them in `shipgen/CMakeLists.txt` and
`shipgen/LinkDef.h`, and adds the generator to both run macros:

- `macro/run_simScript.py` — `--JpsiData` plus `--jpsi-*` knobs. This is the
  main path: full SHiP geometry, standard `sim_<tag>.root` output, and the
  generator configuration written into the output's `FileSummary`.
- `macro/run_fixedTarget.py` — `--jpsi-data`. Needed for the splitting
  regression test, since only this macro can switch on `ShipStack` splitting
  (`--kaon-pion-splits`).

```bash
cd FairShip
git apply --check /path/to/fairship_jpsi.patch && git apply /path/to/fairship_jpsi.patch
pixi run build
pixi run python macro/run_simScript.py --JpsiData -n 10000 --tag jpsi_test
```

Do **not** call `Init()` on the generator yourself. The geometry only exists
once `run.Init()` has run, and `run.Init()` calls `Init()` on every registered
generator; that is when the target scan fixes the vertex CDF, the rate per POT
and the weight. `EventWeight()` and `NEventsToGenerate()` are therefore only
meaningful after `run.Init()`, which is where both macros read them.

### Weights and FairShip splitting

`ShipStack::PushTrack` multiplies a daughter's weight by its parent's when
splitting is enabled. The generator therefore pushes the truth-level J/psi
mother with **weight 1** and the two transported muons with the physical event
weight, so the muons carry w and not w² in either configuration. In
`"jpsi"` mode the J/psi is the transported particle and carries the inclusive
weight itself.

This still deserves a FairShip-level regression test with
`ShipStack::SetSplitting` enabled, which cannot be run outside a full build.

## Systematic variations

- forward tail: `SetForwardTail(5)` … `SetForwardTail(7)`
- rapidity model: `"gauss"` as the deliberately hard-forward extreme, `"hybrid"`
  as the smooth one
- NA60 width: `SetGaussian(-0.2, 0.81)`
- p_T: `SetPtSq(1.4)` … `SetPtSq(2.2)`, or `SetThermalJacobian(false)`
- polarisation: `SetPolarisation(±0.14)`, with the normalisation following
  automatically

## Standalone ntuple writer

Writes an `id:px:py:pz:E:M:mid:mpx:mpy:mpz:mE:w` ntuple plus the metadata. The
extra `w` column makes the file self-contained, but it is therefore **not** a
drop-in charm input: the charm reader ignores both the column and the
file-level metadata. For the direct integration the file is unnecessary.

## Known limitations

- The forward tail is integrated over the p_T spectrum rather than evaluated at
  a reference m_T, but y and p_T are still factorised apart from the kinematic
  limit — the same assumption the data analysis makes.
- Radiative J/psi → μμγ is not modelled (a few percent on the muon momenta).
- The model is an effective thick-target source, not a strictly primary one:
  its forward shape comes from a thick-target measurement. Do not add a cascade
  component on top without revisiting the decomposition.
- The geometry scan follows a single line at (x, y); a beam-spot-averaged scan
  would matter only for a strongly non-uniform target cross section.
