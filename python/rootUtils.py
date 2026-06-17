# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import os
import sys
from collections import Counter

import ROOT

_error_log: Counter[str] = Counter()


def readHists(h, fname, wanted=None) -> None:
    if wanted is None:
        wanted = []
    if fname[0:4] == "/eos":
        eospath = ROOT.gSystem.Getenv("EOSSHIP") + fname
        f = ROOT.TFile.Open(eospath)
    else:
        f = ROOT.TFile(fname)
    for akey in f.GetListOfKeys():
        name = akey.GetName()
        try:
            hname = int(name)
        except ValueError:
            hname = name
        if len(wanted) > 0 and hname not in wanted:
            continue
        obj = akey.ReadObj()
        cln = obj.Class().GetName()
        if "TCanv" in cln:
            h[hname] = obj.Clone()
        if "TH" not in cln:
            continue
        if hname in h:
            rc = h[hname].Add(obj)
            if not rc:
                print("Error when adding histogram ", hname)
        else:
            h[hname] = obj.Clone()
            if h[hname].GetSumw2N() == 0:
                h[hname].Sumw2()
        h[hname].SetDirectory(ROOT.gROOT)
        if cln in {"TH2D", "TH2F"}:
            for p in ["_projx", "_projy"]:
                if isinstance(hname, str):
                    projname = hname + p
                else:
                    projname = str(hname) + p
                if "x" in p:
                    h[projname] = h[hname].ProjectionX()
                else:
                    h[projname] = h[hname].ProjectionY()
                h[projname].SetName(name + p)
                h[projname].SetDirectory(ROOT.gROOT)
    return


def bookHist(
    h,
    key=None,
    title: str = "",
    nbinsx: int = 100,
    xmin: float = 0,
    xmax: float = 1,
    nbinsy: int = 0,
    ymin: float = 0,
    ymax: float = 1,
    nbinsz: int = 0,
    zmin: float = 0,
    zmax: float = 1,
) -> None:
    if key is None:
        print("missing key")
        return
    rkey = str(key)  # in case somebody wants to use integers, or floats as keys
    if key in h:
        h[key].Reset()
    elif nbinsz > 0:
        h[key] = ROOT.TH3D(rkey, title, nbinsx, xmin, xmax, nbinsy, ymin, ymax, nbinsz, zmin, zmax)
    elif nbinsy > 0:
        h[key] = ROOT.TH2D(rkey, title, nbinsx, xmin, xmax, nbinsy, ymin, ymax)
    else:
        h[key] = ROOT.TH1D(rkey, title, nbinsx, xmin, xmax)
    h[key].SetDirectory(ROOT.gROOT)


def bookProf(
    h,
    key=None,
    title: str = "",
    nbinsx: int = 100,
    xmin: float = 0,
    xmax: float = 1,
    ymin: float | None = None,
    ymax: float | None = None,
    option: str = "",
) -> None:
    if key is None:
        print("missing key")
        return
    rkey = str(key)  # in case somebody wants to use integers, or floats as keys
    if key in h:
        h[key].Reset()
    if ymin is None or ymax is None:
        h[key] = ROOT.TProfile(rkey, title, nbinsx, xmin, xmax, option)
    else:
        h[key] = ROOT.TProfile(rkey, title, nbinsx, xmin, xmax, ymin, ymax, option)
    h[key].SetDirectory(ROOT.gROOT)


def writeHists(h, fname, plusCanvas: bool = False) -> None:
    f = ROOT.TFile(fname, "RECREATE")
    for akey in h:
        if not hasattr(h[akey], "Class"):
            continue
        cln = h[akey].Class().GetName()
        if "TH" in cln or "TP" in cln:
            h[akey].Write()
        if plusCanvas and "TC" in cln:
            h[akey].Write()
    f.Close()


def bookCanvas(h, key=None, title: str = "", nx: int = 900, ny: int = 600, cx: int = 1, cy: int = 1) -> None:
    if key is None:
        print("missing key")
        return
    if key not in h:
        h[key] = ROOT.TCanvas(key, title, nx, ny)
        h[key].Divide(cx, cy)


def reportError(s) -> None:
    _error_log[s] += 1


def errorSummary() -> None:
    if _error_log:
        print("Summary of recorded incidents:")
    for e in _error_log:
        print(e, ":", _error_log[e])


def checkFileExists(x) -> str:
    if isinstance(x, str):
        tx = [x]
    else:
        tx = x
    if isinstance(tx, (list, tuple)):
        # See what we are looking at and make sure all the files are of the same type
        fileType = ""
        for _f in tx:
            if _f[0:4] == "/eos":
                f = ROOT.gSystem.Getenv("EOSSHIP") + _f
            else:
                f = _f
            test = ROOT.TFile.Open(f)
            if not test:
                print("ERROR FileCheck: input file", f, " does not exist. Missing authentication?")
                sys.exit(1)
            if test.FindObjectAny("cbmsim") and fileType in ["tree", ""]:
                fileType = "tree"
            elif fileType in ["ntuple", ""]:
                fileType = "ntuple"
            else:
                print("ERROR FileCheck: Supplied list of files not all of tree or ntuple type")
        return fileType
    else:
        print("ERROR FileCheck: File must be either a string or list of files")
        os._exit(1)
