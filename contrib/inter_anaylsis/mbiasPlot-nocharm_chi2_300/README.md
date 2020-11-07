### This folder contains all the relevant files for plotting the momentum distribution.

Settings:

- chi2 < 0.9
- goodTrack == 111
- momentum range: 0 - 300 GeV
- transverse mometum range: 0 - 40 GeV

For creating histogram files: 

- makeHisto.py XXXXX-Y
  - creates histograms hppt, hp and hpt of the ntuple.

- setup.py
  - creates a list of XXXXX-Y.
  - creates a HTCondor submit file that loops over the ntuples.
  - creates all relevant directories for the output.

- HTCondorPlotHistos.sub
  - created from setup.py.
  - to submit jobs, do `condor_submit HTCondorPlotHistos.sub`

For checking potential errors in HTCondor:

- checkError.py
  - checks that all jobs in each log are terminated with exit code 0.
  - checks that all files are transferred back from HTCondor.

After creating all the relevant histogram files: 

- addHisto.py
  - adds all histograms together.
