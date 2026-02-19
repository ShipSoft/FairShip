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
        self.det_field = None
        self.mc_field = None

        # Register hit field with model
        if branchName:
            field_name = f"Digi_{branchName}Hits"
        else:
            field_name = f"Digi_{name}Hits"

        self.det_field = self.model.MakeField[f"std::vector<{name}Hit>"](field_name)

        # Register MC field if requested
        if mcBranchName:
            self.MCdet = ROOT.std.vector("std::vector< int >")()
            self.mc_field = self.model.MakeField["std::vector<std::vector<int>>"](mcBranchName)

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
        if self.det_field:
            entry[self.det_field.GetFieldName()] = self.det

        # Fill MC field if present
        if self.mc_field and self.MCdet:
            entry[self.mc_field.GetFieldName()] = self.MCdet

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
