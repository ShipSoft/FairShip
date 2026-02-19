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
        model,
        branchName=None,
        mcBranchType=None,
        mcBranchName=None,
    ):
        """Initialize the detector digitizer.

        Args:
            name: Detector name
            intree: Input TTree for reading MC data
            model: RNTupleModel for registering output fields
            branchName: Optional custom branch name
            mcBranchType: Type for MC branch (unused in RNTuple)
            mcBranchName: Name for MC branch
        """
        self.name = name
        self.intree = intree
        self.model = model
        self.det = ROOT.std.vector(f"{name}Hit")()
        self.MCdet = None
        self.det_field_name = None
        self.mc_field_name = None

        # Register hit field with model
        if branchName:
            self.det_field_name = f"Digi_{branchName}Hits"
        else:
            self.det_field_name = f"Digi_{name}Hits"

        self.model.MakeField[f"std::vector<{name}Hit>"](self.det_field_name)

        # Register MC field if requested
        if mcBranchName:
            self.MCdet = ROOT.std.vector("std::vector< int >")()
            self.mc_field_name = mcBranchName
            self.model.MakeField["std::vector<std::vector<int>>"](self.mc_field_name)

    def delete(self):
        """Clear detector hit containers."""
        self.det.clear()
        if self.MCdet:
            self.MCdet.clear()

    def fill(self, entry):
        """Fill detector hit fields into RNTuple entry.

        Args:
            entry: RNTuple entry to fill
        """
        # Fill hit field
        if self.det_field_name:
            entry[self.det_field_name] = self.det

        # Fill MC field if present
        if self.mc_field_name and self.MCdet:
            entry[self.mc_field_name] = self.MCdet

    @abstractmethod
    def digitize(self):
        """Digitize detector hits.

        This method must be implemented by all detector subclasses to convert
        MC hits into digitized detector responses.
        """
        pass

    def process(self, entry=None):
        """Process one event: delete, digitize, and fill.

        Args:
            entry: RNTuple entry to fill (optional for backward compatibility)
        """
        self.delete()
        self.digitize()
        if entry is not None:
            self.fill(entry)
