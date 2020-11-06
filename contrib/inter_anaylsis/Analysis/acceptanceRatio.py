#!/usr/bin/python3
from ROOT import TFile, TCanvas, TLegend, TH1F, TF1, TLine, kBlack, kBlue
from array import array
import os

os.mkdir('plots3')

correctmean = False

fd = TFile.Open("plots2/Data.root","read")
fm = TFile.Open("plots2/MCpure.root","read")
cd = fd.Get("canvas Data")
cm = fm.Get("canvas MCpure")
hid = cd.GetPrimitive("inter/hpd")
hfd = cd.GetPrimitive("full/hpd")
him = cm.GetPrimitive("inter/hpm")
hfm = cm.GetPrimitive("full/hpm")
hfm2 = cm.GetPrimitive("full/hpm-10GeV")

rebinListm = list(range(0,21))+list(range(22,32,2))+list(range(35,55,5))+[60,70,80,100,120,500]
hfmrebin = hfm.Rebin(len(rebinListm)-1,"hrmrebin",array('d',rebinListm))
himrebin = him.Rebin(len(rebinListm)-1,"hrmrebin",array('d',rebinListm))
hrm = hfmrebin.Clone()
hrm.Divide(himrebin)
rebinListd = list(range(0,60))+list(range(60,80,2))+list(range(80,120,4))+[120]
hfdrebin = hfd.Rebin(len(rebinListd)-1,"hrdrebin",array('d',rebinListd))
hidrebin = hid.Rebin(len(rebinListd)-1,"hrdrebin",array('d',rebinListd))
hrd = hfdrebin.Clone()
hrd.Divide(hidrebin)


legendr = TLegend(0.55,0.1,0.9,0.2)
legendr.AddEntry(hrd,"data","lp")
legendr.AddEntry(hrm,"MC inclusive","lp")

if correctmean:
  hrm.Scale(1/1.0002)
  hrd.Scale(1/0.9766)
else:
  fitm = TF1("fitMC","pol 0",30,120)
  hrm.Fit(fitm,"E","",30,120)
  fitd = TF1("fitData","pol 0",30,120)
  fitd.SetLineColor(kBlue)
  hrd.Fit(fitd,"E","",30,120)
"""
fitam = TF1("fitMCasymptote","[0]/([1]*e^([2]-x)+1)",5,100)
fitam.SetParLimits(0,0.9,1)
hrm.Fit(fitam,"E","",13,100)
fitad = TF1("fitDataasymptote","[0]/([1]*e^([2]-x)+1)",5,100)
fitad.SetParLimits(0,0.9,1)
fitad.SetLineColor(kBlue)
hrd.Fit(fitad,"E","",13,100)

fitm2 = TF1("fitMC2","[0]-[1]/(x-[2])",5,100)
fitm2.FixParameter(0,fitm.GetParameter(0))
hrm.Fit(fitm2,"E","",10,100)
fitd2 = TF1("fitData2","[0]-[1]/(x-[2])",5,100)
fitd2.SetLineColor(kBlue)
fitd2.FixParameter(0,fitd.GetParameter(0))
hrd.Fit(fitd2,"E","",10,100)
"""

cr = TCanvas("canvas ratio")
hrd.SetLineColor(kBlue)
hrm.SetAxisRange(5,120-0.5,"X")
hrm.SetMinimum(0.9)
hrm.SetMaximum(1.1)
hrm.GetXaxis().SetTitle("P [GeV/c]")
hrm.SetTitle("Acceptance ratio")
hrm.SetLineColor(2)
hrm.Draw("e")
hrd.Draw("same")
line = TLine(5,1,120,1)
line.SetLineColor(kBlack)
line.SetLineWidth(1)
line.Draw("same")
legendr.Draw()
cr.Print("plots3/AcceptanceRatio.pdf")

fo = TFile.Open("plots3/AcceptanceRatio.root","RECREATE")
cr.Write()
fo.Close()
