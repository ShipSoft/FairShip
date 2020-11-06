#!/usr/bin/python3
from ROOT import TFile
from array import array

f = TFile.Open("plots/inter-MC-ComparisonChi2mu_P.root","open")
c = f.Get("c")
hd = c.GetPrimitive("inter/hpd")
hM = c.GetPrimitive("inter/hpM")
rebinList = [0,5,10,25,50,75,100,125,150,200,250,300,500]
hdrebin = hd.Rebin(len(rebinList)-1,"hdrebin",array('d',rebinList))
hMrebin = hM.Rebin(len(rebinList)-1,"hMrebin",array('d',rebinList))
hdrebin.Scale(1e9)
hMrebin.Scale(1e9)
print("{:>14}{:^11}{:^10}{:^10}{:^10}{:^10}{:^10}".format("Interval","data","error","MC","error","ratio","error"))
formatlist = " {:>13} {:>10.3f} {:>9.3f} {:>9.3f} {:>9.3f} {:>9.3f} {:>9.3f}"
bins = ["5-10 GeV/c","10-25 GeV/c","25-50 GeV/c","50-75 GeV/c","75-100 GeV/c","100-125 GeV/c","125-150 GeV/c","150-200 GeV/c","200-250 GeV/c","250-300 GeV/c"]
widths = [5,15,25,25,25,25,25,50,50,50]
print
for i in range(10):
  data = hdrebin.GetBinContent(i+2)
  mccc = hMrebin.GetBinContent(i+2)
  dataerror = hdrebin.GetBinError(i+2)
  mcccerror = hMrebin.GetBinError(i+2)
  datacombinederror = ((dataerror/data)**2+0.024**2)**0.5
  mccccombinederror = ((mcccerror/mccc)**2+0.033**2)**0.5
  ratioerror = (datacombinederror**2+mccccombinederror**2)**0.5
  width = widths[i]
  bin = bins[i]
  print(formatlist.format(bin, data/width, datacombinederror*data/width ,mccc/width, mccccombinederror*mccc/width, data/mccc, ratioerror*data/mccc))
