# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

from ctypes import c_double

import ROOT
import hepunits as u


def MCPointPrintOut(self) -> str:
    p = ROOT.TDatabasePDG.Instance().GetParticle(self.PdgCode())
    n = ""
    if p:
        n = p.GetName()
    return (
        f'("{self.Class_Name()}") X:{self.GetX():6.3F}cm Y:{self.GetY():6.3F}cm '
        f"Z:{self.GetZ():6.3F}cm dE/dx:{self.GetEnergyLoss() / u.MeV:6.2F}MeV {n}"
    )


def MCTrackPrintOut(self) -> str:
    c = self.GetPdgCode()
    p = ROOT.TDatabasePDG.Instance().GetParticle(c)
    n = ""
    if p:
        n = p.GetName()
    m = self.GetMotherId()
    return '("ShipMCTrack") pdgCode: %7i(%10s)  Z=%6.1F m P=%6.3F GeV/c mother=%i %s' % (
        c,
        n,
        self.GetStartZ() / u.m,
        self.GetP(),
        m,
        self.GetProcName(),
    )


def vetoHitPrintOut(self) -> str:
    return '("vetoHit") detID:%7i  ADC:%5.2F TDC:%5.2F' % (self.GetDetectorID(), self.GetADC(), self.GetTDC())


def TimeDetHitPrintOut(self) -> str:
    t = self.GetMeasurements()
    return '("TimeDetHit") detID:%7i  TDC1:%5.2F TDC2:%5.2F  isValid:%r' % (
        self.GetDetectorID(),
        t[0],
        t[1],
        self.isValid(),
    )


def FitTrackPrintOut(self) -> str:
    st = self.getFitStatus()
    if st.isFitConverged():
        chi2DoF = st.getChi2() / st.getNdf()
        sta = self.getFittedState()
        P = sta.getMomMag()
        return '("FitTrack") chi2/dof:%3.1F  P:%5.2FGeV/c pdg:%i' % (chi2DoF, P, sta.getPDG())
    return '("FitTrack") fit not converged'


def TParticlePrintOut(self) -> str:
    return f'("TParticle") {self.GetName()}  P:{self.P():5.2F}GeV/c VxZ:{self.Vz() / u.m:5.2F}m'


def ShipParticlePrintOut(self) -> str:
    return (
        f'("ShipParticle") {self.GetName()} M:{self.GetMass():5.2F}GeV/c2 '
        f"P:{self.P():5.2F}GeV/c VxZ:{self.Vz() / u.m:5.2F}m"
    )


def Dump(self) -> None:
    for k, obj in enumerate(self):
        print(k, obj.__repr__())


def TVector3PrintOut(self) -> str:
    return f"{self.X():9.5F},{self.Y():9.5F},{self.Z():9.5F}"


def TLorentzVectorPrintOut(self) -> str:
    return f"{self.Px():9.5F},{self.Py():9.5F},{self.Pz():9.5F},{self.E():9.5F},{self.Mag():9.5F}"


def TEvePointSetPrintOut(self) -> str:
    x, y, z = c_double(), c_double(), c_double()
    txt = ""
    if self.GetN() == 0:
        txt = "<ROOT.TEvePointSet object>"
    for n in range(self.GetN()):
        self.GetPoint(n, x, y, z)
        txt += f"{n:6d} {x.value:7.1f}, {y.value:7.1f}, {z.value:9.1f} x, y, z cm\n"

    return txt


def apply_decorators() -> None:
    """Apply custom __repr__ methods to ROOT classes.

    Call this function after ROOT libraries are fully loaded to enable
    enhanced string representations for ROOT objects.
    """
    # Method-replacement is the whole point of this function; mypy flags
    # each line with [method-assign] regardless.
    ROOT.FairMCPoint.__repr__ = MCPointPrintOut  # type: ignore[method-assign]
    ROOT.ShipMCTrack.__repr__ = MCTrackPrintOut  # type: ignore[method-assign]
    ROOT.genfit.Track.__repr__ = FitTrackPrintOut  # type: ignore[method-assign]
    ROOT.TClonesArray.Dump = Dump  # type: ignore[method-assign]
    ROOT.TVector3.__repr__ = TVector3PrintOut  # type: ignore[method-assign]
    ROOT.TParticle.__repr__ = TParticlePrintOut  # type: ignore[method-assign]
    ROOT.ShipParticle.__repr__ = ShipParticlePrintOut  # type: ignore[method-assign]
    ROOT.TEvePointSet.__repr__ = TEvePointSetPrintOut  # type: ignore[method-assign]
    ROOT.vetoHit.__repr__ = vetoHitPrintOut  # type: ignore[method-assign]
    ROOT.TimeDetHit.__repr__ = TimeDetHitPrintOut  # type: ignore[method-assign]
    ROOT.TLorentzVector.__repr__ = TLorentzVectorPrintOut  # type: ignore[method-assign]
