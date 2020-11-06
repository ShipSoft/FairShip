This folder contains all the relevant files for plotting the momentum distribution.

For creating histogram files: 

- makeHisto.py XXXXX-Y
  creates histograms hppt, hp and hpt of the ntuple.

- setup.py
  creates a list of XXXXX-Y.
  creates a HTCondor submit file that loops over the ntuples.
  creates all relevant directories for the output.

- HTCondorPlotHistos.sub
  created from setup.py.
  to submit jobs, do
  > condor_submit HTCondorPlotHistos.sub

For checking potential errors in HTCondor:

- checkErrorInLog.py output/$(ClusterId).log
  checks that all jobs in a cluster are terminated with exit code 0.

- checkMissingFiles.py
  checks that all files are transferred back from HTCondor.

After creating all the relevant histogram files: 

- addHisto.py
  adds all histograms together.
