#!/bin/python
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Plot the components of a FairShip field map, straight from the file.

``ShipFieldMaker::plotField`` also draws the three components, but it needs a
built geometry and samples the field through it. This reads the map on its own,
so it can be pointed at a file before anything is simulated, and it can show
the same file read two ways.

The panels are chosen to make an x/y transposition obvious: a dipole aperture
is not square, so the x and y profiles and the aperture outline disagree at a
glance when the two axes are swapped.
"""

import argparse
import sys

import fieldMapTools as fmt
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

#: Nominal half-aperture of the SHiP spectrometer, in cm.
APERTURE = (200.0, 300.0)


def bending_power(field, rng):
    """Integral of Bx along z at every (x, y), in T cm.

    Trapezoidal, so the integral covers the intervals between nodes rather
    than counting the two end nodes as whole steps.
    """
    return np.trapezoid(field[..., 0], dx=rng.dz, axis=2)


def draw(axes, rng, field, label, aperture):
    xs, ys, zs = rng.axis_values()
    centre = np.abs(zs).argmin()
    i0, j0 = np.abs(xs).argmin(), np.abs(ys).argmin()

    slice_xy = field[:, :, centre, 0].T
    limit = np.abs(slice_xy).max()
    mesh = axes[0].pcolormesh(xs, ys, slice_xy, cmap="RdBu_r", vmin=-limit, vmax=limit)
    axes[0].figure.colorbar(mesh, ax=axes[0], label="$B_x$ [T]")
    if aperture:
        axes[0].add_patch(
            plt.Rectangle(
                (-aperture[0], -aperture[1]),
                2 * aperture[0],
                2 * aperture[1],
                fill=False,
                linestyle="--",
                edgecolor="k",
            )
        )
    axes[0].set(xlabel="x [cm]", ylabel="y [cm]", title=f"{label}: $B_x$ at z = {zs[centre]:.0f} cm")
    axes[0].set_aspect("equal")

    axes[1].plot(xs, field[:, j0, centre, 0], label="along x, y = 0")
    axes[1].plot(ys, field[i0, :, centre, 0], label="along y, x = 0")
    # Clip to the aperture field so the coil and yoke return flux, which is an
    # order of magnitude larger, does not flatten the profiles.
    on_axis = abs(field[i0, j0, centre, 0])
    axes[1].set_ylim(-1.5 * on_axis, 1.5 * on_axis)
    axes[1].axhline(0.0, color="k", linewidth=0.5)
    axes[1].legend()
    axes[1].grid(alpha=0.3)
    axes[1].set(xlabel="x or y [cm]", ylabel="$B_x$ [T]", title=f"{label}: transverse profiles")

    integral = bending_power(field, rng).T
    limit = np.abs(integral).max()
    mesh = axes[2].pcolormesh(xs, ys, integral, cmap="RdBu_r", vmin=-limit, vmax=limit)
    axes[2].figure.colorbar(mesh, ax=axes[2], label=r"$\int B_x \mathrm{d}z$ [T cm]")
    axes[2].set(xlabel="x [cm]", ylabel="y [cm]", title=f"{label}: bending power")
    axes[2].set_aspect("equal")

    axes[3].plot(zs, field[i0, j0, :, 0], label="$B_x$")
    axes[3].plot(zs, field[i0, j0, :, 1], label="$B_y$")
    axes[3].plot(zs, field[i0, j0, :, 2], label="$B_z$")
    axes[3].legend()
    axes[3].grid(alpha=0.3)
    axes[3].set(xlabel="z [cm]", ylabel="B [T]", title=f"{label}: on the beam axis")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", help="field map to plot")
    parser.add_argument("-o", "--output", default="fieldMap.pdf", help="file to write")
    parser.add_argument(
        "--data-order",
        choices=fmt.ORDERS,
        default="xslow",
        help="how to unroll the entries; xslow is what ShipBFieldMap assumes",
    )
    parser.add_argument(
        "--compare-orders",
        action="store_true",
        help="draw both unrollings side by side",
    )
    parser.add_argument(
        "--no-aperture",
        action="store_true",
        help="leave out the nominal spectrometer aperture outline",
    )
    parser.add_argument(
        "--probe",
        nargs=2,
        type=float,
        action="append",
        metavar=("X", "Y"),
        help="also print the bending power at this (x, y), repeatable",
    )
    args = parser.parse_args()

    rng = fmt.read_range(args.input)
    field = fmt.read_field(args.input, order=args.data_order, rng=rng)
    aperture = None if args.no_aperture else APERTURE

    readings = [(args.data_order, field)]
    if args.compare_orders:
        other = "yslow" if args.data_order == "xslow" else "xslow"
        readings.append((other, fmt.transpose_xy(field)))

    figure, grid = plt.subplots(4, len(readings), figsize=(7 * len(readings), 20), squeeze=False, layout="constrained")
    for column, (label, values) in enumerate(readings):
        draw([grid[row][column] for row in range(4)], rng, values, label, aperture)
    figure.suptitle(args.input)
    figure.savefig(args.output)
    print(f"Wrote {args.output}")

    if args.probe:
        xs, ys, _ = rng.axis_values()
        for label, values in readings:
            integral = bending_power(values, rng)
            for x, y in args.probe:
                i, j = np.abs(xs - x).argmin(), np.abs(ys - y).argmin()
                print(f"  {label}: int Bx dz at ({xs[i]:.0f}, {ys[j]:.0f}) cm = {integral[i, j]:.3f} T cm")
    return 0


if __name__ == "__main__":
    sys.exit(main())
