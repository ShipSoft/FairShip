#!/usr/bin/python3
import os, sys, subprocess

def error():
  print("Correct usage: python setRun.py #run")
  print("#run = 2383,2388,2389,2390,2392,2395,2396")
  print("optional: use -f to specify JobFlavour.")
  print("flavours = espresso, microcentury, longlunch, workday, tomorrow, testmatch, nextweek")

eosship = "root://eospublic.cern.ch/"
eospath = "/eos/experiment/ship/user/truf/muflux-reco/"
runs = ['2383','2388','2389','2390','2392','2395','2396'] # intermediate fields
flavours = ["espresso","microcentury","longlunch","workday","tomorrow","testmatch","nextweek"]

if len(sys.argv) != 2 and len(sys.argv) != 4:
  print("Error: number of arguments does not match.")
  error()
elif not sys.argv[1] in runs:
  print("Error: #run specified is not done in intermediate field.")
  error()
else:
  flavour = "espresso"
  if len(sys.argv) == 4:
    if sys.argv[2] != "-f":
      print("Warning: "+sys.argv[2]+" is not an option.")
      print("Option is ignored.")
      error()
    elif not sys.argv[3] in flavours:
      print("Warning: "+sys.argv[3]+" is not a valid JobFlavour.")
      print("Option is ignored.")
      error()
    else:
      flavour = sys.argv[3]
  # -----Create list-----
  temp = subprocess.check_output("xrdfs "+eosship+" ls "+eospath+"RUN_8000_"+sys.argv[1],shell=True).decode()
  rf = open("runList.txt","w")
  for f in temp.split("\n"):
    if f.find("ntuple")!=-1 and f.find("refit")!=-1:
      rf.write(f[f.find("ntuple"):]+"\n")
  rf.close()
  # -----Write submit description file-----
  rc = open("HTCondorPlotHistos.sub","w")
  rc.write("executable            = makeHisto.py\n")
  rc.write("arguments             = $(inFile) "+sys.argv[1]+"\n")
  rc.write("output                = stdout/RUN_8000_"+sys.argv[1]+"/$(inFile).out\n")
  rc.write("error                 = stderr/RUN_8000_"+sys.argv[1]+"/$(inFile).err\n")
  rc.write("log                   = log/$(ClusterId).log\n")
  rc.write("\n")
  rc.write("requirements            = (CERNEnvironment =!= \"qa\") && (Machine =!= LastRemoteHost)\n")
  rc.write("should_transfer_files   = YES\n")
  rc.write("when_to_transfer_output = ON_EXIT\n")
  rc.write("transfer_output_remaps  = \"output.root = output/RUN_8000_"+sys.argv[1]+"/histo-$(inFile)\"\n")
  rc.write("+JobFlavour             = \""+flavour+"\"\n")
  rc.write("\n")
  rc.write("on_exit_remove          = (ExitBySignal == False) && (ExitCode == 0)\n")
  rc.write("max_retries             = 5\n")
  rc.write("\n")
  rc.write("queue inFile from runList.txt\n")
  rc.close()
  # -----Create directories if they do not already exist-----
  dirList = ["stdout","stdout/RUN_8000_"+sys.argv[1],"stderr","stderr/RUN_8000_"+sys.argv[1],"log","output","output/RUN_8000_"+sys.argv[1]]
  for dir in dirList:
    if not os.path.exists(dir):
      os.mkdir(dir)
