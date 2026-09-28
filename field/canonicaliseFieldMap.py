#!/bin/python
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Rewrite a FairShip ROOT field map in the ordering ShipBFieldMap expects.

``ShipBFieldMap`` reads the ``Data`` tree sequentially and indexes it as
``(iX*Ny + iY)*Nz + iZ``: z is increased first, then y, then x. A map written
in any other order is read transposed, and when ``Nx == Ny`` with matching x
and y ranges even the entry count still adds up, so nothing complains.

This script reorders the field into that convention and writes the node
coordinates alongside it, so the map states its own ordering and FairShip can
check it at startup.

The input order can be inferred two ways, and the script uses both. The stored
``x``, ``y`` and ``z`` branches say what the writer thought it was doing, and
the divergence of the field says what is actually there: a physical field has
div B = 0, which no transposition survives. When the two disagree the file is
internally inconsistent and the order has to be given on the command line.
"""

import argparse
import hashlib
import sys

import fieldMapTools as fmt
import numpy as np


def checksum(path):
    """Hash of the field components, to tell a repack from a rewrite."""
    field = fmt.read_field(path).ravel()
    return hashlib.sha256(field.tobytes()).hexdigest()[:16]


#: How much cleaner one reading's divergence has to be before it counts as
#: the answer. A field symmetric about the x = y plane scores the same either
#: way up to rounding, and the weakest real map here separates by 1.6.
DIVERGENCE_MARGIN = 1.1


def divergence_order(field, rng):
    """The ordering whose div B is smaller, with both values and the scale.

    The order is None when the two are too close to choose between, so a
    symmetric map is reported as undecided instead of arbitrarily transposed.
    """
    as_read, scale = fmt.div_b_rms(field, rng)
    transposed, _ = fmt.div_b_rms(fmt.transpose_xy(field), rng)
    lower, upper = sorted((as_read, transposed))
    if upper <= lower * DIVERGENCE_MARGIN:
        order = None
    else:
        order = "xslow" if as_read < transposed else "yslow"
    return order, as_read, transposed, scale


def describe(path, rng, field):
    """Print what the file says about itself and what the field says."""
    residuals = fmt.coord_residuals(path, rng)
    print(f"  grid            {rng.Nx} x {rng.Ny} x {rng.Nz} = {rng.N} nodes")
    print(f"  extent mismatch {tuple(float(round(e, 4)) for e in rng.extent_mismatch())} bins")
    if residuals is None:
        print("  coordinates     absent")
    else:
        print(
            f"  coordinates     off by {tuple(float(round(r, 3)) for r in residuals)} bins "
            f"from canonical order -> {fmt.infer_data_order(path, rng) or 'neither'}"
        )
    order, as_read, transposed, scale = divergence_order(field, rng)
    print(
        f"  RMS(div B)      xslow {as_read:.3e}, yslow {transposed:.3e} "
        f"(gradient scale {scale:.3e}) -> {order or 'too close to call'}"
    )
    on_axis = fmt.on_axis(field, rng)
    peaks = [float(np.abs(on_axis[:, i]).max()) for i in range(3)]
    print(f"  peak on axis    Bx {peaks[0]:.4f}, By {peaks[1]:.4f}, Bz {peaks[2]:.4f} T")
    return order


def resolve_order(path, rng, field, requested):
    """Settle on the input ordering, or explain why it cannot be settled."""
    from_field = divergence_order(field, rng)[0]
    from_coords = fmt.infer_data_order(path, rng)

    if requested != "auto":
        if from_field is not None and requested != from_field:
            print(
                f"Warning: --data-order {requested} disagrees with the divergence "
                f"of the field, which points at {from_field}.",
                file=sys.stderr,
            )
        return requested

    if from_field is not None and from_coords is not None and from_coords != from_field:
        raise SystemExit(
            f"{path} is internally inconsistent: its coordinates are written in "
            f"{from_coords} order but its field is only divergence-free read as "
            f"{from_field}. Pass --data-order explicitly once you know which is "
            "right; the coordinates are regenerated either way."
        )
    if from_coords is not None:
        return from_coords
    if from_field is not None:
        print(f"Using {from_field} from the divergence of the field; the map stores no usable coordinates.")
        return from_field
    raise SystemExit(
        f"{path} does not say what order it is in: its coordinates match neither "
        "layout, and its divergence is the same read either way. Pass "
        "--data-order explicitly."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", help="field map to read")
    parser.add_argument("-o", "--output", help="field map to write (omit to only report)")
    parser.add_argument(
        "--data-order",
        choices=("auto", *fmt.ORDERS),
        default="auto",
        help="ordering of the input; auto requires the coordinates and the field to agree",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="report on the input and exit non-zero unless it is already canonical",
    )
    args = parser.parse_args()

    rng = fmt.read_range(args.input)
    field = fmt.read_field(args.input, rng=rng)

    print(f"{args.input}:")
    from_field = describe(args.input, rng, field)

    if args.check_only:
        residuals = fmt.coord_residuals(args.input, rng)
        # An undecided divergence leaves the coordinates as the authority.
        canonical = from_field != "yslow" and residuals is not None and max(residuals) < 0.5
        print("  verdict         " + ("canonical" if canonical else "NEEDS REPACKING"))
        return 0 if canonical else 1

    if not args.output:
        parser.error("give --output, or --check-only to just report")

    order = resolve_order(args.input, rng, field, args.data_order)
    print(f"Reading {args.input} as {order} and writing {args.output}")
    fmt.canonicalise(args.input, args.output, order=order, rng=rng)

    print(f"{args.output}:")
    written = fmt.read_field(args.output)
    describe(args.output, fmt.read_range(args.output), written)
    before, after = checksum(args.input), checksum(args.output)
    print(f"  field contents  {before} -> {after} ({'unchanged' if before == after else 'reordered'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
