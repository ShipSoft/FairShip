"""Base class for detector digitisation."""

from abc import ABC, abstractmethod

import ROOT


class BaseDetector(ABC):
    """Abstract base class for detector digitisation."""

    def __init__(
        self,
        name,
        intree,
        branchType="TClonesArray",
        branchName=None,
        mcBranchType=None,
        mcBranchName=None,
        splitLevel=99,
    ):
        """Initialise detector digitisation."""
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
        """Clear detector containers."""
        if self.isVector:
            self.det.clear()
        else:
            self.det.Delete()

        if self.MCdet:
            self.MCdet.clear()

    def fill(self):
        """Fill TTree branches."""
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
        """Process one event: delete, digitise, and fill."""
        self.delete()
        self.digitize()
        self.fill()
