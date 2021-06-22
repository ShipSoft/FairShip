"""from the neutrinos produced by the FLUKA simulation, extract a subsample of interacting according to the GENIE cross section"""

import argparse
import ROOT as r

parser = argparse.ArgumentParser(description="Extract interacting neutrinos")
parser.add_argument(
    "--geniepath",
    type=str,
    dest="geniepath",
    default=None,
    help="Path of Genie simulated neutrinos interactions, where also to store the subsample of interacting Fluka neutrinos",
)
parser.add_argument(
    "--flukapath",
    type=str,
    dest="flukapath",
    default=None,
    help="Path of Fluka produced neutrinos",
)

options = parser.parse_args()

# inputfiles
geniefile = r.TFile.Open(options.geniepath, "UPDATE")
flukafile = r.TFile.Open(options.flukapath, "READ")
# Retrieve neutrino energy histogram from FLUKA file


def lookfornuhist(flukafile):
    """the actual name of the histograms depend on the neutrino we are reading,
    i loop over all possible candidates"""
    nup_histnames = ["1012", "1014", "1016", "2012", "2014", "2016"]
    myhist = r.TH1F()
    for name in nup_histnames:
        temphist = flukafile.Get(name)
        if temphist:
            myhist = temphist
    return myhist


hfluka_nuE = lookfornuhist(flukafile)
nbins = hfluka_nuE.GetNbinsX()
minE = hfluka_nuE.GetXaxis().GetBinLowEdge(1)
maxE = hfluka_nuE.GetXaxis().GetBinUpEdge(nbins)

# Draw neutrino energy from GENIE file (bins must be the same of fluka files)
df = r.RDataFrame("gst", geniefile)
hgenie_nuE = df.Histo1D(
    (
        "hgenie_nuE",
        "Energy of muon neutrinos from genie spectrum;E[GeV]",
        nbins,
        minE,
        maxE,
    ),
    "pzv",
)

# drawing distributions to check them

c1 = r.TCanvas()
hfluka_nuE.Draw("histo")

c2 = r.TCanvas()
hgenie_nuE.DrawClone("histo")

# computing cross section distributions
# correctly handling errors in division

hfluka_nuE.Sumw2()
hgenie_nuE.Sumw2()

hnuratio = r.TH1D(
    "hnuratio",
    "ratio between Genie and Fluka energies, proportional to the cross section",
    nbins,
    minE,
    maxE,
)
# making division and plotting ratio distribution
hnuratio.Divide(hgenie_nuE.GetPtr(), hfluka_nuE)

c3 = r.TCanvas()
hnuratio.Draw("histo")

# hit or miss section
maxratio = hnuratio.GetMaximum()

# cloning fluka tree into an empty output tree
flukatree = flukafile.Get("t")
output_nutree = flukatree.CloneTree(0)
output_nutree.SetName("fluka_neutrinos_selected")
output_nutree.SetTitle("Neutrinos from Fluka simulation after hit and miss selection")

nneutrinos = flukatree.GetEntries()
print("Starting loop over {} neutrinos".format(nneutrinos))

for nuevent in flukatree:
    Ekin = nuevent.Ekin
    # get uniform random number between 0 and maximum ratio
    randomratio = r.gRandom.Uniform(0, maxratio)
    # finding ratio for that neutrino energy
    matchingratio = hnuratio.GetBinContent(hnuratio.FindBin(Ekin))
    # if the found ratio is larger than random number, accept neutrino as interacting
    if matchingratio > randomratio:
        output_nutree.Fill()
# writing tree and closing file

# writing tree, closing file
geniefile.cd()
output_nutree.Write("fluka_neutrinos_selected",r.TFile.kOverwrite)
geniefile.Close()
