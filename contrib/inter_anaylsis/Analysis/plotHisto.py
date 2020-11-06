#!/usr/bin/python3
#Usage: python3 fullHisto.py [option] [argument]
import sys, os, argparse
from ROOT import TFile, TCanvas, TLegend, gROOT

class SmartFormatter(argparse.HelpFormatter):

  def _split_lines(self, text, width):
    if text.startswith('R|'):
      return text[2:].splitlines()
    # this is the RawTextHelpFormatter._split_lines
    return argparse.HelpFormatter._split_lines(self, text, width)

# -----deal with options-----
parser = argparse.ArgumentParser(description="Plot momentum distribution histograms stored in root files.", formatter_class=SmartFormatter)
# parser.add_argument('-i', required=True, metavar='inFile.root',help="path and name of the input root file, required", dest='inFile')
parser.add_argument('-o', metavar='outFile.pdf',help="R|name of the output file\nif not specified, it is test.pdf", dest='outFile')
parser.add_argument('--plottype', required=True, help="R|types of 1D plot:\n""  P        = momentum distribution\n""  Pt       = transverse momentum distribution\n""  PtSlice  = Pt distribution in a slice of P\n""types of 2D plot:\n""  PtPratio = ratio of data to MC tracks in bins of Pt and P\n""  PtP      = distribution in Pt and P for data", choices=['P','Pt','PtSlice','PtPratio','PtP'])
parser.add_argument('--xmin', type=int, help="minimum of x-axis variable")
parser.add_argument('--xmax', type=int, help="maximum of x-axis variable")
parser.add_argument('--xrebin', type=int, metavar='N', help="combine every N bins into one in the x-axis")
parser.add_argument('--yrebin', type=int, metavar='N', help="combine every N bins into one in the y-axis")
parser.add_argument('--ymin', type=int, help="minimum of y-axis variable")
parser.add_argument('--ymax', type=int, help="maximum of y-axis variable")
#parser.add_argument('--yrebin', type=int, metavar='N', help="combine every N bins into one in the y-axis")
parser.add_argument('-l','--log', action='store_true', help="display data in log scale")
args = parser.parse_args()

# -----set up file I/O-----
inFileData  = "Histograms/histo-intermediate-data.root"
inFileMbias = "Histograms/histo-intermediate-mbias-nocharm.root"
inFileCharm = "Histograms/histo-intermediate-charm.root"
outFile = "test.pdf"
if args.outFile:
  outFile = args.outFile
  
outPath ="plots/"
if not os.path.exists(outPath):
  os.mkdir(outPath)

gROOT.SetBatch(1)
fd = TFile.Open(inFileData,"read")
fm = TFile.Open(inFileMbias,"read")
fc = TFile.Open(inFileCharm,"read")

PoTperMuEvent = 625
MuEventData = 31205773
efficiencyCorrectionMC = (1-0.018)
PoTData = PoTperMuEvent * MuEventData
PoTMbias = 1.806e9
PoTCharm = 10.21e9

# -----plot P histogram-----
if args.plottype == 'P':
  hpd = fd.Get("hp")
  hpm = fm.Get("hp")
  hpc = fc.Get("hp")
  hp2 = fm.Get("hp2")
  hp3 = fm.Get("hp3")
  hp4 = fm.Get("hp4")
  hp7 = fm.Get("hp7")
  hpd.SetNameTitle("inter/hpd","P")
  hpm.SetNameTitle("inter/hpm","P")
  hpc.SetNameTitle("inter/hpc","P")
  hp2.SetNameTitle("inter/hp2","P")
  hp3.SetNameTitle("inter/hp3","P")
  hp4.SetNameTitle("inter/hp4","P")
  hp7.SetNameTitle("inter/hp7","P")
  # -----rebinning and scaling----------------------------
  if args.xrebin:
    hpd.Rebin(int(args.xrebin))
    hpm.Rebin(int(args.xrebin))
    hpc.Rebin(int(args.xrebin))
    hp2.Rebin(int(args.xrebin))
    hp3.Rebin(int(args.xrebin))
    hp4.Rebin(int(args.xrebin))
    hp7.Rebin(int(args.xrebin))
  hpd.Scale(1/PoTData)
  hpm.Scale(efficiencyCorrectionMC/PoTMbias)
  hp2.Scale(efficiencyCorrectionMC/PoTMbias)
  hp3.Scale(efficiencyCorrectionMC/PoTMbias)
  hp4.Scale(efficiencyCorrectionMC/PoTMbias)
  hp7.Scale(efficiencyCorrectionMC/PoTMbias)
  hpc.Scale(efficiencyCorrectionMC/PoTCharm)
  hpM = hpm.Clone()
  hpM.Add(hpc)
  hpM.SetNameTitle("inter/hpM","P")
  # -----drawing histograms-------------------------------
  c = TCanvas("c")
  c.SetLogy(args.log)
  xmin = 5
  xmax = 300
  if args.xmin:
    xmin = args.xmin
  if args.xmax:
    xmax = args.xmax
  hpd.SetAxisRange(xmin,xmax-0.5,"X")
  hpd.SetStats(0)
  hpd.GetXaxis().SetTitle("P [GeV/c]")
  hpd.GetYaxis().SetTitle("N [/(GeV/c)/POT]")
  hpd.Draw("h")
  hpM.SetLineColor(2)
  hpM.Draw("same")
  hpc.SetLineColor(3)
  hpc.Draw("same")
  hp2.SetLineColor(433)
  hp2.Draw("same")
  hp3.SetLineColor(8)
  hp3.Draw("same")
  hp4.SetLineColor(634)
  hp4.Draw("same")
  hp7.SetLineColor(7)
  hp7.Draw("same")
  legend = TLegend(0.55,0.6,0.9,0.9)
  legend.AddEntry(hpd,"data","l")
  legend.AddEntry(hpM,"MC inclusive","l")
  legend.AddEntry(hpc,"Charm","l")
  legend.AddEntry(hp7,"Dimuon from decays P8","l")
  legend.AddEntry(hp2,"Dimuon from decays G4","l")
  legend.AddEntry(hp3,"Photon conversion","l")
  legend.AddEntry(hp4,"Positron annihilation","l")
  legend.Draw()
  
# ----plot Pt histogram-----
elif args.plottype == 'Pt':
  hptd = fd.Get("hpt")
  hptm = fm.Get("hpt")
  hptc = fc.Get("hpt")
  hpt2 = fm.Get("hpt2")
  hpt3 = fm.Get("hpt3")
  hpt4 = fm.Get("hpt4")
  hpt7 = fm.Get("hpt7")
  hptd.SetNameTitle("inter/hptd","P_{T}")
  hptm.SetNameTitle("inter/hptm","P_{T}")
  hptc.SetNameTitle("inter/hptc","P_{T}")
  hpt2.SetNameTitle("inter/hpt2","P_{T}")
  hpt3.SetNameTitle("inter/hpt3","P_{T}")
  hpt4.SetNameTitle("inter/hpt4","P_{T}")
  hpt7.SetNameTitle("inter/hpt7","P_{T}")
  # -----rebinning and scaling----------------------------
  if args.xrebin:
    hptd.Rebin(int(args.xrebin))
    hptm.Rebin(int(args.xrebin))
    hptc.Rebin(int(args.xrebin))
    hpt2.Rebin(int(args.xrebin))
    hpt3.Rebin(int(args.xrebin))
    hpt4.Rebin(int(args.xrebin))
    hpt7.Rebin(int(args.xrebin))
  hptd.Scale(1/PoTData)
  hptm.Scale(efficiencyCorrectionMC/PoTMbias)
  hpt2.Scale(efficiencyCorrectionMC/PoTMbias)
  hpt3.Scale(efficiencyCorrectionMC/PoTMbias)
  hpt4.Scale(efficiencyCorrectionMC/PoTMbias)
  hpt7.Scale(efficiencyCorrectionMC/PoTMbias)
  hptc.Scale(efficiencyCorrectionMC/PoTCharm)
  hptM = hptm.Clone()
  hptM.Add(hptc)
  hptM.SetNameTitle("inter/hptM","P")
  # -----drawing histograms-------------------------------
  c = TCanvas("c")
  c.SetLogy(args.log)
  xmin = 0
  xmax = 4
  if args.xmin:
    xmin = args.xmin
  if args.xmax:
    xmax = args.xmax
  hptd.SetAxisRange(xmin,xmax-0.05,"X")
  hptd.SetStats(0)
  hptd.GetXaxis().SetTitle("P_{T} [GeV/c]")
  hptd.GetYaxis().SetTitle("N [/(GeV/c)/POT]")
  hptd.Draw("h")
  hptM.SetLineColor(2)
  hptM.Draw("same")
  hptc.SetLineColor(3)
  hptc.Draw("same")
  hpt2.SetLineColor(433)
  hpt2.Draw("same")
  hpt3.SetLineColor(8)
  hpt3.Draw("same")
  hpt4.SetLineColor(634)
  hpt4.Draw("same")
  hpt7.SetLineColor(7)
  hpt7.Draw("same")
  legend = TLegend(0.55,0.6,0.9,0.9)
  legend.AddEntry(hptd,"data","l")
  legend.AddEntry(hptM,"MC inclusive","l")
  legend.AddEntry(hptc,"Charm","l")
  legend.AddEntry(hpt7,"Dimuon from decays P8","l")
  legend.AddEntry(hpt2,"Dimuon from decays G4","l")
  legend.AddEntry(hpt3,"Photon conversion","l")
  legend.AddEntry(hpt4,"Positron annihilation","l")
  legend.Draw()
  
# -----plot PtSlice histogram-----
elif args.plottype == 'PtSlice':
  hpptd = fd.Get("hppt")
  hpptm = fm.Get("hppt")
  hpptc = fc.Get("hppt")
  hppt2 = fm.Get("hppt2")
  hppt3 = fm.Get("hppt3")
  hppt4 = fm.Get("hppt4")
  hppt7 = fm.Get("hppt7")
  xmin = 0
  xmax = 4
  ymin = 5
  ymax = 10
  if args.xmin:
    xmin = args.xmin
  if args.xmax:
    xmax = args.xmax
  if args.ymin:
    ymin = args.ymin
  if args.ymax:
    ymax = args.ymax
  # -----sum P in a given range---------------------------
  for j in range(xmax*10):
    for i in range(ymin):
      hpptd.SetBinContent(i+1,j+1,0)
      hpptm.SetBinContent(i+1,j+1,0)
      hpptc.SetBinContent(i+1,j+1,0)
      hppt2.SetBinContent(i+1,j+1,0)
      hppt3.SetBinContent(i+1,j+1,0)
      hppt4.SetBinContent(i+1,j+1,0)
      hppt7.SetBinContent(i+1,j+1,0)
    for i in range(ymax,300):
      hpptd.SetBinContent(i+1,j+1,0)
      hpptm.SetBinContent(i+1,j+1,0)
      hpptc.SetBinContent(i+1,j+1,0)
      hppt2.SetBinContent(i+1,j+1,0)
      hppt3.SetBinContent(i+1,j+1,0)
      hppt4.SetBinContent(i+1,j+1,0)
      hppt7.SetBinContent(i+1,j+1,0)
  hsliced = hpptd.ProjectionY().Clone()
  hslicem = hpptm.ProjectionY().Clone()
  hslicec = hpptc.ProjectionY().Clone()
  hslice2 = hppt2.ProjectionY().Clone()
  hslice3 = hppt3.ProjectionY().Clone()
  hslice4 = hppt4.ProjectionY().Clone()
  hslice7 = hppt7.ProjectionY().Clone()
  # -----rebinning and scaling----------------------------
  if args.xrebin:
    hsliced.Rebin(int(args.xrebin))
    hslicem.Rebin(int(args.xrebin))
    hslicec.Rebin(int(args.xrebin))
    hslice2.Rebin(int(args.xrebin))
    hslice3.Rebin(int(args.xrebin))
    hslice4.Rebin(int(args.xrebin))
    hslice7.Rebin(int(args.xrebin))
  hsliced.Scale(1/PoTData)
  hslicem.Scale(efficiencyCorrectionMC/PoTMbias)
  hslice2.Scale(efficiencyCorrectionMC/PoTMbias)
  hslice3.Scale(efficiencyCorrectionMC/PoTMbias)
  hslice4.Scale(efficiencyCorrectionMC/PoTMbias)
  hslice7.Scale(efficiencyCorrectionMC/PoTMbias)
  hslicec.Scale(efficiencyCorrectionMC/PoTCharm)
  hsliceM = hslicem.Clone()
  hsliceM.Add(hslicec)
  # -----renaming histograms------------------------------
  hsliced.SetNameTitle("inter/hsliced","P_{T} for "+str(ymin)+" < P < "+str(ymax)+" GeV/c")
  hsliceM.SetNameTitle("inter/hsliceM","P_{T} for "+str(ymin)+" < P < "+str(ymax)+" GeV/c")
  hslicec.SetNameTitle("inter/hslicec","P_{T} for "+str(ymin)+" < P < "+str(ymax)+" GeV/c")
  hslice2.SetNameTitle("inter/hslice2","P_{T} for "+str(ymin)+" < P < "+str(ymax)+" GeV/c")
  hslice3.SetNameTitle("inter/hslice3","P_{T} for "+str(ymin)+" < P < "+str(ymax)+" GeV/c")
  hslice4.SetNameTitle("inter/hslice4","P_{T} for "+str(ymin)+" < P < "+str(ymax)+" GeV/c")
  hslice7.SetNameTitle("inter/hslice7","P_{T} for "+str(ymin)+" < P < "+str(ymax)+" GeV/c")
  # -----drawing histograms-------------------------------
  c = TCanvas("c")
  c.SetLogy(args.log)
  hsliced.SetStats(0)
  hsliceM.SetStats(0)
  hsliced.GetXaxis().SetTitle("P_{T} [GeV/c]")
  hsliceM.GetXaxis().SetTitle("P_{T} [GeV/c]")
  hsliced.Scale(PoTData)
  hsliceM.Scale(PoTData)
  hslicec.Scale(PoTData)
  hsliceM.SetLineColor(2)
  hslicec.SetLineColor(3)
  hslice2.SetLineColor(433)
  hslice3.SetLineColor(8)
  hslice4.SetLineColor(634)
  hslice7.SetLineColor(7)
  """
  hsliced.SetAxisRange(xmin,xmax-0.05,"X")
  hsliceM.SetAxisRange(xmin,xmax-0.05,"X")
  hslicec.SetAxisRange(xmin,xmax-0.05,"X")
  hslice2.SetAxisRange(xmin,xmax-0.05,"X")
  hslice3.SetAxisRange(xmin,xmax-0.05,"X")
  hslice4.SetAxisRange(xmin,xmax-0.05,"X")
  hslice7.SetAxisRange(xmin,xmax-0.05,"X")
  hsliced.SetMinimum(0)
  hsliceM.SetMinimum(0)
  hslicec.SetMinimum(0)
  hslice2.SetMinimum(0)
  hslice3.SetMinimum(0)
  hslice4.SetMinimum(0)
  hslice7.SetMinimum(0)
  """
  if hsliceM.GetMaximum() > hsliced.GetMaximum():
    hsliceM.Draw()
    hsliced.Draw("hist same")
  else:
    hsliced.Draw("hist")
    hsliceM.Draw("same")
  hslicec.Draw("same")
  hslice2.Draw("same")
  hslice3.Draw("same")
  hslice4.Draw("same")
  hslice7.Draw("same")
  legend = TLegend(0.55,0.6,0.9,0.9)
  legend.AddEntry(hsliced,"data","l")
  legend.AddEntry(hsliceM,"MC inclusive","l")
  legend.AddEntry(hslicec,"Charm","l")
  legend.AddEntry(hslice7,"Dimuon from decays P8","l")
  legend.AddEntry(hslice2,"Dimuon from decays G4","l")
  legend.AddEntry(hslice3,"Photon conversion","l")
  legend.AddEntry(hslice4,"Positron annihilation","l")
  legend.Draw()
  
# -----plot PtPratio histogram-----
elif args.plottype == 'PtPratio':
  c = TCanvas("c")
  hpptd = fd.Get("hppt")
  hpptm = fm.Get("hppt")
  hpptc = fc.Get("hppt")
  hpptd.Rebin2D(25,5)
  hpptm.Rebin2D(25,5)
  hpptc.Rebin2D(25,5)
  hpptd.Scale(1/PoTData)
  hpptm.Scale(efficiencyCorrectionMC/PoTMbias)
  hpptc.Scale(efficiencyCorrectionMC/PoTCharm)
  hpptM = hpptm.Clone()
  hpptM.Add(hpptc)
  hpptRatio = hpptd.Clone()
  hpptRatio.Divide(hpptM)
  hpptRatio.GetXaxis().SetTitle("P [GeV/c]")
  hpptRatio.GetYaxis().SetTitle("P_{T} [GeV/c]")
  hpptRatio.SetNameTitle("inter/hpptratio","Ratio of data to MC tracks")
  hpptRatio.SetAxisRange(0,300-12.5,"X")
  hpptRatio.SetAxisRange(0,4-0.25,"Y")
  hpptRatio.SetStats(0)
  hpptRatio.Draw("TEXT")
  
# -----plot PtP histogram-----
elif args.plottype == 'PtP':
  c = TCanvas("c")
  c.SetLogz(args.log)
  hppt = fd.Get("hppt")
  xmin = 0
  xmax = 300
  ymin = 0
  ymax = 3.9
  if args.xmin:
    xmin = args.xmin
  if args.xmax:
    xmax = args.xmax
  if args.ymin:
    ymin = args.ymin
  if args.ymax:
    ymax = args.ymax
  hppt.SetAxisRange(xmin,xmax-0.5,"X")
  hppt.SetAxisRange(ymin,ymax-0.05,"Y")
  hppt.SetStats(0)
  hppt.GetXaxis().SetTitle("P [GeV/c]")
  hppt.GetXaxis().CenterTitle()
  hppt.GetYaxis().SetTitle("P_{T} [GeV/c]")
  hppt.GetYaxis().CenterTitle()
  hppt.GetXaxis().SetTitleOffset(1.5)
  if args.xrebin:
    hppt.RebinX(int(args.xrebin))
  if args.yrebin:
    hppt.RebinY(int(args.yrebin))
  hppt.SetNameTitle("inter/hpptd","P_{T} vs P")
  hppt.Draw("lego")
  c.SetPhi(224)
  
c.Print(outPath+outFile)
fo = TFile.Open(outPath+outFile.replace("pdf","root"),"RECREATE")
c.Write()
fo.Close()
