#!/usr/bin/python3
# Usage: python3 checkError.py
import os, sys, subprocess

def checkLog(logname):
  logfile = "log/"+logname
  loglines = list(open(logfile))
  submitList = []
  goodTerminationList = []
  badTerminationList = []
  for i,line in enumerate(loglines):
    if line.find("Job submitted from host:") > 0:
      submitList.append(int(line[12:15]))
    termstrpos = line.find("(1) Normal termination (return value ")
    if termstrpos > 0:
      if line[termstrpos+37] == '0':
        goodTerminationList.append(int(loglines[i-1][12:15]))
      else:
        badTerminationList.append(int(loglines[i-1][12:15]))
  Nentries = len(submitList)
  goodTerminationList.sort()
  print("Number of jobs submitted                   : "+str(Nentries))
  print("Number of jobs terminated with exit code 0 : "+str(len(goodTerminationList)))
  if Nentries == len(goodTerminationList):
    print("All jobs terminated at exit code 0.")
  else:
    print("Some jobs are not executed at exit code 0.")
    print(badTerminationList)

loglist = subprocess.check_output("ls log",shell=True).decode().split("\n")
print("------------------------------------------------")
for log in loglist:
  if log:
    print("Log file: "+log)
    checkLog(log)
    print("------------------------------------------------")

fileList = subprocess.check_output("ls output",shell=True).decode().split("\n")
if len(fileList) - 1 == 100:
  print("There is no missing file.")
  sys.exit(0)

print("There is missing file(s).")
for XXXXX in range(0,20000,1000):
  for Y in range(5):
    if "histo-"+str(XXXXX)+"-"+str(Y)+".root" not in fileList:
      print("histo-"+str(XXXXX)+"-"+str(Y)+".root")
