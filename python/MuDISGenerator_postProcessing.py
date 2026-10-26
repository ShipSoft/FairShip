# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Restore incoming-muon detector points after NewMuDISGenerator simulation."""

import math
import os
import shutil
import tempfile
from pathlib import Path

import ROOT

# Required input branch, simulation branch / point class.
_POINT_BRANCHES = (
    ("muon_UBTPoints", "UpstreamTaggerPoint"),
    ("muon_SBTPoints", "vetoPoint"),
    ("muon_SSTPoints", "strawtubesPoint"),
    ("muon_TDPoints", "TimeDetPoint"),
)
_MARKER = "MuDISGenerator_postProcessing"
# Per-event identity written by NewMuDISGenerator.RegisterOutputBranches.
_IDENTITY_BRANCHES = ("muDIS_muEntry", "muDIS_material", "muDIS_disIndex")


def _dis_events(input_files, start_event):
    """Yield the muon tree, DIS z and identity in the generator's replay order.

    The identity is (muon entry across all input files, material label, DIS
    index within that muon and material), as NewMuDISGenerator writes it.
    """
    # Use the generator's material order from MuDISDefs.h.
    materials = [str(label) for label in ROOT.NewMuDISGenerator.GetMaterialNames()]
    skip = start_event
    offset = 0  # entries in the preceding input files
    for name in input_files:
        with ROOT.TFile.Open(str(name), "READ") as source:
            tree = source.Get("MuonDIS")
            if not tree:
                raise ValueError(f"Missing MuonDIS tree in {name}")
            entries = tree.GetEntries()
            if skip >= entries:
                skip -= entries
                offset += entries
                continue
            required = [branch for branch, _ in _POINT_BRANCHES]
            for material in materials:
                required.extend((f"muon_nDISevt_{material}", f"mudis_DISvz_{material}"))
            for branch in required:
                if not tree.GetBranch(branch):
                    raise ValueError(f"Missing {branch} in {name}")
            # Avoid reading the large DIS daughter arrays.
            tree.SetBranchStatus("*", False)
            for branch in required:
                tree.SetBranchStatus(branch + "*", True)
            for entry in range(skip, entries):
                if tree.GetEntry(entry) <= 0:
                    raise OSError(f"Cannot read MuonDIS entry {entry} in {name}")
                for material in materials:
                    count = int(getattr(tree, f"muon_nDISevt_{material}"))
                    vertices = getattr(tree, f"mudis_DISvz_{material}")
                    if count < 0 or len(vertices) != count:
                        raise ValueError(f"Invalid DIS count/vertices in {name}, entry {entry}, material {material}")
                    for index, z in enumerate(vertices):
                        if not math.isfinite(z):
                            raise ValueError(f"Non-finite DIS vertex in {name}, entry {entry}")
                        yield tree, float(z), (offset + entry, material, index)
            skip = 0
            offset += entries


def _copy_metadata(source, destination, skip=()):
    """Preserve the latest key of every other object, including directories."""
    names = dict.fromkeys(key.GetName() for key in source.GetListOfKeys())
    for name in names:
        if name in skip:
            continue
        obj = source.Get(name)
        destination.cd()
        if obj.InheritsFrom("TDirectory"):
            _copy_metadata(obj, destination.mkdir(name, obj.GetTitle()))
            continue
        if obj.InheritsFrom("TTree"):
            obj = obj.CloneTree(-1, "fast")
        if obj.Write(name, ROOT.TObject.kSingleKey) <= 0:
            raise OSError(f"Cannot copy output metadata {name}")


def post_process(output_file, input_files, start_event=0):
    """Append input-muon hits with z < DIS z to each simulated cbmsim event.

    Input files and start_event (a zero-based muon entry across the files) must
    match NewMuDISGenerator.Init. Output must still be in generator order, before
    any event skimming. Its entry count sets how many DIS interactions to consume.
    Each output entry's muDIS_muEntry, muDIS_material and muDIS_disIndex must
    match the interaction read here; any mismatch raises before the output is
    replaced, so hits are never attached to the wrong event.
    Copied points reference MCTrack[0], the untracked incoming muon; their event
    IDs are updated too. Other point properties and simulated hits are preserved.

    Rewrite to a temporary sibling file, preserving metadata, and replace the
    output only after success. Return the number of appended hits per detector.
    """
    if start_event < 0:
        raise ValueError("start_event must be nonnegative")
    if isinstance(input_files, (str, os.PathLike)):
        input_files = [input_files]
    else:
        input_files = list(input_files)
    if not input_files:
        raise ValueError("At least one MuonDIS input file is required")
    output_path = Path(output_file).resolve()
    if any(os.path.realpath(str(name)) == str(output_path) for name in input_files):
        raise ValueError("Simulation output must differ from the MuonDIS input")

    # FairRunSim can still own an open output file at this point.
    for opened in ROOT.gROOT.GetListOfFiles():
        if (
            isinstance(opened, ROOT.TFile)
            and os.path.realpath(opened.GetName()) == str(output_path)
            and opened.IsWritable()
        ):
            opened.Flush()

    counts = dict.fromkeys((branch for _, branch in _POINT_BRANCHES), 0)
    events = _dis_events(input_files, start_event)
    temporary = None
    try:
        with ROOT.TFile.Open(str(output_path), "READ") as source:
            if source.Get(_MARKER):
                raise ValueError("Incoming-muon hits have already been restored in this output")
            tree = source.Get("cbmsim")
            if not tree:
                raise ValueError("Simulation output has no cbmsim tree")
            for branch in ("MCTrack", *(name for _, name in _POINT_BRANCHES), *_IDENTITY_BRANCHES):
                if not tree.GetBranch(branch):
                    raise ValueError(f"Simulation output has no {branch} branch")
            fd, temporary = tempfile.mkstemp(
                prefix=f".{output_path.stem}.mudis-", suffix=".root", dir=output_path.parent
            )
            os.close(fd)
            with ROOT.TFile.Open(temporary, "RECREATE") as destination:
                destination.SetCompressionSettings(source.GetCompressionSettings())
                rewritten = tree.CloneTree(0)
                for entry in range(tree.GetEntries()):
                    if tree.GetEntry(entry) <= 0:
                        raise OSError(f"Cannot read simulation entry {entry}")
                    try:
                        muon, vertex_z, expected = next(events)
                    except StopIteration as error:
                        raise ValueError(
                            f"No input DIS interaction corresponding to simulation entry {entry}"
                        ) from error
                    replayed = (int(tree.muDIS_muEntry), str(tree.muDIS_material), int(tree.muDIS_disIndex))
                    if replayed != expected:
                        raise ValueError(
                            f"Simulation entry {entry} replayed (muon entry, material, DIS index) = {replayed}, "
                            f"but the input order gives {expected}. Check that the input files and start "
                            "entry match the simulation run and that the output was not skimmed."
                        )
                    tracks = tree.MCTrack
                    if not tracks.size() or abs(tracks[0].GetPdgCode()) != 13 or tracks[0].GetMotherId() != -1:
                        raise ValueError(f"Simulation entry {entry} has no incoming muon at MCTrack[0]")
                    for input_branch, output_branch in _POINT_BRANCHES:
                        points = getattr(tree, output_branch)
                        point_class = getattr(ROOT, output_branch)
                        for hit in getattr(muon, input_branch):
                            if hit.GetZ() < vertex_z:
                                copied = point_class(hit)
                                copied.SetTrackID(0)
                                copied.SetEventID(tracks[0].GetEventID())
                                points.push_back(copied)
                                counts[output_branch] += 1
                    if rewritten.Fill() < 0:
                        raise OSError(f"Cannot write simulation entry {entry}")
                destination.cd()
                if rewritten.Write("cbmsim", ROOT.TObject.kOverwrite) <= 0:
                    raise OSError("Cannot write restored cbmsim tree")
                _copy_metadata(source, destination, skip=("cbmsim",))
                destination.cd()
                ROOT.TNamed(_MARKER, "Incoming-muon hits restored for z < DIS vertex z").Write()
                destination.Flush()
                if destination.TestBit(ROOT.TFile.kWriteError):
                    raise OSError("Error writing restored simulation output")
        shutil.copymode(output_path, temporary)
        os.replace(temporary, output_path)
        temporary = None
    finally:
        events.close()
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)
    print(f"Restored incoming-muon hits in {output_file}: {counts}")
    return counts
