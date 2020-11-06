#!/usr/bin/python3
import os

# -----Create list-----
rf = open("runList.txt","w")
for XXXXX in range(0,20000,1000):
  for Y in range(5):
    rf.write(str(XXXXX)+"-"+str(Y)+"\n")
rf.close()
# -----Write submit description file-----
rc = open("HTCondorPlotHistos.sub","w")
rc.write("executable            = makeHisto.py\n")
rc.write("arguments             = $(inFile)\n")
rc.write("output                = stdout/$(ClusterId)-$(ProcId).out\n")
rc.write("error                 = stderr/$(ClusterId)-$(ProcId).err\n")
rc.write("log                   = log/$(ClusterId).log\n")
rc.write("\n")
rc.write("requirements            = (CERNEnvironment =!= \"qa\") && (Machine =!= LastRemoteHost)\n")
rc.write("should_transfer_files   = YES\n")
rc.write("when_to_transfer_output = ON_EXIT\n")
rc.write("transfer_output_remaps  = \"output.root = output/histo-$(inFile).root\"\n")
rc.write("+JobFlavour             = \"espresso\"\n")
rc.write("\n")
rc.write("on_exit_remove          = (ExitBySignal == False) && (ExitCode == 0)\n")
rc.write("max_retries             = 5\n")
rc.write("\n")
rc.write("queue inFile from runList.txt\n")
rc.close()
# -----Create directories if they do not already exist-----
dirList = ["stdout","stderr","log","output"]
for dir in dirList:
  if not os.path.exists(dir):
    os.mkdir(dir)
