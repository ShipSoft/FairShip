# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Helpers for reading, validating and repacking FairShip magnetic field maps.

A FairShip ROOT field map holds two trees. ``Range`` has a single entry with
the coordinate limits and bin widths (cm), and ``Data`` has ``Nx*Ny*Nz``
entries with the field components (Tesla), optionally accompanied by the node
coordinates.

``ShipBFieldMap`` reads ``Data`` sequentially and only imposes the grid
structure at lookup time, through ``index = (iX*Ny + iY)*Nz + iZ``: z is
increased first, then y, then x. Nothing in the file states the ordering, so a
map written in a different order is read transposed. When ``Nx == Ny`` and the
x and y ranges agree, even the entry count still matches and the mistake is
silent. The functions here make the ordering checkable, from both the stored
coordinates and from the field itself.
"""

import os
from dataclasses import dataclass

import numpy as np
import ROOT

#: Field component branch names, in the order they are stored.
FIELD_BRANCHES = ("Bx", "By", "Bz")

#: Node coordinate branch names, written when a map is converted with
#: ``storeCoords``.
COORD_BRANCHES = ("x", "y", "z")

#: Supported data orderings. ``xslow`` is the one FairShip assumes.
ORDERS = ("xslow", "yslow")


@dataclass(frozen=True)
class MapRange:
    """Coordinate limits and binning of a field map, in cm."""

    xMin: float
    xMax: float
    dx: float
    yMin: float
    yMax: float
    dy: float
    zMin: float
    zMax: float
    dz: float

    @staticmethod
    def _bins(lo, hi, step):
        # Same arithmetic as ShipBFieldMap::setLimits(): the 1.5 rounds up to
        # the nearest integer while counting both endpoints.
        if step <= 0.0:
            raise ValueError(f"Non-positive bin width {step}")
        return int((hi - lo) / step + 1.5)

    @property
    def Nx(self):
        return self._bins(self.xMin, self.xMax, self.dx)

    @property
    def Ny(self):
        return self._bins(self.yMin, self.yMax, self.dy)

    @property
    def Nz(self):
        return self._bins(self.zMin, self.zMax, self.dz)

    @property
    def N(self):
        return self.Nx * self.Ny * self.Nz

    @property
    def shape(self):
        return (self.Nx, self.Ny, self.Nz)

    def axis_values(self):
        """Nominal node coordinates along each axis."""
        return (
            self.xMin + self.dx * np.arange(self.Nx),
            self.yMin + self.dy * np.arange(self.Ny),
            self.zMin + self.dz * np.arange(self.Nz),
        )

    def node_indices(self, entries, order="xslow"):
        """Grid indices (iX, iY, iZ) of the given entry numbers."""
        entries = np.asarray(entries)
        iZ = entries % self.Nz
        if order == "xslow":
            return entries // (self.Ny * self.Nz), (entries // self.Nz) % self.Ny, iZ
        if order == "yslow":
            return (entries // self.Nz) % self.Nx, entries // (self.Nx * self.Nz), iZ
        raise ValueError(f"Unknown data order {order!r}, expected one of {ORDERS}")

    def extent_mismatch(self):
        """Deviation of each axis extent from a whole number of bins, in bins.

        A non-zero value means the limits and the bin width disagree, so the
        node coordinates drift away from the nominal grid.
        """
        return tuple(
            abs((n - 1) * d - (hi - lo)) / d
            for n, d, lo, hi in (
                (self.Nx, self.dx, self.xMin, self.xMax),
                (self.Ny, self.dy, self.yMin, self.yMax),
                (self.Nz, self.dz, self.zMin, self.zMax),
            )
        )


def read_range(path):
    """Read the ``Range`` tree of a field map."""
    columns = ROOT.RDataFrame("Range", str(path)).AsNumpy(
        ["xMin", "xMax", "dx", "yMin", "yMax", "dy", "zMin", "zMax", "dz"]
    )
    values = {name: float(column[0]) for name, column in columns.items()}
    return MapRange(**values)


def is_field_map(path):
    """Whether the file holds both trees a FairShip field map needs.

    False for anything ROOT cannot open, an unfetched git-lfs pointer
    included. PyROOT raises OSError there rather than handing back a null
    file, so checking the returned handle would never catch it.
    """
    try:
        handle = ROOT.TFile.Open(str(path))
    except OSError:
        return False
    try:
        trees = {key.GetName() for key in handle.GetListOfKeys()}
    finally:
        handle.Close()
    return {"Range", "Data"} <= trees


def branches(path):
    """Names of the branches of the ``Data`` tree."""
    return {str(name) for name in ROOT.RDataFrame("Data", str(path)).GetColumnNames()}


def entry_count(path):
    """Number of entries in the ``Data`` tree."""
    return int(ROOT.RDataFrame("Data", str(path)).Count().GetValue())


def has_coords(path):
    """Whether the map stores the node coordinates alongside the field."""
    return set(COORD_BRANCHES) <= branches(path)


def _columns(path, names):
    data = ROOT.RDataFrame("Data", str(path)).AsNumpy(list(names))
    return [np.asarray(data[name], dtype=np.float64) for name in names]


def read_field(path, order="xslow", rng=None):
    """Read the field as an ``(Nx, Ny, Nz, 3)`` array of Tesla.

    ``order`` says how the flat entries map onto the grid: ``xslow`` is the
    canonical ``(iX*Ny + iY)*Nz + iZ``, ``yslow`` its x/y transpose.
    """
    if order not in ORDERS:
        raise ValueError(f"Unknown data order {order!r}, expected one of {ORDERS}")
    rng = rng or read_range(path)
    field = np.stack(_columns(path, FIELD_BRANCHES), axis=-1)
    if len(field) != rng.N:
        raise ValueError(f"{path}: expected {rng.N} entries but found {len(field)}")
    if order == "xslow":
        return field.reshape(rng.Nx, rng.Ny, rng.Nz, 3)
    return field.reshape(rng.Ny, rng.Nx, rng.Nz, 3).transpose(1, 0, 2, 3)


def transpose_xy(field):
    """The same field read with x and y swapped."""
    return field.transpose(1, 0, 2, 3)


def read_coords(path):
    """Read the stored node coordinates, or ``None`` if the map has none."""
    if not has_coords(path):
        return None
    return _columns(path, COORD_BRANCHES)


def _residuals(coords, rng, order):
    """Per-axis deviation of the stored coordinates from ``order``, in bins."""
    nodes = rng.node_indices(np.arange(rng.N), order)
    limits = ((rng.xMin, rng.dx), (rng.yMin, rng.dy), (rng.zMin, rng.dz))
    return tuple(
        np.abs(stored - (lo + node * step)).max() / step for stored, node, (lo, step) in zip(coords, nodes, limits)
    )


def coord_residuals(path, rng=None, order="xslow"):
    """Largest deviation of a stored coordinate from the node ``order`` puts it at.

    Returned per axis, in bin widths, over every entry. A map in the given
    order sits within a fraction of a bin; a permuted one is off by tens of
    bins. ``None`` if the map stores no coordinates.
    """
    coords = read_coords(path)
    if coords is None:
        return None
    rng = rng or read_range(path)
    if len(coords[0]) != rng.N:
        raise ValueError(f"{path}: expected {rng.N} entries but found {len(coords[0])}")
    return _residuals(coords, rng, order)


def infer_data_order(path, rng=None):
    """Guess the data order from the stored coordinates.

    Returns ``"xslow"``, ``"yslow"``, or ``None`` when the map stores no
    coordinates or matches neither ordering.
    """
    coords = read_coords(path)
    if coords is None:
        return None
    rng = rng or read_range(path)
    if len(coords[0]) != rng.N:
        return None
    # Check every node against both candidates rather than watch a single
    # transition: a layout that is neither has to come back unknown, or
    # canonicalise() would reorder from a premise that does not hold.
    matching = [order for order in ORDERS if max(_residuals(coords, rng, order)) < 0.5]
    return matching[0] if len(matching) == 1 else None


def core_slices(rng, xy_fraction=0.3, z_fraction=0.25):
    """Slices selecting the middle of the map, away from coils and yoke."""
    xs, ys, zs = rng.axis_values()

    def middle(values, fraction):
        centre = 0.5 * (values[0] + values[-1])
        half = fraction * 0.5 * (values[-1] - values[0])
        (inside,) = np.nonzero(np.abs(values - centre) <= half)
        if not inside.size:
            # Too few nodes for the fraction to reach one of them. Take the
            # node nearest the centre so the caller gets a region, not an
            # IndexError.
            nearest = int(np.abs(values - centre).argmin())
            return slice(nearest, nearest + 1)
        return slice(inside[0], inside[-1] + 1)

    return (
        middle(xs, xy_fraction),
        middle(ys, xy_fraction),
        middle(zs, z_fraction),
    )


def div_b_rms(field, rng, region=None):
    """RMS of div B over the core of the map, and the local gradient scale.

    A physical field has div B = 0, so an ordering that scrambles neighbouring
    nodes shows up as a large residual. The gradient scale is the RMS of the
    three diagonal derivatives, which is what the residual should be compared
    against: it is the size div B would have if the derivatives did not cancel.
    """
    region = region or core_slices(rng)
    terms = [np.gradient(field[..., axis], step, axis=axis) for axis, step in enumerate((rng.dx, rng.dy, rng.dz))]
    dBx, dBy, dBz = (term[region] for term in terms)
    divergence = dBx + dBy + dBz
    scale = sum(float((term**2).mean()) for term in (dBx, dBy, dBz))
    return float(np.sqrt((divergence**2).mean())), float(np.sqrt(scale))


def on_axis(field, rng):
    """Field along z at the grid node closest to x = y = 0."""
    xs, ys, _ = rng.axis_values()
    return field[np.abs(xs).argmin(), np.abs(ys).argmin()]


def canonicalise(in_path, out_path, order="xslow", rng=None):
    """Write a field map in canonical order, with matching node coordinates.

    ``order`` is the order the *input* is in. The output is always
    ``(iX*Ny + iY)*Nz + iZ`` with freshly generated ``x``, ``y`` and ``z``
    branches, so ``ShipBFieldMap`` can verify it.
    """
    # Snapshot recreates the output, and the Range tree is copied out of the
    # input afterwards, so writing over the input would lose it.
    if os.path.exists(out_path) and os.path.samefile(in_path, out_path):
        raise ValueError(f"{out_path} is the input; write the repacked map somewhere else")

    rng = rng or read_range(in_path)
    field = read_field(in_path, order=order, rng=rng).reshape(rng.N, 3)

    xs, ys, zs = rng.axis_values()
    x, y, z = (grid.ravel() for grid in np.meshgrid(xs, ys, zs, indexing="ij"))

    columns = {
        "x": x.astype(np.float32),
        "y": y.astype(np.float32),
        "z": z.astype(np.float32),
    }
    columns.update({name: field[:, i].astype(np.float32) for i, name in enumerate(FIELD_BRANCHES)})
    ROOT.RDF.FromNumpy(columns).Snapshot("Data", str(out_path))

    # Snapshot writes a fresh file, so copy the Range tree over afterwards.
    source = ROOT.TFile.Open(str(in_path))
    destination = ROOT.TFile.Open(str(out_path), "UPDATE")
    destination.cd()
    source.Get("Range").CloneTree(-1, "fast").Write()
    destination.Close()
    source.Close()
