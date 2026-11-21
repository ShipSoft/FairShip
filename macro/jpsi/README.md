# Data map of the J/ψ generator

By default, `JpsiGenerator` (`shipgen/`) uses the NA50 normalisation and
rapidity shape below y_cm = 0.4 and the published SHiP Table 5 shape
(arXiv:2604.03661) up to y_cm = 2.0. A *data map* fitted to corrected J/ψ
yields in (y, p_T) cells can replace the shape above y_cm = 0.6:

    w(y, pT) = exp(D (b1 + b2 D) + c D (min(pT², 16) − 1.5)),   D = clamp(y − 0.6, 0, 1)

Above the end of the map (y_cm = 1.6) the SHiP table continues it, scaled to
the map there. If the map file also has a fitted forward exponent (`tail_n`,
written by `JpsiDataMap.C`), the map is continued instead with
dN/dx_F ∝ (1 − |x_F|)^n from its end (`forward_tail map`), so no table bin is
used with the map.

The map is not built in. It is read from a file through a configuration file
(`data_map <file>`, relative paths are taken from the configuration file's
directory), with `run_fixedTarget.py --jpsi-config` or `makeJpsiNtuple
--config`. The map file and the configuration text are stored in the output
(`FileSummary`).

This folder holds the code that fits a map.

| file | what it does |
|---|---|
| `DumpTargetLayers.C` | the target slabs of a geometry file as a layer file |
| `makeJpsiNtuple.cxx` | generator samples, among them the map base (built as `build/bin/makeJpsiNtuple`) |
| `JpsiDataMap.C` | the fit; writes the map file |
| `target_2018.txt` | the 2018 target (Mo and W slabs) |
| `../../shipgen/JpsiDataMapFit.h` | the fit model; minimised with Minuit2 (tested by `tests/test_jpsi_datamap_fit.cxx`) |

## Fitting a map

Run from the FairShip source directory, in the FairShip environment.

1. **Target.** `target_2018.txt` comes from the geometry of the 2018 simulation
   (the geometry file of the muon-flux data, `muflux_geofile.root`, has no target):

   ```
   root -l -b -q 'macro/jpsi/DumpTargetLayers.C("/eos/experiment/ship/data/muflux/MC/geofile_full.conical.MuonBack-TGeant4.root","target_2018.txt")'
   ```

2. **Base configuration.** The map corrects one p_T model and polarisation;
   the sampler refuses it on another one (unless `map_base_check 0`). Write
   them in a configuration file, for example `base.cfg`:

   ```
   ptsq 1.9
   pt_sq_slope 0
   lambda 0.11
   ```

   `lambda 0.11` is the built-in polarisation (the SHiP measurement); a map
   fitted on it can be used with the default configuration.

3. **Map base**: the generator with the NA50 shape and the map at zero, on the
   2018 target, keeping J/ψ whose muons can reach the fiducial region:

   ```
   build/bin/makeJpsiNtuple -n 4000000 --layers macro/jpsi/target_2018.txt \
       --config base.cfg --map-base --mu-pmin 20 --mu-thmax 0.1 \
       --out gen_mapbase.root
   ```

4. **Corrected data.** The fit takes `acceptance.root` files of a J/ψ
   analysis of the 2018 data (not part of FairShip). They hold the corrected
   fiducial J/ψ yields per POT in y × p_T cells (`corr_cell2`, the fit input),
   in p_z × p_T cells (`corr_cell1`, a check) and in y (`corr_y`), with the
   cell edges and the POT. An optional second file with a variation of the
   selection decides which cells have a stable acceptance.

5. **Fit**:

   ```
   root -l -b -q 'macro/jpsi/JpsiDataMap.C+("acceptance.root","gen_mapbase.root","jpsi_datamap.txt","jpsi_datamap","acceptance_variation.root")' > jpsi_datamap.log 2>&1
   ```

   The log lists the nested fits (N only, + b1, + b2, + c), the cells used, and
   the checks (p_z × p_T cells, binned ⟨p_T²⟩), before and after the map.

   It then fits the forward exponent n to `corr_y` from y_cm = 1.0 (last
   argument) to its last bin, with the normalisation free: the base events are
   reweighted with the sampler's own joint densities, so the fit uses the
   generator's p_T spectrum and kinematic limit. n is also printed for fits
   from 0.8 and 1.2, with the χ² at the built-in n = 5.5, and the generator
   with the fitted map and either continuation is compared with `corr_y` bin
   by bin (`4_forward_tail.png`). The map file gets `tail_n` and `tail_n_err`.

6. **Use.** A configuration file with the base settings and the map:

   ```
   ptsq 1.9
   pt_sq_slope 0
   data_map jpsi_datamap.txt
   ```

   Each key may appear once, in any order. The map file also records the
   base it was fitted on; `map_b1`, `map_b2` and `map_c` vary the parameters
   within their errors. `forward_tail table` and `tail 5.5` go back to the table
   continuation with the Table 5 exponent above y_cm = 2.0;
   `tail <n>` varies the fitted exponent.

## Nuclear dependence of the shape

The shape is measured on one target (the 2018 target: J/ψ made 98% in Mo).
`alpha_xf <a1> <a2> [<A>]` multiplies the (y, p_T) density by
(A_eff / A)^(a1 x_F + a2 x_F²), where A is the mass number of the target the
shape was measured on (default 95.95) and A_eff the J/ψ-weighted mass number of
the target model (`a_eff` in the stored settings; 183.8 for a W target). It
describes σ ∝ A^α(x_F) with α falling at large x_F. Off by default: NA60 at
400 GeV sees no x_F dependence for −0.075 < x_F < 0.125, so values from higher
energies are a systematic variation, not a default.
