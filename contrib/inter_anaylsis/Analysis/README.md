### This folder contains scripts that make comparison plots between data, MC and its contributions.

- `plotHisto.py`
  - creates momentum, transverse momentum, slices of transverse momentum, ratio data/MC, and momentum/ transverse momeutum (3D plot).
  - to see all options do `plotHisto.py -h`.
  - assume all root files generated from `/dataPlot_chi2_300/`, `/mbiasPlot-nocharm_chi2_300/` and `/charmPlot_chi2_300/` are stored in `/Analysis/Histograms/`.
  - plots are stored in `/plots/`.

- `loop.sh`
  - loop over plotHisto.py with default options.

- `compareFullInter.py`
  - assume `/Analysis/FullFieldData/MC-ComparisonChi2mu_linP.root` and `/Analysis/plots/inter-MC-ComparisonChi2mu_linP.root` exist.
  - creates comparison momentum plots between full and intermediate fields for each contribution.
  - plots are stored in `/plots2/`.

- `printBinnedTable.py`
  - print count and error in each bin, normalised to per 10<sup>9</sup> POT.

