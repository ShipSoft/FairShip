### This folder contains scripts that make comparison plots between data, MC and its contributions.

- `plotHisto.py`
  - creates momentum, transverse momentum, slices of transverse momentum, ratio data/MC, and momentum/ transverse momeutum (3D plot).
  - to see all options use `plotHisto.py -h`
  - assume all root files generated from `/dataPlot_chi2_300/`, `/mbiasPlot-nocharm_chi2_300/` and `/charmPlot_chi2_300/` are stored in `/IntermediateField/Histograms/`.

- `loop.sh`
  - loop over plotHisto.py with default options.

- `printBinnedTable.py`
  - print count and error in each bin, normalised to 10<sup>9</sup> POT.

