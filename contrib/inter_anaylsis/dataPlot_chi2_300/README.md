### This folder contains all the relevant files for plotting the momentum distribution.

Settings:

- runs: 2383,2388,2389,2390,2392,2395,2396
- chi2 < 0.9
- goodTrack == 111
- momentum range: 0 - 300 GeV
- transverse mometum range: 0 - 40 GeV

For creating histogram files: 

- makeHisto.py [inFile] [run]
  - creates histograms hppt, hp and hpt of the ntuple.

- setRun.py [run] [optional: -f JobFlavour]
  - creates a list of ntuples from the specified run.
  - creates a HTCondor submit file that loops over the ntuples.
  - creates all relevant directories for the output.

- HTCondorPlotHistos.sub
  - created from setRun.py.
  - to submit jobs, do `condor_submit HTCondorPlotHistos.sub`

For checking potential errors in HTCondor:

- checkError.py
  - checks that all jobs in each log are terminated with exit code 0.
  - checks that all files are transferred back from HTCondor.

After creating all the relevant histogram files: 

- addHisto.py [run/TOTAL/LOOP]
  - adds all histograms together in a run/ all runs/ for each run.
  
For counting event:

- trackEventCount.py
  - counts nTr in all runs without veto
