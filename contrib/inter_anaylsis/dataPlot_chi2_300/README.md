This folder contains all the relevant files for plotting the momentum distribution.

Settings:

- chi2 < 0.9

- momentum range: 0 - 300 GeV

For creating histogram files: 

- makeHisto.py [inFile] [run]
  creates histograms hppt, hp and hpt of the ntuple.

- setRun.py [run] [optional: -f JobFlavour]
  creates a list of ntuples from the specified run.
  creates a HTCondor submit file that loops over the ntuples.
  creates all relevant directories for the output.

- HTCondorPlotHistos.sub
  created from setRun.py.
  to submit jobs, do
  > condor_submit HTCondorPlotHistos.sub

For checking potential errors in HTCondor:

- checkErrorInLog.py output/$(ClusterId).log
  checks that all jobs in a cluster are terminated with exit code 0.

- checkMissingFiles.py
  check that all files are transferred back from HTCondor.

After creating all the relevant histogram files: 

- addHisto.py [arg:run/TOTAL/LOOP]
  adds all histograms together in a run/ all runs/ for each run.
