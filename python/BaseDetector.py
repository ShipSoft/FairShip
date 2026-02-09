# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Base class for detector digitization."""

from abc import ABC, abstractmethod

import ROOT


class BaseDetector(ABC):
    """Abstract base class for detector digitization using template method pattern."""

    def __init__(
        self,
        name,
        intree,
        branchName=None,
        mcBranchType=None,
        mcBranchName=None,
        splitLevel=99,
        outtree=None,
    ):
        """Initialize the detector digitizer."""
        self.name = name
        self.intree = intree
        # If outtree provided, use it for output; else intree for compatibility
        self.outtree = outtree if outtree is not None else intree
        self.det = ROOT.std.vector(f"{name}Hit")()
        self.MCdet = None
        self.mcBranch = None
        if mcBranchName:
            self.MCdet = ROOT.std.vector("std::vector< int >")()
            self.mcBranch = self.outtree.Branch(mcBranchName, self.MCdet, 32000, splitLevel)

        if branchName:
            self.branch = self.outtree.Branch(f"Digi_{branchName}Hits", self.det, 32000, splitLevel)
        else:
            self.branch = self.outtree.Branch(f"Digi_{name}Hits", self.det, 32000, splitLevel)

    def delete(self):
        """Clear detector hit containers."""
        self.det.clear()
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
