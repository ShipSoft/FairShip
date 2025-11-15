# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN on behalf of the SHiP Collaboration

"""Base class for detector digitization."""

from abc import ABC, abstractmethod

import ROOT


class BaseDetector(ABC):
    """Abstract base class for detector digitization using template method pattern."""

    def __init__(
        self,
        name,
        intree,
        branchType="TClonesArray",
        branchName=None,
        mcBranchType=None,
        mcBranchName=None,
        splitLevel=-1,
    ):
        """Initialize the detector digitizer."""
        self.name = name
        self.intree = intree
        self.isVector = False
        self.det = eval(f"ROOT.{branchType}('{name}Hit')")
        self.MCdet = None
        self.mcBranch = None
        if mcBranchName:
            self.MCdet = ROOT.std.vector("std::vector< int >")()
            self.mcBranch = self.intree.Branch(
                mcBranchName, self.MCdet, 32000, splitLevel
            )

        if "std.vector" in branchType:
            self.det = self.det()
            self.isVector = True
        if branchName:
            self.branch = self.intree.Branch(
                f"Digi_{branchName}Hits", self.det, 32000, splitLevel
            )
        else:
            self.branch = self.intree.Branch(
                f"Digi_{name}Hits", self.det, 32000, splitLevel
            )

    def delete(self):
        """Clear detector hit containers."""
        if self.isVector:
            self.det.clear()
        else:
            self.det.Delete()

        if self.MCdet:
            self.MCdet.clear()

    def fill(self):
        """Fill detector hit branches."""
        self.branch.Fill()
        if self.mcBranch:
            self.mcBranch.Fill()

    @abstractmethod
    def digitize(self):
        """Digitize detector hits.

        This method must be implemented by all detector subclasses to convert
        MC hits into digitized detector responses.
        """
        pass

    def process(self):
        """Process one event: delete, digitize, and fill."""
        self.delete()
        self.digitize()
        self.fill()
