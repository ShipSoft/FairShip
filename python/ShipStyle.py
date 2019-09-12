from __future__ import print_function
# Global scope variables
from ROOT import *
from ROOT import Double
lhcbstyle = TStyle()     # general lhcb style
lhcbName  = TPaveText()  # standard lhcb text for plot
lhcbLabel = TText  # style for Ttext
lhcbLatex = TLatex #style for TLatex

# define names for colours
black=1
red=2
green=3
blue=4
yellow=5 
magenta=6
cyan=7
purple=9

def lhcbstyleSetup():

##################################
# PURPOSE:
#
# This macro defines a standard style for (black-and-white) 
# "publication quality" LHCb ROOT plots. 
#
# USAGE:
#
# Include the lines
#   gROOT.ProcessLine(".L lhcbstyle.C")
#   lhcbstyle()
# at the beginning of your root macro.
#
# Example usage is given in myPlot.C
#
# COMMENTS:
#
# Font:
# 
# The font is chosen to be 62, this is helvetica-bold-r-normal with
# precision 2.
#
# "Landscape histograms":
#
# The style here is designed for more or less square plots.
# For longer histograms, or canvas with many pads, adjustements are needed. 
# For instance, for a canvas with 1x5 histograms:
#  TCanvas* c1 = new TCanvas("c1", "L0 muons", 600, 800)
#  c1.Divide(1,5)
#  Adaptions like the following will be needed:
#  lhcbstyle.SetTickLength(0.05,"x")
#  lhcbstyle.SetTickLength(0.01,"y")
#  lhcbstyle.SetLabelSize(0.15,"x")
#  lhcbstyle.SetLabelSize(0.1,"y")
#  lhcbstyle.SetStatW(0.15)
#  lhcbstyle.SetStatH(0.5)
#
# Authors: Thomas Schietinger, Andrew Powell, Chris Parkes
# Maintained by Editorial board member (currently Chris)
#################################/

 lhcbstyle=TStyle("lhcbstyle","Standard LHCb plots style")

# use helvetica-bold-r-normal, precision 2 (rotatable)
 lhcbFont = 62
# line thickness
 lhcbWidth = int(3.00)

# use plain black on white colors
 lhcbstyle.SetFrameBorderMode(0)
 lhcbstyle.SetCanvasBorderMode(0)
 lhcbstyle.SetPadBorderMode(0)
 lhcbstyle.SetPadColor(0)
 lhcbstyle.SetCanvasColor(0)
 lhcbstyle.SetStatColor(0)
 lhcbstyle.SetPalette(1)

# set the paper & margin sizes
 lhcbstyle.SetPaperSize(20,26)
 lhcbstyle.SetPadTopMargin(0.05)
 lhcbstyle.SetPadRightMargin(0.05) # increase for colz plots
 lhcbstyle.SetPadBottomMargin(0.16)
 lhcbstyle.SetPadLeftMargin(0.14)

# use large fonts
 lhcbstyle.SetTextFont(lhcbFont)
 lhcbstyle.SetTextSize(0.08)
 lhcbstyle.SetLabelFont(lhcbFont,"x")
 lhcbstyle.SetLabelFont(lhcbFont,"y")
 lhcbstyle.SetLabelFont(lhcbFont,"z")
 lhcbstyle.SetLabelSize(0.04,"x")
 lhcbstyle.SetLabelSize(0.04,"y")
 lhcbstyle.SetLabelSize(0.04,"z")
 lhcbstyle.SetTitleFont(lhcbFont)
 lhcbstyle.SetTitleSize(0.05,"x")
 lhcbstyle.SetTitleSize(0.05,"y")
 lhcbstyle.SetTitleSize(0.05,"z")

# use bold lines and markers
 lhcbstyle.SetLineWidth(lhcbWidth)
 lhcbstyle.SetFrameLineWidth(lhcbWidth)
 lhcbstyle.SetHistLineWidth(lhcbWidth)
 lhcbstyle.SetFuncWidth(lhcbWidth)
 lhcbstyle.SetGridWidth(lhcbWidth)
 lhcbstyle.SetLineStyleString(2,"[12 12]") # postscript dashes
 lhcbstyle.SetMarkerStyle(20)
 lhcbstyle.SetMarkerSize(1.5)

# label offsets
 lhcbstyle.SetLabelOffset(0.015)

# by default, do not display histogram decorations:
 lhcbstyle.SetOptStat(0)  
 lhcbstyle.SetOptStat("emr")  # show only nent -e , mean - m , rms -r
# full opts at http:#root.cern.ch/root/html/TStyle.html#TStyle:SetOptStat
 lhcbstyle.SetStatFormat("6.3g") # specified as c printf options
 lhcbstyle.SetOptTitle(0)
 lhcbstyle.SetOptFit(0)
#lhcbstyle.SetOptFit(1011) # order is probability, Chi2, errors, parameters

# look of the statistics box:
 lhcbstyle.SetStatBorderSize(0)
 lhcbstyle.SetStatFont(lhcbFont)
 lhcbstyle.SetStatFontSize(0.05)
 lhcbstyle.SetStatX(0.9)
 lhcbstyle.SetStatY(0.9)
 lhcbstyle.SetStatW(0.25)
 lhcbstyle.SetStatH(0.15)
# put tick marks on top and RHS of plots
 lhcbstyle.SetPadTickX(1)
 lhcbstyle.SetPadTickY(1)

# histogram divisions: only 5 in x to avoid label overlaps
 lhcbstyle.SetNdivisions(505,"x")
 lhcbstyle.SetNdivisions(510,"y")


#define style for text
 lhcbLabel = TText()
 lhcbLabel.SetTextFont(lhcbFont)
 lhcbLabel.SetTextColor(1)
 lhcbLabel.SetTextSize(0.04)
 lhcbLabel.SetTextAlign(12)

# define style of latex text
 lhcbLatex = TLatex()
 lhcbLatex.SetTextFont(lhcbFont)
 lhcbLatex.SetTextColor(1)
 lhcbLatex.SetTextSize(0.04)
 lhcbLatex.SetTextAlign(12)

# set this style
 gROOT.SetStyle("lhcbstyle")
 gROOT.ForceStyle()


def printLHCb(optLR="L", optPrelim="Final", optText=""):
#####################################
# routine to print 'LHCb', 'LHCb Preliminary' on plots 
# options: optLR=L (top left) / R (top right) of plots
#          optPrelim= Final (LHCb), Prelim (LHCb Preliminary), Other
#          optText= text printed if 'Other' specified
##################################
  if optLR=="R" :   
    lhcbName = TPaveText(0.70 - lhcbstyle.GetPadRightMargin(),
                         0.75 - lhcbstyle.SetPadTopMargin(0.05),
                         0.95 - lhcbstyle.GetPadRightMargin(),
                         0.85 - lhcbstyle.SetPadTopMargin(0.05),
                         "BRNDC")
  elif optLR=="L":
    lhcbName = TPaveText(lhcbstyle.GetPadLeftMargin() + 0.05,
                         0.87 - lhcbstyle.GetPadTopMargin(),
                         lhcbstyle.GetPadLeftMargin() + 0.30,
                         0.95 - lhcbstyle.GetPadTopMargin(),
                                        "BRNDC")
  else :
   print("printLHCb: option unknown" , optLR)  
  if optPrelim=="Final":
    lhcbName.AddText("LHCb")
  elif optPrelim=="Prelim":
    lhcbName.AddText("#splitline{LHCb}{#scale[1.0]{Preliminary}}")  
  elif optPrelim=="Other":
    lhcbName.AddText(optText)
  else :
    print("printLHCb: option unknown " , optPrelim)
  lhcbName.SetFillColor(0)
  lhcbName.SetTextAlign(12)
  lhcbName.SetBorderSize(0)
  lhcbName.Draw()
